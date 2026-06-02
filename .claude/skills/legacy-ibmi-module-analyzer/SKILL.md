---
name: legacy-ibmi-module-analyzer
description: Synthesize a complete IBM i business module from multiple flow analyses, BAU notes, or a ready module-first context package, producing the canonical Mermaid-backed 4-view module analysis (Operation Flow, System Flow, Program Flow, Data Flow). Use when multiple flows belong to the same business module, or when `legacy-module-context-intake` has normalized external RAG / human four-view context and you need module synthesis to feed BRD writing and review before spec-writing. Layer 1.5 (platform-specific) skill. Implements the model defined in `docs/module-analysis-model.md`.
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
| Problem solved | Synthesizes multiple IBM i flows or module-first context into the canonical four-view module analysis. |
| Input | Flow analyses, program analyses, data/screen evidence, BAU notes, or an accepted `00_context_packages/<MODULE-SLUG>/` package. |
| Output | Mermaid-backed Operation Flow, System Flow, Program Flow, and Data Flow module analysis with review status. |
| Core prompt strategy | Preserve evidence boundaries across views, use diagrams as traceable summaries, and keep uncertain behavior as TBDs. |
| Upstream skill | `legacy-ibmi-flow-analyzer` or `legacy-module-context-intake`. |
| Downstream consumer | `legacy-brd-writer`, `legacy-spec-writer`, SMEs, and module review workflows. |
| Validation standard | Four views align without contradictions, all key nodes trace to evidence, and module-analysis model rules are followed. |
| Known risk | Producing polished diagrams that make unresolved flow gaps look approved. |
| Practical example | Combine order entry, release, and cancellation flows into one four-view Order Management module analysis. |

## Purpose

Synthesize multiple flow analyses, BAU (Business As Usual) notes, and SME
context into one **business module** analysis covering four standard
views: Operation Flow, System Flow, Program Flow, Data Flow.

This skill is the **last platform-specific layer** before `legacy-brd-writer`
and the BRD Review Gate. It does not re-analyze flows or programs; it
aggregates and synthesizes what flow-analyzer and program-analyzer produced.
For the standard BRD/spec path, those code-backed inputs are required: a
module-first context package can seed the synthesis, but it cannot by itself
make View 3 (Program Flow), View 4 (Data Flow), or the downstream BRD
`confirmed_from_code`.

This is the only skill that produces the canonical four module-analysis view
artifacts under `04_modules/<MODULE-SLUG>/`. If upstream
`00_context_packages/` files already contain four context views, treat them as
evidence/context input and synthesize fresh module-analysis outputs here. Do
not copy or report upstream context views as the final module-analysis views.

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
  analysis.
- **Approved flow analyses** for every flow in scope
  (`flow-<FLOW-SLUG>.md`)
  - For code-backed runs, each approved flow should be
    `legacy-ibmi-flow-analyzer` v0.2.2 or later, or otherwise expose the
    equivalent `Flow Replay Path`, `Cross-Program Field Lineage`,
    `Flow Persistence Matrix` with File I/O Purpose, edge Evidence Source /
    Resolution, and `Exception Propagation Chain` with Validation Logic /
    routine-local exception closure carry-forward sections.
    Older flow artifacts require refresh or a named SME waiver before they
    can support module-level replay, lineage, persistence, or exception
    claims.
- **Approved program analyses** for every program referenced by those flows
  - For code-backed runs, prefer program-analyzer v0.2.5 or later where
    Routine Logic Details include conditioned calculation blocks,
    routine-local field lineage / carriers, and routine-local exception
    closure, with front-loaded Validation Logic. Use these rows to preserve
    field calculations, handoffs, skipped
    work, rollback, and visible error outcomes when flow evidence references
    the underlying program-level detail.
- **Approved inventory** with module scope confirmed
- **BAU notes from SME** — operational rhythm, manual processes,
  exception handling, business context not in code
- **Optional:** architecture diagrams (for System Flow), data lineage
  documents, regulatory references
- **Conditionally required from triggers:**
  - When `inventory.yaml.sme_review.downstream_required.screen_report_analyzer.required: true`
    → approved `screen-report-analysis.md` for every triggered DSPF /
    PRTF / menu. View 1 (Operation Flow) consumes these as primary
    sources for screen-driven rules; absence means missing 40% of
    user-facing decisions.
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
  SME waiver exists → route back to `legacy-ibmi-flow-analyzer` for v0.2.2
  refresh
- A trigger is `required: true` but the corresponding artifact is missing
  → route to the triggered skill (`legacy-ibmi-screen-report-analyzer`
  or `legacy-ibmi-data-model-analyzer`), do NOT begin synthesis
- Module boundary is ambiguous (does flow X belong here or in another
  module?) → SME-only decision
- No SME has confirmed the business name and scope of the module
- BAU notes are absent; the Operation Flow view requires SME input that
  cannot be derived from code alone

## Output Contract

Produce a directory `04_modules/<MODULE-SLUG>/`:

```
04_modules/<MODULE-SLUG>/
├── module-overview.md          ← summary, 4-view index, blocking TBDs, sign-off
├── 01-operation-flow.md        ← View 1: Business view + BAU
├── 02-system-flow.md           ← View 2: Integration view
├── 03-program-flow.md          ← View 3: Application/program view (aggregates flows)
├── 04-data-flow.md             ← View 4: Data view (aggregates lineage and persistence)
└── module-review-checklist.md  ← SME sign-off for the whole module
```

Use:

- `templates/module-overview.md` and `templates/view-template.md` as scaffolding
- `references/output-contract.md` for the file format and required fields for
  module-overview and all four views
- `references/synthesis-rules.md` for how to aggregate across flows
- `../../docs/module-analysis-model.md` for the canonical model

Follow:

- `../../docs/id-conventions.md` for stable IDs
  (`MODULE-*`, `VIEW-*`, `BR-*`, `ACTOR-*`, `SYS-*`, `DATA-*`)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence tagging
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Each of the four view files must include a `## Mermaid Flow Diagram` section
immediately after the view status / summary material and before evidence,
inventory, or traceability tables. Mermaid diagrams are the primary visual flow
surface for SME review. Tables remain required as evidence and traceability
support, but a table-only view is not a valid module-analysis flow. When input
is incomplete, include a Mermaid placeholder node with a named `TBD-*` rather
than omitting the diagram.

Mermaid preview guardrail: Mermaid source blocks are required; rendered IDE,
browser, or extension previews are optional. Do not open diagram previews unless
the user explicitly asks for visual inspection. For large modules, many
in-scope flows, or diagrams with more than about 80 nodes/edges, skip preview,
record the skip in `module-overview.md`, and continue with structural/manual
review. Never reopen the same preview or preview all four views as a completion
check.

Examples:

- `examples/module-positive/` — complete CARD-AUTH module with all 4 views
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
  `program-analysis-<OBJ-ID>.md` for every program referenced by confirmed
  flows; approved `flow-<FLOW-SLUG>.md` for every in-scope flow; BAU notes
  from SME covering operational rhythm and manual procedures.
- **Required for explicit context-only drafts**: ready
  `00_context_packages/<MODULE-SLUG>/context-index.yaml` from
  `legacy-module-context-intake`; named owner risk acceptance that
  source/object evidence is unavailable for this cycle; all missing
  inventory/program/flow coverage carried as `TBD-*`; BAU notes from SME.
- **Optional**: architecture diagrams (View 2), data lineage docs
  (View 4), regulatory references.
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
    v0.2.1 replay / field-lineage / persistence / edge-resolution /
    exception-chain sections
    are also supplied.
  - Missing architecture diagrams or regulatory references does not block the
    module analysis unless the module scope specifically depends on them.
- **Readiness checks**: for code-backed runs, every in-scope flow is
  `approved` or `approved_with_non_blocking_tbd`, every referenced program
  analysis is approved, inventory/object map is approved, and each in-scope
  flow exposes replay, lineage, persistence, and exception-chain coverage
  (or a named waiver); for context-only drafts, the context package status is
  `ready_for_module_analysis` / `ready_with_warnings` and the output is
  explicitly non-approved; SME has confirmed the module's business name and
  boundary; BAU notes are present (View 1 requires SME input that code alone
  cannot supply).
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
  existing Object Dependency data.
- **Forbidden assumptions**: inventing business actors, upstream /
  downstream systems, BAU rhythm, regulatory requirements, manual
  intervention procedures, cross-module dependencies, module-level replay
  paths, field lineage, persistence lifecycles, exception recovery, or
  business rules (these remain seeds). Tier-2 SME claims that contradict
  tier-1 code become TBDs, not overrides.
- **TBD handling**: missing flow analysis → `TBD: pending_source`
  routing to `legacy-ibmi-flow-analyzer`; business context absent from
  BAU notes → `TBD: pending_sme_judgment`; ambiguous module boundary
  → `TBD: pending_sme_judgment`; incomplete data lifecycle →
  `TBD: pending_sme` (archive/purge ownership); missing replay, field-lineage,
  persistence, or exception-chain coverage in older flow artifacts →
  `TBD: pending_source` unless waived by named SME.

### Output

- **Canonical directory**: `04_modules/<MODULE-SLUG>/` containing
  `module-overview.md`, `01-operation-flow.md`, `02-system-flow.md`,
  `03-program-flow.md`, `04-data-flow.md`, `module-review-checklist.md`.
- **Required sections**: 4-view index with per-view status, top blocking
  TBDs, module-level capability seeds, BRD Functional Analysis Input
  Crosswalk, Module Program-Chain Readiness, Module Persistence & Critical
  Field Summary, Module Exception & Recovery Summary, per-view `## Mermaid
  Flow Diagram` sections, and per-view review checklists. View 3 must include
  Replay Coverage Summary. View 4 must include Module Persistence Matrix,
  Critical Field Lineage Across Module, and Exception-Aware Data Risks.
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
  inventory/object map, program analyses, and flow analyses. A context-only
  module may be reviewed as draft material, but it must remain `draft` or
  `needs_sme_review` for BRD approval until the missing code-backed artifacts
  are supplied.
  `blocked_pending_source` / `blocked_pending_sme` halt BRD writing and any
  later spec-writing.

### Validation

- **Mechanical**: all four views plus overview present; each view has a
  fenced Mermaid `flowchart` diagram before its evidence / traceability
  tables; every Mermaid node or edge traces to source artifact, named SME
  note, or named `TBD-*`; every claim traces to source artifact or named SME
  note; every cross-view reference resolves; every TBD carries a category and
  ID; capability seeds carry IDs.
- **AI semantic**: cross-flow synthesis matches the flow analyses (no
  new IBM i facts introduced); cross-view consistency holds (every View 1
  actor appears in View 3 or is tagged manual; every View 2 system
  appears in View 3; every View 4 data object traces to a flow); seeds
  are questions, not approved rules; replay, field-lineage, persistence, and
  exception-chain gaps are carried forward instead of being summarized away;
  tier-2 claims contradicting tier-1 are surfaced as TBDs; BRD sections 1-9
  are either covered by named module evidence or carry explicit `TBD-*` gaps.
- **SME / human approval**: View 1 by business owner, View 2 by
  integration architect, View 3 by dev lead, View 4 by data analyst.
  All four sign-offs are required to promote the module past
  `approved_with_non_blocking_tbd` for BRD writer consumption.
- **Blocking conditions**: any view lacks an SME sign-off; any
  cross-view inconsistency unresolved; any in-scope flow missing or unapproved
  in a code-backed run; missing `object-map.md` or program analyses for a
  standard BRD/spec target; any capability seed contradicts the underlying
  flows; BAU notes still absent.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with
status `pass`, `pass_with_warnings`, or `blocked` when reporting upward
to the orchestrator.

## Workflow

1. **Confirm Module Scope**
   - Validate the module slug, business name, and scope statement with SME
   - If `00_context_packages/<MODULE-SLUG>/` is supplied, read
     `context-index.yaml`, `contradiction-log.md`, and `open-questions.md`
     first; block if the context package is not ready for module analysis
   - Determine `evidence_mode`: `code_backed` when approved
     inventory/object-map + program + flow analyses are present;
     `context_only` only when a named owner has accepted missing source
     coverage for this cycle
   - Treat any `00_context_packages/` view files as intake context only; the
     canonical module views must be generated under `04_modules/<MODULE-SLUG>/`
   - List in-scope flows; check every one has an approved analysis
   - For code-backed runs, confirm each in-scope flow exposes `Flow Replay
     Path`, `Cross-Program Field Lineage`, `Flow Persistence Matrix`, edge
     Evidence Source / Resolution, and `Exception Propagation Chain`, or
     record a named SME waiver and `TBD-*`
   - Confirm no in-scope flow actually belongs to a different module
   - Assign `MODULE-<SLUG>-001`

2. **Aggregate Inventory of Programs & Objects**
   - List every program touched by any flow in scope (from each flow's
     Nodes section)
   - List every object and key field touched (from each program's Object
     Dependencies, Key File & Field Logic, File I/O Purpose, and Field
     Mutation Matrix sections). Preserve source identifiers plus business
     meanings for critical fields.
   - Cross-check against `01_inventory/inventory.yaml`; create
     `pending_source` TBDs for gaps
   - If the run is intended to feed an approvable BRD/spec and
     `01_inventory/object-map.md` is missing, stop and route to
     `legacy-ibmi-inventory`

3. **Build View 1 — Operation Flow / Business Background**
   - Use the View 1 section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`
   - **Primary source: SME interviews + BAU notes.** Code is secondary.
   - Capture: business scope, actors, business events, BAU rhythm,
     manual intervention points, exception lifecycle, business-rule seeds
   - Consume each flow's `Flow Replay Path` to ensure every business event has
     a replayable path or a named gap
   - Consume each flow's `Exception Propagation Chain` to aggregate
     operational exception outcomes, skipped work, manual recovery, and
     BRD error-handling seeds
   - Draw the Mermaid flow from actors to business events, manual
     interventions, exception outcomes, and BRD-relevant rule seeds
   - Do **not** derive business rules from field names
   - Output: `01-operation-flow.md`

4. **Build View 2 — System Flow**
   - Use the View 2 section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`
   - **Primary source: architecture diagrams, integration specs, SME.**
     Code (especially API/MQ/IFS code in flows) confirms.
   - Capture: upstream systems, downstream systems, external interfaces,
     integration patterns, sync/async boundaries, SLA constraints,
     security boundaries
   - Draw the Mermaid system/interface flow across upstream systems,
     interfaces, the IBM i module boundary, downstream systems, and security
     boundaries
   - Output: `02-system-flow.md`

5. **Build View 3 — Program Flow (Aggregate)**
   - Use the View 3 section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`
   - **Primary source: all `flow-<FLOW-SLUG>.md` documents.**
   - Aggregate per-flow summaries; identify cross-flow dependencies and
     shared sub-programs
   - Add a Replay Coverage Summary that lists each in-scope flow's
     `REPLAY-*` paths, major decision / exception branches, persisted
     outcomes, and missing replay / lineage / persistence gaps
   - Draw the Mermaid program flow / call topology across the in-scope flows,
     entry programs, shared programs, exits, and external response or batch
     outcomes
   - Do **not** re-derive control flow; reference the flow / program
     analyses. Do not use an ASCII tree as the primary topology diagram.
   - Output: `03-program-flow.md`

6. **Build View 4 — Data Flow (Aggregate)**
   - Use the View 4 section in `references/output-contract.md` and the
     aggregation rules in `references/synthesis-rules.md`
   - **Primary source: every flow's Cross-Program Data Flow,
     Cross-Program Field Lineage, Flow Persistence Matrix, and Exception
     Propagation Chain sections, backed by every program's Data Touch Map,
     Object Dependencies, File I/O Purpose, Field Mutation Matrix, Key File &
     Field Logic, and Validation Logic.**
   - Compute data lifecycle per object (created / updated / read /
     archived / purged) by walking flows
   - Compute coupling score (number of flows touching each object)
   - Identify critical field lineage, persisted outputs, skipped mutations,
     commit/rollback/retry impacts, coupling hotspots, cross-module data
     dependencies, and DB table relationships
   - Draw the Mermaid data movement / lifecycle flow showing which flows
     create, update, read, hand off, archive, or purge the major data objects
   - Output: `04-data-flow.md`

7. **Cross-View Consistency Check**
   - Every business actor in View 1 should map to at least one entry node
     in View 3 (or be tagged "manual actor — no code path")
   - Every upstream/downstream system in View 2 should appear at least
     once in View 3 as a trigger or external call
   - Every business-rule seed in View 1 must reference at least one
     program / file in View 3 / View 4
   - Every `REPLAY-*` path in View 3 should map to a View 1 business event
     or exception outcome
   - Every external or durable `PERSIST-*` output should map to View 2
     system/manual consumers or View 4 data objects
   - Every `LINEAGE-*` / `PERSIST-*` claim should appear in View 4
   - Every `EXCHAIN-*` should have a View 1 operational outcome and BRD
     error-handling crosswalk coverage or a named `TBD-*`
   - Every data object in View 4 must trace to at least one flow / program
     in View 3
   - Mismatches → cross-view TBDs

8. **Write module-overview.md**
   - 4-view index with status per view
   - Top blocking TBDs surfaced from any view
   - Module Program-Chain Readiness summary across replay / lineage /
     persistence / exception-chain coverage
   - Module Persistence & Critical Field Summary for BRD dependencies and
     downstream SDD data contracts
   - Module Exception & Recovery Summary for BRD error-handling coverage
   - Module-level capability seeds (which capabilities live in this module,
     to be turned into BRD Packages by `legacy-brd-writer` before spec-writing)
   - Module-level review checklist

9. **Prepare for SME Review**
   - Each view independently goes to its appropriate SME (business owner
     for View 1, integration architect for View 2, dev lead for View 3,
     data analyst for View 4)
   - Module is approved only when **all four views** are at least
     `approved_with_non_blocking_tbd`

10. **Finalize and stop**
    - After the four view files, `module-overview.md`,
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

- `3f Module Analysis Done` when all 4 views (Operation / System / Program
  / Data) and `module-overview.md` are approved, capability seeds (`CAP-*`)
  are listed in the overview, and View 1 business rule seeds (`BR-*`)
  carry `evidence_id` + `knowledge_type`
- `3e Module Analysis In Progress` when one or more views are still draft
  or any required section is missing

**Last artifact path pattern:**
`04_modules/<MODULE-SLUG>/module-overview.md` (with sibling view files)

**Writes per run:**

1. Overwrite `capabilities[<CAP-* from current_focus>]` (or, for each
   `CAP-*` seeded in `module-overview.md` if the orchestrator scoped the
   module rather than a single capability) with stage id, overview path,
   `last_skill: legacy-ibmi-module-analyzer`, and blocking IDs (`tbds`,
   `sme_pending` for every `inferred_business_rule`).
2. Append one `history[]` entry with `note` naming the module
   (e.g. `"synthesized CREDIT-CHECK 4 views"`).
3. Overwrite `project.last_updated_at` / `project.last_updated_by`.

If this module yields multiple `CAP-*` seeds and the orchestrator scoped
the entire module (not a single capability), write one `capabilities[]`
entry per seed at the same `stage_id: "3f Module Analysis Done"`. Do not
silently collapse them into one entry.

Never touch `current_focus`, other capabilities' entries beyond your
module's seeds, or past `history[]` rows.

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`.
View 1 (Operation Flow) and View 2 (System Flow) **necessarily** rely on
SME and integration documentation (tier 2/3) because business "why" and
architectural intent live outside code. However, any tier-2 claim that
contradicts tier-1 evidence (e.g., SME says "we no longer use path X"
but code still has the path; SME says "every transaction is logged" but
the log write is conditional in code) **does not override the code**.
The spec records what code does; the SME claim becomes a TBD requiring
SME to confirm whether the code is dead, drifted, or correct.

Views 3 and 4 are tier-1-grounded by construction (they aggregate
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
- **Business rules** — only seeds (questions); the BRD writer reviews them in
  business language, and the spec-writer later resolves formal rule promotion
  with SME approval

**Instead:**

- If View 1 needs business context not in BAU notes → TBD: pending_sme_judgment
- If View 2 needs integration detail not in any flow → TBD: pending_source
  (request integration spec) or pending_sme
- If a flow seems to belong to multiple modules → TBD: pending_sme_judgment
  on module boundary
- If a data object's lifecycle is incomplete → TBD: pending_sme
  (who archives / purges this?)

**Evidence minimum:**

- Every claim in every view must trace to either source (flow / program /
  inventory) or to a named SME / SME note.
- "Confirmed by SME [name] on [date]" is valid evidence; "common knowledge"
  is not.

## SME Review Questions

Per view:

**View 1 (Operation Flow):**
- Are the business actors complete? Any missing roles?
- Is the BAU rhythm correct? Cut-off times, peak hours, seasonal patterns?
- Are exception-handling procedures accurate?
- Do the exception outcomes from each `EXCHAIN-*` match actual recovery,
  escalation, skipped work, and manual handling?
- Are the business-rule seeds reasonable questions?

**View 2 (System Flow):**
- All upstream and downstream systems listed?
- Integration patterns correct?
- SLAs accurate?
- Do durable outputs from `PERSIST-*` map to the correct external systems,
  files, queues, spool users, or manual consumers?

**View 3 (Program Flow):**
- All flows in scope? Any missing or extra flows?
- Can each flow be replayed from trigger to final response, persistence,
  rollback, or manual outcome?
- Cross-flow dependencies correct?
- Shared sub-programs correctly identified?

**View 4 (Data Flow):**
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
  guardrails so large four-view module packages do not keep processing after
  view files, overview, checklist, and workflow-state write-back are recorded.

- v0.1.5 (2026-05-30): Added code-backed vs context-only evidence mode. A
  module-first context package can seed draft synthesis, but standard BRD/spec
  work now requires `object-map.md`, program analyses, and flow analyses before
  module output can be treated as code-backed.

- v0.1.4 (2026-05-29): Aligned module-analyzer downstream wording with the
  BRD-first workflow and made Mermaid diagrams mandatory for each view. The
  four canonical module-analysis view files are still generated here, but their
  standard consumer is `legacy-brd-writer` before any spec-writing.

- v0.1.3 (2026-05-29): Added canonical timing guidance so upstream context
  package views are consumed as inputs and final four module-analysis view
  artifacts are generated only under `04_modules/<MODULE-SLUG>/`.

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
  - Added per-view review checklists (View 1–4) to output contract
  - Strengthened evidence traceability (TBD ID and Evidence Ref columns)
  - Added positive and negative smoke test prompts to runtime-smoke-tests.md
  - Ready for smoke testing in Codex CLI, Claude Code, OpenCode

- v0.1.0 (2026-05-14): Initial release
  - 9-step workflow
  - 4-view synthesis (Operation / System / Program / Data)
  - Cross-view consistency checks
  - Module-level capability seeds (for BRD writer and later spec-writer)
  - Feedback loops to flow-analyzer, program-analyzer, inventory
  - Examples: complete module (CARD-AUTH), incomplete module (missing flow)
