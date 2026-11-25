import json

import pytest

from analyst.db import schema_summary
from analyst.entities import load_entities
from analyst.llm import FakeLLM, LLMUnavailable
from analyst.pipeline import QUOTA_MESSAGE, answer, answer_to_record

YEARS = (2021, 2026)
JETT_SQL = "SELECT agent_name, count(*) AS picks FROM fact_player_map WHERE agent_name = 'jett' GROUP BY 1"


def draft(sql, **mentioned):
    return json.dumps({"sql": sql, "mentioned": mentioned})


@pytest.fixture
def run(mini_con):
    schema, ents = schema_summary(mini_con), load_entities(mini_con)

    def _run(responses, question="How many times was Jett picked?", checks_enabled=True):
        llm = FakeLLM(responses)
        a = answer(question, mini_con, llm, ents, schema, "dictionary", YEARS, checks_enabled=checks_enabled)
        return a, llm
    return _run


def test_ok_path(run):
    a, _ = run([draft(JETT_SQL, agents=["Jett"]), "Jett was picked 3 times."])
    assert a.status == "ok", a.message
    assert a.df.iloc[0]["picks"] == 3
    assert [c.name for c in a.checks] == ["safety", "grounding", "runs", "empty", "sanity", "explanation"]


def test_garbage_response_refused(run):
    a, llm = run(["lol no"])
    assert a.status == "refused" and a.df is None and len(llm.prompts) == 1


def test_drop_table_refused(run, mini_con):
    a, _ = run([draft("DROP TABLE dim_agent")])
    assert a.status == "refused"
    assert mini_con.execute("SELECT count(*) FROM dim_agent").fetchone()[0] == 4


def test_retry_fixes_error(run):
    a, llm = run([draft("SELECT agent_nme FROM fact_player_map"), draft(JETT_SQL), "Jett was picked 3 times."])
    assert a.status == "ok", a.message
    assert len(llm.prompts) == 3


def test_retry_fails_refused(run):
    # the bad column passes grounding as an alias, so the failure surfaces when it runs
    bad = "SELECT x.agent_nme FROM (SELECT 1 AS agent_nme) y, fact_player_map x"
    a, _ = run([draft(bad), draft(bad)])
    assert a.status == "refused" and "runs" in a.message


def test_unknown_agent_refused(run):
    a, _ = run([draft(JETT_SQL, agents=["Phoenixx"])])
    assert a.status == "refused" and "Phoenixx" in a.message


def test_empty_no_data(run):
    a, llm = run([draft("SELECT * FROM fact_player_map WHERE kills > 999")])
    assert a.status == "no_data" and a.explanation is None and len(llm.prompts) == 1


def test_hallucinated_number_flagged(run):
    a, _ = run([draft(JETT_SQL), "Jett was picked 71 times."])
    assert a.status == "flagged" and "71" in a.message


def test_quota_unavailable(run):
    a, _ = run([LLMUnavailable("429 RESOURCE_EXHAUSTED")])
    assert a.status == "unavailable" and a.message == QUOTA_MESSAGE


def test_checks_disabled_baseline(run):
    a, _ = run([draft(JETT_SQL, agents=["Phoenixx"]), "Jett was picked 71 times."], checks_enabled=False)
    assert a.status == "ok" and [c.name for c in a.checks] == ["runs"]


def test_record_is_json_safe(run):
    a, _ = run([draft(JETT_SQL), "Jett was picked 3 times."])
    rec = answer_to_record(a)
    json.dumps(rec)
    assert rec["status"] == "ok" and rec["rows"][0]["picks"] == 3
