import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class RunArtifactCreate(BaseModel):
    run_id: uuid.UUID
    artifact_id: uuid.UUID
    alias: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c",
                "artifact_id": "8f6e2a1b-3c4d-4e5f-9a0b-7c6d5e4f3a2b",
                "alias": "best_model",
            }
        }
    )


class RunArtifactUpdate(BaseModel):
    alias: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alias": "confusion_matrix",
            }
        }
    )


class RunArtifactRead(ORMBase):
    run_artifact_id: uuid.UUID
    run_id: uuid.UUID
    artifact_id: uuid.UUID
    alias: str | None
    created_at: datetime
