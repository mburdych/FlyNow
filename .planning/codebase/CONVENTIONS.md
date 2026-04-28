# Coding Conventions

**Analysis Date:** 2026-04-28

## Naming Patterns

**Established in codebase:**
- **Files:** Python modules use snake_case (for example `custom_components/flynow/config_flow.py`, `custom_components/flynow/flight_log.py`); frontend source uses kebab-case (`lovelace/flynow-card/src/flynow-card.ts`) and simple noun files (`lovelace/flynow-card/src/types.ts`).
- **Functions:** Python uses snake_case helpers and async handlers (`custom_components/flynow/notifications.py`, `custom_components/flynow/coordinator.py`); TypeScript methods use camelCase (`lovelace/flynow-card/src/flynow-card.ts`).
- **Constants:** Shared Python constants use SCREAMING_SNAKE_CASE in `custom_components/flynow/const.py`; frontend static keys also use SCREAMING_SNAKE_CASE in `lovelace/flynow-card/src/flynow-card.ts`.
- **Types:** TypeScript interfaces and type aliases use PascalCase (`FlyNowStatusAttributes`, `HomeAssistantLike`) in `lovelace/flynow-card/src/types.ts`.

**Aspirational/documented-only:**
- `.planning/research/STACK.md` recommends additional conventions such as strict mypy discipline and broader HA fixture patterns that are only partially implemented in tracked source.

## Code Style

**Established in codebase:**
- **Python:** Type hints are common (`dict[str, Any]`, `tuple[str, ...]`) across `custom_components/flynow/*.py`; module-level docstrings are consistently used.
- **TypeScript:** Strict compiler settings are enabled (`"strict": true`, `"noEmit": true`) in `lovelace/flynow-card/tsconfig.json`.
- **Formatting cues:** Multi-line wrapping and explicit intermediate variables are favored in complex logic (`custom_components/flynow/coordinator.py`, `custom_components/flynow/flight_log.py`).

**Aspirational/documented-only:**
- `ruff`/`mypy --strict` are repeatedly required in planning docs (`.planning/research/STACK.md`), but no active root lint/type config (`pyproject.toml`, `ruff.toml`, `mypy.ini`) is present in repository root.

## Import Organization

**Established in codebase:**
1. Stdlib imports first.
2. Third-party imports next (`aiohttp`, `voluptuous`).
3. Local relative imports last.
- This pattern is consistent in `custom_components/flynow/coordinator.py`, `custom_components/flynow/flight_log.py`, and `custom_components/flynow/config_flow.py`.

**Path Aliases:**
- Not used in TypeScript; relative imports are used from `lovelace/flynow-card/src/flynow-card.ts` to `./types` and `./flight-log-types`.

## Typing and Async Practices

**Established in codebase:**
- Integration logic is async-first with `async def` lifecycle/service functions in `custom_components/flynow/__init__.py` and `custom_components/flynow/flight_log.py`.
- Network and service fanout use async primitives (`aiohttp.ClientSession`, `asyncio.gather`) in `custom_components/flynow/coordinator.py` and `custom_components/flynow/notifications.py`.
- Python typing is pragmatic: `Any` is used frequently at HA boundaries (`hass`, `entry`, service payloads), while internal structures use stronger types in `custom_components/flynow/const.py`.
- TypeScript uses typed service responses and domain types (`LogFlightResponse`, `FlyNowStatusAttributes`) in `lovelace/flynow-card/src/flynow-card.ts`.

**Aspirational/documented-only:**
- Full strict typing for Python is not enforced by checked-in tooling; current code relies on convention rather than repository-level type gates.

## Error Handling

**Established in codebase:**
- Explicit domain exceptions wrap external failures (`OpenMeteoError` in `custom_components/flynow/open_meteo.py`).
- Coordinator converts integration failures to HA-friendly update failures in `custom_components/flynow/coordinator.py`.
- Flight-log persistence handles malformed JSON with backup and recovery in `custom_components/flynow/flight_log.py`.
- Frontend falls back to stale cached entity attributes for resilience in `lovelace/flynow-card/src/flynow-card.ts`.

## Frontend Patterns

**Established in codebase:**
- Single LitElement component as integration UI surface in `lovelace/flynow-card/src/flynow-card.ts`.
- Translation dictionary is local and strongly keyed via `TranslationKey` in `lovelace/flynow-card/src/types.ts`.
- UI state is class-private and event-driven (`handleInput`, `handleFlightSubmit`, `toggleSettingsPanel`) with minimal external dependencies.
- Card reads one HA entity (`binary_sensor.flynow_status`) and derives all sections from attributes.

**Aspirational/documented-only:**
- No frontend unit/component test runner is configured for TypeScript runtime behavior; contract checks exist only from Python-side source-string assertions.

## Testing and Commit Discipline (Inferred)

**Established in codebase:**
- Tests are required during development flow: repository keeps focused pytest suites in `tests/` and phase summaries routinely reference command-level verification in `.planning/phases/*`.
- Async tests use `pytest.mark.anyio` with lightweight doubles rather than full HA fixtures in `tests/test_coordinator.py`, `tests/test_notifications.py`, and `tests/test_flight_log.py`.

**Aspirational/documented-only:**
- CI-enforced discipline is not detected (`.github/workflows/*` absent), so test/lint execution appears manual and dependent on local habits.
- Planning artifacts often mention stricter quality bars than currently machine-enforced in-repo.

## Practical Rules For New Code

- Follow Python import ordering and naming established in `custom_components/flynow/*.py`.
- Keep HA entry points and service handlers async; do not introduce blocking I/O on event-loop paths.
- Add or extend constants in `custom_components/flynow/const.py` instead of hardcoding string keys.
- In frontend changes, extend `lovelace/flynow-card/src/types.ts` first, then consume types in `flynow-card.ts`.
- Add targeted pytest coverage in `tests/` for any behavior change; prefer behavior tests over implementation-string assertions.

---

*Convention analysis: 2026-04-28*
