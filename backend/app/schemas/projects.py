import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class ProjectCreate(BaseModel):
    org_id: uuid.UUID
    name: str
    description: str | None = None
    status: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectRead(ORMBase):
    project_id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
