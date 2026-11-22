"""Common data schema. Every tool's output is converted into these models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator

SCHEMA_VERSION = "0.1"

Severity = Literal["high", "medium", "low", "info"]
SourceTool = Literal["ruff", "bandit", "semgrep"]
Category = Literal["security", "correctness", "bug-risk", "style", "other"]
ToolStatus = Literal["ok", "partial", "error", "missing", "timeout"]

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


class Evidence(BaseModel):
    """Why a finding exists: what the tool said and the code it points at."""

    tool_message: str
    snippet: Optional[str] = None
    snippet_start_line: Optional[int] = None
    reference_url: Optional[str] = None
    cwe_id: Optional[int] = None


class Finding(BaseModel):
    id: str
    # Milestone 5 will add "ai" findings. Today everything is deterministic.
    origin: Literal["deterministic"] = "deterministic"
    source_tool: SourceTool
    category: Category
    severity: Severity
    rule_id: str
    message: str
    file_path: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    evidence: Evidence
    # Only set when the tool itself reports one (Bandit does, Ruff does not).
    confidence: Optional[Literal["high", "medium", "low"]] = None
    suggested_fix: Optional[str] = None

    @model_validator(mode="after")
    def _check_lines(self) -> "Finding":
        if self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class ToolRun(BaseModel):
    """Outcome of one tool invocation. Failures are recorded, never hidden."""

    tool: SourceTool
    status: ToolStatus
    detail: Optional[str] = None
    tool_version: Optional[str] = None
    duration_s: float = 0.0
    finding_count: int = 0


class AnalysisResult(BaseModel):
    schema_version: str = SCHEMA_VERSION
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    file_name: str
    line_count: int
    tool_runs: list[ToolRun]
    findings: list[Finding]

    @property
    def all_tools_ok(self) -> bool:
        return all(r.status == "ok" for r in self.tool_runs)
