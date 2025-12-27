import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    is_active: bool = True
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "User Example",
                "password": "demo123",
                "is_active": True,
            }
        }
    )


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Updated User",
                "password": "newpass123",
                "is_active": False,
            }
        }
    )


class UserRead(ORMBase):
    user_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
