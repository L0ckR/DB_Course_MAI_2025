"""initial schema

Revision ID: 0001_init
Revises: 
Create Date: 2025-01-01 00:00:00.000000
"""
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


SQL_DIR = Path(__file__).resolve().parents[2] / "sql"


def _run_sql_file(filename: str) -> None:
    sql_path = SQL_DIR / filename
    op.execute(sql_path.read_text(encoding="utf-8"))


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "organizations",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", onupdate="CASCADE"),
            nullable=False,
        ),
    )

    op.create_table(
        "org_members",
        sa.Column("org_member_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("role IN ('owner','admin','member','viewer')", name="ck_org_members_role"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_members_org_user"),
    )

    op.create_table(
        "ml_projects",
        sa.Column("project_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.org_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("status IN ('active','archived')", name="ck_projects_status"),
        sa.UniqueConstraint("org_id", "name", name="uq_projects_org_name"),
    )

    op.create_table(
        "project_members",
        sa.Column("project_member_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("role IN ('admin','editor','viewer')", name="ck_members_role"),
        sa.UniqueConstraint("project_id", "user_id", name="uq_project_members_project_user"),
    )

    op.create_table(
        "datasets",
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("task_type", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "task_type IN ('classification','regression','ranking','segmentation','nlp','other')",
            name="ck_datasets_task_type",
        ),
        sa.UniqueConstraint("project_id", "name", name="uq_datasets_project_name"),
    )

    op.create_table(
        "dataset_versions",
        sa.Column("dataset_version_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("datasets.dataset_id", ondelete="CASCADE"), nullable=False),
        sa.Column("version_label", sa.Text(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("row_count", sa.BigInteger(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("row_count IS NULL OR row_count >= 0", name="ck_dv_row"),
        sa.CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_dv_size"),
        sa.UniqueConstraint("dataset_id", "version_label", name="uq_dv_dataset_version"),
        sa.UniqueConstraint("dataset_id", "content_hash", name="uq_dv_dataset_hash"),
    )

    op.create_index("ix_dataset_versions_dataset_label", "dataset_versions", ["dataset_id", "version_label"])
    op.create_index("ix_dataset_versions_content_hash", "dataset_versions", ["content_hash"])

    op.create_table(
        "experiments",
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("objective", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", onupdate="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("project_id", "name", name="uq_experiments_project_name"),
    )

    op.create_table(
        "runs",
        sa.Column("run_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("experiment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("experiments.experiment_id", ondelete="CASCADE"), nullable=False),
        sa.Column("dataset_version_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dataset_versions.dataset_version_id", onupdate="CASCADE"), nullable=False),
        sa.Column("run_name", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("git_commit", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('queued','running','finished','failed','killed')",
            name="ck_runs_status",
        ),
    )

    op.create_index("ix_runs_experiment_status_started", "runs", ["experiment_id", "status", "started_at"])

    op.create_table(
        "run_configs",
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.run_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("params_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("env_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("command_line", sa.Text(), nullable=True),
        sa.Column("seed", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "metric_definitions",
        sa.Column("metric_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("key", sa.Text(), nullable=False, unique=True),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("unit", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("goal IN ('min','max','last')", name="ck_metric_goal"),
    )

    op.create_table(
        "run_metric_values",
        sa.Column("run_metric_value_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("metric_definitions.metric_id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=True),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("scope IN ('train','val','test')", name="ck_rmv_scope"),
        sa.CheckConstraint("step IS NULL OR step >= 0", name="ck_rmv_step"),
    )

    op.create_index(
        "ix_rmv_run_metric_scope_step",
        "run_metric_values",
        ["run_id", "metric_id", "scope", "step"],
    )

    op.create_table(
        "artifacts",
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ml_projects.project_id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("checksum", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "artifact_type IN ('model','plot','log','report','dataset-sample','other')",
            name="ck_artifacts_type",
        ),
        sa.CheckConstraint("size_bytes IS NULL OR size_bytes >= 0", name="ck_artifacts_size"),
    )

    op.create_index(
        "ix_artifacts_project_type_created",
        "artifacts",
        ["project_id", "artifact_type", "created_at"],
    )

    op.create_table(
        "run_artifacts",
        sa.Column("run_artifact_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("runs.run_id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.artifact_id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("run_id", "artifact_id", name="uq_run_artifacts_run_artifact"),
        sa.UniqueConstraint("run_id", "alias", name="uq_run_artifacts_alias"),
    )

    op.create_table(
        "audit_log",
        sa.Column("audit_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("table_name", sa.Text(), nullable=False),
        sa.Column("operation", sa.Text(), nullable=False),
        sa.Column("row_pk", sa.Text(), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("old_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("operation IN ('I','U','D')", name="ck_audit_operation"),
    )

    op.create_table(
        "batch_import_jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("source_format", sa.Text(), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id"), nullable=True),
        sa.Column("stats_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "job_type IN ('users','datasets','runs','metrics','artifacts')",
            name="ck_jobs_type",
        ),
        sa.CheckConstraint(
            "status IN ('created','running','finished','failed')",
            name="ck_jobs_status",
        ),
        sa.CheckConstraint("source_format IN ('csv','json')", name="ck_jobs_format"),
    )

    op.create_table(
        "batch_import_errors",
        sa.Column("error_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("batch_import_jobs.job_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("raw_row", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "project_metric_summary",
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ml_projects.project_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "metric_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("metric_definitions.metric_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("scope", sa.Text(), primary_key=True),
        sa.Column("best_value", sa.Float(), nullable=True),
        sa.Column(
            "best_run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("runs.run_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.CheckConstraint("scope IN ('train','val','test')", name="ck_pms_scope"),
    )

    _run_sql_file("functions.sql")
    _run_sql_file("project_metric_summary.sql")
    _run_sql_file("views.sql")
    _run_sql_file("audit_triggers.sql")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_project_metric_summary ON run_metric_values")
    op.execute("DROP FUNCTION IF EXISTS fn_update_project_metric_summary()")
    op.execute("DROP FUNCTION IF EXISTS fn_experiment_leaderboard(uuid, text, text, integer)")
    op.execute("DROP FUNCTION IF EXISTS fn_best_run_id(uuid, text, text)")
    op.execute("DROP FUNCTION IF EXISTS fn_audit_log()")

    op.execute("DROP VIEW IF EXISTS v_project_quality_dashboard")
    op.execute("DROP VIEW IF EXISTS v_best_runs_per_experiment")
    op.execute("DROP VIEW IF EXISTS v_runs_with_final_metrics")

    op.drop_table("project_metric_summary")
    op.drop_table("batch_import_errors")
    op.drop_table("batch_import_jobs")
    op.drop_table("audit_log")
    op.drop_table("run_artifacts")
    op.drop_index("ix_artifacts_project_type_created", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_index("ix_rmv_run_metric_scope_step", table_name="run_metric_values")
    op.drop_table("run_metric_values")
    op.drop_table("metric_definitions")
    op.drop_table("run_configs")
    op.drop_index("ix_runs_experiment_status_started", table_name="runs")
    op.drop_table("runs")
    op.drop_table("experiments")
    op.drop_index("ix_dataset_versions_content_hash", table_name="dataset_versions")
    op.drop_index("ix_dataset_versions_dataset_label", table_name="dataset_versions")
    op.drop_table("dataset_versions")
    op.drop_table("datasets")
    op.drop_table("project_members")
    op.drop_table("ml_projects")
    op.drop_table("org_members")
    op.drop_table("organizations")
    op.drop_table("users")
