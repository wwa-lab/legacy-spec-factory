<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
-->

> Status: `draft_exploratory`
>
> This is a non-formal scan-result merge. It uses the same reader-first
> section order as the formal SME Core Review, but may contain pending facts,
> unavailable-program markers, and unresolved readiness findings. Do not call
> it approved or hand it off as the final SME/Dify review.
>
> Use `program-analysis-summary.yaml`, `source-index.yaml`,
> `routine-logic-details.yaml`, and `message-inventory.yaml` only for
> reconciliation; the reader-first Markdown remains the semantic primary input.

## Program Set Reading Summary

Summarize the available reader-first contribution of every requested program.
Keep the original program order as navigation evidence only; do not present it
as a confirmed execution sequence or call chain. Mark unavailable or draft
programs explicitly.

| Program | Scope / Reader-First Contribution | Artifact Readiness | Coverage | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- |
| <PROGRAM> | <available source-backed contribution or unavailable marker> | ready / pending / not_ready | complete / pending | <review-summary-001> | <SF-*> |

## Cross-Program Processing Overview

Use thematic reading orientation only. Do not invent calls, execution order,
lineage, or producer-consumer relationships from the program list.

| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
| Program scope | <PROGRAM / routines> | <available contribution> | <review-overview-scope-001> | <SF-*> |
| Calculation themes | <PROGRAM / RLOG> | <available calculations and carriers> | <review-overview-calc-001> | <SF-*> |
| Validation themes | <PROGRAM / RLOG> | <available guards, statuses, destinations> | <review-overview-val-001> | <SF-*> |
| Exception / message themes | <PROGRAM / RLOG / MSG> | <available handling and outcomes> | <review-overview-exc-001> | <SF-*> |

## Calculation Logic

Retain every available material calculation, assignment, carrier, guard, and
effect. Mark unresolved or unavailable evidence as pending.

| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <available calculation or pending marker> | <PROGRAM> | <routine / RLOG> | <carrier> | <operands> | <guard> | <effect> | <source refs> | confirmed / inferred / unresolved / pending | <review-calc-001> | <SF-*> |

## Validation Logic

Retain every available exact status, outcome, condition, destination, and
effect. Never replace an unknown description with an invented meaning.

| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <exact status/outcome or pending marker> | <source-backed description or unresolved> | <PROGRAM> | <routine / RLOG> | <condition> | <destination> | <effect> | <source refs> | confirmed / inferred / unresolved / pending | <review-val-001> | <SF-*> |

## Exception Handling

Retain every available exception path, detection mechanism, message/flag,
handling action, and observed effect.

| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <available exception or pending marker> | <PROGRAM> | <routine / RLOG> | <mechanism> | <messages / flags> | <action> | <effect> | <source refs> | confirmed / inferred / unresolved / pending | <review-exc-001> | <SF-*> |

## Message Inventory

Preserve every exact message, status, return code, SQL state, response literal,
operator text, or generic-handler token found in the available scan results.

| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Condition / Handler | Carrier / Destination | Effect | Detail Refs | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <exact message/status/literal/token> | <source-backed or unresolved> | <type> | <PROGRAM / routine> | <count> | <condition / handler> | <destination> | <effect> | <source refs> | confirmed / inferred / unresolved / pending | <review-msg-001> | <SF-*> |

## Core Completeness Ledger

List every requested program and all pending readiness, deep-read, RLOG,
sidecar, identity, message, or source-mapping findings.

| Program | Run Resolution | Artifact Readiness | Five Primary Sections | Source Facts | Pending Findings / Follow-up |
| --- | --- | --- | --- | --- | --- |
| <PROGRAM> | <resolution> | ready / pending / not_ready | complete / partial / unavailable | <count> | <findings> |

## Coverage Reconciliation

Keep every normalized source fact visible. In a partial draft, unresolved
items remain `pending`; do not hide them to make the document look complete.

| Source Fact ID | Program | Source Section | Disposition | Review Row ID / Anchor | Merged Fact IDs / Exclusion Reason |
| --- | --- | --- | --- | --- | --- |
| <SF-*> | <PROGRAM> | <reader-first section> | included / merged / excluded_non_core / pending | <review-*> | <reason or merged IDs> |

## Sources

| Program | Analysis Directory | Primary Analysis | Readiness Evidence | Notes |
| --- | --- | --- | --- | --- |
| <PROGRAM> | <path> | <PROGRAM>-program-analysis.md | <readiness / pending findings> | <sidecars> |

## Run Profile

| Field | Value |
| --- | --- |
| Review Status | draft_exploratory |
| Program Order Semantics | SME navigation only; not a confirmed call chain |
| Artifact Repo Mode | <approved_document_repo / current_run> |
| Core Review Profile | standard_reader_first / minimal_reader_first |

## Source Inventory Cache

| Field | Value |
| --- | --- |
| Inventory Checked | <path or not_checked> |
| Freshness | <fresh / stale / not_checked / not_needed> |
| Targeted Recovery Queue | <path or none> |

<!--
This draft deliberately has no formal-review front matter or final-review H1.
Once every program is ready and coverage has zero pending facts, rewrite the
content as templates/sme-core-review.md and use the canonical formal filename.
-->
