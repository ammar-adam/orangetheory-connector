from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    otf_email: str
    otf_password: str
    otf_base_url: str
    otf_login_endpoint: str
    otf_refresh_endpoint: str
    otf_bookings_endpoint: str
    otf_workouts_endpoint: str
    otf_token_path: Path
    google_client_secret_path: Path
    google_token_path: Path
    google_calendar_id: str
    google_maps_api_key: str
    strava_client_id: str
    strava_client_secret: str
    strava_token_path: Path
    database_path: Path
    timezone: str
    cancel_behavior: str
    log_level: str


def _path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def load_settings() -> Settings:
    load_dotenv()
    cancel_behavior = os.getenv("CANCEL_BEHAVIOR", "label").lower()
    if cancel_behavior not in {"label", "delete"}:
        raise ValueError("CANCEL_BEHAVIOR must be 'label' or 'delete'")

    return Settings(
        otf_email=os.getenv("OTF_EMAIL", ""),
        otf_password=os.getenv("OTF_PASSWORD", ""),
        otf_base_url=os.getenv("OTF_BASE_URL", "").rstrip("/"),
        otf_login_endpoint=os.getenv("OTF_LOGIN_ENDPOINT", ""),
        otf_refresh_endpoint=os.getenv("OTF_REFRESH_ENDPOINT", ""),
        otf_bookings_endpoint=os.getenv("OTF_BOOKINGS_ENDPOINT", ""),
        otf_workouts_endpoint=os.getenv("OTF_WORKOUTS_ENDPOINT", ""),
        otf_token_path=_path(os.getenv("OTF_TOKEN_PATH", "./data/otf_token.json")),
        google_client_secret_path=_path(
            os.getenv("GOOGLE_CLIENT_SECRET_PATH", "./data/google_client_secret.json")
        ),
        google_token_path=_path(os.getenv("GOOGLE_TOKEN_PATH", "./data/google_token.json")),
        google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY", ""),
        strava_client_id=os.getenv("STRAVA_CLIENT_ID", ""),
        strava_client_secret=os.getenv("STRAVA_CLIENT_SECRET", ""),
        strava_token_path=_path(os.getenv("STRAVA_TOKEN_PATH", "./data/strava_token.json")),
        database_path=_path(os.getenv("DATABASE_PATH", "./data/otf_connector.sqlite3")),
        timezone=os.getenv("TIMEZONE", "America/Toronto"),
        cancel_behavior=cancel_behavior,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
