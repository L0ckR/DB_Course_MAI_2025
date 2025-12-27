import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import TaskType


class DatasetCreate(BaseModel):
    project_id: uuid.UUID
    name: str
    task_type: TaskType
    description: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "b7c5f1b2-6f2c-4b58-9c19-2c8d9a7b3c11",
                "name": "cifar10",
                "task_type": "classification",
                "description": "Image classification dataset",
            }
        }
    )


class DatasetUpdate(BaseModel):
    name: str | None = None
    task_type: TaskType | None = None
    description: str | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "cifar10_v2",
                "task_type": "classification",
                "description": "Updated dataset description",
            }
        }
    )


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
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": "e1c5f0c0-7f1b-4dd9-9cf0-2a5a0b1c2d3e",
                "version_label": "v1",
                "storage_uri": "s3://ml-data/cifar10/v1",
                "content_hash": "sha256:abcdef123456",
                "row_count": 60000,
                "size_bytes": 170000000,
                "schema_json": {"features": ["image"], "label": "class"},
            }
        }
    )


class DatasetVersionUpdate(BaseModel):
    version_label: str | None = None
    storage_uri: str | None = None
    content_hash: str | None = None
    row_count: int | None = None
    size_bytes: int | None = None
    schema_json: dict | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version_label": "v2",
                "storage_uri": "s3://ml-data/cifar10/v2",
                "content_hash": "sha256:fedcba654321",
                "row_count": 70000,
                "size_bytes": 190000000,
                "schema_json": {"features": ["image"], "label": "class"},
            }
        }
    )


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
