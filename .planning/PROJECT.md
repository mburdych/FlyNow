# FlyNow

## What This Is

FlyNow is a Home Assistant integration for hot air balloon crew and pilots. It checks weather conditions across a configurable radius, returns a single go/no-go answer for morning flying windows, and proactively notifies the crew and pilot via push notification, calendar event, and messaging (WhatsApp/Signal) when conditions look good. Built for OM-0007 and OM-0008 operating out of Slovakia.

## Core Value

One shared go/no-go answer that the crew and pilot both receive automatically — so nobody has to check five weather apps or call each other to decide.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Weather & Analysis**
- [ ] Fetch hourly forecast data from Open-Meteo for a user-configured location (Slovakia)
- [ ] Analyze key balloon parameters: surface wind speed/direction, wind shear at altitude, cloud ceiling, precipitation probability, visibility
- [ ] Filter analysis to early-morning windows (configurable time range, e.g. 05:00–09:00)
- [ ] Produce a go/no-go recommendation with condition breakdown
- [ ] Analyze conditions across ~100 km radius around launch site

**Configuration**
- [ ] User-configurable go/no-go thresholds (crew knows their limits — not just defaults)
- [ ] Support multiple named launch sites (OM-0007 vs OM-0008 may differ)
- [ ] Configurable forecast look-ahead: rough check 2–3 days out, firm check night before

**Alerting & Sharing**
- [ ] HA push notification to crew and pilot phones when a good window is detected
- [ ] Calendar event creation (Google Calendar) for confirmed good windows
- [ ] Outbound message via WhatsApp or Signal to a configured group/contact
- [ ] No-alert when conditions are poor (silence = no-go)

**Home Assistant Integration**
- [ ] Config flow UI for setup (location, API keys if needed, contacts, thresholds)
- [ ] Sensor entities exposing current go/no-go status and condition breakdown
- [ ] DataUpdateCoordinator refreshing on a schedule (e.g. every 1–3 hours)
- [ ] Lovelace card showing go/no-go, condition details, and next good window

**Flight Logging (v1 stretch)**
- [ ] Form in Lovelace card to log completed flights (date, time, site, outcome, notes)
- [ ] Store logs locally in HA config dir

### Out of Scope

- ML/weighted learning from flight history — deferred to v2; needs sufficient flight data to be meaningful
- Multi-pilot fleet management — built for one crew + one pilot, not a SaaS
- Paid weather APIs — Open-Meteo covers the use case for free
- Passenger flight vs fun flight threshold differentiation — same rules apply to both
- Automated no-go alerting (explicit message) — silence is sufficient for now

## Context

- **Crew role**: User is balloon crew, not the pilot. Decision authority is the pilot's, but crew needs the same information to coordinate.
- **Balloons**: OM-0007 and OM-0008 — Slovak registration, operated in Slovakia
- **Flight types**: Both commercial (passenger) and recreational. Same go/no-go thresholds apply to both.
- **Current workflow pain**: Checking Windy, Meteoblue, and other apps independently; pilot decides alone without shared view; good windows sometimes missed; hard to explain no-go decisions to passengers without clear data
- **Time sensitivity**: Balloon flying happens at dawn when thermals are calm. Decision windows matter — too late = missed flight, too early = forecast uncertainty
- **Forecast cadence**: Rough planning 2–3 days out, firm go/no-go decision the night before
- **Weather region**: Slovakia — Open-Meteo has good European coverage with no API key required
- **HA ecosystem**: User has Home Assistant already. This is a HACS-installable custom integration.

## Constraints

- **Tech stack**: Python async (HA integration), TypeScript/lit-html (Lovelace card), standard HACS patterns
- **Weather API**: Open-Meteo — free, no key, hourly forecasts, wind at multiple altitudes. No paid fallback for v1.
- **Messaging**: WhatsApp/Signal integration complexity depends on available APIs; may require HA notification service or third-party bridge
- **HA conventions**: Must follow HA code quality requirements — strict mypy, ruff, async throughout, config via config_entries
- **Data storage**: Flight logs in HA config dir (`/config/flynow_flights.json`) — no external database

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Open-Meteo for weather | Free, no API key, good European coverage, hourly wind at multiple altitudes | — Pending |
| Silence = no-go for alerts | Only notify on good windows; bad conditions don't need an alert | — Pending |
| Same thresholds for all flights | Pilot and crew agreed: passenger and fun flights use identical limits | — Pending |
| Flight log learning deferred to v2 | Insufficient data at launch to make learning meaningful | — Pending |
| HACS distribution | Standard way to install custom HA integrations; familiar to HA users | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-16 after initialization*
