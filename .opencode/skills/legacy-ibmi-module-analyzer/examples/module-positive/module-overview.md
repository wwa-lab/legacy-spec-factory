# Module: Card Authorization (MODULE-CARD-AUTH-001)

## Metadata
- **Module ID:** MODULE-CARD-AUTH-001
- **Business Name:** Card Authorization
- **Scope Statement:** Processes on-us card authorization requests from external networks (Visa, Mastercard), supports manual authorization via CSR menu, and performs nightly reconciliation against GL. Excludes settlement (handled by separate module SETTLEMENT) and dispute handling (CHARGEBACK module).
- **Module Owner:** Anna Chen (Card Operations Lead) — confirmed scope and boundaries 2026-05-12
- **Evidence Mode:** code_backed
- **In-scope Flows:**
  - FLOW-ONUS-AUTH-001 — On-us authorization request (API/MQ)
  - FLOW-MANUAL-AUTH-001 — Manual authorization via CSR menu
  - FLOW-NIGHTLY-RECON-001 — Nightly reconciliation (Scheduler+Batch)
- **Status:** draft → needs_sme_review
- **Mermaid Preview Status:** not_requested
- **Completion Boundary:** stop_after_writeback

## Evidence View Index
| View | File | Status | Reviewer |
| --- | --- | --- | --- |
| Program Flow | 03-program-flow.md | draft | Liu Wei (Dev Lead) |
| Data Flow | 04-data-flow.md | draft | Maria Lopez (Data Analyst) |

## Optional Source-Backed Context Notes
| Context Area | Source | Eligibility | Notes / TBD |
| --- | --- | --- | --- |
| Business operation / BAU | Anna Chen SME notes, 2026-05-12 | confirmed_by_sme | On-us authorization, manual authorization, and nightly reconciliation are in scope. Settlement and dispute handling are out of scope. |
| Channels / systems / interfaces | approved flow trigger context and integration notes | mixed_with_questions | Visa/MC MQ, CSR menu, scheduler, GL handoff, risk monitoring, and compliance/report consumers appear in approved flow evidence or source-backed notes. |

## Top Blocking TBDs (aggregated across all views)

- **TBD-CARD-AUTH-001** (pending_source): GL system's downstream consumer
  not in this repo; need cross-module agreement on GLPOSTPF schema
- **TBD-CARD-AUTH-002** (pending_sme): Confirm whether RC=-2 threshold in
  nightly reconciliation is regulatory or operational policy
- **TBD-CARD-AUTH-003** (pending_sme): CVV verification — required for
  all auths or only ATMP? (capability seed BR-02)

## Non-Blocking Carry-Forward TBDs

- **TBD-CARD-AUTH-004** (pending_analysis): CSR menu screen/report analysis
  is still needed to enrich BRD section 4, but it does not block module review.

## Module Program-Chain Readiness

| Flow ID | Replay Coverage | Edge Resolution Coverage | Critical Lineage Coverage | Persistence Coverage | Exception Chain Coverage | Blocking Gap |
| --- | --- | --- | --- | --- | --- | --- |
| FLOW-ONUS-AUTH-001 | complete (`REPLAY-ONUS-AUTH-001`) | complete (no unresolved dynamic edges) | partial (`LINEAGE-ONUS-AUTH-001`, CVV path TBD) | complete (`PERSIST-ONUS-AUTH-001`) | complete (`EXCHAIN-ONUS-AUTH-001`) | TBD-CARD-AUTH-003 |
| FLOW-MANUAL-AUTH-001 | complete (`REPLAY-MANUAL-AUTH-001`) | complete (no unresolved dynamic edges) | complete (`LINEAGE-MANUAL-AUTH-001`) | complete (`PERSIST-MANUAL-AUTH-001`) | complete (`EXCHAIN-MANUAL-AUTH-001`) | none |
| FLOW-NIGHTLY-RECON-001 | complete (`REPLAY-NIGHTLY-RECON-001`) | complete (scheduler + CALL edges resolved) | complete (`LINEAGE-NIGHTLY-RECON-001`) | complete (`PERSIST-NIGHTLY-RECON-001`) | partial (`EXCHAIN-NIGHTLY-RECON-001`, threshold owner TBD) | TBD-CARD-AUTH-002 |

## Module Persistence & Critical Field Summary

| Data / Field / Outcome | Source Flows | Persistence / Output With Purpose | Downstream Consumer | Risk / TBD |
| --- | --- | --- | --- | --- |
| AUTH_STATUS (authorization decision/status) | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001 (`LINEAGE-*`, `PERSIST-*`) | TXNLOGPF status row (audit authorization outcome) + MQ/menu response | Card network, CSR, nightly reconciliation | none |
| GLPOSTPF.POST_AMT (GL posting amount) and EXC_COUNT (exception count) | FLOW-NIGHTLY-RECON-001 (`LINEAGE-NIGHTLY-RECON-001`, `PERSIST-NIGHTLY-RECON-001`) | GLPOSTPF (GL staging handoff), RECONPRT (finance exception report), RECONDTAQ (monitoring status) | GL system, Finance Analyst, Risk Monitoring | TBD-CARD-AUTH-001, TBD-CARD-AUTH-002 |
| CVV_RESULT (CVV verification result) | FLOW-ONUS-AUTH-001 (`LINEAGE-ONUS-AUTH-002`) | transient decision field; no stored value confirmed | authorization response | TBD-CARD-AUTH-003 |

## Module Exception & Recovery Summary

| Exception Cluster | Source Flow / EXCHAIN | Error Type / Output Carrier | Business Outcome | Manual / Operational Recovery | BRD Coverage / TBD |
| --- | --- | --- | --- | --- | --- |
| Online auth timeout / MQ failure | FLOW-ONUS-AUTH-001 (`EXCHAIN-ONUS-AUTH-001`) | external handoff timeout / MQ status + response code | decline response, no GL impact | partner retry; Ops monitors queue depth | covered |
| Nightly recon RC=-2 threshold breach | FLOW-NIGHTLY-RECON-001 (`EXCHAIN-NIGHTLY-RECON-001`) | validation threshold / RC out parameter + RECONPRT spool | GL posting deferred, RECONPRT spool generated | Finance Analyst review, Card Ops escalation | TBD-CARD-AUTH-002 |

## Capability Seeds For BRD / Spec

| CAP Seed | Business Signal | Evidence Basis | SME Question |
| --- | --- | --- | --- |
| CAP-CARD-AUTH-001 | On-us authorization has distinct actors, decision outcome, and real-time response obligation | SME scope notes + Program Flow entry/replay evidence | Is "On-Us Authorization" a distinct capability or part of broader "Authorization"? |
| CAP-CARD-AUTH-002 | Daily reconciliation has a separate BAU rhythm, cut-off, exception review, and finance owner | SME/source notes + Program Flow nightly recon evidence | Is "Daily Reconciliation" a separate capability or part of "Authorization"? |
| CAP-CARD-AUTH-003 | Credit limit enforcement is a policy cluster reused across authorization channels | Program/Data Flow behavior and lineage evidence | Is "Credit Limit Enforcement" its own capability or a rule within "Authorization"? |

## BRD Functional Analysis Input Crosswalk

| BRD Section | SME-Required Area | Primary Module Source | Evidence / IDs | Coverage Status | Carry-Forward TBD |
| --- | --- | --- | --- | --- | --- |
| 1 | Function Purpose | Module scope statement + SME notes | MODULE-CARD-AUTH-001, Anna Chen SME note | covered | none |
| 2 | Business Scenarios / Use Cases | In-scope flows + Program Flow replay coverage + SME/source notes | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001, FLOW-NIGHTLY-RECON-001, REPLAY-ONUS-AUTH-001, REPLAY-NIGHTLY-RECON-001 | covered | none |
| 3 | Channels | Flow trigger context + source-backed interface notes | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001 | covered | none |
| 4 | User Interface / User Touchpoints | Screen/report analysis + manual auth flow trigger context | FLOW-MANUAL-AUTH-001 | partial | TBD-CARD-AUTH-004 (screen-report analysis for CSR menu pending) |
| 5 | System Interfaces | Flow external calls + source-backed interface notes | IF-CARD-AUTH-01, FLOW-ONUS-AUTH-001, FLOW-NIGHTLY-RECON-001 | covered | none |
| 6 | Process Flow | Program Flow replay coverage + Flow Replay Path | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001, FLOW-NIGHTLY-RECON-001, REPLAY-ONUS-AUTH-001 | covered | none |
| 7 | Validation Rules | Program/flow Validation Logic + field lineage + exception-chain seeds | LINEAGE-ONUS-AUTH-001, EXCHAIN-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-003 |
| 8 | Error Handling | Module Exception Summary + flow Exception Propagation Chain | EXCHAIN-ONUS-AUTH-001, EXCHAIN-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-002 |
| 9 | Dependencies | Program Flow dependencies + Data Flow persistence/dependencies | DATA-AUTHLOG, DATA-GLPOST, PERSIST-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-001 |
| 10 | Security / Authentication (optional) | Source-backed interface/security notes | IF-CARD-AUTH-01 | optional_covered | none |
| 11 | Workflow / Design Notes (optional) | Program Flow topology | FLOW-ONUS-AUTH-001 | optional_covered | none |
| 12 | Source Document Mapping (optional) | Not supplied in this module example | none | not_evidenced | none |

## Module Review Checklist

- [ ] Program Flow is at least `approved_with_non_blocking_tbd`
- [ ] Data Flow is at least `approved_with_non_blocking_tbd`
- [ ] Program/Data consistency check passed
  - [X] Every replay path maps to a module event, persisted outcome, exception outcome, or named TBD
  - [X] Durable persistence outputs map to Data Flow objects or source-backed downstream consumers
  - [X] Every data object in Data Flow traces to Program Flow / approved flow evidence
- [ ] Replay / field-lineage / persistence / exception-chain coverage summarized
- [ ] Critical field lineage and persistence risks carried into BRD crosswalk
- [ ] BRD sections 1-9 have crosswalk coverage or named carry-forward TBDs
- [ ] No blocking TBDs remain — 3 blocking TBDs pending
- [ ] Capability seeds list is complete and SME-confirmed
- [ ] Module ready for BRD writer

## Sign-Off
- **Module Owner:** Anna Chen — pending
- **Date:** —
- **Decision:** pending (3 blocking TBDs)
