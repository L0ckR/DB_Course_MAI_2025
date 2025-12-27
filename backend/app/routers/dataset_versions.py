import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import Dataset, DatasetVersion, MLProject, OrgMember, ProjectMember, User
from app.schemas.datasets import (
    DatasetVersionCreate,
    DatasetVersionRead,
    DatasetVersionUpdate,
)

router = APIRouter(prefix="/dataset-versions", tags=["dataset-versions"])


@router.post("", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def create_dataset_version(
    version_in: DatasetVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetVersion:
    dataset = db.get(Dataset, version_in.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    require_project_role(db, current_user.user_id, dataset.project_id, "editor")
    version = DatasetVersion(**version_in.model_dump())
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("", response_model=list[DatasetVersionRead])
def list_dataset_versions(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DatasetVersion]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    versions = db.scalars(
        select(DatasetVersion)
        .join(Dataset, Dataset.dataset_id == DatasetVersion.dataset_id)
        .join(MLProject, MLProject.project_id == Dataset.project_id)
        .where(
            or_(
                Dataset.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return versions


@router.get("/{dataset_version_id}", response_model=DatasetVersionRead)
def get_dataset_version(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetVersion:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    dataset = db.get(Dataset, version.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    require_project_role(db, current_user.user_id, dataset.project_id, "viewer")
    return version


@router.put("/{dataset_version_id}", response_model=DatasetVersionRead)
def update_dataset_version(
    dataset_version_id: uuid.UUID,
    version_in: DatasetVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DatasetVersion:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    dataset = db.get(Dataset, version.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    require_project_role(db, current_user.user_id, dataset.project_id, "editor")
    for key, value in version_in.model_dump(exclude_unset=True).items():
        setattr(version, key, value)
    db.commit()
    db.refresh(version)
    return version


@router.delete("/{dataset_version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset_version(
    dataset_version_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    dataset = db.get(Dataset, version.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found"
        )
    require_project_role(db, current_user.user_id, dataset.project_id, "editor")
    db.delete(version)
    db.commit()
    return None
