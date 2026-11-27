from analyst.llm import FakeLLM, LLMUnavailable
from analyst.prompt import (build_explain_prompt, build_fix_prompt, build_sql_prompt,
                            parse_sql_response)

GOOD = '{"sql": "SELECT agent_name FROM dim_agent", "mentioned": {"agents": ["Jett"], "maps": []}}'


def test_parse_raw_json():
    d = parse_sql_response(GOOD)
    assert d.sql == "SELECT agent_name FROM dim_agent"
    assert d.mentioned["agents"] == ["Jett"]
    assert d.mentioned["teams"] == []  # missing kinds filled in


def test_parse_fenced_json():
    d = parse_sql_response("Here you go:\n```json\n" + GOOD + "\n```\n")
    assert d is not None and d.sql.startswith("SELECT")


def test_parse_garbage_returns_none():
    assert parse_sql_response("Sure! Here's a query: SELECT * FROM dim_agent") is None


def test_parse_missing_sql_returns_none():
    assert parse_sql_response('{"mentioned": {}}') is None
    assert parse_sql_response('{"sql": ""}') is None


def test_sql_prompt_contains_dictionary_and_question():
    p = build_sql_prompt("Who played the most Jett?", "## dim_agent — agents")
    assert "Who played the most Jett?" in p and "## dim_agent — agents" in p
    assert "JSON" in p and "SELECT" in p


def test_explain_prompt_contains_table():
    p = build_explain_prompt("Top agents?", "| agent | picks |\n| jett | 40 |")
    assert "jett | 40" in p and "Top agents?" in p


def test_fix_prompt_contains_error():
    p = build_fix_prompt("q", "SELECT x FROM y", "Table y does not exist", "dict")
    assert "Table y does not exist" in p and "SELECT x FROM y" in p


def test_fake_llm_returns_and_raises_in_order():
    llm = FakeLLM(["a", LLMUnavailable("429")])
    assert llm.complete("p1") == "a"
    try:
        llm.complete("p2")
        assert False
    except LLMUnavailable:
        pass
    assert llm.prompts == ["p1", "p2"]


def test_read_secret_from_streamlit_file(tmp_path, monkeypatch):
    from analyst.llm import read_secret
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    f = tmp_path / "secrets.toml"
    f.write_text('# comment\nGEMINI_API_KEY = "abc123"\n')
    assert read_secret("GEMINI_API_KEY", str(f)) == "abc123"


def test_read_secret_prefers_environment(tmp_path, monkeypatch):
    from analyst.llm import read_secret
    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    assert read_secret("GEMINI_API_KEY", str(tmp_path / "missing.toml")) == "from-env"


def test_explain_prompt_asks_to_name_the_measure():
    assert "which measure" in build_explain_prompt("best map for Chamber?", "map,picks\nIcebox,1405")
