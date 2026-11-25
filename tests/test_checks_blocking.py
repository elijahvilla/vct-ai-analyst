import pytest

from analyst.checks import check_grounding, check_runs, check_safety
from analyst.db import schema_summary
from analyst.entities import load_entities


def test_safety_allows_select():
    res, sql = check_safety("SELECT agent_name FROM dim_agent")
    assert res.passed and res.blocking and res.name == "safety"
    assert "LIMIT 1000" in sql.upper()


def test_safety_keeps_smaller_limit():
    res, sql = check_safety("SELECT agent_name FROM dim_agent LIMIT 5")
    assert res.passed
    assert "LIMIT 5" in sql.upper() and "1000" not in sql


def test_safety_caps_bigger_limit():
    res, sql = check_safety("SELECT agent_name FROM dim_agent LIMIT 50000")
    assert res.passed and "LIMIT 1000" in sql.upper()


@pytest.mark.parametrize("bad", [
    "DROP TABLE dim_agent",
    "DELETE FROM dim_agent",
    "UPDATE dim_agent SET role = 'duelist'",
    "CREATE TABLE x AS SELECT 1",
    "INSERT INTO dim_map VALUES ('Fake')",
])
def test_safety_blocks_writes(bad):
    res, _ = check_safety(bad)
    assert not res.passed and res.blocking


def test_safety_blocks_multiple_statements():
    res, _ = check_safety("SELECT 1; DROP TABLE dim_map")
    assert not res.passed


def test_safety_blocks_unparseable():
    res, _ = check_safety("here is your query!")
    assert not res.passed


def test_runs_ok(mini_con):
    res, df = check_runs(mini_con, "SELECT agent_name FROM dim_agent")
    assert res.passed and len(df) == 4


def test_runs_error(mini_con):
    res, df = check_runs(mini_con, "SELECT * FROM nope")
    assert not res.passed and res.blocking and df is None
    assert "nope" in res.reason


@pytest.fixture
def ctx(mini_con):
    return schema_summary(mini_con), load_entities(mini_con)


def test_grounding_ok(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT a.role FROM dim_agent a WHERE a.agent_name = 'jett'", {"agents": ["Jett"]}, schema, ents)
    assert res.passed, res.reason


def test_grounding_unknown_table(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT * FROM agents_table", {}, schema, ents)
    assert not res.passed and res.blocking and "agents_table" in res.reason


def test_grounding_unknown_column(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT win_rate FROM dim_agent", {}, schema, ents)
    assert not res.passed and "win_rate" in res.reason


def test_grounding_allows_aliases_and_ctes(ctx):
    schema, ents = ctx
    sql = ("WITH w AS (SELECT agent_name, avg((result = 'win')::INT) AS win_rate FROM fact_team_comp GROUP BY 1) "
           "SELECT w.agent_name, w.win_rate FROM w ORDER BY w.win_rate DESC")
    res = check_grounding(sql, {}, schema, ents)
    assert res.passed, res.reason


def test_grounding_case_insensitive(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT 1", {"agents": ["jett", "Kay/O"], "teams": ["SENTINELS"]}, schema, ents)
    assert res.passed, res.reason


def test_grounding_unknown_agent(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT 1", {"agents": ["Phoenixx"]}, schema, ents)
    assert not res.passed and "Phoenixx" in res.reason


def test_grounding_unknown_event(ctx):
    schema, ents = ctx
    res = check_grounding("SELECT 1", {"events": ["Champions 2019"]}, schema, ents)
    assert not res.passed and "Champions 2019" in res.reason


def test_grounding_event_partial_name_ok(ctx):
    # people say "Champions 2024", the table says "Valorant Champions 2024"
    schema, ents = ctx
    res = check_grounding("SELECT 1", {"events": ["Champions 2024"]}, schema, ents)
    assert res.passed, res.reason
