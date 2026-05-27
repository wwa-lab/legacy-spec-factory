---
name: legacy-flow-context-normalizer
description: Normalize scattered legacy documentation in Visio, Word, Excel, PDF, PowerPoint, exported diagrams, RAG summaries, and SME notes into draft four-view module flows: Operation / Business Flow, System Flow, Program Flow, and Data Flow. Use when a team has historical documents that do not yet conform to the Legacy Spec Factory four-flow standard and needs a traceable SME review package before `legacy-module-context-intake`, `legacy-ibmi-module-analyzer`, or BRD generation. Blocks on unknown evidence authorization, missing module scope, unsupported opaque files with no readable export, hidden contradictions, or attempts to treat draft extracted flows as approved business rules.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Flow Context Normalizer

## Purpose

Turn scattered historical documentation into a **draft, evidence-linked
four-flow review package**:

```text
00_context_packages/<MODULE-SLUG>/flow-normalization/
|-- flow-context-index.yaml
|-- source-document-index.yaml
|-- 01-operation-business-flow.md
|-- 02-system-flow.md
|-- 03-program-flow.md
|-- 04-data-flow.md
|-- evidence-map.md
|-- contradiction-log.md
|-- open-questions.md
`-- sme-review-pack.md
```

This skill is the upstream bridge for teams whose knowledge is trapped in
Visio, Word, Excel, PDF, PowerPoint, exported screenshots, old process decks,
runbooks, or SME notes. It makes the material reviewable, but it does **not**
approve flows, mint final `BR-*` rules, or generate a BRD.

## Boundary

Use this skill before `legacy-module-context-intake` when the team does **not**
yet have SME-reviewed four-view module context.

Do not use it as a replacement for:

- `legacy-ibmi-evidence-intake` when raw source/runtime evidence authorization
  or redaction is unresolved.
- `legacy-module-context-intake` when the four flows are already
  SME-reviewed or explicitly supplied as human-confirmed context.
- `legacy-ibmi-flow-analyzer` when the task is source-backed call-chain
  analysis across IBM i programs.
- `legacy-brd-writer` when the user wants the BRD; BRD generation requires
  approved module context first.

## Required Inputs

- Module slug, business name, draft scope statement, and owner or SME role.
- One or more source documents or exported readable forms:
  - Visio / diagram exports (`.vsdx`, PDF, SVG, PNG, or image export)
  - Word / runbook / procedure docs
  - Excel / CSV process, application, interface, data dictionary, or CRUD lists
  - PDF / PPT / PPTX decks
  - RAG or code-knowledge summaries
  - SME notes, meeting notes, or annotated screenshots
- Evidence authorization signal for every source:
  - approved evidence manifest,
  - synthetic / non-production / public classification, or
  - explicit owner approval for agent review.

## Stop Conditions

Stop and produce only blocking findings if any apply:

| Condition | Route |
| --- | --- |
| Any source/runtime evidence has unknown sensitivity or missing authorization | `legacy-ibmi-evidence-intake` |
| Confidential or production evidence needs redaction and no approved redaction exists | `legacy-ibmi-evidence-intake` |
| Module slug, business name, or scope is missing | module owner / SME clarification |
| A proprietary binary file cannot be read and no export is supplied | request PDF/SVG/PNG/CSV/text export |
| Documents appear to cover multiple modules and the boundary is unclear | SME boundary decision |
| Contradictions are found but the user asks to hide or smooth them over | block; keep `contradiction-log.md` visible |
| Draft flows are requested as approved rules, approved module context, or BRD input without SME review | block; route through SME review first |

## Output Contract

Use `references/output-contract.md` for required fields and examples. Start
from the templates under `templates/`.

For deterministic local validation, run:

```bash
python3 skills/legacy-flow-context-normalizer/scripts/validate_flow_context_package.py \
  00_context_packages/<MODULE-SLUG>/flow-normalization
```

The package status in `flow-context-index.yaml` must be one of:

- `draft_needs_sme_review`
- `ready_for_context_intake`
- `ready_with_warnings`
- `blocked_pending_evidence`
- `blocked_pending_scope`
- `blocked_pending_readable_source`
- `blocked_pending_contradiction_review`

Allowed handoff:

- `draft_needs_sme_review` -> SME review or `legacy-sme-review-facilitator`
- `ready_for_context_intake` / `ready_with_warnings` -> `legacy-module-context-intake`
- any `blocked_*` -> do not route downstream; record exact remediation in
  `open-questions.md` and `flow-context-index.yaml`

## Step Contract

This skill conforms to the Legacy Spec Factory Step Contract.

### Input

- **Required**: module identity, source document list, evidence authorization,
  and enough readable content to identify at least one candidate flow view.
- **Optional**: existing RAG output, ARCAD / application inventory extracts,
  data dictionary exports, screen/report samples, meeting notes, known SME
  owner, and reviewed module glossary.
- **Input readiness scoring**:
  - `0-5 blocked`: evidence authorization unresolved, module scope missing,
    source files unreadable with no export, or all documents out of scope.
  - `6 minimum_pass`: module identity, authorized readable documents, and at
    least one flow candidate are present.
  - `7-8 usable`: documents cover most of the four views, with visible source
    provenance, gaps, and contradictions.
  - `9-10 strong`: each view has multiple corroborating sources, data
    dictionary or interface context is present, and SME owner is assigned.

### Execution

- **Procedure**: follow the Workflow below.
- **Allowed inference**: classify document fragments into the four views;
  normalize labels; create candidate flow steps from supplied document content;
  connect repeated system, program, file, and actor names across sources when
  evidence is visible.
- **Forbidden assumptions**: inventing actors, systems, programs, file names,
  field meanings, sequence order, trigger timing, exception handling, manual
  workarounds, business rules, SLAs, or modernization decisions.
- **ID policy**: may mint `DOC-*`, `FRAG-*`, `STEP-*`, `SYS-*`, `PGM-*`,
  `DATA-*`, `CAND-*`, `CONFLICT-*`, and `TBD-*` within the draft
  package. Do not mint final `BR-*`, `CAP-*`, `DEC-*`, `AC-*`, or `TC-*`.

### Output

- **Canonical directory**:
  `00_context_packages/<MODULE-SLUG>/flow-normalization/`.
- **Required files**: the ten files listed in Purpose.
- **Required gates**: evidence authorization, readable source, module scope,
  four-view coverage, contradiction visibility, SME review, and no rule
  promotion.
- **Handoff status**: only `ready_for_context_intake` and
  `ready_with_warnings` may feed `legacy-module-context-intake`.

### Validation

- **Mechanical**: all required files exist; the index lists every input and
  output; every view file has status, summary, evidence-linked flow steps,
  candidate seeds, and gaps; every evidence ID referenced by a view appears in
  `evidence-map.md`.
- **Semantic**: no draft flow is presented as approved; contradictions are not
  hidden; View 1 uses business language first; View 2 captures system and
  integration behavior; View 3 captures application/program/job behavior;
  View 4 captures data movement and ownership questions.
- **SME / human approval**: SME or accountable owner confirms module boundary,
  flow sequence, missing or obsolete documents, exception behavior, manual
  steps, and which contradictions block context intake.
- **Blocking conditions**: authorization gap, unreadable required source,
  module boundary ambiguity, hidden contradiction, missing evidence links for
  major flow steps, or absent SME decision when package claims readiness.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with status
`pass`, `pass_with_warnings`, or `blocked` when reporting upward to the
orchestrator.

## Workflow

1. **Resolve module identity**
   - Confirm `MODULE-SLUG`, business name, scope statement, owner, and SME role.
   - If one document bundle covers multiple modules, split or block until SME
     assigns boundaries.

2. **Gate evidence authorization**
   - Check source sensitivity, redaction, and owner approval before reading
     content.
   - If **any** source has unknown authorization, route the entire package to
     `legacy-ibmi-evidence-intake`. Do not proceed with only the authorized
     subset; authorization must be resolved for every document before
     normalization begins.
   - Exception: if an unauthorized document is clearly out of scope and the
     owner explicitly confirms it can be excluded, set its `readable_status` to
     `not_needed`, record the exclusion in `open-questions.md`, and proceed
     with the remaining authorized documents.

3. **Inventory source documents**
   - Create `source-document-index.yaml`.
   - Assign stable `DOC-*` IDs and record path, format, readable extraction
     method, sensitivity, owner, date, and confidence.
   - Follow `references/source-classification.md` for format-specific notes.

4. **Extract candidate fragments**
   - Extract only enough content needed for flow normalization.
   - Mint `FRAG-*` IDs for relevant diagram nodes, table rows, paragraphs,
     slide elements, or SME notes.
   - Preserve page, sheet, slide, row, shape, or section references.

5. **Classify fragments into four views**
   - Operation / Business Flow: actors, BAU sequence, approvals, manual steps,
     exceptions, customer or operational outcome.
   - System Flow: upstream/downstream systems, interfaces, batches, queues,
     files, schedules, security/SLA hints.
   - Program Flow: applications, menus, jobs, programs, call hints, trigger
     points, technical branching.
   - Data Flow: files/tables, business data objects, fields, read/write/update
     direction, derivation, retention, ownership.

6. **Draft each view**
   - Use `templates/view-template.md`.
   - Keep every major step evidence-linked and marked `needs_sme_review`.
   - Put technical names in `Evidence Basis` when the view is business-facing.

7. **Build evidence map**
   - Use `templates/evidence-map.md`.
   - Map every `DOC-*` / `FRAG-*` / source row to the views that use it.

8. **Carry contradictions and gaps**
   - Use `templates/contradiction-log.md` and `templates/open-questions.md`.
   - Keep obsolete-document signals visible rather than deleting them.
   - Ask SME to decide whether a contradiction is blocking, obsolete, or a real
     alternate path.

9. **Prepare SME review package**
   - Use `templates/sme-review-pack.md`.
   - Group questions by view and prioritize blockers first.
   - Include explicit approval choices; do not ask SME to review raw dumps.

10. **Set handoff status**
    - `draft_needs_sme_review` when flow content is usable but SME decision is
      not recorded.
    - `ready_for_context_intake` only when SME review confirms the four flows
      or accepts non-blocking TBDs.
    - `ready_with_warnings` only when unresolved items are explicitly
      non-blocking and carried into `open-questions.md`.
    - `blocked_*` when a downstream skill would need to invent facts.

11. **Validate**
    - Run the bundled validator:
      ```bash
      python3 skills/legacy-flow-context-normalizer/scripts/validate_flow_context_package.py \
        --allow-draft 00_context_packages/<MODULE-SLUG>/flow-normalization
      ```
    - Fix every reported finding, then re-run until the validator outputs
      `OK: flow context package is structurally valid`.
    - Do not route to SME review or context intake until the validator passes.

## Handoff

After SME approval, run `legacy-module-context-intake` with:

- the four flow files from this package,
- `evidence-map.md`,
- `contradiction-log.md`,
- `open-questions.md`,
- `sme-review-pack.md` or the recorded SME decision log,
- evidence authorization metadata.

Do not hand this package directly to `legacy-brd-writer`.

## Version

- v0.1.0 (2026-05-27): Initial document-to-four-flow normalization skill.
