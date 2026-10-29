"""
Database connection and session lifecycle management for SQLite.
Provides engine creation, foreign key constraint enforcement, and safe initialization.
"""

from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from backend.config import DATABASE_URL

# SQLite requires check_same_thread=False for multithreaded FastAPI worker handling
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
)


@event.listens_for(Engine, "connect")
def _enforce_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    """
    Enforces SQLite foreign key constraints.
    SQLite has foreign keys disabled by default; this ensures referential integrity.
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        # Pass non-fatal errors if connected to non-SQLite backends during testing
        pass


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db(engine_override: Optional[Engine] = None) -> None:
    """
    Safely initializes database tables using Base.metadata.create_all.
    Non-destructive operation: will create missing tables but never drops or overwrites existing data.
    """
    import backend.models  # noqa: F401 Ensure models are loaded into Base.metadata
    target_engine = engine_override or engine
    Base.metadata.create_all(bind=target_engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a scoped database session.
    Guarantees clean session closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

