from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class TokenState:
    access_token: str
    refresh_token: str | None = None
    expires_at: int | None = None
    raw: dict[str, Any] | None = None

    @property
    def should_refresh(self) -> bool:
        if not self.access_token:
            return True
        if self.expires_at is None:
            return False
        return self.expires_at <= int(time.time()) + 300


class TokenStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> TokenState | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return TokenState(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token"),
            expires_at=data.get("expires_at"),
            raw=data.get("raw"),
        )

    def save(self, token: TokenState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_at": token.expires_at,
            "raw": token.raw or {},
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def jwt_expiry(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    payload = parts[1] + "=" * (-len(parts[1]) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload)
        data = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return None
    exp = data.get("exp")
    return int(exp) if exp else None


def token_from_response(data: dict[str, Any]) -> TokenState:
    access_token = data.get("access_token") or data.get("token") or data.get("id_token")
    if not access_token:
        raise ValueError("OTF auth response did not include an access token")

    expires_at = None
    expires_in = data.get("expires_in")
    if expires_in:
        expires_at = int(time.time()) + int(expires_in)
    expires_at = expires_at or jwt_expiry(access_token)

    return TokenState(
        access_token=access_token,
        refresh_token=data.get("refresh_token"),
        expires_at=expires_at,
        raw=data,
    )
