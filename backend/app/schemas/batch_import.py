import uuid
from datetime import datetime

from app.schemas.base import ORMBase


class BatchImportJobRead(ORMBase):
    job_id: uuid.UUID
    job_type: str
    status: str
    source_format: str
    source_uri: str
    started_at: datetime | None
    finished_at: datetime | None
    created_by: uuid.UUID | None
    stats_json: dict | None
