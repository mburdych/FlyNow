# Phase 1: Core Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 01-core-integration
**Areas discussed:** Condition Scoring Model, Sensor Entity Structure, Config Flow Scope, Flight Window Data Model

---

## Condition Scoring Model

| Option | Description | Selected |
|--------|-------------|----------|
| Strict AND — any fail = NO-GO | Any single threshold exceeded → entire window is NO-GO | ✓ |
| Tiered — hard limits + soft warnings | Two levels per parameter; result is GO / MARGINAL / NO-GO | |
| Weighted scoring | Each parameter gets a score; combined total determines GO/NO-GO | |

**User's choice:** Strict AND

---

### Window duration evaluation (WEATHER-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Worst-case in window | Use max wind, min ceiling, max precip across the full flight window | ✓ |
| All hours must pass | Check each hourly slot individually; report which slot failed | |

**User's choice:** Worst-case in window

**Notes:** User specified wind units are m/s throughout. Provided key domain thresholds:
- Surface wind: ~4 m/s ground launch limit
- Primary flight level: ~1000ft AGL (~300m), prefer ≤10 m/s
- Direction correction altitude: ~3000ft AGL (~900m)
- Also noted: VFR zone and controlled airspace awareness, multiple "favourite" starting places

---

## Sensor Entity Structure

| Option | Description | Selected |
|--------|-------------|----------|
| One binary sensor + rich attributes | Single binary_sensor.flynow_status with all data in attributes | ✓ |
| Multiple discrete sensors | Separate sensor per condition + master binary GO/NO-GO | |
| Both — master binary + discrete sensors | Most flexible, most entities | |

**User's choice:** One binary sensor + rich attributes

---

### Multi-window storage

| Option | Description | Selected |
|--------|-------------|----------|
| Multiple windows in attributes | Both evening and morning window data embedded in one sensor's attributes | ✓ |
| One sensor per window type | binary_sensor.flynow_morning and binary_sensor.flynow_evening as separate entities | |

**User's choice:** Multiple windows in attributes

---

## Config Flow Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Defer contacts to Phase 2 | Phase 1 covers location, flight params, thresholds only | ✓ |
| Include contact fields in Phase 1 | Add WhatsApp/Calendar fields now, even if unused until Phase 2 | |

**User's choice:** Defer contacts to Phase 2

---

### Multi-site support

| Option | Description | Selected |
|--------|-------------|----------|
| Single location, multi-site in v2 | Phase 1 one site only; multi-site deferred | ✓ |
| Multi-site from Phase 1 | Config flow allows adding multiple named sites | |

**User's choice:** Single location in Phase 1

---

## Flight Window Data Model

| Option | Description | Selected |
|--------|-------------|----------|
| Today + next 2 days (3-day rolling) | Initial option presented | |
| Today + tomorrow only (2 days) | Simpler, less data | |

**User's choice:** Extended scope (user clarified): 4 evening windows (today + 3 days) + 3 morning windows (tomorrow + 2 days). Today's morning skipped if it's already midday.

**Notes:** User requested:
- Day labels in Slovak (Dnes, Zajtra, then Slovak weekday names)
- Can consider Windy, SHMU, METAR data in the future
- Testing location: Malý Maďarás, LZMADA

---

### Data sources

| Option | Description | Selected |
|--------|-------------|----------|
| Open-Meteo only in Phase 1 | Locked constraint; SHMU/METAR deferred to Phase 2 | ✓ |
| Add SHMU / METAR to Phase 1 | Multi-source fetcher in Phase 1 | |

**User's choice:** Open-Meteo only in Phase 1

---

## Claude's Discretion

- Open-Meteo pressure level selection for altitude layers
- Coordinator fetch error handling and retry logic
- Internal coordinator state data structures
- HA async lifecycle (async_setup_entry / async_unload_entry) details

## Deferred Ideas

- SHMU + METAR cross-validation (Phase 2 candidate)
- Multi-site support (v2)
- VFR zone / controlled airspace awareness (v2 spatial analysis)
- Explicit no-go notification (v2, NOTIF-V2-01)
