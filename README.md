# LeakLens

Audit datasets and ML pipelines for data leakage before it fools you.

## Detects
- Target leakage (single features that almost perfectly predict the label)
- ID-like columns
- Train/test row overlap
- Temporal leakage (train data newer than test data)

## Quick start

pip install -e “.[dev]”
leaklens train.csv --target label --test test.csv --time date

Exit code is 1 when a high-severity leak is found, so it works in CI.

## Roadmap
- [x] Core detectors + CLI
- [ ] Static scanner for notebooks/scripts (fit-before-split)
- [ ] Model arena with MLflow
- [ ] FastAPI + Streamlit UI
- [ ] Docker, GitHub Action, trust-score badge