import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import MLProject, OrgMember, ProjectMember

ORG_ROLE_RANK = {
    "viewer": 0,
    "member": 1,
    "admin": 2,
    "owner": 3,
}

PROJECT_ROLE_RANK = {
    "viewer": 0,
    "editor": 1,
    "admin": 2,
}


def _has_role(current_role: str, required_role: str, rank: dict[str, int]) -> bool:
    return rank.get(current_role, -1) >= rank.get(required_role, 0)


def require_org_role(
    db: Session, user_id: uuid.UUID, org_id: uuid.UUID, required_role: str
) -> OrgMember:
    member = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == org_id,
            OrgMember.user_id == user_id,
            OrgMember.is_active.is_(True),
        )
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Org access denied",
        )
    if not _has_role(member.role, required_role, ORG_ROLE_RANK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Org role is insufficient",
        )
    return member


def require_project_role(
    db: Session, user_id: uuid.UUID, project_id: uuid.UUID, required_role: str
) -> MLProject:
    project = db.get(MLProject, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.is_active.is_(True),
        )
    )
    if member and _has_role(member.role, required_role, PROJECT_ROLE_RANK):
        return project

    org_member = db.scalar(
        select(OrgMember).where(
            OrgMember.org_id == project.org_id,
            OrgMember.user_id == user_id,
            OrgMember.is_active.is_(True),
        )
    )
    if org_member and _has_role(org_member.role, "admin", ORG_ROLE_RANK):
        return project

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Project access denied",
    )
