import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from leaklens.audit import audit
from leaklens.leakage import scan, score, split_overlap, temporal_overlap
from leaklens.scanner import scan_file, scan_source

st.set_page_config(page_title="LeakLens", layout="wide")
st.title("LeakLens")
st.caption("Catch data leakage before it fools you.")
t1, t2, t3 = st.tabs(["Dataset audit", "Code scanner", "Model arena"])


def show(fs):
    c1, c2 = st.columns(2)
    c1.metric("Trust score", f"{score(fs)}/100")
    c2.metric("High-severity leaks", sum(f.severity == "high" for f in fs))
    if fs:
        st.dataframe(pd.DataFrame([f.to_dict() for f in fs]))
    else:
        st.success("No leakage found.")


with t1:
    up = st.file_uploader("Training CSV", type="csv", key="tr")
    if up:
        df = pd.read_csv(up)
        target = st.selectbox("Target column", list(df.columns), index=len(df.columns) - 1)
        thr = st.slider("Leak threshold", 0.80, 1.00, 0.95, 0.01)
        te_up = st.file_uploader("Optional test CSV (checks overlap)", type="csv", key="te")
        fs = scan(df, target, thr)
        if te_up:
            te = pd.read_csv(te_up)
            fs += split_overlap(df, te)
            tc = st.selectbox("Time column (optional)", [""] + list(df.columns))
            if tc and tc in te.columns:
                fs += temporal_overlap(df, te, tc)
        show(fs)
        st.json(audit(df, target), expanded=False)

with t2:
    code = st.text_area("Paste Python code", height=220)
    nb = st.file_uploader("...or a .py / .ipynb file", type=["py", "ipynb"])
    if nb:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / Path(nb.name).name
            p.write_bytes(nb.getvalue())
            show(scan_file(p))
    elif code.strip():
        show(scan_source(code, "pasted"))

with t3:
    up3 = st.file_uploader("Training CSV", type="csv", key="ar")
    if up3:
        df3 = pd.read_csv(up3)
        tgt = st.selectbox("Target", list(df3.columns), index=len(df3.columns) - 1, key="tg")
        tcol = st.selectbox("Time column (optional)", [""] + list(df3.columns), key="tc")
        if st.button("Run arena"):
            try:
                from leaklens.arena import run
            except ImportError:
                st.error('pip install -e ".[arena]"')
            else:
                with st.spinner("Training 3 model families..."):
                    res = run(df3, tgt, tcol or None)
                st.write(f"Ranked by {res.attrs['primary']}. Auto-dropped: {', '.join(map(str, res.attrs['dropped'])) or 'none'}")
                st.dataframe(res.round(4))
                st.caption("Best model saved to models/best.joblib")