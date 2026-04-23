# Launch Sites — FlyNow

Reference list of favorite balloon launch sites + full identifier set for weather data lookup.
Used by: coordinator (API queries), UI (preset picker), notifications (per-site targeting).

---

## Weather data strategy — read first

Both Open-Meteo and OpenWeather forecast APIs are **gridded NWP models**. Station IDs only apply to:
- **METAR / TAF** — aviation real-time obs + short-term forecast (ICAO code)
- **WMO SYNOP** — surface observations; used by Open-Meteo historical archive AND directly queryable via SHMÚ website (5-digit WMO ID)

**Forecast is always fetched by `lat, lon` directly.** ICAO / WMO refs below are for cross-validation and historical tuning.

### Open-Meteo forecast models available for Slovakia

Verified by sample API call — **all 3 models resolve for all 3 sites**:

| Model | Resolution | Coverage | Notes for balloon use |
|-------|-----------|----------|-----------------------|
| `icon_d2` | **~2 km** | DE + neighbours incl. all of SK | **Primary** — highest-res, hourly, 48h horizon |
| `icon_eu` | ~7 km | Europe | Secondary / fallback beyond 48h |
| `ecmwf_ifs025` | ~25 km | Global | Tertiary / beyond 120h. **Does NOT return `wind_speed_100m`** |

Request `models=icon_d2,icon_eu,ecmwf_ifs025` for multi-model ensemble. Or `best_match` to let Open-Meteo pick.

### Parameters to fetch (Open-Meteo `/v1/forecast?hourly=...`)

```
wind_speed_10m, wind_direction_10m, wind_gusts_10m,
wind_speed_100m, wind_direction_100m,
wind_speed_180m, wind_direction_180m,      # shear detection (ICON only)
cloud_cover, cloud_cover_low, cloud_cover_mid,
cloud_base,                                 # ceiling proxy (ICON-D2)
precipitation, precipitation_probability,
visibility,
temperature_2m, dew_point_2m,               # fog risk
cape,                                       # thermal activity
pressure_msl, surface_pressure              # density altitude
```

Additional request params:
```
timezone=Europe/Bratislava
windspeed_unit=kmh
timeformat=iso8601
forecast_days=3
```

### Additional data sources — confirmed endpoints

- **aviationweather.gov API** — free METAR/TAF in JSON, no key
  `https://aviationweather.gov/api/data/metar?ids=LZIB,LZPP,LZNI&format=json`

- **ogimet.com** — historical METAR + SYNOP archive (scrape-friendly, slow)

- **Meteoalarm (EU CAP v2)** — **primary path for Slovak warnings**, standardized Common Alerting Protocol:
  - Hub API: `https://hub.meteoalarm.org/api/v1` (CAP v2)
  - All-warnings stream: `https://hub.meteoalarm.org/api/v1/stream-buffers/all-warnings/warnings`
  - Feeds domain: `https://feeds.meteoalarm.org`
  - Slovakia UI: `https://www.meteoalarm.org/en/live/region/SK`
  - Warnings keyed by **kraj** (region). Our okresy → kraje mapping:
    - Dunajská Streda (Maďaras) → **TTSK** Trnavský
    - Trnava (Katarínka) → **TTSK** Trnavský
    - Nitra (Nitra lúka) → **NSK** Nitriansky
  - Licensing: free, attribution required. No API key.

- **SHMÚ** (shmu.sk) — Slovak national weather service. **Primary domestic source for station obs:**
  - **Station obs URL pattern:** `https://www.shmu.sk/sk/?page=1&id=meteo_apocasie_sk&ii={WMO_ID}` (HTML, scrape). WMO `ii=` params verified from [station list](https://www.shmu.sk/en/?page=59).
  - **OpenDATA portal:** `https://meteo.shmu.sk/customer/home/opendata/` — official REST API with CSV payload (confirmed exists via DanubeHack 3.0). Date-parameterized URLs `?observations;date=DD.MM.YYYY:HH`. Full endpoint catalogue + auth details TODO.
  - **Warnings:** prefer **Meteoalarm CAP feed** (above) over SHMÚ HTML scraping. Same data, standardized format.
  - **ALADIN/SLOVAKIA** — domestic NWP ~4 km, tuned for SK terrain. Access mechanism TODO.
  - **Radar composites**, nowcast — URLs TODO.

- **OpenWeather One Call 3.0** — alt forecast, needs API key. Query by `lat, lon` directly.

- **DWD Open Data** — raw ICON-D2 GRIB2 if we ever need custom post-processing.

- **Community SHMÚ projects (reference for reverse-engineered endpoints):**
  - [ZatON318/SHMU_api](https://github.com/ZatON318/SHMU_api)
  - [soit-sk/scraper-shmu-observations](https://github.com/soit-sk/scraper-shmu-observations)
  - [jose1711/weather.shmu.pocasie](https://github.com/jose1711/weather.shmu.pocasie) (Kodi addon)

---

## Sites

### 1. LZMADA — Letisko Malý Madaras

| Field | Value |
|-------|-------|
| **Position** | `48.1429562, 17.3773480` |
| **Elevation (DEM)** | `125 m` AMSL (Open-Meteo) |
| **Timezone** | `Europe/Bratislava` (UTC+2 DST / UTC+1 std) |
| **Region** | Žitný ostrov |
| **Okres / kraj** | Dunajská Streda / Trnavský (TTSK) |
| **Type** | Aeroclub airfield (local code `LZMADA`, not 4-letter ICAO) |
| **Open-Meteo models** | `icon_d2` ✓, `icon_eu` ✓, `ecmwf_ifs025` ✓ |

**Nearest ICAO (METAR / TAF):**
| Rank | ICAO | Name | Distance | Coords |
|------|------|------|----------|--------|
| 1 | **LZIB** | Bratislava M.R.Štefánik | ~12.5 km W | 48.17020, 17.21270 |
| 2 | LZPP | Piešťany | ~63 km NE | 48.62520, 17.82840 |

**WMO SYNOP station (verified via [SHMÚ live list](https://www.shmu.sk/en/?page=59)):**
| Rank | WMO | Name | Distance |
|------|-----|------|----------|
| 1 | **11817** | Kráľova pri Senci | ~10 km NE |
| 2 | 11816 | Bratislava Ivanka (= LZIB) | ~12.5 km W |
| 3 | 11813 | Bratislava Koliba | ~21 km W (long historical record) |

SHMÚ obs URL: `https://www.shmu.sk/sk/?page=1&id=meteo_apocasie_sk&ii=11817`

**Meteoalarm region:** TTSK (Trnavský kraj)

**OpenWeather:** query directly by `lat, lon` via One Call 3.0 — city IDs not needed.

**Terrain notes:** flat lowland (~125 m). Low thermal activity pre-dawn. Summer thermals strengthen fast after sunrise. Danube river nearby → fog risk autumn/winter.

---

### 2. Lúka pri Katarínke (Dechtice / Naháč)

| Field | Value |
|-------|-------|
| **Position** | `48.5500809, 17.5535781` |
| **Elevation (DEM)** | `312 m` AMSL (Open-Meteo) |
| **Timezone** | `Europe/Bratislava` (UTC+2 DST / UTC+1 std) |
| **Region** | Malé Karpaty — eastern slope, pod zrúc. kláštora Katarínka |
| **Okres / kraj** | Trnava / Trnavský (TTSK) |
| **Type** | Meadow (unofficial field launch) |
| **Open-Meteo models** | `icon_d2` ✓, `icon_eu` ✓, `ecmwf_ifs025` ✓ |

**Nearest ICAO (METAR / TAF):**
| Rank | ICAO | Name | Distance | Coords |
|------|------|------|----------|--------|
| 1 | **LZPP** | Piešťany | ~22 km NE | 48.62520, 17.82840 |
| 2 | LZTN | Trenčín | ~48 km N | 48.86779, 18.00249 |
| 3 | LZIB | Bratislava | ~49 km SW | 48.17020, 17.21270 |

Note: `LZSE` Senica aeroclub (~19 km NW) is geographically closer than LZPP but **does not reliably publish METAR**. Use LZPP for aviation cross-check.

**WMO SYNOP station (verified):**
| Rank | WMO | Name | Distance |
|------|-----|------|----------|
| 1 | **11819** | Jaslovské Bohunice | ~12 km SE (NPP site — high-quality continuous obs) |
| 2 | 11805 | Senica | ~19 km NW |
| 3 | 11826 | Piešťany | ~22 km NE |
| 4 | 11806 | Myjava | ~22 km N |

SHMÚ obs URL: `https://www.shmu.sk/sk/?page=1&id=meteo_apocasie_sk&ii=11819`

**Meteoalarm region:** TTSK (Trnavský kraj)

**OpenWeather:** query directly by `lat, lon` via One Call 3.0 — city IDs not needed.

**Terrain notes:** eastern slope of Malé Karpaty, elevation **312 m** (~190 m above surrounding lowland). **Ridge wind effects** — W/NW winds accelerate over Malé Karpaty ridge (8 km to W). Autumn fog common in valleys below. `wind_speed_100m` vs `wind_speed_10m` differential will be large here — critical for pre-launch shear check.

---

### 3. Lúka pri Nitre

| Field | Value |
|-------|-------|
| **Position** | `48.3187712, 18.0547891` |
| **Elevation (DEM)** | `141 m` AMSL (Open-Meteo) |
| **Timezone** | `Europe/Bratislava` (UTC+2 DST / UTC+1 std) |
| **Region** | Ponitrie (~3 km W of Nitra centre, smer Lehota / Alekšince) |
| **Okres / kraj** | Nitra / Nitriansky (NSK) |
| **Type** | Meadow (unofficial field launch) |
| **Open-Meteo models** | `icon_d2` ✓, `icon_eu` ✓, `ecmwf_ifs025` ✓ |

**Nearest ICAO (METAR / TAF):**
| Rank | ICAO | Name | Distance | Coords |
|------|------|------|----------|--------|
| 1 | **LZNI** | Nitra Airfield | ~7.3 km SE | 48.27940, 18.13280 |
| 2 | LZPP | Piešťany | ~38 km NW | 48.62520, 17.82840 |
| 3 | LZTN | Trenčín | ~61 km N | 48.86779, 18.00249 |

Note: `LZNI` publishes METAR **irregularly** (small aeroclub airport). For reliable aviation obs cross-check use **LZPP** as fallback despite greater distance.

**WMO SYNOP station (verified):**
| Rank | WMO | Name | Distance |
|------|-----|------|----------|
| 1 | **11855** | Nitra | ~3 km E (essentially co-located) |
| 2 | 11819 | Jaslovské Bohunice | ~38 km NW |
| 3 | 11858 | Hurbanovo | ~50 km S (long reference record) |

SHMÚ obs URL: `https://www.shmu.sk/sk/?page=1&id=meteo_apocasie_sk&ii=11855`

**Meteoalarm region:** NSK (Nitriansky kraj)

**OpenWeather:** query directly by `lat, lon` via One Call 3.0 — city IDs not needed.

**Terrain notes:** open Nitra plain, elevation **141 m**. Tribeč hills (~600 m) 10 km NE. **Wind channelling along Nitra river valley** (NE–SW axis). Moderate thermal activity — less shear than Katarínka but more than Madaras. River fog possible in calm autumn mornings.

---

## Identifier completeness matrix

| Site | lat/lon | elevation | ICAO | WMO | Meteoalarm | OWM | tz |
|------|---------|-----------|------|-----|-----------|-----|----|
| LZMADA | ✅ | ✅ 125 m | ✅ LZIB (12.5 km) | ✅ 11817 Kráľova (~10 km) | ✅ TTSK | ✅ lat/lon | ✅ |
| Katarínka | ✅ | ✅ 312 m | ✅ LZPP (22 km) | ✅ 11819 J. Bohunice (~12 km) | ✅ TTSK | ✅ lat/lon | ✅ |
| Nitra lúka | ✅ | ✅ 141 m | ✅ LZNI (7.3 km) / LZPP fallback | ✅ 11855 Nitra (~3 km) | ✅ NSK | ✅ lat/lon | ✅ |

**All identifier slots: ✅ RESOLVED.**

---

## YAML schema (for code consumption)

```yaml
sites:
  - id: lzmada
    name: "LZMADA — Malý Madaras"
    lat: 48.1429562
    lon: 17.3773480
    elevation_m: 125
    timezone: "Europe/Bratislava"
    region: "Žitný ostrov"
    admin:
      okres: "Dunajská Streda"
      kraj: "Trnavský"
      kraj_code: "TTSK"              # Meteoalarm region key
    kind: airfield
    local_code: "LZMADA"
    metar_icao_primary: LZIB
    metar_icao_distance_km: 12.5
    wmo_station: 11817               # Kráľova pri Senci (~10 km NE)
    openmeteo_models: [icon_d2, icon_eu, ecmwf_ifs025]

  - id: katarinka
    name: "Lúka pri Katarínke"
    lat: 48.5500809
    lon: 17.5535781
    elevation_m: 312
    timezone: "Europe/Bratislava"
    region: "Malé Karpaty (východný svah)"
    admin:
      okres: "Trnava"
      kraj: "Trnavský"
      kraj_code: "TTSK"
    kind: meadow
    metar_icao_primary: LZPP
    metar_icao_distance_km: 22
    wmo_station: 11819               # Jaslovské Bohunice (~12 km SE)
    openmeteo_models: [icon_d2, icon_eu, ecmwf_ifs025]
    terrain_flags: [ridge_effect_W, valley_fog_risk]

  - id: nitra-luka
    name: "Lúka pri Nitre"
    lat: 48.3187712
    lon: 18.0547891
    elevation_m: 141
    timezone: "Europe/Bratislava"
    region: "Ponitrie"
    admin:
      okres: "Nitra"
      kraj: "Nitriansky"
      kraj_code: "NSK"
    kind: meadow
    metar_icao_primary: LZNI
    metar_icao_fallback: LZPP        # LZNI METAR publishing irregular
    metar_icao_distance_km: 7.3
    wmo_station: 11855               # Nitra (~3 km E)
    openmeteo_models: [icon_d2, icon_eu, ecmwf_ifs025]
    terrain_flags: [valley_channeling_NE_SW, river_fog_risk]
```

---

## Outstanding TODOs

1. ~~WMO SYNOP station IDs~~ — **RESOLVED 2026-04-23:** all three verified via SHMÚ live station list.
2. ~~OpenWeather city IDs~~ — **RESOLVED 2026-04-23:** skip city IDs, query OWM One Call 3.0 directly by `lat, lon`.
3. **GPS precision** *(user action — cannot resolve remotely)* — coordinates above are pilot-provided; pilots confirm on-site at actual takeoff points.
4. **SHMÚ OpenDATA portal — auth + endpoint catalogue** — `meteo.shmu.sk/customer/home/opendata/` confirmed exists (REST API with CSV). Still unknown: does it require registration/API key, full endpoint list, rate limits, commercial-use licensing. Direct contact with SHMÚ may be needed. **Priority: MEDIUM** (nice-to-have; Meteoalarm + SHMÚ HTML scraping already cover warnings + observations).
5. **ALADIN/SLOVAKIA NWP access** — resolution ~4 km, SK-tuned. Access mechanism unknown. **Priority: LOW** (ICON-D2 at 2 km already gives us higher resolution). Revisit if ICON-D2 quality issues emerge.
6. **Radar tiles** — SHMÚ radar composite URLs for Lovelace card overlay. **Priority: LOW** (v2 feature).
