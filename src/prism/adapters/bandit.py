"""Bandit adapter (common Python security patterns)."""

from __future__ import annotations

import json
from pathlib import Path

from prism.adapters.base import AdapterResult, make_id
from prism.evidence import extract_snippet
from prism.models import Evidence, Finding
from prism.runner import ToolOutputError, run_module

_LEVEL = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low"}


def parse_bandit_output(raw: str, source_lines: list[str], display_name: str) -> AdapterResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolOutputError(f"Bandit did not return valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ToolOutputError("Bandit JSON output is missing a 'results' list.")

    result = AdapterResult()
    for err in data.get("errors") or []:
        reason = err.get("reason", "unknown error") if isinstance(err, dict) else str(err)
        result.warnings.append(f"Bandit reported: {reason}")

    for item in data["results"]:
        try:
            line_start = int(item["line_number"])
            line_range = item.get("line_range") or [line_start]
            line_end = max(line_start, max(int(n) for n in line_range))
            message = str(item["issue_text"])
            rule_id = str(item["test_id"])
            severity = _LEVEL.get(str(item["issue_severity"]).upper(), "info")
        except (KeyError, TypeError, ValueError) as exc:
            raise ToolOutputError(f"Unexpected Bandit finding shape: {exc!r}") from exc

        confidence = _LEVEL.get(str(item.get("issue_confidence", "")).upper())
        cwe = item.get("issue_cwe")
        cwe_id = cwe.get("id") if isinstance(cwe, dict) and isinstance(cwe.get("id"), int) else None
        snippet, snippet_line = extract_snippet(source_lines, line_start, line_end)
        result.findings.append(
            Finding(
                id=make_id("bandit", rule_id, line_start, message),
                source_tool="bandit",
                category="security",
                severity=severity,
                rule_id=rule_id,
                message=message,
                file_path=display_name,
                line_start=line_start,
                line_end=line_end,
                evidence=Evidence(
                    tool_message=message,
                    snippet=snippet,
                    snippet_start_line=snippet_line,
                    reference_url=item.get("more_info"),
                    cwe_id=cwe_id,
                ),
                confidence=confidence,
            )
        )
    return result


def run_bandit(path: Path, source_lines: list[str], display_name: str, timeout: float) -> AdapterResult:
    # Exit 0 = no issues, 1 = issues found. Anything else is a tool failure.
    raw = run_module(
        "bandit",
        ["-f", "json", "-q", path.name],
        cwd=path.parent,
        timeout=timeout,
        ok_exit_codes=(0, 1),
    )
    return parse_bandit_output(raw, source_lines, display_name)
