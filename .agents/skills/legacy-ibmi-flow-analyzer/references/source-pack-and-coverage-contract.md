# Source Pack And Coverage Contract

This reference defines the lossless boundary between finalized per-program
analysis and the formal cross-program SME review.

## Source Pack Boundary

For every distinct resolved scan result, extract the available bodies of these five
top-level sections from the final `<PROGRAM>-program-analysis.md`:

```text
Program Reading Summary
Calculation Logic
Validation Logic
Exception Handling
Message Inventory
```

Preserve text, tables, exact literals, evidence IDs, RLOG references, TBD
wording, and source order. Wrap content with explicit program and section
markers. Extraction may normalize line endings but must not summarize,
truncate, merge, reorder, or silently deduplicate content.

The five sections in the main Markdown are the semantic primary input. YAML
and Markdown sidecars may confirm row completeness and add stable machine
fields; they must not displace or contradict the primary input.

## Readiness Before Formal Handoff

The strict readiness gate controls formal synthesis and handoff. A failed,
missing, ambiguous, placeholder, pending-deep-read, non-terminal-batch, or
blocking/required message-description gap remains visible as a pending finding
or unavailable-program marker in a scan-result merge. It blocks the formal
review, but it does not prevent preserving available scan output in the source
pack. A concrete evidence-bounded non-blocking unresolved/TBD carried by terminal
`approved_with_non_blocking_tbd` remains legal input and must be preserved; it
is not equivalent to an empty TODO or scaffold placeholder.

## Normalized Source Facts

Create facts from every material contribution in the source pack, including:

- each program's reading-summary contribution;
- every calculation/assignment row and material thematic statement;
- every validation/status/outcome row and material thematic statement;
- every exception/error-path row and material thematic statement;
- every exact message, status, return code, SQL state, response literal,
  operator text, or generic-handler token row, including its trigger/handler,
  carrier/destination, and effect;
- every material routine/RLOG contribution needed to retain carrier, guard,
  action, or outcome meaning; and
- explicit unresolved statements that remain allowed by terminal upstream
  status.

Recognize the canonical upstream table headers as well as documented aliases.
In particular, `Message / Code / Literal` plus `Short Description` is a
canonical message table, not an unknown table.

Each fact contains enough data to audit its source:

```yaml
source_fact_id: SF-<PROGRAM>-<KIND>-<stable-token>
program: <PROGRAM>
section: <source H2>
kind: summary | calculation | validation | exception | message | routine
content: <complete normalized meaning>
exact_value: <message/status/literal when applicable>
routine: <routine or RLOG when available>
evidence_reference: <evidence/RLOG/source reference when available>
evidence_status: confirmed | inferred | unresolved | evidence_present
source_location: <artifact and section/row identity>
```

The identifier must be deterministic from stable source identity/content, not
list position or processing timestamp. A present Evidence ID without an
explicit Evidence Status is `evidence_present`; it must not be reclassified as
unresolved solely because the status column is absent.

## Initial Coverage

Preparation emits exactly one `pending` item for every `source_fact_id`.
Coverage counts must equal normalized fact counts per program, section, kind,
and total.

```yaml
source_fact_id: SF-CU106-CALC-...
program: CU106
section: Calculation Logic
status: pending
review_anchor: null
merged_source_fact_ids: []
exclusion_reason: null
```

## LLM Coverage Completion

The executing skill LLM assigns exactly one of:

- `included`: one direct anchored review row;
- `merged`: one lossless anchored review row carrying every merged fact ID;
- `excluded_non_core`: a genuinely non-core contextual fact with a specific
  contract-based reason; or
- `pending`: not yet mapped and therefore not deliverable.

Plan anchors in working memory before formal output. An anchor must be stable,
unique, present in the eventual formal review, and referenced by the coverage
item. The review row must display its `Review Row ID` and `Source Fact Refs`.
HTML anchors such as `<a id="review-calc-001"></a>` are portable; use the
validator-supported form consistently.

Material calculations, validations, exception paths, exact messages/statuses/
literals/generic-handler tokens, and material routine outcomes cannot use
`excluded_non_core` merely to fit a shorter document. For
`minimal_reader_first`, message facts move to `Message Coverage Control`; they
do not disappear.

Do not create the formal `<folder_slug>--sme-core-review.md` while any coverage
item is pending. Finish synthesis and the anchor plan first. If a persisted
intermediate is unavoidable, use `<folder_slug>--partial-draft.md` without the
formal front matter/H1; it is never an SME/Dify deliverable.

## Reconciliation Invariants

Final validation proves all of the following:

1. Every manifest program has all five source-pack sections.
2. Every material source-pack contribution has one stable normalized fact.
3. Every normalized fact has exactly one coverage item.
4. Every `included`/`merged` item points to an existing unique review anchor.
5. Every anchored review row lists the same fact IDs claimed by coverage.
6. Every exact message/status/literal is textually preserved.
7. Per-program, per-section, per-kind, and total counts agree.
8. No coverage item is pending and every exclusion is supported.

The gate is bidirectional: it re-extracts facts from each marked lossless
source-pack block and compares the complete fact IDs and content with the
normalized inventory. Deleting the same fact from facts, coverage, and review
therefore still fails. Exact values use token-aware matching (`00` is not
present inside `100`). Each material mapped row must also retain its typed
routine, carrier, guard/condition, action/effect, evidence, and other
source-row semantics—not merely the anchor, fact ID, and exact token.

An anchor definition appears exactly once. Multiple facts may share it only
when every corresponding coverage item is `merged` and declares the complete
merged fact group. For schema `0.4`, `items` and `coverage_items` are identical
mirrors, `coverage_status` is `complete`, and declared counts match both lists.
Overview rows likewise carry a unique anchor and known source fact refs;
untracked call, producer/consumer, or execution-sequence claims fail.

The validator must reject omissions even when the resulting review reads
smoothly. Readability never overrides fact coverage.

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
-->
