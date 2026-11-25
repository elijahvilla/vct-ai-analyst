# VCT AI Analyst — Design

**Date:** 2026-11-25
**Owner / builder:** Elijah Villa (MIS, University of Arizona, May 2027), building with AI assistance
**Status:** draft for approval (builder check done; owner answers folded in 2026-11-25)

## 1. Intent and why

A portfolio project, published as a public GitHub repo with a live demo, that the owner builds himself and can explain line by line in interviews.

It exists to give real, demonstrable evidence for gaps that came up across his 2027 new-grad applications:

- **Building with AI / LLMs** — Red Ventures' AI APM role asks for "multiple examples of using ML, generative AI, or other modern technologies to build working solutions."
- **Human judgment over AI output** — Protiviti asks for someone who "effectively leverages AI tools with strong human judgment in the loop."
- **SQL / Python / BI depth** for data and BI analyst roles and rotational tech programs.

It is about **pro Valorant (VCT)**, because the owner is a big Valorant fan. Domain knowledge is central to the design: he must be able to tell when an AI answer about Valorant is wrong.

## 2. What it is

An "AI analyst" for professional Valorant:

1. A user types a question in plain English (e.g. "Which agents had the highest win rate on Ascent at Champions 2024?").
2. An LLM translates it into SQL against a VCT database.
3. The app runs the SQL and shows the result table plus a short plain-English explanation.
4. A **check layer** validates every answer before showing it, and flags anything suspicious.
5. Every question, the generated SQL, the checks' verdicts and the final answer are logged, so the owner can show an "accuracy report": how often the AI was right, and what kinds of mistakes it made.

Plus a **Tableau Public dashboard** of agent and map trends across VCT seasons, built from the same cleaned data and linked from the README.

## 3. Goals, non-goals, anti-goals

**Goals**
- Works end to end on real VCT data (2021 onward) and can answer a broad set of everyday questions about agents, maps, teams, players and events.
- The check layer catches the common LLM failure modes (see §6) and the owner can explain each check.
- A measured accuracy report on a fixed test set of questions with known correct answers (see §7).
- Costs $0 to run and host.
- A README a recruiter can understand in 60 seconds: what it does, a demo video/GIF, the accuracy numbers, the stack, and what the owner learned.
- Resume-ready: produces 2–3 honest, quantified bullets (e.g. "N-question test set, X% correct after checks").

**Non-goals**
- Not a betting or prediction tool. Predicting match outcomes is out of scope (a stretch idea only, see §10).
- Not real-time / live match data.
- Not a general chatbot about Valorant lore, patch notes or anything outside the database.
- Not a multi-user product with accounts.

**Anti-goals (failure even if it "works")**
- Code the owner cannot explain. Every component must be something he understands and can walk through.
- Showing AI answers as fact without validation, or hiding the AI's mistakes. The mistakes and how they are caught are the story.
- Inflated claims in the README or on the resume (accuracy numbers must come from the logged test set).
- Violating the dataset's license or vlr.gg's terms (no new scraping of vlr.gg by this project).

## 4. Constraints

- **$0 budget:** free hosting and a free LLM tier.
- **Time:** about 3–4 weekends, part time, during senior year and an internship.
- **Skills:** strong in SQL, Python (pandas, scikit-learn), Tableau, Power BI; has not built a web app or called an LLM API before.
- **Data:** public dataset only (§5). Check its license on Kaggle before publishing a derived database or dashboard.
- **Free LLM tier limits:** rate limits and daily quotas; the app must degrade gracefully and the demo video is the fallback.
- **No secrets in the repo:** the API key lives in environment variables / Streamlit secrets, never committed.

## 5. Data

**Source:** Kaggle dataset "Valorant Champion Tour 2021–2026 Data" by Ryan Luong, scraped from vlr.gg (a public analysis reports its main stats file at about 1.1 million rows, 23 columns).

**First task before anything else:** download it, list its files and columns, and confirm its license allows reuse in a public repo.

- **License allows sharing:** commit the cleaned DuckDB file (or a compressed export) so the app and a clean clone work without a Kaggle account.
- **License forbids sharing (builder's call):** the repo ships a download + ETL script; the live app downloads the dataset from Kaggle on startup using a Kaggle API key stored in Streamlit secrets and caches the built DuckDB file; the Tableau dashboard publishes only aggregated tables (rates, counts), not row-level data. Setup docs say a free Kaggle account is required.

**Target model (adjusted to whatever the files actually contain):** a small star schema in DuckDB, built by a Python cleaning script:
- Facts: player-map stats (kills, deaths, assists, ACS, ADR, KAST, first kills, agent), map results (map, winner, score, side rounds), agent picks.
- Dimensions: events/tournaments (name, year, stage), teams, players, agents (with role: duelist / initiator / controller / sentinel), maps.
- A written **data dictionary** (markdown) for every table and column; it doubles as the context the LLM reads.

## 6. The check layer (the core of the project)

Each generated query passes these checks, in order, before an answer is shown. Each check has a name, a pass/fail verdict and a reason, and all of it is logged.

1. **Safety:** only `SELECT` statements; no writes, no DDL; one statement; a row limit is applied.
2. **Runs:** the SQL executes without error. On error, the app retries once, sending the error message back to the LLM; a second failure is shown as "couldn't answer," never guessed.
3. **Grounding:** every table and column exists in the schema; every agent, map, team, player or event named in the question exists in the dimension tables (catches made-up names and misspellings, e.g. an agent that doesn't exist).
4. **Sanity rules:** results stay within known bounds (rates between 0 and 100%, no negative counts, pick counts not above matches played, years within the dataset's range).
5. **Explanation consistency:** every number in the LLM's written explanation must appear in (or be computable from) the result table; numbers that don't match are flagged as a possible hallucination.
6. **Empty-result honesty:** zero rows produces "no data for that," not an invented answer.

**Block vs flag (builder's call):** checks 1 (safety), 2 (runs, after the one retry) and 3 (grounding: unknown tables, columns or named entities) **block**: the user sees "couldn't answer" with the reason, never a result. Checks 4 (sanity) and 5 (explanation consistency) **flag**: the answer is shown with a ⚠ badge and the reason. Check 6 replaces the answer with an honest "no data" message.

The UI shows a small verdict badge ("checked ✓" / "flagged ⚠ — reason") and the generated SQL in an expandable panel, so the user sees how the answer was produced.

## 7. Evaluation (accuracy report)

- A fixed **test set of 30–50 questions** written by the owner across difficulty levels (simple counts, filters, aggregations, multi-table joins, tricky wording, and a few deliberately impossible or trick questions).
- For each one, the owner writes the correct SQL by hand (his own SQL skills are the ground truth).
- A script runs the whole set through the pipeline and reports: correct / wrong / refused, which checks fired, and the error types.
- **Scoring (builder's call):** an answer is **correct** when its result set matches the owner's hand-written SQL result: same rows as sets (row order ignored), extra columns ignored, numbers equal after rounding to 1 decimal (percentages) or exactly (counts). **Refused** = blocked by a check or "no data." **Wrong** = shown (flagged or not) but not matching. Flagged answers are scored by their content; the report also shows how often a ⚠ flag landed on a wrong answer (flag precision) and how many wrong answers slipped through unflagged.
- "Before vs after the check layer" = the same test set run with checks off (raw LLM SQL) and on.
- Only eval-runner results count for the README and resume; live-app logs are throwaway (Streamlit Community Cloud storage resets on restart).
- Results are published in the README with honest numbers, before and after the check layer, plus 2–3 examples of mistakes the checks caught.

## 8. Approaches considered

| Approach | Trade-off | Decision |
|---|---|---|
| **A. AI analyst (text-to-SQL) with a check layer + dashboard** | Most work (3–4 weekends), but the only option that closes the AI-building gap and tells a "human judgment over AI" story | **Chosen by the owner** |
| B. Esports market study (prize money, viewership, sponsors) with dashboard + deck | Strong for consulting-style roles, but no real AI building | Not chosen; a business-trends page may be added to the dashboard |
| C. Data pipeline with automated quality checks | Good data-engineering / controls signal, little AI | Not chosen; its quality-check idea lives inside approach A's check layer |

Game choice: **Valorant** (owner's passion; he can judge answers) over League of Legends (better data via Oracle's Elixir, but he is new to the game). Rainbow Six had no usable public pro data.

Presentation: **live free app plus a GitHub README with a demo video**, chosen by the owner as "the free version."

## 9. How — decisions

Owner decided: approach A; Valorant; free to run; live demo plus README.

**Who writes what (owner decided: mixed):**
- **The owner writes by hand** the parts interviews will probe: the DuckDB schema and ETL SQL, the data dictionary, every check in §6 (with AI help for debugging only), and the eval test set with its hand-written correct SQL.
- **The AI assistant writes** the plumbing: project setup, the LLM wrapper, the Streamlit UI, logging, the eval runner scaffolding, and deployment config. The owner runs each piece and must be able to explain it back before the next step (explain-back checkpoint per task).
- The README states honestly that the project was built with AI assistance and which parts the owner wrote.

**Timeline and cuts (owner agreed):** target about 4 weekends, finished before interview season (aim: early January 2027; no hard external deadline stated). If time runs short, cut in this order: (1) the Tableau dashboard, (2) the live app (keep the demo video). The checks and the accuracy report are never cut. **Minimum shippable version:** ETL + DuckDB + text-to-SQL with all six checks + eval report + README with demo video.

Builder's calls (correctable):
- **Language:** Python.
- **Database:** DuckDB (single file, fast on millions of rows, standard SQL, no server).
- **LLM:** Google Gemini API free tier, called through a thin wrapper so the model can be swapped later (e.g. to Claude) without touching the rest.
- **App:** Streamlit, hosted on Streamlit Community Cloud (free; connects to the public GitHub repo; secrets stored there).
- **Dashboard:** Tableau Public, fed from a CSV export of the cleaned tables.
- **Repo layout:** `data/` (download script, not raw data if the license says so), `etl/` (cleaning + load), `analyst/` (prompting, checks, logging), `app/` (Streamlit), `eval/` (test set + runner), `docs/` (data dictionary, design). Short README at the root.
- **Quality:** unit tests for each check in §6; the eval runner is the integration test.
- **Logging:** the eval runner writes a persistent log (question, SQL, verdicts, answer, score) committed as a results file. The live app keeps only a throwaway in-memory/session log, anonymous, with no personal data.

## 10. Left to the builder / later

- Exact schema, once the real files are inspected.
- Prompt wording and how much schema/context to send the LLM.
- Visual design of the Streamlit page (keep it simple and readable).
- Which dashboard views (suggested: agent pick and win rate by map over seasons; meta shifts by patch or event; team map pools).
- Stretch ideas, only after the core is done: a simple match-outcome model with scikit-learn; a "compare two teams" page; swapping in a stronger LLM to compare accuracy.

## 11. Definition of done

- Public GitHub repo with README, demo GIF/video, accuracy report, data dictionary, and setup steps that work from a clean clone.
- Live Streamlit app that answers questions with check badges (or degrades gracefully when the free quota is out).
- Tableau Public dashboard linked from the README.
- Eval script and test set in the repo; numbers in the README match its output.
- The owner can explain every part: the schema, the prompt, each check, and the eval.
- After it's done, the project is added to `cv.md` through career-ops' `add` mode, with bullets that use only the measured results.
