"""VCT AI Analyst — ask about pro Valorant in plain English.  Run: streamlit run app/streamlit_app.py"""
import html
import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyst.db import connect, schema_summary  # noqa: E402
from analyst.entities import load_entities  # noqa: E402
from analyst.llm import GeminiLLM, LLMUnavailable  # noqa: E402
from analyst.pipeline import QUOTA_MESSAGE, Answer, answer  # noqa: E402
from app.style import CSS  # noqa: E402
from app.view import badge, hero_stats  # noqa: E402

YEARS = (2021, 2026)
REPO_URL = "https://github.com/elijahvilla/vct-ai-analyst"
EXAMPLES = [
    "Which 5 agents had the highest pick rate at Valorant Champions 2024?",
    "Which player had the most kills on Jett in 2025?",
    "What is Sentinels' map win rate on Ascent across all years?",
    "Which team won the most maps at Valorant Champions 2023?",
]


@st.cache_resource
def resources():
    con = connect(str(ROOT / "data" / "vct.duckdb"))
    dictionary = (ROOT / "docs" / "data_dictionary.md").read_text(encoding="utf-8")
    return con, schema_summary(con), load_entities(con), dictionary, hero_stats(con)


@st.cache_resource
def model():
    try:
        key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        key = None
    return GeminiLLM(api_key=key)


def set_question(q: str) -> None:
    st.session_state.question = q


st.set_page_config(page_title="VCT AI Analyst", page_icon="🎯", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)
con, schema, ents, dictionary, stats = resources()

st.markdown(f"""
<div class="hero">
  <div class="kicker">Pro Valorant · AI analyst</div>
  <h1>VCT <span>AI</span> Analyst</h1>
  <p>Ask anything about pro matches in plain English. An AI writes the SQL, and six checks catch its mistakes before you see the answer.</p>
  <div class="stats">
    <div class="stat"><b>{stats['seasons']}</b><small>Seasons</small></div>
    <div class="stat"><b>{stats['events']:,}</b><small>Events</small></div>
    <div class="stat"><b>{stats['maps']:,}</b><small>Maps played</small></div>
    <div class="stat"><b>{stats['players']:,}</b><small>Players</small></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="label">Try one</div>', unsafe_allow_html=True)
cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True, on_click=set_question, args=(ex,))

st.markdown('<div class="label">Ask your own</div>', unsafe_allow_html=True)
question = st.text_input("Your question", key="question", label_visibility="collapsed",
                         placeholder="e.g. Which agents had the best win rate on Lotus in 2025?")

if question:
    with st.spinner("Analyzing the VOD… (10–20 seconds on the free AI tier)"):
        try:
            a = answer(question, con, model(), ents, schema, dictionary, YEARS)
        except LLMUnavailable:
            a = Answer(question=question, status="unavailable", message=QUOTA_MESSAGE)
    text, kind = badge(a)
    body = html.escape(a.explanation) if a.explanation else ""
    st.markdown(f"""
<div class="card">
  <span class="verdict {kind}">{html.escape(text)}</span>
  <div class="q">{html.escape(question)}</div>
  <div class="a">{body}</div>
</div>""", unsafe_allow_html=True)
    if a.df is not None:
        st.dataframe(a.df, hide_index=True, use_container_width=True)
    with st.expander("How this answer was made"):
        if a.sql:
            st.code(a.sql, language="sql")
        rows = []
        for c in a.checks:
            dot = "ok" if c.passed else ("block" if c.blocking else "flag")
            why = html.escape(c.reason) if c.reason else ("passed" if c.passed else "")
            rows.append(f'<div class="check"><span class="dot {dot}"></span><span class="name">{c.name}</span>'
                        f'<span class="why">{why}</span></div>')
        st.markdown("".join(rows) or "No checks ran.", unsafe_allow_html=True)

st.markdown(f"""
<div class="foot">
Data: Kaggle “Valorant Champion Tour 2021–2026 Data” by Ryan Luong (MIT license), originally from vlr.gg.
Code and accuracy report on <a href="{REPO_URL}">GitHub</a>. Built with AI assistance.
Fan project, not affiliated with or endorsed by Riot Games.
</div>""", unsafe_allow_html=True)
