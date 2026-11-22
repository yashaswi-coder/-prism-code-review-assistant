"""Small helpers for exact-label static-analysis benchmark scoring."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

FindingKey = tuple[str, ...]


def score_findings(
    expected: Iterable[FindingKey],
    predicted: Iterable[FindingKey],
) -> dict[str, int | float | None]:
    """Micro-score (tool, rule ID) labels, preserving duplicate occurrences."""
    expected_counts = Counter(expected)
    predicted_counts = Counter(predicted)
    true_positives = sum((expected_counts & predicted_counts).values())
    false_positives = sum(predicted_counts.values()) - true_positives
    false_negatives = sum(expected_counts.values()) - true_positives
    predicted_total = true_positives + false_positives
    expected_total = true_positives + false_negatives
    precision = true_positives / predicted_total if predicted_total else None
    recall = true_positives / expected_total if expected_total else None
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall
        else (0.0 if precision is not None and recall is not None else None)
    )
    return {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
