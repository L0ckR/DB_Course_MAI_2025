import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import Artifact, MLProject, OrgMember, ProjectMember, User
from app.schemas.artifacts import ArtifactCreate, ArtifactRead, ArtifactUpdate

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact(
    artifact_in: ArtifactCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Artifact:
    require_project_role(db, current_user.user_id, artifact_in.project_id, "editor")
    artifact = Artifact(**artifact_in.model_dump())
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.get("", response_model=list[ArtifactRead])
def list_artifacts(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Artifact]:
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
        select(Artifact)
        .join(MLProject, MLProject.project_id == Artifact.project_id)
        .where(
            or_(
                Artifact.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return artifacts


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Artifact:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    require_project_role(db, current_user.user_id, artifact.project_id, "viewer")
    return artifact


@router.put("/{artifact_id}", response_model=ArtifactRead)
def update_artifact(
    artifact_id: uuid.UUID,
    artifact_in: ArtifactUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Artifact:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    require_project_role(db, current_user.user_id, artifact.project_id, "editor")
    for key, value in artifact_in.model_dump(exclude_unset=True).items():
        setattr(artifact, key, value)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(
    artifact_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    require_project_role(db, current_user.user_id, artifact.project_id, "editor")
    db.delete(artifact)
    db.commit()
    return None
