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

## View Index
| View | File | Status | Reviewer |
| --- | --- | --- | --- |
| 1. Operation Flow | 01-operation-flow.md | draft | Anna Chen (Card Ops) |
| 2. System Flow | 02-system-flow.md | draft | David Park (Integration Architect) |
| 3. Program Flow | 03-program-flow.md | draft | Liu Wei (Dev Lead) |
| 4. Data Flow | 04-data-flow.md | draft | Maria Lopez (Data Analyst) |

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
| CAP-CARD-AUTH-001 | On-us authorization has distinct actors, decision outcome, and real-time response obligation | View 1 actors/events + View 3 entry-flow evidence | Is "On-Us Authorization" a distinct capability or part of broader "Authorization"? |
| CAP-CARD-AUTH-002 | Daily reconciliation has a separate BAU rhythm, cut-off, exception review, and finance owner | View 1 BAU + View 3 nightly recon evidence | Is "Daily Reconciliation" a separate capability or part of "Authorization"? |
| CAP-CARD-AUTH-003 | Credit limit enforcement is a policy cluster reused across authorization channels | View 1 BR seeds + supporting behavior/evidence | Is "Credit Limit Enforcement" its own capability or a rule within "Authorization"? |

## BRD Functional Analysis Input Crosswalk

| BRD Section | SME-Required Area | Primary Module Source | Evidence / IDs | Coverage Status | Carry-Forward TBD |
| --- | --- | --- | --- | --- | --- |
| 1 | Function Purpose | View 1 Business Scope + module scope statement | EVENT-CARD-AUTH-01, EVENT-CARD-AUTH-02 | covered | none |
| 2 | Business Scenarios / Use Cases | View 1 Business Events + BAU Rhythm + Flow Replay Path | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001, FLOW-NIGHTLY-RECON-001, REPLAY-ONUS-AUTH-001, REPLAY-NIGHTLY-RECON-001 | covered | none |
| 3 | Channels | View 2 Upstream Systems + flow Trigger Context | SYS-CARD-AUTH-01, FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001 | covered | none |
| 4 | User Interface / User Touchpoints | View 1 Manual Intervention + manual auth flow | FLOW-MANUAL-AUTH-001 | partial | TBD-CARD-AUTH-004 (screen-report analysis for CSR menu pending) |
| 5 | System Interfaces | View 2 Upstream / Downstream Systems | SYS-CARD-AUTH-01, SYS-CARD-AUTH-10, IF-CARD-AUTH-01 | covered | none |
| 6 | Process Flow | View 1 Events + View 3 Replay Coverage Summary | FLOW-ONUS-AUTH-001, FLOW-MANUAL-AUTH-001, FLOW-NIGHTLY-RECON-001, REPLAY-ONUS-AUTH-001 | covered | none |
| 7 | Validation Rules | View 1 Business Rule Seeds + field lineage + exception-chain seeds | BR-CARD-AUTH-01, BR-CARD-AUTH-02, BR-CARD-AUTH-03, LINEAGE-ONUS-AUTH-001, EXCHAIN-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-003 |
| 8 | Error Handling | View 1 Exception Lifecycle + flow Exception Propagation Chain | EXCHAIN-ONUS-AUTH-001, EXCHAIN-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-002 |
| 9 | Dependencies | View 2 System Flow + View 4 Data Flow / Persistence Matrix | SYS-CARD-AUTH-10, DATA-AUTHLOG, DATA-GLPOST, PERSIST-NIGHTLY-RECON-001 | partial | TBD-CARD-AUTH-001 |
| 10 | Security / Authentication (optional) | View 2 Security & Network Boundaries | IF-CARD-AUTH-01 | optional_covered | none |
| 11 | Workflow / Design Notes (optional) | View 3 topology | FLOW-ONUS-AUTH-001 | optional_covered | none |
| 12 | Source Document Mapping (optional) | Not supplied in this module example | none | not_evidenced | none |

## Module Review Checklist

- [ ] All four views are at least `approved_with_non_blocking_tbd`
- [ ] Cross-view consistency check passed
  - [X] Every actor in View 1 maps to entry node in View 3 — Cardholder/Merchant → Visa MQ entry, Risk Officer → manual_actor: yes
  - [X] Every system in View 2 appears in View 3 — Visa, GL, Risk Monitoring all referenced
  - [X] Every BR seed in View 1 references supporting evidence — all 4 seeds traced
  - [X] Every replay path maps to a business event or exception outcome
  - [X] Durable persistence outputs map to View 2 consumers or View 4 objects
  - [X] Every data object in View 4 traces to flow in View 3 — all traced
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
