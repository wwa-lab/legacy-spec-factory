# Stage 06: Spec Writing (one capability at a time)

**You are here if:** module analysis is approved (4 views + overview), the
selected `CAP-*` has an approved legacy BRD Package plus an explicit post-BRD
promotion / disposition decision (or an explicit technical-spec-only bypass),
and you want to produce a per-capability `spec.yaml` + `spec.md` that
downstream forward SDLC can consume.

You produce **one spec per `CAP-*`** capability seed listed in
`module-overview.md`. Do not bundle multiple capabilities into one spec.

## Need before starting

- `04_modules/<MODULE-SLUG>/` — overview + all 4 views, all approved
  (prefer module-analyzer v0.2.2 evidence summaries for replay, edge
  resolution, field lineage, routine-local evidence carry-forward,
  persistence purpose, and exception recovery)
- `05_brds/<CAPABILITY-SLUG>/` — approved BRD Package with `brd.md`,
  `brd-review.md`, `validation-scenarios.md`, `traceability.md`, and review /
  approval evidence; bypass allowed only when explicitly recorded as a risk
- Post-BRD promotion / disposition evidence showing this is not No-gap, Gap1,
  follow-new-system, or pending-decision and is ready to move beyond discovery
- A single `CAP-*` from `module-overview.md` to scope this spec
- Linked `BR-*` rules and `evidence_id`s for that capability
- Analyzer evidence consumed where it exists for observed behaviors, outputs,
  data model fields, and exceptions:
  - flow-analyzer v0.2.2 rows (`REPLAY-*`, `LINEAGE-*`, `PERSIST-*`,
    `EXCHAIN-*`, edge Evidence Source / Resolution, Cross-Program Field
    Lineage, Flow Persistence Matrix, and Exception Propagation Chain)
  - program-analyzer v0.2.4 rows (Routine Logic Details, routine-local
    carrier/lineage rows, routine-local exception closure, File I/O Purpose,
    source identifier + business meaning fields, Error Code Inventory, and
    Exception Closure Ledger)
- SME availability for `inferred_business_rule` confirmation and the
  `draft → in_review → approved` transitions

## Run

- **Skill:** `legacy-spec-writer` (Implemented v0.1.6)
- **Manual fallback:** Use `schemas/spec.schema.yaml` and the templates in
  `skills/legacy-spec-writer/references/`

Optional companions:

- `legacy-modernization-decision-writer` — if the spec proposes a large /
  risky `DEC-*` decision, formalize it as a separate decision package
- `legacy-sme-review-facilitator` — to organize the SME review session
  that closes the `in_review → approved` transition
- `legacy-html-exporter` — after `spec.md`, `traceability.md`, or review /
  question-pack Markdown exists and SMEs need a browser-friendly review view.
  Markdown remains canonical; fix Markdown first and regenerate HTML if content
  changes.

## Produce

- **Artifact set per capability:**
  - `spec.yaml`  (machine-readable contract; conforms to `schemas/spec.schema.yaml`)
  - `spec.md`    (human-readable explanation)
  - `traceability.md` (rule → evidence → test mapping)
  - `review-report.md` (optional, from `legacy-spec-reviewer` when available)
- **Save under:** `05_specs/<CAP-ID>/` *(relative to your `project.root`)*
  e.g. `docs/XXX260004-demo/05_specs/CAP-ORDER-PRICING/spec.yaml`
- **Consumed by:** `legacy-brd-to-sdd-handoff`,
  `legacy-golden-master-test-planner`, forward SDLC
  (`wwa-lab/build-agent-skill`)

## Gate before advancing

- **Name:** Evidence Approval Gate (during writing) → SME approval
  (transition to `approved`)
- **Check:**
  - Approved BRD Package exists for the selected `CAP-*`, or an explicit
    technical-spec-only bypass is recorded
  - A named stakeholder post-BRD promotion / disposition decision exists for
    the capability
  - No-gap, Gap1, follow-new-system, and pending-decision outcomes are not
    being promoted into requirements
  - Every rule has at least one linked `evidence_id`
  - Observed behaviors, data fields, outputs, and exceptions preserve
    available module / flow / program evidence, including routine-local
    carrier/lineage and exception closure where it explains calculations,
    handoffs, skipped work, rollback, persistence, or visible error outcomes
  - No rule with `knowledge_type: inferred_business_rule` has
    `review_status: needs_sme_review`
  - Every approved rule has `acceptance_criteria`
  - `spec.yaml.status: approved` AND no blocking `TBD-*` remain
- **Blocks if:** any of the above fail. The orchestrator must refuse to
  hand off to the Forward Handoff Gate until all are satisfied.
- **HTML export note:** HTML companions never satisfy this gate. They only make
  stable Markdown easier to review.

## SME action

- **Required:** yes — at two points:
  1. Per-rule confirmation for every `inferred_business_rule`
  2. Sign-off for `spec.yaml.status: in_review → approved`
- **Ask:** "Confirm each inferred rule (correct / wrong / needs change).
  Are the acceptance criteria sufficient? Approve the spec?"
- **Recorded in:** `spec.yaml.rules[].review_status` +
  `spec.yaml.status` + `spec.yaml.sme_review`

## Next card

[`07-forward-handoff.md`](07-forward-handoff.md) — once `spec.yaml.status:
approved` for every capability planned in this delivery, **and** the
equivalence test pack is ready.
