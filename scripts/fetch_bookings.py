from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from otf.client import OTFClient
from otf_connector.config import load_settings
from otf_connector.logging import configure_logging


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    bookings = OTFClient(settings).get_bookings()
    print(json.dumps([booking.__dict__ | {"raw": booking.raw} for booking in bookings], default=str, indent=2))


if __name__ == "__main__":
    main()
