# Architecture

**Analysis Date:** 2026-04-28

## Pattern Overview

**Overall:** Home Assistant coordinator-centric backend + Lovelace custom-card frontend with entity-attribute contracts.

**Key Characteristics:**
- One integration-level runtime coordinator computes all site/window decisions in `custom_components/flynow/coordinator.py`.
- One binary sensor entity projects coordinator state into Home Assistant state machine in `custom_components/flynow/sensor.py`.
- Frontend card reads entity attributes and calls integration domain services directly in `lovelace/flynow-card/src/flynow-card.ts`.

## Layers

**Integration Entry Layer:**
- Purpose: Bootstrap config entries, migrations, coordinator lifecycle, and platform forwarding.
- Location: `custom_components/flynow/__init__.py`
- Contains: `async_setup_entry`, `async_unload_entry`, `async_migrate_entry`.
- Depends on: coordinator, constants, flight-log service registration.
- Used by: Home Assistant config entry runtime.

**Configuration Layer:**
- Purpose: Collect and validate setup values via multi-step UI flow.
- Location: `custom_components/flynow/config_flow.py`, copy text in `custom_components/flynow/strings.json` and `custom_components/flynow/translations/sk.json`.
- Contains: user step, flight parameters step, thresholds step, notifications step.
- Depends on: constants/ranges from `custom_components/flynow/const.py`.
- Used by: Home Assistant integration setup UI.

**Forecast Orchestration Layer:**
- Purpose: Pull weather, build windows, evaluate go/no-go, maintain dedup state, fan out notifications.
- Location: `custom_components/flynow/coordinator.py`
- Contains: `FlyNowCoordinator._async_update_data()`, EASA day-boundary helper.
- Depends on: `custom_components/flynow/open_meteo.py`, `custom_components/flynow/windows.py`, `custom_components/flynow/analyzer.py`, `custom_components/flynow/notifications.py`.
- Used by: entity projection layer.

**Domain Logic Layer:**
- Purpose: Evaluate suitability metrics and construct launch windows.
- Location: `custom_components/flynow/analyzer.py`, `custom_components/flynow/windows.py`
- Contains: strict-AND threshold checks, non-blocking fog-risk metric, morning/evening window composition.
- Depends on: normalized hourly weather payload and configured thresholds.
- Used by: coordinator update cycle.

**Outbound Integration Layer:**
- Purpose: Integrate with external APIs and HA services.
- Location: `custom_components/flynow/open_meteo.py`, `custom_components/flynow/notifications.py`
- Contains: Open-Meteo fetch/normalization, notify/calendar service calls, transition dedup/cooldown.
- Depends on: `aiohttp`, HA service registry.
- Used by: coordinator runtime.

**Entity Projection Layer:**
- Purpose: Provide authoritative HA state and contract-rich attributes for automation/card usage.
- Location: `custom_components/flynow/sensor.py` (despite file name, class is binary sensor) and setup bridge in `custom_components/flynow/binary_sensor.py`.
- Contains: `FlyNowStatusSensor.is_on`, `extra_state_attributes`.
- Depends on: coordinator data model.
- Used by: dashboard card and any HA automations.

**Service Persistence Layer:**
- Purpose: Store and return flight history with atomic local persistence.
- Location: `custom_components/flynow/flight_log.py`, schema metadata in `custom_components/flynow/services.yaml`
- Contains: `log_flight` and `list_flights` service handlers, bounded history, corrupt-file recovery.
- Depends on: local JSON file under HA config path.
- Used by: Lovelace card service calls.

**Frontend Presentation Layer:**
- Purpose: Render operational status, condition breakdown, language toggle, and flight-log UX.
- Location: `lovelace/flynow-card/src/flynow-card.ts`, registration in `lovelace/flynow-card/src/index.ts`.
- Contains: Lit web component, stale-cache behavior, per-site detail selection, service call actions.
- Depends on: binary sensor attributes + `flynow.log_flight` and `flynow.list_flights`.
- Used by: Home Assistant Lovelace dashboard runtime.

## Data Flow

**Forecast To UI Flow:**

1. Config entry setup creates `FlyNowCoordinator` and performs first refresh in `custom_components/flynow/__init__.py`.
2. Coordinator fetches Open-Meteo payload per catalog site (`SITE_CATALOG`) in `custom_components/flynow/coordinator.py`.
3. Coordinator computes day boundaries and time windows via `custom_components/flynow/windows.py`.
4. Each window gets analyzed via strict threshold checks in `custom_components/flynow/analyzer.py`.
5. Coordinator publishes combined payload (`sites`, `sites_summary`, `active_window`, `notification_result`) consumed by `FlyNowStatusSensor` in `custom_components/flynow/sensor.py`.
6. Card reads `binary_sensor.flynow_status` attributes and renders tiles/condition rows in `lovelace/flynow-card/src/flynow-card.ts`.

**GO Transition Notification Flow:**

1. Coordinator keeps previous window state and dedup map in `custom_components/flynow/coordinator.py`.
2. On NO-GO -> GO transition, it calls `dispatch_go_transition_notifications` in `custom_components/flynow/notifications.py`.
3. Notification fanout sends three notify channels plus one calendar event using HA service calls.
4. Dedup key format `{window_key}@{launch_start}` and cooldown are enforced before repeated sends.

**Flight Log Flow:**

1. Backend registers `flynow.log_flight` and `flynow.list_flights` once in `custom_components/flynow/flight_log.py`.
2. Card submit action calls `flynow.log_flight`; response payload is used for optimistic UX update in `lovelace/flynow-card/src/flynow-card.ts`.
3. Card refresh action calls `flynow.list_flights`; backend returns newest-first, bounded list.
4. Storage writes are atomic temp-file replacements in `custom_components/flynow/flight_log.py`.

**State Management:**
- Backend authoritative state lives in coordinator memory (`_previous_windows`, `_notification_dedup`) and HA entity attributes.
- Persistent business state is local JSON only for flight history (`flynow_flights.json` path from HA config).
- Frontend transient state includes stale cache (`lastKnownAttributes`), selected site, language, and form/history state.

## Key Abstractions

**Coordinator Data Contract:**
- Purpose: Single payload shared between backend computation and entity/frontend presentation.
- Examples: `custom_components/flynow/coordinator.py`, `custom_components/flynow/sensor.py`, `lovelace/flynow-card/src/types.ts`
- Pattern: dynamic dictionary contract with optional backward-compatible keys.

**Window-Based Decision Model:**
- Purpose: Evaluate discrete morning/evening launch opportunities.
- Examples: `custom_components/flynow/windows.py`, `custom_components/flynow/analyzer.py`
- Pattern: build temporal windows first, then attach condition verdicts per window.

**Service-Based Write Model:**
- Purpose: Keep write operations explicit and HA-native.
- Examples: `custom_components/flynow/flight_log.py`, `custom_components/flynow/services.yaml`, `lovelace/flynow-card/src/flynow-card.ts`
- Pattern: card does not write entity state directly; it calls integration services.

## Entry Points

**Home Assistant Integration Runtime:**
- Location: `custom_components/flynow/__init__.py`
- Triggers: config entry load/reload/unload.
- Responsibilities: coordinator lifecycle, platform setup, migration, domain service registration.

**Periodic Forecast Refresh:**
- Location: `custom_components/flynow/coordinator.py`
- Triggers: DataUpdateCoordinator interval (`CONF_UPDATE_INTERVAL_MIN`) and first-refresh path.
- Responsibilities: pull weather, evaluate windows, dispatch notifications, publish state payload.

**Lovelace Resource Runtime:**
- Location: `lovelace/flynow-card/src/index.ts` and bundled output from `lovelace/flynow-card/scripts/build.mjs`.
- Triggers: card instantiation in dashboard.
- Responsibilities: register web component and render sensor-backed UI.

## Error Handling

**Strategy:** Raise recoverable update failures in backend fetch layer, return guarded fallbacks in UI and services.

**Patterns:**
- Open-Meteo HTTP/network/payload errors are wrapped as `OpenMeteoError` then promoted to coordinator `UpdateFailed` (`custom_components/flynow/open_meteo.py`, `custom_components/flynow/coordinator.py`).
- Notification fanout isolates per-channel failures and reports partial success (`custom_components/flynow/notifications.py`).
- Flight log corrupt JSON is quarantined to backup filename and reset to empty list (`custom_components/flynow/flight_log.py`).
- Card shows stale cached values when entity is `unavailable` or `unknown` (`lovelace/flynow-card/src/flynow-card.ts`).

## Cross-Cutting Concerns

**Logging:** Python logging used in coordinator and flight log modules (`custom_components/flynow/coordinator.py`, `custom_components/flynow/flight_log.py`).
**Validation:** Config flow range/domain checks + voluptuous schemas for service payloads (`custom_components/flynow/config_flow.py`, `custom_components/flynow/flight_log.py`).
**Authentication:** None inside integration code; relies on Home Assistant authenticated runtime/service context.

## Architectural Risks & Ambiguities

- **Contract drift risk:** frontend expects both old and new key variants (`surface_wind` vs `surface_wind_ms`, `pass` vs `ok`) in `lovelace/flynow-card/src/flynow-card.ts` and `lovelace/flynow-card/src/types.ts`, while analyzer only emits `_ms` + `ok` keys in `custom_components/flynow/analyzer.py`.
- **Potential notification message mismatch:** message builder reads `precip_prob_pct` key, but analyzer emits `precip_prob` (`custom_components/flynow/notifications.py`, `custom_components/flynow/analyzer.py`), which can degrade precipitation figures in outbound text.
- **Scaling bottleneck:** coordinator performs per-site Open-Meteo calls sequentially in one client session loop (`custom_components/flynow/coordinator.py`), increasing latency as site catalog grows.
- **Single-entity contract concentration:** all card functionality depends on one binary sensor attribute payload (`custom_components/flynow/sensor.py`); malformed payloads affect multiple UX sections at once.
- **Ambiguous platform naming:** entity implementation is in `sensor.py` while platform list points to `binary_sensor` and setup bridge exists in `binary_sensor.py`, which can slow onboarding due to indirection (`custom_components/flynow/const.py`, `custom_components/flynow/binary_sensor.py`, `custom_components/flynow/sensor.py`).

---

*Architecture analysis: 2026-04-28*
