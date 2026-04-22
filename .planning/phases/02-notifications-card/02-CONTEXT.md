# Phase 2: Notifications & Card - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers outbound GO notifications and the first Lovelace card UI. When a window changes to GO, crew and pilot must be alerted through configured channels (HA push, calendar event, messaging) with deduplication so the same window is not spammed. In parallel, the card must present today's evening and tomorrow's morning status with condition thresholds and launch window timing from the existing integration sensor data.

</domain>

<decisions>
## Implementation Decisions

### Alert Channel Policy
- **D-01:** Notification fan-out runs in parallel and independently across channels. A failure in one channel does not block the others.
- **D-02:** Messaging path for v1 is WhatsApp-first. Signal support is deferred to a future phase/extension.

### Deduplication Rules
- **D-03:** Dedup identity is `window_key + launch_start` (for example `tomorrow_evening@18:30`).
- **D-04:** The 1-hour cooldown starts at first successful send attempt (first channel that actually delivers).

### Card Information Design
- **D-05:** Card top section uses a two-window summary: today's evening and tomorrow's morning GO/NO-GO tiles first.
- **D-06:** Condition rows show numeric value plus threshold and pass/fail indicator (for example `3.8 / 4.0 m/s` with a status chip/icon).

### Card Update Behavior
- **D-07:** Card updates reactively from Home Assistant entity state changes with near-real-time UX target (~5 seconds).
- **D-08:** On temporary data unavailability, card keeps last known values and displays a clear stale-data badge.

### Claude's Discretion
- Final visual styling details for the card (spacing, icon style, typography) as long as the two-window-first information hierarchy is preserved.
- Internal retry/backoff implementation for failed channels under the independent fan-out model.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase + Requirements
- `.planning/ROADMAP.md` — Phase 2 goal, requirement IDs `NOTIF-01..04` and `CARD-01..03`, plus success criteria.
- `.planning/REQUIREMENTS.md` — detailed definitions for all notification and card requirements.

### Project Constraints
- `.planning/PROJECT.md` — core value, GO-only alert expectation, and platform constraints.
- `CLAUDE.md` — stack conventions for HA integration and Lovelace card implementation.

### Prior Phase Decisions
- `.planning/phases/01-core-integration/01-CONTEXT.md` — existing `binary_sensor.flynow_status` attribute shape and phase boundary carry-forward decisions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `custom_components/flynow/sensor.py` — existing `FlyNowStatusSensor` already exposes per-window attributes and active window fields used by card and alert logic.
- `custom_components/flynow/coordinator.py` — single coordinator source of truth for window projections and analyzed conditions.
- `custom_components/flynow/const.py` — window key constants and integration defaults for consistent key usage.

### Established Patterns
- Single authoritative binary sensor pattern already in place (`flynow_status`); Phase 2 should consume rather than duplicate decision computation.
- Async coordinator-driven update flow is established for data refresh and should remain the trigger foundation for notifications.

### Integration Points
- Notification trigger logic should connect to state transitions from coordinator/sensor outputs (NO-GO -> GO).
- Lovelace card should subscribe to HA entity state and render directly from sensor attributes for both windows and metric breakdown.

</code_context>

<specifics>
## Specific Ideas

- Messaging summary should include GO/NO-GO decision, launch window, and compact condition snapshot aligned with card metric names.
- Threshold comparison visibility is a UX requirement, not optional decoration.

</specifics>

<deferred>
## Deferred Ideas

- Signal-first or dual WhatsApp/Signal runtime selection in v1.
- Alternative card-first layouts (single active window only, full multiday grid first).
- Card polling/manual-refresh modes (reactive entity updates selected for v1).

</deferred>

---

*Phase: 02-notifications-card*
*Context gathered: 2026-04-22*
