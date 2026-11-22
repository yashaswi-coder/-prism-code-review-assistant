"""Privacy-conscious export of explicit finding feedback labels."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from prism.models import AnalysisResult

FeedbackLabel = Literal["useful", "incorrect", "not_useful"]
FEEDBACK_LABELS = frozenset({"useful", "incorrect", "not_useful"})


def serialize_feedback(
    result: AnalysisResult,
    labels_by_finding_id: dict[str, str],
) -> str:
    """Return an explicit, minimal JSON export; nothing is saved automatically.

    The export intentionally omits source code, snippets, finding messages,
    file paths, and line numbers so it can be used as a label seed without
    copying submitted code or local paths into the dataset.
    """
    records = []
    for finding in result.findings:
        label = labels_by_finding_id.get(finding.id)
        if label not in FEEDBACK_LABELS:
            continue
        records.append(
            {
                "finding_id": finding.id,
                "tool": finding.source_tool,
                "rule_id": finding.rule_id,
                "severity": finding.severity,
                "category": finding.category,
                "label": label,
            }
        )
    return json.dumps(
        {
            "schema_version": "prism-feedback-v1",
            "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "records": records,
        },
        indent=2,
    )
