"""Validation and changed-line extraction for single-file unified diffs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from prism.inputs import MAX_BYTES, InputError, sanitize_file_name

_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass(frozen=True)
class DiffSpec:
    """The Python file and added/changed new-file lines described by a diff."""

    file_path: str
    changed_lines: frozenset[int]


def decode_diff_upload(data: bytes, upload_name: str) -> DiffSpec:
    """Decode and validate a UTF-8 .diff/.patch file, returning its changed lines."""
    suffix = PurePosixPath(upload_name.replace("\\", "/")).suffix.lower()
    if suffix not in {".diff", ".patch"}:
        raise InputError("Upload a unified diff file with a .diff or .patch extension.")
    if len(data) > MAX_BYTES:
        raise InputError(f"Diff is larger than the {MAX_BYTES:,}-byte limit.")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Diff is not valid UTF-8 text.") from exc
    return parse_unified_diff(text)


def parse_unified_diff(text: str) -> DiffSpec:
    """Parse one Python file's unified diff and collect added-line numbers.

    This first version intentionally supports a single file. It filters analyzer
    results after analyzing the separately uploaded, complete current file.
    """
    if not text or not text.strip():
        raise InputError("Diff is empty.")
    if "\x00" in text:
        raise InputError("Diff contains NUL bytes and is not valid text.")
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise InputError(f"Diff is larger than the {MAX_BYTES:,}-byte limit.")

    lines = text.splitlines()
    file_headers = [line[4:].split("\t", 1)[0] for line in lines if line.startswith("+++ ")]
    if len(file_headers) != 1:
        raise InputError("Provide a unified diff for exactly one file.")
    new_path = file_headers[0]
    if new_path == "/dev/null":
        raise InputError("Deleted files are not supported; upload a diff for an existing Python file.")
    if new_path.startswith("b/"):
        new_path = new_path[2:]
    normalized = PurePosixPath(new_path.replace("\\", "/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise InputError("Diff contains an unsafe file path.")
    file_path = sanitize_file_name(normalized.name)

    changed: set[int] = set()
    hunk_count = 0
    index = 0
    while index < len(lines):
        match = _HUNK.match(lines[index])
        if not match:
            index += 1
            continue
        hunk_count += 1
        old_remaining = int(match.group(2) or 1)
        new_remaining = int(match.group(4) or 1)
        new_line = int(match.group(3))
        index += 1
        while index < len(lines) and (old_remaining or new_remaining):
            line = lines[index]
            if line.startswith("\\ No newline at end of file"):
                index += 1
                continue
            if not line:
                raise InputError("Diff has a malformed hunk line.")
            marker = line[0]
            if marker == " ":
                old_remaining -= 1
                new_remaining -= 1
                new_line += 1
            elif marker == "+":
                changed.add(new_line)
                new_remaining -= 1
                new_line += 1
            elif marker == "-":
                old_remaining -= 1
            else:
                raise InputError("Diff has a malformed hunk line.")
            if old_remaining < 0 or new_remaining < 0:
                raise InputError("Diff hunk line counts do not match its header.")
            index += 1
        if old_remaining or new_remaining:
            raise InputError("Diff hunk is incomplete or its line counts are invalid.")

    if hunk_count == 0:
        raise InputError("No unified diff hunks were found.")
    if not changed:
        raise InputError("Diff contains no added or changed lines to review.")
    return DiffSpec(file_path=file_path, changed_lines=frozenset(changed))
