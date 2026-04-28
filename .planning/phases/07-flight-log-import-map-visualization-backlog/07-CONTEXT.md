# Phase 07: Flight Log Import + Map Visualization (BACKLOG) - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 07 adds delayed-friendly flight import with track visualization and immutable weather correlation context so crew can compare what FlyNow predicted vs what was actually observed at flight time.

This phase covers import contract, persistence model, weather snapshot strategy, and map/privacy direction. It does not introduce a full analytics suite or expand beyond the existing flight-log domain.

</domain>

<decisions>
## Implementation Decisions

### Import Contract + Validation
- **D-01:** Support `GPX` and `CSV` as first-class import formats.
- **D-02:** Timestamp policy accepts either strict UTC/RFC3339 or local timestamps with explicit offset; naive local timestamps are rejected.
- **D-03:** Import is resilient for point-level quality issues: drop invalid points, keep valid points, and report warnings.

### Data Model + Persistence
- **D-04:** Store imported track/weather payload in a sidecar store keyed by flight ID to preserve backward compatibility for existing `flynow_flights.json` consumers.
- **D-05:** Track persistence stores full raw points plus derived summary metrics for both auditability and fast UI rendering.
- **D-06:** Canonical flight identity is a generated stable UUID per flight.

### Forecast vs Reality Snapshot Strategy
- **D-07:** Freeze forecast snapshot at FlyNow decision time; if missing, freeze during flight log finalization/import.
- **D-08:** Observed reality source priority is `METAR history` -> `historical/archive API` -> `manual pilot entry`.
- **D-09:** Snapshot policy is immutable base records with append-only correction records.
- **D-10:** If historical weather lookup fails, import still succeeds with explicit `weather_missing` flag and failure reason.

### Claude's Discretion
- Exact CSV column naming/versioning as long as required fields and timezone constraints remain enforced.
- Exact warning payload schema and surfacing style for dropped points.
- Exact sidecar file partitioning/chunking strategy, provided linkage by stable UUID is deterministic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope + Product Direction
- `.planning/ROADMAP.md` — Phase 07 goal, delayed-import constraints, and task checklist.
- `.planning/PROJECT.md` — shipped scope context and product boundaries.
- `.planning/STATE.md` — current milestone/deployment context and ordering constraints.

### Prior Decisions to Carry Forward
- `.planning/phases/03-flight-logging/03-CONTEXT.md` — existing flight-log required fields and atomic persistence expectations.
- `.planning/phases/04-multi-site-forecast-planning-card/04-CONTEXT.md` — card-level comparison intent and payload projection conventions.
- `.planning/phases/06-lovelace-card-language-toggle-backlog/06-CONTEXT.md` — current card interaction and persistence patterns.

### Existing Code Surface
- `custom_components/flynow/flight_log.py` — current flight logging schema and persistence behavior.
- `custom_components/flynow/coordinator.py` — decision-time weather computation path where forecast snapshots can be captured.
- `custom_components/flynow/sensor.py` — entity attribute contract exposed to Lovelace.
- `lovelace/flynow-card/src/flynow-card.ts` — card rendering and interaction integration point for map/correlation UI.
- `lovelace/flynow-card/src/types.ts` — frontend typing contracts for extended payload shape.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `custom_components/flynow/flight_log.py`: already owns local JSON persistence semantics and is the natural entry for import/finalize linkage.
- `custom_components/flynow/coordinator.py`: already computes decision-time weather context and can emit freezeable snapshots.
- `lovelace/flynow-card/src/flynow-card.ts`: existing summary/detail rendering flow can host correlation and map-facing sections.

### Established Patterns
- Integration favors async service handlers plus atomic JSON writes for durable local state.
- Frontend uses strict TypeScript contracts and derived rendering from one sensor payload.

### Integration Points
- Import service should attach/merge by stable UUID with existing flight records.
- Snapshot capture should hook both decision-time flow and import/finalization fallback path.
- Map/correlation rendering should consume typed sidecar-linked payload, not ad-hoc local parsing.

</code_context>

<specifics>
## Specific Ideas

- Keep delayed-import reliability as first-class behavior: do not block import on missing weather provider data.
- Preserve a forensic trail by storing immutable baseline plus append-only corrections.
- Prioritize verifiable external observations (`METAR`) before lower-confidence/manual fallback.

</specifics>

<deferred>
## Deferred Ideas

- Broader analytics dashboard beyond per-flight correlation view.
- Additional import sources beyond GPX/CSV in initial phase scope.
- Advanced privacy modes (e.g., route obfuscation profiles by role) beyond baseline map/privacy policy.

</deferred>

---

*Phase: 07-flight-log-import-map-visualization-backlog*
*Context gathered: 2026-04-28*
