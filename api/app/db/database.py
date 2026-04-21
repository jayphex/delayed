from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine

from ..config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


def parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def prepare_database() -> None:
    init_db()


def get_session():
    with Session(engine) as session:
        yield session
