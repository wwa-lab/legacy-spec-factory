# Flow Analysis Sample: Card Account Status Update

## Flow Summary

`FLOW-CARD-STATUS-UPDATE` describes a synthetic card account maintenance flow.
The flow validates a requested status change, applies the update to the account
master file, and writes an audit trail.

## Program Call Chain

```text
AMHMAIN
  -> AMHVALR
  -> AMHUPDR
  -> AMHAUDR
```

## Replay Path

| Step | Program | Behavior |
| --- | --- | --- |
| 1 | `AMHMAIN` | Receives the account maintenance request and calls validation. |
| 2 | `AMHVALR` | Checks account existence and request eligibility. |
| 3 | `AMHUPDR` | Applies the status change when validation passes. |
| 4 | `AMHAUDR` | Writes audit evidence for the completed update. |

## Cross-Program Evidence

| ID | Finding | Evidence |
| --- | --- | --- |
| `BEH-FLOW-CARD-001` | The flow has a validation-before-update structure. | `ARCAD-XREF-0001`, `ARCAD-XREF-0002`, `AMHVALR`, `AMHUPDR` |
| `BEH-FLOW-CARD-002` | Account status persistence occurs in `AMHUPDR`, not in the entry program. | `AMHUPDR.rpgle:91-108` |
| `BEH-FLOW-CARD-003` | Audit write is downstream of successful update. | `ARCAD-XREF-0003`, `AMHAUDR` |

## Modernization Evidence

| ID | Evidence | Downstream use |
| --- | --- | --- |
| `EV-CARD-STATUS-001` | `CALLS` relationship from `AMHVALR` to `AMHUPDR` | Service boundary discovery |
| `EV-CARD-STATUS-002` | `CARDACCT.STATUS` update in `AMHUPDR` | Data ownership and write-path design |
| `EV-CARD-STATUS-003` | Audit call after update | Non-functional audit requirement candidate |

## SME Review Points

- Confirm whether closed-account rejection is a business rule.
- Confirm whether all status changes require audit records.
- Identify any manual override or batch correction path outside this flow.
