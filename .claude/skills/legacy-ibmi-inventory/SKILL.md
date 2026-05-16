---
name: legacy-ibmi-inventory
description: Inventory IBM i / AS400 legacy assets for modernization. Use when collecting or reviewing RPGLE, CLLE, COBOL, DDS, DB2 for i, jobs, screens, reports, spool, and runtime evidence before generating an evidence-backed spec. Layer 1 (platform-specific) skill of the Legacy Spec Factory reverse chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Inventory

## Purpose

Create a structured inventory of IBM i / AS400 legacy assets for one business
capability. This skill does not infer business rules and does not generate
Java. It establishes the evidence baseline required before deeper analysis or
`spec.yaml` generation.

## Inputs

Accept any combination of:

- source member listings or exported source files
- RPGLE, CLLE, COBOL, DDS source
- DB2 for i table and field metadata
- job descriptions, scheduler notes, or CL command flow
- DSPF, PRTF, spool, report, and screen samples
- SME notes about known programs, files, jobs, reports, or hidden dependencies

If raw production evidence is present, stop and require redaction review using
`../../docs/data-collection-and-redaction.md`.

## Output Contract

Produce:

- `01_inventory/inventory.yaml`
- `01_inventory/object-map.md`
- `01_inventory/inventory-review-checklist.md`
- unresolved questions using `TBD-<SLUG>-<NNN>` IDs

Use the templates in:

- `templates/inventory.yaml`
- `templates/inventory-review-checklist.md`

Follow:

- `../../docs/id-conventions.md`
- `../../docs/evidence-and-knowledge-taxonomy.md`
- `references/output-contract.md`

Examples:

- `examples/redacted-customer-credit-check/`
- `examples/missing-artifact-negative-case/`

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required**: redacted evidence bundle (source members, DDS, DB2 metadata,
  job/scheduler notes, screen/spool/report samples), capability scope
  (name + slug + libraries + collection date), assigned SME owner.
- **Optional**: prior shop inventory spreadsheets, wiki references, vendor
  docs (treat as tier 3/4 hints, never as ground truth).
- **Readiness checks**: Redaction Gate has cleared each evidence item; no
  `sensitive: unknown`; capability slug stable; SME owner named.
- **Stop conditions**: raw production evidence is present without redaction;
  capability is "the whole application" (require a narrower slice); no SME
  owner assigned; ground-truth tier 1 source listings (`WRKOBJ` /
  `DSPOBJD` / source-member listings) are not available.

### Execution

- **Procedure**: see the Workflow section below (7 ordered steps).
- **Allowed inference**: cross-referencing a referenced object against the
  inventory; classifying object types from DDS/source headers; assigning
  evidence IDs.
- **Forbidden assumptions**: inventing libraries, programs, files, fields,
  jobs, reports, or calls; inferring business rules from inventory alone;
  treating source comments or prior spreadsheets as truth without tier-1
  verification.
- **TBD handling**: use `TBD-<SLUG>-<NNN>`. Distinguish `coverage_gaps`
  (artifact missing — a developer can fix) from `open_questions` (only an
  SME can answer) per `references/output-contract.md`.

### Output

- **Canonical artifacts**: `01_inventory/inventory.yaml`,
  `01_inventory/object-map.md`,
  `01_inventory/inventory-review-checklist.md`.
- **Required fields/sections**: capability metadata, evidence ledger, object
  inventory, relationship map, `coverage_gaps`, `open_questions`,
  `sme_review`.
- **Required IDs**: `OBJ-*` for every object; `EV-*` for every evidence
  item; `TBD-*` for every gap or open question. No `BR-*`, `BEH-*`, or
  `DEC-*` minted here.
- **Handoff status**: `sme_review.decision` must be `approved` or
  `approved_with_non_blocking_tbd` before downstream skills run; `blocked`
  halts the chain.

### Validation

- **Mechanical**: every object has `id`, `evidence_ids`, and a non-`unknown`
  sensitivity; every relationship resolves to two `OBJ-*`; every TBD
  carries a category; required files exist.
- **AI semantic**: object scope matches the capability slug; no inferred
  business rules sneaking into `notes`; comments/spreadsheets cited as
  hints, not as ground truth; PRTF/DSPF/PF/LF/job/subroutine gaps surfaced
  as TBDs rather than smoothed over.
- **SME / human approval**: SME records `sme_review.decision`, signed-off
  object coverage, hidden-dependency confirmation, report/spool
  confirmation, sensitivity confirmation.
- **Blocking conditions**: any object lacks an ID or evidence link; any
  `sensitive: unknown` remains; SME marks `decision: blocked`; any
  `coverage_gaps` entry with `blocking: yes` is unresolved.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with status
`pass`, `pass_with_warnings`, or `blocked` when reporting upward to the
orchestrator.

## Workflow

1. **Define capability scope**
   Identify the business capability name, slug, source libraries, date of
   collection, and known SME owner. If the scope is a whole application, ask
   for a narrower slice.

2. **Classify input evidence**
   Assign evidence IDs to each source bundle, metadata export, report sample,
   spool sample, job log, screen sample, and SME note. Mark sensitivity as
   `yes`, `no`, or `unknown`.

3. **Inventory legacy objects**
   Extract or list programs, service programs, CL commands, PF, LF, DSPF, PRTF,
   jobs, reports, data areas, data queues, message queues, copybooks, and
   external interfaces.

4. **Capture relationships**
   Record known or observed relationships:

   - program calls
   - file usage
   - display file usage
   - printer file usage
   - submitted jobs
   - external calls
   - control tables
   - data areas and queues

5. **Identify coverage gaps**
   Create TBDs for missing DDS, missing PRTF, unresolved called programs,
   unknown job flow, unclear screen/report artifacts, or sensitive evidence
   awaiting redaction.

6. **Prepare SME review**
   Generate an inventory review checklist that asks the SME to confirm object
   coverage, hidden dependencies, critical reports, and missing runtime
   evidence.

7. **Gate the output**
   Do not mark the inventory `approved` unless:

   - every listed object has an ID
   - every object links to evidence or SME confirmation
   - missing objects are explicit TBDs
   - sensitivity is not `unknown`
   - PRTF, DSPF, PF/LF, job, and deep subroutine gaps are called out

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md`. The
inventory enumerates objects that actually exist in the production
library — confirmed via current `WRKOBJ` / `DSPOBJD` / source-member
listings (tier 1). Prior inventory spreadsheets, shop catalogs, wikis,
and SME recollection are starting points (tier 3/4); every entry must
be verified against tier 1 before being recorded.

- Do not invent libraries, programs, files, fields, jobs, reports, or calls.
- If a referenced object is not present in current production, create a TBD instead of filling it in (it may be deprecated, renamed, or never have existed).
- Do not infer business rules from inventory alone.
- Do not treat source comments as truth without tier-1 verification or SME review.
- Keep `observed`, `inferred`, and `unknown` separate.

## SME Review Questions

Ask the SME to confirm:

- Are all expected programs and called routines listed?
- Are any CL-submitted jobs, job scheduler entries, or overrides missing?
- Are all PF/LF, DSPF, and PRTF objects accounted for?
- Are there control files, data areas, data queues, or message queues?
- Are reports and spool outputs tied to the correct printer files?
- Are there shop-specific naming conventions or copybooks that affect analysis?
- Which missing items block downstream program analysis or spec generation?

## Runtime Portability

The canonical skill source lives under:

```text
skills/legacy-ibmi-inventory/SKILL.md
```

Runtime copies may be synced to:

```text
.claude/skills/legacy-ibmi-inventory/SKILL.md
.opencode/skills/legacy-ibmi-inventory/SKILL.md
.agents/skills/legacy-ibmi-inventory/SKILL.md
.codex/skills/legacy-ibmi-inventory/SKILL.md
```

Use `../../scripts/sync-skills.sh` to create or check runtime copies.

## Version History

- v0.1.0 (2026-05-13): Initial reference implementation for the Legacy Spec
  Factory review gate.
