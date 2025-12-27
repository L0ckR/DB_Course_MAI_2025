import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class AuditLogCreate(BaseModel):
    table_name: str
    operation: str
    row_pk: str
    changed_by: uuid.UUID | None = None
    old_data: dict | None = None
    new_data: dict | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "table_name": "runs",
                "operation": "I",
                "row_pk": "{\"run_id\":\"4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c\"}",
                "changed_by": "9c5a9b8f-1b2a-4f9a-8b21-4f3c0d1e2f34",
                "old_data": None,
                "new_data": {"status": "queued"},
            }
        }
    )


class AuditLogUpdate(BaseModel):
    table_name: str | None = None
    operation: str | None = None
    row_pk: str | None = None
    changed_by: uuid.UUID | None = None
    old_data: dict | None = None
    new_data: dict | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operation": "U",
                "new_data": {"status": "running"},
            }
        }
    )


class AuditLogRead(ORMBase):
    audit_id: int
    table_name: str
    operation: str
    row_pk: str
    changed_by: uuid.UUID | None
    changed_at: datetime
    old_data: dict | None
    new_data: dict | None
