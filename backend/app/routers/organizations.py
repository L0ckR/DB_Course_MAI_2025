import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.models import Organization
from app.schemas.organizations import (
    OrganizationCreate,
    OrganizationRead,
    OrganizationUpdate,
)

router = APIRouter(prefix="/orgs", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
def create_org(
    org_in: OrganizationCreate, db: Session = Depends(get_db)
) -> Organization:
    org = Organization(**org_in.model_dump())
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


@router.get("", response_model=list[OrganizationRead])
def list_orgs(
    limit: int = 100, offset: int = 0, db: Session = Depends(get_db)
) -> list[Organization]:
    orgs = db.scalars(select(Organization).limit(limit).offset(offset)).all()
    return orgs


@router.get("/{org_id}", response_model=OrganizationRead)
def get_org(org_id: uuid.UUID, db: Session = Depends(get_db)) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    return org


@router.put("/{org_id}", response_model=OrganizationRead)
def update_org(
    org_id: uuid.UUID, org_in: OrganizationUpdate, db: Session = Depends(get_db)
) -> Organization:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    for key, value in org_in.model_dump(exclude_unset=True).items():
        setattr(org, key, value)
    db.commit()
    db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_org(org_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    org = db.get(Organization, org_id)
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Org not found")
    db.delete(org)
    db.commit()
    return None
