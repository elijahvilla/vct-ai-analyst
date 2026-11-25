from eval.run_eval import summarize


def rec(score, category="simple", status="ok", flagged=False):
    return {"score": score, "category": category, "status": "flagged" if flagged else status}


def test_summarize_counts_and_flag_stats():
    on = [rec("correct"), rec("wrong", flagged=True), rec("wrong"), rec("refused", "impossible", "refused"),
          rec("correct", "join")]
    s = summarize(on)
    assert s["total"] == 5
    assert s["correct"] == 2 and s["wrong"] == 2 and s["refused"] == 1
    assert s["accuracy_pct"] == 40.0
    assert s["flagged"] == 1 and s["flagged_and_wrong"] == 1
    assert s["wrong_unflagged"] == 1
    assert s["by_category"]["simple"] == {"correct": 1, "wrong": 2, "refused": 0}
