# FlyNow

## What This Is

FlyNow is a Home Assistant integration for hot air balloon crew and pilots that provides one shared GO/NO-GO decision for morning/evening flight windows, sends aligned notifications, and supports post-flight logging.

## Core Value

One shared go/no-go answer that the crew and pilot both receive automatically.

## Current State

- **Latest shipped milestone:** v1.1 (2026-04-24)
- **Delivered scope:** Core integration, notifications, Lovelace card, flight logging, multi-site planning, translation contract parity fix
- **Deployment state:** Stable HAOS operation with known same-day production fixes documented in `.planning/reference/RELEASE-NOTES-2026-04-24.md`

## Requirements

### Validated

- ✓ Weather analysis and time-window evaluation (WEATHER-01..05, TIME-01..04, FORE-01..02) — v1.0
- ✓ HA integration setup, coordinator lifecycle, and sensor contract (HA-01..03) — v1.0
- ✓ Notification delivery and dedup behavior (NOTIF-01..04) — v1.0
- ✓ Lovelace card status and threshold rendering (CARD-01..03) — v1.0
- ✓ Flight logging form and atomic local persistence (LOG-01..02) — v1.0
- ✓ Three-site comparison planning with backward compatibility (SITE-01..04) — v1.0
- ✓ Translation contract parity and Slovak diacritics (TR-01..05) — v1.1

### Active

- [ ] Ceiling/cloud-base reliability hardening for low-quality forecast scenarios
- [ ] Structured UAT checklist with screenshot baselines
- [ ] v2 learning loop from historical flights (LEARN-01..02)

### Out of Scope

- Multi-pilot / fleet management
- Paid weather APIs
- Separate passenger vs recreational threshold sets

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Open-Meteo as primary weather source | Free, no key, sufficient coverage | ✓ Shipped in v1.0 |
| Silence equals no-go for alerts | Reduce noise, notify on actionable GO only | ✓ Shipped in v1.0 |
| Backward-compatible `binary_sensor.flynow_status` | Protect existing automations while extending UI payload | ✓ Shipped in v1.0 |
| Civil twilight operational boundary | Align behavior to EASA/SERA day limits | ✓ Shipped in v1.0 |
| Keep localization keys parity-locked between source and locale files | Prevent config-flow regressions from drift | ✓ Shipped in v1.1 |

---
*Last updated: 2026-04-24 after v1.1 milestone closure*
