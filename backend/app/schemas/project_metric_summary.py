import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import MetricScope


class ProjectMetricSummaryCreate(BaseModel):
    project_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    best_value: float | None = None
    best_run_id: uuid.UUID | None = None
    sample_size: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "b7c5f1b2-6f2c-4b58-9c19-2c8d9a7b3c11",
                "metric_id": "c96b1d1f-1b40-4961-a49e-93d7429c33dd",
                "scope": "val",
                "best_value": 0.93,
                "best_run_id": "4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c",
                "sample_size": 100,
            }
        }
    )


class ProjectMetricSummaryUpdate(BaseModel):
    best_value: float | None = None
    best_run_id: uuid.UUID | None = None
    sample_size: int | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "best_value": 0.94,
                "best_run_id": "4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c",
                "sample_size": 120,
            }
        }
    )


class ProjectMetricSummaryRead(ORMBase):
    project_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    best_value: float | None
    best_run_id: uuid.UUID | None
    updated_at: datetime
    sample_size: int | None
