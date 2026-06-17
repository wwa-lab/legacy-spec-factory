---
name: legacy-ibmi-flow-analyzer
description: Merge multiple IBM i program-analysis artifacts into a compact SME program-set core review, especially when an SME provides a program-flow list and wants Calculation Logic, Validation Logic, Exception Handling, and Message Inventory without rescanning. Supports central artifact reuse from delivery repo remote main before source scan and records per-program lookup status. Also retains explicit full transaction-flow analysis support for seven trigger models when requested separately. Layer 1.5 (platform-specific) skill of the Legacy Spec Factory reverse chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Flow Analyzer

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Merges a SME-provided multi-program flow/list into one compact program-set core review without losing any requested program. Full transaction-flow analysis remains available only when explicitly requested. |
| Input | Approved inventory, relevant program analyses or central delivery artifact paths, trigger context, runtime clues, screen/report evidence, and SME notes. |
| Output | For SME-provided program-flow/core merge requests, `program-set-sme-core-review.md` only. For separately requested full transaction-flow analysis, `flow-<FLOW-SLUG>.md`. |
| Core prompt strategy | Reuse remote-main central program artifacts first, aggregate compact core artifacts, preserve SME order as navigation evidence, and expose missing programs/sections in a completeness ledger. |
| Upstream skill | `legacy-ibmi-program-analyzer` and `legacy-ibmi-inventory`. |
| Downstream consumer | `legacy-ibmi-module-analyzer`, `legacy-brd-writer`, and capability/spec preparation. |
| Validation standard | All called programs and files map to inventory IDs, trigger model is declared, and unresolved branches are not hidden. |
| Known risk | Over-connecting programs into a transaction flow because names or call chains look related. |
| Practical example | Analyze an order-release flow from menu option through RPGLE validation, update programs, spool output, and error handling. |

## Purpose

For the current SME program-flow workflow, merge multiple analyzed programs
into one compact **program-set SME core review**. Where
`legacy-ibmi-program-analyzer` looks inside one program, this skill combines
the already-produced core logic from every program the SME named, without
re-reading full source and without producing a full engineering flow artifact.

Full transaction-flow analysis is still available when explicitly requested,
but it is not the default output for SME-provided program-flow intake.

The primary orientation view is a **Transaction Call Map**: an RDi-style
cross-program/cross-boundary call map. It is not a statement-level
flowchart. It should preserve the transaction's program and external
dependency structure while keeping full call details in tables.

This skill supports **central artifact reuse** before any source scan. If the
central delivery documents repo remote `main` already contains an exact
program folder for a program named by the user or discovered in the flow, load
that program's compact artifacts from the remote-main sparse checkout or a
fresh cache verified against `origin/main`; do not rescan the program and do
not read from an unverified local copy. Only programs with
`central_lookup_result: not_found_on_remote_main` are routed to
`legacy-ibmi-program-analyzer`.

This skill supports these assembly modes:

- **`core_review_only` (default for SME-provided program-flow input)** — user
  provides an ordered or partial program flow/list; the analyzer produces
  `program-set-sme-core-review.md` by merging compact program-analysis
  artifacts. Do not produce `flow-<FLOW-SLUG>.md` in this mode.
- **`orchestrated`** — start from a trigger / entry program, discover the
  involved programs, run or route missing per-program analysis first, then
  assemble a full transaction flow from the generated compact artifacts. Use
  only when the user explicitly asks for full flow analysis.
- **`assemble_existing`** — user provides existing per-program analysis
  directories, and the flow analyzer assembles them into one flow, filling only
  missing artifacts when possible. Use only when the user explicitly asks for
  full flow analysis.

This skill does **not** re-analyze individual program semantics inline. Every
program in the program set must have program analysis evidence from remote
`main` or from a newly routed source scan. Core
artifacts are `program-analysis-summary.yaml`, `source-index.yaml`,
`routine-logic-details.yaml`, and `message-inventory.yaml`; optional sidecars
such as `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
`sql-inventory.yaml` are required only when program-analyzer triggers produced
them or when the flow claim needs file I/O, persisted mutation, or SQL
evidence. If required core artifacts or claim-specific optional artifacts are
missing, route only that program back to
`legacy-ibmi-program-analyzer` instead of concatenating full Markdown analyses
or restarting the whole flow.

This skill also supports two analysis intents:

- **`standalone_exploratory`** — default. Use for quick SME validation, partial
  flow scans, or assembling existing program artifacts before the chain is fully
  approved. Missing inventory approval, missing sidecars, or incomplete
  program approval become downstream-readiness gaps / TBDs, not immediate
  blockers, unless the trigger is ambiguous or the requested flow cannot be
  scoped to one business transaction.
- **`chain_ready`** — strict downstream mode. Requires approved inventory,
  approved program analyses, required compact sidecars, coverage gates, and
  trigger clarity before the flow can feed module/BRD/spec work.

This skill does **not** infer business rules. It captures the *structure*
of the transaction so that downstream `legacy-spec-writer` (via
`legacy-ibmi-module-analyzer`) can derive business rules with proper SME
involvement.

## Inputs

Accept:

- **Analysis intent** — `standalone_exploratory` by default, or `chain_ready`
  when the user explicitly asks for downstream-ready output.
- **SME-provided program flow** — an ordered or partial list of programs,
  entry/exit hints, menu/job/API context, or a rough sequence from the SME.
  When the SME provides a program flow for the current core-merge workflow,
  default `flow_scan_mode` to `core_review_only`, preserve the supplied order as
  SME navigation evidence, and output `program-set-sme-core-review.md`.
  Reconcile contradictions against upstream Call Evidence as notes/TBDs rather
  than silently rewriting the SME-provided list.
- **Central delivery artifact root / repo** — optional GitHub repo, local
  checkout, or `delivery_artifact_lookup_profile` for
  `legacy-modernization-delivery` or an equivalent delivery documents repo. The
  accepted artifact source of truth is GitHub remote `main`; local checkouts
  are caches only after freshness is verified against `origin/main`. The repo
  name, branch, module roots, and program folder patterns are configurable.
  Search the remote-current snapshot before asking to rescan source. For other
  teams, start from `templates/delivery-profile.yaml`.
- **Delivery workspace profile** — optional `delivery_workspace_profile`
  describing where new scan output is written in the delivery repo. The current
  default is `branch_mode: use_or_create_provided` with a provided
  `develop-<person>` branch such as `develop-leo`; create it from `origin/main`
  if it does not exist, but never write directly to `main`.
- **Flow definition** — the entry point of the chain, declared as one of
  seven trigger types (see `references/trigger-models.md`):
  - batch job (CL + SBMJOB or direct CALL)
  - interactive menu (`*MENU` option selection)
  - subfile dispatch (option codes 1/4/5/9/etc.)
  - F-key branch (DSPF function-key handling)
  - DB trigger (file trigger program)
  - scheduler (WRKJOBSCDE entry)
  - API / remote (remote PGM call, MQ message, HTTP, IFS drop)
- **Approved program analyses** for every program in the chain. Preferred
  core inputs are compact artifacts from `legacy-ibmi-program-analyzer`:
  `program-analysis-summary.yaml`, `source-index.yaml`,
  `routine-logic-details.yaml`, `message-inventory.yaml`, and the human review
  `program-analysis-<OBJ-ID>.md` / `program-analysis.md` when needed.
  Optional sidecars (`file-io-inventory.yaml`,
  `field-mutation-matrix.yaml`, `sql-inventory.yaml`) are required only when
  present/triggered by the program tier or when the flow needs native file I/O,
  persisted field mutation, or SQLRPGLE evidence.
- **Central lookup result per program** — record one row per requested or
  discovered program:
  `found_on_remote_main`, `not_found_on_remote_main`, or
  `remote_unavailable`. Do not scan every program in a provided flow just
  because one node is missing; scan only programs with
  `not_found_on_remote_main`. For `found_on_remote_main`, read the compact
  artifacts from the remote-main checkout/cache used for the lookup.
- **Approved inventory** with `relationships` populated for the involved objects
- Optional: SME notes on trigger context, BAU rhythm, known error scenarios
- Optional: DSPF / PRTF / MENU object definitions (for UI-aware flows)

Each upstream program-analysis should expose the program-chain readiness
sections and sidecars from `legacy-ibmi-program-analyzer` v0.2.5 or later:
`program-analysis-summary.yaml`, `source-index.yaml`,
`routine-logic-details.yaml`, `message-inventory.yaml`, plus triggered
optional sidecars (`file-io-inventory.yaml`, `field-mutation-matrix.yaml`,
`sql-inventory.yaml`),
`Program Call Map` with `Call Evidence`, `Logic Decomposition Ledger`,
`Routine Logic Details` with conditioned calculation blocks, routine-local
field lineage / carriers, and routine-local exception closure,
`Key File & Field Logic` with source identifiers plus business meanings,
`file-io-inventory.yaml`, `field-mutation-matrix.yaml`,
`sql-inventory.yaml`, `External Calls` with dynamic-call resolution status,
`Validation Logic`, `Exception Closure Ledger`, `Routine / Window Data Flow`,
`Redundancy Candidate Notes`, and `Open Items / Limitations`. If an older
approved program-analysis is used,
the flow must either route back for refresh or record a named SME waiver for
each missing v0.2.4 detail.

Stop and require clarification if:

- In `orchestrated` mode, the trigger / entry point is missing or ambiguous.
- In `assemble_existing` mode, the user-provided program set does not describe
  one flow or lacks an entry / ordering hint.
- In `chain_ready`, a required program in the chain lacks approved program
  analysis artifacts → route only the missing program to
  `legacy-ibmi-program-analyzer`. In `standalone_exploratory`, record
  `missing_program_artifact` and continue with a quick-validation draft when
  enough compact evidence exists.
- In `chain_ready`, a required call edge, data flow, or error path depends on
  an upstream program routine marked `blocked` or `indexed_only` with business
  state impact → route back to `legacy-ibmi-program-analyzer`. In
  `standalone_exploratory`, mark the affected flow claim unresolved and record
  a downstream-readiness gap.
- In `chain_ready`, inventory `sme_review.decision` is `blocked` or
  `relationships` are incomplete → route to `legacy-ibmi-inventory`. In
  `standalone_exploratory`, record inventory linkage gaps and keep the artifact
  `draft_exploratory`.
- Trigger model cannot be identified from the entry point → require SME
  clarification (do not guess)
- Flow appears to span multiple business modules → narrow scope; one flow
  = one business transaction

## Output Contract

For current SME-provided program-flow/core-merge requests, produce only:

- `program-set-sme-core-review.md`

Do not produce `flow-<FLOW-SLUG>.md` for this current workflow. Produce a full
flow artifact only when the user explicitly asks for full transaction-flow
analysis with trigger/context, edges, data flow, persistence, replay, and
capability seeds.

`program-set-sme-core-review.md` must include a **Core Completeness Ledger**
before the four core sections. The ledger lists every program from the
SME-provided flow, inventory relationship, discovered call evidence, or central
artifact lookup; its `central_lookup_result`; required compact artifacts;
missing core sections; and whether the next action is reuse, source scan, or
remote-access follow-up. No program may be omitted merely because its artifact
is missing.

`<FLOW-SLUG>` is uppercase, hyphen-separated, business-event named (e.g.,
`ONUS-AUTH`, `BATCH-RECON`, `CHARGEBACK-INTAKE`), and stable across the
analysis chain.

Use:

- `templates/flow.md` as the starting structure
- `templates/sme-core-review.md` as the starting structure for the compact
  multi-program SME review view
- `references/output-contract.md` for section definitions and required fields
- `references/trigger-models.md` for trigger-specific analysis guidance
- `references/data-flow-patterns.md` for cross-program data passing
- `references/error-propagation.md` for error-chain analysis

Follow:

- `../../docs/id-conventions.md` for stable IDs (`FLOW-*`, `NODE-*`, `EDGE-*`, `DATA-*`)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence strength tagging
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Examples:

- `examples/batch-job-positive/` — straightforward batch chain (`CL → RPG1 → RPG2 → SQLRPG`)
- `examples/menu-flow-positive/` — interactive flow with `*MENU` + DSPF + subfile dispatch
- `examples/incomplete-flow-negative/` — flow with a missing program-analysis (must route back)

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required**: `analysis_intent` set to `standalone_exploratory` by default
  or `chain_ready` when downstream-ready handoff is requested; `flow_scan_mode`
  set to `orchestrated` or `assemble_existing`; and enough program evidence to
  identify at least one entry node and one flow path.
- **Required for `chain_ready`**: approved `01_inventory/inventory.yaml` with
  `relationships` populated for the involved objects; approved program
  analysis evidence for every program in the chain; required core compact
  artifacts; triggered/claim-specific optional sidecars; and coverage gates
  satisfied.
- **Required for `orchestrated`**: flow definition (entry point + one of seven
  trigger models). The analyzer may discover the program set from inventory
  relationships and program call summaries, but any missing per-program
  artifact must be routed back to `legacy-ibmi-program-analyzer`.
- **Required for `assemble_existing`**: user-provided program analysis
  directories or artifact list, preferably including
  `program-analysis-summary.yaml`, `source-index.yaml`,
  `routine-logic-details.yaml`, and `message-inventory.yaml` for each program,
  plus optional `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
  `sql-inventory.yaml` when present/triggered or needed by a flow claim.
  Missing required artifacts should be filled for only the affected program
  when source is available; otherwise record `TBD: missing_program_artifact`.
- **Optional**: DSPF / PRTF / `*MENU` definitions (UI-aware flows);
  `WRKJOBSCDE` export (scheduler triggers); trigger-program registration
  (DB triggers); SME notes on BAU rhythm and known error scenarios.
- **Input readiness scoring**:
  - `0-5 blocked`: trigger model / entry unresolved, provided programs cannot
    be scoped to one business transaction, source authorization unresolved, or
    a `chain_ready` request is missing approved inventory / required program
    analyses.
  - `6 minimum_pass`: enough compact evidence exists to produce a
    `standalone_exploratory` quick-validation flow draft. Missing approvals,
    inventory linkage, or sidecars are recorded as downstream-readiness gaps.
  - `7-8 usable`: scheduler/job notes, menu/display/report definitions, and
    object dependencies are available for most chain edges.
  - `9-10 strong`: runtime logs, screen/report samples, SME notes on triggers
    and manual workarounds, and known exception cases are also supplied.
  - Missing runtime samples does not block structural flow analysis; it leaves
    runtime ordering and trigger confidence lower.
- **Readiness checks**: trigger model identified unambiguously for
  `orchestrated`; the flow represents one business transaction; every node
  has approved program-analysis evidence or an explicit
  `missing_program_artifact` TBD. For `chain_ready`, Inventory Completeness
  Gate must pass and no load-bearing program artifacts may be missing.
- **Stop conditions**: trigger / entry ambiguity; user-provided program set
  spans multiple business transactions; any required `chain_ready` node missing
  approved program-analysis evidence needed for flow claims and not repairable
  in the current run;
  a required call edge, data flow, or error path depends on an upstream
  routine marked `blocked` or `indexed_only` with business state impact;
  inventory `sme_review.decision` is `blocked` or relationships are
  incomplete; trigger model cannot be identified from the entry point;
  flow spans multiple business modules.

### Execution

- **Procedure**: see the Workflow section below (12 ordered steps).
- **Allowed inference**: assembling cross-program call edges from upstream
  `Call Evidence` and `External Calls` rows; classifying call types (CALL /
  CALLP / CALLPRC / SBMJOB / remote); deriving branch destinations from
  DSPF option tables; stitching cross-program field lineage only through
  upstream Key File & Field Logic, Routine / Window Data Flow, field
  mutation matrices, visible carrier fields, or SME-confirmed handoffs;
  reading scheduler / trigger / API configuration exports as tier-1 evidence.
- **Forbidden assumptions**: calls not visible in upstream `Call Evidence`
  or `External Calls` rows; dynamic calls whose upstream resolution is
  `unresolved` or `needs_sme_review` unless a named SME waiver is recorded;
  data flow whose parameter semantics require guessing; branch destinations
  not in DSPF DDS; trigger conditions without configuration export; scheduler
  frequency without `WRKJOBSCDE`; commit boundaries without code or SME
  confirmation; flow-level field lineage not backed by upstream lineage,
  source identifier + business meaning pairs, or a visible carrier; persisted
  file/field updates absent from upstream mutation matrices; exception
  propagation not backed by upstream Validation Logic / Exception Closure
  Ledger rows; business rules (these are seeds, never facts).
- **TBD handling**: missing program-analysis or sidecar →
  `TBD: missing_program_artifact` routing only the affected program to
  `legacy-ibmi-program-analyzer`; ambiguous trigger →
  `TBD: pending_sme_judgment`; unnamed business event → stop and request
  the name from SME (do not autogenerate from program names). In
  `standalone_exploratory`, unresolved artifacts become downstream-readiness
  gaps unless they prevent identifying the flow itself.
- **Coverage propagation**: consume each upstream program's compact artifacts
  first: `program-analysis-summary.yaml`, `source-index.yaml`,
  `routine-logic-details.yaml`, `message-inventory.yaml`,
  `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
  `sql-inventory.yaml`. Use full
  `program-analysis.md` / `program-analysis-<OBJ-ID>.md` only for targeted
  clarification, not as the primary flow aggregation input. The compact
  artifacts must expose Analysis Coverage & Scope, Routine Cards / routine
  summary, Routine Logic Details sidecar status, front-loaded Validation Logic
  references, Deep Read Windows, Call Evidence, Logic Decomposition Ledger,
  Key File & Field Logic, `file-io-inventory.yaml`,
  `field-mutation-matrix.yaml`, `sql-inventory.yaml`, Exception Closure
  Ledger, Routine / Window Data Flow, Redundancy Candidate Notes, and Open
  Items / Limitations before using program-level evidence in a flow. If
  the requested flow relies on a
  routine that was only `indexed_only` and that routine changes state,
  performs external handoff, handles commit/rollback, controls error
  outcome, supplies critical field lineage, or mutates persisted fields,
  flow analysis is blocked until the routine is `deep_read` or a named
  SME waiver is recorded in review metadata.

### Output

- **Default SME program-flow artifact**: `program-set-sme-core-review.md`.
  This artifact contains the Sources table, Core Completeness Ledger,
  Calculation Logic, Validation Logic, Exception Handling, and Message
  Inventory, aggregated from the participating program analyses.
- **Full transaction-flow artifact**: `flow-<FLOW-SLUG>.md`, only when the user
  explicitly asks for full flow analysis.
- **Required sections**: front-loaded Calculation Logic, Validation Logic,
  Exception Handling, Message Inventory, metadata, trigger model & entry point,
  transaction call map, nodes, edges, common dependencies, cross-program data
  flow, flow replay path, cross-program field lineage, flow persistence matrix,
  branch points, UI surfaces (or `N/A — non-interactive`), error propagation &
  commit boundaries, exception propagation chain, capability seeds, SME review
  checklist.
- **Required IDs**: mints `FLOW-*`, `NODE-*`, `EDGE-*`, `DATA-*`,
  `REPLAY-*`, `LINEAGE-*`, `PERSIST-*`, `EXCHAIN-*`, `SEED-*`,
  `TBD-*`; reuses `OBJ-*`, `EV-*`, and program-level `BEH-*` from
  upstream. Flow analysis does not mint `BR-*`; branch points are
  represented by `NODE-*` / `EDGE-*` entries and capability questions by
  `SEED-*`.
- **Handoff status**: `status: draft_exploratory` for standalone quick
  validation; `status: draft` → `needs_sme_review` → `approved` or
  `approved_with_non_blocking_tbd` for chain-ready flow work.
  `blocked_pending_source` and `blocked_pending_sme` halt
  module-analyzer. `draft_exploratory` is not eligible for module/BRD/spec
  handoff until rerun or promoted as `chain_ready`.

### Validation

- **Mechanical**: every edge traces to evidence type 1, 2, or 3 (source
  statement, config export, or integration contract); every data exchange
  traces to a source line; every UI surface traces to a DSPF/PRTF/`*MENU`
  in inventory; every trigger has evidence type 2 plus SME confirmation
  of business meaning; every replay step maps to `NODE-*`, `EDGE-*`,
  `DATA-*`, `PERSIST-*`, or `EXCHAIN-*`; every field lineage is backed
  by upstream field lineage or visible carrier fields; every persistence
  row is backed by upstream `field-mutation-matrix.yaml` and, for SQLRPGLE,
  `sql-inventory.yaml`; every node carries
  upstream coverage state and any blocking coverage gaps; all required
  sections populated.
- **AI semantic**: edges match upstream program-analyses (no invented
  calls); branch destinations match DSPF option tables; error
  propagation matches each node's program-analysis Exception Closure
  Ledger; commit boundaries are evidenced, not assumed; flow evidence is
  not taken from
  `indexed_only` or `blocked` routines when those routines have business
  state impact unless a named SME waiver is recorded; capability seeds
  are *questions*, not rule claims.
- **SME / human approval**: SME confirms trigger model, business event
  name, node/edge correctness, branch points, UI surfaces (interactive
  flows), error propagation realism, commit boundaries, and that seeds
  are reasonable questions. Required when a cross-program rule emerges
  or when the flow touches money, inventory, compliance, or customer
  status.
- **Blocking conditions**: trigger model unresolved; business event name
  unnamed by SME; ambiguous module boundary. For `chain_ready`, also block when
  any node lacks approved program-analysis evidence, any edge has no evidence,
  required flow evidence depends on `blocked` coverage or `indexed_only`
  state-impacting routines without a named SME waiver, or SME absence conflicts
  with the flow's risk class. For `standalone_exploratory`, these become
  downstream-readiness gaps unless they prevent identifying the flow itself.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with
status `pass`, `pass_with_warnings`, or `blocked` when reporting upward
to the orchestrator.

## Workflow

1. **Select Analysis Intent & Flow Scan Mode**
   - Default `analysis_intent` to `standalone_exploratory` unless the user asks
     for approved/downstream-ready/chain-ready output.
   - Use `analysis_intent: chain_ready` only when the flow must feed module,
     BRD, spec, or formal downstream handoff.
   - If the SME provides a program flow/list and asks for core logic merge,
     default to `flow_scan_mode: core_review_only`, normalize the supplied
     program list/order, and mark it as SME navigation evidence. Do not produce
     `flow-<FLOW-SLUG>.md` unless the user explicitly asks for full transaction
     flow analysis.
   - Load the team/project delivery profile when supplied. If no team profile is
     supplied, use `templates/delivery-profile.yaml` as the editable starting
     shape. Keep the lookup profile and workspace profile separate: lookup reads
     remote `main`; output writes to the provided delivery working branch.
   - Run **central artifact reuse** before routing any program to source scan:
     resolve the remote-current snapshot using Git method 2:
     `git ls-remote` followed by a temporary shallow clone / sparse checkout
     of `main`, or an already-fresh local cache verified against `origin/main`.
     Do not use GitHub API tooling, a stale local checkout, or a feature branch
     to conclude that a program artifact is absent.
   - Use the profile's `program_folder_patterns` to find each program. The
     current lending-card default supports exact `modules/*/{PROGRAM}` folder
     matching and preserves leading `@`, so `@CU118` and `CU118` are distinct
     programs. Other departments can override the repo name, branch,
     `module_roots`, folder patterns, artifact filenames, and alias rules.
   - Search remote-current central artifacts for each program named by the SME,
     discovered from the entry program, or present in inventory relationships.
     Match by exact program/member name first, then `OBJ-*`, module/CAP-ID,
     source library/member, and source ref when available.
   - Record `central_lookup_result` for every program:
     `found_on_remote_main`, `not_found_on_remote_main`, or
     `remote_unavailable`.
   - Do not rescan programs with `found_on_remote_main`; tell the user they
     have already been scanned, then read their compact artifacts from the
     remote-main sparse checkout or fresh cache and use those rows in
     `program-set-sme-core-review.md`. Scan only programs with
     `not_found_on_remote_main`. If any lookup is `remote_unavailable`, ask for
     access/context instead of assuming missing.
   - When new source scan output is needed, write it to the delivery repo
     working branch named by the user/profile, normally `develop-<person>`. If
     that branch does not exist, create it from `origin/main`; if it exists,
     update it before writing. This working branch is a draft workspace only and
     must not be used as the approved reuse lookup source.
   - Write newly scanned program artifacts under
     `delivery_workspace_profile.program_tier_roots` by size tier. Write
     `program-set-sme-core-review.md` under
     `delivery_workspace_profile.program_set_review_parent/{REVIEW_SLUG}/`.
   - Use `flow_scan_mode: orchestrated` when the user explicitly provides a trigger /
     entry program and wants the skill to discover, index, and assemble the
     whole flow.
   - Use `flow_scan_mode: assemble_existing` when the user explicitly provides several
     existing program analysis directories and asks to combine them into one
     flow.
   - In all modes, aggregation must prefer compact artifacts:
     `program-analysis-summary.yaml`, `source-index.yaml`,
     `routine-logic-details.yaml`, `message-inventory.yaml`,
     `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
     `sql-inventory.yaml`.
   - Do not concatenate full `program-analysis.md` / `program-analysis-*.md`
     files across programs. Open full Markdown only for targeted human-readable
     clarification when compact artifacts are insufficient.
   - If the user asks to merge multiple program-analysis results or provides a
     SME program flow for core SME review, generate
     `program-set-sme-core-review.md` from `templates/sme-core-review.md`.
     Include the Source table and Core Completeness Ledger, then only
     Calculation Logic, Validation Logic, Exception Handling, and Message
     Inventory. Do not include Nodes, Edges, Replay, Persistence, Lineage, UI
     Surfaces, Capability Seeds, or SME Checklist in that compact core-review
     artifact.
   - In `standalone_exploratory`, continue with warning rows when approvals,
     inventory linkage, or sidecars are missing; in `chain_ready`, enforce the
     blocking gates.

2. **Identify Trigger Model & Entry Point**
   - Determine which of the seven trigger models applies (see
     `references/trigger-models.md`). If unsure, ask the SME — do not guess.
     In `assemble_existing` mode, accept the user's stated entry/order hint; if
     it is missing or contradictory, stop for SME clarification.
   - Document the trigger object:
     - batch job → CL program + direct CALL from another program or operator
     - menu → `*MENU` object name + option number
     - subfile dispatch → DSPF subfile + option-code table
     - F-key → DSPF + function-key handler
     - DB trigger → file name + trigger program + event (insert/update/delete)
     - scheduler → WRKJOBSCDE entry + frequency (may submit a batch job via SBMJOB)
     - API / remote → remote-call mechanism + parameter contract
   - **Note:** Scheduler-submitted batch jobs form a single flow: the scheduler
     entry is the primary trigger, SBMJOB is the submission mechanism, and the
     CL/RPG program(s) are the nodes. This is one trigger model, not two.
   - Assign `FLOW-<SLUG>-<NNN>` ID.
   - Capture the **business event name** the SME uses for this flow
     (e.g., "Customer authorization request", not "RPG1 call").

3. **Enumerate Nodes (Programs in the Chain)**
   - List every program the flow touches, in call order.
   - For each node:
     - assign `NODE-<SLUG>-<NNN>` (sequence-numbered)
     - reference the program's `OBJ-*` (from inventory) and approved
       program-analysis artifact set
     - record artifact availability:
       `program-analysis-summary.yaml`, `source-index.yaml`,
       `routine-logic-details.yaml`, `message-inventory.yaml`,
       `file-io-inventory.yaml`, `field-mutation-matrix.yaml`,
       `sql-inventory.yaml`, and optional human-readable
       `program-analysis-<OBJ-ID>.md`
     - record the program's role in the flow (entry / orchestrator /
       worker / data-access / reporter / exit)
     - carry forward the program's Analysis Coverage & Scope, Routine
       Cards, and Deep Read Windows; record node coverage status as
       `deep_read`, `indexed_only`, or `blocked` plus flow readiness
       (`approved`, `warning`, or `blocked`)
     - record blocking coverage gaps when a required call edge, data
       exchange, branch, error path, or commit boundary depends on a
       routine that is `blocked` or is `indexed_only` with business state
       impact
   - If a node has no approved program-analysis evidence, create
     `TBD-<SLUG>-<NNN>: missing_program_artifact` routing only that program
     back to `legacy-ibmi-program-analyzer`. In `chain_ready`, stop; in
     `standalone_exploratory`, continue only with claims supported by available
     compact evidence.
   - If a node has an approved human-readable analysis but lacks compact
     sidecars, fill only the missing sidecars when local source is available;
     otherwise create `TBD-<SLUG>-<NNN>: missing_program_artifact` and avoid
     using that program for flow claims that require the missing sidecar.
   - If a node's required state-impacting routine is only `indexed_only`,
     stop in `chain_ready` until `legacy-ibmi-program-analyzer` deep-reads it
     or a named SME waiver is recorded in evidence/review/sign-off metadata. In
     `standalone_exploratory`, mark the affected flow claim unresolved and keep
     it out of downstream-ready conclusions.

4. **Trace Edges (Calls Between Nodes)**
   - For every call between two nodes, document an edge:
     - `EDGE-<SLUG>-<NNN>: NODE-A → NODE-B`
     - Call type (CALL, CALLP, CALLPRC, EXSR-not-applicable-cross-program,
       SBMJOB, remote-call)
     - Call site (source program + line number) — from the caller's
       `program-analysis`
     - `Via` routine/procedure — the internal node from the caller's
       Program Call Map where the edge exits the program, when visible
     - Call condition (always / conditional / loop / error path)
   - Build the **Transaction Call Map** (see
     `references/output-contract.md` for format). The map shows
     cross-program and cross-boundary structure; detailed call conditions
     remain in the edge table.

5. **Classify Common Dependencies**
   - If multiple nodes call the same common program, service program, API,
     data queue, message queue, or wrapper, keep every inbound call in the
     edge table and summarize the target in Common Dependencies.
   - Keep common nodes expanded as formal flow nodes when they write
     business files, change customer/account/inventory/money state,
     decide approve/decline outcomes, control commit/rollback, or call an
     external business system.
   - Fold common nodes in the visual map only when they are technical
     utilities such as logging, message formatting, date/time,
     delay/wait, or wrapper code. Folding is visual only; evidence and
     edge rows remain complete.
   - Do not infer a Java service boundary from shared usage alone. That is
     a modernization decision for module/spec stages with SME review.

6. **Cross-Program Data Flow**
   - For each edge, document what data passes (see
     `references/data-flow-patterns.md`):
     - parameters passed in the CALL
     - shared data area (`*DTAARA`) updates / reads
     - data queue (`*DTAQ`) messages
     - shared file writes/reads (program A writes, program B reads)
     - temporary work files / spool / IFS files
     - signal flags (return codes, indicators, error fields)
   - For each `DATA-*`, capture carrier, producer, consumer, mechanism,
     payload/key fields, direction and timing, state impact, and
     evidence. Preserve critical fields as `FIELD_NAME` (business meaning)
     or `VARIABLE_NAME` (business meaning) [direction] whenever the upstream
     program-analysis resolved both identity and meaning. A carrier can be an
     `EDGE-*`, PF/LF, data area, data
     queue, message queue, spool, IFS file, DSPF field set, or manual
     handoff.
   - Track object / record / critical-field granularity. Critical fields
     include money, account/customer/card/inventory identifiers,
     approval/decline/status/posting flags, return/error codes, audit
     IDs, and external payload fields. Do not trace every temporary work
     variable.
   - Add short critical trails for business-important records or
     messages, such as `request -> DTAQ -> program -> log PF -> batch
     posting`.
   - Assign `DATA-<SLUG>-<NNN>` for each distinct data exchange.
   - Tag evidence; cross-reference to source line numbers via EV-\*.

7. **Build Flow Replay Path, Field Lineage & Persistence Matrix**
   - Build a **Flow Replay Path** from trigger to terminal outcome:
     trigger, entry parameters, node execution, data handoff, key
     decisions, persisted mutations, commit/rollback/output, and final
     response or operator-visible state.
   - Each replay step must reference existing `NODE-*`, `EDGE-*`,
     `DATA-*`, `PERSIST-*`, `EXCHAIN-*`, or `UI-*` rows. Do not invent
     a replay step that is not supported by an upstream program-analysis
     or flow evidence.
   - Build **Cross-Program Field Lineage** for critical fields that
     cross program boundaries. Stitch program-local lineages through
     CALL parameters, shared files, data areas, queues, screens, IFS,
     spool, or SME-confirmed manual handoffs. Do not collapse a resolved
     source identifier and business meaning into a plain field label.
     For program-analyzer v0.2.5 inputs, prefer Routine Logic Details'
     conditioned calculation blocks and routine-local field lineage / carrier
     rows when they provide the guard-scoped source carrier, intermediate
     variable, output/persisted carrier, or lineage/mutation reference for a
     cross-program value.
   - Build the **Flow Persistence Matrix** by aggregating each
     program-analysis `file-io-inventory.yaml`,
     `field-mutation-matrix.yaml`, and `sql-inventory.yaml` summary into
     transaction-level outcomes:
     - node and routine that performs the mutation
     - file and field persisted, updated, deleted, or skipped
     - upstream field / parameter / carrier that drives it
     - downstream readers or consumers
     - commit / rollback / retry impact
     - evidence and TBDs for missing DDS, mutation source, SQL host-variable
       mapping, or rollback
       behavior
   - For read-only flows, explicitly mark the persistence matrix
     `N/A — read-only flow` and cite the upstream analyses proving no
     persisted mutations.

8. **Branch Points & Decision Nodes**
   - Identify points where the flow forks (subfile option, F-key,
     conditional CALL, trigger event).
   - For each branch point:
     - the deciding artifact (which field / which key / which condition)
     - the alternatives and which target node each leads to
     - whether unhandled options/keys exist (silently dropped vs. error)

9. **UI Surfaces (interactive flows only)**
   - List every DSPF / PRTF / MENU the user sees during the flow.
   - For each:
     - object name + `OBJ-*`
     - which node displays it
     - key fields shown / entered
     - F-keys handled
     - branch destination per F-key / option
   - For non-interactive flows (batch, trigger, scheduler, API), this
     section may be `N/A — non-interactive flow`.

10. **Error Propagation & Exception Chain**
   - For each node, summarise (from its `program-analysis` Error Handling
     section) what happens when each error condition occurs.
   - Trace propagation: does the error abort the whole flow, roll back to
     a checkpoint, log-and-continue, or branch to an error handler?
   - Build an **Exception Propagation Chain** from every upstream Error Code
     Inventory / Exception Closure Ledger row and Routine Logic Details'
     routine-local exception closure row that affects this flow. Each
     row must show source node, observed message ID / error code / return
     code, error type, output carrier, evidence status, propagation carrier,
     caller reaction, skipped/allowed downstream edges, persistence impact,
     operator/user visibility, and final flow outcome.
   - Identify **commit boundaries**: where does the flow consider work
     "committed" vs "rolled back"?
   - Identify **unhandled error windows**: nodes where an unhandled
     error would crash the entire flow without recovery (create TBD).
   - See `references/error-propagation.md`.

11. **Business Capability Seeds**
   - Extract `SEED-*` candidates (business rule seeds) that this flow
     plausibly enforces — **without inventing rules**.
   - Each seed is a *question* for SME review (e.g., "Does the rule
     'credit limit must not be exceeded' live in this flow?").
   - Phrase the candidate and SME question in business terms first:
     business event, business object, decision, outcome, control, or
     exception. Put program names, node IDs, field names, and file names in
     `Evidence Basis`, not in the candidate statement.
   - Evidence Basis should reference replay path, cross-program field
     lineage, persistence matrix, or exception chain rows when those
     rows are the real support for the seed.
   - The spec-writer skill will resolve seeds into approved rules; the
     flow analyzer never approves rules itself.
   - **Note:** flow analysis does not mint `BR-*` IDs. Branch points are
     represented by `NODE-*` / `EDGE-*` entries; capability seeds use
     `SEED-*` IDs.

12. **Prepare for SME Review**
   - Consolidate all TBDs grouped by blocking status (`pending_source` /
     `missing_program_artifact` / `pending_sme_judgment` / `non_blocking`).
   - **If `analysis_intent: standalone_exploratory`:**
     - Mark flow as `draft_exploratory`.
     - Complete the quick-validation artifact with all visible Calculation
       Logic, Validation Logic, Exception Handling, Message Inventory, Nodes,
       Edges, and gaps.
     - Record missing approvals, inventory linkage, sidecars, and indexed-only
       state-impacting routines as downstream-readiness gaps.
     - Do not route to module-analyzer until rerun/promoted as `chain_ready`.
   - **If `analysis_intent: chain_ready` and any blocking TBDs exist:**
     - Mark flow as `blocked_pending_source` (missing program-analysis, missing DSPF, etc.)
       or `blocked_pending_sme` (ambiguous trigger, unclear error handling, missing business context)
     - Do not complete the full required analysis; provide partial flow stub
     - Route to `legacy-ibmi-program-analyzer` or SME assignment process
     - Do not proceed to module-analyzer
   - **If `analysis_intent: chain_ready` and no blocking TBDs exist:**
     - Confirm every node's `program-analysis` is approved.
     - Generate the flow review checklist (see `templates/trigger-checklist.md`).
     - Mark flow as `draft` and route to SME.
   - **Gate:** the flow is ready for module-analyzer when:
     - all required sections populated
     - every node has an approved `program-analysis`
     - no blocking TBDs (or SME has explicitly waived them)
     - SME has signed off on the trigger model + business event name +
       capability seeds

## Workflow State Write-Back

At the end of a flow-analysis run, update
`<project-root>/workflow-state.yaml` per
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md).
Template: [`skills/legacy-modernization-orchestrator/references/state-writeback-snippet.md`](../legacy-modernization-orchestrator/references/state-writeback-snippet.md).

**Stage this skill produces:**

- `3d Flow Analysis Done` when every in-scope SME program set has a completed
  `program-set-sme-core-review.md`, or every explicitly requested full
  transaction flow has an approved `flow-*.md`
- `3c Flow Analysis In Progress` when one or more in-scope program sets or full
  flows are still draft, blocked, or missing

**Last artifact path pattern:**
`03_flows/<MODULE-SLUG>/program-set-sme-core-review.md` for the current SME
program-flow core-merge workflow, or
`03_flows/<MODULE-SLUG>/flow-<FLOW-SLUG>.md` for explicitly requested full flow
analysis.

**Writes per run:**

1. Overwrite `capabilities[<CAP-* from current_focus>]` with stage id, the
   path of the program-set core review or full flow you just saved,
   `last_skill: legacy-ibmi-flow-analyzer`, and blocking IDs (`tbds`,
   `sme_pending` for missing program artifacts or, for full flow analysis,
   trigger context / commit boundary questions).
2. Append one `history[]` entry with `note` naming the flow
   (e.g. `"analyzed flow-submit-order"`).
3. Overwrite `project.last_updated_at` / `project.last_updated_by`.

Never touch `current_focus`, other capabilities' entries, or past
`history[]` rows. A re-run on the same flow is allowed; a re-run that
would lower `stage_id` requires the orchestrator's Rollback Protocol.

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`. Every
edge in this flow must trace to **evidence** from authoritative sources
(see `references/output-contract.md` Evidence Taxonomy). Authoritative
evidence includes:

- **Source statements** (CALL, CALLP, SBMJOB in code)
- **Configuration exports** (WRKJOBSCDE, DSPF DDS, trigger registration)
- **Integration contracts** (MQ queue configs, API gateway definitions, DDM registrations)
- **SME confirmation** (documented procedures, business event naming, SLA agreement)

Shop documentation, prior architecture diagrams, and SME recollection are
navigation aids; they do not become evidence until **tier-1 authoritative
confirmation** exists. If SME claims a flow path the code does not contain,
both observations are recorded and a TBD blocks the flow until SME reconciles them.

**Do NOT invent:**

- **Calls** not visible in any program's `program-analysis` Call Evidence or
  External Calls sections
- **Data flow** that requires guessing parameter semantics (use only what
  source explicitly shows or SME confirms)
- **Cross-program field lineage** that cannot be stitched through
  upstream program-analysis lineage, source identifier + business meaning
  pairs, carrier fields, or SME-approved manual handoff
- **Persistence outcomes** not present in upstream `file-io-inventory.yaml`,
  `field-mutation-matrix.yaml`, `sql-inventory.yaml`, or SME-confirmed
  durable-output evidence
- **Exception chains** not present in upstream Validation Logic /
  Exception Closure Ledger rows, return-code checks, message IDs, or
  SME-confirmed operational recovery notes
- **Branch destinations** for F-keys / options not visible in DSPF DDS
- **Trigger conditions** for DB triggers without seeing trigger configuration export
- **Scheduler frequency or submitted command** without WRKJOBSCDE evidence
- **Commit boundaries** if neither code nor SME has confirmed them
- **Business capabilities or rules** — these are seeds (questions), not
  facts; spec-writer resolves them

**Instead:**

- If a node's `program-analysis` is missing → `TBD: pending_source` →
  route to `legacy-ibmi-program-analyzer`
- If configuration evidence is missing → `TBD: pending_source` → request
  WRKJOBSCDE export, DDS listing, or trigger configuration
- If a trigger model is ambiguous → `TBD: pending_sme_judgment`
- If the SME cannot name the business event → stop and request a name
  (do not autogenerate from program names)
- If error propagation is unclear → tag `needs_sme_review`; do not assume
  commit / rollback behavior

**Evidence minimum** (see Evidence Taxonomy):

- Every edge must trace to evidence type 1, 2, or 3 (source statement, config export, or integration contract)
- Every edge derived from a program call must cite upstream Call Evidence
  and carry its resolution status (`confirmed_from_code`, `observed_in_runtime`,
  `sme_confirmed`, `needs_sme_review`, or `unresolved`)
- Every data exchange must trace to source (parameter, data area, queue,
  file, screen field, message, IFS file, or SME note)
- Every UI surface must trace to a DSPF / PRTF / MENU object in inventory
- Every trigger must have evidence type 2 (config export) + evidence type 4 (SME confirmation of business meaning)

## SME Review Questions

When full transaction-flow analysis is explicitly requested, the generated
`flow-<FLOW-SLUG>.md` must include a review checklist covering:

- [ ] Trigger model correctly identified (batch / menu / subfile /
      F-key / trigger / scheduler / API)
- [ ] Business event name accurately reflects what the business calls this
      transaction
- [ ] All nodes (programs) in scope are correct; no missing programs and
      no extra programs
- [ ] All edges (calls) reflect actual production behavior
- [ ] Cross-program data flow captures carriers, producers, consumers,
      timing, state impacts, and no undocumented shared files or data areas
- [ ] Flow Replay Path can be followed from trigger to final outcome
- [ ] Cross-program field lineage preserves critical source, carrier,
      mutation, and output fields
- [ ] Flow Persistence Matrix lists transaction-level writes, updates,
      deletes, skipped mutations, and commit/rollback impacts
- [ ] Branch points correctly capture user-visible decision points
- [ ] UI surfaces match production screens (interactive flows only)
- [ ] Error propagation matches operational reality (what actually
      happens when this fails in prod)
- [ ] Exception Propagation Chain lists observed message IDs, error
      codes, return codes, skipped downstream edges, and final outcomes
- [ ] Commit boundaries are correct (one transaction vs. multiple)
- [ ] Capability seeds are reasonable questions backed by replay,
      lineage, persistence, or exception evidence; not invented rules

## Runtime Portability

Canonical source: `skills/legacy-ibmi-flow-analyzer/SKILL.md`

Runtime adapters are synced via `scripts/sync-skills.sh`:

- Codex: `.codex/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- Claude Code: `.claude/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- OpenCode: `.opencode/skills/legacy-ibmi-flow-analyzer/SKILL.md`
- Agents: `.agents/skills/legacy-ibmi-flow-analyzer/SKILL.md`

No runtime-specific assumptions are embedded in the canonical source.

## Version History

- v0.2.4 (2026-06-17): Central artifact reuse and SME program-flow intake
  - Added central artifact reuse before missing-program scans
  - Uses configurable `delivery_artifact_lookup_profile` values for delivery
    repo, branch, module roots, and program folder patterns instead of assuming
    every department uses the same repository layout; the lending-card default
    preserves leading `@` as part of program identity
  - Added per-program `central_lookup_result` routing:
    `found_on_remote_main`, `not_found_on_remote_main`, or
    `remote_unavailable`
  - Required compact SME core reviews to include a Core Completeness Ledger so
    every requested/discovered program is accounted for even when an artifact is
    missing
  - Scoped SME-provided program-flow intake to
    `program-set-sme-core-review.md` by default; full `flow-<FLOW-SLUG>.md`
    generation is reserved for explicit full transaction-flow analysis
  - Added `templates/delivery-profile.yaml` as the portable team configuration
    shape for central lookup, `develop-*` delivery working branches,
    tier-specific program artifact roots, and cross-tier program-set review
    output

- v0.2.3 (2026-06-06): Program-analysis dense evidence sidecar consumption
  alignment
  - Required flow aggregation to prefer `file-io-inventory.yaml`,
    `field-mutation-matrix.yaml`, and `sql-inventory.yaml` alongside the
    existing compact program artifacts
  - Updated node artifact availability, persistence matrix evidence, and
    missing-artifact routing for File I/O dense and SQLRPGLE programs

- v0.2.1 (2026-06-02): Program-analysis v0.2.1 consumption alignment
  - Required flow analysis to consume Call Evidence, File I/O Purpose,
    dynamic-call resolution status, Validation Logic, Routine / Window
    Data Flow, and Open Items / Limitations
  - Required flow field, lineage, persistence, and exception tables to
    preserve source identifiers with business meanings where upstream
    program-analysis resolved them

- v0.2.2 (2026-06-02): Program-analysis v0.2.4 routine-local evidence
  consumption alignment
  - Required flow analysis to consume Routine Logic Details, routine-local
    field lineage / carrier rows, and routine-local exception closure rows
    when building Cross-Program Field Lineage and Exception Propagation Chain
  - Updated older-program-analysis waiver language from v0.2.1 detail gaps to
    v0.2.4 detail gaps

- v0.2.0 (2026-06-01): Replayable program-chain hardening
  - Added Flow Replay Path, Cross-Program Field Lineage, Flow
    Persistence Matrix, and Exception Propagation Chain requirements
  - Required flow analysis to consume program-analyzer v0.2.0 ledgers
    where available
  - Tightened capability seeds so evidence basis can reference replay,
    lineage, persistence, and exception-chain rows

- v0.1.2 (2026-05-26): Business-readable seed hardening
  - Reframed capability seeds as business-language questions
  - Kept technical node, program, field, and object references in
    `Evidence Basis`

- v0.1.1 (2026-05-14): Field-pilot hardening
  - Added smoke test prompts and evidence taxonomy
  - Clarified trigger model rules: Scheduler + SBMJOB is one trigger (not composite)
  - Added blocked status values (blocked_pending_source, blocked_pending_sme) with routing rules
  - Standardized capability seed IDs on SEED-* and clarified that flow analysis does not mint BR-* IDs
  - Added evidence taxonomy: 4 types (source statement, IBM i config, integration contract, SME confirmation)
  - Updated anti-hallucination rules to allow config and contract evidence, not just source code
  - All 5 review blockers (FLOW-REV-001 to FLOW-REV-005) resolved
  - Ready for smoke test execution in Codex CLI, Claude Code, and OpenCode

- v0.1.0 (2026-05-14): Initial release
  - 9-step workflow
  - 7 trigger-model support (batch / menu / subfile / F-key / trigger /
    scheduler / API)
  - Cross-program data flow analysis
  - Error propagation and commit boundary detection
  - UI-surface mapping for interactive flows
  - Business capability seed extraction (no rule invention)
  - Feedback loop to `legacy-ibmi-program-analyzer` and
    `legacy-ibmi-inventory`
  - Examples: batch positive, menu positive, incomplete-flow negative
