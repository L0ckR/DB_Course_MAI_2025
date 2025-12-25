import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    is_active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    is_active: bool | None = None


class UserRead(ORMBase):
    user_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
