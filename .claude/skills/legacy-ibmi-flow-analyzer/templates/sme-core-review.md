# Program Set SME Core Review: [Program Set Name]

Purpose: compact SME review view that merges multiple program-analysis results
without the engineering flow sections. Use this as
`program-set-sme-core-review.md` for SME-provided program-flow/list input.

Lookup Profile:

| Field | Value |
| --- | --- |
| Repo | [owner/repo from delivery_artifact_lookup_profile] |
| Branch | [main or configured branch] |
| Module Roots | [modules/* or configured roots] |
| Program Folder Patterns | [modules/*/{PROGRAM}; or configured patterns] |
| Program Name Normalization | [uppercase; preserve leading @; exact folder-name match; or configured rule] |

Sources:

| Program | Analysis Directory | Central Lookup Result | Compact Artifacts Used | Coverage / Readiness | Notes |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | [remote-main path or local scan path] | found_on_remote_main / not_found_on_remote_main / remote_unavailable | program-analysis-summary.yaml; routine-logic-details.yaml; message-inventory.yaml; [optional sidecars] | deep_read / indexed_only / warning / blocked | [notes] |

Core Completeness Ledger:

| Program | Expected In Scope From | Central Lookup Result | Calculation Logic | Validation Logic | Exception Handling | Message Inventory | Missing / Targeted Follow-up |
| --- | --- | --- | --- | --- | --- | --- | --- |
| [PROGRAM] | SME-provided flow / central lookup / inventory / call evidence | found_on_remote_main / not_found_on_remote_main / remote_unavailable | present / missing / N/A | present / missing / N/A | present / missing / N/A | present / missing / N/A | [none / scan this program / remote unavailable] |

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
  Handling, Message Inventory, plus the Sources table and Core Completeness
  Ledger used to prove coverage.
- Do not include Nodes, Edges, Transaction Call Map, Replay, Persistence,
  Lineage, UI Surfaces, Capability Seeds, flow-level TBD tables, or SME
  Checklist.
- No program may be omitted from the Core Completeness Ledger. If the exact
  program folder is not on remote `main`, keep the row and mark
  `not_found_on_remote_main`; if the remote cannot be checked, mark
  `remote_unavailable`.
- Message Inventory must list every exact message/status/literal observed
  across the participating program analyses. Do not replace individual rows
  with grouped labels.
