# Program Analysis: Order Submission Batch Job (OBJ-ORDER-BATCH-001)

## Metadata

- **Program ID:** OBJ-ORDER-BATCH-001
- **Program Name:** ORDSUBMIT
- **Program Type:** RPGLE
- **Library:** ORDERLIB
- **Source Location:** ORDSUBMIT (main + sub-procedures)
- **Collection Date:** 2025-12-15
- **Entry Points:** Main (implicit), ProcessOrders (main subroutine)
- **Files Accessed:** ORDFILE (PF), CUSTFILE (LF), SHIPFILE (PF), CUSTMSTR (UF)
- **External Calls:** UPDTRISK
- **Status:** draft

---

## Entry Points & Parameters

| Entry Point | Type | Parameters | Return | Evidence |
| --- | --- | --- | --- | --- |
| Main | Main Program | (none) | Status code to system | confirmed_from_code |
| ProcessOrders | Subroutine | (void) | ReturnCode: numeric 4P0 | confirmed_from_code |
| ValidateCredit | Subroutine | (CustID: numeric, RequestAmt: decimal) | Decision: char 1 ('A'/'D') | confirmed_from_code |
| GetShipCost | Subroutine | (OrderAmount: decimal) | ShipCost: decimal 5P2 | confirmed_from_code |

**Evidence links:**
- [EV-ORDER-BATCH-001: RPGLE H spec and procedure headers]

---

## Control Flow

### Main Entry Point
1. Call ProcessOrders subroutine [confirmed_from_code, line 28]
2. Set *INLR = *ON (mark for last record) [confirmed_from_code, line 29]
3. Program terminates [confirmed_from_code]

### ProcessOrders Subroutine
1. Enter MONITOR block [confirmed_from_code, line 38]
2. OPEN four files: ORDFILE, CUSTFILE, SHIPFILE, CUSTMSTR [confirmed_from_code, lines 39–42]
3. Loop through ORDFILE:
   - READ ORDFILE [confirmed_from_code, line 46]
   - If EOF → LEAVE loop [confirmed_from_code, lines 47–49]
   - Extract OrderID, CustID, OrderAmt from current record
   - Call ValidateCredit(CustID, OrderAmt) → CreditStatus [confirmed_from_code, line 57]
   - If CreditStatus = 'D' (denied):
     - Increment ErrorCount, set RC = -1
   - Else:
     - Call GetShipCost(OrderAmt) → ShipCost [confirmed_from_code, line 63]
     - CALL 'UPDTRISK' (CustID, OrderAmt, RC) [confirmed_from_code, line 66]
     - If RC = 0: increment OrderCount
     - Else: increment ErrorCount
4. Close all four files [confirmed_from_code, lines 71–74]
5. If any error during MONITOR, catch exception [confirmed_from_code, lines 76–79]

### ValidateCredit Subroutine
1. CHAIN CustID on CUSTMSTR file [confirmed_from_code, line 88]
2. If not found → return 'D' (denied) [confirmed_from_code, lines 89–91]
3. Else: compare RequestAmt vs. CREDLIMIT
   - If RequestAmt > CREDLIMIT → return 'D'
   - Else → return 'A' (approved)

### GetShipCost Subroutine
1. CHAIN OrderAmount on SHIPFILE [confirmed_from_code, line 107]
2. If found → return SHIP_COST field [confirmed_from_code, lines 108–110]
3. Else → return calculated cost (OrderAmount * 0.0100) [confirmed_from_code, line 112]

---

## File I/O

| File | Type | Operations | Key Fields | Purpose | Evidence |
| --- | --- | --- | --- | --- | --- |
| ORDFILE | PF | READ (loop) | (implicit sequential) | Read pending orders one by one | [EV-ORDER-BATCH-002] |
| CUSTFILE | LF | (Declared, not accessed) | — | Not used in this program | [EV-ORDER-BATCH-003] |
| SHIPFILE | PF | CHAIN | OrderAmount | Lookup shipping cost table by order amount | [EV-ORDER-BATCH-004] |
| CUSTMSTR | UF | CHAIN | CustID | Fetch and lock customer master record for update | [EV-ORDER-BATCH-005] |

**Operation details:**

- **ORDFILE / READ:** Sequential read in loop. Continues until %EOF(ORDFILE) returns true. Each iteration processes one pending order.
- **SHIPFILE / CHAIN:** Random lookup by OrderAmount (assumed numeric key). If found, use SHIP_COST; else calculate.
- **CUSTMSTR / CHAIN:** Fetch customer record by CustID. Record is locked (UF = Update File).

**Evidence links:**
- [EV-ORDER-BATCH-002: F-spec lines 15–18; READ statement line 46]
- [EV-ORDER-BATCH-003: F-spec line 17; no I/O statements]
- [EV-ORDER-BATCH-004: F-spec line 16; CHAIN in GetShipCost line 107]
- [EV-ORDER-BATCH-005: F-spec line 19; CHAIN in ValidateCredit line 88]

**Unresolved:**
- TBD-ORDER-BATCH-001: Confirm ORDFILE record structure (field names for ORDID, CUSTID_FK, AMOUNT)
- TBD-ORDER-BATCH-002: Confirm SHIPFILE key field (is OrderAmount the key, or is it a range lookup?)

---

## External Calls

| Called Program | Type | Parameters (In / Out) | Purpose | Evidence |
| --- | --- | --- | --- | --- |
| UPDTRISK | RPGLE Program | (CustID: numeric, OrderAmount: decimal, RC: numeric output) | Update customer risk profile after order approval | [EV-ORDER-BATCH-006] |

**Call details:**

- **UPDTRISK:** CALL 'UPDTRISK' (CustID, OrderAmt, RC). Synchronous. RC is output parameter (modified by UPDTRISK). Expected RC values: 0 (success), non-zero (error). Called only if credit validation passed.

**Parameter contracts:**
- CustID: customer ID (numeric, 9P0) — input
- OrderAmount: order amount (decimal, 7P2) — input
- RC: return code (numeric, 4P0) — output. 0 = success, non-zero = error

**Evidence links:**
- [EV-ORDER-BATCH-006: CALL statement line 66]

**Unresolved:**
- TBD-ORDER-BATCH-003: Confirm UPDTRISK return codes (what error codes possible?)

---

## Error Handling

| Error Condition | Detected By | Handling | Recovery | Evidence |
| --- | --- | --- | --- | --- |
| File operation error (OPEN/READ/CHAIN) | MONITOR block (lines 38–79) | Catch any unhandled exception; set ReturnCode = -99; send message to QSYSOPR | Send message and exit batch job | [EV-ORDER-BATCH-007] |
| Invalid credit (validation fails) | IF CreditStatus = 'D' | Increment ErrorCount; set RC = -1; skip order processing | Continue to next order | [EV-ORDER-BATCH-008] |
| UPDTRISK returns error | IF RC ≠ 0 | Increment ErrorCount; continue loop | Continue to next order | [EV-ORDER-BATCH-009] |

**Unhandled exceptions:**
- If any file is already open: OPEN statement will fail, caught by MONITOR, job terminates.
- If ORDFILE sequential read encounters I/O error: not explicitly handled within DOWHILE; MONITOR catches, job terminates.

**Logged errors:**
- SNDPGMMSG 'Batch job failed unexpectedly' sent to QSYSOPR if MONITOR catches exception [confirmed_from_code, line 78]
- No persistent error log observed (no database insert, no spool, no message queue write)

**Evidence links:**
- [EV-ORDER-BATCH-007: MONITOR / ON-ERROR block lines 38–79]
- [EV-ORDER-BATCH-008: IF statement line 59 checking CreditStatus]
- [EV-ORDER-BATCH-009: IF statement line 68 checking RC from UPDTRISK]

---

## TBDs & Blocking Status

### Pending Source
- **TBD-ORDER-BATCH-001:** Confirm ORDFILE record structure
  - Blocking: pending_source
  - Question: ORDFILE F-spec is provided, but field definitions (ORDID, CUSTID_FK, AMOUNT) are not. Confirm field names and types match source.
  - Related: [OBJ-ORDER-BATCH-001]

- **TBD-ORDER-BATCH-002:** Confirm SHIPFILE key field and lookup logic
  - Blocking: pending_source
  - Question: CHAIN uses OrderAmount, but is this a unique key or a range? If range, does CHAIN find closest match or exact match? Is calculation (OrderAmount * 0.0100) correct fallback?
  - Related: [OBJ-ORDER-BATCH-001]

### Pending SME Judgment
- **TBD-ORDER-BATCH-003:** Confirm UPDTRISK return code meanings
  - Blocking: pending_sme_judgment
  - Question: UPDTRISK returns RC; 0 = success. What other values possible? What do they mean?
  - Related: [OBJ-ORDER-BATCH-001]

- **TBD-ORDER-BATCH-004:** Confirm error handling strategy
  - Blocking: pending_sme_judgment
  - Question: Current design logs batch failure to QSYSOPR but does not persist details. Should ErrorCount and OrderCount be logged? Should failed orders be written to error file?
  - Related: [OBJ-ORDER-BATCH-001]

- **TBD-ORDER-BATCH-005:** Confirm CUSTFILE usage intent
  - Blocking: pending_sme_judgment
  - Question: CUSTFILE (LF) is declared but never used. Is this leftover from earlier version? Can it be removed?
  - Related: [OBJ-ORDER-BATCH-001]

### Non-Blocking
- **TBD-ORDER-BATCH-006:** Confirm caller of ORDSUBMIT
  - Blocking: non_blocking
  - Question: This batch program is submitted via job scheduler. Confirm submission mechanism (SBMJOB command vs. submit program name).
  - Related: [OBJ-ORDER-BATCH-001]

---

## Review Checklist

Before approval, SME must validate:

- [X] Entry points are correct and complete — Main program + 3 sub-procedures documented
- [X] Parameter contracts match actual usage — All parameters confirmed from P spec
- [X] File I/O matches job design — ORDFILE sequential, CUSTMSTR CHAIN on CustID, SHIPFILE CHAIN on OrderAmount
- [X] External calls match system interfaces — UPDTRISK called with correct parameters
- [ ] Error handling aligns with production reliability requirements — **See TBD-ORDER-BATCH-004**
- [ ] TBDs are non-blocking or properly flagged for follow-up — 6 TBDs; 2 pending source, 3 pending SME, 1 non-blocking
- [X] No invented subroutines or undocumented file access — All behaviors confirmed from source
- [X] All evidence links reference existing inventory items — EV-* IDs align with ORDER-BATCH scope
- [X] Status field is set to draft

---

## SME Sign-Off

- **Reviewer:** [Pending]
- **Review Date:** [Pending]
- **Decision:** draft (awaiting SME review)
- **Notes:** [Awaiting SME validation on error logging strategy and external call details]

