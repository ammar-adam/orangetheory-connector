from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Booking:
    otf_booking_id: str
    class_name: str
    studio_name: str
    studio_address: str
    start_datetime: datetime
    end_datetime: datetime
    raw: dict


@dataclass(frozen=True)
class Workout:
    otf_workout_id: str
    class_name: str
    completed_at: datetime
    duration_minutes: int | None
    calories: int | None
    avg_hr: int | None
    splat_points: int | None
    hr_zone_breakdown: dict[str, int | float | None]
    raw: dict
