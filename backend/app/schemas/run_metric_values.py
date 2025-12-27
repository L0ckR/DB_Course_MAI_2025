import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import MetricScope


class RunMetricValueCreate(BaseModel):
    run_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    step: int | None = None
    value: float
    recorded_at: datetime | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "run_id": "4f5a6b7c-8d9e-4f0a-9b1c-2d3e4f5a6b7c",
                "metric_id": "c96b1d1f-1b40-4961-a49e-93d7429c33dd",
                "scope": "val",
                "step": 5,
                "value": 0.91,
                "recorded_at": "2025-01-01T10:10:00Z",
            }
        }
    )


class RunMetricValueUpdate(BaseModel):
    scope: MetricScope | None = None
    step: int | None = None
    value: float | None = None
    recorded_at: datetime | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scope": "test",
                "step": 10,
                "value": 0.94,
                "recorded_at": "2025-01-01T10:20:00Z",
            }
        }
    )


class RunMetricValueRead(ORMBase):
    run_metric_value_id: uuid.UUID
    run_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    step: int | None
    value: float
    recorded_at: datetime
