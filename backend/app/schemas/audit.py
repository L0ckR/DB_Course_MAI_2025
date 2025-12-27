import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class AuditLogCreate(BaseModel):
    table_name: str
    operation: str
    row_pk: str
    changed_by: uuid.UUID | None = None
    old_data: dict | None = None
    new_data: dict | None = None


class AuditLogUpdate(BaseModel):
    table_name: str | None = None
    operation: str | None = None
    row_pk: str | None = None
    changed_by: uuid.UUID | None = None
    old_data: dict | None = None
    new_data: dict | None = None


class AuditLogRead(ORMBase):
    audit_id: int
    table_name: str
    operation: str
    row_pk: str
    changed_by: uuid.UUID | None
    changed_at: datetime
    old_data: dict | None
    new_data: dict | None
