"""Ruff adapter (lint/style/bug-risk). Security rules (S) are left to Bandit."""

from __future__ import annotations

import json
from pathlib import Path

from prism.adapters.base import AdapterResult, make_id
from prism.evidence import extract_snippet
from prism.models import Evidence, Finding
from prism.runner import ToolOutputError, run_module

# Deliberately excludes "S" (flake8-bandit) to avoid duplicating Bandit.
RULE_SELECTION = "E,F,W,B"

# Ruff has no severity field we can rely on. This mapping is PRism's own
# heuristic, not Ruff's judgment. Documented in docs/architecture.md.
_CATEGORY = {"F": "correctness", "B": "bug-risk", "E": "style", "W": "style"}
_SEVERITY = {"F": "medium", "B": "medium", "E": "low", "W": "low"}


def parse_ruff_output(raw: str, source_lines: list[str], display_name: str) -> AdapterResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolOutputError(f"Ruff did not return valid JSON: {exc}") from exc
    if not isinstance(data, list):
        raise ToolOutputError("Ruff JSON output was not a list.")

    result = AdapterResult()
    for item in data:
        try:
            line_start = int(item["location"]["row"])
            line_end = max(line_start, int(item["end_location"]["row"]))
            message = str(item["message"])
            code = item.get("code")  # syntax errors: None (older Ruff) or "invalid-syntax"
        except (KeyError, TypeError, ValueError) as exc:
            raise ToolOutputError(f"Unexpected Ruff finding shape: {exc!r}") from exc

        if code is None or code == "invalid-syntax":
            rule_id, category, severity = "syntax-error", "correctness", "high"
        else:
            rule_id = str(code)
            category = _CATEGORY.get(rule_id[:1], "other")
            severity = _SEVERITY.get(rule_id[:1], "low")

        fix = item.get("fix")
        suggested = fix.get("message") if isinstance(fix, dict) else None
        snippet, snippet_line = extract_snippet(source_lines, line_start, line_end)
        result.findings.append(
            Finding(
                id=make_id("ruff", rule_id, line_start, message),
                source_tool="ruff",
                category=category,
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
                    reference_url=item.get("url"),
                ),
                suggested_fix=suggested,
            )
        )
    return result


def run_ruff(path: Path, source_lines: list[str], display_name: str, timeout: float) -> AdapterResult:
    # Exit 0 = clean, 1 = findings, 2 = ruff itself failed.
    raw = run_module(
        "ruff",
        ["check", "--output-format", "json", "--no-cache", "--isolated",
         "--select", RULE_SELECTION, path.name],
        cwd=path.parent,
        timeout=timeout,
        ok_exit_codes=(0, 1),
    )
    return parse_ruff_output(raw, source_lines, display_name)
