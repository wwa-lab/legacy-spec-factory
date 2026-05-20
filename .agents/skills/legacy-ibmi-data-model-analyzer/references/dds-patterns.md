# DDS Pattern Recognition Guide

This guide helps identify and extract IBM i DDS constructs (physical files, logical files, record formats, fields, keys, and constraints) when analyzing data models.

## Physical File (PF) Structure

### Basic Format

```dds
     A                                      UNIQUE
     A          R RECNAME
     A            FIELD1        10A       COLHDG('Column One')
     A            FIELD2         5P 2     COLHDG('Decimal Field')
     A            FIELD3         8  0     COLHDG('Integer Field')
     A          K FIELD1
     A          K FIELD2
```

### Key DDS Keywords

| Keyword | Position | Meaning | Evidence Marker |
| --- | --- | --- | --- |
| R | 17-28 | Record format name | Start of record definition |
| A | 6-6 | DDS specification line | Indicates an active DDS spec line |
| K | 17-28 | Key field | Part of keyed access path; not by itself proof of uniqueness |
| FIELD | 9-14 | Field name | Exact field identifier |
| 10A | 30-39 | Type and length (A=alphanumeric) | Data type: A (char), B (binary), P (packed), S (zoned), F (float), blank for numeric |
| COLHDG | 44+ | Column heading | Metadata for display |
| EDTCDE | 44+ | Edit code (e.g., Z, A, Y) | Display format hint |
| ALWNULL | 44+ | Allow null values | DB2 compatibility indicator |

### Field Type Codes

| Code | Type | Example | Notes |
| --- | --- | --- | --- |
| A | Alphanumeric | CUSTNAME 30A | Text; blank padded |
| B | Binary | COUNT 4B 0 | Binary integer |
| P | Packed decimal | AMOUNT 9P 2 | Compressed numeric; format 9P2 means 9 digits, 2 decimals |
| S | Zoned decimal | AMOUNT 9S 2 | Readable numeric; each digit stored separately |
| F | Floating point | PRICE 8F | Double-precision floating point |

### Access Path Definition

```dds
     A          K FIELDNAME {A|D}          K = key, A = ascending (default), D = descending
```

Example:
```dds
     A          K CUSTNO
     A          K SALESMAN
     A          K CUSTDATE D               Descending sort for date
```

### Unique Access Path

```dds
     A                                      UNIQUE
     A          R CUSTREC
     A            CUSTNO        10A
     A          K CUSTNO
```

**Interpretation**: the access path over `CUSTNO` is unique because the DDS
`UNIQUE` keyword is present. If only `K CUSTNO` appears, document a keyed
access path, not a confirmed unique or business primary key.

## Logical File (LF) Structure

### Simple Logical File (Select/Omit)

```dds
     A          R RECNAME                  PFILE(PHYSFILE)
     A            FIELD1
     A            FIELD2
     A          K FIELD1                   Rekeys physical file
     A          K FIELD3
     A          S FIELD2       *NE ' '     SELECT: include only non-blank FIELD2
```

### Join Logical File

```dds
     A          R RECNAME                  JFILE(FILE1 FILE2)
     A            FIELD1                   FROM FILE1
     A            FIELD2                   FROM FILE1
     A            FIELD3                   FROM FILE2
     A          J                          Start join specification
     A            4                        JOIN TYPE: 1=inner, 4=left, 8=full
     A          JFLD(FILE1.JKEY FILE2.JKEY)  Join fields
     A          K FIELD1
     A          K FIELD2
     A          JDFTVAL(FILE2 'default')   Default value for unmatched FILE2 record
```

**Join Type Codes**:
- 1 = Inner join
- 4 = Left outer join
- 8 = Full outer join

### SELECT/OMIT Logic

```dds
     A          S FIELD1       *EQ 'A'     SELECT records where FIELD1 = 'A'
     A          O FIELD2       *GT 100     OMIT records where FIELD2 > 100
```

**Comparison Operators**:
- \*EQ = Equal
- \*NE = Not equal
- \*LT = Less than
- \*LE = Less than or equal
- \*GT = Greater than
- \*GE = Greater than or equal

### Key Lines for Reordering

```dds
     A          R LFREC
     A            CUSTNO                   FROM PHYSICAL FILE
     A            ORDNO
     A          K ORDNO                    Rekey on ORDNO (instead of CUSTNO from PF)
     A          K CUSTNO
```

## Record Format Rules

- **One per LF or PF section**: Multiple RECORD statements create multiple record formats
- **Field order**: Fields are listed in the order they appear in the file
- **Overlay fields**: OVERLAY keyword allows multiple interpretations of same bytes (rare)
- **RENAME**: LF can rename fields from PF; FIELD A RENAME(FIELD B) means use FIELD B from PF, call it FIELD A in LF

## Field Naming: The Dual-Name Model

IBM i DDS fields have two names, and they serve different audiences.

### System column name (DDS name)

The field name as declared in DDS. Maximum 10 characters. This is what:
- RPGLE programs use in C-specs (`CHAIN CUSTID CREDFILE`)
- EXTNAME DS subfields are named after
- Copybooks reference
- SETLL / READE key fields reference

### SQL column name (ALIAS name)

An optional longer name defined via the `ALIAS` DDS keyword. Used by:
- DB2 SQL queries (`SELECT CUSTOMER_ID FROM CREDFILE`)
- JDBC / ODBC connections
- Modern application layers

```dds
A          R CREDMST
A            CUSTID        9P 0   COLHDG('Cust ID')
A+                                ALIAS(CUSTOMER_ID)
A            CRDLMT        9P 2   COLHDG('Credit Limit')
A+                                ALIAS(CREDIT_LIMIT)
A            LSTUPD        8A     COLHDG('Last Update')
A+                                ALIAS(LAST_UPDATE_DATE)
A          K CUSTID
```

| DDS name (system) | SQL alias | RPGLE uses | Target DB uses |
|---|---|---|---|
| `CUSTID` | `CUSTOMER_ID` | `CUSTID` | `CUSTOMER_ID` |
| `CRDLMT` | `CREDIT_LIMIT` | `CRDLMT` | `CREDIT_LIMIT` |
| `LSTUPD` | `LAST_UPDATE_DATE` | `LSTUPD` | `LAST_UPDATE_DATE` |

**Modernization impact:** When migrating to a modern DB, the target column name
should come from `ALIAS` (if present) rather than the 10-char DDS name. If no
`ALIAS` is defined, the 10-char DDS name carries over — and the modernization
spec must decide whether to keep it or rename.

**Analysis rule:** Always document both names when `ALIAS` is present. Flag
mismatches between DDS name and ALIAS as a naming-convention decision point
for the modernization spec.

### TEXT keyword — field description source

The `TEXT` keyword is the DDS field's description. It is the closest thing to
a field-level comment and is the primary source for understanding what the field
means when variable names are cryptic.

```dds
A            CRDLMT        9P 2   TEXT('Customer credit limit in local currency')
```

Always extract `TEXT` values — they feed into data dictionary entries and field
documentation in the target system.

---

## Reference File Inheritance (REFFILE / REFFLD)

DDS allows fields to inherit attributes (type, length, decimals, TEXT, COLHDG)
from a reference physical file. This avoids duplication across related files.

```dds
A                                      REF(REFFILE)        File-level reference
A          R ORDREC
A            CUSTID    R              Field inherits type/length from REFFILE.CUSTID
A            AMOUNT    R   REFFLD(AMT *SRC)   Inherits from REFFILE field AMT
A            ORDDATE       8A         No R — explicit definition, no inheritance
```

### Reading reference-inherited fields

| DDS indicator | Meaning |
|---|---|
| `R` in col 29 (reference) | This field inherits type/length/decimals from the reference file |
| `REF(filename)` at file level | Sets the default reference file for all `R` fields |
| `REFFLD(field source)` | Override — inherit from a specific field name |
| No `R` | Explicitly defined; what you see is what you get |

**Analysis rule:** When you see `R` in the reference column and the field has
no explicit type/length, the actual type comes from the reference file's DDS.
If the reference file DDS is not in the inventory, the field type is unknown —
create a TBD.

```
TBD-<SLUG>-NNN: Provide DDS for reference file <REFFILE> — fields marked R
in <THISFILE> inherit type/length from it
```

---

## Evidence Collection

When extracting DDS:

1. **Source Location**: Note the source library, physical file name, and member name
   - Example: `SRCLIB/SRCPF(SRCMBR)` or `QSYS/QRPGLESRC(MYFILE)`

2. **Line Numbers**: Record the line number (column 5-8 in DDS) for each significant declaration
   - Example: "Key field CUSTNO declared at line 25"

3. **Complete Records**: Ensure all lines of a record definition are captured (from R card to next R card or EOF)
   - Watch for continuation lines (+ in column 6)

4. **No Truncation**: DDS lines can extend to column 80+ in fixed format; capture full content

## Common DDS Patterns

### Pattern: Multi-Field Keyed Access Path

```dds
     A          K COMPANY
     A          K BRANCH
     A          K CUSTNO
```

**Interpretation**: the access path is ordered by `(COMPANY, BRANCH, CUSTNO)`.
It is a confirmed unique or primary-key-like structure only when `UNIQUE`,
DB2 constraint metadata, or SME-confirmed current production evidence supports
that claim.

### Pattern: Unique Compound Access Path

```dds
     A                                      UNIQUE
     A          R CUSTALT
     A            TAXID         15A
     A            EMAIL         60A
     A          K TAXID
     A          K EMAIL
```

**Interpretation**: the compound key `(TAXID, EMAIL)` is unique only if the
`UNIQUE` keyword applies to that access path. Do not infer separate unique
constraints for each field unless separate DDS/DB2 evidence exists.

### Pattern: Selective Logical File

```dds
     A          S ACTIVE_FLAG  *EQ 'Y'
     A          S DELDATE      *BLANKS     Include only records with blank delete date
     A          O TESTFLAG     *EQ 'T'     Exclude test records
```

**Interpretation**: Include active records (ACTIVE_FLAG='Y') and non-deleted records (DELDATE blank), except test records.

### Pattern: Composite Join Key

```dds
     A          JFLD(PARENT.COMPANY CHILD.COMPANY)
     A          JFLD(PARENT.CUSTNO CHILD.CUSTNO)
```

**Interpretation**: Join on compound key (COMPANY, CUSTNO).

## Gotchas and Ambiguities

1. **Whitespace**: DDS is position-sensitive in fixed format; columns 6-80 are meaningful
2. **Comments**: \* in column 7 indicates comment line; ignore it
3. **Continuation**: + in column 6 continues the previous line; merge before parsing
4. **Field Names**: Must match between PF and LF when not renamed
5. **Implicit Keys**: If an LF does not declare key lines, verify whether it
   inherits or exposes the base access path in that shop's metadata before
   making a claim; otherwise create a TBD
6. **Join Order**: JFILE(A B) means A is left table, B is right table
7. **Multiple Record Formats**: One PF can have multiple RECORD sections; LF can select which to expose

---

Generated by legacy-ibmi-data-model-analyzer v0.1.0
Legacy Spec Factory Copyright 2026 Leo L Zhang
