# PRism: evidence-grounded code review assistant

> **Status: work in progress.** PRism has a 24-case synthetic Python benchmark and an early Java analyzer using a small local Semgrep rule set. Neither is a real-world quality estimate.

Research question: *How can code-review suggestions be made more evidence-grounded, useful, and measurable, while controlling false positives?*

## What is implemented (local MVP)
- Paste Python or Java code, or upload a `.py` or `.java` file in a Streamlit UI.
- Review a single-file `.diff`/`.patch` by uploading the unified diff and the complete updated `.py` file; analysis runs on the full file and displays findings that overlap added/changed lines.
- Deterministic analysis with **Ruff** (rules `E,F,W,B`) and **Bandit** (security patterns) for Python, plus a small set of bundled **Semgrep** rules for Java (hardcoded credentials, weak MD5 digest use, command execution, and SQL string concatenation).
- Findings normalized to one schema (`src/prism/models.py`) with evidence: tool, rule id, file, line range, code snippet, reference URL, CWE (Bandit).
- Filters by source, severity, category. Markdown and JSON report downloads.
- Mark findings as useful, incorrect, or not useful. Feedback is session-only and can be explicitly exported as JSON without code, snippets, messages, paths, or line numbers.
- Run a 24-case labeled synthetic Python benchmark for exact (case, tool, rule ID) precision/recall/F1, including per-tool and per-rule breakdowns; see [`docs/benchmark.md`](docs/benchmark.md). Java is not yet included in the benchmark.
- Failures (missing tool, timeout, bad output, unparseable file) are shown in the UI and reports, never hidden.
- Unit tests with fixtures that are real tool output, plus a headless UI smoke test.

## What is NOT implemented (planned, see `docs/roadmap.md`)
- AI review suggestions (no model code exists; the app has no network calls)
- An independently reviewed benchmark representative of real-world code; current 24-case synthetic scores are only a development baseline
- GitHub Action / PR integration

## Safety properties (and how they are checked)
- Submitted code is **never executed or imported**; tools only read it. Test: `test_submitted_code_is_never_executed`.
- Tools run via argument lists, no `shell=True`, with timeouts, using `python -I`. Test: `test_subprocess_uses_argv_list_without_shell`.
- Input limits: 200 KB, UTF-8 text, `.py` and `.java` source uploads and Python `.diff`/`.patch` uploads only, no NUL bytes.
- Code is written to a temp directory that is deleted after analysis. PRism does not log or save source. Streamlit usage stats are disabled in `.streamlit/config.toml`. While you use the app, results (including code snippets) stay in your browser session's memory.
- Finding feedback remains in the browser session unless you explicitly download it. The JSON export contains labels and rule metadata only; it excludes source code, snippets, finding messages, file paths, and line numbers.
- Semgrep runs locally with a bundled rule file and metrics disabled; Java analysis is a narrow rule-based prototype, not comprehensive Java review.
- Not covered: this is a local tool, not a hardened multi-user service. Do not expose it publicly as-is.

## Setup and run
Requires Python (declared `>=3.10`; **only 3.12.3 has been tested**).
The root `requirements.txt` installs the project in editable mode for Streamlit Community Cloud; runtime dependencies remain declared in `pyproject.toml`.
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
streamlit run app.py          # opens http://localhost:8501
pytest                         # run the tests
```
Try `samples/vulnerable_sample.py` (synthetic, deliberately flawed; it is never executed).
For the Java prototype, try `samples/vulnerable_sample.java` (also synthetic and never executed).

## Verified so far (run in the build environment, Python 3.12.3, ruff 0.17.6, bandit 1.9.4, streamlit 1.67.0, pydantic 2.14.4)
- `pytest`: 35 passed.
- `streamlit run app.py --server.headless true`: server responded `200 ok` on the health endpoint.
- Sample file yields 6 findings (1 Ruff, 5 Bandit).
- **Unverified:** behavior on Windows/macOS, other Python versions, browsers, large inputs near the limit, and any real-world codebase.

## Known limitations
- Static analysis yields false positives and false negatives. No findings != safe.
- Ruff has no severity field; the severity/category for Ruff rules is a PRism heuristic (`docs/architecture.md`).
- Single-file analysis only; no cross-file context.

## Before linking this in an application
Run it yourself from a clean clone, confirm the commands above work, keep the WIP label until the benchmark exists, and only describe what you can demonstrate. This project does not guarantee any admission or hiring outcome.
