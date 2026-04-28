# Phase 09: Fog Risk Hardening — Trend Monotonicity, Dedup, Pilot-Tunable Thresholds - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 09-fog-risk-hardening-trend-monotonicity-dedup-pilot-tunable-thresholds
**Areas discussed:** Trend monotonicity strategy, Dedup scope, Fog threshold tunability surface, Rollout boundary
**Mode:** `--auto` (recommended defaults selected)

---

## Trend monotonicity strategy

| Option | Description | Selected |
|--------|-------------|----------|
| First-vs-last deltas only | Keep current endpoint delta logic for visibility + spread | |
| Monotonic direction model | Use full-series monotonic direction with visibility priority and spread as tiebreaker | ✓ |
| Aggressive directional labeling | Mark trend from net movement even when series is non-monotonic | |

**Auto choice:** Monotonic direction model.
**Notes:** Chosen as the safest hardening path to avoid false trend labels from noisy windows while still detecting meaningful direction.

---

## Dedup scope

| Option | Description | Selected |
|--------|-------------|----------|
| Keep duplicate parsing | Leave visibility parsing in both `_fog_risk()` and `analyze_window()` | |
| Shared helper refactor | Introduce one visibility-series helper reused in both call sites; preserve behavior | ✓ |
| Broader cross-module dedup | Expand dedup to card/sensor/notification payload generation now | |

**Auto choice:** Shared helper refactor.
**Notes:** Keeps phase focused on C6 analyzer cleanup without broad architectural churn.

---

## Fog threshold tunability surface

| Option | Description | Selected |
|--------|-------------|----------|
| Keep hardcoded thresholds | No config changes; retain constants in `_fog_risk()` | |
| Global tunables in config flow | Add integration-level fog threshold fields with current defaults and range validation | ✓ |
| Per-site overrides now | Add site-specific fog thresholds in this same phase | |

**Auto choice:** Global tunables in config flow.
**Notes:** Aligns with C5 while avoiding per-site UX/scope expansion in this hardening pass.

---

## Rollout boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Code-side only hardening | Backend/config changes + tests; no new user-facing operational step | ✓ |
| Partial UI exposure | Add optional card hints/controls for new thresholds | |
| Full user workflow update | Add explicit user migration/onboarding flow | |

**Auto choice:** Code-side only hardening.
**Notes:** Matches phase definition and user instruction: no new user-facing step.

---

## Claude's Discretion

- Threshold key naming, helper naming, and exact safe-range constants.
- Exact placement of fog tunables within existing thresholds config step layout.

## Deferred Ideas

- Per-site terrain-aware fog threshold overrides.
- Potential future change to make fog risk blocking in GO/NO-GO.
