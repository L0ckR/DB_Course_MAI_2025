import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import ProjectStatus


class ProjectCreate(BaseModel):
    org_id: uuid.UUID
    name: str
    description: str | None = None
    status: ProjectStatus


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectRead(ORMBase):
    project_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    created_at: datetime
