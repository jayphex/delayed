from __future__ import annotations

import argparse
import time
from datetime import date, datetime, timezone

from sqlmodel import Session

from api.app.db.database import engine, prepare_database
from api.app.sync import sync_games_for_date


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync NBA game schedule and observed tip-off data into the Delayed database."
    )
    parser.add_argument(
        "--date",
        default=datetime.now(timezone.utc).date().isoformat(),
        help="Game date in YYYY-MM-DD format. Defaults to today in UTC.",
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
        help="Run one sync and exit.",
    )
    return parser.parse_args()


def run_sync(target_date: date) -> int:
    prepare_database()
    with Session(engine) as session:
        return sync_games_for_date(
            session,
            target_date,
            observed_at=datetime.now(timezone.utc),
        )


def main() -> None:
    args = parse_args()
    target_date = date.fromisoformat(args.date)

    while True:
        synced_games = run_sync(target_date)
        print(
            f"[{datetime.now().isoformat(timespec='seconds')}] synced {synced_games} games for {target_date.isoformat()}"
        )
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
