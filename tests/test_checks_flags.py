import pandas as pd

from analyst.checks import check_empty, check_explanation, check_sanity

YEARS = (2021, 2026)


def test_sanity_rate_fraction_ok():
    assert check_sanity(pd.DataFrame({"agent": ["jett"], "win_rate": [0.62]}), YEARS).passed


def test_sanity_rate_percent_ok():
    assert check_sanity(pd.DataFrame({"agent": ["jett"], "win_rate": [62.0]}), YEARS).passed


def test_sanity_rate_out_of_range():
    res = check_sanity(pd.DataFrame({"agent": ["jett"], "pick_rate": [140.0]}), YEARS)
    assert not res.passed and not res.blocking and "pick_rate" in res.reason


def test_sanity_negative_count():
    res = check_sanity(pd.DataFrame({"player": ["TenZ"], "kills": [-3]}), YEARS)
    assert not res.passed and "kills" in res.reason


def test_sanity_year_outside():
    res = check_sanity(pd.DataFrame({"year": [2019], "maps": [10]}), YEARS)
    assert not res.passed and "2019" in res.reason


def test_sanity_ignores_text_columns_with_rate_in_name():
    assert check_sanity(pd.DataFrame({"rate_label": ["high"]}), YEARS).passed


def test_explanation_matches_fraction_as_percent():
    df = pd.DataFrame({"agent": ["jett"], "pick_rate": [0.625]})
    assert check_explanation("Jett had a 62.5% pick rate.", df, YEARS).passed


def test_explanation_matches_rounded_value():
    df = pd.DataFrame({"agent": ["omen"], "win_pct": [52.34]})
    assert check_explanation("Omen won 52.3% of maps.", df, YEARS).passed


def test_explanation_hallucinated_number():
    df = pd.DataFrame({"agent": ["jett"], "maps_won": [64]})
    res = check_explanation("Jett won 71 maps.", df, YEARS)
    assert not res.passed and not res.blocking and "71" in res.reason


def test_explanation_ignores_years():
    df = pd.DataFrame({"agent": ["jett"], "maps_won": [64]})
    assert check_explanation("At Champions 2024, Jett won 64 maps.", df, YEARS).passed


def test_explanation_no_numbers():
    df = pd.DataFrame({"agent": ["jett"]})
    assert check_explanation("Jett was the most picked agent.", df, YEARS).passed


def test_empty():
    res = check_empty(pd.DataFrame({"agent": []}))
    assert not res.passed and res.name == "empty" and not res.blocking


def test_not_empty():
    assert check_empty(pd.DataFrame({"agent": ["jett"]})).passed


def test_explanation_allows_numbers_from_the_question():
    # regression: "Which 5 agents..." -> "The 5 agents ..." was flagged as a made-up number
    df = pd.DataFrame({"agent_name": ["omen"], "pick_rate_pct": [62.2]})
    res = check_explanation("The 5 agents with the highest pick rates: omen at 62.2.", df, YEARS,
                            question="Which 5 agents had the highest pick rate?")
    assert res.passed, res.reason


def test_explanation_still_flags_numbers_not_in_question_or_result():
    df = pd.DataFrame({"agent_name": ["omen"], "pick_rate_pct": [62.2]})
    res = check_explanation("The 5 agents: omen at 71.0.", df, YEARS, question="Which 5 agents?")
    assert not res.passed and "71" in res.reason
