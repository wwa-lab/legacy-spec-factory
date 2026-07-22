# Output Contract: Reader-First Program Analysis Merger

This contract defines the v0.4.0 preparation bundle and the one formal SME
review produced from finalized IBM i program analyses. It does not define a
transaction flow, trigger model, call graph, replay, lineage, or modernization
artifact.

## Responsibility Split

Deterministic scripts own artifact resolution, upstream readiness validation,
lossless extraction, fact normalization, initial pending coverage, targeted
queue creation, and final structural/coverage validation.

The LLM executing `legacy-ibmi-flow-analyzer` owns cross-program thematic
synthesis. A deterministic script must not generate a review skeleton, write a
formal review, claim semantic completion, or call an external LLM service.

## Output Identity And Placement

`--project-root` is the normal invocation surface and resolves its output
parent to `<project-root>/outputs/`, creating that directory when needed.
`--output-dir` remains an explicit advanced override and always means the
parent of a program-set bundle. The bundle
identity is:

```text
<folder_slug> = <FLOW-SLUG>--<PROGRAM-SET-SLUG>
```

`FLOW-SLUG` is collision-resistant while remaining readable:

```text
raw_identity = exact --flow-slug value, when supplied; otherwise exact review name
readable = slugify(raw_identity)[:64].rstrip("_")
FLOW-SLUG = readable + "_" + sha256_utf8(raw_identity)[:8]
```

`slugify` lowercases the value, replaces each non-alphanumeric run with `_`,
and trims surrounding `_`; an empty readable result becomes
`program_set_review`. Hash the unmodified raw identity, not the normalized
readable value. Consequently, raw identities that normalize to the same text
still produce distinct flow slugs.

Append `<folder_slug>` exactly once. If the supplied output path already ends
with that slug, use it directly. Program-set identity is always bound to the
sorted, distinct normalized program names and a short stable hash; a user-
supplied program-set slug is a readable prefix, not permission to reuse one
identity for a different set. Program order does not affect identity. If an
existing target manifest records a different flow/program-set identity, fail
without overwriting it. Normalization collisions must be rejected or resolved
with the stable identity hash, never silently overwritten.

The ready preparation bundle is:

```text
<output-parent>/<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
```

After LLM synthesis planning and zero-pending coverage reconciliation, exactly
one formal review is allowed:

```text
<folder_slug>--sme-core-review.md
```

The review filename is unique at file level as well as folder level. Do not
write or maintain `program-set-sme-core-review.md` as a generic alias.

Artifact resolution and workspace placement are configured by
`program_artifact_resolution_profile` and `delivery_workspace_profile` in the
delivery profile.

When readiness is blocked, the default bundle is:

```text
<output-parent>/<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-core-coverage.yaml       # overall blocked; no synthesized fact mappings
  missing-program-list-batch/          # created by the adapter for a blocked manifest
```

Within `missing-program-list-batch/`, the adapter also writes
`recovery-plan.md` (reader-facing) and `recovery-status.yaml` (machine-facing).
They preserve each program's upstream validator findings and classify targeted
next actions. `message-evidence-requests/` is present only for observed
message/status/code values whose descriptions still require source, catalog,
runtime, or SME evidence.

Only programs with a fresh exact mapping enter `program-list.csv` and
`prompt-queue/`; their generated prompt includes the retained recovery actions
and validator findings. Missing, stale, or unmapped programs enter only
`blocked-programs.csv` with `source_mapping_required`, and receive no guessed
path or generated scan prompt. If all programs are ready, the adapter is not
run and this directory must not exist.

The one-step intake defaults to a Cline serial recovery queue. Its explicit
`--recovery-runner kiro_parallel` mode instead forces immediate validation and
scaffold precreation, then adds isolated worker prompts and the Kiro dispatch
plan to this same directory. The recovery runner must repair an existing
`candidate_artifact_root` in place; it must not create a second tier-derived
program directory, because duplicate artifact roots remain a blocking
ambiguity.

Do not write `program-set-reader-first-source-pack.md`,
`program-set-core-facts.yaml`, the uniquely named formal review, or a generic
review alias while blocked. Partial source-pack/fact content is not a legal
synthesis input.

## Artifact Roles

### `program-list.txt`

Preserves the SME-supplied program navigation order and exact normalized
identity. That order is not evidence of runtime execution or a call chain.

The original SME programs file must remain available at the absolute path
recorded in `run_profile.program_list_source.path` through final validation;
the same record carries its SHA-256. `program-list.txt` is only the bundle
copy. The final gate re-reads the original file and requires its current digest
and ordered inputs to agree with the recorded manifest input, the normalized
distinct program identities, and the sibling copy. Missing, moved, modified,
or reordered source input fails validation instead of trusting coordinated
edits to derived bundle artifacts.

### `program-set-core-input-manifest.yaml`

Records stable review/folder identity, profile, artifact repo mode, program
order, distinct program resolution, artifact paths, readiness summary, source
inventory status, and formal review filename.

Required pre-synthesis program-set gate states in manifest `review_status`:

- `ready_for_synthesis`
- `blocked_artifact_readiness`

After the LLM completes zero-pending coverage and writes the formal review,
manifest, coverage, and formal-review `review_status` all become
`complete_exploratory`.

The legacy `partial_pending_program` review state is retained only as a
historical term and is not emitted in v0.4.0; blocked readiness produces no
formal review.

Keep four meanings separate:

- each program's `artifact_readiness.status` is `ready` or `not_ready`;
- manifest program-set `artifact_readiness` is `ready` when every distinct
  program passes the core reader-first gate; strict upstream findings may still
  be carried as per-program `pending_findings`;
- manifest program-set lifecycle is `blocked_artifact_readiness` or
  `ready_for_synthesis`, then `complete_exploratory` only after synthesis;
- manifest `merge_coverage` is `blocked` while readiness is blocked, `pending`
  during LLM reconciliation, and `complete` only after every fact is accounted.

The formal Markdown, manifest, and coverage may use
`review_status: complete_exploratory` only after every program is ready and
merge coverage is complete with zero pending items. A pre-synthesis gate status
never means the SME review is complete.

Legal `run_resolution` values include:

- `analyzed_this_run`
- `reused_same_run`
- `reused_artifact_repo`
- `pending_source`
- `blocked_missing_source`

`reused_artifact_repo` is legal only with explicit
`artifact_repo_mode: approved_document_repo`. The default is `current_run`; it
must never search arbitrary historical output or remote main.

### `program-set-artifact-readiness.yaml`

Contains one readiness result per distinct program and the exact upstream
validator outcome. Early intake uses `core_reader_first_lenient`: `ready`
requires the primary Markdown, correct program identity, safe/unambiguous
resolution, and meaningful content in all five reader-first sections. Strict
upstream findings that are outside those core sections (pending deep reads,
retained batch completion, sidecar/RLOG drift, terminal status, and unresolved
message descriptions) are retained in `pending_findings` rather than blocking
source-pack preparation.

The validator reconciles the main analysis with tier-required sidecars,
including `<PROGRAM>-program-analysis-summary.yaml`,
`<PROGRAM>-source-index.yaml`, `<PROGRAM>-routine-logic-details.yaml`, and
`<PROGRAM>-message-inventory.yaml`.

Missing/ambiguous paths, wrong program identity, or a missing/meaningless core
reader-first section is `not_ready` and blocks the whole formal review. A
`ready` row may still contain pending non-core findings; those findings remain
visible and the formal review is still prohibited until final coverage and the
strict validator pass.

### `program-set-reader-first-source-pack.md`

The lossless source pack contains, for every ready distinct program, the
complete bodies of:

1. `## Program Reading Summary`
2. `## Calculation Logic`
3. `## Validation Logic`
4. `## Exception Handling`
5. `## Message Inventory`

Program and section boundaries must be explicit. Do not shorten, paraphrase,
deduplicate, or replace these sections with compact sidecars during extraction.
See [`source-pack-and-coverage-contract.md`](source-pack-and-coverage-contract.md).

### `program-set-core-facts.yaml`

Normalizes every material contribution in the source pack and supporting
machine-readable artifacts. Every fact has a stable `source_fact_id`, program,
source section, exact value/content, routine and evidence when available, and
source location. Reordering programs or rerunning unchanged input must not
change an ID.

Evidence ID without an explicit Evidence Status is evidence present, not an
automatic unresolved fact. Canonical table headers from the upstream program
contract, including `Message / Code / Literal` and `Short Description`, must be
recognized.

### `program-set-core-coverage.yaml`

Preparation creates one `pending` coverage item per normalized source fact.
The executing skill LLM plans review rows/anchors and updates each item to
exactly one disposition before it writes the uniquely named formal review:

| Status | Meaning | Required mapping |
| --- | --- | --- |
| `included` | Fact appears directly in the review. | Existing review anchor and source fact reference. |
| `merged` | Fact is losslessly combined with related facts. | Existing anchor plus all merged source fact IDs. |
| `excluded_non_core` | Fact is genuinely outside the core contract. | Specific, auditable exclusion reason. |
| `pending` | Fact is not reconciled. | Final validation fails. |

Material calculations, validations, exceptions, exact messages/status/literals,
generic-handler tokens, and material routine outcomes cannot be excluded merely
for brevity. Every `included` or `merged` fact maps to exactly one stable review
row anchor. Any remaining `pending` item prohibits the formal review. When a
persisted intermediate is unavoidable, use only
`<folder_slug>--partial-draft.md` without final front matter/H1.

### `<folder_slug>--sme-core-review.md`

The LLM-created review front matter identifies at least `document_id`,
`flow_slug`, `program_set_slug`, programs, `review_status`, and
`artifact_version`. `artifact_version` is `0.4`; the skill/template generator
version may be `0.4.0`. Formal `review_status` is `complete_exploratory` and is
legal only after all artifact readiness checks and zero-pending coverage pass.
It begins with an SME-readable synthesis rather than an artifact inventory.

The default `standard_reader_first` order is:

```markdown
## Program Set Reading Summary
## Cross-Program Processing Overview
## Calculation Logic
## Validation Logic
## Exception Handling
## Message Inventory
## Core Completeness Ledger
## Coverage Reconciliation
## Sources
## Run Profile
## Source Inventory Cache
```

`minimal_reader_first` is explicit opt-in. It may move messages out of the
primary path, but must add `## Message Coverage Control` in the audit area and
retain every exact message fact, anchor, and source fact reference.

## Core Review Tables

Each material row requires a stable `Review Row ID` and `Source Fact Refs`.

### Program Set Reading Summary

The prose states scope, each program's contribution, all-program artifact
readiness, zero-pending coverage, `complete_exploratory` status, SME/Dify
deliverability, and navigation-order semantics. It also carries one anchored
contribution row per program:

```markdown
| Program | Scope / Reader-First Contribution | Artifact Readiness | Coverage | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- |
```

### Cross-Program Processing Overview

```markdown
| Processing Layer | Programs / Main Routines | What To Understand First | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- |
```

This is thematic reading orientation, not a sequence or call map. Any material
thematic source fact carried here requires its own anchor/reference; the table
must not introduce untracked claims.

### Calculation Logic

```markdown
| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Validation Logic

```markdown
| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Exception Handling

```markdown
| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Message Inventory / Message Coverage Control

```markdown
| Message / Status / Literal | Description | Type | Program / Routine Sources | Occurrences | Condition / Handler | Carrier / Destination | Effect | Detail Refs | Evidence Status | Review Row ID | Source Fact Refs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

Exact IDs, statuses, return codes, literals, operator text, and generic-handler
tokens must not be grouped into a label that loses individual values.

## LLM Merge Rules

- Read the full source pack before drafting.
- Organize facts by cross-program business/technical theme, not by file list.
- Preserve program, routine, carriers, guards, outcomes, exact messages,
  evidence, and all mapped `source_fact_id` values.
- Use one anchored row for a lossless merge; otherwise keep separate rows.
- Keep every requested program visible in the summary, completeness ledger,
  sources, and coverage reconciliation.
- State explicitly that the SME program order is navigation only.
- Include cross-program relationships only when upstream evidence directly
  supports them. Similar names or adjacency in the list are insufficient.
- Do not add business rules, call edges, lineage, or modernization decisions.

Never concatenate complete program-analysis files into the formal review. The
source pack preserves the five complete primary sections for audit; the LLM
must synthesize them into reader-first themes.

## Missing-Program Queue

When a requested program is missing or semantically not ready, run the recovery
adapter against the blocked manifest. Reuse an externally prepared fresh repo
inventory or exact approved mapping; never scan the entire repository as a
substitute for targeted recovery. The adapter writes a `recovery-plan.md` and
`recovery-status.yaml` alongside the queue. They classify each retained
validator finding as a required-artifact rebuild, reader-first structure repair,
semantic deep-read, message-evidence request, terminal approval, or targeted
refresh. Only affected programs with fresh exact paths enter
`program-list.csv`/`prompt-queue/`. Programs absent from fresh inventory, or
blocked by stale/unknown inventory, go only to `blocked-programs.csv` with a
source-mapping action and receive no guessed path.

The queue is placed at:

```text
<bundle>/missing-program-list-batch/
```

Do not create that directory for an all-ready manifest.

After targeted work completes, rerun preparation and readiness validation from
the original program list. No formal review is allowed while any program is
not ready.

## Five-Way Validation Gate

Before handoff, reconcile:

```text
manifest <-> source pack <-> facts <-> coverage <-> formal review
```

The validator fails when it finds any of these conditions:

- manifest program absent from the source pack, facts, ledger, or sources;
- missing or incomplete primary section for any program;
- missing, duplicated, or count-mismatched source fact;
- a source-pack fact absent from facts even when the same omission was also
  made in coverage and the review;
- `pending` coverage or unsupported `excluded_non_core`;
- missing/duplicate review anchor—including summary/thematic contributions—or
  a row that omits mapped fact IDs;
- changed or dropped exact message/status/literal;
- substring-only exact matches (`100` cannot satisfy source status `00`) or a
  mapped row that changes its routine, carrier, guard, effect, or evidence;
- divergent `items`/`coverage_items`, non-complete final coverage status, or a
  reused anchor that is not one declared lossless merge group;
- changed or dropped generic-handler token or message carrier/destination;
- placeholder/scaffold content, link-only core rows, or definitive claims with
  no supporting evidence;
- review written while readiness is blocked;
- filename/front matter/identity mismatch;
- navigation order described as a source-confirmed execution/call chain; or
- an Overview row/prose claim about calls, producer/consumer, or execution
  sequence without known supporting source fact references; or
- a forbidden full-flow section such as Trigger Inventory, Nodes, Edges,
  Transaction Call Map, Replay, Persistence, Lineage, UI Surfaces, Capability
  Seeds, or SME Checklist.

Only a zero-finding result is suitable for SME/Dify handoff.

Concrete `unresolved`/`TBD-*` rows from an upstream
`approved_with_non_blocking_tbd` artifact are allowed when they retain source
evidence and identify the precise unresolved point. They are distinct from
blank/TODO/generic scaffold placeholders, which always fail.

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
-->
