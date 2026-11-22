"""Input validation. Nothing here executes or imports submitted code."""

from __future__ import annotations

import re

MAX_BYTES = 200_000  # ~200 KB per submission
ALLOWED_SUFFIXES = (".py", ".java")
DEFAULT_NAME = "pasted_code.py"


class InputError(ValueError):
    """The submission was rejected before any tool ran."""


def sanitize_file_name(name: str | None) -> str:
    """Keep only a short, printable basename for display in reports."""
    if not name:
        return DEFAULT_NAME
    base = re.split(r"[\\/]", name)[-1]
    base = re.sub(r"[^\w.\- ]", "_", base)[:100].strip()
    if not base.lower().endswith(ALLOWED_SUFFIXES):
        raise InputError(f"Unsupported file type: only {', '.join(ALLOWED_SUFFIXES)} files are accepted.")
    return base


def validate_source(source: str) -> str:
    if not source or not source.strip():
        raise InputError("Input is empty.")
    if "\x00" in source:
        raise InputError("Input contains NUL bytes; it does not look like source text.")
    if len(source.encode("utf-8")) > MAX_BYTES:
        raise InputError(f"Input is larger than the {MAX_BYTES:,}-byte limit.")
    return source


def decode_upload(data: bytes, file_name: str) -> tuple[str, str]:
    """Validate an uploaded file; return (source_text, display_name)."""
    name = sanitize_file_name(file_name)
    if len(data) > MAX_BYTES:
        raise InputError(f"File is larger than the {MAX_BYTES:,}-byte limit.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("File is not valid UTF-8 text.") from exc
    return validate_source(text), name
