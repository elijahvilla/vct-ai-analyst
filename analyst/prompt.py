"""Prompts sent to the model, and parsing of its answers."""
import json
import re
from dataclasses import dataclass, field

ENTITY_KINDS = ("agents", "maps", "teams", "players", "events")


@dataclass
class SqlDraft:
    sql: str
    mentioned: dict[str, list[str]] = field(default_factory=dict)
    unanswerable: str = ""


def build_sql_prompt(question: str, data_dictionary: str) -> str:
    return f"""You write DuckDB SQL for a database of professional Valorant (VCT) matches.

Use ONLY the tables and columns in this data dictionary:
{data_dictionary}

Rules:
- One read-only SELECT statement (CTEs allowed). Never modify data.
- Agent names are lowercase in the data ('jett', 'kayo' for KAY/O). Match names case-insensitively.
- Count maps with count(DISTINCT match_map_id); never count player rows as maps.
- Give rates as percentages 0-100 rounded to 1 decimal, with clear column names.
- If these tables cannot answer the question (for example viewers, prize money, salaries or anything not listed),
  do not answer a different question. Reply {{"sql": "", "unanswerable": "<short reason>"}} instead.

Also list every agent, map, team, player and event NAME the question refers to, exactly as written in the question.

Reply with JSON only, no prose:
{{"sql": "...", "mentioned": {{"agents": [], "maps": [], "teams": [], "players": [], "events": []}}}}

Question: {question}"""


def build_fix_prompt(question: str, sql: str, error: str, data_dictionary: str) -> str:
    return f"""Your DuckDB query failed. Fix it.

Data dictionary:
{data_dictionary}

Question: {question}
Query: {sql}
Error: {error}

Reply with JSON only: {{"sql": "...", "mentioned": {{"agents": [], "maps": [], "teams": [], "players": [], "events": []}}}}"""


def build_explain_prompt(question: str, result_markdown: str) -> str:
    return f"""Answer the question in 1-3 short sentences using ONLY the numbers in this result table.
Do not add numbers that are not in the table. Do not guess beyond it.
If the question uses a vague word like "best" or "top", say which measure the table uses (e.g. most picks, highest win rate).

Question: {question}
Result:
{result_markdown}"""


def parse_sql_response(text: str) -> SqlDraft | None:
    """Accept raw JSON or JSON inside a ``` fence. Anything else -> None (refused, never run)."""
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else text.strip()
    if not candidate.startswith("{"):
        return None
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    sql = (data.get("sql") or "").strip()
    reason = str(data.get("unanswerable") or "").strip()
    if not sql and reason:
        return SqlDraft(sql="", mentioned={k: [] for k in ENTITY_KINDS}, unanswerable=reason)
    if not sql:
        return None
    raw = data.get("mentioned") or {}
    mentioned = {k: [str(x) for x in (raw.get(k) or [])] for k in ENTITY_KINDS}
    return SqlDraft(sql=sql, mentioned=mentioned)
