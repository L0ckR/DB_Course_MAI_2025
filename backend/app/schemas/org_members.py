import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import OrgMemberRole


class OrgMemberCreate(BaseModel):
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgMemberRole
    is_active: bool = True


class OrgMemberUpdate(BaseModel):
    role: OrgMemberRole | None = None
    is_active: bool | None = None


class OrgMemberRead(ORMBase):
    org_member_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgMemberRole
    joined_at: datetime
    is_active: bool
