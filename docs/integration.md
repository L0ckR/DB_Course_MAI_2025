# Integration notes (MLflow / scikit-learn)

This repo does not implement the MLflow tracking API. Below are practical options to integrate common ML stacks with the current schema.

## Option A: scikit-learn → direct API logging (recommended for demo)

Use a small helper to create a run, then push metrics to the API. Authenticate with a bearer token (obtain it from `/api/auth/login`) to keep audit logging intact.

```python
import uuid
import requests
from sklearn.metrics import accuracy_score

API = "http://localhost:8000/api"
HEADERS = {"Authorization": "Bearer <access_token>"}

# 1) Create a run
payload = {
    "experiment_id": "<experiment_uuid>",
    "dataset_version_id": "<dataset_version_uuid>",
    "run_name": "sklearn-baseline",
    "status": "running",
    "config": {
        "params_json": {"model": "LogisticRegression", "C": 1.0},
        "env_json": {"python": "3.12", "sklearn": "1.5"},
        "command_line": "python train.py",
        "seed": 42
    }
}
run = requests.post(f"{API}/runs", json=payload, headers=HEADERS).json()

# 2) Log metrics
accuracy = accuracy_score([1, 0, 1], [1, 0, 0])
requests.post(
    f"{API}/runs/{run['run_id']}/metrics",
    json=[{"metric_key": "accuracy", "scope": "val", "value": accuracy}],
    headers=HEADERS,
)

# 3) Complete run
requests.post(
    f"{API}/runs/{run['run_id']}/complete",
    json={"status": "finished"},
    headers=HEADERS,
)
```

## Option B: MLflow export/import (batch)

1. Log with MLflow as usual (`mlflow.log_param`, `mlflow.log_metric`, `mlflow.log_artifact`).
2. Export the MLflow run data from the local `mlruns/` store.
3. Map MLflow entities to this schema:

- MLflow experiment → `ml_projects` + `experiments`
- MLflow run → `runs` + `run_configs` (params into `params_json`)
- MLflow metrics → `run_metric_values`
- MLflow artifacts → `artifacts` + `run_artifacts` (store URI only)

This can be automated with a small script that reads the MLflow file store and uses the `/api/batch-import` endpoint for metrics.

## Option C: MLflow API compatibility (future)

Implement a minimal subset of MLflow tracking REST endpoints and translate them into the existing database tables. This keeps MLflow clients unchanged but requires additional backend work:

- `/api/2.0/mlflow/experiments/*`
- `/api/2.0/mlflow/runs/*`
- `/api/2.0/mlflow/metrics/*`

For the course demo, Option A or B is usually enough.
