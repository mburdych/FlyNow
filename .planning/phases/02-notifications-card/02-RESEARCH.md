# Phase 2: Notifications & Card - Research

**Researched:** 2026-04-22  
**Domain:** Home Assistant notification orchestration + custom Lovelace card  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Notification fan-out runs in parallel and independently across channels. A failure in one channel does not block the others.
- **D-02:** Messaging path for v1 is WhatsApp-first. Signal support is deferred to a future phase/extension.
- **D-03:** Dedup identity is `window_key + launch_start` (for example `tomorrow_evening@18:30`).
- **D-04:** The 1-hour cooldown starts at first successful send attempt (first channel that actually delivers).
- **D-05:** Card top section uses a two-window summary: today's evening and tomorrow's morning GO/NO-GO tiles first.
- **D-06:** Condition rows show numeric value plus threshold and pass/fail indicator (for example `3.8 / 4.0 m/s` with a status chip/icon).
- **D-07:** Card updates reactively from Home Assistant entity state changes with near-real-time UX target (~5 seconds).
- **D-08:** On temporary data unavailability, card keeps last known values and displays a clear stale-data badge.

### Claude's Discretion
- Final visual styling details for the card (spacing, icon style, typography) as long as the two-window-first information hierarchy is preserved.
- Internal retry/backoff implementation for failed channels under the independent fan-out model.

### Deferred Ideas (OUT OF SCOPE)
- Signal-first or dual WhatsApp/Signal runtime selection in v1.
- Alternative card-first layouts (single active window only, full multiday grid first).
- Card polling/manual-refresh modes (reactive entity updates selected for v1).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NOTIF-01 | HA push notification sent to crew and pilot phones on flyable window detection (GO only) | Use HA notify actions with explicit notifier targets and coordinator-driven GO transition detection `[CITED: https://www.home-assistant.io/integrations/notify/]` `[CITED: https://developers.home-assistant.io/docs/integration_fetching_data/]` |
| NOTIF-02 | Google Calendar event created for confirmed good windows with launch time and duration | Use `calendar.create_event` with `summary`, `start_date_time`, `end_date_time` `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]` |
| NOTIF-03 | WhatsApp or Signal group message sent with go/no-go decision and condition summary | Route through configured HA notifier entity; prefer WhatsApp notifier in v1 per D-02 `[CITED: https://www.home-assistant.io/integrations/notify/]` |
| NOTIF-04 | Deduplication: no repeat notification for same window within 1 hour | Persist per-window send ledger keyed by `window_key@launch_start` + cooldown timestamp `[VERIFIED: codebase custom_components/flynow/const.py + 02-CONTEXT.md D-03/D-04]` |
| CARD-01 | Card displays today's evening window and tomorrow's morning window with clear GO/NO-GO status | Card binds to `flynow_status` attributes for both windows `[VERIFIED: codebase custom_components/flynow/sensor.py]` |
| CARD-02 | Card shows condition breakdown with threshold comparison | Reuse per-window `*_conditions` payload and threshold values from integration state `[VERIFIED: codebase custom_components/flynow/sensor.py]` |
| CARD-03 | Card shows calculated launch window times | Use `*_launch_start` and `*_launch_end` attributes already exposed `[VERIFIED: codebase custom_components/flynow/sensor.py]` |
</phase_requirements>

## Summary

Phase 2 should be planned as two coordinated streams: backend notification orchestration in the HA integration and frontend status rendering in a custom Lovelace card `[VERIFIED: roadmap Phase 2 plans in .planning/ROADMAP.md]`. The existing coordinator/sensor architecture already centralizes weather decisions and window payloads, so this phase should consume existing outputs rather than recomputing weather logic `[VERIFIED: codebase custom_components/flynow/coordinator.py + sensor.py]`.

For notifications, the safest standard path is to invoke HA `notify` and `calendar.create_event` actions from integration-side async code when a window transitions to GO, while enforcing dedup by the locked identity/cooldown decisions `[CITED: https://www.home-assistant.io/integrations/notify/]` `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]` `[VERIFIED: 02-CONTEXT.md D-03/D-04]`. Fan-out should use concurrent tasks with per-channel isolation so one failing target does not block others `[VERIFIED: 02-CONTEXT.md D-01]`.

For the card, plan a Lit-based custom element registered as a HA dashboard resource, subscribe to entity state updates, and render the fixed two-window-first hierarchy with stale-data affordance `[CITED: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/]` `[CITED: https://lit.dev/docs/components/properties/]` `[VERIFIED: 02-CONTEXT.md D-05..D-08]`.

**Primary recommendation:** Implement a transition-aware notification service in `custom_components/flynow` and a Lit custom card that directly projects `binary_sensor.flynow_status` attributes without introducing a parallel data model `[VERIFIED: codebase sensor attribute shape + coordinator pattern]`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Detect NO-GO -> GO transition | API / Backend (HA integration) | Database / Storage | Decision state is coordinator/entity data; dedup ledger persistence is integration responsibility `[VERIFIED: custom_components/flynow/coordinator.py]` |
| Push notification fan-out | API / Backend (HA integration) | External HA notify services | Notify actions are backend service calls, not frontend work `[CITED: https://www.home-assistant.io/integrations/notify/]` |
| Calendar event creation | API / Backend (HA integration) | External calendar integration | `calendar.create_event` is a backend action call `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]` |
| WhatsApp-first delivery routing | API / Backend (HA integration) | External notifier bridge | Channel selection and retries belong in integration orchestration `[VERIFIED: 02-CONTEXT.md D-02]` |
| Window status visualization | Browser / Client (Lovelace card) | API / Backend (entity state source) | Card renders from HA entity state subscription `[CITED: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/]` |
| Stale-data badge handling | Browser / Client (Lovelace card) | API / Backend (last update timestamp source) | UX display lives in card, freshness signal comes from state metadata `[VERIFIED: D-08 + ASSUMED timestamp strategy]` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Home Assistant core actions (`notify.*`, `notify.send_message`) | 2026.4.x docs baseline | Push + messaging delivery entry points | First-party notify API with entity/action model `[CITED: https://www.home-assistant.io/integrations/notify/]` |
| Home Assistant calendar action (`calendar.create_event`) | 2026.4.x docs baseline | Create flight window events | First-party calendar action with explicit payload schema `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]` |
| Lit | 3.3.2 | Reactive custom card rendering | Current npm release verified; standard for HA custom cards `[VERIFIED: npm registry lit@3.3.2 published 2025-12-23]` `[CITED: https://lit.dev/docs/components/properties/]` |
| TypeScript | 6.0.3 | Type-safe card implementation | Current npm release verified; strong typing for HA state payloads `[VERIFIED: npm registry typescript@6.0.3 published 2026-04-16]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant.helpers.storage.Store` | bundled with HA core `[ASSUMED]` | Persist dedup ledger across restarts | Use for NOTIF-04 cooldown durability `[ASSUMED]` |
| HA `asyncio` task fan-out (`asyncio.gather`) | Python stdlib 3.14 present | Parallel independent channel sends | Use to satisfy D-01 non-blocking fan-out `[VERIFIED: python 3.14.3 available]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Integration-owned notifier dispatch | HA automation authored by user | Less code but weaker control over D-03/D-04 dedup semantics `[CITED: https://www.home-assistant.io/docs/automation/action/]` |
| Lit custom card | Built-in markdown/entities cards composition | Faster initial setup but cannot enforce D-05/D-06 hierarchy cleanly `[ASSUMED]` |

**Installation:**
```bash
npm install lit typescript
```

**Version verification:**  
- `lit`: 3.3.2 (published 2025-12-23T22:03:29.485Z) `[VERIFIED: npm view lit version/time]`  
- `typescript`: 6.0.3 (published 2026-04-16T23:38:27.905Z) `[VERIFIED: npm view typescript version/time]`

## Architecture Patterns

### System Architecture Diagram

```text
Open-Meteo refresh -> FlyNowCoordinator computes windows/conditions
                    -> FlyNowStatusSensor attributes update in HA state machine
                    -> Transition detector compares previous vs current window GO state
                    -> [if NO-GO -> GO and cooldown clear]
                       -> fan-out task A: notify crew/pilot push
                       -> fan-out task B: calendar.create_event
                       -> fan-out task C: WhatsApp notifier
                    -> dedup ledger write (window_key@launch_start, first_success_at)

HA entity state updates -> Lovelace custom card subscription
                        -> render today_evening + tomorrow_morning tiles
                        -> render condition rows (value/threshold/pass-fail)
                        -> render launch timing + stale badge
```

### Recommended Project Structure
```text
custom_components/flynow/
├── notifications.py      # transition detection, fan-out, dedup store
├── services.py           # optional service wrappers for notify/calendar calls
├── coordinator.py        # existing source of weather/window truth
├── sensor.py             # existing entity attributes consumed by card
└── const.py              # keys, cooldown constants, channel config keys

lovelace/flynow-card/
├── src/flynow-card.ts    # Lit card class + render logic
├── src/types.ts          # typed entity attribute contract
└── package.json          # frontend build dependencies/scripts
```

### Pattern 1: Transition-Gated Notification Pipeline
**What:** Trigger outbound notifications only when a specific window transitions into GO.  
**When to use:** Every coordinator refresh where windows are recalculated.  
**Example:**
```python
# Source: https://developers.home-assistant.io/docs/integration_fetching_data/
window_id = f"{window_key}@{launch_start}"
if became_go and not dedup_store.in_cooldown(window_id, now_utc):
    results = await asyncio.gather(
        send_push(...),
        create_calendar_event(...),
        send_whatsapp(...),
        return_exceptions=True,
    )
    if any_success(results):
        await dedup_store.mark_sent(window_id, now_utc)
```

### Pattern 2: Entity-Driven Lit Rendering
**What:** Keep card reactive by consuming Home Assistant state context and re-rendering on state changes.  
**When to use:** Custom card visualization of live integration data.  
**Example:**
```typescript
// Source: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/
const stateObj = this.hass.states["binary_sensor.flynow_status"];
const eveningGo = stateObj?.attributes?.today_evening_go;
const tomorrowMorningGo = stateObj?.attributes?.tomorrow_morning_go;
```

### Pattern 3: Threshold Row Projection
**What:** Render each metric as `actual / threshold` with pass/fail marker from shared helper.  
**When to use:** CARD-02 condition visibility requirement.  
**Example:**
```typescript
// Source: https://lit.dev/docs/components/properties/
renderConditionRow(label: string, value: number, threshold: number, pass: boolean) {
  return html`${label}: ${value} / ${threshold} ${pass ? "PASS" : "FAIL"}`;
}
```

### Anti-Patterns to Avoid
- **Recomputing weather decisions in the card:** duplicates backend logic and can drift from sensor truth `[VERIFIED: coordinator/sensor already project decisions]`.
- **Using `notify.notify` implicit target:** can route to unintended notifier; use explicit notifier entities `[CITED: https://www.home-assistant.io/integrations/notify/]`.
- **Serial fan-out with early abort:** violates D-01 and delays successful channels `[VERIFIED: 02-CONTEXT.md D-01]`.
- **Dedup keyed only by day/window type:** breaks D-03 and risks suppressing distinct windows `[VERIFIED: 02-CONTEXT.md D-03]`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Notification transport adapters | Custom direct HTTP clients per provider | HA notify integrations/entities | Existing HA notification ecosystem already handles delivery backends `[CITED: https://www.home-assistant.io/integrations/notify/]` |
| Calendar ICS writer | Custom `.ics` generator | `calendar.create_event` action | Native action supports event creation payloads `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]` |
| Frontend reactive engine | Manual DOM diffing | Lit reactive properties/templates | Lit provides tested reactive update cycle `[CITED: https://lit.dev/docs/components/properties/]` |

**Key insight:** For Phase 2, correctness depends on orchestration and state transitions, not novel protocol implementations, so reuse HA actions and Lit reactivity wherever possible `[VERIFIED: phase scope + existing FlyNow architecture]`.

## Common Pitfalls

### Pitfall 1: Duplicate GO alerts on every refresh
**What goes wrong:** Every coordinator poll sends a fresh alert for the same window.  
**Why it happens:** Missing persisted dedup ledger or cooldown check.  
**How to avoid:** Store `window_key@launch_start` with first-success timestamp and check 1-hour cooldown before fan-out `[VERIFIED: D-03/D-04]`.  
**Warning signs:** Repeated notify logs at refresh interval cadence.

### Pitfall 2: Calendar event with invalid time payload
**What goes wrong:** Event creation silently fails or stores wrong duration.  
**Why it happens:** Using unsupported payload fields or zero-duration windows.  
**How to avoid:** Use documented `summary` + `start_date_time` + `end_date_time` fields; enforce end > start `[CITED: https://www.home-assistant.io/integrations/calendar/#action-create-event]`.  
**Warning signs:** Action trace errors on `calendar.create_event`.

### Pitfall 3: Card shows stale or blank values during transient backend gaps
**What goes wrong:** UI appears broken while backend recovers.  
**Why it happens:** Card treats temporary `unavailable` as hard failure with no fallback.  
**How to avoid:** Cache last known render model in component state and surface stale badge `[VERIFIED: D-08]`.  
**Warning signs:** Flickering tiles and missing condition rows during refresh.

## Code Examples

Verified patterns from official sources:

### HA notify send action
```yaml
# Source: https://www.home-assistant.io/integrations/notify/#example-with-the-entity-platform-notify-action
action: notify.send_message
data:
  entity_id: notify.my_direct_message_notifier
  message: "You have an update!"
  title: "Status changed"
```

### HA calendar create event action
```yaml
# Source: https://www.home-assistant.io/integrations/calendar/#action-create-event
action: calendar.create_event
target:
  entity_id: calendar.device_automation_schedules
data:
  summary: "Example"
  start_date_time: "2026-04-22 18:30:00"
  end_date_time: "2026-04-22 20:00:00"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy `notify.<service>` only | Entity-platform `notify.send_message` + explicit notifier targeting | Active migration phase in current docs | Better multi-target and clearer routing semantics `[CITED: https://www.home-assistant.io/integrations/notify/]` |
| Ad-hoc custom element state polling | Context/state subscription model for custom cards | Current HA frontend custom card docs | Near-real-time card updates without manual polling loops `[CITED: https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/]` |

**Deprecated/outdated:**
- Blind `notify.notify` shorthand for production fan-out: discouraged because target can be ambiguous `[CITED: https://www.home-assistant.io/integrations/notify/]`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `homeassistant.helpers.storage.Store` is available and preferred for dedup persistence in this custom integration | Standard Stack | If unavailable, planner must switch to alternative persistence path |
| A2 | Built-in cards cannot satisfy D-05/D-06 information hierarchy without custom card compromises | Standard Stack | Could overbuild frontend if a simpler built-in composition is acceptable |
| A3 | Stale badge can rely on integration-provided freshness metadata without additional backend changes | Architectural Responsibility Map | Might require extra sensor attributes if freshness is not currently exposed |

## Open Questions (RESOLVED)

1. **Which concrete notifier entities are configured for crew and pilot?**  
   **RESOLVED:** The integration will require explicit notifier configuration via config entry fields: `crew_notifier`, `pilot_notifier`, and `group_notifier`. Setup validation will verify each entity exists in `hass.states` and block setup with a clear repairable error if any target is missing.

2. **Should calendar dedup use event lookup or rely solely on notification ledger?**  
   **RESOLVED:** v1 dedup will rely solely on the shared notification ledger keyed by `window_key@launch_start` with the first-success cooldown timestamp (D-03/D-04). Calendar event lookups are deferred and can be added later if deployment evidence shows duplicate events despite ledger protection.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Lovelace card build | ✓ | v22.22.0 | — |
| npm | Frontend dependency install | ✓ | 11.11.0 | — |
| Python | HA integration runtime/tests | ✓ | 3.14.3 | — |
| pip | Python dependency install | ✓ | 26.0.1 | — |
| Home Assistant runtime | End-to-end notification/card behavior | ✗ (not detected in local shell) | — | Unit tests + static validation only |
| Google Calendar integration configured in HA | NOTIF-02 execution | ? | — | Local calendar or skip calendar action in dev |
| WhatsApp-capable notifier in HA | NOTIF-03 execution | ? | — | Persistent notification during development |

**Missing dependencies with no fallback:**
- None identified for coding/testing in repository scope.

**Missing dependencies with fallback:**
- Live HA integration targets (calendar/notifier entities) can be replaced with mock services in tests.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Rely on HA auth/session model; no custom auth layer in integration `[ASSUMED]` |
| V3 Session Management | no | Delegated to Home Assistant platform `[ASSUMED]` |
| V4 Access Control | yes | Restrict service calls to configured entity IDs from config entry `[ASSUMED]` |
| V5 Input Validation | yes | Validate notifier IDs, calendar entity, and message template inputs before action call `[CITED: https://www.home-assistant.io/docs/automation/action/]` |
| V6 Cryptography | no (directly) | Use existing secure transport of underlying integrations; do not hand-roll crypto `[ASSUMED]` |

### Known Threat Patterns for HA integration + custom card

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Template/message injection via user-configured text | Tampering | Strictly format outbound payloads and avoid executing dynamic templates from untrusted input `[ASSUMED]` |
| Notification spam amplification | Denial of Service | Enforce D-03/D-04 dedup and per-channel timeout/retry bounds `[VERIFIED: 02-CONTEXT.md D-03/D-04]` |
| Unintended notifier target misuse | Information Disclosure | Validate target entities belong to configured allowlist `[ASSUMED]` |

## Sources

### Primary (HIGH confidence)
- [https://developers.home-assistant.io/docs/integration_fetching_data/](https://developers.home-assistant.io/docs/integration_fetching_data/) - DataUpdateCoordinator and polling/update patterns.
- [https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/](https://developers.home-assistant.io/docs/frontend/custom-ui/custom-card/) - Custom card lifecycle, state context subscription, sizing.
- [https://www.home-assistant.io/integrations/notify/](https://www.home-assistant.io/integrations/notify/) - Notify actions, explicit target guidance, `notify.send_message`.
- [https://www.home-assistant.io/integrations/calendar/#action-create-event](https://www.home-assistant.io/integrations/calendar/#action-create-event) - Calendar event action payload contract.
- [https://lit.dev/docs/components/properties/](https://lit.dev/docs/components/properties/) - Lit reactive properties and update behavior.
- npm registry via `npm view` - `lit` 3.3.2 and `typescript` 6.0.3 current versions and publish timestamps.
- Local codebase: `custom_components/flynow/coordinator.py`, `custom_components/flynow/sensor.py`, `custom_components/flynow/const.py`, and `.planning/phases/02-notifications-card/02-CONTEXT.md`.

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - HA + Lit + npm versions verified with official docs/registry.
- Architecture: HIGH - locked phase decisions and existing coordinator/sensor structure are explicit in repo.
- Pitfalls: MEDIUM - grounded in docs and architecture but some operational behavior depends on actual HA deployment config.

**Research date:** 2026-04-22  
**Valid until:** 2026-05-22
