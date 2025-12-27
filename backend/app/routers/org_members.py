import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_org_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import OrgMember, User
from app.schemas.org_members import OrgMemberCreate, OrgMemberRead, OrgMemberUpdate

router = APIRouter(prefix="/org-members", tags=["org-members"])


@router.post("", response_model=OrgMemberRead, status_code=status.HTTP_201_CREATED)
def create_org_member(
    member_in: OrgMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    require_org_role(db, current_user.user_id, member_in.org_id, "admin")
    member = OrgMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("", response_model=list[OrgMemberRead])
def list_org_members(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[OrgMember]:
    org_ids = (
        select(OrgMember.org_id)
        .where(
            OrgMember.user_id == current_user.user_id,
            OrgMember.is_active.is_(True),
        )
        .subquery()
    )
    members = db.scalars(
        select(OrgMember)
        .where(OrgMember.org_id.in_(select(org_ids.c.org_id)))
        .limit(limit)
        .offset(offset)
    ).all()
    return members


@router.get("/{org_member_id}", response_model=OrgMemberRead)
def get_org_member(
    org_member_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    member = db.get(OrgMember, org_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Org member not found"
        )
    require_org_role(db, current_user.user_id, member.org_id, "viewer")
    return member


@router.put("/{org_member_id}", response_model=OrgMemberRead)
def update_org_member(
    org_member_id: uuid.UUID,
    member_in: OrgMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OrgMember:
    member = db.get(OrgMember, org_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Org member not found"
        )
    require_org_role(db, current_user.user_id, member.org_id, "admin")
    for key, value in member_in.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{org_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_org_member(
    org_member_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    member = db.get(OrgMember, org_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Org member not found"
        )
    require_org_role(db, current_user.user_id, member.org_id, "admin")
    db.delete(member)
    db.commit()
    return None
