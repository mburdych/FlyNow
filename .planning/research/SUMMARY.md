# Research Summary

**Project:** FlyNow — HA integration for hot air balloon go/no-go
**Researched:** 2026-04-16
**Research files:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

## Recommended Stack

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12+ | HA integration | HA requirement; async/await mature |
| Home Assistant | 2025.1+ | Platform | Target runtime; DataUpdateCoordinator, config_flow |
| aiohttp | 3.9+ | Async HTTP | HA standard; never use `requests` (blocks event loop) |
| pydantic | 2.4+ | API response validation | Type-safe Open-Meteo parsing |
| TypeScript | 5.3+ | Lovelace card | Type safety for frontend |
| LitElement | 4.0+ | Card UI framework | HA community standard since 2022 |
| esbuild | 0.20+ | Card bundler | Fast, minimal config, HA community endorsed |
| Open-Meteo | free | Weather API | Free, no key, European coverage, hourly wind at multiple altitudes |
| Google Calendar | native HA | Shared calendar | Built-in HA integration |
| CallMeBot | free | WhatsApp notifications | Simple HTTP GET, low-volume reliable |
| pytest-homeassistant-custom-component | latest | Testing | HA integration test framework |
| ruff | 0.1+ | Linting | HA CI requirement |
| mypy | 1.7+ strict | Type checking | HA CI requirement |

## Table Stakes (Must Have in v1)

- Go/no-go binary recommendation from weather analysis
- Wind speed analysis at surface (10m) + altitude (80m/100m) for shear detection
- Cloud ceiling check (> 500m minimum)
- Precipitation probability filter (< 10%)
- Visibility filter (> 5 km)
- Time-bounded analysis: configurable early-morning window (default 05:00–09:00 local)
- Configurable thresholds for all parameters (crew knows their own limits)
- Push notification to crew + pilot on GO window (silence = no-go)
- HA sensor entities exposing go/no-go status and condition breakdown
- Lovelace card with visual status and next good window

## Architecture Overview

FlyNow follows the standard HA integration pattern centered on `DataUpdateCoordinator`. Every 30–60 minutes, the coordinator fetches hourly forecast data from Open-Meteo, runs it through a condition analyzer, and updates sensor entities. When the analyzer detects a transition from NO-GO to GO (with deduplication to prevent spam), it triggers the notification pipeline.

```
config_flow (user setup: location, thresholds, contacts)
    ↓
__init__.py (lifecycle: setup/unload/reload)
    ↓
Coordinator (30-60 min refresh cycle)
    ├→ open_meteo.py (async API client — aiohttp)
    ├→ analyzer.py (score conditions: wind/shear/ceiling/precip/visibility)
    ├→ notifications/pusher.py (trigger on GO state transition only)
    └→ sensor entities (CoordinatorEntity — state syncs automatically)
    ↓
Lovelace card (subscribes to entity state via WebSocket)
```

Sensor entities subclass `CoordinatorEntity` so state updates flow automatically without manual polling. The Lovelace card subscribes via `subscribeMessage` in `connectedCallback()` — never reads state once on mount.

## Top Pitfalls

1. **Blocking calls freeze HA** — Use `aiohttp` and `aiofiles` throughout; never `requests` or `time.sleep()`. Phase 1.
2. **Timezone off-by-one at DST** — Open-Meteo returns UTC; use HA `dt_util` to convert to Europe/Bratislava before dawn window filtering. Test CET→CEST transition. Phase 1.
3. **Notification spam** — Send exactly once per GO window. Track `_last_notified_window`; require 15+ min sustained GO before alerting; 1–2 sec delay between notification channels. Phase 2.
4. **Config reload doesn't apply options** — Implement `async_reload_entry()` callback + test that options flow changes take effect. Phase 1.
5. **Missing wind shear** — Fetch wind at both 10m AND 80m/100m; don't rely on surface wind alone. Validate parameter names with Open-Meteo API before Phase 1. Phase 1.
6. **Stale Lovelace card** — Card must subscribe to entity state changes via WebSocket, not read once on mount. Phase 2.
7. **Flight log corruption** — Atomic writes: write to temp file, rename to target. On load, backup corrupted files rather than failing. Phase 3.
8. **Config flow silent failure** — Validate location by actually calling Open-Meteo API in the config flow step. Phase 1.
9. **API rate limit exhaustion** — Set `SCAN_INTERVAL = timedelta(minutes=30)` minimum; implement exponential backoff on 429. Phase 1.
10. **Memory leaks on unload** — Implement `async_unload_entry()`: cancel all tasks, close HTTP sessions, clean `hass.data`. Phase 1.

## Suggested Build Order

| Phase | Focus | Rationale |
|-------|-------|-----------|
| 1 | Core integration: config_flow, coordinator, Open-Meteo client, analyzer, sensors | Async architecture must be right from day one — expensive to fix later |
| 2 | Push notifications + Lovelace card | First user-visible value; crew + pilot get notified |
| 3 | Google Calendar + WhatsApp/Signal | Shared awareness channels add coordination value |
| 4 | Flight logging | Data collection for future learning |
| 5 | Spatial radius analysis (~100 km) | Improves accuracy; requires multi-point API calls |
| 6 (v2) | ML learning from flight history | Deferred until 30+ flights collected |

## Open Questions (Before Phase 1)

- **Open-Meteo wind parameters** — Confirm `wind_speed_80m` / `wind_speed_100m` are available for Slovakia and what units they return
- **Pilot wind shear tolerance** — Maximum acceptable km/h difference between 10m and 100m wind for OM-0007/OM-0008
- **Pilot ceiling minimum** — Confirm legal + safe minimum (research suggests 500–1000m; needs pilot validation)
- **Precipitation threshold** — Exact probability % the pilot uses as a cutoff
- **Dawn window times** — Confirm 05:00–09:00 local is correct for Slovakia summer/winter
- **Google Calendar OAuth in Slovakia** — Available via native HA integration?
- **WhatsApp/Signal bridge** — Confirm CallMeBot is still active and reliable; assess Signal-cli setup complexity

## High-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Wind shear parameters wrong or unavailable | Core feature broken | Verify API before writing analyzer |
| Pilot thresholds not validated | Safety-critical: wrong GO/NO-GO | Interview pilot before Phase 1 ships |
| Async blocking on HA event loop | HA becomes unresponsive | aiohttp everywhere; profile coordinator |
| Timezone errors near DST | Wrong dawn window detection | dt_util + explicit DST test cases |
| Notification spam annoys crew | Integration gets disabled | Strict deduplication; < 1 alert per window |
| HACS validation failure | Can't distribute | Conservative min_version; test on minimum HA version |
