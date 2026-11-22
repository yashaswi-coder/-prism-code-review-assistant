"""Small helpers for exact-label static-analysis benchmark scoring."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

FindingKey = tuple[str, ...]
CaseFinding = tuple[str, str, str]


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


def score_by_tool(
    expected: Iterable[CaseFinding],
    predicted: Iterable[CaseFinding],
) -> dict[str, dict[str, int | float | None]]:
    expected_rows = list(expected)
    predicted_rows = list(predicted)
    tools = sorted({row[1] for row in expected_rows + predicted_rows})
    return {
        tool: score_findings(
            ((case_id, rule_id) for case_id, source_tool, rule_id in expected_rows if source_tool == tool),
            ((case_id, rule_id) for case_id, source_tool, rule_id in predicted_rows if source_tool == tool),
        )
        for tool in tools
    }


def score_by_rule(
    expected: Iterable[CaseFinding],
    predicted: Iterable[CaseFinding],
) -> dict[str, dict[str, int | float | None]]:
    expected_rows = list(expected)
    predicted_rows = list(predicted)
    labels = sorted({(row[1], row[2]) for row in expected_rows + predicted_rows})
    return {
        f"{tool}:{rule_id}": score_findings(
            (case_id for case_id, source_tool, source_rule in expected_rows
             if source_tool == tool and source_rule == rule_id),
            (case_id for case_id, source_tool, source_rule in predicted_rows
             if source_tool == tool and source_rule == rule_id),
        )
        for tool, rule_id in labels
    }
