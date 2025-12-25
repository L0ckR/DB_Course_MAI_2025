import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import Artifact
from app.schemas.artifacts import ArtifactCreate, ArtifactRead, ArtifactUpdate

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.post("", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_artifact(
    artifact_in: ArtifactCreate, db: Session = Depends(get_db)
) -> Artifact:
    artifact = Artifact(**artifact_in.model_dump())
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.get("", response_model=list[ArtifactRead])
def list_artifacts(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Artifact]:
    artifacts = db.scalars(select(Artifact).limit(limit).offset(offset)).all()
    return artifacts


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
    artifact_id: uuid.UUID, db: Session = Depends(get_db)
) -> Artifact:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    return artifact


@router.put("/{artifact_id}", response_model=ArtifactRead)
def update_artifact(
    artifact_id: uuid.UUID, artifact_in: ArtifactUpdate, db: Session = Depends(get_db)
) -> Artifact:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    for key, value in artifact_in.model_dump(exclude_unset=True).items():
        setattr(artifact, key, value)
    db.commit()
    db.refresh(artifact)
    return artifact


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_artifact(artifact_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    artifact = db.get(Artifact, artifact_id)
    if not artifact:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artifact not found")
    db.delete(artifact)
    db.commit()
    return None
