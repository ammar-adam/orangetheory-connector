from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

import httpx

from db.models import Database
from otf_connector.config import Settings


@dataclass(frozen=True)
class StudioLocation:
    formatted_address: str
    google_maps_url: str
    place_id: str | None = None


class GoogleMapsClient:
    def __init__(self, settings: Settings, db: Database):
        self.settings = settings
        self.db = db
        self.http = httpx.Client(timeout=15)

    def enrich(self, studio_name: str, studio_address: str) -> StudioLocation:
        cache_key = self._cache_key(studio_name, studio_address)
        cached = self.db.get_studio_location(cache_key)
        if cached:
            return StudioLocation(
                formatted_address=cached["formatted_address"],
                google_maps_url=cached["google_maps_url"],
                place_id=cached["google_maps_place_id"],
            )

        location = self._lookup(studio_name, studio_address)
        self.db.save_studio_location(
            cache_key,
            studio_name,
            studio_address,
            location.formatted_address,
            location.place_id,
            location.google_maps_url,
        )
        return location

    def _lookup(self, studio_name: str, studio_address: str) -> StudioLocation:
        query = " ".join(part for part in [studio_name, studio_address] if part).strip()
        fallback_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"
        if not self.settings.google_maps_api_key:
            return StudioLocation(
                formatted_address=studio_address,
                google_maps_url=fallback_url,
                place_id=None,
            )

        response = self.http.get(
            "https://maps.googleapis.com/maps/api/place/findplacefromtext/json",
            params={
                "input": query,
                "inputtype": "textquery",
                "fields": "formatted_address,place_id",
                "key": self.settings.google_maps_api_key,
            },
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return StudioLocation(studio_address, fallback_url, None)

        candidate = candidates[0]
        place_id = candidate.get("place_id")
        maps_url = (
            f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}&query_place_id={place_id}"
            if place_id
            else fallback_url
        )
        return StudioLocation(
            formatted_address=candidate.get("formatted_address") or studio_address,
            google_maps_url=maps_url,
            place_id=place_id,
        )

    @staticmethod
    def _cache_key(studio_name: str, studio_address: str) -> str:
        return f"{studio_name.lower().strip()}|{studio_address.lower().strip()}"
