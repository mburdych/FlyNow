# Phase 03: flight-logging - Pattern Map

**Mapped:** 2026-04-23
**Files analyzed:** 11
**Analogs found:** 11 / 11

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `custom_components/flynow/flight_log.py` | service | request-response + file-I/O | `custom_components/flynow/notifications.py` | role-match |
| `custom_components/flynow/__init__.py` | provider | request-response wiring | `custom_components/flynow/__init__.py` | exact |
| `custom_components/flynow/const.py` | config | transform | `custom_components/flynow/const.py` | exact |
| `custom_components/flynow/services.yaml` | config | request-response contract | `custom_components/flynow/strings.json` | partial |
| `custom_components/flynow/strings.json` | config | transform | `custom_components/flynow/strings.json` | exact |
| `lovelace/flynow-card/src/flynow-card.ts` | component | request-response | `lovelace/flynow-card/src/flynow-card.ts` | exact |
| `lovelace/flynow-card/src/flight-log-form.ts` | component | request-response + event-driven | `lovelace/flynow-card/src/flynow-card.ts` | role-match |
| `lovelace/flynow-card/src/flight-log-list.ts` | component | transform | `lovelace/flynow-card/src/flynow-card.ts` | role-match |
| `lovelace/flynow-card/src/flight-log-types.ts` | model | transform | `lovelace/flynow-card/src/types.ts` | exact |
| `lovelace/flynow-card/src/types.ts` | model | request-response typing | `lovelace/flynow-card/src/types.ts` | exact |
| `tests/test_flight_log.py` | test | request-response + file-I/O | `tests/test_coordinator.py` | role-match |

## Pattern Assignments

### `custom_components/flynow/flight_log.py` (service, request-response + file-I/O)

**Analog:** `custom_components/flynow/notifications.py`

**Imports + module shape** (`notifications.py`, lines 1-17):
```python
"""Notification orchestration for GO transitions."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from .const import (
    CONF_CALENDAR_ENTITY,
    CONF_CREW_NOTIFIER,
    ...
)
```

**Service call pattern** (`notifications.py`, lines 63-71):
```python
async def _send_notify(
    hass: Any, notifier_entity: str, message: str, title: str, channel_name: str
) -> str:
    await hass.services.async_call(
        "notify",
        "send_message",
        {"entity_id": notifier_entity, "message": message, "title": title},
        blocking=True,
    )
```

**Error fanout pattern** (`notifications.py`, lines 92-98, 165-173):
```python
async def _run_channel(channel: str, coro: Any) -> tuple[str, Exception | None]:
    try:
        await coro
        return channel, None
    except Exception as err:
        return channel, err
```

Use same "return structured result with sent/errors/reason" style for `log_flight` and `list_flights`.

---

### `custom_components/flynow/__init__.py` (provider, request-response wiring)

**Analog:** `custom_components/flynow/__init__.py`

**Setup wiring pattern** (lines 11-17):
```python
async def async_setup_entry(hass: Any, entry: Any) -> bool:
    hass.data.setdefault(DOMAIN, {})
    coordinator = FlyNowCoordinator(hass, entry.data)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR_DATA: coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
```

For Phase 3, keep this flow and add one idempotent service registration call after coordinator setup.

---

### `custom_components/flynow/const.py` (config, transform)

**Analog:** `custom_components/flynow/const.py`

**Constant declaration style** (lines 7-25, 83-110):
```python
DOMAIN = "flynow"
PLATFORMS = ["binary_sensor"]
...
SITE_CATALOG: Final[tuple[dict[str, object], ...]] = (
    {"id": "lzmada", ...},
    {"id": "katarinka", ...},
    {"id": "nitra-luka", ...},
)
SITE_IDS: Final[tuple[str, ...]] = ("lzmada", "katarinka", "nitra-luka")
```

Add service names, outcome enum, and log filename in this exact constant-centric style.

---

### `custom_components/flynow/services.yaml` (config, request-response contract)

**Analog:** `custom_components/flynow/strings.json` (closest config metadata file)

There is no existing `services.yaml` analog in this repo. Keep it small and explicit with two services:
- `log_flight` (required fields + selectors)
- `list_flights` (no fields, response-only behavior)

Pattern guidance from repo: keep integration metadata files colocated in `custom_components/flynow/` (`manifest.json`, `strings.json` already follow this).

---

### `lovelace/flynow-card/src/flynow-card.ts` (component, request-response)

**Analog:** `lovelace/flynow-card/src/flynow-card.ts`

**Reactive property pattern** (lines 15-32):
```typescript
static properties = {
  hass: { attribute: false },
};

private _hass?: HomeAssistantLike;
...
set hass(value: HomeAssistantLike | undefined) {
  const oldValue = this._hass;
  this._hass = value;
  this.requestUpdate("hass", oldValue);
}
```

**Section rendering pattern** (lines 132-147):
```typescript
return html`<ha-card>
  <div class="card-content">
    ...
    <div class="selected-site-details">
      ${this.renderConditionSection(attrs)}
      ${this.renderLaunchWindow(attrs)}
    </div>
  </div>
</ha-card>`;
```

Add flight logging UI as another card section following this compositional render style.

---

### `lovelace/flynow-card/src/flight-log-form.ts` (component, request-response + event-driven)

**Analog:** `lovelace/flynow-card/src/flynow-card.ts`

**Event handler style** (lines 177-181, 258-261):
```typescript
@click=${() => this.selectSite(siteId)}
...
private selectSite(siteId: string): void {
  this.selectedDetailSiteId = siteId;
  this.requestUpdate();
}
```

Use same inline event binding and internal state mutation pattern for form inputs and submit.

**Strong typing convention** (`types.ts`, lines 22-39):
```typescript
export interface FlyNowStatusAttributes {
  active_window: string;
  launch_start: string | null;
  ...
}
```

New form payload types should follow this interface-first style.

---

### `lovelace/flynow-card/src/flight-log-list.ts` (component, transform)

**Analog:** `lovelace/flynow-card/src/flynow-card.ts`

**List rendering pattern** (lines 139-141):
```typescript
<div class="sites-summary">
  ${SITE_ORDER.map((siteId) => this.renderSiteTile(siteId, attrs))}
</div>
```

Use same `map(...)` rendering and helper-method decomposition for log rows.

---

### `lovelace/flynow-card/src/flight-log-types.ts` (model, transform)

**Analog:** `lovelace/flynow-card/src/types.ts`

**Type grouping pattern** (lines 1-7, 22-31, 65-72):
```typescript
export type WindowKey = "today_evening" | "tomorrow_morning";

export interface FlyNowStatusAttributes {
  ...
}

export interface HomeAssistantLike {
  states: Record<string, HassEntityState | undefined>;
}
```

Keep flat exports and explicit unions/interfaces for payloads (`FlightOutcome`, `LogFlightRequest`, `LoggedFlight`).

---

### `lovelace/flynow-card/src/types.ts` (model, request-response typing)

**Analog:** `lovelace/flynow-card/src/types.ts`

Extend `HomeAssistantLike` with a typed `callService` signature (without changing existing naming conventions).

---

### `tests/test_flight_log.py` (test, request-response + file-I/O)

**Analog:** `tests/test_coordinator.py`

**Async pytest style** (lines 30-31):
```python
@pytest.mark.anyio
async def test_coordinator_dispatches_notifications_on_go_transition(monkeypatch) -> None:
```

**Local fake-hass pattern** (lines 15-28):
```python
class _Services:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

class _Hass:
    def __init__(self) -> None:
        self.services = _Services()
```

Reuse this lightweight mock style for service registration and call assertions in flight log tests.

---

## Shared Patterns

### Integration typing and import conventions
**Source:** `custom_components/flynow/__init__.py`, `custom_components/flynow/coordinator.py`
**Apply to:** all new Python integration files
```python
from __future__ import annotations
from typing import Any
```

### Voluptuous schema style
**Source:** `custom_components/flynow/config_flow.py` (lines 107-113, 176-193, 225-237)
**Apply to:** `log_flight` payload validation
```python
schema = vol.Schema(
    {
        vol.Required(...): ...,
        vol.Required(...): ...,
    }
)
```

### Card component structure
**Source:** `lovelace/flynow-card/src/flynow-card.ts` (lines 14-32, 122-148)
**Apply to:** `flight-log-form.ts`, `flight-log-list.ts`, card integration changes
```typescript
export class FlyNowCard extends LitElement {
  static properties = { hass: { attribute: false } };
  protected render(): TemplateResult { ... }
}
```

### Contract-style frontend tests
**Source:** `tests/test_card_contract.py` (lines 11-56)
**Apply to:** card log UI string/structure checks
```python
source = _card_text()
assert "..." in source
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `custom_components/flynow/services.yaml` | config | request-response | No existing `services.yaml` in repository |
| `custom_components/flynow/flight_log.py` (file-I/O section) | service | file-I/O | No current integration module performs persistent local JSON file writes |

## Metadata

**Analog search scope:** `custom_components/flynow/`, `lovelace/flynow-card/src/`, `tests/`
**Files scanned:** 10 source/test files + 2 metadata files
**Pattern extraction date:** 2026-04-23
