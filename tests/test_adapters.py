"""Parsing/normalization tests. Fixtures are real tool output (see tests/fixtures/README.md)."""

from pathlib import Path

import pytest

from prism.adapters.bandit import parse_bandit_output
from prism.adapters.ruff import parse_ruff_output
from prism.runner import ToolOutputError

FIX = Path(__file__).parent / "fixtures"
SAMPLE_LINES = (Path(__file__).parent.parent / "samples" / "vulnerable_sample.py").read_text().splitlines()


def _read(name):
    return (FIX / name).read_text()


def test_ruff_normalization():
    res = parse_ruff_output(_read("ruff_sample.json"), SAMPLE_LINES, "s.py")
    assert [(f.rule_id, f.line_start) for f in res.findings] == [("F401", 2)]
    f = res.findings[0]
    assert (f.source_tool, f.category, f.severity) == ("ruff", "correctness", "medium")
    assert f.confidence is None  # Ruff reports no confidence
    assert f.evidence.snippet == "import os"
    assert "Remove unused import" in f.suggested_fix


def test_ruff_syntax_error_is_high_severity_correctness():
    lines = ["def broken(:", "    pass"]
    res = parse_ruff_output(_read("ruff_syntax_error.json"), lines, "s.py")
    assert res.findings and all(f.rule_id == "syntax-error" for f in res.findings)
    assert all(f.severity == "high" and f.category == "correctness" for f in res.findings)


def test_ruff_empty_list_is_no_findings():
    assert parse_ruff_output("[]", [], "s.py").findings == []


@pytest.mark.parametrize("raw", ["", "not json", "{}", '[{"message": "x"}]'])
def test_ruff_invalid_output_raises(raw):
    with pytest.raises(ToolOutputError):
        parse_ruff_output(raw, [], "s.py")


def test_bandit_normalization():
    res = parse_bandit_output(_read("bandit_sample.json"), SAMPLE_LINES, "s.py")
    by_rule = {f.rule_id: f for f in res.findings}
    assert set(by_rule) == {"B404", "B602", "B324", "B307", "B105"}
    shell = by_rule["B602"]
    assert (shell.severity, shell.confidence, shell.category) == ("high", "high", "security")
    assert shell.evidence.cwe_id == 78
    assert "shell=True" in shell.evidence.snippet
    assert by_rule["B105"].confidence == "medium"


def test_bandit_parse_error_becomes_warning_not_silence():
    res = parse_bandit_output(_read("bandit_syntax_error.json"), [], "s.py")
    assert res.findings == []
    assert any("syntax error" in w for w in res.warnings)


@pytest.mark.parametrize("raw", ["", "nope", "[]", '{"results": "x"}'])
def test_bandit_invalid_output_raises(raw):
    with pytest.raises(ToolOutputError):
        parse_bandit_output(raw, [], "s.py")
