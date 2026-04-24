# Roadmap: FlyNow

**Created:** 2026-04-16
**Phases:** 5

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 shipped (2026-04-24), archived in `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 translations fix** — Phase 5 shipped (2026-04-24), archived in `.planning/milestones/v1.1-ROADMAP.md`

## Current Milestone

No active milestone is currently in progress.

## Next Action

Run `/gsd-new-milestone` to define v1.2 scope and requirements.

## Backlog

### Phase 999.1: Lovelace Card Language Toggle (BACKLOG)

**Goal:** Add a user-facing language switch in the FlyNow Lovelace card so the user explicitly chooses the UI language (SK/EN), independent of browser or HA locale defaults.
**Source:** Post-v1.1 UAT feedback
**Deferred at:** 2026-04-24
**Tasks:**
- [ ] Define UX for language selector placement and persistence behavior
- [ ] Default to automatic detection only on first load, then always honor the user-selected language
- [ ] Implement runtime text dictionary for at least Slovak and English
- [ ] Wire toggle state into all card labels/messages
- [ ] Verify behavior in HA with `sk` and `en` profiles

### Phase 999.2: Flight Log Import + Map Visualization (BACKLOG)

**Goal:** Explore a future release where users can import flight records that include position and time data, visualize the track on a map, and **persist weather context for correlation**: what was **forecast** vs **observed reality** (wind speed and direction, and other agreed parameters) at flight time, alongside the flight itself—so we can compare prediction, reality, and the actual flight outcome.

**Constraint:** Imports may happen **several days after the flight**. Weather enrichment must use **sources that support past dates** (archives / reanalysis / historical observation APIs), not only “current forecast” endpoints. Where FlyNow already computed a snapshot near flight time, prefer **persisting that snapshot at decision time** so delayed import does not depend on retroactive API availability.
**Source:** Product direction / user request
**Deferred at:** 2026-04-24
**Tasks:**
- [ ] Define supported import formats (e.g. GPX, CSV with lat/lon/timestamp) and validation rules
- [ ] Extend or parallel the flight log model to store optional track points without breaking existing `flynow_flights.json` consumers
- [ ] Specify **weather snapshot schema** per flight: timestamp/location anchor, **forecast** fields (e.g. surface/altitude wind, direction, ceiling, precip—aligned with FlyNow analyzer), and **reality** fields (source: METAR, personal log, or post-flight API—TBD)
- [ ] On import (or on “finalize log”), capture or re-fetch **forecast-as-known-before-flight** vs **observations-at-flight-time** and store immutably on the record for later analysis
- [ ] **Historical data strategy:** shortlist providers that allow query by `lat/lon` + **past** `datetime` (e.g. archive forecast APIs, station/METAR history, reanalysis—each with latency, resolution, and licensing notes); define primary + fallback chain when import is days late
- [ ] Optional: when user logs or FlyNow evaluates a window, **write a compact weather snapshot to the flight record or a sidecar store** immediately, so delayed import mainly attaches track + merges existing snapshot
- [ ] UI/reporting: side-by-side or overlay view showing forecast vs reality vs go/no-go and flight path (correlation-focused, not just pretty map)
- [ ] Choose map stack (HA-friendly: static image, embedded map lib, or external link) and privacy constraints
- [ ] Prototype import flow and map rendering in the card or a dedicated panel
- [ ] Document backup/migration implications for larger track payloads and richer per-flight weather blobs
