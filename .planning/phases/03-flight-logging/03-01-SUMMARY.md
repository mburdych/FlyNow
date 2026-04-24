# 03-01 Summary: Flight log backend contract

## Delivered

- Added backend constants for flight-log contract in `custom_components/flynow/const.py`.
- Wired service setup from integration entry setup in `custom_components/flynow/__init__.py`.
- Added new `custom_components/flynow/flight_log.py` with:
  - strict schemas (`LOG_FLIGHT_SCHEMA`, `LIST_FLIGHTS_SCHEMA`)
  - normalized record shape (`id`, `created_at`, `schema_version`, LOG-01 fields)
  - atomic JSON persistence to `/config/flynow_flights.json` via temp-file replacement
  - malformed JSON recovery (`flynow_flights.json.corrupt-<UTC-timestamp>`)
  - bounded newest-first history response (`FLIGHT_HISTORY_LIMIT = 200`)
  - idempotent domain service registration (`flynow.log_flight`, `flynow.list_flights`)
- Added HA service metadata in `custom_components/flynow/services.yaml`.
- Added backend regression suite in `tests/test_flight_log.py`.

## Verification

- `python -m pytest tests/test_flight_log.py -x` ✅
- `python -m pytest tests/test_coordinator.py -x` ✅

## Requirement coverage

- `LOG-01` backend service contract for form submission and listing is implemented.
- `LOG-02` local persistence at `/config/flynow_flights.json` with atomic writes and recovery behavior is implemented.
