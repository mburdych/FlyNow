# Feature Research: Hot Air Balloon Flying Condition Advisor

**Domain:** Home Assistant custom integration for balloon crew/pilot go-no-go coordination
**Research Date:** 2026-04-16
**Confidence:** MEDIUM (training data + domain context; web search/official docs blocked)

## Executive Summary

FlyNow targets a specific niche: balloon crew and pilot need one shared, automated go-no-go answer rather than independently checking 5+ weather apps. The feature set focuses on three pillars:

1. **Unified Decision Making** — Single authoritative recommendation replaces app fatigue
2. **Proactive Alerting** — Crew and pilot get notified together, no coordination overhead
3. **Actionable Details** — Show *why* the answer is go/no-go to explain to crew/passengers and let pilot override if needed

This differs from general aviation weather apps (which optimize for exploration) and flight planning tools (which assume active user engagement). FlyNow assumes users are passive until alerted, then need to make a quick decision.

## Balloon-Specific Flight Parameters

Based on CLAUDE.md and standard hot air balloon operating practices:

### Critical Parameters (Decision-Blocking)

| Parameter | Typical Threshold | Why It Matters |
|-----------|------------------|---------------|
| Surface wind speed | < 15 km/h (8 knots) at launch | Balloon envelope deployment, ground control, passenger safety |
| Wind direction variability | < 45° shift in next 2h | Unpredictable drift patterns, launch site safety margins |
| Cloud base ceiling | > 300-500m minimum | Legal flight altitude, thermal activity visibility, safety ceiling |
| Precipitation probability | < 5-10% in flight window | Envelope damage, visibility, passenger comfort |
| Visibility | > 5-10 km | Navigation, spotting landing zones, safety |

### Secondary Parameters (Decision-Informing)

| Parameter | Typical Range | Why It Matters |
|-----------|---------------|---------------|
| Wind shear (surface to 500m) | Smooth gradient preferred | Envelope stress, altitude control behavior |
| Thermal activity | Weak/none in morning | Balloon stability in early morning is key; strong thermals = unstable conditions |
| Humidity | Moderate range | Affects density altitude, lift performance |
| Temperature stability | No sudden changes | Affects thermal environment, balloon performance |
| Pressure trend | Stable or rising preferred | Indicates weather stability |

### Time-of-Day Dependency

**Balloon flying requires early morning stability:**
- Optimal window: 05:00–08:30 (before thermals strengthen)
- Forecast must specifically analyze this time range (not all-day averages)
- Afternoon flying possible but less ideal for recreational/passenger ops

---

## Table Stakes Features

**These are expected by any balloon weather app. Missing one feels incomplete.**

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|-----------|-------|
| Go/No-Go recommendation | Core use case — pilot needs a clear answer | Low | Binary or 2-3 tier (Go / Marginal / No-Go) |
| Wind speed at surface | Most critical safety parameter | Low | Display current + 2-hour trend |
| Wind direction + trend | Directly affects launch zone safety | Low | Show vector, not just speed |
| Cloud ceiling (CEIL) | Ceiling legal minimum, affects thermal behavior | Medium | Requires processing cloud layers from weather data |
| Precipitation probability | Passenger comfort + envelope safety | Low | Show % chance and timing within flight window |
| Visibility | Safety and navigation | Low | Actual visibility or visibility category |
| Time-bounded analysis | Balloon flying happens at dawn, not all-day | Medium | Filter analysis to configurable window (e.g. 05:00–09:00) |
| Multi-hour forecast | Early decision (2-3 days out), firm decision (night before) | Low | Show hourly data for 6-12 hour window |
| Configurable location/site | Balloon ops have multiple launch sites | Low | Support multiple named locations, select active site |
| Configurable thresholds | Different balloons/crews have different limits | Medium | UI to adjust wind speed, ceiling, precipitation limits |
| HA sensor entities | Integration with HA automations + dashboards | Low | Standard HA entity patterns (sensor, binary_sensor) |
| Status display card | Quick visual status for crew | Low | Lovelace card showing go/no-go + key conditions |

---

## Differentiators

**Features that set FlyNow apart from checking raw weather apps.**

| Feature | Value Proposition | Complexity | Rationale |
|---------|-------------------|-----------|-----------|
| Automated morning window detection | Crew + pilot both get notified at the right time, don't have to check app constantly | High | Real differentiator: crew doesn't wake up checking weather; they get one notification when it's good |
| Spatial analysis (100km radius) | Local conditions vary significantly; one-point forecast isn't enough | High | Balloon can drift; conditions at launch site ≠ landing zone; radius analysis critical for safety |
| Single shared notification to crew + pilot together | Eliminates "did pilot see this?" coordination overhead | Medium | Both receive push notification simultaneously; shared calendar event proves mutual awareness |
| Calendar event for confirmed go windows | Integrates with existing crew scheduling; clear commitment to flight date | Medium | Pilots and crew use Google Calendar; event = "this is real, book passengers" signal |
| Group message (WhatsApp/Signal) | Works across Android/iOS/web; doesn't require HA app | Medium | Many crew members don't use Home Assistant; WhatsApp is lingua franca for coordination |
| Historical flight logging + pattern learning (v2) | Learns which conditions actually worked for this crew | Very High | Deferred to v2; needs data; could improve accuracy by 30-50% over time |
| Multi-day look-ahead + firm night-before re-check | Rough planning 2-3 days out, updated forecast 6-12h before launch | Medium | Passengers book in advance; crew needs to tell them "probably yes" or "let's wait"; firm check prevents surprises |
| Condition breakdown rationale | Crew can explain "why no-go" to disappointed passengers | Low | Instead of "weather says no," crew says "wind is too strong (16 km/h, limit 15)" |
| Integration with HA automations | Advanced users can trigger their own actions (light up a "flying day" indicator, etc.) | Low | Sensor entities expose data; users build their own automations |

---

## Anti-Features

**Commonly requested but problematic for this use case.**

| Anti-Feature | Why Requested | Why Problematic | Alternative |
|--------------|---------------|-----------------|-------------|
| Automated "no-go" notification | "Tell us when NOT to fly" seems logical | Noise: 90% of days are no-go; spam kills adoption; silence is golden | Silence = no-go. If crew needs explicit no-go, they can set up HA automation to send one-time alert at day-start |
| ML learning enabled immediately at v1 launch | "Learn from past flights to improve accuracy" sounds smart | Requires 20-50 historical flights to establish meaningful patterns; launching with broken/unreliable learning hurts trust | Defer to v2; collect data at v1; validate patterns in v1.5 beta; ship v2 with learning only after validation |
| Multi-day hour-by-hour forecast display | "Show all possible windows" seems helpful | Decision paralysis: crew sees marginal conditions at 06:30, better at 07:00, worse at 07:30; can't act on all of it; adds cognitive load | Show only 1 recommended window per day; if marginal, highlight all marginal hours but flag only 1 as primary |
| Support unlimited launch sites | "Future-proof for multiple balloons" | Config complexity explodes; most crews run 1-2 sites; adding 10 sites adds 10x thresholds to tune; not worth it yet | Support 2 named sites at v1; v2 revisit if multi-operator coordination required |
| Real-time alerts (minute-by-minute updates) | "Don't miss the window" feels urgent | Creates notification fatigue; window is typically 2-3 hours long; checking every 15 min is noise | Update forecast on 1-3 hour schedule; single notification when good window detected + firm check 6-12h before launch |
| Passenger-facing mobile app | "Crew needs to show passengers the decision" | Out of scope for v1; adds app store management, iOS/Android versioning, push notification infrastructure; Home Assistant already handles notifications | Crew receives notification on their phone; they explain in person. v2: optional public link showing current status |

---

## Feature Dependencies

```
Core:
  Go/No-Go Recommendation
    ├─ Open-Meteo API integration (fetches weather)
    ├─ Wind speed analysis
    ├─ Precipitation analysis
    ├─ Ceiling/cloud analysis
    ├─ Visibility analysis
    └─ Configurable thresholds

Notifications:
  Crew/Pilot Push Notification
    ├─ HA notification service (built-in)
    └─ Good window detection logic

  Group Message (WhatsApp/Signal)
    ├─ HA notification service integration
    └─ Third-party bridge (external dependency, may delay v1)

  Google Calendar Event
    ├─ Google Calendar API integration
    ├─ OAuth setup in config flow
    └─ Good window detection

Display:
  HA Sensor Entities
    ├─ Go/No-Go state
    ├─ Individual condition breakdowns
    └─ DataUpdateCoordinator

  Lovelace Card
    ├─ Sensor entity data via HA frontend API
    ├─ Visual go/no-go display
    └─ Condition detail breakdown

Flight Logging (v2):
  Flight Log Form
    ├─ Lovelace card UI
    └─ Local JSON storage

  Pattern Learning
    ├─ Flight log data
    ├─ Historical recommendation accuracy
    └─ Weighted threshold adjustment (or simple ML)
```

---

## MVP Definition

### Launch With (v1.0)

**Core go-no-go decision + notification:**

1. **Weather Analysis Engine**
   - Fetch Open-Meteo hourly forecast for configurable location
   - Analyze conditions in configurable early-morning window (default 05:00–09:00)
   - Evaluate: wind speed, wind direction stability, ceiling, precipitation, visibility
   - Compare against configurable thresholds
   - Return go/no-go decision with condition breakdown

2. **HA Integration**
   - Config flow: location (lat/lon), thresholds, contact list
   - Sensor entities: `binary_sensor.flynow_go_nogo`, `sensor.flynow_conditions` (JSON breakdown)
   - DataUpdateCoordinator: refresh every 2-3 hours
   - Async throughout, strict mypy/ruff compliance

3. **Lovelace Card**
   - Display go/no-go status (large, clear)
   - Show each condition (wind, ceil, precip, visibility) with current value + threshold
   - Next good window forecast (if any)
   - Time until next check

4. **Push Notification**
   - HA native notification when good window is detected (once per day)
   - Message: "{balloon_name} flying possible 05:00–09:00. Wind {X} km/h, ceiling {Y}m, no rain."

5. **Configuration**
   - Location (select from HA known locations, or manual lat/lon)
   - Thresholds: wind speed, ceiling, precipitation %, visibility
   - Time window (default 05:00–09:00, user-configurable)
   - Notification destinations (push to Home Assistant user accounts)

**NOT in v1:**
- Google Calendar (defer; OAuth flow adds complexity)
- WhatsApp/Signal (defer; requires third-party bridge)
- Flight logging (defer; need data first)
- ML learning (defer; insufficient data)
- Spatial radius analysis (defer to v1.1 if Open-Meteo cost permits)

### Add After Validation (v1.x)

**After one flying season (3-6 months), based on user feedback:**

1. **Google Calendar Integration** (v1.1)
   - Config flow: authorize Google Calendar, select calendar
   - Create event for confirmed good window
   - Event title: "{Balloon} Flying Day"
   - Event time: actual morning window (05:00–09:00)
   - Description: condition summary + link to Lovelace card

2. **Spatial Radius Analysis** (v1.2)
   - Fetch Open-Meteo for multiple points in 100 km radius around launch site
   - Aggregate conditions (min wind, min ceiling, avg precip, etc.)
   - Return more conservative go/no-go (harder to satisfy)
   - Rationale: balloon drifts; landing zone weather matters

3. **WhatsApp/Signal Integration** (v1.2 or v1.3)
   - Depends on available HA automation bridges
   - Send group message when go window detected
   - Message: same as push notification

4. **Flight Logging Form** (v1.3)
   - Lovelace card form: date, time, launch site, outcome (flew/no-fly), duration, notes
   - Store in `/config/flynow_flights.json`
   - Display in card: "Last 5 flights" summary

5. **Second Named Launch Site** (v1.2)
   - Config flow: add second site with independent thresholds
   - Card dropdown: switch between sites
   - Sensor entities per site: `sensor.flynow_site_1_conditions`, `sensor.flynow_site_2_conditions`

### Future Consideration (v2+)

1. **ML Learning from Flight History**
   - Analyze: which weather conditions led to actual successful flights?
   - Adjust thresholds dynamically based on data
   - Requires 30+ historical flights to be meaningful
   - Implement in v2 after v1 data collection

2. **Crew Absence Handling**
   - "If crew member X is on vacation, don't send notification" (optional muting)
   - Season management (Oct–Mar only, user-configurable)
   - Requires expansion of config flow

3. **Real-Time Wind Monitoring**
   - Integrate with weather station (e.g. MQTT sensor in HA)
   - Compare actual wind vs forecast; adjust recommendation
   - Requires HA weather station setup (out of scope for v1)

4. **Public Status Page**
   - Optional: expose read-only Lovelace card view to public link
   - Passengers can check "is today flying?" without app
   - Requires HA public URL + auth handling

5. **Integration with Crew Management System**
   - Sync confirmed flights to crew calendar
   - Send notifications based on crew availability
   - Requires external CRM integration (v2+)

---

## Feature Prioritization Matrix

**Scoring: Importance (1-5) × Complexity Inverse (1-5) ÷ Risk (1-3)**

Higher score = earlier priority.

| Feature | Importance | Complexity | Risk | Score | Priority | Version |
|---------|-----------|-----------|------|-------|----------|---------|
| Go/No-Go recommendation | 5 | 5 (simple) | 1 | 5.0 | **P0** | v1.0 |
| Push notification on good window | 5 | 4 (medium) | 1 | 5.0 | **P0** | v1.0 |
| HA sensor entities | 4 | 5 (simple) | 1 | 4.0 | **P1** | v1.0 |
| Lovelace card display | 4 | 3 (medium) | 1 | 2.7 | **P1** | v1.0 |
| Configurable thresholds | 4 | 3 (medium) | 1 | 2.7 | **P1** | v1.0 |
| Multi-site support | 2 | 2 (medium) | 2 | 1.0 | **P3** | v1.2 |
| Google Calendar event | 3 | 3 (medium) | 2 | 1.5 | **P2** | v1.1 |
| Spatial radius analysis | 4 | 1 (complex) | 2 | 2.0 | **P2** | v1.2 |
| WhatsApp/Signal message | 3 | 2 (medium) | 2 | 1.5 | **P2** | v1.2+ |
| Flight logging form | 2 | 2 (medium) | 1 | 1.0 | **P3** | v1.3 |
| ML learning | 2 | 1 (complex) | 3 | 0.7 | **P4** | v2.0 |

---

## User Research Context

Based on PROJECT.md and CLAUDE.md domain notes:

**User Profile:**
- Balloon crew (not pilot) coordinating with one pilot
- Both commercial (passenger) and recreational flights
- Location: Slovakia, using OM-0007 and OM-0008 balloons
- Current pain: Checking 5+ apps (Windy, Meteoblue, etc.), pilot decides alone, good windows missed, no clear explanation for passengers

**Success Metrics (from PROJECT.md):**
- One shared go-no-go answer (not crew + pilot checking separately)
- Crew receives notification automatically (not "I should check the app today")
- Clear rationale to explain no-go to passengers
- Decision window respected: rough check 2-3 days out, firm check 6-12h before

**Decision Cadence:**
- Rough planning: 2-3 days in advance (forecast may shift)
- Firm decision: night before (final forecast + commitment to crew/passengers)
- Go window: early morning (05:00–09:00 typical, depends on season)

---

## Notable Gaps in This Research

Due to WebSearch/WebFetch restrictions, unable to verify:

1. **Competitor Feature Audit** — What exact features do Windy, SkySight, XCSkies, UAVforecast display? MEDIUM priority: would confirm whether spatial radius is truly a differentiator or table stakes.

2. **Home Assistant Notification Ecosystem** — Exact state of WhatsApp/Signal bridges in HA. May be available as built-in service or require third-party MQTT setup. MEDIUM priority: affects v1.1 timeline.

3. **Open-Meteo API Capabilities** — Exact parameters available (cloud layers, wind shear at altitude, thermal stability indices). HIGH priority: directly affects feature feasibility. **Recommend phase-specific research before v1 implementation starts.**

4. **Balloon Operating Practices** — Exact FAA/EASA/Slovak regulations on wind speed, ceiling, visibility minimums. Training data suggests thresholds but not authoritative sources. MEDIUM priority: thresholds should be validated with actual pilots before shipping.

5. **Historical Flight Data Volume** — How quickly can typical balloon crew collect 30-50 flights? Affects v2 ML learning timeline. LOW priority: track during v1 to inform v2 planning.

---

## Recommendations for Roadmap

**Phase 1 (v1.0 Launch):**
- Implement core go/no-go logic with configurable thresholds
- Push notification when good window detected
- HA sensor entities + basic Lovelace card
- **Research gate before implementation:** Verify Open-Meteo parameter availability + confirm wind/ceiling/visibility thresholds with actual pilot

**Phase 2 (v1.x Expansion):**
- Google Calendar integration (likely v1.1)
- Spatial radius analysis (if Open-Meteo cost permits; likely v1.2)
- WhatsApp/Signal (depends on HA notification ecosystem; likely v1.2+)
- Second launch site support (v1.2)

**Phase 3 (v2 + ML):**
- Flight logging + historical analysis
- Threshold learning (after 1 flying season of data collection)
- Crew management integrations (future, lower priority)

---

## Sources

**Training Data:**
- Hot air balloon flight operations, FAA/EASA general knowledge
- Home Assistant integration patterns, Lovelace card architecture
- Weather API capabilities (Open-Meteo, OpenWeatherMap general knowledge)

**Project-Specific Context:**
- CLAUDE.md (FlyNow architecture, constraints, domain notes)
- PROJECT.md (user pain points, requirements, out-of-scope decisions)

**Notes:**
- Research constrained by WebSearch/WebFetch blocking; findings flagged as MEDIUM confidence where verification unavailable
- Phase 1 implementation should include research gate for Open-Meteo parameter verification
- Recommend contacting actual balloon pilots (OM-0007/OM-0008 operators) to validate wind/ceiling/visibility thresholds before shipment
