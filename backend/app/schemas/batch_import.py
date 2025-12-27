import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import BatchJobStatus, BatchJobType, SourceFormat


class BatchImportJobCreate(BaseModel):
    job_type: BatchJobType
    status: BatchJobStatus
    source_format: SourceFormat
    source_uri: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_by: uuid.UUID | None = None
    stats_json: dict | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "job_type": "metrics",
                "status": "created",
                "source_format": "csv",
                "source_uri": "uploads/metrics.csv",
                "stats_json": {"rows": 100, "inserted": 0, "errors": 0},
            }
        }
    )


class BatchImportJobUpdate(BaseModel):
    status: BatchJobStatus | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stats_json: dict | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "finished",
                "finished_at": "2025-01-01T11:00:00Z",
                "stats_json": {"rows": 100, "inserted": 95, "errors": 5},
            }
        }
    )


class BatchImportJobRead(ORMBase):
    job_id: uuid.UUID
    job_type: BatchJobType
    status: BatchJobStatus
    source_format: SourceFormat
    source_uri: str
    started_at: datetime | None
    finished_at: datetime | None
    created_by: uuid.UUID | None
    stats_json: dict | None
