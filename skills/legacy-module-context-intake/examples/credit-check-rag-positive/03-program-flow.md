# View 3: Program Flow - Credit Check

## Intake Status
- status: ready_for_module_analysis
- source_state: rag_hydrated
- primary_sources:
  - RAG-20260521-001
  - SNP-CREDIT-CHECK-001
  - SNP-CREDIT-CHECK-003
  - SNP-CREDIT-CHECK-004
  - SNP-CREDIT-CHECK-005

## Summary

`CRDTCMD` calls `CREDITCHK`. The business decision appears concentrated in
`CREDITCHK`, which reads `CREDITVW`, defaults the decision to deny, branches on
missing/error/inactive/amount conditions, writes denial/error text to `QSYSPRT`,
and returns a decision.

## Evidence-Linked Details

| Claim ID | Knowledge Type | Statement | Evidence | Strength | Review Status |
| --- | --- | --- | --- | --- | --- |
| CTX-CREDIT-CHECK-PGM-001 | observed_behavior | Program flow starts at `CRDTCMD` and calls `CREDITCHK`. | SNP-CREDIT-CHECK-001 | confirmed_from_code | needs_sme_review |
| CTX-CREDIT-CHECK-PGM-002 | observed_behavior | `CREDITCHK` branches through denial, approval, over-limit cap, and return-value behavior. | SNP-CREDIT-CHECK-004 | confirmed_from_code | needs_sme_review |
| CTX-CREDIT-CHECK-PGM-003 | observed_behavior | Denial and error messages are written to `QSYSPRT`. | SNP-CREDIT-CHECK-005 | confirmed_from_code | needs_sme_review |

## Candidate Seeds

| Candidate ID | Candidate Statement | Suggested By | Required Review |
| --- | --- | --- | --- |
| RAG-ASM-CREDIT-CHECK-001 | `CRDTCMD` is operational glue, not the business rule owner. | SME-CREDIT-CHECK-001 | IBM i developer / SME |
| RAG-ASM-CREDIT-CHECK-002 | `CREDITCHK` should be prioritized for full program analysis. | SNP-CREDIT-CHECK-004 | IBM i developer |

## Gaps For Module Analyzer

| TBD ID | Category | Question | Evidence | Owner | Blocking |
| --- | --- | --- | --- | --- | --- |
| TBD-CREDIT-CHECK-003 | pending_source | Are there any additional callers of `CREDITCHK` outside the synthetic fixture? | RAG-GAP-CREDIT-CHECK-003 | IT SME | no |
