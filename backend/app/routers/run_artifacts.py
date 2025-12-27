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
    RunArtifact,
    User,
)
from app.schemas.run_artifacts import RunArtifactCreate, RunArtifactRead, RunArtifactUpdate

router = APIRouter(prefix="/run-artifacts", tags=["run-artifacts"])


@router.post("", response_model=RunArtifactRead, status_code=status.HTTP_201_CREATED)
def create_run_artifact(
    run_artifact_in: RunArtifactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunArtifact:
    run = db.get(Run, run_artifact_in.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    run_artifact = RunArtifact(**run_artifact_in.model_dump())
    db.add(run_artifact)
    db.commit()
    db.refresh(run_artifact)
    return run_artifact


@router.get("", response_model=list[RunArtifactRead])
def list_run_artifacts(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RunArtifact]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    artifacts = db.scalars(
        select(RunArtifact)
        .join(Run, Run.run_id == RunArtifact.run_id)
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
    return artifacts


@router.get("/{run_artifact_id}", response_model=RunArtifactRead)
def get_run_artifact(
    run_artifact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunArtifact:
    run_artifact = db.get(RunArtifact, run_artifact_id)
    if not run_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run artifact not found"
        )
    run = db.get(Run, run_artifact.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    return run_artifact


@router.put("/{run_artifact_id}", response_model=RunArtifactRead)
def update_run_artifact(
    run_artifact_id: uuid.UUID,
    run_artifact_in: RunArtifactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RunArtifact:
    run_artifact = db.get(RunArtifact, run_artifact_id)
    if not run_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run artifact not found"
        )
    run = db.get(Run, run_artifact.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    for key, value in run_artifact_in.model_dump(exclude_unset=True).items():
        setattr(run_artifact, key, value)
    db.commit()
    db.refresh(run_artifact)
    return run_artifact


@router.delete("/{run_artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run_artifact(
    run_artifact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    run_artifact = db.get(RunArtifact, run_artifact_id)
    if not run_artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Run artifact not found"
        )
    run = db.get(Run, run_artifact.run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    experiment = db.get(Experiment, run.experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    db.delete(run_artifact)
    db.commit()
    return None
