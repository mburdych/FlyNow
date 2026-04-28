# Ceiling + Fog — Correction Plan

**Source:** Code review of Cursor's ceiling+fog implementation (commit `d2f6ca9`, deployed to HAOS 2026-04-28). C7 follow-up shipped in `f398b3e` 2026-04-28.

**Status — CLOSED 2026-04-28:**
| ID | Title | Status | Resolution |
|---|---|---|---|
| C1 | Fog row warn-state CSS | ✅ DONE | Implemented in base commit `d2f6ca9` (Cursor included risk-aware classes upfront — review missed it) |
| C2 | Card SK/EN labels | ✅ DONE | Implemented in base commit `d2f6ca9` |
| C3 | Alias parity test | ❌ OBSOLETE | Aliases removed in C7 — no test target left |
| C4 | Trend monotonicity | 📤 DEFERRED | Push to v1.2 fog hardening phase (nice-to-have, not user-facing bug) |
| C5 | Pilot-tunable fog heuristic | 📤 DEFERRED → phase 09 | Run `/gsd-add-backlog` when starting v1.2 milestone |
| C6 | Visibility series dedup | 📤 DEFERRED | Push to v1.2 (pure refactor, no behavior change) |
| **C7** | **Drop cloud-base check entirely** | ✅ DONE | Commit `f398b3e` — entry version bumped to 2, async_migrate_entry strips `min_ceiling_m` |

**Outcome:** Document closed. Code in master `f398b3e`. Deploy pending (HAOS network access). C4-C6 carried forward to v1.2 milestone planning.

---

## 🔴 MUST FIX (ship blockers)

### C1. Fog row visual: HIGH risk must not look green

**File:** [`lovelace/flynow-card/src/flynow-card.ts`](lovelace/flynow-card/src/flynow-card.ts)
**Symptom:** `renderFogRiskRow()` always emits `<span class="result-pass">INFO</span>`, so a `value="high"` fog risk shows the green PASS badge — false safety signal to the crew.

**Change:**
1. In `renderFogRiskRow()` (around line 358-366), replace the hardcoded `result-pass` class with a risk-aware class:
   ```ts
   private renderFogRiskRow(item: FlyNowConditionValue | undefined): TemplateResult {
     if (!item) return html``;
     const risk = this.formatValue(item.value).toUpperCase();
     const trend = item.trend ? ` (${item.trend})` : "";
     const riskClass = this.fogRiskClass(item.value);
     const badge = this.fogRiskBadge(item.value);
     return html`<div class="condition-row">
       <span>Fog risk</span>
       <span>${risk}${trend}</span>
       <span class="${riskClass}">${badge}</span>
     </div>`;
   }

   private fogRiskClass(value: number | string | null | undefined): string {
     switch (value) {
       case "high": return "result-fail";
       case "medium": return "result-warn";
       case "low-medium": return "result-warn";
       default: return "result-pass";
     }
   }

   private fogRiskBadge(value: number | string | null | undefined): string {
     return value === "high" ? "RISK" : value === "low" ? "OK" : "INFO";
   }
   ```
2. Add CSS for `.result-warn` (amber) in the card's styles block. Match the pattern used by `result-pass` / `result-fail` (look near existing condition-row styling).

**Acceptance:**
- HIGH → red `RISK` badge.
- MEDIUM / LOW-MEDIUM → amber `INFO` badge.
- LOW → green `OK` badge.
- Manual: load card with mocked `fog_risk.value = "high"` → red.

---

### C2. Card i18n: Slovak user sees English labels

**File:** [`lovelace/flynow-card/src/flynow-card.ts`](lovelace/flynow-card/src/flynow-card.ts)
**Symptom:** `"Cloud base (m AGL)"`, `"Fog risk"`, `"Surface wind"`, `"Altitude wind"`, `"Precipitation probability"`, `"Visibility"`, `"INFO"`, `"PASS"`, `"FAIL"`, section title `"Condition thresholds"` are all hardcoded English. Phase 06 already exists for full card language toggle, but the **new ceiling/fog labels** widen the gap visibly for the SK user RIGHT NOW.

**Two acceptable options — pick one:**

**Option A (minimal, ship now):** Add a tiny built-in label dictionary keyed on `hass.language` (already available on the card), no UI toggle. Covers only the new labels added by this change set. Avoids enlarging 06 scope.

```ts
private get labels() {
  const lang = (this.hass?.language ?? "en").toLowerCase().startsWith("sk") ? "sk" : "en";
  const dict = {
    en: { cloudBase: "Cloud base (m AGL)", fogRisk: "Fog risk", section: "Condition thresholds",
          surfaceWind: "Surface wind", altitudeWind: "Altitude wind",
          precipitation: "Precipitation probability", visibility: "Visibility",
          pass: "PASS", fail: "FAIL", info: "INFO", risk: "RISK", ok: "OK" },
    sk: { cloudBase: "Spodná hranica oblačnosti (m AGL)", fogRisk: "Riziko hmly",
          section: "Podmienky", surfaceWind: "Vietor pri zemi", altitudeWind: "Vietor vo výške",
          precipitation: "Pravdepodobnosť zrážok", visibility: "Dohľadnosť",
          pass: "OK", fail: "ZLE", info: "INFO", risk: "RIZIKO", ok: "OK" },
  };
  return dict[lang];
}
```
Then replace all hardcoded strings via `${this.labels.cloudBase}` etc.

**Option B (defer):** Explicitly add the new English labels to phase 06 task list and ship as-is.

**Recommendation:** Option A — it's <30 LOC, ships consistent UX immediately, and 06 still owns the full toggle later.

**Acceptance (Option A):**
- HA running with `language: sk` → card shows `"Spodná hranica oblačnosti"`, `"Riziko hmly"`.
- HA `language: en` → unchanged English.
- Test: snapshot of card rendered with both `hass.language = "sk"` and `"en"`.

---

### C3. Backward-compat alias regression test

**File:** [`tests/test_analyzer.py`](tests/test_analyzer.py)
**Symptom:** `analyzer.py` emits `cloud_base_min_m`, `ceiling_m`, and `ceiling` as three copies of the same dict via `{**cloud_base}`. No test asserts they stay in sync. A future refactor could silently break payload consumers reading the old keys.

**Change:** Append to `tests/test_analyzer.py`:
```py
def test_analyzer_keeps_legacy_ceiling_aliases_in_sync():
    hourly = {
        "wind_speed_10m": [2.0],
        "wind_speed_975hPa": [5.0],
        "wind_speed_925hPa": [5.0],
        "precipitation_probability": [0],
        "cloud_base": [800],
        "cloud_cover": [40],
        "visibility": [10000],
    }
    cfg = {
        "max_surface_wind_ms": 4.0, "max_altitude_wind_ms": 10.0,
        "max_precip_prob_pct": 20.0, "min_ceiling_m": 500.0, "min_visibility_km": 5.0,
    }
    conditions = analyze_window(hourly, cfg)["conditions"]
    primary = conditions["cloud_base_min_m"]
    for alias_key in ("ceiling_m", "ceiling"):
        alias = conditions[alias_key]
        assert alias["ok"] == primary["ok"]
        assert alias["value"] == primary["value"]
        assert alias["threshold"] == primary["threshold"]
        assert alias.get("reason") == primary.get("reason")
```

**Acceptance:** Test passes. If anyone later changes alias logic to filter fields, this test fails first.

---

## 🟡 NICE TO HAVE (follow-up — can land in same PR if cheap)

### C4. Trend logic: use monotonicity, not just first-vs-last

**File:** [`custom_components/flynow/analyzer.py`](custom_components/flynow/analyzer.py) lines 114-119.
**Symptom:** Current trend uses `vis_km[-1] - vis_km[0]` which misses non-monotonic windows (good→fog→good = "stable") and requires BOTH visibility AND spread to move significantly (`AND` is too strict — visibility alone is usually enough signal).

**Change:** Replace the trend block with:
```py
trend = "stable"
def _direction(series: list[float]) -> int:
    """+1 if monotonically improving, -1 if worsening, 0 mixed."""
    if len(series) < 2: return 0
    diffs = [series[i] - series[i-1] for i in range(1, len(series))]
    if all(d >= 0 for d in diffs) and series[-1] - series[0] > 0: return 1
    if all(d <= 0 for d in diffs) and series[0] - series[-1] > 0: return -1
    return 0

vis_dir = _direction(vis_km)
spread_dir = _direction(spread_values)
# Visibility is the stronger signal; spread acts as a tiebreaker.
if vis_dir == 1 or (vis_dir == 0 and spread_dir == 1):
    trend = "improving"
elif vis_dir == -1 or (vis_dir == 0 and spread_dir == -1):
    trend = "worsening"
```

**Acceptance:** New unit tests for:
- Monotonic improving visibility → "improving".
- Non-monotonic (good→bad→good) → "stable".
- Visibility flat + spread closing → "worsening".

---

### C5. Add backlog item for fog heuristic tunability

**Action:** Run `/gsd-add-backlog` with description:
> Pilot-tunable fog heuristic — surface the visibility / humidity / dew-point-spread thresholds (currently hardcoded 1.0/3.0 km, 95%/90%, 1.5/2.5°C in `_fog_risk()`) into config flow so each pilot/region can calibrate. Optional: per-launch-site overrides driven by `terrain_flags` (e.g. `valley_fog_risk` from launch-sites.md raises sensitivity).

This becomes phase 09. Do NOT bundle into this correction PR — it needs its own discuss-phase to figure out config UX.

---

### C6. Remove visibility duplication

**File:** [`custom_components/flynow/analyzer.py`](custom_components/flynow/analyzer.py)
**Symptom:** `visibility` is parsed in both `_fog_risk()` (`vis_values = _clean_numeric(...)`) and `analyze_window()` (`visibility_km = _safe_min(...)`). Same field, two parses.

**Change:** Extract `_visibility_km_series()` helper returning `(min_km, all_km)` and consume from both sites. Pure refactor — no behavior change. Skip if you want to keep the diff small.

---

## 🔴 C7. Drop cloud-base check entirely (added 2026-04-28)

**Decision:** User dropped cloud-base from the product. No card row, no GO/NO-GO contribution, no API field, no config option. Existing `config_entries` get migrated to remove orphan `min_ceiling_m`. **Aliases are removed (no `ceiling`/`ceiling_m` in payload).** This obsoletes C3.

### C7.1 — `custom_components/flynow/const.py`

Remove these lines:
```py
CONF_MIN_CEILING_M = "min_ceiling_m"
DEFAULT_MIN_CEILING_M = 500
MIN_CEILING_M = 100
MAX_CEILING_M = 5000
```
Add (right next to `DOMAIN`):
```py
CONFIG_VERSION = 2  # bump on cloud-base removal; triggers async_migrate_entry
```

### C7.2 — `custom_components/flynow/manifest.json`

No changes (manifest version is integration version, separate from config entry version).

### C7.3 — `custom_components/flynow/__init__.py`

Add migration before `async_setup_entry`:
```py
from .const import CONFIG_VERSION

async def async_migrate_entry(hass: Any, entry: Any) -> bool:
    if entry.version >= CONFIG_VERSION:
        return True
    new_data = {k: v for k, v in entry.data.items() if k != "min_ceiling_m"}
    hass.config_entries.async_update_entry(entry, data=new_data, version=CONFIG_VERSION)
    return True
```
Update `async_setup_entry` first line:
```py
async def async_setup_entry(hass: Any, entry: Any) -> bool:
    # entry.version is now CONFIG_VERSION after migration
    hass.data.setdefault(DOMAIN, {})
    ...
```
Note: also need to set `version=CONFIG_VERSION` in the ConfigFlow class (see C7.4).

### C7.4 — `custom_components/flynow/config_flow.py`

1. Remove all `CONF_MIN_CEILING_M`, `DEFAULT_MIN_CEILING_M`, `MIN_CEILING_M`, `MAX_CEILING_M` imports.
2. Remove the `min_ceiling_m` line from `(checks = [...]` validator block (around line 160).
3. Remove the `vol.Required(CONF_MIN_CEILING_M, default=DEFAULT_MIN_CEILING_M): vol.Coerce(int),` line from the schema (around line 184).
4. Add to the ConfigFlow class:
   ```py
   from .const import CONFIG_VERSION

   class FlyNowConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
       VERSION = CONFIG_VERSION
   ```
   (find the existing class declaration and add `VERSION = CONFIG_VERSION` as the first class attribute.)

### C7.5 — `custom_components/flynow/coordinator.py`

1. Remove `CONF_MIN_CEILING_M` from imports (line ~23).
2. Remove this line from the `thresholds` dict (~line 82):
   ```py
   "min_ceiling_m": float(self._config[CONF_MIN_CEILING_M]),
   ```

### C7.6 — `custom_components/flynow/analyzer.py`

1. Delete the entire `_cloud_base_metric()` function (~lines 142-165).
2. In `analyze_window()`, remove these lines:
   ```py
   cloud_base = _cloud_base_metric(hourly_slice, float(config["min_ceiling_m"]))
   ...
   "cloud_base_min_m": cloud_base,
   "ceiling_m": {**cloud_base},
   "ceiling": {**cloud_base},
   ```
3. Final `checks` dict should contain only: `surface_wind_ms`, `altitude_wind_ms`, `precip_prob`, `visibility_km`, `fog_risk`.

### C7.7 — `custom_components/flynow/open_meteo.py`

Remove from `HOURLY_FIELDS`:
```py
"cloud_cover",
"cloud_base",
```
Plus the comment block about `ceiling`. Keep `relative_humidity_2m`, `temperature_2m`, `dew_point_2m` (used by fog).

### C7.8 — `custom_components/flynow/strings.json` + `translations/sk.json`

In both files, remove the `min_ceiling_m` keys from BOTH the `data` and `data_description` blocks under the thresholds step.

### C7.9 — `lovelace/flynow-card/src/types.ts`

Remove from `FlyNowConditionSet`:
```ts
cloud_base_min_m?: FlyNowConditionValue;
ceiling?: FlyNowConditionValue;
ceiling_m?: FlyNowConditionValue;
```

### C7.10 — `lovelace/flynow-card/src/flynow-card.ts`

In `renderConditions()`:
1. Remove the `cloudBase` const declaration.
2. Remove the `${this.renderConditionRow("Cloud base (m AGL)", cloudBase)}` line (in SK dictionary the key/usage too).
3. If the SK label dictionary has `cloudBase` entry, remove from both `en` and `sk` dicts.

### C7.11 — `tests/test_analyzer.py`

1. Delete entirely: `test_analyzer_does_not_fail_cloud_base_when_clear_sky_and_missing_cloud_base`.
2. In `test_analyzer_strict_and_logic`: remove asserts referencing `cloud_base_min_m`, `ceiling_m`, `ceiling`. Remove `min_ceiling_m` from the `cfg` dict.
3. In `test_analyzer_handles_none_values_without_crash`: remove the `cloud_base_min_m` asserts and the `min_ceiling_m` from `cfg`.
4. In `test_analyzer_reports_fog_risk_metadata`: remove `min_ceiling_m` from `cfg`, remove `cloud_base` and `cloud_cover` from `hourly`.

### C7.12 — Acceptance

After deploy + restart:
- Card shows 5 condition rows (was 6): Surface wind, Altitude wind, Precipitation, Visibility, Fog risk.
- Config flow "thresholds" step has 4 fields (was 5).
- HA log: clean restart, no `KeyError: 'min_ceiling_m'` from existing entries (migration handles it).
- `pytest tests/` green.
- ruff + mypy clean.

### C7.13 — Verify migration worked on HAOS

After deploy, in Web Terminal:
```bash
sudo grep -A20 '"flynow"' /config/.storage/core.config_entries | grep -E 'version|min_ceiling_m'
# Expect: "version": 2  AND  no min_ceiling_m line
```

---

## ❌ Out of scope for this correction PR

- **Wind shear analysis.** Mentioned in original plan but never implemented. Track as separate phase.
- **Fog as GO/NO-GO blocker.** Original plan said "additive first" — keep `blocking=False`. Promotion to blocker is a v2 decision.
- ~~Config key rename `min_ceiling_m` → `min_cloud_base_m`~~ — moot, key removed entirely (C7).

---

## Suggested commit sequence (revised after C7)

**Ship batch (C1 + C7) — recommended single deploy:**
1. `feat(flynow)!: drop cloud-base check from product (C7)` — breaking config schema, includes migration. Bump entry version to 2.
2. `fix(card): risk-aware fog row badge (C1)` — keeps red HIGH visible.

**Follow-up (no rush):**
3. `refactor(analyzer): monotonic fog trend detection (C4)`.
4. `chore(planning): phase 09 fog heuristic tunability (C5)` — via `/gsd-add-backlog`.
5. (optional) `refactor(analyzer): dedupe visibility series parsing (C6)`.

C2 already done in base. C3 obsoleted by C7 (no aliases to test).

---

## Verification before merge

```bash
# Python
ruff check custom_components/flynow/
mypy custom_components/flynow/
pytest tests/

# Card
cd lovelace/flynow-card && npm run build && npm test  # if test script exists

# Manual HA smoke (cez SSH to HAOS — see .planning/reference/HAOS-DEPLOYMENT.md)
# - Reload integration, reload Lovelace.
# - Switch HA language EN ↔ SK, confirm card labels switch.
# - Mock cloud_base=null with cloud_cover=10 → confirm row shows "n/a / 500 threshold" PASS.
# - Mock fog_risk.value="high" → confirm red RISK badge.
```
