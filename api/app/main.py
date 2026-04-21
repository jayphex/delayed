from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_
from sqlmodel import Session, select

from .config import get_settings
from .db.database import get_session, prepare_database
from .db.models import Game, WatchLog
from .schemas import GameOut, SummaryOut, SyncResponse, WatchLogCreate, WatchLogEntry
from .sync import sync_games_for_date

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    prepare_database()
    yield


app = FastAPI(title="Delayed API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def to_iso(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def delay_minutes(game: Game) -> float:
    if not game.scheduled_start or not game.actual_start:
        return 0.0
    delta = (game.actual_start - game.scheduled_start).total_seconds() / 60
    return round(max(delta, 0.0), 1)


def serialize_game(game: Game, watched_ids: set[str]) -> GameOut:
    delay = delay_minutes(game)
    return GameOut(
        game_id=game.game_id,
        date=game.date.isoformat(),
        home_team=game.home_team,
        away_team=game.away_team,
        scheduled_start=to_iso(game.scheduled_start),
        actual_start=to_iso(game.actual_start),
        status=game.status,
        delay_minutes=delay,
        started_late=delay > 0,
        tipoff_state="scheduled" if not game.actual_start else "late" if delay > 0 else "on_time",
        watched=game.game_id in watched_ids,
    )


def serialize_watch_log(entry: WatchLog) -> WatchLogEntry:
    return WatchLogEntry(
        id=entry.id or 0,
        user_id=entry.user_id,
        game_id=entry.game_id,
        watched_at=entry.watched_at,
    )


def user_watch_ids(session: Session, user_id: str) -> set[str]:
    watched_rows = session.exec(
        select(WatchLog.game_id).where(WatchLog.user_id == user_id)
    ).all()
    return set(watched_rows)


def filtered_games(
    session: Session,
    *,
    game_date: Optional[date],
    team: Optional[str],
    watched: Optional[bool],
    min_delay: float,
) -> list[GameOut]:
    statement = select(Game)
    if game_date:
        statement = statement.where(Game.date == game_date)
    if team:
        team_code = team.upper()
        statement = statement.where(
            or_(Game.home_team == team_code, Game.away_team == team_code)
        )

    games = session.exec(statement.order_by(Game.date.desc(), Game.scheduled_start)).all()
    watched_ids = user_watch_ids(session, settings.default_user_id)
    serialized = [serialize_game(game, watched_ids) for game in games]

    if watched is True:
        serialized = [game for game in serialized if game.watched]
    elif watched is False:
        serialized = [game for game in serialized if not game.watched]

    if min_delay > 0:
        serialized = [game for game in serialized if game.delay_minutes >= min_delay]

    serialized.sort(
        key=lambda game: (game.date, game.delay_minutes, game.scheduled_start or ""),
        reverse=True,
    )
    return serialized


def require_sync_token(request: Request, token: Optional[str]) -> None:
    expected = settings.sync_token
    if not expected:
        return

    auth_header = request.headers.get("authorization", "")
    bearer = auth_header[7:] if auth_header.lower().startswith("bearer ") else None
    header_token = request.headers.get("x-sync-token")
    candidate = token or header_token or bearer
    if candidate != expected:
        raise HTTPException(status_code=401, detail="Invalid sync token.")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Delayed API is running."}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/games", response_model=list[GameOut])
def get_games(
    session: Session = Depends(get_session),
    game_date: Optional[date] = Query(None, alias="date"),
    team: Optional[str] = None,
    watched: Optional[bool] = None,
    minDelay: float = Query(0, ge=0),
) -> list[GameOut]:
    return filtered_games(
        session,
        game_date=game_date,
        team=team,
        watched=watched,
        min_delay=minDelay,
    )


@app.get("/stats/summary", response_model=SummaryOut)
def summary(
    session: Session = Depends(get_session),
    game_date: Optional[date] = Query(None, alias="date"),
    team: Optional[str] = None,
    watched: Optional[bool] = None,
    minDelay: float = Query(0, ge=0),
) -> SummaryOut:
    games = filtered_games(
        session,
        game_date=game_date,
        team=team,
        watched=watched,
        min_delay=minDelay,
    )
    if not games:
        return SummaryOut(
            games=0,
            countDelayed=0,
            avgDelay=0,
            maxDelay=0,
            watchedGames=0,
            totalDelayMinutes=0,
            watchedDelayMinutes=0,
        )

    watched_games = [game for game in games if game.watched]
    delays = [game.delay_minutes for game in games]
    watched_delays = [game.delay_minutes for game in watched_games]

    return SummaryOut(
        games=len(games),
        countDelayed=sum(1 for game in games if game.delay_minutes > 0),
        avgDelay=round(sum(delays) / len(delays), 1),
        maxDelay=round(max(delays), 1),
        watchedGames=len(watched_games),
        totalDelayMinutes=round(sum(delays), 1),
        watchedDelayMinutes=round(sum(watched_delays), 1),
    )


@app.get("/watchlog", response_model=list[WatchLogEntry])
def get_watchlog(session: Session = Depends(get_session)) -> list[WatchLogEntry]:
    entries = session.exec(
        select(WatchLog)
        .where(WatchLog.user_id == settings.default_user_id)
        .order_by(WatchLog.watched_at.desc())
    ).all()
    return [serialize_watch_log(entry) for entry in entries]


@app.post("/watchlog", response_model=WatchLogEntry)
def post_watchlog(
    payload: WatchLogCreate,
    session: Session = Depends(get_session),
) -> WatchLogEntry:
    game = session.get(Game, payload.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Unknown game id.")

    existing = session.exec(
        select(WatchLog).where(
            WatchLog.user_id == settings.default_user_id,
            WatchLog.game_id == payload.game_id,
        )
    ).first()
    if existing:
        return serialize_watch_log(existing)

    entry = WatchLog(
        user_id=settings.default_user_id,
        game_id=payload.game_id,
        watched_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return serialize_watch_log(entry)


@app.delete("/watchlog/{game_id}")
def unwatch_game(
    game_id: str,
    session: Session = Depends(get_session),
) -> dict[str, int]:
    entries = session.exec(
        select(WatchLog).where(
            WatchLog.user_id == settings.default_user_id,
            WatchLog.game_id == game_id,
        )
    ).all()
    for entry in entries:
        session.delete(entry)
    session.commit()
    return {"removed": len(entries)}


@app.api_route("/internal/sync-games", methods=["GET", "POST"], response_model=SyncResponse)
def sync_games(
    request: Request,
    session: Session = Depends(get_session),
    game_date: Optional[date] = Query(None, alias="date"),
    token: Optional[str] = None,
) -> SyncResponse:
    require_sync_token(request, token)
    target_date = game_date or datetime.now(timezone.utc).date()
    observed_at = datetime.now(timezone.utc)
    synced_games = sync_games_for_date(session, target_date, observed_at=observed_at)
    return SyncResponse(
        date=target_date.isoformat(),
        synced_games=synced_games,
        observed_at=to_iso(observed_at) or "",
    )
