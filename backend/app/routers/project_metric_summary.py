import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import MLProject, OrgMember, ProjectMember, ProjectMetricSummary, User
from app.schemas.project_metric_summary import (
    ProjectMetricSummaryCreate,
    ProjectMetricSummaryRead,
    ProjectMetricSummaryUpdate,
)

router = APIRouter(prefix="/project-metric-summary", tags=["project-metric-summary"])


@router.post("", response_model=ProjectMetricSummaryRead, status_code=status.HTTP_201_CREATED)
def create_project_metric_summary(
    payload: ProjectMetricSummaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMetricSummary:
    require_project_role(db, current_user.user_id, payload.project_id, "editor")
    summary = ProjectMetricSummary(**payload.model_dump())
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


@router.get("", response_model=list[ProjectMetricSummaryRead])
def list_project_metric_summary(
    project_id: uuid.UUID | None = None,
    metric_id: uuid.UUID | None = None,
    scope: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectMetricSummary]:
    member_projects = select(ProjectMember.project_id).where(
        ProjectMember.user_id == current_user.user_id,
        ProjectMember.is_active.is_(True),
    )
    org_admin_orgs = select(OrgMember.org_id).where(
        OrgMember.user_id == current_user.user_id,
        OrgMember.is_active.is_(True),
        OrgMember.role.in_(["owner", "admin"]),
    )
    query = (
        select(ProjectMetricSummary)
        .join(MLProject, MLProject.project_id == ProjectMetricSummary.project_id)
        .where(
            or_(
                ProjectMetricSummary.project_id.in_(member_projects),
                MLProject.org_id.in_(org_admin_orgs),
            )
        )
    )
    if project_id:
        require_project_role(db, current_user.user_id, project_id, "viewer")
        query = query.where(ProjectMetricSummary.project_id == project_id)
    if metric_id:
        query = query.where(ProjectMetricSummary.metric_id == metric_id)
    if scope:
        query = query.where(ProjectMetricSummary.scope == scope)

    rows = db.scalars(query.limit(limit).offset(offset)).all()
    return rows


@router.get("/{project_id}/{metric_id}/{scope}", response_model=ProjectMetricSummaryRead)
def get_project_metric_summary(
    project_id: uuid.UUID,
    metric_id: uuid.UUID,
    scope: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMetricSummary:
    summary = db.get(ProjectMetricSummary, (project_id, metric_id, scope))
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found"
        )
    require_project_role(db, current_user.user_id, project_id, "viewer")
    return summary


@router.put("/{project_id}/{metric_id}/{scope}", response_model=ProjectMetricSummaryRead)
def update_project_metric_summary(
    project_id: uuid.UUID,
    metric_id: uuid.UUID,
    scope: str,
    payload: ProjectMetricSummaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMetricSummary:
    summary = db.get(ProjectMetricSummary, (project_id, metric_id, scope))
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found"
        )
    require_project_role(db, current_user.user_id, project_id, "editor")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(summary, key, value)
    db.commit()
    db.refresh(summary)
    return summary


@router.delete("/{project_id}/{metric_id}/{scope}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_metric_summary(
    project_id: uuid.UUID,
    metric_id: uuid.UUID,
    scope: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    summary = db.get(ProjectMetricSummary, (project_id, metric_id, scope))
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Summary not found"
        )
    require_project_role(db, current_user.user_id, project_id, "editor")
    db.delete(summary)
    db.commit()
    return None
