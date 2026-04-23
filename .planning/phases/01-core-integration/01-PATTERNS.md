# Phase 1: Core Integration - Pattern Map

**Mapped:** 2026-04-20
**Files analyzed:** 10
**Analogs found:** 0 / 10 (greenfield repo)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `custom_components/flynow/manifest.json` | config | request-response | None in repo; use HA manifest skeleton from `01-RESEARCH.md` | no-analog |
| `custom_components/flynow/__init__.py` | provider | request-response | None in repo; use HA coordinator setup pattern from `01-RESEARCH.md` | no-analog |
| `custom_components/flynow/const.py` | config | transform | None in repo; use HA constants module convention (ecosystem) | no-analog |
| `custom_components/flynow/config_flow.py` | controller | request-response | None in repo; use HA ConfigFlow pattern from `01-RESEARCH.md` | no-analog |
| `custom_components/flynow/coordinator.py` | service | request-response | None in repo; use DataUpdateCoordinator pattern from `01-RESEARCH.md` | no-analog |
| `custom_components/flynow/analyzer.py` | service | transform | None in repo; derive from D-01/D-02 strict AND + worst-case logic in `01-CONTEXT.md` | no-analog |
| `custom_components/flynow/windows.py` | utility | transform | None in repo; derive from TIME-01..04 and D-11..D-13 in `01-CONTEXT.md` | no-analog |
| `custom_components/flynow/sensor.py` | component | request-response | None in repo; use HA binary sensor pattern from `01-RESEARCH.md` references | no-analog |
| `custom_components/flynow/strings.json` | config | transform | None in repo; use HA config flow translation skeleton (ecosystem) | no-analog |
| `tests/test_coordinator.py` (and related Phase 1 tests) | test | batch | None in repo; use `pytest-homeassistant-custom-component` fixture pattern from `01-RESEARCH.md` | no-analog |

## Pattern Assignments

### `custom_components/flynow/manifest.json` (config, request-response)

**Analog:** No in-repo analog. Use ecosystem skeleton from `01-RESEARCH.md`.

**Core manifest pattern** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 296-303):
```json
{
  "domain": "flynow",
  "name": "FlyNow",
  "config_flow": true
}
```

**Guidance to copy:** Keep `config_flow: true`; add required HA manifest keys (`version`, `requirements`, `codeowners`, `iot_class`) during implementation.

---

### `custom_components/flynow/__init__.py` (provider, request-response)

**Analog:** No in-repo analog. Use coordinator setup lifecycle from `01-RESEARCH.md`.

**Setup pattern** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 207-212):
```python
coordinator = FlyNowCoordinator(hass, entry)
await coordinator.async_config_entry_first_refresh()
async_add_entities([FlyNowStatusBinarySensor(coordinator)])
```

**Guidance to copy:** In `async_setup_entry`, instantiate coordinator, run first refresh, store coordinator in `hass.data[DOMAIN][entry.entry_id]`, then forward entry setup to `sensor`.

---

### `custom_components/flynow/const.py` (config, transform)

**Analog:** No in-repo analog. Use HA constants-file convention (ecosystem + project docs).

**Config key scope to encode** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 55-58):
```text
Step 1: latitude, longitude, launch site name
Step 2: flight_duration_min, prep_time_min, update_interval_min
Step 3: max_surface_wind_ms, max_altitude_wind_ms, min_ceiling_m, max_precip_prob_pct, min_visibility_km
```

**Guidance to copy:** Centralize domain string, defaults, config keys, attribute keys, and Slovak day labels in `const.py` to avoid duplicated literals.

---

### `custom_components/flynow/config_flow.py` (controller, request-response)

**Analog:** No in-repo analog. Use HA ConfigFlow class skeleton from `01-RESEARCH.md`.

**Config flow class pattern** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 218-223):
```python
class FlyNowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        ...
```

**Phase-specific step structure** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 53-58):
```text
3 steps only:
1) Location
2) Flight parameters
3) Thresholds
```

**Guidance to copy:** Implement exactly three steps for Phase 1 (D-08/D-09), validate ranges, and create a single config entry payload with all fields.

---

### `custom_components/flynow/coordinator.py` (service, request-response)

**Analog:** No in-repo analog. Use DataUpdateCoordinator implementation skeleton from `01-RESEARCH.md`.

**Coordinator init pattern** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 280-293):
```python
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

**Open-Meteo request shape** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 306-325):
```python
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

**Guidance to copy:** Keep all I/O in coordinator; normalize API data once; compute 7 windows and publish a single coordinator data object consumed by the sensor.

---

### `custom_components/flynow/analyzer.py` (service, transform)

**Analog:** No in-repo analog. Use locked decision logic from context as canonical pattern.

**Decision pattern** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 20-22):
```text
Strict AND logic
Worst-case across window
Wind units are m/s
```

**Guidance to copy:** Implement pure functions taking `window_hourly_samples + thresholds` and returning `go/no-go + condition breakdown + *_ok flags + threshold echo fields`.

---

### `custom_components/flynow/windows.py` (utility, transform)

**Analog:** No in-repo analog. Use locked window model from context as canonical pattern.

**Window model pattern** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 62-67):
```text
7 windows total:
- Evenings: today, tomorrow, day+2, day+3
- Mornings: tomorrow, day+2, day+3
Skip expired windows using time-aware logic
Use Slovak day labels in attributes
```

**Guidance to copy:** Keep this module deterministic and side-effect free: input sunrise/sunset + now + config, output window boundaries and display labels.

---

### `custom_components/flynow/sensor.py` (component, request-response)

**Analog:** No in-repo analog. Use binary sensor + coordinator projection pattern from research.

**Projection pattern** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 225-236):
```python
state = {
    "is_go": any(window["go"] for window in windows if window["is_active_candidate"]),
    "active_window": pick_active_window(windows),
    "windows": windows,
}
```

**Attribute shape contract** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 31-48):
```text
Single binary_sensor.flynow_status
Attributes include active_window, launch_start/end, and all 7 per-window condition blocks
```

**Guidance to copy:** `is_on` and `extra_state_attributes` should only read from `coordinator.data`; no API calls or heavy computation in entity properties.

---

### `custom_components/flynow/strings.json` (config, transform)

**Analog:** No in-repo analog. Use HA integration translation skeleton conventions.

**Input source for labels** (`.planning/phases/01-core-integration/01-CONTEXT.md`, lines 53-58):
```text
Config flow labels must cover:
- location fields
- flight parameter fields
- threshold fields
```

**Guidance to copy:** Mirror config flow step names and field keys exactly; keep user-facing text centralized for localization.

---

### `tests/test_coordinator.py` and related tests (test, batch)

**Analog:** No in-repo analog. Use `pytest-homeassistant-custom-component` ecosystem pattern from research.

**Test tooling source** (`.planning/phases/01-core-integration/01-RESEARCH.md`, lines 132-134):
```text
pytest-homeassistant-custom-component
```

**Guidance to copy:** Build fixtures around mocked Open-Meteo payloads and assert:
- strict AND behavior
- worst-case reduction behavior
- 7-window output shape
- expired-window omission behavior

## Shared Patterns

### Integration lifecycle
**Source:** `.planning/phases/01-core-integration/01-RESEARCH.md` (lines 203-212, 279-293)  
**Apply to:** `__init__.py`, `coordinator.py`, `sensor.py`

```python
coordinator = FlyNowCoordinator(hass, entry)
await coordinator.async_config_entry_first_refresh()
```

### Request/response boundary
**Source:** `.planning/phases/01-core-integration/01-RESEARCH.md` (lines 306-325)  
**Apply to:** `coordinator.py`

```python
params = {
    "timezone": "Europe/Bratislava",
    "wind_speed_unit": "ms",
    "forecast_days": 7,
}
```

### Decision engine contract
**Source:** `.planning/phases/01-core-integration/01-CONTEXT.md` (lines 20-23, 49, 62-67)  
**Apply to:** `analyzer.py`, `windows.py`, `sensor.py`

```text
Strict AND + worst-case window evaluation
7-window model with expired-window skip logic
Condition breakdown contains per-metric value, _ok flag, and threshold
```

### Validation boundary
**Source:** `.planning/phases/01-core-integration/01-CONTEXT.md` (lines 53-58) and `.planning/phases/01-core-integration/01-RESEARCH.md` (lines 383-392)  
**Apply to:** `config_flow.py`

```text
Validate lat/lon, timing, and threshold bounds in config flow steps
```

## No Analog Found

Files with no close match in this repository (planner should use research-backed ecosystem skeletons for initial implementation):

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `custom_components/flynow/manifest.json` | config | request-response | No existing HA integration files in repo |
| `custom_components/flynow/__init__.py` | provider | request-response | No existing setup lifecycle code |
| `custom_components/flynow/const.py` | config | transform | No constants modules exist |
| `custom_components/flynow/config_flow.py` | controller | request-response | No config flows exist |
| `custom_components/flynow/coordinator.py` | service | request-response | No coordinator implementations exist |
| `custom_components/flynow/analyzer.py` | service | transform | No weather/domain analyzers exist |
| `custom_components/flynow/windows.py` | utility | transform | No time-window utilities exist |
| `custom_components/flynow/sensor.py` | component | request-response | No sensor entities exist |
| `custom_components/flynow/strings.json` | config | transform | No translation bundles exist |
| `tests/test_coordinator.py` | test | batch | No test suite exists yet |

## Metadata

**Analog search scope:** `C:/Users/dwdv8103/Projects/FlyNow`  
**Files scanned:** 17 total repository files (planning/docs only)  
**Pattern extraction date:** 2026-04-20
