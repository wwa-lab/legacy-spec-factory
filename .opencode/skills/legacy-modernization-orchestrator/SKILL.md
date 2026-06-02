---
name: legacy-modernization-orchestrator
description: "Entry-point router for the Legacy Spec Factory reverse chain. Use for natural-language guidance through IBM i / AS400 / RPGLE / CLLE / COBOL modernization, including document/spec/RAG/context intake, inventory, program and flow analysis, module analysis, legacy BRD discovery, post-BRD old-vs-new disposition, spec writing, and SDLC handoff. Routes users to the safest next skill and does not replace downstream extraction, synthesis, review, risk-assessment, or gap-analysis processes."
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Modernization Orchestrator

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Routes a legacy modernization request to the safest next Legacy Spec Factory skill and gate. |
| Input | User goal, available artifacts, source/evidence type, current stage, approval status, and constraints. |
| Output | Routing decision, next-step guidance, required inputs, stop conditions, and handoff target. |
| Core prompt strategy | Identify stage and target outcome first, enforce hard gates, minimize unnecessary steps, and yield to the downstream skill. |
| Upstream skill | None; this is the entry-point router. |
| Downstream consumer | Any Legacy Spec Factory skill, especially evidence intake, context intake, inventory, analysis, BRD, spec, and handoff skills. |
| Validation standard | Recommended route matches input readiness, does not skip evidence/SME gates, and clearly names blockers or next artifact. |
| Known risk | Performing downstream analysis inside the router instead of handing off once the correct skill is known. |
| Practical example | Given a Visio flow, RPGLE source, and a request for a migration spec, route first to document/evidence intake before inventory or spec writing. |

Routes legacy reverse-modernization work to the correct skill in the correct
order. The output is a routing decision and next-step execution guidance — not
an inventory, not a spec, not a review report, and not source code.

This skill is the **entry point** for users who are new to Legacy Spec
Factory, who do not know which skill to call next, or who want a guided path
through the chain.

For the full grouping of all 22 skills into 7 families (routing, module-first
context intake, Layer 1 extraction, Layer 2 synthesis, bridge/handoff,
governance, verification),
see [`docs/skill-families.md`](../../docs/skill-families.md). That document
also records which skill pairs were intentionally **not** merged and why.

## Reverse Chain Map

```
Module-First Entry (scattered docs / external RAG / four-view context)
   ↓ legacy-document-evidence-intake (only when source is raw Office/Visio/PDF/image and not yet normalized)
      - normalize Excel/Word/PPT/Visio/PDF/image → Markdown/CSV/PDF/PNG/SVG + manifests + evidence coordinates
00_context_packages/<MODULE-SLUG>/document-intake/<DOCSET-SLUG>/ (ready / ready_with_warnings before normalization)
   ↓ legacy-flow-context-normalizer
      - L3/L2: draft Mermaid-backed context views for SME review
      - L1: source-quality triage when no safe flow can be generated
00_context_packages/<MODULE-SLUG>/flow-normalization/ (draft or triage, SME/source review first)
   ↓ legacy-module-context-intake
00_context_packages/<MODULE-SLUG>/ (context only, not approved module analysis)
   ↓ CODE-BACKED ENRICHMENT CHECKPOINT for standard BRD/spec work
      - if source/object evidence exists or the target is a code-backed BRD,
        run inventory → program analysis → flow analysis before approving
        module/BRD outputs
   ↓ legacy-ibmi-module-analyzer

Raw Legacy Evidence (IBM i source, DDS, DB2, job log, spool, screen, SME notes)
   ↓ legacy-ibmi-evidence-intake
Evidence Manifest + Redaction Log + Redacted Evidence Bundle
   ↓ REDACTION GATE (docs/data-collection-and-redaction.md)
   ↓
[Layer 1 — IBM i Extraction]
   legacy-ibmi-inventory ───────────► inventory.yaml + object-map.md
        ↓ INVENTORY GATE
   legacy-ibmi-program-analyzer ────► program-analysis.md
        ↓
   legacy-ibmi-flow-analyzer ───────► flow.md
        ↓
   legacy-ibmi-module-analyzer ─────► 4-view module analysis
   ↓
[Layer 2 — Platform-Agnostic Synthesis]
   legacy-brd-writer ───────────────► legacy BRD Package for migration discovery
        ↓ BRD REVIEW GATE
        └─ post-BRD old-vs-new comparison / risk / gap-analysis decision
             ├─ No-gap / Gap1 / follow-new-system → stop in discovery
             └─ promoted legacy behavior / capability → legacy-spec-writer
   legacy-spec-writer ──────────────► spec.yaml + spec.md + traceability.md
        ↓ EVIDENCE APPROVAL / SME APPROVAL
   legacy-spec-reviewer ────────────► review-report.md (future/manual)
        ↓
   legacy-equivalence-test-generator ► golden-master tests (planned)
        ↓ FORWARD HANDOFF GATE (docs/forward-sdlc-contract.md)
Forward SDLC (wwa-lab/build-agent-skill: ibm-i-program-spec, code-generator, …)

Folded MVP capabilities: Program Call Map, CRUD matrix, DDS/screen schema extraction,
business-rule mining, and capability mapping are produced inside the program,
flow, module, and spec-writer artifacts rather than routed as separate active
skills.
```

Future Layer 1 families (`legacy-cobol-*`, `legacy-mainframe-*`) feed the same
Layer 2 chain unchanged.

## When to Use This Skill

Trigger on any of these signals:

- User asks "what should I do next?" with a legacy modernization artifact
- User asks which Legacy Spec Factory skill to use
- User shows up with raw source / a partial spec / SME notes and asks for guidance
- User asks whether a stage can be skipped
- User wants end-to-end orchestration across the reverse chain
- A skill rejects input and the user needs to know what to do instead

**Do NOT trigger** when:

- The correct downstream skill is already obvious and the input is sufficient
- The user has explicitly asked for one specific downstream task
- The user is in the middle of a downstream skill's workflow

In those cases, hand off directly to the downstream skill.

## Role

You are the workflow router for the Legacy Spec Factory reverse chain. Your
responsibility is to:

- identify the user's current stage from the artifact(s) they have
- identify the user's target outcome
- decide the safest next skill (implemented or planned)
- enforce the hard gates (evidence authorization, inventory completeness, BRD
  review, post-BRD disposition, evidence approval, forward handoff)
- recommend SME involvement at every approval point
- minimize unnecessary steps without allowing unsafe stage skipping
- yield to the downstream skill once routing is decided and input is sufficient

You do not replace any downstream skill. You route to it.

## Core Process

### Step 0 — Resolve Project and Read Workflow State

Every project lives under `docs/<project-name>/` (see
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md)).
A single repository may hold many projects, each with its own
`workflow-state.yaml` and artifact tree. This step picks WHICH project
this turn targets and reads its state file.

#### 0.a — Enumerate existing projects

Scan `docs/*/workflow-state.yaml`. Build a list of `(project-name,
project.root, project.last_updated_at, current_focus.capability_id)`
tuples. This list is the input to the project picker below.

#### 0.b — Resolve the project for this turn

Apply in order, first match wins:

| Signal | Action |
| --- | --- |
| User message names a project (`XXX260004-demo`, `docs/XXX260004-demo`, path under `docs/<name>/...`) | Use the named project. If it doesn't exist, plan to create at Step 8. |
| Exactly one project exists in `docs/` | Default to it. Tell the user (e.g. "Resuming `docs/XXX260004-demo/`"). |
| Multiple projects exist and user did not name one | Present a project picker (list each project + its current focus + last-updated date). ASK rather than guess. |
| No projects exist | Prompt: "What is the project name? Use PPCR convention `<PPCR-Number>-<short-description>` (e.g. `XXX260004-demo`). Allowed characters: A-Z, a-z, 0-9, hyphen. Must start alphanumeric." |

Validation: project name MUST match `^[A-Za-z0-9][A-Za-z0-9-]*$`.

**Be forgiving on input — never reject silently.** When the user types
something close-but-not-conforming (`"XXX260004 demo"`, `"XXX260004.demo"`,
`"xxx260004_demo"`, `"XXX260004 / demo"`), do NOT just say "rejected,
re-enter". Instead:

1. Auto-normalize:
   - replace runs of whitespace / `.` / `_` / `/` / `\` with a single `-`
   - strip leading and trailing hyphens
   - strip any character that is not `[A-Za-z0-9-]`
   - preserve case (PPCR numbers are typically uppercase; descriptions
     typically lowercase — do NOT force-case-fold)
2. Show the normalized result back and ASK: "I'll use `<normalized>` as the
   project name (path: `docs/<normalized>/`). Confirm? Or give a different
   name."
3. Only after the user confirms, treat the name as resolved.
4. If the normalized result is empty (input was all punctuation) or starts
   with a hyphen after stripping, ask the user to provide a new name.

Examples:

| User typed | Auto-normalized | Asked back |
| --- | --- | --- |
| `XXX260004 demo` | `XXX260004-demo` | confirm? |
| `XXX260004.demo` | `XXX260004-demo` | confirm? |
| `xxx260004_demo` | `xxx260004-demo` | confirm? (note lowercase preserved) |
| `XXX260004 / demo (v2)` | `XXX260004-demo-v2` | confirm? |
| `   ---` | (empty after strip) | ask for a real name |

The output of Step 0.b is `project.name` and `project.root = docs/<name>/`.
All subsequent path interpretation in Steps 0.5–8 uses this root.

#### 0.c — Read this project's state file

Open `<repo-root>/<project.root>/workflow-state.yaml`. Three cases:

| State of the file | What to do |
| --- | --- |
| **Exists and current** | Seed `current_focus`, `capabilities[]`, `open_gates` from the file. Skip stage-rederivation when the file already names the user's current capability. |
| **Exists but stale or empty** | Use it as a hint, then re-verify stage by reading the cited artifacts (under `project.root`). If artifacts disagree, trust the artifacts and plan to rewrite at Step 8 with `history[]` note: `"state corrected from artifact"`. |
| **Missing** | Plan to create at Step 8 using [`templates/workflow-state.yaml`](templates/workflow-state.yaml) with `project.name` and `project.root` filled in from Step 0.b. Do NOT pre-create empty artifact directories — those are created on demand by downstream skills. |

Read-only verification rules:

- All artifact paths in this state file are **relative to `project.root`**
  — not the repo root. Resolve before checking existence.
- Trust artifacts over the state file when they disagree.
- Never write to the state file in this step.
- Do not block the user if the file is missing — proceed to Steps 0.5–6
  and offer to create it in Step 8.

### Step 0.5 — Determine Focus

Before classifying stage, decide **what the user is working on this turn**.
Multi-capability projects, mid-chain entry, repo handover, and rollback all
hinge on this step. Without it, every routing decision silently assumes
"continue the most recent thing" — which breaks for everyone except the
linear first-time user.

Use [`references/focus-selection.md`](references/focus-selection.md). Its
decision tree resolves the user's natural-language input plus
`workflow-state.yaml` into one of five outcomes:

| Outcome | Meaning |
| --- | --- |
| `continued` | User implicitly continues `state.current_focus` (no `CAP-*` / `MODULE-*` named) |
| `switched` | User named a different capability / module that already exists in `capabilities[]` |
| `new` | User starts a brand-new capability / module not yet tracked |
| `scan` | No `current_focus` set; enumerate existing artifacts and present a picker |
| `rollback` | User wants to redo / revert to an earlier stage within current focus |

Signals to detect from the user's natural-language input:

- Literal `CAP-*` / `MODULE-*` IDs
- File paths matching the directory layout (`05_specs/CAP-XXX/...`,
  `04_modules/<MODULE>/...`, etc.) — extract the capability or module
- Verbs: `继续` / `next` / `下一步` / `接着` → `continued`
- Verbs: `重做` / `redo` / `回到` / `rollback` / `revert` / `回滚` →
  `rollback`
- Verbs: `新的` / `new` / `切换` / `switch` → `new` (if target not in
  `capabilities[]`) or `switched` (if target exists)

Rules:

- Never invent a `CAP-*` or `MODULE-*` ID that has no evidence in artifacts,
  state, or user message.
- When the resolution is ambiguous (multiple capabilities match the user's
  phrasing), ASK rather than pick.
- When `current_focus` is unset and artifacts exist, run **scan mode** —
  enumerate `01_inventory/`, `04_modules/`, `05_specs/` (full source list
  in `references/focus-selection.md`) and present a picker before routing.
- When the outcome is `rollback`, apply the Rollback Protocol in
  `references/focus-selection.md`: target must be strictly earlier than
  current `stage_id` AND must have been previously reached. Never silently
  overwrite a later `stage_id`.
- When the outcome is `switched`, apply the Switch Protocol: do not mutate
  the old `capabilities[]` entry; just rewrite `current_focus` and append
  one `history[]` line.

The output of this step is a resolved tuple `(capability_id, module_slug,
focus_intent)` that scopes everything Steps 1–8 do this turn. Record the
chosen outcome — it appears on the Quick Card's `FOCUS` line at the end.

### Step 1 — Identify Current Stage

Classify what the user currently has. See
[references/stage-identification.md](references/stage-identification.md) for
the full table. Common cases:

| Current Input | Stage |
| --- | --- |
| Scattered authorized Visio / Word / Excel / PDF / PowerPoint / Function Spec / Technical Design / Program Spec / File Spec / SME-note docs without SME-reviewed flows | Flow Context Normalization |
| `flow-normalization/flow-context-index.yaml` with `triage_needs_source_enrichment` | Flow Context Normalization — source enrichment needed |
| `flow-normalization/flow-context-index.yaml` with `draft_needs_sme_review` | Flow Context Normalization — SME review needed |
| Raw legacy source / job log / spool that has not been redacted | Evidence Intake (pre-redaction) |
| Redacted evidence bundle with sensitivity recorded | Evidence Ready |
| `inventory.yaml` with `sme_review.decision: blocked` | Inventory Blocked |
| `inventory.yaml` with `decision: approved` or `approved_with_non_blocking_tbd` | Inventory Done |
| `program-analysis.md` for one or more programs | Program Analysis Done |
| `runtime-evidence.jsonl` plus samples | Runtime Evidence Mined |
| `business-rules.md` (draft) | Business Rules Drafted |
| `capability-map.md` | Capabilities Mapped |
| `05_brds/<CAPABILITY-SLUG>/brd.md` with `status: draft` or `in_review` | BRD Discovery In Review |
| `05_brds/<CAPABILITY-SLUG>/brd.md` with `status: approved` | BRD Discovery Approved |
| Approved BRD plus pending old-vs-new comparison, risk assessment, gap analysis, or promotion decision | Post-BRD Comparison / Disposition Open |
| `spec.yaml` with `status: draft` | Spec Drafted |
| `spec.yaml` with `status: in_review` plus `review-report.md` | Spec Reviewed |
| `spec.yaml` with `status: approved` | Spec Approved |
| Approved spec + golden-master test pack | Equivalence Pack Ready |

If the stage is ambiguous, identify the most likely stage conservatively and
note what makes it unclear. Do not invent maturity.

### Step 2 — Identify Desired Outcome

Determine what the user is trying to reach:

| User Goal | Desired Outcome |
| --- | --- |
| Get started safely with a legacy bundle | Run inventory after redaction |
| Understand one program's logic | Program Analysis |
| Map calls / file usage / DDS / runtime | Static Analysis (call-graph, CRUD, DDS, runtime evidence) |
| Extract business rules from analysis | Business Rule Mining |
| Group rules into business capabilities | Capability Mapping |
| Produce a business-facing BRD for review | BRD Discovery Writing |
| Classify old-vs-new differences | Post-BRD Comparison / Disposition |
| Produce a reviewable `spec.yaml` / `spec.md` after BRD review and promotion decision | Spec Writing |
| Validate a draft spec | Spec Review |
| Build old-vs-new comparison tests | Equivalence Test Generation |
| Hand off to forward Java/cloud SDLC after approved spec | Forward SDLC Handoff |

If the user asks for "end-to-end", route to the next missing stage rather than
collapsing the entire chain into one unsafe jump.

### Step 3 — Apply Safe Routing Rules

Use the decision table to pick the next skill. See
[references/routing-decision-table.md](references/routing-decision-table.md)
for the full table. Common routes:

| Current Stage | Desired Outcome | Route To | Skill Status |
| --- | --- | --- | --- |
| Raw Office/Visio/PDF/image docs, no `document-intake` manifest yet (authorized, sensitivity known) | Normalize formats + evidence coordinates | `legacy-document-evidence-intake` | Implemented v0.1.0 |
| Scattered docs, specs, or sparse module notes, no reviewed four-view context | Normalize or triage context | `legacy-flow-context-normalizer` | Implemented v0.1.10 |
| Evidence Intake (unredacted or unregistered) | Any downstream | `legacy-ibmi-evidence-intake` | Implemented v0.1.0 |
| Evidence Ready (IBM i source) | Start reverse engineering | `legacy-ibmi-inventory` | Implemented |
| Evidence Ready (COBOL source) | Start reverse engineering | `legacy-cobol-inventory` | Future — manual workflow |
| Inventory Blocked | Any downstream | **STOP — Inventory Completeness Gate** | N/A (doc) |
| Inventory Done | Understand one program | `legacy-ibmi-program-analyzer` | **Implemented v0.2.4** |
| Inventory Done | Map calls / CRUD / DSPF | (subsumed by program / flow / module analyses) | n/a |
| Program Analysis Done | Analyze a complete call chain | `legacy-ibmi-flow-analyzer` | **Implemented v0.2.2** |
| Flow Analysis Done | Synthesize module (4 views) | `legacy-ibmi-module-analyzer` | **Implemented v0.2.2** |
| Module context ready but no `01_inventory/object-map.md`, `02_programs/`, or `03_flows/` for a requested code-backed BRD | Build code evidence backbone | `legacy-ibmi-inventory` first, then program / flow analysis | **Implemented** |
| Module Analysis Done, no approved BRD Package | Produce legacy BRD for SME discovery review | `legacy-brd-writer` | **Implemented v0.1.7** |
| Approved BRD Package, post-BRD No-gap / Gap1 / follow-new-system decision | Discovery complete for that item; new system is source of truth | Stop / record disposition outside BRD | Human gate |
| Approved BRD Package, post-BRD risk assessment or gap analysis open | Resolve disposition before spec-writing | Risk / gap-analysis process, then route back | Human / external gate |
| Approved BRD Package plus explicit post-BRD promotion / disposition decision | Produce capability spec | `legacy-spec-writer` | **Implemented v0.1.6** |
| Spec Drafted | Validate spec | `legacy-spec-reviewer` | Future (deferred from MVP) |
| Spec Reviewed (no blocking findings) | Promote to approved | SME approval — not a skill | Human gate |
| Spec Approved | Equivalence tests | `legacy-equivalence-test-generator` | Future (deferred from MVP) |
| Equivalence Pack Ready | Forward SDLC handoff | **Forward Handoff Gate** then cross to `wwa-lab/build-agent-skill` | N/A (gate + external chain) |

For any route where the target skill is `Planned` or `Future`, see
[references/manual-fallback.md](references/manual-fallback.md) — the
orchestrator must still tell the user what to do manually until the skill
exists.

### Step 4 — Enforce Stage-Skipping Rules

A stage may be skipped only when the current artifact already contains the
substance the skipped layer would have contributed.

#### Safe Skip Examples

- Document / RAG context → Module Analyzer
  only as a **context-only** synthesis path when the package is
  `ready_for_module_analysis` or explicitly risk-accepted
  `ready_with_warnings`; the result must preserve missing source coverage as
  TBDs and must not claim code-backed approval.
- Program Analysis Done → Business Rule Miner
  if runtime evidence is not required for the rule (rule is `confirmed_from_code`)

#### Unsafe Skip Examples

- Evidence Ready → Spec Writer (skipping inventory + analysis)
- Inventory Done → Spec Writer (skipping rule mining)
- Inventory Blocked → anywhere downstream
- Module context / document-normalization output → approved BRD while
  `01_inventory/object-map.md`, required `program-analysis-<OBJ-ID>.md`, or
  required `flow-<FLOW-SLUG>.md` are missing, unless the requester records an
  explicit context-only BRD draft risk acceptance and the BRD remains
  non-approved
- Module Analysis Done → Spec Writer without an approved BRD Package, unless
  the requester explicitly records a technical-spec-only bypass and accepts the
  review risk
- Spec Drafted → Forward Handoff (skipping review and approval)
- Any stage where evidence has `sensitivity: unknown` → any downstream

If a skip is unsafe, say so and route to the missing prerequisite.

### Module-First Document Routing

**Pre-route rule (format normalization first).** Before routing to
`legacy-flow-context-normalizer`, check the form of the source material:

- If the inputs are raw Office / Visio / PDF / image files (`.xlsx`, `.xlsm`,
  `.xls`, `.docx`, `.doc`, `.pptx`, `.ppt`, `.vsdx`, `.vsd`, `.pdf`, `.png`,
  `.jpg`, `.tif`, scanned pages) **and** there is no
  `00_context_packages/<MODULE-SLUG>/document-intake/<DOCSET-SLUG>/intake.manifest.yaml`
  yet, route to `legacy-document-evidence-intake` first.
- **Exception:** if any source has `sensitivity: unknown` or missing/`unauthorized`
  authorization (or unapproved production data, or required redaction), route to
  `legacy-ibmi-evidence-intake` first instead — neither this orchestrator nor the
  document-intake skill may open unauthorized content.
- If an `intake.manifest.yaml` exists with gate `ready` or `ready_with_warnings`,
  proceed to `legacy-flow-context-normalizer` using its normalized outputs,
  `evidence-coordinates.md`, and `extraction-warnings.md`.
- If the material is already normalized text/Markdown/CSV (or external RAG), skip
  document intake and route straight to `legacy-flow-context-normalizer`.

When the user has historical documents/specs but no SME-reviewed module
context, route to `legacy-flow-context-normalizer` even when the material
looks weak. The router must not require perfect four-view input before
starting. Function Specs, Technical Designs, Program Specs, File Specs,
interface specs, data dictionaries, RAG summaries, and SME notes are all valid
optional starting material.

Use this quality-aware routing:

| Input Quality | Route | Expected Status |
| --- | --- | --- |
| Documents/specs appear able to support all four views | `legacy-flow-context-normalizer` | `draft_needs_sme_review` or later `ready_for_context_intake` |
| Documents/specs support only some views | `legacy-flow-context-normalizer` | `draft_needs_sme_review` with placeholders, or SME-accepted `ready_with_warnings` |
| Documents/specs are authorized/readable but too sparse to form a safe sequence | `legacy-flow-context-normalizer` | `triage_needs_source_enrichment` |
| Sparse package already has named owner risk acceptance and no additional inputs can be provided | `legacy-module-context-intake` | `ready_with_warnings` only; preserve `quality_level: L1 sparse` and carry-forward TBDs |
| Documents are unauthorized, unreadable, out of scope, or lack any module boundary | Evidence intake, readable export, or SME boundary clarification | `blocked_*` remediation |

Do not route a `triage_needs_source_enrichment` package to
`legacy-module-context-intake`, `legacy-ibmi-module-analyzer`, or
`legacy-brd-writer`. Route it to source-owner supplement collection or SME
clarification first. If the owner explicitly accepts that no more flow input
can be provided, route the resulting `ready_with_warnings` package to
`legacy-module-context-intake`, not to module analysis or BRD generation.
State that all sparse facts remain low-confidence and cannot become approved
rules without later corroboration.

### Code-Backed BRD Enrichment Gate

The standard Legacy Spec Factory BRD is **code-backed**. A document-first or
RAG-first run may create useful context packages, but those packages do not
replace the Layer 1 evidence backbone when the user expects a BRD that describes
the legacy system with code confidence.

Before routing a module-first package to an approvable module analysis or BRD,
check whether any of the following are true:

- the user's target is a production / internal-use BRD, migration discovery
  baseline, spec, or SDD handoff input
- the input package references IBM i / AS400 programs, jobs, files, PF/LF,
  DSPF, PRTF, DDS/DDL, ARCAD inventory, DSPPGMREF output, source members, or
  code/RAG snippets
- `flow-context-index.yaml.coverage.technical_anchor_coverage.program_anchors`
  or `data_anchors` is `partial`, `usable`, or `strong`
- the generated module or BRD would otherwise state behavior as
  `confirmed_from_code`

If any condition applies, the next route is the earliest missing code-backed
artifact:

1. `legacy-ibmi-inventory` to produce `01_inventory/inventory.yaml` and
   `01_inventory/object-map.md`
2. `legacy-ibmi-program-analyzer` for every in-scope `OBJ-*`
3. `legacy-ibmi-flow-analyzer` for every in-scope business transaction
4. `legacy-ibmi-module-analyzer` to synthesize the canonical four views
5. `legacy-brd-writer`

Only allow a direct context-only module / BRD draft when the user explicitly
records a named owner risk acceptance that source/object evidence is not
available for this cycle. In that case:

- the module and BRD must label the evidence mode as `context_only`
- missing object map, program analysis, and flow analysis are explicit
  `TBD-*` blockers for code-backed approval
- `brd.md` may be `draft` or `in_review`, but not `approved`
- traceability must not use `confirmed_from_code` unless linked code-derived
  evidence exists

### Canonical Four-Flow Timing

Only `legacy-ibmi-module-analyzer` produces the canonical four module-flow
artifacts under `04_modules/<MODULE-SLUG>/`. Earlier module-first stages may
write four files under `00_context_packages/`, but those are draft or
normalized context views. When reporting upstream work, use wording such as
"created draft context views" or "normalized a context package"; do not say
"created the four module flows" until the module analyzer writes
`module-overview.md`, `01-operation-flow.md`, `02-system-flow.md`,
`03-program-flow.md`, and `04-data-flow.md` under `04_modules/`.

### BRD Discovery Review Gate

After module analysis completes, the default next route is
`legacy-brd-writer`, not `legacy-spec-writer` or
`legacy-brd-to-sdd-handoff`. The BRD Package is the primary migration-discovery
artifact for old-system understanding. It must cover BRD functional-analysis
sections 1-9, while sections 10-12 remain optional and evidence-backed.

Route to `legacy-spec-writer` only when one of these is true:

- `05_brds/<CAPABILITY-SLUG>/` contains an approved BRD Package
  (`brd.md`, `brd-review.md`, `validation-scenarios.md`, `traceability.md`,
  and approval / review decision evidence) for the selected `CAP-*` **and** a
  named post-BRD stakeholder promotion / disposition decision says the
  capability should move beyond discovery; or
- the requester explicitly asks for a technical-spec-only bypass, names the
  approver, and accepts that the missing BRD review is a documented risk.

Do not route No-gap, Gap1, follow-new-system, or pending-decision outcomes to
spec-writing. When risk assessment or gap analysis is open, route to the named
business/risk/gap-analysis owner first.

If BRD review is still draft, blocked, or missing sections 1-9 without named
`TBD-*` carry-forward, route back to `legacy-brd-writer` or
`legacy-sme-review-facilitator`.

### Step 4B — Apply Hard Gates

Before any handoff, check the gate that applies to that transition. See
[references/gates.md](references/gates.md) for full criteria.

| Gate | When Applied | Blocks If |
| --- | --- | --- |
| **Evidence Authorization Gate** | Before any Layer 1 skill or any agent reads evidence | Any evidence has `sensitivity: unknown`, lacks source-path authorization, or requires redaction without an approval record |
| **Inventory Completeness Gate** | Before any Layer 1 analyzer downstream of inventory, and before any Layer 2 skill | `inventory.yaml.sme_review.decision: blocked`, or any `coverage_gaps` entry with `blocking: yes` is unresolved |
| **Code-Backed Analysis Gate** | Before approving module analysis or BRD for standard BRD/spec work | Missing `01_inventory/object-map.md`, incomplete in-scope program analyses, incomplete in-scope flow analyses, or no explicit context-only risk acceptance |
| **BRD Discovery Gate** | After module analysis and before any spec-writing decision | No approved BRD Package exists for the selected `CAP-*`, BRD sections 1-9 are incomplete without named `TBD-*`, or BRD review is blocked |
| **Post-BRD Disposition Gate** | Before `legacy-spec-writer` in the standard workflow | Approved BRD has no separate promotion decision, item is No-gap / Gap1 / follow-new-system, or risk/gap-analysis owner has not cleared promotion |
| **Evidence Approval Gate** | Before `legacy-spec-writer` produces an approvable spec | Any business rule has `review_status: needs_sme_review` or no linked evidence, and `knowledge_type` is not `modernization_decision` |
| **Forward Handoff Gate** | Before crossing to `wwa-lab/build-agent-skill` | `spec.yaml.status` is not `approved`, any critical rule unapproved, any blocking TBD remains, or `acceptance_criteria` missing for any approved rule |

If a gate is blocked, the orchestrator must:

1. State which gate failed
2. List the specific unresolved items (TBD IDs, evidence IDs, rule IDs)
3. Route to the prerequisite skill or doc that resolves it
4. Refuse to route further downstream until the gate clears

### Step 5 — SME Reminders

The SME is the control point for reverse modernization. Proactively remind the
user when SME involvement is required:

| Just Produced | SME Reminder |
| --- | --- |
| `inventory.yaml` (draft) | Request SME review against `inventory-review-checklist.md` before moving to analysis |
| `program-analysis.md` | SME validation recommended if the program affects money, inventory, compliance, or customer status |
| `business-rules.md` (draft) | SME must confirm every rule with `knowledge_type: inferred_business_rule` before approval |
| `brd.md` / BRD Package (draft) | SME / business review required before using as legacy-system discovery baseline; sections 1-9 must be reviewed, sections 10-12 may remain absent unless evidence exists; old-vs-new comparison is outside the BRD Package |
| `spec.yaml` (in_review) | SME sign-off required to move from `in_review` to `approved` |
| Modernization decisions added | Architecture/product approval, not just IBM i SME |

For trivial L1-level slices (single field, single read-only program), note
that SME review is still recommended but does not block draft progress.

### Step 6 — Execute or Route

After deciding:

- if the user clearly wants the next artifact produced now AND the next skill
  is implemented AND input is sufficient → hand off to that skill
- if the next skill is planned → return the routing decision plus the manual
  fallback instructions from [references/manual-fallback.md](references/manual-fallback.md)
- if a gate is blocked → return the blocking finding, do NOT hand off
- if the user is asking only for guidance → return the routing decision and
  what input is still needed

The orchestrator should create momentum, not bureaucracy.

### Step 7 — Attach the Stage Card

Every routing decision **must** end with the **Quick Card** block defined in
the Output Structure section below, and **must** point the user to the
matching one-page stage card under
[`references/stage-cards/`](references/stage-cards/INDEX.md).

Stage-card mapping (use the same number that appears in
`references/stage-identification.md`):

| Identified Stage | Stage Card |
| --- | --- |
| 0 Evidence Intake | `references/stage-cards/00-evidence-intake.md` |
| 1 Evidence Ready | `references/stage-cards/01-evidence-ready.md` |
| 2a / 2b / 2c Inventory | `references/stage-cards/02-inventory.md` |
| 3a / 3b Program Analysis | `references/stage-cards/03-program-analysis.md` |
| 3c / 3d Flow Analysis | `references/stage-cards/04-flow-analysis.md` |
| 3e / 3f Module Analysis | `references/stage-cards/05-module-analysis.md` |
| 3f Module Analysis Done, BRD gate open | `references/stage-cards/05a-brd-writing.md` |
| 8a / 8b / 8c Spec | `references/stage-cards/06-spec-writing.md` |
| 9 / 10 Equivalence / Handoff | `references/stage-cards/07-forward-handoff.md` |

The cards are deterministic cheat sheets — they tell first-time users exactly
what input to have, what skill to run, where to save the output, which gate
to check, and which SME action is required. Attaching the card is mandatory
because it makes the next step legible even when the LLM running the
orchestrator is weak or context-starved.

### Step 8 — Write Workflow State

After the routing decision is rendered, update
`<repo-root>/<project.root>/workflow-state.yaml` (e.g.
`docs/XXX260004-demo/workflow-state.yaml`) so the next session (or the
next skill) can resume without re-deriving stage. The project root was
resolved at Step 0.b. All artifact paths written into the state file
(`current_focus.next_artifact`, `capabilities[].last_artifact`,
`history[].artifact`) are **relative to `project.root`**.

The orchestrator's write scope is:

1. **`current_focus`** — overwrite entirely with this turn's routing
   decision (capability id, module slug, `stage_id` verbatim from
   `references/stage-identification.md`, `next_skill`, `next_artifact`,
   `stage_card`, and `open_gates`).
2. **`capabilities[]`** — overwrite only the entry matching the routed
   capability (`id`). If no entry exists yet, append one. Never delete or
   mutate other entries.
3. **`history[]`** — append exactly one entry:
   ```yaml
   - at: <ISO 8601 timestamp>
     skill: legacy-modernization-orchestrator
     capability_id: <CAP-* | null>
     stage_after: <stage_id from references/stage-identification.md>
     artifact: null            # router does not produce business artifacts
     note: <one-line summary, e.g. "routed to legacy-ibmi-flow-analyzer">
   ```
4. **`project.last_updated_at` / `project.last_updated_by`** — overwrite
   with this turn's timestamp and `legacy-modernization-orchestrator`.

Special cases:

- **State file missing**: emit the populated file at
  `docs/<project.name>/workflow-state.yaml` based on the template at
  [`templates/workflow-state.yaml`](templates/workflow-state.yaml). Fill
  `project.name` and `project.root` (`docs/<project.name>/`). Tell the
  user (in the prose section above the Quick Card) that the file has
  been created, that any in-flight artifacts should be moved under the
  new project root, and that the file should be committed. Do NOT
  pre-create the 9 artifact subdirectories — downstream skills create
  them on demand.
- **State file disagrees with artifacts**: rewrite the affected
  `capabilities[]` entry to match the artifact's `status` field and append
  a `history[]` entry with `note: "state corrected from artifact"`.
- **Routing decision is BLOCKED by a gate**: still write the state — record
  the blocked gate in `current_focus.open_gates` and in
  `capabilities[].blocking.gates`. Do not advance `stage_id`.

The orchestrator MUST NOT write to fields owned by downstream skills (no
other `capabilities[]` entries; no edits to past `history[]` entries; no
schema changes). See
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md)
for the full field-level contract that every skill in the chain follows.

### Step 8.5 — Regenerate STATUS.md

After Step 8 writes the YAML state, regenerate the human-readable
companion `docs/<project>/STATUS.md` so a human reader can see project
status at a glance without parsing YAML.

In GitHub Copilot hosted-agent mode, do not run the status generator or
configure Python. In an already-prepared local shell only, run
`scripts/generate-status.py docs/<project-name>/` with an existing Python
interpreter.

The script emits a single-page snapshot: current focus, all capabilities
with their stage / blocking, open blockers grouped by capability, and the
last 10 history entries. It is **always** in sync with
`workflow-state.yaml` because it is derived from it — never hand-edit
STATUS.md.

Run the script only with an already-available Python interpreter. Do not create
a virtual environment, install packages, or wait on interactive environment
configuration for status regeneration. If the script or interpreter is
unavailable in the runtime, or startup remains configuring/evaluating for more
than about 30 seconds, skip this step and tell the user (in the prose above the
Quick Card): "STATUS.md not regenerated — run
`scripts/generate-status.py docs/<project>/` manually with an existing Python
interpreter."

Downstream skills SHOULD also call this script at the end of their own
write-back, but the orchestrator running it after every routing decision
is the canonical guarantee that STATUS.md never drifts.

## Output Structure

Use the following structure. Keep it proportionate to the decision — for an
obvious route, one short paragraph may be enough.

```
## Workflow Decision

- **Current Stage:** <stage from Step 1>
- **Desired Outcome:** <outcome from Step 2>
- **Recommended Next Skill:** <skill name> (status: implemented | planned | future | doc-only)
- **Why:** <1–3 short sentences>

## Routing Notes

- **Stage skip safe?** <yes / no — which stages, why>
- **Gate check:** <gate name: pass | blocked — list unresolved items | not applicable>
- **Minimum input needed next:** <list>
- **Route confidence:** <high / medium / low>
- **Next artifact expected:** <artifact name and suggested filename>

## Next Step

- **Invoke:** <skill name | follow doc <path>>
- **Produce:** <next artifact>
- **Save reminder:** <save current artifact as [suggested filename]; consumed by [downstream skill]>
- **SME reminder:** <when SME is required and what to ask>
- **Review/export reminder:** <when Markdown should remain canonical; whether `legacy-html-exporter` is useful for SME/browser review; or "not applicable">
- **Manual fallback (if skill is planned):** <what to do until the skill exists; pointer to references/manual-fallback.md>
```

Review/export reminder rules:

- Markdown remains canonical for human-facing artifacts (`spec.md`, `brd.md`,
  `traceability.md`, `STATUS.md`, review packs, question packs, handoff docs).
- `spec.yaml` remains the machine-readable source of truth for downstream
  automation.
- Recommend `legacy-html-exporter` only after a stable human-facing Markdown
  artifact exists and the user needs browser-friendly SME / user review.
- If Markdown is missing, blocked, or wrong, route to the producing skill first;
  do not suggest HTML as a workaround for unfinished content.
- If the user asks for HTML to replace Markdown or become the source of truth,
  block that request and state that HTML is a companion view only.
- Do not put `legacy-html-exporter` in `RUN NEXT` unless the user's desired
  outcome is explicitly review packaging, browser view, HTML export, or easier
  SME/user reading. Otherwise mention it only in the Review/export reminder.

### Mandatory Quick Card footer

Every routing decision MUST end with the block below, rendered verbatim with
each `<...>` replaced by one short value. **Do not omit any line. Do not add
commentary inside the block. Do not change the line order or labels.** This
block is the user's at-a-glance cheat sheet — keep it grep-friendly so it
survives weak LLMs, copy-paste, and session restarts.

```
----------------------------------------------------------------------
QUICK CARD — Stage <stage-id> : <stage name>
----------------------------------------------------------------------
PROJECT:       docs/<project-name>/   [<resumed | created | switched-project>]
PROGRESS:      [●●●○○○○○○○] 3/10 <milestone label>
FOCUS:         <CAP-* | MODULE-* | unset> [continued | switched | new | scan | rollback]
YOU ARE HERE:  <stage-id from references/stage-identification.md>
JUST SAVED:    <full path of the artifact the user just produced, or "nothing yet">
RUN NEXT:      <next skill name>   [<implemented | planned | future | doc-only>]
WILL PRODUCE:  <full path of the next artifact, including filename>
GATE CHECK:    <pass | not applicable | BLOCKED: <gate name> — <unresolved IDs>>
SME ACTION:    <required | recommended | not needed> — <one-line action>
STAGE CARD:    references/stage-cards/<NN>-<slug>.md
STATE FILE:    docs/<project-name>/workflow-state.yaml [<updated | created | unchanged>]
MANUAL FALLBACK: <path under references/manual-fallback.md, or "not needed (skill is implemented)">
----------------------------------------------------------------------
```

Rules for filling the Quick Card:

- `PROJECT` reports the resolved project root from Step 0.b plus an
  intent label: `resumed` (existing project default-picked or named by
  user), `created` (Step 0 just created `docs/<name>/`),
  `switched-project` (user named a different project than the prior
  turn). The path always ends with `/`. WILL PRODUCE / JUST SAVED / STATE
  FILE paths in this card MUST live underneath this project root — never
  cross into another project.
- `PROGRESS` shows the focused capability's position in the 10-step
  reverse chain as `[●●●○○○○○○○] N/10 <milestone label>`. Mapping (use
  the milestone label verbatim):
  - `0` → step 0 "Evidence Intake"
  - `1` → step 1 "Evidence Ready"
  - `2*` → step 2 "Inventory"
  - `3a/3b` → step 3 "Program Analysis"
  - `3c/3d` → step 4 "Flow Analysis"
  - `3e/3f` → step 5 "Module Analysis"
  - `8a` → step 6 "Spec Drafted"
  - `8b` → step 7 "Spec In Review"
  - `8c` → step 8 "Spec Approved"
  - `9` → step 9 "Equivalence Pack Ready"
  - `10` → step 10 "Forward Handoff Ready"
  Supplemental stages (`4*`, `5`, `6`, `7`) do not advance the bar — they
  remain at the prior step's filled count with the appropriate milestone
  label noted. When `current_focus` is unset, write `[○○○○○○○○○○] 0/10
  not started`.
- `FOCUS` reports the outcome of Step 0.5: the resolved `CAP-*` /
  `MODULE-*` (or `unset` only when scan mode is still pending), followed
  by exactly one intent label from `[continued | switched | new | scan |
  rollback]`. Never omit. If the orchestrator skipped Step 0.5 because
  the user input was advisory only, write `unset [continued]`.
- `YOU ARE HERE` uses the exact stage id from
  `references/stage-identification.md` (e.g. `2c Inventory Done`,
  `3b Program Analysis Done`).
- `JUST SAVED` is the artifact the user produced in the **previous** step,
  not the one they are about to produce. If the user is just starting, write
  `nothing yet`.
- `RUN NEXT` is one skill name. Never list two. If the path forks, pick the
  earliest sufficient one and explain alternatives in the prose above, not
  inside the card.
- `WILL PRODUCE` is a full suggested path, including filename, drawn from the
  stage card. Do not invent novel paths — use the directory layout in
  `references/stage-identification.md` (`Stage to Output Directory` table).
- `GATE CHECK` either passes, is not applicable, or names the specific
  blocking gate plus the unresolved item IDs (`TBD-*`, `EV-*`, `BR-*`,
  `coverage_gaps[i]`). Never leave the reason vague.
- `STAGE CARD` is always populated using the mapping in **Step 7 — Attach
  the Stage Card** above.
- `STATE FILE` reports the outcome of Step 8: `updated` if an existing
  `workflow-state.yaml` was overwritten, `created` if the file was emitted
  for the first time this turn, or `unchanged` if this turn was advisory
  only and no state mutation occurred. Never omit this line — silence
  hides whether the chain still has a valid resume point.
- `MANUAL FALLBACK` is required whenever the recommended skill is `planned`
  or `future`. When the skill is implemented, write
  `not needed (skill is implemented)` rather than omitting the line.

Validation: a routing decision that omits the Quick Card, omits any of its
lines, or invents stage / skill / card paths fails the Mechanical validation
check in the Step Contract below.

## Step Contract

The orchestrator is one step in the Legacy Spec Factory reverse chain — its
step produces a **routing decision**, not a business artifact. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required**: a description of what the user currently has (the
  candidate stage) and what they want to reach (the desired outcome).
  At minimum: artifact name(s) and observed status; or, when no artifact
  exists yet, the legacy evidence the user is starting from.
- **Optional**: SME availability, target platform hint, urgency, scope
  preference (one capability vs. whole module).
- **Workflow state**: `<project-root>/workflow-state.yaml` if present.
  Read at Step 0 per `docs/workflow-state-contract.md`. Treated as a
  resume hint; artifacts remain the source of truth.
- **Focus signals**: literal `CAP-*` / `MODULE-*` IDs, file paths matching
  the directory layout, and continue / rollback / new / switch verbs in
  the user's natural-language message. Resolved at Step 0.5 per
  `references/focus-selection.md` into one of `continued | switched | new |
  scan | rollback`. When ambiguous, the orchestrator asks rather than guesses.
- **Readiness checks**: artifact filenames and statuses can be cited
  verbatim from the user's repo or notes (not paraphrased); evidence
  sensitivity is known or explicitly flagged `unknown`.
- **Stop conditions**: stage cannot be classified even conservatively
  (request a concrete artifact); user wants an unsafe downstream skip
  (refuse and route to the missing prerequisite); evidence sensitivity
  is `unknown` and the user is asking to invoke a Layer 1 skill (Redaction
  Gate blocks).

### Execution

- **Procedure**: see the Core Process section above (Steps 1–6).
- **Allowed inference**: conservatively classifying the current stage
  from the artifact's status field; reading the applicable hard gates from
  the artifact's own evidence (not from user assertion); choosing the
  earliest sufficient next skill.
- **Forbidden assumptions**: inferring that a `Planned` / `Future`
  skill exists; claiming a gate has passed without checking the relevant
  fields; collapsing evidence / behavior / rule / decision into one
  bucket; "rounding up" a partial artifact's maturity; skipping an SME
  reminder to make the user happier.
- **TBD handling**: when the stage is genuinely ambiguous, report it as
  ambiguous and request a specific artifact rather than guessing; when a
  gate-blocker exists, surface the specific unresolved item IDs and
  refuse to route further downstream.

### Output

- **Canonical artifact**: a routing decision rendered in the **Output
  Structure** template above (Workflow Decision + Routing Notes + Next
  Step). The orchestrator does not produce inventory, program analyses,
  flows, modules, specs, or reviews.
- **Required sections**: current stage, desired outcome, recommended next
  skill (with implementation status), why, stage-skip safety, gate-check
  result, minimum input needed next, route confidence, next artifact
  expected, invoke / produce / save reminder / SME reminder /
  review-export reminder / manual fallback (if next skill is planned).
- **Required IDs**: no new ID minting. Cites existing IDs from upstream
  artifacts when surfacing blockers (`TBD-*`, `EV-*`, `BR-*`, etc.).
- **Handoff status**: the decision either hands off to a downstream
  skill (when input is sufficient and the skill is implemented), returns
  a manual fallback (when the skill is planned), or returns a blocking
  finding (when a gate fails). Across turns, continuity is provided by
  `workflow-state.yaml` (Step 0 reads, Step 8 writes) per
  `docs/workflow-state-contract.md`. Within a single turn, every routing
  decision still restates its premise from the cited artifacts — the
  state file is a resume hint, not a substitute for artifact evidence.

### Validation

- **Mechanical**: every routing field present (current stage, desired
  outcome, recommended next skill + status, why, stage-skip safe?, gate
  check, minimum input, route confidence, next artifact, invoke / produce
  / save / SME / review-export / manual fallback); cited skill names exist
  in the chain; cited gates exist in `references/gates.md`; the **Quick
  Card** footer block is present, all twelve lines are filled, the cited
  stage-card path
  resolves under `references/stage-cards/`, the `WILL PRODUCE` path lives
  under the resolved `PROJECT` root and conforms to the directory layout
  in `references/stage-identification.md`, `STATE FILE` resolves to
  `<PROJECT>workflow-state.yaml` and reports one of `updated | created |
  unchanged` matching the actual Step 8 outcome, `FOCUS` reports a
  resolved `CAP-* | MODULE-* | unset` plus one of `continued | switched
  | new | scan | rollback` matching Step 0.5, `PROJECT` matches the
  resolved `project.root` from Step 0.b (PPCR-validated name), and
  `PROGRESS` shows `[●…○…] N/10 <milestone>` derived from
  `current_focus.stage_id` per the mapping table above.
- **AI semantic**: recommended next skill is the **earliest sufficient**
  stage (no upstream over-routing, no unsafe downstream jump); gate state
  reflects the artifact's actual fields rather than a confident summary;
  implementation status is honest (`Implemented` vs `Planned` /
  `Future`); SME reminder included whenever SME is required; HTML export is
  recommended only as a companion read view for stable human-facing Markdown.
- **SME / human approval**: not required for the routing decision itself,
  but the orchestrator must **flag** every SME control point the
  downstream skill will hit and refuse to advise skipping it.
- **Blocking conditions**: any hard gate fails (Evidence Authorization Gate,
  Inventory Completeness Gate, BRD Discovery Gate, Post-BRD Disposition Gate,
  Evidence Approval Gate, Forward Handoff Gate); recommended skill status is
  `Planned` / `Future` and no
  manual fallback is provided; stage cannot be classified even
  conservatively; user-asserted artifact maturity contradicts the
  artifact's own status field.

When asked for a compact result by another agent (e.g., a parent
orchestrator or `legacy-step-contract`), emit:

```
status: pass | pass_with_warnings | blocked
step_id: STEP-ROUTING-<NNN>
blocking_items: [<gate or TBD IDs>]
warnings: [<non-blocking items>]
sme_decision: not_required
downstream_next_step: <skill-name | doc-path | none>
remediation_step: <skill-name | doc-path | none>
```

The fuller routing prose stays in the Output Structure template above.

## Core Rules

### Router-Only Rule

This skill routes work. It does not replace any downstream skill. If a clear
downstream skill exists and input is sufficient, hand off rather than stopping
at routing commentary.

### Evidence-Authorization-First Rule

Never route a user to any agent skill when the evidence has `sensitivity:
unknown`, lacks `source_path_verified: true`, or has `redaction_required: true`
without a redaction approval record. The Evidence Authorization Gate must pass
first, even if the user is impatient. Do not require SME ownership or a separate
redacted copy for Step 0 internal source review when the user has provided the
same source path as the approved analysis path.

### Inventory-Before-Inference Rule

Do not route to `legacy-business-rule-miner` or any Layer 2 synthesizer before
inventory is at least `approved_with_non_blocking_tbd`. Rule mining without a
sound inventory invites hallucinated rules.

### SME-Always Rule

Modernization decisions, inferred business rules affecting money / inventory /
compliance / customer status / posting, and `spec.yaml` approval transitions
require SME confirmation. The orchestrator must surface the requirement even
when the user does not ask for it.

### Safest Sufficient Stage Rule

Route to the earliest stage that is sufficient for safe progress. Do not send
users upstream unnecessarily, but do not allow unsafe downstream jumps.

### No-Hallucination Rule

Do not invent missing artifact maturity. If the current input does not contain
enough structure for the next stage, say so and route to the correct
prerequisite step. Do not "round up" a partial artifact.

### Planned-Skill Honesty Rule

When the recommended next skill is `Planned` or `Future`, say so clearly.
Provide the manual fallback. Do not pretend the skill is available.

### Momentum Rule

Prefer one clear next skill, one clear reason, one clear note about missing
input or gate failure. Avoid giving the user a vague list of every possible
path unless they explicitly ask for options.

## Anti-Hallucination Rules

- Do not infer that a skill exists when its status is `Planned`.
- Do not claim a gate has passed without checking the specific fields.
- Do not invent stage classifications. If unsure, say "ambiguous" and ask for
  a specific input.
- Do not collapse evidence, behavior, rule, and decision into one bucket. The
  taxonomy in `docs/evidence-and-knowledge-taxonomy.md` is the source of truth.
- Do not skip SME reminders to make the user happier.
- Do not let HTML replace Markdown or `spec.yaml` as a source of truth.

## Quality Checklist

Before outputting workflow guidance, confirm:

- [ ] Current stage has been identified correctly or conservatively
- [ ] Desired outcome has been identified correctly
- [ ] Recommended next skill is the safest sufficient next step
- [ ] Stage-skipping rules respected
- [ ] All applicable hard gates checked
- [ ] SME reminder included when SME is required
- [ ] Review/export reminder preserves Markdown / `spec.yaml` source-of-truth rules
- [ ] Planned vs implemented status stated for the recommended skill
- [ ] Manual fallback offered if skill is planned
- [ ] No invented artifact maturity
- [ ] Guidance is proportionate and creates forward motion
- [ ] **Quick Card** footer block is present and complete (all twelve lines filled)
- [ ] `PROGRESS` step count and milestone label match the focused capability's `stage_id` per the mapping in the Quick Card rules
- [ ] `STAGE CARD` line points to an existing file under `references/stage-cards/`
- [ ] `WILL PRODUCE` path lives under the resolved `PROJECT` root and matches the directory layout in `references/stage-identification.md`
- [ ] Step 0.b resolved a PPCR-valid project name (`^[A-Za-z0-9][A-Za-z0-9-]*$`); if multiple projects exist, the picker was shown rather than silently defaulted
- [ ] Step 0.c read `docs/<project>/workflow-state.yaml` (or recorded that it was missing)
- [ ] No artifact directories were pre-created; only the writing skill's target directory is created on demand
- [ ] Step 8.5 regenerated `docs/<project>/STATUS.md` (or recorded that the script was unavailable)
- [ ] When the user-typed project name was non-conforming, Step 0.b auto-normalized + asked the user to confirm — did not silently reject
- [ ] Step 0.5 resolved focus to one of `continued | switched | new | scan | rollback`; ambiguous inputs were ASKED rather than guessed
- [ ] No `CAP-*` / `MODULE-*` invented; all IDs trace to artifacts, state, or user message
- [ ] Rollback (if any) targets a strictly earlier stage AND a previously reached stage, and added a `history[]` note
- [ ] Scan mode (if triggered) presented the picker; orchestrator did not pre-pick silently
- [ ] Step 8 updated / created `workflow-state.yaml` per `docs/workflow-state-contract.md` (or wrote `unchanged` with justification)
- [ ] `current_focus` overwrite respects ownership (no edits to other capabilities' entries or past `history[]` rows)

## Relationship to Other Legacy Spec Factory Skills

This skill coordinates the rest of the reverse chain:

### Layer 1 — Platform-specific extraction (IBM i)

| Skill | Status | Orchestrator Use |
| --- | --- | --- |
| `legacy-ibmi-inventory` | **Implemented v0.1.0** | First call after evidence redaction; produces `inventory.yaml` |
| `legacy-ibmi-program-analyzer` | **Implemented v0.2.4** | Per-program: Program Call Map Call Evidence, Routine Logic Details with routine-local lineage / carriers and exception closure, source identifier + meaning fields, File I/O Purpose, object deps, dynamic-call resolution, Error Code Inventory, exception closure |
| `legacy-ibmi-flow-analyzer` | **Implemented v0.2.2** | Per call chain: 7 trigger models; replay path; edge Evidence Source / Resolution; field lineage consuming routine-local carriers, persistence matrix with purpose; exception chain consuming routine-local exception closure; commit boundaries |
| `legacy-ibmi-module-analyzer` | **Implemented v0.2.2** | 4-view module synthesis plus module replay readiness, edge-resolution coverage, critical field lineage, persistence purpose, and exception recovery summaries per `docs/module-analysis-model.md` |
| `legacy-ibmi-runtime-evidence-miner` | Future (deferred from MVP) | Mine job logs, spool, samples to strengthen evidence |

### Layer 1 — Future platforms

`legacy-cobol-*` and `legacy-mainframe-*` families: future. Until they exist,
COBOL/mainframe shops use manual extraction following the same output
contract Layer 2 expects.

### Layer 2 — Platform-agnostic synthesis

| Skill | Status | Orchestrator Use |
| --- | --- | --- |
| `legacy-business-rule-miner` | Subsumed by module-analyzer View 1 + spec-writer rule-extraction protocol | (BR seeds in module View 1; spec-writer formalizes) |
| `legacy-capability-mapper` | Subsumed by module-analyzer overview Capability Seeds | (CAP-* in `module-overview.md`) |
| `legacy-brd-writer` | **Implemented v0.1.7** | Produce the legacy BRD Package as the legacy-system discovery baseline without old-vs-new comparison or disposition notes |
| `legacy-spec-writer` | **Implemented v0.1.6** | Produce `spec.yaml` + `spec.md` + `spec-review.md` + `traceability.md` per capability after BRD review plus explicit post-BRD promotion / disposition decision and analyzer v0.2.4 routine-local evidence consumption |
| `legacy-spec-reviewer` | Future (deferred from MVP) | Validate draft spec against gate; until implemented, use spec-writer's review templates with SME |
| `legacy-equivalence-test-generator` | Planned | Old-vs-new golden master tests |
| `legacy-html-exporter` | **Implemented v0.1.0** | Optional companion export for stable human-facing Markdown; creates `.html` / `index.html` without changing the source of truth |

### Documentation routes (not skills)

| Doc | When the orchestrator points to it |
| --- | --- |
| `docs/data-collection-and-redaction.md` | Evidence Authorization Gate and governed redaction |
| `docs/id-conventions.md` | ID prefix / format questions |
| `docs/evidence-and-knowledge-taxonomy.md` | Confidence / strength / approval questions |
| `docs/forward-sdlc-contract.md` | Forward Handoff Gate, crossing to `wwa-lab/build-agent-skill` |
| `docs/mvp-scope.md` | Scoping the first slice |

## Runtime Portability

The canonical skill source lives under:

```text
skills/legacy-modernization-orchestrator/SKILL.md
```

Runtime copies may be synced to:

```text
.claude/skills/legacy-modernization-orchestrator/SKILL.md
.opencode/skills/legacy-modernization-orchestrator/SKILL.md
.agents/skills/legacy-modernization-orchestrator/SKILL.md
.codex/skills/legacy-modernization-orchestrator/SKILL.md
```

From the repository root, use `scripts/sync-skills.sh` to create or check
runtime copies.

## Version History

- v0.2.10 (2026-06-02): Aligned routing tables, gates, and stage cards with
  program-analyzer v0.2.4, flow-analyzer v0.2.2, module-analyzer v0.2.2, and
  spec-writer v0.1.6 so orchestration checks Routine Logic Details,
  routine-local lineage/carrier rows, routine-local exception closure, and
  their downstream flow/module/spec consumption before BRD / spec handoff.

- v0.2.9 (2026-06-02): Aligned routing tables, gates, and stage cards with
  program/flow/module analyzer v0.2.1 contracts so orchestration checks for
  Call Evidence, source identifier + business meaning fields, File I/O
  Purpose, dynamic-call resolution, Error Code Inventory, edge Evidence Source
  / Resolution, persistence purpose, and exception-chain evidence before BRD /
  spec handoff.

- v0.2.8 (2026-06-01): Aligned routing tables and stage cards with
  program/flow/module analyzer v0.2.0 contracts so orchestration checks for
  key field logic, field-level persistence, replay, lineage, and exception
  chain evidence before BRD/spec handoff.

- v0.2.7 (2026-05-30): Added the Code-Backed BRD Enrichment Gate so
  document-first / RAG-first runs cannot jump from context packages directly to
  approvable BRDs while skipping `object-map.md`, per-program analysis, or
  flow analysis. Context-only BRDs now require explicit named risk acceptance
  and remain non-approved drafts.

- v0.2.6 (2026-05-30): Reframed BRD routing as migration discovery. After
  module analysis, the primary near-term route is legacy BRD generation. BRD is
  legacy-system-only; No-gap / Gap1 / Gap2 comparison happens in a separate
  post-BRD disposition process before any spec-writing decision.

- v0.2.5 (2026-05-29): Made BRD-first routing explicit. After module
  analysis, the standard route is `legacy-brd-writer`; `legacy-spec-writer`
  requires an approved BRD Package or an explicit technical-spec-only bypass
  with risk acceptance. Added `05a-brd-writing.md` as the BRD review stage
  card between module analysis and spec writing.
- v0.12.0 (2026-05-16): Closed two linear-chain gaps.
  `legacy-ibmi-screen-report-analyzer` and
  `legacy-ibmi-data-model-analyzer` graduate from optional supplemental
  to **conditionally required** via a new mechanism: inventory's
  `sme_review.downstream_required` block. Inventory auto-detects DSPF /
  PRTF / menu objects (→ screen-report-analyzer required) and ≥ 3 files
  with FK-like relations or compound master writes (→
  data-model-analyzer required); SME confirms in the same batched
  signoff as criticality. Orchestrator's `3b Program Analysis Done`
  gate now mechanically enforces these triggers. Module-analyzer
  Inputs + spec-writer Inputs declare the conditional dependency;
  spec-writer populates `data_model.entities` verbatim from
  `dictionary.md` when triggered, preserving cross-program invariants.
  Trigger rules, override protocol, and anti-patterns in
  `skills/legacy-ibmi-inventory/references/downstream-triggers.md`.
- v0.11.0 (2026-05-16): SME-bandwidth strategy completion. Three skills
  now collaborate to drop typical SME review load 70-80%:
  (1) `legacy-ibmi-inventory` v0.2 adds `criticality` (critical /
  standard / low_risk) + single-batched SME confirmation;
  (2) `legacy-ibmi-runtime-evidence-miner` v0.2 adds Rule Auto-Validation
  (promote `inferred_business_rule` to `auto_validated_spot_check_only`
  when ≥ N runtime samples corroborate; never auto-validate critical
  money/posting/compliance);
  (3) NEW skill `legacy-ibmi-batch-digest` aggregates per-module
  program analyses into a single SME-facing scan page grouped by
  criticality with one-line roles, top-3 pending decisions, TBD counts,
  and SME signoff stub — replaces "open N files" friction with "scan
  one page". `legacy-sme-review-facilitator` updated with Three-Bucket
  Review Routing (Full review / Spot-check / Batch confirm). Spec
  schema extended with `auto_validated_spot_check_only` review_status
  and `auto_validation` audit block. EXAMPLE-tutorial demonstrates all
  three strategies end-to-end.
- v0.10.0 (2026-05-16): Tier 3 polish. Added `PROGRESS` line (12th) to
  the Quick Card showing visual `[●●●○○○○○○○] 3/10 <milestone>` mapping
  from `stage_id` to a 10-step pipeline view. Same progress bar
  surfaced in `scripts/generate-status.py` (under Current Focus + new
  Progress column on the Capabilities table) and in
  `scripts/list-projects.py` (new Progress column in text + markdown
  output). Added [`docs/collaboration.md`](../../docs/collaboration.md)
  — multi-user patterns (one-project-per-operator recommended; parallel
  capabilities; sequential handoffs), per-section merge rules for
  `workflow-state.yaml` conflicts (`version`/`project` immutable,
  `current_focus` last-writer-wins, `capabilities[]` per-id with later
  stage winning, `history[]` union-merge with timestamp re-sort), and
  an optional `.gitattributes` recipe. README + QUICKSTART now link the
  collaboration doc.
- v0.9.0 (2026-05-16): Tier 2 UX completion. Added
  [`QUICKSTART.md`](../../QUICKSTART.md) at repo root — a 10-minute
  walkthrough for first-time users with each step's natural-language
  trigger phrase. Added [`docs/EXAMPLE-tutorial/`](../../docs/EXAMPLE-tutorial/)
  — a fully-populated minimal project (1 program, 1 flow, 1 capability,
  1 spec) showing every artifact's shape and traceability end-to-end,
  including `workflow-state.yaml`, auto-generated `STATUS.md`, and lint
  validation. Added SME communication package templates to
  `legacy-sme-review-facilitator` (`sme-review-email.md` +
  `sme-review-checklist.md`) so operators can copy-paste a structured
  request to the SME in 30 seconds instead of drafting from scratch.
  README now leads with QUICKSTART + EXAMPLE pointers.
- v0.8.0 (2026-05-16): First-time-user UX pass (Tier 1). Expanded
  frontmatter `description` with natural-language trigger phrases in
  English and Chinese ("我有 AS400 / RPGLE 要分析", "我刚接了 PPCR XXX...",
  "I just inherited a legacy project", etc.) so the orchestrator matches
  organic user phrasing instead of requiring "use legacy-modernization-
  orchestrator". Reworked Step 0.b validation: project names that do not
  conform to PPCR convention are **auto-normalized** (whitespace / `.` /
  `_` / `/` → `-`, strip non-alphanumeric, preserve case) and asked back
  for confirmation instead of being silently rejected. Added Step 8.5:
  every routing decision regenerates `docs/<project>/STATUS.md` via
  `scripts/generate-status.py` so the human-readable status snapshot is
  always in sync with the machine state. New scripts:
  `scripts/generate-status.py` (renders STATUS.md from one project's
  state file) and `scripts/list-projects.py` (scans `docs/*/workflow-
  state.yaml` in cwd; text / markdown / json output). Both scripts
  registered in README.
- v0.7.0 (2026-05-16): Multi-project layout. Every project now lives under
  `docs/<project-name>/` (PPCR convention: `^[A-Za-z0-9][A-Za-z0-9-]*$`,
  e.g. `XXX260004-demo`). One repository can hold many fully-isolated
  projects. Added `project.name` and `project.root` to
  `workflow-state.yaml`; all artifact paths are now resolved relative to
  `project.root`. Replaced Step 0 with a 3-substep flow: 0.a enumerate
  `docs/*/workflow-state.yaml`, 0.b resolve / prompt for project name
  with PPCR validation (picker when multiple, prompt when none), 0.c
  read the chosen project's state file. Added `PROJECT` line (11th) to
  the Quick Card showing `docs/<project>/` plus a `resumed | created |
  switched-project` intent label. Updated contract, snippet,
  stage-identification, focus-selection (scan mode is now
  project-scoped), all 8 stage cards, INDEX (added Path Convention
  note), and lint script (validates PPCR name + `docs/<name>/` root
  shape; `--template` flag relaxes for the canonical template).
  Directories created on demand by writing skills; no pre-creation of
  empty stage folders.
- v0.6.0 (2026-05-16): Closed the chain-spine loop. Added Workflow State
  Write-Back sections to 11 additional skills: 2 Tier 1 (full overwrite —
  `legacy-golden-master-test-planner` at stage 9,
  `legacy-ibmi-runtime-evidence-miner` at stage 5) and 9 Tier 2
  (history-only or scoped blocking edits — `legacy-step-validator`,
  `legacy-traceability-packager`, `legacy-sme-review-facilitator`,
  `legacy-runtime-matrix-tester`, `legacy-step-contract`,
  `legacy-ibmi-screen-report-analyzer`,
  `legacy-ibmi-data-model-analyzer`,
  `legacy-modernization-decision-writer`, `legacy-brd-writer`).
  Reclassified `legacy-brd-writer` as supplemental / history-only in the
  snippet table. Added `scripts/check-workflow-state.py` (PyYAML-only)
  validating version, project, capabilities[].{id, stage_id, blocking},
  current_focus.{capability_id, stage_id, stage_card} cross-checks, and
  history[] append-only ordering. Documented the script in `README.md`.
  All 18 skills in the reverse chain now participate as peer writers
  to `workflow-state.yaml`, making the orchestrator-as-chain-spine usage
  truly closed-loop: any LLM / session / operator can resume from any
  capability, at any stage, via the lint-validated state file.
- v0.5.0 (2026-05-16): Mid-chain entry and natural-language focus resolution.
  Added **Step 0.5 — Determine Focus** to Core Process and a new reference
  [`references/focus-selection.md`](references/focus-selection.md) defining
  the five focus outcomes (`continued | switched | new | scan | rollback`),
  signal detection (CAP-* / MODULE-* / file paths / verbs in any language),
  the Scan Mode picker for inherited repos and lost state, the Switch
  Protocol, and the Rollback Protocol (strictly earlier + previously
  reached; never silent stage overwrite). Added `FOCUS` line (10th) to the
  Quick Card footer. Extended Step Contract Input to enumerate focus
  signals, tightened Mechanical Validation and Quality Checklist with
  focus-resolution requirements (no invented IDs, ambiguity must be asked,
  rollback / scan rules enforced). Designed for orchestrator-as-chain-
  spine: any user can drop in at any stage of any capability via natural
  language and get a deterministic route to the right downstream skill.
- v0.4.0 (2026-05-16): Cross-session state persistence. Added Step 0 (read
  `workflow-state.yaml`) and Step 8 (write `workflow-state.yaml`) to Core
  Process. Added template at `templates/workflow-state.yaml` and the
  full read/write contract at `docs/workflow-state-contract.md` so every
  downstream skill can participate as a peer writer (own its
  `capabilities[]` entry, append one `history[]` line, never touch others).
  Added `STATE FILE` line to the Quick Card footer and tightened
  Mechanical Validation + Quality Checklist to enforce Step 0 / Step 8.
  Designed for orchestrator-as-chain-spine usage: the state file is the
  resume point that lets a weaker LLM, a new session, or any peer skill
  pick up exactly where the chain left off without re-deriving stage from
  artifacts.
- v0.3.0 (2026-05-16): First-time-user UX hardening. Added 8 deterministic
  one-page **stage cards** under `references/stage-cards/` (`00-evidence-intake`
  through `07-forward-handoff` plus `INDEX.md`) covering input / skill /
  output path / gate / SME action / next card per stage. Added a mandatory
  **Quick Card** footer block to the Output Structure (8 fixed lines) that
  every routing decision must render verbatim — designed so weak LLMs and
  first-time users always see the next step, save path, gate state, SME
  action, and stage-card pointer at a glance. Added Step 7 (Attach the
  Stage Card) with a stage → card mapping table. Tightened the Mechanical
  Validation and Quality Checklist to enforce the new footer and card
  pointer.
- v0.2.1 (2026-05-27): Aligned module-first routing with
  `legacy-flow-context-normalizer` v0.1.4. Added quality-aware routing for
  strong, partial, sparse, and blocked document inputs, including
  `triage_needs_source_enrichment` handling so sparse authorized documents
  route to source-quality triage instead of being rounded up or blocked
  unnecessarily.
- v0.2.2 (2026-05-27): Added the risk-accepted sparse-input route. If the
  source owner/SME confirms no further flow input can be provided, the router
  may send an owner-accepted `ready_with_warnings` package to
  `legacy-module-context-intake` while preserving low confidence and blocking
  direct module-analysis or BRD routing.
- v0.2.3 (2026-05-28): Expanded module-first routing triggers beyond flow
  documents to Function Specs, Technical Designs, Program Specs, File Specs,
  interface specs, and data dictionaries as optional starting material for
  `legacy-flow-context-normalizer` v0.1.6.
- v0.2.4 (2026-05-29): Clarified four-flow timing so module-first context
  normalization reports `00_context_packages/` files as context views, while
  canonical `04_modules/` four-flow artifacts remain owned by
  `legacy-ibmi-module-analyzer`.
- v0.2.0 (2026-05-14): MVP scope expansion. Added stages 3c–3f (flow
  analysis, module analysis) reflecting the implementation of three new
  skills: `legacy-ibmi-flow-analyzer`, `legacy-ibmi-module-analyzer`, and
  `legacy-spec-writer`. Updated routing-decision-table and stage-identification
  to mark these skills `Implemented v0.1.0`. Marked subsumed legacy stages
  (call-graph, CRUD matrix, DSPF schema analyzer; business-rule-miner;
  capability-mapper) as folded into the new skills. All MVP-required
  Layer 1/2 skills now implemented; pipeline is e2e-ready for air-gapped
  pilot delivery.
- v0.1.1 (2026-05-13): Hardened runtime portability notes by using
  repository-root-relative paths for cross-repository references so synced
  adapter copies do not depend on canonical folder depth. Added a planned-skill
  manual-fallback routing example.
- v0.1.0 (2026-05-13): Initial entry-point router. Covers all 11 planned
  reverse-chain skills (1 implemented, 10 planned) plus the four hard gates
  and forward SDLC handoff. Includes manual-fallback guidance so the
  orchestrator is useful even before downstream skills are built.
