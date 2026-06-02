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

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Creates an evidence-backed technical analysis of one RPGLE, CLLE, or COBOL program. |
| Input | One approved source program, its `OBJ-*` inventory entry, referenced DDS/copybooks, and optional runtime or SME notes. |
| Output | `program-analysis-<OBJ-ID>.md` covering call map, control flow, file I/O, external calls, and error handling. |
| Core prompt strategy | Extract concrete code behavior first, tag every inference, avoid business-rule invention, and stop on missing inventory/source. |
| Upstream skill | `legacy-ibmi-inventory`. |
| Downstream consumer | `legacy-ibmi-flow-analyzer`, `legacy-ibmi-module-analyzer`, data-model analysis, batch digest, and spec synthesis. |
| Validation standard | Program ID resolves in approved inventory, evidence tags are present, and all calls/files/errors are grounded in source. |
| Known risk | Inferring business intent from field or routine names without SME or runtime confirmation. |
| Practical example | Analyze `ORDENTR` RPGLE to document subroutines, PF/LF I/O, display-file indicators, and calls to credit-check programs. |

## Purpose

Create a detailed analysis of one IBM i program (RPGLE, CLLE, or COBOL)
documenting its RDi-style program call map, control flow, file I/O
operations, external calls, and error handling. This skill does not infer
business rules and does not generate modernization code. It produces
evidence-backed analysis ready for SME validation and downstream spec
generation.

## Inputs

Accept:

- One RPGLE, CLLE, or COBOL source file (the program to analyze)
- Optional: DDS copybook definitions (DSPF, PRTF, PF, LF) referenced by the program
- Optional: SME notes on entry points, quirks, or runtime behavior
- **Required:** Program must be referenced in an approved `01_inventory/inventory.yaml` via program ID (OBJ-*)

Stop and require clarification if:

- Program source is missing or incomplete (create a `blocked_pending_source`
  artifact or TBD routing note instead of guessing)
- Program is marked `blocked` in the inventory
- Program ID (OBJ-*) cannot be located in inventory
- Source contains raw, unredacted production data (require redaction review per `../../docs/data-collection-and-redaction.md`)

## Output Contract

Produce:

- `program-analysis-<OBJ-ID>.md` per program (one file per analysis session)

Use:

- `templates/program-analysis.md` as starting point
- `references/output-contract.md` for field definitions and evidence tagging
- `references/large-program-analysis.md` for large-program, segmented, and context-window-safe analysis
- `references/control-flow-patterns.md` for language-specific pattern recognition
- `references/error-handling-taxonomy.md` for error detection
- `references/evidence-tagging.md` for evidence strength levels and tagging methodology
- `templates/evidence-tags.md` as a quick reference card for inline evidence annotation

Follow:

- `../../docs/id-conventions.md` for stable IDs (OBJ-*, EV-*, TBD-*)
- `../../docs/evidence-and-knowledge-taxonomy.md` for evidence strength labels
- `../../docs/input-readiness-rubric.md` for input readiness scoring

Examples:

- `examples/simple-crud-rpgle/` — straightforward CRUD program, high-confidence analysis
- `examples/complex-batch-job/` — multi-subroutine batch job, moderate complexity
- `examples/incomplete-source-negative/` — negative case: missing source, TBD handling

## Step Contract

This skill is one step in the Legacy Spec Factory reverse chain. It conforms
to the canonical Step Contract shape — see
`../legacy-step-contract/SKILL.md` and
`../legacy-step-contract/references/step-contract.md` for the full
field-level rules. The summary below is normative for this skill.

### Input

- **Required**: one RPGLE / CLLE / COBOL source program; the program's
  `OBJ-*` ID located in an `approved` (or
  `approved_with_non_blocking_tbd`) `01_inventory/inventory.yaml`.
- **Optional**: DDS copybook source (DSPF, PRTF, PF, LF) for files the
  program touches; SME notes on entry points, quirks, or runtime behavior.
- **Input readiness scoring**:
  - `0-5 blocked`: program source missing/incomplete, `OBJ-*` not found,
    inventory status blocked, or evidence authorization unresolved.
  - `6 minimum_pass`: one current program source and its approved inventory
    `OBJ-*` link are present; missing copybooks/runtime details become TBDs.
  - `7-8 usable`: referenced DDS/copybooks and object metadata are available
    for most file and display/report interactions.
  - `9-10 strong`: runtime logs, screen/report samples, SME notes, known
    edge cases, and parameter/interface notes are also supplied.
  - Missing runtime samples or SME notes does not block static program
    analysis; it limits confidence for business meaning and exception realism.
- **Readiness checks**: Inventory Completeness Gate passing; program is
  not marked `blocked` in inventory; source is current production (tier 1)
  rather than archival; evidence authorization is resolved.
- **Stop conditions**: source missing or incomplete; program marked
  `blocked` in inventory; `OBJ-*` not found in inventory; raw unredacted
  production data present.

### Execution

- **Procedure**: see the Workflow section below (11 ordered steps).
- **Large-program mode**: when source is greater than 10,000 lines,
  contains more than 25 routines, contains more than 20 external calls,
  or cannot safely fit in context with evidence windows, use
  `references/large-program-analysis.md`. Do not produce whole-program
  business narrative until the source index, routine cards, Program Call
  Map, Data Touch Map, and coverage ledger exist.
- **Allowed inference**: control flow extracted from EXSR/CALL/PERFORM;
  calculations and branch logic from source statements; file I/O from
  F-spec and I/O statements; field lineage from visible assignments,
  DDS/copybooks, and parameter lists; error paths from MONITOR/
  MONMSG/ON-ERROR or explicit return/status checks; pattern-based
  labeling tagged `strongly_inferred` or `medium_confidence` with
  explicit notes.
- **Forbidden assumptions**: inventing subroutines, file access beyond
  what I/O statements show, business meaning from field names, external
  call parameters absent from source or copybooks, error codes not
  explicitly caught or returned; reading non-redacted evidence.
- **TBD handling**: missing DDS → `TBD: pending_source`; undefined
  subroutine reference → `TBD: pending_source`; unclear error path →
  `TBD: pending_sme_judgment`; non-blocking gaps tagged `non_blocking`.

### Output

- **Canonical artifact**: `program-analysis-<OBJ-ID>.md` (one per program).
- **Required sections**: `Metadata`, `Analysis Coverage & Scope`,
  `Program Call Map`, `Routine Cards`, `Routine Logic Details`,
  `Validation Logic`, `Deep Read Windows`, `Entry Points & Parameters`,
  `Object Dependencies`,
  `Logic Decomposition Ledger`, `Data Touch Map`,
  `Key File & Field Logic`, `Control Flow`, `File I/O`,
  `External Calls`, `Error Handling`, `Redundancy Candidate Notes`,
  `TBDs & Blocking Status`, `Review Checklist`.
- **Required IDs**: reuses `OBJ-*` and `EV-*` from inventory; mints
  program-local `BEH-*`, `EX-*`, and `TBD-*`. Does not mint `BR-*`,
  `CAP-*`, `DEC-*`.
- **Handoff status**: `status: draft` until SME review; `approved` or
  `approved_with_non_blocking_tbd` is required before
  `legacy-ibmi-flow-analyzer` runs against the chain that includes this
  program.

### Validation

- **Mechanical**: every non-trivial behavior has ≥1 `EV-*` link; every
  call/object reference resolves against inventory; every TBD has a
  blocking-status tag; required sections all present.
- **AI semantic**: behaviors are consistent with the linked source lines;
  no invented subroutines, fields, files, field mutations, message IDs,
  or error codes; evidence strength not overstated (no
  `weakly_inferred` posing as `confirmed_from_code`); flow header (if
  present) reconciled against the code-derived program call map.
- **Report quality**: Program Call Map uses compact `Visual Overview`
  plus auditable `Call Evidence`; key fields and variables preserve
  `FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning)
  [direction]; external/dynamic calls and error codes carry resolution
  status; unresolved items are centralized in TBDs / Open Items.
- **SME / human approval**: SME signs entry points, parameter contracts,
  file I/O semantics, external interface contracts, and error handling
  realism. Required when the program affects money, inventory,
  compliance, or customer status; recommended otherwise.
- **Blocking conditions**: any `BEH-*` without evidence; any invented
  IBM i fact; any unresolved `pending_source` TBD on a section that is
  load-bearing for the next flow analysis; SME absence when SME is
  required by the program's risk class.

Emit a Step Validation Report (see
`../legacy-step-contract/templates/step-validation-report.md`) with
status `pass`, `pass_with_warnings`, or `blocked` when reporting upward
to the orchestrator.

## Workflow

1. **Size & Structure Preflight**
   - Count approximate source lines, routine definitions, external calls,
     and object dependencies before writing business summary prose
   - Select analysis mode: `standard`, `segmented`, or `large_program`
   - For `segmented` or `large_program`, build the structure index before
     any business summary prose
   - Create Analysis Coverage & Scope and initialize the coverage ledger
   - Prevent claims of complete understanding until coverage supports
     them with indexed routines, deep-read windows, resolved call/data
     edges, and explicit gaps

2. **Select Program & Verify Inventory**
   - Accept program ID (OBJ-*) from approved `01_inventory/inventory.yaml`
   - Confirm program name, type (RPGLE / CLLE / COBOL), and library
   - Stop if program is marked `blocked` or inventory is not approved
   - Document source location and collection date

3. **Extract Entry Points & Parameters**
   - Identify main entry point (program parameter list, return value or status code)
   - Identify callable sub-procedures:
     - RPGLE procedures: Fixed-form `P ... B` / `P ... E` or free-form `dcl-proc` / `end-proc`; both callable via CALL statement
     - RPGLE subroutines: `BEGSR` / `ENDSR` blocks (internal subroutines, callable only from within same program)
     - CLLE: `SUBR` label blocks and `CALLSUBR` invocations (internal subroutines); external procedures via CALL
     - COBOL: ENTRY statements, PERFORM … UNTIL / VARYING
   - Document parameter types, expected ranges, and direction (input/output/both)
   - Tag with evidence: `confirmed_from_code` (from source headers or RPGLE specifications)
   - Create TBD if parameter contract is undocumented or unclear

4. **Trace Main Control Flow & Logic Ledger**
   - Document procedure call sequence (what calls what, in what order)
   - For every load-bearing mainline segment, subroutine, procedure, or
     paragraph, add **Routine Logic Details**. Load-bearing means the routine
     performs field calculation, validation, downstream-affecting branching,
     file mutation, external handoff, error/status assignment, display/report
     output, or queue/message interaction.
   - In Routine Logic Details, explain each routine's execution trigger,
     step-by-step logic, field calculations/assignments, branch outcomes,
     exits, and evidence. Do not summarize a routine as "validation logic" or
     "amount calculation" without target fields, operands, expressions,
     branch guards, precision/conversion notes, and business effect.
   - Within each Routine Logic Details subsection, add **Conditioned
     calculation blocks** for every guard-scoped calculation chain that affects
     money, percentage, quantity, status, return value, message/error code,
     persisted field, display/report field, queue payload, or downstream
     branch. In fixed-format RPG this includes conditioning indicators,
     named/numbered condition groups, result indicators, `IFxx` / `ELSE` /
     `ENDIF`, `CASxx`, `DO` scopes, and operation-level indicators. A block
     such as "Condition 5" must be analyzed as its own source-backed unit: list
     the guard, all guarded statements in order, each target assignment,
     intermediate variables, final output/error effect, and source line range.
     Do not hide these chains in a generic branch outcome or only in the
     Logic Decomposition Ledger.
   - Within each Routine Logic Details subsection, add **Outcome reverse
     traces** for every material message ID, status code, return code,
     response value, indicator-driven outcome, or error field produced by the
     routine. Start from the visible outcome (for example `UCC1852` or
     `W0BUR`), walk backwards to the exact branch/guard that sets or emits it,
     then continue backwards through the conditioned calculation block,
     comparison threshold, intermediate variables, and source operands/carriers
     that make the outcome true. A result such as `UCC1852` must not be left as
     "warning/reject condition" if the source shows a trigger chain such as
     `CAACOS/CAACCM/CATTHD/CATCAM/CAACLT -> WOOVAM -> WOACLT -> WOOVPE ->
     BBLSOP -> UCC1852`.
   - Within each Routine Logic Details subsection, connect calculated or
     assigned fields back to data carriers: source file/parameter/queue/screen
     field, intermediate work variables, output or persisted carrier, and the
     related Field Lineage / Field Mutation Matrix row when one exists.
   - Within each Routine Logic Details subsection, close routine-local
     exceptions: trigger, error/status/message fields, handling action,
     downstream skip/rollback/output, Validation Logic row, and evidence.
     If no exception path is observed for a routine, state `none observed`
     rather than leaving the closure implicit.
   - Identify conditional branching:
     - RPGLE: IF, SELECT, indicator-driven branching
     - CLLE: IF, ELSE, GOTO
     - COBOL: IF, EVALUATE, PERFORM … UNTIL
   - Identify loops and exit conditions (DO, DOWHILE, PERFORM, VARYING)
   - Build the **Logic Decomposition Ledger** for rules that must not be
     compressed into generic prose:
     - arithmetic operations (`ADD`, `SUB`, `MULT`, `DIV`, `EVAL`
       expressions) with source operands, result fields, and rounding or
       precision behavior
     - string construction (`CAT`, `MOVE`, substring operations) where it
       creates business identifiers, keys, or external payload fields
     - constants and literals used in limits, status values, rates,
       return codes, message IDs, flags, or branch decisions
     - single-condition, compound-condition, nested-condition, `SELECT` /
       `CASE`, and loop rules with explicit branch priority
   - Preserve condition order and nesting when it changes behavior. Do
     not flatten mutually exclusive tiers or fallback branches into
     unrelated bullet points.
   - Add **Routine / Window Data Flow** for every load-bearing routine or
     deep-read window: purpose, input variables, transformation logic,
     output variables, side effects, source lines, and evidence. Use
     `VARIABLE_NAME` (business meaning) [direction], and mark inferred or
     unresolved meanings explicitly.
   - Document handled vs. unhandled paths
   - Tag each non-trivial control structure: `confirmed_from_code` or `medium_confidence` if inferred
   - Create TBD for unclear program flow (missing subroutines, undefined labels)

5. **Build Program Call Map**
   - Treat the call map as the default entry view for every program,
     regardless of size. It should resemble an IBM RDi call-hierarchy
     view: routines and external boundaries connected by call edges,
     not a statement-level flowchart.
   - **First, look for a source-level flow header** at the top of the program. Many IBM i shops embed an ASCII tree comment like:
     ```
     Main line                Main flow control
     |-- SR990                First time initialization
     |-- SR100                Card validation
     |    |-- SR110           Currency conversion
     |    |    |-- SR111      Convert transaction amount
     ```
     If present, capture it verbatim — it is the program author's documented intent (tier 3 evidence per `../../docs/code-as-ground-truth.md`). Useful as a navigation aid, **not authoritative** when it disagrees with actual EXSR/CALL statements.
   - **Independently derive a program call map from code** by scanning
     for EXSR / CALLP / CALL / PERFORM / CALLPRC statements and
     BEGSR-ENDSR / BEGPR-ENDPR / paragraph definitions.
   - **Compare header vs. code-derived graph:**
     - If they match → tag `confirmed_from_code` (with source-level flow header as evidence)
     - If header exists but code differs → create TBD (comment drift, dead code, or missing subroutine)
     - If no header exists → use code-derived graph, tag `confirmed_from_code` (from EXSR/CALL/PERFORM statements)
   - Produce the required views (see `references/output-contract.md`):
     - **Visual overview** (RDi-style orientation graph; compact by design)
     - **Node inventory** (mainline, internal routines, procedures, external programs, APIs, queues, services)
     - **Call Evidence** (caller, callee, call type, condition, source
       lines, evidence source, and resolution status)
     - **Reverse caller index** (for each node, who calls it)
   - Use the wording `Evidence basis: source-level flow header + derived
     call analysis` when header and code-derived evidence are both used.
   - Treat dynamic calls as unresolved until a concrete target is proven
     from source, runtime evidence, inventory, or SME notes. Capture the
     target variable and assignment lines when available.
   - Identify hub/common candidates and orphaned routines. A hub/common
     label is structural only; do not promote it into a business service
     or modernization boundary without flow/module evidence and SME
     confirmation.

6. **List Object Dependencies (flat reference inventory)**
   - Match the shop's `F5-OBJREF TREE` output format: enumerate **every external object** referenced by the program, regardless of how it is used.
   - Object types to cover:
     - Files: PF (physical), LF (logical), DSPF (display), PRTF (printer)
     - Data: \*DTAARA (data area), \*DTAQ (data queue), \*MSGF (message file)
     - Programs: \*PGM (called program), \*SRVPGM (bound service program)
     - Source-level: Copybooks / `/COPY` directives, data-structure includes
   - Capture columns: object name, type, version (if shop tracks one), description, inventory ID (OBJ-\*), evidence
   - Cross-reference each entry against `01_inventory/inventory.yaml`:
     - If a matching OBJ-\* exists → link it
     - If not → create TBD: inventory gap (the inventory missed this object)
   - This section is the **flat parent list**; deeper per-object analysis happens in steps 7 (Data Touch Map + File I/O) and 8 (External Calls).
   - Tag: `confirmed_from_code` (visible in F-spec, D-spec, /COPY, or CALL statement)

7. **Document Data Touch Map, Key Fields & File I/O**
   - Build a program-local **Data Touch Map** before the detailed File
     I/O table. This is the data companion to the Program Call Map: it
     shows which routines touch which data carriers and where state
     enters, changes, leaves, or persists.
   - Track object / record / critical-field level movement. Do **not**
     enumerate every temporary RPG work variable.
   - Critical fields include money/amount fields, account/customer IDs,
     inventory quantities, approval/decline decisions, posting flags,
     status fields, return codes, error codes, audit IDs, and external
     message payload fields.
   - For every data carrier, capture:
     - carrier/object (PF, LF, DSPF, PRTF, `*DTAARA`, `*DTAQ`, `*MSGQ`,
       CALL parameter list, copybook/data structure, IFS file)
     - routine/procedure touching it
     - operation (read, write, update, delete, send, receive, parameter
       in/out/inout)
     - key/payload fields
     - state impact (`read-only`, `creates`, `updates`, `deletes`,
       `async send`, `async receive`, `external handoff`)
     - evidence and TBDs for unclear payload structure or direction
   - Build the **Key File & Field Logic** section:
     - classify each key file as driver, lookup/reference, state update,
       transaction/detail insert, audit/log, screen/report, queue/message,
       or parameter/data-structure carrier
     - classify each key field by role: access key, input, derived value,
       calculation operand/result, branch condition, status/flag,
       return/error code, message ID, external parameter, persisted field,
       or audit/output field
     - show field lineage for critical fields as
       `physical/source field -> alias/data structure -> work variable ->
       calculation/condition -> write-back alias -> persisted field`
     - preserve source identifiers and business meaning together:
       `FIELD_NAME` (business meaning). If one side is unresolved, write
       `field unresolved` (business meaning) or `FIELD_NAME` (meaning
       unresolved); mark inferred meanings inline.
     - preserve variable flow as `VARIABLE_NAME` (business meaning)
       [input/output/input-output/local/control]
     - create TBDs when DDS/copybook metadata is missing, physical-field
       mapping is unclear, or a variable participates in a critical path
       but its source cannot be proven
   - For each file from step 6 (PF / LF / DSPF / PRTF), classify operations:
     - Sequential read: READ (next record), READP / READPE (read previous)
     - Random read: SETLL (set lower limit), READE (read equal), CHAIN (random access)
     - Write operations: WRITE (add new record), UPDATE (modify record), DELETE
     - Display file: EXFMT (format + read interaction with DSPF for menus, input screens)
     - Embedded SQL / SQLRPGLE: EXEC SQL blocks, cursor operations, SQLCODE / SQLSTATE error handling
     - Note key fields used in each operation (e.g., CHAIN on CUSTID)
   - For every WRITE / UPDATE / DELETE / SQL mutation, produce a
     field-level mutation row that names:
     - record format and access key
     - branch condition that permits the mutation
     - fields assigned immediately before the mutation
     - source value, literal, expression, or copied field used for each
       persisted field
     - indicators, `%FOUND`, `%ERROR`, `SQLCODE`, `SQLSTATE`, or return
       codes checked before and after the mutation
     - a File Access Summary purpose using an action verb that explains
       why the file is accessed; do not use Purpose as a substitute for
       field descriptions
   - Reference file definitions from inventory via evidence ID (EV-\*)
   - Tag evidence: `confirmed_from_code` (from file specifications or I/O statements)
   - Create TBD if DDS is missing, key field unclear, or SQL schema is not documented

8. **Identify External Calls**
   - List all external program calls:
     - RPGLE: CALL, CALLP (procedure call)
     - CLLE: CALL, CALLPRC
     - COBOL: CALL, CICS, MQ, REST
   - List external service program calls (binding)
   - List external interfaces: IFS, HTTP, message queues, data queues
   - Document parameter contract if visible in source (call statement, copybook)
   - For dynamic calls, document the target variable, source lines where
     the target is assigned, parameters, resolution status (`resolved`,
     `partially_resolved`, `dynamic_unresolved`, `inferred`, `confirmed`),
     and any evidence gap.
   - Tag: `confirmed_from_code` (source statement visible) or `needs_sme_review` (undocumented)
   - Create TBD if external interface is unknown or network-dependent

9. **Document Error Handling**
   - List monitored errors:
     - RPGLE: MONITOR / ON-ERROR block, escape messages
     - CLLE: MONMSG (monitor message)
     - COBOL: ON ERROR, error flag checking
   - Document error codes and recovery paths (retry, log, return error)
   - Document logged errors or message writes (DSPLY, message queue, spool)
   - Document unhandled exceptions (crash, abort)
   - Build an **Exception Closure Ledger** that covers every observed
     business, parameter, and system I/O exception path. Each row must
     include trigger condition, message ID / error code / return code,
     detection mechanism, fields set, handling action (`RETURN`, `GOTO`,
     rollback, skip write, log, send message, continue), and downstream
     impact.
   - Build a front-loaded **Validation Logic** section immediately after
     Routine Logic Details and before Deep Read Windows. It must list every
     validation, status, response, return-code, message, indicator-driven
     outcome, and generic handler outcome observed in source or message-file
     references, including `CPF*`, `CPD*`, `MCH*`, `RNX*`, `SQL*`, shop-local
     `UCC*` / `LCC*`, and literal business error codes. Do not limit the
     inventory to shop-local message prefixes or bury it inside Error
     Handling.
   - Populate Validation Logic with Message / Status Code, Message
     Description, Validation / Error Type, Set By / Source Lines, Trigger
     Condition, Reverse Trigger Chain / Routine Logic Link, Output Carrier,
     Downstream Effect, and Evidence Status.
     Include status codes, response codes, indicator-driven error branches,
     exception/log output codes, data queue response status values, and
     message/status fields assigned during validation or file I/O failures.
   - Create one Validation Logic row per explicit message ID, status code, return
     code, response value, SQLSTATE, CPF/MCH/RNX/CPD message, user-defined
     code, or generic catch-all token. Do not group multiple message IDs into
     one row and do not replace individual descriptions with summary labels
     such as "validation messages" or "call-specific message IDs".
   - Populate Message Description from message files, source literals,
     comments, runtime evidence, vendor references, or SME notes. If the
     description is not available, write
     `unresolved - message description not available`, mark the row
     unresolved, and create a TBD / Open Item.
   - If literal code assignments cannot be fully traced, state
     `Validation logic unresolved:` with the concrete tracing gap.
   - For every material Validation Logic row, populate Reverse Trigger
     Chain / Routine Logic Link. This must point to the Routine Logic Details
     subsection, conditioned calculation block, outcome reverse trace, or
     source-backed TBD that explains why the code is set. Generic triggers such
     as "validation failed", "warning/reject condition", or "product/group
     control check" are not sufficient when source operands, comparisons, or
     intermediate calculations are visible.
   - When a catch-all handler is present (`MONMSG MSGID(*ANY)`, bare
     `ON-ERROR`, generic exception paragraph), mark it as generic
     coverage and still list the specific observed messages handled
     elsewhere. Do not infer specific message IDs from a generic handler.
   - Tag: `confirmed_from_code` (explicit error block) or `strongly_inferred` (pattern-based)
   - Create TBD if error handling is unclear or context-dependent

10. **Mark Redundancy Candidates Conservatively**
   - Do not delete or suppress code during program analysis.
   - Mark a move, assignment, temporary variable, branch, or routine as
     `candidate_redundancy: yes` only when it is not observed in any
     calculation, condition, file mutation, log/message, exception path,
     external output, parameter handoff, or persisted field lineage.
   - Use `candidate_redundancy: unknown` when downstream source,
     copybooks, DDS, or called-program behavior is missing.
   - Preserve the trace that proves the decision.

11. **Prepare for SME Review**
   - Consolidate all TBDs created in steps 3–10 with clear blocking status:
     - `pending_source` — missing DDS, incomplete source
     - `pending_sme_judgment` — behavior unclear from source alone
     - `non_blocking` — known gaps that don't affect downstream analysis
   - Add or preserve a centralized **Open Items / Limitations** table
     with Open Item, Impact, Evidence Gap, and Suggested Follow-up.
   - Generate review checklist for SME validation
   - Mark analysis as `blocked_pending_source` when missing or incomplete
     source prevents safe analysis; otherwise mark as `draft` (ready for
     review)
   - Gate: Analysis artifact is ready when every non-TBD behavior has an evidence_strength of `confirmed_from_code`, `strongly_inferred`, or `medium_confidence` (the latter two only when an SME review note is attached)

## Workflow State Write-Back

At the end of a program-analysis run, update
`<project-root>/workflow-state.yaml` per
[`docs/workflow-state-contract.md`](../../docs/workflow-state-contract.md).
Template: [`skills/legacy-modernization-orchestrator/references/state-writeback-snippet.md`](../legacy-modernization-orchestrator/references/state-writeback-snippet.md).

**Stage this skill produces:**

- `3b Program Analysis Done` when **every** in-scope program in
  `inventory.yaml` has an approved `program-analysis.md`
- `3a Program Analysis In Progress` when one or more in-scope programs
  still lack an analysis

**Last artifact path pattern:**
`02_programs/<MODULE-SLUG>/<OBJ-PROGRAM>/program-analysis.md`

**Writes per run:**

1. Overwrite `capabilities[<CAP-* from current_focus>]` with stage id,
   the path of the analysis you just saved, `last_skill:
   legacy-ibmi-program-analyzer`, and blocking IDs (`tbds`, `sme_pending`
   for any money / inventory / compliance branch awaiting SME).
2. Append one `history[]` entry with `note` naming the program analyzed
   (e.g. `"analyzed ORDENTR"`).
3. Overwrite `project.last_updated_at` / `project.last_updated_by`.

Never touch `current_focus`, other capabilities' entries, or past
`history[]` rows. A re-run on the same program is allowed; a re-run that
would lower `stage_id` requires the orchestrator's Rollback Protocol.

## Anti-Hallucination Rules

**Code is ground truth.** See `../../docs/code-as-ground-truth.md` for
the full principle. When source code disagrees with comments,
source-level flow headers, shop tool outputs, or SME recollection,
**the code wins** for behavioral claims. The disagreement itself
becomes a TBD asking the SME to confirm whether the secondary source
is stale or the code drifted from intent — but until then, the
analysis describes what the code actually does.

**Do NOT invent:**

- **Subroutine entry points** not directly visible in source (no inventing BEGPR blocks or subroutine labels)
- **File access** beyond what I/O statements (SETLL, READE, CHAIN, WRITE, UPDATE, DELETE) directly show
- **Business logic** from field names alone (e.g., a field named CREDLIMIT does not explain *why* the limit exists or how it's used)
- **External call parameters** if not visible in source headers, copybooks, or CALL statements
- **Error codes** if not explicitly caught or returned
- **Key-file roles, field lineage, or field mutations** when the source
  only proves a generic file reference
- **Message IDs** from generic handlers or message prefix conventions
  alone

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
- [ ] Program Call Map keeps a compact Visual Overview and a traceable Call Evidence table
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] Routine Logic Details explain every load-bearing routine/subroutine/procedure, including field calculations, carrier/lineage ties, routine-local exception closure, branch outcomes, exits, and evidence
- [ ] Routine Logic Details break out every material conditioned calculation block, including RPG conditioning indicators / condition groups such as `Condition 5`, with guarded statements, calculation order, target fields, intermediate variables, final output/error effect, and source evidence
- [ ] Routine Logic Details include outcome reverse traces from every material message/status/error/return outcome back to the branch guard, conditioned calculation block, comparison threshold, intermediate variables, and source operands/carriers that make the outcome true
- [ ] Logic Decomposition Ledger preserves calculations, constants, branch priority, loops, and CASE/SELECT behavior
- [ ] Routine / Window Data Flow shows variable-level input, transformation, output, side effects, source lines, and evidence
- [ ] Data Touch Map captures critical carriers, keys, payloads, and state impacts
- [ ] Key File & Field Logic preserves source identifiers with business meanings for key fields, aliases, work variables, calculations/conditions, and persisted fields
- [ ] File I/O Key Fields preserve source identifiers plus business meanings, and Purpose describes file access behavior
- [ ] File I/O field mutation matrix names which files and fields are written, updated, deleted, or skipped
- [ ] External and dynamic calls include caller routine, source lines, parameters, resolution status, purpose, and evidence
- [ ] Validation Logic is front-loaded after Routine Logic Details, has one row per message/status/return/response/generic outcome with message descriptions and reverse trigger chains, and Error Handling closes each exception path through return, rollback, skip, log, or downstream impact
- [ ] Inferred and unresolved calls, fields, variable meanings, and error codes are explicitly marked
- [ ] Code identifiers remain intact and readable in rendered tables/lists
- [ ] Redundancy candidates are conservative and do not remove hidden rules
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
  - 10-step workflow for RPGLE, CLLE, COBOL (with Program Call Map extraction and flat object-dependency listing)
  - Entry point extraction, control flow tracing, file I/O documentation
  - External call and error handling detection
  - Evidence tagging and TBD handling
  - SME review checklist
  - Positive and negative examples
- v0.2.0 (2026-06-01): Program-chain readiness tightening
  - Added Logic Decomposition Ledger, Key File & Field Logic, field-level File I/O mutation matrix, Exception Closure Ledger, and conservative redundancy candidate notes
  - Required every observed message ID / error code and every critical field lineage or mutation to carry evidence or a TBD
- v0.2.1 (2026-06-02): Evidence-first report format tightening
  - Renamed the Program Call Map tree-style subsection to auditable `Call Evidence`
  - Required source identifier + business meaning for key fields and variables
  - Added File I/O Purpose, external/dynamic call resolution status, Error Code Inventory, Routine / Window Data Flow, and centralized Open Items / Limitations
- v0.2.2 (2026-06-02): Error Code Inventory precision tightening
  - Required one Error Code Inventory row per explicit message ID, status code, return code, response value, SQLSTATE, or generic catch-all token
  - Renamed the inventory description column to `Message Description` and required description evidence or an unresolved TBD
  - Explicitly forbids grouped message-family summaries such as "validation messages" in place of per-message rows
- v0.2.3 (2026-06-02): Per-routine logic detail tightening
  - Added required Routine Logic Details for each load-bearing routine, subroutine, procedure, paragraph, or mainline segment
  - Required field calculation / assignment rows with target fields, expressions, operands, branch guards, precision/conversion notes, business effect, and evidence
  - Forbids compressing subroutine logic into generic summaries such as "validation logic" or "amount calculation"
- v0.2.4 (2026-06-02): Routine-local lineage and exception closure tightening
  - Added routine-local field lineage / carrier rows so calculations connect source carrier, intermediate variables, output/persisted carrier, and lineage/mutation references
  - Added routine-local exception closure rows for trigger, error/status/message fields, handling action, downstream skip/rollback/output, and Error Code Inventory link
  - Tightened subroutine output to match the program-single to program-chain principles for data-source preservation and exception closure
- v0.2.5 (2026-06-02): Conditioned calculation and outcome reverse-trace tightening
  - Required Routine Logic Details to break out material guard-scoped calculation chains, including fixed-format RPG conditioning indicators / named condition groups such as `Condition 5`
  - Requires guarded statement order, target assignments, intermediate variables, final output/error effect, source line range, and evidence for each material conditioned calculation block
  - Requires outcome reverse traces from material message/status/error outcomes back to branch guards, conditioned calculation blocks, comparison thresholds, intermediate variables, and source operands/carriers
  - Renamed the current output section from `Error Code Inventory` to front-loaded `Validation Logic`, placed immediately after Routine Logic Details
  - Forbids hiding condition-scoped calculation chains only in generic branch outcomes, Validation Logic summaries, or the Logic Decomposition Ledger
