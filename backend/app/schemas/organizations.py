import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class OrganizationCreate(BaseModel):
    name: str
    description: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "ML Research Org",
                "description": "Organization for ML experiments",
            }
        }
    )


class OrganizationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "ML Research Org",
                "description": "Updated description",
            }
        }
    )


class OrganizationRead(ORMBase):
    org_id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    created_by: uuid.UUID
