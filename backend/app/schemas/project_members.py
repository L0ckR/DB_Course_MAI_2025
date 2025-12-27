import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import ProjectMemberRole


class ProjectMemberCreate(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectMemberRole
    is_active: bool = True
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "b7c5f1b2-6f2c-4b58-9c19-2c8d9a7b3c11",
                "user_id": "9c5a9b8f-1b2a-4f9a-8b21-4f3c0d1e2f34",
                "role": "editor",
                "is_active": True,
            }
        }
    )


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole | None = None
    is_active: bool | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "viewer",
                "is_active": True,
            }
        }
    )


class ProjectMemberRead(ORMBase):
    project_member_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectMemberRole
    added_at: datetime
    is_active: bool
