"""Spot vague questions ("best map for Chamber?") and offer clear versions to pick from."""
import re

VAGUE = re.compile(r"\b(best|top|strongest|greatest|worst|better|good|goat)\b", re.I)
MEASURE = re.compile(
    r"pick|picked|win|won|wins|kill|kills|rating|acs|adr|kast|rate|played|maps|rounds|first|deaths|assists|"
    r"\(by |count|most|highest|lowest|average", re.I)


def clarify_options(question: str) -> list[str] | None:
    """None when the question is clear; otherwise two rewritten questions that each name a measure."""
    q = question.strip()
    if not VAGUE.search(q) or MEASURE.search(VAGUE.sub("", q)):
        return None
    if re.search(r"\bplayers?\b|\bwho\b", q, re.I):
        measures = ["highest average rating", "most kills"]
    else:
        measures = ["most picks", "highest win rate, at least 20 picks"]
    return [f"{q} (by {m})" for m in measures]
