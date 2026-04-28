# Codebase Structure

**Analysis Date:** 2026-04-28

## Directory Layout

```text
FlyNow/
├── custom_components/flynow/        # Home Assistant integration backend
├── lovelace/flynow-card/            # Custom Lovelace card (TypeScript + Lit)
├── tests/                           # Python test suite for integration and card contracts
├── .planning/                       # GSD planning artifacts and generated codebase docs
├── .cursor/rules/                   # Workspace-level Cursor rules
├── .claude/                         # Local skills/tooling metadata
├── CLAUDE.md                        # Project operating guide and constraints
├── .gitignore                       # Ignore policy (includes real secrets file)
└── secrets.yaml.example             # Example config template for local setup
```

## Directory Purposes

**`custom_components/flynow`:**
- Purpose: Runtime integration loaded by Home Assistant.
- Contains: config flow, coordinator/orchestration, analyzer, API client, entity projection, service handlers, translation files.
- Key files: `custom_components/flynow/__init__.py`, `custom_components/flynow/coordinator.py`, `custom_components/flynow/config_flow.py`, `custom_components/flynow/flight_log.py`, `custom_components/flynow/services.yaml`.

**`lovelace/flynow-card`:**
- Purpose: Frontend dashboard card rendering operational status and flight-log UX.
- Contains: TypeScript source, type contracts, esbuild script, package metadata.
- Key files: `lovelace/flynow-card/src/flynow-card.ts`, `lovelace/flynow-card/src/types.ts`, `lovelace/flynow-card/src/flight-log-types.ts`, `lovelace/flynow-card/scripts/build.mjs`.

**`tests`:**
- Purpose: Validate backend behavior and protect frontend contract expectations.
- Contains: pytest files for coordinator, notifications, windows, analyzer, config flow, flight log, and card text-level contract checks.
- Key files: `tests/test_coordinator.py`, `tests/test_notifications.py`, `tests/test_flight_log.py`, `tests/test_card_contract.py`.

**`.planning`:**
- Purpose: Project/milestone/phase tracking and generated mapping docs consumed by GSD workflows.
- Contains: roadmaps, phase artifacts, and `.planning/codebase/` mapping outputs.
- Key files: `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`.

## Key File Locations

**Entry Points:**
- `custom_components/flynow/__init__.py`: integration startup, migration, coordinator boot, service registration.
- `custom_components/flynow/binary_sensor.py`: HA platform hook that instantiates runtime sensor entity.
- `lovelace/flynow-card/src/index.ts`: frontend component registration (`flynow-card` custom element).

**Configuration:**
- `custom_components/flynow/manifest.json`: HA integration metadata and platform type.
- `custom_components/flynow/config_flow.py`: setup flow and input validation.
- `custom_components/flynow/strings.json`: English config-flow labels/errors.
- `custom_components/flynow/translations/sk.json`: Slovak config-flow localization.
- `lovelace/flynow-card/tsconfig.json`: frontend type-check compiler settings.
- `lovelace/flynow-card/package.json`: card build dependencies and script.

**Core Logic:**
- `custom_components/flynow/coordinator.py`: periodic forecast aggregation and notification trigger.
- `custom_components/flynow/open_meteo.py`: external weather API client.
- `custom_components/flynow/windows.py`: window timeline generation.
- `custom_components/flynow/analyzer.py`: threshold/fog decision engine.
- `custom_components/flynow/notifications.py`: notification dedup and fanout.
- `custom_components/flynow/flight_log.py`: service schemas and atomic flight history persistence.
- `custom_components/flynow/sensor.py`: binary sensor state/attribute projection.

**Testing:**
- `tests/test_config_flow.py`: config and notification-step validation.
- `tests/test_sensor.py`: projected entity state/attribute shape.
- `tests/test_coordinator.py`: multi-site and notification behavior.
- `tests/test_notifications.py`: transition dedup and partial-failure behavior.
- `tests/test_flight_log.py`: schema and persistence guarantees.
- `tests/test_card_contract.py`: string/contract presence in card implementation.

## Naming Conventions

**Files:**
- Backend Python modules use snake_case (example: `custom_components/flynow/flight_log.py`).
- Frontend source uses kebab-case for component file and lower-case descriptors for types (example: `lovelace/flynow-card/src/flynow-card.ts`).
- Tests follow `test_*.py` naming in `tests/`.

**Directories:**
- HA integration package path follows domain name under `custom_components/`.
- Card package is isolated under `lovelace/flynow-card/`.
- Planning artifacts are centralized under `.planning/` and phase-numbered subdirectories.

## Ownership of Responsibilities

**Operational Decision Ownership:**
- Launch feasibility decisions are owned by backend coordinator + analyzer in `custom_components/flynow/coordinator.py` and `custom_components/flynow/analyzer.py`.

**UI Rendering Ownership:**
- Presentation and interaction state are owned by the card in `lovelace/flynow-card/src/flynow-card.ts`.

**Persistence Ownership:**
- Flight history persistence and schema normalization are owned by `custom_components/flynow/flight_log.py`.

**Contract Boundary Ownership:**
- Shared runtime contract is effectively owned by sensor attributes in `custom_components/flynow/sensor.py`.
- Type expectations are mirrored in `lovelace/flynow-card/src/types.ts` and `lovelace/flynow-card/src/flight-log-types.ts`.

## Build and Deploy Entry Points

**Frontend Build:**
- Run `npm run build` in `lovelace/flynow-card/` (`lovelace/flynow-card/package.json`).
- Type-check runs via `tsc --noEmit`; bundle output is `lovelace/flynow-card/dist/flynow-card.js` (`lovelace/flynow-card/scripts/build.mjs`).

**Integration Runtime Deployment Unit:**
- Deploy the package directory `custom_components/flynow/` to Home Assistant custom components path.
- Service metadata is included via `custom_components/flynow/services.yaml`.

**Card Runtime Deployment Unit:**
- Deploy `lovelace/flynow-card/dist/` to HA static path for `/local/flynow-card/flynow-card.js`.

## Where to Add New Code

**New Backend Feature:**
- Primary code: `custom_components/flynow/` (choose module by responsibility: coordinator, analyzer, services, API client).
- Tests: `tests/test_<feature>.py`.

**New Frontend Feature:**
- Implementation: `lovelace/flynow-card/src/flynow-card.ts` for UI behavior.
- Shared/frontend types: `lovelace/flynow-card/src/types.ts` or `lovelace/flynow-card/src/flight-log-types.ts`.

**New External Integration:**
- API client/helper: `custom_components/flynow/<integration>.py`.
- Orchestration hook: `custom_components/flynow/coordinator.py`.
- Contract exposure: `custom_components/flynow/sensor.py`.

**New Service Endpoint:**
- Service handler + schema: `custom_components/flynow/flight_log.py` (or new module if domain diverges).
- Service schema docs: `custom_components/flynow/services.yaml`.
- Card caller (if user-facing): `lovelace/flynow-card/src/flynow-card.ts`.

## Special Directories

**`.planning/codebase`:**
- Purpose: Generated codebase maps used by planning/execution workflows.
- Generated: Yes.
- Committed: Yes.

**`.pytest_cache` and `.ruff_cache`:**
- Purpose: Local test/lint cache artifacts.
- Generated: Yes.
- Committed: No.

## Structural Risks & Ambiguities

- **Boundary naming mismatch:** runtime binary sensor logic lives in `custom_components/flynow/sensor.py` while platform wiring lives in `custom_components/flynow/binary_sensor.py`.
- **No dedicated backend package layering:** all domain/service/integration modules sit flat in one directory, which can increase coupling as modules grow (`custom_components/flynow/*`).
- **Card contract is partially text-level tested:** `tests/test_card_contract.py` validates source text markers, not rendered DOM/runtime integration, so regressions can pass if strings still exist.
- **Dual path style artifacts:** repository contains both slash-style and backslash-style listings for same paths in tooling output; onboarding docs should always use canonical repo paths with `/`.

---

*Structure analysis: 2026-04-28*
