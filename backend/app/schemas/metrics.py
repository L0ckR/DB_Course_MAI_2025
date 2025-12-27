import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import ORMBase
from app.schemas.enums import MetricGoal, MetricScope, RunStatus


class MetricDefinitionCreate(BaseModel):
    key: str
    display_name: str
    unit: str | None = None
    goal: MetricGoal
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "key": "accuracy",
                "display_name": "Accuracy",
                "unit": "ratio",
                "goal": "max",
            }
        }
    )


class MetricDefinitionUpdate(BaseModel):
    display_name: str | None = None
    unit: str | None = None
    goal: MetricGoal | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "Validation Accuracy",
                "unit": "ratio",
                "goal": "max",
            }
        }
    )


class MetricDefinitionRead(ORMBase):
    metric_id: uuid.UUID
    key: str
    display_name: str
    unit: str | None
    goal: MetricGoal
    created_at: datetime


class RunMetricValueCreate(BaseModel):
    metric_id: uuid.UUID | None = None
    metric_key: str | None = None
    scope: MetricScope
    step: int | None = None
    value: float
    recorded_at: datetime | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "metric_key": "accuracy",
                "scope": "val",
                "step": 1,
                "value": 0.92,
                "recorded_at": "2025-01-01T10:05:00Z",
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


class RunCompleteRequest(BaseModel):
    status: RunStatus
    finished_at: datetime | None = None
    final_metrics: list[RunMetricValueCreate] | None = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "finished",
                "finished_at": "2025-01-01T10:30:00Z",
                "final_metrics": [
                    {
                        "metric_key": "accuracy",
                        "scope": "val",
                        "value": 0.93,
                    }
                ],
            }
        }
    )
