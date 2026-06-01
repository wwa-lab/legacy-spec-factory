# Module: [Business Module Name] (MODULE-[SLUG]-001)

## Metadata
- **Module ID:** MODULE-[SLUG]-001
- **Business Name:** [Name]
- **Scope Statement:** [SME-confirmed one paragraph]
- **Module Owner:** [SME name / role]
- **Evidence Mode:** code_backed | context_only
- **In-scope Flows:**
  - FLOW-[SLUG]-001 ([business event])
  - FLOW-[SLUG]-002 ([business event])
- **Status:** draft | needs_sme_review | approved | approved_with_non_blocking_tbd | blocked_pending_source | blocked_pending_sme | rejected
- **Mermaid Preview Status:** not_requested | skipped_large_module | passed | failed | timed_out
- **Completion Boundary:** stop_after_writeback

## View Index
| View | File | Status | Reviewer |
| --- | --- | --- | --- |
| 1. Operation Flow | 01-operation-flow.md | draft | [SME] |
| 2. System Flow | 02-system-flow.md | draft | [SME] |
| 3. Program Flow | 03-program-flow.md | draft | [SME] |
| 4. Data Flow | 04-data-flow.md | draft | [SME] |

## Top Blocking TBDs
(Aggregate of `pending_source` and `pending_sme_judgment` from all views.)

## Module Program-Chain Readiness
| Flow ID | Replay Coverage | Critical Lineage Coverage | Persistence Coverage | Exception Chain Coverage | Blocking Gap |
| --- | --- | --- | --- | --- | --- |
| FLOW-[SLUG]-001 | complete / partial / missing (`REPLAY-*`) | complete / partial / missing (`LINEAGE-*`) | complete / partial / missing (`PERSIST-*`) | complete / partial / missing (`EXCHAIN-*`) | none / TBD-[SLUG]-[NNN] |

Use this section to show whether the module can be replayed end-to-end from
business trigger through program chain, field movement, persistence, exception
handling, and final outcome.

## Module Persistence & Critical Field Summary
| Data / Field / Outcome | Source Flows | Persistence / Output | Downstream Consumer | Risk / TBD |
| --- | --- | --- | --- | --- |
| [critical field or durable outcome] | FLOW-[SLUG]-001 (`LINEAGE-*`, `PERSIST-*`) | [file / DTAQ / spool / IFS / response / skipped write] | [system / actor / module] | none / TBD-[SLUG]-[NNN] |

## Module Exception & Recovery Summary
| Exception Cluster | Source Flow / EXCHAIN | Business Outcome | Manual / Operational Recovery | BRD Coverage / TBD |
| --- | --- | --- | --- | --- |
| [message / RC / error family] | FLOW-[SLUG]-001 (`EXCHAIN-*`) | [response / rollback / retry / skipped persistence / manual review] | [owner / procedure / unknown] | covered / TBD-[SLUG]-[NNN] |

## Capability Seeds For BRD / Spec
| CAP Seed | Business Signal | Evidence Basis | SME Question |
| --- | --- | --- | --- |
| CAP-[SLUG]-001 | [business event / outcome / rule cluster suggesting a capability] | [view / flow / program evidence refs] | [business-language boundary question] |

Capability seeds are business capability candidates, not program-entry
wrappers. Use program flow only as evidence for boundaries and dependencies.

## BRD Functional Analysis Input Crosswalk

| BRD Section | SME-Required Area | Primary Module Source | Evidence / IDs | Coverage Status | Carry-Forward TBD |
| --- | --- | --- | --- | --- | --- |
| 1 | Function Purpose | View 1 Business Scope + Scope Statement | [EV-* / SME note] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 2 | Business Scenarios / Use Cases | View 1 Business Events + BAU Rhythm + Flow Replay Path | [EVENT-* / FLOW-* / REPLAY-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 3 | Channels | View 1 Actors + View 2 Upstream Systems + Trigger Context | [ACTOR-* / SYS-* / FLOW-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 4 | User Interface / User Touchpoints | View 1 Manual Intervention + screen/report evidence | [OBJ-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 5 | System Interfaces | View 2 Systems and External Interfaces | [SYS-* / IF-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 6 | Process Flow | View 1 Events + View 3 Replay Coverage Summary + Flow Replay Path | [EVENT-* / FLOW-* / REPLAY-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 7 | Validation Rules | View 1 Business Rule Seeds + flow branch points + field lineage + exception-chain seeds | [BR-* / SEED-* / LINEAGE-* / EXCHAIN-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 8 | Error Handling | View 1 Exception Lifecycle + flow Exception Propagation Chain | [EXCHAIN-* / EV-* / FLOW-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 9 | Dependencies | View 2 + View 3 + View 4 data / persistence dependencies | [SYS-* / DATA-* / OBJ-* / PERSIST-* / LINEAGE-* / EV-*] | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 10 | Security / Authentication (optional) | View 2 Security & Network Boundaries | [IF-* / EV-*] | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |
| 11 | Workflow / Design Notes (optional) | View 3 topology or supplied workflow docs | [FLOW-* / EV-*] | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |
| 12 | Source Document Mapping (optional) | Context package / evidence map | [DOC-* / FRAG-* / EV-*] | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |

This crosswalk feeds `legacy-brd-writer`. It should not invent missing BRD
content; partial or missing required areas must carry a `TBD-*`.

## Module Review Checklist
- [ ] All four views are at least `approved_with_non_blocking_tbd`
- [ ] For `code_backed` mode, `01_inventory/object-map.md`, in-scope
      `program-analysis.md`, and in-scope `flow-*.md` artifacts are present
      and approved
- [ ] For `context_only` mode, missing object-map / program / flow artifacts
      are carried as `TBD-*` blockers and the module is not approved for a
      standard BRD/spec path
- [ ] Cross-view consistency check passed
- [ ] Replay / field-lineage / persistence / exception-chain coverage
      summarized for every in-scope flow, or named TBD / waiver recorded
- [ ] Critical field lineage and persistence risks carried into the BRD
      crosswalk where they affect scenarios, rules, dependencies, or errors
- [ ] BRD sections 1-9 have crosswalk coverage or named carry-forward TBDs
- [ ] No blocking TBDs remain
- [ ] Capability seeds reviewed
- [ ] Module ready for BRD writer

## Sign-Off
- **Module Owner:** ____
- **Date:** ____
- **Decision:** ____
