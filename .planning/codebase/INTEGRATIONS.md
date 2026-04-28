# External Integrations

**Analysis Date:** 2026-04-28

## APIs & External Services

**Weather API:**
- Open-Meteo Forecast API - weather inputs for go/no-go analysis.
  - Endpoint evidence: `https://api.open-meteo.com/v1/forecast` in `custom_components/flynow/open_meteo.py`.
  - Request contract: hourly fields (`wind_speed_10m`, `wind_speed_975hPa`, `wind_speed_925hPa`, `precipitation_probability`, `visibility`, `relative_humidity_2m`, `temperature_2m`, `dew_point_2m`) and daily `sunrise,sunset` in `custom_components/flynow/open_meteo.py`.
  - Auth: none detected (no API key or auth header usage in `custom_components/flynow/open_meteo.py`).

**Home Assistant service bus:**
- Notification fanout - calls `notify.send_message` for crew, pilot, and WhatsApp notifier entities in `custom_components/flynow/notifications.py`.
- Calendar event creation - calls `calendar.create_event` in `custom_components/flynow/notifications.py`.
- Internal domain services - exposes `flynow.log_flight` and `flynow.list_flights` in `custom_components/flynow/flight_log.py` and schema in `custom_components/flynow/services.yaml`.

## Data Storage

**Databases:**
- Not detected.
  - No ORM/client dependencies found; persistence is file-based.

**File Storage:**
- Local filesystem in HA config directory.
  - Primary store: `flynow_flights.json` (resolved via `hass.config.path(...)`) in `custom_components/flynow/flight_log.py`.
  - Write strategy: temp file + atomic replace with retry on `PermissionError` in `custom_components/flynow/flight_log.py`.

**Caching:**
- In-memory runtime state only.
  - Previous window snapshot and notification dedup timestamps in `custom_components/flynow/coordinator.py`.
  - Last-known UI state cache in card component `lovelace/flynow-card/src/flynow-card.ts`.

## Authentication & Identity

**Auth Provider:**
- Home Assistant auth/session model (implicit; integration uses `hass` context and service APIs in `custom_components/flynow/*.py`).
  - No custom user auth provider in code.

**External API auth:**
- Open-Meteo requests are unauthenticated in current implementation (`custom_components/flynow/open_meteo.py`).

## Monitoring & Observability

**Error Tracking:**
- No external APM or error tracker detected.

**Logs:**
- Python `logging` used for warnings/errors in `custom_components/flynow/coordinator.py` and `custom_components/flynow/flight_log.py`.
- Operational log inspection guidance documented in `.planning/reference/HAOS-DEPLOYMENT.md`.

## CI/CD & Deployment

**Hosting:**
- Home Assistant OS target at `192.168.68.111` (user `miro`) documented in `.planning/reference/HAOS-DEPLOYMENT.md`.

**CI Pipeline:**
- Not detected (`.github/workflows/` absent in repository).

**Deployment path contracts:**
- Backend integration: `custom_components/flynow/` -> `/config/custom_components/flynow/` in `.planning/reference/HAOS-DEPLOYMENT.md`.
- Frontend card bundle: `lovelace/flynow-card/dist/` -> `/config/www/flynow-card/` served as `/local/flynow-card/flynow-card.js` in `.planning/reference/HAOS-DEPLOYMENT.md`.
- Transport method: tar-over-SSH deploy commands documented in `.planning/reference/HAOS-DEPLOYMENT.md`.

## Environment Configuration

**Required runtime config fields (Config Entry):**
- Site/forecast params and thresholds from `custom_components/flynow/const.py` and `custom_components/flynow/config_flow.py`.
- Required notifier/calendar entity IDs validated in `custom_components/flynow/config_flow.py`:
  - `crew_notifier`, `pilot_notifier`, `whatsapp_notifier` must be `notify.*`.
  - `calendar_entity` must be `calendar.*`.

**Secrets location:**
- No app-managed secret file usage detected in repo code.
- Deployment SSH key path is documented externally in `.planning/reference/HAOS-DEPLOYMENT.md`; key file itself is outside repository.

## Webhooks & Callbacks

**Incoming:**
- None detected (no webhook endpoints or HTTP server routes in integration code).

**Outgoing:**
- HTTPS GET to Open-Meteo endpoint from `custom_components/flynow/open_meteo.py`.
- Home Assistant internal service invocations via `hass.services.async_call` in `custom_components/flynow/notifications.py`.

## Data Contracts

**Weather payload contract (internal normalization):**
- `fetch_forecast()` returns `{ "hourly": ..., "daily": ... }` in `custom_components/flynow/open_meteo.py`.
- Coordinator expects `daily.sunrise` and `daily.sunset` arrays in `custom_components/flynow/coordinator.py`.

**Entity contract to Lovelace card:**
- Card reads `binary_sensor.flynow_status` attributes in `lovelace/flynow-card/src/flynow-card.ts`.
- Attribute/interface expectations defined in `lovelace/flynow-card/src/types.ts` (e.g., `sites_summary`, `sites`, `active_window`, condition sets).

**Flight log service contract:**
- Request payload and response shape validated in `custom_components/flynow/flight_log.py` and reflected in `lovelace/flynow-card/src/flight-log-types.ts`.

## Confidence and Unknowns

- High confidence: Open-Meteo integration, HA service integrations, data file persistence, deploy target mapping (all directly evidenced in source/config files).
- Medium confidence: operational notify backend details for specific entity IDs (`notify.whatsapp_callmebot`, mobile app notifiers) because they are deployment-environment specific and documented in `.planning/reference/HAOS-DEPLOYMENT.md`, not in integration source logic.
- Unknown: external CI integrations or cloud observability stack (no in-repo configuration found).

---

*Integration audit: 2026-04-28*
