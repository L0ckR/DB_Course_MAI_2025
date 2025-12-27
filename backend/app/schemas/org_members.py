import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import OrgMemberRole


class OrgMemberCreate(BaseModel):
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgMemberRole
    is_active: bool = True
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "org_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "user_id": "9c5a9b8f-1b2a-4f9a-8b21-4f3c0d1e2f34",
                "role": "admin",
                "is_active": True,
            }
        }
    )


class OrgMemberUpdate(BaseModel):
    role: OrgMemberRole | None = None
    is_active: bool | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "member",
                "is_active": True,
            }
        }
    )


class OrgMemberRead(ORMBase):
    org_member_id: uuid.UUID
    org_id: uuid.UUID
    user_id: uuid.UUID
    role: OrgMemberRole
    joined_at: datetime
    is_active: bool
