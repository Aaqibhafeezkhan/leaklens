from __future__ import annotations

import ast
import json
import re
import warnings
from pathlib import Path

from .leakage import Finding

FIT = {"fit", "fit_transform", "fit_resample"}
HINTS = ("Scaler", "Imputer", "Encoder", "PCA", "SMOTE", "ADASYN", "Vectorizer", "Normalizer",
         "Transformer", "Selector", "RandomOverSampler", "RandomUnderSampler", "Binarizer", "Discretizer")
RESAMPLE = ("SMOTE", "ADASYN", "RandomOverSampler", "RandomUnderSampler")
BENIGN = ("LabelEncoder", "OrdinalEncoder", "OneHotEncoder")
EVAL = re.compile(r"(^|[_\W])(test|val|valid|validation|eval)([_\W]|$)", re.I)
SKIP = {".venv", "venv", ".git", "node_modules", "site-packages", "__pycache__"}


def _name(c: ast.Call) -> str:
    f = c.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def scan_source(src: str, label: str = "<src>", cells=None) -> list[Finding]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
    except SyntaxError as e:
        return [Finding("low", "parse_error", label, str(e))]
    ctor, calls = {}, []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    ctor[t.id] = _name(n.value)
        elif isinstance(n, ast.Call):
            calls.append(n)

    def is_split(c):
        if _name(c) == "train_test_split":
            return True
        f = c.func
        return (isinstance(f, ast.Attribute) and f.attr == "split" and isinstance(f.value, ast.Name)
                and any(k in ctor.get(f.value.id, "") for k in ("Fold", "Split")))

    splits = [c.lineno for c in calls if is_split(c)]
    first = min(splits) if splits else None

    def loc(line):
        if cells:
            hit = [(s, i) for s, i in cells if s <= line]
            if hit:
                s, i = hit[-1]
                return f"{label}[cell {i}]:{line - s + 1}"
        return f"{label}:{line}"

    out = []
    for c in sorted(calls, key=lambda x: (x.lineno, x.col_offset)):
        f = c.func
        if not (isinstance(f, ast.Attribute) and f.attr in FIT and isinstance(f.value, ast.Name)):
            continue
        cls = ctor.get(f.value.id, "")
        if not any(h in cls for h in HINTS):
            continue
        args = ", ".join(ast.unparse(a) for a in c.args)
        if EVAL.search(args):
            out.append(Finding("high", "fit_on_eval_data", loc(c.lineno),
                               f"{cls}.{f.attr}({args}) learns from evaluation data"))
        elif first is not None and c.lineno < first:
            kind = "resample_before_split" if any(r in cls for r in RESAMPLE) else "preprocess_before_split"
            sev = "low" if any(b in cls for b in BENIGN) else "high"
            if sev == "low":
                kind = "encoder_before_split"
            out.append(Finding(sev, kind, loc(c.lineno),
                               f"{cls}.{f.attr}() runs before the split at {loc(first)}"))
    return out


def scan_file(path) -> list[Finding]:
    p = Path(path)
    txt = p.read_text(encoding="utf-8", errors="ignore")
    if p.suffix != ".ipynb":
        return scan_source(txt, str(p))
    try:
        nb = json.loads(txt)
    except ValueError as e:
        return [Finding("low", "parse_error", str(p), str(e))]
    parts, cells, line = [], [], 1
    for i, c in enumerate(nb.get("cells", [])):
        if c.get("cell_type") != "code":
            continue
        src = c.get("source", "")
        if isinstance(src, list):
            src = "".join(src)
        lines = []
        for l in src.splitlines():
            if l.lstrip().startswith(("%", "!")):
                l = l[: len(l) - len(l.lstrip())] + "pass"
            lines.append(l)
        cells.append((line, i))
        parts.append("\n".join(lines))
        line += max(len(lines), 1)
    return scan_source("\n".join(parts), str(p), cells)


def scan_path(path) -> list[Finding]:
    p = Path(path)
    if p.is_file():
        files = [p]
    else:
        files = [f for f in sorted(p.rglob("*")) if f.suffix in (".py", ".ipynb") and not (SKIP & set(f.parts))]
    out = []
    for f in files:
        out += scan_file(f)
    return out