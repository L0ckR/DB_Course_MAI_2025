import uuid
from datetime import datetime

from pydantic import BaseModel

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


class BatchImportJobUpdate(BaseModel):
    status: BatchJobStatus | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    stats_json: dict | None = None


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
