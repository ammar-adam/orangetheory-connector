from __future__ import annotations

from fastapi import FastAPI

from db import Database
from otf_connector.config import load_settings

app = FastAPI(title="OTF Connector Health")


@app.get("/health")
def health() -> dict:
    settings = load_settings()
    db = Database(settings.database_path)
    return {"status": "ok", "syncs": db.latest_syncs()}
