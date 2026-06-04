from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def psycopg_connect_args() -> dict[str, object]:
    if settings.database_url.startswith("postgresql+psycopg"):
        return {"prepare_threshold": None}

    return {}


engine = create_engine(settings.database_url, pool_pre_ping=True, connect_args=psycopg_connect_args())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
