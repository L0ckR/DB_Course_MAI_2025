import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import ArtifactType


class ArtifactCreate(BaseModel):
    project_id: uuid.UUID
    artifact_type: ArtifactType
    uri: str
    checksum: str | None = None
    size_bytes: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "b7c5f1b2-6f2c-4b58-9c19-2c8d9a7b3c11",
                "artifact_type": "model",
                "uri": "s3://ml-artifacts/model.pt",
                "checksum": "sha256:abcdef123456",
                "size_bytes": 12345678,
            }
        }
    )


class ArtifactUpdate(BaseModel):
    artifact_type: ArtifactType | None = None
    uri: str | None = None
    checksum: str | None = None
    size_bytes: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "artifact_type": "report",
                "uri": "s3://ml-artifacts/report.pdf",
                "checksum": "sha256:fedcba654321",
                "size_bytes": 2048,
            }
        }
    )


class ArtifactRead(ORMBase):
    artifact_id: uuid.UUID
    project_id: uuid.UUID
    artifact_type: ArtifactType
    uri: str
    checksum: str | None
    size_bytes: int | None
    created_at: datetime
