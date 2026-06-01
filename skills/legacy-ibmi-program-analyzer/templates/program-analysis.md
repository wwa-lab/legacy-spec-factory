# Program Analysis: [Program Name] (OBJ-[ID])

## Metadata

- **Program ID:** OBJ-[SLUG]-[NNN]
- **Program Name:** [SOURCE_PROGRAM_NAME]
- **Program Type:** RPGLE | CLLE | COBOL
- **Library:** [LIBRARY_NAME]
- **Source Location:** [file path or collection ID]
- **Collection Date:** YYYY-MM-DD
- **Entry Points:** [List entry point names]
- **Files Accessed:** [List file names and types]
- **External Calls:** [List called program/service names]
- **Status:** draft | needs_sme_review | blocked_pending_source | approved | approved_with_non_blocking_tbd | rejected

---

## Analysis Coverage & Scope

Purpose: state how much source was available, how the analysis was scoped, and
which claims are fully supported versus indexed-only.

### Source Size & Strategy

| Source Lines | Analysis Mode | Mode Reason | Structure Index Built | Full Source In Context | Business Narrative Allowed |
| --- | --- | --- | --- | --- | --- |
| [N lines] | standard / segmented / large-program | [why this mode was selected] | yes / no | yes / no | yes / limited / no |

### Coverage Ledger

| Routines Found | Routines Deep-Read | Routines Indexed Only | External Edges Resolved | Data Touches Resolved | Blocking Gaps | Non-Blocking Gaps |
| --- | --- | --- | --- | --- | --- | --- |
| [N] | [N] | [N] | [N/N] | [N/N] | [N] | [N] |

### Source Index Summary

| Mainline Segments | Subroutines / Procedures | External Calls | File Operations | Display / Report Operations | Commit / Rollback Points |
| --- | --- | --- | --- | --- | --- |
| [N] | [N] | [N] | [N] | [N] | [N] |

## Program Call Map

Purpose: RDi-style structural view of the program. This is a call map, not
a business-process diagram.

### Visual Overview

Source: source-level flow header (lines [XX-YY]) | derived-from-code | both (matched)

```mermaid
flowchart LR
  MAIN["[PROGRAM] mainline"]
  MAIN --> SR100["SR100"]
  MAIN --> SR200["SR200"]
  SR200 --> SR980["SR980"]
  SR980 --> EXT1["[EXTERNAL_PROGRAM]"]
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

### Call Tree

Source: source-level flow header (lines [XX-YY]) | derived-from-code | both (matched)

```text
Main line                    Main flow control
|-- [SR_NAME]                [description from header, if present]
|    |-- [SR_NAME]           [description]
|         |-- [SR_NAME]      [description]
|-- [SR_NAME]                [description]
```

**Evidence:**
- [EV-[SLUG]-[NNN]: source-level flow header lines XX-YY] (if header present)
- [EV-[SLUG]-[NNN]: EXSR / CALL / PERFORM statements] (code-derived)

**Header vs. code:** matched | drift detected -> see TBD-[SLUG]-[NNN]

### Call Edge Table

| From | To | Type | Line | Call Condition / Context | Evidence |
| --- | --- | --- | --- | --- | --- |
| [CALLER] | [CALLEE] | EXSR / CALLP / CALL / PERFORM / CALLPRC | [LINE] | always / in loop / only if X / first-time-only | [EV-[SLUG]-[NNN]] |

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
| [FILE_NAME] | PF / LF | CHAIN / READ / READE / WRITE / UPDATE / DELETE | [SRxxx / procedure] | key=[FIELD] | [amount/status/customer/account/RC/etc.] | read-only / creates / updates / deletes | [EV-*] |
| [DTAARA_NAME] | *DTAARA | IN / OUT / CHGDTAARA / RTVDTAARA | [SRxxx / procedure] | [value or structure] | [critical fields] | reads shared state / updates shared state | [EV-*] |
| [DTAQ_NAME] | *DTAQ | SNDDTAQ / RCVDTAQ / QSNDDTAQ / QRCVDTAQ | [SRxxx / procedure] | [message structure] | [critical fields] | async send / async receive | [EV-*] |
| [CALL_TARGET] | CALL parameters | in / out / inout | [SRxxx / procedure] | [parameter list] | [decision/status/error fields] | passes state across program boundary | [EV-*] |

### Critical Field Watchlist

| Field / Data Structure | Object / Carrier | Why It Matters | Observed Operations | Evidence |
| --- | --- | --- | --- | --- |
| [FIELD_NAME] | [OBJECT] | amount / status / customer / account / inventory / posting / approval / error code | read / written / compared / returned | [EV-*] |

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about payload structure, key field, direction, or state impact]

---

## Key File & Field Logic

Purpose: identify the files and fields that define the program's replayable
behavior: access keys, calculation inputs/results, branch drivers, error/status
fields, external parameters, and persisted fields.

### Key Files

| File / Carrier | Role in Program | Routines | Access / Mutation Pattern | Key Fields | Critical Persisted / Output Fields | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [FILE_NAME] | driver / lookup / state-update / detail-insert / audit-log / screen-report / queue-message / parameter-DS | [SRxxx] | [READ loop / CHAIN lookup / UPDATE / WRITE / DELETE / EXFMT / CALL inout] | [FIELD_NAMES] | [FIELD_NAMES] | [EV-*] |

### Key Fields

| Field / Data Structure | Source Object / Carrier | Role | Used In | Values / Domain Observed | Downstream Impact | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| [FIELD_NAME] | [FILE / DS / parameter / work variable] | access-key / input / derived / calculation-result / branch-condition / status-flag / return-code / error-code / message-id / external-parameter / persisted-field / audit-output | [routine, condition, mutation, call] | [literal/domain/range if visible] | [write, return, skip, error, external handoff] | [EV-*] |

### Field Lineage

| Lineage ID | Source / Physical Field | Alias / Data Structure | Work Variables | Calculation / Condition | Write-Back Alias | Persisted / Output Field | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LIN-[SLUG]-[NNN] | [FILE.FIELD or parameter] | [alias/copybook field] | [work variables] | [operation or branch] | [alias field] | [FILE.FIELD / message / call parameter] | [EV-*] |

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

### File Access Summary

| File | Record Format | Type | Operations | Key Fields | Read / Mutation Conditions | Indicators / Status Checks | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [FILE_NAME] | [FORMAT] | PF / LF / DSPF / PRTF | SETLL, READE, CHAIN, WRITE, UPDATE, DELETE | [KEY_FIELD_NAMES] | [IF/loop/SELECT context] | [*INxx / %FOUND / %ERROR / SQLCODE / SQLSTATE] | [EV-*] |

### Field Mutation Matrix

| File | Operation | Routine / Lines | Access Key / Record Condition | Field Mutated / Persisted | Source Value / Expression | Assignment Evidence | Error / Rollback Handling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [FILE_NAME] | WRITE / UPDATE / DELETE / EXEC SQL | [SRxxx lines XX-YY] | [key fields and condition] | [FIELD_NAME or record delete] | [literal, source field, calculation, moved value] | [EV-* assignment lines] | [handler, message ID, return code, or unhandled] |

**Operation details:**

- **[FILE_NAME] / [OPERATION] on [KEY]:** [Description of operation, fields assigned before mutation, indicators/status checks, result].

**Evidence links:**
- [EV-[SLUG]-[NNN]: Source lines / DDS reference]

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question about file access or missing DDS]

---

## External Calls

| Called Program | Type | Parameters (In / Out) | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| [PROGRAM_NAME] | RPGLE Program / CLLE Program / Service Program / API / etc. | (param1: type, param2: type) → (return: type) | [Purpose description] | [EV-[SLUG]-[NNN]] |

**Call details:**

- **[PROGRAM_NAME]:** [Description of parameters, return values, synchronous/asynchronous, known error handling].

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

### Message / Error Code Inventory

| Message ID / Code | Source | Meaning Observed In Code | Handler / Branch | Evidence |
| --- | --- | --- | --- | --- |
| [CPFxxxx / UCCxxxx / literal code] | MONMSG / ON-ERROR / MOVE / SNDPGMMSG / MSGF / SQL | [meaning if explicit; otherwise TBD] | [routine or generic handler] | [EV-*] |

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
- [ ] Analysis Coverage & Scope honestly states whether this was standard, segmented, or large-program mode
- [ ] Routine Cards cover every routine that affects calls, data, errors, or external boundaries
- [ ] Deep Read Windows support all high-risk claims and state-changing behavior
- [ ] Indexed-only routines are either technical utilities or routed to explicit review items
- [ ] No whole-program business summary exceeds the documented coverage
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] Logic Decomposition Ledger preserves calculations, constants, branch priority, loops, and CASE/SELECT behavior
- [ ] Data Touch Map captures critical carriers, keys, payloads, and state impacts
- [ ] Key File & Field Logic shows source fields, aliases, work variables, calculations/conditions, and persisted fields
- [ ] File I/O field mutation matrix names which files and fields are written, updated, deleted, or skipped
- [ ] External calls match system interfaces (especially for undocumented calls)
- [ ] Error handling lists every observed message ID / error code and closes each exception path through return, rollback, skip, log, or downstream impact
- [ ] Redundancy candidates are conservative and do not remove hidden rules
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] No invented subroutines or undocumented file access
- [ ] All evidence links reference existing inventory items (OBJ-*, EV-*)
- [ ] Status field is set correctly (`draft` → `needs_sme_review` /
  `blocked_pending_source` → `approved` / `approved_with_non_blocking_tbd` /
  `rejected`)

### SME Sign-Off

- **Reviewer:** [Name]
- **Review Date:** [YYYY-MM-DD]
- **Decision:** approved | approved_with_non_blocking_tbd | rejected
- **Notes:** [Free-form SME commentary]
