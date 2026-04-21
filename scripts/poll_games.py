from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from nba_api.stats.endpoints import scoreboardv2
from nba_api.stats.library.http import NBAStatsHTTP
from nba_api.stats.static import teams

NBAStatsHTTP._NBAStatsHTTP__HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_PATH = DATA_DIR / "games.csv"
STATE_PATH = DATA_DIR / "poll_state.json"
SCHEDULE_TIME_RE = re.compile(r"^\s*(\d{1,2}:\d{2}\s*[ap]m)\s*ET\s*$", re.IGNORECASE)
TEAM_BY_ID = {team["id"]: team["abbreviation"] for team in teams.get_teams()}
CSV_COLUMNS = [
    "game_id",
    "date",
    "home_team",
    "away_team",
    "scheduled_start",
    "actual_start",
    "status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Poll the NBA scoreboard and persist scheduled vs observed tip-off times."
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Game date in YYYY-MM-DD format. Defaults to today in local time.",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Polling interval in seconds when running continuously.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Fetch once and exit instead of polling forever.",
    )
    return parser.parse_args()


def load_state() -> dict[str, dict[str, str]]:
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text())
    except json.JSONDecodeError:
        return {}


def save_state(state: dict[str, dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2))


def load_existing_games() -> pd.DataFrame:
    if not OUTPUT_PATH.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)

    df = pd.read_csv(OUTPUT_PATH)
    for column in CSV_COLUMNS:
        if column not in df.columns:
            df[column] = None
    return df[CSV_COLUMNS]


def save_games(df: pd.DataFrame) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ordered = df.copy()
    ordered = ordered.sort_values(
        by=["date", "scheduled_start", "game_id"],
        ascending=[False, True, True],
        na_position="last",
    )
    ordered.to_csv(OUTPUT_PATH, index=False)


def fetch_scoreboard(date: str) -> pd.DataFrame:
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date, timeout=60)
    frames = scoreboard.get_data_frames()
    return frames[0]


def parse_scheduled_tip(date: str, status_text: Any) -> str | None:
    if status_text is None:
        return None

    match = SCHEDULE_TIME_RE.match(str(status_text))
    if not match:
        return None

    eastern = ZoneInfo("America/New_York")
    local_dt = datetime.strptime(f"{date} {match.group(1).upper()}", "%Y-%m-%d %I:%M %p")
    localized = local_dt.replace(tzinfo=eastern)
    return localized.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_status(date: str, row: pd.Series) -> str:
    status_id = int(row.get("GAME_STATUS_ID") or 0)
    status_text = str(row.get("GAME_STATUS_TEXT") or "").strip()

    if status_id == 1 or parse_scheduled_tip(date, status_text):
        return "scheduled"
    if status_id == 2:
        return "in_progress"
    if status_id == 3 or status_text.lower().startswith("final"):
        return "final"
    return status_text.lower().replace(" ", "_") or "scheduled"


def derive_actual_start(
    state: dict[str, dict[str, str]],
    existing_actual_start: str | None,
    game_id: str,
    status: str,
) -> str | None:
    if existing_actual_start:
        return existing_actual_start

    state_entry = state.setdefault(game_id, {})
    if "actual_start" in state_entry:
        return state_entry["actual_start"]

    if status in {"in_progress", "final"}:
        observed = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state_entry["actual_start"] = observed
        return observed

    return None


def update_rows(date: str) -> int:
    state = load_state()
    existing = load_existing_games().set_index("game_id", drop=False)
    board = fetch_scoreboard(date)

    updated_rows: list[dict[str, Any]] = []
    for _, row in board.iterrows():
        game_id = str(row["GAME_ID"])
        existing_row = existing.loc[game_id] if game_id in existing.index else None

        scheduled_start = None
        if existing_row is not None and pd.notna(existing_row["scheduled_start"]):
            scheduled_start = str(existing_row["scheduled_start"])
        if not scheduled_start:
            scheduled_start = parse_scheduled_tip(date, row.get("GAME_STATUS_TEXT"))

        status = normalize_status(date, row)
        actual_start = derive_actual_start(
            state=state,
            existing_actual_start=(
                str(existing_row["actual_start"])
                if existing_row is not None and pd.notna(existing_row["actual_start"])
                else None
            ),
            game_id=game_id,
            status=status,
        )

        updated_rows.append(
            {
                "game_id": game_id,
                "date": date,
                "home_team": TEAM_BY_ID.get(int(row["HOME_TEAM_ID"]), str(row["HOME_TEAM_ID"])),
                "away_team": TEAM_BY_ID.get(
                    int(row["VISITOR_TEAM_ID"]), str(row["VISITOR_TEAM_ID"])
                ),
                "scheduled_start": scheduled_start,
                "actual_start": actual_start,
                "status": status,
            }
        )

    latest = pd.DataFrame(updated_rows, columns=CSV_COLUMNS).set_index("game_id", drop=False)
    merged = existing.combine_first(latest)
    merged.update(latest)

    save_games(merged.reset_index(drop=True))
    save_state(state)
    return len(updated_rows)


def main() -> None:
    args = parse_args()

    while True:
        count = update_rows(args.date)
        print(
            f"[{datetime.now().isoformat(timespec='seconds')}] updated {count} games for {args.date}"
        )

        if args.once:
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
