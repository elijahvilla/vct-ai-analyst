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
