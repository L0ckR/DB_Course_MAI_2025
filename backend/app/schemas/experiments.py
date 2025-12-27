import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase


class ExperimentCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    objective: str | None = None


class ExperimentUpdate(BaseModel):
    name: str | None = None
    objective: str | None = None


class ExperimentRead(ORMBase):
    experiment_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    objective: str | None
    created_by: uuid.UUID
    created_at: datetime
