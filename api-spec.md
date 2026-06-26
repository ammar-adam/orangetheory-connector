# OTF API Specification

Status: pending capture.

This project depends on reverse engineering the Orangetheory Fitness API from the official app or web portal. Fill this document with sanitized request and response examples before enabling real sync.

## Capture Target

- OTF app version:
- Capture date:
- Capture path:
  - iOS + mitmproxy
  - Android + mitmproxy/Frida
  - OTF web portal + browser DevTools

## Required `.env` Values After Capture

```env
OTF_BASE_URL=
OTF_LOGIN_ENDPOINT=
OTF_REFRESH_ENDPOINT=
OTF_BOOKINGS_ENDPOINT=
OTF_WORKOUTS_ENDPOINT=
```

## Login

- Method:
- URL:
- Required headers:
- Request payload:
- Response payload:
- Access token field:
- Refresh token field:
- Expiry behavior:

## Upcoming Bookings

- Method:
- URL:
- Required headers:
- Query params:
- Response payload:

Required normalized fields:

- `otf_booking_id`
- `class_name`
- `studio_name`
- `studio_address`
- `start_datetime`
- `end_datetime`

## Past Workouts

- Method:
- URL:
- Required headers:
- Query params:
- Response payload:

Required normalized fields:

- `otf_workout_id`
- `class_name`
- `completed_at`
- `duration_minutes`
- `calories`
- `avg_hr`
- `splat_points`
- `hr_zone_breakdown`

## Rate Limits

- 429 observed:
- Retry headers:
- Other throttling behavior:

## Certificate Pinning

- Pinning observed:
- Workaround:
