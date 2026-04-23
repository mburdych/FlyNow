# Phase 3: Flight Logging - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 adds flight logging to the existing FlyNow Lovelace card so crew can record completed flights and review previously logged entries. This phase covers the log form UX contract and persistent local storage in `/config/flynow_flights.json` with atomic writes.

It does not add learning/scoring logic, messaging changes, or new weather analysis capabilities.

</domain>

<decisions>
## Implementation Decisions

### Form Fields + Defaults
- **D-01:** All core fields are required except notes. Required: date, balloon, launch time, duration, site, and outcome.
- **D-02:** Form prefill behavior: date defaults to today, balloon defaults to last used balloon, site defaults to selected site, duration defaults to 90 minutes.
- **D-03:** Outcome uses a fixed enum with options: `flown`, `cancelled-weather`, `cancelled-other`.
- **D-04:** Launch time entry uses a local 24-hour time picker (not free text).

### Claude's Discretion
- Submission feedback microcopy and visual styling details, as long as success/error state is clear.
- Exact list rendering density for prior logs, while preserving a clear and readable history list.
- Internal JSON schema representation details, as long as LOG-01 fields are fully preserved and storage remains atomically safe.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope + Requirements
- `.planning/ROADMAP.md` — Phase 3 goal, LOG-01 and LOG-02 requirements, and success criteria.
- `.planning/REQUIREMENTS.md` — detailed definitions for flight logging requirements.
- `.planning/PROJECT.md` — project constraints, especially local HA config storage expectation.

### Prior Phase Decisions to Carry Forward
- `.planning/phases/01-core-integration/01-CONTEXT.md` — data conventions and integration boundary.
- `.planning/phases/02-notifications-card/02-CONTEXT.md` — existing card behavior and UX consistency expectations.
- `.planning/phases/04-multi-site-forecast-planning-card/04-CONTEXT.md` — selected-site behavior and card-level context from current implementation.

### Existing Implementation Surface
- `lovelace/flynow-card/src/flynow-card.ts` — current card structure and interaction patterns.
- `lovelace/flynow-card/src/types.ts` — frontend attribute/data contracts.
- `custom_components/flynow/coordinator.py` — existing integration data flow.
- `custom_components/flynow/sensor.py` — current entity exposure patterns.

No external ADR/spec files were referenced during this discussion.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `lovelace/flynow-card/src/flynow-card.ts`: Existing card rendering and site selection interaction can host the logging form and log list UI.
- `lovelace/flynow-card/src/types.ts`: Existing typed interface patterns should be extended for log form/list contracts.

### Established Patterns
- Card is already summary-first with detail sections and explicit stale-state signaling; logging UI should follow this style.
- Integration remains coordinator/sensor-driven; log persistence should align with HA async patterns and local file handling.

### Integration Points
- Card form submission should call a backend service endpoint in the integration domain.
- Persistence should resolve path via HA config directory and write atomically to `flynow_flights.json`.

</code_context>

<specifics>
## Specific Ideas

- Preserve exactly the LOG-01 field set in stored records.
- Keep defaults tuned for frequent repeated operations (same balloon/site, default 90 min).
- Use local 24-hour time semantics to match existing ops workflow.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-flight-logging*
*Context gathered: 2026-04-23*
