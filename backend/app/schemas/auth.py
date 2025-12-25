import uuid

from pydantic import BaseModel

from app.schemas.base import ORMBase


class AuthRegister(BaseModel):
    email: str
    full_name: str
    password: str


class AuthLogin(BaseModel):
    email: str
    password: str


class AuthSession(ORMBase):
    user_id: uuid.UUID
    email: str
    full_name: str
