# Requirements: FlyNow

**Defined:** 2026-04-16
**Core Value:** One shared go/no-go answer that crew and pilot both receive automatically — so nobody has to check five weather apps or call each other to decide.

## v1 Requirements

### Weather Analysis

- [ ] **WEATHER-01**: System fetches hourly Open-Meteo forecast for a configured launch location (lat/lon)
- [ ] **WEATHER-02**: System analyzes wind at surface (10m) and at balloon operating altitude (600–1000m AGL) using pressure-level data
- [ ] **WEATHER-03**: System analyzes cloud ceiling, precipitation probability, and visibility
- [ ] **WEATHER-04**: All go/no-go thresholds are configurable by the crew (not hard-coded defaults)
- [ ] **WEATHER-05**: Conditions are analyzed across the full flight window (60–90 min duration), not just launch moment

### Time Windows

- [ ] **TIME-01**: System calculates sunrise and sunset times for the launch location on a given date
- [ ] **TIME-02**: Evening window: latest launch = sunset minus flight duration (60–90 min) minus prep time (~30 min); must land before sunset
- [ ] **TIME-03**: Morning window: earliest launch = sunrise plus prep time (~30 min); cannot start before sunrise
- [ ] **TIME-04**: Both morning and evening windows are evaluated; evening is the primary use case

### Forecast Look-Ahead

- [ ] **FORE-01**: System provides a rough 2–3 day look-ahead (is Thursday evening flyable?)
- [ ] **FORE-02**: System provides a firm go/no-go check for the next flight window (night-before decision)

### Home Assistant Integration

- [ ] **HA-01**: Config flow UI for setup: launch location, go/no-go thresholds, flight duration, notification contacts
- [ ] **HA-02**: Sensor entities expose: go/no-go status, active window type (morning/evening/none), condition breakdown (wind surface, wind altitude, ceiling, precip, visibility), calculated launch window times
- [ ] **HA-03**: DataUpdateCoordinator refreshes forecast data every 30–60 minutes

### Notifications

- [ ] **NOTIF-01**: HA push notification sent to crew and pilot phones when a flyable window is detected (GO only — silence = no-go)
- [ ] **NOTIF-02**: Google Calendar event created for confirmed good windows, showing calculated launch time and window duration
- [ ] **NOTIF-03**: WhatsApp or Signal group message sent with go/no-go decision and key condition summary
- [ ] **NOTIF-04**: Deduplication: no repeat notification for the same window within 1 hour

### Lovelace Card

- [x] **CARD-01**: Card displays today's evening window and tomorrow's morning window with clear GO/NO-GO status
- [x] **CARD-02**: Card shows condition breakdown: surface wind, altitude wind, ceiling, precipitation, visibility — each with threshold comparison
- [x] **CARD-03**: Card shows calculated launch window times (e.g. "Launch by 18:30 — Sunset 20:15")

### Flight Logging

- [ ] **LOG-01**: Lovelace card includes a form to log a completed flight: date, balloon (OM-0007 / OM-0008), launch time, flight duration, launch site, outcome, notes
- [ ] **LOG-02**: Flight logs stored locally in HA config directory (`/config/flynow_flights.json`) with atomic writes

## v2 Requirements

### Spatial Analysis

- **SPATIAL-01**: Analyze conditions across ~100 km radius around launch site using multi-point Open-Meteo queries
- **SPATIAL-02**: Aggregate radius results (min wind, min ceiling, avg precipitation) for a conservative go/no-go

### Learning from Flight History

- **LEARN-01**: System analyzes logged flight history (after 30+ flights) to identify which conditions correlated with good/bad outcomes
- **LEARN-02**: Weighted threshold adjustment based on historical outcome patterns per launch site

### Advanced Notifications

- **NOTIF-V2-01**: Explicit no-go notification option (for users who want confirmation, not just silence)
- **NOTIF-V2-02**: Weekly summary of upcoming flyable windows (Monday morning forecast digest)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-pilot / fleet management | Built for one crew + one pilot; not a SaaS product |
| Paid weather APIs | Open-Meteo free tier covers the use case fully |
| Passenger vs. fun flight threshold differentiation | Crew confirmed: same limits apply to both |
| Different thresholds per balloon (OM-0007 vs OM-0008) | One team, same conditions, same thresholds |
| Automated no-go alert (explicit message) | Silence = no-go is the agreed convention; explicit no-go adds noise |
| ML learning in v1 | Insufficient flight data at launch; deferred until data validates approach |
| Real-time weather station integration | Open-Meteo forecast sufficient; live station data adds complexity without clear v1 value |
| Web app or mobile app | Home Assistant integration is the right fit for the user's setup |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| WEATHER-01 | Phase 1 | Pending |
| WEATHER-02 | Phase 1 | Pending |
| WEATHER-03 | Phase 1 | Pending |
| WEATHER-04 | Phase 1 | Pending |
| WEATHER-05 | Phase 1 | Pending |
| TIME-01 | Phase 1 | Pending |
| TIME-02 | Phase 1 | Pending |
| TIME-03 | Phase 1 | Pending |
| TIME-04 | Phase 1 | Pending |
| FORE-01 | Phase 1 | Pending |
| FORE-02 | Phase 1 | Pending |
| HA-01 | Phase 1 | Pending |
| HA-02 | Phase 1 | Pending |
| HA-03 | Phase 1 | Pending |
| NOTIF-01 | Phase 2 | Pending |
| NOTIF-02 | Phase 2 | Pending |
| NOTIF-03 | Phase 2 | Pending |
| NOTIF-04 | Phase 2 | Pending |
| CARD-01 | Phase 2 | Complete |
| CARD-02 | Phase 2 | Complete |
| CARD-03 | Phase 2 | Complete |
| LOG-01 | Phase 3 | Pending |
| LOG-02 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 23 total
- Mapped to phases: 23 ✓
- Unmapped: 0 ✓

---

*Requirements defined: 2026-04-16*
*Roadmap created: 2026-04-16*
*Last updated: 2026-04-16 after roadmap creation*
