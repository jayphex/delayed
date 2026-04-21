from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


API_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = API_DIR.parent
DATA_DIR = REPO_DIR / "data"
load_dotenv(API_DIR / ".env")


def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    values = [item.strip() for item in raw.split(",")]
    return [value for value in values if value]


def _database_url() -> str:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError("DATABASE_URL is required for the API to start.")
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql://", 1)
    return raw


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: list[str]
    default_user_id: str
    sync_token: Optional[str]


@lru_cache
def get_settings() -> Settings:
    return Settings(
        database_url=_database_url(),
        cors_origins=_csv_env("CORS_ORIGINS", "http://localhost:3000"),
        default_user_id=os.getenv("DEFAULT_USER_ID", "demo"),
        sync_token=os.getenv("CRON_SECRET") or os.getenv("SYNC_TOKEN"),
    )
