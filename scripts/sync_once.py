from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db import Database
from gcal import GoogleCalendarSync
from maps import GoogleMapsClient
from otf import OTFClient
from otf_connector.config import load_settings
from otf_connector.logging import configure_logging
from strava import StravaAuth, StravaSync


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["gcal", "strava"], help="Run only one sync type")
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_level)
    db = Database(settings.database_path)
    otf_client = OTFClient(settings)
    results = {}

    if args.only in {None, "gcal"}:
        maps_client = GoogleMapsClient(settings, db)
        results["gcal"] = GoogleCalendarSync(settings, db, otf_client, maps_client).run()

    if args.only in {None, "strava"}:
        auth = StravaAuth(settings)
        results["strava"] = StravaSync(settings, db, otf_client, auth).run()

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
