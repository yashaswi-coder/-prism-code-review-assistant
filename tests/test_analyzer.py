"""Orchestration tests. Some run the real tools (installed via the dev extras)."""

import subprocess
from pathlib import Path

import pytest

from prism import runner
from prism.adapters.base import AdapterResult
from prism.analyzer import analyze_source
from prism.inputs import InputError
from prism.report import to_json, to_markdown

SAMPLE = Path(__file__).parent.parent / "samples" / "vulnerable_sample.py"


def test_empty_input_rejected_before_tools_run():
    with pytest.raises(InputError):
        analyze_source("   ")


def test_real_tools_on_synthetic_sample():
    r = analyze_source(SAMPLE.read_text(), "vulnerable_sample.py")
    assert [t.status for t in r.tool_runs] == ["ok", "ok"]
    rules = {f.rule_id for f in r.findings}
    assert {"F401", "B602", "B324", "B307", "B105"} <= rules


def test_clean_code_has_no_findings():
    r = analyze_source('"""Clean."""\n\n\ndef add(a, b):\n    return a + b\n')
    assert r.findings == [] and r.all_tools_ok


def test_syntax_error_is_reported_not_hidden():
    r = analyze_source("def broken(:\n    pass\n")
    assert any(f.rule_id == "syntax-error" for f in r.findings)
    bandit = next(t for t in r.tool_runs if t.tool == "bandit")
    assert bandit.status == "partial" and "syntax error" in bandit.detail


def test_submitted_code_is_never_executed(tmp_path):
    marker = tmp_path / "executed.txt"
    code = f"open({str(marker)!r}, 'w').write('x')\n"
    analyze_source(code)
    assert not marker.exists()


def test_missing_tool_is_recorded(monkeypatch):
    monkeypatch.setattr(runner.importlib.util, "find_spec", lambda name: None)
    r = analyze_source("x = 1\n")
    assert [t.status for t in r.tool_runs] == ["missing", "missing"]
    assert not r.all_tools_ok


def test_timeout_is_recorded(monkeypatch):
    def boom(*a, **k):
        raise subprocess.TimeoutExpired(cmd="x", timeout=1)

    monkeypatch.setattr(runner.subprocess, "run", boom)
    r = analyze_source("x = 1\n")
    assert [t.status for t in r.tool_runs] == ["timeout", "timeout"]


def test_unexpected_exit_status_is_recorded(monkeypatch):
    fake = subprocess.CompletedProcess(args=[], returncode=2, stdout="", stderr="boom")
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: fake)
    r = analyze_source("x = 1\n")
    assert all(t.status == "error" and "boom" in t.detail for t in r.tool_runs)


def test_garbage_tool_output_is_recorded(monkeypatch):
    fake = subprocess.CompletedProcess(args=[], returncode=0, stdout="<<garbage>>", stderr="")
    monkeypatch.setattr(runner.subprocess, "run", lambda *a, **k: fake)
    r = analyze_source("x = 1\n")
    assert all(t.status == "error" and "valid JSON" in t.detail for t in r.tool_runs)


def test_one_failing_tool_does_not_hide_the_other():
    def good(path, lines, name, timeout):
        return AdapterResult()

    def bad(path, lines, name, timeout):
        raise runner.ToolExecutionError("nope")

    r = analyze_source("x = 1\n", adapters={"ruff": good, "bandit": bad})
    assert [t.status for t in r.tool_runs] == ["ok", "error"]


def test_subprocess_uses_argv_list_without_shell(monkeypatch):
    seen = {}

    def spy(cmd, **kwargs):
        seen["cmd"], seen["kwargs"] = cmd, kwargs
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="[]", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", spy)
    runner.run_module("ruff", ["check"], cwd=Path("."), timeout=5)
    assert isinstance(seen["cmd"], list) and "-I" in seen["cmd"]
    assert seen["kwargs"]["shell"] is False and seen["kwargs"]["timeout"] == 5


def test_reports_render_and_json_roundtrips():
    r = analyze_source(SAMPLE.read_text(), "vulnerable_sample.py")
    md, js = to_markdown(r), to_json(r)
    assert "B602" in md and "Limitations" in md and "Work in progress" in md
    from prism.models import AnalysisResult

    assert AnalysisResult.model_validate_json(js).findings == r.findings


def test_markdown_fence_grows_when_snippet_contains_backticks():
    r = analyze_source("import os; x = '```'\n")  # F401 on a line containing ```
    md = to_markdown(r)
    assert "````python" in md  # 4-backtick fence so the snippet cannot close it early
