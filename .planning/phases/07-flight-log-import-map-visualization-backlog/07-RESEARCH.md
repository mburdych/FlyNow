# Phase 07: Flight Log Import + Map Visualization (BACKLOG) - Research

**Researched:** 2026-04-28  
**Domain:** Delayed flight import, geospatial track rendering, immutable weather correlation  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- Broader analytics dashboard beyond per-flight correlation view.
- Additional import sources beyond GPX/CSV in initial phase scope.
- Advanced privacy modes (e.g., route obfuscation profiles by role) beyond baseline map/privacy policy.
</user_constraints>

## Summary

Phase 07 should be planned as an additive extension to existing flight logging, not a rewrite. Current persistence already uses atomic JSON writes and stable UUID IDs in `custom_components/flynow/flight_log.py`, and current card/service contracts assume a compact list of records in `flynow_flights.json`; therefore sidecar storage keyed by the existing UUID is the safest path for compatibility. [VERIFIED: codebase `custom_components/flynow/flight_log.py`, `tests/test_flight_log.py`]

Delayed import fundamentally changes weather-correlation reliability: forecast APIs cannot fully reconstruct "what FlyNow knew before launch" unless a snapshot was stored at decision time. The current coordinator computes forecast windows but does not persist immutable forecast snapshots, so the plan must add snapshot capture hooks in coordinator/finalize-import paths and append-only correction semantics. [VERIFIED: codebase `custom_components/flynow/coordinator.py`, `custom_components/flynow/flight_log.py`; CITED: https://open-meteo.com/en/docs]

For observed weather when imports happen days later, METAR API is strong for near-term recency and station-truth but is time-window limited; Open-Meteo archive/reanalysis provides long-tail historical coverage by lat/lon/time and should be fallback after METAR. [CITED: https://aviationweather.gov/data/api/; CITED: https://open-meteo.com/en/docs/historical-weather-api]

**Primary recommendation:** Implement import + map around an immutable `flight_id`-linked sidecar (`track`, `weather_snapshot`, `corrections`) with provider chain `METAR -> Open-Meteo archive -> manual`, and never block import on weather enrichment failure. [VERIFIED: phase decisions D-04..D-10]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| GPX/CSV parsing + validation | API / Backend | Browser / Client | Canonical validation and durable writes must run server-side; client pre-validation is optional UX. [VERIFIED: codebase pattern in service handlers] |
| Stable UUID linkage to existing logs | API / Backend | Database / Storage | UUID lifecycle and linkage integrity belong to persistence boundary. [VERIFIED: codebase `id` generation] |
| Raw track storage + derived metrics | Database / Storage | API / Backend | Storage owns durable payload; backend computes summaries to avoid client duplication. [VERIFIED: D-05] |
| Forecast snapshot freeze | API / Backend | Database / Storage | Snapshot timing depends on decision/finalization workflow, not UI. [VERIFIED: D-07] |
| Reality provider orchestration | API / Backend | External APIs | Backend controls retries, provenance, and failure flags. [VERIFIED: D-08, D-10] |
| Track/map rendering | Browser / Client | API / Backend | Visualization is frontend concern; backend serves normalized geometry/summary. [VERIFIED: existing card architecture] |
| Privacy redaction policy | API / Backend | Browser / Client | Privacy-safe defaults and data minimization must be enforced before data reaches frontend. [ASSUMED] |

## Project Constraints (from .cursor/rules/)

- Use HAOS deploy topology and paths from `.planning/reference/HAOS-DEPLOYMENT.md`; `/config/www/community/` must not be used. [CITED: `.cursor/rules/haos-deployment.mdc`]
- SSH deployment is key-based on port 22; `ha` CLI is unavailable in SSH session, so restart must be done via HA UI. [CITED: `.cursor/rules/haos-deployment.mdc`]
- Python integration changes must remain async and HA-conventional (`config_entries`, coordinator pattern, strict lint/type expectations). [CITED: `CLAUDE.md`]
- Workflow pattern in this project uses GSD phase-oriented flow (`/gsd-plan-phase` with research/planning verification) rather than ad-hoc edits. [CITED: `CLAUDE.md`; VERIFIED: inspected `gsd-plan-phase` / `gsd-research-phase` skills]
- No project-local `.claude/skills/` directory exists in repo, so planning should rely on standard GSD workflow skills and existing phase artifacts. [VERIFIED: `ls .claude/skills`]

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `csv`, `datetime`, `uuid`, `json`, `xml.etree` | bundled | Baseline CSV parsing, timestamp normalization, sidecar writes | Zero extra dependency surface for strict schema + timezone guardrails. [VERIFIED: codebase + Python runtime] |
| `gpxpy` | 1.6.2 | Robust GPX parser for tracks/segments/points | Mature parser avoids fragile hand-rolled XML GPX handling. [VERIFIED: pip index] |
| `lit` | 3.3.2 (repo), compatible with map libs | Card rendering foundation | Already used by card; keeps map integration incremental. [VERIFIED: `lovelace/flynow-card/package.json`] |
| `leaflet` | 1.9.4 (latest stable), 2.0.0-alpha.1 (alpha) | Browser map rendering for polyline + markers | Stable and widely used in HA map ecosystem; avoid alpha in this phase. [VERIFIED: npm registry; CITED: https://leafletjs.com/reference.html] |
| `PapaParse` | 5.5.3 | Browser CSV prototype parsing (optional) | Handles field mismatch/errors and large-file streaming ergonomically. [VERIFIED: npm registry; CITED: https://www.papaparse.com/docs] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@mapbox/togeojson` | 0.16.2 | GPX->GeoJSON conversion in frontend prototypes | Use only if client-side GPX preview is needed before upload. [VERIFIED: npm registry] |
| AviationWeather Data API (`/api/data/metar`) | N/A (service API) | METAR-based observed reality, priority source | Use for near-term observed validation where station/time coverage exists (up to previous 15 days). [CITED: https://aviationweather.gov/data/api/] |
| Open-Meteo archive API (`/v1/archive`) | N/A (service API) | Historical/reanalysis fallback by lat/lon/date | Use when METAR unavailable or outside retention window; supports long historical ranges. [CITED: https://open-meteo.com/en/docs/historical-weather-api] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Leaflet map in custom card | Native HA map card | Native card is simpler but less fit for immutable forecast/reality overlays and custom import UX. [CITED: https://www.home-assistant.io/lovelace/map/] |
| `gpxpy` backend parse | `@mapbox/togeojson` only | Browser-only conversion weakens server-side canonical validation and auditability. [ASSUMED] |
| METAR primary | Open-Meteo archive only | Archive has wider history; METAR remains stronger for station-observed "reality" semantics. [CITED: aviationweather + open-meteo docs] |

**Installation:**
```bash
pip install gpxpy
npm install leaflet papaparse @mapbox/togeojson
```

**Version verification:**  
- `leaflet` latest stable `1.9.4` (published 2023-05-18; alpha exists). [VERIFIED: npm registry]  
- `papaparse` latest `5.5.3` (published 2025-05-19). [VERIFIED: npm registry]  
- `@mapbox/togeojson` latest `0.16.2` (published 2023-09-27). [VERIFIED: npm registry]  
- `gpxpy` latest `1.6.2`. [VERIFIED: `pip index versions gpxpy`]

## Architecture Patterns

### System Architecture Diagram

```text
[User uploads GPX/CSV in card]
          |
          v
[Frontend pre-checks: file type/size only]
          |
          v
[HA service: import_flight_track]
          |
          +--> [Parse + timezone validate + drop bad points w/ warnings]
          |             |
          |             v
          |    [Persist sidecar by flight_id: raw track + derived summary]
          |
          +--> [Weather snapshot resolver]
                     |
                     +--> [Forecast snapshot exists? yes -> freeze existing]
                     |                              no -> freeze on import/finalize
                     |
                     +--> [Observed chain: METAR -> Open-Meteo archive -> manual]
                     |
                     v
            [Immutable base + append-only corrections]
                     |
                     v
 [Sensor attributes / dedicated service payload for card correlation view]
                     |
                     v
       [Map + Forecast vs Reality comparison UI]
```

### Recommended Project Structure
```text
custom_components/flynow/
├── flight_log.py                 # Existing base flight log service/store
├── flight_import.py              # NEW import parser + validation orchestration
├── flight_sidecar_store.py       # NEW sidecar atomic persistence keyed by flight_id
├── weather_snapshot.py           # NEW snapshot freeze + provider-chain resolver
└── sensor.py                     # Extended attributes/projections (bounded)

lovelace/flynow-card/src/
├── flynow-card.ts                # Import UI + map/correlation sections
├── types.ts                      # Extended types for track/snapshot payloads
└── map-renderer.ts               # NEW isolated Leaflet rendering adapter
```

### Pattern 1: Backend-Canonical Import Validation
**What:** Parse and validate GPX/CSV in backend service; keep frontend validation lightweight. [VERIFIED: existing HA service pattern]
**When to use:** Any import that writes durable state or influences forecast/reality analytics.
**Example:**
```python
# Source: existing service pattern in custom_components/flynow/flight_log.py
async def _handle_import(call: Any) -> dict[str, Any]:
    payload = IMPORT_SCHEMA(dict(call.data))
    normalized = normalize_import_payload(payload)  # timezone + point validation
    saved = await sidecar_store.async_upsert(normalized)
    return {"flight_id": saved["flight_id"], "warnings": saved["warnings"]}
```

### Pattern 2: Immutable Snapshot + Append-Only Corrections
**What:** Never mutate base forecast/reality snapshot; add correction records with provenance/timestamp. [VERIFIED: D-09]
**When to use:** Any late data repair, provider mismatch, or manual override.
**Example:**
```python
# Source: phase decision D-09
snapshot = {
    "base": {"forecast": forecast_obj, "observed": observed_obj, "frozen_at": frozen_at},
    "corrections": [
        {"ts": correction_ts, "source": "manual", "field": "wind_speed_10m", "value": 4.2}
    ],
}
```

### Pattern 3: Map Rendering Isolation
**What:** Encapsulate Leaflet setup/teardown in a dedicated renderer module to avoid Lit lifecycle leaks. [CITED: Leaflet docs + community behavior]
**When to use:** Any dynamic re-rendering of track layers in custom cards.
**Example:**
```typescript
// Source: https://leafletjs.com/reference.html
const map = L.map(container, { attributionControl: true });
L.tileLayer(urlTemplate, { attribution }).addTo(map);
L.polyline(latLngs, { color: "#1e88e5" }).addTo(map);
```

### Anti-Patterns to Avoid
- **Recomputing historical "forecast as known" from archive only:** this is not equivalent to decision-time forecast and breaks D-07 intent. [CITED: Open-Meteo forecast/archive docs]
- **Blocking import on weather provider failures:** contradicts D-10 and harms delayed-import reliability. [VERIFIED: D-10]
- **Mutating existing snapshots in place:** destroys audit trail and conflict analysis. [VERIFIED: D-09]
- **Loading huge raw tracks directly into card attributes:** risks HA state bloat and frontend latency. [ASSUMED]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GPX XML parsing | Custom XML traversal + waypoint logic | `gpxpy` | GPX variants/segments/extensions are error-prone to parse manually. [VERIFIED: gpxpy package + GPX domain] |
| CSV edge-case parser | Custom split/quote parser | `csv` module backend, optional PapaParse frontend | Quoting, escaped delimiters, and row mismatches are non-trivial. [CITED: https://www.papaparse.com/docs] |
| Interactive map engine | Handcrafted canvas/SVG map | `leaflet` | Tile layers, projection, pan/zoom, attribution are solved problems. [CITED: https://leafletjs.com/reference.html] |
| Observation provider abstraction from scratch without provenance | Opaque "best effort" merge | Explicit provider chain + source tagging | Correlation accuracy depends on traceable source and fallback path. [VERIFIED: D-08] |

**Key insight:** this phase risk is data integrity and provenance, not map drawing; invest effort in immutable snapshot + provenance model first, then UI polish. [VERIFIED: phase scope + decisions]

## Common Pitfalls

### Pitfall 1: Timezone Drift in Imported Tracks
**What goes wrong:** imported local times are misaligned with forecast/observed lookups. [VERIFIED: D-02 relevance]  
**Why it happens:** naive timestamps (no offset) or mixed timezone formats. [VERIFIED: D-02]  
**How to avoid:** reject naive local times, normalize to UTC internally, store original timezone metadata. [VERIFIED: D-02]  
**Warning signs:** impossible launch/landing sequence, observed lookup returning wrong hour blocks.

### Pitfall 2: Conflating Forecast and Observed Semantics
**What goes wrong:** "reality" is filled with model reanalysis and treated as station observation. [CITED: METAR vs reanalysis docs]  
**Why it happens:** missing source provenance fields. [ASSUMED]  
**How to avoid:** persist `source_type` (`metar`, `archive`, `manual`) with confidence rank and retrieval timestamp. [VERIFIED: D-08]  
**Warning signs:** operator confusion during post-flight review.

### Pitfall 3: Unbounded Payload Growth
**What goes wrong:** large tracks degrade HA sensor/card performance and backup size. [ASSUMED]  
**Why it happens:** full point arrays embedded in sensor attributes. [ASSUMED]  
**How to avoid:** keep raw track in sidecar file, expose summarized geometry and on-demand detail fetch. [VERIFIED: D-04/D-05 intent]  
**Warning signs:** sluggish Lovelace render, oversized state payloads.

## Code Examples

Verified patterns from official sources:

### CSV Parse with Header Validation
```typescript
// Source: https://www.papaparse.com/docs
Papa.parse(file, {
  header: true,
  skipEmptyLines: "greedy",
  complete(results) {
    // Validate required headers + row-level warnings
  },
});
```

### Leaflet Tile Attribution (legal requirement)
```typescript
// Source: https://leafletjs.com/reference.html
L.tileLayer(tileUrl, {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);
```

### Historical Weather Archive Query Shape
```text
# Source: https://open-meteo.com/en/docs/historical-weather-api
GET /v1/archive?latitude=48.4&longitude=17.6&start_date=2026-04-20&end_date=2026-04-20
  &hourly=wind_speed_10m,wind_direction_10m,precipitation,visibility
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy AviationWeather `cgi-bin` endpoints | Product-specific `/api/data/*` endpoints and revised schema | 2025 API redevelopment | Planner must target new endpoint contracts and error handling. [CITED: https://aviationweather.gov/data/api/] |
| Flat mutable flight-record weather fields | Immutable base + append-only correction entries | Modern audit/provenance practice [ASSUMED] | Enables forensic correlation and trustworthy post-flight analysis. |
| Direct map feature hacking in monolithic card code | Isolated map renderer module with controlled lifecycle | Common HA custom-card maintainability trend [ASSUMED] | Reduces UI regressions and memory leaks. |

**Deprecated/outdated:**
- AviationWeather `/cgi-bin` interface: unsupported and replaced by `/api/data`. [CITED: https://aviationweather.gov/data/api/]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Privacy enforcement should be backend-first before map payload reaches frontend | Architectural Responsibility Map | May require redesign if user explicitly wants client-only privacy controls |
| A2 | Sidecar-to-sensor summarization is necessary to avoid HA payload/perf issues | Anti-patterns / Pitfalls | Could be over-optimization for expected data volumes |
| A3 | Isolating Leaflet renderer as separate module is superior for maintainability | State of the Art | Could add complexity if map scope stays tiny |

## Open Questions (Resolved)

1. **Map delivery mode in initial implementation — RESOLVED**
   - Decision: deliver map rendering inside the existing `flynow-card` using an isolated `map-renderer.ts` module, not a separate dedicated panel/card in Phase 07.
   - Rationale: preserves Phase 07 scope, matches existing Lit card integration patterns, and keeps map lifecycle concerns isolated.
   - Planning impact: implemented through typed contract extension + renderer module + card integration in `07-03-PLAN.md`.

2. **Observed-weather station matching policy — RESOLVED**
   - Decision: use deterministic nearest-station selection for METAR with explicit fallback order per D-08 (`METAR -> archive -> manual`), and persist provenance metadata for selected source.
   - Policy: choose closest eligible station within configured search radius; if no eligible station/data, fall back to archive provider, then manual entry.
   - Planning impact: enforced in snapshot resolver/provider chain tasks in `07-02-PLAN.md`.

3. **Granularity of stored track points — RESOLVED**
   - Decision: persist full raw track points as canonical record per D-05 and additionally store derived summary/simplified geometry for UI performance.
   - Rationale: keeps auditability and replay fidelity while preventing oversized frontend payloads.
   - Planning impact: sidecar persistence + compact sensor projection split across `07-01-PLAN.md` and `07-02-PLAN.md`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Lovelace card build/map libs | ✓ | v22.22.0 | — |
| npm | Installing frontend deps | ✓ | 11.11.0 | — |
| Python | HA backend import services | ✓ | 3.14.3 (local dev) | HAOS runtime Python 3.12.13 |
| pytest | Test execution in this environment | ✗ | — | Use `python -m pytest` after installing pytest |
| AviationWeather API | METAR observed fallback | external | n/a | Open-Meteo archive, then manual |
| Open-Meteo archive API | Historical fallback | external | n/a | Manual observed entry |

**Missing dependencies with no fallback:**
- None for planning; implementation can proceed.

**Missing dependencies with fallback:**
- `pytest` command missing locally; install pytest or run via `python -m pytest` after dependency install.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Reuse HA auth context and service permissions [ASSUMED] |
| V3 Session Management | no | Managed by HA frontend/backend platform [ASSUMED] |
| V4 Access Control | yes | Restrict import/update services to HA-authorized users and service-call context [ASSUMED] |
| V5 Input Validation | yes | Strict schema validation (`voluptuous`) + timestamp format checks [VERIFIED: existing code + D-02] |
| V6 Cryptography | no | No new crypto required; do not hand-roll if future signing/hash arrives [ASSUMED] |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSV formula injection when exported/re-opened | Tampering | Escape formula-leading cells (`=,+,-,@`) if any CSV export/report is added. [CITED: https://www.papaparse.com/docs] |
| Malicious oversized GPX/CSV payload | DoS | File size caps, row/point count caps, stream parsing, timeout guards. [ASSUMED] |
| Coordinate privacy leakage in UI | Information Disclosure | Default privacy policy: minimize precision / optional redaction before frontend projection. [ASSUMED] |
| Provider response spoofing/ambiguity | Tampering | Store provider name, station ID, retrieval timestamp, and immutable record lineage. [VERIFIED: D-08/D-09 intent] |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `custom_components/flynow/flight_log.py`, `custom_components/flynow/coordinator.py`, `custom_components/flynow/sensor.py`, `lovelace/flynow-card/src/flynow-card.ts`, `lovelace/flynow-card/src/types.ts`, `tests/test_flight_log.py`
- Open-Meteo forecast docs: https://open-meteo.com/en/docs
- Open-Meteo historical archive docs: https://open-meteo.com/en/docs/historical-weather-api
- Home Assistant custom card docs: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
- AviationWeather Data API: https://aviationweather.gov/data/api/
- Leaflet API reference: https://leafletjs.com/reference.html
- Papa Parse docs: https://www.papaparse.com/docs
- Package registry checks: `npm view leaflet version time --json`, `npm view papaparse version time --json`, `npm view @mapbox/togeojson version time --json`, `python -m pip index versions gpxpy`

### Secondary (MEDIUM confidence)
- HA map-card ecosystem signal (`ha-map-card`) from web search: https://github.com/nathan-gs/ha-map-card

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - key library/API/runtime claims verified by registry/docs and codebase.
- Architecture: HIGH - tightly constrained by locked decisions D-01..D-10 and existing service/card structure.
- Pitfalls: MEDIUM - timezone/provider issues are well-evidenced; some performance/privacy pitfalls are assumption-based.

**Research date:** 2026-04-28  
**Valid until:** 2026-05-28
