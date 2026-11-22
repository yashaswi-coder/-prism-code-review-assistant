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

Next recommended step: add independently reviewed and feedback-labeled examples to the benchmark, then report per-rule and aggregate results before adding AI suggestions.
