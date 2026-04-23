# Phase 04 — Design Discussion Log

**Session:** 2026-04-23
**Scope:** Richer UX layer for multi-site forecast planning card (04-02 source material)

---

## Problem framing

User brief: show flight-suitability visualization across N launch sites (v1 = 3, western Slovakia) for multiple upcoming time windows (today PM if morning, tomorrow AM+PM, day+2 AM+PM, weekend). Signaling must be glanceable (none / maybe / high / very high), responsive, readable on phone via HA portal.

Purpose clarified on turn 2: **planning tool**, not status dashboard. Goal = decide quickly when and where to fly so crew can call passengers and schedule.

---

## Layout options explored

Three layout archetypes were presented:

1. **Heatmap matrix** (rows = sites, cols = time slots) — dense, fast scan.
2. **Per-site rows with horizontal timeline** — mobile-friendly, site-first mental model.
3. **Best-window-first cards + grid detail** — casual-user friendly, hides data.

User rejected all three in favor of a **map-based layout**: underlay a schematic/real map of western Slovakia, render sites at their real geographic positions, show wind direction per site, slider to scrub through time. Rationale: map reveals how weather systems move across the region — a spatial cue that grid layouts cannot.

Main-stream input also suggested heatmap as a natural fit for this data. Noted but not adopted — user preference for map stands. Heatmap kept as a potential secondary view toggle (deferred).

---

## Locked design summary

### Banner (always visible, top)
Two lines:
- `Perfektné` → nearest future window with any site scoring 4/4
- `Možné` → nearest future window with any site scoring ≥ 2/4

Click on either row jumps slider to that slot. Empty-state fallbacks defined (no 4/4 in horizon → dash; no 2/4 anywhere → single-line message).

### Schematic map (middle)
- SVG outline of western Slovakia — minimal (no cities, no roads).
- Malé Karpaty as single curved line, Dunaj as one river.
- 3 pins at real lat/lon positions of LZMADA, Katarínka, Nitra lúka.
- Pin color driven by score for currently-selected slider slot.
- Two wind arrows per pin: surface (solid) + ~600m (outlined).
- Arrow length ∝ speed (cap 8 m/s), rotation = direction.
- Numeric under pin: `{surface}/{alt} m/s`.
- Meteoalarm triangle badge overlay if kraj has active warning.
- Pin click: **no action**. Data lives in detail panel.

### Swipe slider (under map)
- Horizontal, adaptive 8-window sequence.
- Swipe gesture is primary; tap on pill is accessibility fallback.
- Weekend-adaptive labeling: Mon–Wed collapses weekend to single tile; Thu–Fri explodes to explicit Sat/Sun AM/PM.
- Default slot at open = earliest future window where cutoff not yet passed.

### Detail panel (below slider)
- All 3 sites sorted by score for selected slot (best → worst).
- Per site: score X/4, launch time, surface wind, 600m wind, meteoalarm badge.
- NO-GO rows: one-sentence terrain-aware reason (e.g. "W vietor 5.4 m/s + ridge efekt Malých Karpát").

### Severity scoring (4-level)
- VERY HIGH (4/4), HIGH (3/4), LOW (2/4), NONE (0–1/4).
- Each signal triple-encoded: color + icon + number.
- Score computed by a separate analysis component — not by the card.

### Cutoff-based default slot
Pilots need lead time to call passengers. Default open slot = earliest future window where `now < cutoff`. Cutoffs (user-configurable):
- AM window cutoff = previous day 23:00
- PM window cutoff = same day 13:00

Examples confirmed with user:
- Tue 12:59 → Tue PM
- Tue 13:01 → Wed AM
- Tue 23:01 → Wed PM

### Out of scope for this layer
- Filter by passenger region (future: dropdown limiting sites).
- Hourly fine scrub.
- OSM / tile map.
- Heatmap secondary view toggle.
- 4th+ launch site (still locked at 3).

---

## Decisions not modified from 04-CONTEXT.md

All of D-01..D-09 (locked 3-site catalog, Open-Meteo-only source, legacy sensor backward-compat, comparison-first default) remain in force. The richer UX layer rebuilds the card presentation but consumes the existing `sites_summary` / `sites` / `selected_site_id` contracts from 04-01.

---

## Data contract expectations for scoring component

The card assumes the integration provides per site per window:
- `score`: integer 0–4
- `wind_speed_10m`, `wind_direction_10m`
- `wind_speed_600m`, `wind_direction_600m` (may be `null` if API cannot resolve)
- `launch_start`, `launch_end` (or `null` if no window computable)
- `nogo_reason`: short human string (terrain-aware), present when score < 2
- `meteoalarm_active`: bool for the site's kraj

If any field is missing, the card degrades gracefully (dash placeholder, not zero).

---

## Confirmations captured

- User explicit "súhlasím" at the close of the 6-turn discussion.
- Semantic 4-level scale accepted ("neskôr zmenime" — revisit later if needed).
- Schematic map confirmed over OSM.
- Pin-click-does-nothing confirmed.
- Swipe gesture confirmed as primary over tap.
- Cutoff values (23:00 / 13:00) confirmed with examples.
- Future regional filter noted but out of v1 scope.

---

*Discussion captured: 2026-04-23*
