# Roadmap

Status key: **done** (implemented and tested here), **planned** (not started).

| Milestone | Status |
|---|---|
| 0 Inspect and plan | done |
| 1 Repository foundation | done |
| 2 Ruff/Bandit engine + normalized schema + failure handling | done |
| 3 Streamlit UI, filters, Markdown/JSON reports, single-file changed-line diff review | done |
| 4 Tests and reproducibility | done for current scope |
| 5 AI review layer (opt-in, validated against source) | planned |
| 6 Session-only finding feedback + metadata export + 24-case synthetic baseline with per-tool/per-rule scoring | implemented; independently reviewed benchmark planned |
| 7 GitHub Action, then opt-in PR comments | planned |
| 8 Research extensions (one at a time, hypothesis first) | planned |
| 9 Java source analysis with local Semgrep rules | prototype in progress; validation, benchmark coverage, and deployed verification remain |

Next recommended step: validate the Java rules against labeled examples and false-positive cases, add Java cases to the benchmark, then gather structured developer feedback before claiming cross-language quality.
