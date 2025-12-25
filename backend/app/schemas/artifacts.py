import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class ArtifactCreate(BaseModel):
    project_id: uuid.UUID
    artifact_type: str
    uri: str
    checksum: str | None = None
    size_bytes: int | None = None


class ArtifactUpdate(BaseModel):
    artifact_type: str | None = None
    uri: str | None = None
    checksum: str | None = None
    size_bytes: int | None = None


class ArtifactRead(ORMBase):
    artifact_id: uuid.UUID
    project_id: uuid.UUID
    artifact_type: str
    uri: str
    checksum: str | None
    size_bytes: int | None
    created_at: datetime
