import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import Experiment, MLProject, OrgMember, ProjectMember, User
from app.schemas.experiments import ExperimentCreate, ExperimentRead, ExperimentUpdate

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(
    experiment_in: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Experiment:
    require_project_role(db, current_user.user_id, experiment_in.project_id, "editor")
    experiment = Experiment(
        **experiment_in.model_dump(),
        created_by=current_user.user_id,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.get("", response_model=list[ExperimentRead])
def list_experiments(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Experiment]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    experiments = db.scalars(
        select(Experiment)
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
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: uuid.UUID,
    experiment_in: ExperimentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    for key, value in experiment_in.model_dump(exclude_unset=True).items():
        setattr(experiment, key, value)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    require_project_role(db, current_user.user_id, experiment.project_id, "editor")
    db.delete(experiment)
    db.commit()
    return None
