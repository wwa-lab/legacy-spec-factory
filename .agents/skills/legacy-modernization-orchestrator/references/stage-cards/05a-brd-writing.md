# Stage 05a: BRD Discovery Writing And Review

**You are here if:** module analysis is approved for a selected `CAP-*`, and
you need the legacy-system BRD Package for SME / stakeholder migration
discovery review.

This is the standard discovery gate after module synthesis. The BRD answers
"what does the old system do, what evidence supports it, and what remains
unclear?" in SME-readable language.

## Need before starting

- `04_modules/<MODULE-SLUG>/` — overview + all 4 views, all approved
- For standard code-backed BRDs: `01_inventory/object-map.md`, all in-scope
  `02_programs/<MODULE>/<OBJ>/program-analysis.md`, and all in-scope
  `03_flows/<MODULE>/flow-<FLOW-SLUG>.md`, approved or
  `approved_with_non_blocking_tbd`
- A single `CAP-*` from `module-overview.md` to scope this BRD
- Linked `BR-*`, `BEH-*`, `EV-*`, and `TBD-*` seeds for that capability
- Capability owner SME / BA availability for BRD review

If these code-backed artifacts are missing, route back to the earliest missing
stage first. A context-only BRD draft is allowed only with named owner risk
acceptance and cannot be approved.

## Run

- **Skill:** `legacy-brd-writer` (Implemented v0.1.7)
- **Manual fallback:** Use the templates in
  `skills/legacy-brd-writer/templates/` and keep sections 1-9 populated with
  evidence-backed content or named `TBD-*` gaps.

## Produce

- **Artifact set per capability:**
  - `brd.md` — business-facing BRD; sections 1-9 required, 10-12 optional
  - `brd-review.md` — SME review checklist and sign-off page
  - `validation-scenarios.md` — BRD-stage `VAL-*` scenario seeds
  - `traceability.md` — BRD requirement / behavior / evidence / TBD mapping
- **Save under:** `05_brds/<CAPABILITY-SLUG>/` *(relative to your
  `project.root`)*
- **Consumed by:** `legacy-sme-review-facilitator`, then `legacy-spec-writer`
  only for explicitly promoted items

## Gate before advancing

- **Name:** BRD Discovery Gate
- **Check:**
  - BRD sections 1-9 are present and SME-reviewable
  - Missing details are explicit `TBD-*`, not silent blanks
  - Observed behavior, inferred rules, SME decisions, assumptions, and TBDs are
    separated
  - BRD Package contains no old-vs-new comparison, No-gap / Gap1 / Gap2
    classification, target-system disposition, or handoff content
  - `brd-review.md` or `review-decision.yaml` records SME / business approval
- **Blocks if:** BRD is missing, draft without review, blocked by SME, or any
  required section 1-9 is absent without a named `TBD-*`. It also blocks if a
  standard BRD lacks object-map, program-analysis, or flow-analysis support.
  Spec-writing also blocks until a separate post-BRD comparison / promotion
  decision exists.

## SME action

- **Required:** yes — this is the main business review point.
- **Ask:** "Do sections 1-9 correctly describe the old-system function purpose,
  use cases, channels, user touchpoints, interfaces, process, validation, error
  handling, and dependencies?"
- **Recorded in:** `brd-review.md` and, when used,
  `review-decision.yaml`.

## Next card

[`06-spec-writing.md`](06-spec-writing.md) — only after the BRD Package is
approved and a separate post-BRD comparison / promotion decision exists, or
after an explicit technical-spec-only bypass has been recorded.
