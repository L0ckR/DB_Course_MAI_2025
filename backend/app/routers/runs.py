import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import MetricDefinition, Run, RunConfig, RunMetricValue
from app.schemas.metrics import RunCompleteRequest, RunMetricValueCreate, RunMetricValueRead
from app.schemas.runs import RunCreate, RunRead, RunUpdate

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(run_in: RunCreate, db: Session = Depends(get_db)) -> Run:
    run_data = run_in.model_dump(exclude={"config"})
    run = Run(**run_data)
    db.add(run)
    db.flush()
    config = RunConfig(run_id=run.run_id, **run_in.config.model_dump())
    db.add(config)
    db.commit()
    db.refresh(run)
    return run


@router.get("", response_model=list[RunRead])
def list_runs(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Run]:
    runs = db.scalars(select(Run).limit(limit).offset(offset)).all()
    return runs


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: uuid.UUID, db: Session = Depends(get_db)) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.put("/{run_id}", response_model=RunRead)
def update_run(
    run_id: uuid.UUID, run_in: RunUpdate, db: Session = Depends(get_db)
) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    for key, value in run_in.model_dump(exclude_unset=True).items():
        setattr(run, key, value)
    db.commit()
    db.refresh(run)
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    db.delete(run)
    db.commit()
    return None


@router.post("/{run_id}/metrics", response_model=list[RunMetricValueRead])
def add_run_metrics(
    run_id: uuid.UUID, metrics: list[RunMetricValueCreate], db: Session = Depends(get_db)
) -> list[RunMetricValue]:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    metric_keys = {m.metric_key for m in metrics if m.metric_key}
    key_map: dict[str, uuid.UUID] = {}
    if metric_keys:
        metric_rows = db.scalars(
            select(MetricDefinition).where(MetricDefinition.key.in_(metric_keys))
        ).all()
        key_map = {row.key: row.metric_id for row in metric_rows}
        missing = metric_keys - set(key_map.keys())
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown metric keys: {sorted(missing)}",
            )

    values: list[dict] = []
    for item in metrics:
        metric_id = item.metric_id or key_map.get(item.metric_key or "")
        if not metric_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="metric_id or metric_key is required",
            )
        row = {
            "run_id": run_id,
            "metric_id": metric_id,
            "scope": item.scope,
            "step": item.step,
            "value": item.value,
        }
        if item.recorded_at is not None:
            row["recorded_at"] = item.recorded_at
        values.append(row)

    if values:
        db.execute(insert(RunMetricValue), values)
        db.commit()

    result = db.scalars(
        select(RunMetricValue).where(RunMetricValue.run_id == run_id)
    ).all()
    return result


@router.get("/{run_id}/metrics", response_model=list[RunMetricValueRead])
def get_run_metrics(
    run_id: uuid.UUID,
    metric_key: str | None = None,
    scope: str | None = None,
    from_step: int | None = Query(None, ge=0),
    to_step: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> list[RunMetricValue]:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    query = select(RunMetricValue).where(RunMetricValue.run_id == run_id)
    if metric_key:
        query = query.join(MetricDefinition).where(MetricDefinition.key == metric_key)
    if scope:
        query = query.where(RunMetricValue.scope == scope)
    if from_step is not None:
        query = query.where(RunMetricValue.step >= from_step)
    if to_step is not None:
        query = query.where(RunMetricValue.step <= to_step)

    return db.scalars(query).all()


@router.post("/{run_id}/complete", response_model=RunRead)
def complete_run(
    run_id: uuid.UUID, payload: RunCompleteRequest, db: Session = Depends(get_db)
) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")

    run.status = payload.status
    run.finished_at = payload.finished_at or datetime.utcnow()

    if payload.final_metrics:
        metrics = [
            RunMetricValueCreate(
                metric_id=item.metric_id,
                metric_key=item.metric_key,
                scope=item.scope,
                step=None,
                value=item.value,
                recorded_at=item.recorded_at,
            )
            for item in payload.final_metrics
        ]
        add_run_metrics(run_id=run_id, metrics=metrics, db=db)
    else:
        db.commit()

    db.refresh(run)
    return run
