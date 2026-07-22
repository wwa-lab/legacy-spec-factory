# Active Example: Ready Reader-First Merge

This is the active positive contract walkthrough for the v0.4.0 Program
Analysis Merger. It demonstrates deterministic preparation followed by
synthesis by the LLM executing the skill. Paths and fact IDs below are
symbolic; executable fixture bundles live in the repository test suite.

## Request

```text
Review name: Credit check
Artifact repo mode: approved_document_repo
Profile: standard_reader_first
Programs in SME navigation order:
1. CU106
2. CU101A
```

Both program directories pass the upstream program final validator. Their
terminal status is approved, all retained deep-read batches are complete, and
their five reader-first sections are complete and synchronized with routine
and message sidecars.

## Deterministic Preparation Result

```text
outputs/<FLOW-SLUG>--<PROGRAM-SET-SLUG>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
```

Every program row has `artifact_readiness.status: ready`. The manifest has
`review_status: ready_for_synthesis`, `artifact_readiness: ready`, and
`merge_coverage: pending`. The source pack contains the complete Program
Reading Summary, Calculation Logic, Validation Logic, Exception Handling, and
Message Inventory from CU106 and CU101A. All normalized facts begin as
`pending`. No Markdown review exists yet.

## LLM Synthesis Result

The executing skill LLM reads the full source pack, groups related facts by
calculation, validation, and failure/outcome themes, plans anchors, and clears
all pending coverage. Only then does it write exactly:

```text
<FLOW-SLUG>--<PROGRAM-SET-SLUG>--sme-core-review.md
```

Example lossless mappings:

```markdown
| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Derive the approved amount and place it on the response carrier. | CU106 | MAIN | APPROVED_AMOUNT | REQUEST_AMOUNT; ACCOUNT_LIMIT | request valid and account active | returns the approved amount | EV-CU106-CALC-001 | confirmed | <a id="review-calc-001"></a> review-calc-001 | SF-CU106-CALC-A1B2 |
```

Coverage marks that fact `included` at `review-calc-001`. If one thematic row
also represents a compatible CU101A fact, the row lists both IDs and coverage
marks both facts `merged` to the same anchor. Exact messages remain separate
auditable values. The completed manifest records
`review_status: complete_exploratory`, `artifact_readiness: ready`, and
`merge_coverage: complete`; coverage and formal review also record
`review_status: complete_exploratory`.

Final validation reconciles manifest, source pack, facts, coverage, and review.
The SME list order remains navigation only; this example makes no call-chain
claim.

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang
Original author: Leo L Zhang
License: Apache License 2.0
-->
