# Phase 07: Flight Log Import + Map Visualization (BACKLOG) - Pattern Map

**Mapped:** 2026-04-28  
**Files analyzed:** 9  
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `custom_components/flynow/flight_import.py` | service | file-I/O, transform, request-response | `custom_components/flynow/flight_log.py` | role-match |
| `custom_components/flynow/flight_sidecar_store.py` | service | file-I/O, CRUD | `custom_components/flynow/flight_log.py` | exact |
| `custom_components/flynow/weather_snapshot.py` | service | request-response, transform | `custom_components/flynow/coordinator.py` | role-match |
| `custom_components/flynow/flight_log.py` (modify) | service | request-response, CRUD | `custom_components/flynow/flight_log.py` | exact |
| `custom_components/flynow/coordinator.py` (modify) | service | request-response, event-driven | `custom_components/flynow/coordinator.py` | exact |
| `custom_components/flynow/sensor.py` (modify) | projection/entity | transform | `custom_components/flynow/sensor.py` | exact |
| `lovelace/flynow-card/src/types.ts` (modify) | model | transform | `lovelace/flynow-card/src/types.ts` | exact |
| `lovelace/flynow-card/src/flynow-card.ts` (modify) | component | request-response, event-driven | `lovelace/flynow-card/src/flynow-card.ts` | exact |
| `lovelace/flynow-card/src/map-renderer.ts` | utility | transform, event-driven | `lovelace/flynow-card/src/flynow-card.ts` | partial |

## Pattern Assignments

### `custom_components/flynow/flight_import.py` (service, file-I/O + transform + request-response)

**Analog:** `custom_components/flynow/flight_log.py`

**Imports + schema pattern** (lines 5-17, 39-52):
```python
import asyncio
import json
import logging
from datetime import UTC, date, datetime, time
from pathlib import Path
from typing import Any
import voluptuous as vol

LOG_FLIGHT_SCHEMA = vol.Schema(
    {
        vol.Required("date"): vol.Coerce(str),
        vol.Required("balloon"): vol.In(BALLOON_IDS),
        vol.Required("launch_time"): vol.Coerce(str),
        ...
    },
    extra=vol.PREVENT_EXTRA,
)
```

**Service handler contract pattern** (lines 166-177):
```python
async def _handle_log_flight(call: Any) -> dict[str, Any]:
    candidate_payload = dict(call.data)
    if candidate_payload.get("notes") is None:
        candidate_payload["notes"] = ""
    payload = LOG_FLIGHT_SCHEMA(candidate_payload)
    entry = await store.async_append(payload)
    return {"entry": entry}
```

**Normalization + explicit validators** (lines 57-64, 140-154):
```python
def _validate_date(value: str) -> str:
    date.fromisoformat(value)
    return value

def _validate_time(value: str) -> str:
    parsed = time.fromisoformat(value)
    return parsed.strftime("%H:%M")
```

**Integration points for Phase 07**
- Register new import service in same `async_register_services()` style.
- Reuse schema-first validation approach for GPX/CSV metadata + timezone policy.
- Return response payload with accepted points, dropped-point warnings, and sidecar linkage by stable `flight_id`.

---

### `custom_components/flynow/flight_sidecar_store.py` (service, file-I/O + CRUD)

**Analog:** `custom_components/flynow/flight_log.py`

**Atomic write pattern** (lines 120-139):
```python
def _write_entries_sync(self, entries: list[dict[str, Any]]) -> None:
    self._path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=self._path.parent, delete=False, suffix=".tmp"
    ) as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)
        temp_path = Path(handle.name)
    for attempt in range(5):
        try:
            temp_path.replace(self._path)
            break
        except PermissionError:
            if attempt == 4:
                raise
            time_module.sleep(0.02 * (attempt + 1))
```

**Corruption recovery pattern** (lines 98-115):
```python
def _load_entries_sync(self) -> list[dict[str, Any]]:
    if not self._path.exists():
        return []
    try:
        with self._path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        backup_path = self._path.with_name(
            f"{FLIGHT_LOG_FILENAME}.corrupt-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        )
        shutil.move(str(self._path), str(backup_path))
        return []
```

**Concurrency guard pattern** (lines 73-90):
```python
self._lock = asyncio.Lock()

async def async_append(self, payload: dict[str, Any]) -> dict[str, Any]:
    async with self._lock:
        await self._async_load_locked()
        entry = self._normalize(payload)
        next_entries = [*self._entries, entry]
        await self._async_write(next_entries)
        self._entries = next_entries
        return entry
```

**Integration points for Phase 07**
- Keep sidecar writes atomic and independent from legacy `flynow_flights.json`.
- Use lock-scoped read-modify-write to keep immutable base + append-only corrections consistent.
- Store raw points + derived summary in one sidecar record keyed by `flight_id`.

---

### `custom_components/flynow/weather_snapshot.py` (service, request-response + transform)

**Analog:** `custom_components/flynow/coordinator.py`

**Async provider call + domain exception handling** (lines 90-95, 132-134):
```python
async with aiohttp.ClientSession() as session:
    payload = await fetch_forecast(session, float(site["lat"]), float(site["lon"]))
...
except OpenMeteoError as err:
    raise UpdateFailed(str(err)) from err
```

**Snapshot-friendly assembled payload pattern** (lines 124-131, 171-180):
```python
sites[site_id] = {
    "site_id": site_id,
    "site_name": str(site["name"]),
    "windows": result_windows,
    "active_window": next(iter(result_windows.values()), None),
}

return {
    "active_window": active,
    "windows": result_windows,
    "data_last_updated_utc": now_utc.isoformat(),
    "sites": sites,
}
```

**Deterministic fallback pattern** (lines 83-88, 135-137):
```python
selected_site_id = str(self._config.get(CONF_SELECTED_SITE_ID, DEFAULT_SELECTED_SITE_ID))
if selected_site_id not in SITE_IDS:
    selected_site_id = DEFAULT_SELECTED_SITE_ID

selected_site = sites.get(selected_site_id) or sites.get(DEFAULT_SELECTED_SITE_ID) or {}
active = selected_site.get("active_window")
```

**Integration points for Phase 07**
- Freeze forecast snapshot at decision time using coordinator-computed window context.
- Use deterministic source chain resolver for observed weather (`metar` -> `archive` -> `manual`) and persist provenance.
- On lookup failure, keep import successful and emit `weather_missing` marker in sidecar payload.

---

### `custom_components/flynow/flight_log.py` (modify; service, request-response + CRUD)

**Analog:** `custom_components/flynow/flight_log.py` (self)

**Canonical ID pattern to preserve** (lines 144-147):
```python
return {
    "id": str(uuid4()),
    "created_at": datetime.now(UTC).isoformat(),
    "schema_version": 1,
    ...
}
```

**Service registration pattern to extend** (lines 179-190):
```python
hass.services.async_register(
    DOMAIN,
    SERVICE_LOG_FLIGHT,
    _handle_log_flight,
    supports_response=SupportsResponse.ONLY,
)
```

**Integration points for Phase 07**
- Keep legacy schema backward compatible.
- Add sidecar linkage fields without breaking existing list/log service response shape consumed by card/tests.
- Add finalize/import hook path that can trigger snapshot freeze when missing.

---

### `custom_components/flynow/coordinator.py` (modify; service, request-response + event-driven)

**Analog:** `custom_components/flynow/coordinator.py` (self)

**Per-site decision map pattern** (lines 117-131):
```python
result_windows: dict[str, Any] = {}
for window in windows:
    result_windows[window["key"]] = {
        **window,
        **analyze_window(payload["hourly"], thresholds),
    }
sites[site_id] = {
    "site_id": site_id,
    "site_name": str(site["name"]),
    "windows": result_windows,
    "active_window": next(iter(result_windows.values()), None),
}
```

**State-carrying pattern across updates** (lines 71-73, 170):
```python
self._previous_windows: dict[str, dict[str, Any]] = {}
self._notification_dedup: dict[str, datetime] = {}
...
self._previous_windows = result_windows
```

**Integration points for Phase 07**
- Capture and persist forecast snapshot when transitioning to decision-ready state.
- Reuse existing per-site structures so snapshot payload can align with card’s selected-site view.

---

### `custom_components/flynow/sensor.py` (modify; projection/entity, transform)

**Analog:** `custom_components/flynow/sensor.py` (self)

**Attribute projection pattern** (lines 43-58):
```python
attrs: dict[str, Any] = {
    "active_window": "none",
    "launch_start": None,
    "launch_end": None,
    "data_last_updated_utc": data.get("data_last_updated_utc"),
    "notification_result": data.get("notification_result", {}),
    "selected_site_id": selected_site_id,
    "sites_summary": data.get("sites_summary", {}),
    "sites": data.get("sites", {}),
}
```

**Window flattening compatibility pattern** (lines 63-68):
```python
for key, item in windows.items():
    attrs[f"{key}_go"] = item.get("go")
    attrs[f"{key}_launch_start"] = item.get("launch_start")
    attrs[f"{key}_launch_end"] = item.get("launch_end")
    attrs[f"{key}_conditions"] = item.get("conditions", {})
```

**Integration points for Phase 07**
- Expose compact correlation/map summary attributes only (avoid full raw track arrays in sensor state).
- Keep flattened compatibility keys where needed for existing card code paths.

---

### `lovelace/flynow-card/src/types.ts` (modify; model, transform)

**Analog:** `lovelace/flynow-card/src/types.ts`

**Union + interface contract style** (lines 1-2, 56-67, 81-98):
```typescript
export type WindowKey = "today_evening" | "tomorrow_morning";
export type LanguageCode = "sk" | "en";

export interface FlyNowConditionValue {
  value: number | string | null;
  threshold: number | string | null;
  pass: boolean;
  ...
}

export interface FlyNowStatusAttributes {
  active_window: string;
  launch_start: string | null;
  launch_end: string | null;
  ...
}
```

**Service call typing pattern** (lines 134-145):
```typescript
export interface HomeAssistantLike {
  callService<T = unknown>(
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>,
    target?: Record<string, unknown>,
    notifyOnError?: boolean,
    returnResponse?: boolean
  ): Promise<{ context: { id: string }; response?: T }>;
}
```

**Integration points for Phase 07**
- Add strongly typed `track summary`, `weather snapshot`, and `corrections` interfaces.
- Keep nullable/optional field style aligned with existing payload evolution.

---

### `lovelace/flynow-card/src/flynow-card.ts` (modify; component, request-response + event-driven)

**Analog:** `lovelace/flynow-card/src/flynow-card.ts` (self)

**Service-call interaction pattern** (lines 771-778, 803-810):
```typescript
const response = await this.hass.callService<LogFlightResponse>(
  "flynow",
  "log_flight",
  { ...this.logForm },
  undefined,
  false,
  true
);
```

**Sectioned render composition pattern** (lines 439-447):
```typescript
<div class="sites-summary">
  ${SITE_ORDER.map((siteId) => this.renderSiteTile(siteId, attrs))}
</div>
<div class="selected-site-details">
  ${this.renderConditionSection(attrs)}
  ${this.renderLaunchWindow(attrs)}
</div>
${this.renderFlightLogSection(attrs)}
```

**Local component state pattern** (lines 147-154):
```typescript
private flightHistory: LoggedFlight[] = [];
private historyLoading = false;
private flightSubmitState: "idle" | "saving" | "success" | "error" = "idle";
private submitMessage = "";
private logForm: LogFlightPayload = this.createDefaultLogForm();
```

**Integration points for Phase 07**
- Add import/map/correlation UI as additional render section(s), following helper-method segmentation.
- Keep all backend interactions via typed `callService` wrappers.
- Surface dropped-point warnings and weather provenance in status blocks consistent with existing submit feedback pattern.

---

### `lovelace/flynow-card/src/map-renderer.ts` (utility, transform + event-driven)

**Analog:** `lovelace/flynow-card/src/flynow-card.ts` (partial)

**Closest reusable local pattern**
- Isolate UI concerns into helper methods (e.g., `renderConditionSection`, `renderLaunchWindow`, `renderFlightLogSection`) instead of monolithic `render()`.
- Keep state updates explicit and trigger rerender via `requestUpdate()` when needed.

**Integration points for Phase 07**
- Create a focused renderer utility that receives normalized track coordinates + style options from card component.
- Keep renderer lifecycle separate from service calls and domain state mutation.

## Shared Patterns

### Validation-first service boundary
**Source:** `custom_components/flynow/flight_log.py` (lines 39-52, 166-171)  
**Apply to:** `flight_import.py`, `weather_snapshot.py` inputs
```python
LOG_FLIGHT_SCHEMA = vol.Schema(..., extra=vol.PREVENT_EXTRA)
payload = LOG_FLIGHT_SCHEMA(candidate_payload)
```

### Atomic local JSON persistence
**Source:** `custom_components/flynow/flight_log.py` (lines 120-139)  
**Apply to:** `flight_sidecar_store.py`, any immutable snapshot/corrections persistence
```python
with tempfile.NamedTemporaryFile(...) as handle:
    json.dump(entries, handle, ensure_ascii=False, indent=2)
temp_path.replace(self._path)
```

### Stable identity + append model
**Source:** `custom_components/flynow/flight_log.py` (lines 144-147)  
**Apply to:** sidecar keying and record lineage
```python
"id": str(uuid4()),
"created_at": datetime.now(UTC).isoformat(),
"schema_version": 1,
```

### Per-site coordinator payload shaping
**Source:** `custom_components/flynow/coordinator.py` (lines 124-131, 171-180)  
**Apply to:** forecast snapshot freeze payload and card-facing summary payloads
```python
sites[site_id] = {..., "windows": result_windows, "active_window": ...}
return {"active_window": active, "windows": result_windows, "sites": sites}
```

### Typed frontend contracts for evolving payloads
**Source:** `lovelace/flynow-card/src/types.ts` (lines 81-98, 109-127)  
**Apply to:** track summary, snapshot, corrections typing
```typescript
export interface FlyNowStatusAttributes { ... }
export interface FlyNowWindowData { ... }
```

### Typed HA service calls in card
**Source:** `lovelace/flynow-card/src/flynow-card.ts` (lines 771-778, 803-810)  
**Apply to:** import service invocation and detail fetches
```typescript
await this.hass.callService<ResponseType>("flynow", "service_name", payload, undefined, false, true)
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `lovelace/flynow-card/src/map-renderer.ts` | utility | event-driven, transform | No existing dedicated renderer utility module in card codebase; only component-level render helpers exist. |

## Metadata

**Analog search scope:** `custom_components/flynow/`, `lovelace/flynow-card/src/`, `tests/`, phase context docs  
**Files scanned:** 11  
**Pattern extraction date:** 2026-04-28
