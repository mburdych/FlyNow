# Phase 06: Lovelace Card Language Toggle (BACKLOG) - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a user-facing language switch to the FlyNow Lovelace card so users can explicitly choose `sk` or `en`. Automatic detection is allowed only on first load when no preference exists; after that, the card must honor the user-selected language independent of browser or Home Assistant locale defaults.

</domain>

<decisions>
## Implementation Decisions

### Language Selector UX
- **D-01:** Place the language switcher in the card header as an explicit `SK/EN` segmented control.
- **D-02:** Switching is one-tap direct toggle between Slovak and English.
- **D-03:** Selector is placed inside a collapsible settings panel instead of always-on display.

### Persistence Policy
- **D-04:** Persist language choice in card frontend storage using a dedicated `localStorage` key.
- **D-05:** On first load (no saved preference), detect from `hass.language` once and immediately persist the inferred choice.
- **D-06:** If stored value is missing/invalid, re-run first-load detection and overwrite with a valid value.

### Translation Architecture
- **D-07:** Use one typed runtime dictionary object keyed by language and translation key.
- **D-08:** Enforce strict SK/EN key parity via shared TypeScript contracts.
- **D-09:** Missing runtime key falls back to English for that key while continuing to render.

### Claude's Discretion
- Exact iconography, spacing, and animation details of the collapsible language settings row.
- Exact localStorage key name and helper function placement in card source structure.
- Internal helper naming for dictionary access and fallback wrappers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Backlog Scope
- `.planning/ROADMAP.md` — Phase `06` goal and task checklist for language toggle behavior.

### Product Constraints
- `.planning/PROJECT.md` — current value and requirement context for shipped card behavior expectations.

### Prior Decisions
- `.planning/phases/02-notifications-card/02-CONTEXT.md` — reactive card behavior and threshold-rendering constraints.
- `.planning/phases/04-multi-site-forecast-planning-card/04-CONTEXT.md` — current card information hierarchy and multi-site UI structure.
- `.planning/phases/05-translations-fix/05-CONTEXT.md` — translation parity intent and localization quality expectations.

### Current Card Implementation
- `lovelace/flynow-card/src/flynow-card.ts` — existing locale detection (`hass.language`) and hardcoded label usage to refactor.
- `lovelace/flynow-card/src/types.ts` — frontend typing contracts that translation helpers must remain compatible with.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FlyNowCard.labels` getter in `lovelace/flynow-card/src/flynow-card.ts`: existing bilingual label surface that can be replaced by typed dictionary lookup.
- Existing `localStorage` usage (`flynow.last_balloon`) in `flynow-card.ts`: demonstrates established persistence pattern in this card.

### Established Patterns
- Card rendering is LitElement reactive and centralized through `render()` and section helpers; language switching should trigger immediate rerender through reactive state.
- Existing SK/EN switch logic currently derives from `this.hass?.language`, proving locale context is already available.

### Integration Points
- New toggle state should be consumed by `labels` (or replacement helper) so all sections (status chips, thresholds, launch text, log form, history states) use the same selected language.
- Selector UI belongs in `render()` card body flow without breaking site summary/details/log section ordering.

</code_context>

<specifics>
## Specific Ideas

- Keep the selector explicit and easy to trigger (one tap), but tucked into collapsible settings to reduce visual noise.
- Respect user agency over automatic locale behavior by persisting first inferred language immediately and honoring explicit changes afterward.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 06-lovelace-card-language-toggle-backlog*
*Context gathered: 2026-04-28*
