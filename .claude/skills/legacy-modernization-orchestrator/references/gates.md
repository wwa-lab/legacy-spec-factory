# Hard Gates Reference

Six numbered gates plus the Code-Backed Analysis sub-gate protect the reverse
chain. The orchestrator must check the applicable gate before routing across
the corresponding boundary.

## Gate 1 — Evidence Authorization Gate

**Boundary:** raw legacy evidence → any agent skill

**Pass criteria (all required):**

- every evidence item has `sensitivity: public | internal | confidential`
  (never `unknown`)
- every evidence item has an approved analysis path
- each item has either `source_path_verified: true` for internal source review
  or `redaction_required: true` with `redaction_status: approved`
- raw production data is not in committed paths (`evidence/raw/` is in
  `.gitignore`)
- source authorization or redaction notes are recorded without raw sensitive
  values
- `docs/data-collection-and-redaction.md` checklist completed when governed
  redaction is required

**Block actions:**

1. Refuse to route to any Layer 1 skill
2. Send user to `legacy-ibmi-evidence-intake`
3. List which evidence items have `sensitivity: unknown`, missing source-path
   authorization, or incomplete required redaction

## Gate 2 — Inventory Completeness Gate

**Boundary:** `inventory.yaml` → any downstream Layer 1 analyzer or any Layer 2 skill

**Pass criteria (all required):**

- `inventory.yaml.sme_review.decision` is one of `approved` or
  `approved_with_non_blocking_tbd`
- no `coverage_gaps[]` entry has `blocking: yes` unresolved
- every listed object has at least one `evidence_ids[]` or SME confirmation
- no object has `sensitivity: unknown`

**Block actions:**

1. State `decision` value and the count of blocking gaps
2. List the specific blocking gap IDs (`TBD-<SLUG>-<NNN>`)
3. Route to `legacy-ibmi-inventory` to resume, or to SME for waiver

**Waiver path:** an SME may mark a blocking gap non-blocking by adding a
review note and changing `blocking: pending_sme_judgment` → `no`. Record the
SME decision in `sme_review.notes`.

## Gate 2B — Code-Backed Analysis Gate

**Boundary:** module-first / document-first context → approvable module
analysis or standard BRD

**Pass criteria (all required for standard BRD/spec work):**

- `01_inventory/object-map.md` exists and aligns with
  `01_inventory/inventory.yaml`
- every in-scope program has an approved or
  `approved_with_non_blocking_tbd`
  `02_programs/<MODULE>/<OBJ>/program-analysis.md`
  with Call Evidence, Routine Logic Details, routine-local field lineage /
  carrier rows, routine-local exception closure, key file/field logic
  preserving source identifiers plus business meanings, File I/O Purpose,
  field-level mutation, dynamic-call resolution, Error Code Inventory, and
  exception closure coverage, or named `TBD-*` gaps
- every in-scope business transaction has an approved or
  `approved_with_non_blocking_tbd`
  `03_flows/<MODULE>/flow-<FLOW-SLUG>.md`
  with Flow Replay Path, edge Evidence Source / Resolution, Cross-Program Field
  Lineage, Flow Persistence Matrix, and Exception Propagation Chain coverage,
  or named `TBD-*` gaps / waiver
- module View 3 and View 4 claims that cite code use code-derived evidence,
  not only document or RAG context
- module overview summarizes program-chain readiness, persistence / critical
  fields, and exception / recovery coverage for every in-scope flow, or
  carries named `TBD-*` gaps
- any missing source/object evidence is represented by named `TBD-*` blockers

**Context-only exception:** a named accountable owner may explicitly accept a
context-only draft for this cycle when source/object evidence is unavailable.
This exception does not pass the code-backed gate; it only allows draft
review material. The module / BRD must record `evidence_mode: context_only`,
remain non-approved, carry missing object-map / program / flow work as
`TBD-*`, and avoid `confirmed_from_code` evidence strength unless a linked
code-derived artifact exists.

**Block actions:**

1. Route to `legacy-ibmi-inventory` if `object-map.md` is missing or partial.
2. Route to `legacy-ibmi-program-analyzer` for missing in-scope
   `program-analysis-<OBJ-ID>.md` files or older program analyses that lack key
   file/field meaning, Routine Logic Details, routine-local carrier/lineage,
   routine-local exception closure, File I/O Purpose, field mutation,
   dynamic-call resolution, Error Code Inventory, or exception closure coverage.
3. Route to `legacy-ibmi-flow-analyzer` for missing in-scope
   `flow-<FLOW-SLUG>.md` files or older flow analyses that lack replay,
   edge resolution, lineage, persistence, or exception-chain coverage.
4. Refuse BRD approval and spec-writing until the gate passes or a
   context-only draft exception is recorded.

## Gate 3 — BRD Discovery Gate

**Boundary:** approved module analysis → migration-discovery BRD baseline

**Pass criteria (all required unless an explicit technical-spec-only bypass is
recorded):**

- `05_brds/<CAPABILITY-SLUG>/brd.md` exists for the selected `CAP-*`
- BRD sections 1-9 are present and SME-reviewable
- missing section details are explicit named `TBD-*`, not silent blanks
- BRD review evidence records SME / business approval, such as
  `brd-review.md` sign-off or `review-decision.yaml`
- blocked BRD findings are resolved or explicitly accepted as non-blocking

**Block actions:**

1. Route to `legacy-brd-writer` if the BRD Package is missing or incomplete.
2. Route to `legacy-sme-review-facilitator` if BRD content exists but review /
   approval is missing.
3. Refuse standard spec-writing until this gate and the Post-BRD Disposition
   Gate pass, or until the requester records a technical-spec-only bypass with
   approver and risk acceptance.

## Gate 4 — Post-BRD Disposition Gate

**Boundary:** approved BRD Package → `legacy-spec-writer`

**Pass criteria (all required unless an explicit technical-spec-only bypass is
recorded):**

- a named stakeholder decision outside the BRD Package promotes the capability
  beyond legacy discovery
- No-gap, Gap1, and follow-new-system outcomes are explicitly left with the new
  system as source of truth
- risk assessment or gap analysis, when required, has owner approval to proceed
- pending migration decisions are resolved before spec-writing
- no BRD content is being silently converted into old-vs-new comparison,
  `AC-*`, `DEC-*`, or implementation scope

**Block actions:**

1. If No-gap, Gap1, follow-new-system, or pending decision, stop in discovery
   and record the disposition outside the BRD Package.
2. If risk assessment or gap analysis is open, route to the named business /
   risk / gap-analysis owner.
3. Refuse spec-writing and SDD handoff until promotion is explicit.

## Gate 5 — Evidence Approval Gate

**Boundary:** `business-rules.md` (draft) → `legacy-spec-writer`,
or any approval transition on rules / behaviors

**Pass criteria (per claim):**

- `knowledge_type` ≠ `unknown_tbd`
- at least one linked evidence item has `evidence_strength` of:
  - `confirmed_from_code`, or
  - `observed_in_runtime`, or
  - `confirmed_by_sme`, or
  - `strongly_inferred` plus explicit SME approval
- all linked TBDs resolved or marked non-blocking by SME
- `review_status` is `approved`

See repository path `docs/evidence-and-knowledge-taxonomy.md` for the
canonical taxonomy.

**Block actions:**

1. List rule IDs whose status is not `approved`
2. For each, state which approval criterion failed
3. Route to SME review or to additional evidence collection (often
   `legacy-ibmi-runtime-evidence-miner`)

**Exception:** `modernization_decision` claims do not need the same evidence
strength; they need architecture/product approval recorded in
`review_notes`.

## Gate 6 — Forward Handoff Gate

**Boundary:** approved `spec.yaml` → `wwa-lab/build-agent-skill` chain

**Pass criteria (all required):**

- `spec.yaml.status: approved`
- every business-critical rule has `review_status: approved`
- every approved rule has at least one acceptance criterion (`AC-*`)
- every approved rule has at least one linked evidence item
- no `open_questions[].blocking: yes` remains
- data sensitivity reviewed; sample transactions for golden master are
  redacted
- modernization decisions are clearly separated from observed behavior

See repository path `docs/forward-sdlc-contract.md` for the full handoff
contract.

**Block actions:**

1. List the specific gate criteria that failed
2. Route to whichever upstream skill resolves them:
   - missing acceptance criterion → `legacy-spec-writer`
   - failed review → `legacy-spec-reviewer`
   - missing equivalence test for business-critical rule →
     `legacy-equivalence-test-generator`
3. Refuse to provide the handoff manifest until the gate clears

## Gate Interaction Rules

- Gates compound: a downstream gate only matters if all upstream gates have
  already passed.
- The orchestrator may not "skip" a gate even if the user asks. Gate skipping
  is the most common path to a hallucinated spec.
- Every gate failure must produce a specific blocking ID list, not a generic
  "needs work" message.
- A gate that has previously passed must be re-checked when the underlying
  artifact changes (inventory updated -> re-check Gate 2; BRD updated ->
  re-check Gate 3; rule added -> re-check Gate 4).
