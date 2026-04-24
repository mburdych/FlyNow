# Phase 5 Context: Translations Fix

## Why this phase exists

After shipping v1.0, the next operational gap is localization quality in config flow:
- integration title visibility in HA config flow
- Slovak translation quality and consistency
- strict key parity between English baseline and Slovak locale

## Inputs

- `.planning/research/TRANSLATIONS-RESEARCH.md`
- `.planning/REQUIREMENTS.md` (TR-01..TR-05)
- `.planning/phases/05-translations-fix/05-01-PLAN.md`

## Scope

- Translation assets only:
  - `custom_components/flynow/strings.json`
  - `custom_components/flynow/translations/sk.json`
- No backend behavior changes outside translation rendering contract.

## Done when

- Plan `05-01-PLAN.md` is executed and summary produced.
- Verification remains passed for TR-01..TR-05.
