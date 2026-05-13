---
name: legacy-ibmi-program-analyzer
description: Analyze individual IBM i programs (RPGLE, CLLE, COBOL) to extract control flow, file I/O, external calls, and error handling with evidence backing. Use when diving deep into one program's behavior from an approved inventory. Layer 1 (platform-specific) skill of the Legacy Spec Factory reverse chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Legacy Program Analyzer

## Purpose

Create a detailed analysis of one IBM i program (RPGLE, CLLE, or COBOL) documenting control flow, file I/O operations, external calls, and error handling. This skill does not infer business rules and does not generate modernization code. It produces evidence-backed analysis ready for SME validation and downstream spec generation.

## Inputs

Accept:

- One RPGLE, CLLE, or COBOL source file (the program to analyze)
- Optional: DDS copybook definitions (DSPF, PRTF, PF, LF) referenced by the program
- Optional: SME notes on entry points, quirks, or runtime behavior
- **Required:** Program must be referenced in an approved `01_inventory/inventory.yaml` via program ID (OBJ-*)

Stop and require clarification if:

- Program source is missing or incomplete (create TBD instead of guessing)
- Program is marked `blocked` in the inventory
- Program ID (OBJ-*) cannot be located in inventory
- Source contains raw, unredacted production data (require redaction review per `../../docs/data-collection-and-redaction.md`)

## Output Contract

Produce:

- `program-analysis-<OBJ-ID>.md` per program (one file per analysis session)

Use:

- `templates/program-analysis.md` as starting point
- `references/output-contract.md` for field definitions and evidence tagging
- `references/control-flow-patterns.md` for language-specific pattern recognition
- `references/error-handling-taxonomy.md` for error detection

Follow:

- `../../docs/id-conventions.md` for stable IDs (OBJ-*, EV-*, TBD-*)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence strength labels

Examples:

- `examples/simple-crud-rpgle/` — straightforward CRUD program, high-confidence analysis
- `examples/complex-batch-job/` — multi-subroutine batch job, moderate complexity
- `examples/incomplete-source-negative/` — negative case: missing source, TBD handling

## Workflow

1. **Select Program & Verify Inventory**
   - Accept program ID (OBJ-*) from approved `01_inventory/inventory.yaml`
   - Confirm program name, type (RPGLE / CLLE / COBOL), and library
   - Stop if program is marked `blocked` or inventory is not approved
   - Document source location and collection date

2. **Extract Entry Points & Parameters**
   - Identify main entry point (program parameter list, return value or status code)
   - Identify callable sub-procedures:
     - RPGLE: BEGPR / ENDPR blocks, callable subroutines
     - CLLE: subroutine labels, CALL targets within same source
     - COBOL: ENTRY statements, PERFORM … UNTIL / VARYING
   - Document parameter types, expected ranges, and direction (input/output/both)
   - Tag with evidence: `confirmed_from_code` (from source headers or RPGLE specifications)
   - Create TBD if parameter contract is undocumented or unclear

3. **Trace Main Control Flow**
   - Document procedure call sequence (what calls what, in what order)
   - Identify conditional branching:
     - RPGLE: IF, SELECT, indicator-driven branching
     - CLLE: IF, ELSE, GOTO
     - COBOL: IF, EVALUATE, PERFORM … UNTIL
   - Identify loops and exit conditions (DO, DOWHILE, PERFORM, VARYING)
   - Document handled vs. unhandled paths
   - Tag each non-trivial control structure: `confirmed_from_code` or `medium_confidence` if inferred
   - Create TBD for unclear program flow (missing subroutines, undefined labels)

4. **Document File I/O**
   - List all physical files (PF) and logical files (LF) accessed by the program
   - Classify operations per file:
     - Read operations: SETLL (set lower limit), READE (read equal), CHAIN (random access)
     - Write operations: WRITE (add new record), UPDATE (modify record), DELETE
     - Note key fields used in each operation (e.g., CHAIN on CUSTID)
   - Reference file definitions from inventory via evidence ID (EV-*)
   - Tag evidence: `confirmed_from_code` (from file specifications or I/O statements)
   - Create TBD if DDS is missing or key field unclear

5. **Identify External Calls**
   - List all external program calls:
     - RPGLE: CALL, CALLP (procedure call)
     - CLLE: CALL, CALLPRC
     - COBOL: CALL, CICS, MQ, REST
   - List external service program calls (binding)
   - List external interfaces: IFS, HTTP, message queues, data queues
   - Document parameter contract if visible in source (call statement, copybook)
   - Tag: `confirmed_from_code` (source statement visible) or `needs_sme_review` (undocumented)
   - Create TBD if external interface is unknown or network-dependent

6. **Document Error Handling**
   - List monitored errors:
     - RPGLE: MONITOR / ON-ERROR block, escape messages
     - CLLE: MONMSG (monitor message)
     - COBOL: ON ERROR, error flag checking
   - Document error codes and recovery paths (retry, log, return error)
   - Document logged errors or message writes (DSPLY, message queue, spool)
   - Document unhandled exceptions (crash, abort)
   - Tag: `confirmed_from_code` (explicit error block) or `strongly_inferred` (pattern-based)
   - Create TBD if error handling is unclear or context-dependent

7. **Prepare for SME Review**
   - Consolidate all TBDs created in steps 2–6 with clear blocking status:
     - `pending_source` — missing DDS, incomplete source
     - `pending_sme_judgment` — behavior unclear from source alone
     - `non_blocking` — known gaps that don't affect downstream analysis
   - Generate review checklist for SME validation
   - Mark analysis as `draft` (ready for review)
   - Gate: Analysis artifact is ready when every non-TBD behavior has an evidence_strength of `confirmed_from_code`, `strongly_inferred`, or `medium_confidence` (the latter two only when an SME review note is attached)

## Anti-Hallucination Rules

**Do NOT invent:**

- **Subroutine entry points** not directly visible in source (no inventing BEGPR blocks or subroutine labels)
- **File access** beyond what I/O statements (SETLL, READE, CHAIN, WRITE, UPDATE, DELETE) directly show
- **Business logic** from field names alone (e.g., a field named CREDLIMIT does not explain *why* the limit exists or how it's used)
- **External call parameters** if not visible in source headers, copybooks, or CALL statements
- **Error codes** if not explicitly caught or returned

**Instead:**

- If DDS is missing, create `TBD-<SLUG>-NNN: Confirm field meaning from [file-name] DDS`
- If subroutine is referenced but undefined, create `TBD-<SLUG>-NNN: Locate subroutine definition [name]`
- If error handling is unclear, tag `needs_sme_review` instead of inventing error recovery
- If external interface parameters are unknown, create `TBD-<SLUG>-NNN: Confirm parameter contract for [program-name]`

**Evidence minimum:**

- Every non-trivial behavior must have ≥1 evidence link, even if evidence_strength is low
- Do not document "likely" behavior without explicit evidence tag
- TBD questions count as evidence of a gap, not coverage

## SME Review Questions

The generated `program-analysis-<OBJ-ID>.md` must include a checklist. Before approval, SME must validate:

- [ ] Entry points are correct and complete (no missing callable subroutines)
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] File I/O matches job design (no hallucinated key fields or unobserved operations)
- [ ] External calls match system interfaces (especially for undocumented calls)
- [ ] Error handling aligns with production reliability requirements
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] Analysis contains no invented subroutines or undocumented file access

## Runtime Portability

Canonical source: `skills/legacy-ibmi-program-analyzer/SKILL.md`

Runtime adapters are synced via `scripts/sync-skills.sh`:

- Codex: `.codex/skills/legacy-ibmi-program-analyzer/SKILL.md`
- Claude Code: `.claude/skills/legacy-ibmi-program-analyzer/SKILL.md`
- OpenCode: `.opencode/skills/legacy-ibmi-program-analyzer/SKILL.md`

No runtime-specific assumptions are embedded in the canonical version.

## Version History

- v0.1.0 (2026-05-14): Initial release
  - 7-step workflow for RPGLE, CLLE, COBOL
  - Entry point extraction, control flow tracing, file I/O documentation
  - External call and error handling detection
  - Evidence tagging and TBD handling
  - SME review checklist
  - Positive and negative examples

