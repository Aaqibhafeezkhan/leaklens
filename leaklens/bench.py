"""Labeled regression benchmark for the code scanner.

Usage: python -m leaklens.bench [--write docs/BENCHMARK.md]
"""
from __future__ import annotations

import sys
from pathlib import Path

from .scanner import scan_source

SPLIT = "from sklearn.model_selection import train_test_split\n"
CASES: list[tuple[str, str, bool]] = []

for _cls, _m in [("StandardScaler", "fit_transform"), ("MinMaxScaler", "fit_transform"),
                 ("RobustScaler", "fit_transform"), ("SimpleImputer", "fit_transform"),
                 ("PCA", "fit_transform"), ("TfidfVectorizer", "fit_transform"),
                 ("SelectKBest", "fit_transform"), ("SMOTE", "fit_resample"), ("ADASYN", "fit_resample")]:
    head = f"from x import {_cls}\n" + SPLIT
    CASES.append((f"{_cls} fitted before split", head + f"obj = {_cls}()\nX = obj.{_m}(X)\na = train_test_split(X, y)\n", True))
    CASES.append((f"{_cls} fitted after split on train", head + f"a = train_test_split(X, y)\nobj = {_cls}()\nX_train = obj.{_m}(X_train)\n", False))

CASES += [
    ("scale() before split",
     "from sklearn.preprocessing import scale\n" + SPLIT + "X = scale(X)\na = train_test_split(X, y)\n", True),
    ("scaler fitted on test data",
     "from sklearn.preprocessing import StandardScaler\nsc = StandardScaler()\nZ = sc.fit_transform(X_test)\n", True),
    ("scaler before KFold",
     "from sklearn.preprocessing import StandardScaler\nfrom sklearn.model_selection import KFold\n"
     "sc = StandardScaler()\nX = sc.fit_transform(X)\nkf = KFold(5)\nfor tr, te in kf.split(X):\n    pass\n", True),
    ("imputer .fit before split",
     "from sklearn.impute import SimpleImputer\n" + SPLIT + "imp = SimpleImputer()\nimp.fit(X)\na = train_test_split(X, y)\n", True),
    ("fit on train, transform test",
     "from sklearn.preprocessing import StandardScaler\n" + SPLIT +
     "a = train_test_split(X, y)\nsc = StandardScaler()\nX_train = sc.fit_transform(X_train)\nX_test = sc.transform(X_test)\n", False),
    ("pipeline inside cross_val_score",
     "from sklearn.pipeline import make_pipeline\nfrom sklearn.model_selection import cross_val_score\n"
     "pipe = make_pipeline(StandardScaler(), LogisticRegression())\nscores = cross_val_score(pipe, X, y)\n", False),
    ("label encoder before split (benign)",
     "from sklearn.preprocessing import LabelEncoder\n" + SPLIT + "le = LabelEncoder()\ny = le.fit_transform(y)\na = train_test_split(X, y)\n", False),
    ("one-hot before split (benign)",
     "from sklearn.preprocessing import OneHotEncoder\n" + SPLIT + "ohe = OneHotEncoder()\nX = ohe.fit_transform(X)\na = train_test_split(X, y)\n", False),
    ("transform only",
     "from sklearn.preprocessing import StandardScaler\nsc = StandardScaler()\nX_test = sc.transform(X_test)\n", False),
    ("fit inside KFold loop",
     "from sklearn.preprocessing import StandardScaler\nfrom sklearn.model_selection import KFold\n"
     "kf = KFold(5)\nfor tr, te in kf.split(X):\n    sc = StandardScaler()\n    Xtr = sc.fit_transform(X[tr])\n", False),
    ("no preprocessing",
     SPLIT + "from sklearn.linear_model import LogisticRegression\na = train_test_split(X, y)\nm = LogisticRegression()\nm.fit(X_train, y_train)\n", False),
    ("scale() on train after split",
     "from sklearn.preprocessing import scale\n" + SPLIT + "a = train_test_split(X, y)\nXs = scale(X_train)\n", False),
]


def evaluate() -> dict:
    tp = fp = tn = fn = 0
    errors = []
    for name, code, leaky in CASES:
        flagged = any(f.severity in ("high", "medium") for f in scan_source(code, name))
        if leaky and flagged:
            tp += 1
        elif leaky:
            fn += 1
            errors.append(f"missed: {name}")
        elif flagged:
            fp += 1
            errors.append(f"false alarm: {name}")
        else:
            tn += 1
    prec = tp / (tp + fp) if tp + fp else 1.0
    rec = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"n": len(CASES), "leaky": tp + fn, "clean": tn + fp, "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": prec, "recall": rec, "f1": f1, "errors": errors}


def markdown(m: dict) -> str:
    miss = "\n".join(f"- {e}" for e in m["errors"]) or "- none"
    return (
        "# Scanner benchmark\n\n"
        f"{m['n']} hand-written labeled snippets ({m['leaky']} leaky, {m['clean']} clean). "
        "A snippet counts as flagged when the scanner reports a high or medium finding.\n\n"
        "| Metric | Value |\n|---|---|\n"
        f"| Precision | {m['precision']:.2f} |\n| Recall | {m['recall']:.2f} |\n| F1 | {m['f1']:.2f} |\n"
        f"| True / false positives | {m['tp']} / {m['fp']} |\n| True / false negatives | {m['tn']} / {m['fn']} |\n\n"
        f"Misclassified:\n{miss}\n\n"
        "## Caveats\n"
        "The set is small, hand-written and partly shaped by the scanner's own rules, so it guards against "
        "regressions; it does not measure real-world accuracy. For prevalence on real notebooks, "
        "see [STUDY.md](STUDY.md) (also a heuristic).\n"
    )


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    m = evaluate()
    text = markdown(m)
    print(text)
    if len(argv) >= 2 and argv[0] == "--write":
        out = Path(argv[1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return 1 if m["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())