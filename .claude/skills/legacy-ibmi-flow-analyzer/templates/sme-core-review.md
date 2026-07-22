---
document_id: <stable-document-id>
flow_slug: <flow-slug>
program_set_slug: <program-set-slug>
programs:
  - <PROGRAM_A>
  - <PROGRAM_B>
review_status: complete_exploratory
artifact_version: "0.4"
profile: standard_reader_first
---

# Program Set SME Core Review: <folder_slug>

> Authoring contract: instantiate this formal template only after all program
> artifacts are `ready`, the manifest has reached `ready_for_synthesis`, and
> the LLM has completed an anchor plan with zero pending coverage. The LLM
> executing the skill writes this review from the complete source pack and
> normalized facts, then records the manifest/coverage/formal-review completion
> state as `complete_exploratory`. A deterministic script must never emit this
> file as a skeleton. If an intermediate file is unavoidable, use only
> `<folder_slug>--partial-draft.md` without this final front matter or H1.

## Program Set Reading Summary

Explain what the selected program set contributes in SME language. Preserve
the material calculation, validation, exception, message/status, carrier,
guard, evidence, and outcome contributions of every program. State that the
SME-supplied program order is navigation only and is not a confirmed execution
sequence or call chain.

This must be a cross-program synthesis, not an artifact inventory and not a
concatenation of the per-program summaries. State that every program passed
artifact readiness, all source facts have zero-pending coverage, the status is
`complete_exploratory`, and the artifact is ready for SME/Dify review.

| Program | Scope / Reader-First Contribution | Artifact Readiness | Coverage | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- |
| <PROGRAM> | <complete contribution from Program Reading Summary> | ready | complete; zero pending | <a id="review-summary-001"></a> review-summary-001 | <SF-*; SF-*> |

## Cross-Program Processing Overview

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Program scope | <PROGRAM / routines> | <what this program contributes to the requested review> | <a id="review-overview-scope-001"></a> review-overview-scope-001 | <SF-*> |
| Calculation themes | <PROGRAM / RLOG> | <material calculations, assignments, and carriers> | <a id="review-overview-calc-001"></a> review-overview-calc-001 | <SF-*> |
| Validation themes | <PROGRAM / RLOG> | <guards, exact statuses, destinations, and outcomes> | <a id="review-overview-val-001"></a> review-overview-val-001 | <SF-*> |
| Exception / message themes | <PROGRAM / RLOG / MSG> | <failure handling and exact reviewer-visible outcomes> | <a id="review-overview-exc-001"></a> review-overview-exc-001 | <SF-*> |

This table is reading orientation only. Do not present its row order as a call
or runtime sequence.

## Calculation Logic

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <complete material calculation/assignment> | <PROGRAM> | <MAIN / routine / RLOG> | <target field/carrier> | <source operands/carriers> | <guard or always> | <returned/persisted/passed/skipped effect> | <evidence/RLOG/source refs> | confirmed / inferred / unresolved / evidence_present | <a id="review-calc-001"></a> review-calc-001 | <SF-*; SF-*> |

Do not merge rows when doing so would hide a program, carrier, guard, or
outcome. When several facts are losslessly represented by one row, list every
mapped `source_fact_id`.

## Validation Logic

| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <exact code/status/outcome> | <source-backed description> | <PROGRAM> | <MAIN / routine / RLOG> | <guard/evidence> | <response/parameter/queue/file> | <continue/stop/return/etc.> | <evidence/RLOG/source refs> | confirmed / inferred / unresolved / evidence_present | <a id="review-val-001"></a> review-val-001 | <SF-*; SF-*> |

## Exception Handling

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <business/I-O/SQL/external/generic path> | <PROGRAM> | <MAIN / routine / RLOG> | <IF/MONITOR/ON-ERROR/return check> | <exact status/message/flag> | <return/rollback/skip/continue/abort/log> | <observed outcome> | <evidence/RLOG/source refs> | confirmed / inferred / unresolved / evidence_present | <a id="review-exc-001"></a> review-exc-001 | <SF-*; SF-*> |

## Message Inventory

`standard_reader_first` requires this section in the primary reading path.
Preserve every exact observed message ID, status, return code, SQL state,
response literal, operator text, and generic-handler token as an individually
auditable value.

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Condition / Handler | Carrier / Destination | Effect | Detail Refs | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <exact message/status/literal/token> | <source-backed description> | <message/status/return_code/response/SQLSTATE/operator_text/generic_handler_token> | <PROGRAM / routine> | <count> | <condition or handler> | <response/parameter/queue/job log/file> | <observed outcome> | <MSG/RLOG/evidence refs> | confirmed / inferred / unresolved / evidence_present | <a id="review-msg-001"></a> review-msg-001 | <SF-*; SF-*> |

> `minimal_reader_first` is explicit opt-in. In that profile, move this complete
> table after Coverage Reconciliation and rename its H2 to `Message Coverage
> Control`. Do not remove, group away, or de-scope message facts.

## Core Completeness Ledger

| Program | Expected In Scope From | Run Resolution | Artifact Readiness | Five Primary Sections | Source Facts | Missing / Targeted Follow-up |
| --- | --- | --- | --- | --- | --- | --- |
| <PROGRAM> | SME program list | analyzed_this_run / reused_same_run / reused_artifact_repo | ready | complete | <count> | none |

No program may be omitted. Every requested program must appear. A formal review is illegal when a row
would be `not_ready`, `pending_source`, or `blocked_missing_source`.

## Coverage Reconciliation

| Source Fact ID | Program | Source Section | Disposition | Review Row ID / Anchor | Merged Fact IDs / Exclusion Reason |
| --- | --- | --- | --- | --- | --- |
| <SF-*> | <PROGRAM> | <Program Reading Summary / Calculation Logic / Validation Logic / Exception Handling / Message Inventory> | included / merged / excluded_non_core | <review-*> | <all merged IDs or precise non-core reason> |

Counts in this table must agree with `program-set-core-facts.yaml` and
`program-set-core-coverage.yaml`. No `pending` item is allowed.

An `unresolved` or `TBD-*` row is legal only when it is concrete,
evidence-bounded, and allowed by terminal upstream
`approved_with_non_blocking_tbd` status. Blank examples, TODO text,
artifact-link-only rows, and generic scaffold prose are not legal review rows.

## Sources

| Program | Analysis Directory | Run Resolution | Primary Analysis | Readiness Evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| <PROGRAM> | <current-run path or approved local repo path> | analyzed_this_run / reused_same_run / reused_artifact_repo | <PROGRAM>-program-analysis.md | upstream validator passed; artifact readiness ready | <sidecars used for reconciliation> |

Supporting paths are for traceability only; they are not substitutes for the logic
written in the core sections.

Sidecar reconciliation covers `<PROGRAM>-program-analysis-summary.yaml`,
`<PROGRAM>-source-index.yaml`, `<PROGRAM>-routine-logic-details.yaml`, and
`<PROGRAM>-message-inventory.yaml`. They validate the self-contained SME
reading surfaces; they do not replace the complete reader-first main sections.

## Run Profile

| Field | Value |
| --- | --- |
| Folder Slug | <FLOW-SLUG>--<PROGRAM-SET-SLUG> |
| Formal Review Filename | <folder_slug>--sme-core-review.md |
| Artifact Root | <approved local clone by default or explicit current-run root> |
| Artifact Repo Mode | approved_document_repo (default) / current_run (explicit) |
| Reuse Policy | approved_document_repo_clone (default) / current_run_only (explicit) |
| Core Review Profile | standard_reader_first / minimal_reader_first |
| Program Order Semantics | SME navigation only; not a confirmed call chain |

## Source Inventory Cache

| Field | Value |
| --- | --- |
| Inventory Checked | <path or not_needed> |
| Freshness | fresh / not_needed |
| Targeted Recovery Queue | none |

## Final Author Check

- Every manifest program is present in the summary, ledger, sources, facts, and
  coverage.
- Every source fact has exactly one completed coverage disposition.
- Every included/merged item points to an existing unique review anchor, and
  the anchored row lists the same source fact IDs.
- Exact messages/statuses/literals and per-program fact counts are preserved.
- No unsupported cross-program call or execution order is asserted.
- No full transaction-flow section is present.
- The five-way validator reports zero findings.

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
-->
