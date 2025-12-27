#!/usr/bin/env python3
import csv
import hashlib
import os
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError as exc:
    raise SystemExit("Missing dependency: requests. Install with 'pip install requests'.") from exc

try:
    import sklearn
    from sklearn.datasets import load_breast_cancer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, f1_score, log_loss, roc_auc_score
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: scikit-learn. Install with 'pip install scikit-learn'."
    ) from exc


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        if key and key not in os.environ:
            os.environ[key] = value


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"Missing required env var: {name}")
    return value


def api_request(method: str, base_url: str, path: str, token: str | None, **kwargs):
    url = base_url.rstrip("/") + path
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(method, url, headers=headers, timeout=30, **kwargs)
    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise SystemExit(f"{method} {path} failed: {response.status_code} {detail}")
    if response.status_code == 204 or not response.content:
        return None
    return response.json()


def get_token(base_url: str, email: str, password: str) -> str:
    url = base_url.rstrip("/") + "/api/auth/token"
    response = requests.post(
        url,
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    if response.status_code >= 400:
        raise SystemExit(f"Auth failed: {response.status_code} {response.text}")
    return response.json()["access_token"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def write_dataset_csv(path: Path, feature_names, data, target) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(list(feature_names) + ["label"])
        for row, label in zip(data, target):
            writer.writerow(list(row) + [int(label)])


def ensure_metrics(base_url: str, token: str, specs: list[dict]) -> dict[str, str]:
    metrics = api_request("GET", base_url, "/api/metric-definitions", token)
    key_map = {metric["key"]: metric["metric_id"] for metric in metrics}
    for spec in specs:
        if spec["key"] in key_map:
            continue
        created = api_request(
            "POST",
            base_url,
            "/api/metric-definitions",
            token,
            json=spec,
        )
        key_map[created["key"]] = created["metric_id"]
    return key_map


def create_org(base_url: str, token: str, suffix: str) -> dict:
    payload = {
        "name": f"sklearn-demo-org-{suffix}",
        "description": "Org for sklearn demo experiment",
    }
    return api_request("POST", base_url, "/api/orgs", token, json=payload)


def create_project(base_url: str, token: str, org_id: str, suffix: str) -> dict:
    payload = {
        "org_id": org_id,
        "name": f"sklearn-demo-project-{suffix}",
        "description": "Breast cancer classifier demo",
        "status": "active",
    }
    return api_request("POST", base_url, "/api/projects", token, json=payload)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    load_env_file(root / ".env")

    base_url = os.getenv("API_URL", "http://localhost:8000")
    email = require_env("API_EMAIL")
    password = require_env("API_PASSWORD")

    token = get_token(base_url, email, password)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    org = create_org(base_url, token, timestamp)
    project = create_project(base_url, token, org["org_id"], timestamp)

    dataset = load_breast_cancer()
    X_train, X_val, y_train, y_val = train_test_split(
        dataset.data,
        dataset.target,
        test_size=0.2,
        random_state=42,
        stratify=dataset.target,
    )

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, solver="lbfgs"),
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_val)
    probs = model.predict_proba(X_val)[:, 1]

    metrics = {
        "accuracy": accuracy_score(y_val, preds),
        "f1": f1_score(y_val, preds),
        "auc": roc_auc_score(y_val, probs),
        "val_loss": log_loss(y_val, probs),
    }

    artifacts_dir = root / "scripts" / "artifacts"
    dataset_path = artifacts_dir / f"breast_cancer_{timestamp}.csv"
    model_path = artifacts_dir / f"breast_cancer_model_{timestamp}.pkl"

    write_dataset_csv(dataset_path, dataset.feature_names, dataset.data, dataset.target)

    dataset_payload = {
        "project_id": project["project_id"],
        "name": f"breast_cancer_{timestamp}",
        "task_type": "classification",
        "description": "sklearn breast cancer dataset",
    }
    dataset_row = api_request("POST", base_url, "/api/datasets", token, json=dataset_payload)

    dataset_version_payload = {
        "dataset_id": dataset_row["dataset_id"],
        "version_label": "v1",
        "storage_uri": dataset_path.as_uri(),
        "content_hash": sha256_file(dataset_path),
        "row_count": int(dataset.data.shape[0]),
        "size_bytes": dataset_path.stat().st_size,
        "schema_json": {
            "features": list(dataset.feature_names),
            "label": "target",
        },
    }
    dataset_version = api_request(
        "POST", base_url, "/api/dataset-versions", token, json=dataset_version_payload
    )

    metric_specs = [
        {"key": "accuracy", "display_name": "Accuracy", "unit": "ratio", "goal": "max"},
        {"key": "f1", "display_name": "F1", "unit": "ratio", "goal": "max"},
        {"key": "auc", "display_name": "AUC", "unit": "ratio", "goal": "max"},
        {"key": "val_loss", "display_name": "Validation Loss", "unit": "loss", "goal": "min"},
    ]
    ensure_metrics(base_url, token, metric_specs)

    experiment_payload = {
        "project_id": project["project_id"],
        "name": f"breast_cancer_logreg_{timestamp}",
        "objective": "maximize AUC and accuracy",
    }
    experiment = api_request(
        "POST", base_url, "/api/experiments", token, json=experiment_payload
    )

    started_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    run_payload = {
        "experiment_id": experiment["experiment_id"],
        "dataset_version_id": dataset_version["dataset_version_id"],
        "run_name": f"logreg_{timestamp}",
        "status": "running",
        "started_at": started_at,
        "git_commit": "demo",
        "notes": "sklearn demo run",
        "config": {
            "params_json": {
                "model": "LogisticRegression",
                "max_iter": 1000,
                "test_size": 0.2,
                "random_state": 42,
            },
            "env_json": {
                "python": sys.version.split()[0],
                "sklearn": sklearn.__version__,
            },
            "command_line": "python scripts/demo_sklearn_experiment.py",
            "seed": 42,
        },
    }
    run = api_request("POST", base_url, "/api/runs", token, json=run_payload)

    step_metrics = []
    for step, factor in enumerate([0.6, 0.8, 1.0], start=1):
        step_metrics.append(
            {
                "metric_key": "accuracy",
                "scope": "train",
                "step": step,
                "value": round(metrics["accuracy"] * factor, 6),
            }
        )
        step_metrics.append(
            {
                "metric_key": "val_loss",
                "scope": "val",
                "step": step,
                "value": round(metrics["val_loss"] * (1.2 - 0.1 * step), 6),
            }
        )

    api_request(
        "POST",
        base_url,
        f"/api/runs/{run['run_id']}/metrics",
        token,
        json=step_metrics,
    )

    final_metrics = [
        {"metric_key": "accuracy", "scope": "val", "value": round(metrics["accuracy"], 6)},
        {"metric_key": "f1", "scope": "val", "value": round(metrics["f1"], 6)},
        {"metric_key": "auc", "scope": "val", "value": round(metrics["auc"], 6)},
        {"metric_key": "val_loss", "scope": "val", "value": round(metrics["val_loss"], 6)},
    ]
    api_request(
        "POST",
        base_url,
        f"/api/runs/{run['run_id']}/complete",
        token,
        json={"status": "finished", "final_metrics": final_metrics},
    )

    with model_path.open("wb") as handle:
        pickle.dump(model, handle)

    artifact_payload = {
        "project_id": project["project_id"],
        "artifact_type": "model",
        "uri": model_path.as_uri(),
        "checksum": sha256_file(model_path),
        "size_bytes": model_path.stat().st_size,
    }
    artifact = api_request("POST", base_url, "/api/artifacts", token, json=artifact_payload)

    run_artifact_payload = {
        "run_id": run["run_id"],
        "artifact_id": artifact["artifact_id"],
        "alias": "model",
    }
    api_request("POST", base_url, "/api/run-artifacts", token, json=run_artifact_payload)

    leaderboard = api_request(
        "GET",
        base_url,
        f"/api/reports/experiments/{experiment['experiment_id']}/leaderboard"
        "?metric_key=accuracy&scope=val&limit=3",
        token,
    )

    dashboard = api_request(
        "GET",
        base_url,
        f"/api/reports/projects/{project['project_id']}/dashboard",
        token,
    )

    audit_logs = api_request(
        "GET",
        base_url,
        "/api/audit-log?limit=5",
        token,
    )

    print("Created project:", project["project_id"], project["name"])
    print("Created experiment:", experiment["experiment_id"])
    print("Created run:", run["run_id"])
    print("Metrics:", {k: round(v, 4) for k, v in metrics.items()})
    print("Leaderboard:", leaderboard)
    print("Dashboard:", dashboard)
    print("Audit log sample:", audit_logs)


if __name__ == "__main__":
    main()
