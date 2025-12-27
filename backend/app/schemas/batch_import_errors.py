import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class BatchImportErrorCreate(BaseModel):
    job_id: uuid.UUID
    row_number: int | None = None
    raw_row: dict | None = None
    error_message: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_id": "6a7b8c9d-0e1f-4a2b-8c9d-0e1f2a3b4c5d",
                "row_number": 15,
                "raw_row": {"metric_key": "accuracy", "value": "bad"},
                "error_message": "invalid value",
            }
        }
    )


class BatchImportErrorUpdate(BaseModel):
    row_number: int | None = None
    raw_row: dict | None = None
    error_message: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "row_number": 15,
                "raw_row": {"metric_key": "accuracy", "value": "bad"},
                "error_message": "invalid value",
            }
        }
    )


class BatchImportErrorRead(ORMBase):
    error_id: int
    job_id: uuid.UUID
    row_number: int | None
    raw_row: dict | None
    error_message: str
    created_at: datetime
