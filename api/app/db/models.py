from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Game(SQLModel, table=True):
    __tablename__ = "games"

    game_id: str = Field(primary_key=True)
    date: date = Field(index=True)
    home_team: str = Field(index=True, max_length=8)
    away_team: str = Field(index=True, max_length=8)
    scheduled_start: Optional[datetime] = Field(default=None, index=True)
    actual_start: Optional[datetime] = None
    status: str = Field(default="scheduled", index=True, max_length=32)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now, nullable=False)

    watch_entries: list["WatchLog"] = Relationship(back_populates="game")


class WatchLog(SQLModel, table=True):
    __tablename__ = "watch_logs"
    __table_args__ = (UniqueConstraint("user_id", "game_id", name="uq_watch_logs_user_game"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    game_id: str = Field(foreign_key="games.game_id", index=True)
    watched_at: datetime = Field(default_factory=utc_now, nullable=False)

    game: Optional[Game] = Relationship(back_populates="watch_entries")
