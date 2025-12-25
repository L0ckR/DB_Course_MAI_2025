from fastapi import Request
from sqlalchemy import text

from app.db.session import SessionLocal


def get_db(request: Request):
    db = SessionLocal()
    try:
        user_id = request.headers.get("X-User-Id")
        if user_id:
            db.execute(
                text("SELECT set_config('app.user_id', :user_id, true)"),
                {"user_id": user_id},
            )
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
