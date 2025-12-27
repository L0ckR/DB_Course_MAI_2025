import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class RunConfigCreateDirect(BaseModel):
    run_id: uuid.UUID
    params_json: dict
    env_json: dict | None = None
    command_line: str | None = None
    seed: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c",
                "params_json": {"lr": 0.001, "batch_size": 32},
                "env_json": {"python": "3.12", "cuda": "12.2"},
                "command_line": "python train.py --lr 0.001",
                "seed": 42,
            }
        }
    )


class RunConfigUpdate(BaseModel):
    params_json: dict | None = None
    env_json: dict | None = None
    command_line: str | None = None
    seed: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "params_json": {"lr": 0.0005, "batch_size": 64},
                "command_line": "python train.py --lr 0.0005",
                "seed": 7,
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
