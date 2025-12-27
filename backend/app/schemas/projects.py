import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import ProjectStatus


class ProjectCreate(BaseModel):
    org_id: uuid.UUID
    name: str
    description: str | None = None
    status: ProjectStatus
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "Vision Models",
                "description": "Image classification experiments",
                "status": "active",
            }
        }
    )


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Vision Models v2",
                "description": "Updated description",
                "status": "archived",
            }
        }
    )


class ProjectRead(ORMBase):
    project_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
