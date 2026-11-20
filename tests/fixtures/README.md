Fixtures are raw output captured from the real tools run on `samples/vulnerable_sample.py`
(and a two-line file with a syntax error), using:

    cd samples && ruff check --output-format json --no-cache --isolated --select E,F,W,B vulnerable_sample.py
    cd samples && bandit -f json -q vulnerable_sample.py

Captured with ruff 0.17.6 and bandit 1.9.4. Newer versions may change output; if parsing tests
fail after an upgrade, that is the adapter doing its job. Re-capture and review the diff.
