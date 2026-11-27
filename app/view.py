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


def pretty_sql(sql: str) -> str:
    """Multi-line, indented SQL for display; unchanged if it can't be parsed."""
    import sqlglot

    try:
        return sqlglot.transpile(sql, read="duckdb", write="duckdb", pretty=True)[0]
    except Exception:
        return sql


def chart_spec(df) -> dict | None:
    """Pick a chart for a result: year trends -> line, rankings of names -> bar, else none."""
    import pandas as pd

    if df is None or len(df) < 2 or len(df) > 30:
        return None
    def is_num(c) -> bool:
        return pd.api.types.is_numeric_dtype(df[c]) or pd.to_numeric(df[c], errors="coerce").notna().all()

    numeric = [c for c in df.columns if is_num(c) and str(c).lower() != "year"]
    text = [c for c in df.columns if not is_num(c)]
    if "year" in [str(c).lower() for c in df.columns] and numeric:
        year = next(c for c in df.columns if str(c).lower() == "year")
        return {"kind": "line", "x": year, "y": numeric[0]}
    if len(text) == 1 and numeric:
        return {"kind": "bar", "x": text[0], "y": numeric[-1]}
    return None


def build_chart(df):
    """Altair chart (Valorant red) for a result, or None when a chart wouldn't help."""
    import altair as alt

    spec = chart_spec(df)
    if not spec:
        return None
    data = df.head(30).copy()
    data[spec["y"]] = data[spec["y"]].astype(float)
    label = str(spec["y"]).replace("_", " ")
    if spec["kind"] == "bar":
        chart = alt.Chart(data).mark_bar(color="#FF4655").encode(
            x=alt.X(f"{spec['y']}:Q", title=label), y=alt.Y(f"{spec['x']}:N", sort="-x", title=None))
    else:
        chart = alt.Chart(data).mark_line(color="#FF4655", point=True).encode(
            x=alt.X(f"{spec['x']}:O", title=None), y=alt.Y(f"{spec['y']}:Q", title=label))
    return chart.properties(height=min(40 * len(data) + 40, 420))
