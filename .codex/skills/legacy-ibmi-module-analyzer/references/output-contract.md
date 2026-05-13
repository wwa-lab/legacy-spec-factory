# Output Contract: Module Analysis

This document defines the precise file shape and required fields for each
of the six artifacts in `02_modules/<MODULE-SLUG>/`.

The canonical model is in `../../../docs/module-analysis-model.md`. This
document defines the *file format*; that document defines the *intent*.

---

## File 1: `module-overview.md`

```markdown
# Module: [Business Module Name] (MODULE-<SLUG>-001)

## Metadata
- **Module ID:** MODULE-CARD-AUTH-001
- **Business Name:** Card Authorization
- **Scope Statement:** [one paragraph from SME]
- **Module Owner:** [SME name / role]
- **In-scope Flows:** [list of FLOW-* with link to each flow analysis]
- **Status:** draft | needs_sme_review | approved | approved_with_non_blocking_tbd | rejected

## View Index
| View | File | Status | Reviewer |
| --- | --- | --- | --- |
| 1. Operation Flow | 01-operation-flow.md | [status] | [SME name] |
| 2. System Flow | 02-system-flow.md | [status] | [SME name] |
| 3. Program Flow | 03-program-flow.md | [status] | [SME name] |
| 4. Data Flow | 04-data-flow.md | [status] | [SME name] |

## Top Blocking TBDs
(Aggregate of `pending_source` and `pending_sme_judgment` TBDs from all four views.)

## Capability Seeds For spec-writer
(Module-level capability candidates; one row per CAP-*; the spec-writer
resolves each into one or more `spec.yaml` artifacts.)

| CAP Seed | Suggested By | SME Question |
| --- | --- | --- |
| CAP-CARD-AUTH-001 | View 1 + View 3 | Is "On-Us Card Authorization" a distinct capability or part of a broader "Authorization" capability? |

## Module Review Checklist
- [ ] All four views are at least `approved_with_non_blocking_tbd`
- [ ] Cross-view consistency check passed (see view 3 ↔ view 1 actor mapping, etc.)
- [ ] No blocking TBDs remain
- [ ] Capability seeds reviewed by spec-writer SME

## Sign-Off
- **Module Owner:** ____
- **Date:** ____
- **Decision:** ____
```

---

## File 2: `01-operation-flow.md` (View 1 — Business)

```markdown
# View 1: Operation Flow / Business Background — [Module Name]

## Status: draft | needs_sme_review | approved | ...

## Business Scope
[Paragraph from SME describing what the module does for the business.]

## Business Actors
| Actor ID | Name / Role | Description | Source |
| --- | --- | --- | --- |
| ACTOR-CARD-AUTH-01 | Cardholder | Person making the transaction | SME (Anna Chen) |
| ACTOR-CARD-AUTH-02 | Merchant | Party requesting authorization | SME |
| ACTOR-CARD-AUTH-03 | Risk Officer | Manual review of flagged transactions | SME |
| ACTOR-CARD-AUTH-04 | Operations | Monitors batch jobs | SME |

## Business Events
| Event ID | Event Name | Trigger | Flow ID | Notes |
| --- | --- | --- | --- | --- |
| EVENT-CARD-AUTH-01 | On-us authorization request | Visa API call | FLOW-ONUS-AUTH-001 | sub-second SLA |
| EVENT-CARD-AUTH-02 | Nightly reconciliation | Scheduler 22:00 | FLOW-NIGHTLY-RECON-001 | cut-off 06:00 next day |
| EVENT-CARD-AUTH-03 | Manual override (call center) | CSR menu option | FLOW-MANUAL-AUTH-001 | supervisor approval required |

## BAU Rhythm
| BAU Item | Cadence | Owner | Notes |
| --- | --- | --- | --- |
| Peak transactions | Mon-Fri 12:00–14:00, Sat 10:00–22:00 | Ops | from SME observation |
| Cut-off windows | Daily 06:00, Month-end 23:59 last day | Finance | from SME |
| Manual exception review | Daily morning, ~30min | Risk team | from SME |

## Manual Intervention Points
| Intervention | When | Who | What | Source |
| --- | --- | --- | --- | --- |
| Override declined auth | On-demand | Supervisor | Manually approve via menu | SME |
| Partial-restart recovery | After batch failure | Ops | Re-run last node only | SME (see flow-NIGHTLY-RECON) |
| Daily exception review | Each morning | Risk team | Read spool RECONPRT | SME |

## Exception Lifecycle
[Free-form description from SME of how exceptions flow from detection
through to resolution. Often a small flowchart.]

## Business Rule Seeds
(Module-level seeds aggregating across all in-scope flows.)

| Seed ID | Candidate Rule | Suggested By | SME Question |
| --- | --- | --- | --- |
| BR-CARD-AUTH-01 | Credit limit must be respected for every on-us auth | FLOW-ONUS-AUTH SEED-01 | Regulatory or operational? |
| BR-CARD-AUTH-02 | Decline audit row must persist before response | FLOW-ONUS-AUTH SEED-03 | Hard requirement or best-effort? |
| ... | ... | ... | ... |

## TBDs
(Group by blocking status, with the SME each TBD requires.)

## Review Checklist
[per-view checklist]

## SME Sign-Off
[reviewer / date / decision]
```

---

## File 3: `02-system-flow.md` (View 2 — Integration)

```markdown
# View 2: System Flow — [Module Name]

## Status: ...

## Upstream Systems
| System ID | Name | Type | Integration Pattern | Flow(s) | Evidence |
| --- | --- | --- | --- | --- | --- |
| SYS-CARD-AUTH-01 | Visa | External card network | MQ (mTLS) | FLOW-ONUS-AUTH | EV / SME |
| SYS-CARD-AUTH-02 | ATM channel | Internal channel | DTAQ (sync) | FLOW-ATM-AUTH | EV / SME |

## Downstream Systems
| System ID | Name | Type | Integration Pattern | Flow(s) | Evidence |
| --- | --- | --- | --- | --- | --- |
| SYS-CARD-AUTH-10 | GL | Internal accounting | File handoff GLPOSTPF | FLOW-NIGHTLY-RECON | EV |
| SYS-CARD-AUTH-11 | Risk monitoring | Internal | DTAQ async | FLOW-NIGHTLY-RECON | EV |
| SYS-CARD-AUTH-12 | Compliance reporting | Internal | spool / IFS | FLOW-NIGHTLY-RECON | EV |

## External Interfaces
| Interface ID | Counterparty | Direction | Format | SLA | Auth | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| IF-CARD-AUTH-01 | Visa | Bidirectional | ISO 8583 over MQ | sub-second | mTLS + HMAC | SME / spec |

## Integration Patterns Summary
| Pattern | Used By | Async Boundary | Notes |
| --- | --- | --- | --- |
| MQ (mTLS) | Visa | Yes (inbound queue) | retries by Visa |
| File handoff | GL | No (sync batch read) | cut-off enforced |
| Spool | Compliance | No (manual pickup) | morning review |

## Security & Network Boundaries
[Diagram or text describing DMZ, partition boundaries, where TLS terminates, etc.]

## TBDs / Checklist / Sign-Off
[as for View 1]
```

---

## File 4: `03-program-flow.md` (View 3 — Application)

```markdown
# View 3: Program Flow — [Module Name]

## Status: ...

## Flow Inventory
| Flow ID | Business Event | Trigger Model | Entry Program | Exit Program | Runtime |
| --- | --- | --- | --- | --- | --- |
| FLOW-ONUS-AUTH-001 | On-us auth request | API/Remote | CU101A | CU199Z | sync, real-time |
| FLOW-NIGHTLY-RECON-001 | Nightly recon | Scheduler+Batch | RECONCL | RECONSQL | async, batch |
| FLOW-MANUAL-AUTH-001 | Manual auth via CSR | Menu | MANAUTH | MANAUTH | sync, interactive |

## Cross-Flow Dependencies
| From Flow | To Flow | Mechanism | Reason |
| --- | --- | --- | --- |
| FLOW-ONUS-AUTH-001 | FLOW-NIGHTLY-RECON-001 | Shared file TXNLOGPF | online auth writes log; reconciliation reads |
| FLOW-MANUAL-AUTH-001 | FLOW-NIGHTLY-RECON-001 | Shared file TXNLOGPF | manual auth also writes log |

## Shared Sub-Programs (called by multiple flows)
| Program | Called By Flows | Role | Notes |
| --- | --- | --- | --- |
| CREDITCHK | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH | Credit check utility | shared validation |
| TXNLOG | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH, FLOW-NIGHTLY-RECON | Audit log writer | hot path |

## Overall Call Topology
[Top-level sequence / ASCII tree showing how flows compose.]

## TBDs / Checklist / Sign-Off
```

---

## File 5: `04-data-flow.md` (View 4 — Data)

```markdown
# View 4: Data Flow — [Module Name]

## Status: ...

## Data Objects in Scope
(Aggregated from every program's Object Dependencies section.)

| Object | Type | Inventory ID | Producer Flows | Consumer Flows | Coupling Score | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| TXNLOGPF | PF | OBJ-CARD-AUTH-050 | FLOW-ONUS-AUTH, FLOW-MANUAL-AUTH | FLOW-NIGHTLY-RECON | 3 (HIGH) | EV |
| GLPOSTPF | PF | OBJ-CARD-AUTH-060 | FLOW-NIGHTLY-RECON | (external — GL system) | 1 | EV |
| HSSDTAR002 | *DTAARA | OBJ-CARD-AUTH-070 | FLOW-NIGHTLY-RECON | FLOW-NIGHTLY-RECON | 1 (internal) | EV |
| CUSTMSTR | PF | OBJ-CARD-AUTH-080 | (external) | FLOW-ONUS-AUTH | 1 | EV |

## Data Lifecycle
| Object | Created By | Updated By | Read By | Archived By | Purged By |
| --- | --- | --- | --- | --- | --- |
| TXNLOGPF | FLOW-ONUS-AUTH (per transaction) | (none — append-only) | FLOW-NIGHTLY-RECON, FLOW-MANUAL-AUTH | (monthly archive job — out of module) | (yearly purge — out of module) |

## Coupling Hotspots (Modernization Risks)
| Object | Coupling Score | Risk | Mitigation |
| --- | --- | --- | --- |
| TXNLOGPF | HIGH (3 flows) | Schema change ripples through all flows | Maintain backward compatibility; version transactions |

## Critical Data Trails
[End-to-end paths of important data — e.g., a transaction record from
intake → log → GL posting → archive.]

## DB Table Relationships
[ER-style diagram or table listing PK/FK relationships among the module's
PF / LF / SQL tables.]

## Cross-Module Data Dependencies
| Object | Owned By Module | Used By This Module | Mechanism |
| --- | --- | --- | --- |
| CUSTMSTR | CUSTOMER-MASTER module | CARD-AUTH (read-only lookup) | Direct CHAIN |
| GLPOSTPF | (this module produces; GL consumes) | n/a | File handoff |

## TBDs / Checklist / Sign-Off
```

---

## File 6: `module-review-checklist.md`

```markdown
# Module Review Checklist — [Module Name]

## Module-Level Sign-Off

- [ ] All four views are approved (or approved_with_non_blocking_tbd)
- [ ] Cross-view consistency verified
  - [ ] Every business actor (View 1) maps to a node in View 3 OR is
        tagged as manual-only
  - [ ] Every upstream/downstream system (View 2) appears in View 3
  - [ ] Every business-rule seed (View 1) references a program / file in
        View 3 / View 4
  - [ ] Every data object (View 4) traces to a program in View 3
- [ ] No blocking TBDs remain
- [ ] Capability seeds list is complete and SME-confirmed
- [ ] Module ready for spec-writer

## Per-View Reviewers
- View 1 (Business): ____ — date: ____ — decision: ____
- View 2 (Integration): ____ — date: ____ — decision: ____
- View 3 (Application): ____ — date: ____ — decision: ____
- View 4 (Data): ____ — date: ____ — decision: ____

## Module Owner Sign-Off
- ____ — date: ____ — decision: ____
```

---

## ID Conventions

| Prefix | Artifact | Example |
|---|---|---|
| `MODULE-` | the module | `MODULE-CARD-AUTH-001` |
| `ACTOR-` | business actor (View 1) | `ACTOR-CARD-AUTH-03` |
| `EVENT-` | business event (View 1) | `EVENT-CARD-AUTH-02` |
| `SYS-` | upstream / downstream system (View 2) | `SYS-CARD-AUTH-01` |
| `IF-` | external interface (View 2) | `IF-CARD-AUTH-01` |
| `BR-` | business-rule seed (View 1) | `BR-CARD-AUTH-01` |
| `CAP-` | capability seed (overview) | `CAP-CARD-AUTH-001` |
| `TBD-` | open question | `TBD-CARD-AUTH-005` |
| `EV-` | evidence | `EV-CARD-AUTH-012` |

Flow / Node / Edge / Data IDs from flow-analyzer remain valid in View 3 / 4.
Object IDs (`OBJ-*`) and evidence IDs (`EV-*`) from inventory and
program-analyzer remain valid throughout.
