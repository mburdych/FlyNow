# Phase 1: Core Integration - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the HA integration foundation: fetch Open-Meteo hourly forecast data, analyze balloon flying conditions against configurable thresholds, calculate time-bounded flight windows (sunrise/sunset), and expose the results via HA sensor entities and a config flow UI. No notifications, no Lovelace card, no messaging — those are Phase 2.

Success means: HA knows autonomously whether conditions are flyable right now and in the next ~3 days, sensors update every 30–60 minutes, and crew can see go/no-go status from HA.

</domain>

<decisions>
## Implementation Decisions

### Condition Scoring Model

- **D-01:** Strict AND logic — any single parameter exceeding its threshold makes the window NO-GO. If wind is too high, ceiling too low, precipitation too likely, or visibility too low → NO-GO regardless of other conditions. No weighted scoring, no partial credit.
- **D-02:** Worst-case across window — for WEATHER-05, evaluate the max wind, min ceiling, and max precipitation probability across the entire flight window (default 90 min). The GO/NO-GO decision uses these worst-case values, not the launch moment values.
- **D-03:** Wind units are **m/s** (not km/h) throughout — API fetch, storage, thresholds, and sensor attributes all use m/s.
- **D-04:** Altitude layers of interest:
  - Surface: 10m (launch condition, limit ~4 m/s default)
  - Primary flight level: ~300m AGL (~1000ft AFL), target ≤10 m/s max
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external ADRs or specs exist yet — this is a greenfield project. All decisions are captured in this context file and the project-level documents below.

### Project Context
- `.planning/PROJECT.md` — Core value, constraints, key decisions, out-of-scope items
- `.planning/REQUIREMENTS.md` — Full requirement list with IDs (WEATHER-01–05, TIME-01–04, FORE-01–02, HA-01–03) and traceability table
- `.planning/ROADMAP.md` — Phase 1 success criteria, plan breakdown, dependency map
- `CLAUDE.md` — Tech stack decisions, Open-Meteo API endpoints, HA conventions, what NOT to use

### External References (no local files — look up during research)
- Open-Meteo API docs — `https://open-meteo.com/en/docs` — pressure level wind parameters, hourly variables list, 7-day forecast range
- HA DataUpdateCoordinator pattern — `https://developers.home-assistant.io/docs/integration_fetching_data/` — async coordinator lifecycle
- HA config_flow docs — `https://developers.home-assistant.io/docs/config_entries_config_flow_handler/` — multi-step config flow pattern
- HACS requirements — `https://hacs.xyz/docs/publish/requirements` — manifest.json standards

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — this is a greenfield project. No existing components.

### Established Patterns
- None yet — Phase 1 establishes the patterns. Downstream phases will follow what Phase 1 creates.
- HA conventions apply: async throughout, `aiohttp` for HTTP, `pydantic` for data validation, `ruff` + strict `mypy`.

### Integration Points
- `custom_components/flynow/` — integration root (to be created in Phase 1)
- `coordinator.py` → feeds `sensor.py` which creates `binary_sensor.flynow_status`
- Config entries store site config, thresholds, flight params — `const.py` defines all keys

</code_context>

<specifics>
## Specific Ideas

- **Testing location:** Malý Maďarás airfield, ICAO: LZMADA, Slovakia. Use this as the default/example site during development and testing. Coordinates to be looked up by researcher (approx. southern Slovakia near Hungarian border).
- **Wind display:** Always m/s. No unit conversion needed in v1.
- **Day name labels in Slovak:** "Dnes" (Today), "Zajtra" (Tomorrow), then actual Slovak weekday names (Pondelok, Utorok, Streda, Štvrtok, Piatok, Sobota, Nedeľa).
- **Evening is the primary use case.** Morning windows are important but crew's primary planning is for late-afternoon/evening flights (better thermal conditions for hot air balloons in Slovakia summer evenings).

</specifics>

<deferred>
## Deferred Ideas

- **SHMU + METAR integration** — Slovak national weather service (SHMU) and METAR observations from LZMADA for cross-validation. Phase 2 candidate to improve forecast accuracy and confidence.
- **Multi-site support** — Multiple named launch sites with per-site coordinates. Deferred to v2. Phase 1 supports one site.
- **VFR zone / controlled airspace awareness** — Understanding which launch sites are inside/near controlled airspace (CTR, TMA). Relevant to the 100km radius analysis in v2 spatial requirements (SPATIAL-01/02).
- **Explicit no-go notification** — Currently "silence = no-go". Explicit no-go alerts are in v2 requirements (NOTIF-V2-01).

</deferred>

---

*Phase: 01-core-integration*
*Context gathered: 2026-04-16*
