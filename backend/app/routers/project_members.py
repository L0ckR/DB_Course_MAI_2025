import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import ProjectMember, User
from app.schemas.project_members import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate,
)

router = APIRouter(prefix="/project-members", tags=["project-members"])


@router.post("", response_model=ProjectMemberRead, status_code=status.HTTP_201_CREATED)
def create_project_member(
    member_in: ProjectMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    require_project_role(db, current_user.user_id, member_in.project_id, "admin")
    member = ProjectMember(**member_in.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


@router.get("", response_model=list[ProjectMemberRead])
def list_project_members(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectMember]:
    project_ids = (
        select(ProjectMember.project_id)
        .where(
            ProjectMember.user_id == current_user.user_id,
            ProjectMember.is_active.is_(True),
        )
        .subquery()
    )
    members = db.scalars(
        select(ProjectMember)
        .where(ProjectMember.project_id.in_(select(project_ids.c.project_id)))
        .limit(limit)
        .offset(offset)
    ).all()
    return members


@router.get("/{project_member_id}", response_model=ProjectMemberRead)
def get_project_member(
    project_member_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    member = db.get(ProjectMember, project_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    require_project_role(db, current_user.user_id, member.project_id, "viewer")
    return member


@router.put("/{project_member_id}", response_model=ProjectMemberRead)
def update_project_member(
    project_member_id: uuid.UUID,
    member_in: ProjectMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    member = db.get(ProjectMember, project_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    require_project_role(db, current_user.user_id, member.project_id, "admin")
    for key, value in member_in.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    db.commit()
    db.refresh(member)
    return member


@router.delete("/{project_member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_member(
    project_member_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    member = db.get(ProjectMember, project_member_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project member not found"
        )
    require_project_role(db, current_user.user_id, member.project_id, "admin")
    db.delete(member)
    db.commit()
    return None
