"""Scan public GitHub notebooks and report how many trip LeakLens's pipeline-leak rules.

Usage: python scripts/study.py [per_query_limit]   (needs the gh CLI, logged in)
"""
import collections
import concurrent.futures as cf
import datetime
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

from leaklens.scanner import scan_file

QUERIES = [
    "StandardScaler fit_transform",
    "SMOTE fit_resample",
    "MinMaxScaler fit_transform",
    "RobustScaler fit_transform",
]


def search(q, limit):
    r = subprocess.run(["gh", "search", "code", q, "--extension", "ipynb", "--limit", str(limit),
                        "--json", "path,repository"], capture_output=True, text=True)
    if r.returncode != 0:
        print("search failed:", r.stderr.strip()[:200])
        return []
    return json.loads(r.stdout or "[]")


def fetch(item):
    repo = item["repository"]["nameWithOwner"]
    url = f"https://raw.githubusercontent.com/{repo}/HEAD/{urllib.parse.quote(item['path'])}"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return item, r.read(3_000_000)
    except Exception:
        return item, None


def main(n=100):
    seen, items = set(), []
    for q in QUERIES:
        res = search(q, n)
        print(q, len(res))
        for it in res:
            k = (it["repository"]["nameWithOwner"], it["path"])
            if k not in seen:
                seen.add(k)
                items.append(it)
        time.sleep(7)
    print(len(items), "notebooks found")
    kinds = collections.Counter()
    scanned = flagged = 0
    with tempfile.TemporaryDirectory() as td, cf.ThreadPoolExecutor(8) as ex:
        for i, (it, data) in enumerate(ex.map(fetch, items)):
            if not data:
                continue
            if b"train_test_split" not in data and b"KFold" not in data:
                continue
            p = pathlib.Path(td) / f"{i}.ipynb"
            p.write_bytes(data)
            fs = scan_file(p)
            if any(f.kind == "parse_error" for f in fs):
                continue
            scanned += 1
            hi = {f.kind for f in fs if f.severity == "high"}
            if hi:
                flagged += 1
                kinds.update(hi)
    if not scanned:
        print("nothing scanned (check gh auth / network)")
        return 1
    pct = 100 * flagged / scanned
    lines = [
        "# Leakage study",
        "",
        f"Run on {datetime.date.today()} with `python scripts/study.py`.",
        "",
        f"- Public notebooks with a train/test split scanned: **{scanned}**",
        f"- Flagged with at least one high-severity pipeline leak: **{flagged} ({pct:.0f}%)**",
        "",
        "| Pattern | Notebooks |",
        "|---|---|",
    ]
    lines += [f"| {k} | {v} |" for k, v in kinds.most_common()]
    lines += [
        "",
        "## Method and caveats",
        "Notebooks come from GitHub code search for common scikit-learn preprocessing and split calls, "
        "so the sample is not random. The scanner is a static heuristic: it can flag code that is fine "
        "(for example a fit on a different, already-split frame) and miss leaks it cannot see. "
        "Treat the numbers as a rough prevalence signal, not a verdict on any notebook. "
        "Notebooks with syntax errors were skipped. No repositories are named.",
    ]
    out = pathlib.Path("docs") / "STUDY.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 100))