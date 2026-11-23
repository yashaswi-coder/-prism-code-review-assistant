"""Run PRism on the small, manually labeled synthetic benchmark."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from prism.analyzer import analyze_source  # noqa: E402
from prism.evaluation import score_by_rule, score_by_tool, score_findings  # noqa: E402


def load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest.get("cases"), list) or not manifest["cases"]:
        raise ValueError("Benchmark manifest must contain a non-empty cases list.")
    return manifest


def run_benchmark(manifest_path: Path) -> dict:
    manifest = load_manifest(manifest_path)
    benchmark_root = manifest_path.parent.resolve()
    case_results = []
    all_expected = []
    all_predicted = []
    versions: dict[str, str] = {}
    by_language: dict[str, dict[str, list[tuple[str, str, str]]]] = {}

    for case in manifest["cases"]:
        relative = Path(case["file"])
        source_path = (benchmark_root / relative).resolve()
        suffix = source_path.suffix.lower()
        if benchmark_root not in source_path.parents or suffix not in {".py", ".java"}:
            raise ValueError(f"Unsafe or unsupported benchmark path: {relative}")
        language = {".py": "python", ".java": "java"}[suffix]
        source = source_path.read_text(encoding="utf-8")
        result = analyze_source(source, f"{case['id']}{suffix}")
        failed_runs = [run for run in result.tool_runs if run.status != "ok"]
        if failed_runs:
            failures = ", ".join(f"{run.tool}: {run.status} ({run.detail})" for run in failed_runs)
            raise RuntimeError(f"Analysis failed for case {case['id']}: {failures}")
        for run in result.tool_runs:
            if run.tool_version:
                versions[run.tool] = run.tool_version

        expected = [(item["tool"], item["rule_id"]) for item in case["expected_findings"]]
        predicted = [(item.source_tool, item.rule_id) for item in result.findings]
        all_expected.extend((case["id"], *key) for key in expected)
        all_predicted.extend((case["id"], *key) for key in predicted)
        language_rows = by_language.setdefault(language, {"expected": [], "predicted": []})
        language_rows["expected"].extend((case["id"], *key) for key in expected)
        language_rows["predicted"].extend((case["id"], *key) for key in predicted)
        case_score = score_findings(expected, predicted)
        expected_counts = Counter(expected)
        predicted_counts = Counter(predicted)
        case_results.append(
            {
                "id": case["id"],
                "language": language,
                "expected_findings": [
                    {"tool": tool, "rule_id": rule_id} for tool, rule_id in expected
                ],
                "predicted_findings": [
                    {"tool": tool, "rule_id": rule_id} for tool, rule_id in predicted
                ],
                "score": case_score,
                "unexpected": [
                    {"tool": tool, "rule_id": rule_id, "count": count}
                    for (tool, rule_id), count in (predicted_counts - expected_counts).items()
                ],
                "missed": [
                    {"tool": tool, "rule_id": rule_id, "count": count}
                    for (tool, rule_id), count in (expected_counts - predicted_counts).items()
                ],
            }
        )

    total_score = score_findings(all_expected, all_predicted)
    return {
        "benchmark_version": manifest["dataset_version"],
        "evaluated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "matching": manifest["matching"],
        "python_version": platform.python_version(),
        "tool_versions": versions,
        "case_count": len(case_results),
        "score": total_score,
        "score_by_tool": score_by_tool(all_expected, all_predicted),
        "score_by_rule": score_by_rule(all_expected, all_predicted),
        "score_by_language": {
            language: score_findings(rows["expected"], rows["predicted"])
            for language, rows in sorted(by_language.items())
        },
        "cases": case_results,
        "interpretation": (
            "Development baseline on synthetic cases; not a real-world quality estimate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "benchmarks" / "manifest.json",
        help="Path to the labeled benchmark manifest.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for saving the JSON results; defaults to stdout.",
    )
    args = parser.parse_args()
    try:
        report = run_benchmark(args.manifest.resolve())
    except (OSError, ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"Benchmark could not complete: {exc}", file=sys.stderr)
        return 1

    output = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Wrote benchmark results to {args.output}")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
