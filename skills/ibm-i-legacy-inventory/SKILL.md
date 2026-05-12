---
name: ibm-i-legacy-inventory
description: Inventory IBM i / AS400 legacy assets for modernization. Use when collecting or reviewing RPGLE, CLLE, COBOL, DDS, DB2 for i, jobs, screens, reports, spool, and runtime evidence before generating an evidence-backed spec.
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

- Do not invent libraries, programs, files, fields, jobs, reports, or calls.
- If a referenced object is not present, create a TBD instead of filling it in.
- Do not infer business rules from inventory alone.
- Do not treat source comments as truth without evidence or SME review.
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
skills/ibm-i-legacy-inventory/SKILL.md
```

Runtime copies may be synced to:

```text
.claude/skills/ibm-i-legacy-inventory/SKILL.md
.opencode/skills/ibm-i-legacy-inventory/SKILL.md
.agents/skills/ibm-i-legacy-inventory/SKILL.md
.codex/skills/ibm-i-legacy-inventory/SKILL.md
```

Use `../../scripts/sync-skills.sh` to create or check runtime copies.

## Version History

- v0.1.0 (2026-05-13): Initial reference implementation for the Legacy Spec
  Factory review gate.
