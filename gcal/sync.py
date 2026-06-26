from __future__ import annotations

import logging
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from db.models import Database
from maps.client import GoogleMapsClient, StudioLocation
from otf.client import OTFClient
from otf.models import Booking
from otf_connector.config import Settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class GoogleCalendarSync:
    def __init__(self, settings: Settings, db: Database, otf_client: OTFClient, maps_client: GoogleMapsClient):
        self.settings = settings
        self.db = db
        self.otf_client = otf_client
        self.maps_client = maps_client

    def run(self) -> dict[str, int]:
        created = 0
        cancelled = 0
        try:
            service = self._service()
            bookings = self.otf_client.get_bookings()
            remote_ids = {booking.otf_booking_id for booking in bookings}

            for booking in bookings:
                if self.db.get_booking(booking.otf_booking_id):
                    continue
                location = self.maps_client.enrich(booking.studio_name, booking.studio_address)
                event_id = self._create_event(service, booking, location)
                self.db.save_booking(booking, event_id, location.place_id, location.google_maps_url)
                created += 1

            for stale_id in self.db.active_booking_ids() - remote_ids:
                row = self.db.get_booking(stale_id)
                if not row:
                    continue
                self._handle_cancelled(service, row["gcal_event_id"])
                self.db.mark_booking_cancelled(stale_id)
                cancelled += 1

            self.db.log_sync("gcal", "success")
            return {"created": created, "cancelled": cancelled}
        except Exception as exc:
            logger.exception("Google Calendar sync failed")
            self.db.log_sync("gcal", "error", str(exc))
            raise

    def _service(self):
        creds = None
        if self.settings.google_token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.settings.google_token_path), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.settings.google_client_secret_path.exists():
                    raise RuntimeError(
                        "Google client secret is missing. Put it at GOOGLE_CLIENT_SECRET_PATH."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.settings.google_client_secret_path),
                    SCOPES,
                )
                creds = flow.run_local_server(port=0)
            self.settings.google_token_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings.google_token_path.write_text(creds.to_json(), encoding="utf-8")

        return build("calendar", "v3", credentials=creds)

    def _create_event(self, service, booking: Booking, location: StudioLocation) -> str:
        event = {
            "summary": booking.class_name,
            "location": location.formatted_address or booking.studio_address,
            "description": self._description(booking, location),
            "start": {
                "dateTime": booking.start_datetime.isoformat(),
                "timeZone": self.settings.timezone,
            },
            "end": {
                "dateTime": booking.end_datetime.isoformat(),
                "timeZone": self.settings.timezone,
            },
            "extendedProperties": {
                "private": {"otf_booking_id": booking.otf_booking_id},
            },
        }
        created = (
            service.events()
            .insert(calendarId=self.settings.google_calendar_id, body=event)
            .execute()
        )
        return created["id"]

    def _handle_cancelled(self, service, event_id: str | None) -> None:
        if not event_id:
            return
        if self.settings.cancel_behavior == "delete":
            service.events().delete(calendarId=self.settings.google_calendar_id, eventId=event_id).execute()
            return

        event = service.events().get(calendarId=self.settings.google_calendar_id, eventId=event_id).execute()
        summary = event.get("summary", "")
        if not summary.startswith("[CANCELLED] "):
            event["summary"] = f"[CANCELLED] {summary}"
        service.events().update(
            calendarId=self.settings.google_calendar_id,
            eventId=event_id,
            body=event,
        ).execute()

    @staticmethod
    def _description(booking: Booking, location: StudioLocation) -> str:
        return "\n".join(
            [
                "Orangetheory class synced by OTF Connector.",
                "",
                f"Studio: {booking.studio_name}",
                f"Address: {location.formatted_address or booking.studio_address}",
                f"Map: {location.google_maps_url}",
                f"OTF Booking ID: {booking.otf_booking_id}",
                f"Synced at: {datetime.utcnow().isoformat()}Z",
            ]
        )
