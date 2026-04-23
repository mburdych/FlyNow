---
phase: 02-notifications-card
plan: 01
subsystem: api
tags: [home-assistant, notifications, dedup, coordinator]
requires:
  - phase: 01-core-integration
    provides: binary sensor window projections and coordinator refresh flow
provides:
  - GO transition notification fan-out for push, calendar, and WhatsApp
  - One-hour dedup ledger keyed by window identity and launch start
  - Coordinator freshness metadata for Lovelace card consumers
affects: [phase-02-plan-02-card, phase-03-flight-logging]
tech-stack:
  added: [ruff]
  patterns: [transition-gated dispatch, independent channel fanout, entity-id domain validation]
key-files:
  created: [custom_components/flynow/notifications.py]
  modified: [custom_components/flynow/config_flow.py, custom_components/flynow/coordinator.py, custom_components/flynow/sensor.py, tests/test_config_flow.py, tests/test_notifications.py, tests/test_coordinator.py, tests/test_sensor.py]
key-decisions:
  - "Treat notifier/calendar entity domain validation as a phase-2 correctness requirement."
  - "Dispatch notifications from coordinator snapshots to preserve NO-GO to GO transition semantics."
patterns-established:
  - "Use asyncio.gather(return_exceptions=True) for non-blocking channel fan-out."
  - "Expose freshness metadata on sensor attributes for frontend stale-state UX."
requirements-completed: [NOTIF-01, NOTIF-02, NOTIF-03, NOTIF-04]
duration: 35min
completed: 2026-04-22
---

# Phase 2 Plan 1: Notification Pipeline Summary

**Coordinator-driven NO-GO to GO alerts now fan out independently across push, calendar, and WhatsApp with one-hour window dedup and card-consumable freshness metadata.**

## Performance

- **Duration:** 35 min
- **Started:** 2026-04-22T12:10:00Z
- **Completed:** 2026-04-22T12:45:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Enforced notification target contracts in config flow, including required `notify.*` and `calendar.*` entity IDs.
- Added dedicated notification orchestration module with transition detection, dedup keys (`window_key@launch_start`), and one-hour cooldown.
- Wired coordinator refresh lifecycle to dispatch transition events and publish freshness metadata for downstream card rendering.

## Task Commits

1. **Task 1: Define notification config and dedup contracts** - `652bc5e` (feat)
2. **Task 2: Implement transition-gated fan-out and dedup ledger** - `3d6807d` (feat)
3. **Task 3: Wire coordinator invocation and expose freshness metadata for card consumers** - `bd4f1e3` (feat)

## Files Created/Modified

- `custom_components/flynow/notifications.py` - transition detector, fan-out orchestration, and dedup cooldown handling.
- `custom_components/flynow/config_flow.py` - notification target validation and notifications step constraints.
- `custom_components/flynow/coordinator.py` - dispatch hook after refresh plus freshness and notification result payload.
- `custom_components/flynow/sensor.py` - freshness and notification metadata attributes for card consumers.
- `tests/test_config_flow.py` - config validation coverage for notification targets.
- `tests/test_notifications.py` - fan-out and dedup behavior coverage.
- `tests/test_coordinator.py` - coordinator transition dispatch integration test.
- `tests/test_sensor.py` - freshness attribute projection coverage.

## Decisions Made

- Validate notifier and calendar entities by expected domain during config flow to satisfy threat mitigation for target spoofing.
- Keep notification dispatch in coordinator state update path so transition semantics remain centralized and deterministic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added notifier/calendar domain validation**
- **Found during:** Task 1 (Define notification config and dedup contracts)
- **Issue:** Notification step accepted arbitrary non-empty entity IDs, which violated threat-model mitigation requirements.
- **Fix:** Added `notify.*` and `calendar.*` validation and test coverage.
- **Files modified:** `custom_components/flynow/config_flow.py`, `custom_components/flynow/strings.json`, `tests/test_config_flow.py`
- **Verification:** `python -m pytest tests/test_config_flow.py -k "notifier or calendar or notification" -x`
- **Committed in:** `652bc5e`

**2. [Rule 3 - Blocking] Installed missing ruff dependency for lint verification**
- **Found during:** Plan verification
- **Issue:** `python -m ruff` failed because `ruff` was not installed in the environment.
- **Fix:** Installed `ruff` via `python -m pip install ruff` before rerunning checks.
- **Files modified:** none
- **Verification:** `python -m ruff check custom_components/flynow tests`
- **Committed in:** not committed (environment-only tooling install)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 blocking)
**Impact on plan:** All deviations were required for secure target handling and successful verification execution.

## Issues Encountered

- `pytest` command alias was unavailable in PowerShell; used `python -m pytest` for all verification commands.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Backend notification pipeline and freshness metadata are ready for card wiring in plan `02-02`.
- No blockers remain for frontend implementation.

## Self-Check: PASSED

---
*Phase: 02-notifications-card*
*Completed: 2026-04-22*
