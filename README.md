# VCT AI Analyst

**Ask about pro Valorant in plain English. An AI writes the SQL, and six checks catch its mistakes before you see the answer.**

[![tests](https://github.com/elijahvilla/vct-ai-analyst/actions/workflows/tests.yml/badge.svg)](https://github.com/elijahvilla/vct-ai-analyst/actions/workflows/tests.yml)
**Live app:** link coming shortly

![Demo: asking about Champions 2024 pick rates, a vague question getting clarified, and a fake player getting blocked](docs/media/demo.gif)

## What it does

Type a question like *"Which 5 agents had the highest pick rate at Valorant Champions 2024?"* and get:

- a table and a chart of the answer
- a one-sentence explanation
- a verdict: **✓ checked**, **⚠ flagged** (with the reason) or **couldn't answer**
- "How this answer was made": the exact SQL and every check's result

It covers 6 seasons of VCT (2021–2026): 250 events, 27,394 maps and 15,339 players.

## Why the checks matter

Language models write SQL that runs, looks right, and is sometimes wrong. On my test set, the model alone gave a confident answer to every question the data can't answer ("Who won Champions 2019?", "What was the prize pool of Masters Madrid?"). The checks are the human judgment in the loop:

| Check | Blocks or warns | Catches |
|---|---|---|
| **Safety** | blocks | anything but one read-only `SELECT`; caps results at 1,000 rows |
| **Runs** | blocks (after one fix-it retry) | SQL that errors; the error goes back to the model once |
| **Grounding** | blocks | tables, columns, agents, maps, teams, players or events that don't exist ("Phoenixx", "Champions 2019") |
| **Sanity** | warns | impossible numbers: rates outside 0–100, negative counts, years outside 2021–2026 |
| **Explanation** | warns | numbers in the written answer that aren't in the result table (made-up stats) |
| **Empty** | replaces | no rows: says "No data for that question" instead of guessing |

Vague questions ("best map for Chamber?") get a **"Did you mean…?"** choice between *most picks* and *highest win rate* instead of a silent guess.

## Accuracy

Final numbers are being re-run after the latest fixes. The current report is in [`eval/results/summary.md`](eval/results/summary.md).

41 questions across six types (simple, filter, aggregate, join, tricky wording, impossible), each with a hand-checked correct answer. Full report: [`eval/results/summary.md`](eval/results/summary.md). Run it yourself with `python -m eval.run_eval --checks on`.

**What it still gets wrong:** the checks catch impossible answers well, but not SQL that is believable and measures the wrong thing. For example, the model once averaged per-map percentages and reported Omen at 64.7% instead of 62.2%. That's why every answer shows its SQL, and why the database hands the model ready-made counts instead of percentages.

## How it works

```
question ──► Gemini writes SQL + names it mentions (JSON)
               │
               ▼
        safety ─► grounding ─► runs (one fix-it retry) ─► empty
               │                                             │
            blocked ◄──────────── any failure            rows found
                                                             │
                                                             ▼
                                        Gemini explains the result in 1–3 sentences
                                                             │
                                                             ▼
                                         sanity + explanation checks ─► ✓ or ⚠
```

**Data model:** a DuckDB star schema built from 134 raw CSVs (1.5 GB):

- dimensions: `dim_event` (with an `is_international` flag), `dim_team`, `dim_player`, `dim_agent` (roles), `dim_map`
- facts: `fact_map_result`, `fact_player_map`, `fact_team_comp`
- ready-made metrics: `metric_agent_event_map`, `metric_team_event_map`, `metric_player_event`

The raw data had traps that would silently corrupt answers, all documented in [`docs/data_notes.md`](docs/data_notes.md):

- every player-map row appears three times (full map, attack half, defense half)
- "All Maps" rollup rows sit next to real ones
- percentages are stored as text
- the team-comp file changes format in 2024
- a team named "Stay Small, Stay Second" breaks naive CSV parsing

The model reads [`docs/data_dictionary.md`](docs/data_dictionary.md) before writing SQL.

**Stack:** Python 3.12 · DuckDB · sqlglot · Google Gemini (free tier) · Streamlit · pytest (119 tests, run on every push)

## Run it locally

```bash
git clone https://github.com/elijahvilla/vct-ai-analyst && cd vct-ai-analyst
python -m venv .venv && source .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
echo 'GEMINI_API_KEY = "your-free-key"' > .streamlit/secrets.toml   # free key: aistudio.google.com
streamlit run app/streamlit_app.py
```

The cleaned database (`data/vct.duckdb`, 11.5 MB) is in the repo. To rebuild it from the raw Kaggle files, download them into `data/raw/` and run `python -m etl.build_db`.

## What I learned

- **Clean data beats a smarter model.** Pre-computing the tricky metrics raised the model's own accuracy more than any prompt change did.
- **Checks can be wrong too.** Real model output exposed false alarms in my own checks (a number from the question flagged as made up; event names in a different word order blocked), so I measure the checks as well as the model.
- **A green checkmark isn't proof.** The worst bug was a wrong answer that passed every check. I found it by reviewing output against known answers, not by trusting the badge.

## Credits

Data: [Valorant Champion Tour 2021–2026 Data](https://www.kaggle.com/datasets/ryanluong1/valorant-champion-tour-2021-2023-data) by Ryan Luong (MIT license), originally from [vlr.gg](https://www.vlr.gg). Built by Elijah Villa with AI assistance. I designed the project, made the data and check decisions, and reviewed every result. This is a fan project, not affiliated with Riot Games.
