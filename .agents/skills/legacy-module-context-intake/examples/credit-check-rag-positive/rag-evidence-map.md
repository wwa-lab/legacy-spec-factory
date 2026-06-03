# RAG Evidence Map - CREDIT-CHECK

## RAG Runs

| Run ID | Source Snapshot | Dictionary Version | Sensitivity | Status |
| --- | --- | --- | --- | --- |
| RAG-20260521-001 | synthetic-sqlrpgle-credit-check-happy-2026-05-21 | synthetic-dict-v1 | synthetic_non_production | ready_with_warnings |

## Source Snippets

| Evidence ID | Artifact | Lines | Summary | Strength | Coverage / Consumer |
| --- | --- | ---: | --- | --- | --- |
| SNP-CREDIT-CHECK-001 | SRC-CREDIT-CHECK-CRDTCMD-001 | 7 | `CRDTCMD` calls `CREDITCHK`. | confirmed_from_code | system_interfaces, program_anchors |
| SNP-CREDIT-CHECK-003 | SRC-CREDIT-CHECK-CREDITCHK-001 | 29-36 | `CREDITCHK` reads `STATUS` and `AVAIL_CREDIT` from `CREDITVW`. | confirmed_from_code | system_interfaces, program_anchors |
| SNP-CREDIT-CHECK-004 | SRC-CREDIT-CHECK-CREDITCHK-001 | 38-67 | Denial, approval, over-limit cap, and return-value behavior. | confirmed_from_code | business_process, program_anchors |
| SNP-CREDIT-CHECK-005 | SRC-CREDIT-CHECK-CREDITCHK-001 | 69-74 | Denial/error message text is written to `QSYSPRT`. | confirmed_from_code | program_anchors |
| DDS-CREDIT-CHECK-CUSTMAST-001 | DDS-CREDIT-CHECK-CUSTMAST-001 | 1-6 | Physical customer credit fields. | confirmed_from_code | data_anchors |
| DDS-CREDIT-CHECK-CREDITVW-001 | DDS-CREDIT-CHECK-CREDITVW-001 | 1-5 | Logical view fields used by `CREDITCHK`. | confirmed_from_code | data_anchors |

## Runtime Observations

| Evidence ID | Source | Lines | Observed Detail | Coverage / Consumer |
| --- | --- | ---: | --- | --- |
| RUN-CREDIT-CHECK-JOBLOG-001 | runtime/sample-joblog.txt | 1-9 | Wrapper completion and over-limit diagnostic message. | system_interfaces |
| RUN-CREDIT-CHECK-SPOOL-001 | runtime/sample-spool.txt | 1-9 | Denied over-limit scenario with approved amount capped to available credit. | business_process |

## Dictionary Mappings

| Standard Field ID | Legacy Reference | Meaning | Owner | Status | Coverage / Consumer |
| --- | --- | --- | --- | --- | --- |
| DD-CUSTOMER-NUMBER | CUSTMAST.CUSTNO, CREDITVW.CUSTNO, CREDITCHK.CustNo | Stable customer identifier used for credit lookup. | Credit Operations | approved_dictionary | data_anchors |
| DD-CREDIT-AVAILABLE-AMOUNT | CREDITVW.AVAIL_CREDIT, CREDITCHK.AvailCredit | Amount currently available for order approval. | Credit Operations | approved_dictionary | data_anchors |
| DD-CREDIT-DECISION-CODE | CREDITCHK.Decision | Legacy approve/deny indicator returned by credit checking. | Credit Operations | approved_dictionary | business_process |

## Impact Scope

| Target | Impact Type | Evidence | Confidence | Coverage / Consumer |
| --- | --- | --- | --- | --- |
| PROGRAM-CREDITCHK | Reads `CREDITVW.STATUS` and `CREDITVW.AVAIL_CREDIT`. | SNP-CREDIT-CHECK-003 | high | system_interfaces, program_anchors |
| PROGRAM-CREDITCHK | Compares requested amount to available credit. | SNP-CREDIT-CHECK-004 | high | business_process, program_anchors |
| TABLE_OR_FILE-CUSTMAST | Physical base file for `CREDITVW`. | DDS-CREDIT-CHECK-CUSTMAST-001 | medium | data_anchors |

## Candidate Facts

| Candidate ID | Statement | Business Signal | Evidence Basis | Promotion Status | Required Review |
| --- | --- | --- | --- | --- | --- |
| RAG-CAND-CREDIT-CHECK-001 | Missing customers are denied by default. | Customer service cannot continue order release when the account cannot be resolved. | SNP-CREDIT-CHECK-003, SNP-CREDIT-CHECK-004 | needs_sme_review | Credit Operations SME |
| RAG-CAND-CREDIT-CHECK-002 | Inactive customers are denied even if credit exists. | Customer eligibility status can override available credit. | SNP-CREDIT-CHECK-004, SME-CREDIT-CHECK-001 | needs_sme_review | Credit Operations SME |
| RAG-CAND-CREDIT-CHECK-004 | Requests over available credit are denied and return available credit as the maximum approvable amount. | Over-limit orders are blocked, but the response exposes the amount that may be approvable. | SNP-CREDIT-CHECK-004, RUN-CREDIT-CHECK-SPOOL-001 | needs_sme_review | Credit Operations SME |
| RAG-ASM-CREDIT-CHECK-001 | Business-rule ownership appears to sit in the credit decision routine rather than the operational wrapper. | Modernization scope should focus the component that determines approval, denial, and amount behavior. | `CRDTCMD`; SME-CREDIT-CHECK-001 | deferred | IBM i developer / SME |
| RAG-ASM-CREDIT-CHECK-002 | Full program analysis should prioritize the credit decision routine. | Approval, denial, over-limit, and returned-amount behavior appear concentrated in one routine. | `CREDITCHK`; SNP-CREDIT-CHECK-004 | deferred | IBM i developer |
| RAG-GAP-CREDIT-CHECK-001 | Available credit derivation is not proven by the supplied DDS. | Data ownership and calculation semantics must be clear before approving credit-amount behavior. | `CREDITVW.AVAIL_CREDIT`; DDS-CREDIT-CHECK-CUSTMAST-001, DDS-CREDIT-CHECK-CREDITVW-001 | deferred | Data owner |
| RAG-GAP-CREDIT-CHECK-003 | The full caller scope for the credit decision routine is not proven by the synthetic fixture. | Reuse outside the sampled path could expand modernization scope. | `CREDITCHK`; SNP-CREDIT-CHECK-001 | deferred | IT SME |
| RAG-GAP-CREDIT-CHECK-004 | No evidence shows whether over-limit denials are queued, audited, or rejected inline. | Exception handling affects operations, auditability, and customer follow-up. | SME-CREDIT-CHECK-001 | deferred | Credit Operations SME |
| RAG-GAP-CREDIT-CHECK-005 | The supplied wrapper does not visibly capture the return decision. | The calling path may ignore or transform the approval decision. | `CRDTCMD`, `CREDITCHK`; SNP-CREDIT-CHECK-001, SNP-CREDIT-CHECK-004 | deferred | IBM i developer |
