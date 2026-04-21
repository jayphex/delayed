from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .schemas import GameOut, SummaryOut, WatchLogCreate, WatchLogEntry

app = FastAPI(title="Delayed API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
PRIMARY_GAMES_PATH = DATA_DIR / "games.csv"
SAMPLE_GAMES_PATH = DATA_DIR / "sample_games.csv"
WATCH_LOG_PATH = DATA_DIR / "watch_log.json"
DEFAULT_USER_ID = "demo"
GAME_COLUMNS = [
    "game_id",
    "date",
    "home_team",
    "away_team",
    "scheduled_start",
    "actual_start",
    "status",
]


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _validate_model(model_class, payload):
    if hasattr(model_class, "model_validate"):
        return model_class.model_validate(payload)
    return model_class.parse_obj(payload)


def _dump_model(model) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return json.loads(model.json())


def _games_path() -> Path:
    return PRIMARY_GAMES_PATH if PRIMARY_GAMES_PATH.exists() else SAMPLE_GAMES_PATH


def _iso_or_none(value: object) -> str | None:
    if value is None:
        return None
    timestamp = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(timestamp):
        return None
    return timestamp.isoformat().replace("+00:00", "Z")


def _minutes_between(start: object, end: object) -> float:
    start_ts = pd.to_datetime(start, utc=True, errors="coerce")
    end_ts = pd.to_datetime(end, utc=True, errors="coerce")
    if pd.isna(start_ts) or pd.isna(end_ts):
        return 0.0
    return round(max((end_ts - start_ts).total_seconds() / 60, 0.0), 1)


def _normalize_games(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    for column in GAME_COLUMNS:
        if column not in working.columns:
            working[column] = None

    working = working[GAME_COLUMNS]
    working["game_id"] = working["game_id"].astype(str)
    working["home_team"] = working["home_team"].fillna("").astype(str).str.upper()
    working["away_team"] = working["away_team"].fillna("").astype(str).str.upper()
    working["status"] = working["status"].fillna("scheduled").astype(str).str.lower()

    scheduled = pd.to_datetime(working["scheduled_start"], utc=True, errors="coerce")
    actual = pd.to_datetime(working["actual_start"], utc=True, errors="coerce")

    inferred_date = scheduled.dt.strftime("%Y-%m-%d")
    working["date"] = working["date"].fillna(inferred_date).fillna("")
    working["scheduled_start"] = scheduled.map(_iso_or_none)
    working["actual_start"] = actual.map(_iso_or_none)
    working["delay_minutes"] = [
        _minutes_between(start, end)
        for start, end in zip(working["scheduled_start"], working["actual_start"])
    ]
    working["started_late"] = working["delay_minutes"] > 0
    working["tipoff_state"] = working.apply(
        lambda row: "scheduled"
        if not row["actual_start"]
        else "late"
        if row["delay_minutes"] > 0
        else "on_time",
        axis=1,
    )

    working = working.sort_values(
        by=["date", "delay_minutes", "scheduled_start"],
        ascending=[False, False, True],
        na_position="last",
    )
    return working.where(working.notna(), None)


def load_games() -> pd.DataFrame:
    path = _games_path()
    if not path.exists():
        return _normalize_games(pd.DataFrame(columns=GAME_COLUMNS))
    df = pd.read_csv(path)
    return _normalize_games(df)


def load_watch_log() -> list[WatchLogEntry]:
    _ensure_data_dir()
    if not WATCH_LOG_PATH.exists():
        return []

    raw_entries = json.loads(WATCH_LOG_PATH.read_text() or "[]")
    entries: list[WatchLogEntry] = []
    for raw in raw_entries:
        try:
            entries.append(_validate_model(WatchLogEntry, raw))
        except Exception:
            continue
    return entries


def save_watch_log(entries: list[WatchLogEntry]) -> None:
    _ensure_data_dir()
    WATCH_LOG_PATH.write_text(
        json.dumps([_dump_model(entry) for entry in entries], indent=2)
    )


def watched_ids_for(user_id: str = DEFAULT_USER_ID) -> set[str]:
    return {entry.game_id for entry in load_watch_log() if entry.user_id == user_id}


def filtered_games(
    date: str | None,
    team: str | None,
    watched: bool | None,
    min_delay: float,
) -> pd.DataFrame:
    df = load_games()
    watched_ids = watched_ids_for()
    df["watched"] = df["game_id"].isin(watched_ids)

    if date:
        df = df[df["date"] == date]
    if team:
        team_code = team.upper()
        df = df[(df["home_team"] == team_code) | (df["away_team"] == team_code)]
    if watched is True:
        df = df[df["watched"]]
    elif watched is False:
        df = df[~df["watched"]]
    if min_delay > 0:
        df = df[df["delay_minutes"] >= min_delay]

    return df.where(df.notna(), None)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Delayed API is running."}


@app.get("/games", response_model=list[GameOut])
def get_games(
    date: str | None = None,
    team: str | None = None,
    watched: bool | None = None,
    minDelay: float = Query(0, ge=0),
) -> list[GameOut]:
    df = filtered_games(date=date, team=team, watched=watched, min_delay=minDelay)
    return [_validate_model(GameOut, record) for record in df.to_dict(orient="records")]


@app.get("/stats/summary", response_model=SummaryOut)
def summary(
    date: str | None = None,
    team: str | None = None,
    watched: bool | None = None,
    minDelay: float = Query(0, ge=0),
) -> SummaryOut:
    df = filtered_games(date=date, team=team, watched=watched, min_delay=minDelay)

    if df.empty:
        return SummaryOut(
            games=0,
            countDelayed=0,
            avgDelay=0,
            maxDelay=0,
            watchedGames=0,
            totalDelayMinutes=0,
            watchedDelayMinutes=0,
        )

    return SummaryOut(
        games=int(len(df)),
        countDelayed=int((df["delay_minutes"] > 0).sum()),
        avgDelay=round(float(df["delay_minutes"].mean()), 1),
        maxDelay=round(float(df["delay_minutes"].max()), 1),
        watchedGames=int(df["watched"].sum()),
        totalDelayMinutes=round(float(df["delay_minutes"].sum()), 1),
        watchedDelayMinutes=round(float(df.loc[df["watched"], "delay_minutes"].sum()), 1),
    )


@app.get("/watchlog", response_model=list[WatchLogEntry])
def get_watchlog() -> list[WatchLogEntry]:
    return load_watch_log()


@app.post("/watchlog", response_model=WatchLogEntry)
def post_watchlog(payload: WatchLogCreate = Body(...)) -> WatchLogEntry:
    entries = load_watch_log()
    if any(
        entry.game_id == payload.game_id and entry.user_id == DEFAULT_USER_ID
        for entry in entries
    ):
        return next(
            entry
            for entry in entries
            if entry.game_id == payload.game_id and entry.user_id == DEFAULT_USER_ID
        )

    game_ids = set(load_games()["game_id"].astype(str))
    if payload.game_id not in game_ids:
        raise HTTPException(status_code=404, detail="Unknown game id.")

    entry = WatchLogEntry(
        id=max((existing.id for existing in entries), default=0) + 1,
        user_id=DEFAULT_USER_ID,
        game_id=payload.game_id,
        watched_at=datetime.now(timezone.utc),
    )
    entries.append(entry)
    save_watch_log(entries)
    return entry


@app.delete("/watchlog/{game_id}")
def unwatch_game(game_id: str) -> dict[str, int]:
    entries = load_watch_log()
    kept_entries = [
        entry
        for entry in entries
        if not (entry.game_id == game_id and entry.user_id == DEFAULT_USER_ID)
    ]
    removed = len(entries) - len(kept_entries)
    save_watch_log(kept_entries)
    return {"removed": removed}
