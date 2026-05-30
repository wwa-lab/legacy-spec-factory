---
name: legacy-brd-writer
description: Use when migration discovery needs an evidence-backed legacy-system BRD for one capability, with SME-reviewable observed behaviors, inferred rule seeds, open gaps, traceability, and BRD-stage validation scenario seeds. This is the primary near-term old-system discovery artifact; it does not compare against the new system, create an SDD handoff, or mandate target-system changes.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy BRD Writer

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Turns legacy analysis evidence into a stakeholder-readable old-system BRD for migration discovery and SME review. |
| Input | Module analysis, flow/program evidence, observed behaviors, inferred rule seeds, gaps, and traceability references. |
| Output | Legacy BRD Package with behaviors, open questions, validation scenario seeds, and review status. |
| Core prompt strategy | Separate observed behavior from inferred rules, keep target-system comparison out, and write reviewable business language with evidence tags. |
| Upstream skill | `legacy-ibmi-module-analyzer` or an accepted module-first context package. |
| Downstream consumer | SMEs, gap-analysis / old-vs-new reviewers, `legacy-spec-writer`, and decision writers. |
| Validation standard | BRD sections complete, evidence strength declared, unresolved gaps visible, and BRD review gate not bypassed. |
| Known risk | Mistaking old-system description for a mandate to preserve every behavior in the target system. |
| Practical example | Given a four-view order-entry module analysis, produce a BRD package that lists observed hold-release behavior and questions for SME confirmation. |

## Purpose

Synthesize one **legacy-system Business Requirements Document (BRD) Package**
from an approved module analysis, making the distinction between observed
behaviors, inferred rules, SME decisions, open gaps, BRD-stage validation
scenarios, and traceability **visible and reviewable** by non-technical
stakeholders.

In the current migration-discovery operating model, the BRD is the primary
near-term output. Its job is to prepare the old system's business
understanding, not to compare old and new systems or force a handoff to
delivery. Old-vs-new comparison, No-gap / Gap1 / Gap2 disposition,
spec-writing, and SDD handoff are downstream activities that happen after the
legacy BRD is approved and after new-system context is available.

The BRD is a **business synthesis layer**, not a technical specification or
handoff package. It shows:

- The **business process story** in SME language: triggering event, actors,
  customer/account impact, business state changes, normal path, exception paths,
  controls, and unresolved policy questions
- What the legacy system **demonstrably does** (`BEH-*`)
- What business rules we **infer from evidence** (`BR-*` seeds from module, status
  `needs_sme_review` or `draft`)
- What questions remain **unresolved** (`TBD-*`)
- **How confident** each claim is, derived from linked evidence records
- Which **business validation scenarios** (`VAL-*`) SMEs and downstream teams
  should use to review the BRD scope

The BRD consumes module analysis, flow analyses, program analyses, and SME /
BA legacy context. It does **not** produce formal acceptance criteria, formal
`TC-*` test cases, modernization decisions, target-platform choices,
old-vs-new comparison, target-system requirements, or SDD handoff files.
`VAL-*` entries are scenario seeds only; `AC-*` belongs to
`legacy-spec-writer`, and formal `TC-*` belongs to
`legacy-golden-master-test-planner`.

For the standard migration-discovery path, the BRD is **code-backed**. A
module-first context package or document-normalized four-view draft can inform
the BRD, but it does not replace `01_inventory/object-map.md`, per-program
analysis, or flow analysis. A context-only BRD is allowed only as a
non-approved draft with named owner risk acceptance and visible TBD blockers.

The BRD body follows the SME-required functional analysis shape. Sections 1-9
are mandatory in `brd.md`: Function Purpose, Business Scenarios / Use Cases,
Channels, User Interface / User Touchpoints, System Interfaces, Process Flow,
Validation Rules, Error Handling, and Dependencies. Sections 10-12 are optional
and evidence-backed only: Security / Authentication Requirements, Supporting
Workflow or Design Notes, and Source Document Mapping.

Document-quality or readiness criteria do **not** belong in `brd.md`. Checks
such as "the BRD clearly explains the business boundary" evaluate the artifact,
not the business capability; keep them in `brd-review.md` or traceability
validation instead of adding a generic `Success Criteria` section to the BRD.

## When to Use

Trigger on any of these signals:

- Module analysis is **approved** or **approved_with_non_blocking_tbd** and
  stakeholders need a **business-readable artifact** for scope review
- SME owner wants to **validate business scope and rules** before forwarding to
  `legacy-spec-writer`
- SME / BA / vendor stakeholders need **test-aware scenario seeds** to discuss
  coverage, SOW scope, and missing runtime evidence without creating formal
  test cases yet
- You are **orchestrating a discovery phase** and need a non-technical bridge
  artifact that explains the old system before any gap-analysis or forward-SDLC
  decision
- Migration stakeholders need an **as-is legacy BRD** that can later be compared
  against a new-system BRD or product design in a separate comparison /
  gap-analysis process
- Legal, compliance, or product stakeholders need **clear visibility** into what
  rules are observed vs. inferred vs. uncertain

## When NOT to Use

Do not trigger when:

- The output is **code** or **target-platform implementation** (use
  `legacy-spec-writer` then `build-agent-skill`)
- The requester wants an **SDD handoff package** or Atlas-ready delivery bundle
  (use `legacy-brd-to-sdd-handoff` only after approved BRD + approved spec)
- The requester wants old-vs-new **No-gap / Gap1 / Gap2 classification** or
  target-system scope decisions in the BRD itself. Finish the legacy BRD first,
  then route comparison to the post-BRD migration disposition process.
- The requester has an explicitly approved **technical-spec-only bypass** and
  accepts the missing BRD review as a documented risk (route to
  `legacy-spec-writer` with that bypass recorded)
- No **SME is available** to review and approve the BRD
- The module analysis is **below `approved_with_non_blocking_tbd`** status (route
  back to `legacy-ibmi-module-analyzer`)
- The selected module / capability is context-only and lacks
  `01_inventory/object-map.md`, required program analyses, or required flow
  analyses, unless the requester explicitly asks for a context-only draft and a
  named owner accepts that it cannot be approved as code-backed

This skill is a **migration discovery and business synthesis layer**. If you
find yourself writing formal acceptance criteria, minting formal `TC-*` test
cases, minting `DEC-*` ids, specifying target architecture, or producing an
Atlas/SDD package, you are in the wrong skill. Route to
`legacy-spec-writer`, `legacy-golden-master-test-planner`, or
`legacy-brd-to-sdd-handoff` as appropriate.

It is also the wrong output shape if the BRD reads like a program walkthrough.
Runtime chains, object lists, file-copy details, and call-sequence summaries are
evidence, not the main BRD narrative. Keep program names in evidence references,
traceability, or a short appendix when needed; do not make them the reader's
primary path through the business requirement.

## Role

You are the **business requirements synthesizer** for one capability.

You must:

- translate module / flow / program evidence into business-process language
  before drafting the BRD body
- write an as-is business narrative that a SME, BA, operations owner, product
  owner, or compliance reviewer can discuss without knowing IBM i object names
- extract observed behaviors (`BEH-*`) from flow and program analyses without
  invention or inference
- aggregate inferred rules (`BR-*` seeds) from the module analysis; keep their
  status as `needs_sme_review` (do not promote to `approved`)
- fill all SME-required BRD sections 1-9, using `TBD-*` where required evidence
  or SME confirmation is missing
- include optional sections 10-12 only when security/auth details, workflow or
  design notes, or source document mappings are available from evidence or SME
  input
- distinguish **knowledge type** (observed_behavior / inferred_business_rule)
  on every claim, and link each claim to evidence records whose strength is
  recorded in the evidence index per
  `docs/evidence-and-knowledge-taxonomy.md`
- surface unresolved items (`TBD-*`) with category and resolver
- draft BRD-stage validation scenario seeds (`VAL-*`) that map to existing
  `BEH-*`, `BR-*`, and `EV-*` references
- frame unclear scope as SME-answerable boundary questions, not as a generic
  problem statement about document fragmentation or analysis-process risk
- keep artifact-readiness checks in `brd-review.md`; do not put generic
  document-quality criteria in the BRD body
- refuse to produce formal acceptance criteria, modernization decisions, or
  platform choices — those belong in `legacy-spec-writer`
- refuse to classify legacy behavior as No-gap / Gap1 / Gap2 inside the BRD;
  that classification belongs after BRD approval when new-system context is
  available
- refuse to produce formal `TC-*` test cases or invented exact expected outputs
  — those belong in `legacy-golden-master-test-planner` after spec approval
- require SME sign-off before the BRD leaves `in_review` status

You must not:

- present the BRD as a direct runtime chain, call graph, program inventory, file
  movement list, or object-by-object analysis
- create a standalone `Problem Statement` section that mixes business scope,
  evidence gaps, technical coupling, and downstream rework risk
- create a generic `Success Criteria`, `Success Criiteria`, `Document Success
  Criteria`, or similar section in `brd.md`; those checks belong in
  `brd-review.md`, not the BRD body
- invent channels, user interfaces, system interfaces, security requirements,
  diagrams, source documents, or dependencies just to satisfy the BRD shape
- invent business rules beyond what the module analysis suggests + SME
  confirmation
- invent a new-system comparison, gap classification, risk assessment, or
  gap-analysis disposition
- promote a `BR-*` seed to `approved` status in the BRD; SME confirmation is
  recorded as review input, and `legacy-spec-writer` performs the final rule
  promotion in `spec.yaml`
- generate formal acceptance criteria (spec-writer's job)
- generate formal `TC-*` test cases or exact expected outputs
- include target platform or modernization decisions
- include SDD handoff package content
- mark No-gap, Gap1, or Gap2 status inside the BRD
- collapse observed behavior into inferred rules without marking the
  distinction
- treat high-confidence inferences as facts without SME validation

## Inputs

Accept:

- **Approved module analysis** (`04_modules/<MODULE-SLUG>/` with all four views
  at `approved` or `approved_with_non_blocking_tbd`)
  - Prefer module analyses whose `module-overview.md` includes the BRD
    Functional Analysis Input Crosswalk. Use that crosswalk to populate SME
    required sections 1-9 and to carry missing / partial areas as `TBD-*`
    instead of rediscovering them from program or flow details.
- **Approved code evidence backbone** for standard BRDs:
  `01_inventory/inventory.yaml`, `01_inventory/object-map.md`, in-scope
  `02_programs/<MODULE>/<OBJ>/program-analysis.md`, and in-scope
  `03_flows/<MODULE>/flow-<FLOW-SLUG>.md`
- **One or more capability seeds** — selected from the module overview's
  Capability Seeds; the SME has confirmed each is a distinct, in-scope business
  capability
- **Capability-owner SME** (required for sign-off)
- **Optional:** BAU notes or additional context from the SME

Stop and require clarification if:

- Module status is below `approved_with_non_blocking_tbd` → route back to
  `legacy-ibmi-module-analyzer`
- Standard BRD requested but the code evidence backbone is missing
  `object-map.md`, required program analyses, or required flow analyses → route
  to the earliest missing code-backed skill before drafting or approving the
  BRD
- Context-only draft requested without named owner risk acceptance → stop and
  request risk acceptance or route back to source/object evidence collection
- The selected capability seed has **blocking TBDs** in the module analysis →
  escalate to SME for resolution before proceeding
- No **SME owner is assigned** → stop; cannot proceed to review without SME
- The capability **boundary is ambiguous** (does flow X belong here or to another
  capability?) → SME must decide
- The user asks the BRD writer to classify old-vs-new No-gap / Gap1 / Gap2 or
  decide target-system scope → explain that the BRD must first capture the
  legacy baseline; comparison/disposition is a post-BRD process

## Output Contract

Produce a directory `05_brds/<CAPABILITY-SLUG>/`:

```
05_brds/<CAPABILITY-SLUG>/
├── brd.md                    ← canonical business requirements document
├── brd-review.md            ← SME review checklist and sign-off page
├── validation-scenarios.md  ← SME-reviewable VAL-* scenario seeds
└── traceability.md          ← cross-reference report (BRD req → EV/BEH/VAL/TBD)
```

Use:

- `templates/brd.md`, `templates/brd-review.md`,
  `templates/validation-scenarios.md`, `templates/traceability.md` as starting
  structure
- `references/synthesis-rules.md` for how to extract behaviors and aggregate
  rules
- `references/anti-hallucination.md` for what the BRD must refuse to invent

Follow:

- `../../docs/id-conventions.md` for stable IDs (`CAP-*`, `BEH-*`, `BR-*`,
  `TBD-*`, `VAL-*`, etc.)
- `../../docs/evidence-and-knowledge-taxonomy.md` for knowledge-type /
  evidence-strength distinction
  - Use only these evidence strength values in evidence records:
    `confirmed_from_code`, `observed_in_runtime`, `confirmed_by_sme`,
    `strongly_inferred`, `weakly_inferred`, `needs_sme_review`,
    `contradictory`, `missing`
- `../../docs/data-collection-and-redaction.md` for evidence sensitivity
  checks
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Post-BRD comparison note:

- The legacy BRD is the baseline input for later old-vs-new comparison.
- No-gap / Gap1 / Gap2 classification, risk assessment, and formal gap analysis
  are outside this skill and must not be written into `brd.md`,
  `brd-review.md`, `validation-scenarios.md`, or `traceability.md`.

Examples:

- `examples/brd-positive/` — one approved BRD (Credit Limit Enforcement from
  CARD-AUTH module)
- `examples/incomplete-input-negative/` — BRD with non-blocking TBDs (awaiting
  SME decision on open questions)

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms to
the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for full field-level rules.
The summary below is normative for this skill.

### Input

- **Required for standard code-backed BRDs**: approved
  `04_modules/<MODULE-SLUG>/` (all four views at `approved` or
  `approved_with_non_blocking_tbd`, `evidence_mode: code_backed`); one or more
  `CAP-*` capability seeds from the module overview, validated by SME; named
  capability-owner SME; all referenced `flow-<FLOW-SLUG>.md` and
  `program-analysis-<OBJ-ID>.md` at `approved` or
  `approved_with_non_blocking_tbd`; approved `01_inventory/inventory.yaml`;
  `01_inventory/object-map.md`.
- **Required for context-only BRD drafts**: module overview or context package
  marked `evidence_mode: context_only`; named owner risk acceptance; missing
  inventory, object-map, program-analysis, and flow-analysis artifacts carried
  as `TBD-*`; BRD status limited to `draft` or `in_review`.
- **Optional**: BAU notes, supplemental legacy-system context, source document
  pointers, runtime observations, and policy notes from SMEs.
- **Input readiness scoring**:
  - `0-5 blocked`: approved module missing, selected `CAP-*` unresolved,
    blocking TBDs remain, capability boundary ambiguous, no SME owner, or
    evidence authorization unresolved.
  - `6 minimum_pass`: approved code-backed module, selected SME-confirmed
    capability seed, named capability-owner SME, approved upstream analyses,
    and approved object map are present. Context-only drafts can reach
    `minimum_pass` only for draft review, not BRD approval.
  - `7-8 usable`: BAU notes, supplemental SME context, and related open-TBD
    history are supplied.
  - `9-10 strong`: examples of real scenarios, exception cases, runtime
    observations, policy notes, and downstream reader context are also supplied.
  - Missing supplemental context does not block BRD drafting; it should produce
    clearer SME questions instead of invented rules.
- **Readiness checks**: module and all upstream analyses at required status;
  object map exists for standard BRDs; no `sensitivity: unknown` evidence in
  scope; SME owner available to approve BRD.
- **Stop conditions**: module below `approved_with_non_blocking_tbd` (route back
  to `legacy-ibmi-module-analyzer`); standard BRD requested without object map,
  program analyses, or flow analyses; context-only draft requested without
  named risk acceptance; capability seed has blocking TBDs (escalate to SME);
  no SME owner assigned; capability boundary ambiguous; request asks BRD writer
  to classify No-gap / Gap1 / Gap2 or decide target-system scope.

### Execution

- **Procedure**: see the Workflow section below (9 ordered steps).
- **Allowed inference**: lifting `BEH-*` from flow control flow, program branch
  points, and error handling (factual statements about what the legacy system
  does); aggregating `BR-*` seeds from module overview and cross-checking
  against program/flow context; computing confidence levels based on evidence
  strength; surfacing contradictions as TBDs.
- **Forbidden assumptions**: inventing business rules beyond module BR-* seeds +
  SME confirmation; promoting a BR-* seed to `approved` status (only
  `legacy-spec-writer` may do that); generating formal acceptance criteria;
  generating formal `TC-*` test cases or invented exact expected outputs;
  specifying target platform or modernization decisions; adding old-vs-new
  comparison or target-system disposition; reading raw IBM i source code
  (consume upstream analyses only); treating weak inferences as facts.
  Do not label a context-only document or RAG claim as `confirmed_from_code`.
- **TBD handling**: unconfirmed rule → `BR-*` seed with `status: needs_sme_review`
  (marked in BRD); contradictory evidence → `TBD-*` with `category:
  contradictory_evidence` and resolver; missing context → `TBD-*` with
  `category: sme_questions` or `category: evidence_gaps`; legacy behavior that
  needs later comparison or promotion review may be referenced by a `TBD-*`
  with `category: downstream_handoff_blockers` and `blocking: no` for BRD
  approval unless the SME marks it business-critical.

### Output

- **Canonical directory**: `05_brds/<CAPABILITY-SLUG>/` containing `brd.md`,
  `brd-review.md`, `validation-scenarios.md`, `traceability.md`.
- **Required sections/fields** (see `templates/brd.md`): sections 1-9 in the
  SME functional-analysis shape: Function Purpose, Business Scenarios / Use
  Cases, Channels, User Interface / User Touchpoints, System Interfaces,
  Process Flow, Validation Rules, Error Handling, and Dependencies. Sections
  10-12 (Security / Authentication Requirements, Supporting Workflow or Design
  Notes, Source Document Mapping) are optional and evidence-backed only.
- **Required IDs**: mints `BRD-*` for the document, `VAL-*` for BRD-stage
  validation scenario seeds, and `TBD-*` for open
  questions. Reuses `CAP-*`, `OBJ-*`, `EV-*`, `BEH-*`, `BR-*` seeds,
  `MODULE-*`, `FLOW-*` from upstream. If a new candidate rule appears during
  BRD review and has no upstream `BR-*`, record it as a `TBD-*` requiring
  module/spec review instead of minting a new `BR-*` here. Does NOT mint
  `DEC-*`, `AC-*`, `IN-*`, `OUT-*`, `STEP-*`, `TC-*`, or new `BR-*`.
- **Review status**: `status: draft` → `in_review` → `approved` (SME sign-off).
  The approved BRD is ready as the legacy-system discovery baseline.
  `legacy-spec-writer` consumes it only after a separate post-BRD comparison /
  promotion decision says the capability or selected legacy behavior should
  move beyond discovery. Direct module-to-spec generation is an exception that
  requires an explicit technical-spec-only bypass with approver and risk
  acceptance.
  A context-only BRD draft cannot become `approved` until the Code-Backed
  Analysis Gate passes; keep missing object map, program analysis, and flow
  analysis as blocking `TBD-*` items in `brd-review.md` and `traceability.md`.

### Validation

Validation has three distinct layers, in order. None substitutes for another.

#### 4a. Mechanical Validation

What can be checked by a script, schema, or deterministic linter:

- required files exist at expected paths
- all referenced IDs resolve (no dangling `EV-*`, `BEH-*`, `BR-*`, `CAP-*`,
  `VAL-*`, `TBD-*`)
- ID prefixes match `docs/id-conventions.md`
- every claim has at least one linked evidence item (`EV-*` or `BEH-*`)
- no `sensitivity: unknown` in evidence references
- traceability table is complete and consistent (all claims appear in
  `traceability.md`)
- standard BRDs cite `01_inventory/object-map.md`, in-scope program analyses,
  and in-scope flow analyses; context-only drafts visibly block approval
- BRD does not include acceptance criteria, modernization decisions, or target
  platform details
- `validation-scenarios.md` does not mint `AC-*` or `TC-*`

Mechanical validation **must** be reproducible. If it depends on judgment, move
it to AI semantic review.

#### 4b. AI Semantic Review

What an LLM (or careful reviewer) can check by reading the artifact against
upstream evidence:

- observed behaviors (`BEH-*`) are factual statements about what the code / data /
  logs show, not inferences
- the section 6 process flow is a business process narrative, not a program
  call chain; program and file names appear only when they are essential
  identifiers or evidence references
- inferred business rules (`BR-*` seeds) are supported by `BEH-*` and linked
  `EV-*` content (not just ID reference)
- knowledge type (observed_behavior / inferred_business_rule) is correctly
  marked for every claim
- evidence support is not overstated (no weak evidence record used as if it
  were direct code/runtime/SME confirmation)
- context-only module or document evidence is not presented as code-confirmed
  behavior
- no invented IBM i facts (object names, fields, programs, jobs)
- no scope creep into other capabilities
- no acceptance criteria or platform decisions hidden in prose
- validation scenarios map to existing `BEH-*`, `BR-*`, and `EV-*` references
  without introducing new rules
- TBDs are explicit, not hidden inside prose

AI semantic review **must** call out uncertainty rather than smooth it over.

#### 4c. SME / Human Approval

What only a domain expert can decide:

- are the observed behaviors accurate to legacy system reality?
- are the inferred rules actually business rules, or are they implementation
  artifacts?
- is the capability scope and boundary correct?
- are there unspoken business rules the code doesn't show?
- do the `VAL-*` scenario seeds cover the important happy path, exception,
  boundary, and manual review cases for this BRD?
- are TBDs blocking or non-blocking for BRD approval or later comparison,
  gap-analysis, or spec-writing?
- is the BRD safe to promote to `approved` as a migration-discovery artifact?

SME approval is a **control point**, not a rubber stamp. The Step Validation
Report must record the SME's name (or role), the date, and the specific
decision.

## Workflow

1. **Confirm Capability Scope**
   - Take one or more `CAP-*` seeds from the module overview's Capability Seeds
   - Validate with SME: is each a distinct capability worth its own BRD?
   - Assign `brd_id` and confirm `capability.{id, name, slug, owner}`
   - Define `scope.in_scope` and `scope.out_of_scope` from SME
   - Record `evidence_mode`: `code_backed` for standard BRDs, or
     `context_only` only when named risk acceptance exists and the BRD will
     remain non-approved

2. **Collect Evidence Bundle**
   - Gather every `EV-*` referenced by flows / programs / module that touch this
     capability
   - Confirm the code-backed evidence backbone exists for standard BRDs:
     `01_inventory/object-map.md`, in-scope program analyses, and in-scope
     flow analyses
   - Populate evidence index with source, type, sensitivity, and confidence
   - Confirm `sensitive` flag is set on all evidence; if any `sensitive:
     unknown`, stop and request redaction review
   - If context-only, create `TBD-*` blockers for each missing code-backed
     artifact and prevent approval in `brd-review.md`

3. **Translate Technical Evidence into Business Process Language**
   - Create a short business-first process flow before writing `BEH-*`
   - Describe the triggering business event, primary actor or system party,
     business object/state affected, normal outcome, exception outcomes,
     operational controls, and handoffs
   - Use domain nouns (`cardholder`, `replacement request`, `address
     verification response`, `exception queue`) before implementation nouns
     (`program`, `file`, `library`, `commit`, `copy`)
   - If source materials are scattered or the capability boundary is unclear,
     do not write a standalone `Problem Statement`. Capture the SME decision
     needed under `Scope Clarification Need` and create explicit `TBD-*` items
     for actors, triggers, state transitions, handoffs, or in/out-of-scope
     boundaries.
   - Do not add `Success Criteria` or document-readiness bullets to `brd.md`.
     If those checks are useful, place them in the author/synthesizer preflight
     section of `brd-review.md`.
   - Populate the SME-required sections explicitly:
     Function Purpose, Business Scenarios / Use Cases, Channels, User
     Interface / User Touchpoints, System Interfaces, Process Flow, Validation
     Rules, Error Handling, and Dependencies.
   - Include Security / Authentication Requirements, Supporting Workflow or
     Design Notes, and Source Document Mapping only when evidence or SME input
     supports them; otherwise omit the optional section or create a `TBD-*` if
     confirmation is required.
   - If the only available description is a runtime chain, convert it into 3-6
     business phases and create `TBD-*` questions for any phase whose business
     purpose is unclear
   - Keep program names, file names, and object IDs in evidence references,
     traceability, or appendix notes unless a SME must recognize the object to
     confirm scope

4. **Lift Observed Behaviors (BEH-*)**
   - From flow analyses' control flow points, branch conditions, error handlers
     (factual statements about legacy system behavior)
   - Each BEH must trace to ≥1 `EV-*`
   - These are *factual* — what the system does, not why or whether it's correct
   - Phrase each BEH as business-visible behavior first; implementation details
     may appear after the business behavior only as supporting context

5. **Aggregate Business Rules (BR-*)**
   - From module analysis's `BR-*` seeds (View 1 / Capability Seeds)
   - Cross-check against flow / program analyses
   - Keep each BR-* at status `needs_sme_review` (do NOT promote to `approved`);
     that is spec-writer's job
   - Reuse upstream `BR-*` seeds only. If BRD review reveals a candidate rule
     with no upstream `BR-*`, record a `TBD-*` for module/spec review instead
     of minting a new `BR-*`
   - Each BR must:
     - Reference ≥1 `BEH-*` it abstracts
     - Reference ≥1 `EV-*` that supports it
     - Be marked `knowledge_type: inferred_business_rule`

6. **Draft Validation Scenario Seeds (VAL-*)**
   - Convert approved observed behaviors and inferred rule candidates into
     SME-reviewable business validation scenarios
   - Each `VAL-*` must map to at least one existing `BEH-*` or `BR-*` and at
     least one `EV-*`
   - Cover happy path, exception, boundary, and manual-review cases where the
     evidence supports them
   - Mark readiness as `ready_for_spec`, `needs_sme_review`, or
     `needs_runtime_evidence`
   - Do not invent exact expected outputs, formal `AC-*`, formal `TC-*`, target
     system behavior, or new business rules
   - If a useful scenario cannot be drafted safely, put it in Deferred
     Scenarios with the evidence gap and resolver

7. **Surface Open Questions (TBD-*)**
   - Contradictory evidence → `TBD-*` with category `contradictory_evidence`
   - Missing context → `TBD-*` with category `sme_questions`
   - Ambiguous scope → `TBD-*` with category `sme_questions`
   - Legacy behavior that may need later comparison or promotion review →
     `TBD-*` with category `downstream_handoff_blockers` only when the blocker
     is visible from legacy evidence
   - Each TBD must name a resolver and indicate what it blocks: BRD approval,
     later comparison, gap analysis, spec-writing, or SDD handoff

8. **Build Traceability**
   - Generate `traceability.md` cross-reference table
   - Every BEH-* and BR-* must have ≥1 supporting EV-*
   - Every VAL-* must map back to BEH-* or BR-* and supporting EV-*
   - Every TBD must be listed with category and resolver
   - Verify complete coverage (no claim is missing from the table)

9. **Prepare for SME Approval**
   - Mark `status: in_review`
   - Generate `brd-review.md` checklist
   - Generate `validation-scenarios.md` for SME scenario coverage review
   - Capability owner SME approves the BRD; BRD is then `status: approved`
   - Keep `BR-*` review status as `needs_sme_review` in the BRD even when SME
     notes confirm it for later spec promotion
   - If SME finds issues, mark `status: blocked` with specific findings

## Workflow State Write-Back (history-only discovery gate)

This is the standard business-review gate for the migration-discovery phase.
It produces a business-facing legacy BRD after module analysis. It does NOT
advance the numeric `stage_id`; it records BRD review status and blocking
metadata until approval. It does NOT mutate `current_focus`.

After a run, append one `history[]` entry to
`<project-root>/workflow-state.yaml` per
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md):

```yaml
history:
  - at: <ISO 8601>
    skill: legacy-brd-writer
    capability_id: <CAP-* from current_focus>
    stage_after: <UNCHANGED stage_id>
    artifact: <path to brd.md, e.g. 05_brds/<CAPABILITY-SLUG>/brd.md>
    note: "BRD authored for <CAP-*> — status: draft | in_review | approved"
```

Also overwrite `project.last_updated_at` / `project.last_updated_by`.

**Permitted side-effect:** if BRD authoring surfaces inferred business rules or
open gaps not already in
`capabilities[<CAP-*>].blocking.*`, you MAY append them to
`blocking.sme_pending` (rule IDs) or `blocking.tbds`. You MUST NOT change
`stage_id`, `last_artifact`, or `last_skill` — the linear stage owner remains
`legacy-ibmi-module-analyzer` unless a later stakeholder decision routes the
capability to `legacy-spec-writer`.

If `workflow-state.yaml` does not exist, this skill does NOT create it.

## Anti-Hallucination Rules

The BRD is the first **business-facing** artifact. The temptation to "smooth out"
gaps or invent business logic is high. Discipline is essential.

**Observed behavior is ground truth.** A BEH can only be claimed when it is
grounded in:

- **Tier 1** (upstream flow / program analysis) — for what the system does, or
- **Tier 2** (named, date-stamped SME confirmation) — for context the code
  doesn't show (manual procedures, business policy)

**Do NOT:**

- **Invent business rules** beyond what module BR-* seeds suggest + SME
  confirmation
- **Promote a BR-* seed to `approved`** (only `legacy-spec-writer` may do that)
- **Generate formal acceptance criteria** (spec-writer's job)
- **Generate formal `TC-*` test cases or invented expected outputs**
  (golden-master planner's job after spec approval and runtime evidence review)
- **Include target platform or modernization decisions** (spec-writer's job)
- **Add old-vs-new comparison or target disposition to the BRD**. No-gap,
  Gap1, Gap2, risk assessment, and formal gap analysis belong after BRD
  approval when new-system context is available.
- **Add generic BRD success criteria to `brd.md`**; artifact-readiness checks
  belong in `brd-review.md`, not in the business requirements document
- **Invent optional functional-analysis details** such as channels, UI screens,
  security rules, diagrams, or source documents when they are not evidenced
- **Claim behavior from field names or comments alone** (factual evidence
  required)
- **Pretend ambiguity is resolved** by picking one interpretation when SME
  hasn't confirmed → mark as TBD instead
- **Include any fact** that doesn't trace to an `EV-*` in the evidence index

**Instead:**

- If a BR seed is plausible but SME hasn't confirmed → keep it at
  `needs_sme_review`, do not hide uncertainty
- If evidence is contradictory → create a `TBD-*`, mark the category, and name
  a resolver
- If a field's meaning is unclear → create a `TBD-*` on semantics; do not guess
- If scope is contested → create a `TBD-*` on boundary; let SME decide
- If a test-like scenario needs runtime data or expected output evidence →
  create a `VAL-*` with `readiness: needs_runtime_evidence` or defer it; do not
  invent the expected result
- If later comparison is needed → finish the legacy BRD first, then route the
  approved BRD into the separate comparison / gap-analysis process

## Quality Checklist

Before marking the BRD `approved`, confirm:

- [ ] All four files exist at correct paths (`brd.md`, `brd-review.md`,
      `validation-scenarios.md`, `traceability.md`)
- [ ] Every claim in `brd.md` appears in `traceability.md`
- [ ] Section 6 Process Flow is business-readable and does not read as a direct
      runtime chain, object inventory, or call graph
- [ ] No standalone `Problem Statement` section mixes business scope,
      evidence gaps, technical coupling, and delivery/rework risk
- [ ] No generic `Success Criteria` or document-quality/readiness section is
      included in `brd.md`
- [ ] Required sections 1-9 are present: Function Purpose, Business Scenarios /
      Use Cases, Channels, User Interface / User Touchpoints, System
      Interfaces, Process Flow, Validation Rules, Error Handling, Dependencies
- [ ] Optional sections 10-12 are included only when evidence-backed or
      explicitly SME-confirmed; missing optional details are omitted or tracked
      as `TBD-*`
- [ ] Every `BEH-*` and `BR-*` links to ≥1 `EV-*`
- [ ] Every `VAL-*` maps to existing `BEH-*` or `BR-*` and ≥1 `EV-*`
- [ ] `validation-scenarios.md` contains no formal `AC-*`, formal `TC-*`,
      target architecture, or invented exact expected output
- [ ] No No-gap / Gap1 / Gap2 classification, risk assessment, gap-analysis
      disposition, target-system requirement, or SDD handoff content appears in
      the BRD Package
- [ ] No invented IBM i facts; all object names come from upstream artifacts
- [ ] Knowledge type (observed_behavior / inferred_business_rule) is marked for
      every claim
- [ ] `BR-*` seeds carry `status: needs_sme_review` (not promoted to `approved`)
- [ ] No acceptance criteria, modernization decisions, or platform details in
      BRD
- [ ] All `TBD-*` items carry a category (missing_inputs, evidence_gaps,
      contradictory_evidence, sme_questions, downstream_handoff_blockers)
- [ ] SME has reviewed and approved the BRD
- [ ] Capability scope and boundaries are validated by SME

## Relationship to Other Skills

- **`legacy-ibmi-module-analyzer`** (upstream): produces module analysis with
  BR-* seeds and capability seeds. BRD consumes this output.
- **`legacy-spec-writer`** (downstream): consumes module analysis plus the
  approved BRD Package only after a separate post-BRD comparison / promotion
  decision says the capability or selected legacy behavior should move beyond
  discovery. The BRD is the business context layer for later rule promotion and
  acceptance criteria; it is not itself a mandate to implement legacy-only
  behavior. Direct module-only spec writing requires an explicit
  technical-spec-only bypass.
- **`legacy-golden-master-test-planner`** (downstream verification): consumes
  approved spec acceptance criteria, runtime evidence, and approved scenario
  context to mint formal `TC-*` golden master cases. BRD `VAL-*` entries are
  planning seeds, not final test cases.
- **`legacy-step-contract`** (parallel): defines the Step Contract shape that
  this skill conforms to.
- **`legacy-modernization-orchestrator`** (meta): routes to BRD-writer as the
  standard legacy-discovery output after module analysis and routes to
  spec-writing only after a separate post-BRD promotion / gap-analysis
  decision.

## Runtime Portability

The canonical skill source lives under:

```
skills/legacy-brd-writer/SKILL.md
skills/legacy-brd-writer/templates/
skills/legacy-brd-writer/references/
skills/legacy-brd-writer/examples/
```

Runtime copies may be synced to:

```
.claude/skills/legacy-brd-writer/
.opencode/skills/legacy-brd-writer/
.agents/skills/legacy-brd-writer/
.codex/skills/legacy-brd-writer/
```

From the repository root, use `scripts/sync-skills.sh` to create or check
runtime copies. Do not edit adapter copies directly.

No runtime-specific assumptions are baked into this canonical source.

## Version History

- v0.1.7 (2026-05-30): Added code-backed BRD gate. Standard BRDs now require
  `object-map.md`, approved program analyses, and approved flow analyses before
  approval; context-only BRDs require named risk acceptance and remain
  non-approved drafts with visible TBD blockers.

- v0.1.6 (2026-05-30): Reframed BRD writer for migration discovery. BRD is now
  the primary near-term old-system artifact and remains legacy-system-only:
  No-gap / Gap1 / Gap2 comparison, risk assessment, formal gap analysis, target
  requirements, and SDD handoff content are explicitly post-BRD concerns.

- v0.1.5 (2026-05-29): Aligned the BRD writer with BRD-first orchestration.
  BRD became the required business review artifact before any later
  spec-writing decision; direct module-to-spec work required an explicit
  technical-spec-only bypass.

- v0.1.4 (2026-05-27): SME functional-analysis alignment
  - Reframed `brd.md` around required SME sections 1-9
  - Made security/auth, workflow/design notes, and source document mapping
    optional evidence-backed sections
  - Kept document-readiness checks in `brd-review.md` instead of BRD body

- v0.1.3 (2026-05-26): Business-readable BRD hardening
  - Added an explicit technical-evidence-to-business-process translation step
  - Required an as-is business process summary before BEH / BR extraction
  - Prohibited direct runtime-chain, program-inventory, and file-movement prose
    as the primary BRD narrative
  - Clarified that program/object details belong in evidence, traceability, or
    appendix context unless essential for SME review

- v0.1.2 (2026-05-21): BRD-stage validation scenario seeds
  - Added `validation-scenarios.md` as a fourth BRD Package artifact
  - Introduced `VAL-*` scenario seeds for SME review, SOW discussion, and
    downstream acceptance/golden-master planning
  - Kept formal `AC-*` ownership with `legacy-spec-writer` and formal `TC-*`
    ownership with `legacy-golden-master-test-planner`

- v0.1.1 (2026-05-16): Runtime smoke test hardening
  - Clarified BRD writer reuses upstream `BR-*` seeds only; new candidate
    rules become `TBD-*` for module/spec review
  - Normalized ambiguous-scope TBDs to `sme_questions`
  - Pinned the allowed evidence-strength enum in the core instructions
  - Passed smoke tests in Codex CLI (gpt-5.4-mini), Claude Code (haiku), and
    OpenCode (minimax-m2.5-free)

- v0.1.0 (2026-05-15): Initial BRD Writer skill
  - 7-step workflow producing brd.md + brd-review.md + traceability.md
  - Strict anti-hallucination at the business rule synthesis step
  - Clear role separation from spec-writer (BRD = business layer, spec =
    technical layer)
  - Optional artifact in the workflow (module → spec is the direct path)
  - Portable across Codex, Claude Code, and OpenCode (awaiting runtime
    smoke-test validation)
