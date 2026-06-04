# Module Analysis Model: Focused Evidence Views

This document defines the module-level analysis model used by Legacy Spec
Factory for IBM i / AS400 modernization.

The model is intentionally focused on the two module artifacts that are
consistently evidence-backed in field work:

- `03-program-flow.md` — program and flow replay coverage
- `04-data-flow.md` — data movement, lineage, persistence, and exception-state
  impact

`01-operation-flow.md` and `02-system-flow.md` are no longer default module
outputs. Field testing showed they frequently became weak summaries or
incorrect business/architecture narratives unless backed by strong SME,
operations, integration, or architecture evidence. Business and system context
is still valuable, but it belongs in `module-overview.md` as source-backed
context notes, BRD crosswalk evidence, or explicit TBDs.

## Default Artifacts

A module analysis produces:

```text
04_modules/<MODULE-SLUG>/
├── module-overview.md          ← summary, evidence-view index, readiness, BRD crosswalk
├── 03-program-flow.md          ← Program Flow: application/program view + replay coverage
├── 04-data-flow.md             ← Data Flow: data, lineage, persistence, exception impact
└── module-review-checklist.md  ← SME sign-off for the module package
```

The numbering for `03` and `04` is preserved to reduce disruption for existing
links and downstream references. The missing `01` and `02` slots are reserved
for non-default, explicitly requested, source-backed business/system views if a
future workflow needs them.

## Program Flow

**Question answered:** "What is the actual program-level call structure and
replay readiness across all transactions in this module?"

**Captures:**
- Inventory of flows in scope, one row per `flow-<FLOW-SLUG>.md`
- Per-flow summary: trigger model, entry program, exit program, runtime model
- Cross-flow dependencies: which flow writes data another flow reads
- Replay coverage from trigger to final response, durable persistence,
  rollback, skipped work, or manual outcome
- Key decision and exception paths, carrying `REPLAY-*`, `PERSIST-*`, and
  `EXCHAIN-*` evidence from flow analysis
- Shared sub-programs called from multiple flows
- Overall call topology of the module

**Primary source:** approved `flow-<FLOW-SLUG>.md` documents and approved child
`program-analysis-<OBJ-ID>.md` artifacts.

This view does not re-analyze individual programs; it references and
synthesizes approved flow/program evidence.

## Data Flow

**Question answered:** "How does data move through this module?"

**Captures:**
- Data objects in scope: PF, LF, DSPF, PRTF, `*DTAARA`, `*DTAQ`, `*MSGF`,
  copybooks, parameter data structures, queues, spool, IFS handoffs, and
  response payloads
- Data lifecycle per object: created, updated, read, sent/received, archived,
  purged
- Critical field lineage across programs and flows
- Module persistence matrix: writes, updates, deletes, skipped mutations,
  response payloads, queues, spool files, checkpoints, commit/rollback/retry
  effects
- Exception-aware data risks: how exception chains affect state and downstream
  consumers
- Coupling hotspots and cross-module data dependencies
- DB table relationships where evidenced

**Primary source:** flow `Cross-Program Field Lineage`, `Flow Persistence
Matrix`, and `Exception Propagation Chain` sections; program `Data Touch Map`,
`Object Dependencies`, `Key File & Field Logic`, `File I/O Purpose`, `Field
Mutation Matrix`, and `Validation Logic`; inventory/DDS evidence; data-model
dictionary output where triggered.

## Module Overview

`module-overview.md` is the place to collect:

- Module identity, scope, owner, evidence mode, and status
- Evidence view index for Program Flow and Data Flow
- Optional source-backed business operation / BAU notes
- Optional source-backed channel, system, interface, SLA, security, and
  architecture notes
- Top blocking TBDs
- Module Program-Chain Readiness
- Module Persistence & Critical Field Summary
- Module Exception & Recovery Summary
- Capability seeds for BRD/spec work
- BRD Functional Analysis Input Crosswalk
- BRD Source Eligibility Crosswalk
- Module review checklist and sign-off

Rows backed only by generated drafts, RAG candidates, unreviewed documents, or
missing evidence must remain `questions_only` or `needs_sme_review`; they do
not become BRD conclusions.

## Consistency Rules

- Every `REPLAY-*` path in Program Flow maps to a module event, persisted
  outcome, exception outcome, or named `TBD-*`.
- Every external or durable `PERSIST-*` output maps to a Data Flow object,
  output carrier, downstream consumer, or named `TBD-*`.
- Every module-critical `LINEAGE-*` and durable `PERSIST-*` claim appears in
  Data Flow.
- Every material `EXCHAIN-*` has module-level error/recovery crosswalk coverage
  or a named `TBD-*`.
- Every data object in Data Flow traces to at least one approved flow/program,
  dictionary row, inventory object, or named source gap.
- Any business operation or system-interface claim in the overview must cite
  named SME/source evidence or become a TBD.

## Granularity Rules

- **Capability within Module.** A module contains one or more business
  capabilities. `spec.yaml` is produced per capability; module analysis informs
  all capabilities under it.
- **Flow within Module.** A module contains multiple flows. A flow is the unit
  produced by `legacy-ibmi-flow-analyzer`.
- **Program within Flow.** A program participates in one or more flows.
- **Object within Program.** Objects are referenced by one or more programs.

```text
Module
├─ Capability   (CAP-* seeds; BRD/spec unit candidate)
├─ Flow         (business transaction; flow-*.md)
│   └─ Program  (program-analysis-*.md)
│       └─ Object Dependencies + File I/O Purpose + Field Mutation Matrix
├─ Replay / Lineage / Persistence / Exception evidence
└─ Source-backed SME/context notes
```

## Status Values

Each default evidence view and the overview use:

- `draft` — initial synthesis, ready for review
- `needs_sme_review` — has blocking TBDs or ambiguities
- `approved` — reviewer confirmed
- `approved_with_non_blocking_tbd` — approved with known non-blocking gaps
- `blocked_pending_source` — missing required source evidence
- `blocked_pending_sme` — missing required owner/scope/SME judgment
- `rejected` — reviewer found errors

The module is approved only when `module-overview.md`, `03-program-flow.md`,
`04-data-flow.md`, and `module-review-checklist.md` are approved or
`approved_with_non_blocking_tbd`, and no blocking BRD crosswalk gaps remain.

## Why Not Default Operation/System Views

Operation Flow and System Flow are useful only when the evidence is strong:
SME-reviewed operating procedures, BAU notes, integration specs, architecture
diagrams, runbooks, or confirmed interface contracts. Code alone cannot prove
business actors, BAU rhythm, SLAs, network boundaries, or business intent.

Default generation of those files created polished artifacts that looked
authoritative while often being speculative. The focused model keeps the
default package anchored to code-backed program/data evidence and moves weaker
business/system material into overview notes and BRD crosswalk TBDs.

## Relationship to Existing Documents

- `docs/id-conventions.md` — stable IDs used across module artifacts
- `docs/evidence-and-knowledge-taxonomy.md` — evidence tagging applies to every
  claim
- `docs/skill-review-gate.md` — module-analyzer review gate
- `docs/runtime-matrix.md` — module-analyzer runtime sync status
- `schemas/spec.schema.yaml` — `spec.yaml` references module/capability IDs
