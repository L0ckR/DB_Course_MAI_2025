import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import DatasetVersion
from app.schemas.datasets import (
    DatasetVersionCreate,
    DatasetVersionRead,
    DatasetVersionUpdate,
)

router = APIRouter(prefix="/dataset-versions", tags=["dataset-versions"])


@router.post("", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def create_dataset_version(
    version_in: DatasetVersionCreate, db: Session = Depends(get_db)
) -> DatasetVersion:
    version = DatasetVersion(**version_in.model_dump())
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


@router.get("", response_model=list[DatasetVersionRead])
def list_dataset_versions(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[DatasetVersion]:
    versions = db.scalars(select(DatasetVersion).limit(limit).offset(offset)).all()
    return versions


@router.get("/{dataset_version_id}", response_model=DatasetVersionRead)
def get_dataset_version(
    dataset_version_id: uuid.UUID, db: Session = Depends(get_db)
) -> DatasetVersion:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    return version


@router.put("/{dataset_version_id}", response_model=DatasetVersionRead)
def update_dataset_version(
    dataset_version_id: uuid.UUID,
    version_in: DatasetVersionUpdate,
    db: Session = Depends(get_db),
) -> DatasetVersion:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    for key, value in version_in.model_dump(exclude_unset=True).items():
        setattr(version, key, value)
    db.commit()
    db.refresh(version)
    return version


@router.delete("/{dataset_version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset_version(
    dataset_version_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    version = db.get(DatasetVersion, dataset_version_id)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dataset version not found"
        )
    db.delete(version)
    db.commit()
    return None
