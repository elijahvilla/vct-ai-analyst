"""Pure display helpers for the Streamlit page (kept out of the page so they can be tested)."""
from analyst.pipeline import Answer


def badge(a: Answer) -> tuple[str, str]:
    """(text, Streamlit message kind) for an answer's status."""
    if a.status == "ok":
        return "✓ checked", "success"
    if a.status == "flagged":
        reason = next((c.reason for c in a.checks if not c.passed and not c.blocking and c.name != "empty"), a.message)
        return f"⚠ flagged: {reason}", "warning"
    if a.status == "no_data":
        return "No data for that question.", "info"
    if a.status == "unavailable":
        return a.message, "error"
    return f"Couldn't answer: {a.message}", "error"
