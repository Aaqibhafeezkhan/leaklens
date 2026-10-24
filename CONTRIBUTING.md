# Contributing to LeakLens

1. Fork and clone, then `python -m venv .venv` and activate it.
2. `pip install -e ".[dev,app]"`
3. Make your change and add a test in `tests/`.
4. `pytest -q` must pass, and `leaklens --scan leaklens` must report no leaks.
5. Open a PR with a short description of the leak it detects or the bug it fixes.

New detectors belong in `leaklens/leakage.py` (data) or `leaklens/scanner.py` (code). Each one returns `Finding` objects with a severity of `high`, `medium` or `low`.

Look for issues labeled **good first issue**.
## Claiming an issue
Comment on the issue to claim it. The first person to ask gets it assigned; others please pick another issue (or review the open PR). First-time contributors: one issue at a time. If an assigned issue has no activity for 7 days, a maintainer may offer it to someone else. Questions are welcome in the issue thread.