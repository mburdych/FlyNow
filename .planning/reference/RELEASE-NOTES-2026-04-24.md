# Release Notes — 2026-04-24

## Summary

FlyNow moved from planned implementation to stable HAOS deployment with full end-to-end operation:

- Integration setup is healthy.
- Multi-site forecast status is rendered in Lovelace card.
- Flight logging form and backend persistence are operational.
- Day/night operational logic aligned to EASA/SERA civil twilight.

## Delivered capabilities

- Multi-site planning output for `lzmada`, `katarinka`, `nitra-luka`.
- GO/NO-GO evaluation with condition breakdown and launch windows.
- Notification orchestration framework with dedup state output.
- Local flight logging services:
  - `flynow.log_flight`
  - `flynow.list_flights`
- Atomic JSON persistence at `/config/flynow_flights.json`.
- Lovelace card sections:
  - Site comparison tiles
  - Condition thresholds
  - Launch window + sunrise/sunset + EASA day window
  - Flight log form + history list

## Production issues fixed same day

- Open-Meteo request field contract (`ceiling` -> `cloud_base`).
- Analyzer crash on `None` weather values (safe numeric filtering).
- Missing HA platform module (`binary_sensor.py` added).
- Custom card config contract (`setConfig` / `getCardSize` added).
- Card data-mapping regressions (`ok` handling, active-window key mapping).
- EASA civil twilight boundaries integrated into window calculations.

## Operational decision log

- **Regulatory basis:** EASA/SERA definition of night.
- **Product decision:** enforce EASA civil twilight operational boundary.
- **Implementation outcome:** `day_start` / `day_end` derived from civil twilight and surfaced in backend attributes + UI.

## Validation snapshot

- Local tests passing during stabilization:
  - `tests/test_coordinator.py`
  - `tests/test_analyzer.py`
  - `tests/test_flight_log.py`
  - `tests/test_card_contract.py`
- Frontend build passing:
  - `npm --prefix lovelace/flynow-card run build`
- Remote deploy verification:
  - Syntax compile for `/config/custom_components/flynow/*.py`
  - Presence of updated `/config/www/flynow-card/flynow-card.js`

## Follow-up (next milestone candidates)

- Improve ceiling reliability strategy when cloud-base data is missing/low-quality.
- Add translation polish for config flow and card copy.
- Add documented UAT checklist with screenshot baselines.
