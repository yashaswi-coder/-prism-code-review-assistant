# PRism development benchmark

This is a small, synthetic benchmark for checking that PRism's current Ruff,
Bandit, and early Java Semgrep rules find known examples and do not report
findings on simple clean examples. It is a development baseline, not a real-world
accuracy claim or an independently reviewed security benchmark.

## Run

From the repository root, install the project and development dependencies, then
run:

```powershell
python -m pip install -e ".[dev]"
python scripts/evaluate_benchmark.py
```

The script prints JSON to standard output. Save a report explicitly with:

```powershell
python scripts/evaluate_benchmark.py --output work/benchmark-results.json
```

The evaluation reads each `.py` or `.java` case as text and passes it to PRism's
static analyzer. It never imports or executes benchmark code. Each case has a
small expected-finding list in `benchmarks/manifest.json`. Reports include a
`score_by_language` section so Python and Java scores are reported separately.

## Scoring

A finding matches when its case ID, source tool, and rule ID match an expected
label. Repeated occurrences count separately. The report includes micro-averaged
true positives, false positives, false negatives, precision, recall, and F1
(`null` when a denominator is zero), with per-case, per-tool, and per-rule scores,
unexpected and missed findings, and tool versions.

The cases are synthetic and hand-labeled. The Java subset covers four deliberately
vulnerable patterns and three clean examples, so it is especially small. The
benchmark does not measure whether a finding is useful to a developer, whether
rules are correct across diverse codebases, or how often real issues are missed.
Expand the dataset with reviewed examples before using scores to compare versions
or make claims.

## Version 0.1 initial run

The initial local run used Python 3.15.0, Ruff 0.17.6, and Bandit 1.9.4. It
matched all 5 expected finding instances across 6 cases (precision 1.0, recall
1.0, F1 1.0). Two clean cases had no expected or predicted findings, so their
per-case precision/recall/F1 are `null`. These values only confirm that this tiny
synthetic set and evaluator agree; they are not evidence of real-world accuracy.

## Version 0.2 Python run

With the same Python 3.15.0, Ruff 0.17.6, and Bandit 1.9.4 environment, the
expanded set contains 24 cases and 18 expected finding instances. The evaluator
matched 18/18 (precision 1.0, recall 1.0, F1 1.0), with 8 clean cases returning
no findings. These deliberately small synthetic cases check rule wiring and
metric calculations; they do not estimate behavior on real repositories.

## Version 0.3 Python and Java run

Version 0.3 adds four Java cases with one expected finding each (hardcoded
credential, weak digest, command execution, and SQL concatenation), plus three
clean Java cases. Inspect the Java-specific `score_by_language` values in the
report. This small synthetic set is only a development check, not a quality
claim about Java analysis.

## Add a case

1. Add a small synthetic Python file under `benchmarks/cases/` or Java file under `benchmarks/cases/java/`.
2. Add a manifest entry with a unique ID, case path, and expected `{ "tool", "rule_id" }` records.
3. Run the evaluator and inspect the unexpected/missed details before updating
   expected labels. Keep cases synthetic unless real code is explicitly licensed
   and safe to publish.
