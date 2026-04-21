from __future__ import annotations

import re
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.library.http import NBAStatsHTTP
from nba_api.stats.static import teams
from sqlmodel import Session, select

from .db.models import Game

NBAStatsHTTP._NBAStatsHTTP__HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}

SCHEDULE_TIME_RE = re.compile(r"^\s*(\d{1,2}:\d{2}\s*[ap]m)\s*ET\s*$", re.IGNORECASE)
TEAM_BY_ID = {team["id"]: team["abbreviation"] for team in teams.get_teams()}


def fetch_scoreboard_rows(game_date: date) -> list[dict]:
    scoreboard = scoreboardv2.ScoreboardV2(game_date=game_date.isoformat(), timeout=60)
    data = scoreboard.get_normalized_dict()
    return data.get("GameHeader", [])


def parse_scheduled_tip(game_date: date, status_text: Optional[str]) -> Optional[datetime]:
    if not status_text:
        return None

    match = SCHEDULE_TIME_RE.match(status_text)
    if not match:
        return None

    eastern = ZoneInfo("America/New_York")
    local_dt = datetime.strptime(
        f"{game_date.isoformat()} {match.group(1).upper()}",
        "%Y-%m-%d %I:%M %p",
    )
    localized = local_dt.replace(tzinfo=eastern)
    return localized.astimezone(timezone.utc)


def normalize_status(game_date: date, row: dict) -> str:
    status_id = int(row.get("GAME_STATUS_ID") or 0)
    status_text = str(row.get("GAME_STATUS_TEXT") or "").strip()

    if status_id == 1 or parse_scheduled_tip(game_date, status_text):
        return "scheduled"
    if status_id == 2:
        return "in_progress"
    if status_id == 3 or status_text.lower().startswith("final"):
        return "final"
    return status_text.lower().replace(" ", "_") or "scheduled"


def sync_games_for_date(
    session: Session,
    game_date: date,
    observed_at: Optional[datetime] = None,
) -> int:
    rows = fetch_scoreboard_rows(game_date)
    if not rows:
        return 0

    observed = observed_at or datetime.now(timezone.utc)
    game_ids = [str(row["GAME_ID"]) for row in rows]
    existing_games = {
        game.game_id: game
        for game in session.exec(select(Game).where(Game.game_id.in_(game_ids))).all()
    }

    for row in rows:
        game_id = str(row["GAME_ID"])
        existing = existing_games.get(game_id)
        status = normalize_status(game_date, row)
        scheduled_start = (
            existing.scheduled_start if existing and existing.scheduled_start else None
        ) or parse_scheduled_tip(game_date, row.get("GAME_STATUS_TEXT"))

        actual_start = existing.actual_start if existing else None
        if actual_start is None and status in {"in_progress", "final"}:
            actual_start = observed

        if existing:
            existing.date = game_date
            existing.home_team = TEAM_BY_ID.get(
                int(row["HOME_TEAM_ID"]), str(row["HOME_TEAM_ID"])
            )
            existing.away_team = TEAM_BY_ID.get(
                int(row["VISITOR_TEAM_ID"]), str(row["VISITOR_TEAM_ID"])
            )
            existing.scheduled_start = scheduled_start
            existing.actual_start = actual_start
            existing.status = status
            existing.updated_at = observed
        else:
            session.add(
                Game(
                    game_id=game_id,
                    date=game_date,
                    home_team=TEAM_BY_ID.get(
                        int(row["HOME_TEAM_ID"]), str(row["HOME_TEAM_ID"])
                    ),
                    away_team=TEAM_BY_ID.get(
                        int(row["VISITOR_TEAM_ID"]), str(row["VISITOR_TEAM_ID"])
                    ),
                    scheduled_start=scheduled_start,
                    actual_start=actual_start,
                    status=status,
                    created_at=observed,
                    updated_at=observed,
                )
            )

    session.commit()
    return len(rows)
