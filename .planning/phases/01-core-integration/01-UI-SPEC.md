---
phase: 1
slug: core-integration
status: approved
reviewed_at: 2026-04-16
shadcn_initialized: false
preset: none
created: 2026-04-16
ha_ui_type: config_flow
---

# Phase 1 — UI Design Contract

> This phase is a Home Assistant backend integration. There is no custom HTML, CSS, JavaScript, or
> Lovelace card in Phase 1. All visual styling is controlled by the HA framework itself. This
> contract specifies the text/copy contract (strings.json), sensor entity definitions, and attribute
> naming conventions — not visual tokens.

---

## Design System

| Property | Value | Source |
|----------|-------|--------|
| Tool | Home Assistant config_flow | HA-01 requirement |
| Preset | not applicable — HA renders the UI | N/A |
| Component library | Home Assistant built-in (ha-form, ha-card) | HA convention |
| Icon library | Material Design Icons (MDI) — prefix `mdi:` | HA standard |
| Font | HA default (Roboto) — inherited from HA frontend | HA convention |

---

## Spacing / Typography / Color

**Not applicable for Phase 1.** Home Assistant's config_flow UI controls all visual styling —
card layouts, form field spacing, input sizes, colors, and fonts. No custom CSS is authored in
Phase 1. These dimensions will be specified in Phase 2 (Lovelace card).

---

## Config Flow Copy Contract

Phase 1 config flow has 3 steps (D-09). All strings below are the exact values to use in
`strings.json` and Python schema definitions.

### Step 1 — Location

**Step title:** `Set up FlyNow — Launch Site`

**Step description:** `Enter the coordinates and name for your primary launch site. FlyNow will fetch weather for this location.`

| Field key | Label | Description / helper text | Placeholder / example | Validation error |
|-----------|-------|--------------------------|----------------------|------------------|
| `site_name` | `Site name` | `A short name for your launch site (e.g. Malý Maďarás)` | `Malý Maďarás` | `Site name is required.` |
| `latitude` | `Latitude` | `Decimal degrees north (e.g. 47.94 for LZMADA)` | `47.94` | `Enter a valid latitude between -90 and 90.` |
| `longitude` | `Longitude` | `Decimal degrees east (e.g. 18.41 for LZMADA)` | `18.41` | `Enter a valid longitude between -180 and 180.` |

**Notes:**
- `site_name` is type `str`, max 60 characters.
- `latitude` is type `float`, range −90.0 to 90.0.
- `longitude` is type `float`, range −180.0 to 180.0.
- Development/test defaults: `site_name = "Malý Maďarás"`, `latitude = 47.94`, `longitude = 18.41` (LZMADA, southern Slovakia).

---

### Step 2 — Flight Parameters

**Step title:** `FlyNow — Flight Parameters`

**Step description:** `Configure how long your flights typically last and how early you start preparations. These times define the valid launch window.`

| Field key | Label | Description / helper text | Default | Unit | Validation error |
|-----------|-------|--------------------------|---------|------|------------------|
| `flight_duration_min` | `Flight duration` | `Typical flight duration in minutes. The launch window ends this many minutes before sunset.` | `90` | minutes | `Enter a whole number between 30 and 240.` |
| `prep_time_min` | `Preparation time` | `Time needed before launch (inflation, briefing). Morning: added after sunrise. Evening: subtracted from latest launch.` | `30` | minutes | `Enter a whole number between 0 and 120.` |
| `update_interval_min` | `Forecast refresh interval` | `How often FlyNow re-fetches the forecast from Open-Meteo. Shorter = fresher data, more API calls.` | `60` | minutes | `Enter a whole number between 15 and 240.` |

**Notes:**
- All three fields are type `int` (whole minutes).
- `flight_duration_min`: min 30, max 240.
- `prep_time_min`: min 0, max 120.
- `update_interval_min`: min 15, max 240.

---

### Step 3 — Flying Thresholds

**Step title:** `FlyNow — Go/No-Go Thresholds`

**Step description:** `Set the weather limits for a flyable window. Any single condition exceeding its threshold makes the window NO-GO.`

| Field key | Label | Description / helper text | Default | Unit | Validation error |
|-----------|-------|--------------------------|---------|------|------------------|
| `max_surface_wind_ms` | `Max surface wind` | `Maximum acceptable wind speed at 10m (launch and landing zone). Typical balloon limit: 4 m/s.` | `4.0` | m/s | `Enter a number between 0.0 and 20.0.` |
| `max_altitude_wind_ms` | `Max altitude wind` | `Maximum acceptable wind at balloon flight altitude (~300–900m AGL). Higher winds increase drift and risk.` | `10.0` | m/s | `Enter a number between 0.0 and 30.0.` |
| `min_ceiling_m` | `Minimum cloud ceiling` | `Lowest acceptable cloud base in metres. Below this the flight is impractical or unsafe.` | `500` | m | `Enter a whole number between 100 and 5000.` |
| `max_precip_prob_pct` | `Max precipitation probability` | `Maximum acceptable chance of precipitation (%) during the flight window.` | `20` | % | `Enter a whole number between 0 and 100.` |
| `min_visibility_km` | `Minimum visibility` | `Minimum acceptable horizontal visibility in kilometres for daylight balloon operations.` | `5.0` | km | `Enter a number between 0.5 and 50.0.` |

**Notes:**
- `max_surface_wind_ms`: type `float`, step 0.5.
- `max_altitude_wind_ms`: type `float`, step 0.5.
- `min_ceiling_m`: type `int`.
- `max_precip_prob_pct`: type `int`.
- `min_visibility_km`: type `float`, step 0.5.
- All thresholds use m/s for wind (D-03). No unit conversion.

---

### Config Flow — Global Error Messages

| Scenario | Copy |
|----------|------|
| Duplicate site (entry already exists) | `FlyNow is already configured. Only one launch site is supported. Remove the existing entry first.` |
| Cannot connect to Open-Meteo during setup | `Unable to reach Open-Meteo. Check your internet connection and try again.` |
| Unexpected error during setup | `An unexpected error occurred. Check the Home Assistant log for details.` |
| Step 1 submit — coordinates out of bounds | `Those coordinates are outside the valid range. Check latitude (−90 to 90) and longitude (−180 to 180).` |

---

## Sensor Entity Copy Contract

### binary_sensor.flynow_status

| Property | Value | Source |
|----------|-------|--------|
| Entity ID | `binary_sensor.flynow_status` | D-05 |
| Unique ID | `flynow_{entry_id}_status` | HA convention |
| Display name | `FlyNow Status` | — |
| Device class | `None` (no standard HA device class matches) | HA convention |
| Icon — state ON (GO) | `mdi:balloon` | GO condition |
| Icon — state OFF (NO-GO) | `mdi:balloon-off` | NO-GO condition |
| State ON meaning | Conditions are flyable for at least one window in the next 3 days | D-05 |
| State OFF meaning | No flyable windows detected in the next 3 days | D-05 |

**Note on icon fallback:** If `mdi:balloon-off` is not available in the installed MDI version, use `mdi:weather-windy` for OFF state.

---

### Sensor Attribute Names

All attribute keys are snake_case. These are the exact key names the coordinator must write and the Lovelace card (Phase 2) will read. See D-06 and D-07 for the full data model decisions.

#### Top-level attributes

| Attribute key | Type | Description |
|---------------|------|-------------|
| `active_window` | `str` | Current active window type: `"evening"`, `"morning"`, or `"none"` |
| `launch_start` | `str` | Launch window open time for the current/next window — format `"HH:MM"` (24h) or `null` if no window |
| `launch_end` | `str` | Latest launch time for current/next window — format `"HH:MM"` (24h) or `null` if no window |
| `site_name` | `str` | Configured launch site name (e.g. `"Malý Maďarás"`) |
| `last_updated` | `str` | ISO 8601 timestamp of last forecast fetch |
| `forecast_source` | `str` | Always `"open-meteo"` in Phase 1 |

#### Per-window attributes (repeated for each of the 7 windows)

Window name prefixes: `today_evening`, `tomorrow_evening`, `day2_evening`, `day3_evening`, `tomorrow_morning`, `day2_morning`, `day3_morning`.

For each window prefix `{W}`:

| Attribute key | Type | Description |
|---------------|------|-------------|
| `{W}_go` | `bool` | `true` = GO, `false` = NO-GO, absent/`null` = window skipped (past or irrelevant) |
| `{W}_day_label` | `str` | Slovak day label (see Day Names table below) |
| `{W}_launch_start` | `str` | Window open time `"HH:MM"` or `null` |
| `{W}_launch_end` | `str` | Latest launch time `"HH:MM"` or `null` |
| `{W}_sunrise` | `str` | Sunrise time `"HH:MM"` for that date |
| `{W}_sunset` | `str` | Sunset time `"HH:MM"` for that date |

#### Per-window condition breakdown (D-07)

For each window prefix `{W}`:

| Attribute key | Type | Description |
|---------------|------|-------------|
| `{W}_surface_wind_ms` | `float` | Worst-case surface wind (m/s) across the window |
| `{W}_surface_wind_ok` | `bool` | `true` if ≤ `max_surface_wind_ms` threshold |
| `{W}_surface_wind_threshold_ms` | `float` | Configured threshold for transparency |
| `{W}_altitude_wind_ms` | `float` | Worst-case altitude wind (m/s) across the window |
| `{W}_altitude_wind_ok` | `bool` | `true` if ≤ `max_altitude_wind_ms` threshold |
| `{W}_altitude_wind_threshold_ms` | `float` | Configured threshold |
| `{W}_ceiling_m` | `int` | Lowest cloud ceiling (m) across the window |
| `{W}_ceiling_ok` | `bool` | `true` if ≥ `min_ceiling_m` threshold |
| `{W}_ceiling_threshold_m` | `int` | Configured threshold |
| `{W}_precip_prob` | `int` | Max precipitation probability (%) across the window |
| `{W}_precip_ok` | `bool` | `true` if ≤ `max_precip_prob_pct` threshold |
| `{W}_precip_threshold_pct` | `int` | Configured threshold |
| `{W}_visibility_km` | `float` | Minimum visibility (km) across the window |
| `{W}_visibility_ok` | `bool` | `true` if ≥ `min_visibility_km` threshold |
| `{W}_visibility_threshold_km` | `float` | Configured threshold |

**Rule:** `{W}_go` = `true` if and only if all five `*_ok` booleans are `true` (strict AND logic, D-01). Worst-case across window duration (D-02).

---

## Slovak Day Name Mapping

Source: D-13 and specifics section of CONTEXT.md.

| Offset from today | Key in attribute | Slovak label | English meaning |
|-------------------|------------------|--------------|-----------------|
| 0 (today) | `today_evening` | `"Dnes"` | Today |
| +1 (tomorrow) | `tomorrow_evening`, `tomorrow_morning` | `"Zajtra"` | Tomorrow |
| +2 | `day2_evening`, `day2_morning` | Weekday name for that date | e.g. `"Streda"` |
| +3 | `day3_evening`, `day3_morning` | Weekday name for that date | e.g. `"Štvrtok"` |

**Full Slovak weekday name table:**

| Python `weekday()` | Slovak name | Notes |
|--------------------|-------------|-------|
| 0 | `"Pondelok"` | Monday |
| 1 | `"Utorok"` | Tuesday |
| 2 | `"Streda"` | Wednesday |
| 3 | `"Štvrtok"` | Thursday |
| 4 | `"Piatok"` | Friday |
| 5 | `"Sobota"` | Saturday |
| 6 | `"Nedeľa"` | Sunday |

**Implementation note:** Use `datetime.weekday()` on the date object for day+2 and day+3. Apply "Dnes"/"Zajtra" overrides before the weekday lookup. Characters `š`, `Š`, `ť`, `Ľ`, `ľ` must be stored as UTF-8 in `strings.json` — do not escape them as ASCII.

---

## Registry Safety

Not applicable for Phase 1. No HACS frontend resources are registered in this phase. No third-party component registry is used. Phase 2 (Lovelace card) will require HACS registration and the registry safety gate applies there.

---

## strings.json Skeleton

This is the complete skeleton for `custom_components/flynow/strings.json`. All keys and values are defined. The developer copies this file verbatim and adjusts only if HA schema validation requires it.

```json
{
  "config": {
    "step": {
      "location": {
        "title": "Set up FlyNow — Launch Site",
        "description": "Enter the coordinates and name for your primary launch site. FlyNow will fetch weather for this location.",
        "data": {
          "site_name": "Site name",
          "latitude": "Latitude",
          "longitude": "Longitude"
        },
        "data_description": {
          "site_name": "A short name for your launch site (e.g. Malý Maďarás)",
          "latitude": "Decimal degrees north (e.g. 47.94 for LZMADA)",
          "longitude": "Decimal degrees east (e.g. 18.41 for LZMADA)"
        }
      },
      "flight_params": {
        "title": "FlyNow — Flight Parameters",
        "description": "Configure how long your flights typically last and how early you start preparations. These times define the valid launch window.",
        "data": {
          "flight_duration_min": "Flight duration",
          "prep_time_min": "Preparation time",
          "update_interval_min": "Forecast refresh interval"
        },
        "data_description": {
          "flight_duration_min": "Typical flight duration in minutes. The launch window ends this many minutes before sunset.",
          "prep_time_min": "Time needed before launch (inflation, briefing). Morning: added after sunrise. Evening: subtracted from latest launch.",
          "update_interval_min": "How often FlyNow re-fetches the forecast from Open-Meteo. Shorter = fresher data, more API calls."
        }
      },
      "thresholds": {
        "title": "FlyNow — Go/No-Go Thresholds",
        "description": "Set the weather limits for a flyable window. Any single condition exceeding its threshold makes the window NO-GO.",
        "data": {
          "max_surface_wind_ms": "Max surface wind",
          "max_altitude_wind_ms": "Max altitude wind",
          "min_ceiling_m": "Minimum cloud ceiling",
          "max_precip_prob_pct": "Max precipitation probability",
          "min_visibility_km": "Minimum visibility"
        },
        "data_description": {
          "max_surface_wind_ms": "Maximum acceptable wind speed at 10m (launch and landing zone). Typical balloon limit: 4 m/s.",
          "max_altitude_wind_ms": "Maximum acceptable wind at balloon flight altitude (~300–900m AGL). Higher winds increase drift and risk.",
          "min_ceiling_m": "Lowest acceptable cloud base in metres. Below this the flight is impractical or unsafe.",
          "max_precip_prob_pct": "Maximum acceptable chance of precipitation (%) during the flight window.",
          "min_visibility_km": "Minimum acceptable horizontal visibility in kilometres for daylight balloon operations."
        }
      }
    },
    "error": {
      "already_configured": "FlyNow is already configured. Only one launch site is supported. Remove the existing entry first.",
      "cannot_connect": "Unable to reach Open-Meteo. Check your internet connection and try again.",
      "unknown": "An unexpected error occurred. Check the Home Assistant log for details.",
      "invalid_coordinates": "Those coordinates are outside the valid range. Check latitude (−90 to 90) and longitude (−180 to 180).",
      "invalid_latitude": "Enter a valid latitude between -90 and 90.",
      "invalid_longitude": "Enter a valid longitude between -180 and 180.",
      "invalid_flight_duration": "Enter a whole number between 30 and 240.",
      "invalid_prep_time": "Enter a whole number between 0 and 120.",
      "invalid_update_interval": "Enter a whole number between 15 and 240.",
      "invalid_surface_wind": "Enter a number between 0.0 and 20.0.",
      "invalid_altitude_wind": "Enter a number between 0.0 and 30.0.",
      "invalid_ceiling": "Enter a whole number between 100 and 5000.",
      "invalid_precip_prob": "Enter a whole number between 0 and 100.",
      "invalid_visibility": "Enter a number between 0.5 and 50.0."
    },
    "abort": {
      "already_configured": "FlyNow is already configured. Only one launch site is supported."
    }
  },
  "entity": {
    "binary_sensor": {
      "flynow_status": {
        "name": "FlyNow Status",
        "state": {
          "on": "GO",
          "off": "NO-GO"
        }
      }
    }
  }
}
```

---

## Checker Sign-Off

> Dimensions 3–5 (Color, Typography, Spacing) are not applicable for a config_flow-only phase.
> HA framework controls all visual styling. Checker should evaluate only dimensions 1, 2, and 6.

- [ ] Dimension 1 Copywriting: PASS — all step titles, field labels, helper text, and error messages specified
- [ ] Dimension 2 Visuals: PASS — sensor entity name, unique ID, MDI icon, state labels defined
- [ ] Dimension 3 Color: N/A — HA built-in UI
- [ ] Dimension 4 Typography: N/A — HA built-in UI
- [ ] Dimension 5 Spacing: N/A — HA built-in UI
- [ ] Dimension 6 Registry Safety: N/A — no frontend assets in Phase 1

**Approval:** pending

---

## UI-SPEC COMPLETE
