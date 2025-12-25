# agents.md

## Назначение репозитория
Проект: информационная система для версионирования ML-экспериментов, метрик и ссылок на артефакты моделей.
Стек: PostgreSQL + FastAPI + SQLAlchemy + Alembic + Docker Compose.

Цель: продемонстрировать проектирование реляционной БД, ограничения целостности, триггеры и аудит, SQL-функции и VIEW, оптимизацию запросов (индексы + EXPLAIN ANALYZE), batch-import и интеграцию с backend API (Swagger/OpenAPI).

## Архитектура (ожидаемая)
- `backend/` — FastAPI приложение
- `backend/app/models/` — ORM-модели SQLAlchemy
- `backend/app/routers/` — роутеры CRUD и reports
- `backend/app/db/` — сессия, engine, транзакции
- `migrations/` — Alembic миграции
- `sql/` — дополнительные SQL-скрипты (views/functions/triggers/perf)
- `scripts/` — генерация seed-данных, утилиты импорта
- `docs/` — perf_report.md, описания запросов и примеров

## Правила безопасности и качества (обязательно)
1) Никаких секретов в репозитории:
   - пароли/URI/ключи только через env
   - хранить шаблон в `.env.example`

2) Запрещено формировать SQL через f-string/конкатенацию.
   - использовать параметризацию (SQLAlchemy bind params / text + params)
   - любые raw SQL-запросы должны быть безопасными

3) Все изменения БД — через Alembic миграции.
   - не допускается “ручное” изменение схемы без миграций

4) Триггеры аудита и функции — в SQL-скриптах, применяются миграциями.
   - аудит должен фиксировать INSERT/UPDATE/DELETE минимум для ключевых таблиц

## Как поднять проект (локально)
1) Скопировать env:
   - `cp .env.example .env`

2) Запуск:
   - `docker compose up --build`

3) Миграции:
   - `docker compose exec backend alembic upgrade head`

4) Seed:
   - `docker compose exec backend python scripts/seed.py`

5) Swagger:
   - открыть `/docs` на адресе backend-контейнера

## Batch import
- Endpoint: `POST /api/batch-import`
- Требования:
  - сохранять job в `batch_import_jobs`
  - ошибки строк — в `batch_import_errors`
  - продолжать импорт при ошибках отдельных строк

## Производительность
- В `docs/perf_report.md` должен быть результат `EXPLAIN ANALYZE` для 1–2 ключевых запросов:
  - до индексов и после индексов
- Индексы добавлять осмысленно (WHERE/JOIN/ORDER BY)

## Что считать “готово”
- Все таблицы, VIEW, функции, триггеры созданы миграциями
- CRUD-операции доступны через API
- Отчёты (leaderboard/best-run/dashboard) работают
- Batch-import работает и логирует ошибки
- EXPLAIN ANALYZE отчёт добавлен в `docs/`

## Стиль и соглашения
- Python: форматирование и линтинг по проектным настройкам (если добавлены)
- Имена:
  - таблицы snake_case
  - PK: `<entity>_id`
  - внешние ключи: `<ref>_id`
- Временные поля: `created_at`, `updated_at` (если используется)
