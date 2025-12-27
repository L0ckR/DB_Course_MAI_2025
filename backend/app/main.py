from fastapi import FastAPI

from app.core.config import settings
from app.routers import (
    artifacts,
    audit_log,
    auth,
    batch_import_errors,
    batch_import,
    batch_import_jobs,
    dataset_versions,
    datasets,
    experiments,
    metric_definitions,
    org_members,
    organizations,
    project_members,
    project_metric_summary,
    projects,
    reports,
    run_artifacts,
    run_configs,
    run_metric_values,
    runs,
    users,
)

app = FastAPI(title=settings.app_name)

api_prefix = settings.api_prefix
app.include_router(users.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(organizations.router, prefix=api_prefix)
app.include_router(org_members.router, prefix=api_prefix)
app.include_router(projects.router, prefix=api_prefix)
app.include_router(project_members.router, prefix=api_prefix)
app.include_router(datasets.router, prefix=api_prefix)
app.include_router(dataset_versions.router, prefix=api_prefix)
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(runs.router, prefix=api_prefix)
app.include_router(run_configs.router, prefix=api_prefix)
app.include_router(run_metric_values.router, prefix=api_prefix)
app.include_router(metric_definitions.router, prefix=api_prefix)
app.include_router(artifacts.router, prefix=api_prefix)
app.include_router(run_artifacts.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(batch_import.router, prefix=api_prefix)
app.include_router(batch_import_jobs.router, prefix=api_prefix)
app.include_router(batch_import_errors.router, prefix=api_prefix)
app.include_router(audit_log.router, prefix=api_prefix)
app.include_router(project_metric_summary.router, prefix=api_prefix)
