# Real-notebook validation

Five public notebooks were drawn at random from notebooks the scanner had already flagged in the study sample, then read by hand against the scanner output. This estimates how many *flagged* findings are real. It says nothing about recall (leaks the scanner misses). Five notebooks is a tiny sample: treat it as a sanity check, not a measurement. The notebooks are not redistributed and not named.

| # | Notebook | v0.10.0 | v0.11.0 |
|---|---|---|---|
| 1 | k-means on a card-fraud table | 2 high (scale and PCA before the split), both real | unchanged |
| 2 | classifier with repeated cross-validation | 1 high, 7 medium "fit on full data", 13 low, 1 low outside-CV. Every scaler leak was real, but 7 were labeled "fine for a final refit" while their output feeds splits and CV | 4 high before-split, 4 high outside-CV (about 40 repeated calls grouped), 1 medium, 13 low |
| 3 | tutorial: gradient descent with a ColumnTransformer | 1 medium (one-hot only), over-severe | 1 low |
| 4 | tutorial: ColumnTransformer pieces | 1 high and 2 medium, transformers fitted on test data, real | unchanged |
| 5 | World Cup match model | 1 high and 1 medium (the same imputer mistake repeated later), real | 2 high |

Counting high and medium findings: v0.10.0 reported 16, of which 15 were real leaks (the over-severe one-hot case was not). v0.11.0 reports 16, of which 15 are real (one medium finding concerns a scaled array that is never used afterwards). Precision is unchanged on this sample. What changed is the accuracy of the finding kind and severity, support for `permutation_test_score`, and the noise: repeated lines are grouped per transform.

Known misses on these notebooks: `fillna(df.mean())` before a split (open issue), and leaks hidden inside helper functions (open issue).