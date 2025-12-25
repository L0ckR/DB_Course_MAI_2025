#!/bin/sh
set -e

python - <<'PY'
import os
import time
import psycopg

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL is not set")

if url.startswith("postgresql+psycopg://"):
    url = url.replace("postgresql+psycopg://", "postgresql://", 1)

for _ in range(30):
    try:
        conn = psycopg.connect(url)
        conn.close()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("Database not ready")
PY

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
