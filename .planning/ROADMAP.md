# Roadmap: FlyNow

**Created:** 2026-04-16
**Phases:** 4
**Requirements:** 27 v1 requirements mapped

## Overview

| # | Phase | Goal | Requirements | Plans |
|---|-------|------|--------------|-------|
| 1 | Core Integration | 3/3 | Complete    | 2026-04-22 |
| 2 | Notifications & Card | 2/2 | Complete   | 2026-04-23 |
| 3 | Flight Logging | 2/2 | Complete | 2026-04-24 |
| 4 | Multi-site forecast planning card | 1/1 | Complete | 2026-04-23 |

## Phase Details

### Phase 1: Core Integration

**Goal:** Home Assistant fetches, analyzes, and exposes balloon-flyable condition data via sensors and config flow — no external dependencies, async-safe architecture proven.

**Requirements:**
- WEATHER-01: System fetches hourly Open-Meteo forecast for configured launch location
- WEATHER-02: System analyzes wind at surface (10m) and balloon altitude (600–1000m AGL)
- WEATHER-03: System analyzes cloud ceiling, precipitation probability, visibility
- WEATHER-04: All go/no-go thresholds are user-configurable
- WEATHER-05: Conditions analyzed across full flight window (60–90 min), not just launch moment
- TIME-01: System calculates sunrise and sunset times for launch location on given date
- TIME-02: Evening window: latest launch = sunset minus flight duration minus prep time; must land before sunset
- TIME-03: Morning window: earliest launch = sunrise plus prep time; cannot start before sunrise
- TIME-04: Both morning and evening windows evaluated; evening is primary
- FORE-01: System provides rough 2–3 day look-ahead (is Thursday evening flyable?)
- FORE-02: System provides firm go/no-go check for next flight window (night-before decision)
- HA-01: Config flow UI for setup (location, thresholds, flight duration, contacts)
- HA-02: Sensor entities expose go/no-go status, window type, condition breakdown, launch window times
- HA-03: DataUpdateCoordinator refreshes forecast every 30–60 minutes

**Plans:**
3/3 plans complete
2. Sunrise/sunset calculation, time window logic, config flow setup — enables time-bound analysis
3. DataUpdateCoordinator, sensor entities, coordinator lifecycle — proves async architecture

**Success Criteria** (what must be TRUE):
1. User can configure launch location and go/no-go thresholds via config flow UI without errors
2. HA sensors automatically update every 30–60 minutes with current go/no-go status and condition details (wind, ceiling, precip, visibility)
3. Crew can manually trigger a sensor refresh and see results within 5 seconds
4. Sensor data correctly reflects tomorrow morning and tomorrow evening windows with accurate sunrise/sunset times
5. Config reload applies new thresholds without restarting Home Assistant

**Dependencies:** None (first phase)

---

### Phase 2: Notifications & Card

**Goal:** Crew and pilot both receive real-time alerts when a good flying window is detected, and can view full status and window details in the Lovelace card.

**Requirements:**
- NOTIF-01: HA push notification sent to crew and pilot phones on flyable window detection (GO only)
- NOTIF-02: Google Calendar event created for confirmed good windows with launch time and duration
- NOTIF-03: WhatsApp or Signal group message sent with go/no-go decision and condition summary
- NOTIF-04: Deduplication: no repeat notification for same window within 1 hour
- CARD-01: Card displays today's evening window and tomorrow's morning window with clear GO/NO-GO status
- CARD-02: Card shows condition breakdown: surface wind, altitude wind, ceiling, precipitation, visibility — each with threshold comparison
- CARD-03: Card shows calculated launch window times (e.g. "Launch by 18:30 — Sunset 20:15")

**Plans:**
2/2 plans complete
2. Lovelace card (TypeScript, LitElement) with live state subscription — provides visual status and window details

**Success Criteria** (what must be TRUE):
1. When conditions transition from NO-GO to GO, push notification arrives on crew and pilot phones within 2 minutes
2. Calendar event appears on shared Google Calendar with correct launch time and window end time within 2 minutes of GO detection
3. WhatsApp or Signal group message arrives within 3 minutes of GO detection with condition summary and launch window
4. Same good window does not trigger duplicate notifications within 1 hour
5. Lovelace card displays current status (GO/NO-GO) and shows both morning and evening windows for the next 2 days
6. Card updates in real-time (within 5 sec) when sensor state changes

**Dependencies:** Phase 1 (requires working sensors and coordinator)

**UI hint:** yes

---

### Phase 3: Flight Logging

**Goal:** Crew can record completed flights in the Lovelace card with outcome and notes, storing data locally for future learning analysis.

**Requirements:**
- LOG-01: Lovelace card includes form to log completed flight (date, balloon, launch time, duration, site, outcome, notes)
- LOG-02: Flight logs stored locally in HA config directory with atomic writes

**Plans:**
2/2 plans complete

Plans:
- [x] 03-01-PLAN.md — Flight log backend services + atomic JSON persistence
- [x] 03-02-PLAN.md — Lovelace form + history service integration

**Success Criteria** (what must be TRUE):
1. User can fill out flight log form in card and submit without errors
2. Submitted log appears in `/config/flynow_flights.json` with all fields correctly preserved
3. Card allows user to view previously logged flights in a list
4. Interrupted writes (e.g. HA crash mid-write) do not corrupt the flight log file

**Dependencies:** Phase 2 (logging form integrates into card)

**UI hint:** yes

---

## Requirement Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| WEATHER-01 | Phase 1 | Pending |
| WEATHER-02 | Phase 1 | Pending |
| WEATHER-03 | Phase 1 | Pending |
| WEATHER-04 | Phase 1 | Pending |
| WEATHER-05 | Phase 1 | Pending |
| TIME-01 | Phase 1 | Pending |
| TIME-02 | Phase 1 | Pending |
| TIME-03 | Phase 1 | Pending |
| TIME-04 | Phase 1 | Pending |
| FORE-01 | Phase 1 | Pending |
| FORE-02 | Phase 1 | Pending |
| HA-01 | Phase 1 | Pending |
| HA-02 | Phase 1 | Pending |
| HA-03 | Phase 1 | Pending |
| NOTIF-01 | Phase 2 | Pending |
| NOTIF-02 | Phase 2 | Pending |
| NOTIF-03 | Phase 2 | Pending |
| NOTIF-04 | Phase 2 | Pending |
| CARD-01 | Phase 2 | Pending |
| CARD-02 | Phase 2 | Pending |
| CARD-03 | Phase 2 | Pending |
| LOG-01 | Phase 3 | Complete |
| LOG-02 | Phase 3 | Complete |
| SITE-01 | Phase 4 | Complete |
| SITE-02 | Phase 4 | Complete |
| SITE-03 | Phase 4 | Complete |
| SITE-04 | Phase 4 | Complete |

**Coverage:** 27/27 v1 requirements mapped ✓

### Phase 4: Multi-site forecast planning card

**Goal:** Crew can compare near-term GO/NO-GO launch planning outcomes across Malý Madaras, Katarínka, and Nitra lúka in one Lovelace card, while existing automations continue to use the same `binary_sensor.flynow_status`.

**Requirements:**
- SITE-01: Integration uses exactly three predefined launch sites from `.planning/reference/launch-sites.md` with static metadata (id, name, coordinates, region/elevation context).
- SITE-02: Coordinator computes forecast window analysis per site using existing Open-Meteo + analyzer/window logic and exposes a multi-site summary payload.
- SITE-03: `binary_sensor.flynow_status` remains backward-compatible for selected-site automation triggers while adding explicit multi-site summary attributes for UI consumption.
- SITE-04: Lovelace card shows comparison-first planning status for all three sites (GO/NO-GO + launch window timing) with optional selected-site detail view.

**Depends on:** Phase 3
**Plans:** 1 plans

Plans:
- [x] 04-01-PLAN.md — Add fixed three-site forecast projection and comparison-first planning card contract

---

*Roadmap created: 2026-04-16*
