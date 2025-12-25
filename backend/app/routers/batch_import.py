import csv
import io
import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import (
    BatchImportError,
    BatchImportJob,
    Dataset,
    MetricDefinition,
    RunMetricValue,
)
from app.schemas.batch_import import BatchImportJobRead

router = APIRouter(prefix="", tags=["batch-import"])


def _parse_uuid(value: str | None) -> uuid.UUID | None:
    if value in (None, ""):
        return None
    return uuid.UUID(str(value))


def _parse_int(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _parse_float(value: str | None) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _parse_datetime(value: str | None) -> datetime | None:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(value)


def _load_rows(source_format: str, content: io.TextIOBase) -> list[dict]:
    if source_format == "csv":
        reader = csv.DictReader(content)
        return list(reader)
    if source_format == "json":
        data = json.load(content)
        if isinstance(data, list):
            return data
        raise ValueError("JSON payload must be a list")
    raise ValueError("Unsupported source format")


@router.post("/batch-import", response_model=BatchImportJobRead)
def batch_import(
    job_type: str = Form(...),
    format: str = Form(...),
    source_uri: str | None = Form(None),
    created_by: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> BatchImportJob:
    if not file and not source_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file or source_uri is required",
        )

    allowed_job_types = {"metrics", "datasets"}
    if job_type not in allowed_job_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"job_type must be one of {sorted(allowed_job_types)}",
        )

    source_format = format.lower()
    if source_format not in {"csv", "json"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="format must be csv or json",
        )
    source_name = source_uri or (file.filename if file else "upload")
    created_by_uuid = _parse_uuid(created_by) if created_by else None

    job = BatchImportJob(
        job_type=job_type,
        status="created",
        source_format=source_format,
        source_uri=source_name,
        created_by=created_by_uuid,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job.status = "running"
    job.started_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    inserted = 0
    errors = 0

    try:
        if file:
            content = io.TextIOWrapper(file.file, encoding="utf-8")
        else:
            content = open(source_uri, "r", encoding="utf-8")

        with content:
            rows = _load_rows(source_format, content)
    except Exception as exc:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        job.stats_json = {"inserted": inserted, "errors": errors}
        db.add(
            BatchImportError(
                job_id=job.job_id,
                row_number=None,
                raw_row=None,
                error_message=str(exc),
            )
        )
        db.commit()
        return job

    metric_cache: dict[str, uuid.UUID] = {}

    for row_number, row in enumerate(rows, start=1):
        try:
            if job_type == "metrics":
                run_id = _parse_uuid(row.get("run_id"))
                metric_id = _parse_uuid(row.get("metric_id"))
                metric_key = row.get("metric_key")
                scope = row.get("scope")
                step = _parse_int(row.get("step"))
                value = _parse_float(row.get("value"))
                recorded_at = _parse_datetime(row.get("recorded_at"))

                if not run_id or not scope or value is None:
                    raise ValueError("run_id, scope, and value are required")

                if not metric_id:
                    if not metric_key:
                        raise ValueError("metric_id or metric_key is required")
                    if metric_key not in metric_cache:
                        metric = db.scalar(
                            select(MetricDefinition).where(
                                MetricDefinition.key == metric_key
                            )
                        )
                        if not metric:
                            raise ValueError(f"Unknown metric_key: {metric_key}")
                        metric_cache[metric_key] = metric.metric_id
                    metric_id = metric_cache[metric_key]

                data = {
                    "run_id": run_id,
                    "metric_id": metric_id,
                    "scope": scope,
                    "step": step,
                    "value": value,
                }
                if recorded_at:
                    data["recorded_at"] = recorded_at

                db.execute(insert(RunMetricValue), data)

            elif job_type == "datasets":
                project_id = _parse_uuid(row.get("project_id"))
                name = row.get("name")
                task_type = row.get("task_type")
                description = row.get("description")
                if not project_id or not name or not task_type:
                    raise ValueError("project_id, name, task_type are required")

                data = {
                    "project_id": project_id,
                    "name": name,
                    "task_type": task_type,
                    "description": description,
                }
                db.execute(insert(Dataset), data)
            else:
                raise ValueError(f"Unsupported job_type: {job_type}")

            db.commit()
            inserted += 1
        except Exception as exc:
            db.rollback()
            errors += 1
            db.add(
                BatchImportError(
                    job_id=job.job_id,
                    row_number=row_number,
                    raw_row=row,
                    error_message=str(exc),
                )
            )
            db.commit()

    job.status = "finished"
    job.finished_at = datetime.utcnow()
    job.stats_json = {"inserted": inserted, "errors": errors}
    db.commit()
    db.refresh(job)
    return job
