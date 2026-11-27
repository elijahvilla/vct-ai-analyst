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


def hero_stats(con) -> dict:
    """Headline numbers for the page banner, read live from the database."""
    lo, hi, events, maps = con.execute(
        "SELECT min(year), max(year), count(DISTINCT event_id), count(*) FROM fact_map_result").fetchone()
    players = con.execute("SELECT count(DISTINCT player_id) FROM fact_player_map").fetchone()[0]
    seasons = str(lo) if lo == hi else f"{lo}–{hi}"
    return {"seasons": seasons, "events": events, "maps": maps, "players": players}
