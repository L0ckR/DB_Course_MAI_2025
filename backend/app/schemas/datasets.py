import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import TaskType


class DatasetCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    task_type: TaskType
    description: str | None = None


class DatasetUpdate(BaseModel):
    name: str | None = None
    task_type: TaskType | None = None
    description: str | None = None


class DatasetRead(ORMBase):
    dataset_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    task_type: TaskType
    description: str | None
    created_at: datetime


class DatasetVersionCreate(BaseModel):
    dataset_id: uuid.UUID
    version_label: str
    storage_uri: str
    content_hash: str
    row_count: int | None = None
    size_bytes: int | None = None
    schema_json: dict | None = None


class DatasetVersionUpdate(BaseModel):
    version_label: str | None = None
    storage_uri: str | None = None
    content_hash: str | None = None
    row_count: int | None = None
    size_bytes: int | None = None
    schema_json: dict | None = None


class DatasetVersionRead(ORMBase):
    dataset_version_id: uuid.UUID
    dataset_id: uuid.UUID
    version_label: str
    storage_uri: str
    content_hash: str
    row_count: int | None
    size_bytes: int | None
    schema_json: dict | None
    created_at: datetime
