# Roadmap: FlyNow

**Created:** 2026-04-16
**Phases:** 9

## Milestones

- ✅ **v1.0 milestone** — Phases 1-4 shipped (2026-04-24), archived in `.planning/milestones/v1.0-ROADMAP.md`
- ✅ **v1.1 translations fix** — Phase 5 shipped (2026-04-24), archived in `.planning/milestones/v1.1-ROADMAP.md`

## Current Milestone

**v1.2** — in progress (informal). Phases 06 and 07 executed locally, awaiting HAOS deploy. 08 and 09 queued in backlog.

## Next Action

Run `/gsd-new-milestone` to formalize v1.2 scope/requirements (or deploy 06+07 to HAOS first, then formalize).

## Executed (awaiting deploy)

### Phase 06: Lovelace Card Language Toggle ✅

**Goal:** Add a user-facing language switch in the FlyNow Lovelace card so the user explicitly chooses the UI language (SK/EN), independent of browser or HA locale defaults.
**Source:** Post-v1.1 UAT feedback
**Status:** Executed `2bc1c8a` (2026-04-24), awaiting HAOS deploy.
**Artifacts:** `.planning/phases/06-lovelace-card-language-toggle-backlog/`

### Phase 07: Flight Log Import + Map Visualization ✅

**Goal:** Allow users to import flight records (GPX/CSV with position + time), visualize tracks on a map, and persist immutable weather snapshots for forecast-vs-reality correlation. Delayed imports (days after flight) are first-class — provider chain `METAR → Open-Meteo archive → manual` and import never blocks on weather lookup failure.
**Source:** Product direction / user request
**Status:** Executed 2026-04-28 across 3 plans (14 commits, last `60c9b29`), awaiting HAOS deploy.
**Artifacts:** `.planning/phases/07-flight-log-import-map-visualization-backlog/` (CONTEXT, RESEARCH, PATTERNS, DISCUSSION-LOG, 3× PLAN+SUMMARY, LEARNINGS)
**Key outcomes:**
- Backend: `flight_import.py`, `flight_sidecar_store.py`, `weather_snapshot.py` (immutable base + append-only corrections)
- Coordinator decision-time forecast freeze + import-fallback freeze
- Frontend: typed contracts, isolated `map-renderer.ts` (Leaflet lifecycle), correlation panel with provenance + missing-weather states

## Backlog

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
