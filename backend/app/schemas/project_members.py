import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import ProjectMemberRole


class ProjectMemberCreate(BaseModel):
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectMemberRole
    is_active: bool = True


class ProjectMemberUpdate(BaseModel):
    role: ProjectMemberRole | None = None
    is_active: bool | None = None


class ProjectMemberRead(ORMBase):
    project_member_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectMemberRole
    added_at: datetime
    is_active: bool
