import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.permissions import require_project_role
from app.core.security import get_current_user
from app.db.deps import get_db
from app.models.models import Experiment, User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/experiments/{experiment_id}/leaderboard")
def experiment_leaderboard(
    experiment_id: uuid.UUID,
    metric_key: str = Query(...),
    scope: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    rows = db.execute(
        text(
            "SELECT * FROM fn_experiment_leaderboard(:experiment_id, :metric_key, :scope, :limit)"
        ),
        {
            "experiment_id": experiment_id,
            "metric_key": metric_key,
            "scope": scope,
            "limit": limit,
        },
    ).all()
    return [dict(row._mapping) for row in rows]


@router.get("/experiments/{experiment_id}/best-run")
def experiment_best_run(
    experiment_id: uuid.UUID,
    metric_key: str = Query(...),
    scope: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
    require_project_role(db, current_user.user_id, experiment.project_id, "viewer")
    result = db.execute(
        text(
            "SELECT fn_best_run_id(:experiment_id, :metric_key, :scope) AS run_id"
        ),
        {
            "experiment_id": experiment_id,
            "metric_key": metric_key,
            "scope": scope,
        },
    ).scalar()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No runs found")
    return {"run_id": result}


@router.get("/projects/{project_id}/dashboard")
def project_dashboard(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    require_project_role(db, current_user.user_id, project_id, "viewer")
    row = db.execute(
        text("SELECT * FROM v_project_quality_dashboard WHERE project_id = :project_id"),
        {"project_id": project_id},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    return dict(row)
