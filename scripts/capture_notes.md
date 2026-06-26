# OTF API Capture Notes

Use this file while capturing traffic. Move sanitized findings into `api-spec.md`.

## Windows + iPhone mitmproxy Checklist

1. Install mitmproxy.
2. Run `mitmweb --listen-port 8080`.
3. Find the Windows local IP address.
4. On iPhone, configure the WiFi HTTP proxy to the Windows IP and port `8080`.
5. Open `http://mitm.it` on the iPhone and install the mitmproxy certificate.
6. Trust the certificate under Settings > General > About > Certificate Trust Settings.
7. Open the Orangetheory app and capture:
   - login
   - upcoming schedule
   - class detail
   - completed workout summary
   - profile/stats page

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
