"""Local Semgrep adapter for Java source using PRism's bundled rules."""

from __future__ import annotations

import json
from pathlib import Path

from prism.adapters.base import AdapterResult, make_id
from prism.evidence import extract_snippet
from prism.models import Evidence, Finding
from prism.runner import ToolOutputError, run_python_callable

JAVA_RULES = Path(__file__).resolve().parents[3] / "rules" / "java.yml"
_SEVERITY = {"ERROR": "high", "WARNING": "medium", "INFO": "info"}


def parse_semgrep_output(raw: str, source_lines: list[str], display_name: str) -> AdapterResult:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ToolOutputError(f"Semgrep did not return valid JSON: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise ToolOutputError("Semgrep JSON output is missing a 'results' list.")

    result = AdapterResult()
    for error in data.get("errors") or []:
        message = error.get("message", "unknown error") if isinstance(error, dict) else str(error)
        result.warnings.append(f"Semgrep reported: {message}")

    for item in data["results"]:
        try:
            check_id = str(item["check_id"])
            extra = item["extra"]
            start = int(item["start"]["line"])
            end = max(start, int(item.get("end", {}).get("line", start)))
            message = str(extra["message"])
            severity_name = str(extra.get("severity", "INFO")).upper()
        except (KeyError, TypeError, ValueError) as exc:
            raise ToolOutputError(f"Unexpected Semgrep finding shape: {exc!r}") from exc

        metadata = extra.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        raw_category = str(metadata.get("category", "security")).lower()
        category = raw_category if raw_category in {"security", "correctness", "bug-risk", "style", "other"} else "security"
        rule_id = check_id.rsplit("/", 1)[-1]
        snippet, snippet_line = extract_snippet(source_lines, start, end)
        references = metadata.get("references") or []
        reference_url = references[0] if references and isinstance(references[0], str) else None
        cwe_value = metadata.get("cwe")
        cwe_text = cwe_value[0] if isinstance(cwe_value, list) and cwe_value else cwe_value
        cwe_digits = "".join(ch for ch in str(cwe_text or "") if ch.isdigit())

        result.findings.append(
            Finding(
                id=make_id("semgrep", rule_id, start, message),
                source_tool="semgrep",
                category=category,
                severity=_SEVERITY.get(severity_name, "info"),
                rule_id=rule_id,
                message=message,
                file_path=display_name,
                line_start=start,
                line_end=end,
                evidence=Evidence(
                    tool_message=message,
                    snippet=snippet,
                    snippet_start_line=snippet_line,
                    reference_url=reference_url,
                    cwe_id=int(cwe_digits) if cwe_digits else None,
                ),
            )
        )
    return result


def run_semgrep_java(
    path: Path, source_lines: list[str], display_name: str, timeout: float
) -> AdapterResult:
    raw = run_python_callable(
        "semgrep.console_scripts.entrypoint",
        "main",
        [
            "scan",
            "--config", str(JAVA_RULES),
            "--json",
            "--quiet",
            "--metrics=off",
            "--disable-version-check",
            "--no-git-ignore",
            path.name,
        ],
        cwd=path.parent,
        timeout=timeout,
    )
    return parse_semgrep_output(raw, source_lines, display_name)
