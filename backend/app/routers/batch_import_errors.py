import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import BatchImportError, BatchImportJob, User
from app.schemas.batch_import_errors import (
    BatchImportErrorCreate,
    BatchImportErrorRead,
    BatchImportErrorUpdate,
)

router = APIRouter(prefix="/batch-import-errors", tags=["batch-import-errors"])


@router.post("", response_model=BatchImportErrorRead, status_code=status.HTTP_201_CREATED)
def create_batch_import_error(
    payload: BatchImportErrorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportError:
    job = db.get(BatchImportJob, payload.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
        )
    if job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    error = BatchImportError(**payload.model_dump())
    db.add(error)
    db.commit()
    db.refresh(error)
    return error


@router.get("", response_model=list[BatchImportErrorRead])
def list_batch_import_errors(
    job_id: uuid.UUID | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[BatchImportError]:
    query = select(BatchImportError).join(
        BatchImportJob, BatchImportJob.job_id == BatchImportError.job_id
    )
    query = query.where(BatchImportJob.created_by == current_user.user_id)
    if job_id:
        job = db.get(BatchImportJob, job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found"
            )
        if job.created_by != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        query = query.where(BatchImportError.job_id == job_id)
    errors = db.scalars(
        query.order_by(BatchImportError.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return errors


@router.get("/{error_id}", response_model=BatchImportErrorRead)
def get_batch_import_error(
    error_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportError:
    error = db.get(BatchImportError, error_id)
    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import error not found"
        )
    job = db.get(BatchImportJob, error.job_id)
    if not job or job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return error


@router.put("/{error_id}", response_model=BatchImportErrorRead)
def update_batch_import_error(
    error_id: int,
    payload: BatchImportErrorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchImportError:
    error = db.get(BatchImportError, error_id)
    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import error not found"
        )
    job = db.get(BatchImportJob, error.job_id)
    if not job or job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(error, key, value)
    db.commit()
    db.refresh(error)
    return error


@router.delete("/{error_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_batch_import_error(
    error_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    error = db.get(BatchImportError, error_id)
    if not error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Import error not found"
        )
    job = db.get(BatchImportJob, error.job_id)
    if not job or job.created_by != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    db.delete(error)
    db.commit()
    return None
