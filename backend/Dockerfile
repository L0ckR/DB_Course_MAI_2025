FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/app /app/app
COPY backend/entrypoint.sh /app/entrypoint.sh
COPY migrations /app/migrations
COPY sql /app/sql
COPY scripts /app/scripts
COPY alembic.ini /app/alembic.ini

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
