---
name: legacy-ibmi-module-analyzer
description: Assemble and validate an IBM i business module from approved flow analyses or a ready module-first context package, producing the evidence-backed module overview plus Program Flow and Data Flow artifacts. Operation Flow and System Flow are no longer default outputs because they require stronger SME or architecture evidence than most code-backed runs provide. Use when multiple flows belong to the same business module, or when `legacy-module-context-intake` has normalized external RAG / human context and you need evidence-bounded module assembly before BRD writing and review. Layer 1.5 (platform-specific) skill. Implements the model defined in `docs/module-analysis-model.md`.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Module Analyzer

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Assembles multiple IBM i flows or module-first context into a focused module coverage map and BRD eligibility crosswalk. |
| Input | Flow analyses, program analyses, data/screen evidence, BAU notes, or an accepted `00_context_packages/<MODULE-SLUG>/` package. |
| Output | `module-overview.md`, Mermaid-backed `03-program-flow.md`, `04-data-flow.md`, and `module-review-checklist.md` with review status and BRD source eligibility. |
| Core prompt strategy | Preserve evidence boundaries across views, use diagrams as traceable summaries only where sourced, and keep uncertain/generated behavior as TBDs. |
| Upstream skill | `legacy-ibmi-flow-analyzer` or `legacy-module-context-intake`. |
| Downstream consumer | `legacy-brd-writer`, `legacy-spec-writer`, SMEs, and module review workflows. |
| Validation standard | Program Flow and Data Flow align without contradictions, all key nodes trace to eligible evidence or TBDs, and module-analysis model rules are followed. |
| Known risk | Producing polished diagrams or BRD crosswalk rows that make unresolved flow gaps look approved. |
| Practical example | Combine order entry, release, and cancellation flows into one focused Order Management module analysis with program and data coverage. |

## Purpose

Assemble multiple flow analyses, BAU (Business As Usual) notes, and SME
context into one **business module** coverage map focused on the two views
that are consistently evidence-backed in code-driven field work: Program Flow
and Data Flow.

This skill is the **last platform-specific layer** before `legacy-brd-writer`
and the BRD Review Gate. It does not re-analyze flows or programs; it
aggregates and validates what flow-analyzer and program-analyzer produced.
Do not concatenate full flow or program Markdown to assemble a module. Use
approved flow rows and compact program artifacts first, then open
human-readable Markdown only for targeted clarification.
For the standard BRD/spec path, those code-backed inputs are required: a
module-first context package can seed the synthesis, but it cannot by itself
make Program Flow, Data Flow, or the downstream BRD `confirmed_from_code`.

This is the only skill that produces the canonical module-analysis artifacts
under `04_modules/<MODULE-SLUG>/`. If upstream `00_context_packages/` files
already contain operation/system/program/data context views, treat them as
evidence/context input only. Do not copy or report upstream context views as
final module-analysis outputs.

`01-operation-flow.md` and `02-system-flow.md` are intentionally not default
outputs. In field testing they often carried weak, over-generalized, or
incorrect business/architecture narratives unless backed by strong SME or
architecture evidence. Preserve such information as SME-confirmed scope,
interface notes, BRD crosswalk rows, or TBDs in `module-overview.md` instead
of generating standalone flow files.

The module overview and evidence views are **not** a BRD fact source by
default. They are a coverage and review surface. Only rows backed by
`confirmed_by_sme`, approved
flow/program/inventory evidence, or other explicitly eligible evidence may be
marked as BRD source material. Context-only, generated-draft, candidate-only,
or source-documented-but-unreviewed rows must become `TBD-*`, SME questions, or
coverage gaps in the BRD handoff.

The canonical model is documented in `../../docs/module-analysis-model.md` —
read that first if you have not already.

## Inputs

Accept:

- **Module definition** — module slug, business name, scope statement,
  the list of flows that belong to this module
- **Ready module context package** from `legacy-module-context-intake`
  (`00_context_packages/<MODULE-SLUG>/context-index.yaml`) when this is a
  module-first RAG / human-context run. Treat it as context and evidence map,
  not as approved module analysis, object inventory, program analysis, or flow
  analysis. Preserve its source eligibility labels.
- **Approved flow analyses** for every flow in scope
  (`flow-<FLOW-SLUG>.md`)
  - For code-backed runs, each approved flow should be
    `legacy-ibmi-flow-analyzer` v0.2.3 or later, or otherwise expose the
    equivalent `Flow Replay Path`, `Cross-Program Field Lineage`,
    `Flow Persistence Matrix`, node artifact availability for compact
    program sidecars, edge Evidence Source / Resolution, and `Exception
    Propagation Chain` with Validation Logic / routine-local exception closure
    carry-forward sections.
    Older flow artifacts require refresh or a named SME waiver before they
    can support module-level replay, lineage, persistence, or exception
    claims.
- **Approved program analyses** for every program referenced by those flows
  - For code-backed runs, prefer program-analyzer v0.2.8 or later compact
    artifacts: `program-analysis-summary.yaml`, `source-index.yaml`,
    `routine-logic-details.yaml`, `message-inventory.yaml`,
    `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
    `sql-inventory.yaml`. Use these sidecars to preserve field calculations,
    handoffs, skipped work, rollback, message meanings, SQLRPGLE evidence, and
    visible error outcomes when flow evidence references the underlying
    program-level detail.
- **Approved inventory** with module scope confirmed
- **BAU notes from SME** — operational rhythm, manual processes,
  exception handling, business context not in code
- **Optional:** architecture diagrams (for overview interface notes), data lineage
  documents, regulatory references
- **Conditionally required from triggers:**
  - When `inventory.yaml.sme_review.downstream_required.screen_report_analyzer.required: true`
    → approved `screen-report-analysis.md` for every triggered DSPF /
    PRTF / menu. The overview and BRD crosswalk consume these as primary
    sources for screen-driven rules; absence means missing 40% of user-facing
    decisions.
  - When `inventory.yaml.sme_review.downstream_required.data_model_analyzer.required: true`
    → approved `04_modules/<MODULE-SLUG>/data-model/dictionary.md`. View
    4 (Data Flow) populates from this dictionary verbatim instead of
    re-deriving entities from per-program File I/O tables.

Trigger rules and override protocol live in
[`skills/legacy-ibmi-inventory/references/downstream-triggers.md`](../legacy-ibmi-inventory/references/downstream-triggers.md).

Stop and require clarification if:

- Any in-scope flow lacks an approved `flow-<FLOW-SLUG>.md` → route to
  `legacy-ibmi-flow-analyzer`, unless a ready
  `00_context_packages/<MODULE-SLUG>/` package is explicitly being used for a
  context-only draft; in that case, carry missing flow-analysis coverage as
  `TBD-*`, set `evidence_mode: context_only`, and keep affected claims at
  `needs_sme_review`
- The requested output is a standard code-backed BRD/spec input but
  `01_inventory/object-map.md`, in-scope program analyses, or in-scope flow
  analyses are missing → route to the earliest missing code-backed skill
  (`legacy-ibmi-inventory`, `legacy-ibmi-program-analyzer`, or
  `legacy-ibmi-flow-analyzer`) instead of approving module synthesis
- The requested output is a standard code-backed BRD/spec input but in-scope
  flow analyses do not expose replay, field-lineage, persistence, edge
  Evidence Source / Resolution, and exception-chain coverage, and no named
  SME waiver exists → route back to `legacy-ibmi-flow-analyzer` for v0.2.3
  refresh
- A trigger is `required: true` but the corresponding artifact is missing
  → route to the triggered skill (`legacy-ibmi-screen-report-analyzer`
  or `legacy-ibmi-data-model-analyzer`), do NOT begin synthesis
- Module boundary is ambiguous (does flow X belong here or in another
  module?) → SME-only decision
- No SME has confirmed the business name and scope of the module

## Output Contract

Produce a directory `04_modules/<MODULE-SLUG>/`:

```
04_modules/<MODULE-SLUG>/
├── module-overview.md          ← summary, evidence-view index, blocking TBDs, sign-off
├── 03-program-flow.md          ← Program Flow: application/program view (aggregates flows)
├── 04-data-flow.md             ← Data Flow: data view (aggregates lineage and persistence)
└── module-review-checklist.md  ← SME sign-off for the whole module
```

Use:

- `templates/module-overview.md` and `templates/view-template.md` as scaffolding
- `references/output-contract.md` for the file format and required fields for
  module-overview and the two default evidence views
- `references/synthesis-rules.md` for how to aggregate across flows
- `../../docs/module-analysis-model.md` for the canonical model

Follow:

- `../../docs/id-conventions.md` for stable IDs
  (`MODULE-*`, `VIEW-*`, `BR-*`, `ACTOR-*`, `SYS-*`, `DATA-*`)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence tagging
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Each default evidence view file must include a `## Mermaid Flow Diagram` section
immediately after the view status / summary material and before evidence,
inventory, or traceability tables. Mermaid diagrams are a visual coverage
surface for SME review, not independent evidence. Tables remain required as
evidence and traceability support, and every node/edge must be backed by
eligible evidence or a named `TBD-*`. When input is incomplete, include a
Mermaid placeholder node with a named `TBD-*` rather than drawing a plausible
but unsupported flow.

Mermaid preview guardrail: Mermaid source blocks are required; rendered IDE,
browser, or extension previews are optional. Do not open diagram previews unless
the user explicitly asks for visual inspection. For large modules, many
in-scope flows, or diagrams with more than about 80 nodes/edges, skip preview,
record the skip in `module-overview.md`, and continue with structural/manual
review. Never reopen the same preview or preview every view as a completion
check.

Examples:

- `examples/module-positive/` — complete CARD-AUTH module with overview plus
  Program Flow and Data Flow
- `examples/incomplete-module-negative/` — module with missing flow / SME gap

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required for standard code-backed runs**: module definition (slug +
  business name + scope statement + list of in-scope flows); approved
  `01_inventory/inventory.yaml` plus `01_inventory/object-map.md`; approved
  `flow-<FLOW-SLUG>.md` for every in-scope flow; compact program artifacts
  for every program referenced by confirmed flows (`program-analysis-summary.yaml`,
  `source-index.yaml`, `routine-logic-details.yaml`,
  `message-inventory.yaml`, `file-io-inventory.yaml`,
  `field-mutation-matrix.yaml`, `sql-inventory.yaml`); BAU notes from SME
  covering operational rhythm and manual procedures.
- **Required for explicit context-only drafts**: ready
  `00_context_packages/<MODULE-SLUG>/context-index.yaml` from
  `legacy-module-context-intake`; named owner risk acceptance that
  source/object evidence is unavailable for this cycle; all missing
  inventory/program/flow coverage carried as `TBD-*`; BAU notes from SME;
  source eligibility labels preserved for every carried context claim.
- **Optional**: architecture diagrams, data lineage docs, regulatory references.
- **Input readiness scoring**:
  - `0-5 blocked`: module scope unresolved, neither approved upstream flow
    analyses nor an explicit risk-accepted context-only package is supplied,
    triggered data/screen/report analysis missing, evidence links broken, or
    evidence authorization unresolved.
  - `6 minimum_pass`: for code-backed runs, approved inventory/object map,
    required flows, required program analyses, module slug/name/scope, and SME
    BAU notes are present; for context-only drafts, a ready context package
    plus named risk acceptance is present, with missing source coverage carried
    as blocking TBDs for later code-backed approval.
  - `7-8 usable`: triggered data/screen/report outputs, architecture notes,
    data lineage, and known TBD ledgers are supplied.
  - `9-10 strong`: SME edge cases, exception examples, sample transactions,
    regulatory context, modernization decision context, and flow-analyzer
    v0.2.3 replay / field-lineage / persistence / edge-resolution /
    exception-chain sections plus compact program sidecars
    are also supplied.
  - Missing architecture diagrams or regulatory references does not block the
    module analysis unless the module scope specifically depends on them.
- **Readiness checks**: for code-backed runs, every in-scope flow is
  `approved` or `approved_with_non_blocking_tbd`, every referenced program
  analysis and compact sidecar set is approved/present, inventory/object map
  is approved, and each in-scope flow exposes replay, lineage, persistence,
  node artifact availability, and exception-chain coverage (or a named waiver);
  for context-only drafts, the context package status is
  `ready_for_module_analysis` / `ready_with_warnings` and the output is
  explicitly non-approved; SME has confirmed the module's business name and
  boundary.
- **Stop conditions**: any in-scope flow lacks an approved analysis in a
  code-backed run; any in-scope flow lacks replay / lineage / persistence /
  exception-chain sections needed for code-backed module claims and no waiver
  exists; any code-backed artifact is missing and no context-only risk
  acceptance is recorded; module boundary is ambiguous (which module owns flow
  X); no SME has confirmed module identity; BAU notes are absent.

### Execution

- **Procedure**: see the Workflow section below (9 ordered steps).
- **Allowed inference**: aggregating across approved flow/program/
  inventory artifacts; aggregating approved flow replay paths, field lineage,
  persistence outcomes, and exception propagation chains; cross-view
  consistency checking; computing data lifecycle and coupling score from
  existing Object Dependency data; deriving BRD source eligibility from
  upstream evidence labels.
- **Forbidden assumptions**: inventing business actors, upstream /
  downstream systems, BAU rhythm, regulatory requirements, manual
  intervention procedures, cross-module dependencies, module-level replay
  paths, field lineage, persistence lifecycles, exception recovery, or
  business rules or BRD conclusions (these remain seeds/questions). Tier-2 SME claims that contradict
  tier-1 code become TBDs, not overrides.
- **TBD handling**: missing flow analysis → `TBD: pending_source`
  routing to `legacy-ibmi-flow-analyzer`; business context absent from
  BAU notes → `TBD: pending_sme_judgment`; ambiguous module boundary
  → `TBD: pending_sme_judgment`; incomplete data lifecycle →
  `TBD: pending_sme` (archive/purge ownership); missing replay, field-lineage,
  persistence, or exception-chain coverage in older flow artifacts →
  `TBD: pending_source` unless waived by named SME; missing compact program
  sidecars → `TBD: pending_source` routed to `legacy-ibmi-program-analyzer`.

### Output

- **Canonical directory**: `04_modules/<MODULE-SLUG>/` containing
  `module-overview.md`, `03-program-flow.md`, `04-data-flow.md`,
  `module-review-checklist.md`. Do not create `01-operation-flow.md` or
  `02-system-flow.md` by default.
- **Required sections**: evidence-view index with per-view status, top blocking
  TBDs, module-level capability seeds, BRD Functional Analysis Input
  Crosswalk, BRD Source Eligibility Crosswalk, Module Program-Chain Readiness,
  Module Persistence & Critical Field Summary, Module Exception & Recovery
  Summary, per-view `## Mermaid Flow Diagram` sections, and per-view review
  checklists. Program Flow must include Replay Coverage Summary. Data Flow must
  include Module Persistence Matrix, Critical Field Lineage Across Module, and
  Exception-Aware Data Risks.
- **Required IDs**: mints `MODULE-*`, `VIEW-*`, `ACTOR-*`, `SYS-*`,
  module-level `BR-*` **seeds**, module-level `CAP-*` **seeds**, and
  `TBD-*`. Reuses `OBJ-*`, `EV-*`, `FLOW-*`, `NODE-*`, `EDGE-*`,
  `DATA-*`, and flow-analyzer v0.2 IDs such as `REPLAY-*`, `LINEAGE-*`,
  `PERSIST-*`, and `EXCHAIN-*`. `legacy-brd-writer` reviews these seeds in
  business language; final promotion of `BR-*` still happens later in
  `legacy-spec-writer`.
- **Handoff status**: each view independently `draft` → `in_review` →
  `approved` or `approved_with_non_blocking_tbd`. For standard BRD/spec work,
  module approval requires the Code-Backed Analysis Gate: approved
  inventory/object map, flow analyses, and compact program artifacts. A context-only
  module may be reviewed as draft material, but it must remain `draft` or
  `needs_sme_review` for BRD approval until the missing code-backed artifacts
  are supplied.
  Only BRD crosswalk rows with source eligibility `confirmed_by_sme`,
  `code_backed`, or approved equivalent may be marked `brd_conclusion_allowed`.
  `candidate_only`, `generated_draft`, `source_documented` without review, and
  `missing` rows are `questions_only`.
  `blocked_pending_source` / `blocked_pending_sme` halt BRD writing and any
  later spec-writing.

### Validation

- **Mechanical**: overview, Program Flow, Data Flow, and checklist present;
  each evidence view has a
  fenced Mermaid `flowchart` diagram before its evidence / traceability
  tables; every Mermaid node or edge traces to source artifact, named SME
  note, or named `TBD-*`; every claim traces to source artifact or named SME
  note; every cross-view reference resolves; every TBD carries a category and
  ID; capability seeds carry IDs.
- **AI semantic**: cross-flow synthesis matches the flow analyses (no
  new IBM i facts introduced); consistency holds (every Program Flow replay
  path maps to a module event/outcome/TBD, and every Data Flow object traces
  to an approved flow/program); seeds
  are questions, not approved rules; replay, field-lineage, persistence, and
  exception-chain gaps are carried forward instead of being summarized away;
  tier-2 claims contradicting tier-1 are surfaced as TBDs; BRD sections 1-9
  are either covered by BRD-eligible evidence or carry explicit `TBD-*` gaps.
  AI-organized context cannot make a section `covered`.
- **SME / human approval**: module owner validates overview and scope,
  dev lead validates Program Flow, and data analyst validates Data Flow.
  Business or integration SMEs are required only for BRD crosswalk rows that
  depend on business/architecture claims.
- **Blocking conditions**: overview, Program Flow, or Data Flow lacks required
  review; any consistency gap unresolved; any in-scope flow missing or unapproved
  in a code-backed run; missing `object-map.md` or program analyses for a
  standard BRD/spec target; any capability seed contradicts the underlying
  flows; module scope still unconfirmed.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with
status `pass`, `pass_with_warnings`, or `blocked` when reporting upward
to the orchestrator.

## Workflow

1. **Confirm Module Scope**
   - Validate the module slug, business name, and scope statement with SME or
     an accepted context package.
   - If `00_context_packages/<MODULE-SLUG>/` is supplied, read
     `context-index.yaml`, `contradiction-log.md`, and `open-questions.md`
     first; block if the context package is not ready for module analysis.
   - Determine `evidence_mode`: `code_backed` when approved
     inventory/object-map + program + flow analyses are present;
     `context_only` only when a named owner has accepted missing source
     coverage for this cycle.
   - Treat any `00_context_packages/` operation/system/program/data view files
     as intake context only. Do not copy them into `04_modules/`.
   - List in-scope flows; check every one has an approved analysis.
   - For code-backed runs, confirm each in-scope flow exposes `Flow Replay
     Path`, `Cross-Program Field Lineage`, `Flow Persistence Matrix`, edge
     Evidence Source / Resolution, node artifact availability for
     `program-analysis-summary.yaml`, `source-index.yaml`,
     `routine-logic-details.yaml`, `message-inventory.yaml`,
     `file-io-inventory.yaml`, `field-mutation-matrix.yaml`,
     `sql-inventory.yaml`, and `Exception Propagation Chain`, or record a
     named SME waiver and `TBD-*`.
   - Confirm no in-scope flow actually belongs to a different module.
   - Assign `MODULE-<SLUG>-001`.

2. **Aggregate Programs, Objects, and Context**
   - List every program touched by any flow in scope.
   - List every object and key field touched from each flow's node artifact set
     and each program's compact sidecars: `program-analysis-summary.yaml`,
     `source-index.yaml`, `routine-logic-details.yaml`,
     `message-inventory.yaml`, `file-io-inventory.yaml`,
     `field-mutation-matrix.yaml`, and `sql-inventory.yaml`. Preserve source
     identifiers plus business meanings for critical fields.
   - Cross-check against `01_inventory/inventory.yaml`; create
     `pending_source` TBDs for gaps.
   - If business operation, channel, interface, SLA, security, or BAU context
     is supported by SME notes or source documents, carry it into
     `module-overview.md` and the BRD crosswalk with source eligibility.
     Otherwise mark it as partial/missing; do not synthesize standalone
     Operation/System flow files.

3. **Build Program Flow**
   - Use the Program Flow section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`.
   - **Primary source: all approved `flow-<FLOW-SLUG>.md` documents and their
     approved child compact program artifacts.** Do not concatenate full
     program analyses or flow analyses; use full Markdown only for targeted
     clarification when compact rows are insufficient.
   - Aggregate per-flow summaries; identify cross-flow dependencies and shared
     sub-programs.
   - Add a Replay Coverage Summary that lists each in-scope flow's `REPLAY-*`
     paths, major decision / exception branches, persisted outcomes, and
     missing replay / lineage / persistence gaps.
   - Draw the Mermaid program flow / call topology across the in-scope flows,
     entry programs, shared programs, exits, and external response or batch
     outcomes.
   - Do not re-derive control flow; reference the flow / program analyses. Do
     not use an ASCII tree as the primary topology diagram.
   - Output: `03-program-flow.md`.

4. **Build Data Flow**
   - Use the Data Flow section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`.
   - **Primary source: every flow's Cross-Program Data Flow,
     Cross-Program Field Lineage, Flow Persistence Matrix, and Exception
     Propagation Chain sections, backed by every program's
     `program-analysis-summary.yaml`, `source-index.yaml`,
     `routine-logic-details.yaml`, `message-inventory.yaml`,
     `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
     `sql-inventory.yaml`.**
   - Compute data lifecycle per object (created / updated / read /
     archived / purged) by walking flows.
   - Compute coupling score (number of flows touching each object).
   - Identify critical field lineage, persisted outputs, skipped mutations,
     commit/rollback/retry impacts, coupling hotspots, cross-module data
     dependencies, and DB table relationships.
   - Draw the Mermaid data movement / lifecycle flow showing which flows
     create, update, read, hand off, archive, or purge the major data objects.
   - Output: `04-data-flow.md`.

5. **Evidence-View Consistency Check**
   - Every `REPLAY-*` path in Program Flow maps to a module event, persisted
     outcome, exception outcome, or named `TBD-*`.
   - Every external or durable `PERSIST-*` output maps to a Data Flow object,
     output carrier, downstream consumer, or named `TBD-*`.
   - Every `LINEAGE-*` / `PERSIST-*` claim that affects modernization appears
     in Data Flow.
   - Every `EXCHAIN-*` has module-level error/recovery crosswalk coverage or a
     named `TBD-*`.
   - Every data object in Data Flow traces to at least one approved flow /
     program, dictionary row, or named source gap.
   - Mismatches become consistency TBDs; do not paper over them with business
     or architecture narrative.

6. **Build BRD Source Eligibility Crosswalk**
   - For each BRD section 1-9, list the module rows that could support the BRD.
   - Use Program Flow, Data Flow, approved flows/programs/inventory,
     SME-confirmed scope notes, and source-documented context as sources.
   - Mark each row `brd_conclusion_allowed` only when backed by
     `confirmed_by_sme`, `code_backed`, or approved flow/program/inventory
     evidence.
   - Mark `source_documented` rows as `needs_sme_review` unless the document has
     explicit SME approval for that claim.
   - Mark `candidate_only`, `generated_draft`, and `missing` rows as
     `questions_only`; they may become `TBD-*` or SME review prompts but not
     BRD conclusions.

7. **Write module-overview.md**
   - Evidence-view index with status for Program Flow and Data Flow.
   - Top blocking TBDs surfaced from overview, Program Flow, and Data Flow.
   - Optional SME-confirmed business / interface context notes when available.
   - Module Program-Chain Readiness summary across replay / lineage /
     persistence / exception-chain coverage.
   - Module Persistence & Critical Field Summary for BRD dependencies and
     downstream SDD data contracts.
   - Module Exception & Recovery Summary for BRD error-handling coverage.
   - Module-level capability seeds to be turned into BRD Packages by
     `legacy-brd-writer` before spec-writing.
   - BRD Source Eligibility Crosswalk and module-level review checklist.

8. **Prepare for SME Review**
   - Module owner reviews overview, scope, capability seeds, and BRD crosswalk
     eligibility.
   - Dev lead reviews `03-program-flow.md`.
   - Data analyst or data owner reviews `04-data-flow.md`.
   - Business or integration SMEs review only the overview/crosswalk rows that
     depend on business operation, channel, interface, SLA, security, or BAU
     claims.
   - Module is approved only when overview, Program Flow, and Data Flow are at
     least `approved_with_non_blocking_tbd` and no blocking crosswalk gaps
     remain.

9. **Finalize and stop**
   - After `03-program-flow.md`, `04-data-flow.md`, `module-overview.md`,
     `module-review-checklist.md`, and workflow-state write-back are recorded,
     stop the run and report the module package path plus any manual preview
     follow-up.
   - Do not keep re-reading the module directory, repeatedly checking workflow
     status, or opening Mermaid previews after write-back unless a concrete
     validation finding names a file to fix.

## Workflow State Write-Back

At the end of a module-analysis run, update
`<project-root>/workflow-state.yaml` per
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md).
Template: [`skills/legacy-modernization-orchestrator/references/state-writeback-snippet.md`](../legacy-modernization-orchestrator/references/state-writeback-snippet.md).

**Stage this skill produces:**

- `3f Module Analysis Done` when `module-overview.md`, `03-program-flow.md`,
  `04-data-flow.md`, and `module-review-checklist.md` are approved or
  `approved_with_non_blocking_tbd`; capability seeds (`CAP-*`) are listed in
  the overview with source eligibility; and no blocking BRD crosswalk gaps
  remain.
- `3e Module Analysis In Progress` when overview, Program Flow, Data Flow, or
  any required coverage section is still draft or missing.

**Last artifact path pattern:**
`04_modules/<MODULE-SLUG>/module-overview.md` (with sibling view files)

**Writes per run:**

1. Overwrite `capabilities[<CAP-* from current_focus>]` (or, for each
   `CAP-*` seeded in `module-overview.md` if the orchestrator scoped the
   module rather than a single capability) with stage id, overview path,
   `last_skill: legacy-ibmi-module-analyzer`, and blocking IDs (`tbds`,
   `sme_pending` for every `inferred_business_rule`).
2. Append one `history[]` entry with `note` naming the module
   (e.g. `"synthesized CREDIT-CHECK module overview, program flow, and data flow"`).
3. Overwrite `project.last_updated_at` / `project.last_updated_by`.

If this module yields multiple `CAP-*` seeds and the orchestrator scoped
the entire module (not a single capability), write one `capabilities[]`
entry per seed at the same `stage_id: "3f Module Analysis Done"`. Do not
silently collapse them into one entry.

Never touch `current_focus`, other capabilities' entries beyond your
module's seeds, or past `history[]` rows.

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`.
Business operation and system-landscape context **necessarily** rely on SME and
integration documentation (tier 2/3) because business "why" and architectural
intent live outside code. Preserve that context in `module-overview.md` and the
BRD crosswalk only when it is source-backed; do not generate standalone
Operation/System flow files by default. Any tier-2 claim that contradicts
tier-1 evidence (e.g., SME says "we no longer use path X" but code still has
the path; SME says "every transaction is logged" but the log write is
conditional in code) **does not override the code**. The spec records what code
does; the SME claim becomes a TBD requiring SME to confirm whether the code is
dead, drifted, or correct.

Program Flow and Data Flow are tier-1-grounded by construction (they aggregate
code-derived flow / program analyses).

**Do NOT invent:**

- **Business actors** not named by SME (no inferring "the marketing team
  uses this" from code)
- **Upstream/downstream systems** not visible in any flow's Trigger
  Context or External Calls section
- **BAU rhythm** (cut-off times, peak hours) — must come from SME
- **Regulatory requirements** — must come from SME or referenced doc
- **Manual intervention procedures** — must come from SME
- **Cross-module data dependencies** without seeing the consuming module's
  inventory or SME confirmation
- **Module-level replay paths, field lineage, persistence lifecycles, or
  exception recovery** not present in approved flow/program artifacts or named
  SME notes
- **File I/O, mutation, or SQL behavior** not present in approved
  `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, `sql-inventory.yaml`,
  flow `PERSIST-*` / `LINEAGE-*` / `EXCHAIN-*` rows, or named SME notes
- **Business rules** — only seeds (questions); the BRD writer reviews them in
  business language, and the spec-writer later resolves formal rule promotion
  with SME approval

**Instead:**

- If BRD crosswalk needs business context not in SME/source notes → TBD:
  pending_sme_judgment
- If BRD crosswalk needs integration detail not in any flow → TBD: pending_source
  (request integration spec) or pending_sme
- If a flow seems to belong to multiple modules → TBD: pending_sme_judgment
  on module boundary
- If a data object's lifecycle is incomplete → TBD: pending_sme
  (who archives / purges this?)

**Evidence minimum:**

- Every claim in overview, Program Flow, and Data Flow must trace to either
  source (flow / program / inventory) or to a named SME / SME note.
- "Confirmed by SME [name] on [date]" is valid evidence; "common knowledge"
  is not.

## SME Review Questions

**Module Overview / BRD Crosswalk:**
- Is the module scope statement correct and bounded?
- Are capability seeds reasonable business questions rather than program-entry
  wrappers?
- Are business operation, channel, interface, SLA, security, or BAU claims
  backed by named SME/source evidence?
- Are partial or missing BRD sections carried as `TBD-*` instead of being
  inferred from code?

**Program Flow:**
- All flows in scope? Any missing or extra flows?
- Can each flow be replayed from trigger to final response, persistence,
  rollback, or manual outcome?
- Cross-flow dependencies correct?
- Shared sub-programs correctly identified?

**Data Flow:**
- Data lifecycle correct for each major object?
- Are critical fields traced from source through module-level persistence and
  downstream outputs?
- Are skipped mutations, rollback/retry effects, and exception-state writes
  represented accurately?
- Coupling hotspots match operational reality (which files are "scary
  to change")?
- Cross-module data dependencies correctly identified?

## Runtime Portability

Canonical source: `skills/legacy-ibmi-module-analyzer/SKILL.md`

Synced via `scripts/sync-skills.sh` to all four runtime adapters.

## Version History

- v0.2.5 (2026-06-06): Compact flow/program sidecar aggregation alignment
  - Required module analysis to consume flow-analyzer v0.2.3 node artifact
    availability and compact child program artifacts before full Markdown
  - Added module-level Flow Artifact Set tracking for
    `program-analysis-summary.yaml`, `source-index.yaml`,
    `routine-logic-details.yaml`, `message-inventory.yaml`,
    `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
    `sql-inventory.yaml`
  - Routed missing compact program sidecars back to
    `legacy-ibmi-program-analyzer` instead of allowing module synthesis to
    infer from concatenated documents

- v0.2.4 (2026-06-04): Removed default Operation Flow and System Flow outputs.
  Module analysis now produces `module-overview.md`, `03-program-flow.md`,
  `04-data-flow.md`, and `module-review-checklist.md` by default. Business and
  system context remain source-backed notes / BRD crosswalk inputs in the
  overview, not standalone generated flow files.

- v0.2.3 (2026-06-03): Recast module analysis as evidence-bounded assembly and
  coverage mapping. Added BRD source eligibility so context-only,
  generated-draft, candidate-only, or unreviewed source-documented rows feed
  BRD questions/TBDs only, not BRD conclusions.

- v0.2.2 (2026-06-02): Aligned module synthesis inputs with
  program-analyzer v0.2.5 routine-local evidence. View 4 and readiness checks
  now preserve Routine Logic Details' conditioned calculation blocks,
  carrier/lineage, and exception closure evidence when it explains critical
  field calculations, persistence, rollback/skipped work, or module-level
  exception-aware data risks.

- v0.2.1 (2026-06-02): Aligned module synthesis with flow/program v0.2.1.
  Code-backed module analysis now preserves flow edge Evidence Source /
  Resolution, source identifier + business meaning field pairs, File I/O
  Purpose, Validation Logic carry-forward, and upstream Open Items /
  Limitations when aggregating readiness, data, exception, and BRD crosswalk
  outputs.

- v0.2.0 (2026-06-01): Aligned module synthesis with program/flow v0.2.0.
  Code-backed module analysis now requires or waives replay, critical field
  lineage, persistence, and exception-chain coverage, and aggregates those
  surfaces into module-level readiness, data, and BRD crosswalk outputs.

- v0.1.6 (2026-05-31): Added Mermaid preview and stop-after-writeback
  guardrails so large module packages do not keep processing after view files,
  overview, checklist, and workflow-state write-back are recorded.

- v0.1.5 (2026-05-30): Added code-backed vs context-only evidence mode. A
  module-first context package can seed draft synthesis, but standard BRD/spec
  work now requires `object-map.md`, program analyses, and flow analyses before
  module output can be treated as code-backed.

- v0.1.4 (2026-05-29): Aligned module-analyzer downstream wording with the
  BRD-first workflow and made Mermaid diagrams mandatory for each view. The
  standard consumer is `legacy-brd-writer` before any spec-writing.

- v0.1.3 (2026-05-29): Added canonical timing guidance so upstream context
  package views are consumed as inputs and final module-analysis artifacts are
  generated only under `04_modules/<MODULE-SLUG>/`.

- v0.1.2 (2026-05-28): BRD functional-analysis crosswalk
  - Added a module-level crosswalk for SME-required BRD sections 1-9 and
    optional sections 10-12
  - Required missing or partial BRD inputs to be carried as named `TBD-*`
    gaps instead of being inferred downstream
  - Updated the positive module example and output contract so
    `legacy-brd-writer` can consume module analysis without remapping sources

- v0.1.1 (2026-05-14): Post-review hardening
  - Fixed broken reference links in SKILL.md (nonexistent per-view methodology files)
  - Added `blocked_pending_source` and `blocked_pending_sme` status values
  - Added per-view review checklists to output contract
  - Strengthened evidence traceability (TBD ID and Evidence Ref columns)
  - Added positive and negative smoke test prompts to runtime-smoke-tests.md
  - Ready for smoke testing in Codex CLI, Claude Code, OpenCode

- v0.1.0 (2026-05-14): Initial release
  - 9-step workflow
  - Module synthesis across operation, system, program, and data concerns
  - Cross-view consistency checks
  - Module-level capability seeds (for BRD writer and later spec-writer)
  - Feedback loops to flow-analyzer, program-analyzer, inventory
  - Examples: complete module (CARD-AUTH), incomplete module (missing flow)
