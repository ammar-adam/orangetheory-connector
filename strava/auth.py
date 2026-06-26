from __future__ import annotations

import json
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path

import httpx

from otf_connector.config import Settings


@dataclass
class StravaToken:
    access_token: str
    refresh_token: str
    expires_at: int

    @property
    def expired(self) -> bool:
        return self.expires_at <= int(time.time()) + 300


class StravaAuth:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.http = httpx.Client(timeout=30)

    def access_token(self) -> str:
        token = self._load()
        if token and not token.expired:
            return token.access_token
        if token and token.refresh_token:
            token = self._refresh(token.refresh_token)
            self._save(token)
            return token.access_token
        token = self._interactive_auth()
        self._save(token)
        return token.access_token

    def _interactive_auth(self) -> StravaToken:
        if not self.settings.strava_client_id or not self.settings.strava_client_secret:
            raise RuntimeError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET are required")
        auth_url = (
            "https://www.strava.com/oauth/authorize"
            f"?client_id={self.settings.strava_client_id}"
            "&response_type=code"
            "&redirect_uri=http://localhost/exchange_token"
            "&approval_prompt=auto"
            "&scope=activity:write"
        )
        print("Open this Strava authorization URL and paste the returned code:")
        print(auth_url)
        try:
            webbrowser.open(auth_url)
        except webbrowser.Error:
            pass
        code = input("Strava code: ").strip()
        response = self.http.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": self.settings.strava_client_id,
                "client_secret": self.settings.strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        return self._from_response(response.json())

    def _refresh(self, refresh_token: str) -> StravaToken:
        response = self.http.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": self.settings.strava_client_id,
                "client_secret": self.settings.strava_client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        response.raise_for_status()
        return self._from_response(response.json())

    def _load(self) -> StravaToken | None:
        path = self.settings.strava_token_path
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return StravaToken(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=int(data["expires_at"]),
        )

    def _save(self, token: StravaToken) -> None:
        path: Path = self.settings.strava_token_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(token.__dict__, indent=2), encoding="utf-8")

    @staticmethod
    def _from_response(data: dict) -> StravaToken:
        return StravaToken(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=int(data["expires_at"]),
        )
