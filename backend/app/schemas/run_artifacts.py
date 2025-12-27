import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class RunArtifactCreate(BaseModel):
    run_id: uuid.UUID
    artifact_id: uuid.UUID
    alias: str | None = None


class RunArtifactUpdate(BaseModel):
    alias: str | None = None


class RunArtifactRead(ORMBase):
    run_artifact_id: uuid.UUID
    run_id: uuid.UUID
    artifact_id: uuid.UUID
    alias: str | None
    created_at: datetime
