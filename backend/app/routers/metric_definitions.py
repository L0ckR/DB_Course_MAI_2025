import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import MetricDefinition
from app.schemas.metrics import (
    MetricDefinitionCreate,
    MetricDefinitionRead,
    MetricDefinitionUpdate,
)

router = APIRouter(
    prefix="/metric-definitions",
    tags=["metric-definitions"],
    dependencies=[Depends(get_current_user)],
)


@router.post("", response_model=MetricDefinitionRead, status_code=status.HTTP_201_CREATED)
def create_metric_definition(
    metric_in: MetricDefinitionCreate, db: Session = Depends(get_db)
) -> MetricDefinition:
    metric = MetricDefinition(**metric_in.model_dump())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@router.get("", response_model=list[MetricDefinitionRead])
def list_metric_definitions(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[MetricDefinition]:
    metrics = db.scalars(select(MetricDefinition).limit(limit).offset(offset)).all()
    return metrics


@router.get("/{metric_id}", response_model=MetricDefinitionRead)
def get_metric_definition(
    metric_id: uuid.UUID, db: Session = Depends(get_db)
) -> MetricDefinition:
    metric = db.get(MetricDefinition, metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
    return metric


@router.put("/{metric_id}", response_model=MetricDefinitionRead)
def update_metric_definition(
    metric_id: uuid.UUID,
    metric_in: MetricDefinitionUpdate,
    db: Session = Depends(get_db),
) -> MetricDefinition:
    metric = db.get(MetricDefinition, metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
    for key, value in metric_in.model_dump(exclude_unset=True).items():
        setattr(metric, key, value)
    db.commit()
    db.refresh(metric)
    return metric


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric_definition(
    metric_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    metric = db.get(MetricDefinition, metric_id)
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
    db.delete(metric)
    db.commit()
    return None
