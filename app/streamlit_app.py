"""VCT AI Analyst — ask about pro Valorant in plain English.  Run: streamlit run app/streamlit_app.py"""
import pathlib
import sys

import streamlit as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyst.db import connect, schema_summary  # noqa: E402
from analyst.entities import load_entities  # noqa: E402
from analyst.llm import GeminiLLM, LLMUnavailable  # noqa: E402
from analyst.pipeline import QUOTA_MESSAGE, Answer, answer  # noqa: E402
from app.view import badge  # noqa: E402

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
    return con, schema_summary(con), load_entities(con), dictionary


@st.cache_resource
def model():
    key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None
    return GeminiLLM(api_key=key)


st.set_page_config(page_title="VCT AI Analyst", page_icon="🎯", layout="centered")
st.title("VCT AI Analyst")
st.caption("Ask about pro Valorant (VCT 2021–2026). An AI writes the SQL; six checks catch its mistakes before you see the answer.")

if "question" not in st.session_state:
    st.session_state.question = ""
cols = st.columns(2)
for i, ex in enumerate(EXAMPLES):
    if cols[i % 2].button(ex, use_container_width=True):
        st.session_state.question = ex

question = st.text_input("Your question", key="question", placeholder="e.g. Which agents had the best win rate on Lotus in 2025?")

if question:
    con, schema, ents, dictionary = resources()
    with st.spinner("Thinking…"):
        try:
            a = answer(question, con, model(), ents, schema, dictionary, YEARS)
        except LLMUnavailable:
            a = Answer(question=question, status="unavailable", message=QUOTA_MESSAGE)
    text, kind = badge(a)
    getattr(st, kind)(text)
    if a.df is not None:
        st.dataframe(a.df, hide_index=True, use_container_width=True)
    if a.explanation:
        st.write(a.explanation)
    with st.expander("How this answer was made"):
        if a.sql:
            st.code(a.sql, language="sql")
        for c in a.checks:
            icon = "✅" if c.passed else ("⛔" if c.blocking else "⚠️")
            st.write(f"{icon} **{c.name}**" + (f" — {c.reason}" if c.reason else ""))

st.divider()
st.caption(f"Data: Kaggle “Valorant Champion Tour 2021–2026 Data” by Ryan Luong (MIT), from vlr.gg. "
           f"Code and accuracy report: [GitHub]({REPO_URL}). Built with AI assistance.")
