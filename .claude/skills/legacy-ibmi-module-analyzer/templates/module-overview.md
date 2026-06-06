# Module: [Business Module Name] (MODULE-[SLUG]-001)

## Metadata
- **Module ID:** MODULE-[SLUG]-001
- **Business Name:** [Name]
- **Scope Statement:** [SME-confirmed one paragraph]
- **Module Owner:** [SME name / role]
- **Evidence Mode:** code_backed | context_only
- **BRD Source Eligibility:** code_backed_only | mixed_with_questions | questions_only
- **In-scope Flows:**
  - FLOW-[SLUG]-001 ([business event])
  - FLOW-[SLUG]-002 ([business event])
- **Status:** draft | needs_sme_review | approved | approved_with_non_blocking_tbd | blocked_pending_source | blocked_pending_sme | rejected
- **Mermaid Preview Status:** not_requested | skipped_large_module | passed | failed | timed_out
- **Completion Boundary:** stop_after_writeback

## Evidence View Index
| View | File | Status | Reviewer |
| --- | --- | --- | --- |
| Program Flow | 03-program-flow.md | draft | [Dev lead] |
| Data Flow | 04-data-flow.md | draft | [Data owner] |

## Optional Source-Backed Context Notes
| Context Area | Source | Eligibility | Notes / TBD |
| --- | --- | --- | --- |
| Business operation / BAU | [SME note / source doc / missing] | confirmed_by_sme / source_documented / missing | [summary or TBD-*] |
| Channels / systems / interfaces | [flow trigger / integration spec / SME / missing] | code_backed / source_documented / missing | [summary or TBD-*] |

## Top Blocking TBDs
(Aggregate of `pending_source` and `pending_sme_judgment` from all views.)

## Module Program-Chain Readiness
| Flow ID | Replay Coverage | Edge Resolution Coverage | Critical Lineage Coverage | Persistence Coverage | Exception Chain Coverage | Blocking Gap |
| --- | --- | --- | --- | --- | --- | --- |
| FLOW-[SLUG]-001 | complete / partial / missing (`REPLAY-*`) | complete / partial / missing (Evidence Source + Resolution) | complete / partial / missing (`LINEAGE-*`) | complete / partial / missing (`PERSIST-*`) | complete / partial / missing (`EXCHAIN-*`) | none / TBD-[SLUG]-[NNN] |

Use this section to show whether the module can be replayed end-to-end from
business trigger through program chain, field movement, persistence, exception
handling, and final outcome.

## Flow Artifact Set

Do not concatenate full flow or program Markdown to satisfy this table. Use
approved flow rows and core compact program artifacts first; open
human-readable Markdown only for targeted clarification. Optional program
sidecars are required only when triggered by program tier or needed by module
claims.

| Flow ID | Flow Analysis | Program Summary | Source Index | Routine Logic | Message Inventory | File I/O | Mutation Matrix | SQL Inventory | Gap / Waiver |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FLOW-[SLUG]-001 | `flow-[SLUG].md` | `program-analysis-summary.yaml` present / missing | `source-index.yaml` present / missing | `routine-logic-details.yaml` present / missing | `message-inventory.yaml` present / missing | `file-io-inventory.yaml` present / optional_not_triggered / missing_when_needed | `field-mutation-matrix.yaml` present / optional_not_triggered / missing_when_needed | `sql-inventory.yaml` present / not_applicable / missing_when_needed | none / TBD-[SLUG]-[NNN] |

## Module Persistence & Critical Field Summary
| Data / Field / Outcome | Source Flows | Persistence / Output With Purpose | Downstream Consumer | Risk / TBD |
| --- | --- | --- | --- | --- |
| [FIELD_NAME (business meaning) or durable outcome] | FLOW-[SLUG]-001 (`LINEAGE-*`, `PERSIST-*`) | [file / DTAQ / spool / IFS / response / skipped write + purpose] | [system / actor / module] | none / TBD-[SLUG]-[NNN] |

## Module Exception & Recovery Summary
| Exception Cluster | Source Flow / EXCHAIN | Error Type / Output Carrier | Business Outcome | Manual / Operational Recovery | BRD Coverage / TBD |
| --- | --- | --- | --- | --- | --- |
| [message / RC / error family] | FLOW-[SLUG]-001 (`EXCHAIN-*`) | [business / technical / system + output carrier] | [response / rollback / retry / skipped persistence / manual review] | [owner / procedure / unknown] | covered / TBD-[SLUG]-[NNN] |

## Capability Seeds For BRD / Spec
| CAP Seed | Business Signal | Evidence Basis | SME Question |
| --- | --- | --- | --- |
| CAP-[SLUG]-001 | [business event / outcome / rule cluster suggesting a capability] | [view / flow / program evidence refs] | [business-language boundary question] |

Capability seeds are business capability candidates, not program-entry
wrappers. Use program flow only as evidence for boundaries and dependencies.

## BRD Functional Analysis Input Crosswalk

| BRD Section | SME-Required Area | Primary Module Source | Evidence / IDs | Source Eligibility | Coverage Status | Carry-Forward TBD |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Function Purpose | Module scope statement + SME/source notes | [EV-* / SME note] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 2 | Business Scenarios / Use Cases | In-scope flows + Program Flow replay coverage + SME/source notes | [FLOW-* / REPLAY-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 3 | Channels | Flow trigger context + source-backed interface notes | [FLOW-* / IF-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 4 | User Interface / User Touchpoints | Screen/report analysis + flow trigger context | [OBJ-* / EV-* / FLOW-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 5 | System Interfaces | Flow external calls + source-backed interface notes | [IF-* / EDGE-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 6 | Process Flow | Program Flow replay coverage + Flow Replay Path | [FLOW-* / REPLAY-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 7 | Validation Rules | Program/flow Validation Logic + field lineage + exception-chain seeds | [LINEAGE-* / EXCHAIN-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 8 | Error Handling | Module Exception Summary + flow Exception Propagation Chain | [EXCHAIN-* / EV-* / FLOW-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 9 | Dependencies | Program Flow dependencies + Data Flow persistence/dependencies | [DATA-* / OBJ-* / PERSIST-* / LINEAGE-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | covered / partial / missing | none / TBD-[SLUG]-[NNN] |
| 10 | Security / Authentication (optional) | Source-backed interface/security notes | [IF-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |
| 11 | Workflow / Design Notes (optional) | Program Flow topology or supplied workflow docs | [FLOW-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |
| 12 | Source Document Mapping (optional) | Context package / evidence map | [DOC-* / FRAG-* / EV-*] | brd_conclusion_allowed / needs_sme_review / questions_only | optional_covered / not_evidenced | none / TBD-[SLUG]-[NNN] |

This crosswalk feeds `legacy-brd-writer`. It should not invent missing BRD
content; partial or missing required areas must carry a `TBD-*`.
`questions_only` rows must become SME questions or TBDs, not BRD conclusions.

## Module Review Checklist
- [ ] Program Flow is at least `approved_with_non_blocking_tbd`
- [ ] Data Flow is at least `approved_with_non_blocking_tbd`
- [ ] For `code_backed` mode, `01_inventory/object-map.md`, in-scope
      `flow-*.md` artifacts and compact program artifacts are present and
      approved: `program-analysis-summary.yaml`, `source-index.yaml`,
      `routine-logic-details.yaml`, `message-inventory.yaml`,
      `file-io-inventory.yaml`, `field-mutation-matrix.yaml`, and
      `sql-inventory.yaml`
- [ ] For `context_only` mode, missing object-map / program / flow artifacts
      are carried as `TBD-*` blockers and the module is not approved for a
      standard BRD/spec path
- [ ] Program/Data consistency check passed
- [ ] Replay / field-lineage / persistence / exception-chain coverage
      summarized for every in-scope flow, or named TBD / waiver recorded
- [ ] Critical field lineage and persistence risks carried into the BRD
      crosswalk where they affect scenarios, rules, dependencies, or errors
- [ ] BRD sections 1-9 have crosswalk coverage or named carry-forward TBDs
- [ ] No BRD section is marked covered using only candidate/generated or
      unreviewed source-documented context
- [ ] No blocking TBDs remain
- [ ] Capability seeds reviewed
- [ ] Module ready for BRD writer

## Sign-Off
- **Module Owner:** ____
- **Date:** ____
- **Decision:** ____
