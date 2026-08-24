from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    """
    Railway provides DATABASE_URL automatically when
    PostgreSQL is connected to the service.

    SQLite is kept as a local fallback.
    """

    return os.getenv(
        "DATABASE_URL",
        "sqlite:///botlab.db",
    )


DATABASE_URL = get_database_url()

# Railway/PostgreSQL URLs can sometimes use postgres://.
# SQLAlchemy expects postgresql://.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://",
        "postgresql://",
        1,
    )


engine_kwargs = {
    "pool_pre_ping": True,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
    }

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def initialize_database() -> None:
    """
    Create all SQLAlchemy tables that do not already exist.

    Production schema changes should eventually be handled
    through Alembic migrations.
    """

    # Import models so SQLAlchemy knows about every table.
    from database import models  # noqa: F401

    Base.metadata.create_all(
        bind=engine,
    )
