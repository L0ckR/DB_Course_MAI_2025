import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import Dataset
from app.schemas.datasets import DatasetCreate, DatasetRead, DatasetUpdate

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: DatasetCreate, db: Session = Depends(get_db)
) -> Dataset:
    dataset = Dataset(**dataset_in.model_dump())
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=list[DatasetRead])
def list_datasets(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Dataset]:
    datasets = db.scalars(select(Dataset).limit(limit).offset(offset)).all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset


@router.put("/{dataset_id}", response_model=DatasetRead)
def update_dataset(
    dataset_id: uuid.UUID, dataset_in: DatasetUpdate, db: Session = Depends(get_db)
) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    for key, value in dataset_in.model_dump(exclude_unset=True).items():
        setattr(dataset, key, value)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    db.delete(dataset)
    db.commit()
    return None
