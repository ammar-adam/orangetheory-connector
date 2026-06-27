# Orangetheory Connector

Self-hosted Python service that syncs Orangetheory Fitness bookings to Google Calendar, enriches studio locations with Google Maps links, and posts completed workouts to Strava.

This is a weekend-build MVP. The OTF API is undocumented, so the first required step is capturing your own OTF endpoints and filling `api-spec.md`.

## What Works

- Local `.env` configuration
- SQLite dedupe database
- OTF auth/token cache scaffolding
- Google Calendar event creation
- Google Maps studio enrichment with API-key lookup or free fallback search URL
- Strava OAuth and manual activity creation
- APScheduler jobs
- Docker Compose local deployment
- `/health` endpoint for latest sync status

## What Still Requires Capture

The Orangetheory API endpoints are not included. Capture them with mitmproxy or browser DevTools and then configure:

```env
OTF_BASE_URL=
OTF_LOGIN_ENDPOINT=
OTF_REFRESH_ENDPOINT=
OTF_BOOKINGS_ENDPOINT=
OTF_WORKOUTS_ENDPOINT=
```

Document the captured details in `api-spec.md`.

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
```

Put Google OAuth credentials at:

```text
./data/google_client_secret.json
```

Then edit `.env`.

## Capture OTF API

On Windows:

```bash
pip install -r requirements-dev.txt
python scripts/start_capture.py
```

The script starts `mitmweb`, prints the Windows local IP address, and saves captured flows to:

```text
./data/otf-capture.mitm
```

Configure your iPhone WiFi HTTP proxy to the printed Windows IP on port `8080`, install the certificate from `http://mitm.it`, and trust it in iOS settings.

Capture:

- login
- upcoming schedule
- class detail
- completed workout summary

If iOS certificate pinning blocks capture, try the OTF web portal in browser DevTools or an Android capture path.

After capture, generate a redacted API draft:

```bash
python scripts/extract_otf_flows.py ./data/otf-capture.mitm
```

Review `api-spec.captured.md`, then move the confirmed endpoints and payload shapes into `api-spec.md`.

## Run Once

```bash
python scripts/sync_once.py
```

Run only Calendar:

```bash
python scripts/sync_once.py --only gcal
```

Run only Strava:

```bash
python scripts/sync_once.py --only strava
```

## Run Scheduled Service

```bash
docker compose up --build
```

Google Calendar sync runs every four hours. Strava sync runs daily at 6am in the configured timezone.

Health endpoint:

```text
http://localhost:8000/health
```

## Google Maps

Set `GOOGLE_MAPS_API_KEY` to use the Places API. If it is blank, the connector still adds a deterministic Google Maps search URL to calendar events.

## Strava

Create a Strava API app and set:

```env
STRAVA_CLIENT_ID=
STRAVA_CLIENT_SECRET=
```

On first run, the connector prints an authorization URL. Paste the returned code to create `STRAVA_TOKEN_PATH`.

## Duplicate Prevention

- Google Calendar events are deduped by `otf_booking_id`.
- Strava activities are deduped by `otf_workout_id`.
- Dedupe state is stored in SQLite at `DATABASE_PATH`.

## Cancellation Behavior

Set:

```env
CANCEL_BEHAVIOR=label
```

or:

```env
CANCEL_BEHAVIOR=delete
```

`label` updates stale calendar events with `[CANCELLED]`. `delete` removes them.
