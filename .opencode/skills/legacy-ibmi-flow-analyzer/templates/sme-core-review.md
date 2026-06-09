# SME Core Review: [Flow or Program Set Name]

Purpose: compact SME review view that merges multiple program-analysis results
without the engineering flow sections.

Sources:

| Program | Analysis Directory | Compact Artifacts Used | Coverage / Readiness | Notes |
| --- | --- | --- | --- | --- |
| [PROGRAM] | [path] | program-analysis-summary.yaml; routine-logic-details.yaml; message-inventory.yaml; [optional sidecars] | deep_read / indexed_only / warning / blocked | [notes] |

## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [material calculation] | [PROGRAM] | [MAIN / SRxxx / procedure] | [field / response DS / file field / parameter] | [fields, constants, queues, files] | [always / condition / error path] | [returned, persisted, passed, message set, skipped] | [RLOG-* / LINEAGE-* / PERSIST-* / TBD-*] | confirmed / inferred / unresolved |

## Validation Logic

| Message / Status / Outcome | Description | Program | Routine | Trigger Chain | Carrier / Destination | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [exact code/status/literal] | [description or unresolved - message description not available] | [PROGRAM] | [MAIN / SRxxx / procedure] | [guard -> calculation -> outcome] | [response / return parameter / queue / message / file] | [approve / decline / abort / skip / continue / rollback] | [MSG-* / RLOG-* / EXCHAIN-* / TBD-*] | confirmed / inferred / unresolved |

## Exception Handling

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [business / file I/O / SQL / external call / generic handler] | [PROGRAM] | [MAIN / SRxxx / procedure] | [IF / MONITOR / ON-ERROR / return-code check] | [status, message, flag, log text] | return / rollback / skip / continue / abort / log | [flow or program outcome] | [RLOG-* / MSG-* / TBD-*] | confirmed / inferred / unresolved |

## Message Inventory

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Trigger / Handler | Effect | Detail Refs | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [exact message ID / status value / return code / response literal / operator text] | [description or unresolved - message description not available] | message / status / return_code / response / SQLSTATE / operator_text / generic_handler | [PROGRAM SRxxx; PROGRAM SRyyy] | [count] | [condition or handler summary] | [outcome affected / not flow-affecting] | [MSG-* / RLOG-* / TBD-*] | confirmed / inferred / unresolved |

Rules:

- This artifact contains only Calculation Logic, Validation Logic, Exception
  Handling, and Message Inventory.
- Do not include Nodes, Edges, Transaction Call Map, Replay, Persistence,
  Lineage, UI Surfaces, Capability Seeds, TBD tables, or SME Checklist.
- Message Inventory must list every exact message/status/literal observed
  across the participating program analyses. Do not replace individual rows
  with grouped labels.
