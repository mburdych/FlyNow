---
phase: 07
phase_name: "Flight Log Import + Map Visualization (BACKLOG)"
project: "FlyNow"
generated: "2026-04-28"
counts:
  decisions: 10
  lessons: 5
  patterns: 5
  surprises: 3
missing_artifacts:
  - "VERIFICATION.md"
  - "UAT.md"
---

# Phase 07 Learnings: Flight Log Import + Map Visualization (BACKLOG)

## Decisions

### D-01: GPX + CSV as first-class import formats
Support both GPX and CSV as official import formats in v1.

**Rationale:** Balanced format coverage with manageable parser scope; covers both native track-format users (GPX) and flexible exporters (CSV).
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-02: Timestamp policy — UTC/RFC3339 or explicit-offset only
Accept strict UTC/RFC3339 or local timestamps with explicit offset; reject naive local timestamps.

**Rationale:** Naive timestamps cause forecast/observed lookup misalignment and break delayed-import correlation. Inferring TZ from HA location was rejected as too implicit.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md, 07-RESEARCH.md (Pitfall 1)

---

### D-03: Partial-success import — drop invalid points, keep valid ones, emit warnings
Import does not fail-fast on point-level quality issues; it preserves usable data and surfaces a structured warning list.

**Rationale:** Real-world GPX/CSV exports are noisy; aborting the entire import on one bad point destroys usability. Warnings keep the operator informed.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-04: Sidecar storage keyed by flight ID
Imported track + weather payload lives in a sidecar store, not embedded in `flynow_flights.json`.

**Rationale:** Preserves backward compatibility for existing flight-log consumers (Phase 03 contract) and isolates heavy payloads from the compact list view.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-05: Persist full raw points + derived summary metrics
Sidecar stores both raw track points and pre-computed summary metrics.

**Rationale:** Auditability/replay fidelity requires raw data; UI performance requires derived summaries to avoid recomputation on every render.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-06: Stable UUID as canonical flight identity
Use generated UUID (not composite date+site+balloon, not file hash) as the durable merge/link key.

**Rationale:** Composite keys risk collisions; file hashes are import-specific. UUID enables robust linkage between manual logs and imported payloads.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-07: Freeze forecast at decision time, fallback at import/finalize
Forecast snapshot is captured when FlyNow makes the go/no-go decision; if missing, freeze on flight log finalization or import.

**Rationale:** Forecast APIs cannot reconstruct "what FlyNow knew before launch" days later; only decision-time snapshots preserve that truth. Fallback covers cases where import precedes a captured snapshot.
**Source:** 07-CONTEXT.md, 07-RESEARCH.md, 07-DISCUSSION-LOG.md

---

### D-08: Observed-weather provider chain — METAR → archive → manual
Deterministic source priority: METAR history first, Open-Meteo archive second, manual pilot entry last.

**Rationale:** External station-observed data (METAR) outranks reanalysis/model output for "reality" semantics; manual is last resort. Provenance is persisted alongside values.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md, 07-RESEARCH.md

---

### D-09: Immutable base + append-only corrections
Snapshots are never mutated in place; corrections are appended as separate records with source/reason/timestamp.

**Rationale:** Mutation destroys the audit trail and breaks forensic correlation analysis. Append-only model makes conflicts visible.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

### D-10: Import never blocks on weather lookup failure
If historical weather lookup fails, import still completes with explicit `weather_missing` flag and reason.

**Rationale:** Delayed imports must remain operable even when external providers are flaky or out of retention window. Operation flow > completeness guarantee.
**Source:** 07-CONTEXT.md, 07-DISCUSSION-LOG.md

---

## Lessons

### Decision-time snapshots are the only reliable source of "forecast as known"
Open-Meteo and other forecast endpoints cannot retrieve the forecast that was active at a past `t`; only stored snapshots preserve it. Without snapshot capture in the coordinator, post-flight forecast-vs-reality comparison would always be reconstructed (and wrong).

**Context:** Discovered while researching whether archive APIs could substitute for decision-time freezing — they can serve "observed reality" but not "forecast at the time."
**Source:** 07-RESEARCH.md (Summary, Anti-Patterns)

---

### Existing flight log contract is fragile to record-shape changes
Phase 03's `flynow_flights.json` consumers (card list view, tests, sensor projections) assume a compact record shape. Embedding heavy track/weather payloads inline would have triggered cascading frontend and test breakage.

**Context:** Confirmed during pattern mapping; sidecar approach was chosen specifically to avoid touching the canonical record shape.
**Source:** 07-PATTERNS.md (flight_log.py analog), 07-RESEARCH.md (Summary)

---

### METAR has retention limits — archive fallback is mandatory, not optional
AviationWeather METAR API is strong for ~15-day windows but does not cover long history. For imports that arrive months later, only Open-Meteo archive (or manual entry) can provide observed values.

**Context:** Surfaced during research while validating D-08 priority order; the chain is not just preference but a coverage necessity.
**Source:** 07-RESEARCH.md (Summary, Standard Stack)

---

### Leaflet lifecycle leaks if not isolated from Lit re-renders
Embedding Leaflet calls directly in `flynow-card.ts` render() risks duplicate map instances, orphaned event listeners, and memory leaks across card detach/re-render cycles. Required a dedicated lifecycle wrapper.

**Context:** Recognized in research as a known HA custom-card pitfall; led to creating `map-renderer.ts` as a separate utility module with init/update/dispose semantics.
**Source:** 07-RESEARCH.md (State of the Art, Pattern 3), 07-PATTERNS.md (map-renderer.ts no-analog entry)

---

### Sensor attributes must stay bounded — raw tracks belong in sidecar only
Embedding full point arrays in HA sensor state degrades Lovelace render performance and bloats backups. Required a deliberate split: full raw in sidecar file, compact summary in sensor.

**Context:** Listed as Pitfall 3 in research; enforced by D-05 + sensor projection task in 07-02-PLAN.md.
**Source:** 07-RESEARCH.md (Pitfall 3), 07-02-PLAN.md (Task 3)

---

## Patterns

### Backend-Canonical Import Validation
Parse and validate GPX/CSV in the HA service handler; keep frontend validation lightweight (file type/size only). Canonical schema lives backend-side.

**When to use:** Any import that writes durable state or feeds analytics/correlation. Avoid client-side-only validation when the data influences forecasts or audit records.
**Source:** 07-RESEARCH.md (Pattern 1), 07-PATTERNS.md (flight_import.py analog)

---

### Immutable Base + Append-Only Corrections
Snapshot records have an immutable `base` block and a `corrections[]` array. Each correction carries `ts`, `source`, `field`, `value`, and `reason`. No in-place edits.

**When to use:** Any late data repair, provider mismatch reconciliation, or manual override that must remain auditable.
**Source:** 07-RESEARCH.md (Pattern 2), 07-CONTEXT.md (D-09)

---

### Sidecar Storage Keyed by Stable UUID
Heavy or evolving per-record payloads live in a separate file/store keyed by the canonical UUID; the legacy compact record stays unchanged. Atomic write + lock-scoped read-modify-write.

**When to use:** When extending an existing record-set with optional rich data while preserving backward compatibility for existing consumers/tests.
**Source:** 07-PATTERNS.md (flight_sidecar_store.py), 07-CONTEXT.md (D-04, D-06)

---

### Isolated Map Renderer Lifecycle
Encapsulate Leaflet (or any browser map engine) in a dedicated module exposing `init / updateTrack / dispose`. Card component owns state; renderer owns DOM/lib lifecycle.

**When to use:** Any dynamic map rendering inside a Lit-based custom card; prevents lifecycle leaks across re-renders.
**Source:** 07-RESEARCH.md (Pattern 3, State of the Art), 07-03-PLAN.md (Task 2)

---

### Compact Sensor Projection of Heavy Sidecar Data
Sensor exposes only summary fields (`observed_source`, `weather_missing`, `weather_missing_reason`, `correction_count`); raw track and full snapshot stay off HA state. Frontend fetches detail on demand.

**When to use:** Whenever a phase adds bulky per-record data behind an existing sensor entity. Keeps state payload bounded for Lovelace and backups.
**Source:** 07-02-PLAN.md (Task 3), 07-PATTERNS.md (sensor.py analog)

---

## Surprises

### Map renderer needed lazy Leaflet import for Node test execution
Node-based card tests cannot eagerly import Leaflet (browser-only globals); required adjusting `map-renderer.ts` to lazy-load Leaflet on init rather than at module load time.

**Impact:** Only deviation recorded across the entire phase. Caught during test wiring; trivial to apply but worth remembering for any future browser-only library brought into the card.
**Source:** 07-03-SUMMARY.md (Deviations)

---

### AviationWeather legacy `/cgi-bin` endpoints are gone
Older HA forum recipes reference the deprecated AviationWeather CGI interface; the current API is `/api/data/*` with revised schema. Any planning that copied old patterns would have produced broken integration code.

**Impact:** Forced research to validate every external API claim against current docs; reinforces the "verify version" discipline before committing to a provider integration.
**Source:** 07-RESEARCH.md (State of the Art / Deprecated)

---

### No prior renderer-utility analog existed in the card codebase
Pattern mapping found 9/9 analogs for new files except `map-renderer.ts` — the card historically inlined all rendering as helper methods on the component. This phase introduced the first standalone utility module under `lovelace/flynow-card/src/`.

**Impact:** Set a new convention for the frontend codebase: future complex/lifecycle-bound rendering concerns can follow the same isolated-utility pattern instead of growing `flynow-card.ts`.
**Source:** 07-PATTERNS.md (No Analog Found section)

---
