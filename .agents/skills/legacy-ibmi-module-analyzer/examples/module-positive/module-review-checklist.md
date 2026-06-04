# Module Review Checklist — Card Authorization

## Module-Level Sign-Off

- [ ] Module overview, Program Flow, and Data Flow are approved (or approved_with_non_blocking_tbd)
  - module-overview.md: draft → needs_sme_review (scope/crosswalk blockers)
  - 03-program-flow.md: draft → needs_sme_review (1 pending SME on cross-module CREDITCHK)
  - 04-data-flow.md: draft → needs_sme_review (2 pending source/SME)

- [X] Program/Data consistency verified
  - [X] Every `REPLAY-*` path maps to a module event, persisted outcome, exception outcome, or named TBD
  - [X] Every durable `PERSIST-*` output maps to a Data Flow object/output or source-backed downstream consumer
  - [X] Every module-critical `LINEAGE-*` and material `EXCHAIN-*` appears in Data Flow or carries a named TBD
  - [X] Every data object traces to an approved flow/program — all 8 objects traced
  - [X] Every flow touches at least one data object — confirmed

- [ ] No blocking TBDs remain — 3 blocking TBDs across views
- [ ] Capability seeds list is complete and SME-confirmed
- [ ] Module ready for BRD writer — not yet (blockers above)

## Reviewers

- **Module Overview / Crosswalk:** Anna Chen — pending — needs_sme_review
- **Program Flow:** Liu Wei — pending — needs_sme_review
- **Data Flow:** Maria Lopez — pending — needs_sme_review

## Module Owner Sign-Off

- **Anna Chen (Module Owner):** pending
- **Date:** —
- **Decision:** pending until per-view reviews complete

## Next Steps

1. Each SME reviews their view independently
2. Resolve 3 blocking TBDs:
   - GL system schema contract (TBD-CARD-AUTH-001) → cross-team coordination
   - BR-01 regulatory framing (TBD-CARD-AUTH-002) → Anna Chen + compliance
   - CVV scope (TBD-CARD-AUTH-003) → Anna Chen + Risk Officer
3. Once overview, Program Flow, and Data Flow are at least `approved_with_non_blocking_tbd`,
   module is ready for `legacy-brd-writer` to produce one BRD Package per
   selected capability seed before spec-writing.
