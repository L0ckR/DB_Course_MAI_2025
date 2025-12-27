import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import RunStatus


class RunConfigCreate(BaseModel):
    params_json: dict
    env_json: dict | None = None
    command_line: str | None = None
    seed: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "params_json": {"lr": 0.001, "batch_size": 32, "epochs": 10},
                "env_json": {"python": "3.12", "cuda": "12.2", "torch": "2.2.0"},
                "command_line": "python train.py --lr 0.001 --batch_size 32",
                "seed": 42,
            }
        }
    )


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
    status: RunStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_by: uuid.UUID | None = None
    git_commit: str | None = None
    notes: str | None = None
    config: RunConfigCreate
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "experiment_id": "2d2a2b2c-3d3e-4f4a-8b8c-9d9e0f0a0b0c",
                "dataset_version_id": "d5f6a1b2-3c4d-4e5f-9a0b-1c2d3e4f5a6b",
                "run_name": "run-001",
                "status": "running",
                "started_at": "2025-01-01T10:00:00Z",
                "git_commit": "abc123def",
                "notes": "initial baseline",
                "config": {
                    "params_json": {"lr": 0.001, "batch_size": 32, "epochs": 10},
                    "env_json": {"python": "3.12", "cuda": "12.2", "torch": "2.2.0"},
                    "command_line": "python train.py --lr 0.001 --batch_size 32",
                    "seed": 42,
                },
            }
        }
    )


class RunUpdate(BaseModel):
    dataset_version_id: uuid.UUID | None = None
    run_name: str | None = None
    status: RunStatus | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    git_commit: str | None = None
    notes: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "finished",
                "finished_at": "2025-01-01T10:30:00Z",
                "notes": "completed",
            }
        }
    )


class RunRead(ORMBase):
    run_id: uuid.UUID
    experiment_id: uuid.UUID
    dataset_version_id: uuid.UUID
    run_name: str | None
    status: RunStatus
    started_at: datetime | None
    finished_at: datetime | None
    created_by: uuid.UUID | None
    git_commit: str | None
    notes: str | None
