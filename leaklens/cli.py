from __future__ import annotations

import argparse
import json

import pandas as pd

from .audit import audit
from .leakage import scan, score, split_overlap, temporal_overlap
from .scanner import scan_path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="leaklens", description="Audit datasets and ML code for leakage")
    p.add_argument("train", nargs="?")
    p.add_argument("--target")
    p.add_argument("--test")
    p.add_argument("--time")
    p.add_argument("--threshold", type=float, default=0.95)
    p.add_argument("--scan", help="file or folder of .py/.ipynb to scan for pipeline leaks")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if not a.train and not a.scan:
        p.error("give a CSV and/or --scan PATH")
    if a.train and not a.target:
        p.error("--target is required with a CSV")
    fs, rep = [], {}
    if a.train:
        tr = pd.read_csv(a.train)
        fs += scan(tr, a.target, a.threshold)
        if a.test:
            te = pd.read_csv(a.test)
            fs += split_overlap(tr, te)
            if a.time:
                fs += temporal_overlap(tr, te, a.time)
        rep["audit"] = audit(tr, a.target)
    if a.scan:
        fs += scan_path(a.scan)
    rep = {"trust_score": score(fs), **rep, "findings": [f.to_dict() for f in fs]}
    if a.json:
        print(json.dumps(rep, indent=2))
    else:
        print(f"LeakLens trust score: {rep['trust_score']}/100")
        for f in fs:
            print(f"[{f.severity.upper()}] {f.kind} :: {f.column} :: {f.detail}")
        if not fs:
            print("No leakage found.")
    return 1 if any(f.severity == "high" for f in fs) else 0