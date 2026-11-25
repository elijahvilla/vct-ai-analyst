"""The six checks every AI-written query passes before an answer is shown.

Blocking (answer is never shown if they fail): safety, runs, grounding.
Flag-only (answer shown with a warning): sanity, explanation.
Empty result: replaced by an honest "no data" message.
"""
import re
from dataclasses import dataclass

import duckdb
import pandas as pd
import sqlglot
from sqlglot import exp

from analyst.entities import Entities, normalize

ROW_LIMIT = 1000

# Statement types that change data or the database. Any of these anywhere = blocked.
WRITE_NODES = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Merge, exp.Command)


@dataclass
class CheckResult:
    name: str
    passed: bool
    blocking: bool
    reason: str = ""


# ---------------------------------------------------------------- 1. safety
def check_safety(sql: str) -> tuple[CheckResult, str]:
    """Only one read-only SELECT, and never more than ROW_LIMIT rows.

    DuckDB's own parser decides what the statement is (it understands every query DuckDB can run).
    sqlglot then applies the row limit; if sqlglot can't read the query, it gets wrapped instead.
    """
    try:
        statements = duckdb.extract_statements(sql)
    except duckdb.Error as e:
        return CheckResult("safety", False, True, f"not valid SQL: {str(e).splitlines()[0]}"), sql
    if len(statements) != 1:
        return CheckResult("safety", False, True, f"expected one statement, got {len(statements)}"), sql
    if statements[0].type != duckdb.StatementType.SELECT:
        return CheckResult("safety", False, True, f"only SELECT queries are allowed (got {statements[0].type.name})"), sql
    try:
        stmt = sqlglot.parse_one(sql, read="duckdb")
    except sqlglot.errors.ParseError:
        stmt = None
    if not isinstance(stmt, exp.Query) or any(stmt.find_all(*WRITE_NODES)):
        inner = sql.strip().rstrip(";")
        return CheckResult("safety", True, True), f"SELECT * FROM ({inner}) AS limited LIMIT {ROW_LIMIT}"
    limit = stmt.args.get("limit")
    current = None
    if limit is not None:
        value = limit.args.get("expression") or limit.this
        if isinstance(value, exp.Literal) and value.is_int:
            current = int(value.this)
    if current is None or current > ROW_LIMIT:
        stmt = stmt.limit(ROW_LIMIT)
    return CheckResult("safety", True, True), stmt.sql(dialect="duckdb")


# ---------------------------------------------------------------- 2. runs
def check_runs(con: duckdb.DuckDBPyConnection, sql: str) -> tuple[CheckResult, pd.DataFrame | None]:
    try:
        df = con.execute(sql).fetchdf()
    except duckdb.Error as e:
        return CheckResult("runs", False, True, str(e).splitlines()[0]), None
    return CheckResult("runs", True, True), df


# ---------------------------------------------------------------- 3. grounding
ENTITY_KINDS = ("agents", "maps", "teams", "players", "events")


def _known(kind: str, name: str, ents: Entities) -> bool:
    n = normalize(name)
    pool = getattr(ents, kind)
    if n in pool:
        return True
    # People shorten event names ("Champions 2024" for "Valorant Champions 2024").
    return kind == "events" and len(n) >= 6 and any(n in e for e in pool)


def check_grounding(sql: str, mentioned: dict[str, list[str]], schema: dict[str, list[str]], ents: Entities) -> CheckResult:
    """Every table, column and named agent/map/team/player/event must really exist."""
    problems: list[str] = []
    try:
        tree = sqlglot.parse_one(sql, read="duckdb")
    except sqlglot.errors.ParseError:
        tree = None  # sqlglot can't read it: tables/columns are left to the "runs" check

    if tree is not None:
        problems += _schema_problems(tree, schema)

    for kind in ENTITY_KINDS:
        for name in (mentioned or {}).get(kind, []) or []:
            if name and not _known(kind, name, ents):
                problems.append(f"no {kind[:-1]} called '{name}' in the data")

    if problems:
        return CheckResult("grounding", False, True, "; ".join(dict.fromkeys(problems)))
    return CheckResult("grounding", True, True)


def _schema_problems(tree: exp.Expression, schema: dict[str, list[str]]) -> list[str]:
    problems: list[str] = []
    cte_names = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    known_tables = {t.lower() for t in schema}
    for table in tree.find_all(exp.Table):
        name = table.name.lower()
        if name and name not in known_tables and name not in cte_names:
            problems.append(f"unknown table '{table.name}'")

    known_columns = {c.lower() for cols in schema.values() for c in cols}
    defined_here = {a.alias.lower() for a in tree.find_all(exp.Alias) if a.alias}
    defined_here |= {c.name.lower() for ta in tree.find_all(exp.TableAlias) for c in ta.columns}
    for col in tree.find_all(exp.Column):
        name = col.name.lower()
        if name and name not in known_columns and name not in defined_here:
            problems.append(f"unknown column '{col.name}'")
    return problems


# ---------------------------------------------------------------- 4. sanity
RATE_COLS = re.compile(r"rate|pct|percent|ratio", re.I)
COUNT_COLS = re.compile(r"count|kills|deaths|assists|picks|matches|maps|rounds|wins|losses", re.I)


def check_sanity(df: pd.DataFrame, year_range: tuple[int, int]) -> CheckResult:
    """Numbers must be possible: rates within 0-1 or 0-100, counts not negative, years in the data."""
    problems: list[str] = []
    for col in df.columns:
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if values.empty:
            continue
        name = str(col)
        if RATE_COLS.search(name) and (values.min() < 0 or values.max() > 100):
            problems.append(f"{name} has values outside 0-100 (max {values.max():g})")
        if COUNT_COLS.search(name) and values.min() < 0:
            problems.append(f"{name} has negative values (min {values.min():g})")
        if name.lower() == "year":
            outside = sorted({int(v) for v in values if not year_range[0] <= v <= year_range[1]})
            if outside:
                problems.append(f"year {outside[0]} is outside the data ({year_range[0]}-{year_range[1]})")
    if problems:
        return CheckResult("sanity", False, False, "; ".join(problems))
    return CheckResult("sanity", True, False)


# ---------------------------------------------------------------- 5. explanation
NUMBER = re.compile(r"(?<![\w.])-?\d+(?:,\d{3})*(?:\.\d+)?")


def _candidates(df: pd.DataFrame) -> set[float]:
    """Every number in the result, plus its percent/fraction twin, rounded to 1 decimal."""
    out: set[float] = set()
    for col in df.columns:
        for v in pd.to_numeric(df[col], errors="coerce").dropna():
            v = float(v)
            out |= {round(v, 1), round(v * 100, 1), round(v / 100, 1), float(round(v))}
    return out


def check_explanation(explanation: str, df: pd.DataFrame, year_range: tuple[int, int], question: str = "") -> CheckResult:
    """Every number the AI writes must come from the result table or the question (catches made-up numbers)."""
    allowed = _candidates(df) | {round(float(q.replace(",", "")), 1) for q in NUMBER.findall(question or "")}
    bad = []
    for raw in NUMBER.findall(explanation or ""):
        n = float(raw.replace(",", ""))
        if n.is_integer() and year_range[0] - 5 <= n <= year_range[1] + 1:
            continue  # a year, e.g. "Champions 2024"
        if round(n, 1) not in allowed and float(round(n)) not in allowed:
            bad.append(raw)
    if bad:
        return CheckResult("explanation", False, False, f"numbers not in the result: {', '.join(bad)}")
    return CheckResult("explanation", True, False)


# ---------------------------------------------------------------- 6. empty
def check_empty(df: pd.DataFrame) -> CheckResult:
    if df is None or len(df) == 0:
        return CheckResult("empty", False, False, "the query returned no rows")
    return CheckResult("empty", True, False)
