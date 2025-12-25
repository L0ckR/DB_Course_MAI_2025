import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import Experiment
from app.schemas.experiments import ExperimentCreate, ExperimentRead, ExperimentUpdate

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(
    experiment_in: ExperimentCreate, db: Session = Depends(get_db)
) -> Experiment:
    experiment = Experiment(**experiment_in.model_dump())
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.get("", response_model=list[ExperimentRead])
def list_experiments(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Experiment]:
    experiments = db.scalars(select(Experiment).limit(limit).offset(offset)).all()
    return experiments


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(
    experiment_id: uuid.UUID, db: Session = Depends(get_db)
) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    return experiment


@router.put("/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: uuid.UUID,
    experiment_in: ExperimentUpdate,
    db: Session = Depends(get_db),
) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    for key, value in experiment_in.model_dump(exclude_unset=True).items():
        setattr(experiment, key, value)
    db.commit()
    db.refresh(experiment)
    return experiment


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found"
        )
    db.delete(experiment)
    db.commit()
    return None
