# PRTF Report Patterns Reference

Use this reference when analyzing IBM i printer-file DDS, RPG output specs
(O-specs), report programs, and spool samples. Keep layout facts separate from
calculation and print-order facts.

## PRTF DDS Column Layout

PRTF DDS is column-based like all IBM i DDS. The form type in col 6 (A-spec)
and the position of the name field determine what each line defines.

```
Col  6      : A (always — marks a DDS spec line; * = comment, skip it)
Col  7      : Form type indicator (R=record format, blank=field/keyword)
Col  8–16   : Name (record format name or field name)
Col  17     : Reference indicator (R = inherits type from reference file)
Col  18–19  : Length (for field lines)
Col  20     : Data type (A=char, P=packed, S=zoned, B=binary, blank=depends)
Col  21–22  : Decimal positions
Col  23–27  : Usage (O=output only, B=both, P=program-only, H=hidden)
Col  28–29  : Line number (row on page, 1-based)
Col  30–32  : Position (column on page, 1-based)
Col  33+    : Keywords
```

### Form type letters (col 7)

| Col 7 | Meaning |
|---|---|
| `R` | Record format — begins a named section of the report |
| blank | Field or keyword continuation of the current record format |

### Identifying a record format

```
     A          R RPTHDR                    TEXT('Report Header')
     A            TITLE         80A   O  1  5
     A            RUNDATE        8A   O  1 60
     A            PAGNO          4  0 O  1 70    EDTCDE(Z)
```

- Line beginning with `R` = record format `RPTHDR` starts here
- Fields below it (`TITLE`, `RUNDATE`, `PAGNO`) belong to `RPTHDR` until the next `R` line
- `O` in col 23 = output-only (report output, never returned to program)
- `1  5` = row 1, column 5 (printed position on page)

### Field data types in PRTF

Same type codes as PF DDS:

| Code | Type | Typical use in reports |
|---|---|---|
| `A` | Alphanumeric | Names, codes, labels |
| `P` | Packed decimal | Amounts, totals (always with EDTCDE) |
| `S` | Zoned decimal | Older numeric style |
| blank + len + dec | Numeric (EDTCDE/EDTWRD determines appearance) | Calculated totals |

### Edit codes (EDTCDE) — what numbers look like on the report

| Code | Format | Example (value 1234567) |
|---|---|---|
| `1` | Comma, no sign, blank zero | `1,234,567` |
| `2` | Comma, no sign, zero as zero | `1,234,567` |
| `3` | No comma, no sign | `1234567` |
| `4` | No comma, sign | `1234567` |
| `A` | Comma, CR for negative | `1,234,567` |
| `B` | Comma, minus for negative | `1,234,567-` |
| `J` | Comma, with sign protection | `1,234,567` |
| `Z` | Suppress leading zeros | `1234567` (no commas) |

**Modernization note:** EDTCDE encodes display-only formatting. Do not treat the
edit code as a business rule — it is a presentation choice. Capture it so the
target UI can replicate the appearance, but do not infer precision or sign
convention from it alone.

### Spacing keywords — section separators

| Keyword | Meaning |
|---|---|
| `SPACEA(n)` | Skip n lines **after** printing this format |
| `SPACEB(n)` | Skip n lines **before** printing this format |
| `SKIPA(n)` | Skip **to** line n after printing |
| `SKIPB(n)` | Skip **to** line n before printing |
| `SKIPA(01)` | Skip to line 1 = new page after printing |
| `SKIPB(01)` | Skip to line 1 before printing = new page before |

A `SKIPA(01)` or `SKIPB(01)` on a record format usually marks a page boundary.
A `SPACEA(2)` after a detail format and `SPACEA(1)` on a subtotal format means
detail lines are single-spaced and subtotals get a blank line before them.

### Overflow indicator (OVERFLOW keyword)

```
     A          R RPTDET                    OVERFLOW(OA)
```

`OVERFLOW(OA)` means indicator `OA` (overflow A) is set by the system when
printing this format would exceed the page length. The program tests `*INOA`
and decides whether to write a new page header before the next detail line.

### Constants (literal text)

```
     A                         10A   O  1  2 'REPORT TITLE'
```

A field with a literal value in quotes is a constant — printed text that never
changes. These are labels, headings, or column headers. Capture them for
report layout documentation but do not treat them as data fields.

---

## Evidence Boundaries

| Evidence | What it can prove | What it cannot prove alone |
| --- | --- | --- |
| PRTF DDS | Record formats, fields, constants, positions, spacing, page size, overflow, edit codes/masks | Which records print in what business sequence, total formulas, filters, sorting |
| RPG / COBOL / CL program evidence | WRITE order, O-specs, control-break tests, accumulator updates, OVRPRTF usage | SME meaning of a total or regulatory intent |
| Spool sample | Runtime appearance, page breaks in that run, observed subtotal/grand-total lines | General formulas unless reconciled to source/data |
| SME note | Business meaning, intended report use, whether a behavior is required | Source-level proof of exact implementation |

If PRTF DDS and program/spool evidence disagree, create a `TBD-*` instead of
choosing the smoother story.

## Common PRTF DDS Keywords and Constructs

### Page and Printer Definition

| Keyword / construct | Purpose | Analysis note |
| --- | --- | --- |
| `PAGESIZE` | Page length and width | Cite exact value and source line |
| `OVERFLOW` | Overflow line or condition | Confirms layout boundary, not full page-break behavior by itself |
| `SPACEA` / `SPACEB` | Space after / before a record format | Helps distinguish section spacing in spool |
| `SKIPA` / `SKIPB` | Skip after / before printing | May indicate page or section transitions |
| `PAGNBR` / page-number field | Page number output | Confirm display position and edit format |
| `EDTCDE` / `EDTWRD` / `EDTMSK` | Numeric formatting | Formatting only; not business calculation |
| `TEXT` / literals | Labels and headings | Labels are presentation evidence, not rule proof |

### Record Format Classification

PRTF DDS usually defines named record formats. Classify each format by
evidence, not by name alone:

| Role | Typical evidence |
| --- | --- |
| Page header | Written at page start or appears on each page in spool |
| Report header | Written once near report start |
| Column header | Repeating literals above detail rows |
| Detail | Repeated once per input record or line item |
| Subtotal / break | Appears when a grouped value changes; requires program/spool/SME evidence |
| Grand total / trailer | Appears at report end; requires program/spool/SME evidence |
| Exception / message | Printed only under error or special condition |

Do not treat record format names like `TOTAL`, `SUBTL`, or `HEADER` as proof
without WRITE order, O-spec, spool, or SME evidence.

## Report Structure Analysis

For each report, capture:

- Page dimensions and overflow definition
- Record formats and literal headings
- Field inventory with position, type, length, decimals, edit code/mask
- Record format roles with evidence source
- Program touchpoints: WRITE statements, O-specs, overrides, sorting/filtering
- Runtime reconciliation against spool samples
- Totals and counts as observed behaviors until source/SME confirms the formula

## Control Breaks and Totals

Control breaks and totals are load-bearing for downstream specifications. Use
this evidence ladder:

1. Program code or O-spec explicitly tests a control field and writes a break
   record.
2. Spool sample shows grouped detail rows followed by a subtotal and the input
   data supports the grouping.
3. SME confirms the intended break and total semantics.

If only a label such as `Customer Total` is visible, create a `SEED-*` or
`TBD-*`; do not mint a business rule.

### Total Classification

| Classification | Required evidence |
| --- | --- |
| Displayed total | Spool/report shows a total-like value |
| Layout total field | PRTF DDS has a field placed on a total/trailer format |
| Program-computed total | Program code accumulates or assigns the value |
| Business-approved total | SME confirms meaning and expected inclusion/exclusion rules |

## Spool Sample Reconciliation

When spool evidence is available:

1. Preserve fixed-width formatting.
2. Mark page boundaries, headings, detail rows, subtotals, trailers, and blank
   lines.
3. Reconcile each visible field to a PRTF field or literal when possible.
4. Reconcile totals only when the source rows in the same sample are sufficient.
5. Create `TBD-*` for missing pages, redacted amounts that prevent arithmetic
   checks, or unexplained totals.

## Common Anti-Patterns

1. **Treating PRTF layout as calculation logic.** A positioned amount field is
   not proof of the formula that produced it.
2. **Inferring control breaks from labels only.** `Department Total` is a hint,
   not proof of the break trigger.
3. **Using one redacted page as full report evidence.** Single-page samples
   rarely prove page overflow, repeated headers, or end-of-report trailers.
4. **Assuming all numeric fields are additive.** Counts, averages, rates,
   balances, and signs require source or SME evidence.
5. **Collapsing O-spec and PRTF DDS.** Record which artifact supplied each
   claim; do not call RPG output specs PRTF DDS.

## Review Checklist

- [ ] Page and printer settings are sourced from PRTF DDS or OVRPRTF evidence
- [ ] Each record format role is supported by source, WRITE order, spool, or SME evidence
- [ ] Every total/counter has an evidence classification
- [ ] Control-break fields are not inferred from labels alone
- [ ] Spool samples are redacted but still preserve fixed-width structure
- [ ] Any formula, inclusion rule, sort order, or filter becomes `TBD-*` unless evidenced
