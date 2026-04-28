# Phase 06 Validation Architecture

## Purpose

Define Nyquist-style validation coverage for phase `06` so execution can prove the language-toggle goal is met with deterministic automated checks and focused manual UAT.

## Requirement Coverage Map

| Requirement | Validation Signals |
|---|---|
| BL-06-01 (selector UX + placement) | Build passes, selector markup present, manual check confirms collapsible settings with explicit `SK/EN` control |
| BL-06-02 (first-load detect then persist) | Source assertion for `localStorage` + `hass.language` init path, manual first-load + reload behavior |
| BL-06-03 (typed SK/EN dictionary parity) | TypeScript compile/typecheck passes with strict contracts |
| BL-06-04 (all card-authored labels/messages wired) | Build/typecheck pass + manual sweep of all card sections under both languages |
| BL-06-05 (HA `sk`/`en` verification) | Manual HA profile language scenario checks with persistent user override validation |

## Automated Validation Pipeline

1. `npm --prefix lovelace/flynow-card run typecheck`
   - Proves typed language/key contracts compile and no type regressions.
2. `npm --prefix lovelace/flynow-card run build`
   - Proves card compiles and bundle output remains valid after UI/state changes.
3. `python -c "from pathlib import Path; s=Path('lovelace/flynow-card/src/flynow-card.ts').read_text(encoding='utf-8'); assert 'localStorage' in s and 'hass.language' in s; print('init lifecycle present')"`
   - Guards deterministic persistence lifecycle implementation.
4. `python -c "from pathlib import Path; s=Path('lovelace/flynow-card/src/flynow-card.ts').read_text(encoding='utf-8'); assert 'SK' in s and 'EN' in s; print('selector labels present')"`
   - Guards explicit selector presence signal.

## Manual UAT Scenarios

1. Clear language key from browser storage, open card, confirm first render follows HA locale.
2. Toggle `SK`/`EN`, confirm immediate updates across all static card labels/messages.
3. Reload dashboard, confirm previously selected language persists.
4. Change HA user profile language after explicit selection, confirm card keeps user-selected language.
5. Expand/collapse settings row repeatedly and verify selector remains functional and keyboard reachable.

## Exit Gate

Phase is validation-complete when:
- All automated checks pass without modification to validation commands.
- All five manual UAT scenarios pass in HA.
- Any failure creates a follow-up fix task before phase completion.
