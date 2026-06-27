from __future__ import annotations

import argparse
import shutil
import socket
import subprocess
import sys
import webbrowser
from pathlib import Path


def local_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]


def main() -> None:
    parser = argparse.ArgumentParser(description="Start mitmweb for OTF API capture.")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--save-stream-file", default="./data/otf-capture.mitm")
    args = parser.parse_args()

    mitmweb = shutil.which("mitmweb")
    if not mitmweb:
        print("mitmweb is not installed or not on PATH.")
        print("Install dev dependencies with: pip install -r requirements-dev.txt")
        sys.exit(1)

    ip = local_ip()
    capture_file = Path(args.save_stream_file).resolve()
    capture_file.parent.mkdir(parents=True, exist_ok=True)

    print("Starting mitmweb for OTF capture.")
    print("")
    print("iPhone proxy settings:")
    print(f"  Server: {ip}")
    print(f"  Port:   {args.port}")
    print("")
    print("Certificate setup:")
    print("  1. On the iPhone, open http://mitm.it")
    print("  2. Install the iOS certificate")
    print("  3. Trust it under Settings > General > About > Certificate Trust Settings")
    print("")
    print("Capture these OTF app actions:")
    print("  1. Log out and log back in")
    print("  2. Open upcoming bookings")
    print("  3. Tap a class detail")
    print("  4. Open a completed workout summary")
    print("  5. Open profile/stats")
    print("")
    print(f"Flows will be saved to: {capture_file}")
    print("After capture, run:")
    print(f"  python scripts/extract_otf_flows.py {capture_file}")
    print("")

    webbrowser.open(f"http://127.0.0.1:{args.port + 1}")
    subprocess.run(
        [
            mitmweb,
            "--listen-port",
            str(args.port),
            "--web-port",
            str(args.port + 1),
            "--save-stream-file",
            str(capture_file),
        ],
        check=False,
    )


if __name__ == "__main__":
    main()
