from analyst.checks import CheckResult
from analyst.pipeline import QUOTA_MESSAGE, Answer
from app.view import badge


def test_badge_ok():
    assert badge(Answer("q", status="ok")) == ("✓ checked", "success")


def test_badge_flagged_shows_first_failed_flag():
    a = Answer("q", status="flagged", checks=[CheckResult("sanity", True, False),
                                              CheckResult("explanation", False, False, "numbers not in the result: 71")])
    assert badge(a) == ("⚠ flagged: numbers not in the result: 71", "warning")


def test_badge_refused():
    a = Answer("q", status="refused", message="grounding: no agent called 'Phoenixx' in the data")
    text, kind = badge(a)
    assert kind == "error" and text.startswith("Couldn't answer:") and "Phoenixx" in text


def test_badge_no_data():
    assert badge(Answer("q", status="no_data")) == ("No data for that question.", "info")


def test_badge_unavailable():
    assert badge(Answer("q", status="unavailable", message=QUOTA_MESSAGE)) == (QUOTA_MESSAGE, "error")


def test_hero_stats(mini_con):
    from app.view import hero_stats
    s = hero_stats(mini_con)
    assert s == {"seasons": "2024", "events": 2, "maps": 3, "players": 4}


def test_pretty_sql_formats_one_line_query():
    from app.view import pretty_sql
    out = pretty_sql("SELECT agent_name, count(*) AS picks FROM fact_team_comp WHERE year = 2024 GROUP BY 1 LIMIT 1000")
    assert out.count("\n") >= 3 and "FROM fact_team_comp" in out


def test_pretty_sql_falls_back_on_unparseable():
    from app.view import pretty_sql
    assert pretty_sql("not sql at all ((") == "not sql at all (("
