"""The six checks every AI-written query passes before an answer is shown.

Blocking (answer is never shown if they fail): safety, runs, grounding.
Flag-only (answer shown with a warning): sanity, explanation.
Empty result: replaced by an honest "no data" message.
"""
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
    """Only one read-only SELECT, and never more than ROW_LIMIT rows."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except sqlglot.errors.ParseError as e:
        return CheckResult("safety", False, True, f"not valid SQL: {str(e).splitlines()[0]}"), sql
    if len(statements) != 1:
        return CheckResult("safety", False, True, f"expected one statement, got {len(statements)}"), sql
    stmt = statements[0]
    if not isinstance(stmt, exp.Query) or any(stmt.find_all(*WRITE_NODES)):
        return CheckResult("safety", False, True, f"only SELECT queries are allowed (got {type(stmt).__name__})"), sql
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
    except sqlglot.errors.ParseError as e:
        return CheckResult("grounding", False, True, f"not valid SQL: {str(e).splitlines()[0]}")

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

    for kind in ENTITY_KINDS:
        for name in (mentioned or {}).get(kind, []) or []:
            if name and not _known(kind, name, ents):
                problems.append(f"no {kind[:-1]} called '{name}' in the data")

    if problems:
        return CheckResult("grounding", False, True, "; ".join(dict.fromkeys(problems)))
    return CheckResult("grounding", True, True)
