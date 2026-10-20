# LeakLens

Audit datasets and ML code for data leakage before it fools you.

## Detects
- Target leakage (a single feature that almost perfectly predicts the label)
- ID-like columns
- Train/test row overlap
- Temporal leakage (train data newer than test data)
- Pipeline leaks in `.py` and `.ipynb`: scaler/encoder/imputer fitted before the split, SMOTE before the split, transformers fitted on test/validation data

## Quick start

pip install -e “.[dev]”
leaklens train.csv --target label --test test.csv --time date
leaklens --scan notebooks/
leaklens --scan examples/bad_pipeline.py --json

Exit code is 1 when a high-severity leak is found, so it works in CI.

## Roadmap
- [x] Core detectors + CLI
- [x] Static scanner for notebooks/scripts
- [ ] Model arena with MLflow
- [ ] FastAPI + Streamlit UI
- [ ] Docker, GitHub Action, trust-score badge