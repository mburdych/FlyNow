# Architecture Research: Home Assistant Custom Integration

**Domain:** Home Assistant custom integration with external API, async data processing, and multi-channel notifications
**Researched:** 2026-04-16
**Confidence:** MEDIUM (based on HA conventions and established patterns; verification needed against current HA 2026 versions)

## Standard HA Integration Architecture

Home Assistant integrations follow a standardized component structure. All integrations are domain-based packages in `custom_components/{domain}/` with these core files:

```
custom_components/flynow/
├── __init__.py              # Integration lifecycle (setup_entry, unload_entry)
├── manifest.json            # Metadata, dependencies, version
├── const.py                 # Constants (domain, config keys, defaults)
├── config_flow.py           # UI-based configuration form
├── coordinator.py           # DataUpdateCoordinator (data fetch + analysis)
├── sensor.py                # Sensor entities (expose data to HA)
├── strings.json             # Localizable UI strings (config flow, entity names)
├── py.typed                 # Marks package for strict mypy typing
└── translations/
    └── en.json              # English translations (optional, recommended)
```

### Component Responsibilities

| Component | Purpose | Key Patterns |
|-----------|---------|--------------|
| **manifest.json** | Integration metadata, version, requirements, HA version constraint | Declares home_assistant version, required_version, dependencies (aiohttp), HACS config |
| **__init__.py** | Setup/teardown lifecycle, config entry handling | `async_setup_entry()`, `async_unload_entry()`, store coordinator in `hass.data` |
| **const.py** | Constants, default thresholds, domain name | DOMAIN = "flynow", CONF_LOCATION, CONF_LATITUDE, CONF_LONGITUDE, DEFAULT_SCAN_INTERVAL |
| **config_flow.py** | User-facing setup UI with validation | Multi-step form for location, timezone, thresholds, API keys, notification contacts |
| **coordinator.py** | DataUpdateCoordinator subclass | Async fetch from Open-Meteo, call analysis engine, update interval, error handling |
| **sensor.py** | Sensor entity classes | BaseCoordinatorEntity subclass for each sensor (go_no_go, wind_speed, ceiling, etc.) |
| **strings.json** | UI text (config flow steps, entity names, option keys) | i18n strings for forms, entity descriptions, field labels |

## Recommended Project Structure

```
FlyNow/
├── .planning/
│   ├── PROJECT.md
│   └── research/
│       └── ARCHITECTURE.md (this file)
├── custom_components/
│   └── flynow/
│       ├── __init__.py
│       ├── manifest.json
│       ├── const.py
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── sensor.py
│       ├── py.typed
│       ├── strings.json
│       ├── strings/
│       │   └── en.json
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── analyzer.py         # Go/no-go logic (wind, ceiling, shear, etc.)
│       │   └── open_meteo.py       # Open-Meteo API client
│       ├── notifications/
│       │   ├── __init__.py
│       │   ├── pusher.py           # Trigger HA push notifications
│       │   ├── calendar.py         # Google Calendar integration
│       │   └── messaging.py        # WhatsApp/Signal if needed
│       ├── storage/
│       │   ├── __init__.py
│       │   └── flight_log.py       # Flight log I/O
│       └── tests/
│           ├── conftest.py         # pytest fixtures
│           ├── test_init.py        # Integration setup tests
│           ├── test_coordinator.py # Coordinator fetch/update tests
│           ├── test_analyzer.py    # Analysis logic tests
│           └── test_config_flow.py # Config flow validation tests
├── lovelace/
│   └── flynow-card/
│       ├── package.json
│       ├── tsconfig.json
│       ├── rollup.config.js        # Build configuration
│       ├── src/
│       │   ├── index.ts            # Card entry point
│       │   ├── flynow-card.ts      # Main card component
│       │   ├── styles.css
│       │   └── types.ts            # TypeScript interfaces
│       ├── dist/                   # Compiled output
│       └── README.md               # Card documentation
├── manifest.json                   # HACS package manifest
├── README.md                       # Project README
├── hacs.json                       # HACS registration (integration + card)
└── requirements.txt                # Python dev dependencies (optional, for development)
```

## Architectural Patterns

### Pattern 1: DataUpdateCoordinator for Multi-Step Data Pipeline

**Purpose:** Centralize async data fetching, parsing, analysis, and coordinate updates across all sensor entities.

**Structure:**
```python
# coordinator.py
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class FlyNowCoordinator(DataUpdateCoordinator):
    """Coordinator for FlyNow weather analysis."""
    
    def __init__(self, hass, config_entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),  # Refresh every hour
        )
        self.config_entry = config_entry
        self.api_client = OpenMeteoClient()
        self.analyzer = BalloonConditionAnalyzer()
    
    async def _async_update_data(self):
        """Fetch data from Open-Meteo and analyze."""
        try:
            # Step 1: Fetch weather from Open-Meteo
            weather_data = await self.api_client.fetch_forecast(
                latitude=self.config_entry.data[CONF_LATITUDE],
                longitude=self.config_entry.data[CONF_LONGITUDE],
            )
            
            # Step 2: Analyze conditions using configured thresholds
            analysis = self.analyzer.analyze(
                weather_data=weather_data,
                thresholds=self._load_thresholds(),
                time_window=(5, 9),  # Morning window
            )
            
            # Step 3: Trigger notifications if good conditions
            await self._trigger_notifications(analysis)
            
            return analysis
        except Exception as err:
            raise UpdateFailed(f"Error fetching/analyzing weather: {err}") from err
    
    async def _trigger_notifications(self, analysis):
        """Side effect: notify crew/pilot if conditions are good."""
        if analysis["recommendation"] == "GO":
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {"title": "FlyNow: Good conditions!", "message": analysis["summary"]}
            )
```

**Key points:**
- Coordinator lives in memory across Home Assistant restarts (data is not persisted)
- `_async_update_data()` runs at configured `update_interval`; failures are caught and logged
- All entities subscribe to coordinator updates via `async_add_coordinator_update_listener()`
- Coordinator handles retry logic, rate limiting, and error states

**Why this matters for FlyNow:**
- Multi-step pipeline: fetch → analyze → notify
- Shared data source for all sensors (wind, ceiling, go/no-go status)
- Single point of control for update scheduling and error handling

### Pattern 2: Sensor Entities for Computed Values

**Purpose:** Expose go/no-go analysis results as Home Assistant sensor entities.

**Structure:**
```python
# sensor.py
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

async def async_setup_entry(hass, entry, async_add_entities: AddEntitiesCallback):
    """Set up sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        GoNoGoSensor(coordinator, entry),
        WindSpeedSensor(coordinator, entry),
        CeilingSensor(coordinator, entry),
        WindShearSensor(coordinator, entry),
    ])

class GoNoGoSensor(CoordinatorEntity, SensorEntity):
    """Go/no-go recommendation sensor."""
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_go_no_go_{entry.entry_id}"
        self._attr_name = "Go / No-Go"
        self._attr_icon = "mdi:check-circle" if self.is_on else "mdi:close-circle"
    
    @property
    def native_value(self):
        """Return current recommendation: 'GO' or 'NO-GO'."""
        return self.coordinator.data.get("recommendation")
    
    @property
    def extra_state_attributes(self):
        """Return detailed condition breakdown."""
        return {
            "wind_speed": self.coordinator.data.get("wind_speed"),
            "ceiling": self.coordinator.data.get("ceiling"),
            "precipitation": self.coordinator.data.get("precipitation"),
            "next_good_window": self.coordinator.data.get("next_good_window"),
        }
```

**Key points:**
- `CoordinatorEntity` automatically subscribes to coordinator updates
- `native_value` property returns the sensor's primary value
- `extra_state_attributes` provide detailed breakdowns (accessible in HA UI and automations)
- Entity naming follows HA conventions: lowercase, underscores, unique_id must be globally unique

**Why this matters for FlyNow:**
- Go/no-go status is a computed value (not raw data)
- Multiple sensors expose different aspects of the analysis
- Conditions are included as attributes for Lovelace card display

### Pattern 3: Config Flow for Multi-Field Configuration

**Purpose:** UI-based setup with validation, handling location, thresholds, and notification contacts.

**Structure:**
```python
# config_flow.py
from homeassistant.config_entries import ConfigFlow, ConfigEntry
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

class FlyNowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for FlyNow."""
    
    VERSION = 1
    CONNECTION_CLASS = "cloud_poll"  # Data fetched via external API
    
    async def async_step_user(self, user_input=None) -> FlowResult:
        """Initial setup: location and site name."""
        errors = {}
        if user_input is not None:
            # Validate location is valid
            try:
                await self._validate_location(user_input)
            except ValueError as err:
                errors["base"] = "invalid_location"
            else:
                self.location_data = user_input
                return await self.async_step_thresholds()
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_LATITUDE): cv.latitude,
                vol.Required(CONF_LONGITUDE): cv.longitude,
                vol.Optional(CONF_TIMEZONE, default="Europe/Bratislava"): str,
            }),
            errors=errors,
        )
    
    async def async_step_thresholds(self) -> FlowResult:
        """Configure go/no-go thresholds."""
        if self.show_advanced_options:
            schema = vol.Schema({
                vol.Optional(CONF_MAX_WIND_SPEED, default=15): cv.positive_int,
                vol.Optional(CONF_MIN_CEILING, default=500): cv.positive_int,
                vol.Optional(CONF_MAX_PRECIPITATION, default=10): cv.positive_int,
                vol.Optional(CONF_MAX_WIND_SHEAR, default=5): cv.positive_float,
            })
        else:
            # Skip advanced options
            return self.async_create_entry(
                title=self.location_data[CONF_NAME],
                data={**self.location_data, **DEFAULT_THRESHOLDS}
            )
        
        if user_input is not None:
            return self.async_create_entry(
                title=self.location_data[CONF_NAME],
                data={**self.location_data, **user_input}
            )
        
        return self.async_show_form(step_id="thresholds", data_schema=schema)
    
    async def async_step_init(self, user_input=None) -> FlowResult:
        """Options flow: allow updating thresholds after setup."""
        if user_input is not None:
            return self.async_abort(reason="reconfigure_successful")
        
        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Optional(CONF_MAX_WIND_SPEED): cv.positive_int,
            vol.Optional(CONF_MIN_CEILING): cv.positive_int,
        }))
```

**Key points:**
- Multi-step flow allows progressive disclosure (basic setup → advanced options)
- Validators (cv.latitude, cv.longitude) catch invalid input
- `async_step_init()` allows users to change options after initial setup
- Defaults make basic setup fast for new users

**Why this matters for FlyNow:**
- Users configure location, timezone, and threshold limits (wind, ceiling, shear)
- Advanced users can customize; basic users get sensible defaults
- Options flow allows tweaking thresholds without reinstalling

### Pattern 4: Lovelace Card Build Pipeline

**Purpose:** Package TypeScript component as HACS-installable frontend resource.

**Structure:**

```bash
# File: lovelace/flynow-card/package.json
{
  "name": "flynow-card",
  "version": "1.0.0",
  "description": "Home Assistant Lovelace card for FlyNow balloon condition advisor",
  "main": "dist/flynow-card.js",
  "scripts": {
    "build": "rollup -c",
    "watch": "rollup -c -w",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.0",
    "@types/node": "^18.0",
    "lit": "^2.8",
    "rollup": "^3.0",
    "@rollup/plugin-typescript": "^11.0",
    "home-assistant-js-websocket": "^8.0"
  },
  "dependencies": {
    "lit": "^2.8"
  }
}
```

```typescript
// File: lovelace/flynow-card/src/flynow-card.ts
import { LitElement, html, css } from "lit";
import { customElement, property, state } from "lit/decorators.js";

@customElement("flynow-card")
export class FlyNowCard extends LitElement {
  @property({ attribute: false }) hass!: HomeAssistant;
  @property() config?: CardConfig;
  @state() recommendation: string = "";
  @state() conditions: ConditionBreakdown = {};

  setConfig(config: CardConfig): void {
    this.config = config;
  }

  render() {
    if (!this.hass || !this.config) return html`<p>Loading...</p>`;

    const recommendation = this.hass.states[this.config.entity_id];
    const status = recommendation?.state || "unknown";

    return html`
      <ha-card>
        <div class="card-content">
          <h2>FlyNow Weather Check</h2>
          <div class="status ${status}">
            <div class="icon">${this._renderIcon(status)}</div>
            <div class="text">${status === "GO" ? "Good to fly!" : "Not ideal conditions"}</div>
          </div>
          <div class="details">
            ${this._renderConditions(recommendation?.attributes || {})}
          </div>
          <div class="flight-log">
            <button @click=${this._openFlightLog}>Log Flight</button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderIcon(status: string) {
    return html`
      <ha-icon icon=${status === "GO" ? "mdi:check-circle" : "mdi:close-circle"}></ha-icon>
    `;
  }

  private _renderConditions(attrs: any) {
    return html`
      <div class="condition">
        <span>Wind:</span> <span>${attrs.wind_speed || "—"} km/h</span>
      </div>
      <div class="condition">
        <span>Ceiling:</span> <span>${attrs.ceiling || "—"} m</span>
      </div>
    `;
  }

  static get styles() {
    return css`
      .card-content {
        padding: 16px;
      }
      .status {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px;
        border-radius: 4px;
        margin: 12px 0;
      }
      .status.GO {
        background-color: #c8e6c9;
      }
      .status.NO_GO {
        background-color: #ffcdd2;
      }
    `;
  }
}
```

**Build process:**
```bash
# package.json scripts
npm run build      # Compile TS to single JS file in dist/
npm run watch      # Hot reload during development
npm run lint       # Check code style
```

**HACS registration:**
```json
{
  "name": "FlyNow Card",
  "render_readme": true,
  "homeassistant": "2025.1.0",
  "filename_regex": "^(?!-)",
  "javascript_url": "/local/community/flynow-card/dist/flynow-card.js",
  "resources": [
    {
      "url": "/local/community/flynow-card/dist/flynow-card.js",
      "type": "js_module"
    }
  ]
}
```

**Key points:**
- lit-element provides lightweight component framework
- Rollup bundles TypeScript into single JS file
- Custom element extends `LitElement` and registers with `@customElement`
- HACS serves compiled JS from `/local/community/` path
- Card receives hass object and entity state automatically

**Why this matters for FlyNow:**
- Card displays go/no-go status with wind/ceiling/precipitation details
- Flight log form embedded in card for quick logging
- Single-file distribution via HACS

## Data Flow

### Request-Response Cycle (Hourly Update)

```
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant Update Interval (DataUpdateCoordinator)       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ OpenMeteoClient.fetch_forecast(lat, lon)                    │
│ → GET https://api.open-meteo.com/v1/forecast                │
│   - Hourly wind speed, direction, gust, cloud ceiling       │
│   - Wind at 10m, 80m, 120m altitude                         │
│   - Precipitation probability                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ BalloonConditionAnalyzer.analyze(weather, thresholds)       │
│ → Filter to morning window (05:00–09:00)                    │
│ → Score each hour:                                          │
│   - Wind speed ≤ threshold? ✓/✗                            │
│   - Wind shear ≤ threshold? ✓/✗                            │
│   - Cloud ceiling ≥ threshold? ✓/✗                         │
│   - Precipitation < threshold? ✓/✗                         │
│ → Return best window + all-conditions summary               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Coordinator.data ← analysis result                          │
│ {                                                            │
│   "recommendation": "GO",                                   │
│   "best_window": "05:30–07:30",                             │
│   "wind_speed": 8,                                          │
│   "ceiling": 1200,                                          │
│   "precipitation": 0,                                       │
│   "wind_shear": 3                                           │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
            ┌───────────────┬───────────────┐
            ↓               ↓               ↓
    ┌───────────────┐ ┌──────────────┐ ┌────────────────────┐
    │ All Sensors   │ │ Notification │ │ Lovelace Card      │
    │ Updated:      │ │ Service Call │ │ Refreshes (via WS) │
    │ - GoNoGo      │ │ (if GO)       │ │                    │
    │ - Wind        │ │ persistent_   │ │ Shows status,      │
    │ - Ceiling     │ │ notification, │ │ conditions, next   │
    │ - Shear       │ │ calendar,     │ │ good window        │
    │               │ │ messaging API │ │                    │
    └───────────────┘ └──────────────┘ └────────────────────┘
```

### Configuration Setup (One-Time)

```
┌──────────────────────────────┐
│ User in HA UI:               │
│ Settings → Devices & Services│
│ → Create Integration         │
└──────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────┐
│ config_flow.async_step_user()                    │
│ - Ask for location (lat/lon)                     │
│ - Ask for site name, timezone                    │
└──────────────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────┐
│ config_flow.async_step_thresholds()              │
│ - Ask for wind limit, ceiling limit              │
│ - Ask for shear limit, precipitation limit       │
│ - Offer "use defaults" skip option               │
└──────────────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────┐
│ ConfigEntry created + stored in                  │
│ .config/flynow/entry.json (managed by HA)        │
└──────────────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────┐
│ __init__.async_setup_entry()                     │
│ - Create coordinator                             │
│ - Store in hass.data[DOMAIN]                     │
│ - Register sensor platform                       │
└──────────────────────────────────────────────────┘
            ↓
┌──────────────────────────────────────────────────┐
│ Sensors created + subscribed to coordinator      │
│ Coordinator starts hourly update cycle           │
└──────────────────────────────────────────────────┘
```

## Integration Points

| System | Purpose | Implementation | Notes |
|--------|---------|-----------------|-------|
| **Open-Meteo API** | Weather forecast | AsyncHTTPClient (aiohttp) | Free, no key, 100 km radius sampling |
| **HA Persistent Notification** | Good-window alert | `hass.services.async_call()` | Built-in, requires no setup |
| **Google Calendar API** | Event creation | Separate async client, Google credentials | Optional; requires OAuth setup |
| **WhatsApp/Signal API** | Crew messaging | Twilio or similar bridge | Optional; requires API key + phone setup |
| **HA Sensor Platform** | Expose data to automations | `CoordinatorEntity` subclass | Built-in, no external dependency |
| **Lovelace WebSocket** | Card real-time updates | HA provides `hass` object to card | Built-in, automatic subscription |
| **HA File System** | Flight log storage | `hass.config.path()` + asyncio file I/O | `/config/flynow_flights.json` |

## Suggested Build Order

This ordering reflects dependency relationships and minimizes rework:

### Phase 1: Core Integration Structure
**Goal:** Get basic HA integration working, coordinator fetching weather, sensor entities exposing data.

**What to build:**
1. `manifest.json` — Declare version, dependencies (aiohttp)
2. `const.py` — Domain, config keys, defaults
3. `__init__.py` — Integration lifecycle, store coordinator
4. `config_flow.py` — Location + basic thresholds config
5. `coordinator.py` — Open-Meteo client, basic fetch
6. `analysis/open_meteo.py` — API client (separate from coordinator for testability)
7. `analysis/analyzer.py` — Scoring logic (wind, ceiling, shear, precipitation)
8. `sensor.py` — Sensor entities (go/no-go, wind, ceiling, shear)
9. `strings.json` — UI labels

**Why this order:**
- Coordinator depends on config (config_flow must exist first)
- Sensors depend on coordinator (must be ready to consume data)
- API client separated early for testability
- Analyzer logic testable independently of HA

**Test coverage:**
- Unit tests for analyzer (inputs → recommendation)
- Unit tests for API client (mock responses)
- Integration tests for coordinator + sensors (mock Open-Meteo)
- Config flow tests (validation)

**Outcome:** Users can install, configure location, and see go/no-go status + condition breakdown.

### Phase 2: Notifications
**Goal:** Trigger alerts when good conditions appear.

**What to build:**
1. `notifications/pusher.py` — Call HA persistent_notification service
2. `notifications/calendar.py` — Google Calendar event creation (optional for v1)
3. `notifications/messaging.py` — WhatsApp/Signal integration (optional for v1)
4. `coordinator.py` update — Call notification methods on good window

**Why this phase:**
- Depends on Phase 1 (coordinator + analysis must work first)
- Notifications are side effects; core feature is condition analysis
- Can defer WhatsApp/Signal to later release if time-constrained

**Test coverage:**
- Mock notification service calls
- Verify notifications only trigger on GO conditions
- Test notification templates (message formatting)

**Outcome:** Crew and pilot receive alerts automatically when conditions improve.

### Phase 3: Lovelace Card
**Goal:** Display analysis with flight log form.

**What to build:**
1. `lovelace/flynow-card/` — TypeScript component
2. Build pipeline — rollup, npm scripts
3. Card UI — status display, condition details, flight log form
4. `hacs.json` — HACS registration

**Why this phase:**
- Depends on Phase 1 sensors (card displays their data)
- Independent of Phase 2 (notifications work separately)
- Can iterate quickly on UI without touching backend

**Test coverage:**
- Visual regression tests (if using tools like Percy)
- Unit tests for card logic (attribute parsing, condition rendering)

**Outcome:** Users can see a polished view of conditions and log flights from one card.

### Phase 4: Flight Log Storage & Analysis (v1+ Stretch)
**Goal:** Store completed flights, prepare for future ML.

**What to build:**
1. `storage/flight_log.py` — JSON read/write with async file I/O
2. Config flow update — contacts for notification (optional)
3. Card update — flight log form submission

**Why this phase:**
- Depends on Phase 1 (core features must be solid first)
- Stretch goal; can be deferred if time-constrained
- Data collection enables Phase 2 ML/learning

**Test coverage:**
- File I/O edge cases (missing file, permission errors)
- JSON schema validation
- Async race conditions

**Outcome:** Flight logs collected in HA config dir for future analysis.

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **DataUpdateCoordinator for fetch+analyze** | Single source of truth for data; automatic retry + error handling; all sensors subscribe to one source |
| **Async throughout** | HA requirement; ensures responsiveness during network delays |
| **Config flow multi-step** | Basic users get defaults; advanced users can customize without overwhelming UI |
| **Open-Meteo over paid APIs** | Free, no key, good European coverage, meets requirements |
| **Coordinator side effect for notifications** | Keeps logic close to data; simpler than HA automations for this use case |
| **Separate analyzer module** | Testable independent of HA; easy to iterate on scoring logic |
| **Sensor entities for computed go/no-go** | Enables automations, templating, multi-card dashboards in HA |
| **Lovelace card in TypeScript** | Standard HACS pattern; lit-element is lightweight |
| **Flight logs in JSON (not SQLite)** | Simpler for v1; SQLite can be added later if needed |

## Sources & Confidence Notes

**HIGH CONFIDENCE:**
- Home Assistant integration architecture (manifest, __init__, config_flow structure) — established since HA 0.100+, stable patterns
- DataUpdateCoordinator patterns — standard in modern HA integrations (2021+)
- Sensor entity lifecycle — documented and consistent
- Async/await requirement — enforced in HA 0.99+

**MEDIUM CONFIDENCE:**
- Specific config_flow validation library (voluptuous) — widely used but could change
- Lovelace card build pipeline (rollup, lit-element) — community standard but not officially documented by HA
- HACS registration paths — based on community conventions

**LOW CONFIDENCE:**
- Exact Open-Meteo API format for wind shear, ceiling data — needs verification against current API docs
- Google Calendar API integration complexity — depends on current OAuth flow
- WhatsApp/Signal integration approach — may require third-party bridge (Twilio, custom webhook)

**Recommendations for verification:**
1. Verify Open-Meteo API format before Phase 1 implementation — check https://open-meteo.com/en/docs/
2. Check latest HA developer docs (https://developers.home-assistant.io/) for config_flow validation changes
3. Review 2–3 HACS integrations of similar scope (data fetch + sensor + notification) to confirm patterns
4. Prototype Google Calendar integration separately before incorporating into coordinator
5. Test async file I/O in HA context before Phase 4 (race conditions possible with config reloads)

