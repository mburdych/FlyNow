# Roadmap: FlyNow

**Created:** 2026-04-16
**Phases:** 9

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 shipped (2026-04-24), archived in `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 translations fix** — Phase 5 shipped (2026-04-24), archived in `.planning/milestones/v1.1-ROADMAP.md`

## Current Milestone

No active milestone is currently in progress.

## Next Action

Run `/gsd-new-milestone` to define v1.2 scope and requirements.

## Backlog

### Phase 06: Lovelace Card Language Toggle (BACKLOG)

**Goal:** Add a user-facing language switch in the FlyNow Lovelace card so the user explicitly chooses the UI language (SK/EN), independent of browser or HA locale defaults.
**Source:** Post-v1.1 UAT feedback
**Deferred at:** 2026-04-24
**Tasks:**
- [ ] Define UX for language selector placement and persistence behavior
- [ ] Default to automatic detection only on first load, then always honor the user-selected language
- [ ] Implement runtime text dictionary for at least Slovak and English
- [ ] Wire toggle state into all card labels/messages
- [ ] Verify behavior in HA with `sk` and `en` profiles

### Phase 07: Flight Log Import + Map Visualization (BACKLOG)

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

### Phase 08: Card Time Slider — Scrub Forecast Across Launch Sites (BACKLOG)

**Goal:** Add a horizontal time slider to the FlyNow Lovelace card. Dragging the handle from left to right advances the forecast time within the morning window, and all per-launch-site condition values (wind, cloud_base, fog risk, GO/NO-GO) update live to reflect that time. Lets the crew preview how conditions evolve hour-by-hour without waiting for the next coordinator update.
**Source:** User request
**Deferred at:** 2026-04-28
**Tasks:**
- [ ] Define slider range (e.g. full forecast horizon vs. only morning window) and step granularity (hourly vs. finer)
- [ ] Decide how the selected time interacts with the existing GO/NO-GO display (override current "now" view vs. side-by-side preview)
- [ ] Ensure coordinator payload exposes the full hourly per-site series the slider needs (not just aggregated window summary)
- [ ] Update card types and rendering in `lovelace/flynow-card/` to drive all per-site rows from the slider's selected timestamp
- [ ] Visual treatment: time label, snap-to-hour, keyboard accessibility, mobile touch behavior
- [ ] Reset behavior when new coordinator data arrives (preserve user's selection vs. snap back to "now")
- [ ] Verify with multiple sites that values change consistently and no stale row remains

### Phase 09: Fog Risk Hardening — Trend Monotonicity, Dedup, Pilot-Tunable Thresholds (BACKLOG)

**Goal:** Ship a code-side hardening bundle for fog-risk evaluation by combining corrections C4 + C5 + C6 from `CEILING-FOG-CORRECTIONS.md`: enforce trend monotonicity, deduplicate repetitive outputs/notifications, and add pilot-tunable fog thresholds.
**Source:** `CEILING-FOG-CORRECTIONS.md` correction bundle (C4, C5, C6)
**Deferred at:** 2026-04-28
**Tasks:**
- [ ] Implement trend monotonicity hardening in fog-risk pipeline so forecast progression cannot regress due to ordering/noise artifacts
- [ ] Add dedup logic for repeated fog-risk states/results so unchanged outcomes do not re-emit redundant payloads
- [ ] Introduce pilot-tunable fog thresholds in integration config/runtime evaluation path (code-side only)
- [ ] Add/extend tests covering monotonic trend behavior, dedup behavior, and threshold override behavior
- [ ] Verify no user-facing workflow/UI step is required for the initial hardening rollout
