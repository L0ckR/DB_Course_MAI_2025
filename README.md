# DB_Course_MAI_2025

Minimal ML experiment tracking system (PostgreSQL + FastAPI + SQLAlchemy + Alembic).

## Quick start

1) Copy env

```bash
cp .env.example .env
```

2) Start services

```bash
docker compose up --build
```

3) Run migrations

```bash
docker compose exec backend alembic upgrade head
```

4) Seed data

```bash
docker compose exec backend python scripts/seed.py
```

5) Open Swagger

- `http://localhost:8000/docs`

## Notes

- Audit triggers use `current_setting('app.user_id', true)`; set `X-User-Id` header in API requests to populate `changed_by`.
- Batch import endpoint: `POST /api/batch-import` (supports `metrics` and `datasets`).
- Performance demo SQL: `sql/perf_demo.sql`, paste output into `docs/perf_report.md`.
