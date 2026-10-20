# LeakLens

Audit datasets and ML code for data leakage before it fools you.

## Detects
- Target leakage (a single feature that almost perfectly predicts the label)
- ID-like columns
- Train/test row overlap
- Temporal leakage (train data newer than test data)
- Pipeline leaks in `.py` and `.ipynb`: scaler/encoder/imputer fitted before the split, SMOTE before the split, transformers fitted on test/validation data

## Model arena
Auto-drops leaking and ID columns, then trains three model families (linear, gradient-boosted trees, neural net) inside leak-safe pipelines. Every run is tracked in a local MLflow store (SQLite) and the winner is saved to `models/best.joblib`. Use `--time` for a temporal split.

## REST API and UI

pip install -e “.[dev,app]”
uvicorn leaklens.api:app --port 8000 # docs at http://localhost:8000/docs
streamlit run leaklens/ui.py

Endpoints: `GET /health`, `POST /audit` (CSV upload + target), `POST /scan` (Python source), `POST /predict` (rows scored by the saved best model).

## CLI quick start

leaklens train.csv --target label --test test.csv --time date
leaklens --scan notebooks/
python examples/make_demo.py
leaklens demo.csv --target is_fraud --arena
mlflow ui --backend-store-uri sqlite:///mlflow.db

Exit code is 1 when a high-severity leak is found, so it works in CI.

## Roadmap
- [x] Core detectors + CLI
- [x] Static scanner for notebooks/scripts
- [x] Model arena with MLflow
- [x] FastAPI + Streamlit UI
- [ ] Docker, GitHub Action, trust-score badge