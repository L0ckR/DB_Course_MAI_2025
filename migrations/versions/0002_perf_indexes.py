"""additional indexes for analytics

Revision ID: 0002_perf_indexes
Revises: 0001_init
Create Date: 2025-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_perf_indexes"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_experiments_project_id "
        "ON experiments (project_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_runs_dataset_version_id "
        "ON runs (dataset_version_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_run_artifacts_run_id "
        "ON run_artifacts (run_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_run_artifacts_artifact_id "
        "ON run_artifacts (artifact_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_rmv_final_metric "
        "ON run_metric_values (metric_id, scope, value) "
        "WHERE step IS NULL"
    )


def downgrade() -> None:
    op.drop_index("ix_rmv_final_metric", table_name="run_metric_values")
    op.drop_index("ix_run_artifacts_artifact_id", table_name="run_artifacts")
    op.drop_index("ix_run_artifacts_run_id", table_name="run_artifacts")
    op.drop_index("ix_runs_dataset_version_id", table_name="runs")
    op.drop_index("ix_experiments_project_id", table_name="experiments")
