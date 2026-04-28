# Phase 07: Flight Log Import + Map Visualization (BACKLOG) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `07-CONTEXT.md` — this log preserves alternatives considered.

**Date:** 2026-04-28
**Phase:** 07-flight-log-import-map-visualization-backlog
**Areas discussed:** Import format + validation, Data model + persistence, Weather snapshot strategy

---

## Import format + validation

| Option | Description | Selected |
|--------|-------------|----------|
| GPX + CSV | Balanced support and manageable parser scope | ✓ |
| GPX only | Simplest parser scope, strongest native track semantics | |
| CSV only | Flexible exports, higher validation burden | |

**User's choice:** GPX + CSV
**Notes:** Chosen as initial official support.

| Option | Description | Selected |
|--------|-------------|----------|
| Strict UTC/RFC3339 only | Deterministic weather correlation | |
| UTC/RFC3339 OR local+offset | Accept explicit-offset local times and normalize | ✓ |
| Naive local accepted | Infer timezone from HA location | |

**User's choice:** Combined strict UTC + explicit-offset local acceptance (`a+b` clarified to mixed policy).
**Notes:** Naive local timestamps rejected.

| Option | Description | Selected |
|--------|-------------|----------|
| Fail fast | Entire import aborts on first hard error | |
| Drop invalid points, keep rest | Preserve usable data with warning report | ✓ |
| Strict required, soft quality | Mixed strictness model | |

**User's choice:** Drop invalid points and continue.
**Notes:** Requires explicit warning surfacing.

---

## Data model + persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Sidecar by flight ID | Preserve old consumers, isolate heavy payloads | ✓ |
| Embed optional fields in existing record | Single-file simplicity, larger records | |
| Dual mode migratable | Start embedded then migrate | |

**User's choice:** Sidecar store keyed by flight ID.
**Notes:** Compatibility with existing `flynow_flights.json` consumers is a priority.

| Option | Description | Selected |
|--------|-------------|----------|
| Full raw + derived summary | Auditability plus fast render | ✓ |
| Downsampled only | Smaller storage, lower fidelity | |
| Summary only | Minimal storage, no replay fidelity | |

**User's choice:** Full raw points plus derived summary.
**Notes:** Supports future diagnostics and map rendering.

| Option | Description | Selected |
|--------|-------------|----------|
| Stable UUID | Durable merge/link key | ✓ |
| Composite date/time+site+balloon | Human-readable but collision risk | |
| Source file hash | Import-specific identity | |

**User's choice:** Stable UUID as canonical identity.
**Notes:** Enables robust linking between manual logs and imported payloads.

---

## Weather snapshot strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Freeze at decision time; fallback on finalize/import | Best preserves "forecast as known then" | ✓ |
| Freeze only on import | Simpler but loses earlier decision context | |
| Recompute on demand | Always current but not immutable history | |

**User's choice:** Freeze at decision time, fallback to finalize/import when missing.
**Notes:** Protects delayed imports from provider retention limits.

| Option | Description | Selected |
|--------|-------------|----------|
| METAR -> archive API -> manual | Verifiable-first source chain | ✓ |
| Archive API -> METAR -> manual | Provider-first chain | |
| Manual first | Fastest but lowest external validation | |

**User's choice:** METAR first, then archive API, then manual fallback.
**Notes:** External evidence preferred where available.

| Option | Description | Selected |
|--------|-------------|----------|
| Immutable + append corrections | Preserves original and allows audit-safe fixes | ✓ |
| Fully mutable latest-wins | Simpler edits, weak audit trail | |
| Immutable no corrections | Strong immutability, low recoverability | |

**User's choice:** Immutable base snapshots with append-only corrections.
**Notes:** Audit trail required.

| Option | Description | Selected |
|--------|-------------|----------|
| Import succeeds with weather-missing flag | Keeps operation flow unblocked | ✓ |
| Block import | Strong completeness guarantee, bad UX risk | |
| Store nearest-time estimate | Best effort, can blur truthfulness | |

**User's choice:** Import succeeds with explicit missing-weather flag and reason.
**Notes:** Delayed imports must remain operable.

---

## Claude's Discretion

- CSV schema key naming/version strategy within selected validation policy.
- Warning payload formatting for dropped points.
- Sidecar partitioning details (single file vs segmented) while preserving stable UUID linking.

## Deferred Ideas

- Rich analytics dashboards beyond per-flight correlation.
- Non-GPX/CSV import source expansion.
- Advanced role-based privacy obfuscation presets.
