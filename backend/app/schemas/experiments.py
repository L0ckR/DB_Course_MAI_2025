import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase


class ExperimentCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    objective: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "b7c5f1b2-6f2c-4b58-9c19-2c8d9a7b3c11",
                "name": "resnet50_baseline",
                "objective": "maximize accuracy",
            }
        }
    )


class ExperimentUpdate(BaseModel):
    name: str | None = None
    objective: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "resnet50_tuned",
                "objective": "maximize accuracy on val",
            }
        }
    )


class ExperimentRead(ORMBase):
    experiment_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    objective: str | None
    created_by: uuid.UUID
    created_at: datetime
