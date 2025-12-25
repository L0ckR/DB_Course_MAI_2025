import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class RunConfigCreate(BaseModel):
    params_json: dict
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


class RunCreate(BaseModel):
    experiment_id: uuid.UUID
    dataset_version_id: uuid.UUID
    run_name: str | None = None
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_by: uuid.UUID | None = None
    git_commit: str | None = None
    notes: str | None = None
    config: RunConfigCreate


class RunUpdate(BaseModel):
    dataset_version_id: uuid.UUID | None = None
    run_name: str | None = None
    status: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    git_commit: str | None = None
    notes: str | None = None


class RunRead(ORMBase):
    run_id: uuid.UUID
    experiment_id: uuid.UUID
    dataset_version_id: uuid.UUID
    run_name: str | None
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_by: uuid.UUID | None
    git_commit: str | None
    notes: str | None
