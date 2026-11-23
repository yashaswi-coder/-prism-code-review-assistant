"""Integration checks for PRism's early, synthetic Java rule set."""

from pathlib import Path

from prism.analyzer import analyze_source

ROOT = Path(__file__).parent.parent


def test_vulnerable_java_sample_reports_expected_security_rules():
    source = (ROOT / "samples" / "vulnerable_sample.java").read_text(encoding="utf-8")
    result = analyze_source(source, "vulnerable_sample.java")

    assert result.all_tools_ok
    rule_ids = {finding.rule_id for finding in result.findings}
    assert any(rule_id.endswith("java.hardcoded-credential") for rule_id in rule_ids)
    assert any(rule_id.endswith("java.weak-message-digest") for rule_id in rule_ids)
    assert any(rule_id.endswith("java.runtime-exec") for rule_id in rule_ids)
    assert any(rule_id.endswith("java.sql-string-concatenation") for rule_id in rule_ids)


def test_clean_java_sample_has_no_findings():
    source = (ROOT / "samples" / "clean_sample.java").read_text(encoding="utf-8")
    result = analyze_source(source, "clean_sample.java")

    assert result.all_tools_ok
    assert result.findings == []
