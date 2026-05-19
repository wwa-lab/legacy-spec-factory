# Opcode Taxonomy: C-Spec Operation Codes

This taxonomy groups C-spec opcodes by **intent**, not alphabetically.
When analyzing a C-spec line, first classify the opcode's intent, then extract
the relevant fields (Factor 1, Factor 2, Result, resulting indicators).

---

## Category 1 — External Program / Procedure Calls

These opcodes cross a program boundary. They are the most important for understanding
module coupling, integration points, and modernization scope.

| Opcode | Factor 1 | Factor 2 | Result | Notes |
|---|---|---|---|---|
| `CALL` | — | Program name (literal or var) | — | Calls OPM/ILE program by name; literal = static, variable = dynamic |
| `CALLB` | — | Procedure pointer or name | — | Calls bound procedure; older ILE style |
| `CALLP` | — | Prototype call expression | — | Calls ILE procedure via prototype; free-format style in fixed C-spec |
| `PARM` | — | Parameter value or var | Result field | Defines one parameter for preceding CALL/CALLB; in-order |

**Analysis rules:**
- If Factor 2 of `CALL` is a quoted literal (e.g., `'GETRATE'`), the call target is statically known → extract it as an external dependency.
- If Factor 2 is a variable (e.g., `PgmName`), the call is **dynamic** → tag as `needs_sme_review`; list the variable name.
- Count `PARM` lines following a `CALL` to determine the parameter count.
- The first PARM after `CALL` is parameter 1; order matters.

**Modernization significance:** HIGH — every CALL represents a service boundary in the target architecture.

---

## Category 2 — File I/O (Database / Sequential)

These opcodes access physical files (DB2 tables or sequential files). They define
what data the program reads, writes, and modifies.

### Random access (key-based)

| Opcode | Factor 1 | Factor 2 | Result | Ind 1 | Ind 2 | Ind 3 |
|---|---|---|---|---|---|---|
| `CHAIN` | Key field(s) | File/record-format name | — | — | not found | I/O error |
| `SETLL` | Key field(s) | File/record-format name | — | — | not found | equal |
| `SETGT` | Key field(s) | File/record-format name | — | — | not found | — |

### Sequential access

| Opcode | Factor 1 | Factor 2 | Result | Ind 1 | Ind 2 | Ind 3 |
|---|---|---|---|---|---|---|
| `READ` | — | File/record-format name | — | — | EOF | I/O error |
| `READE` | Key field(s) | File/record-format name | — | — | EOF/key-change | I/O error |
| `READP` | — | File/record-format name | — | — | BOF | I/O error |
| `READPE` | Key field(s) | File/record-format name | — | — | BOF/key-change | I/O error |
| `READC` | — | Subfile record-format name | — | — | EOF | — |

### Write / modify

| Opcode | Factor 1 | Factor 2 | Result | Ind 2 | Ind 3 |
|---|---|---|---|---|---|
| `WRITE` | — | Record-format name | — | — | I/O error |
| `UPDATE` | — | Record-format name | — | — | I/O error |
| `DELETE` | Key field(s) | File/record-format name | — | not found | I/O error |
| `EXCEPT` | Output format name | — | — | — | — |

### File control

| Opcode | Factor 2 | Notes |
|---|---|---|
| `OPEN` | File name | Opens file declared with USROPN keyword |
| `CLOSE` | File name | Closes file |
| `UNLOCK` | File name | Releases record lock without update |
| `FEOD` | File name | Force end-of-data (flush output buffer) |

**Analysis rules:**
- Factor 2 of `CHAIN`/`READ`/`WRITE`/`UPDATE`/`DELETE` is the **file or record format name** — map it to F-spec declarations to get the physical file name.
- Factor 1 of `CHAIN`/`SETLL`/`SETGT`/`READE` is the key — identifies how the record is located.
- A `SETLL` always paired with `READE` = "read all records matching key" loop pattern.
- Resulting indicator in cols 73–74 for CHAIN = not-found flag; always check whether the program tests it.
- `DELETE` with a key in Factor 1 = delete by key (positions and deletes); without Factor 1 = delete current record.

**Modernization significance:** HIGH — each file touched = one table/entity in the target data model.

---

## Category 3 — Screen / Workstation Interaction

These opcodes interact with display files (WORKSTN device). They mark the boundary
between batch logic and interactive logic.

| Opcode | Factor 1 | Factor 2 | Notes |
|---|---|---|---|
| `EXFMT` | — | Record-format name | Write screen then wait for user input (combined write+read) |
| `DSPLY` | Message text | — | Display simple message on operator console |
| `IN` | — | Data Area name | Read a data area into a DS |
| `OUT` | — | Data Area name | Write a DS to a data area |

**Analysis rules:**
- Any `EXFMT` = interactive program; the record format name identifies the screen panel.
- Programs with `EXFMT` cannot be run batch — tag as `interactive` in the program analysis.
- `DSPLY` in a batch program = operator message, rare; tag as unusual.

**Modernization significance:** HIGH — interactive programs require UI replacement in the target system.

---

## Category 4 — Internal Subroutine Control

These opcodes call and return from subroutines defined within the same source member.

| Opcode | Factor 1 | Factor 2 | Notes |
|---|---|---|---|
| `EXSR` | — | Subroutine name | Call internal subroutine (no parameters) |
| `BEGSR` | Subroutine name | — | Begin subroutine definition |
| `ENDSR` | Return point | — | End subroutine; optional Factor 1 = label to return to |
| `LEAVESR` | — | — | Exit subroutine early (like RETURN inside BEGSR) |
| `CASxx` | Factor 1 | Factor 2 | Conditional EXSR (CAS, CASEQ, CASNE, CASGT, etc.) |

**Analysis rules:**
- `EXSR` with a name = internal call; do not confuse with `CALL` (external).
- `BEGSR`/`ENDSR` pairs define subroutine boundaries; extract them as logical units.
- Subroutines share all variables with the main procedure (no parameter passing) — flag global variable dependency.
- `CASxx` is an older conditional EXSR; treat as IF + EXSR for analysis purposes.

**Modernization significance:** MEDIUM — subroutines should become private methods or functions in the target; watch for global state sharing.

---

## Category 5 — Structured Control Flow

Flow control opcodes. These structure the logic but do not touch files or external systems.

### Conditionals

| Opcode | Factor 1 | Factor 2 | Notes |
|---|---|---|---|
| `IF` (free), `IFxx` | Factor 1 | Factor 2 | Condition — `IFEQ`, `IFNE`, `IFLT`, `IFLE`, `IFGT`, `IFGE` |
| `ELSE` | — | — | Alternate branch |
| `ELSEIF` | — | condition | Chained condition (free-format) |
| `ENDIF` | — | — | End IF block |
| `SELECT` | — | — | Begin multi-way branch |
| `WHEN` | — | condition | Branch condition |
| `OTHER` | — | — | Default branch |
| `ENDSL` | — | — | End SELECT block |
| `COMP` | Factor 1 | Factor 2 | Compare; sets resulting indicators only — used before CASxx |

### Loops

| Opcode | Factor 1 | Factor 2 | Notes |
|---|---|---|---|
| `DOW` (free), `DOWxx` | Factor 1 | Factor 2 | Do-while; `DOWEQ`, `DOWNE`, `DOWLT`, etc. |
| `DOU` (free), `DOUxx` | Factor 1 | Factor 2 | Do-until |
| `FOR` | — | loop expression | For-loop (free-format style) |
| `DO` | times | start-value | Fixed-count loop (older style) |
| `ENDDO` | — | — | End DO/DOW/DOU/FOR block |
| `ITER` | — | — | Skip to next iteration (continue) |
| `LEAVE` | — | — | Exit loop early (break) |

### Unconditional branching (legacy — treat as risk)

| Opcode | Factor 2 | Notes |
|---|---|---|
| `GOTO` | Tag name | Unconditional jump; spaghetti risk — tag as `needs_sme_review` |
| `TAG` | Tag name | Jump target definition |

**Analysis rules:**
- `GOTO` / `TAG` pairs are unstructured flow — flag them. They often signal error exits or retry loops that need careful tracing.
- Nested `DOW` + `READE` = "read-all-matching-records" loop; very common pattern.
- `SELECT`/`WHEN`/`OTHER`/`ENDSL` = switch statement; map each `WHEN` branch as a separate logic path.

**Modernization significance:** LOW for structured flow (IF/DO/SELECT); HIGH for GOTO (unstructured risk).

---

## Category 6 — Data Movement and Assignment

These opcodes move data between fields. Important for tracing data flow but generally
low modernization risk.

| Opcode | Factor 1 | Factor 2 | Result | Notes |
|---|---|---|---|---|
| `EVAL` | — | Expression | Result | Assign expression to result; workhorse of free-ish C-spec |
| `EVALR` | — | Expression | Result | Assign right-adjusted |
| `EVAL-CORR` | — | Source DS | Target DS | Copy matching field names between structures |
| `MOVE` | — | Factor 2 | Result | Move value (right-to-left alignment) |
| `MOVEL` | — | Factor 2 | Result | Move left (left-to-right alignment) |
| `MOVEA` | — | Factor 2 | Result | Move array element |
| `Z-ADD` | — | Factor 2 | Result | Zero-then-add (numeric assign) |
| `Z-SUB` | — | Factor 2 | Result | Zero-then-subtract |
| `ADD` | Factor 1 | Factor 2 | Result | Result = F1 + F2 (or F2 + Result if F1 blank) |
| `SUB` | Factor 1 | Factor 2 | Result | Result = F1 - F2 |
| `MULT` | Factor 1 | Factor 2 | Result | Result = F1 × F2 |
| `DIV` | Factor 1 | Factor 2 | Result | Result = F1 ÷ F2 |
| `MVR` | — | — | Result | Move remainder from preceding DIV |
| `CLEAR` | — | — | Target | Zero/blank all fields in a variable or DS |
| `RESET` | — | — | Target | Reset variable to its initial value (from `INZ` keyword) |
| `SORTA` | — | Array name | — | Sort array in place |

**Analysis rules:**
- `EVAL` is the modern assignment; `MOVE`/`MOVEL`/`Z-ADD` are older equivalents — treat them the same for data flow purposes.
- `EVAL-CORR` between two DS variables means "copy overlapping fields" — important for understanding data transformation.
- `CLEAR` on a DS = initialise all fields; often signals the start of a new transaction or record.

---

## Category 7 — Transaction and Commitment Control

These opcodes bracket database transactions.

| Opcode | Factor 2 | Notes |
|---|---|---|
| `COMMIT` | Boundary ID (optional) | Commit all changes since last commit/rollback |
| `ROLBK` | — | Roll back all changes since last commit |

**Analysis rules:**
- Presence of `COMMIT`/`ROLBK` means the program participates in a database transaction.
- Identify what file operations fall between `COMMIT` boundaries — that defines the atomic unit of work.
- If `COMMIT` is absent but the program does `WRITE` + `UPDATE` across multiple files, ask SME about transaction integrity.

**Modernization significance:** HIGH — transaction boundaries must be preserved exactly in the target system.

---

## Category 8 — Error Handling and Monitoring

| Opcode | Factor 1 | Factor 2 | Notes |
|---|---|---|---|
| `MONITOR` | — | — | Begin monitored block |
| `ON-ERROR` | Message ID(s) | — | Catch specific CPF/MCH messages; blank = catch-all |
| `ENDMON` | — | — | End monitored block |
| `DUMP` | — | — | Force program dump for debugging; treat as dead code in production |

**Analysis rules:**
- A `MONITOR` block wrapping a `CALL` = the program defensively handles external program failure.
- `ON-ERROR` with a specific CPF code (e.g., `CPF4101`) = the program knows about a specific failure mode — document it.
- `ON-ERROR` with no code = catch-all; weaker error handling.
- Nested `MONITOR` blocks are allowed; trace them separately.

---

## Category 9 — Return and Program Termination

| Opcode | Notes |
|---|---|
| `RETURN` | Return from current procedure to caller; in main procedure = end program |
| `*INLR = *ON` then fall-through | Legacy main-procedure exit; `*INLR` (Last Record indicator) signals program end |

**Analysis rules:**
- In OPM / cycle-based programs, the program ends when `*INLR` is set `*ON` and the cycle completes. Look for `EVAL *INLR = *ON` (free) or `SETON LR` (fixed).
- In ILE procedure-based programs, `RETURN` exits the current procedure; the main procedure's return exits the program.
- Multiple `RETURN` paths = multiple exit conditions; trace each one.

---

## Quick-Reference: Opcode → Intent

```
CALL / CALLB / CALLP  →  External program/procedure call
CHAIN                 →  Random read (by key)
SETLL + READE loop    →  Sequential read (all matching records)
READ loop             →  Sequential read (all records)
WRITE                 →  Insert new record
UPDATE                →  Modify existing record
DELETE                →  Remove record
EXFMT                 →  Interactive screen I/O
EXSR                  →  Internal subroutine call
COMMIT / ROLBK        →  Transaction boundary
MONITOR / ON-ERROR    →  Error handling
EVAL / MOVE / Z-ADD   →  Data assignment
IF / SELECT / DOW     →  Structured flow control
GOTO / TAG            →  Unstructured flow (risk flag)
*INLR / RETURN        →  Program/procedure exit
```
