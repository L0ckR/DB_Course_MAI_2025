from fastapi import FastAPI

from app.core.config import settings
from app.routers import (
    artifacts,
    auth,
    batch_import,
    dataset_versions,
    datasets,
    experiments,
    metric_definitions,
    organizations,
    projects,
    reports,
    runs,
    users,
)

app = FastAPI(title=settings.app_name)

api_prefix = settings.api_prefix
app.include_router(users.router, prefix=api_prefix)
app.include_router(auth.router, prefix=api_prefix)
app.include_router(organizations.router, prefix=api_prefix)
app.include_router(projects.router, prefix=api_prefix)
app.include_router(datasets.router, prefix=api_prefix)
app.include_router(dataset_versions.router, prefix=api_prefix)
app.include_router(experiments.router, prefix=api_prefix)
app.include_router(runs.router, prefix=api_prefix)
app.include_router(metric_definitions.router, prefix=api_prefix)
app.include_router(artifacts.router, prefix=api_prefix)
app.include_router(reports.router, prefix=api_prefix)
app.include_router(batch_import.router, prefix=api_prefix)
