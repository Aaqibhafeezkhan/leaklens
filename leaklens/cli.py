from __future__ import annotations

import argparse
import json

import pandas as pd

from .audit import audit
from .leakage import scan, score, split_overlap, temporal_overlap


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="leaklens", description="Audit a dataset for ML leakage")
    p.add_argument("train")
    p.add_argument("--target", required=True)
    p.add_argument("--test")
    p.add_argument("--time")
    p.add_argument("--threshold", type=float, default=0.95)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    tr = pd.read_csv(a.train)
    fs = scan(tr, a.target, a.threshold)
    if a.test:
        te = pd.read_csv(a.test)
        fs += split_overlap(tr, te)
        if a.time:
            fs += temporal_overlap(tr, te, a.time)
    rep = {"trust_score": score(fs), "audit": audit(tr, a.target), "findings": [f.to_dict() for f in fs]}
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(f"LeakLens trust score: {rep['trust_score']}/100")
        for f in fs:
            print(f"[{f.severity.upper()}] {f.kind} :: {f.column} :: {f.detail}")
        if not fs:
            print("No leakage found.")
    return 1 if any(f.severity == "high" for f in fs) else 0