# Orangetheory Connector Weekend Build Plan

Repo: git@github.com:ammar-adam/orangetheory-connector.git

## Weekend Goal

Build a self-hosted Python MVP that:

1. Fetches upcoming Orangetheory bookings from the reverse engineered OTF API.
2. Enriches studio locations with Google Maps links.
3. Creates deduplicated Google Calendar events for upcoming classes.
4. Fetches completed workout summaries.
5. Posts completed workouts to Strava without duplicates.

The weekend build is not a polished public launch. It is a working vertical slice proving that OTF auth, booking sync, Maps enrichment, and Strava posting all work end to end.

## Hard Scope

Included:

- Python service
- `.env` configuration
- SQLite dedupe database
- OTF auth and token cache
- upcoming bookings fetch
- completed workouts fetch, if exposed by OTF API
- Google Calendar event creation
- Google Maps location enrichment
- Strava manual activity creation
- Docker Compose local run
- `api-spec.md` with captured endpoints

Excluded:

- Web UI
- mobile app
- shared server
- class booking or cancellation
- Apple Health, Garmin, Wahoo
- Railway button
- full alerting
- complex health dashboard
- multi-user support

## Architecture

```text
OTF API
  -> otf/client.py
  -> normalized bookings/workouts
  -> SQLite dedupe tables
  -> Google Calendar sync
       -> Google Maps enrichment for studio address/map link
  -> Strava sync
```

## Repo Structure

```text
orangetheory-connector/
  otf/
    __init__.py
    auth.py
    client.py
    models.py
  gcal/
    __init__.py
    sync.py
  maps/
    __init__.py
    client.py
  strava/
    __init__.py
    auth.py
    sync.py
  db/
    __init__.py
    models.py
    migrations.py
  scripts/
    capture_notes.md
    fetch_bookings.py
    fetch_workouts.py
    sync_once.py
  data/
    .gitkeep
  api-spec.md
  scheduler.py
  health.py
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
  README.md
```

## Environment Variables

```env
OTF_EMAIL=
OTF_PASSWORD=
OTF_TOKEN_PATH=./data/otf_token.json

GOOGLE_CLIENT_SECRET_PATH=./data/google_client_secret.json
GOOGLE_TOKEN_PATH=./data/google_token.json
GOOGLE_CALENDAR_ID=primary
GOOGLE_MAPS_API_KEY=

STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
STRAVA_TOKEN_PATH=./data/strava_token.json

DATABASE_PATH=./data/otf_connector.sqlite3
TIMEZONE=America/Toronto
CANCEL_BEHAVIOR=label
```

## Data Model

### bookings

- `otf_booking_id` primary key
- `gcal_event_id`
- `class_name`
- `class_time`
- `studio_name`
- `studio_address`
- `google_maps_place_id`
- `google_maps_url`
- `synced_at`
- `status`

### workouts

- `otf_workout_id` primary key
- `strava_activity_id`
- `class_name`
- `completed_at`
- `duration_minutes`
- `calories`
- `avg_hr`
- `splat_points`
- `hr_zone_breakdown_json`
- `synced_at`

### sync_log

- `id`
- `sync_type`
- `status`
- `timestamp`
- `error_message`

## Google Maps Role

Google Maps should be used for studio enrichment, not as a separate user-facing product.

For every booking:

1. Take `studio_name` and `studio_address` from OTF.
2. Call Google Maps Places API or Geocoding API.
3. Store:
   - `place_id`
   - normalized formatted address
   - Google Maps URL
4. Put the Maps URL in the Google Calendar event description.
5. Use the normalized address as the event location.

Calendar event description format:

```text
Orangetheory class synced by OTF Connector.

Studio: OTF Example Studio
Address: 123 Main St, Toronto, ON
Map: https://www.google.com/maps/search/?api=1&query=...
OTF Booking ID: abc123
```

Weekend simplification:

- Cache Maps lookups by `studio_name + studio_address`.
- If Maps API fails, still create the calendar event using the raw OTF address.

## Strava Role

Strava sync should create manual activities for completed OTF workouts.

Activity fields:

- `name`: `Orangetheory - {class_name}`
- `type`: `Workout`
- `start_date_local`: workout completion/start time
- `elapsed_time`: duration in seconds
- `description`: splat points, calories, average HR, HR zones

Description format:

```text
Synced from Orangetheory.

Calories: 520
Average HR: 148
Splat Points: 18

HR Zones:
Zone 1: 4 min
Zone 2: 9 min
Zone 3: 14 min
Zone 4: 18 min
Zone 5: 5 min
```

Weekend simplification:

- Sync workouts from the last 7 days, not full history.
- If OTF workout stats are incomplete, post what exists and omit missing fields.
- If past workouts are not exposed by OTF API, leave Strava sync implemented behind a fixture/sample payload and document the blocker in `api-spec.md`.

## Schedule

### Friday Night: Repo and API Capture

Deliverables:

- repo initialized
- base Python project committed
- mitmproxy capture completed or blocker documented
- `api-spec.md` started

Tasks:

1. Set up Python project.
2. Add `.env.example`.
3. Add SQLite schema.
4. Run mitmweb on Windows.
5. Capture:
   - login
   - upcoming bookings
   - class detail
   - completed workout summary
6. Sanitize and paste examples into `api-spec.md`.

Exit criteria:

- You know whether iOS capture works.
- You have at least one OTF endpoint mapped.
- You know whether workout stats are available.

### Saturday Morning: OTF Client

Deliverables:

- `OTFClient.login()`
- `OTFClient.get_bookings()`
- `OTFClient.get_past_workouts()`
- token cache
- normalized models

Tasks:

1. Implement token storage in `otf/auth.py`.
2. Decode JWT expiry if applicable.
3. Re-auth when token is expired or near expiry.
4. Normalize bookings.
5. Normalize workouts.
6. Add scripts:
   - `scripts/fetch_bookings.py`
   - `scripts/fetch_workouts.py`

Exit criteria:

- `python scripts/fetch_bookings.py` prints upcoming bookings.
- `python scripts/fetch_workouts.py` prints recent workouts or a documented API blocker.

### Saturday Afternoon: Google Calendar and Google Maps

Deliverables:

- Google OAuth token handling
- Maps enrichment client
- deduped Calendar event creation

Tasks:

1. Implement Google OAuth.
2. Implement `maps/client.py`.
3. Cache Maps results in SQLite or a simple `studio_locations` table if needed.
4. Implement event creation in `gcal/sync.py`.
5. Dedupe by `otf_booking_id`.
6. Add cancellation labeling.

Exit criteria:

- First sync creates calendar events.
- Second sync creates zero duplicates.
- Calendar event contains studio address and Google Maps link.

### Saturday Night: Strava

Deliverables:

- Strava OAuth token handling
- manual activity creation
- workout dedupe

Tasks:

1. Implement Strava auth exchange.
2. Implement refresh-token flow.
3. Implement activity creation.
4. Store `otf_workout_id -> strava_activity_id`.
5. Format readable stats description.

Exit criteria:

- One OTF workout becomes one Strava activity.
- Re-running sync does not create a duplicate.

### Sunday Morning: Orchestration

Deliverables:

- `scripts/sync_once.py`
- `scheduler.py`
- Docker Compose run

Tasks:

1. Implement `sync_once.py` to run bookings and workouts once.
2. Implement APScheduler:
   - GCal every 4 hours
   - Strava daily at 6am
3. Add Dockerfile.
4. Add docker-compose.yml with `./data` mounted as a volume.

Exit criteria:

- `python scripts/sync_once.py` works locally.
- `docker compose up` starts the scheduler.

### Sunday Afternoon: README and Hardening

Deliverables:

- README
- final `api-spec.md`
- known limitations
- setup instructions

Tasks:

1. Document Windows mitmproxy capture.
2. Document required Google APIs:
   - Google Calendar API
   - Google Maps Places API or Geocoding API
3. Document Strava app setup.
4. Document `.env`.
5. Add troubleshooting:
   - OTF certificate pinning
   - auth failures
   - duplicate prevention
   - missing workout stats

Exit criteria:

- A technical user can clone, configure `.env`, and run the connector.

## Implementation Order

1. `api-spec.md`
2. SQLite schema
3. OTF auth
4. OTF bookings
5. Google Maps enrichment
6. Google Calendar sync
7. OTF workouts
8. Strava auth
9. Strava sync
10. scheduler and Docker
11. README

## Weekend Acceptance Criteria

- OTF upcoming bookings are fetched from the real API.
- Google Calendar events are created with no duplicates.
- Each calendar event includes a Google Maps URL for the studio.
- Completed workouts are posted to Strava, or a documented API blocker explains why they cannot be.
- SQLite prevents duplicate Calendar events and duplicate Strava activities.
- One command runs the app locally:

```bash
docker compose up
```

## Biggest Risks

### OTF API capture fails

Mitigation:

- Try OTF web portal in browser DevTools.
- Try Android capture if iOS certificate pinning blocks mitmproxy.
- Continue building against sanitized fixtures only if real capture is blocked.

### OTF does not expose workout stats

Mitigation:

- Ship Calendar + Maps MVP.
- Keep Strava integration implemented but disabled until workout endpoint is mapped.

### Google Maps API billing friction

Mitigation:

- Make Maps API optional.
- Fallback to deterministic Google Maps search URL:

```text
https://www.google.com/maps/search/?api=1&query={encoded_studio_address}
```

### Strava manual activity fields are limited

Mitigation:

- Put detailed OTF stats in the activity description.
- Use standard Strava fields only for elapsed time, type, name, and calories if accepted.

## Definition of Done

The weekend build is done when:

1. `api-spec.md` explains the captured OTF API clearly.
2. `scripts/sync_once.py` can run bookings and workout syncs.
3. Google Calendar events include class time, studio address, and Google Maps link.
4. Strava receives workout activities without duplicate posting.
5. `docker compose up` runs the scheduled service.
6. README explains setup from a fresh clone.
