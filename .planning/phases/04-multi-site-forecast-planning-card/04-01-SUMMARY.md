---
phase: 04-multi-site-forecast-planning-card
plan: 01
subsystem: ui
tags: [home-assistant, open-meteo, lovelace, multi-site]
requires:
  - phase: 02-notifications-card
    provides: selected-window sensor payload and card contract baseline
provides:
  - static three-site launch catalog with deterministic default selection
  - coordinator multi-site forecast projection with selected-site compatibility
  - comparison-first three-site Lovelace planning UI
affects: [coordinator, binary_sensor, lovelace-card]
tech-stack:
  added: []
  patterns: [fixed-site catalog, selected-site projection, comparison-first card rendering]
key-files:
  created: []
  modified:
    - custom_components/flynow/const.py
    - custom_components/flynow/coordinator.py
    - custom_components/flynow/sensor.py
    - lovelace/flynow-card/src/flynow-card.ts
    - lovelace/flynow-card/src/types.ts
    - tests/test_coordinator.py
    - tests/test_sensor.py
    - tests/test_card_contract.py
key-decisions:
  - "Locked site catalog to lzmada/katarinka/nitra-luka from launch-sites reference and kept lzmada as deterministic default."
  - "Preserved binary_sensor.flynow_status semantics by projecting selected site to existing top-level attributes."
  - "Kept Open-Meteo as the only source and reused existing analyzer/windows logic per site."
patterns-established:
  - "Coordinator payload now includes selected_site_id, sites, and sites_summary while preserving active_window/windows."
  - "Card keeps comparison visible at top and detail section switchable by site selection."
requirements-completed: [SITE-01, SITE-02, SITE-03, SITE-04]
duration: 30min
completed: 2026-04-23
---

# Phase 4 Plan 01: Multi-site forecast planning card Summary

**Three-site Open-Meteo planning now ships as a comparison-first card while retaining legacy `binary_sensor.flynow_status` automation behavior through selected-site projection.**

## Performance

- **Duration:** 30 min
- **Started:** 2026-04-23T14:26:00Z
- **Completed:** 2026-04-23T14:56:00Z
- **Tasks:** 3/3
- **Files modified:** 8

## Accomplishments

- Added fixed site catalog for Maly Madaras, Katarinka, and Nitra luka with deterministic default selected site `lzmada`.
- Refactored coordinator update cycle to fetch/analyze Open-Meteo forecasts for each site and emit `sites`, `sites_summary`, and `selected_site_id`.
- Preserved legacy sensor keys and `is_on` semantics while extending state attributes for multi-site card consumption.
- Reworked Lovelace card into a comparison-first three-site layout with persistent top summary and manual detail switching.

## Task Commits

1. **Task 1: Add locked multi-site catalog and coordinator per-site projection (RED)** - `243f5b3` (test)
2. **Task 1: Add locked multi-site catalog and coordinator per-site projection (GREEN)** - `862c191` (feat)
3. **Task 2: Preserve legacy binary sensor behavior while exposing multi-site summary (RED)** - `d54b27c` (test)
4. **Task 2: Preserve legacy binary sensor behavior while exposing multi-site summary (GREEN)** - `bdfb187` (feat)
5. **Task 3: Implement comparison-first multi-site planning card contract (RED)** - `b2b6e3a` (test)
6. **Task 3: Implement comparison-first multi-site planning card contract (GREEN)** - `dd19be8` (feat)
7. **Auto-fix commit** - `6572be3` (fix)

## Files Created/Modified

- `custom_components/flynow/const.py` - Added static three-site catalog and selected-site constants.
- `custom_components/flynow/coordinator.py` - Added per-site projection and selected-site backward-compatible view.
- `custom_components/flynow/sensor.py` - Added `selected_site_id`, `sites_summary`, and `sites` attributes while keeping existing keys.
- `lovelace/flynow-card/src/flynow-card.ts` - Implemented top comparison tiles and switchable selected-site detail section.
- `lovelace/flynow-card/src/types.ts` - Extended card-side attribute typing for multi-site payload.
- `tests/test_coordinator.py` - Added multi-site payload contract tests.
- `tests/test_sensor.py` - Added multi-site summary projection assertions.
- `tests/test_card_contract.py` - Added fixed three-site comparison contract assertions.

## Decisions Made

- Fixed catalog order and labels to launch-site decision order: Madaras, Katarinka, Nitra.
- Kept detail rendering resilient with fallback to legacy top-level attributes if site detail payload is missing.
- Did not introduce any non-Open-Meteo dependencies; all per-site analysis uses existing helpers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched test invocation from `pytest` to `python -m pytest`**
- **Found during:** Task 1 RED
- **Issue:** `pytest` binary unavailable on PATH in execution shell.
- **Fix:** Used module invocation for all Python test runs.
- **Verification:** Full test verification suite passed with module invocation.
- **Committed in:** task commits (command-level adjustment only)

**2. [Rule 1 - Bug] Removed stale imports after coordinator refactor**
- **Found during:** Final verification
- **Issue:** `ruff` failed with unused `CONF_LATITUDE`/`CONF_LONGITUDE` imports.
- **Fix:** Removed stale imports from coordinator module.
- **Files modified:** `custom_components/flynow/coordinator.py`
- **Verification:** `python -m ruff check custom_components/flynow tests` passed.
- **Committed in:** `6572be3`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both deviations were required for a passing, clean implementation; no scope expansion.

## Issues Encountered

None remaining after automatic fixes.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Multi-site forecast payload and card contract are in place for downstream notification/site-targeting work.
- Existing automations on `binary_sensor.flynow_status` remain compatible via selected-site projection.

## Self-Check: PASSED

- Confirmed summary file exists.
- Confirmed all task commit hashes resolve in git history.
