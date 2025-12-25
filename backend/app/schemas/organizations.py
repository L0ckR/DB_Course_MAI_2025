import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None
    created_by: uuid.UUID


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class OrganizationRead(ORMBase):
    org_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    created_by: uuid.UUID
