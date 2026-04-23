---
phase: 02-notifications-card
plan: 02
subsystem: ui
tags: [home-assistant, lovelace, lit, typescript]
requires:
  - phase: 02-notifications-card
    provides: GO-transition notifications and freshness metadata from plan 02-01
provides:
  - Two-window-first Lovelace card for today evening and tomorrow morning
  - Threshold comparison rows with value/threshold and PASS/FAIL markers
  - Reactive stale-cache rendering for temporary unavailable entity state
affects: [phase-03-flight-logging]
tech-stack:
  added: [lit, typescript, esbuild]
  patterns: [entity-driven Lit rendering, source-contract tests, stale-cache fallback]
key-files:
  created: [lovelace/flynow-card/package.json, lovelace/flynow-card/src/types.ts, lovelace/flynow-card/src/flynow-card.ts, lovelace/flynow-card/src/index.ts, tests/test_card_contract.py]
  modified: [lovelace/flynow-card/src/flynow-card.ts, tests/test_card_contract.py]
key-decisions:
  - "Render exactly two summary tiles first (today evening and tomorrow morning) to enforce D-05 hierarchy."
  - "Handle unavailable/unknown states by reusing cached attributes plus explicit stale badge, without polling loops."
patterns-established:
  - "Use repository contract tests to assert required card text/structure markers."
  - "Use a `hass` setter and Lit reactivity rather than manual timers for UI updates."
requirements-completed: [CARD-01, CARD-02, CARD-03]
duration: 39min
completed: 2026-04-23
---

# Phase 2 Plan 2: Lovelace Card Summary

**Built a Lit-based FlyNow Lovelace card that always shows today-evening and tomorrow-morning GO/NO-GO first, includes threshold comparisons, and keeps last known values with stale labeling during temporary sensor gaps.**

## Performance

- **Duration:** 39 min
- **Started:** 2026-04-23T00:00:00Z
- **Completed:** 2026-04-23T00:39:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Scaffolded a buildable `lovelace/flynow-card` package with strict TypeScript, Lit dependency setup, and card registration entrypoint.
- Implemented fixed two-window-first rendering, condition threshold rows, and launch timing line from `binary_sensor.flynow_status` attributes.
- Added reactive stale-cache behavior that preserves last known values and displays a stale badge for `unavailable`/`unknown` entity states.

## Task Commits

1. **Task 1: Scaffold Lovelace card package and typed entity contract** - `4fec2da` (feat)
2. **Task 2 (RED): Implement two-window-first rendering and threshold comparison rows** - `f865d70` (test)
3. **Task 2 (GREEN): Implement two-window-first rendering and threshold comparison rows** - `54e9262` (feat)
4. **Task 3 (RED): Implement reactive updates and stale-data badge behavior** - `99380d0` (test)
5. **Task 3 (GREEN): Implement reactive updates and stale-data badge behavior** - `c8046f1` (feat)

## Files Created/Modified

- `lovelace/flynow-card/package.json` - card package scripts and dependencies.
- `lovelace/flynow-card/tsconfig.json` - strict TypeScript settings for card source.
- `lovelace/flynow-card/src/types.ts` - typed FlyNow entity attribute contract.
- `lovelace/flynow-card/src/index.ts` - custom card registration for `custom:flynow-card`.
- `lovelace/flynow-card/src/flynow-card.ts` - main card rendering logic and stale-cache behavior.
- `tests/test_card_contract.py` - contract tests covering required card UX markers.

## Decisions Made

- Keep rendering source tied directly to the HA entity attributes from plan 02-01 instead of creating a separate frontend data model.
- Use source-level contract tests in Python for deterministic requirement markers (window labels, threshold tags, launch/stale strings).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- PowerShell in this environment does not support `&&`; verification commands were executed with explicit `if ($LASTEXITCODE -ne 0)` guards.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 backend notifications and frontend card are both implemented and verified.
- Flight logging phase can now consume the same sensor/card contract without UI blockers.

## Self-Check: PASSED

---
*Phase: 02-notifications-card*
*Completed: 2026-04-23*
