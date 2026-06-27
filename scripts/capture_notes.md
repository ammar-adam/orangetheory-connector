# OTF API Capture Notes

Use this file while capturing traffic. Move sanitized findings into `api-spec.md`.

## Windows + iPhone mitmproxy Checklist

1. Install dev dependencies with `pip install -r requirements-dev.txt`.
2. Run `python scripts/start_capture.py`.
3. On iPhone, configure the WiFi HTTP proxy to the printed Windows IP and port `8080`.
4. Open `http://mitm.it` on the iPhone and install the mitmproxy certificate.
5. Trust the certificate under Settings > General > About > Certificate Trust Settings.
6. Open the Orangetheory app and capture:
   - login
   - upcoming schedule
   - class detail
   - completed workout summary
   - profile/stats page
7. Stop capture and run `python scripts/extract_otf_flows.py ./data/otf-capture.mitm`.
8. Review `api-spec.captured.md` and move confirmed details into `api-spec.md`.

## Endpoints

### Login

- Method:
- URL:
- Required headers:
- Request body:
- Response body:
- Token expiry:
- Refresh token:

### Upcoming Bookings

- Method:
- URL:
- Required headers:
- Response body:

### Past Workouts

- Method:
- URL:
- Required headers:
- Response body:

## Notes

- Certificate pinning observed:
- Rate limit headers:
- OTF app version:
