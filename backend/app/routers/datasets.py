import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import Dataset, MLProject, OrgMember, ProjectMember, User
from app.schemas.datasets import DatasetCreate, DatasetRead, DatasetUpdate

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    require_project_role(db, current_user.user_id, dataset_in.project_id, "editor")
    dataset = Dataset(**dataset_in.model_dump())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetRead])
def list_datasets(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Dataset]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    datasets = db.scalars(
        select(Dataset)
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
    return datasets


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    require_project_role(db, current_user.user_id, dataset.project_id, "viewer")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetRead)
def update_dataset(
    dataset_id: uuid.UUID,
    dataset_in: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    require_project_role(db, current_user.user_id, dataset.project_id, "editor")
    for key, value in dataset_in.model_dump(exclude_unset=True).items():
        setattr(dataset, key, value)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    require_project_role(db, current_user.user_id, dataset.project_id, "editor")
    db.delete(dataset)
    db.commit()
    return None
