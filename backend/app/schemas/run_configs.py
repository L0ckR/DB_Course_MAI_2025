import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class RunConfigCreateDirect(BaseModel):
    run_id: uuid.UUID
    params_json: dict
    env_json: dict | None = None
    command_line: str | None = None
    seed: int | None = None


class RunConfigUpdate(BaseModel):
    params_json: dict | None = None
    env_json: dict | None = None
    command_line: str | None = None
    seed: int | None = None


class RunConfigRead(ORMBase):
    run_id: uuid.UUID
    params_json: dict
    env_json: dict | None
    command_line: str | None
    seed: int | None
    created_at: datetime
