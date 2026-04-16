# Domain Pitfalls: Home Assistant Custom Integration + Weather + Notifications

**Domain:** Home Assistant custom integration (weather data + multi-channel notifications + Lovelace card)
**Researched:** 2026-04-16
**Confidence:** MEDIUM (training data through Feb 2025; HA community patterns stable; specific Open-Meteo/Slovakia constraints require runtime validation)

---

## Critical Pitfalls

### Pitfall 1: Blocking Calls in Async Context

**What goes wrong:**
Integration hangs, HA becomes unresponsive, config entries fail to load, or system restarts with timeout errors. Lovelace cards don't update. Other automations and integrations experience delays.

**Why it happens:**
Developers new to HA use synchronous libraries (e.g., `requests.get()`, `json.load()` on files, database queries) inside async functions (`async_setup_entry`, `async_fetch_data`, coordinator updates). Even a single blocking call (e.g., 5-second HTTP request) blocks the entire HA event loop.

**Consequences:**
- HA becomes sluggish or unresponsive during weather API calls
- Config validation during setup can timeout
- Coordinator updates block other integrations
- Users experience frequent "not responding" warnings
- System stability issues, especially on slower hardware (Pi, NUC)
- Crashes during peak activity (multiple notification sends + API calls + card updates)

**Prevention:**
- Use `aiohttp` (async HTTP) instead of `requests`
- Use `async` file I/O (`aiofiles`) instead of blocking `open()`/`json.load()`
- Wrap blocking calls with `asyncio.to_thread()` (HA 2022.09+) or `loop.run_in_executor()`
- Profile coordinator update time; alert if > 2 seconds
- Never use `time.sleep()`; use `asyncio.sleep()` instead
- All HA entry points must be `async def`:
  ```python
  async def async_setup_entry(hass, entry):
      # All calls here must be awaited or non-blocking
      data = await fetch_weather_data()
  ```

**Detection:**
- Logs show "Timeout fetching data" or "Executor overloaded"
- HA becomes unresponsive during forecast refresh
- Coordinator takes > 2 seconds to complete an update
- Config validation hangs during setup

**Phase to address:** Phase 1 (coordination setup) — this must be correct before shipping; reworking async architecture late is expensive.

---

### Pitfall 2: Config Entry Reload Not Persisting Options Changes

**What goes wrong:**
User changes thresholds or location via Options UI → logs show "reload" success → but sensor entities continue reporting old values. Changes appear to apply, then revert on integration reload. Tests pass, but production shows stale state.

**Why it happens:**
- `async_reload_entry()` is not implemented; options changes trigger a full unload/reload, but coordinator cache is not cleared
- Options flow doesn't call coordinator reload; data is stale
- Config entry data and options are not distinguished; old values persist in memory
- Coordinator caches weather data but options change doesn't invalidate cache

**Consequences:**
- Users change thresholds, nothing happens
- Location changes don't fetch new forecast data
- Old sensor state persists, confusing debugging
- Tests of "change option → verify state" fail in integration tests

**Prevention:**
```python
async def async_reload_entry(hass, entry) -> bool:
    """Reload config entry after options change."""
    return await hass.config_entries.async_reload(entry.entry_id)

# In coordinator init:
async def _async_update_data(self):
    """Fetch new data using current config entry options."""
    location = self.config_entry.options.get(CONF_LOCATION)
    # Use options, not stale config data
    return await fetch_weather(location)
```

- Always distinguish `entry.data` (setup-time config) from `entry.options` (user-changeable options)
- Reload coordinator when options change:
  ```python
  async def async_options_update_listener(hass, config_entry):
      await hass.config_entries.async_reload(config_entry.entry_id)
  ```
- Add integration tests that verify: change option → coordinator updates → sensor state changes

**Detection:**
- User reports: "Changed threshold in UI, but sensor still shows old value"
- Options change appears in logs, but sensor doesn't reflect it
- Integration tests for options changes fail

**Phase to address:** Phase 1 (config flow). Easy to get wrong initially; test early with manual option changes.

---

### Pitfall 3: Entity State Not Updating or Updating Stale Values

**What goes wrong:**
Coordinator fetches new weather data, but Lovelace card and sensors don't reflect changes. Forecast shows 2-hour-old conditions. Card refresh button doesn't work.

**Why it happens:**
- Coordinator calls `async_request_refresh()` but doesn't push state to entities
- Entity `async_update()` is not connected to coordinator; entities don't listen for updates
- Sensor state is set once during setup; never refreshed
- Coordinator data is fetched, but entities are not notified
- Coordinator update fails silently (exception caught, no state push)

**Consequences:**
- Lovelace card shows "Updated 3 hours ago"
- Users see old forecast in card, current in sensor
- No-go condition changes but card doesn't reflect it
- Crew and pilot miss good windows because card is stale

**Prevention:**
Use `CoordinatorEntity` base class; it automatically syncs with coordinator:

```python
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class FlynowForecastSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, name):
        super().__init__(coordinator)
        self._attr_name = name

    @property
    def native_value(self):
        """Return current forecast state."""
        return self.coordinator.data.get("go_no_go")

    @property
    def extra_state_attributes(self):
        """Return additional forecast details."""
        return {
            "wind_speed": self.coordinator.data.get("wind_speed"),
            "ceiling": self.coordinator.data.get("ceiling"),
            "updated_at": self.coordinator.last_update_success_time,
        }
```

- Coordinator handles retry logic and pushes updates automatically
- Entities inherit `available` property from coordinator
- Always implement `@property native_value()` to read from `coordinator.data`
- Never cache data in entity; always read from coordinator on property access
- Add `extra_state_attributes` with parsed forecast breakdown

**Detection:**
- Card shows "last updated" timestamp older than current time
- Manual HA reload fixes state (indicates entities didn't subscribe)
- Coordinator logs show "data fetched" but sensors show old values
- Tests pass, but manual checks show stale data

**Phase to address:** Phase 1 (sensor setup). Test by manually refreshing HA UI or calling coordinator refresh.

---

### Pitfall 4: Missing or Incomplete `async_unload_entry()` Cleanup

**What goes wrong:**
User uninstalls integration → memory leaks → HA slowly consumes memory → system becomes unstable after days. Leftover listeners cause duplicate notifications. Manual reloads create phantom entity instances.

**Why it happens:**
- `async_unload_entry()` not implemented; HA can't clean up coordinator, listeners, or API connections
- Listeners registered but not cancelled
- HTTP session not closed
- Hass data not removed from `hass.data[DOMAIN]`
- Tasks created in setup but not cancelled on unload

**Consequences:**
- Memory leak over time (especially on Pi or NUC)
- Duplicate notifications sent (old listeners still active)
- Config reload creates multiple coordinators
- Integration can't be cleanly removed

**Prevention:**
```python
async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    
    if unload_ok:
        # Cancel any pending tasks
        if DOMAIN in hass.data:
            coordinator = hass.data[DOMAIN].get(entry.entry_id)
            if coordinator:
                await coordinator.async_shutdown()
        
        # Remove from hass.data
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok

async def async_remove_entry(hass, entry):
    """Called when entry is uninstalled (not just unloaded)."""
    # Clean up persistent data (e.g., flight logs)
    flight_log_path = hass.config.path(FLIGHT_LOG_FILE)
    if os.path.exists(flight_log_path):
        # Archive or delete as appropriate
        pass
```

- Always implement both `async_unload_entry()` and `async_remove_config_entry_async_remove_callback()`
- Cancel all listeners and tasks in unload
- Close HTTP sessions
- Remove all entries from `hass.data`

**Detection:**
- Memory usage grows over days
- Integration reload creates duplicate coordinator instances
- Config reload breaks until HA restart
- Notifications sent multiple times

**Phase to address:** Phase 1 (entry lifecycle). Test by repeatedly adding/removing the integration.

---

### Pitfall 5: Manifest.json Version/Dependency Mismatch Breaking HACS Install

**What goes wrong:**
User tries to install via HACS → "Incompatible with your Home Assistant" → integration won't install. OR: integration installs but requires `aiohttp` 3.9, HA env has 3.8 → runtime import errors.

**Why it happens:**
- `manifest.json` declares `homeassistant.min_version` as 2025.12, but code uses features from 2026.1
- Listed dependencies (`aiohttp`, `pyyaml`) don't match installed versions
- HA version requirement too new (no users on that version yet)
- Python syntax (e.g., type hints) incompatible with declared HA version

**Consequences:**
- Integration fails HACS validation, won't publish
- Users can't install on their HA version
- Runtime ImportError or AttributeError in production
- HACS version/compatibility matrix breaks

**Prevention:**
```json
{
  "domain": "flynow",
  "name": "FlyNow",
  "version": "0.1.0",
  "homeassistant": {
    "min_version": "2024.12"
  },
  "requirements": [
    "aiohttp>=3.9.0"
  ],
  "codeowners": ["@dwdv8103"],
  "documentation": "https://github.com/dwdv8103/ha-flynow/wiki",
  "issue_tracker": "https://github.com/dwdv8103/ha-flynow/issues",
  "hacs": {
    "category": "integration",
    "zip_release": true
  }
}
```

- Set `min_version` conservatively (e.g., 2024.12, not 2025.12)
- Test on minimum declared version before release
- Pin major versions of dependencies; let HA handle patch versions
- Validate manifest with `python -m json.tool` + online validator
- HACS tests `min_version` before installation; respect it

**Detection:**
- HACS shows "Incompatible" badge
- RuntimeError during import (missing feature in HA version)
- Dependency version mismatch in logs

**Phase to address:** Phase 0 (scaffolding) — get this right before first release; retroactive fixes require major version bump.

---

### Pitfall 6: Open-Meteo Rate Limits and Polling Too Often

**What goes wrong:**
Integration polls Open-Meteo every 5 minutes → after 2 days, IP is throttled to 1 request/minute → coordinator starts failing → forecasts become stale.

**Why it happens:**
- Coordinator update interval set too aggressively (5 min instead of 30–60 min)
- No retry backoff; failed requests immediately retry, doubling rate
- Config validation calls API during setup; multiple reloads = multiple API calls
- User has 5 launch sites configured; polling each one exhausts quota

**Consequences:**
- IP throttling after 1–2 days
- Forecasts become unavailable
- Integration fails silently (no logs of rate limit)
- Users think integration is broken; trust erodes

**Prevention:**
```python
# In coordinator.py
SCAN_INTERVAL = timedelta(minutes=30)  # Not 5!

async def _async_update_data(self):
    try:
        location = self.config_entry.options[CONF_LOCATION]
        # Fetch once per update; don't call API multiple times
        data = await open_meteo_client.get_forecast(location)
        return data
    except Exception as err:
        raise UpdateFailed(f"Error fetching Open-Meteo: {err}")
```

- Set `SCAN_INTERVAL` to 30–60 minutes (dawn check only needs rough forecast)
- DataUpdateCoordinator implements exponential backoff; don't override with aggressive retries
- Cache responses; only fetch on config change or explicit refresh
- For validation, use lightweight API call or cache result

**Detection:**
- Open-Meteo returns 429 (Too Many Requests)
- Coordinator update fails after running for 24–48 hours
- Logs show consistent "rate limit" or "throttle" messages

**Phase to address:** Phase 1 (coordinator setup). Test by running for 48 hours and monitoring API call count.

---

### Pitfall 7: Timezone Handling for Dawn Detection

**What goes wrong:**
Integration configured in Slovakia (CET/CEST) → coordinator fetches UTC forecast → dawn threshold filter (`05:00`) doesn't align with local sunrise time → notifies at 04:00 UTC (05:00 CET) even though forecast is for 06:00 sunrise. Card shows correct time, sensor shows wrong time. Crew misses window because times don't match.

**Why it happens:**
- Open-Meteo returns all times in UTC
- Coordinator converts to HA's configured timezone, but threshold comparison is naive string match ("05:00") instead of timezone-aware
- Sunrise time from Open-Meteo is UTC; threshold is local time
- Lovelace card displays times in HA timezone; backend comparison is in UTC

**Consequences:**
- Notifications sent at wrong times
- Crew and pilot confused about when to fly
- Thresholds don't match displayed times
- Off-by-one-hour errors near DST transitions

**Prevention:**
```python
from homeassistant.util import dt as dt_util
from datetime import datetime, timezone, timedelta

async def _async_update_data(self):
    """Fetch and analyze forecast."""
    location = self.config_entry.options[CONF_LOCATION]
    tz = dt_util.get_time_zone(self.hass.config.time_zone)  # User's HA timezone
    
    forecast = await open_meteo_client.get_forecast(location)
    
    # All forecast times are UTC from Open-Meteo
    # Convert to user's timezone for threshold comparison
    dawn_start_local = self.config_entry.options.get(CONF_DAWN_START, "05:00")
    dawn_end_local = self.config_entry.options.get(CONF_DAWN_END, "09:00")
    
    # Parse local time as naive, then localize to user's timezone
    dawn_start = dt_util.parse_time(dawn_start_local)
    dawn_end = dt_util.parse_time(dawn_end_local)
    
    go_no_go_hours = []
    for forecast_hour in forecast['hourly']['time']:
        # forecast_hour is UTC string: "2026-04-16T07:00"
        dt_utc = datetime.fromisoformat(forecast_hour.replace('Z', '+00:00'))
        dt_local = dt_utc.astimezone(tz)
        
        # Check if local time falls in dawn window
        if dawn_start <= dt_local.time() <= dawn_end:
            go_no_go_hours.append({
                "time_utc": dt_utc,
                "time_local": dt_local,
                "wind": forecast['hourly']['wind_speed_10m'][...],
            })
    
    return {
        "go_no_go": calculate_go_no_go(go_no_go_hours),
        "hours": go_no_go_hours,
    }
```

- Always work in UTC internally; convert to local timezone for display and thresholds
- Use HA's `dt_util` helpers; they handle DST correctly
- Store thresholds as local time strings in options; convert at comparison time
- Lovelace card should display all times in HA's configured timezone
- Test DST transitions (spring/fall) in March and October

**Detection:**
- Notifications sent at 04:00 UTC instead of 05:00 local
- Card shows 05:00, sensor shows 04:00 for same event
- Time mismatch grows or shrinks by an hour in spring/fall
- Off-by-one errors in dawn window detection

**Phase to address:** Phase 1 (forecast analysis). Test with Slovakia timezone and DST transitions.

---

### Pitfall 8: Incorrect Open-Meteo Parameters for Wind Shear

**What goes wrong:**
Integration fetches `wind_speed_10m` (10-meter wind) and declares "wind OK" → pilot reports thermals and wind shear different from forecast → crashes or unsafe flight.

**Why it happens:**
- Developers use only surface wind (`wind_speed_10m`), missing wind shear at altitude
- Open-Meteo pressure levels are optional; not fetched by default
- Altitude parameters vary by model; no clear API documentation
- Confusion between `wind_speed` and `wind_speed_10m`; don't know which to use

**Consequences:**
- Forecast missing critical shear data
- Conditions forecast as "good" but shear makes flight dangerous
- Safety margin compromised
- Regulatory/insurance issue if shear causes incident

**Prevention:**
```python
# In Open-Meteo API request:
# Fetch wind at multiple altitudes to detect shear

open_meteo_params = {
    "latitude": lat,
    "longitude": lon,
    "hourly": [
        "temperature_2m",
        "weather_code",
        "wind_speed_10m",  # Surface wind
        "wind_direction_10m",
        "wind_speed_100m",  # Altitude wind (if available)
        "wind_direction_100m",
        "wind_speed_80m",   # Additional altitude levels
        "ceiling",
        "precipitation_probability",
        "visibility",
    ],
    "wind_speed_unit": "kmh",
    "timezone": "Europe/Bratislava",
}

# Calculate shear as difference between surface and altitude winds
def calculate_wind_shear(surface_wind, altitude_wind):
    """Shear > 10 km/h difference is significant for balloons."""
    return abs(altitude_wind - surface_wind)

# Check both surface wind AND shear
if surface_wind <= 15 and wind_shear <= 10:
    condition = "go"
else:
    condition = "no_go"
```

- Request multiple altitude wind measurements from Open-Meteo
- Calculate shear as difference; include in analysis
- Test Open-Meteo API response format for your region (Central Europe)
- Consult balloon pilots on acceptable shear thresholds (likely < 10 km/h)
- Document which parameters are critical vs optional

**Detection:**
- Pilot reports: "Forecast said go, but thermals and shear were rough"
- Actual flight logs contradict predictions
- Wind shear not shown in Lovelace card details

**Phase to address:** Phase 1 (analysis engine). Validate with domain expert (pilot).

---

### Pitfall 9: Multi-Channel Notification Fatigue and Rate Limiting

**What goes wrong:**
Good flying window detected → integration sends notification to HA push + Google Calendar + WhatsApp + Signal simultaneously → some APIs rate-limit or drop messages → crew misses notification → integration sends duplicate reminders → crew annoyed by spam.

**Why it happens:**
- No rate limiting between notification channels
- Fire-and-forget approach: doesn't retry if one channel fails
- WhatsApp/Signal APIs have strict rate limits (1 msg/sec per contact)
- Google Calendar OAuth token expires without refresh
- "Good window detected" condition triggers multiple times; same notification sent 5 times

**Consequences:**
- WhatsApp sends 1 msg, Signal drops 1 msg, HA push succeeds → incomplete notification
- Google Calendar event not created (OAuth expired)
- Spam notifications annoy crew; integration labeled "broken"
- Pilot doesn't receive alert; misses good window

**Prevention:**
```python
async def async_send_notifications(self, go_no_go_event):
    """Send notifications to all channels with rate limiting and retry."""
    
    notification_results = {
        "ha_push": None,
        "google_calendar": None,
        "whatsapp": None,
        "signal": None,
    }
    
    # HA push is reliable; send first
    try:
        await self.hass.services.async_call(
            "notify",
            "mobile_app_crew_phone",
            {"message": f"Good flying window: {go_no_go_event['time_local']}"}
        )
        notification_results["ha_push"] = "sent"
    except Exception as e:
        self._logger.error(f"HA push failed: {e}")
        notification_results["ha_push"] = "failed"
    
    # Google Calendar; handle token refresh
    try:
        await self._create_calendar_event(go_no_go_event)
        notification_results["google_calendar"] = "sent"
    except TokenExpiredError:
        # Refresh OAuth token
        await self._refresh_google_oauth()
        await self._create_calendar_event(go_no_go_event)
        notification_results["google_calendar"] = "sent"
    except Exception as e:
        self._logger.warning(f"Google Calendar failed: {e}")
        notification_results["google_calendar"] = "failed"
    
    # WhatsApp/Signal: rate-limit to 1 msg/sec
    for contact in [WHATSAPP_GROUP, SIGNAL_GROUP]:
        try:
            await asyncio.sleep(1.1)  # Rate limiting
            await self._send_message(contact, f"Go: {go_no_go_event['time_local']}")
            notification_results[contact] = "sent"
        except RateLimitError:
            self._logger.warning(f"{contact} rate limited; retry later")
            notification_results[contact] = "rate_limited"
        except Exception as e:
            self._logger.error(f"{contact} failed: {e}")
            notification_results[contact] = "failed"
    
    # Log result; alert if all channels failed
    await self._log_notification_result(notification_results)
    if all(v in ["failed", "rate_limited"] for v in notification_results.values()):
        self._logger.critical("All notification channels failed!")
        return False
    
    return True
```

- Implement per-notification deduplication (track last notification time; don't re-send if < 1 hour old)
- Serialize multi-channel sends with delays between APIs (avoid thundering herd)
- Implement retry logic with exponential backoff for failed channels
- Handle OAuth token expiry gracefully (refresh in background)
- Log which channels succeeded/failed
- Alert if all channels fail

**Detection:**
- Crew reports: "Received HA notification but not WhatsApp"
- WhatsApp returns 429 (Too Many Requests)
- Duplicate notifications sent within 1 hour
- Google Calendar events not created (OAuth token expired)

**Phase to address:** Phase 2 (notifications). Test with all channels enabled; monitor for 1 week.

---

### Pitfall 10: Lovelace Card Not Updating on Sensor State Change

**What goes wrong:**
Coordinator fetches new forecast → sensor state updates → HA UI shows update → Lovelace card still shows old data. Manual refresh in card works, but automatic updates don't. Card is stale for hours.

**Why it happens:**
- Custom card doesn't subscribe to entity state changes
- Card reads state once on load; doesn't listen for updates
- Card uses incorrect entity ID or domain
- Custom card JS bundle not properly registered in HACS
- Service call cache not invalidated

**Consequences:**
- Crew can't trust card timestamps
- Manual refresh button needed (poor UX)
- Notification sent, but card still shows old forecast
- Mobile app shows old state; desktop shows new state (cache inconsistency)

**Prevention:**
```typescript
// In custom Lovelace card TypeScript:
import { LitElement, html, css } from 'lit';
import { HomeAssistant } from 'custom-card-helpers';

export class FlynowCard extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property() config: any;
  
  private entityId = 'sensor.flynow_go_no_go';
  
  connectedCallback() {
    super.connectedCallback();
    // Subscribe to entity state changes
    this.hass?.connection.subscribeMessage(
      (message) => this._handleStateChange(message),
      { type: 'subscribe_entities', entity_ids: [this.entityId] }
    );
  }
  
  _handleStateChange(message: any) {
    // Card will re-render when state changes
    this.requestUpdate();
  }
  
  render() {
    const state = this.hass?.states[this.entityId];
    if (!state) {
      return html`<p>Entity not found: ${this.entityId}</p>`;
    }
    
    return html`
      <div class="card">
        <h2>FlyNow</h2>
        <p>Status: ${state.state}</p>
        <p>Wind: ${state.attributes.wind_speed} km/h</p>
        <p>Updated: ${new Date(state.last_updated).toLocaleTimeString()}</p>
      </div>
    `;
  }
  
  static get styles() {
    return css`
      .card { padding: 16px; }
    `;
  }
}
```

- Always use `subscribeMessage` with state subscription, not polling
- Read state from `this.hass?.states[entityId]` in render method
- Render timestamps from `state.last_updated` (always current)
- Test card with sensor state change and verify card updates
- Validate custom card in HACS frontend resources

**Detection:**
- Card shows "last updated: 3 hours ago" but sensor shows current time
- Manual refresh in card shows new data
- HA restart fixes card (indicates cache issue)

**Phase to address:** Phase 2 (Lovelace card). Test by triggering coordinator refresh and verifying card updates.

---

### Pitfall 11: Config Flow Validation Not Testing Integration

**What goes wrong:**
User enters location and API key in config flow → validation passes → "Setup complete" → integration fails on load with import error or missing data → user is stuck with broken config.

**Why it happens:**
- Config flow validates only syntax (location is a string, API key format correct)
- Doesn't test actual API call or integration startup
- Async validation disabled for simplicity
- Tests don't validate end-to-end setup

**Consequences:**
- Users create invalid configs
- Integration fails on load with cryptic errors
- Config must be deleted and recreated
- User trust erodes

**Prevention:**
```python
class FlynowConfigFlow(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}
        
        if user_input is not None:
            # Validate location is real; call Open-Meteo
            try:
                client = OpenMeteoClient()
                forecast = await client.get_forecast(
                    latitude=user_input[CONF_LATITUDE],
                    longitude=user_input[CONF_LONGITUDE],
                )
                # If we got here, API works
                return self.async_create_entry(
                    title=f"FlyNow ({user_input[CONF_LOCATION]})",
                    data=user_input,
                )
            except ValueError as e:
                errors["base"] = "invalid_location"
            except Exception as e:
                errors["base"] = "cannot_connect"
        
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_LOCATION): str,
                vol.Required(CONF_LATITUDE): float,
                vol.Required(CONF_LONGITUDE): float,
            }),
            errors=errors,
        )
```

- Test API connectivity in config flow validation
- Return clear error messages for common failures (invalid location, API unreachable)
- Validate coordinates are in expected range (Europe, not Antarctica)
- Write integration tests that simulate config flow end-to-end
- Test with invalid/missing API responses

**Detection:**
- Config flow shows "Setup complete" but integration fails on load
- User must recreate config multiple times
- Integration tests skip validation step

**Phase to address:** Phase 1 (config flow). Test with manual setup and invalid inputs.

---

### Pitfall 12: Flight Log Persistence and File Corruption

**What goes wrong:**
User logs flight after good morning → writes to `/config/flynow_flights.json` → HA restarts during write → JSON file corrupted → integration can't parse it → logs are lost.

**Why it happens:**
- Synchronous file write without buffering or locking
- No atomic write (write to temp file, then rename)
- No backup of previous logs
- File is overwritten, not appended
- Multiple async tasks write simultaneously

**Consequences:**
- Flight logs permanently lost
- Integration can't initialize (JSON parse error)
- User has to manually fix file
- Historical data for learning is unreliable

**Prevention:**
```python
import json
import aiofiles
import tempfile
from pathlib import Path

async def append_flight_log(self, flight_data: dict):
    """Safely append flight to log file."""
    log_path = self.hass.config.path(FLIGHT_LOG_FILE)
    
    # Read existing logs
    existing_logs = []
    if Path(log_path).exists():
        try:
            async with aiofiles.open(log_path, 'r') as f:
                content = await f.read()
                existing_logs = json.loads(content) if content else []
        except json.JSONDecodeError:
            self._logger.error(f"Corrupted flight log; backing up to {log_path}.bak")
            # Preserve corrupted file for manual recovery
            async with aiofiles.open(f"{log_path}.bak", 'w') as f:
                await f.write(content)
            existing_logs = []
    
    # Append new flight
    existing_logs.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **flight_data,
    })
    
    # Write to temp file first
    temp_fd, temp_path = tempfile.mkstemp(dir=Path(log_path).parent)
    try:
        async with aiofiles.open(temp_path, 'w') as f:
            await f.write(json.dumps(existing_logs, indent=2))
        
        # Atomic rename
        Path(temp_path).replace(log_path)
    except Exception as e:
        self._logger.error(f"Failed to write flight log: {e}")
        Path(temp_path).unlink(missing_ok=True)
        raise
    
    self._logger.info(f"Flight logged: {flight_data}")
```

- Use `aiofiles` for async file I/O
- Write to temp file, then atomically rename (prevents corruption)
- Backup corrupted files instead of overwriting
- Lock file during read/write to prevent concurrent access
- Validate JSON on load; recover gracefully if corrupted
- Test file corruption scenarios (HA restart during write)

**Detection:**
- Integration fails to load with "JSON decode error" in flight log
- User reports lost flight logs
- File is corrupted after HA crash

**Phase to address:** Phase 2 (flight logging). Implement atomic writes before shipping.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|-----------------|
| Synchronous API calls | Easier to write | Hangs HA during API delay | Never in production |
| No config reload listener | Skips one file | Options changes don't apply | Before Phase 1 |
| Hard-coded thresholds | Fewer config options | Can't customize for pilot | Only for MVP |
| Single launch site | Simple first version | Can't scale to 2 sites | Phase 0 only |
| No flight log persistence | Focus on core logic | Can't learn from history | Phase 1 OK, Phase 2 required |
| Manual time string parsing | Skip timezone library | Off-by-one errors at DST | Never in production |
| No notification dedup | Ship faster | Spam annoys crew | Before Phase 2 |
| Polling every 5 min | Higher freshness | Rate limits after 24h | Test labs only |
| No sensor attributes | Minimal entity setup | Card can't show details | Only for MVP |
| Custom file format (not JSON) | Slightly smaller size | Users can't inspect/edit | Use JSON always |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Open-Meteo API | Fetching all 1000+ variables | Request only needed fields: wind, ceiling, precip, visibility |
| Open-Meteo API | Forgetting to specify timezone | Always request `&timezone=Europe/Bratislava` |
| Open-Meteo API | Assuming wind_speed is in m/s | Specify `&wind_speed_unit=kmh` explicitly |
| Google Calendar | Storing OAuth token in config_entry.data | Use HA OAuth flow with token refresh |
| Google Calendar | No retry on OAuth failure | Implement token refresh + exponential backoff |
| WhatsApp API | Treating like email (fire and forget) | Implement rate limiting, dequeue on 429 |
| HA DataUpdateCoordinator | Setting update_interval=timedelta(minutes=5) | Use 30–60 min for weather; only dawn hours matter |
| HA config flow | Validating without calling API | Test location exists; validate Open-Meteo returns data |
| HA sensors | Using `update()` method instead of `CoordinatorEntity` | Always subclass CoordinatorEntity; it handles subscriptions |
| HA integration | No `async_unload_entry` | Implement cleanup; prevents memory leaks |
| Lovelace card | Reading state once on load | Subscribe to state changes; re-render on update |
| Lovelace card | Hard-coded entity ID | Make entity ID configurable in card options |
| File I/O | `open()` + `json.dump()` | Use `aiofiles` + atomic write (temp → rename) |
| Notifications | Sending to multiple channels simultaneously | Serialize with rate limiting (1 sec between APIs) |

---

## Performance Traps

| Trap | Symptom | Fix |
|------|---------|-----|
| Polling every 5 minutes | HA becomes sluggish; API throttles after 24h | Set SCAN_INTERVAL = timedelta(minutes=30) minimum |
| Fetching all Open-Meteo variables | API response > 1 MB; slow parsing | Request only: wind, ceiling, precip, visibility, weather_code |
| No caching of forecast data | Re-fetch on every card open | Cache in coordinator; only fetch on schedule or config change |
| Blocking file I/O in coordinator | Coordinator update takes 10 sec | Use aiofiles for async reads |
| Entity state updated in loop | 100 state updates per coordinator refresh | Batch updates; push single state dict to all entities |
| Card re-renders on every tiny state change | Lovelace performance degrades | Debounce state changes; only re-render if value changes > threshold |
| Google Calendar sync on every update | Too many API calls to Calendar | Only create event for single best window, not all good hours |
| Notifications to 5+ channels sequentially | Takes 30 seconds to notify | Parallelize with `asyncio.gather()` where rate limits allow |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|-----------|
| Storing Google OAuth token as plain text in config | Token exposure if config is backed up/shared | Use HA's secure OAuth flow; tokens stored in encrypted vault |
| Hard-coding API credentials in code | Leaked in GitHub/HACS | Use config flow to input credentials; never commit to repo |
| No validation of Open-Meteo response | Malicious response could crash integration | Validate response schema; handle unexpected data gracefully |
| Accepting any webhook from WhatsApp API | Spoofed messages could trigger false alerts | Validate webhook signature with shared secret |
| Flight log file world-readable | Logs could reveal pilot location history | Set file permissions to 0600 (owner read/write only) |
| No rate limiting on flight log form | Attacker floods log with fake entries | Implement per-IP rate limiting on Lovelace form submission |
| Storing pilot phone numbers in config_entry.data | Exposed in config backup | Use HA's secure options flow; encrypt sensitive contacts |
| No HTTPS validation for Google Calendar API | MITM attack possible | Always validate SSL certificates; use `aiohttp` defaults |

---

## "Looks Done But Isn't" Checklist

- [ ] **Config entry reload** — Can you change threshold in UI, see sensor update immediately?
- [ ] **Async throughout** — Does `ruff check` report any blocking calls? Do logs show "Executor overloaded"?
- [ ] **Entity state** — Does Lovelace card show timestamp matching current time after refresh?
- [ ] **Notification dedup** — Does a single good window trigger only one notification, not 5?
- [ ] **Google Calendar OAuth** — Do tokens refresh after 3600 seconds? Can you authenticate without errors?
- [ ] **File persistence** — Can you kill HA mid-flight-log-write and recover without corruption?
- [ ] **Timezone math** — Does 05:00 local threshold match forecast times in Slovakia (CET/CEST)?
- [ ] **API rate limits** — Can you run for 72 hours without Open-Meteo returning 429?
- [ ] **Unload cleanup** — After uninstalling, does HA memory stay stable? No zombie listeners?
- [ ] **HACS validation** — Does manifest.json validate? Can a user install on the min_version declared?
- [ ] **Wind shear data** — Are you fetching wind at 10m AND 80/100m? Is shear calculated?
- [ ] **Flight logs** — Can you parse logs 1 week later? Do backups exist if file corrupts?
- [ ] **Lovelace subscribe** — Does card update when you manually refresh coordinator, not just on timer?
- [ ] **Multi-channel test** — Did WhatsApp succeed when HA push failed? Did all channels get tested?
- [ ] **Config validation** — Does config flow actually call Open-Meteo API to validate location?

---

## Pitfall-to-Phase Mapping

| Pitfall | Phase 0 | Phase 1 | Phase 2 | Phase 3+ |
|---------|---------|---------|---------|----------|
| **Blocking calls** | — | **Critical** | Validate | — |
| **Config reload** | — | **Critical** | Test thoroughly | — |
| **Entity state** | — | **Critical** | Test with card | — |
| **Unload cleanup** | — | **Critical** | Monitor memory | — |
| **Manifest.json** | **Design** | **Test** | Validate | — |
| **Rate limits** | — | Monitor | Tune SCAN_INTERVAL | Alert if exceeded |
| **Timezone handling** | — | **Critical** | Test DST | — |
| **Wind shear params** | — | **Validate with pilot** | Analyze | Learning in v2 |
| **Notification fatigue** | — | — | **Critical** | Monitor |
| **Lovelace updates** | — | — | **Critical** | Test on mobile |
| **File corruption** | — | — | **Critical** | Backup strategy |
| **Config flow validation** | — | **Critical** | Test with bad data | — |

---

## Sources

**HA Community & Official:**
- Home Assistant Developer Docs: Async programming pitfalls, DataUpdateCoordinator patterns, custom integration structure
- HA Community Forums: Recurring issues in integration PRs (HACS reviews)
- HA Code Quality (mypy strict, ruff): Standard lint checks for integrations

**Open-Meteo:**
- Open-Meteo API Docs: Wind parameters, altitude levels, timezone handling, rate limits (1000 requests/day, ~1 request/minute soft limit)
- Community discussions on weather APIs: Shear detection, Central Europe coverage

**Aviation Weather Domain:**
- Balloon operations research: Wind thresholds, shear tolerance, dawn flying windows, thermal activity effects
- FAA/aviation guidance: Safety minimums for balloon operations (derived from domain knowledge)

**Confidence Assessment:**
- **HIGH:** HA async patterns, coordinator architecture, entity state synchronization (stable HA conventions)
- **MEDIUM:** Open-Meteo rate limits and parameters (specific endpoints; requires runtime testing)
- **MEDIUM:** Notification API rate limits (WhatsApp/Signal vary; vendor-specific)
- **LOW:** Aviation-specific wind shear thresholds (requires pilot domain expertise; not verified with specific pilots)

---

## Gaps & Validation Needed

- **Slovakia-specific weather model** — Which Open-Meteo model (ECMWF, GFS, etc.) is best for Central Europe at dawn?
- **Actual pilot wind shear tolerance** — What shear threshold (5 km/h, 10 km/h, 15 km/h) is unsafe for OM-0007/OM-0008?
- **Thermal activity detection** — Open-Meteo doesn't directly provide thermal forecasts; need to derive from CAPE or convective indices
- **Notification channel specifics** — WhatsApp/Signal rate limits and auth flows (OAuth, webhook security)
- **Mobile card performance** — Lovelace card on older phones (iPhone 11, Android 11) — need device testing
- **Actual flight log volume** — How many entries before JSON file becomes problematic (1000? 10K? 100K)?
- **Google Calendar availability** — Is Google Calendar API available via HA's OAuth flow in Slovakia?

These gaps should be addressed during phase-specific research (Phase 1 config/API, Phase 2 notifications, Phase 3+ learning).
