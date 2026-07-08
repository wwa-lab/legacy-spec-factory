# Program Set SME Core Review: [Program Set Name]

Purpose: compact SME review view that merges multiple program-analysis results
without the engineering flow sections. Use this as
`program-set-sme-core-review.md` for SME-provided program-flow/list input.
The four core sections are self-contained SME reading surfaces: use supporting
detail references for traceability, but do not require the reader to open
per-program documents to understand the logic.

## Program Set Reading Summary

Explain in SME-readable language what this program list / program set is,
what business or operational path it helps review, which programs are complete
or still pending source scan, and whether the review is
`standalone_exploratory`, `draft`, or `chain_ready`.

Cover the processing layers in prose: entry/dispatch, calculation, validation,
exception/message handling, and persistence/finalization. Do not leave this as
an artifact list, file inventory, or pending placeholder.

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First |
| --- | --- | --- |
| Entry / dispatch | [PROGRAM MAIN / RLOG-*] | [what starts, dispatches, or orders the set] |
| Calculation | [PROGRAM RLOG-*] | [what calculated values or assignments matter first] |
| Validation | [PROGRAM RLOG-*] | [what checks decide continue / stop / status] |
| Exception / message | [PROGRAM RLOG-* / MSG-*] | [what failure/status paths the SME should read first] |
| Persistence / finalization | [PROGRAM RLOG-* / file/status carrier] | [what completes, persists, or hands off the result] |

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

## Core Completeness Ledger

| Program | Expected In Scope From | Run Resolution | Routine Logic Evidence | Message Inventory | Missing / Targeted Follow-up |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | SME-provided flow / inventory / current-run artifact / approved document repo artifact | analyzed_this_run / reused_same_run / reused_artifact_repo / pending_source / blocked_missing_source | present / missing / N/A | present / missing / N/A | [none / scan this program / missing source] |

## Sources

| Program | Analysis Directory | Run Resolution | Compact Artifacts Used | Coverage / Readiness | Notes |
| --- | --- | --- | --- | --- | --- |
| [PROGRAM] | [working-branch path / approved document repo path / pending source scan] | analyzed_this_run / reused_same_run / reused_artifact_repo / pending_source / blocked_missing_source | program-analysis.md; program-analysis-summary.yaml; source-index.yaml; routine-index.md; message-inventory.yaml; routine-logic-details.md=present/missing; routine-logic-details.yaml=present/missing; [optional sidecars] | deep_read / indexed_only / warning / blocked | [notes] |

## Run Profile

| Field | Value |
| --- | --- |
| Repo | [owner/repo from delivery workspace profile] |
| Working Branch | [develop-person or current delivery branch] |
| Artifact Root | [current delivery working checkout / output root] |
| Artifact Repo Mode | current_run / approved_document_repo |
| Reuse Policy | current_run_only / approved_document_repo_clone |
| Cross-Run Reuse | false |
| Program Folder Patterns | [modules/*/{PROGRAM}; or configured patterns] |
| Program Name Normalization | [uppercase; preserve leading @; exact folder-name match; or configured rule] |

## Source Inventory Cache

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
| [PROGRAM] | analyzed_this_run / reused_same_run / reused_artifact_repo / pending_source / blocked_missing_source | not_needed_current_artifact_present / not_needed_approved_document_repo_artifact_present / found / missing_from_inventory / inventory_cache_missing | [source member path] | normal_program / complex_normal_program / large_extreme_program / unknown | yes / no |

Rules:

- This artifact starts with Program Set Reading Summary and Cross-Program
  Processing Overview, then Calculation Logic, Validation Logic, Exception
  Handling, and Message Inventory. Run Profile, Source Inventory Cache,
  Sources, and Core Completeness Ledger are audit/control sections and must
  appear after the reader-first core.
- The four core sections must contain the merged business/technical logic
  itself: conditions, assignments, carriers, outcomes, handling actions, and
  exact messages/status values. `Supporting Detail` and `Detail Refs` are for
  traceability only; they must not be the only explanation.
- Do not include Nodes, Edges, Transaction Call Map, Replay, Persistence,
  Lineage, UI Surfaces, Capability Seeds, flow-level TBD tables, or SME
  Checklist.
- No program may be omitted from the Core Completeness Ledger. Programs with no
  artifact remain in the row set as `pending_source` or
  `blocked_missing_source`; satisfy rows from existing artifacts only when the
  manifest explicitly uses `run_profile.artifact_repo_mode:
  approved_document_repo` and `run_resolution: reused_artifact_repo`.
- Normal, complex, and large programs all require `routine-logic-details.md`
  and `routine-logic-details.yaml` as routine logic evidence.
- For `pending_source` programs, use source inventory cache only when freshness
  is `fresh`; otherwise rerun repo-level inventory before targeted program scan.
- Message Inventory must list every exact message/status/literal observed
  across the participating program analyses. Do not replace individual rows
  with grouped labels.
