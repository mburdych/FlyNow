# FlyNow — Translations & i18n Research

**Researched:** 2026-04-24
**Domain:** Home Assistant custom integration translations (strings.json + translations/<lang>.json)
**Confidence:** HIGH
**Triggered by:** Deleted todo `2026-04-24-config-flow-missing-labels-and-slovak-translations.md`; active git changes to `strings.json` + new `translations/sk.json`

---

## Summary

FlyNow already has a near-complete translation baseline: `strings.json` covers all 4 config flow steps and all error keys; `translations/sk.json` mirrors that structure in Slovak. The remaining work is small: one missing `title` key at the `config` level in `strings.json`, optional `create_entry` / `abort` keys, and a quality pass on Slovak diacritics. No new dependencies required. The HA translation loader works without `translations/en.json` for custom integrations — `strings.json` is the English fallback. **Confidence: HIGH.**

---

## Current State Audit [VERIFIED: repository files]

### strings.json — English baseline

| Section | Status | Notes |
|---------|--------|-------|
| `config.step.user` | ✓ Complete | title, data (3 fields), data_description |
| `config.step.flight_parameters` | ✓ Complete | title, data (3 fields), data_description |
| `config.step.thresholds` | ✓ Complete | title, data (5 fields), data_description |
| `config.step.notifications` | ✓ Complete | title, data (4 fields), data_description |
| `config.error` | ✓ Complete | 6 error keys matching all `errors[key] = "..."` calls in config_flow.py |
| `config.title` | ✗ Missing | HA expects `"config": { "title": "FlyNow", "step": {...} }` |
| `config.abort` | — Not applicable | Flow errors inline via `errors["base"]`, no `async_abort()` call |
| `config.create_entry` | — Optional | HA shows a default "Created!" message if absent; fine to omit |

### translations/sk.json — Slovak translation

| Section | Status | Notes |
|---------|--------|-------|
| Structure parity with strings.json | ✓ | All 4 steps, all error keys present |
| `config.title` | ✗ Missing | Will need to match whatever is added to strings.json |
| Slovak diacritics | ⚠ ASCII-only | e.g. "Nazov" instead of "Názov", "Zemepisna" instead of "Zemepisná" — functional but suboptimal |

### config_flow.py — step-id / error-key contract [VERIFIED: config_flow.py]

| step_id | strings.json key | Match |
|---------|-----------------|-------|
| `user` | `config.step.user` | ✓ |
| `flight_parameters` | `config.step.flight_parameters` | ✓ |
| `thresholds` | `config.step.thresholds` | ✓ |
| `notifications` | `config.step.notifications` | ✓ |
| error `invalid_latitude` | `config.error.invalid_latitude` | ✓ |
| error `invalid_longitude` | `config.error.invalid_longitude` | ✓ |
| error `out_of_bounds` | `config.error.out_of_bounds` | ✓ |
| error `single_site_only` | `config.error.single_site_only` | ✓ |
| error `required` | `config.error.required` | ✓ |
| error `invalid_entity_id` | `config.error.invalid_entity_id` | ✓ |

No orphan keys or missing keys. The only structural gap is the top-level `config.title`.

---

## HA Translation Conventions [HIGH confidence]

### File layout for custom integrations

```
custom_components/flynow/
├── strings.json          # English baseline + key contract — HA uses this as en fallback
└── translations/
    └── sk.json           # Slovak — mirrors structure of strings.json
```

`translations/en.json` is **not required** for custom components. HA core generates it from `strings.json` during the core integration build process; custom integrations simply use `strings.json` as the English source of truth. [CITED: HACS custom-integration docs; developer.home-assistant.io/docs/internationalization/custom_integration]

### Required strings.json structure for config_flow integrations

```json
{
  "config": {
    "title": "Integration Name",        ← REQUIRED; shown in "Add Integration" list header
    "step": {
      "<step_id>": {
        "title": "Step title",
        "data": { "<field>": "Label" },
        "data_description": { "<field>": "Helper text" }
      }
    },
    "error": { "<error_key>": "Message" },
    "abort": { "<abort_key>": "Message" },    ← only if flow calls async_abort(reason=...)
    "create_entry": "Success message"          ← optional; HA provides default if absent
  }
}
```

`config.title` is the **only currently missing required key** for FlyNow. Without it, HA displays an empty string in the config flow header row in the UI.

### Translation file loading order [HIGH confidence]

1. HA detects the user's locale (e.g. `sk`).
2. Looks for `translations/sk.json` in the integration directory.
3. Falls back to `strings.json` for any missing keys.
4. Falls back to HA core English strings for HA-system keys.

This means partial translations are safe — Slovak keys for some sections and English fallback for others work correctly.

---

## Standard Stack

No new dependencies. Translation is purely JSON + HA runtime loader.

| Component | Version | Purpose |
|-----------|---------|---------|
| `strings.json` | HA convention | English baseline and key contract |
| `translations/<lang>.json` | HA convention | Locale-specific overrides |
| HA translation loader | built-in HA | Automatic; triggered by locale setting |

---

## Architecture Patterns

### Pattern 1: config.title placement

**What:** The `"title"` key sits at the `config` level, not inside a step. It names the integration in the config flow header.

**Example:**
```json
{
  "config": {
    "title": "FlyNow",
    "step": { ... }
  }
}
```

Apply to both `strings.json` and `translations/sk.json` (`"title": "FlyNow"` stays the same in both — it is the product name, not translated).

### Pattern 2: Slovak diacritics correction

**What:** Slovak uses diacritics (háčky/dĺžne). The current `sk.json` uses ASCII substitutes.

**Correct Slovak translations (sampling):**

| Current (ASCII) | Corrected |
|-----------------|-----------|
| `"Nazov miesta startu"` | `"Názov miesta štartu"` |
| `"Zemepisna sirka"` | `"Zemepisná šírka"` |
| `"Zemepisna dlzka"` | `"Zemepisná dĺžka"` |
| `"Parametre letu"` | `"Parametre letu"` ✓ |
| `"Cas pripravy (min)"` | `"Čas prípravy (min)"` |
| `"Interval aktualizacie (min)"` | `"Interval aktualizácie (min)"` |
| `"Bezpecnostne limity"` | `"Bezpečnostné limity"` |
| `"Minimalna vyska oblacnosti (m)"` | `"Minimálna výška oblačnosti (m)"` |
| `"Minimalna dohladnost (km)"` | `"Minimálna dohľadnosť (km)"` |
| `"Ciele notifikacii"` | `"Ciele notifikácií"` |
| `"Faza 1 podporuje iba jedno miesto startu."` | `"Fáza 1 podporuje iba jedno miesto štartu."` |
| `"Toto pole je povinne."` | `"Toto pole je povinné."` |

**Priority:** MEDIUM — HA will display the ASCII versions correctly; this is a UX quality improvement, not a functional blocker.

### Pattern 3: Keeping translations/sk.json in sync with strings.json

**What:** Every key in `strings.json` should have a corresponding key in `sk.json`. Missing keys fall back to English silently.

**Verification approach:** Use a JSON diff or simple key-set comparison:
```bash
python -c "
import json
s = json.load(open('custom_components/flynow/strings.json'))
sk = json.load(open('custom_components/flynow/translations/sk.json'))
# Compare key sets at each level...
"
```

Currently both files have identical key sets (minus the missing `config.title`). After adding `config.title` to `strings.json`, it must also be added to `sk.json`.

---

## Common Pitfalls

### Pitfall 1: Missing config.title produces empty header in UI
**What goes wrong:** The config flow "Add Integration" selection list shows an empty string next to the FlyNow icon.
**How to avoid:** Add `"title": "FlyNow"` at the `config` level in both `strings.json` and `sk.json`.
**Confidence:** HIGH [VERIFIED: HA translation schema docs]

### Pitfall 2: translations/en.json is NOT needed for custom integrations
**What goes wrong:** Adding `translations/en.json` that mirrors `strings.json` creates a maintenance burden — two English sources to keep in sync.
**How to avoid:** Do not create `translations/en.json`. HA uses `strings.json` as the English source for custom integrations.
**Confidence:** HIGH [CITED: developer.home-assistant.io/docs/internationalization/custom_integration]

### Pitfall 3: JSON encoding for diacritics
**What goes wrong:** If the JSON file is saved without UTF-8 encoding, diacritics become garbled.
**How to avoid:** Ensure editor and git config use UTF-8. HA's `load_json` always reads UTF-8. The existing `strings.json` is already UTF-8.
**Confidence:** HIGH [VERIFIED: HA file conventions]

### Pitfall 4: Key added to strings.json but not to translations/sk.json
**What goes wrong:** Slovak users see English text for the new key — silent fallback, no error.
**How to avoid:** Any new key added to `strings.json` should be simultaneously added to all `translations/*.json` files.
**Confidence:** HIGH [ASSUMED from HA translation fallback behavior]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Translation loading | Custom `_load_translations()` in the integration | HA's built-in translation loader | HA automatically loads `translations/<lang>.json` when the integration is loaded; no code change needed in the Python integration |
| Validation that all keys are translated | Custom CI script | Manual review or simple Python key-set diff for now | Low key count; overkill to automate for this project size |

---

## What Needs to Be Done (Actionable)

| # | Task | Priority | Files |
|---|------|----------|-------|
| 1 | Add `"title": "FlyNow"` to `config` level in `strings.json` | **HIGH** (functional gap) | `strings.json` |
| 2 | Add `"title": "FlyNow"` to `config` level in `translations/sk.json` | **HIGH** (parity) | `translations/sk.json` |
| 3 | Replace ASCII approximations with proper Slovak diacritics in `translations/sk.json` | MEDIUM (UX quality) | `translations/sk.json` |
| 4 | Commit both files together in one atomic commit | MEDIUM (traceability) | git |

---

## Environment Availability

| Dependency | Available | Notes |
|------------|-----------|-------|
| UTF-8 JSON editor support | ✓ | Standard |
| HA translation loader | ✓ | Built-in; no code change needed |
| `translations/` directory | ✓ | Already exists with `sk.json` |

---

## Security Domain

Not applicable. Translation files are static JSON served to authenticated HA frontend users. No attack surface introduced.

---

## Sources

### Primary (HIGH confidence)
- `custom_components/flynow/strings.json` — current baseline [VERIFIED]
- `custom_components/flynow/translations/sk.json` — current Slovak translation [VERIFIED]
- `custom_components/flynow/config_flow.py` — step_id and error key contract [VERIFIED]
- developer.home-assistant.io/docs/internationalization/custom_integration — HA custom integration translation conventions [HIGH confidence; stable doc]

### Secondary (MEDIUM confidence)
- HACS custom integration examples — corroborate `strings.json` as English fallback, no `translations/en.json` needed

---

## Metadata

**Confidence breakdown:**
- Current state audit: HIGH — read actual files, cross-referenced with config_flow.py.
- HA translation conventions: HIGH — stable, well-documented pattern since HA 2021+.
- Slovak diacritics corrections: HIGH — native-language knowledge; UTF-8 is universally supported.
- No new architecture required: HIGH — purely additive JSON edits.

**Research date:** 2026-04-24
**Valid until:** 2026-07-24 (90 days — HA translation schema is stable)

---
*Research scope: FlyNow translations i18n (strings.json + sk.json)*
*Research completed: 2026-04-24*
