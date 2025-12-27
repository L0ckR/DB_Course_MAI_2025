import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import MetricGoal, MetricScope, RunStatus


class MetricDefinitionCreate(BaseModel):
    key: str
    display_name: str
    unit: str | None = None
    goal: MetricGoal


class MetricDefinitionUpdate(BaseModel):
    display_name: str | None = None
    unit: str | None = None
    goal: MetricGoal | None = None


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
