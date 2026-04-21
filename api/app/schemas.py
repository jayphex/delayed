from datetime import datetime

from pydantic import BaseModel


class GameOut(BaseModel):
    game_id: str
    date: str
    home_team: str
    away_team: str
    scheduled_start: str | None
    actual_start: str | None
    status: str
    delay_minutes: float
    started_late: bool
    tipoff_state: str
    watched: bool


class SummaryOut(BaseModel):
    games: int
    countDelayed: int
    avgDelay: float
    maxDelay: float
    watchedGames: int
    totalDelayMinutes: float
    watchedDelayMinutes: float


class WatchLogEntry(BaseModel):
    id: int
    user_id: str
    game_id: str
    watched_at: datetime


class WatchLogCreate(BaseModel):
    game_id: str
