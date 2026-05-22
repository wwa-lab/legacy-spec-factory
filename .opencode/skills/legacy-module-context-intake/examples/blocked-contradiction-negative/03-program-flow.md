# View 3: Program Flow - Payment Matching

## Intake Status
- status: draft
- source_state: rag_hydrated
- primary_sources:
  - SNP-PAYMENT-001
  - SNP-PAYMENT-002

## Summary

`PMTMATCH` is the single entry program. It reads payment records in a loop,
looks up matching invoices, posts matches, and routes unmatched records to
suspense. No sub-programs have been identified in the synthetic fixture.

## Evidence-Linked Details

| Claim ID | Knowledge Type | Statement | Evidence | Strength | Review Status |
| --- | --- | --- | --- | --- | --- |
| VIEW3-PMATCH-001 | observed_behavior | `PMTMATCH` is the entry and only identified program. | SNP-PAYMENT-001 | confirmed_from_code | needs_sme_review |
| VIEW3-PMATCH-002 | observed_behavior | `PMTMATCH` writes unmatched records to `PMTSUSP`. | SNP-PAYMENT-002 | confirmed_from_code | needs_sme_review |

## Candidate Seeds

| Candidate ID | Candidate Statement | Suggested By | Required Review |
| --- | --- | --- | --- |
| RAG-ASM-PAYMENT-MATCH-001 | No sub-program calls identified; `PMTMATCH` contains all matching logic inline. | SNP-PAYMENT-001 | needs_sme_review |

## Gaps For Module Analyzer

| TBD ID | Category | Question | Evidence | Owner | Blocking |
| --- | --- | --- | --- | --- | --- |
| TBD-PAYMENT-MATCH-002 | program_scope | Are there other programs that post to the AR balance outside `PMTMATCH`? | SNP-PAYMENT-001 | IT SME | no |
