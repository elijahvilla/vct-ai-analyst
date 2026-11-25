import pandas as pd

from analyst.pipeline import Answer
from eval.score import score


def ans(df=None, status="ok"):
    return Answer(question="q", df=df, status=status)


GOLD = pd.DataFrame({"agent_name": ["omen", "sova"], "pick_rate_pct": [62.2, 52.3]})


def test_score_exact_match():
    assert score(ans(GOLD.copy()), GOLD) == "correct"


def test_score_ignores_row_order():
    assert score(ans(GOLD.iloc[::-1].reset_index(drop=True)), GOLD) == "correct"


def test_score_ignores_column_names_and_extra_columns():
    df = pd.DataFrame({"agent": ["omen", "sova"], "times": [107, 90], "rate": [62.2, 52.3]})
    assert score(ans(df), GOLD) == "correct"


def test_score_rounds_to_one_decimal():
    df = pd.DataFrame({"a": ["omen", "sova"], "r": [62.24, 52.31]})
    assert score(ans(df), GOLD) == "correct"


def test_score_accepts_fraction_scale():
    df = pd.DataFrame({"a": ["omen", "sova"], "r": [0.622, 0.523]})
    assert score(ans(df), GOLD) == "correct"


def test_score_counts_exact():
    gold = pd.DataFrame({"player": ["aspas"], "kills": [731]})
    assert score(ans(pd.DataFrame({"p": ["aspas"], "k": [730]})), gold) == "wrong"


def test_score_case_insensitive_text():
    gold = pd.DataFrame({"player": ["aspas"], "kills": [731]})
    assert score(ans(pd.DataFrame({"p": ["Aspas"], "k": [731.0]})), gold) == "correct"


def test_score_extra_rows_wrong():
    df = pd.DataFrame({"a": ["omen", "sova", "viper"], "r": [62.2, 52.3, 50.0]})
    assert score(ans(df), GOLD) == "wrong"


def test_score_refused():
    assert score(ans(status="refused"), GOLD) == "refused"
    assert score(ans(status="no_data"), GOLD) == "refused"
    assert score(ans(status="unavailable"), GOLD) == "refused"


def test_score_flagged_scored_by_content():
    assert score(ans(GOLD.copy(), status="flagged"), GOLD) == "correct"


def test_score_impossible_question_refused_is_correct():
    assert score(ans(status="refused"), None) == "correct"
    assert score(ans(status="no_data"), None) == "correct"
    assert score(ans(GOLD.copy()), None) == "wrong"
