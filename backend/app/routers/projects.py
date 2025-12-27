import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_org_role, require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import MLProject, OrgMember, ProjectMember, User
from app.schemas.projects import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MLProject:
    require_org_role(db, current_user.user_id, project_in.org_id, "admin")
    project = MLProject(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    db.add(
        ProjectMember(
            project_id=project.project_id,
            user_id=current_user.user_id,
            role="admin",
            is_active=True,
        )
    )
    db.commit()
    return project


@router.get("", response_model=list[ProjectRead])
def list_projects(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MLProject]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    projects = db.scalars(
        select(MLProject)
        .where(
            or_(
                MLProject.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
        .limit(limit)
        .offset(offset)
    ).all()
    return projects


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MLProject:
    require_project_role(db, current_user.user_id, project_id, "viewer")
    project = db.get(MLProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MLProject:
    require_project_role(db, current_user.user_id, project_id, "admin")
    project = db.get(MLProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    for key, value in project_in.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    require_project_role(db, current_user.user_id, project_id, "admin")
    project = db.get(MLProject, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
