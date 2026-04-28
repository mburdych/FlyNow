# Technology Stack

**Analysis Date:** 2026-04-28

## Languages

**Primary:**
- Python 3.12.x - Home Assistant integration runtime in `custom_components/flynow/*.py` (target host reports Python 3.12.13 in `.planning/reference/HAOS-DEPLOYMENT.md`).
- TypeScript (strict, ES2022 target) - Lovelace custom card in `lovelace/flynow-card/src/*.ts` with config in `lovelace/flynow-card/tsconfig.json`.

**Secondary:**
- JSON/YAML - integration metadata and service definitions in `custom_components/flynow/manifest.json`, `custom_components/flynow/services.yaml`, and translation files in `custom_components/flynow/translations/sk.json`.
- JavaScript (Node ESM script) - frontend bundling entry in `lovelace/flynow-card/scripts/build.mjs`.

## Runtime

**Environment:**
- Home Assistant Core (HAOS deployment): 2026.4.3 on Linux appliance, integration domain `flynow` in `custom_components/flynow/manifest.json`.
- Node.js runtime required for card build (exact version not pinned in repo; inferred from `lovelace/flynow-card/package.json` scripts and dependencies).

**Package Manager:**
- npm - used for card dependencies and build (`lovelace/flynow-card/package.json`).
- pip/Python environment tooling - implied by Python test usage in `tests/*.py` and documented commands in `CLAUDE.md`.
- Lockfile: present for frontend (`lovelace/flynow-card/package-lock.json`); no Python lockfile detected.

## Frameworks

**Core:**
- Home Assistant integration API - async config entry + coordinator patterns in `custom_components/flynow/__init__.py`, `custom_components/flynow/config_flow.py`, and `custom_components/flynow/coordinator.py`.
- Lit 3 (`lit`) - custom Lovelace Web Component in `lovelace/flynow-card/src/flynow-card.ts`.

**Testing:**
- pytest - Python tests under `tests/*.py` (e.g., `tests/test_coordinator.py`, `tests/test_notifications.py`).
- pytest anyio marker - async behavior tests (e.g., `tests/test_notifications.py`).

**Build/Dev:**
- TypeScript compiler (`tsc --noEmit`) and esbuild bundler (`lovelace/flynow-card/scripts/build.mjs`) invoked by `npm run build` in `lovelace/flynow-card/package.json`.

## Key Dependencies

**Critical:**
- `aiohttp` - outbound HTTP client for forecast fetch and timeout control in `custom_components/flynow/open_meteo.py` and `custom_components/flynow/coordinator.py`.
- `voluptuous` - config flow and service payload validation in `custom_components/flynow/config_flow.py` and `custom_components/flynow/flight_log.py`.
- `astral` - civil twilight computation fallback-enabled in `custom_components/flynow/coordinator.py`.
- `lit` - frontend rendering/reactivity for Lovelace card in `lovelace/flynow-card/src/flynow-card.ts`.

**Infrastructure:**
- Home Assistant service and entity APIs (`hass.services.async_call`, coordinator/entity abstractions) in `custom_components/flynow/notifications.py`, `custom_components/flynow/binary_sensor.py`, and `custom_components/flynow/sensor.py`.
- Local JSON persistence via Python stdlib (`json`, `tempfile`, atomic replace) in `custom_components/flynow/flight_log.py`.

## Configuration

**Environment:**
- Config is UI-driven via ConfigFlow (no YAML integration setup path detected) in `custom_components/flynow/config_flow.py`.
- Runtime options persisted in config entry data keys defined in `custom_components/flynow/const.py` (site, thresholds, update interval, notifier/calendar entity IDs).
- Flight history file path resolves inside HA config directory via `hass.config.path(...)` in `custom_components/flynow/flight_log.py`.

**Build:**
- Frontend: `lovelace/flynow-card/package.json`, `lovelace/flynow-card/tsconfig.json`, `lovelace/flynow-card/scripts/build.mjs`.
- Integration metadata: `custom_components/flynow/manifest.json`.

## Platform Requirements

**Development:**
- Python environment with Home Assistant integration imports available (tests contain import fallbacks but real runtime depends on HA modules) from `custom_components/flynow/*.py`.
- Node + npm for card build in `lovelace/flynow-card/package.json`.

**Production:**
- HAOS target host with deploy paths `/config/custom_components/flynow/` and `/config/www/flynow-card/` in `.planning/reference/HAOS-DEPLOYMENT.md`.
- SSH deployment workflow expects key-based auth and sudo-capable user as documented in `.planning/reference/HAOS-DEPLOYMENT.md`.

## Confidence and Unknowns

- High confidence: language/framework/tooling and major dependencies (directly evidenced in `manifest.json`, source imports, and card build files).
- Medium confidence: exact Node/npm versions (not pinned in repo), Python package pin set (no `requirements*.txt`/`pyproject.toml` detected).
- Unknown: CI runner/service configuration (`.github/workflows/` not detected in repository).

---

*Stack analysis: 2026-04-28*
