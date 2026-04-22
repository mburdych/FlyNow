# Phase 2: Notifications & Card - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 2-notifications-card
**Areas discussed:** Alert channel policy, Deduplication rules, Card information design, Card update behavior

---

## Alert channel policy

| Option | Description | Selected |
|--------|-------------|----------|
| Parallel + independent | Trigger all channels concurrently; one failure does not block others. | ✓ |
| All-or-nothing | Only treat alert cycle as success if all channels succeed in one run. | |
| Priority sequence | Send push first, then calendar, then messaging. | |

**User's choice:** Parallel + independent
**Notes:** Favor reliability and partial success over coupled channel behavior.

| Option | Description | Selected |
|--------|-------------|----------|
| WhatsApp first | Implement WhatsApp path in v1 and defer Signal. | ✓ |
| Signal first | Start with Signal and defer WhatsApp. | |
| Runtime selectable | Support either WhatsApp/Signal selection in v1 config flow. | |

**User's choice:** WhatsApp first
**Notes:** Signal deferred from v1.

---

## Deduplication rules

| Option | Description | Selected |
|--------|-------------|----------|
| Window key + launch start | Use a specific window identity (for example `tomorrow_evening@18:30`). | ✓ |
| Window key only | Any alert in same window name treated as duplicate. | |
| Time bucket only | Any GO in next 60 minutes treated as duplicate. | |

**User's choice:** Window key + launch start
**Notes:** Explicit dedup identity chosen for predictable behavior.

| Option | Description | Selected |
|--------|-------------|----------|
| From successful send | Start cooldown from first successful delivery. | ✓ |
| From GO detection | Start cooldown immediately at GO detection. | |
| Per-channel cooldown | Keep separate cooldown clocks per channel. | |

**User's choice:** From successful send
**Notes:** Dedup tied to actual delivery rather than mere detection.

---

## Card information design

| Option | Description | Selected |
|--------|-------------|----------|
| Two-window summary | Top focus on today evening + tomorrow morning with GO/NO-GO tiles. | ✓ |
| Single active window | Show only one most relevant window at a time. | |
| Full multiday grid | Show all windows equally first. | |

**User's choice:** Two-window summary
**Notes:** Keeps pilot/crew decision windows immediately visible.

| Option | Description | Selected |
|--------|-------------|----------|
| Numeric + pass/fail indicator | Show measured value, threshold, and clear status indicator. | ✓ |
| Color-only bars | Visual bars without explicit thresholds. | |
| Raw values only | Display values without pass/fail semantics. | |

**User's choice:** Numeric + pass/fail indicator
**Notes:** Threshold transparency is required in the card.

---

## Card update behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Reactive HA entity updates | Re-render when entity state changes (target near real-time). | ✓ |
| Card polling interval | Poll state on a fixed interval. | |
| Manual refresh only | Update only when user refreshes manually. | |

**User's choice:** Reactive HA entity updates
**Notes:** Desired UX is immediate operational feedback.

| Option | Description | Selected |
|--------|-------------|----------|
| Last known + stale badge | Keep latest values visible with stale indication. | ✓ |
| Hard error screen | Replace content with full error-only view. | |
| Blank card | Show nothing until data returns. | |

**User's choice:** Last known + stale badge
**Notes:** Preserve context during temporary outages.

---

## Claude's Discretion

- Implementation details for retries/backoff and logging around independent channel fan-out.
- Card visual polish details that do not alter selected information hierarchy.

## Deferred Ideas

- Signal-first or runtime dual-channel selector in v1.
- Alternate card layouts not chosen in this discussion.
- Polling/manual-refresh card update models.
