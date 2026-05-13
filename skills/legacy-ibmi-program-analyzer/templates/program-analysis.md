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
- **Status:** draft

---

## Entry Points & Parameters

| Entry Point | Type | Parameters | Return | Evidence |
| --- | --- | --- | --- | --- |
| [NAME] | Main Program / Subroutine / Procedure | (param1: type, param2: type) | [return type/code] | confirmed_from_code |

**Evidence links:**
- [EV-[SLUG]-[NNN]: Description]

**Unresolved:**
- TBD-[SLUG]-[NNN]: [Question]

---

## Call Graph

### Tree View

Source: source-level flow header (lines [XX–YY]) | derived-from-code | both (matched)

```text
Main line                    Main flow control
|-- [SR_NAME]                [description from header, if present]
|    |-- [SR_NAME]           [description]
|         |-- [SR_NAME]      [description]
|-- [SR_NAME]                [description]
```

**Evidence:**
- [EV-[SLUG]-[NNN]: source-level flow header lines XX–YY] (if header present)
- [EV-[SLUG]-[NNN]: EXSR / CALL / PERFORM statements] (code-derived)

**Header vs. code:** matched | drift detected → see TBD-[SLUG]-[NNN]

### Call Sites

| Caller | Callee | Type | Line | Call Condition | Evidence |
| --- | --- | --- | --- | --- | --- |
| [CALLER] | [CALLEE] | EXSR / CALLP / CALL / PERFORM / CALLPRC | [LINE] | always / in loop / only if X / first-time-only | confirmed_from_code |

### Reverse Index

| Subroutine | Called By | Notes |
| --- | --- | --- |
| [SR_NAME] | [CALLER] [line] | [hot path / dead code / single callsite / etc.] |

**Orphaned subroutines (declared but never called):**
- [SR_NAME] → TBD-[SLUG]-[NNN]: confirm whether dead code

---

## Control Flow

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

| File | Type | Operations | Key Fields | Purpose | Evidence |
| --- | --- | --- | --- | --- | --- |
| [FILE_NAME] | PF / LF / DSPF / PRTF | SETLL, READE, CHAIN, WRITE, UPDATE, DELETE | [KEY_FIELD_NAMES] | [Purpose description] | [EV-[SLUG]-[NNN]] |

**Operation details:**

- **[FILE_NAME] / [OPERATION] on [KEY]:** [Description of operation, indicators, result].

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

| Error Condition | Detected By | Handling | Recovery | Evidence |
| --- | --- | --- | --- | --- |
| [Error type] | MONITOR block / IF statement / Indicator / File operation | [Description of how error is caught] | [Recovery action or result] | [EV-[SLUG]-[NNN]] |

**Unhandled exceptions:**
- [Description of unhandled error conditions if any]

**Logged errors:**
- [Description of error logging, message queues, spool output]

**Evidence links:**
- [EV-[SLUG]-[NNN]: RPGLE MONITOR blocks / CLLE MONMSG / COBOL ON ERROR]

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

- [ ] Entry points are correct and complete (no missing callable subroutines)
- [ ] Parameter contracts match actual usage (no invented parameters)
- [ ] File I/O matches job design (no hallucinated key fields or unobserved operations)
- [ ] External calls match system interfaces (especially for undocumented calls)
- [ ] Error handling aligns with production reliability requirements
- [ ] TBDs are non-blocking or properly flagged for follow-up
- [ ] No invented subroutines or undocumented file access
- [ ] All evidence links reference existing inventory items (OBJ-*, EV-*)
- [ ] Status field is set correctly (draft → needs_sme_review → approved)

---

## SME Sign-Off

- **Reviewer:** [Name]
- **Review Date:** [YYYY-MM-DD]
- **Decision:** draft | needs_sme_review | approved | approved_with_non_blocking_tbd | rejected
- **Notes:** [Free-form SME commentary]

