import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class AuthRegister(BaseModel):
    email: str
    full_name: str
    password: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "User Example",
                "password": "demo123",
            }
        }
    )


class AuthLogin(BaseModel):
    email: str
    password: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "demo123",
            }
        }
    )


class AuthSession(ORMBase):
    user_id: uuid.UUID
    email: str
    full_name: str
    access_token: str
    token_type: str


class Token(BaseModel):
    access_token: str
    token_type: str
