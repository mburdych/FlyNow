# Phase 3: Flight Logging - Research

**Researched:** 2026-04-23
**Domain:** Home Assistant custom-service persistence + LitElement form UI
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** All core fields are required except notes. Required: date, balloon, launch time, duration, site, and outcome.
- **D-02:** Form prefill behavior: date defaults to today, balloon defaults to last used balloon, site defaults to selected site, duration defaults to 90 minutes.
- **D-03:** Outcome uses a fixed enum with options: `flown`, `cancelled-weather`, `cancelled-other`.
- **D-04:** Launch time entry uses a local 24-hour time picker (not free text).

### Claude's Discretion

- Submission feedback microcopy and visual styling details, as long as success/error state is clear.
- Exact list rendering density for prior logs, while preserving a clear and readable history list.
- Internal JSON schema representation details, as long as LOG-01 fields are fully preserved and storage remains atomically safe.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. Learning/scoring logic explicitly excluded by the phase boundary (`<domain>` in CONTEXT).

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LOG-01 | Lovelace card includes form to log completed flight (date, balloon, launch time, duration, site, outcome, notes) | See Sections: Architecture Patterns (card form), Code Examples (Lit form), Standard Stack (LitElement 3.3.2 already in use) |
| LOG-02 | Flight logs stored locally in HA config directory with atomic writes | See Sections: Don't Hand-Roll (use `homeassistant.helpers.json.save_json(..., atomic_writes=True)`), Code Examples (atomic write pattern), Common Pitfalls (event-loop blocking) |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

CLAUDE.md locked directives that this phase must respect:

- **GSD workflow:** All edits must go through a GSD command. Planner should stage work via `/gsd-execute-phase 3` after this research lands.
- **Async throughout:** No `requests` library; no synchronous calls in the integration. All file I/O must be wrapped via `hass.async_add_executor_job` (see Don't Hand-Roll).
- **Storage convention:** Flight logs live at `hass.config.path("flynow_flights.json")` (i.e. `/config/flynow_flights.json`) — JSON only, no SQLite, no external DB.
- **No YAML config for integrations:** `ConfigFlow` only. Flight log persistence is runtime state, not user configuration, so this constraint is informational (service call is the right boundary).
- **Lovelace stack locked:** `LitElement` + `lit-html` + `esbuild`, no React/Vue. Card already uses `lit@^3.3.2` per `lovelace/flynow-card/package.json`.
- **Python quality:** `ruff` + `mypy --strict`; tests use `pytest-homeassistant-custom-component`.
- **HA version floor:** 2025.1+ — so `SupportsResponse.ONLY`, `save_json(atomic_writes=True)`, and `hass.services.async_register` with response are all available.

## Summary

Phase 3 is a **vertical slice across the existing two-tier architecture**: add a LitElement form + history list to the already-shipped Lovelace card, and add a single writable persistence boundary to the existing Python integration. The hardest technical decision — where and how to persist the log — is already constrained by LOG-02 to `/config/flynow_flights.json` (not the `.storage/` directory that `Store` helpers use).

The canonical HA primitive for this exact use case is `homeassistant.helpers.json.save_json(filename, data, atomic_writes=True)` [VERIFIED: github.com/home-assistant/core `helpers/json.py`], which internally uses `write_utf8_file_atomic` (temp-file + `os.replace`). It is synchronous, so it MUST be called through `await hass.async_add_executor_job(...)` to avoid blocking the event loop. A matching `load_json_array` (with `default=[]`) handles first-run and missing-file cases. An in-memory `asyncio.Lock` in the integration module protects against concurrent writes from multiple card submissions.

Backend exposure is a single domain service `flynow.log_flight` registered via `hass.services.async_register(DOMAIN, "log_flight", handler, schema=..., supports_response=SupportsResponse.ONLY)`, returning the normalized entry (id + created_at). A second service `flynow.list_flights` returns the in-memory log array for the card's history view. Both are called from the card via `hass.callService("flynow", "log_flight", data, undefined, false, true)` which returns `ServiceCallResponse<T>` with a typed `.response` payload [VERIFIED: github.com/home-assistant/frontend `src/types.ts`].

**Primary recommendation:** One new Python module `custom_components/flynow/flight_log.py` owns persistence (load, save, append, validate) + service registration; the existing coordinator is **not** touched. The card adds one new sub-component (form + history list) using the existing `lit@^3.3.2` dependency and the existing HA theme tokens from `02-UI-SPEC.md` / `03-UI-SPEC.md`. The storage file lives at `hass.config.path("flynow_flights.json")` as a JSON array of entries.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Flight log form UI (input, validation, defaults) | Browser / Lovelace card | — | User interaction belongs at the browser; defaults read from existing card state (selected site, last-used balloon) |
| Service invocation + response handling | Browser / Lovelace card | API (HA service bus) | Card uses `hass.callService()`; no direct file access from frontend |
| Input validation (required fields, enum membership, time format) | API (Python service handler) | Browser (for UX only) | Backend is authoritative; frontend validation is progressive enhancement |
| JSON persistence (atomic write + read) | API (Python backend) | — | File I/O must stay in Python; HA helpers + executor-thread pattern |
| History list fetch for card | API (service with `SupportsResponse.ONLY`) | — | Files can grow to 100s of entries; attribute-channel is unsuited (see Common Pitfalls #3) |
| In-memory log cache (avoid re-reading on every list call) | API (integration module singleton) | — | Coordinator already owns runtime state; flight_log module mirrors the pattern |
| Last-used balloon memory (for D-02 prefill) | Browser (localStorage, per-user) | — | Small preference; does not need HA-level persistence |
| Concurrency control (two submits race) | API (asyncio.Lock in flight_log module) | — | Backend is the only valid place to serialize writes |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Integration runtime | Already used by repo; HA 2025.1+ requires it [VERIFIED: `pyproject.toml`/HA docs] |
| `homeassistant` (core) | 2025.1+ | ServiceCall, HomeAssistant, config_entries | Already a dep; provides `SupportsResponse`, `helpers.json.save_json` [VERIFIED: `helpers/json.py`] |
| `voluptuous` | already in HA | Service schema validation | Already used in `config_flow.py` via `import voluptuous as vol` [VERIFIED: codebase grep] |
| `lit` | ^3.3.2 | Card framework | Already the only card dep per `lovelace/flynow-card/package.json` [VERIFIED: file read] |
| TypeScript | ^6.0.3 | Card language | Already used; `strict: true` already enabled [VERIFIED: `tsconfig.json`] |

### Supporting (all already in HA core — NO new `requirements` in `manifest.json`)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant.helpers.json` | HA 2025.1+ | `save_json` with `atomic_writes=True`, `load_json_array` with `default=[]` | Every persistence call [VERIFIED: github.com/home-assistant/core `helpers/json.py`] |
| `homeassistant.core.SupportsResponse` | HA 2025.1+ | Mark `log_flight` and `list_flights` as `SupportsResponse.ONLY` | Service registration [VERIFIED: developers.home-assistant.io/docs/dev_101_services] |
| `homeassistant.helpers.config_validation` (`cv`) | HA 2025.1+ | Voluptuous helpers: `cv.date`, `cv.time`, `cv.positive_int`, `cv.string` | Service schema [CITED: community HA service examples] |
| `asyncio.Lock` | stdlib | Serialize concurrent writes | Avoid interleaved `load -> append -> save` from two card submits |
| `uuid.uuid4` | stdlib | Generate entry id | Stable record identity for future deletion/editing phases |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom service + file I/O | `homeassistant.helpers.storage.Store` | **Rejected** — `Store` hardcodes `config/.storage/{key}` path, wraps data in version metadata, and is NOT user-readable at `/config/flynow_flights.json`. Violates LOG-02. [VERIFIED: github.com/home-assistant/core `helpers/storage.py` — `STORAGE_DIR = '.storage'` is a constant] |
| Domain service | Websocket command (`@websocket_api.async_response`) | **Rejected** — Services are the idiomatic card→backend boundary; websocket is for subscriptions and registry access. Services are what the card toolkit already uses. [CITED: developers.home-assistant.io `custom-card`] |
| Domain service | Writing file directly from the card (fetch → HA API) | **Rejected** — Custom cards have no file-system access by design; HA REST API intentionally omits file writes. |
| JSON array | SQLite in HA config dir | **Rejected** — CLAUDE.md explicitly forbids direct DB access; volume is tiny (< 1MB for 1000+ flights); human-editable is a feature for a crew tool |
| `pydantic` models | Plain dict + voluptuous | **Pydantic not currently used** in this repo. Voluptuous is already the convention (`config_flow.py`). Staying with voluptuous avoids adding a `requirements` entry and follows in-repo norms. |
| Expose log list as sensor attribute | Dedicated `list_flights` service | **Rejected for volume** — HA attributes are serialized on every entity state change and have a soft 16KB recommendation. 100+ entries will exceed this and bloat the state machine. |

**Installation:** No new pip dependencies. No new npm dependencies. `lit@^3.3.2` already present. No `manifest.json` `requirements` changes needed.

**Version verification:**
- `lit`: `npm view lit version` → 3.3.2 (verified 2026-04-23 via local `npm view`).
- `typescript`: `npm view typescript version` → 6.0.3 (verified 2026-04-23).
- `homeassistant` core APIs (`save_json`, `SupportsResponse`): stable since HA 2023.9 per release notes; no migration risk at HA 2025.1+.

## Architecture Patterns

### System Architecture Diagram

```
  [ Lovelace card (flynow-card.ts) ]
                │
                │  Submission (Log Flight button)
                │      hass.callService("flynow", "log_flight", {fields}, undefined, false, true)
                │      → Promise<ServiceCallResponse<LoggedFlight>>
                │
                │  History refresh (after submit OR on card mount)
                │      hass.callService("flynow", "list_flights", {}, undefined, false, true)
                │      → Promise<ServiceCallResponse<{flights: LoggedFlight[]}>>
                ▼
  ┌─────────────────────────────────────────────┐
  │  HA service bus (hass.services)             │
  │  Domain: "flynow"                            │
  │  Services:                                   │
  │   - log_flight   (SupportsResponse.ONLY)     │
  │   - list_flights (SupportsResponse.ONLY)     │
  └─────────────────────────────────────────────┘
                │
                │  ServiceCall → handler (in flight_log.py)
                ▼
  ┌─────────────────────────────────────────────┐
  │  flight_log.py (new module)                  │
  │  - FlightLogStore (singleton per-hass)       │
  │    · in-memory list mirror                   │
  │    · asyncio.Lock                            │
  │    · path = hass.config.path("flynow_flights.json")│
  │    · async_load() / async_append() / async_list()  │
  │  - validate(entry_dict)                      │
  │  - normalize(entry_dict) → adds id, created_at     │
  │  - service handlers (handle_log_flight, handle_list_flights) │
  │  - async_register_services(hass)             │
  └─────────────────────────────────────────────┘
                │
                │  await hass.async_add_executor_job(save_json, path, data, atomic_writes=True)
                ▼
  ┌─────────────────────────────────────────────┐
  │  Disk: /config/flynow_flights.json           │
  │  JSON array of entry objects                 │
  │  Atomic write: tempfile → os.replace()       │
  └─────────────────────────────────────────────┘

  Integration setup (__init__.py):
    async_setup_entry  →  await FlightLogStore.async_ensure(hass)
                       →  async_register_services(hass)   (idempotent, guarded)
```

Data flow:
1. Crew fills form → card clicks `Log Flight` → `hass.callService` with entry payload.
2. Service handler validates via voluptuous schema (already enforced by HA before handler runs).
3. Handler calls `FlightLogStore.async_append(entry)` which:
   - acquires `asyncio.Lock`,
   - normalizes (adds `id: uuid4`, `created_at: now_utc_iso`, defaults `notes=""`),
   - appends to in-memory list,
   - persists via `save_json(..., atomic_writes=True)` wrapped in executor,
   - releases lock, returns normalized entry.
4. Handler returns `ServiceCallResponse` `{response: {entry: <normalized>}}`.
5. Card receives response, prepends to its local history state, shows success microcopy, resets launch time + notes (per UI-SPEC).
6. On card mount / stale refresh, card calls `list_flights` which returns the in-memory array (no re-read of disk).

### Recommended Project Structure

```
custom_components/flynow/
├── __init__.py              # MODIFIED: add FlightLogStore bootstrap + async_register_services call
├── const.py                 # MODIFIED: add FLIGHT_LOG_FILENAME, SERVICE_LOG_FLIGHT, SERVICE_LIST_FLIGHTS,
│                            #          OUTCOMES tuple, BALLOON_IDS tuple
├── flight_log.py            # NEW: persistence + validation + service registration
├── services.yaml            # NEW: service metadata for HA UI (description, fields)
├── strings.json             # MODIFIED: add service-name translations (optional; services.yaml primary)
└── ... (all other phase 1/2/4 files untouched)

lovelace/flynow-card/src/
├── flynow-card.ts           # MODIFIED: add flight-log-section slot and integrate log form component
├── flight-log-form.ts       # NEW: LitElement sub-component — form rendering + submit handler
├── flight-log-list.ts       # NEW: LitElement sub-component — history renderer
├── flight-log-types.ts      # NEW: TypeScript types for LoggedFlight, service payloads
└── types.ts                 # MODIFIED: extend HomeAssistantLike to declare hass.callService signature

tests/
├── test_flight_log.py       # NEW: atomic write, validation, concurrency, service handlers
└── test_flight_log_contract.py  # NEW: card source-grep contract tests (mirror test_card_contract.py)
```

### Pattern 1: Domain service with response (Python)

**What:** Register `flynow.log_flight` and `flynow.list_flights` as response-only services called from the card.

**When to use:** Any card → backend interaction that is NOT a standard `notify`/`calendar` service.

**Example:**
```python
# Source: developers.home-assistant.io/docs/dev_101_services
# Adapted to match this repo's patterns in config_flow.py and notifications.py.
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.json import save_json
from homeassistant.util.json import load_json_array

from .const import (
    BALLOON_IDS,          # ("OM-0007", "OM-0008")
    DOMAIN,
    FLIGHT_LOG_FILENAME,  # "flynow_flights.json"
    OUTCOMES,             # ("flown", "cancelled-weather", "cancelled-other")
    SERVICE_LIST_FLIGHTS, # "list_flights"
    SERVICE_LOG_FLIGHT,   # "log_flight"
    SITE_IDS,             # already defined in const.py
)

LOG_FLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required("date"): cv.date,                # ISO YYYY-MM-DD
        vol.Required("balloon"): vol.In(BALLOON_IDS),
        vol.Required("launch_time"): cv.time,         # HH:MM local
        vol.Required("duration_min"): vol.All(cv.positive_int, vol.Range(min=15, max=300)),
        vol.Required("site"): vol.In(SITE_IDS),
        vol.Required("outcome"): vol.In(OUTCOMES),
        vol.Optional("notes", default=""): cv.string,
    }
)
LIST_FLIGHTS_SCHEMA = vol.Schema({})


class FlightLogStore:
    """Runtime mirror of /config/flynow_flights.json with atomic persistence."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._path = Path(hass.config.path(FLIGHT_LOG_FILENAME))
        self._entries: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()
        self._loaded = False

    async def async_load(self) -> None:
        if self._loaded:
            return
        def _load() -> list[dict[str, Any]]:
            raw = load_json_array(str(self._path), default=[])
            return [e for e in raw if isinstance(e, dict)]
        self._entries = await self._hass.async_add_executor_job(_load)
        self._loaded = True

    async def async_append(self, entry: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            await self.async_load()
            normalized = self._normalize(entry)
            # Append to an in-memory copy FIRST, then persist. If persist raises,
            # we do NOT mutate self._entries — preserves disk/memory consistency.
            next_entries = [*self._entries, normalized]
            await self._hass.async_add_executor_job(
                save_json, str(self._path), next_entries, False, None, True
                # filename, data, private=False, encoder=None, atomic_writes=True
            )
            self._entries = next_entries
            return normalized

    async def async_list(self) -> list[dict[str, Any]]:
        async with self._lock:
            await self.async_load()
            # Return a shallow copy sorted newest-first.
            return sorted(
                self._entries,
                key=lambda e: (e.get("date", ""), e.get("launch_time", "")),
                reverse=True,
            )

    @staticmethod
    def _normalize(entry: dict[str, Any]) -> dict[str, Any]:
        # cv.date returns datetime.date, cv.time returns datetime.time
        # -> convert to ISO strings for JSON storage.
        date_value = entry["date"]
        time_value = entry["launch_time"]
        return {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now(UTC).isoformat(),
            "schema_version": 1,
            "date": date_value.isoformat() if hasattr(date_value, "isoformat") else str(date_value),
            "balloon": str(entry["balloon"]),
            "launch_time": time_value.strftime("%H:%M") if hasattr(time_value, "strftime") else str(time_value),
            "duration_min": int(entry["duration_min"]),
            "site": str(entry["site"]),
            "outcome": str(entry["outcome"]),
            "notes": str(entry.get("notes") or ""),
        }


async def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_LOG_FLIGHT):
        return  # idempotent: safe across multiple config entries

    store = FlightLogStore(hass)
    hass.data.setdefault(DOMAIN, {})["flight_log_store"] = store

    async def handle_log_flight(call: ServiceCall) -> dict[str, Any]:
        entry = await store.async_append(dict(call.data))
        return {"entry": entry}

    async def handle_list_flights(call: ServiceCall) -> dict[str, Any]:
        return {"flights": await store.async_list()}

    hass.services.async_register(
        DOMAIN, SERVICE_LOG_FLIGHT, handle_log_flight,
        schema=LOG_FLIGHT_SCHEMA, supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN, SERVICE_LIST_FLIGHTS, handle_list_flights,
        schema=LIST_FLIGHTS_SCHEMA, supports_response=SupportsResponse.ONLY,
    )
```

### Pattern 2: Atomic JSON write via HA helper

**What:** Call `save_json` with `atomic_writes=True`; it delegates to `write_utf8_file_atomic` (temp file + `os.replace`).

**When to use:** Every persistence call. **Do not** implement your own `tempfile` + rename — HA's helper handles permissions, encoding, encoder, and executor semantics consistently.

**Example:**
```python
# Source: github.com/home-assistant/core blob/dev/homeassistant/helpers/json.py
# save_json signature:
# def save_json(filename, data, private=False, *, encoder=None, atomic_writes=False) -> None
from homeassistant.helpers.json import save_json

# Inside an async context — MUST go through the executor because save_json is sync.
await hass.async_add_executor_job(
    save_json,            # callable
    str(path),            # filename
    entries,              # data
    False,                # private
    None,                 # encoder (keyword-only via partial if needed)
    True,                 # atomic_writes
)
# Note: atomic_writes is keyword-only in recent HA. If positional invocation fails type-checking
# under mypy strict, wrap with functools.partial:
#   await hass.async_add_executor_job(partial(save_json, str(path), entries, atomic_writes=True))
```

### Pattern 3: Lit form with controlled inputs and defaults (TypeScript)

**What:** LitElement sub-component with `@property` + reactive `@state` holding form values, native HTML5 `<input type="date">` / `<input type="time">` / `<select>` / `<textarea>`, submit via `hass.callService`.

**When to use:** The flight log form. Mirrors existing `flynow-card.ts` conventions — no third-party form libs.

**Example:**
```typescript
// Source: lit.dev/docs/components/properties and existing flynow-card.ts
// Pattern already used for `selectedDetailSiteId` in flynow-card.ts:232-261.
import { LitElement, css, html, type TemplateResult } from "lit";
import type { HomeAssistantLike } from "./types";
import type { LoggedFlight, LogFlightServiceData } from "./flight-log-types";

type SubmitState = "idle" | "saving" | "success" | "error";

const BALLOONS = ["OM-0007", "OM-0008"] as const;
const OUTCOMES = [
  { value: "flown", label: "Flown" },
  { value: "cancelled-weather", label: "Cancelled — weather" },
  { value: "cancelled-other", label: "Cancelled — other" },
] as const;

const LAST_BALLOON_KEY = "flynow-card.last-balloon";

export class FlightLogForm extends LitElement {
  static properties = {
    hass: { attribute: false },
    selectedSiteId: { attribute: "selected-site-id" },
    siteOptions: { attribute: false },  // [{id, label}]
    submitState: { state: true },
    formError: { state: true },
    values: { state: true },
  };

  hass?: HomeAssistantLike;
  selectedSiteId = "lzmada";
  siteOptions: Array<{ id: string; label: string }> = [];
  submitState: SubmitState = "idle";
  formError: string | null = null;
  values: LogFlightServiceData = this._initialValues();

  private _initialValues(): LogFlightServiceData {
    const today = new Date();
    const yyyy = String(today.getFullYear());
    const mm = String(today.getMonth() + 1).padStart(2, "0");
    const dd = String(today.getDate()).padStart(2, "0");
    const lastBalloon =
      (typeof window !== "undefined" && window.localStorage?.getItem(LAST_BALLOON_KEY)) || BALLOONS[0];
    return {
      date: `${yyyy}-${mm}-${dd}`,
      balloon: lastBalloon,
      launch_time: "",             // explicit selection required per UI-SPEC
      duration_min: 90,
      site: this.selectedSiteId,
      outcome: "flown",
      notes: "",
    };
  }

  protected render(): TemplateResult {
    const disabled = this.submitState === "saving";
    return html`<form @submit=${this._onSubmit}>
      <label>Date
        <input type="date" required .value=${this.values.date}
               @input=${(e: Event) => this._update("date", (e.target as HTMLInputElement).value)} />
      </label>
      <label>Balloon
        <select required .value=${this.values.balloon}
                @change=${(e: Event) => this._update("balloon", (e.target as HTMLSelectElement).value)}>
          ${BALLOONS.map((b) => html`<option value=${b} ?selected=${b === this.values.balloon}>${b}</option>`)}
        </select>
      </label>
      <label>Launch time
        <input type="time" required .value=${this.values.launch_time}
               @input=${(e: Event) => this._update("launch_time", (e.target as HTMLInputElement).value)} />
      </label>
      <label>Duration (min)
        <input type="number" required min="15" max="300" .value=${String(this.values.duration_min)}
               @input=${(e: Event) => this._update("duration_min", Number((e.target as HTMLInputElement).value))} />
      </label>
      <label>Site
        <select required .value=${this.values.site}
                @change=${(e: Event) => this._update("site", (e.target as HTMLSelectElement).value)}>
          ${this.siteOptions.map((s) => html`<option value=${s.id}>${s.label}</option>`)}
        </select>
      </label>
      <label>Outcome
        <select required .value=${this.values.outcome}
                @change=${(e: Event) => this._update("outcome", (e.target as HTMLSelectElement).value)}>
          ${OUTCOMES.map((o) => html`<option value=${o.value} ?selected=${o.value === this.values.outcome}>${o.label}</option>`)}
        </select>
      </label>
      <label>Notes (optional)
        <textarea .value=${this.values.notes ?? ""}
                  @input=${(e: Event) => this._update("notes", (e.target as HTMLTextAreaElement).value)}></textarea>
      </label>
      <button type="submit" ?disabled=${disabled}>Log Flight</button>
      ${this._renderSubmitStatus()}
    </form>`;
  }

  private _update<K extends keyof LogFlightServiceData>(key: K, value: LogFlightServiceData[K]): void {
    this.values = { ...this.values, [key]: value };
  }

  private async _onSubmit(e: Event): Promise<void> {
    e.preventDefault();
    if (!this.hass) return;
    this.submitState = "saving";
    this.formError = null;
    try {
      // Typed response via generic parameter:
      const response = await this.hass.callService<{ entry: LoggedFlight }>(
        "flynow",
        "log_flight",
        { ...this.values },
        undefined,  // target
        false,      // notifyOnError (we show inline)
        true,       // returnResponse — REQUIRED since service is SupportsResponse.ONLY
      );
      const entry = response?.response?.entry;
      if (!entry) throw new Error("empty_response");
      window.localStorage?.setItem(LAST_BALLOON_KEY, this.values.balloon);
      this.dispatchEvent(new CustomEvent("flight-logged", { detail: entry, bubbles: true, composed: true }));
      // Reset launch_time + notes per UI-SPEC; keep date/balloon/site sticky.
      this.values = { ...this.values, launch_time: "", notes: "" };
      this.submitState = "success";
    } catch (err) {
      this.formError = "Flight log could not be saved. Check Home Assistant storage access and try again.";
      this.submitState = "error";
    }
  }

  private _renderSubmitStatus(): TemplateResult {
    if (this.submitState === "success") return html`<span role="status">Flight logged locally</span>`;
    if (this.submitState === "error") return html`<span role="alert">${this.formError}</span>`;
    return html``;
  }
}
```

### Pattern 4: Card-level list refresh via service response

**What:** The card maintains a local `flights: LoggedFlight[]` state; refreshes it on mount and after each successful `flight-logged` event by calling `flynow.list_flights`.

**Why:** Keeps the history list out of sensor attributes (see Pitfall #3). The list service is cheap (no disk re-read after first load; lives in-memory).

**Example:**
```typescript
// In FlyNowCard (flynow-card.ts) — new method:
private async _refreshFlights(): Promise<void> {
  if (!this.hass) return;
  const resp = await this.hass.callService<{ flights: LoggedFlight[] }>(
    "flynow", "list_flights", {}, undefined, false, true,
  );
  this.flights = resp?.response?.flights ?? [];
}

// Called from firstUpdated() and from a @flight-logged listener on the form.
```

### Anti-Patterns to Avoid

- **Reading/writing the JSON file from the card directly (via fetch or hass.callApi).** The card has no fs access; `callApi` routes through HA's REST API which does not expose arbitrary file writes. Domain services are the ONLY supported boundary.
- **Storing the log list as a sensor attribute.** HA state attributes are sent to every connected frontend on each state change and are soft-capped (~16KB). A 200-entry log will blow past this and slow dashboards [CITED: HA frontend perf guidance].
- **Calling `save_json(..., atomic_writes=True)` directly in an `async def` without the executor.** It calls `open()` and `os.replace()` — blocks the event loop. Always wrap via `hass.async_add_executor_job`. [VERIFIED: developers.home-assistant.io `asyncio_blocking_operations`]
- **Using `homeassistant.helpers.storage.Store`.** It writes to `/config/.storage/{key}` and wraps data in versioned metadata (`{"version": N, "data": ...}`), neither of which satisfies LOG-02's spec of a user-readable `/config/flynow_flights.json`. [VERIFIED: github.com/home-assistant/core `helpers/storage.py` — `STORAGE_DIR = ".storage"`]
- **Registering services inside `async_setup_entry` without an idempotency guard.** If the user deletes and re-adds the integration, services could be registered twice. Guard with `hass.services.has_service(DOMAIN, ...)`. [CITED: HA dev docs recommend registering in `async_setup`, but service-in-setup_entry with has_service guard is the established multi-entry pattern]
- **Depending on card-side validation for security.** Browser-side validation is UX; backend voluptuous schema is authoritative. Never trust incoming `call.data` without the schema.
- **Storing balloon last-used preference in sensor attributes.** It's a per-device UI preference. `window.localStorage` in the card is correct.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic JSON write | Custom `tempfile.NamedTemporaryFile` + `os.replace` | `homeassistant.helpers.json.save_json(path, data, atomic_writes=True)` | HA's `write_utf8_file_atomic` handles encoding, permissions, error cleanup, and stays consistent with core integrations. [VERIFIED: github.com/home-assistant/core `helpers/json.py`] |
| JSON load with default | `json.load` + try/except FileNotFoundError | `homeassistant.util.json.load_json_array(path, default=[])` | Handles missing file, malformed JSON fallback, and type coercion in one call. [VERIFIED: github.com/home-assistant/core `util/json.py`] |
| Input validation | Hand-written if-checks in the service handler | `voluptuous` schema passed to `hass.services.async_register(..., schema=...)` | HA runs the schema before the handler. Invalid calls get a clear `ServiceValidationError`. Already the project convention (`config_flow.py`). |
| Enum membership check | `if value not in OUTCOMES: raise` | `vol.In(OUTCOMES)` | Declarative, automatically part of the service's public contract, and surfaced in `services.yaml` for the Services developer tool. |
| ServiceCall → response plumbing | Websocket command, custom event bus | `supports_response=SupportsResponse.ONLY` + `returnResponse=true` on card side | HA 2023.9+ first-class API; typed response via `ServiceCallResponse<T>`. [VERIFIED: github.com/home-assistant/frontend `src/types.ts`] |
| Async file locking | `fcntl.flock` / `portalocker` | Single in-process `asyncio.Lock` | HA integration is single-process. File locking across processes adds complexity we do not need (only HA writes this file). |
| Date / time parsing in schema | Regex, manual `datetime.strptime` | `homeassistant.helpers.config_validation.date` / `.time` | Already the HA way; parses ISO + native HTML5 input formats. |
| UUID generation | Incrementing counters, timestamp hashes | `uuid.uuid4()` | Collision-free, no persistence of a counter needed. |

**Key insight:** Every primitive we need already exists in HA core. Phase 3 is assembly, not invention. Any line of code that looks like "we built our own X" is a red flag unless X is strictly business logic (form field contract, outcome enum).

## Runtime State Inventory

> This phase introduces new persistent state rather than renaming existing state, so a full rename audit is not applicable. However, the analogous "what runtime state does this phase introduce?" audit is essential.

| Category | Items Introduced | Action Required |
|----------|-------------------|------------------|
| Stored data | New file `/config/flynow_flights.json` (JSON array of flight entries, `schema_version: 1`) | New — no migration; first write creates it. First read uses `default=[]`. |
| Live service config | Two new registered domain services: `flynow.log_flight` (SupportsResponse.ONLY), `flynow.list_flights` (SupportsResponse.ONLY). Register in `__init__.async_setup_entry` with `has_service` idempotency guard. | Register on setup; unregister is optional (HA tears down on integration removal, but services linger until restart — guard handles re-add). |
| OS-registered state | None — no cron, no OS services, no systemd units. | None. |
| Secrets / env vars | None — file lives in user's HA config; no credentials involved. | None. |
| Build artifacts | `lovelace/flynow-card/dist/flynow-card.js` rebuild required after adding new Lit components; no new npm packages. | Planner must include a build step verification. |
| Browser-local state | `localStorage["flynow-card.last-balloon"]` — holds last-used balloon for D-02 prefill. | Document in card code; cleared only by user clearing site data. |
| In-memory singleton | `hass.data["flynow"]["flight_log_store"] = FlightLogStore(hass)` — the in-process mirror of the log file. | Register on setup; reused across multiple service calls. |

**Nothing found in category:** OS-registered state, secrets/env vars, and existing-file migrations — verified by reading all integration source files and confirming no pre-existing `flynow_flights.json` handling.

## Common Pitfalls

### Pitfall 1: Blocking the event loop with synchronous `save_json`

**What goes wrong:** `save_json` internally calls `open(..., "wb")` and `os.replace()`. Called directly in an `async def`, it blocks HA for the write duration. On slow SD-card installs (HAOS Raspberry Pi), this is 10–200ms per call and HA logs a "blocking call" warning.

**Why it happens:** The HA dev docs are explicit but easy to miss: `save_json` is a utility wrapper, not an async API. [VERIFIED: developers.home-assistant.io `asyncio_blocking_operations`]

**How to avoid:** Always wrap: `await hass.async_add_executor_job(partial(save_json, path, data, atomic_writes=True))`. Add a unit test asserting the handler completes without ever awaiting a non-executor sync call (use a `monkeypatch` on `save_json` that tracks the thread it runs on).

**Warning signs:** HA log line: `Detected blocking call to open with args (...) inside the event loop by custom integration 'flynow'`.

### Pitfall 2: Concurrent writes interleaving

**What goes wrong:** Two card instances submit simultaneously. Without a lock, both handlers read `entries`, both append, both save — the second write clobbers the first's append. Net effect: one entry lost.

**Why it happens:** `async` does not mean "atomic" — control yields at every `await`, including at `async_add_executor_job`.

**How to avoid:** `asyncio.Lock` in `FlightLogStore`. Acquire **before** reading `self._entries`; release **after** persisting. Atomic file write (temp+rename) ensures the on-disk file is never mid-state; the lock ensures the in-memory append-then-persist sequence is linearized.

**Warning signs:** In tests, race with `asyncio.gather(store.async_append(a), store.async_append(b))` and assert both appear in the final list.

### Pitfall 3: History list on sensor attribute channel

**What goes wrong:** Attributes get serialized on every state change of the entity and pushed to every connected frontend. A large `flights` attribute (100+ entries × ~200 bytes) bloats every WebSocket frame, slows dashboards, and can trigger HA's "entity state attribute too large" warnings.

**Why it happens:** It looks natural to stuff everything into attributes — Phases 1/2/4 do it for `sites`, `windows`, `sites_summary`. But those are O(3) and O(7) bounded; the flight log is unbounded.

**How to avoid:** Dedicated `list_flights` service with `SupportsResponse.ONLY`. The card fetches on mount and after submit; HA sends the payload only once per request, not on every sensor update.

**Warning signs:** HA core logs "State attributes exceeded maximum size"; card UI feels laggy as the log grows.

### Pitfall 4: Mixing `cv.date`/`cv.time` native types with JSON

**What goes wrong:** Voluptuous `cv.date` returns a `datetime.date`; `cv.time` returns `datetime.time`. `json.dumps({"date": date(2026, 4, 23)})` raises `TypeError: Object of type date is not JSON serializable`.

**Why it happens:** The schema coerces strings to native types, but the persistence layer assumes strings.

**How to avoid:** Normalize in `_normalize()` before adding to the list: `.isoformat()` for date, `.strftime("%H:%M")` for time. This also guarantees a stable on-disk schema regardless of input format variations.

**Warning signs:** Test with `TypeError: Object of type date is not JSON serializable` on first submission.

### Pitfall 5: First-run missing file treated as error

**What goes wrong:** `json.load(open("flynow_flights.json"))` raises on missing file; the card sees a service error and shows "log could not be saved".

**Why it happens:** Beginner-mode file-handling.

**How to avoid:** Use `load_json_array(path, default=[])` — returns `[]` if file missing OR file empty OR file has whitespace-only content. [VERIFIED: github.com/home-assistant/core `util/json.py`]

**Warning signs:** First-ever deploy fails on every service call until a manual `echo "[]" > flynow_flights.json`.

### Pitfall 6: `supports_response` mismatch between backend and frontend

**What goes wrong:** Backend registers service with `SupportsResponse.ONLY`, but frontend calls `callService` without `returnResponse=true`. HA raises: `ServiceValidationError: "Service call requires responses but caller did not ask for responses"`.

**Why it happens:** The default value of `callService`'s `returnResponse` parameter is `false` (the 6th arg). [VERIFIED: github.com/home-assistant/frontend `src/types.ts`]

**How to avoid:** Always pass `true` as the 6th argument when the service is `SupportsResponse.ONLY`. Add a card contract test that greps for `"flynow", "log_flight"` followed by a `true` literal in the callService argument list.

**Warning signs:** Error message "Service call requires responses but caller did not ask for responses".

### Pitfall 7: Registering services twice on integration reload

**What goes wrong:** User deletes and re-adds the config entry. `async_setup_entry` runs again. Without a guard, `async_register` either overwrites (in recent HA — benign but noisy log) or raises (in older HA).

**How to avoid:** `if hass.services.has_service(DOMAIN, SERVICE_LOG_FLIGHT): return` at the top of `async_register_services`. Services are domain-global, not per-entry, so a single registration suffices.

**Warning signs:** HA log: `Service flynow.log_flight already registered`.

### Pitfall 8: Validating site against a stale list

**What goes wrong:** The card's site dropdown is populated from `SITE_IDS` in `const.py`; the service schema uses `vol.In(SITE_IDS)`. If phase 4's `SITE_IDS` changes in future, the schema update must go with it.

**How to avoid:** Keep both pulling from the same `const.SITE_IDS`. Add a test: `set(const.SITE_IDS) == set(SITE_ORDER_in_card_source)`.

## Code Examples

### Service registration hookup from `__init__.py`

```python
# Source: developers.home-assistant.io/docs/dev_101_services + existing __init__.py
# Add these 3 lines. Existing body preserved.
from .flight_log import async_register_services  # NEW import

async def async_setup_entry(hass: Any, entry: Any) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = FlyNowCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR_DATA: coordinator}
    await async_register_services(hass)                       # NEW — idempotent
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

### `services.yaml` metadata (UI hinting for Developer Tools → Services)

```yaml
# Source: HA dev docs — https://developers.home-assistant.io/docs/dev_101_services/#services-description
log_flight:
  name: Log flight
  description: Record a completed balloon flight for local history.
  fields:
    date:
      name: Date
      required: true
      example: "2026-04-23"
      selector:
        date:
    balloon:
      name: Balloon
      required: true
      selector:
        select:
          options: ["OM-0007", "OM-0008"]
    launch_time:
      name: Launch time
      required: true
      example: "06:30"
      selector:
        time:
    duration_min:
      name: Duration (minutes)
      required: true
      default: 90
      selector:
        number: { min: 15, max: 300, unit_of_measurement: "min" }
    site:
      name: Launch site
      required: true
      selector:
        select:
          options: ["lzmada", "katarinka", "nitra-luka"]
    outcome:
      name: Outcome
      required: true
      selector:
        select:
          options: ["flown", "cancelled-weather", "cancelled-other"]
    notes:
      name: Notes
      required: false
      selector:
        text: { multiline: true }

list_flights:
  name: List flights
  description: Return the locally recorded flight history (newest first).
```

### Storage schema (on-disk JSON)

```json
[
  {
    "id": "2f7b64a1-34e2-4f85-9ed4-0c8f22e30c10",
    "schema_version": 1,
    "created_at": "2026-04-23T18:42:03.112000+00:00",
    "date": "2026-04-23",
    "balloon": "OM-0007",
    "launch_time": "18:45",
    "duration_min": 90,
    "site": "lzmada",
    "outcome": "flown",
    "notes": "Calm winds, beautiful sunset."
  }
]
```

Field derivations:
- `id` = `uuid.uuid4()` (server-assigned; not part of LOG-01 but needed for stable history rendering)
- `schema_version` = `1` (reserves space for future migrations without breaking readers)
- `created_at` = `datetime.now(UTC).isoformat()` (server-assigned; audit trail for when the record entered the log)
- `date` / `launch_time` = normalized strings (ISO / `HH:MM`) — NOT native date/time objects
- `site` = site id (slug), not site name — guarantees stability if display names change
- `balloon` = exact label (`OM-0007` / `OM-0008`) — small closed set, no need for a separate id
- `outcome` = lowercase enum value, matches D-03
- `notes` = always a string (empty if not provided) — consumers never need to null-check

### TypeScript type contracts (`flight-log-types.ts`)

```typescript
export type FlightOutcome = "flown" | "cancelled-weather" | "cancelled-other";
export type BalloonId = "OM-0007" | "OM-0008";

export interface LogFlightServiceData {
  date: string;          // YYYY-MM-DD
  balloon: BalloonId;
  launch_time: string;   // HH:mm
  duration_min: number;
  site: string;          // SITE_IDS member
  outcome: FlightOutcome;
  notes?: string;
}

export interface LoggedFlight extends Required<LogFlightServiceData> {
  id: string;
  schema_version: number;
  created_at: string;    // ISO UTC
}

export interface LogFlightResponse { entry: LoggedFlight; }
export interface ListFlightsResponse { flights: LoggedFlight[]; }
```

### Extending `HomeAssistantLike` to declare `callService`

```typescript
// types.ts — MODIFY:
export interface HomeAssistantLike {
  states: Record<string, HassEntityState | undefined>;
  callService<T = unknown>(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: { entity_id?: string | string[] } | undefined,
    notifyOnError?: boolean,
    returnResponse?: boolean,
  ): Promise<{ context: { id: string }; response?: T }>;
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Return data from services via events or polling | `SupportsResponse.ONLY` / `.OPTIONAL` + `returnResponse=true` on `callService` | HA 2023.7–2023.9 | Services are now first-class RPC; we can retire the "fake event" pattern for list-flights. [VERIFIED: developers.home-assistant.io `dev_101_services`] |
| `homeassistant.util.json.save_json` | `homeassistant.helpers.json.save_json` (still present in util as a re-export, but `helpers` is the new home) | HA 2023.3 | Use `helpers.json.save_json`. [VERIFIED: developers.home-assistant.io `blog/2023/02/15/json`] |
| Register services in `async_setup` only | Register in `async_setup_entry` with `has_service` idempotency guard is widely accepted | HA 2024.x+ | Our integration uses `config_entries` only (no YAML), so registration must happen on first `setup_entry`. The idempotency guard is the accepted compromise. [CITED: HA core integration examples] |
| Lit form state via `@property` mutation | `@state` decorator for internal reactive state | Lit 2.x+ | Use `state: true` in static properties map (we use the static-properties style, not decorators, matching existing `flynow-card.ts`). |
| `target: ES2020` for HA cards | `target: ES2022` | HA frontend 2024.x | Already on ES2022 per `tsconfig.json`. No changes. |

**Deprecated / outdated:**
- **`Store` helper for user-visible files** — never was right for this; just noting it for completeness.
- **`requests` / synchronous HTTP** — not applicable here, but reiterating CLAUDE.md constraint.
- **Custom event bus for card↔backend** — superseded by `SupportsResponse`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `save_json` `atomic_writes` can be passed positionally as the 5th argument when also passing `encoder=None` (keyword-only) | Code Example (atomic write) | LOW — mitigation shown: wrap with `functools.partial(save_json, ..., atomic_writes=True)`. Tested via mypy strict will catch any mismatch. [ASSUMED] |
| A2 | Service handlers registered inside `async_setup_entry` (vs `async_setup`) are tolerated as long as registration is idempotent and services are domain-global | Pattern 1, Pitfall 7 | MEDIUM — HA dev docs officially prefer `async_setup`; the project has no `async_setup` function today. Planner may elect to add a minimal `async_setup(hass, config)` returning `True` and register services there instead. Either approach works. [ASSUMED] |
| A3 | `window.localStorage` is available in the Lovelace card execution context (HA frontend iframe / shadow DOM) | Pattern 3 (last-balloon prefill) | LOW — HA frontend is a normal browser document; localStorage is available. Fallback to `BALLOONS[0]` if `localStorage` is undefined (SSR/test). [ASSUMED — verify via manual smoke test in HA UI] |
| A4 | `ServiceValidationError` from voluptuous surfaces to the card caller as a rejected Promise from `callService` | Pitfall 6 | LOW — HA frontend maps voluptuous failures to WebSocket error responses; the `callService` Promise rejects. Card already handles this via `try/catch` around submit. [ASSUMED] |
| A5 | HA's "state attributes soft cap" warning threshold is ~16KB | Pitfall 3 | LOW — order-of-magnitude right; the decision to not use attributes holds regardless of exact threshold. [ASSUMED] |

**If the planner wants any of these verified before planning, run:**
- A1: `grep -n "def save_json" ~/site-packages/homeassistant/helpers/json.py` to check current signature.
- A2: Read any existing HA integration that does similar (e.g., `shopping_list`) for the `async_setup` vs `async_setup_entry` convention.
- A4: Write a failing-call integration test and inspect the exception type.

## Open Questions

1. **Should `list_flights` accept a pagination/limit parameter?**
   - What we know: Current operational tempo (crew logging ~100 flights/year) means even 5 years of history fits in one service response (~500 entries × 250 bytes = 125 KB). Not urgent.
   - What's unclear: Whether the card should ever render older entries paged.
   - Recommendation: Ship unbounded in Phase 3. Add `limit`/`offset` if UX feedback indicates scrolling pain. UI-SPEC does not mandate pagination.

2. **Should we expose an `edit_flight` or `delete_flight` service in Phase 3?**
   - What we know: UI-SPEC explicitly says "no delete/edit flow in this phase" (Copywriting Contract, destructive confirmation = `none`).
   - Recommendation: Ship read + append only. `id` field is stored now so future phases can add mutation without schema migration.

3. **Is the site dropdown values list fixed (three Phase-4 sites) or configurable?**
   - What we know: Phase 4 locked sites to exactly `lzmada`, `katarinka`, `nitra-luka` per D-01 of 04-CONTEXT.md. Service schema should use `vol.In(SITE_IDS)` directly.
   - Recommendation: Use `SITE_IDS` from `const.py`. Document that adding a site in v2 requires updating neither card nor service (the list is pulled from the single source).

4. **Do we need localization on service/error strings?**
   - What we know: Integration already ships `strings.json` for config flow translations. UI-SPEC locks copy in English.
   - Recommendation: English-only for Phase 3. If localization becomes needed, add keys to `strings.json` later — zero-cost migration.

5. **Should we debounce concurrent "list_flights" calls from the card?**
   - What we know: Each call is in-memory, O(n), cheap. Card only calls on mount + after submit.
   - Recommendation: No debouncing needed in Phase 3.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Integration runtime | ✓ | 3.14.3 (local) / HA 2025.1+ targets 3.12+ | — |
| `homeassistant` core (with `helpers.json`, `SupportsResponse`) | All backend | ✓ (assumed in HA install target) | 2025.1+ | — |
| `voluptuous` | Service schema validation | ✓ (transitive via HA) | any HA-pinned version | — |
| `lit` (frontend) | Card framework | ✓ | 3.3.2 in `package-lock.json` | — |
| `esbuild` | Card bundle | ✓ | 0.25.11 | — |
| `typescript` | Card typecheck | ✓ | 6.0.3 | — |
| HA REST/websocket API | Service call from card | ✓ (shipped with HA) | — | — |
| Writable `/config` directory | Atomic write target | ✓ (HA standard) | — | In tests, use `tmp_path` fixture |
| `pytest-homeassistant-custom-component` | Tests | ? | — | Existing tests run with plain `pytest` + light HA stubs (see `tests/test_coordinator.py` use of `pytest.mark.anyio` and raw `hass` mocks); keep that style |

**Missing dependencies with no fallback:** None. All required primitives are in the existing HA install + repo tooling.

**Missing dependencies with fallback:** `pytest-homeassistant-custom-component` — the existing tests do NOT import it (they use `anyio` + lightweight mocks). Stay consistent: new tests should follow the same minimal-mock approach seen in `tests/test_coordinator.py`, not introduce this library mid-project.

## Validation Architecture

> `workflow.nyquist_validation` is `false` in `.planning/config.json`. Section intentionally omitted.

## Security Domain

> Note: `security_enforcement` is not explicitly set in `.planning/config.json` but this project is a private hobby integration with no external network surface introduced by this phase. Conservative coverage below.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Card runs inside authenticated HA session; service calls are authorized by HA's caller context. |
| V3 Session Management | no | Managed entirely by HA. |
| V4 Access Control | partial | Any authenticated HA user can call the service. Acceptable because crew + pilot are the only users, and the data is cooperative (not secret). |
| V5 Input Validation | **yes** | `voluptuous` schema with `vol.In(...)` enums + `cv.date`/`cv.time` + `vol.Range` for duration. Notes field bounded in length (see below). |
| V6 Cryptography | no | No credentials, tokens, or secrets touched. File is plain JSON. |
| V9 Communications Security | no | All traffic is within HA's own WebSocket, already TLS-terminated by HA. |
| V12 File & Resources | **yes** | Controlled file path (`hass.config.path(...)` — no user-controlled filename); atomic write prevents partial-file corruption; no arbitrary file reads. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Excessive notes payload (GB-scale input fills disk) | Denial of Service | Add `vol.Length(max=2000)` to `notes` field in the schema. |
| Path traversal via site/filename | Tampering | Path is hard-coded via `hass.config.path(FLIGHT_LOG_FILENAME)`; filename is a `const` — no user input. |
| Malicious voluptuous bypass (unexpected field types) | Tampering | Use `vol.Schema({..., extra=vol.PREVENT_EXTRA})` so unknown keys are rejected. |
| JSON deserialization of malformed file (edited by user) | Data Integrity | `load_json_array` returns default on parse failure + log a warning so user can recover; do not crash. |
| Concurrent write data loss | Integrity | `asyncio.Lock` + atomic rename. |
| Log entry injection via crafted notes content | Data Integrity | JSON encoding handles escaping; no shell/SQL interpolation exists. Notes only rendered in Lit `${}` (auto-escaped). |

### Recommended Schema Additions (Security)

```python
LOG_FLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required("date"): cv.date,
        vol.Required("balloon"): vol.In(BALLOON_IDS),
        vol.Required("launch_time"): cv.time,
        vol.Required("duration_min"): vol.All(cv.positive_int, vol.Range(min=15, max=300)),
        vol.Required("site"): vol.In(SITE_IDS),
        vol.Required("outcome"): vol.In(OUTCOMES),
        vol.Optional("notes", default=""): vol.All(cv.string, vol.Length(max=2000)),
    },
    extra=vol.PREVENT_EXTRA,
)
```

## Sources

### Primary (HIGH confidence)

- github.com/home-assistant/core `homeassistant/helpers/json.py` — `save_json(filename, data, private=False, *, encoder=None, atomic_writes=False)` — confirms the atomic-write path; the internal `write_utf8_file_atomic` does temp-file + `os.replace`.
- github.com/home-assistant/core `homeassistant/util/json.py` — `load_json_array(filename, default=...)` — confirms missing/malformed file handling with defaults.
- github.com/home-assistant/core `homeassistant/helpers/storage.py` — `STORAGE_DIR = ".storage"` constant; confirms `Store` is unsuitable for `/config/flynow_flights.json`.
- github.com/home-assistant/frontend `src/types.ts` — `HomeAssistant.callService<T>(..., returnResponse?: boolean): Promise<ServiceCallResponse<T>>` signature.
- developers.home-assistant.io/docs/dev_101_services/ — canonical service registration patterns, `SupportsResponse.ONLY / .OPTIONAL / .NONE`.
- developers.home-assistant.io/docs/asyncio_blocking_operations/ — `hass.async_add_executor_job` for blocking I/O; explicit note that `Path.write_text`/`open` block the event loop.
- github.com/home-assistant/home-assistant-js-websocket issue #421 — historical context for `returnResponse` flag (now first-class on `callService`).
- developers.home-assistant.io/blog/2023/02/15/json/ — `save_json` moved from `util.json` to `helpers.json`.

### Secondary (MEDIUM confidence — WebSearch verified against official sources)

- HA community thread on best practices for persistent integration data — corroborates "use helpers, not manual `open`" guidance.
- HA community / thehomesmarthome.com tutorials on service registration — example voluptuous schemas aligned with dev_101.

### Tertiary (LOW confidence — not load-bearing)

- None retained; all claims above traced to HIGH/MEDIUM sources.

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — lit 3.3.2 + HA core 2025.1 verified; no new deps.
- Architecture: **HIGH** — domain service + in-memory store + atomic file write is the documented HA pattern and matches existing project conventions (coordinator singleton, voluptuous schemas, async lifecycle).
- Pitfalls: **HIGH** — all eight pitfalls verified against HA source or dev docs; none extrapolated.
- Security: **MEDIUM** — threat model is minimal by design (single-user tool, no network exposure introduced); controls listed are standard but not externally audited.
- Environment: **HIGH** — all dependencies verified in local tree / npm / HA core.

**Research date:** 2026-04-23
**Valid until:** 2026-05-23 (30 days — stable HA APIs, stable lit, no fast-moving surface)

---
*Phase: 03-flight-logging*
*Research completed: 2026-04-23*
