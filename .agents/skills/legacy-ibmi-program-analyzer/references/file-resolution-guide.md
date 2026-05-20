# File Resolution Guide: Connecting Program Code to DDS

When a program references a file, the F-spec tells you the file name and device
type. The DDS for that file tells you the field structure. This guide explains
how to bridge the two, what to extract at each step, and when to create a TBD
instead of guessing.

---

## Step 1 — Classify the File from the F-Spec

Every file reference in a program starts with an F-spec. Read the device type
(cols 35–42) first to know which kind of DDS to look for.

| F-spec device | File object type | DDS skill | What you need from DDS |
|---|---|---|---|
| `DISK` | PF or LF | `legacy-ibmi-data-model-analyzer` | Field names, types, key fields, access path |
| `WORKSTN` | DSPF | `legacy-ibmi-screen-report-analyzer` | Record formats, field roles, function keys, subfiles |
| `PRINTER` | PRTF | `legacy-ibmi-screen-report-analyzer` | Record formats, field positions, edit codes, control breaks |
| `SEQ` | Sequential / IFS | (inline analysis) | Buffer layout, if program-described |

**If the DDS is not in the inventory**, stop and create a TBD:
```
TBD-<SLUG>-NNN: Provide DDS source for <filename> (<type>) — required to
resolve field structure used in <operation> at line <N>
```

---

## Step 2 — Resolve EXTNAME in D-specs

`EXTNAME` is the most common way a program inherits a file's field structure
into a data structure. It appears in D-specs:

```rpgle
D CREDDATA      E DS          EXTNAME(CREDFILE)
D ORDHEADDS     E DS          EXTNAME(ORDHEADF:ORDHFMT)
```

### What EXTNAME means

`EXTNAME(filename)` — allocate a DS whose subfields exactly match all fields
in the externally described file `filename`. The DS layout comes entirely from
the file's DDS, not from the program source.

`EXTNAME(filename:recordformat)` — same, but scoped to a specific record format
within the file (for files with multiple record formats).

### What to do when you see EXTNAME

1. Look up the file in the inventory by name.
2. Find the DDS for that file.
3. The DS subfields are the DDS field list in declaration order.
4. Any program statement that reads or writes a subfield of this DS is
   operating on the corresponding DDS field.

**If DDS is available:**
- List the resolved fields in the Data Touch Map (name, type, length, decimals).
- Tag evidence as `confirmed_from_code` + `confirmed_from_dds`.

**If DDS is not available:**
- Do not guess field names or types.
- Create: `TBD-<SLUG>-NNN: Provide DDS for <filename> — EXTNAME at line <N>
  requires field list to trace data flow through DS <dsname>`
- Tag all references to that DS as `missing`.

### EXTNAME variants

| Pattern | Meaning |
|---|---|
| `EXTNAME(CREDFILE)` | All fields from CREDFILE's (only) record format |
| `EXTNAME(ORDHEADF:ORDHFMT)` | Fields from record format ORDHFMT only |
| `EXTNAME(CREDFILE) QUALIFIED` | Fields are accessed as `CREDDATA.CUSTID` — qualified names |
| `EXTNAME(CREDFILE) TEMPLATE` | DS is a type template; no storage allocated; used with `LIKEDS` |
| `LIKEDS(CREDDATA)` | Another DS with same layout as CREDDATA (copy-by-structure) |
| `LIKEREC(CREDFILE:*INPUT)` | DS matching the input fields of CREDFILE's record format |

---

## Step 3 — Understand PF vs LF for DISK Files

When a program opens a DISK file, it may be opening either a Physical File (PF)
or a Logical File (LF). The distinction matters for understanding what key the
program is actually using.

### Physical File (PF)

A PF defines the actual stored data and its primary access path (key sequence).

```dds
A          R CREDMST
A            CUSTID        9P 0
A            CREDLIMIT     9P 2
A          K CUSTID
```

A `CHAIN CUSTID CREDFILE` where CREDFILE is this PF uses key `CUSTID`.

### Logical File (LF)

A LF is a view over one or more PFs. It may:
- **Rekey** — define a different access path (K-specs that differ from the PF)
- **Rename** — expose a PF field under a different name
- **Subset** — select/omit records based on conditions
- **Join** — combine fields from multiple PFs

```dds
A          R CRDBYNM                   PFILE(CREDMST)
A            CUSTNAME      30A
A            CUSTID
A          K CUSTNAME
```

A `CHAIN CUSTNAME CRDBYNM` where CRDBYNM is this LF uses key `CUSTNAME`
— not `CUSTID`. The program is doing a lookup by name, not by ID.

### The access-path lookup rule

When a program does `CHAIN key FILENAME` or `SETLL key FILENAME`:

1. Look at the F-spec for FILENAME.
2. Is FILENAME a PF or LF? (Check inventory `object_type` field.)
3. If PF → the key is the PF's K-spec fields in order.
4. If LF → the key is the **LF's** K-spec fields (which may differ from the PF).
5. Document: `CHAIN on <filename> uses key (<field1>, <field2>, ...) via <PF/LF>`

**If you cannot determine PF vs LF from inventory**, create a TBD:
```
TBD-<SLUG>-NNN: Confirm whether <filename> is PF or LF — access path used by
CHAIN at line <N> depends on which K-spec applies
```

---

## Step 4 — Resolve DSPF Record Formats

When a program does `EXFMT RECORDFORMAT` or `WRITE RECORDFORMAT` on a WORKSTN
file, it is interacting with one specific record format in the DSPF.

```rpgle
F ORDMENU     CF   E               WORKSTN
...
C             EXFMT      MAINSCN
C             EXFMT      DETAILSCN
```

For each `EXFMT` or WORKSTN `WRITE`/`READ`:

1. Identify the record format name (Factor 2 of EXFMT, or Factor 2 of
   WRITE/READ on a WORKSTN file).
2. Look up that record format in the DSPF DDS.
3. Extract:
   - Input fields (user can type a value) → program input parameters
   - Output fields (program displays a value) → program output
   - Function key definitions (CA01–CA24, CF01–CF24) → user-triggered events
   - Indicator-conditioned attributes (PROTECT, ERRMSG, DSPATR) → validation/UX rules
4. The program reads `*IN` indicators to know which function key was pressed.

**Function key → indicator mapping (standard):**

| Key | Indicator set by system |
|---|---|
| Enter | No indicator set (default action) |
| F1 | `*IN01` (if CA01/CF01 defined) |
| F2 | `*IN02` |
| F3 | `*IN03` (typically Exit) |
| F4 | `*IN04` (typically Prompt / List of values) |
| F5 | `*IN05` (typically Refresh) |
| F12 | `*IN12` (typically Cancel / Back) |
| F24 | `*IN24` |

After `EXFMT`, the program tests `*INxx` to branch to the correct handler. Trace
this indicator → branch logic to understand the screen flow.

---

## Step 5 — Resolve PRTF Record Formats

When a program does `WRITE RECORDFORMAT` on a PRINTER file, it is writing one
line/section to the spool.

```rpgle
F INVPRT      O    F  132          PRINTER
...
C             WRITE      RPTHDR
C             WRITE      RPTDET
C             WRITE      RPTTOT
```

For each PRINTER `WRITE`:

1. Identify the record format name.
2. Look up that format in the PRTF DDS.
3. Extract field layout, constants, edit codes, spacing.
4. Correlate the WRITE sequence in the program to the report section order
   (header → detail → subtotal → grand total).

---

## Step 6 — When DDS Is Missing: TBD Creation Rules

| Situation | TBD type | Blocking? |
|---|---|---|
| DISK file, DDS not in inventory | `pending_source` | Yes — cannot resolve field names or access path |
| EXTNAME DS, DDS not in inventory | `pending_source` | Yes — cannot trace data flow through DS |
| WORKSTN file, DSPF not in inventory | `pending_source` | Yes — cannot identify screen fields or function keys |
| PRINTER file, PRTF not in inventory | `pending_source` | Yes for report layout; no for basic WRITE order |
| LF referenced, PF DDS known but LF DDS missing | `pending_source` | Yes — cannot confirm key fields used |

**TBD format:**
```
TBD-<SLUG>-NNN (blocking: pending_source)
  artifact_needed: DDS source for <filename> (<PF|LF|DSPF|PRTF>)
  why_blocking: <operation> at line <N> cannot be analyzed without field structure
  who_provides: inventory owner / IBMi system admin
```

Do not proceed past a blocking TBD by guessing field names from variable names
in the program. A guess that looks plausible will propagate through the entire
spec pipeline as a false fact.

---

## Summary: File Resolution Checklist

For each file reference found in F-specs:

- [ ] Identify device type → classify as DISK / WORKSTN / PRINTER
- [ ] Check inventory for DDS availability
- [ ] If DISK: determine PF vs LF; extract key field sequence
- [ ] If DISK + EXTNAME in D-spec: resolve DS subfields from DDS
- [ ] If WORKSTN: map EXFMT/WRITE/READ to DSPF record formats; map F-keys to indicators
- [ ] If PRINTER: map WRITE sequence to PRTF record formats and report sections
- [ ] Create TBD (blocking: pending_source) for any missing DDS
- [ ] Tag all resolved fields as `confirmed_from_code + confirmed_from_dds`
- [ ] Tag all unresolved DS/field references as `missing`
