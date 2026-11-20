"""Orchestrates validation -> temp file -> tools -> normalized result.

The submitted code is written to a temporary file that static-analysis tools
read. It is never imported, compiled, or executed by PRism. The temp directory
is removed when analysis finishes. Source text is not logged or persisted.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Callable

from prism.adapters.base import AdapterResult
from prism.adapters.bandit import run_bandit
from prism.adapters.ruff import run_ruff
from prism.inputs import sanitize_file_name, validate_source
from prism.models import SEVERITY_ORDER, AnalysisResult, ToolRun
from prism.runner import (
    ToolError,
    ToolMissingError,
    ToolTimeoutError,
    tool_version,
)

Adapter = Callable[[Path, list[str], str, float], AdapterResult]

DEFAULT_TIMEOUTS = {"ruff": 30.0, "bandit": 60.0}
ADAPTERS: dict[str, Adapter] = {"ruff": run_ruff, "bandit": run_bandit}


def analyze_source(
    source: str,
    file_name: str | None = None,
    *,
    adapters: dict[str, Adapter] | None = None,
    timeouts: dict[str, float] | None = None,
) -> AnalysisResult:
    """Analyze Python source text. Raises InputError for rejected input."""
    display_name = sanitize_file_name(file_name)
    validate_source(source)
    source_lines = source.splitlines()
    adapters = adapters or ADAPTERS
    timeouts = {**DEFAULT_TIMEOUTS, **(timeouts or {})}

    findings = []
    runs: list[ToolRun] = []
    with tempfile.TemporaryDirectory(prefix="prism_") as tmp:
        target = Path(tmp) / "target.py"
        target.write_text(source, encoding="utf-8")
        for tool, run in adapters.items():
            started = time.monotonic()
            version = tool_version(tool)
            try:
                res = run(target, source_lines, display_name, timeouts.get(tool, 30.0))
            except ToolMissingError as exc:
                runs.append(_failed(tool, "missing", exc, started, version))
            except ToolTimeoutError as exc:
                runs.append(_failed(tool, "timeout", exc, started, version))
            except ToolError as exc:
                runs.append(_failed(tool, "error", exc, started, version))
            else:
                findings.extend(res.findings)
                runs.append(
                    ToolRun(
                        tool=tool,  # type: ignore[arg-type]
                        status="partial" if res.warnings else "ok",
                        detail="; ".join(res.warnings) or None,
                        tool_version=version,
                        duration_s=round(time.monotonic() - started, 3),
                        finding_count=len(res.findings),
                    )
                )

    findings.sort(key=lambda f: (f.line_start, SEVERITY_ORDER[f.severity], f.rule_id))
    return AnalysisResult(
        file_name=display_name,
        line_count=len(source_lines),
        tool_runs=runs,
        findings=findings,
    )


def _failed(tool: str, status: str, exc: Exception, started: float, version: str | None) -> ToolRun:
    return ToolRun(
        tool=tool,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        detail=str(exc),
        tool_version=version,
        duration_s=round(time.monotonic() - started, 3),
    )
