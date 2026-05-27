# View N: <View Name> - <Module Name>

## Normalization Status
- status: draft_needs_sme_review
- source_state: extracted_documents
- primary_sources:
  - DOC-<MODULE-SLUG>-001

## Summary
<Concise normalized view. No invented facts.>

## Evidence-Linked Flow Steps
| Step ID | Sequence | Statement | Evidence Basis | Confidence | Review Status |
| --- | ---: | --- | --- | --- | --- |
| STEP-<MODULE-SLUG>-001 | 1 | <Draft flow step in view-appropriate language.> | DOC-<MODULE-SLUG>-001; FRAG-<MODULE-SLUG>-001 | medium | needs_sme_review |

<!--
Evidence Basis field guidance:
- View 1 (Operation/Business): cite DOC-* and FRAG-* only; keep technical names in parentheses.
- View 2 (System): may also cite SYS-<MODULE-SLUG>-NNN for system nodes extracted from diagrams or
  inventory lists. Example: DOC-<MODULE-SLUG>-001; SYS-<MODULE-SLUG>-001 (HOST-CREDITCHECK).
- View 3 (Program): may also cite PGM-<MODULE-SLUG>-NNN for programs/jobs extracted from documents.
  Example: DOC-<MODULE-SLUG>-001; PGM-<MODULE-SLUG>-001 (CCHK100).
- View 4 (Data): may also cite DATA-<MODULE-SLUG>-NNN for data objects extracted from data
  dictionaries or CRUD tables. Example: DOC-<MODULE-SLUG>-002; DATA-<MODULE-SLUG>-001 (APPLIC).
SYS-*, PGM-*, and DATA-* IDs are draft identifiers; they must appear in evidence-map.md
Extracted Fragments section the same way FRAG-* IDs do.
-->

## Candidate Seeds
| Candidate ID | Candidate Statement | Business Signal | Evidence Basis | Required Review |
| --- | --- | --- | --- | --- |
| CAND-<MODULE-SLUG>-001 | <Candidate to confirm, not a rule.> | <Business decision, control, SLA, ownership, exception, or capability affected.> | DOC-<MODULE-SLUG>-001; FRAG-<MODULE-SLUG>-001 | SME confirm / reject |

## Gaps For SME Review
| TBD ID | Category | Question | Evidence | Owner | Blocking |
| --- | --- | --- | --- | --- | --- |
| TBD-<MODULE-SLUG>-001 | pending_sme_judgment | <Question that must be answered before context intake or can be carried forward.> | DOC-<MODULE-SLUG>-001 | <Owner> | yes |
