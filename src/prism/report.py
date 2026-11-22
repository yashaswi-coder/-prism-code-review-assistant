"""Markdown and JSON report generation."""

from __future__ import annotations

import re

from prism.models import SEVERITY_ORDER, AnalysisResult

LIMITATIONS = (
    "PRism uses Ruff and Bandit for Python and a small local Semgrep rule set for Java. "
    "Java coverage is an early prototype. Static analysis produces false "
    "positives and misses real problems; an empty report is not evidence that the "
    "code is correct or secure. Severity labels for Ruff rules are PRism's own "
    "heuristic. Every finding needs human review. This is a work-in-progress tool "
    "and has not been benchmarked."
)


def to_json(result: AnalysisResult) -> str:
    return result.model_dump_json(indent=2)


def _fence(text: str) -> str:
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def to_markdown(result: AnalysisResult) -> str:
    out = [
        f"# PRism report: {result.file_name}",
        "",
        "> Work in progress. Findings require human review.",
        "",
        f"- Generated: {result.generated_at.isoformat(timespec='seconds')}",
        f"- Lines analyzed: {result.line_count}",
        f"- Findings: {len(result.findings)}",
        f"- Schema version: {result.schema_version}",
        "",
        "## Tool status",
        "",
        "| Tool | Version | Status | Findings | Detail |",
        "|---|---|---|---|---|",
    ]
    for r in result.tool_runs:
        detail = (r.detail or "").replace("|", "\\|").replace("\n", " ")
        out.append(f"| {r.tool} | {r.tool_version or '?'} | {r.status} | {r.finding_count} | {detail} |")
    if not result.all_tools_ok:
        out += ["", "**Warning:** at least one tool did not finish cleanly; results may be incomplete."]

    out += ["", "## Findings (deterministic)", ""]
    if not result.findings:
        out.append("_No findings reported by the tools that ran._")
    for f in sorted(result.findings, key=lambda x: (SEVERITY_ORDER[x.severity], x.line_start)):
        loc = f"{f.file_path}:{f.line_start}" + (f"-{f.line_end}" if f.line_end != f.line_start else "")
        conf = f", confidence {f.confidence}" if f.confidence else ""
        out += [f"### [{f.severity.upper()}] {f.rule_id} ({f.source_tool}, {f.category}{conf})", "",
                f"{f.message}", "", f"- Location: `{loc}`"]
        if f.evidence.reference_url:
            out.append(f"- Reference: {f.evidence.reference_url}")
        if f.evidence.cwe_id:
            out.append(f"- CWE: {f.evidence.cwe_id}")
        if f.suggested_fix:
            out.append(f"- Tool-suggested fix: {f.suggested_fix}")
        if f.evidence.snippet:
            fence = _fence(f.evidence.snippet)
            language = "java" if f.file_path.lower().endswith(".java") else "python"
            out += ["", f"{fence}{language}", f.evidence.snippet, fence]
        out.append("")
    out += ["## Limitations", "", LIMITATIONS, ""]
    return "\n".join(out)
