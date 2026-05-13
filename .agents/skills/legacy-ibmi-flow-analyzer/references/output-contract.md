# Output Contract: Flow Analysis

This document defines the precise shape and required fields for every
`flow-<FLOW-SLUG>.md` artifact.

## File Structure

```markdown
# Flow Analysis: [Business Event Name] (FLOW-*)

## Metadata
## Trigger Context
## Sequence Diagram
## Nodes (Programs in the Chain)
## Edges (Calls Between Nodes)
## Cross-Program Data Flow
## Branch Points
## UI Surfaces                       (N/A for non-interactive flows)
## Error Propagation & Commit Boundaries
## Business Capability Seeds
## TBDs & Blocking Status
## Review Checklist
```

---

## Metadata Section

```markdown
## Metadata

- **Flow ID:** FLOW-ONUS-AUTH-001
- **Business Event Name:** On-Us Card Authorization (online)
- **Trigger Model:** API / Remote (Visa inbound auth request)
- **Module:** [MODULE-SLUG] (e.g., CARD-AUTH)
- **Entry Node:** OBJ-AUTH-ONUS-001 (program CU101A)
- **Exit Node(s):** OBJ-AUTH-ONUS-014 (program CU199Z, returns response to Visa)
- **Runtime Model:** synchronous, real-time, sub-second SLA
- **Status:** draft | needs_sme_review | approved
```

---

## Trigger Context Section

Describe **how the flow starts** in enough detail that an SME can confirm
or correct. The format depends on the trigger model — see
`trigger-models.md`. Common required fields:

- Trigger artifact (CL name, MENU + option, DSPF + option / F-key,
  trigger registration, scheduler entry, API contract)
- Source line / configuration reference for the trigger
- Caller (who invokes — user role, scheduler, external system, internal
  program)
- Frequency / cadence
- SLA expectation (if any)
- Authentication / authorization context (if external)
- Evidence link

---

## Sequence Diagram Section

ASCII sequence diagram showing the call chain. Use the same column
spacing convention as the IBM i flow-header tree.

```markdown
### Sequence Diagram

Source: derived-from-code + SME confirmed | header (if present) | both (matched)

```text
[Visa Inbound]
    │
    ▼
NODE-01 (CU101A)  ── validates auth request, derives currency
    │
    ▼
NODE-02 (CU110A)  ── calls credit-check
    │   │
    │   └─→ NODE-03 (CU111S)  ── credit limit lookup (SQLRPG)
    │
    ▼
NODE-04 (CU120A)  ── extracts track data, classifies recurring
    │
    ▼
NODE-05 (CU130A)  ── CVV validation
    │
    ▼
NODE-06 (CU199Z)  ── builds response, returns to Visa
    │
    ▼
[Visa Outbound response]
```

**Evidence:**
- [EV-...-001: CU101A CALLP CU110A, line 245]
- [EV-...-002: CU110A CALLP CU111S, line 312]
- ...
```

For interactive flows include UI surfaces inline:

```text
[User on MENU CMENU100, option 5]
    │
    ▼
NODE-01 (CU200A)  ── shows DSPF CU200D (customer lookup)
    │
    │  User enters CustID, presses Enter
    ▼
NODE-01 (CU200A)  ── validates input, calls lookup
    │
    ▼
NODE-02 (CU201A)  ── customer record lookup
    │
    ▼
NODE-01 (CU200A)  ── shows DSPF CU200D2 (customer detail subfile)
    │
    │  User selects option 5=Display next to row
    ▼
NODE-03 (CU205A)  ── customer history detail
```

---

## Nodes Section

```markdown
### Nodes

| Node ID | Program (OBJ-*) | Role | Program Analysis | Notes |
| --- | --- | --- | --- | --- |
| NODE-ONUS-AUTH-01 | CU101A (OBJ-AUTH-ONUS-001) | Entry / validator | `program-analysis-OBJ-AUTH-ONUS-001.md` | Validates inbound payload format |
| NODE-ONUS-AUTH-02 | CU110A (OBJ-AUTH-ONUS-002) | Credit orchestrator | `program-analysis-OBJ-AUTH-ONUS-002.md` | Calls credit-check sub-flow |
| NODE-ONUS-AUTH-03 | CU111S (OBJ-AUTH-ONUS-003) | Data access (SQLRPG) | `program-analysis-OBJ-AUTH-ONUS-003.md` | DB2 cursor over credit-history |
| ... | ... | ... | ... | ... |
```

**Role taxonomy:**
- `entry` — first program in the chain after the trigger
- `validator` — input validation, preliminary checks
- `orchestrator` — calls other programs; mostly control flow
- `worker` — does the actual business logic
- `data-access` — primarily DB I/O (SQLRPG, native I/O wrappers)
- `reporter` — produces PRTF / spool / file output
- `exit` — last program; returns response or commits

**Requirements:**
- Every Node must have an approved `program-analysis-<OBJ-ID>.md`. If
  not → blocking TBD (route back to program-analyzer).
- Node IDs are sequence-numbered (`NODE-<SLUG>-01`, `NODE-<SLUG>-02`, …).
- A program that is called multiple times in different roles may appear
  as multiple nodes (with different sequence numbers), or as one node
  with multiple inbound edges — pick what the SME finds clearer.

---

## Edges Section

```markdown
### Edges

| Edge ID | From → To | Call Type | Site (program:line) | Condition | Evidence |
| --- | --- | --- | --- | --- | --- |
| EDGE-ONUS-AUTH-01 | (trigger) → NODE-01 | API inbound | (Visa contract) | always | EV-ONUS-AUTH-001 |
| EDGE-ONUS-AUTH-02 | NODE-01 → NODE-02 | CALLP | CU101A:245 | if validation passed | EV-ONUS-AUTH-002 |
| EDGE-ONUS-AUTH-03 | NODE-02 → NODE-03 | CALLP | CU110A:312 | always | EV-ONUS-AUTH-003 |
| EDGE-ONUS-AUTH-04 | NODE-02 → NODE-04 | CALLP | CU110A:330 | if credit OK | EV-ONUS-AUTH-004 |
| EDGE-ONUS-AUTH-05 | NODE-04 → NODE-05 | CALLP | CU120A:185 | always | EV-ONUS-AUTH-005 |
| EDGE-ONUS-AUTH-06 | NODE-05 → NODE-06 | CALLP | CU130A:90 | always | EV-ONUS-AUTH-006 |
```

**Call types:** `CALL`, `CALLP`, `CALLPRC` (service program), `SBMJOB`,
`trigger-fire`, `API-inbound`, `MENU-option`, `subfile-option`, `F-key`,
`scheduler-fire`, `DTAQ-receive`

**Condition examples:** `always`, `if validation passed`, `in loop per
record`, `error path`, `option = 4`, `F6 pressed`

---

## Cross-Program Data Flow Section

Document **what** travels along each edge. See `data-flow-patterns.md`.

```markdown
### Cross-Program Data Flow

| Data ID | On Edge | Mechanism | Payload | Direction | Evidence |
| --- | --- | --- | --- | --- | --- |
| DATA-ONUS-AUTH-01 | EDGE-02 | CALL parameters | CustID, CardNo, Amount, Currency | NODE-01 → NODE-02 | EV-... |
| DATA-ONUS-AUTH-02 | EDGE-02 | CALL parameter (out) | Decision, AuthCode, ErrorMsg | NODE-02 → NODE-01 | EV-... |
| DATA-ONUS-AUTH-03 | (out of band) | Shared data area HSSDTAR002 | BatchRunDate | written by NODE-02, read by NODE-04 | EV-... |
| DATA-ONUS-AUTH-04 | EDGE-04 | DTAQ ONUSDTAQ | TxnLogMessage | NODE-04 produces, NODE-06 consumes | EV-... |
| DATA-ONUS-AUTH-05 | (file) | PF TXNLOGPF | full transaction record | NODE-04 writes, NODE-06 reads for response | EV-... |
```

**Mechanism taxonomy:**
- `CALL parameters` — passed in call (in / out / inout per parameter)
- `Shared data area` — `*DTAARA` written by one node, read by another
- `Data queue` — `*DTAQ` SNDDTAQ / RCVDTAQ between nodes
- `Shared file` — PF or LF written by one, read by another (with key)
- `Shared work file` — temp file with explicit lifecycle
- `Spool / PRTF` — output for downstream consumption
- `Activation-group globals` — variables shared via ACTGRP

**Required:** every entry traces to source (parameter declaration, data
area access, queue send / receive, file write / read).

---

## Branch Points Section

```markdown
### Branch Points

| Branch ID | Location (node + line) | Decider | Alternatives | Evidence |
| --- | --- | --- | --- | --- |
| BR-ONUS-AUTH-01 | NODE-02 CU110A:300 | Decision field from credit check | A → continue to NODE-04; D → return decline to NODE-01 | EV-... |
| BR-ONUS-AUTH-02 | NODE-05 CU130A:140 | CVV match result | matched → continue; mismatched → reject path | EV-... |
```

**Unhandled branch destinations** (e.g., an option code the dispatcher
doesn't recognize) must be listed explicitly. If unhandled → TBD.

---

## UI Surfaces Section

For interactive flows only. Otherwise: `N/A — non-interactive flow`.

```markdown
### UI Surfaces

| Surface ID | Object | Type | Displayed By | Key Fields | F-Keys Handled | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| UI-CUST-LOOKUP-01 | CU200D | DSPF | NODE-01 (CU200A) | CustID | F3=Exit, F6=New, F12=Cancel | EV-... |
| UI-CUST-LOOKUP-02 | CU200D2 | DSPF (subfile) | NODE-01 (CU200A) | CustID, CustName, Status | F3, F6, F12; subfile options 5=Display, 9=Approve | EV-... |
```

---

## Error Propagation & Commit Boundaries Section

See `error-propagation.md` for full guidance.

```markdown
### Error Propagation

| Error Source | Detected At | Propagation Path | Final Outcome | Commit Behavior | Evidence |
| --- | --- | --- | --- | --- | --- |
| Credit-check failure | NODE-03 (CU111S) | RC=-1 returned to NODE-02, which sets Decision='D', returns to NODE-01 | Decline response to Visa | nothing committed (read-only) | EV-... |
| CVV mismatch | NODE-05 | logged to QSYSOPR, returned to NODE-04, response built by NODE-06 | Decline response + log audit row in TXNLOGPF | TXNLOGPF write committed | EV-... |
| DB read I/O error in CU111S | NODE-03 | unhandled (no MONITOR) | flow aborts; Visa times out | nothing committed | needs_sme_review per TBD |

### Commit Boundaries

The flow has the following commit boundaries:

- **Boundary 1:** NODE-04 writes TXNLOGPF (committed implicitly at WRITE)
- **Boundary 2:** NODE-06 sends response to Visa (final, irrevocable)

Between Boundary 1 and Boundary 2 there is a window: if NODE-06 fails,
TXNLOGPF has a row but Visa got no response. Visa will retry. → TBD:
confirm idempotency strategy.
```

---

## Business Capability Seeds Section

Each seed is a **question for SME**, with pointers — *never* an asserted
rule.

```markdown
### Business Capability Seeds

These seeds are candidate business rules and capabilities suggested by
the flow structure. SME and `legacy-spec-writer` resolve them; the
flow analyzer does not declare rules.

| Seed ID | Candidate Rule / Capability | Suggested By | SME Question |
| --- | --- | --- | --- |
| SEED-ONUS-AUTH-01 | Credit limit must be respected on every authorization | NODE-02 CU110A always calls credit check before approval | Is the rule "no auth above credit limit" enforced here, or partially? |
| SEED-ONUS-AUTH-02 | CVV/CVC verification required for ATMP transactions | NODE-05 conditional on transaction-type field | Is CVV verification required for all transactions or only ATMP? |
| SEED-ONUS-AUTH-03 | Transaction must be logged before response | NODE-04 writes TXNLOGPF before NODE-06 builds response | Is logging a hard requirement (audit), or is best-effort acceptable? |
```

---

## TBDs & Blocking Status Section

Same conventions as program-analyzer. Group by:

- **Pending Source** — missing program-analysis, missing DSPF, missing
  copybook
- **Pending SME Judgment** — trigger model unclear, error intent unclear,
  capability seed unanswered
- **Non-Blocking** — known gaps that don't affect downstream

---

## Review Checklist Section

```markdown
### Review Checklist

Before approval, SME must validate:

- [ ] Trigger model correctly identified
- [ ] Business event name accurately reflects the business transaction
- [ ] All nodes in scope (no missing, no extras)
- [ ] All edges reflect actual production calls
- [ ] Cross-program data flow is complete
- [ ] Branch points capture user-visible decisions
- [ ] UI surfaces match production screens (interactive flows only)
- [ ] Error propagation matches operational reality
- [ ] Commit boundaries correctly identified
- [ ] Capability seeds are reasonable questions, not invented rules
- [ ] All node program-analyses are approved

### SME Sign-Off

- **Reviewer:** ____________________
- **Review Date:** __________________
- **Decision:** approved | approved_with_non_blocking_tbd | rejected
- **Notes:** ____________________
```

---

## ID Conventions for Flow Analysis

| Prefix | Artifact | Example |
|---|---|---|
| `FLOW-` | the flow itself | `FLOW-ONUS-AUTH-001` |
| `NODE-` | one program participating in the flow | `NODE-ONUS-AUTH-03` |
| `EDGE-` | one call between two nodes | `EDGE-ONUS-AUTH-04` |
| `DATA-` | one data exchange (parameter set, DTAARA, DTAQ, shared file) | `DATA-ONUS-AUTH-02` |
| `BR-` | a branch point in the flow | `BR-ONUS-AUTH-01` |
| `UI-` | a UI surface (DSPF / PRTF / MENU) | `UI-ONUS-AUTH-01` |
| `SEED-` | a business-capability seed (question for SME) | `SEED-ONUS-AUTH-02` |
| `TBD-` | an open question | `TBD-ONUS-AUTH-005` |
| `EV-` | a piece of evidence | `EV-ONUS-AUTH-012` |

All IDs scope-prefixed by FLOW-SLUG so they remain unique across modules.
