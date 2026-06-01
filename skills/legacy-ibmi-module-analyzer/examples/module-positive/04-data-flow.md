# View 4: Data Flow — Card Authorization

## Status: draft → needs_sme_review

## Mermaid Flow Diagram

```mermaid
flowchart LR
  FLOW_ONUS_AUTH["FLOW-ONUS-AUTH"] -->|reads| DATA_CUSTMSTR["CUSTMSTR"]
  FLOW_ONUS_AUTH -->|reads via CREDITCHK| DATA_CREDFILE["CREDFILE"]
  FLOW_MANUAL_AUTH["FLOW-MANUAL-AUTH"] -->|reads| DATA_CUSTMSTR
  FLOW_MANUAL_AUTH -->|reads via CREDITCHK| DATA_CREDFILE
  FLOW_ONUS_AUTH -->|creates auth row| DATA_TXNLOGPF["TXNLOGPF"]
  FLOW_MANUAL_AUTH -->|creates manual auth row| DATA_TXNLOGPF
  DATA_TXNLOGPF -->|read by nightly run| FLOW_NIGHTLY_RECON["FLOW-NIGHTLY-RECON"]
  FLOW_NIGHTLY_RECON -->|creates| DATA_GLPOSTPF["GLPOSTPF"]
  FLOW_NIGHTLY_RECON -->|updates checkpoint| DATA_HSSDTAR002["HSSDTAR002"]
  FLOW_NIGHTLY_RECON -->|sends async| DATA_RECONDTAQ["RECONDTAQ"]
  FLOW_NIGHTLY_RECON -->|prints| DATA_RECONPRT["RECONPRT"]
  DATA_GLPOSTPF -->|SFTP handoff| SYS_GL_SYSTEM["GL System"]
  DATA_RECONDTAQ -->|consumed by| SYS_RISK_MONITORING["Risk Monitoring"]
  DATA_RECONPRT -->|manual review| ACTOR_FINANCE_ANALYST["Finance Analyst"]
```

## Data Objects in Scope

| Object | Type | Inventory ID | Producer Flows | Consumer Flows | Coupling Score | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| TXNLOGPF | PF | OBJ-CARD-AUTH-050 | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH | FLOW-NIGHTLY-RECON | 3 (HIGH) | EV / object-deps in all 3 flows |
| CUSTMSTR | PF | OBJ-CARD-AUTH-080 | (external — CUSTOMER-MASTER module) | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH | 2 (read-only here) | EV |
| CREDFILE | PF (DS) | OBJ-CARD-AUTH-081 | (external — CUSTOMER-MASTER module) | FLOW-ONUS-AUTH (via CREDITCHK), FLOW-MANUAL-AUTH (via CREDITCHK) | 2 | EV |
| GLPOSTPF | PF | OBJ-CARD-AUTH-060 | FLOW-NIGHTLY-RECON | (external — GL system) | 1 (outbound) | EV |
| RECONDTAQ | *DTAQ | OBJ-CARD-AUTH-070 | FLOW-NIGHTLY-RECON | (external — Risk Monitoring) | 1 | EV |
| RECONPRT | PRTF | OBJ-CARD-AUTH-071 | FLOW-NIGHTLY-RECON | (manual — Finance Analyst) | 1 | EV |
| HSSDTAR002 | *DTAARA | OBJ-CARD-AUTH-090 | FLOW-NIGHTLY-RECON | FLOW-NIGHTLY-RECON | 1 (internal) | EV |
| AUTHTPDS | PF (DS) | OBJ-CARD-AUTH-018 | (external — Visa interface) | FLOW-ONUS-AUTH | 1 | EV |

## Data Lifecycle

| Object | Created By | Updated By | Read By | Archived By | Purged By |
| --- | --- | --- | --- | --- | --- |
| TXNLOGPF | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH (per auth) | (append-only — never updated) | FLOW-NIGHTLY-RECON | monthly archive job (external — out of module) | yearly purge (external) |
| GLPOSTPF | FLOW-NIGHTLY-RECON | (none — single write per row) | GL system (external) | weekly truncate after GL SFTP confirmed (external) | n/a |
| HSSDTAR002 | FLOW-NIGHTLY-RECON (read-modify-write each day) | FLOW-NIGHTLY-RECON | FLOW-NIGHTLY-RECON | n/a (overwritten daily) | n/a |
| RECONPRT | FLOW-NIGHTLY-RECON (daily spool) | n/a | Finance Analyst (manual) | spool retention 30 days (system policy) | system spool purge |

## Module Persistence Matrix

| Object / Field / Output | Producer Flows (`PERSIST-*`) | Consumer Flows / Systems | Operation Summary | Commit / Retry / Recovery Notes | Evidence |
| --- | --- | --- | --- | --- | --- |
| TXNLOGPF.AUTH_STATUS | FLOW-ONUS-AUTH-001 (`PERSIST-ONUS-AUTH-001`), FLOW-MANUAL-AUTH-001 (`PERSIST-MANUAL-AUTH-001`) | FLOW-NIGHTLY-RECON-001 | append authorization result before external/menu response | failed write returns decline / validation error; no automatic retry observed | flow persistence matrices + TXNLOGWR program analysis |
| GLPOSTPF.POST_AMT | FLOW-NIGHTLY-RECON-001 (`PERSIST-NIGHTLY-RECON-001`) | GL System | creates GL posting rows after reconciliation | skipped when `EXCHAIN-NIGHTLY-RECON-001` threshold breach fires | RECONSQL program analysis |
| RECONPRT spool output | FLOW-NIGHTLY-RECON-001 (`PERSIST-NIGHTLY-RECON-002`) | Finance Analyst | prints daily exception report | always generated on exception threshold breach; manual review required | flow persistence matrix |
| HSSDTAR002.LAST_RUN_DATE | FLOW-NIGHTLY-RECON-001 (`PERSIST-NIGHTLY-RECON-003`) | FLOW-NIGHTLY-RECON-001 | checkpoint update after successful run | partial restart behavior pending SME confirmation | TBD-CARD-AUTH-DAT-003 |

## Critical Field Lineage Across Module

| Critical Field / Business Data | Source Flows (`LINEAGE-*`) | Carriers | Persisted / Output Locations | Consumers | TBD / Risk |
| --- | --- | --- | --- | --- | --- |
| Authorization decision | FLOW-ONUS-AUTH-001 (`LINEAGE-ONUS-AUTH-001`), FLOW-MANUAL-AUTH-001 (`LINEAGE-MANUAL-AUTH-001`) | request DS → CREDITCHK work fields → TXNLOGWR | TXNLOGPF.AUTH_STATUS, MQ/menu response | card network, CSR, nightly recon | none |
| Credit exposure / available limit | FLOW-ONUS-AUTH-001 (`LINEAGE-ONUS-AUTH-002`), FLOW-MANUAL-AUTH-001 (`LINEAGE-MANUAL-AUTH-002`) | CREDFILE fields → CREDITCHK result | transient validation result; not stored separately | authorization decision | field semantics require CUSTOMER-MASTER contract |
| Exception threshold count | FLOW-NIGHTLY-RECON-001 (`LINEAGE-NIGHTLY-RECON-001`) | TXNLOGPF exception rows → RECONSQL count → threshold compare | RECONPRT, RECONDTAQ, GLPOSTPF skipped / written | Finance Analyst, Risk Monitoring, GL System | TBD-CARD-AUTH-002 |

## Exception-Aware Data Risks

| Exception Chain | Data / Persist Impact | Recovery / Manual Action | Evidence / TBD |
| --- | --- | --- | --- |
| `EXCHAIN-ONUS-AUTH-001` MQ timeout | MQ response may fail after TXNLOGPF write; partner retry may create duplicate attempt | upstream retry ownership; idempotency strategy pending | TBD-CARD-AUTH-DAT-001 |
| `EXCHAIN-NIGHTLY-RECON-001` RC=-2 threshold breach | GLPOSTPF write skipped or deferred; RECONPRT and RECONDTAQ still produced | Finance Analyst daily review, Card Ops escalation | TBD-CARD-AUTH-002 |

## Coupling Hotspots (Modernization Risks)

| Object | Coupling Score | Risk | Mitigation |
| --- | --- | --- | --- |
| TXNLOGPF | HIGH (3 flows) | Schema change ripples through 3 flows + downstream nightly recon | Versioned record format; backward-compatible adds only; coordinate releases of all 3 flows |
| CUSTMSTR | MEDIUM (2 flows, read-only here) | Owned by CUSTOMER-MASTER module; we depend on its schema stability | Cross-module schema contract required |

## Critical Data Trails

**Authorization → Audit → Reconciliation → GL trail:**

```mermaid
flowchart TD
  TRAIL_VISA["Visa MQ inbound"]
  TRAIL_AUTH["FLOW-ONUS-AUTH NODE-04"]
  TRAIL_TXNLOGPF["TXNLOGPF one row per transaction"]
  TRAIL_RECON["FLOW-NIGHTLY-RECON NODE-02 reads run-date rows"]
  TRAIL_GLPOSTPF["GLPOSTPF aggregated GL postings"]
  TRAIL_GL["GL system via nightly SFTP"]
  TRAIL_ARCHIVE["Archive monthly job (external)"]

  TRAIL_VISA --> TRAIL_AUTH --> TRAIL_TXNLOGPF --> TRAIL_RECON --> TRAIL_GLPOSTPF --> TRAIL_GL --> TRAIL_ARCHIVE
```

## DB Table Relationships

| Parent | Child | FK | Notes |
| --- | --- | --- | --- |
| CUSTMSTR (CustID PK) | CREDFILE (CustID FK) | CustID | Customer master → credit profile |
| TXNLOGPF (TxnID PK) | GLPOSTPF (TxnID FK) | TxnID | One transaction → one or more GL posting rows |

## Cross-Module Data Dependencies

| Object | Owned By Module | Used By This Module | Mechanism | TBD? |
| --- | --- | --- | --- | --- |
| CUSTMSTR | CUSTOMER-MASTER | CARD-AUTH (read-only via CHAIN) | Direct file access | needs cross-module agreement (TBD-CARD-AUTH-001 captured in overview) |
| CREDFILE | CUSTOMER-MASTER | CARD-AUTH (read-only via EXTNAME) | Direct DDS reference | same TBD |
| GLPOSTPF | CARD-AUTH (we produce) | GL System (external) | File handoff + SFTP | confirmed via integration spec |

## TBDs

### Pending Source
- TBD-CARD-AUTH-DAT-001 — Confirm TXNLOGPF schema version; need to coordinate with FLOW-ONUS-AUTH SEED-04 idempotency strategy

### Pending SME Judgment
- TBD-CARD-AUTH-DAT-002 — Confirm GLPOSTPF retention policy after SFTP success; SME (Maria Lopez) checking

### Non-Blocking
- TBD-CARD-AUTH-DAT-003 — Document HSSDTAR002 checkpoint field format

## SME Sign-Off
- **Reviewer:** Maria Lopez (Data Analyst) — pending
- **Decision:** draft → needs_sme_review
