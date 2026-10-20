from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


@dataclass
class Finding:
    severity: str
    kind: str
    column: str
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


def _encode(s: pd.Series) -> np.ndarray:
    if s.dtype.kind in "biuf":
        fill = s.median() if s.notna().any() else 0.0
        return s.astype(float).fillna(fill).to_numpy().reshape(-1, 1)
    return s.astype("category").cat.codes.to_numpy().astype(float).reshape(-1, 1)


def single_feature_leaks(df, target, threshold=0.95, max_rows=20000, seed=0):
    d = df[df[target].notna()]
    if len(d) > max_rows:
        d = d.sample(max_rows, random_state=seed)
    y_raw = d[target]
    clf = y_raw.dtype.kind not in "iuf" or y_raw.nunique() <= 20
    if clf:
        y = y_raw.astype("category").cat.codes.to_numpy()
        scoring = "roc_auc" if len(np.unique(y)) == 2 else "balanced_accuracy"
        make = lambda: DecisionTreeClassifier(max_depth=4, random_state=seed)
    else:
        y = y_raw.astype(float).to_numpy()
        scoring = "r2"
        make = lambda: DecisionTreeRegressor(max_depth=4, random_state=seed)
    out = []
    for c in d.columns:
        if c == target:
            continue
        try:
            sc = float(cross_val_score(make(), _encode(d[c]), y, cv=5, scoring=scoring).mean())
        except Exception:
            continue
        if sc >= threshold:
            sev = "high"
        elif sc >= threshold - 0.1:
            sev = "medium"
        else:
            continue
        out.append(Finding(sev, "target_leakage", c, f"alone predicts target ({scoring}={sc:.3f})"))
    return out


def id_like(df, target, ratio=0.98):
    out = []
    if len(df) < 50:
        return out
    for c in df.columns:
        if c == target or df[c].dtype.kind not in "OSUiu":
            continue
        r = df[c].nunique(dropna=True) / len(df)
        if r >= ratio:
            out.append(Finding("medium", "id_like", c, f"{r:.1%} unique values; likely an identifier"))
    return out


def split_overlap(train, test):
    cols = [c for c in train.columns if c in test.columns]
    a = set(pd.util.hash_pandas_object(train[cols], index=False))
    n = int(pd.util.hash_pandas_object(test[cols], index=False).isin(a).sum())
    if n == 0:
        return []
    return [Finding("high", "split_overlap", "*", f"{n} test rows ({n / len(test):.1%}) also appear in train")]


def temporal_overlap(train, test, time_col):
    a = pd.to_datetime(train[time_col], errors="coerce")
    b = pd.to_datetime(test[time_col], errors="coerce")
    if a.max() > b.min():
        return [Finding("high", "temporal_leakage", time_col, f"train extends to {a.max()} but test starts {b.min()}")]
    return []


def scan(df, target, threshold=0.95):
    return single_feature_leaks(df, target, threshold) + id_like(df, target)


def score(findings) -> int:
    pen = {"high": 35, "medium": 15, "low": 5}
    return max(0, 100 - sum(pen.get(f.severity, 0) for f in findings))