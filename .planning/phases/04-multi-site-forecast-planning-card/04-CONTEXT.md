# Phase 4: Multi-site forecast planning card - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 upgrades FlyNow from one configured launch site to three predefined launch sites and adds a planning-focused card view that compares near-term GO/NO-GO outcomes per site. The integration must keep one authoritative weather-analysis pipeline, but execute it per selected site and expose a per-site state shape consumable by Lovelace.

This phase is limited to forecast planning across the three launch sites in `.planning/reference/launch-sites.md`. It does not add new weather providers or learning logic.

</domain>

<decisions>
## Implementation Decisions

### Multi-site Data Scope
- **D-01:** Supported sites in Phase 4 are locked to the three reference entries only: `lzmada`, `katarinka`, `nitra-luka` (per `.planning/reference/launch-sites.md`).
- **D-02:** Site metadata (id, name, coordinates, elevation, meteoalarm region) is embedded as static integration constants in code for deterministic behavior; no runtime editing UI in this phase.
- **D-03:** Forecast source remains Open-Meteo only for all sites; request by `lat, lon` per site and reuse existing analyzer/window logic.

### Coordinator + Sensor Contract
- **D-04:** Coordinator stores a per-site result map keyed by site id, plus a selected/primary site pointer used by the existing single binary sensor.
- **D-05:** Existing `binary_sensor.flynow_status` remains backward-compatible for automations by projecting the selected site.
- **D-06:** Sensor attributes must additionally expose a compact `sites_summary` payload for all three sites (GO flag, launch window, updated timestamp) for card rendering.

### Card UX Policy
- **D-07:** Card default view is a 3-site planning comparison (cards/rows), not a single-site details-first view.
- **D-08:** Site ordering is fixed and user-facing: Malý Madaras, Katarínka, Nitra lúka.
- **D-09:** Manual site switching is allowed in-card for details, but summary comparison of all sites always remains visible at top.

### Claude's Discretion
- Exact attribute key names for nested multi-site payloads, as long as they are typed and tested.
- Whether per-site forecast fetch is sequential or parallel, if behavior is deterministic and tests validate it.
- Minor card styling details while preserving decision-driven information hierarchy.

</decisions>

<specifics>
## Specific Ideas

- Keep per-site weather analysis strictly delegated to existing `open_meteo.py`, `windows.py`, and `analyzer.py` helpers to avoid logic drift.
- Reuse Phase 2 card stale-data behavior for each site row using `data_last_updated_utc`.
- Include launch-sites reference fields that help users plan quickly: site name, launch window, GO/NO-GO, and region label.

</specifics>

<deferred>
## Deferred Ideas

- User-defined unlimited site CRUD in config flow.
- Blended model scoring (ICON vs ECMWF comparison output).
- METAR/SHMÚ cross-validation pipeline in decision engine.
- Per-site notification routing rules and automatic multi-site fan-out alerts.

</deferred>

---

*Phase: 04-multi-site-forecast-planning-card*
*Context gathered: 2026-04-23*
