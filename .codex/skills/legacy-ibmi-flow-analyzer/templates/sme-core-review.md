# Program Set SME Core Review: [Program Set Name]

Purpose: compact SME review view that merges multiple program-analysis results
without the engineering flow sections. Use this as
`program-set-sme-core-review.md` for SME-provided program-flow/list input.
The four core sections are self-contained SME reading surfaces: use supporting
detail references for traceability, but do not require the reader to open
per-program documents to understand the logic.

Run Profile:

| Field | Value |
| --- | --- |
| Repo | [owner/repo from delivery workspace profile] |
| Working Branch | [develop-person or current delivery branch] |
| Artifact Root | [current delivery working checkout / output root] |
| Cross-Run Reuse | false |
| Program Folder Patterns | [modules/*/{PROGRAM}; or configured patterns] |
| Program Name Normalization | [uppercase; preserve leading @; exact folder-name match; or configured rule] |

Source Inventory Cache:

| Field | Value |
| --- | --- |
| Default Inventory Dir | outputs/repo-scan |
| Inventory Dir Checked | [<source-root>/outputs/repo-scan or configured override] |
| program-list.csv | present / missing / not_checked |
| scan-summary.yaml | present / missing / not_checked |
| Freshness | fresh / missing / stale / dirty_source / not_checked |
| Action | reuse_inventory / rerun_repo_inventory_scan / provide_source_root_to_check_inventory |

| Program | Run Resolution | Inventory Status | Source Path | Tier | Targeted Scan Allowed |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | analyzed_this_run / reused_same_run / pending_source / blocked_missing_source | not_needed_current_artifact_present / found / missing_from_inventory / inventory_cache_missing | [source member path] | normal_program / complex_normal_program / large_extreme_program / unknown | yes / no |

Sources:

| Program | Analysis Directory | Run Resolution | Compact Artifacts Used | Coverage / Readiness | Notes |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | [working-branch path / pending source scan] | analyzed_this_run / reused_same_run / pending_source / blocked_missing_source | program-analysis-summary.yaml; message-inventory.yaml; routine-logic-details.yaml=present / optional_not_required / missing_when_needed; [optional sidecars] | deep_read / indexed_only / warning / blocked | [notes] |

Core Completeness Ledger:

| Program | Expected In Scope From | Run Resolution | Routine Logic Evidence | Message Inventory | Missing / Targeted Follow-up |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | SME-provided flow / inventory / current-run artifact | analyzed_this_run / reused_same_run / pending_source / blocked_missing_source | present / missing / optional_not_required / N/A | present / missing / N/A | [none / scan this program / missing source] |

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
  Handling, Message Inventory, plus Run Profile, Source Inventory Cache,
  Sources, and Core Completeness Ledger tables used to prove coverage.
- The four core sections must contain the merged business/technical logic
  itself: conditions, assignments, carriers, outcomes, handling actions, and
  exact messages/status values. `Supporting Detail` and `Detail Refs` are for
  traceability only; they must not be the only explanation.
- Do not include Nodes, Edges, Transaction Call Map, Replay, Persistence,
  Lineage, UI Surfaces, Capability Seeds, flow-level TBD tables, or SME
  Checklist.
- No program may be omitted from the Core Completeness Ledger. Programs with no
  current-run artifact remain in the row set as `pending_source` or
  `blocked_missing_source`; do not satisfy them from remote-main or prior-run
  artifacts.
- For `pending_source` programs, use source inventory cache only when freshness
  is `fresh`; otherwise rerun repo-level inventory before targeted program scan.
- Message Inventory must list every exact message/status/literal observed
  across the participating program analyses. Do not replace individual rows
  with grouped labels.
