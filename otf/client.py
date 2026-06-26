from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any

import httpx

from otf.auth import TokenState, TokenStore, token_from_response
from otf.models import Booking, Workout
from otf_connector.config import Settings

logger = logging.getLogger(__name__)


class OTFClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.token_store = TokenStore(settings.otf_token_path)
        self.http = httpx.Client(timeout=30)

    def login(self) -> TokenState:
        self._require_endpoint(self.settings.otf_login_endpoint, "OTF_LOGIN_ENDPOINT")
        if not self.settings.otf_email or not self.settings.otf_password:
            raise RuntimeError("OTF_EMAIL and OTF_PASSWORD are required")

        response = self._request(
            "POST",
            self._url(self.settings.otf_login_endpoint),
            json={"email": self.settings.otf_email, "password": self.settings.otf_password},
            auth_required=False,
        )
        token = token_from_response(response.json())
        self.token_store.save(token)
        return token

    def get_token(self) -> str:
        token = self.token_store.load()
        if token and not token.should_refresh:
            return token.access_token

        if token and token.refresh_token and self.settings.otf_refresh_endpoint:
            try:
                refreshed = self._refresh(token.refresh_token)
                self.token_store.save(refreshed)
                return refreshed.access_token
            except httpx.HTTPError:
                logger.warning("OTF token refresh failed; falling back to full login")

        return self.login().access_token

    def get_bookings(self) -> list[Booking]:
        self._require_endpoint(self.settings.otf_bookings_endpoint, "OTF_BOOKINGS_ENDPOINT")
        response = self._request("GET", self._url(self.settings.otf_bookings_endpoint))
        payload = response.json()
        items = self._items(payload, ("bookings", "classes", "data"))
        return [self._normalize_booking(item) for item in items]

    def get_past_workouts(self, days: int = 7) -> list[Workout]:
        self._require_endpoint(self.settings.otf_workouts_endpoint, "OTF_WORKOUTS_ENDPOINT")
        response = self._request(
            "GET",
            self._url(self.settings.otf_workouts_endpoint),
            params={"days": days},
        )
        payload = response.json()
        items = self._items(payload, ("workouts", "summaries", "data"))
        return [self._normalize_workout(item) for item in items]

    def _refresh(self, refresh_token: str) -> TokenState:
        response = self._request(
            "POST",
            self._url(self.settings.otf_refresh_endpoint),
            json={"refresh_token": refresh_token},
            auth_required=False,
        )
        return token_from_response(response.json())

    def _request(self, method: str, url: str, auth_required: bool = True, **kwargs: Any) -> httpx.Response:
        headers = kwargs.pop("headers", {})
        if auth_required:
            headers["Authorization"] = f"Bearer {self.get_token()}"

        delay = 1.0
        last_error: Exception | None = None
        for attempt in range(4):
            try:
                response = self.http.request(method, url, headers=headers, **kwargs)
                if response.status_code == 429:
                    logger.warning("OTF rate limited request to %s", url)
                response.raise_for_status()
                return response
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == 3:
                    break
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"OTF request failed after retries: {url}") from last_error

    def _url(self, endpoint: str) -> str:
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        if not self.settings.otf_base_url:
            raise RuntimeError("OTF_BASE_URL is required once endpoints are captured")
        return f"{self.settings.otf_base_url}/{endpoint.lstrip('/')}"

    @staticmethod
    def _require_endpoint(value: str, env_name: str) -> None:
        if not value:
            raise RuntimeError(f"{env_name} is not configured. Capture the OTF API and update .env.")

    @staticmethod
    def _items(payload: Any, keys: tuple[str, ...]) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in keys:
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            nested = payload.get("result")
            if isinstance(nested, dict):
                return OTFClient._items(nested, keys)
        raise ValueError("Could not find list of OTF records in response")

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime:
        if not value:
            raise ValueError("Missing datetime value in OTF response")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _normalize_booking(self, item: dict[str, Any]) -> Booking:
        start = self._parse_datetime(
            item.get("start_datetime") or item.get("startTime") or item.get("start_time")
        )
        end_value = item.get("end_datetime") or item.get("endTime") or item.get("end_time")
        end = self._parse_datetime(end_value) if end_value else start + timedelta(minutes=60)
        studio = item.get("studio") if isinstance(item.get("studio"), dict) else {}

        return Booking(
            otf_booking_id=str(item.get("id") or item.get("bookingId") or item.get("booking_id")),
            class_name=item.get("class_name") or item.get("className") or item.get("name") or "Orangetheory",
            studio_name=studio.get("name") or item.get("studio_name") or item.get("studioName") or "",
            studio_address=studio.get("address") or item.get("studio_address") or item.get("studioAddress") or "",
            start_datetime=start,
            end_datetime=end,
            raw=item,
        )

    def _normalize_workout(self, item: dict[str, Any]) -> Workout:
        zones = item.get("hr_zone_breakdown") or item.get("heartRateZones") or item.get("zones") or {}
        return Workout(
            otf_workout_id=str(item.get("id") or item.get("workoutId") or item.get("workout_id")),
            class_name=item.get("class_name") or item.get("className") or item.get("name") or "Orangetheory",
            completed_at=self._parse_datetime(
                item.get("completed_at") or item.get("completedAt") or item.get("start_time") or item.get("startTime")
            ),
            duration_minutes=self._int_or_none(item.get("duration_minutes") or item.get("durationMinutes")),
            calories=self._int_or_none(item.get("calories")),
            avg_hr=self._int_or_none(item.get("avg_hr") or item.get("averageHeartRate") or item.get("avgHeartRate")),
            splat_points=self._int_or_none(item.get("splat_points") or item.get("splatPoints")),
            hr_zone_breakdown=zones if isinstance(zones, dict) else {},
            raw=item,
        )

    @staticmethod
    def _int_or_none(value: Any) -> int | None:
        if value is None or value == "":
            return None
        return int(value)
