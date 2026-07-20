# Output Contract: Program Analysis Merge

This contract defines the compact output for merging multiple existing
`program-analysis` artifacts. It does not define a transaction-flow, trigger,
call-graph, replay, lineage, or modernization artifact.
The merge is program-evidence first, with no cross-run reuse by default.

Artifact resolution and workspace settings come from
`program_artifact_resolution_profile` and `delivery_workspace_profile` in the
delivery profile.

## Primary files

The deterministic builder writes:

```text
program-set-core-input-manifest.yaml
program-set-core-facts.yaml
program-set-sme-core-review.md
```

The stable review path is:

```text
<program-set-review-parent>/<FLOW-SLUG>--<PROGRAM-SET-SLUG>/
  program-set-core-input-manifest.yaml
  program-set-core-facts.yaml
  program-set-sme-core-review.md
```

`program-set-sme-core-review.md` is the canonical filename. The parent folder
provides uniqueness. When no program-set slug is supplied, derive one from
sorted normalized program names plus a short stable hash. Do not add dates or
versions to the canonical filename; reruns of the same set update the same
path.

## Review sections

The default `standard_reader_first` review uses this order:

```markdown
## Program Set Reading Summary
## Cross-Program Processing Overview
## Calculation Logic
## Validation Logic
## Exception Handling
## Message Inventory
## Core Completeness Ledger
## Sources
## Run Profile
## Source Inventory Cache
```

The explicit `minimal_reader_first` profile omits Message Inventory from the
primary reading path. The audit/control sections remain required.

### Program Set Reading Summary

Explain in SME language what the selected program set covers and what each
program contributes to the review. State whether the review is
`complete_exploratory` or `partial_pending_program`. Do not turn this section
into an artifact inventory or a guessed call chain.

### Cross-Program Processing Overview

Use a short orientation table:

```markdown
| Processing Layer | Programs / Main Routines | What To Understand First |
| --- | --- | --- |
| program scope | PROGRAM / RLOG-* | what this set covers |
| calculation | PROGRAM / RLOG-* | source-backed calculation |
| validation | PROGRAM / RLOG-* | status/message condition |
| exception / outcome | PROGRAM / RLOG-* | observed handling or unresolved gap |
```

This is an SME reading orientation. It is not a transaction call map.

### Calculation Logic

Every row must explain the observed calculation or assignment and carry:

```markdown
| Calculation / Assignment | Program | Routine | Target Field / Carrier | Source Operands / Carriers | Guard / Branch | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Validation Logic

Every row must explain the observed validation/status behavior and carry:

```markdown
| Message / Status / Outcome | Description | Program | Routine | Condition / Evidence | Carrier / Destination | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Exception Handling

Every row must explain the observed error path and carry:

```markdown
| Exception / Error Path | Program | Routine | Detection Mechanism | Fields / Messages Set | Handling Action | Effect | Supporting Detail | Evidence Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
```

### Message Inventory

In `standard_reader_first`, list exact observed message IDs, status values,
return codes, literals, descriptions, program/routine sources, and evidence.
Do not add a business interpretation that is not present in the upstream
artifact or approved SME note.

### Core Completeness Ledger

The ledger must include every program from the SME list, in the supplied order
when order was supplied:

```markdown
| Program | Expected In Scope From | Run Resolution | Routine Logic Evidence | Message Inventory | Missing / Targeted Follow-up |
| --- | --- | --- | --- | --- | --- |
```

Use `pending_source` or `blocked_missing_source` when appropriate. Missing
programs must remain visible; do not create invented calculation or exception
rows for them.

### Sources

Sources must map each program to its artifact directory, compact artifacts,
`run_resolution`, and follow-up status. A supporting path is not a substitute for
the explanation in the core reading sections.

An artifact directory is not sufficient by itself: if any required compact
artifact is missing, the program remains pending and the review is partial.

### Run Profile and Source Inventory Cache

These sections record artifact root, run mode, current-run versus explicitly
approved document-repository reuse, inventory path/freshness, and the next
action for pending programs. They are control evidence, not primary SME prose.

## Program artifact contract

Use program-prefixed artifacts first:

```text
<PROGRAM>-program-analysis.md
<PROGRAM>-program-analysis-summary.yaml
<PROGRAM>-source-index.yaml
<PROGRAM>-routine-index.md
<PROGRAM>-message-inventory.yaml
<PROGRAM>-routine-logic-details.md
<PROGRAM>-routine-logic-details.yaml
```

Optional sidecars may include:

```text
<PROGRAM>-file-io-inventory.yaml
<PROGRAM>-field-mutation-matrix.yaml
<PROGRAM>-sql-inventory.yaml
```

Read compact artifacts first. Use the human-readable Markdown only for
targeted clarification. Never concatenate complete program-analysis files.

## Evidence and merge rules

- Program order is navigation evidence, not source-confirmed call evidence.
- Every merged row must identify its Program, Routine when available, and
  upstream Evidence or evidence status.
- Cross-program relationships are included only when the upstream artifacts
  explicitly support them; otherwise keep the facts at program level.
- Similar program names, field names, file names, or statuses do not prove a
  relationship.
- Do not create business rules, modernization decisions, call edges, or
  transaction-level lineage in this artifact.
- Reference packs and control files can clarify terminology but do not replace
  source evidence or SME approval.

## Run resolution

Legal values are:

- `analyzed_this_run`
- `reused_same_run`
- `reused_artifact_repo`
- `pending_source`
- `blocked_missing_source`

`reused_artifact_repo` is legal only when the manifest explicitly records
`artifact_repo_mode: approved_document_repo`. Remote-main or arbitrary prior
run artifacts do not satisfy the default evidence policy.
There is no cross-run reuse unless that approved document repository mode is
selected explicitly.

## Missing-program queue

When required artifacts are missing, the optional queue lives beside the
review:

```text
missing-program-list-batch/
  program-list.csv
  program-list-status.csv
  batch-scan-manifest.yaml
  program-batch-plan.md
  prompt-queue/
  cline-serial-runner-prompt.md
  program-set-scan-queue.yaml
```

Create it with `scripts/create_missing_program_scan_queue.py`. It reuses the
`legacy-ibmi-program-list-batch` initializer and queues only missing programs
that a fresh source inventory can locate. Other programs go to
`blocked-programs.csv` with a source/name follow-up. After queue completion,
rerun the builder and validator.

When no core manifest exists yet, use
`scripts/prepare_program_set_core_review.py`; it creates the manifest first and
then invokes the same queue logic.

## Validation

The validator must confirm:

- selected sections exist in the required order;
- every manifest program appears in Sources and the Completeness Ledger;
- calculation, validation, exception, and standard message rows are not
  placeholders or link-only rows;
- missing programs are explicit pending/blocked rows;
- evidence, carrier, guard, handling, or outcome fields are present;
- full-flow sections are absent from the compact review.

The validator must pass before SME handoff. A partial review may be handed to
the SME only when its status and missing follow-ups are explicit.
