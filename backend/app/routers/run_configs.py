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
    RunConfig,
    User,
)
from app.schemas.run_configs import (
    RunConfigCreateDirect,
    RunConfigRead,
    RunConfigUpdate,
)

router = APIRouter(prefix="/run-configs", tags=["run-configs"])


@router.post("", response_model=RunConfigRead, status_code=status.HTTP_201_CREATED)
def create_run_config(
    config_in: RunConfigCreateDirect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunConfig:
    run = db.get(Run, config_in.run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run not found"
        )
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    config = RunConfig(**config_in.model_dump())
    db.add(config)
    db.commit()
    db.refresh(config)
    return config


@router.get("", response_model=list[RunConfigRead])
def list_run_configs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunConfig]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    configs = db.scalars(
        select(RunConfig)
        .join(Run, Run.run_id == RunConfig.run_id)
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
    return configs


@router.get("/{run_id}", response_model=RunConfigRead)
def get_run_config(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunConfig:
    config = db.get(RunConfig, run_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run config not found"
        )
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    return config


@router.put("/{run_id}", response_model=RunConfigRead)
def update_run_config(
    run_id: uuid.UUID,
    config_in: RunConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunConfig:
    config = db.get(RunConfig, run_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run config not found"
        )
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    for key, value in config_in.model_dump(exclude_unset=True).items():
        setattr(config, key, value)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run_config(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    config = db.get(RunConfig, run_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run config not found"
        )
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    db.delete(config)
    db.commit()
    return None
