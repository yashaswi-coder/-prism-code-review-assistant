## Java prototype demo

> **Status: work in progress.** PRism has a small synthetic Python/Java benchmark and an early Java analyzer using a local Semgrep rule set. Its scores are not a real-world quality estimate.
The vulnerable sample produced two findings: a hardcoded credential and SQL string concatenation.

![Java vulnerable sample results](<Screenshot 2026-11-23 124040.png>)

## What is implemented (local MVP)
- Paste Python or Java code, or upload a `.py` or `.java` file in a Streamlit UI.
- Review a single-file `.diff`/`.patch` by uploading the unified diff and the complete updated `.py` file; analysis runs on the full file and displays findings that overlap added/changed lines.
- Deterministic analysis with **Ruff** (rules `E,F,W,B`) and **Bandit** (security patterns) for Python, plus a small set of bundled **Semgrep** rules for Java (hardcoded credentials, weak MD5 digest use, command execution, and SQL string concatenation).
- **Early Java prototype:** the live demo detected two findings in a deliberately vulnerable sample: a hardcoded credential and SQL built with string concatenation. This demonstrates those two checks only; it is not a measure of general Java analysis quality.
- Findings normalized to one schema (`src/prism/models.py`) with evidence: tool, rule id, file, line range, code snippet, reference URL, CWE (Bandit).
- Filters by source, severity, category. Markdown and JSON report downloads.
- Mark findings as useful, incorrect, or not useful. Feedback is session-only and can be explicitly exported as JSON without code, snippets, messages, paths, or line numbers.
- Run a labeled synthetic Python and Java benchmark for exact (case, tool, rule ID) precision/recall/F1, with per-tool, per-rule, and per-language breakdowns; see [`docs/benchmark.md`](docs/benchmark.md).
- Failures (missing tool, timeout, bad output, unparseable file) are shown in the UI and reports, never hidden.
- Unit tests with fixtures that are real tool output, plus a headless UI smoke test.
The clean sample produced zero findings from the configured rules.

![Java clean sample results](<Screenshot 2026-11-23 123849.png>)

> Early prototype; findings require human review. No findings does not prove code is secure.
