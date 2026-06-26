from __future__ import annotations

import logging
import signal
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from db import Database
from gcal import GoogleCalendarSync
from maps import GoogleMapsClient
from otf import OTFClient
from otf_connector.config import load_settings
from otf_connector.logging import configure_logging
from strava import StravaAuth, StravaSync

logger = logging.getLogger(__name__)


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    db = Database(settings.database_path)
    otf_client = OTFClient(settings)
    maps_client = GoogleMapsClient(settings, db)
    strava_auth = StravaAuth(settings)

    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(
        lambda: GoogleCalendarSync(settings, db, otf_client, maps_client).run(),
        "interval",
        hours=4,
        id="gcal_sync",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.add_job(
        lambda: StravaSync(settings, db, otf_client, strava_auth).run(),
        "cron",
        hour=6,
        minute=0,
        id="strava_sync",
        replace_existing=True,
        max_instances=1,
    )

    logger.info("Starting scheduler")
    scheduler.start()
    stop = threading.Event()

    def handle_stop(*_: object) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    stop.wait()
    scheduler.shutdown()


if __name__ == "__main__":
    main()
