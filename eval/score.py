"""Score one answer against the hand-checked correct result.

correct  — same rows as the gold result (order ignored, extra answer columns ignored, column names ignored),
           numbers equal after rounding to 1 decimal (a 0-1 fraction may stand in for a 0-100 percent)
refused  — the pipeline blocked it, found no data, or the AI was unavailable
wrong    — an answer was shown (flagged or not) but it doesn't match
For impossible questions (gold is None) refusing IS the correct behavior.
"""
from collections import Counter
from typing import Literal

import pandas as pd

from analyst.pipeline import Answer

Score = Literal["correct", "wrong", "refused"]
SCALES = (1.0, 100.0, 0.01)


def _norm(v, scale: float = 1.0):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    num = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
    if pd.notna(num) and not isinstance(v, str):
        return round(float(num) * scale, 1)
    return str(v).strip().lower()


def _column(series: pd.Series, scale: float = 1.0) -> list:
    return [_norm(v, scale) for v in series.tolist()]


def _rows_match(df: pd.DataFrame, gold: pd.DataFrame) -> bool:
    if len(df) != len(gold):
        return False
    used: set[str] = set()
    mapping: list[tuple[str, float]] = []
    for gcol in gold.columns:
        want = Counter(_column(gold[gcol]))
        found = None
        for acol in df.columns:
            if acol in used:
                continue
            for s in SCALES:
                if Counter(_column(df[acol], s)) == want:
                    found = (acol, s)
                    break
            if found:
                break
        if not found:
            return False
        used.add(found[0])
        mapping.append(found)
    gold_rows = Counter(zip(*[_column(gold[c]) for c in gold.columns]))
    ans_rows = Counter(zip(*[_column(df[c], s) for c, s in mapping]))
    return gold_rows == ans_rows


def score(answer: Answer, gold_df: pd.DataFrame | None) -> Score:
    if answer.status in ("refused", "no_data", "unavailable"):
        return "correct" if gold_df is None and answer.status != "unavailable" else "refused"
    if gold_df is None or answer.df is None:
        return "wrong"
    return "correct" if _rows_match(answer.df, gold_df) else "wrong"
