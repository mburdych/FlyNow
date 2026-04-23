# Phase 1: Core Integration - Research

**Researched:** 2026-04-20
**Domain:** Home Assistant custom integration (config entries + DataUpdateCoordinator) with Open-Meteo forecast analysis
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions

### Condition Scoring Model

- **D-01:** Strict AND logic — any single parameter exceeding its threshold makes the window NO-GO. If wind is too high, ceiling too low, precipitation too likely, or visibility too low → NO-GO regardless of other conditions.
- **D-02:** Worst-case across window — for WEATHER-05, evaluate the max wind, min ceiling, and max precipitation probability across the entire flight window (default 90 min). The GO/NO-GO decision uses these worst-case values, not the launch moment values.
- **D-03:** Wind units are **m/s** (not km/h) throughout — API fetch, storage, thresholds, and sensor attributes all use m/s.
- **D-04:** Altitude layers of interest:
  - Surface: 10m (launch condition, limit ~4 m/s default)
  - Primary flight level: ~300m AGL (~1000ft AFL), target <=10 m/s max
  - Direction correction altitude: ~900m AGL (~3000ft), used to assess wind direction for navigation — use Open-Meteo pressure level data closest to these altitudes (975 hPa ≈ 300m, 925 hPa ≈ 760m as proxies)

### Sensor Entity Structure

- **D-05:** Single `binary_sensor.flynow_status` entity — state `on` = GO, `off` = NO-GO. All condition and window data lives in state attributes. One entity to trigger Phase 2 automations on.
- **D-06:** Sensor attributes carry **all windows** simultaneously so the Lovelace card (Phase 2) can display a full multi-day view from one entity. Structure:
  ```
  attributes:
    active_window: evening | morning | none
    # Current/next window
    launch_start: "HH:MM"
    launch_end: "HH:MM"
    # Per-window breakdown (4 evenings + 3 mornings)
    today_evening_go: true/false
    today_evening_launch_start: "HH:MM"
    today_evening_conditions: {surface_wind_ms, altitude_wind_ms, ceiling_m, precip_prob, visibility_km, each _ok bool}
    tomorrow_evening_go: ...
    day2_evening_go: ...
    day3_evening_go: ...
    tomorrow_morning_go: ...
    day2_morning_go: ...
    day3_morning_go: ...
  ```
- **D-07:** Condition breakdown per window includes: surface_wind_ms + _ok, altitude_wind_ms + _ok, ceiling_m + _ok, precip_prob + _ok, visibility_km + _ok, and each parameter's configured threshold for transparency.

### Config Flow Scope (Phase 1 only)

- **D-08:** Phase 1 config flow is 3 steps only. Notification contacts (WhatsApp, Google Calendar) are **deferred to Phase 2** — no contact fields in Phase 1.
- **D-09:** Config flow steps:
  - **Step 1 — Location:** latitude, longitude, launch site name (text, e.g. "Malý Maďarás")
  - **Step 2 — Flight parameters:** flight_duration_min (default 90), prep_time_min (default 30), update_interval_min (default 60)
  - **Step 3 — Thresholds:** max_surface_wind_ms (default 4.0), max_altitude_wind_ms (default 10.0), min_ceiling_m (default 500), max_precip_prob_pct (default 20), min_visibility_km (default 5.0)
- **D-10:** Phase 1 supports **one launch site only**. Multi-site management deferred to v2.

### Flight Window Data Model

- **D-11:** Coordinator calculates and holds **7 windows** in its state:
  - Evening windows: today + tomorrow + day+2 + day+3 (4 evenings)
  - Morning windows: tomorrow + day+2 + day+3 (3 mornings) — today's morning is skipped if the current time is past ~09:00 local time (no longer relevant)
  - Open-Meteo 7-day hourly forecast covers all of these.
- **D-12:** Windows use **time-aware skip logic** — if the current time is past the latest launch time for a window, that window is omitted from the sensor state (marked as `null` or absent, not stale GO/NO-GO).
- **D-13:** Day labels in sensor attributes use **Slovak day names** (e.g. "Dnes", "Zajtra", then actual weekday names like "Streda", "Štvrtok"). These are display labels in attributes — downstream card can use them directly.
- **D-14:** FORE-01 (rough 2–3 day look-ahead) is satisfied by the day+2 and day+3 evening windows. FORE-02 (firm night-before) is satisfied by tomorrow's evening and morning windows (freshest forecast slot).

### Data Sources

- **D-15:** Phase 1 uses **Open-Meteo only**. No secondary sources in Phase 1. SHMU (Slovak Hydrometeorological Institute) and METAR data from LZMADA are noted as Phase 2 enhancements for cross-validation accuracy.

### Claude's Discretion

- Open-Meteo pressure level selection for the two altitude layers (975 hPa, 925 hPa) — exact mapping can be refined during implementation based on API response structure.
- Error handling for coordinator fetch failures — coordinator retry logic is standard HA pattern, Claude decides the approach.
- Internal data structures for the coordinator's state object — the external attribute shape is locked (D-06), internal representation is Claude's choice.
- `async_setup_entry` / `async_unload_entry` lifecycle details — follow HA conventions.

### Deferred Ideas (OUT OF SCOPE)

- **SHMU + METAR integration** — Slovak national weather service (SHMU) and METAR observations from LZMADA for cross-validation. Phase 2 candidate to improve forecast accuracy and confidence.
- **Multi-site support** — Multiple named launch sites with per-site coordinates. Deferred to v2. Phase 1 supports one site.
- **VFR zone / controlled airspace awareness** — Understanding which launch sites are inside/near controlled airspace (CTR, TMA). Relevant to the 100km radius analysis in v2 spatial requirements (SPATIAL-01/02).
- **Explicit no-go notification** — Currently "silence = no-go". Explicit no-go alerts are in v2 requirements (NOTIF-V2-01).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WEATHER-01 | System fetches hourly Open-Meteo forecast for a configured launch location (lat/lon) | Open-Meteo `/v1/forecast` hourly usage and HA coordinator polling pattern defined in Standard Stack + Architecture Patterns. |
| WEATHER-02 | System analyzes wind at surface (10m) and at balloon operating altitude (600–1000m AGL) using pressure-level data | Open-Meteo pressure level mapping (975/925 hPa) and variable selection documented in Architecture Patterns. |
| WEATHER-03 | System analyzes cloud ceiling, precipitation probability, and visibility | Open-Meteo hourly variables + threshold comparison model defined in Don't Hand-Roll + Code Examples. |
| WEATHER-04 | All go/no-go thresholds are configurable by the crew (not hard-coded defaults) | 3-step HA config flow implementation pattern with persisted config entries documented. |
| WEATHER-05 | Conditions are analyzed across the full flight window (60–90 min duration), not just launch moment | Window slicing + worst-case reduction pattern specified in Architecture Patterns. |
| TIME-01 | System calculates sunrise and sunset times for the launch location on a given date | Open-Meteo `daily=sunrise,sunset` with `timezone` requirement documented. |
| TIME-02 | Evening window: latest launch = sunset minus flight duration minus prep time; must land before sunset | Time-window formula and omission logic defined in Architecture Patterns. |
| TIME-03 | Morning window: earliest launch = sunrise plus prep time; cannot start before sunrise | Time-window formula and skip behavior specified in Architecture Patterns. |
| TIME-04 | Both morning and evening windows are evaluated; evening is the primary use case | 7-window state model and prioritization captured in Summary + Architecture Patterns. |
| FORE-01 | System provides a rough 2–3 day look-ahead (is Thursday evening flyable?) | Multi-day evening windows (day+2/day+3) and hourly forecast horizon support documented. |
| FORE-02 | System provides a firm go/no-go check for the next flight window (night-before decision) | Tomorrow evening/morning near-term windows in coordinator state + attribute design documented. |
| HA-01 | Config flow UI for setup: launch location, go/no-go thresholds, flight duration, notification contacts | Phase-scoped HA config flow guidance provided (contacts deferred per locked decision D-08). |
| HA-02 | Sensor entities expose: go/no-go status, active window type (morning/evening/none), condition breakdown, calculated launch window times | Single binary sensor with full attributes architecture documented, aligned to HA binary sensor conventions. |
| HA-03 | DataUpdateCoordinator refreshes forecast data every 30–60 minutes | Coordinator setup with `async_config_entry_first_refresh` and update interval recommendations documented. |

## Summary

Phase 1 should be implemented as a single Home Assistant config-entry integration that polls Open-Meteo on a configurable 30-60 minute interval via `DataUpdateCoordinator`, computes seven time-bounded windows, and exposes one authoritative `binary_sensor.flynow_status` with full breakdown attributes. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [CITED: https://developers.home-assistant.io/docs/core/entity/binary-sensor/] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]

Open-Meteo already provides all required hourly and daily fields: hourly wind/visibility/precipitation probability plus daily sunrise/sunset; pressure-level wind fields are available for 975 hPa (~320 m ASL) and 925 hPa (~800 m ASL), which are suitable proxies for locked altitude checks when combined with conservative thresholds. [CITED: https://open-meteo.com/en/docs] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]

Planning should avoid custom schedulers and custom persistence: config values live in HA config entries, polling and failure semantics stay inside coordinator abstractions, and window outputs are precomputed in coordinator data so entity properties remain memory-only reads. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [CITED: https://developers.home-assistant.io/docs/core/entity/binary-sensor/]

**Primary recommendation:** Use one polling coordinator + one binary sensor with precomputed 7-window attributes and strict worst-case AND evaluation; keep all user-adjustable values in a 3-step config flow. [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Fetch Open-Meteo forecast data | API / Backend (HA integration runtime) | — | External I/O belongs in async backend integration code, not entity properties/UI. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] |
| Compute sunrise/sunset and launch windows | API / Backend (coordinator logic) | — | Time arithmetic and forecast slicing is domain logic shared by all consumers. [VERIFIED: .planning/REQUIREMENTS.md] |
| Evaluate GO/NO-GO thresholds | API / Backend (analyzer service) | — | Decision engine must remain deterministic and centralized for automations. [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md] |
| Persist user settings (thresholds, timings, location) | API / Backend (config entries) | Database / Storage (HA internal storage) | HA config entries are the standard persistence mechanism; no YAML/file custom config. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] |
| Expose flyability state to HA | API / Backend (binary sensor entity) | Browser / Client (Lovelace rendering later) | Sensor entity is canonical source, frontend is downstream consumer. [CITED: https://developers.home-assistant.io/docs/core/entity/binary-sensor/] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| homeassistant | 2026.4.3 | Integration framework, config entries, coordinator, entities | Native API surface for HA custom integrations. [VERIFIED: PyPI] |
| aiohttp | 3.13.5 | Async HTTP client for Open-Meteo requests | Async-first networking aligned with HA event loop constraints. [VERIFIED: PyPI] [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] |
| Open-Meteo Forecast API | live web API | Weather + sunrise/sunset data source | Covers required variables without API key for non-commercial use. [CITED: https://open-meteo.com/en/docs] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.13.2 | Parse/validate Open-Meteo response models | Use if response normalization complexity grows beyond simple dict mapping. [VERIFIED: PyPI] [ASSUMED] |
| pytest-homeassistant-custom-component | 0.13.324 | HA integration test fixtures | Use for config flow, coordinator, and entity behavior tests. [VERIFIED: PyPI] |
| ruff | 0.15.11 | Linting | Enforce HA-friendly lint hygiene in CI/local dev. [VERIFIED: PyPI] |
| mypy | 1.20.1 | Static typing | Enforce strict typing and safer async contracts. [VERIFIED: PyPI] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `aiohttp` | `httpx` | `httpx` ergonomics are good, but `aiohttp` is HA convention and avoids introducing another client stack. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [ASSUMED] |
| pressure-level wind only | height-level wind (`wind_speed_80m/120m/180m`) | Height-level is simpler but does not directly satisfy locked pressure-level direction/altitude intent from context. [CITED: https://open-meteo.com/en/docs] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md] |

**Installation:**
```bash
pip install homeassistant aiohttp pydantic pytest-homeassistant-custom-component ruff mypy
```

**Version verification (PyPI query, 2026-04-20):**
- homeassistant `2026.4.3` (uploaded 2026-04-17T20:24:23Z) [VERIFIED: pypi.org JSON API]
- aiohttp `3.13.5` (uploaded 2026-03-31T22:01:03Z) [VERIFIED: pypi.org JSON API]
- pydantic `2.13.2` (uploaded 2026-04-17T09:31:59Z) [VERIFIED: pypi.org JSON API]
- pytest-homeassistant-custom-component `0.13.324` (uploaded 2026-04-18T05:34:37Z) [VERIFIED: pypi.org JSON API]
- ruff `0.15.11` (uploaded 2026-04-16T18:46:26Z) [VERIFIED: pypi.org JSON API]
- mypy `1.20.1` (uploaded 2026-04-13T02:46:51Z) [VERIFIED: pypi.org JSON API]

## Architecture Patterns

### System Architecture Diagram

```text
[Config Flow (user)]
        |
        v
[Config Entry Data: location + timing + thresholds]
        |
        v
[DataUpdateCoordinator @ 30-60 min]
        |
        +--> [Open-Meteo /v1/forecast hourly + daily sunrise/sunset]
        |
        v
[Forecast Normalizer]
        |
        v
[Window Builder]
 (today+3 evening, tomorrow+3 morning)
        |
        v
[Worst-Case Evaluator (strict AND)]
        |
        v
[Coordinator State Object]
        |
        v
[binary_sensor.flynow_status]
 state: on/off, attrs: active_window + per-window details
```

### Recommended Project Structure
```text
custom_components/flynow/
├── __init__.py         # async_setup_entry / async_unload_entry, coordinator lifecycle
├── manifest.json       # domain metadata, config_flow enabled
├── const.py            # config keys, defaults, attribute keys
├── config_flow.py      # 3-step flow (location, flight params, thresholds)
├── coordinator.py      # API fetch + normalization + window analysis
├── analyzer.py         # strict AND + worst-case checks over a window
├── windows.py          # sunrise/sunset and morning/evening window calculations
├── sensor.py           # binary_sensor.flynow_status exposing coordinator state
└── strings.json        # config flow labels/errors/translations
```

### Pattern 1: Config Entry First-Run + Polling Coordinator
**What:** Initialize coordinator during setup and call `async_config_entry_first_refresh()` before adding entities. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/]
**When to use:** Integrations with one upstream API response used by one or many entities.
**Example:**
```python
# Source: https://developers.home-assistant.io/docs/integration_fetching_data/
coordinator = FlyNowCoordinator(hass, entry)
await coordinator.async_config_entry_first_refresh()
async_add_entities([FlyNowStatusBinarySensor(coordinator)])
```

### Pattern 2: Multi-step Config Flow with Manifest Flag
**What:** Set `config_flow: true` in `manifest.json` and implement `ConfigFlow` steps in `config_flow.py`. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] [CITED: https://developers.home-assistant.io/docs/creating_integration_manifest]
**When to use:** Any custom integration storing user-provided setup values.
**Example:**
```python
# Source: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/
class FlyNowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        ...
```

### Pattern 3: Window-first Analysis Then Entity Projection
**What:** Build all 7 windows in coordinator data, then entity only projects current state + attributes. [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]
**When to use:** Multi-window forecast logic that must power both automations and later UI.
**Example:**
```python
# Source: project context decisions D-05/D-06/D-11
state = {
    "is_go": any(window["go"] for window in windows if window["is_active_candidate"]),
    "active_window": pick_active_window(windows),
    "windows": windows,
}
```

### Anti-Patterns to Avoid
- **Network I/O inside entity properties:** Binary sensor properties must read memory only; fetch via coordinator instead. [CITED: https://developers.home-assistant.io/docs/core/entity/binary-sensor/]
- **Hard-coded thresholds in analyzer:** Violates WEATHER-04 and config-flow requirements. [VERIFIED: .planning/REQUIREMENTS.md]
- **Single-timestamp decisions:** Violates WEATHER-05; must evaluate full window worst-case values. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]
- **Custom YAML setup path:** Config entries are the intended setup mode. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Polling scheduler | Custom async loop/timer management | `DataUpdateCoordinator(update_interval=...)` | Handles refresh lifecycle, retries, and subscriber-aware polling behavior. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] |
| Setup persistence | Custom JSON/YAML config files for setup | HA config entries + config flow | Built-in migration/versioning and UI setup support. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] |
| Sunrise/sunset astronomy math | Custom solar calculations | Open-Meteo daily `sunrise,sunset` output | Reduces timezone/DST errors and keeps one data source. [CITED: https://open-meteo.com/en/docs] |
| Binary state distribution | Multiple overlapping sensors for same decision | Single `binary_sensor.flynow_status` + rich attributes | Locked decision D-05 and simpler automation trigger model. [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md] |

**Key insight:** In this phase, reliability comes from composing HA-native primitives and Open-Meteo outputs rather than adding custom infrastructure. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/]

## Common Pitfalls

### Pitfall 1: Timezone Drift in Window Calculations
**What goes wrong:** Launch windows are shifted by 1 hour around DST or differ from local Slovak time.
**Why it happens:** API requests omit/incorrectly set `timezone` and code assumes UTC timestamps.
**How to avoid:** Request Open-Meteo with `timezone=Europe/Bratislava` (or `auto`) and treat returned timestamps as local. [CITED: https://open-meteo.com/en/docs]
**Warning signs:** Sunrise appears near midnight local time, or morning/evening labels look inverted.

### Pitfall 2: Altitude Confusion (AGL vs ASL)
**What goes wrong:** Pressure-level wind chosen without accounting that Open-Meteo pressure-level altitude is ASL-estimated.
**Why it happens:** Pressure tables are interpreted as fixed AGL heights.
**How to avoid:** Use 975/925 hPa proxies per locked context and keep conservative thresholds; optionally inspect geopotential height for calibration. [CITED: https://open-meteo.com/en/docs] [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md]
**Warning signs:** Direction/wind at “300 m” looks implausible for local terrain days.

### Pitfall 3: Entity Pulling Data Directly
**What goes wrong:** Sensor updates become slow/unreliable and duplicate API calls occur.
**Why it happens:** `is_on`/attributes trigger network calls or parsing.
**How to avoid:** Keep all external fetch/processing in coordinator; entities only read `coordinator.data`. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [CITED: https://developers.home-assistant.io/docs/core/entity/binary-sensor/]
**Warning signs:** Log spam from repeated API requests on state reads.

## Code Examples

Verified patterns from official sources:

### DataUpdateCoordinator Setup
```python
# Source: https://developers.home-assistant.io/docs/integration_fetching_data/
class FlyNowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, api):
        super().__init__(
            hass,
            _LOGGER,
            name="FlyNow",
            config_entry=entry,
            update_interval=timedelta(minutes=entry.data["update_interval_min"]),
            always_update=True,
        )
        self.api = api
```

### Config Flow Registration
```python
# Source: https://developers.home-assistant.io/docs/creating_integration_manifest
{
  "domain": "flynow",
  "name": "FlyNow",
  "config_flow": true
}
```

### Open-Meteo Request Shape
```python
# Source: https://open-meteo.com/en/docs
params = {
    "latitude": lat,
    "longitude": lon,
    "timezone": "Europe/Bratislava",
    "wind_speed_unit": "ms",
    "hourly": [
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_speed_975hPa",
        "wind_direction_975hPa",
        "wind_speed_925hPa",
        "wind_direction_925hPa",
        "visibility",
        "precipitation_probability",
    ],
    "daily": ["sunrise", "sunset"],
    "forecast_days": 7,
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| YAML-only integration setup | Config entries via config flow | Established in modern HA custom integration practices | Better UX, migration support, fewer startup validation failures. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] |
| Per-entity polling logic | Shared `DataUpdateCoordinator` | Long-standing HA recommendation | Lower API load and centralized retry/refresh behavior. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] |
| Single-point launch weather check | Window-wide worst-case checks | Locked for FlyNow phase scope | Better safety envelope for balloon operations. [VERIFIED: .planning/phases/01-core-integration/01-CONTEXT.md] |

**Deprecated/outdated:**
- Direct YAML-first setup paths for new custom integrations should not be the primary architecture for this phase. [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] [ASSUMED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pydantic` should be introduced in Phase 1 only if response normalization complexity grows. | Standard Stack | Added dependency and modeling overhead may be unnecessary if simple dict parsing is enough. |
| A2 | `httpx` remains less aligned than `aiohttp` for HA custom integrations despite being technically viable. | Standard Stack | Team might prefer `httpx`; mismatch could trigger style debates/refactor churn. |
| A3 | YAML-first setup is considered outdated for this project scope. | State of the Art | If team wants YAML import support now, plan would miss migration tasks. |

## Open Questions (RESOLVED)

1. **Pressure-level direction at "~900 m AGL"**
   - **RESOLVED:** Use 925 hPa as the fixed Phase 1 higher-altitude proxy (with 975 hPa for the lower proxy), aligned with locked decision D-04.
   - **Rationale:** This keeps the first release deterministic and traceable to the context contract; terrain calibration can be evaluated in later phases once real flight outcomes are logged.

2. **`single_config_entry` in `manifest.json`**
   - **RESOLVED:** Set `single_config_entry: true` in Phase 1.
   - **Rationale:** D-10 locks Phase 1 to one launch site, and one config entry avoids accidental multi-entry divergence; this can be revisited when multi-site support is introduced in v2. [CITED: https://developers.home-assistant.io/docs/creating_integration_manifest] [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | HA custom integration code/test tooling | ✓ | 3.14.3 | — |
| pip | Installing dev/test dependencies | ✓ | 26.0.1 | — |
| Node.js | GSD/project tooling and optional frontend later phases | ✓ | v24.14.1 | — |
| Open-Meteo HTTP endpoint | Forecast/sunrise/sunset data | ✓ | live API | — |

**Missing dependencies with no fallback:**
- None.

**Missing dependencies with fallback:**
- None.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth in Open-Meteo phase scope. [CITED: https://open-meteo.com/en/docs] |
| V3 Session Management | no | No user sessions; HA runtime manages auth/session globally. [ASSUMED] |
| V4 Access Control | yes | Respect HA config entry ownership boundaries and avoid arbitrary service exposure. [ASSUMED] |
| V5 Input Validation | yes | Validate config flow inputs (lat/lon ranges, threshold bounds, interval bounds). [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] |
| V6 Cryptography | no | No cryptographic material handled in Phase 1 scope. [VERIFIED: .planning/REQUIREMENTS.md] |

### Known Threat Patterns for HA Integration + Weather API

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malformed upstream weather payload | Tampering | Defensive parsing + validation before state publication; fail update gracefully. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] [ASSUMED] |
| Unbounded user-config values causing CPU-heavy loops | Denial of Service | Enforce strict bounds in config flow schema (duration, interval, thresholds). [CITED: https://developers.home-assistant.io/docs/config_entries_config_flow_handler/] |
| Excessive API polling | Denial of Service | Use coordinator update interval floor and avoid entity-level polling. [CITED: https://developers.home-assistant.io/docs/integration_fetching_data/] |

## Sources

### Primary (HIGH confidence)
- https://developers.home-assistant.io/docs/integration_fetching_data/ - Coordinator and polling patterns, setup and update semantics.
- https://developers.home-assistant.io/docs/config_entries_config_flow_handler/ - Config flow design, migration/reconfigure expectations, testing guidance.
- https://developers.home-assistant.io/docs/creating_integration_manifest - Manifest requirements and `config_flow`/`single_config_entry` options.
- https://developers.home-assistant.io/docs/core/entity/binary-sensor/ - Binary sensor behavior constraints.
- https://open-meteo.com/en/docs - Forecast endpoint params, hourly/daily vars, pressure-level mapping, timezone behavior.
- `.planning/phases/01-core-integration/01-CONTEXT.md` - Locked implementation decisions for this phase.
- `.planning/REQUIREMENTS.md` - Requirement IDs and acceptance behavior.

### Secondary (MEDIUM confidence)
- https://hacs.xyz/docs/publish/integration/ - HACS repository structure and manifest key expectations.
- pypi.org JSON package endpoints - current package versions and upload dates.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - official HA/Open-Meteo docs plus live PyPI version checks.
- Architecture: HIGH - directly constrained by locked context decisions and HA integration docs.
- Pitfalls: MEDIUM - grounded in docs plus domain interpretation for balloon operations.

**Research date:** 2026-04-20
**Valid until:** 2026-05-20
