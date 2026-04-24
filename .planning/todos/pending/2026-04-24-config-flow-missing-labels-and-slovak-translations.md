---
created: 2026-04-24T12:16:14.011Z
title: Config flow UI shows raw variable names in English
area: integration
files:
  - custom_components/flynow/strings.json
  - custom_components/flynow/config_flow.py
  - custom_components/flynow/translations/sk.json (to be created)
---

## Problem

Pri prvom spustení config flow po deployi na HAOS (192.168.68.111, HA 2026.4.3, HA language=sk) zobrazuje dialóg **surové názvy premenných namiesto ľudských popisov, a všetko po anglicky**. Screenshot ukázal tieto polia v poslednom kroku:

- `max_surface_wind_ms`
- `max_altitude_wind_ms`
- `min_ceiling_m`
- `max_precip_prob_pct`
- `min_visibility_km`

Problém zasahuje **všetky kroky** config flow (site, times, thresholds, notifiers), nie iba ten zobrazený na screenshote.

## Root cause

1. `strings.json` pre každý `config.step.<step>` pravdepodobne chýba sekcia `data` (popis poľa) a/alebo `data_description` (pomocný popis pod poľom). Bez nich HA frontend fallbackuje na key name (napr. `max_surface_wind_ms`).
2. Chýba `translations/sk.json` — HA detekuje `language=sk` v `.storage/core.config` a hľadá slovenské preklady; ak neexistujú, padne späť na `strings.json` (anglický default).

## Solution

1. **Doplniť `strings.json`** — pre každý config step pridať kompletné `data` + `data_description`:
   ```json
   {
     "config": {
       "step": {
         "thresholds": {
           "title": "Go/no-go thresholds",
           "description": "Maximum and minimum values that define a flyable window.",
           "data": {
             "max_surface_wind_ms": "Max surface wind (m/s)",
             "max_altitude_wind_ms": "Max altitude wind (m/s)",
             "min_ceiling_m": "Minimum cloud ceiling (m)",
             "max_precip_prob_pct": "Max precipitation probability (%)",
             "min_visibility_km": "Minimum visibility (km)"
           },
           "data_description": {
             "max_surface_wind_ms": "Balloon launches require calm surface wind.",
             ...
           }
         }
       }
     }
   }
   ```
2. **Vytvoriť `translations/sk.json`** s rovnakou štruktúrou a slovenskými textami. HA ho načíta automaticky podľa `language=sk`.
3. **Zachovať krokové štruktúry** — config_flow.py má viac `async_step_*` metód (site, windows, thresholds, notifiers); každá musí mať svoj blok v oboch JSON-och.
4. Po zmene: re-deploy (tar+SSH) a reštart HA; preklad sa načíta bez reinštalácie integrácie.

## Context

- Objavené pri **prvom UAT config flow** po deployi, 2026-04-24.
- Súvisiaci bug: submit posledného kroku padá s `expected float` na wind/visibility polia — riešené samostatne (schéma validácie v `config_flow.py`).
- Reference: HA dev docs — Integration translations https://developers.home-assistant.io/docs/internationalization/custom_integration/
