# Stack Research: Home Assistant Custom Integration + Lovelace Card

**Domain:** Home Assistant custom integration + Lovelace card (hot air balloon weather)  
**Researched:** 2026-04-16  
**Confidence:** HIGH (based on HA 2025.x standards, established patterns, training data current through Feb 2025)

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|-----------|---------|---------|-----------------|
| Python | 3.12+ | HA integration runtime | HA core requires 3.12+; async/await support mature; type hints excellent |
| Home Assistant | 2025.1+ | Base platform | Use latest stable release; integration standards refined; DataUpdateCoordinator well-established |
| aiohttp | 3.9+ | Async HTTP client | Standard in HA integrations; efficient async; Open-Meteo API calls |
| TypeScript | 5.3+ | Lovelace card language | Type-safe frontend; lit-html integration smooth; HA community standard |
| LitElement | 4.0+ | Web component framework | Preferred HA Lovelace pattern; lit-html based; smaller bundle than React/Vue |

### Python Integration Stack

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `homeassistant` (core) | 2025.1+ | Integration framework | Required; provides EntityPlatform, DataUpdateCoordinator, config_entries |
| `aiohttp` | 3.9+ | HTTP client | Open-Meteo weather API calls; built-in HA standard |
| `pydantic` | 2.4+ | Data validation | Config validation, weather data parsing; HA standard |
| `python-dateutil` | 2.8+ | Datetime handling | Timezone-aware forecast analysis; already in HA |
| `async-timeout` | 4.0+ | Timeout management | API call timeouts; already in HA deps |

### Lovelace Frontend Stack

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `lit-html` | 3.1+ | Template rendering | Lovelace standard; no virtual DOM overhead; embedded in LitElement |
| `@lit/reactive-element` | 2.0+ | Base class (part of LitElement) | Reactive property updates; standard HA card pattern |
| `TypeScript` | 5.3+ | Language | Type-safe card code; compile to ES2020+ for HA compatibility |

### Build & Tooling (Lovelace Card)

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| `esbuild` | 0.20+ | JavaScript bundler | Fast, HA-endorsed; outputs ES2020; minimal config |
| `typescript` | 5.3+ | Compiler | Type checking; strict mode required for HA HACS |
| `npm` or `pnpm` | Latest | Package manager | npm standard; pnpm faster for large monorepos |

### Development & Testing

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| `pytest` | 7.4+ | Python test framework | HA standard for integration tests |
| `pytest-homeassistant-custom-component` | Latest | HA test fixtures | Provides mock hass, config_entries, async fixtures |
| `ruff` | 0.1+ | Python linter | HA required; ~50x faster than flake8; check + format in one tool |
| `mypy` | 1.7+ | Static type checker | HA requires strict mode; catches integration bugs early |
| `pre-commit` | 3.5+ | Git hook runner | Enforce ruff + mypy before commit; standard HA workflow |

### Configuration & Schema

| Component | Purpose | Details |
|-----------|---------|---------|
| `manifest.json` | Integration metadata | Required; specifies HA version, domain, dependencies, requirements |
| `config_flow.py` | UI-based configuration | Step-based flow for location, API keys, thresholds, contacts |
| `const.py` | Constants & defaults | Domain, config keys, weather thresholds, alert window times |
| `strings.json` | Translatable text | Config flow labels, entity descriptions, notification templates |

## Open-Meteo API Endpoints

For balloon weather analysis, use these Open-Meteo endpoints:

| Endpoint | Parameters | Use Case |
|----------|-----------|----------|
| `/forecast` | `latitude`, `longitude`, `hourly` (wind_speed_10m, wind_direction_10m, wind_speed_100m, wind_direction_100m, cloud_cover, ceiling, precipitation, visibility) | Primary weather fetch; hourly resolution |
| Wind layers | `wind_speed_10m`, `wind_speed_100m`, `wind_speed_200m` | Detect wind shear (surface vs altitude); balloons sensitive to shear |
| Cloud cover & ceiling | `cloud_cover`, `ceiling` | Go/no-go threshold: good ceiling (>1500m), low cloud cover |
| Precipitation | `precipitation`, `precipitation_probability` | Abort if >20% rain probability |
| Visibility | `visibility` | Require >5km (daylight balloon ops) |

**Example request:**
```
GET https://api.open-meteo.com/v1/forecast
?latitude=48.5&longitude=19.1
&hourly=wind_speed_10m,wind_direction_10m,wind_speed_100m,ceiling,cloud_cover,precipitation,visibility
&timezone=Europe/Bratislava
&forecast_days=3
```

**Rationale:** Open-Meteo returns wind at multiple altitudes in one call — critical for detecting shear. No API key required. Covers Slovakia with 11km resolution. Hourly granularity matches early-morning window analysis (05:00–09:00 local).

## Messaging Integration Options

### WhatsApp

| Option | Approach | Trade-offs |
|--------|----------|-----------|
| **CallMeBot** (Recommended) | HTTP GET to `api.callmebot.com/whatsapp.php` with phone + message | Simple, free, no setup; limited formatting; rate-limited (fair use) |
| Signal-cli bridge | HA service + local signal-cli daemon | More control; requires Docker/systemd; harder setup |
| Twilio | Paid API (~$0.01/msg) | Reliable, fast; not needed for hobby use |

**Recommended:** CallMeBot for WhatsApp. Simple HTTP GET, no credentials in HA (QR code scan once, then API call).

**Implementation:**
```python
import aiohttp

async def send_whatsapp(hass, phone, message):
    url = "https://api.callmebot.com/whatsapp.php"
    params = {"phone": phone, "text": message}
    async with aiohttp.ClientSession() as session:
        await session.get(url, params=params, timeout=10)
```

### Signal (Optional in v1, revisit v2)

| Option | Approach | Trade-offs |
|--------|----------|-----------|
| **signal-cli** | Daemon + HA notification service | Encrypted; requires local Docker; complex setup |
| HA built-in Notify | Use `notify` service if crew has Signal Desktop linked | Simple but assumes crew setup |

**Recommendation for v1:** Defer to v2. Focus on WhatsApp via CallMeBot first. Add Signal only if crew demands it.

### Google Calendar (Built-in HA)

Use HA's native Google Calendar integration:

| Component | Details |
|-----------|---------|
| `google_calendar` domain | Requires OAuth setup via HA Companion app |
| `calendar.create_event` service call | Creates calendar event from DataUpdateCoordinator |
| Event details | Start time = next good window, summary = "FlyNow: Good conditions at [site]" |

**Implementation:**
```python
hass.services.async_call("calendar", "create_event", {
    "entity_id": "calendar.crew_calendar",
    "summary": f"FlyNow: {site_name} - GO",
    "description": condition_summary,
    "start_date_time": next_good_window.isoformat(),
    "end_date_time": (next_good_window + timedelta(hours=2)).isoformat(),
})
```

## HA Development Workflow

### Project Structure

```
custom_components/flynow/
├── __init__.py                 # async_setup_entry, async_unload_entry
├── manifest.json               # Domain, version, deps, HA version requirements
├── config_flow.py              # ConfigFlow class with step_user, step_location, etc.
├── coordinator.py              # DataUpdateCoordinator subclass for weather fetch
├── sensor.py                   # Entity definitions for go/no-go status
├── const.py                    # Domain, config keys, defaults, thresholds
├── strings.json                # Config flow labels, notification templates
└── py.typed                    # PEP 561 marker for mypy strict mode

lovelace/flynow-card/
├── src/
│   ├── flynow-card.ts          # Main card class extending LitElement
│   └── types.ts                # TypeScript interfaces for hass, config, state
├── dist/                        # Built output (esbuild)
├── package.json
├── tsconfig.json
├── esbuild.config.js           # Build configuration
└── resources.json              # HACS frontend resource metadata

tests/
├── test_config_flow.py         # ConfigFlow tests
├── test_coordinator.py         # DataUpdateCoordinator tests
├── test_sensor.py              # Sensor entity tests
└── conftest.py                 # pytest fixtures

.pre-commit-config.yaml         # ruff, mypy hooks
```

### Config Flow Pattern

Standard HA pattern (do not deviate):

```python
from homeassistant import config_entries
from homeassistant.core import callback
import voluptuous as vol

class FlyNowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        # First step: location (lat/lon or text search)
        if user_input is not None:
            await self.async_set_unique_id(user_input["location"])
            self._abort_if_unique_id_configured()
            return await self.async_step_thresholds()
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("location"): str,
            })
        )
    
    async def async_step_thresholds(self, user_input=None):
        # Second step: wind, ceiling, visibility thresholds
        ...
    
    async def async_step_contacts(self, user_input=None):
        # Third step: WhatsApp phone, Google Calendar entity
        ...
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return FlyNowOptionsFlowHandler(config_entry)
```

### DataUpdateCoordinator Pattern

Standard pattern for async weather fetches:

```python
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

class FlyNowCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api_client):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=1),
        )
        self.api_client = api_client
        self.weather_data = None
        self.go_no_go = None
    
    async def _async_update_data(self):
        try:
            # Fetch Open-Meteo data
            # Analyze conditions
            # Determine go/no-go
            # Send notifications if needed
            return self.weather_data
        except Exception as e:
            raise UpdateFailed(f"Error fetching weather: {e}")
```

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `requests` library | Not async; blocks HA event loop; discouraged in HA | Use `aiohttp` |
| Synchronous calls in integration | Blocks HA; can freeze UI and all automations | Use `async`/`await` throughout |
| Direct database access | HA config is sqlite; custom code shouldn't access it directly | Use HA's `hass.helpers` helpers or JSON files in config dir |
| Custom YAML config | HA deprecated YAML setup in 2023; use config_entries only | Use ConfigFlow for UI-based setup |
| React/Vue for Lovelace card | Massive bundle; HA uses lit; poor integration; slow | Use LitElement + lit-html |
| Webpack | Outdated for HA; bloated config; esbuild is standard now | Use esbuild for bundling |
| Manual state management in card | Brittle, hard to debug; Lit handles reactivity | Use LitElement `@property` decorators |

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|------------------------|
| **Python version** | 3.12+ | 3.11 | Never; HA now requires 3.12. |
| **Async client** | aiohttp | httpx | httpx slightly better DX; aiohttp is HA standard and pre-installed. |
| **Frontend framework** | LitElement | Vanilla JS | Vanilla if card has no interactivity; LitElement enables reactive properties. |
| **Card bundler** | esbuild | vite | Vite is newer; esbuild simpler, faster, HA-endorsed. |
| **Weather API** | Open-Meteo | OpenWeatherMap | Only if Open-Meteo coverage gaps emerge; requires API key; not worth v1. |
| **Messaging** | CallMeBot | Twilio | CallMeBot free & simple; Twilio if reliability critical (not hobby use). |

## Messenger Integration Rationale

**WhatsApp via CallMeBot (Recommended v1):**
- HTTP GET request, no credentials in HA config
- Free, no rate limit concerns for <10 messages/day
- Works without Docker or systemd setup
- Trade-off: Single-threaded messaging, not formatted (plain text), rate-limited by CallMeBot (typically 100 msg/day fair use)

**Signal via signal-cli (Optional v2):**
- Better security (Signal encryption)
- More setup: Docker container + HA integration or signal-cli systemd service
- Deferred until crew explicitly requests it

**Google Calendar (Recommended v1):**
- Native HA integration
- OAuth-based, secure
- Creates shareable calendar events (crew + pilot both see it)
- HA handles token refresh automatically

## HA Manifest & Dependencies

Minimum viable `manifest.json`:

```json
{
  "domain": "flynow",
  "name": "FlyNow - Hot Air Balloon Weather",
  "codeowners": ["@mburdych"],
  "config_flow": true,
  "documentation": "https://github.com/mburdych/flynow",
  "homeassistant": "2025.1",
  "iot_class": "cloud_polling",
  "requirements": [
    "aiohttp==3.9.*",
    "pydantic==2.4.*",
  ],
  "version": "0.1.0",
  "issue_tracker": "https://github.com/mburdych/flynow/issues"
}
```

## Sources

### Home Assistant Integration Patterns
- **HA Developer Docs** (https://developers.home-assistant.io/) — Integration architecture, config_flow, DataUpdateCoordinator, testing with `pytest-homeassistant-custom-component`. Standards enforced by HA PR reviewers.
- **HA 2025.x Release Notes** — Deprecated YAML config; require 3.12+; async/await standards.

### Frontend Development
- **LitElement Docs** (https://lit.dev/) — Web components, reactive properties, TypeScript integration. Industry standard for web components.
- **HA Lovelace Card Development** (https://developers.home-assistant.io/docs/frontend/custom-cards/) — LitElement pattern; esbuild bundler; HACS registration.

### External APIs
- **Open-Meteo Docs** (https://open-meteo.com/en/docs) — Free weather API; wind at multiple altitudes; European coverage; no API key.
- **CallMeBot WhatsApp** (https://www.callmebot.com/blog/free-api-whatsapp-messages/) — Simple HTTP GET integration.

### Testing & Quality
- **pytest-homeassistant-custom-component** (https://github.com/home-assistant/pytest-homeassistant-custom-component) — Standard fixtures for HA integration testing.
- **ruff** (https://docs.astral.sh/ruff/) — HA-endorsed linter; replaces flake8, black, isort in one tool.

### Community Standards
- **HACS Requirements** (https://hacs.xyz/docs/publish/requirements) — Custom integration & card registration; manifest.json standards; code review expectations.

---

## Confidence Assessment

| Area | Level | Rationale |
|------|-------|-----------|
| Python stack | **HIGH** | HA core requirements (3.12+, async, aiohttp) stable since 2024.1; no changes expected. |
| DataUpdateCoordinator pattern | **HIGH** | Established HA pattern since 2021; refinements in 2024 frozen for 2025.x. |
| Lovelace + LitElement | **HIGH** | HA standard since 2022; lit 3.0+ stable; no major changes planned. |
| Open-Meteo API | **HIGH** | Free API, stable endpoints, excellent European coverage. Company actively maintained. |
| Build tooling (esbuild) | **HIGH** | HA community consensus; faster than webpack; simpler config. |
| Messaging integration options | **MEDIUM** | CallMeBot free tier reliable for low volume; no official HA WhatsApp integration (third-party API). Signal-cli approach solid but setup-heavy. Google Calendar native integration = HIGH confidence. |
| pytest-homeassistant-custom-component | **HIGH** | Standard fixture library; actively maintained by HA core team. |

---

## Notes for Implementation

1. **Do not skip HA code quality.** `strict` mypy mode catches real bugs. Use pre-commit hooks to enforce ruff + mypy before commits.

2. **DataUpdateCoordinator refresh interval:** Start with 1 hour. Balloon flying is dawn-focused; no need to fetch every 10 minutes. Adjust based on crew feedback.

3. **Open-Meteo request timing:** Forecast updates typically ~45 minutes past the hour. Schedule coordinator update at :50 past for fresh data.

4. **Config flow validation:** Validate location (lat/lon or geocode); validate threshold ranges (wind 0–50 km/h, ceiling 500–3000m). Pydantic models help.

5. **Timezone handling:** Store user's timezone in config. Open-Meteo returns UTC; convert to local for analysis. Use `dateutil.tz` for timezone awareness.

6. **Card bundle size:** LitElement + lit-html ~15 KB minified. Aim for <50 KB total card code; HA browsers are often on slow mobile networks.

7. **Testing:** Write tests for:
   - `config_flow`: User input validation, unique_id deduplication
   - `coordinator`: API fetch error handling, condition analysis logic
   - `sensor`: State updates, attribute mapping
   - Card (if TypeScript): Property binding, event dispatch
