from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from db.migrations import SCHEMA
from otf.models import Booking, Workout


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def migrate(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.executescript(SCHEMA)

    def get_booking(self, otf_booking_id: str) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM bookings WHERE otf_booking_id = ?",
                (otf_booking_id,),
            ).fetchone()

    def active_booking_ids(self) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT otf_booking_id FROM bookings WHERE status = 'active'").fetchall()
        return {row["otf_booking_id"] for row in rows}

    def save_booking(
        self,
        booking: Booking,
        gcal_event_id: str,
        google_maps_place_id: str | None,
        google_maps_url: str | None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO bookings (
                    otf_booking_id, gcal_event_id, class_name, class_time, studio_name,
                    studio_address, google_maps_place_id, google_maps_url, synced_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (
                    booking.otf_booking_id,
                    gcal_event_id,
                    booking.class_name,
                    booking.start_datetime.isoformat(),
                    booking.studio_name,
                    booking.studio_address,
                    google_maps_place_id,
                    google_maps_url,
                    utc_now(),
                ),
            )

    def mark_booking_cancelled(self, otf_booking_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE bookings SET status = 'cancelled', synced_at = ? WHERE otf_booking_id = ?",
                (utc_now(), otf_booking_id),
            )

    def get_workout(self, otf_workout_id: str) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM workouts WHERE otf_workout_id = ?",
                (otf_workout_id,),
            ).fetchone()

    def save_workout(self, workout: Workout, strava_activity_id: str) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workouts (
                    otf_workout_id, strava_activity_id, class_name, completed_at,
                    duration_minutes, calories, avg_hr, splat_points,
                    hr_zone_breakdown_json, synced_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workout.otf_workout_id,
                    strava_activity_id,
                    workout.class_name,
                    workout.completed_at.isoformat(),
                    workout.duration_minutes,
                    workout.calories,
                    workout.avg_hr,
                    workout.splat_points,
                    json.dumps(workout.hr_zone_breakdown),
                    utc_now(),
                ),
            )

    def get_studio_location(self, cache_key: str) -> sqlite3.Row | None:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM studio_locations WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()

    def save_studio_location(
        self,
        cache_key: str,
        studio_name: str,
        studio_address: str,
        formatted_address: str,
        google_maps_place_id: str | None,
        google_maps_url: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO studio_locations (
                    cache_key, studio_name, studio_address, formatted_address,
                    google_maps_place_id, google_maps_url, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cache_key,
                    studio_name,
                    studio_address,
                    formatted_address,
                    google_maps_place_id,
                    google_maps_url,
                    utc_now(),
                ),
            )

    def log_sync(self, sync_type: str, status: str, error_message: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO sync_log (sync_type, status, timestamp, error_message)
                VALUES (?, ?, ?, ?)
                """,
                (sync_type, status, utc_now(), error_message),
            )

    def latest_syncs(self) -> list[dict]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT sync_type, status, timestamp, error_message
                FROM sync_log
                WHERE id IN (SELECT MAX(id) FROM sync_log GROUP BY sync_type)
                ORDER BY sync_type
                """
            ).fetchall()
        return [dict(row) for row in rows]
