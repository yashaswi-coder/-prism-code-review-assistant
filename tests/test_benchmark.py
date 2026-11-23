"""Unit tests for benchmark case loading and per-language score reporting."""

import json
from types import SimpleNamespace

from scripts import evaluate_benchmark


def test_benchmark_accepts_java_cases_and_reports_scores_by_language(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    benchmark_root = repo / "benchmarks"
    cases_root = benchmark_root / "cases"
    (cases_root / "java").mkdir(parents=True)
    (cases_root / "java" / "clean.java").write_text("class Clean {}\n", encoding="utf-8")
    (cases_root / "python_case.py").write_text("x = 1\n", encoding="utf-8")
    manifest_path = benchmark_root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "dataset_version": "test",
                "matching": "exact",
                "cases": [
                    {
                        "id": "clean-java",
                        "file": "cases/java/clean.java",
                        "expected_findings": [{"tool": "semgrep", "rule_id": "java.demo"}],
                    },
                    {
                        "id": "python-case",
                        "file": "cases/python_case.py",
                        "expected_findings": [{"tool": "ruff", "rule_id": "F401"}],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(evaluate_benchmark, "ROOT", repo)

    def fake_analyze(source, file_name):
        tool = "semgrep" if file_name.endswith(".java") else "ruff"
        rule_id = "java.demo" if tool == "semgrep" else "F401"
        return SimpleNamespace(
            tool_runs=[SimpleNamespace(status="ok", tool=tool, tool_version="test-version")],
            findings=[SimpleNamespace(source_tool=tool, rule_id=rule_id)],
        )

    monkeypatch.setattr(evaluate_benchmark, "analyze_source", fake_analyze)

    report = evaluate_benchmark.run_benchmark(manifest_path)

    assert report["case_count"] == 2
    assert report["score_by_language"]["java"]["true_positives"] == 1
    assert report["score_by_language"]["python"]["true_positives"] == 1
    assert [case["language"] for case in report["cases"]] == ["java", "python"]
