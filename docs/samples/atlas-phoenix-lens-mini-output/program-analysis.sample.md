# Program Analysis Sample: AMHUPDR

## Metadata

| Field | Value |
| --- | --- |
| Program | `AMHUPDR` |
| Source type | `RPGLE` |
| Flow | `FLOW-CARD-STATUS-UPDATE` |
| Evidence mode | Synthetic sample |
| Status | `review_draft` |

## Observed Behavior

| ID | Behavior | Evidence | Confidence |
| --- | --- | --- | --- |
| `BEH-CARD-STATUS-001` | Reads the current account status before applying an update. | `AMHUPDR.rpgle:42-58` | High |
| `BEH-CARD-STATUS-002` | Rejects updates when the account is already closed. | `AMHUPDR.rpgle:61-76` | Medium |
| `BEH-CARD-STATUS-003` | Updates `CARDACCT.STATUS` when validation has passed. | `AMHUPDR.rpgle:91-108` | High |
| `BEH-CARD-STATUS-004` | Calls `AMHAUDR` after a successful status update. | `AMHUPDR.rpgle:112-118`, `ARCAD-XREF-0003` | High |

## File I/O Evidence

| File | Operation | Purpose |
| --- | --- | --- |
| `CARDACCT` | Read / update | Retrieve and persist account status |
| `CARDAUD` | Indirect write through `AMHAUDR` | Preserve audit trail |

## Business Rule Seeds

| ID | Candidate rule | Status |
| --- | --- | --- |
| `BR-CARD-STATUS-001` | Closed accounts cannot be moved back to active status by this flow. | `needs_sme_review` |
| `BR-CARD-STATUS-002` | Every successful status change requires an audit record. | `needs_sme_review` |

## Open Questions

| ID | Question | Resolver |
| --- | --- | --- |
| `TBD-CARD-STATUS-001` | Is closed-account rejection a business policy or a technical safeguard? | Card operations SME |
| `TBD-CARD-STATUS-002` | Are there override paths outside this flow? | IBM i SME |
