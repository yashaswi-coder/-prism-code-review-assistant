from prism.evaluation import score_findings


def test_score_findings_calculates_precision_recall_and_f1():
    score = score_findings(
        expected=[("ruff", "F401"), ("bandit", "B102")],
        predicted=[("ruff", "F401"), ("bandit", "B602")],
    )

    assert score == {
        "true_positives": 1,
        "false_positives": 1,
        "false_negatives": 1,
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }


def test_score_findings_preserves_duplicate_counts_and_empty_dataset():
    score = score_findings(
        expected=[("ruff", "F401"), ("ruff", "F401")],
        predicted=[("ruff", "F401")],
    )
    assert (score["true_positives"], score["false_negatives"]) == (1, 1)

    empty = score_findings([], [])
    assert (empty["precision"], empty["recall"], empty["f1"]) == (None, None, None)
