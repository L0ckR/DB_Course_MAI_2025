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
- Frontend: `http://localhost:3000`

## Notes

- Audit triggers use `current_setting('app.user_id', true)`; authenticated requests populate `changed_by` automatically.
- Batch import endpoint: `POST /api/batch-import` (supports `metrics` and `datasets`).
- Performance demo SQL: `sql/perf_demo.sql`, paste output into `docs/perf_report.md`.
- Integration notes (MLflow / scikit-learn): `docs/integration.md`.
- Coursework report (TeX): `docs/report.tex`.
- Business queries: `sql/business_queries.sql`.
- Auth endpoints: `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/token` (OAuth2 password flow for Swagger).
  Use the `access_token` with `Authorization: Bearer <token>` (Swagger has the Authorize button).
  Seeded users use the password from `SEED_DEFAULT_PASSWORD`.
  Passwords are hashed with bcrypt via `passlib`.
  Password length is limited to 72 bytes for bcrypt compatibility.
  Test user credentials come from `SEED_TEST_USER_EMAIL` / `SEED_TEST_USER_PASSWORD`.

## Frontend

The frontend lives in `frontend/` and connects to the FastAPI backend.

```bash
cd frontend
npm install
npm run dev
```

The default `VITE_API_URL=/api` keeps a single origin for Docker and local dev (Vite proxies `/api` to `http://localhost:8000`).
Frontend dev reads the repo root `.env`, so there is only one env file for all services.

Open `http://localhost:5173` and sign in with email + password (or register).
