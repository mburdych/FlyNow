# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## Project Overview

**FlyNow** is a Home Assistant (HAOS) integration and Lovelace card that predicts suitable flying conditions for hot air balloon operations.

Core capabilities:
- Fetches public weather forecast data for a user-defined location and date
- Analyzes conditions across a ~100 km radius around the planned launch site
- Returns a go/no-go recommendation with condition details
- Accepts historical flight logs (date, time, place, outcome/details) to learn what conditions work for specific pilots/regions
- Improves prediction accuracy as more flight data is recorded

## Architecture (Planned)

### Home Assistant Integration (`custom_components/flynow/`)
Standard HA integration structure in Python:
- `manifest.json` — integration metadata, dependencies, HACS config
- `__init__.py` — integration setup/unload lifecycle
- `config_flow.py` — UI-based configuration (location, API keys, thresholds)
- `coordinator.py` — `DataUpdateCoordinator` that fetches + analyzes weather on a schedule
- `sensor.py` — exposes forecast analysis as HA sensor entities
- `const.py` — domain name, config keys, defaults

### Lovelace Card (`lovelace/flynow-card/`)
Custom frontend card (TypeScript, lit-html or similar) built as a HACS frontend resource:
- Displays go/no-go status, condition breakdown, radius map overlay
- Provides a form to log completed flights (feeds the learning model)

### Weather Data
Uses public APIs (no paid key required). Likely candidates:
- Open-Meteo (free, no key, hourly forecasts, wind at multiple altitudes)
- OpenWeatherMap free tier
- Meteomatics or similar for aviation-specific parameters

### Condition Analysis / Learning
- Key balloon parameters: surface wind speed/direction, wind shear at altitude, cloud ceiling, precipitation, thermal activity, visibility
- Historical flight store: JSON or SQLite in HA config dir (`/config/flynow_flights.json`)
- Learning: weighted scoring or simple ML (scikit-learn) trained on logged flights

## Home Assistant Conventions
- Integration domain: `flynow`
- All async — use `async_setup_entry`, `async_unload_entry`
- Config stored via `config_entries`, not `configuration.yaml`
- Use `hass.config.path()` to resolve paths inside the HA config directory
- Follow HA code quality requirements: `strict` mypy, `ruff` linting
- Test with `pytest-homeassistant-custom-component`

## Development Setup (Once Scaffolded)
```bash
# Install HA dev dependencies
pip install homeassistant pytest-homeassistant-custom-component

# Run integration tests
pytest tests/

# Lint
ruff check custom_components/flynow/
mypy custom_components/flynow/
```

## Key Domain Notes
- Hot air balloon flying requires: wind < ~15 km/h at surface, no precipitation, good visibility, stable air (low thermal activity), suitable ceiling
- Conditions vary significantly by micro-region — the 100 km radius analysis matters
- Pilots fly in early morning (calm thermals) — time-of-day filtering is important
- "Suitable" thresholds differ per pilot/balloon type — make thresholds configurable

<!-- GSD:project-start source:PROJECT.md -->
## Project

**FlyNow**

FlyNow is a Home Assistant integration for hot air balloon crew and pilots. It checks weather conditions across a configurable radius, returns a single go/no-go answer for morning flying windows, and proactively notifies the crew and pilot via push notification, calendar event, and messaging (WhatsApp/Signal) when conditions look good. Built for OM-0007 and OM-0008 operating out of Slovakia.

**Core Value:** One shared go/no-go answer that the crew and pilot both receive automatically — so nobody has to check five weather apps or call each other to decide.

### Constraints

- **Tech stack**: Python async (HA integration), TypeScript/lit-html (Lovelace card), standard HACS patterns
- **Weather API**: Open-Meteo — free, no key, hourly forecasts, wind at multiple altitudes. No paid fallback for v1.
- **Messaging**: WhatsApp/Signal integration complexity depends on available APIs; may require HA notification service or third-party bridge
- **HA conventions**: Must follow HA code quality requirements — strict mypy, ruff, async throughout, config via config_entries
- **Data storage**: Flight logs in HA config dir (`/config/flynow_flights.json`) — no external database
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
| Endpoint | Parameters | Use Case |
|----------|-----------|----------|
| `/forecast` | `latitude`, `longitude`, `hourly` (wind_speed_10m, wind_direction_10m, wind_speed_100m, wind_direction_100m, cloud_cover, ceiling, precipitation, visibility) | Primary weather fetch; hourly resolution |
| Wind layers | `wind_speed_10m`, `wind_speed_100m`, `wind_speed_200m` | Detect wind shear (surface vs altitude); balloons sensitive to shear |
| Cloud cover & ceiling | `cloud_cover`, `ceiling` | Go/no-go threshold: good ceiling (>1500m), low cloud cover |
| Precipitation | `precipitation`, `precipitation_probability` | Abort if >20% rain probability |
| Visibility | `visibility` | Require >5km (daylight balloon ops) |
## Messaging Integration Options
### WhatsApp
| Option | Approach | Trade-offs |
|--------|----------|-----------|
| **CallMeBot** (Recommended) | HTTP GET to `api.callmebot.com/whatsapp.php` with phone + message | Simple, free, no setup; limited formatting; rate-limited (fair use) |
| Signal-cli bridge | HA service + local signal-cli daemon | More control; requires Docker/systemd; harder setup |
| Twilio | Paid API (~$0.01/msg) | Reliable, fast; not needed for hobby use |
### Signal (Optional in v1, revisit v2)
| Option | Approach | Trade-offs |
|--------|----------|-----------|
| **signal-cli** | Daemon + HA notification service | Encrypted; requires local Docker; complex setup |
| HA built-in Notify | Use `notify` service if crew has Signal Desktop linked | Simple but assumes crew setup |
### Google Calendar (Built-in HA)
| Component | Details |
|-----------|---------|
| `google_calendar` domain | Requires OAuth setup via HA Companion app |
| `calendar.create_event` service call | Creates calendar event from DataUpdateCoordinator |
| Event details | Start time = next good window, summary = "FlyNow: Good conditions at [site]" |
## HA Development Workflow
### Project Structure
### Config Flow Pattern
### DataUpdateCoordinator Pattern
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
- HTTP GET request, no credentials in HA config
- Free, no rate limit concerns for <10 messages/day
- Works without Docker or systemd setup
- Trade-off: Single-threaded messaging, not formatted (plain text), rate-limited by CallMeBot (typically 100 msg/day fair use)
- Better security (Signal encryption)
- More setup: Docker container + HA integration or signal-cli systemd service
- Deferred until crew explicitly requests it
- Native HA integration
- OAuth-based, secure
- Creates shareable calendar events (crew + pilot both see it)
- HA handles token refresh automatically
## HA Manifest & Dependencies
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
## Notes for Implementation
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
