# Phase 4: Multi-site forecast planning card - Research

**Researched:** 2026-04-23
**Domain:** Home Assistant multi-site projection + Lovelace planning comparison
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01..D-03:** Three fixed sites only from `.planning/reference/launch-sites.md`; Open-Meteo-only forecast by `lat,lon`.
- **D-04..D-06:** Coordinator must hold per-site results, keep legacy single sensor semantics, and expose `sites_summary`.
- **D-07..D-09:** Card is comparison-first across all sites with fixed display order and optional detail switch.

### Deferred Ideas (OUT OF SCOPE)
- Unlimited user-managed site CRUD.
- New weather source integrations (METAR/SHMÚ/other APIs).
- Multi-model ensemble decision display.
- Per-site outbound alert orchestration changes.

## Codebase-Grounded Guidance

### Reuse Existing Domain Logic (No New Decision Engine)
- `custom_components/flynow/open_meteo.py` already fetches normalized payloads and should be reused per site.
- `custom_components/flynow/windows.py` builds launch windows and labels; call it unchanged for each site.
- `custom_components/flynow/analyzer.py` performs strict AND / worst-case checks; keep this as single source of truth.

### Extend State Shape, Not Core Behavior
- `custom_components/flynow/coordinator.py` should evolve from single-site output to:
  - `sites`: map of site_id -> current site analysis payload
  - `selected_site_id`: active site for legacy projection
  - `sites_summary`: compact card-facing list/map
- `custom_components/flynow/sensor.py` should preserve existing top-level attributes for selected site while adding multi-site summary keys.

### Card Integration
- Existing `tests/test_card_contract.py` pattern verifies card contract by source assertions; extend these checks for multi-site summary blocks.
- Card implementation should consume `sites_summary` first, then render selected-site detail pane from existing condition fields.

## Minimal File Targets

1. `custom_components/flynow/const.py`
   - Add typed/static site definitions based on `.planning/reference/launch-sites.md`.
2. `custom_components/flynow/coordinator.py`
   - Iterate through sites, fetch+analyze per site, build unified multi-site payload.
3. `custom_components/flynow/sensor.py`
   - Keep backward compatibility while surfacing `sites_summary` and `selected_site_id`.
4. `lovelace/flynow-card/src/flynow-card.ts`
   - Render comparison-first multi-site planning section and selected-site details.
5. Tests:
   - `tests/test_coordinator.py`
   - `tests/test_sensor.py`
   - `tests/test_card_contract.py`
   - (optional) `tests/test_multi_site.py` if logic isolation improves readability.

## Risks and Mitigations

- **Risk:** Breaking existing automations that rely on `binary_sensor.flynow_status`.
  - **Mitigation:** Preserve current top-level selected-site attributes and `is_on` semantics (D-05), add tests for old keys.
- **Risk:** Card contract drift between backend keys and frontend usage.
  - **Mitigation:** Introduce explicit `sites_summary` contract and lock with tests on both backend projection and card source.
- **Risk:** Increased API calls (3x site fetches).
  - **Mitigation:** Keep update interval bounds, fetch per refresh cycle, and avoid extra frontend polling.

## Implementation Recommendation

Use one execution plan with three concrete tasks: (1) static site contract and coordinator multi-site payload, (2) sensor backward-compatible projection + summary exposure, (3) card comparison UI + tests. This stays small, executable, and aligned with existing phase doc style.

## Sources

- `.planning/reference/launch-sites.md`
- `custom_components/flynow/open_meteo.py`
- `custom_components/flynow/windows.py`
- `custom_components/flynow/analyzer.py`
- `custom_components/flynow/coordinator.py`
- `custom_components/flynow/sensor.py`
- `tests/test_coordinator.py`
- `tests/test_sensor.py`
- `tests/test_card_contract.py`
