from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


class Base(DeclarativeBase):
    pass


def _normalize_database_url(url: str) -> str:
    """
    Normalize database URLs supplied by Railway or local development.
    """
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)

    return url


if DATABASE_URL:
    DATABASE_URL = _normalize_database_url(DATABASE_URL)

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

else:
    # Local development fallback.
    # Railway will use PostgreSQL through DATABASE_URL.
    engine = create_engine(
        "sqlite:///botlab_dev.db",
        connect_args={"check_same_thread": False},
    )


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    """
    Get a database session.

    Usage:

        db = next(get_db())
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def initialize_database():
    """
    Create database tables.

    Importing models here ensures SQLAlchemy knows
    about every table before create_all() runs.
    """
    from database import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
