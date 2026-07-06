# Program Analysis: [Program Name] (OBJ-[ID] or unlinked)

## Program Reading Summary

Purpose: give IT SMEs a one-file reading entry before any routine ledger. This
section should explain the program by processing layer or theme, then point to
the main routines to understand first. For `standalone_exploratory` output,
state that no approved `OBJ-*` or `EV-*` trace IDs are asserted.

[Short technical reading summary of the program. Explain the main processing
layers and the safest first-pass reading order.]

| Processing Layer | Main Routines | What To Understand First |
| --- | --- | --- |
| [account/source setup, validation, calculation, persistence, exception, finalization layer] | `[MAIN]`, `[SRxxx] - [SRyyy]` | [reader-useful explanation of what this layer does and why it matters] |

Reading summary rules:

- Explain behavior by theme/layer before listing all routines.
- Keep the artifact one-file readable for SMEs; do not make sidecar links the
  only way to understand calculation, validation, exception, or routine logic.
- Preserve status honestly: `standalone_exploratory` / `draft_exploratory`
  outputs do not claim approved `OBJ-*` or `EV-*` linkage.

---

## Calculation Logic

Purpose: front-load the whole-program calculation and assignment logic that an
IT SME needs first. This section is a reviewer-facing index of the program's
material calculations. Start with reader-oriented themes, then include a
complete routine index. Detailed evidence remains in Routine Logic Details,
Logic Decomposition Ledger, Key File & Field Logic, and File I/O, all inside
this main review artifact.

| Calculation / Assignment | Target Field / Variable | Source Operands / Carriers | Guard / Branch | Output / Business Effect | Supporting Detail Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [amount / quantity / status / key / payload / return-value calculation] | `[FIELD_NAME]` (business meaning) | `[SOURCE_FIELD]`, `[WORK_VAR]`, constants, file/parameter carriers | [always / IF / SELECT / indicator / loop / exception guard] | [persisted field, returned value, downstream call parameter, display/report/queue output, status/message set] | [Routine Logic Details -> routine + conditioned block / Logic Decomposition row / Field Mutation row] | [EV-*] |

Calculation logic rules:

- Put the program's most important calculation chains here before metadata,
  including arithmetic, derived amounts, status/result assignments, key
  construction, message/status carriers, outbound payload fields, and persisted
  field updates.
- Keep this section whole-program and SME-readable. Do not bury a critical
  calculation only inside a routine-local subsection or a later ledger.
- Preserve source identifiers with meaning:
  ``FIELD_NAME`` (business meaning) and ``VARIABLE_NAME`` (business meaning).
- Every row must link to the deeper section that proves the chain. If operands,
  precision, branch priority, or persistence target are unclear, mark the row
  unresolved and create a TBD / Open Item.

**Calculation logic unresolved:** [state whether material calculations,
operands, precision/conversion, branch priority, or output carriers could not
be fully traced, or write "None."]

### Routine Index For Calculation Logic

| RLOG / Routine | Category | Reader-useful Detail |
| --- | --- | --- |
| RLOG-[PROGRAM]-NNN / `[ROUTINE]` | account setup / date derivation / fee calculation / pricing / persistence calculation / finalization | [specific calculation/assignment behavior this routine contributes] |

Routine index rules:

- Include one row for every RLOG declared in `routine-logic-details.yaml`.
- Keep RLOG numbering continuous and ordered.
- Do not use this table as a routine-only ledger; each row needs category and
  reader-useful detail.

---

## Validation Logic

Purpose: front-load the validation, status, return-code, message, and generic
handler outcomes so IT SMEs can find them immediately after the program's
calculation logic. Start with reader-oriented validation themes, then include a
complete routine index. Do not hide these rows later in the document.

| Message / Status Code | Message Description | Validation / Error Type | Set By / Source Lines | Trigger Condition | Reverse Trigger Chain / Routine Logic Link | Output Carrier | Downstream Effect | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `[CPFxxxx / UCCxxxx / literal / response 00 / status value]` | [message description from message file, source literal/comment, runtime evidence, or SME note; otherwise `unresolved - message description not available`] | validation_error / file_io_error / business_rule_error / external_call_error / data_queue_error / response_status / exception_log / unresolved | `[FIELD_NAME]` assignment, MONMSG, ON-ERROR, IF branch, lines [XX-YY] | [condition that sets or handles code] | [Routine Logic Details section + conditioned calculation block / outcome reverse trace / exception closure / source-backed TBD] | response DS / message field / status field / data queue message / exception-log file / return parameter / display-message API | [return, skip write, rollback, log, suppress downstream call, continue, abort] | confirmed / inferred / unresolved |

Validation logic rules:

- Create one row per explicit message ID, status code, return code, response
  value, SQLSTATE, CPF/MCH/RNX/CPD message, user-defined code, indicator-driven
  outcome, or generic catch-all token.
- Do not group multiple message IDs into one row and do not replace individual
  descriptions with family summaries such as "validation messages" or
  "call-specific message IDs".
- If one branch assigns several message IDs, duplicate the branch context and
  create one validation logic row for each message ID.
- `Message Description` must be the best available description from a message
  file, source literal, source comment, runtime trace, vendor reference, or SME
  note. If no description is available, write
  `unresolved - message description not available` and create an Open Item.
  This blocks final delivery until a message file/catalog/reference pack,
  source literal/comment, runtime evidence, or SME-approved description is
  supplied.
- Every material row must point back to Routine Logic Details with the exact
  conditioned calculation block or outcome reverse trace that explains why the
  outcome is reached. If the reverse trigger chain is not visible, mark it as
  unresolved and create a source-backed TBD.

**Validation logic unresolved:** [state whether status/message fields were
detected but literal assignments, descriptions, carriers, or reverse trigger
chains were not fully traced, or write "None."]

### Routine Index For Validation Logic

| RLOG / Routine | Category | Reader-useful Detail |
| --- | --- | --- |
| RLOG-[PROGRAM]-NNN / `[ROUTINE]` | control prerequisite / business-state gate / helper return validation / balance consistency / persistence validation / tolerated missing data | [specific validation, status, carrier, or trigger-chain behavior this routine contributes] |

Routine index rules:

- Include one row for every RLOG declared in `routine-logic-details.yaml`.
- Keep RLOG numbering continuous and ordered.
- Do not group Calculation, Validation, and Exception behavior into one
  routine-only ledger.

---

## Exception Handling

Purpose: front-load how the program handles business, parameter, I/O,
external-call, system, and generic exceptions. This is the whole-program
exception summary for IT SME first-read review; the detailed closure remains in
Routine Logic Details and the later Error Handling section. Start with
reader-oriented exception-flow themes, then include a complete routine index.

| Exception / Error Path | Trigger | Detection Mechanism | Fields / Messages Set | Handling Action | Downstream Effect | Supporting Detail Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [business / parameter / file I/O / SQL / external call / generic handler] | [condition, `%ERROR`, `%FOUND` false, MONMSG, ON-ERROR, return code, indicator] | [IF branch / MONITOR / MONMSG / ON-ERROR / status check / runtime evidence] | [message ID, status field, return code, error flag, log text] | RETURN / rollback / skip write / continue / abort / log / send message | [skipped update/call, rollback, output suppressed, caller response, operator message] | [Routine exception closure / Error Handling -> Exception Closure Ledger row / Validation Logic row] | [EV-*] |

Exception handling rules:

- Include every observed exception path, including generic catch-all handlers.
- Do not infer specific CPF/MCH/RNX/SQL or shop-local message IDs from a
  generic handler. Generic handlers get their own row with unresolved specifics.
- Every row must state whether the exception is closed by return, rollback,
  skip, continue, abort, log/message output, or downstream suppression.
- If the source shows a trigger but not the final handling effect, keep the row
  and create a TBD / Open Item.

**Exception handling unresolved:** [state whether any exception trigger,
message/status field, handling action, rollback/skip behavior, or downstream
effect could not be traced, or write "None."]

### Routine Index For Exception Handling

| RLOG / Routine | Category | Reader-useful Detail |
| --- | --- | --- |
| RLOG-[PROGRAM]-NNN / `[ROUTINE]` | local hard failure / file-operation failure / helper failure / delegated path / tolerated path / overflow routing / centralized return | [specific exception trigger, closure action, or return-routing behavior this routine contributes] |

Routine index rules:

- Include one row for every RLOG declared in `routine-logic-details.yaml`.
- Keep RLOG numbering continuous and ordered.
- Do not leave a finalized routine marked as a stale `not deep-read` gap after
  coverage/source-index shows it has been normalized.

---

## Message Inventory

Purpose: front-load a compact first-read summary of every observed message ID,
status value, return code, response literal, SQLSTATE, CPF/MCH/RNX/CPD message,
operator message, or shop-local message token. Detailed per-occurrence evidence
belongs in `message-inventory.md` / `message-inventory.yaml` for segmented,
large, or message-dense programs.

| Message / Code / Literal | Short Description | Type | Occurrences | Primary Routine(s) | First Seen / Set By | Trigger / Handler Summary | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `[CPFxxxx / UCCxxxx / literal / response 00 / status value / operator text]` | [specific short description from message file, approved reference pack, source literal/comment, runtime evidence, vendor reference, or SME note; otherwise `unresolved - message description not available`] | message / response_status / return_code / SQLSTATE / operator_message / generic_handler / unresolved | [count] | [routine list] | [line / assignment / handler] | [compact condition or handler summary] | [MSG-[PROGRAM]-NNN or `message-inventory.md#...`] |

Message inventory rules:

- Create one summary row for each explicit message/code/literal. Do not group
  message families or prefixes into a single row.
- If the same token appears multiple times, summarize it once with occurrence
  count and link to the detailed sidecar row.
- Preserve the exact code or literal as seen in source.
- If message text or business meaning is unavailable, write
  `unresolved - message description not available` and create an Open Item.
  Do not mark the analysis final-review-ready while any observed
  message/status/code row remains unresolved.
- If an approved reference pack supplies the description, cite the exact pack,
  file, and row/anchor. Do not use reference-pack text to invent a message that
  is not observed in source, runtime, or SME notes.
- Cross-reference the related Validation Logic and Exception Handling rows so
  reviewers can trace message meaning to trigger and closure.
- If there are more than 10 rows, or the program is segmented / large, keep this
  section compact and store full details in `message-inventory.md` and
  `message-inventory.yaml`.

**Message inventory unresolved:** [state whether any observed message/code
lacks description, source, carrier, trigger, or closure, or write "None."]

---

## Metadata

- **Program ID:** OBJ-[SLUG]-[NNN] | unlinked - inventory not provided
- **Program Name:** [SOURCE_PROGRAM_NAME]
- **Program Type:** RPGLE | CLLE | COBOL
- **Library:** [LIBRARY_NAME or "not recorded in inventory"]
- **Build Target:** [BUILD_LIBRARY/PROGRAM or "not recorded"]
- **Build / Library Evidence:**
  - [EV-[SLUG]-[NNN]: inventory/build/member evidence]
- **Reference Packs Used:**
  - [REF-PACK-ID or path: type, source format, normalized output, version, authorization status, owner]
- **Document Intake Manifests:**
  - [path to intake.manifest.yaml or "not used"]
- **Reference Lookup Coverage:**
  - Messages: [matched count / unresolved count]
  - Fields: [matched count / unresolved count]
  - Control values: [matched count / unresolved count]
- **Analysis Intent:** standalone_exploratory | chain_ready
- **Inventory Linkage:** linked | missing | blocked | not_applicable
- **Downstream Readiness:** ready_for_flow_after_approval | not_chain_ready | blocked_pending_source
- **Source Location:** [file path or collection ID]
- **Collection Date:** YYYY-MM-DD
- **Entry Points:** [List entry point names]
- **Files Accessed:**
  - `[FILE_NAME]` ([PF/LF/DSPF/PRTF/etc.])
- **Static Calls:**
  - `[PROGRAM_NAME]`
- **Dynamic Calls:**
  - `[VARIABLE_NAME]` -> `[RESOLVED_TARGET]` | dynamic_unresolved
- **Evidence IDs:**
  - [EV-[SLUG]-[NNN] or source-range/local-reference for standalone exploratory analysis]
- **Status:** draft_exploratory | draft | needs_sme_review | blocked_pending_source | approved | approved_with_non_blocking_tbd | rejected

Source reference rule:

- Do not use `file://`, `vscode://`, `command:`, `javascript:`, or
  `vscode-resource.vscode-cdn.net` links for source evidence. They are
  runtime-specific and often open incorrectly from VSCode previews or exported
  HTML.
- Prefer repo-relative Markdown links when the source file is inside the
  artifact package, for example `[CU101A.RPGLE](source/CU101A.RPGLE)`, plus
  explicit line ranges in the evidence column.
- If the source is outside the package or not safe to link, use plain text such
  as `CU101A.RPGLE lines 120-148` or an `EV-*` reference instead of a local
  filesystem URL.

## Analysis Coverage & Scope

Purpose: state how much source was available, how the analysis was scoped, and
which claims are fully supported versus indexed-only.

### Source Size & Strategy

| Source Lines | Analysis Mode | Mode Reason | Structure Index Built | Full Source In Context | Business Narrative Allowed |
| --- | --- | --- | --- | --- | --- |
| [N lines] | standard / segmented / large-program | [why this mode was selected] | yes / no | yes / no | yes / limited / no |

### Program Size Tier

| Program Size Tier | Tier Reason | Default Output Profile | Optional Sidecars Triggered |
| --- | --- | --- | --- |
| normal_program / complex_normal_program / large_extreme_program | [normal-size default / density reason / large threshold] | reader_first_lightweight_review / reader_first_plus_triggered_sidecars / full_index_and_batched_deep_read | [none / list triggered sidecars] |

### Coverage Ledger

| Routines Found | Routines Deep-Read | Routines Indexed Only | External Edges Resolved | Data Touches Resolved | Blocking Gaps | Non-Blocking Gaps |
| --- | --- | --- | --- | --- | --- | --- |
| [N] | [N] | [N] | [N/N] | [N/N] | [N] | [N] |

### Source Index Summary

| Mainline Segments | Subroutines / Procedures | External Calls | File Operations | Display / Report Operations | Commit / Rollback Points |
| --- | --- | --- | --- | --- | --- |
| [N] | [N] | [N] | [N] | [N] | [N] |

### Sidecar Indexes

| Sidecar | Use In Review | Status |
| --- | --- | --- |
| `message-inventory.yaml` | Machine-readable message/code/literal occurrence detail synchronized with the main Message Inventory | present / pending |
| `message-inventory.md` | Dense reviewer-readable message detail when more than 10 unique messages/status/codes appear | present / optional_triggered / not_written_by_default / pending |
| `routine-logic-details.md` / `routine-logic-details.yaml` | Consolidated audit/checkpoint routine detail and RLOG coverage source, synchronized with main Routine Logic Details | present / not needed / pending |
| `all-routine-coverage-ledger.md` / `deep-read-plan.md` | Batched deep-read planning when more than five windows or complex/large tier needs it | present / optional_triggered / not_written_by_default / pending |
| `file-io-inventory.md` / `file-io-inventory.yaml` | Dense or state-changing native file operation evidence behind File I/O summary rows | present / optional_triggered / not_written_by_default / pending |
| `field-mutation-matrix.md` / `field-mutation-matrix.yaml` | Native and SQL persisted mutation detail behind Calculation Logic and File I/O rows | present / optional_triggered / not_written_by_default / pending |
| `sql-inventory.md` / `sql-inventory.yaml` | SQLRPGLE/free-format embedded SQL statements, host variables, and status checks | present / optional_triggered / not_written_by_default / pending |

## Program Call Map

Purpose: RDi-style structural view of the program. This is a call map, not
a business-process diagram.

### Visual Overview

Evidence basis: source-level flow header + derived call analysis | derived call analysis only | header_only
Visual coverage: complete | main dispatch and high-impact branches only (shows [N] of [TOTAL] routines); complete routine inventory is in `routine-index.md`, Node Inventory, and Call Evidence.

```text
[PROGRAM] mainline
|-- SR100 [purpose / role]
|-- SR200 [purpose / role]
|   |-- SR210 [nested routine / helper]
|   |-- [EXTERNAL_PROGRAM] [external boundary / target]
|-- SR980 return / termination path
```

### Node Inventory

| Node | Node Type | Defined At | Role / Notes | Evidence |
| --- | --- | --- | --- | --- |
| [PROGRAM] | Mainline | lines [XX-YY] | entry orchestration | [EV-[SLUG]-[NNN]] |
| [SR_NAME] | Subroutine / Procedure | line [XX] | [hot path / utility / error handler / unknown] | [EV-[SLUG]-[NNN]] |
| [PROGRAM_NAME] | External Program / Service Program / API / DTAQ / MSGQ | call site line [XX] | external dependency | [EV-[SLUG]-[NNN]] |

**Hub / common candidates:**
- [NODE_NAME]: called by [N] callers; [reason this may matter]

**Orphaned subroutines/procedures:**
- [SR_NAME] -> TBD-[SLUG]-[NNN]: confirm whether dead code, callback entry, or shop convention

### Call Evidence

Evidence basis: source-level flow header + derived call analysis

| Caller | Callee | Call Type | Condition | Source Lines | Evidence Source | Resolution |
| --- | --- | --- | --- | --- | --- | --- |
| `[CALLER]` | `[CALLEE]` | mainline / subroutine / procedure / external_call / dynamic_call / service_program / data_queue / batch_job | always / in loop / only if X / first-time-only | lines [XX-YY] | flow_header / derived_code / flow_header + derived_code / header_only / derived_code_only | confirmed / inferred / unresolved / resolved / partially_resolved / dynamic_unresolved |

**Header vs. code:** matched | drift detected -> see TBD-[SLUG]-[NNN]

### Reverse Caller Index

| Node | Called By | Notes |
| --- | --- | --- |
| [SR_NAME] | [CALLER] [line] | [hot path / common utility / single callsite / etc.] |

---

## Routine Cards

Purpose: summarize every routine that affects calls, data, errors, state, or
external boundaries, including whether the routine was deep-read or only indexed.
SME confirmation belongs in evidence, review notes, or sign-off; it is not a
coverage value.

| Routine | Location | Called By | Calls Out | Data Touches | State Impact | Error Handling | Evidence | Coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [MAIN / SR_NAME / PROCEDURE] | lines [XX-YY] | [CALLER list] | [EXSR / CALL / CALLP / API list] | [files, data areas, queues, parameters] | read-only / creates / updates / deletes / boundary-state | [MONITOR / indicator / ON ERROR / none observed] | [EV-[SLUG]-[NNN]] | indexed_only / deep_read / blocked |

---

## Routine Logic Details

Purpose: explain the internal logic of each load-bearing subroutine, procedure,
paragraph, or mainline segment. For routine-dense programs, keep this main
section table-led and readable, but include complete RLOG headings and
reader-useful detail in `program-analysis.md`. Sidecars are audit,
checkpoint, and machine-readable sources; they are not the only SME reading
path.

| Routine | Role | Source Lines | Coverage | Deep Read Status | State Impact | Detail |
| --- | --- | --- | --- | --- | --- | --- |
| [MAIN / SR_NAME / PROCEDURE] | entry dispatch / state-changing routine / validation-message routine / external boundary / indexed utility | lines [XX-YY] | indexed_only / deep_read / blocked | pending / completed / blocked | read-only / creates / updates / deletes / external handoff / unknown | RLOG-[PROGRAM]-NNN |

Routine detail placement rules:

- `routine_count <= 25`: full Routine Logic Details may appear below in the
  main analysis.
- `routine_count > 25`: keep the main analysis table-led, but include one
  continuous, ordered `### RLOG-[PROGRAM]-NNN / [ROUTINE]` heading per RLOG
  declared in `routine-logic-details.yaml`, with enough detail for one-file SME
  reading.
- `routine_count > 80` or source lines > 10,000: split full human-authored
  semantic detail into `routine-logic-details/part-*.md` or
  `routine-logic-details/deep-read-batch-*.md` retained batch checkpoint files by
  mainline/dispatch, state-changing routines, validation/message routines,
  external boundaries, and indexed utilities.
- Each batch file must start with batch-scoped SME core logic:
  top-level `## Calculation Logic`, `## Validation Logic`, and
  `## Exception Handling` before per-routine detail, so SME reviewers see the
  core logic for that batch first. The full batch layout is fixed:
  `## Calculation Logic`, `## Validation Logic`, `## Exception Handling`,
  `## Scope`, `## Batch Coverage Summary`, `## Message Inventory`,
  `## Routine Details`. Message Inventory must list every exact
  message/status/literal observed in the batch as its own row.
- Batch core logic sections must not contain pasted source code, fenced code
  blocks, or verbatim RPG/CL/COBOL/SQL statements. Use source identifiers,
  normalized logic summaries, source ranges, evidence IDs, and `RLOG-*` links
  instead.
- Final SME review must happen in one consolidated `routine-logic-details.md`.
  After batch deep-read is complete, merge all `part-*.md` /
  `deep-read-batch-*.md` content into `program-analysis.md` and the final
  `routine-logic-details.md` with whole-program `## Calculation Logic`,
  `## Validation Logic`, `## Exception Handling`, `## Message Inventory`,
  `## Routine Detail Index`, and `## Routine Details` sections. Keep
  part/deep-read batch files as audit checkpoints, but do not leave them as the
  only review surface.
- This section must not collapse field calculations into generic labels such as
  "validation logic" or "amount calculation".

### RLOG-[PROGRAM]-NNN / `[ROUTINE_OR_PROCEDURE_NAME]`

**Execution trigger:** [called by / condition / loop scope / entry path]

**Step-by-step logic:**
1. [source-backed step, branch, loop, file access, assignment, or call]
2. [source-backed step]

**Field calculations and assignments:**

| Target Field / Variable | Calculation / Assignment | Source Operands | Branch / Guard | Precision / Conversion | Business Effect | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `[FIELD_NAME]` (business meaning) | [literal / move / expression / formula] | `[FIELD_A]` (meaning), constant `[X]` | [IF/SELECT/loop condition or always] | [rounding, scale, data type conversion, substring, padding, N/A] | [returned, persisted, passed, error/status set, display/report output] | [EV-*] |

**Conditioned calculation blocks:**

| Block / Guard | Guard Type | Source Range | Guarded Statement Order | Calculation Chain | Final Output / Error Effect | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [Condition 5 / indicator combo / IF / ELSE / CASE / loop scope] | RPG conditioning indicator / named condition group / IF / ELSE / CASE / loop / CL IF / COBOL IF/EVALUATE | lines [XX-YY] | [1. statement/opcode; 2. statement/opcode; 3. branch/exit] | [`SOURCE_FIELD` -> `WORK_VAR` -> `TARGET_FIELD` -> message/status/output] | [returned status, persisted field, skipped update, error code, display/report/queue output] | [EV-*] |

**Outcome reverse traces:**

| Outcome Code / Field | Reverse Trigger Chain | Guard / Conditioned Block | Source Operands / Carriers | Downstream Effect | Cross-References | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [message ID / status value / return code / indicator / error field] | [`SOURCE_FIELD` -> `WORK_VAR` -> comparison / threshold -> outcome code] | [Condition 5 / IF / ELSE / CASE / loop / exception block] | [file fields, parameters, constants, work variables] | [skipped update, returned status, log/message, rollback, downstream call] | [Validation Logic row, Exception Closure row, Lineage row, TBD if unresolved] | [EV-*] |

**Routine field lineage / carriers:**

| Target Field / Variable | Source Carrier / Field | Intermediate Variables | Output / Persisted Carrier | Related Lineage / Mutation | Evidence |
| --- | --- | --- | --- | --- | --- |
| `[FIELD_NAME]` (business meaning) | `[FILE.FIELD]` / parameter / queue payload / display field / report field | `[WORK_VAR]` -> `[ALIAS]` | return parameter / `[FILE.FIELD]` / CALL parameter / message / queue / report | LIN-[SLUG]-[NNN] / mutation row / N/A-no persistence | [EV-*] |

**Branch outcomes:**

| Branch / Condition | Fields Set / Actions | Exit / Next Step | Evidence |
| --- | --- | --- | --- |
| [condition] | [assignments, calls, writes, skips] | [RETURN / EXSR / continue / loop / error path] | [EV-*] |

**Routine exception closure:**

| Exception / Guard | Trigger | Fields / Messages Set | Handling Action | Downstream Skip / Rollback / Output | Validation Logic Link | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [business / parameter / I/O / external-call / generic handler / none observed] | [condition, `%ERROR`, MONMSG, return code, indicator] | [ERR_FLAG, ERR_CD, ERR_MSG, TRANS_ERR, log/message fields] | RETURN / rollback / skip write / continue / abort / none | [skipped update/call, rollback, message queue, report, caller response] | [Message / Status Code row or N/A] | [EV-*] |

**Unresolved routine logic:** [None, or TBD references for unclear operands,
constants, branch priority, precision, called routine, or field meaning.]

## Deep Read Windows

Purpose: identify the source windows used to support high-risk claims,
state-changing behavior, and business narrative. For `standard` mode where the
full source was read in context, record one `full-source-read` window or mark
this section `N/A — full source read in context`; do not invent artificial
windows.

| Window ID | Source Range | Reason Selected | Routines Covered | Claims Supported | Evidence |
| --- | --- | --- | --- | --- | --- |
| WIN-[SLUG]-[NNN] | lines [XX-YY] or full-source-read | state change / external boundary / error path / high-risk branch / representative path / full-source-read | [routine list] | [claim IDs or short claim summary] | [EV-[SLUG]-[NNN]] |

---

## Entry Points & Parameters

| Entry Point | Type | Parameters | Return | Evidence |
| --- | --- | --- | --- | --- |
| [NAME] | Main Program / Callable Procedure / External Entry | (param1: type, param2: type) | [return type/code] | confirmed_from_code |

**Evidence links:**
- [EV-[SLUG]-[NNN]: Description]

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question]

---

## Object Dependencies

Source: shop F5-OBJREF TREE tool output | derived-from-code | both (matched)

### Uses (forward dependencies)

| Object | Type | Version | Description | Inventory ID | Evidence |
| --- | --- | --- | --- | --- | --- |
| [OBJ_NAME] | [PF / LF / DSPF / PRTF / *DTAARA / *DTAQ / *MSGF / *PGM / *SRVPGM / Copybook / PF (DS)] | [VERSION or —] | [Description] | OBJ-[SLUG]-[NNN] or TBD-[SLUG]-[NNN] | confirmed_from_code |

**Inventory gaps:**
- TBD-[SLUG]-[NNN]: object [NAME] referenced by program but not in inventory.yaml

### Used By (reverse dependencies)

From `01_inventory/inventory.yaml` `relationships` section.

| Caller     | Type   | Notes                          | Evidence |
| ---        | ---    | ---                            | --- |
| [CALLER]   | *PGM   | [description]                  | from inventory relationships |

---

## Logic Decomposition Ledger

Purpose: preserve calculations, constants, branch priority, loops, and CASE /
SELECT behavior before translating anything into business prose.

| Logic ID | Routine / Lines | Logic Type | Source Inputs / Constants | Operation / Condition | Result Field / Action | Branch Priority / Loop Scope | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LOG-[SLUG]-[NNN] | [SRxxx lines XX-YY] | arithmetic / string-build / precision / constant / IF / SELECT / loop | [fields, literals, constants] | [ADD/SUB/MULT/DIV/CAT/IF/WHEN/etc.] | [field set, return, call, write, skip] | [nested order, fallback, EOF scope] | [EV-*] |

### Routine / Window Data Flow

| Routine / Window | Purpose | Input Variables | Transformation Logic | Output Variables | Side Effects | Source Lines | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `[ROUTINE_OR_WINDOW]` | [business/technical purpose] | `[VARIABLE_NAME]` (business meaning) [input]<br>`[VARIABLE_NAME]` (business meaning) [control] | [maps, validates, calculates, branches, formats, or assigns values] | `[VARIABLE_NAME]` (business meaning) [output] | CHAIN `[FILE]` / WRITE `[FILE]` / CALL `[PROGRAM]` / send DTAQ response / none observed | lines [XX-YY] | [EV-*]; confirmed / inferred / unresolved |

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about operand source, constant meaning, branch priority, precision, or loop scope]

---

## Data Touch Map

Purpose: program-local data movement and state-change view. Track objects,
records, carriers, and critical fields; do not enumerate every temporary
working variable.

### Data Touches

| Data Object / Carrier | Mechanism | Operation | Routine / Procedure | Key / Payload | Critical Fields Touched | State Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `[FILE_NAME]` | PF / LF | CHAIN / READ / READE / WRITE / UPDATE / DELETE | `[SRxxx]` / procedure | key=`[FIELD_NAME]` (business meaning) | `[FIELD_NAME]` (business meaning) | read-only / creates / updates / deletes | [EV-*] |
| `[DTAARA_NAME]` | *DTAARA | IN / OUT / CHGDTAARA / RTVDTAARA | `[SRxxx]` / procedure | `[VALUE_OR_STRUCTURE]` | `[FIELD_NAME]` (business meaning) | reads shared state / updates shared state | [EV-*] |
| `[DTAQ_NAME]` | *DTAQ | SNDDTAQ / RCVDTAQ / QSNDDTAQ / QRCVDTAQ | `[SRxxx]` / procedure | `[MESSAGE_STRUCTURE]` | `[FIELD_NAME]` (business meaning) | async send / async receive | [EV-*] |
| `[CALL_TARGET]` | CALL parameters | in / out / inout | `[SRxxx]` / procedure | `[PARAMETER_LIST]` | `[FIELD_NAME]` (business meaning) | passes state across program boundary | [EV-*] |

### Critical Field Watchlist

| Field / Data Structure | Object / Carrier | Why It Matters | Observed Operations | Evidence |
| --- | --- | --- | --- | --- |
| `[FIELD_NAME]` (business meaning) | `[OBJECT]` | amount / status / customer / account / inventory / posting / approval / error code | read / written / compared / returned | [EV-*] |

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about payload structure, key field, direction, or state impact]

---

## Key File & Field Logic

Purpose: identify the files and fields that define the program's replayable
behavior: access keys, calculation inputs/results, branch drivers, error/status
fields, external parameters, and persisted fields.

Field and variable identity rule: every key field or variable must preserve
the source identifier plus business meaning when resolvable:
`FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning)
[direction]. Use `field unresolved` (business meaning), `FIELD_NAME` (meaning
unresolved), or `FIELD_NAME` (business meaning; inferred) when evidence is
partial.

### Key Files

| File / Carrier | Role in Program | Routines | Access / Mutation Pattern | Key Fields | Critical Persisted / Output Fields | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `[FILE_NAME]` | driver / lookup / state-update / detail-insert / audit-log / screen-report / queue-message / parameter-DS | `[SRxxx]` | [READ loop / CHAIN lookup / UPDATE / WRITE / DELETE / EXFMT / CALL inout] | `[FIELD_NAME]` (business meaning)<br>`[FIELD_NAME]` (business meaning) | `[FIELD_NAME]` (business meaning)<br>`[FIELD_NAME]` (business meaning) | [EV-*] |

### Key Fields

| Field / Data Structure | Source Object / Carrier | Role | Used In | Values / Domain Observed | Downstream Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `[FIELD_NAME]` (business meaning) | `[FILE]` / DS / parameter / work variable | access-key / input / derived / calculation-result / branch-condition / status-flag / return-code / error-code / message-id / external-parameter / persisted-field / audit-output | [routine, condition, mutation, call] | [literal/domain/range if visible] | [write, return, skip, error, external handoff] | [EV-*]; confirmed / inferred / unresolved |

### Field Lineage

| Lineage ID | Source / Physical Field | Alias / Data Structure | Work Variables | Calculation / Condition | Write-Back Alias | Persisted / Output Field | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIN-[SLUG]-[NNN] | `[FILE.FIELD]` (business meaning) or parameter | `[ALIAS_FIELD]` (business meaning) | `[VARIABLE_NAME]` (business meaning) [local] | [operation or branch] | `[ALIAS_FIELD]` (business meaning) | `[FILE.FIELD]` (business meaning) / message / call parameter | [EV-*] |

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about missing DDS/copybook, physical-field mapping, alias meaning, or critical-field source]

---

## Control Flow

Purpose: concise narrative derived from Program Call Map, Routine Cards, Logic
Decomposition Ledger, Data Touch Map, Key File & Field Logic, and Deep Read
Windows. Do not introduce new business facts here that are absent from the
evidence-backed sections above.

### Main Entry Point
1. [Step description] [evidence_strength]
2. [Step description] [evidence_strength]
3. [Conditional/Loop structure]
   - [Path 1 description]
   - [Path 2 description]
4. [Return or final step]

**Control structures observed:**
- [IF/SELECT/MONITOR description with line numbers]

**Evidence links:**
- [EV-[SLUG]-[NNN]: Source lines XX–YY]

### [Sub-Procedure Name]
1. [Step description]
2. [Step description]
3. [Return or final step]

**Error handling:** [Yes/No] — [Description if yes]

---

## File I/O

For file-I/O-dense or SQLRPGLE programs, keep this section as a compact
SME-readable summary. Link to `file-io-inventory.md`,
`field-mutation-matrix.md`, and `sql-inventory.md` detail IDs instead of
expanding every operation, assignment, or host variable inline.

### File Access Summary

| File | Record Format | Type | Operations | Key Fields | Purpose | Read / Mutation Conditions | Indicators / Status Checks | Detail | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `[FILE_NAME]` | `[FORMAT]` | PF / LF / DSPF / PRTF | SETLL, READE, CHAIN, WRITE, UPDATE, DELETE | `[KEY_FIELD]` (business meaning; `standard_field_id` if known)<br>`[KEY_FIELD]` (business meaning) | Validate / read / detect / write / send / log [specific file access behavior]. | [IF/loop/SELECT context] | [*INxx / %FOUND / %ERROR / SQLCODE / SQLSTATE] | FIO-[PROGRAM]-NNN / SQL-[PROGRAM]-NNN | [EV-* or reference pack row for meaning] |

### Field Mutation Matrix

| File | Operation | Routine / Lines | Access Key / Record Condition | Field Mutated / Persisted | Source Value / Expression | Assignment Evidence | Error / Rollback Handling | Detail |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `[FILE_NAME]` | WRITE / UPDATE / DELETE / EXEC SQL | `[SRxxx]` lines [XX-YY] | `[KEY_FIELD]` (business meaning; `standard_field_id` if known) and condition | `[FIELD_NAME]` (business meaning; `standard_field_id` if known) or record delete | literal / source field / calculation / moved value | [EV-* assignment lines] | [handler, message ID, return code, or unhandled] | MUT-[PROGRAM]-NNN |

**Operation details:**

- **[FILE_NAME] / [OPERATION] on [KEY]:** [Description of operation, fields assigned before mutation, indicators/status checks, result].

**Evidence links:**
- [EV-[SLUG]-[NNN]: Source lines / DDS reference]

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about file access or missing DDS]

---

## External Calls

| Program | Call Type | Caller Routine | Source Lines | Parameters | Resolution Status | Purpose | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `[PROGRAM_NAME]` or `[VARIABLE_NAME]` -> `[TARGET]` | external_call / dynamic_call / service_program / data_queue / batch_job | `[CALLER]` | lines [XX-YY] | `[PARAM_NAME]` (business meaning) [input/output/input-output] | resolved / partially_resolved / dynamic_unresolved / inferred / confirmed | [Purpose description grounded in call site and parameters] | [EV-[SLUG]-[NNN]] |

**Call details:**

- **[PROGRAM_NAME]:** [Description of parameters, return values, synchronous/asynchronous, known error handling, target variable assignment if dynamic].

**Parameter contracts:**
- [PROGRAM_NAME] expects [parameter description]. [Evidence or TBD status].

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about parameter contract, error handling, or availability]

---

## Error Handling

### Exception Closure Ledger

| Exception / Error Condition | Trigger / Source | Message ID / Error Code / RC | Detected By | Fields Set / Messages Sent | Handling Action | Downstream Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [Error type] | [condition, file op, call, SQL, validation] | [CPFxxxx / CPDxxxx / MCHxxxx / RNXxxxx / SQLCODE / UCC* / LCC* / literal code / none] | MONMSG / MONITOR ON-ERROR / %ERROR / indicator / IF / RC check / SQLSTATE | [ERR_FLAG, ERR_CD, ERR_MSG, log payload] | RETURN / GOTO / rollback / skip write / log / continue / abort | [blocks update, skips downstream call, returns status, continues] | [EV-*] |

### Validation Logic Cross-Reference

Validation/status/message code rows are front-loaded in `## Validation Logic`.
Every exception row with a message, status, return code, response value, or
generic handler must cross-reference that section through the visible code,
carrier, or source-backed TBD.

**Unhandled exceptions:**
- [Description of unhandled error conditions if any]

**Generic handlers:**
- [MONMSG *ANY / bare ON-ERROR / generic ERROR-HANDLER]: [coverage and limits; do not infer specific message IDs]

**Logged errors:**
- [Description of error logging, message queues, spool output]

**Evidence links:**
- [EV-[SLUG]-[NNN]: RPGLE MONITOR blocks / CLLE MONMSG / COBOL ON ERROR]

---

## Redundancy Candidate Notes

Purpose: mark possible redundancy without deleting or suppressing code facts.
Only mark `yes` when the candidate is not observed in calculation, condition,
file mutation, log/message, exception path, external output, parameter handoff,
or persisted field lineage.

| Candidate | Location | Candidate Redundancy | Reason | Trace / Last Observed Use | Evidence | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| [field / move / routine / branch] | [lines XX-YY] | yes / no / unknown | [why it is or is not safe to mark] | [source -> work variable -> final use] | [EV-*] | preserve / mark / pending_source / pending_sme_judgment |

---

## TBDs & Blocking Status

### Open Items / Limitations

| Open Item | Impact | Evidence Gap | Suggested Follow-up |
| --- | --- | --- | --- |
| [unresolved dynamic call / field meaning / error code assignment / file role] | [why it matters downstream] | [missing source, runtime value, DDS, SME note, called program, or line evidence] | [specific follow-up] |

### Pending Source
- **TBD-[SLUG]-[NNN]:** [Question about missing DDS, source, or documentation]
  - Blocking: pending_source
  - Related: [OBJ-*, EV-*]

### Pending SME Judgment
- **TBD-[SLUG]-[NNN]:** [Question about unclear behavior or undocumented interface]
  - Blocking: pending_sme_judgment
  - Related: [OBJ-*, EV-*]

### Non-Blocking
- **TBD-[SLUG]-[NNN]:** [Question with workaround or non-blocking impact]
  - Blocking: non_blocking
  - Related: [OBJ-*, EV-*]

---

## Review Checklist

Before approval, SME must validate:

- [ ] External entry points and callable procedures are correct and complete
- [ ] Program Reading Summary gives a one-file processing-layer overview before the core logic sections
- [ ] Reader-first golden gate is clean: no pending/placeholder Program Reading Summary, routine-index detail, or main-file RLOG detail remains
- [ ] Analysis Coverage & Scope honestly states `program_size_tier`, compatibility analysis mode, default output profile, and optional sidecar triggers
- [ ] Routine Cards cover every routine that affects calls, data, errors, or external boundaries
- [ ] Deep Read Windows support all high-risk claims and state-changing behavior
- [ ] Indexed-only routines are either technical utilities or routed to explicit review items
- [ ] Routine Logic Details in `program-analysis.md` include continuous, ordered `RLOG-*` headings for every RLOG declared in `routine-logic-details.yaml`
- [ ] Routine Logic Details explain field calculations, conditioned calculation blocks, carrier/lineage ties, routine-local exception closure, branch outcomes, source lines, and evidence; sidecars are audit/checkpoint sources, not the only SME reading path
- [ ] Routine Logic Details include outcome reverse traces from material message/status/error/return outcomes back to branch guards, conditioned calculation blocks, comparison thresholds, intermediate variables, and source operands/carriers
- [ ] No whole-program business summary exceeds the documented coverage
- [ ] Program Call Map keeps a compact ASCII hierarchy Visual Overview and a traceable Call Evidence table
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] Calculation Logic is front-loaded immediately after Program Reading Summary, covers material whole-program calculations/assignments, and links every row to supporting routine-level or ledger evidence
- [ ] Calculation Logic, Validation Logic, and Exception Handling each include a reader-oriented overview plus `Routine Index For ...` rows covering every RLOG in `routine-logic-details.yaml`
- [ ] Logic Decomposition Ledger preserves calculations, constants, branch priority, loops, and CASE/SELECT behavior
- [ ] Routine / Window Data Flow shows input variables, transformations, output variables, side effects, source lines, and evidence
- [ ] Data Touch Map captures critical carriers, keys, payloads, and state impacts
- [ ] Key File & Field Logic preserves `FIELD_NAME` (business meaning) and `VARIABLE_NAME` (business meaning) [direction] for every resolvable key field or variable
- [ ] File I/O Key Fields preserve source identifiers plus business meaning, and Purpose describes why each file is accessed
- [ ] Normal programs use the same reader-first layout as larger programs; dense or state-changing I/O/SQL/mutation detail is routed to triggered sidecars (`file-io-inventory.*`, `field-mutation-matrix.*`, `sql-inventory.*`) instead of bloating the main review
- [ ] External and dynamic calls include caller routine, source lines, parameters, resolution status, purpose, and evidence
- [ ] Validation Logic is front-loaded immediately after Calculation Logic, has one row per message/status/return/response/generic outcome with reverse trigger chains / Routine Logic links, and Error Handling closes each exception path through return, rollback, skip, log, or downstream impact
- [ ] Exception Handling is front-loaded immediately after Validation Logic, covers every observed business/parameter/I/O/external/system/generic exception path, and links each row to closure evidence
- [ ] Message Inventory is front-loaded immediately after Exception Handling, has one summary row per explicit message/code/literal from `message-inventory.yaml`, including late-round tokens, and preserves description source, carrier/destination, trigger/handler, related Validation/Exception row, and evidence status
- [ ] Coverage/TBD wording is current; no stale legacy deep-read gap labels remain after RLOGs are normalized
- [ ] Reference-pack lookups, if used, cite pack ID/version/file/row and do not override source-backed behavior
- [ ] Inferred and unresolved meanings, calls, fields, and error codes are explicitly marked
- [ ] Code identifiers remain intact and readable; long lists use intentional line breaks
- [ ] Redundancy candidates are conservative and do not remove hidden rules
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] No invented subroutines or undocumented file access
- [ ] Evidence linkage matches analysis intent: `chain_ready` links to existing
  inventory items (`OBJ-*`, `EV-*`); `standalone_exploratory` uses source
  ranges/local references, marks inventory linkage missing, and does not
  fabricate `OBJ-*` or `EV-*`
- [ ] Status field is set correctly (`draft` → `needs_sme_review` /
  `draft_exploratory` / `blocked_pending_source` → `approved` /
  `approved_with_non_blocking_tbd` / `rejected`)

### SME Sign-Off

- **Reviewer:** [Name]
- **Review Date:** [YYYY-MM-DD]
- **Decision:** approved | approved_with_non_blocking_tbd | rejected
- **Notes:** [Free-form SME commentary]
