# Leakage study

Run on 2026-10-21 with `python scripts/study.py`.

- Public notebooks with a train/test split scanned: **1729**
- Flagged with at least one high-severity pipeline leak: **882 (51%)**

| Pattern | Notebooks |
|---|---|
| preprocess_before_split | 765 |
| resample_before_split | 112 |
| fit_on_eval_data | 92 |

## Method and caveats
Notebooks come from GitHub code search for common scikit-learn preprocessing calls, so the sample is not random. The scanner is a static heuristic: it can flag code that is fine (for example a fit on a different, already-split frame) and miss leaks it cannot see. Treat the numbers as a rough prevalence signal, not a verdict on any notebook. Notebooks with syntax errors were skipped. No repositories are named.
