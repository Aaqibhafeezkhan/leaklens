from __future__ import annotations

import ast
import warnings

from .leakage import Finding
from .scanner import BENIGN, FUNCS, HINTS, RESAMPLE, _all_names, _name, _sev, _tnames

CV_FUNCS = {"cross_val_score", "cross_validate", "cross_val_predict", "learning_curve", "validation_curve"}
SEARCH = ("GridSearchCV", "RandomizedSearchCV", "HalvingGridSearchCV", "HalvingRandomSearchCV", "BayesSearchCV")


def _fit_cls(c, ctor, funcs):
    f = c.func
    if isinstance(f, ast.Name) and f.id in funcs:
        return f.id
    if isinstance(f, ast.Attribute) and f.attr in ("fit_transform", "fit_resample"):
        b = f.value
        if isinstance(b, ast.Name):
            cls = ctor.get(b.id, "")
        elif isinstance(b, ast.Call):
            cls = _name(b)
        else:
            cls = ""
        if any(h in cls for h in HINTS):
            return cls
    return None


def scan_cv(src: str, label: str = "<src>", cells=None) -> list[Finding]:
    """Preprocessing or resampling done on all rows before cross-validation / hyperparameter search."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tree = ast.parse(src)
    except SyntaxError:
        return []
    ctor, assigns, calls, funcs = {}, [], [], set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            assigns.append(n)
            if isinstance(n.value, ast.Call):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        ctor[t.id] = _name(n.value)
        elif isinstance(n, ast.Call):
            calls.append(n)
        elif isinstance(n, ast.ImportFrom) and (n.module or "").startswith("sklearn.preprocessing"):
            for al in n.names:
                if al.name in FUNCS:
                    funcs.add(al.asname or al.name)
    assigns.sort(key=lambda a: a.lineno)

    tr = {}
    for a in assigns:
        if isinstance(a.value, ast.Call) and _name(a.value) == "train_test_split":
            continue
        hit = None
        for c in ast.walk(a.value):
            if isinstance(c, ast.Call):
                cls = _fit_cls(c, ctor, funcs)
                if cls and not any(b in cls for b in BENIGN):
                    hit = (a.lineno, cls)
                    break
        if hit is None:
            srcs = sorted(_all_names(a.value) & set(tr))
            if srcs:
                hit = tr[srcs[0]]
        if hit:
            for t in a.targets:
                for nm in _tnames(t):
                    tr[nm] = hit

    split_lines = [c.lineno for c in calls if _name(c) == "train_test_split"]

    def loc(line):
        if cells:
            h = [(s, i) for s, i in cells if s <= line]
            if h:
                s, i = h[-1]
                return f"{label}[cell {i}]:{line - s + 1}"
        return f"{label}:{line}"

    out = []
    for c in sorted(calls, key=lambda x: (x.lineno, x.col_offset)):
        f = c.func
        fname = _name(c)
        xs, who = None, ""
        if fname in CV_FUNCS:
            xs = c.args[1:2] + [kw.value for kw in c.keywords if kw.arg == "X"]
            who = fname
        elif isinstance(f, ast.Attribute) and f.attr == "fit":
            b = f.value
            cls = ctor.get(b.id, "") if isinstance(b, ast.Name) else (_name(b) if isinstance(b, ast.Call) else "")
            if any(s in cls for s in SEARCH):
                xs = c.args[:1] + [kw.value for kw in c.keywords if kw.arg == "X"]
                who = cls
        if not xs:
            continue
        hit = None
        for e in xs:
            for nm in sorted(_all_names(e)):
                if nm in tr and tr[nm][0] < c.lineno:
                    hit = tr[nm]
                    break
            if hit:
                break
        if not hit:
            continue
        line, cls = hit
        resample = any(r in cls for r in RESAMPLE)
        kind = "resample_outside_cv" if resample else "preprocess_outside_cv"
        sev = _sev(cls)
        if not resample and any(s < line for s in split_lines):
            sev = "low"
        out.append(Finding(sev, kind, loc(c.lineno),
                           f"{who}() is given data transformed by {cls} at {loc(line)}; the transform has seen "
                           f"every fold's validation rows. Put it inside a Pipeline passed to {who}"))
    return out