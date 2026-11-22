# Architecture (current: MVP)

```
app.py (Streamlit)  ->  analyzer.analyze_source()
                          1. inputs.py      validate size / type / emptiness
                          2. temp dir       write code to target.py or target.java (deleted afterwards)
                          3. adapters/      Python: Ruff + Bandit; Java: local Semgrep rules
                          4. models.py      AnalysisResult(tool_runs, findings)
                       report.py            Markdown / JSON
```

| Module | Responsibility |
|---|---|
| `models.py` | Pydantic schema: `Finding`, `Evidence`, `ToolRun`, `AnalysisResult` |
| `inputs.py` | Input limits and file-name sanitizing |
| `runner.py` | The only place that starts subprocesses (argv list, timeout, `-I`) |
| `adapters/*` | Pure `parse_*` functions (unit-tested on real fixtures) + thin `run_*` wrappers |
| `evidence.py` | Snippets are cut from the submitted text, since Ruff returns none |
| `analyzer.py` | Orchestration; one tool failing does not hide the other's results |

## Design decisions
- **Ruff `S` rules are disabled** so security findings come from Bandit only (avoids double-reporting).
- **Severity/category mapping for Ruff** (PRism heuristic, not Ruff's opinion): `F`->correctness/medium, `B`->bug-risk/medium, `E`,`W`->style/low, syntax errors->correctness/high. Bandit severity and confidence are passed through.
- Java runs Semgrep with the repository's `rules/java.yml`; `--metrics=off` is set so code is analyzed locally. The initial Java rules are intentionally narrow and are not a full Java correctness or security audit.
- **Tool status vocabulary:** `ok`, `partial` (tool ran but reported a problem, e.g. Bandit cannot parse a file with a syntax error), `error`, `missing`, `timeout`.
- **`origin` field** exists on `Finding` (currently only `"deterministic"`) so Milestone 5 can add AI findings without mixing them.
- No database, no network calls, no LLM code.
