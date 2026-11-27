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


def test_chart_spec_ranking_is_bar():
    import pandas as pd
    from app.view import chart_spec
    df = pd.DataFrame({"agent_name": ["omen", "sova", "viper"], "pick_rate_pct": [62.2, 52.3, 50.0]})
    assert chart_spec(df) == {"kind": "bar", "x": "agent_name", "y": "pick_rate_pct"}


def test_chart_spec_year_trend_is_line():
    import pandas as pd
    from app.view import chart_spec
    df = pd.DataFrame({"year": [2021, 2022, 2023], "maps": [14441, 8856, 900]})
    assert chart_spec(df) == {"kind": "line", "x": "year", "y": "maps"}


def test_chart_spec_skips_single_values_and_text_only():
    import pandas as pd
    from app.view import chart_spec
    assert chart_spec(pd.DataFrame({"kills": [731]})) is None
    assert chart_spec(pd.DataFrame({"agent_name": ["omen", "sova"]})) is None
    assert chart_spec(pd.DataFrame({"player": ["aspas"], "kills": [731]})) is None


def test_chart_spec_handles_decimal_numbers():
    # regression: DuckDB returns ROUND(...) on numerics as Decimal objects, which pandas sees as text
    from decimal import Decimal
    import pandas as pd
    from app.view import chart_spec
    df = pd.DataFrame({"agent_name": ["omen", "sova"], "pick_rate_pct": [Decimal("62.2"), Decimal("52.3")]})
    assert chart_spec(df) == {"kind": "bar", "x": "agent_name", "y": "pick_rate_pct"}


def test_build_chart_bar_from_decimal_ranking():
    from decimal import Decimal
    import pandas as pd
    from app.view import build_chart
    df = pd.DataFrame({"agent_name": ["omen", "sova"], "pick_rate_pct": [Decimal("62.2"), Decimal("52.3")]})
    spec = build_chart(df).to_dict()
    assert spec["mark"]["type"] == "bar" and spec["mark"]["color"] == "#FF4655"
    assert spec["encoding"]["y"]["field"] == "agent_name"


def test_build_chart_none_for_single_row():
    import pandas as pd
    from app.view import build_chart
    assert build_chart(pd.DataFrame({"player": ["aspas"], "kills": [731]})) is None
