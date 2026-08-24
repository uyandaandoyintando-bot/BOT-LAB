from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.config import Config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    Config.DATABASE_URL,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def initialize_database() -> None:
    # Import models before create_all so SQLAlchemy
    # knows about every table.
    from database import models  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )
