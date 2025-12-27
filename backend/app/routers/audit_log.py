from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import AuditLog
from app.schemas.audit import AuditLogCreate, AuditLogRead, AuditLogUpdate

router = APIRouter(
    prefix="/audit-log",
    tags=["audit-log"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=AuditLogRead, status_code=status.HTTP_201_CREATED)
def create_audit_log(
    payload: AuditLogCreate, db: Session = Depends(get_db)
) -> AuditLog:
    log = AuditLog(**payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[AuditLog]:
    logs = db.scalars(
        select(AuditLog).order_by(AuditLog.changed_at.desc()).limit(limit).offset(offset)
    ).all()
    return logs


@router.get("/{audit_id}", response_model=AuditLogRead)
def get_audit_log(audit_id: int, db: Session = Depends(get_db)) -> AuditLog:
    log = db.get(AuditLog, audit_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit record not found"
        )
    return log


@router.put("/{audit_id}", response_model=AuditLogRead)
def update_audit_log(
    audit_id: int, payload: AuditLogUpdate, db: Session = Depends(get_db)
) -> AuditLog:
    log = db.get(AuditLog, audit_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit record not found"
        )
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(log, key, value)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audit_log(audit_id: int, db: Session = Depends(get_db)) -> None:
    log = db.get(AuditLog, audit_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit record not found"
        )
    db.delete(log)
    db.commit()
    return None
