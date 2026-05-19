# Fixed-Format RPGLE Reading Guide

Fixed-format RPGLE is column-based: every character position carries a fixed meaning.
This guide documents the column layout for each spec type and the rules for inferring
data types from D-specs. Apply these rules before interpreting any fixed-format source.

---

## Step 0 — Identify the Spec Type

Column 6 (1-based) holds the spec type letter. Everything else depends on which spec
you are reading.

```
Col:  1234 5 6 7...
           ↑ ↑
           │ └─ Spec type letter
           └─── Sequence number area (cols 1-5, ignore for analysis)
```

| Col 6 letter | Spec type | Purpose |
|---|---|---|
| `H` | Control (Header) | Compiler directives, program-level options |
| `F` | File | Declares files/tables the program uses |
| `D` | Definition | Variables, data structures, constants, prototypes |
| `I` | Input | Input record and field definitions (old-style) |
| `C` | Calculation | Business logic operations |
| `O` | Output | Output record and field definitions (old-style) |
| `P` | Procedure | Sub-procedure begin/end |
| ` ` | Continuation | Continuation of previous spec's keywords |

> If col 6 is blank and the line begins with `**`, it is a comment — skip it.
> If col 6 is blank and the line begins with `/` (e.g., `/free`, `/end-free`,
> `/copy`, `/include`), it is a compiler directive — note but do not parse as a spec.

---

## F-Spec (File Declaration)

Columns reference (1-based):

```
Col  6      : Spec type = F
Col  7–16   : File name (10 chars)
Col  17     : File type  — I=Input, O=Output, U=Update, C=Combined
Col  18     : File designation — blank=full-procedural, P=primary, S=secondary
Col  19     : End-of-file — blank or E
Col  20     : File addition — blank or A (add records)
Col  21     : Sequence — blank or A/D (ascending/descending)
Col  22     : File format — F=fixed, E=program-described, blank=externally described
Col  23–27  : Record length (program-described files only)
Col  28     : Limits processing — blank or L
Col  29–33  : Length of key / record address
Col  34     : Record address type — blank=sequential, K=key, ...
Col  35–42  : Device type — DISK, WORKSTN, PRINTER, SEQ, SPECIAL
Col  43–80  : Keywords
```

### What to extract from F-specs

| Field | How to read it | Meaning for analysis |
|---|---|---|
| File name (7–16) | Trim spaces | The physical file / table accessed |
| File type (17) | Single char | I=read-only, U=read-write, O=write-only, C=read+write |
| Device (35–42) | Trim spaces | DISK=DB table, WORKSTN=display file, PRINTER=report |
| Keywords | Parse after col 43 | `KEYED` = key access; `RENAME(x:y)` = record format alias; `USROPN` = manual open |

### Example

```
F CREDFILE   IF   E             K DISK
F ORDHDR     UF   E             K DISK
F INVPRT     O    F  132          PRINTER
F ORDMENU    CF   E               WORKSTN
```

- `CREDFILE` — externally described, input-only, keyed DISK file (read-only table)
- `ORDHDR` — externally described, update, keyed DISK file (read-write table)
- `INVPRT` — fixed-length, output-only, PRINTER (spool report)
- `ORDMENU` — combined (read+write), WORKSTN (interactive display file)

---

## D-Spec (Definition)

The most information-dense spec. Declares variables, data structures, constants,
prototypes (PR), and procedure interfaces (PI).

```
Col  6      : Spec type = D
Col  7–21   : Name (15 chars)
Col  22     : blank (reserved)
Col  23–24  : Definition type — DS, S, C, PR, PI, blank (subfield)
Col  25–32  : From position (for program-described input records only)
Col  33–39  : To position / length (to-position or length depending on context)
Col  40     : Internal data type code (see table below)
Col  41–42  : Decimal positions
Col  43–80  : Keywords
```

> Columns 25–32 and 33–39 carry different meanings depending on context.
> For standalone variables and DS subfields, col 33–39 is the **length**.
> For I-spec derived fields, col 25–32 and 33–39 are from/to positions.

### Definition type codes (col 23–24)

| Col 23–24 | Meaning |
|---|---|
| `S ` or blank-S | Standalone variable |
| `DS` | Data structure begin |
| `C ` | Named constant |
| `PR` | Prototype (external program/procedure declaration) |
| `PI` | Procedure interface (parameter list of current procedure) |
| blank | Subfield of current DS, or continuation |

### Internal data type codes (col 40)

| Code | Type name | Notes |
|---|---|---|
| blank | Character or Zoned/Packed depending on decimals | See type inference rules below |
| `A` | Character | Fixed-length string |
| `B` | Binary integer | 2-byte or 4-byte depending on length |
| `D` | Date | ISO or job format |
| `F` | Float | Single or double precision |
| `G` | Graphic (DBCS) | Double-byte character |
| `I` | Integer | Signed: 3I=8-bit, 5I=16-bit, 10I=32-bit, 20I=64-bit |
| `N` | Indicator | Single character `*ON`/`*OFF` |
| `O` | Object | Java or ILE object reference |
| `P` | Packed decimal | |
| `S` | Zoned decimal | |
| `T` | Time | |
| `U` | Unsigned integer | |
| `Z` | Timestamp | |
| `*` | Pointer (basing or procedure) | |

### D-spec type inference rules

When col 40 is blank, apply these rules in order:

```
1. If col 23–24 = C  → Named constant; type from VALUE keyword
2. If col 23–24 = PR → Prototype declaration; type = return type from col 33–39 + col 40
3. If keywords contain LIKE(x)    → Same type as variable x (look up x's declaration)
4. If keywords contain LIKEDS(x)  → DS subtype matching structure x
5. If keywords contain LIKEREC(x) → DS subtype matching record format x
6. If col 41–42 (decimals) is blank AND col 40 is blank:
       → Character; length = col 33–39 trimmed
7. If col 41–42 (decimals) is non-blank AND col 23 in subfield area:
       a. If preceding DS keyword contains PACKED or col 22 = P → Packed(len:dec)
       b. Else → Zoned(len:dec)
```

### Reading "pretty type" from D-spec columns

| Col 40 | Col 33–39 (len) | Col 41–42 (dec) | Resulting type |
|---|---|---|---|
| blank | 10 | blank | `Char(10)` |
| blank | 7 | 2 | `Zoned(7:2)` |
| `P` | 7 | 2 | `Packed(7:2)` |
| `S` | 7 | 2 | `Zoned(7:2)` |
| `I` | 10 | — | `Int(10)` — 32-bit signed |
| `N` | 1 | — | `Indicator` |
| `D` | 10 | — | `Date` |
| `T` | 8 | — | `Time` |
| `Z` | 26 | — | `Timestamp` |
| `F` | 8 | — | `Float(8)` — double precision |
| `*` | 16 | — | `Pointer` |

### D-spec examples

```
D CustID          S              9P 0
D Amount          S              7P 2
D CustName        S             25
D ValidFlag       S              1N
D StartDate       S              8D
D MaxAmount       C                   CONST(999999.99)
D ErrorCode       S              4A
```

| Name | Col 40 | Len | Dec | Inferred type | Notes |
|---|---|---|---|---|---|
| CustID | blank | 9 | 0 | `Packed(9:0)` | 9-digit integer, packed |
| Amount | blank | 7 | 2 | `Packed(7:2)` | currency-style packed |
| CustName | blank | 25 | blank | `Char(25)` | fixed-length string |
| ValidFlag | `N` | 1 | — | `Indicator` | boolean flag |
| StartDate | `D` | 8 | — | `Date` | date field |
| MaxAmount | `C` | — | — | `Constant` | compile-time constant |
| ErrorCode | blank | 4 | blank | `Char(4)` | 4-char status/error code |

---

## C-Spec (Calculation)

The C-spec encodes one operation per line. Columns are strictly positional.

```
Col  6      : Spec type = C
Col  7–8    : Control level indicator (L0–L9, LR, MR)
Col  9–11   : Conditioning indicators (e.g., 01, N9, LR)
Col  12–25  : Factor 1 (operand / key / compare value)
Col  26–35  : Operation code (opcode) — right-justified, may include extender e.g. CHAIN(N)
Col  36–49  : Factor 2 (operand / file name / called program / value)
Col  50–63  : Result field (target variable / file name for some ops)
Col  64–68  : Field length (for result field definition)
Col  69–70  : Decimal positions
Col  71–72  : Resulting indicator 1 (set on positive / found)
Col  73–74  : Resulting indicator 2 (set on negative / not found / equal)
Col  75–76  : Resulting indicator 3 (set on zero / error)
```

### Opcode extenders (in parentheses after opcode)

| Extender | Meaning |
|---|---|
| `(N)` | No lock — read without locking the record |
| `(E)` | Error handling — sets %error() instead of halting |
| `(H)` | Half-adjust (round) numeric result |
| `(P)` | Pad result with blanks / zeros |

### Reading resulting indicators

Resulting indicators (cols 71–76) are set by the operation:

| Operation | Ind 1 (71–72) | Ind 2 (73–74) | Ind 3 (75–76) |
|---|---|---|---|
| CHAIN | — | not found | I/O error |
| READ / READE | — | EOF | I/O error |
| WRITE | — | — | I/O error |
| UPDATE | — | — | I/O error |
| COMP / IFEQ etc. | positive/true | negative/false | zero/equal |
| CALL / CALLB | — | — | error (LR) |

### C-spec examples

```
C     CUSTID        CHAIN      CREDFILE                           99
C     *IN99         IFEQ       *ON
C                   EVAL       RC = -1
C                   ELSE
C                   EVAL       RC = 0
C                   ENDIF

C                   CALL       'GETRATE'
C                   PARM                    RateCode       4
C                   PARM                    Rate           7 4
```

Reading the CHAIN line:
- Factor 1 = `CUSTID` (key to use)
- Opcode = `CHAIN` (random access by key)
- Factor 2 = `CREDFILE` (file to access)
- Ind 2 (cols 73–74) = `99` → `*IN99` set if record not found

Reading the CALL block:
- Opcode = `CALL`, Factor 2 = `'GETRATE'` (external program name, literal = static call)
- PARM lines define parameters in order: RateCode (4-char in), Rate (7P4 out)

---

## P-Spec (Procedure)

```
Col  6      : Spec type = P
Col  7–21   : Procedure name (15 chars)
Col  22     : blank
Col  23     : Begin/End — B=begin, E=end
Col  43–80  : Keywords (EXPORT, STATIC, etc.)
```

A procedure body is everything between the `P...B` line and the matching `P...E` line.
The D-specs immediately following `P...B` define the procedure's parameters (PI) and
local variables.

```
P ValidateCredit  B
D ValidateCredit  PI             N
D   Amount                       7P 2 CONST
D   Limit                        7P 2 CONST
C   ...
P ValidateCredit  E
```

---

## Common Fixed-Format Reading Mistakes

### Mistake 1 — Mis-reading column 40 blank as "no type"

Blank in col 40 does **not** mean "untyped." Apply the inference rules: check decimals
(col 41–42) to distinguish Character from Zoned/Packed.

### Mistake 2 — Treating all D-specs as variables

`PR` and `PI` specs declare prototypes and interfaces, not storage. A `PR` line means
"this program/procedure exists externally." Do not count them as data fields.

### Mistake 3 — Confusing Factor 1 and Factor 2 in CHAIN/SETLL

`Factor 1` = the **key** used to position. `Factor 2` = the **file** being accessed.
They are often swapped in first-time readings.

```
C     CUSTID        CHAIN      CREDFILE
      ↑ key                    ↑ file
```

### Mistake 4 — Ignoring resulting indicators

A CHAIN with `99` in cols 73–74 means `*IN99` is the not-found flag. If the code then
tests `*IN99`, that is error handling — not dead code.

### Mistake 5 — Missing continuation lines

If a D-spec name ends in `...` (cols 7–21 end with ellipsis), the name continues on the
next line. Do not treat the continuation line as a separate variable.

### Mistake 6 — Confusing /free sections inside fixed-format programs

Some programs mix fixed-format specs with `/free` ... `/end-free` sections. Inside
`/free`, free-format syntax applies (no column rules). Switch parsing mode at the
directive, switch back at `/end-free`.
