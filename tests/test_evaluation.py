from prism.evaluation import score_by_rule, score_by_tool, score_findings


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


def test_grouped_scores_keep_case_identity_for_tool_and_rule_breakdowns():
    expected = [("case-a", "ruff", "F401"), ("case-b", "bandit", "B102")]
    predicted = [
        ("case-a", "ruff", "F401"),
        ("case-b", "bandit", "B602"),
        ("case-c", "bandit", "B404"),
    ]

    by_tool = score_by_tool(expected, predicted)
    assert by_tool["ruff"]["precision"] == 1.0
    assert by_tool["bandit"]["true_positives"] == 0
    assert by_tool["bandit"]["false_positives"] == 2
    assert by_tool["bandit"]["false_negatives"] == 1

    by_rule = score_by_rule(expected, predicted)
    assert by_rule["ruff:F401"]["true_positives"] == 1
    assert by_rule["bandit:B404"]["precision"] == 0.0
    assert by_rule["bandit:B404"]["recall"] is None
