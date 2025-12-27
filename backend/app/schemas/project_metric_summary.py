import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.base import ORMBase
from app.schemas.enums import MetricScope


class ProjectMetricSummaryCreate(BaseModel):
    project_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    best_value: float | None = None
    best_run_id: uuid.UUID | None = None
    sample_size: int | None = None


class ProjectMetricSummaryUpdate(BaseModel):
    best_value: float | None = None
    best_run_id: uuid.UUID | None = None
    sample_size: int | None = None


class ProjectMetricSummaryRead(ORMBase):
    project_id: uuid.UUID
    metric_id: uuid.UUID
    scope: MetricScope
    best_value: float | None
    best_run_id: uuid.UUID | None
    updated_at: datetime
    sample_size: int | None
