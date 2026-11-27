"""Question in, checked answer out. Used by the Streamlit app and the eval runner."""
from dataclasses import dataclass, field
from typing import Literal

import duckdb
import pandas as pd

from analyst.checks import (CheckResult, check_empty, check_explanation, check_grounding,
                            check_runs, check_safety, check_sanity)
from analyst.entities import Entities
from analyst.llm import LLM, LLMUnavailable
from analyst.prompt import build_explain_prompt, build_fix_prompt, build_sql_prompt, parse_sql_response

QUOTA_MESSAGE = "The free AI quota is used up for now, try again later."
Status = Literal["ok", "flagged", "refused", "no_data", "unavailable"]


@dataclass
class Answer:
    question: str
    sql: str | None = None
    df: pd.DataFrame | None = None
    explanation: str | None = None
    checks: list[CheckResult] = field(default_factory=list)
    status: Status = "refused"
    message: str = ""


def _refuse(a: Answer, check: CheckResult) -> Answer:
    a.status, a.message = "refused", f"{check.name}: {check.reason}"
    return a


def answer(question: str, con: duckdb.DuckDBPyConnection, llm: LLM, ents: Entities,
           schema: dict[str, list[str]], dictionary: str, year_range: tuple[int, int],
           checks_enabled: bool = True) -> Answer:
    a = Answer(question=question)
    try:
        draft = parse_sql_response(llm.complete(build_sql_prompt(question, dictionary)))
        if draft is None:
            a.message = "parse: the AI did not return a query"
            return a
        if draft.unanswerable:
            a.message = f"unanswerable: {draft.unanswerable}"
            return a
        a.sql = draft.sql

        if not checks_enabled:  # baseline for the eval: raw AI SQL, no checks, no retry
            res, df = check_runs(con, draft.sql)
            a.checks = [res]
            if not res.passed:
                return _refuse(a, res)
            a.df = df
            a.explanation = llm.complete(build_explain_prompt(question, df.head(50).to_csv(index=False)))
            a.status = "ok"
            return a

        retried = False
        while True:
            a.checks = []
            safety, safe_sql = check_safety(draft.sql)
            a.checks.append(safety)
            if not safety.passed:
                return _refuse(a, safety)
            a.sql = safe_sql

            schema_only = check_grounding(safe_sql, {}, schema, ents)
            grounding = check_grounding(safe_sql, draft.mentioned, schema, ents) if schema_only.passed else schema_only
            a.checks.append(grounding)
            if not schema_only.passed and not retried:  # typo in a table/column: let the AI fix it once
                retried = True
                fixed = parse_sql_response(llm.complete(build_fix_prompt(question, safe_sql, grounding.reason, dictionary)))
                if fixed is None:
                    return _refuse(a, grounding)
                draft = fixed
                continue
            if not grounding.passed:
                return _refuse(a, grounding)

            runs, df = check_runs(con, safe_sql)
            a.checks.append(runs)
            if not runs.passed and not retried:
                retried = True
                fixed = parse_sql_response(llm.complete(build_fix_prompt(question, safe_sql, runs.reason, dictionary)))
                if fixed is None:
                    return _refuse(a, runs)
                draft = fixed
                continue
            if not runs.passed:
                return _refuse(a, runs)
            break

        empty = check_empty(df)
        a.checks.append(empty)
        if not empty.passed:
            a.status, a.message = "no_data", "No data for that question."
            return a
        a.df = df

        try:
            a.explanation = llm.complete(build_explain_prompt(question, df.head(50).to_csv(index=False)))
        except LLMUnavailable:  # the table is already checked; only the summary sentence is missing
            a.explanation = None
        flags = [check_sanity(df, year_range)]
        if a.explanation is not None:
            flags.append(check_explanation(a.explanation, df, year_range, question))
        a.checks.extend(flags)
        failed = [f for f in flags if not f.passed]
        if failed:
            a.status, a.message = "flagged", "; ".join(f"{f.name}: {f.reason}" for f in failed)
        else:
            a.status = "ok"
        if a.explanation is None:
            a.message = (a.message + "; " if a.message else "") + "explanation unavailable (free AI quota), table is checked"
        return a
    except LLMUnavailable:
        a.status, a.message = "unavailable", QUOTA_MESSAGE
        return a


def answer_to_record(a: Answer) -> dict:
    """JSON-safe version for logs and eval results (at most 50 rows)."""
    rows = [] if a.df is None else a.df.head(50).astype(object).where(a.df.head(50).notna(), None).to_dict("records")
    return {
        "question": a.question,
        "sql": a.sql,
        "status": a.status,
        "message": a.message,
        "explanation": a.explanation,
        "checks": [{"name": c.name, "passed": c.passed, "blocking": c.blocking, "reason": c.reason} for c in a.checks],
        "rows": [{k: (v.item() if hasattr(v, "item") else v) for k, v in r.items()} for r in rows],
    }
