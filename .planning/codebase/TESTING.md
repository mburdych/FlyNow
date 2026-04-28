# Testing Patterns

**Analysis Date:** 2026-04-28

## Test Framework

**Runner:**
- `pytest` (used by all tests under `tests/`; import + marker usage visible in multiple files such as `tests/test_coordinator.py` and `tests/test_flight_log.py`).
- Config: Not detected (`pytest.ini`, `pyproject.toml`, `tox.ini` absent at repo root).

**Assertion Library:**
- Native `assert` statements with `pytest.raises` patterns in `tests/test_flight_log.py` and `tests/test_config_flow.py`.

**Run Commands (evidence-based):**
```bash
python -m pytest tests/test_coordinator.py tests/test_sensor.py -q
python -m pytest tests/test_flight_log.py -x
npm --prefix lovelace/flynow-card run build && pytest tests/test_card_contract.py -x
```
- These commands are documented in `.planning/phases/*` summaries and plans, indicating current operational practice.

## Test File Organization

**Location:**
- Centralized under `tests/` with per-module test files (`tests/test_analyzer.py`, `tests/test_notifications.py`, `tests/test_windows.py`).

**Naming:**
- `test_<module_or_feature>.py` pattern across the suite.

**Structure:**
```
tests/
  test_analyzer.py
  test_config_flow.py
  test_coordinator.py
  test_notifications.py
  test_open_meteo.py
  test_sensor.py
  test_windows.py
  test_flight_log.py
  test_card_contract.py
```

## Test Structure

**Established patterns:**
- Small scenario-focused tests with explicit in-test fixtures/doubles (for example `_Hass`, `_Services`) in `tests/test_coordinator.py`, `tests/test_notifications.py`, and `tests/test_flight_log.py`.
- Async behavior tests use `@pytest.mark.anyio` and await direct coroutine calls.
- Monkeypatching is used to isolate network and window-generation dependencies in coordinator tests (`tests/test_coordinator.py`).
- Contract-style frontend checks inspect source text from `lovelace/flynow-card/src/flynow-card.ts` in `tests/test_card_contract.py`.

## Mocking

**Framework:**
- Built-in pytest tools (`monkeypatch`) and handwritten fake classes.

**What is mocked now:**
- Weather fetch calls, window builders, and analyzer logic (`tests/test_coordinator.py`).
- HA service call surfaces through fake `hass.services.async_call` objects (`tests/test_notifications.py`).
- Filesystem behavior is exercised via `tmp_path` with real writes in `tests/test_flight_log.py`.

**What is not mocked (by design):**
- Core transformation logic in `custom_components/flynow/analyzer.py` and `custom_components/flynow/windows.py` is tested directly.

## Coverage Snapshot (inferred from repository)

**Strongly covered areas:**
- Decision analysis and fog metadata (`tests/test_analyzer.py`).
- Notification fanout/dedup transitions (`tests/test_notifications.py`).
- Coordinator multi-site projection and selection behavior (`tests/test_coordinator.py`).
- Flight-log schema validation and persistence recovery (`tests/test_flight_log.py`).
- Sensor projection attributes (`tests/test_sensor.py`).

**Thin/partial coverage areas:**
- Open-Meteo client behavior has only one trivial exception-type test in `tests/test_open_meteo.py`; request parameter contract, HTTP error paths, and payload parsing are not thoroughly asserted.
- Card behavior is validated through static string checks in `tests/test_card_contract.py` rather than runtime rendering/event tests.
- Config flow coverage focuses notification step; earlier flow steps and single-entry guard behavior are not deeply exercised (`tests/test_config_flow.py`).

**Coverage gate:**
- No enforced numeric coverage threshold detected (no coverage config file found).

## Established vs Aspirational Testing Discipline

**Established in repository:**
- Behavior-driven pytest tests with lightweight doubles.
- Async tests exercised without full Home Assistant test harness.
- Manual command-based verification captured in `.planning/phases/*` artifacts.

**Aspirational/documented-only:**
- `.planning/research/STACK.md` and related planning docs call for stricter `ruff`/`mypy` and broader HA testing standards; these are not fully enforced via root config or CI in current repo state.

## Highest-Priority Gaps (ranked)

1. **Missing automated quality gate (High):**
   - No CI workflow detected in `.github/workflows/`.
   - Impact: regressions can merge without running tests/lint/type checks.
   - Recommendation: add CI job to run `pytest` and card `npm run build`.

2. **Open-Meteo client under-tested (High):**
   - `tests/test_open_meteo.py` only checks exception stringification.
   - Impact: API contract changes or HTTP failure paths can break coordinator silently.
   - Recommendation: add async tests for non-200 responses, `aiohttp.ClientError`, missing `hourly`/`daily` keys, and request parameter composition in `custom_components/flynow/open_meteo.py`.

3. **Frontend runtime behavior untested (High):**
   - `tests/test_card_contract.py` relies on source-text assertions, not rendered behavior.
   - Impact: logic bugs in interaction flow (language switching, stale cache fallback, form submit states) may pass tests.
   - Recommendation: add TypeScript unit/component tests (for example Vitest + web-test-runner) for `lovelace/flynow-card/src/flynow-card.ts`.

4. **Config flow branch coverage incomplete (Medium):**
   - `tests/test_config_flow.py` emphasizes constants and notification validation only.
   - Impact: regressions in `async_step_user`, `async_step_flight_parameters`, and threshold bounds may go unnoticed.
   - Recommendation: add full multi-step flow tests including boundary values and `single_site_only` gating.

5. **No declared coverage baseline (Medium):**
   - Coverage tooling/config not detected.
   - Impact: test suite growth does not guarantee critical-path depth.
   - Recommendation: add `pytest-cov` command and a minimum threshold for `custom_components/flynow/`.

---

*Testing analysis: 2026-04-28*
