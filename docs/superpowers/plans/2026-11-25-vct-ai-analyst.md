# VCT AI Analyst Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A public repo + free live app where a question about pro Valorant becomes checked SQL over a VCT 2021–2026 DuckDB database, with an accuracy report proving how often the AI is right.

**Architecture:** An ETL script builds a star-schema DuckDB file from the Kaggle dataset. A pipeline asks an LLM for SQL plus the entities it mentions (JSON), runs six checks (three blocking, two flagging, one "no data"), asks the LLM for a short explanation of the result, and returns an `Answer`. A Streamlit page and an eval runner both call the same pipeline.

**Tech Stack:** Python 3.12, DuckDB, pandas, sqlglot (SQL parsing for checks), google-genai (Gemini free tier), Streamlit, pytest, PyYAML; Tableau Public for the dashboard.

**Spec:** `docs/superpowers/specs/2026-11-25-vct-ai-analyst-design.md`

## Global Constraints

- $0 to run and host: Gemini free tier, Streamlit Community Cloud, Tableau Public.
- No secrets committed: `GEMINI_API_KEY` (and `KAGGLE_USERNAME`/`KAGGLE_KEY` if needed) come from environment variables or `.streamlit/secrets.toml`, which is in `.gitignore`.
- No new scraping of vlr.gg. Data comes only from the Kaggle dataset "Valorant Champion Tour 2021–2026 Data" by Ryan Luong.
- **Owner-written parts** (marked **[OWNER]**): ETL SQL, data dictionary, all six checks, eval questions and gold SQL. The AI may explain and debug these, never write their bodies.
- **AI-written parts** (marked **[AI]**) end with an **explain-back checkpoint**: the owner runs it and explains what it does in his own words before the next task starts.
- Blocking checks: safety, runs (after one retry), grounding. Flag-only: sanity, explanation consistency. Empty result: "no data" message.
- Scoring: correct = same rows as sets (order ignored, extra answer columns ignored), counts exact, other numbers equal after rounding to 1 decimal. Refused = blocked or "no data". Wrong = shown but not matching.
- Only eval-runner results go in the README and on the resume.
- README states the project was built with AI assistance and lists the owner-written parts.
- Cut order if time runs short: Tableau dashboard (Task 11), then live deploy (Task 12, steps 1–4). Checks and the accuracy report are never cut.
- Row limit applied to every query: 1000.

## Review Focus

1. **Name casing and spelling** ("jett", "KAY/O", "kayo", "Fnatic" vs "FNATIC") — grounding must match case-insensitively and ignore "/" and spaces, and an unknown name is blocked with the name in the reason. Test in Task 5.
2. **Free-tier quota or network failure** (HTTP 429, timeout) — the app shows "The free AI quota is used up for now, try again later," never a stack trace. Test in Task 8.
3. **LLM returns non-JSON or markdown-fenced JSON** — fenced JSON is parsed; anything else is refused as "couldn't answer," never executed. Test in Task 7.
4. **Questions outside the data** (a 2019 event, an agent released after the data ends) — refused or "no data," never an invented number. Test in Tasks 5 and 6.
5. **Percentages stored as fractions (0–1) or as 0–100** — sanity and explanation checks accept both scales without false flags. Test in Task 6.

---

## File Structure

```
vct-ai-analyst/
  README.md
  requirements.txt            # pinned deps, also used by Streamlit Cloud
  .python-version             # 3.12
  .gitignore                  # .venv, data/raw, *.duckdb (unless license allows), .streamlit/secrets.toml
  data/download.py            # [AI] Kaggle download into data/raw/
  etl/profile.py              # [AI] prints files, columns, row counts
  etl/sql/01_dims.sql         # [OWNER] dimension tables
  etl/sql/02_facts.sql        # [OWNER] fact tables
  etl/build_db.py             # [AI] runs etl/sql/*.sql in order -> data/vct.duckdb
  etl/export_tableau.py       # [AI] writes aggregated CSVs for Tableau
  docs/data_dictionary.md     # [OWNER] every table/column; also sent to the LLM
  analyst/db.py               # [AI] connect, schema_summary
  analyst/entities.py         # [AI] load known names from dims
  analyst/checks.py           # [OWNER] the six checks
  analyst/llm.py              # [AI] LLM protocol, GeminiLLM, FakeLLM
  analyst/prompt.py           # [AI] prompts + response parsing
  analyst/pipeline.py         # [AI] answer()
  eval/questions.yaml         # [OWNER] 30-50 questions + gold SQL
  eval/score.py               # [AI] score()
  eval/run_eval.py            # [AI] CLI runner, writes results + summary
  eval/results/               # committed results JSONL + summary.md
  app/streamlit_app.py        # [AI] UI
  tests/fixtures/mini.sql     # [AI] tiny DB matching the owner's schema
  tests/test_*.py
```

---

### Task 1: Project setup [AI]

**Files:**
- Create: `.python-version`, `requirements.txt`, `.gitignore`, `README.md` (stub), `tests/test_smoke.py`
- Move in: the existing `docs/superpowers/specs/` and `docs/superpowers/plans/`

**Interfaces:**
- Produces: a `.venv` on Python 3.12 with `duckdb`, `pandas`, `sqlglot`, `google-genai`, `streamlit`, `pytest`, `pyyaml`, `kaggle` installed; `pytest` runs from the repo root.

- [ ] **Step 1:** `git init` in `C:\Users\ual-laptop\Documents\Claude Work\vct-ai-analyst`; branch `main`.
- [ ] **Step 2:** Create a Python 3.12 venv. The machine has Python 3.15, which some wheels (duckdb, streamlit) may not support yet: install 3.12 with `py install 3.12` or `uv python install 3.12`, then `py -3.12 -m venv .venv`. Activate with `source .venv/Scripts/activate` (Git Bash).
- [ ] **Step 3:** Write `requirements.txt` with the packages above pinned to the versions `pip install` resolves; `pip install -r requirements.txt`.
- [ ] **Step 4:** `tests/test_smoke.py`: `def test_imports(): import duckdb, pandas, sqlglot, streamlit, yaml` .
- [ ] **Step 5:** Run `pytest -q`. Expected: `1 passed`.
- [ ] **Step 6:** Commit: `chore: project setup and design docs`.
- [ ] **Step 7: Explain-back.** Owner explains what a venv is, why 3.12, and what each package is for.

### Task 2: Download and profile the data [AI + OWNER]

**Files:**
- Create: `data/download.py`, `etl/profile.py`, `docs/data_notes.md` [OWNER]

**Interfaces:**
- Produces: raw CSVs under `data/raw/`; `docs/data_notes.md` listing each file, its columns, row counts, the year range, and the dataset's license text.

- [ ] **Step 1 [OWNER]:** Create a free Kaggle account, accept the dataset's terms, create an API token, and set `KAGGLE_USERNAME` / `KAGGLE_KEY` as environment variables (never in the repo). Or download the zip by hand into `data/raw/`.
- [ ] **Step 2 [AI]:** `data/download.py`: `def download(dest: str = "data/raw") -> list[str]` using the `kaggle` API, returning the CSV paths. Skips the download if files already exist.
- [ ] **Step 3 [AI]:** `etl/profile.py`: prints, per CSV: path, row count, columns with dtype, 3 sample rows, and distinct-value counts for columns named like agent/map/team/player/event/year.
- [ ] **Step 4:** Run `python etl/profile.py`. Expected: one block per CSV, no errors.
- [ ] **Step 5 [OWNER]:** Write `docs/data_notes.md` from that output, plus the license. **Decision point:** if the license forbids redistribution, keep `*.duckdb` in `.gitignore` and use the startup-download path in Task 12; otherwise the built DB may be committed (compressed if over 100 MB, or rebuilt on startup).
- [ ] **Step 6:** Commit: `data: download script, profiling, data notes` (raw CSVs stay ignored).

### Task 3: Star schema and ETL [OWNER writes SQL; AI writes the runner]

**Files:**
- Create: `etl/sql/01_dims.sql`, `etl/sql/02_facts.sql` [OWNER], `etl/build_db.py` [AI], `docs/data_dictionary.md` [OWNER], `tests/test_db_build.py` [AI]

**Interfaces:**
- Produces: `data/vct.duckdb` with at least these tables and columns (the owner may add columns; renaming any listed one means updating this plan's later tasks and `tests/fixtures/mini.sql`):
  - `dim_event(event_id, event_name, year, stage)`
  - `dim_team(team_id, team_name)`
  - `dim_player(player_id, player_name)`
  - `dim_agent(agent_name, role)` — role in `duelist|initiator|controller|sentinel`
  - `dim_map(map_name)`
  - `fact_map_result(match_map_id, event_id, map_name, team_a_id, team_b_id, winner_team_id, team_a_score, team_b_score)`
  - `fact_player_map(match_map_id, player_id, team_id, agent_name, kills, deaths, assists, acs, adr, kast_pct, first_kills)`
- `etl/build_db.py`: `def build(raw_dir: str = "data/raw", db_path: str = "data/vct.duckdb") -> None` — registers each raw CSV as a DuckDB view named after the file stem (`read_csv_auto`), then runs `etl/sql/*.sql` in filename order.

- [ ] **Step 1 [AI]: Write the failing tests** in `tests/test_db_build.py` (skipped if `data/vct.duckdb` doesn't exist):
  - `test_all_tables_exist` — the seven tables above exist.
  - `test_facts_not_empty` — `fact_player_map` and `fact_map_result` have > 0 rows.
  - `test_agent_roles_valid` — every `dim_agent.role` is one of the four roles; no NULLs.
  - `test_dim_keys_unique` — `event_id`, `team_id`, `player_id`, `agent_name`, `map_name` unique in their dims.
  - `test_facts_join_dims` — zero `fact_player_map` rows whose `agent_name` or `player_id` has no dim row.
  - `test_kast_range` — `kast_pct` between 0 and 100, or between 0 and 1 (record which in the data dictionary).
- [ ] **Step 2:** Run `pytest tests/test_db_build.py -v`. Expected: SKIPPED (no DB yet).
- [ ] **Step 3 [AI]:** Implement `build()` as specified.
- [ ] **Step 4 [OWNER]:** Write `01_dims.sql` and `02_facts.sql` (`CREATE OR REPLACE TABLE ... AS SELECT ...` from the raw views). Agent roles come from a hand-written `VALUES` list in `01_dims.sql`.
- [ ] **Step 5:** `python etl/build_db.py && pytest tests/test_db_build.py -v`. Expected: 6 passed.
- [ ] **Step 6 [OWNER]:** Write `docs/data_dictionary.md`: one section per table, one line per column (meaning, type, units, example). Note the KAST scale and the year range.
- [ ] **Step 7:** Commit: `etl: star schema, build script, data dictionary`.

### Task 4: DB access and known entities [AI]

**Files:**
- Create: `analyst/db.py`, `analyst/entities.py`, `tests/fixtures/mini.sql`, `tests/conftest.py`, `tests/test_entities.py`

**Interfaces:**
- Consumes: the Task 3 table/column names.
- Produces:
  - `analyst.db.connect(path: str = "data/vct.duckdb", read_only: bool = True) -> duckdb.DuckDBPyConnection`
  - `analyst.db.schema_summary(con) -> dict[str, list[str]]` (table -> column names, main schema only)
  - `analyst.entities.Entities` dataclass: `agents, maps, teams, players, events: set[str]` holding **normalized** names
  - `analyst.entities.normalize(name: str) -> str` — lowercase, strip, remove spaces, "/", "-", "."
  - `analyst.entities.load_entities(con) -> Entities`
  - pytest fixture `mini_con` (in-memory DuckDB from `tests/fixtures/mini.sql`: 2 events incl. one "Champions 2024", 3 teams, 4 players, agents Jett/KAY/O/Sova/Omen with roles, maps Ascent/Bind, ~10 player-map rows)

- [ ] **Step 1: Failing tests:** `test_normalize_kayo` (`normalize("KAY/O") == normalize("kayo") == "kayo"`), `test_load_entities` (`"jett" in ents.agents`, `"ascent" in ents.maps`, `len(ents.teams) == 3`), `test_schema_summary` (`"fact_player_map" in summary` and `"agent_name" in summary["fact_player_map"]`).
- [ ] **Step 2:** `pytest tests/test_entities.py -v` → FAIL (module missing).
- [ ] **Step 3:** Implement as specified.
- [ ] **Step 4:** `pytest tests/test_entities.py -v` → 3 passed.
- [ ] **Step 5:** Commit: `feat: db access and entity loading`.
- [ ] **Step 6: Explain-back.**

### Task 5: Blocking checks — safety, runs, grounding [OWNER]

**Files:**
- Create: `analyst/checks.py` (first half), `tests/test_checks_blocking.py` [tests written by AI from this plan, code by OWNER]

**Interfaces:**
- Consumes: `Entities`, `normalize`, `schema_summary` (Task 4).
- Produces:
  - `CheckResult` dataclass: `name: str, passed: bool, blocking: bool, reason: str`
  - `ROW_LIMIT = 1000`
  - `check_safety(sql: str) -> tuple[CheckResult, str]` — returns the result and the SQL with `LIMIT 1000` applied when it has no limit or a larger one. Use `sqlglot.parse(sql, read="duckdb")`.
  - `check_runs(con, sql: str) -> tuple[CheckResult, pandas.DataFrame | None]`
  - `check_grounding(sql: str, mentioned: dict[str, list[str]], schema: dict[str, list[str]], ents: Entities) -> CheckResult` — `mentioned` keys: `agents, maps, teams, players, events`.

- [ ] **Step 1: Failing tests:**
  - `test_safety_allows_select` — passes; returned SQL contains `LIMIT 1000`.
  - `test_safety_keeps_smaller_limit` — `SELECT ... LIMIT 5` keeps `LIMIT 5`.
  - `test_safety_blocks_writes` — `DROP TABLE dim_agent`, `DELETE FROM ...`, `UPDATE ...`, `CREATE TABLE ...` each → `passed=False, blocking=True`.
  - `test_safety_blocks_multiple_statements` — `SELECT 1; DROP TABLE dim_map` → blocked.
  - `test_safety_blocks_unparseable` — `"here is your query!"` → blocked.
  - `test_runs_ok` / `test_runs_error` — valid SQL on `mini_con` returns a DataFrame; `SELECT * FROM nope` → blocked with the DuckDB error text in `reason`.
  - `test_grounding_unknown_table` / `test_grounding_unknown_column` — blocked, the bad name in `reason`.
  - `test_grounding_case_insensitive` — `mentioned={"agents": ["jett", "Kay/O"]}` passes. *(Review Focus 1)*
  - `test_grounding_unknown_agent` — `mentioned={"agents": ["Phoenixx"]}` → blocked, reason contains `Phoenixx`.
  - `test_grounding_unknown_event` — `mentioned={"events": ["Champions 2019"]}` → blocked. *(Review Focus 4)*
- [ ] **Step 2:** `pytest tests/test_checks_blocking.py -v` → FAIL.
- [ ] **Step 3 [OWNER]:** Implement the three checks.
- [ ] **Step 4:** `pytest tests/test_checks_blocking.py -v` → all pass.
- [ ] **Step 5:** Commit: `feat: blocking checks (safety, runs, grounding)`.

### Task 6: Flag checks — sanity, explanation, empty [OWNER]

**Files:**
- Modify: `analyst/checks.py`
- Create: `tests/test_checks_flags.py`

**Interfaces:**
- Produces:
  - `check_sanity(df, year_range: tuple[int, int]) -> CheckResult` — `blocking=False`. Columns whose name contains `rate|pct|percent|ratio` must be in [0, 1] or [0, 100]; columns named like `count|kills|deaths|assists|picks|matches|maps|rounds` must be ≥ 0; a `year` column must be within `year_range`.
  - `check_explanation(explanation: str, df) -> CheckResult` — `blocking=False`. Every number in the explanation (regex, ignoring years already in `year_range` and ordinal words) must equal some value in `df` after rounding to 1 decimal, or equal a 0–1 value × 100 (or a 0–100 value ÷ 100).
  - `check_empty(df) -> CheckResult` — `passed=False, blocking=False, name="empty"` when `df` has 0 rows.

- [ ] **Step 1: Failing tests:**
  - `test_sanity_rate_fraction_ok` (`win_rate` 0.62) and `test_sanity_rate_percent_ok` (`win_rate` 62.0) both pass. *(Review Focus 5)*
  - `test_sanity_rate_out_of_range` — `pick_rate` 140 → flagged.
  - `test_sanity_negative_count` — `kills` -3 → flagged.
  - `test_sanity_year_outside` — `year` 2019 with `year_range=(2021, 2026)` → flagged. *(Review Focus 4)*
  - `test_explanation_matches` — "Jett had a 62.5% pick rate" vs `df` with 0.625 → pass.
  - `test_explanation_hallucinated_number` — "Jett won 71 maps" vs `df` with 64 → flagged, reason contains `71`.
  - `test_explanation_no_numbers` — text with no numbers → pass.
  - `test_empty` — empty DataFrame → `passed=False, name="empty"`.
- [ ] **Step 2:** run → FAIL. **Step 3 [OWNER]:** implement. **Step 4:** run → all pass.
- [ ] **Step 5:** Commit: `feat: flag checks (sanity, explanation, empty)`.

### Task 7: LLM wrapper and prompts [AI]

**Files:**
- Create: `analyst/llm.py`, `analyst/prompt.py`, `tests/test_prompt.py`

**Interfaces:**
- Produces:
  - `class LLM(Protocol): def complete(self, prompt: str) -> str`
  - `class LLMUnavailable(Exception)` — raised on quota (429), auth or network errors
  - `class GeminiLLM` — `__init__(self, api_key: str | None = None, model: str | None = None)`; key from `GEMINI_API_KEY`, model from `GEMINI_MODEL` (default: the current free-tier Flash model listed in Google AI Studio at build time; record it in the README)
  - `class FakeLLM` — `__init__(self, responses: list[str | Exception])`, returns/raises them in order
  - `SqlDraft` dataclass: `sql: str, mentioned: dict[str, list[str]]`
  - `build_sql_prompt(question: str, data_dictionary: str) -> str` — asks for JSON `{"sql": "...", "mentioned": {"agents": [], "maps": [], "teams": [], "players": [], "events": []}}`, DuckDB dialect, SELECT only
  - `parse_sql_response(text: str) -> SqlDraft | None` — accepts raw JSON or JSON in a ``` fence; returns `None` otherwise
  - `build_explain_prompt(question: str, result_markdown: str) -> str` — 1–3 sentences, only numbers present in the table
  - `build_fix_prompt(question: str, sql: str, error: str, data_dictionary: str) -> str`

- [ ] **Step 1: Failing tests:** `test_parse_raw_json`, `test_parse_fenced_json` (```json ... ```), `test_parse_garbage_returns_none` ("Sure! Here's a query:"), `test_parse_missing_sql_returns_none`, `test_sql_prompt_contains_dictionary_and_question`. *(Review Focus 3)*
- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** run → pass.
- [ ] **Step 5:** Manual: `python -c "from analyst.llm import GeminiLLM; print(GeminiLLM().complete('Say hi'))"` with a real free key → prints a greeting.
- [ ] **Step 6:** Commit: `feat: LLM wrapper and prompts`. **Step 7: Explain-back.**

### Task 8: Pipeline and logging [AI]

**Files:**
- Create: `analyst/pipeline.py`, `tests/test_pipeline.py`

**Interfaces:**
- Consumes: Tasks 4–7.
- Produces:
  - `Answer` dataclass: `question: str, sql: str | None, df: DataFrame | None, explanation: str | None, checks: list[CheckResult], status: Literal["ok", "flagged", "refused", "no_data", "unavailable"], message: str`
  - `answer(question: str, con, llm: LLM, ents: Entities, schema: dict[str, list[str]], dictionary: str, year_range: tuple[int, int], checks_enabled: bool = True) -> Answer`
    - Order: SQL prompt → parse (None → refused) → safety → grounding → runs (on error, one fix-prompt retry, then refused) → empty (→ no_data) → explain prompt → sanity + explanation → `flagged` if any flag failed else `ok`.
    - `checks_enabled=False`: skip every check except "runs"; no retry; status `ok` whenever SQL runs (the "before checks" baseline).
    - `LLMUnavailable` at any point → `status="unavailable"`, `message="The free AI quota is used up for now, try again later."`
  - `answer_to_record(a: Answer) -> dict` — JSON-safe (df as list of rows, max 50).

- [ ] **Step 1: Failing tests** (all with `FakeLLM` + `mini_con`):
  - `test_ok_path` — good JSON + good explanation → `status="ok"`, 6 checks recorded.
  - `test_garbage_response_refused` — `"lol no"` → `refused`, SQL never executed.
  - `test_drop_table_refused` — `{"sql": "DROP TABLE dim_agent"}` → `refused`; `dim_agent` still exists.
  - `test_retry_fixes_error` — first SQL errors, fix prompt returns valid SQL → `ok`, 3 LLM calls made.
  - `test_retry_fails_refused` — both SQLs error → `refused`.
  - `test_unknown_agent_refused` — `mentioned.agents=["Phoenixx"]` → `refused`.
  - `test_empty_no_data` — valid SQL with no rows → `no_data`, explanation never requested.
  - `test_hallucinated_number_flagged` — explanation with a wrong number → `flagged`.
  - `test_quota_unavailable` — `FakeLLM([LLMUnavailable("429")])` → `unavailable` with the exact message above. *(Review Focus 2)*
  - `test_checks_disabled_baseline` — unknown-agent SQL that runs → `ok` when `checks_enabled=False`.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement. **Step 4:** run → all pass.
- [ ] **Step 5:** Commit: `feat: answer pipeline`. **Step 6: Explain-back** (owner walks through one question end to end).

### Task 9: Eval set, scorer and runner [OWNER writes questions; AI writes scorer and runner]

**Files:**
- Create: `eval/questions.yaml` [OWNER], `eval/score.py`, `eval/run_eval.py`, `tests/test_score.py` [AI]

**Interfaces:**
- `eval/questions.yaml`: list of `{id: str, category: simple|filter|aggregate|join|tricky|impossible, question: str, gold_sql: str | null}` — `gold_sql: null` means the correct behavior is refused / no data.
- `eval.score.score(answer: Answer, gold_df: DataFrame | None) -> Literal["correct", "wrong", "refused"]` — rules from Global Constraints; for `gold_sql: null`, a refused/no_data answer scores `correct`.
- `python -m eval.run_eval --checks on|off [--limit N]` → writes `eval/results/{on|off}-YYYY-MM-DD.jsonl` (one `answer_to_record` + score per question) and `eval/results/summary.md` (counts per score and category, flag precision, wrong-but-unflagged count, before/after table). Sleeps between calls to respect free-tier rate limits.

- [ ] **Step 1 [AI]: Failing tests:** `test_score_ignores_row_order`, `test_score_ignores_extra_columns`, `test_score_rounds_to_one_decimal` (62.54 vs 62.5 → correct), `test_score_counts_exact` (64 vs 65 → wrong), `test_score_refused`, `test_score_impossible_question_refused_is_correct`.
- [ ] **Step 2:** run → FAIL. **Step 3:** implement scorer and runner. **Step 4:** run → pass.
- [ ] **Step 5 [OWNER]:** Write 30–50 questions across all six categories, at least 5 `impossible`, each `gold_sql` checked by running it in DuckDB.
- [ ] **Step 6:** `python -m eval.run_eval --checks off` then `--checks on`. Expected: both JSONL files and `summary.md` written.
- [ ] **Step 7:** Commit: `eval: test set, scorer, runner, first results`.

### Task 10: Streamlit app [AI]

**Files:**
- Create: `app/streamlit_app.py`, `app/view.py`, `tests/test_view.py`

**Interfaces:**
- `app/view.py`: `badge(a: Answer) -> tuple[str, str]` → (`"✓ checked"`, `"success"`), (`"⚠ flagged: <first failed flag reason>"`, `"warning"`), (`"Couldn't answer: <reason>"`, `"error"`), (`"No data for that question."`, `"info"`), (`a.message`, `"error"`) for ok/flagged/refused/no_data/unavailable.
- Page: title, one-line description, text input, 4 example questions as buttons, result table, explanation, badge, expandable "How this answer was made" (SQL + each check's verdict), footer linking the repo, the accuracy summary and the Tableau dashboard. Connection and entities cached with `st.cache_resource`.

- [ ] **Step 1:** Failing tests for `badge` (one per status). **Step 2:** run → FAIL. **Step 3:** implement `view.py` and the page. **Step 4:** run → pass.
- [ ] **Step 5:** `streamlit run app/streamlit_app.py`; ask the 4 examples and one nonsense question. Expected: badges render, nonsense is refused, nothing crashes.
- [ ] **Step 6:** Commit: `feat: Streamlit app`. **Step 7: Explain-back.**

### Task 11: Tableau dashboard [AI export; OWNER builds dashboard] — first to cut

**Files:**
- Create: `etl/export_tableau.py`

**Interfaces:**
- `export(db_path: str = "data/vct.duckdb", out_dir: str = "data/tableau") -> list[str]` — aggregated CSVs only: `agent_by_map_year.csv` (agent, role, map, year, picks, pick_rate, win_rate), `agent_by_event.csv`, `team_map_pool.csv` (team, map, maps_played, win_rate).

- [ ] **Step 1:** Implement and run; check each CSV opens and has no row-level player-match data.
- [ ] **Step 2 [OWNER]:** Build and publish to Tableau Public: agent meta by map over seasons, meta shift by event, team map pools.
- [ ] **Step 3:** Commit export script; add the public dashboard link to README.

### Task 12: Deploy, README, demo, resume [AI + OWNER]

**Files:**
- Create/Modify: `README.md`, `.streamlit/config.toml`, deploy notes in README

- [ ] **Step 1 [OWNER]:** Create the public GitHub repo `vct-ai-analyst` and push.
- [ ] **Step 2 [AI]:** Startup data path per the Task 2 decision: committed DB, or download + build on first run (Kaggle secrets) cached on disk.
- [ ] **Step 3 [OWNER]:** Deploy on Streamlit Community Cloud with Python 3.12; add `GEMINI_API_KEY` (and Kaggle keys if needed) in the app's Secrets.
- [ ] **Step 4:** Smoke test the live URL with the 4 example questions. Expected: answers with badges; when quota is out, the friendly message.
- [ ] **Step 5 [OWNER, AI drafts]:** README: what it does (2 lines), demo GIF/video, live link, accuracy before/after table from `summary.md`, 2–3 caught mistakes, architecture diagram (text), stack, how to run locally, data source + license, "built with AI assistance; I wrote the schema, checks and test set," what I learned.
- [ ] **Step 6 [OWNER]:** Record a 60–90 second demo video (one good answer, one caught mistake, the accuracy table).
- [ ] **Step 7:** Commit and push: `docs: README, demo, results`.
- [ ] **Step 8:** In career-ops, run `add` mode to add the project to `cv.md` with bullets using only measured results.
