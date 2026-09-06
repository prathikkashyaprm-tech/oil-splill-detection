"""
MarineGuard AI - Database Engine and Session Management
Supports SQLite and PostgreSQL/PostGIS.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
from backend.app.models.schema import Base

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create tables on startup"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
