# Phase 09: Fog Risk Hardening — Trend Monotonicity, Dedup, Pilot-Tunable Thresholds - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Harden fog-risk evaluation internals by bundling C4 + C5 + C6 from `CEILING-FOG-CORRECTIONS.md`: improve trend classification logic, remove duplicate visibility-series parsing paths, and make fog-heuristic thresholds pilot-tunable via integration configuration. This phase is code-side hardening only and must not introduce new end-user workflow steps.

</domain>

<decisions>
## Implementation Decisions

### Trend Monotonicity (C4)
- **D-01:** Replace first-vs-last delta trend logic with monotonic direction analysis over full series.
- **D-02:** Treat visibility as primary signal; use temperature/dew spread only as tiebreaker when visibility direction is neutral.
- **D-03:** Keep non-monotonic series classification as `stable` to avoid false improving/worsening labels from noisy windows.

### Visibility Dedup Refactor (C6)
- **D-04:** Introduce one shared visibility series helper in `analyzer.py` and reuse it from both `_fog_risk()` and `analyze_window()`.
- **D-05:** Keep refactor behavior-preserving for risk level and GO/NO-GO output; only remove duplicated parsing paths.

### Pilot-Tunable Fog Thresholds (C5)
- **D-06:** Surface currently hardcoded fog thresholds to config entry data and validation flow (global integration-level values first; no per-site overrides in this phase).
- **D-07:** Provide conservative defaults matching current production behavior to avoid surprise behavior shifts on upgrade.
- **D-08:** Clamp tunable threshold ranges in config flow to safe operational bounds and reject invalid values.

### Rollout / Surface Area
- **D-09:** No new Lovelace card controls or user-facing onboarding steps in this phase; existing card displays continue to consume backend-calculated fog status.
- **D-10:** Add targeted tests for trend monotonicity edge cases, dedup helper parity, and threshold override behavior.

### Claude's Discretion
- Exact naming of new fog-threshold constants and helper functions.
- Whether tunable values are grouped in existing thresholds step vs a dedicated fog subsection in config-flow schema.
- Exact numeric guardrail ranges, as long as defaults preserve current behavior and ranges remain operationally safe.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backlog / Scope Source
- `.planning/ROADMAP.md` — phase `09` backlog goal and task list.
- `.planning/CEILING-FOG-CORRECTIONS.md` — C4/C5/C6 correction intent and acceptance expectations.

### Existing Fog/Threshold Runtime
- `custom_components/flynow/analyzer.py` — current fog heuristic, trend logic, and duplicated visibility parsing.
- `custom_components/flynow/coordinator.py` — threshold payload assembly passed into analyzer.
- `custom_components/flynow/config_flow.py` — threshold validation and config-entry schema surface.

### Existing Dedup Pattern Reference
- `custom_components/flynow/notifications.py` — existing dedup/cooldown mechanism pattern (for consistency in dedup state handling strategy).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_clean_numeric`, `_safe_min`, `_max_or_none` in `analyzer.py` already provide shared numeric sanitation patterns suitable for new visibility-series helper extraction.
- Config validation helpers in `config_flow.py` (`_in_range`, threshold checks list) can be extended for fog-specific tunables without introducing a new flow step.

### Established Patterns
- Coordinator builds a `thresholds` dict from config entry values and passes it to `analyze_window()`, which is the correct injection point for tunable fog thresholds.
- Notifications already use dedup cooldown state in-memory (`_notification_dedup`) and provide a local pattern for deterministic dedup behavior checks.

### Integration Points
- New fog threshold config keys must be added consistently across `const.py`, `config_flow.py`, and coordinator threshold projection.
- Analyzer refactor must preserve existing `conditions["fog_risk"]` contract shape consumed by card and sensor paths.

</code_context>

<specifics>
## Specific Ideas

- Keep C4/C6 hardening and C5 tunability in one phase to avoid multiple migrations touching the same analyzer/config boundary.
- Preserve today’s operational defaults exactly, then allow pilot adjustment by config values instead of hardcoded literals.
- Prioritize deterministic tests for noisy/non-monotonic sequences and flat-visibility with spread drift.

</specifics>

<deferred>
## Deferred Ideas

- Per-launch-site fog-threshold overrides driven by terrain flags (future enhancement).
- Promotion of fog risk from informational to blocking GO/NO-GO signal (out of scope for this hardening pass).

</deferred>

---

*Phase: 09-fog-risk-hardening-trend-monotonicity-dedup-pilot-tunable-thresholds*
*Context gathered: 2026-04-28*
