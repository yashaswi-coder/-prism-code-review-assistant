from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from prism.models import Finding


@dataclass
class AdapterResult:
    findings: list[Finding] = field(default_factory=list)
    # Non-fatal problems the tool reported (e.g. "could not parse file").
    warnings: list[str] = field(default_factory=list)


def make_id(tool: str, rule_id: str, line: int, message: str) -> str:
    """Stable short id so the same finding gets the same id across runs."""
    digest = hashlib.sha1(f"{tool}|{rule_id}|{line}|{message}".encode()).hexdigest()
    return f"{tool}-{digest[:10]}"
