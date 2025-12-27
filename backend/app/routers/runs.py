import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import insert, or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import (
    Dataset,
    DatasetVersion,
    Experiment,
    MetricDefinition,
    MLProject,
    OrgMember,
    ProjectMember,
    Run,
    RunConfig,
    RunMetricValue,
    User,
)
from app.schemas.metrics import RunCompleteRequest, RunMetricValueCreate, RunMetricValueRead
from app.schemas.runs import RunCreate, RunRead, RunUpdate

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(
    run_in: RunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Run:
    experiment = db.get(Experiment, run_in.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    dataset_version = db.get(DatasetVersion, run_in.dataset_version_id)
    if not dataset_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    dataset = db.get(Dataset, dataset_version.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    if experiment.project_id != dataset.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dataset version belongs to a different project",
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    if run_in.created_by and run_in.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="created_by must match the authenticated user",
        )
    run_data = run_in.model_dump(exclude={"config"})
    run = Run(**run_data, created_by=run_in.created_by or current_user.user_id)
    db.add(run)
    db.flush()
    config = RunConfig(run_id=run.run_id, **run_in.config.model_dump())
    db.add(config)
    db.commit()
    db.refresh(run)
    return run


@router.get("", response_model=list[RunRead])
def list_runs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Run]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    runs = db.scalars(
        select(Run)
        .join(Experiment, Experiment.experiment_id == Run.experiment_id)
        .join(MLProject, MLProject.project_id == Experiment.project_id)
        .where(
            or_(
                Experiment.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return runs


@router.get("/{run_id}", response_model=RunRead)
def get_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    return run


@router.put("/{run_id}", response_model=RunRead)
def update_run(
    run_id: uuid.UUID,
    run_in: RunUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    for key, value in run_in.model_dump(exclude_unset=True).items():
        setattr(run, key, value)
    db.commit()
    db.refresh(run)
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    db.delete(run)
    db.commit()
    return None


@router.post("/{run_id}/metrics", response_model=list[RunMetricValueRead])
def add_run_metrics(
    run_id: uuid.UUID,
    metrics: list[RunMetricValueCreate] = Body(
        ...,
        example=[
            {
                "metric_key": "accuracy",
                "scope": "val",
                "step": 1,
                "value": 0.92,
            },
            {
                "metric_key": "loss",
                "scope": "train",
                "step": 1,
                "value": 0.45,
            },
        ],
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunMetricValue]:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")

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
    metric_key: str | None = Query(None, example="accuracy"),
    scope: str | None = Query(None, example="val"),
    from_step: int | None = Query(None, ge=0, example=0),
    to_step: int | None = Query(None, ge=0, example=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunMetricValue]:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")

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
    run_id: uuid.UUID,
    payload: RunCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")

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
        add_run_metrics(run_id=run_id, metrics=metrics, db=db, current_user=current_user)
    else:
        db.commit()

    db.refresh(run)
    return run
