# Ceiling + Fog — Correction Plan

**Source:** Code review of Cursor's ceiling+fog implementation (commit pending, files modified: `analyzer.py`, `open_meteo.py`, `strings.json`, `sk.json`, `flynow-card.ts`, `types.ts`, `test_analyzer.py`).

**Goal:** Close the gaps surfaced in review before this work is shipped. Coordinator wiring is already clean (verified — `analyze_window()` output flows through `**` spread in [`coordinator.py:121-124`](custom_components/flynow/coordinator.py#L121-L124), no whitelist).

**How to run:** Open this file in Cursor, then `/gsd-quick` or `/gsd-plan-phase` (depending on whether you want full PLAN ceremony). Tasks are ordered by priority — MUST FIX first, then NICE TO HAVE.

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
**Symptom:** `"Cloud base (m AGL)"`, `"Fog risk"`, `"Surface wind"`, `"Altitude wind"`, `"Precipitation probability"`, `"Visibility"`, `"INFO"`, `"PASS"`, `"FAIL"`, section title `"Condition thresholds"` are all hardcoded English. Backlog item 999.1 already exists for full card language toggle, but the **new ceiling/fog labels** widen the gap visibly for the SK user RIGHT NOW.

**Two acceptable options — pick one:**

**Option A (minimal, ship now):** Add a tiny built-in label dictionary keyed on `hass.language` (already available on the card), no UI toggle. Covers only the new labels added by this change set. Avoids enlarging 999.1 scope.

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

**Option B (defer):** Explicitly add the new English labels to backlog 999.1 task list and ship as-is.

**Recommendation:** Option A — it's <30 LOC, ships consistent UX immediately, and 999.1 still owns the full toggle later.

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

This becomes 999.4. Do NOT bundle into this correction PR — it needs its own discuss-phase to figure out config UX.

---

### C6. Remove visibility duplication

**File:** [`custom_components/flynow/analyzer.py`](custom_components/flynow/analyzer.py)
**Symptom:** `visibility` is parsed in both `_fog_risk()` (`vis_values = _clean_numeric(...)`) and `analyze_window()` (`visibility_km = _safe_min(...)`). Same field, two parses.

**Change:** Extract `_visibility_km_series()` helper returning `(min_km, all_km)` and consume from both sites. Pure refactor — no behavior change. Skip if you want to keep the diff small.

---

## ❌ Out of scope for this correction PR

- **Config key rename** `min_ceiling_m` → `min_cloud_base_m`. Would break existing `config_entries`. Do as a separate migration phase in v1.2 if at all (Cursor's choice to keep the legacy key was correct).
- **Wind shear analysis.** Mentioned in original plan but never implemented. Track as separate phase.
- **Fog as GO/NO-GO blocker.** Original plan said "additive first" — keep `blocking=False`. Promotion to blocker is a v2 decision.

---

## Suggested commit sequence

1. `fix(card): risk-aware fog row badge (C1)` — small, isolated, easy to review.
2. `feat(card): minimal SK/EN label dictionary for new ceiling+fog rows (C2)` — option A.
3. `test(analyzer): assert ceiling alias parity (C3)` — guards future regressions.
4. `refactor(analyzer): monotonic fog trend detection (C4)` — only if you want it now.
5. `chore(planning): backlog 999.4 fog heuristic tunability (C5)` — via `/gsd-add-backlog`.
6. (optional) `refactor(analyzer): dedupe visibility series parsing (C6)`.

Each commit independently testable. C1+C2+C3 = minimum ship. C4-C6 = polish.

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
