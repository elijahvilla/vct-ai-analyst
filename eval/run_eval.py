"""Run every question in eval/questions.yaml through the pipeline and score it.

Usage:  python -m eval.run_eval --checks on      (or off for the no-checks baseline)
        python -m eval.run_eval --checks on --limit 5
Writes eval/results/<on|off>.jsonl and rewrites eval/results/summary.md from whichever runs exist.
"""
import argparse
import json
import os
import time
from collections import defaultdict
from datetime import date

import duckdb
import yaml

from analyst.db import connect, schema_summary
from analyst.entities import load_entities
from analyst.llm import GeminiLLM, LLMUnavailable
from analyst.pipeline import answer, answer_to_record
from eval.score import score

YEARS = (2021, 2026)
RESULTS = "eval/results"


def summarize(records: list[dict]) -> dict:
    by_cat: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "wrong": 0, "refused": 0})
    for r in records:
        by_cat[r["category"]][r["score"]] += 1
    total = len(records)
    count = lambda s: sum(r["score"] == s for r in records)  # noqa: E731
    flagged = [r for r in records if r["status"] == "flagged"]
    return {
        "total": total,
        "correct": count("correct"), "wrong": count("wrong"), "refused": count("refused"),
        "accuracy_pct": round(100 * count("correct") / total, 1) if total else 0.0,
        "flagged": len(flagged),
        "flagged_and_wrong": sum(r["score"] == "wrong" for r in flagged),
        "wrong_unflagged": sum(r["score"] == "wrong" and r["status"] != "flagged" for r in records),
        "by_category": dict(by_cat),
    }


def _gold(con: duckdb.DuckDBPyConnection, sql: str | None):
    return None if not sql else con.execute(sql).fetchdf()


def run(checks: bool, limit: int | None, pause: float) -> list[dict]:
    con = connect()
    schema, ents = schema_summary(con), load_entities(con)
    dictionary = open("docs/data_dictionary.md", encoding="utf-8").read()
    questions = yaml.safe_load(open("eval/questions.yaml", encoding="utf-8"))[: limit or None]
    llm = GeminiLLM()
    out = []
    for i, q in enumerate(questions, 1):
        for attempt in range(3):  # free-tier hiccups: retry instead of scoring them
            a = answer(q["question"], con, llm, ents, schema, dictionary, YEARS, checks_enabled=checks)
            if a.status != "unavailable":
                break
            time.sleep(30 * (attempt + 1))
        rec = answer_to_record(a) | {"id": q["id"], "category": q["category"],
                                     "score": score(a, _gold(con, q.get("gold_sql")))}
        out.append(rec)
        print(f"[{i}/{len(questions)}] {q['id']}: {rec['score']} ({rec['status']})", flush=True)
        time.sleep(pause)
    return out


def write_summary() -> None:
    rows = []
    for mode in ("off", "on"):
        path = f"{RESULTS}/{mode}.jsonl"
        if os.path.exists(path):
            recs = [json.loads(l) for l in open(path, encoding="utf-8")]
            rows.append((mode, summarize(recs)))
    lines = [f"# Accuracy report ({date.today()})", "",
             "| Run | Questions | Correct | Wrong | Refused | Accuracy | Flagged (⚠) | Flagged & wrong | Wrong, not flagged |",
             "|---|---|---|---|---|---|---|---|---|"]
    for mode, s in rows:
        label = "AI alone (checks off)" if mode == "off" else "With checks"
        lines.append(f"| {label} | {s['total']} | {s['correct']} | {s['wrong']} | {s['refused']} | {s['accuracy_pct']}% "
                     f"| {s['flagged']} | {s['flagged_and_wrong']} | {s['wrong_unflagged']} |")
    for mode, s in rows:
        lines += ["", f"## By category ({'checks off' if mode == 'off' else 'checks on'})", "",
                  "| Category | Correct | Wrong | Refused |", "|---|---|---|---|"]
        lines += [f"| {c} | {v['correct']} | {v['wrong']} | {v['refused']} |" for c, v in sorted(s["by_category"].items())]
    with open(f"{RESULTS}/summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checks", choices=["on", "off"], default="on")
    p.add_argument("--limit", type=int)
    p.add_argument("--pause", type=float, default=4.0, help="seconds between questions (free-tier rate limits)")
    args = p.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    recs = run(args.checks == "on", args.limit, args.pause)
    with open(f"{RESULTS}/{args.checks}.jsonl", "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, default=str) + "\n")
    write_summary()
    print(open(f"{RESULTS}/summary.md", encoding="utf-8").read())


if __name__ == "__main__":
    main()
