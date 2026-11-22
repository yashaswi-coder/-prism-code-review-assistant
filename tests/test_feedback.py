import json

from prism.feedback import serialize_feedback
from prism.models import AnalysisResult, Evidence, Finding


def make_result():
    finding = Finding(
        id="bandit-0123456789",
        source_tool="bandit",
        category="security",
        severity="high",
        rule_id="B102",
        message="Sensitive finding message should not be exported",
        file_path="private/customer_app.py",
        line_start=8,
        line_end=8,
        evidence=Evidence(
            tool_message="Sensitive tool text",
            snippet="secret_token = 'do-not-export'",
        ),
    )
    return AnalysisResult(
        file_name="customer_app.py",
        line_count=10,
        tool_runs=[],
        findings=[finding],
    ), finding


def test_feedback_export_includes_selected_label_and_minimal_rule_metadata():
    result, finding = make_result()

    exported = json.loads(serialize_feedback(result, {finding.id: "incorrect"}))

    assert exported["schema_version"] == "prism-feedback-v1"
    assert len(exported["records"]) == 1
    assert exported["records"][0] == {
        "finding_id": finding.id,
        "tool": "bandit",
        "rule_id": "B102",
        "severity": "high",
        "category": "security",
        "label": "incorrect",
    }
    serialized = json.dumps(exported)
    for private_value in (
        "Sensitive finding message",
        "Sensitive tool text",
        "secret_token",
        "customer_app.py",
        "private/",
        "line_start",
    ):
        assert private_value not in serialized


def test_feedback_export_omits_unlabeled_and_invalid_labels():
    result, finding = make_result()

    exported = json.loads(
        serialize_feedback(result, {finding.id: "not-a-feedback-label"})
    )

    assert exported["records"] == []
