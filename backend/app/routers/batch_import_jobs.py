import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import BatchImportJob, User
from app.schemas.batch_import import (
    BatchImportJobCreate,
    BatchImportJobRead,
    BatchImportJobUpdate,
)

router = APIRouter(prefix="/batch-import-jobs", tags=["batch-import-jobs"])


@router.post("", response_model=BatchImportJobRead, status_code=status.HTTP_201_CREATED)
def create_batch_import_job(
    payload: BatchImportJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportJob:
    job = BatchImportJob(**payload.model_dump(), created_by=current_user.user_id)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("", response_model=list[BatchImportJobRead])
def list_batch_import_jobs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BatchImportJob]:
    jobs = db.scalars(
        select(BatchImportJob)
        .where(BatchImportJob.created_by == current_user.user_id)
        .order_by(BatchImportJob.started_at.desc().nullslast())
        .limit(limit)
        .offset(offset)
    ).all()
    return jobs


@router.get("/{job_id}", response_model=BatchImportJobRead)
def get_batch_import_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportJob:
    job = db.get(BatchImportJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
    if job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return job


@router.put("/{job_id}", response_model=BatchImportJobRead)
def update_batch_import_job(
    job_id: uuid.UUID,
    payload: BatchImportJobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportJob:
    job = db.get(BatchImportJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
    if job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_import_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    job = db.get(BatchImportJob, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
    if job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    db.delete(job)
    db.commit()
    return None
