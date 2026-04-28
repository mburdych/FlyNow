# Codebase Concerns

**Analysis Date:** 2026-04-28

## Tech Debt

**[High] Analyzer-contract drift in notification payload:**
- Issue: Notification message reads precipitation from `conditions["precip_prob_pct"]`, but analyzer writes `conditions["precip_prob"]`, so precipitation in GO alerts silently falls back to `0%`.
- Files: `custom_components/flynow/notifications.py`, `custom_components/flynow/analyzer.py`, `tests/test_notifications.py`
- Impact: Crew receives misleading precipitation data in operational alerts, degrading trust in GO messages and increasing weather-risk interpretation errors.
- Fix approach: Standardize condition keys via shared typed constants/dataclass; fail-fast on missing keys in `_build_message`; add a regression test that asserts non-zero precipitation renders correctly in notification text.

**[Medium] Multi-site hardcoding conflicts with setup UX and defaults:**
- Issue: Config flow still captures `latitude`/`longitude` but runtime ignores them and always evaluates `SITE_CATALOG`; integration behavior no longer matches user-entered location semantics.
- Files: `custom_components/flynow/config_flow.py`, `custom_components/flynow/coordinator.py`, `custom_components/flynow/const.py`
- Impact: Operators can believe they configured a custom site while backend actually evaluates fixed sites, creating configuration ambiguity and support burden.
- Fix approach: Either remove unused location fields from config flow or restore them as a first-class custom site; add migration and UI copy that explicitly explains selected-site behavior.

## Known Bugs

**[High] Single-site fetch failure collapses entire forecast update:**
- Symptoms: Any `OpenMeteoError` during the site loop aborts the whole coordinator refresh and prevents all site status updates.
- Files: `custom_components/flynow/coordinator.py`, `custom_components/flynow/open_meteo.py`
- Trigger: One transient API/network error for any site during `_async_update_data`.
- Workaround: None in-code; only subsequent refresh attempts may recover.

## Security Considerations

**[Medium] Flight history stores potentially sensitive free-text in plaintext JSON without retention/deletion policy:**
- Risk: `notes` can contain personal or operational details and is stored unencrypted in `/config/flynow_flights.json` indefinitely.
- Files: `custom_components/flynow/flight_log.py`, `custom_components/flynow/services.yaml`, `lovelace/flynow-card/src/flynow-card.ts`
- Current mitigation: Schema limits note length and validates structure.
- Recommendations: Add optional redaction mode (or disable notes), retention window/purge service, and user-facing privacy notice in config flow/docs.

## Performance Bottlenecks

**[Medium] Sequential external API calls increase update latency and stale data risk:**
- Problem: Site forecasts are fetched serially inside one loop with per-request timeout up to 20s.
- Files: `custom_components/flynow/coordinator.py`, `custom_components/flynow/open_meteo.py`
- Cause: No bounded parallelism (`asyncio.gather` with concurrency limit) and no per-site partial result strategy.
- Improvement path: Fetch sites concurrently with capped parallelism and per-site error isolation; preserve successful site data when one site fails.

## Fragile Areas

**[Medium] Behavioral contract between backend condition schema and card rendering is informal:**
- Files: `custom_components/flynow/analyzer.py`, `custom_components/flynow/sensor.py`, `lovelace/flynow-card/src/flynow-card.ts`, `tests/test_card_contract.py`
- Why fragile: Frontend supports multiple fallback keys (`surface_wind` vs `surface_wind_ms`, etc.), indicating schema drift already occurred and can regress silently.
- Safe modification: Introduce explicit typed response contract shared between Python entity attributes and TS card types; version attributes and enforce compatibility checks.
- Test coverage: Card contract tests assert static strings/source markers, not runtime JSON compatibility under realistic state payloads.

## Scaling Limits

**[Medium] Flight log growth is unbounded on disk:**
- Current capacity: Response caps at 200 rows, but persisted JSON keeps all historical records.
- Limit: File size and write/replace time grow indefinitely, increasing risk of slow writes and corruption recovery events.
- Scaling path: Enforce max persisted records or archive rotation in `FlightLogStore._async_write`, with optional export before prune.

## Dependencies at Risk

**[Low] Integration metadata points to placeholder repository links:**
- Risk: `documentation` and `issue_tracker` reference `github.com/example/flynow`, reducing operator supportability and release traceability.
- Impact: Users cannot reach valid docs/issues from HA UI.
- Migration plan: Update `manifest.json` with real project URLs and verify in release checklist.

## Missing Critical Features

**[High] No confidence/uncertainty guardrails for GO decisioning:**
- Problem: Decision output is strict boolean without API freshness confidence, per-metric missing-data quality, or recommendation confidence score.
- Blocks: Safe operational use during degraded data quality and transparent risk communication.

## Test Coverage Gaps

**[High] External client and end-to-end service integration are under-tested:**
- What's not tested: Open-Meteo payload edge cases, HTTP error-body parsing behavior, and real HA integration flow for coordinator + services + card state.
- Files: `tests/test_open_meteo.py`, `tests/test_coordinator.py`, `tests/test_card_contract.py`, `custom_components/flynow/open_meteo.py`
- Risk: Regressions in payload shape or service interaction can ship undetected.
- Priority: High.

## Prioritized Mitigation Sequence

1. **Reliability + correctness first (High):** Fix precipitation key mismatch and isolate per-site fetch failures in `custom_components/flynow/notifications.py` and `custom_components/flynow/coordinator.py`.
2. **Contract hardening (High):** Define shared schema/constants for condition payloads consumed by `custom_components/flynow/sensor.py` and `lovelace/flynow-card/src/flynow-card.ts`.
3. **Testing uplift (High):** Add Open-Meteo client tests and state-shape integration tests around coordinator/card contracts in `tests/`.
4. **Privacy + scaling controls (Medium):** Add retention/purge support and optional note redaction in `custom_components/flynow/flight_log.py` and exposed services.
5. **Ops/documentation cleanup (Low/Medium):** Correct deployment/resource docs and manifest links in `lovelace/flynow-card/README.md` and `custom_components/flynow/manifest.json`.

---

*Concerns audit: 2026-04-28*
