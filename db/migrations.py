from __future__ import annotations

SCHEMA = """
CREATE TABLE IF NOT EXISTS bookings (
    otf_booking_id TEXT PRIMARY KEY,
    gcal_event_id TEXT,
    class_name TEXT NOT NULL,
    class_time TEXT NOT NULL,
    studio_name TEXT,
    studio_address TEXT,
    google_maps_place_id TEXT,
    google_maps_url TEXT,
    synced_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'cancelled'))
);

CREATE TABLE IF NOT EXISTS workouts (
    otf_workout_id TEXT PRIMARY KEY,
    strava_activity_id TEXT,
    class_name TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    duration_minutes INTEGER,
    calories INTEGER,
    avg_hr INTEGER,
    splat_points INTEGER,
    hr_zone_breakdown_json TEXT,
    synced_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type TEXT NOT NULL CHECK (sync_type IN ('gcal', 'strava')),
    status TEXT NOT NULL CHECK (status IN ('success', 'error')),
    timestamp TEXT NOT NULL,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS studio_locations (
    cache_key TEXT PRIMARY KEY,
    studio_name TEXT,
    studio_address TEXT,
    formatted_address TEXT,
    google_maps_place_id TEXT,
    google_maps_url TEXT,
    updated_at TEXT NOT NULL
);
"""
