from __future__ import annotations

import logging

import httpx

from db.models import Database
from otf.client import OTFClient
from otf.models import Workout
from otf_connector.config import Settings
from strava.auth import StravaAuth

logger = logging.getLogger(__name__)


class StravaSync:
    def __init__(self, settings: Settings, db: Database, otf_client: OTFClient, auth: StravaAuth):
        self.settings = settings
        self.db = db
        self.otf_client = otf_client
        self.auth = auth
        self.http = httpx.Client(timeout=30)

    def run(self, days: int = 7) -> dict[str, int]:
        created = 0
        skipped = 0
        try:
            workouts = self.otf_client.get_past_workouts(days=days)
            for workout in workouts:
                if self.db.get_workout(workout.otf_workout_id):
                    skipped += 1
                    continue
                activity_id = self._create_activity(workout)
                self.db.save_workout(workout, activity_id)
                created += 1
            self.db.log_sync("strava", "success")
            return {"created": created, "skipped": skipped}
        except Exception as exc:
            logger.exception("Strava sync failed")
            self.db.log_sync("strava", "error", str(exc))
            raise

    def _create_activity(self, workout: Workout) -> str:
        response = self.http.post(
            "https://www.strava.com/api/v3/activities",
            headers={"Authorization": f"Bearer {self.auth.access_token()}"},
            data={
                "name": f"Orangetheory - {workout.class_name}",
                "type": "Workout",
                "start_date_local": workout.completed_at.isoformat(),
                "elapsed_time": (workout.duration_minutes or 60) * 60,
                "description": self._description(workout),
            },
        )
        response.raise_for_status()
        data = response.json()
        return str(data["id"])

    @staticmethod
    def _description(workout: Workout) -> str:
        lines = ["Synced from Orangetheory.", ""]
        if workout.calories is not None:
            lines.append(f"Calories: {workout.calories}")
        if workout.avg_hr is not None:
            lines.append(f"Average HR: {workout.avg_hr}")
        if workout.splat_points is not None:
            lines.append(f"Splat Points: {workout.splat_points}")
        if workout.hr_zone_breakdown:
            lines.extend(["", "HR Zones:"])
            for zone, value in workout.hr_zone_breakdown.items():
                lines.append(f"{zone}: {value}")
        return "\n".join(lines)
