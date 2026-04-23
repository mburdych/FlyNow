---
phase: 04-multi-site-forecast-planning-card
slug: multi-site-forecast-planning-card
status: draft
shadcn_initialized: false
preset: none
created: 2026-04-23
scope: richer-ux-layer-on-top-of-04-01
---

# Phase 04 — UI Design Contract (richer UX layer)

> Design contract for the richer multi-site planning card UI. Builds on top of 04-01 (comparison-first three-site baseline) with banner, schematic map, adaptive time slider, 4-level scoring, wind visualization, and cutoff-based default slot. Source: design discussion logged in 04-DISCUSSION-LOG.md.

---

## Scope Relationship to 04-01

04-01 (shipped) provides:
- Fixed 3-site catalog (`lzmada`, `katarinka`, `nitra-luka`)
- Coordinator `sites_summary` payload
- Comparison-first card with GO/NO-GO tiles + site-switcher detail

04-02 (this UI-SPEC) adds a richer UX layer intended to replace the 04-01 card rendering while preserving 04-01 backend contract. It introduces:
- Top banner with "Perfektné" + "Možné" hints
- Schematic map of western Slovakia with wind-vane pins
- Swipe-scrub time slider for adaptive 8-window timeline
- 4-level severity scoring per site per window
- Detail panel driven by selected slider slot
- Meteoalarm warning overlay per site
- Terrain-aware NO-GO explanations

The scoring component (4-level, wind at ~600m, terrain-aware reasons) is consumed from the integration — not computed in the card.

---

## Information Hierarchy (top → bottom)

| Section | Purpose | Persistence |
|---------|---------|-------------|
| Banner | Fast "should I call passengers?" answer | Always visible |
| Schematic map | Spatial intuition; wind change in time | Always visible |
| Time slider | Scrub through adaptive 8-window timeline | Always visible |
| Detail panel | Numeric conditions for selected slot | Always visible, updates with slider |

Anchor rule: **banner + map + slider are visible without scroll on mobile** (~400 px width, ~700 px height).

---

## Design System

| Property | Value |
|----------|-------|
| Tool | none |
| Preset | not applicable |
| Component library | none (custom Lovelace card with Lit) |
| Icon library | Home Assistant Material Design Icons (`mdi:*`) |
| Font | HA theme default (`var(--primary-font-family)`) |
| Map rendering | SVG inline (schematic outline) — not Leaflet/OSM |

Rationale: schematic map is intentional per design discussion — OSM tiles add weight and noise; we need only enough spatial context to read wind direction across 3 sites in a small region.

---

## Spacing Scale

Declared values (must be multiples of 4):

| Token | Value | Usage |
|-------|-------|-------|
| xs | 4px | Icon-to-label micro gaps, wind-value inline spacing |
| sm | 8px | Row spacing inside detail panel, slider pill gap |
| md | 16px | Default internal padding; banner row spacing; detail card padding |
| lg | 24px | Separation between banner / map / slider / detail sections |
| xl | 32px | Vertical gap between major card sections when detail expanded |
| 2xl | 48px | Dashboard-level gap around the card |

Exceptions: map inner padding is visually tuned (not token-bound) to keep pins clear of SVG edges.

---

## Typography

| Role | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| Body | 14px | 400 | 1.5 | Detail panel wind values, descriptions |
| Label | 12px | 600 | 1.2 | Slider pill labels, metric labels |
| Heading | 20px | 600 | 1.2 | Site name in detail row |
| Display | 28px | 600 | 1.2 | Score number `X/4` in banner (when present) |

---

## Color

| Role | Value | Usage |
|------|-------|-------|
| Dominant (60%) | `var(--primary-background-color)` | Card background, map background |
| Secondary (30%) | `var(--card-background-color)` | Banner surface, detail row surface |
| Accent (10%) | `var(--state-icon-active-color)` | Selected slider pill, active best-window indicator |
| Destructive | `var(--error-color)` | Explicit NO-GO chip, meteoalarm warning badge |

### Severity Color Scale (4-level)

| Score | Level | Color token | Icon | Number label |
|-------|-------|-------------|------|--------------|
| 4/4 | VERY HIGH | deep green + subtle glow | ⭐ or `mdi:weather-sunny` | `4/4` |
| 3/4 | HIGH | green (`--success-color`) | `mdi:check-circle` | `3/4` |
| 2/4 | LOW / MAYBE | amber (`--warning-color`) | `mdi:alert` | `2/4` |
| 0–1/4 | NONE | dim grey + red edge | `mdi:close-circle` | `0/4` |

Redundant encoding rule: every severity indicator **must carry all three** — color, icon, number. Color alone is insufficient (accessibility + mobile-in-sunlight).

---

## Banner Contract

Two always-visible hint rows:

```
⭐ Perfektné:  {site} · {day+window} · 4/4
✓  Možné:     {day+window} · {site} · {best_score ≥ 2/4}
```

Logic:
- **Perfektné** = nearest future window where any site scores `4/4`. If none in 8-window horizon → "— (žiadne 4/4 v nasledujúcich 3 dňoch)".
- **Možné** = nearest future window where any site scores `≥ 2/4`. If none → "Žiadne letové okná v horizonte".
- Click on either row → slider jumps to that slot.
- Empty state: single row "Žiadne letové okná v horizonte" centered.

---

## Schematic Map Contract

Inline SVG rendering of western Slovakia:

| Element | Specification |
|---------|---------------|
| Outline | Simplified political outline of western Slovakia (no admin subdivisions) |
| Terrain hints | Malé Karpaty as a simple curved line; Dunaj as one river line |
| Cities/roads | **None** — kept deliberately minimal |
| Site pins | 3 fixed positions per lat/lon from `.planning/reference/launch-sites.md` |
| Pin color | Driven by score for currently-selected slider slot |
| Pin label | Site name only (no region, no elevation) |
| Pin interaction | **None** — pin is indicator only, clicks go nowhere |
| Wind arrows | Two per pin (see Wind Visualization) |
| Meteoalarm overlay | Small triangular badge on pin when active warning for site's kraj |

### Wind Visualization per pin

Two arrows anchored at pin center, both rotated by wind direction:

| Arrow | Style | Length mapping | Source attribute |
|-------|-------|----------------|------------------|
| Surface (10m) | solid fill, saturated color | `speed_m_s × K`, cap at 8 m/s | `wind_speed_10m`, `wind_direction_10m` |
| Flight altitude (~600m) | outlined, lighter weight | same mapping, cap at 8 m/s | `wind_speed_600m`, `wind_direction_600m` |

Numeric label below pin: `{surface} / {600m} m/s` (e.g. `2.1 / 5.4 m/s`). If 600m altitude data unavailable (API limitation), show `—` instead of `0` in the altitude slot.

---

## Time Slider Contract

### Adaptive 8-Window Sequence

Maximum 8 tiles, computed from current local day-of-week:

| Today | Tile sequence |
|-------|---------------|
| Mon–Wed | today PM, day+1 AM, day+1 PM, day+2 AM, day+2 PM, weekend (So+Ne summary) |
| Thu | today PM, Fri AM, Fri PM, Sat AM, Sat PM, Sun AM, Sun PM |
| Fri | today PM, Sat AM, Sat PM, Sun AM, Sun PM, Mon AM, Mon PM |
| Sat–Sun | today remaining + tomorrow AM/PM + next week tiles |

Rule: windows within 72h are always explicit AM/PM; windows at 72–120h collapse to summary if not weekend.

### Default Open Slot (cutoff-based)

Find earliest future window where `now < window.cutoff`. Cutoffs (configurable):

| Window type | Default cutoff |
|-------------|----------------|
| AM (morning flight ~05:00–09:00) | previous day 23:00 local |
| PM (evening flight ~17:00–20:00) | same day 13:00 local |

Cutoff values must be user-configurable via config flow — rationale: different pilots need different lead-time before calling passengers.

Example transitions:
- Tue 12:59 → default = Tue PM (cutoff 13:00 not passed)
- Tue 13:01 → default = Wed AM (Tue 13:00 passed, Tue 23:00 not)
- Tue 23:01 → default = Wed PM (Tue 23:00 passed)

### Interaction Gestures

| Input | Behavior | Priority |
|-------|----------|----------|
| Horizontal swipe on slider area | Scrub through tiles; map pins + detail panel update in real time; snap to nearest tile on release | Primary |
| Tap on individual tile pill | Discrete jump to that slot | Accessibility fallback |
| Click on banner line | Jump to that slot | Shortcut |

Long-press and drag beyond slider bounds: reserved for future hourly-scrub mode; NOT in scope for 04-02.

---

## Detail Panel Contract

Rendered below slider; content driven by currently-selected slot.

Layout: vertical list of **all 3 sites sorted by score (best → worst)**.

Per-site row:
- Site name + score badge (color + icon + `X/4`)
- Launch time for this slot (or "—" if no computed window)
- Surface wind: `{speed} m/s {direction}` with arrow glyph
- 600m wind: `{speed} m/s {direction}` with arrow glyph, or `—` if unavailable
- Meteoalarm badge if warning active for site's kraj
- If score < 2/4: human-readable NO-GO reason (e.g. "W vietor 5.4 m/s + ridge efekt Malých Karpát")

Reason text comes from scoring component (terrain-aware). Card renders it verbatim.

---

## Empty / Error / Stale States

| State | Card behavior |
|-------|---------------|
| No sensor data yet | Render empty banner + gray map + disabled slider + "Čakám na prvé vyhodnotenie" |
| All windows in horizon are NONE | Banner shows "Žiadne letové okná v horizonte"; slider still scrubs; detail panel shows reasons per site |
| Stale data (> 2× refresh interval since `data_last_updated_utc`) | Yellow stale-data badge in banner area; values remain visible (from 02-CONTEXT D-08) |
| Temporary fetch error | Preserve last known values + stale badge + subtle retry indicator |
| 600m wind unavailable for a site | Show `—` in that row; do not collapse the row |

---

## Copywriting Contract (Slovak, primary)

| Element | Copy |
|---------|------|
| Banner line 1 label | `Perfektné` |
| Banner line 2 label | `Možné` |
| Banner empty fallback | `Žiadne letové okná v horizonte` |
| Banner perfect absent | `— (žiadne 4/4 v nasledujúcich 3 dňoch)` |
| Stale badge | `Staré dáta` |
| NO-GO chip text | `Nie` |
| Meteoalarm tooltip prefix | `Meteoalarm {kraj_code}` |
| Detail wind surface label | `Prízemie` |
| Detail wind altitude label | `600 m` |
| Detail altitude unavailable | `—` |

English localization deferred to future phase.

---

## Registry Safety

| Registry | Blocks Used | Safety Gate |
|----------|-------------|-------------|
| shadcn official | none | not applicable |
| third-party | none | not applicable |

---

## Interaction Summary (what the card guarantees)

1. Banner answers "should I call passengers?" within 500 ms of card mount.
2. Map makes wind direction changes across 3 sites readable without reading numbers.
3. Swipe slider updates pins + detail in under 100 ms per tile.
4. Default slot is cutoff-aware so the opening view is never an already-impossible window.
5. Every severity signal is triple-encoded (color + icon + number).
6. No click traps: pins do nothing on click; slider is the only navigation affordance (plus banner shortcut).

---

## Source Decisions Applied

From design discussion (see 04-DISCUSSION-LOG.md):
- **UX-01:** Purpose is *planning*, not reporting — one-glance "when and where" to coordinate passengers.
- **UX-02:** Pilot must see numeric data; banner is a hint, never the decision.
- **UX-03:** Wind surface + ~600m required per slot. 600m not always available → degrade to `—`.
- **UX-04:** 4-level severity with redundant encoding (color + icon + number).
- **UX-05:** Schematic map preferred over OSM (clarity on mobile, lightweight).
- **UX-06:** Pin is indicator only; no click action. Data lives in detail panel.
- **UX-07:** Two-line banner: nearest `4/4` (perfect) and nearest `≥2/4` (possible).
- **UX-08:** Swipe gesture is primary slider control; tap is accessibility fallback.
- **UX-09:** Default slot is cutoff-based, not score-based (AM cutoff = prev day 23:00, PM cutoff = same day 13:00, configurable).
- **UX-10:** Adaptive 8-window sequence; weekend collapses to summary if > 72h away, explicit AM/PM within 72h.
- **UX-11:** Meteoalarm badge is parallel to score, not absorbed into score.
- **UX-12:** NO-GO rows include terrain-aware human explanation (from scorer).

From `04-CONTEXT.md`:
- D-01..D-09 (three-site scope, legacy sensor compat, comparison-first baseline) remain in force.

From `04-01-SUMMARY.md`:
- Card consumes `sites_summary`, `sites`, `selected_site_id` contracts established in 04-01.

---

## Out of Scope for 04-02

- Filter-by-passenger-region (future: dropdown limiting visible sites per passenger origin) — deferred per user.
- Hourly fine-grain scrub beyond discrete windows — deferred.
- Heatmap secondary view toggle — deferred.
- English localization — Slovak only for v1.
- OSM / tile-based map — schematic only.
- Adding 4th+ launch site — still locked to 3 per D-01.

---

## Checker Sign-Off

- [ ] Dimension 1 Copywriting: PASS
- [ ] Dimension 2 Visuals: PASS
- [ ] Dimension 3 Color: PASS
- [ ] Dimension 4 Typography: PASS
- [ ] Dimension 5 Spacing: PASS
- [ ] Dimension 6 Registry Safety: PASS

**Approval:** pending
