#!/usr/bin/env python3
import csv
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError as exc:
    raise SystemExit("Missing dependency: requests. Install with 'pip install requests'.") from exc


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


def create_org(base_url: str, token: str, suffix: str) -> dict:
    payload = {
        "name": f"batch-demo-org-{suffix}",
        "description": "Org for batch import demo",
    }
    return api_request("POST", base_url, "/api/orgs", token, json=payload)


def create_project(base_url: str, token: str, org_id: str, suffix: str) -> dict:
    payload = {
        "org_id": org_id,
        "name": f"batch-demo-project-{suffix}",
        "description": "Project for batch import demo",
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

    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    org = create_org(base_url, token, suffix)
    project = create_project(base_url, token, org["org_id"], suffix)

    rows = [
        {
            "project_id": project["project_id"],
            "name": f"batch_ok_{suffix}",
            "task_type": "classification",
            "description": "valid row",
        },
        {
            "project_id": project["project_id"],
            "name": f"batch_bad_{suffix}",
            "task_type": "",
            "description": "missing task_type",
        },
    ]

    with tempfile.NamedTemporaryFile("w", newline="", suffix=".csv", delete=False) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["project_id", "name", "task_type", "description"],
        )
        writer.writeheader()
        writer.writerows(rows)
        csv_path = Path(handle.name)

    with csv_path.open("rb") as file_handle:
        job = api_request(
            "POST",
            base_url,
            "/api/batch-import",
            token,
            data={
                "job_type": "datasets",
                "format": "csv",
                "source_uri": str(csv_path),
            },
            files={"file": (csv_path.name, file_handle, "text/csv")},
        )

    errors = api_request(
        "GET",
        base_url,
        f"/api/batch-import-errors?job_id={job['job_id']}",
        token,
    )

    print("Batch import job:", job)
    print("Batch import errors:", errors)


if __name__ == "__main__":
    main()
