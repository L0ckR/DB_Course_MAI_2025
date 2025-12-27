import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import MetricScope


class RunMetricValueCreate(BaseModel):
    run_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    step: int | None = None
    value: float
    recorded_at: datetime | None = None


class RunMetricValueUpdate(BaseModel):
    scope: MetricScope | None = None
    step: int | None = None
    value: float | None = None
    recorded_at: datetime | None = None


class RunMetricValueRead(ORMBase):
    run_metric_value_id: uuid.UUID
    run_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    step: int | None
    value: float
    recorded_at: datetime
