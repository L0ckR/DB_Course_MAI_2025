import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class BatchImportErrorCreate(BaseModel):
    job_id: uuid.UUID
    row_number: int | None = None
    raw_row: dict | None = None
    error_message: str


class BatchImportErrorUpdate(BaseModel):
    row_number: int | None = None
    raw_row: dict | None = None
    error_message: str | None = None


class BatchImportErrorRead(ORMBase):
    error_id: int
    job_id: uuid.UUID
    row_number: int | None
    raw_row: dict | None
    error_message: str
    created_at: datetime
