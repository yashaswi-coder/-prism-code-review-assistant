"""Build evidence snippets from the submitted text (not from tool output)."""

from __future__ import annotations

MAX_SNIPPET_LINES = 10


def extract_snippet(
    source_lines: list[str], line_start: int, line_end: int
) -> tuple[str | None, int | None]:
    """Return (snippet, first_line_number), or (None, None) if out of range."""
    if line_start < 1 or line_start > len(source_lines):
        return None, None
    end = min(max(line_end, line_start), len(source_lines), line_start + MAX_SNIPPET_LINES - 1)
    return "\n".join(source_lines[line_start - 1 : end]), line_start
