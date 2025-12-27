import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import (
    Experiment,
    MLProject,
    OrgMember,
    ProjectMember,
    Run,
    RunMetricValue,
    User,
)
from app.schemas.run_metric_values import (
    RunMetricValueCreate,
    RunMetricValueRead,
    RunMetricValueUpdate,
)

router = APIRouter(prefix="/run-metric-values", tags=["run-metric-values"])


@router.post("", response_model=RunMetricValueRead, status_code=status.HTTP_201_CREATED)
def create_run_metric_value(
    value_in: RunMetricValueCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunMetricValue:
    run = db.get(Run, value_in.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    payload = value_in.model_dump(exclude_unset=True)
    value = RunMetricValue(**payload)
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


@router.get("", response_model=list[RunMetricValueRead])
def list_run_metric_values(
    run_id: uuid.UUID | None = None,
    metric_id: uuid.UUID | None = None,
    scope: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunMetricValue]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    query = (
        select(RunMetricValue)
        .join(Run, Run.run_id == RunMetricValue.run_id)
        .join(Experiment, Experiment.experiment_id == Run.experiment_id)
        .join(MLProject, MLProject.project_id == Experiment.project_id)
        .where(
            or_(
                Experiment.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
    )
    if run_id:
        query = query.where(RunMetricValue.run_id == run_id)
    if metric_id:
        query = query.where(RunMetricValue.metric_id == metric_id)
    if scope:
        query = query.where(RunMetricValue.scope == scope)

    values = db.scalars(query.limit(limit).offset(offset)).all()
    return values


@router.get("/{run_metric_value_id}", response_model=RunMetricValueRead)
def get_run_metric_value(
    run_metric_value_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunMetricValue:
    value = db.get(RunMetricValue, run_metric_value_id)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run metric value not found"
        )
    run = db.get(Run, value.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    return value


@router.put("/{run_metric_value_id}", response_model=RunMetricValueRead)
def update_run_metric_value(
    run_metric_value_id: uuid.UUID,
    value_in: RunMetricValueUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunMetricValue:
    value = db.get(RunMetricValue, run_metric_value_id)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run metric value not found"
        )
    run = db.get(Run, value.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    for key, field_value in value_in.model_dump(exclude_unset=True).items():
        setattr(value, key, field_value)
    db.commit()
    db.refresh(value)
    return value


@router.delete("/{run_metric_value_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run_metric_value(
    run_metric_value_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    value = db.get(RunMetricValue, run_metric_value_id)
    if not value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run metric value not found"
        )
    run = db.get(Run, value.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    db.delete(value)
    db.commit()
    return None
