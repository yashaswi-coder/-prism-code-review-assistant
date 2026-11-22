# Roadmap

Status key: **done** (implemented and tested here), **planned** (not started).

| Milestone | Status |
|---|---|
| 0 Inspect and plan | done |
| 1 Repository foundation | done |
| 2 Ruff/Bandit engine + normalized schema + failure handling | done |
| 3 Streamlit UI, filters, Markdown/JSON reports, single-file changed-line diff review | done |
| 4 Tests and reproducibility | done for current scope; no benchmark metrics exist |
| 5 AI review layer (opt-in, validated against source) | planned |
| 6 Session-only finding feedback + metadata export | implemented; labeled benchmark/evaluation planned |
| 7 GitHub Action, then opt-in PR comments | planned |
| 8 Research extensions (one at a time, hypothesis first) | planned |

Next recommended step: Milestone 6 *before* 5 is worth considering. A benchmark of labeled snippets lets you measure the static-only baseline first, so any AI layer is compared against real numbers instead of impressions. Decide that explicitly.
