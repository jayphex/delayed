from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from pathlib import Path
from datetime import datetime

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATA = Path(__file__).resolve().parents[2] / "data" / "sample_games.csv"

WATCH_LOG = [{
  "id": 1,
  "user_id": "demo",
  "game_id": "0022300001",
  "watched_at": "2024-10-26T20:00:00Z"
  }
]

def load_games():
    df = pd.read_csv(DATA)
    # compute delay in minutes (NaN → 0)
    def delay(row):
        if pd.isna(row["actual_start"]): return 0.0
        a = pd.to_datetime(row["actual_start"], utc=True)
        s = pd.to_datetime(row["scheduled_start"], utc=True)
        d = (a - s).total_seconds() / 60.0
        return round(max(d, 0.0), 2)
    df["delay_minutes"] = df.apply(delay, axis=1)
    df = df.where(df.notna(), None)
    return df

@app.get("/")
def root():
    return {"message": "delayed API is running!"}

@app.get("/games")
def get_games(date: str | None = None, 
              team: str | None = None, 
              watched: bool | None = None, 
              minDelay: float = 0 ):
    watched_ids = {e["game_id"] for e in WATCH_LOG if e["user_id"] == "demo"}
    df = load_games()
    df["game_id"] = df["game_id"].astype(str)
    if watched is True:
        df = df[df["game_id"].isin(watched_ids)]
    elif watched is False:
        df = df[~df["game_id"].isin(watched_ids)]
    if date: df = df[df["date"] == date]
    if team: df = df[(df.home_team == team) | (df.away_team == team)]
    df = df[df["delay_minutes"] >= minDelay]
    df = df.where(df.notna(), None)
    return df.to_dict(orient="records")

@app.get("/stats/summary")
def summary(date: str | None = None, 
            team: str | None = None, 
            minDelay: float = 0,
            watched: bool | None = None):
    watched_ids = {e["game_id"] for e in WATCH_LOG if e["user_id"] == "demo"}
    df = load_games()
    df["game_id"] = df["game_id"].astype(str)
    if watched is True:
        df = df[df["game_id"].isin(watched_ids)]
    elif watched is False:
        df = df[~df["game_id"].isin(watched_ids)]
    if date: df = df[df["date"] == date]
    if team: df = df[(df.home_team == team) | (df.away_team == team)]
    df = df[df["delay_minutes"] >= minDelay]
    return {
        "countDelayed": int((df.delay_minutes > 0).sum()),
        "avgDelay": float(df.delay_minutes.mean() if len(df) else 0),
        "maxDelay": float(df.delay_minutes.max() if len(df) else 0)
    }

@app.get("/watchlog")
def get_watchlog():
    return WATCH_LOG


@app.post("/watchlog")
def post_watchlog(game_id: str = Body(..., embed=True)):
    id = len(WATCH_LOG) + 1
    user_id = "demo"
    watched_at = datetime.utcnow().isoformat() + "Z"
    entry ={
        "id": id,
        "user_id": user_id,
        "game_id": game_id,
        "watched_at": watched_at
    }
    WATCH_LOG.append(entry)
    return entry

@app.delete("/watchlog/{game_id}")
def unwatch_game(game_id: str):
    global WATCH_LOG
    before = len(WATCH_LOG)
    WATCH_LOG = [e for e in WATCH_LOG if e["game_id"] != game_id]
    after = len(WATCH_LOG)
    return {"remove": before - after}
