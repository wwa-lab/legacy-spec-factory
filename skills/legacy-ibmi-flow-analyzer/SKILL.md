---
name: legacy-ibmi-flow-analyzer
description: Merge existing IBM i program-analysis artifacts into one compact SME review. Use when an SME provides a program list or program flow and wants the core Calculation Logic, Validation Logic, Exception Handling, and Message Inventory combined without reconstructing a transaction flow.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Program Analysis Merger

## Skill Card

| Field | Notes |
| --- | --- |
| Problem solved | Combines several existing program-analysis results into one readable SME review. |
| Input | SME program list/order plus program-analysis artifacts from a working output root or approved document repository. |
| Output | `program-set-sme-core-review.md`, its manifest, bounded core facts, and optional missing-program scan queue. |
| Default behavior | Read and merge evidence that already exists. Do not reconstruct an end-to-end transaction flow. |
| Upstream skill | `legacy-ibmi-program-analyzer` and, when source discovery is needed, `legacy-ibmi-program-list-batch`. |
| Downstream consumer | SME review and later module/spec preparation after human approval. |
| Main risk | Inventing cross-program calls, business rules, or data lineage from program names or list order. |

## Purpose

This skill is intentionally small. It takes the results of independent
program scans and makes them easier for an SME to review together.
The merge is program-evidence first, with no cross-run reuse by default.

The core operation is:

```text
program list
  -> locate each program-analysis artifact
  -> extract core evidence
  -> merge by review section
  -> validate coverage and evidence links
```

The program list is navigation and scope evidence. Its order is not proof of a
call chain. The skill does not discover runtime order, infer calls, or turn the
set into a transaction graph.

## Scope

The default review contains these reader-first sections:

1. Program Set Reading Summary
2. Cross-Program Processing Overview
3. Calculation Logic
4. Validation Logic
5. Exception Handling
6. Message Inventory

`standard_reader_first` is the default profile. `minimal_reader_first` may be
selected explicitly when Message Inventory should not be part of the primary
reading path.

The review is self-contained for SME reading. Each logic row should identify
the Program, Routine, observed logic, carrier/guard/outcome, and Evidence. A
supporting path is useful for traceability, but a link by itself is not an
explanation.

## Explicit non-goals

This skill does not:

- classify or analyze transaction entry mechanisms;
- reconstruct a complete transaction flow or call graph;
- generate Nodes, Edges, Transaction Call Maps, Replay, Lineage, or a
  transaction-level Persistence Matrix;
- infer business rules, modernization decisions, or service boundaries;
- concatenate full program-analysis Markdown files into one large document;
- rescan the entire source repository because one program is missing.

Older full-flow templates and references may remain in the repository for
historical compatibility, but they are not part of this skill's active
workflow or output contract.

## Inputs

Required:

- an ordered or unordered SME program list, with a review name;
- a program artifact root containing the requested program folders; and
- the program-analysis artifact set for each program that is already scanned.

Preferred per-program artifacts are program-prefixed:

```text
<PROGRAM>-program-analysis.md
<PROGRAM>-program-analysis-summary.yaml
<PROGRAM>-source-index.yaml
<PROGRAM>-routine-index.md
<PROGRAM>-message-inventory.yaml
<PROGRAM>-routine-logic-details.md
<PROGRAM>-routine-logic-details.yaml
```

Optional sidecars are consumed when they exist or when the upstream analyzer
produced them:

```text
<PROGRAM>-file-io-inventory.yaml
<PROGRAM>-field-mutation-matrix.yaml
<PROGRAM>-sql-inventory.yaml
```

Optional run inputs:

- `delivery-profile.yaml` for artifact folder/name patterns and output roots;
- a source root plus a fresh `outputs/repo-scan` inventory when missing
  programs may need a targeted scan;
- an approved local document repository clone, selected explicitly with
  `artifact_repo_mode: approved_document_repo`;
- reference packs or control files for targeted message/status clarification.

The portable configuration uses `program_artifact_resolution_profile` and
`delivery_workspace_profile`; see `templates/delivery-profile.yaml`.

No trigger model, entry point, scheduler export, screen definition, or runtime
trace is required for this merge.

## Artifact resolution and status

Resolve each distinct normalized program exactly once for the current request.
Use program-prefixed filenames first, with the configured bare-name fallback
for older artifacts. A program is resolved only when all required compact
artifacts are present. A folder with only some artifacts is still pending and
must not be treated as usable analysis evidence. Record one `run_resolution`
per program:

- `analyzed_this_run` — complete artifacts are present in the current output
  root;
- `reused_same_run` — the same program appeared earlier in this request and
  reuses that current-run artifact;
- `reused_artifact_repo` — the artifact came from an explicitly approved local
  document repository;
- `pending_source` — the requested program needs a source scan;
- `blocked_missing_source` — the requested program cannot be located or its
  source mapping is not available.

Do not silently use remote-main, arbitrary prior-run folders, or another
analyst's unapproved output as current evidence.
There is no cross-run reuse unless an approved document repository is selected
explicitly.

## Output contract

The primary output folder is:

```text
<program-set-review-parent>/<FLOW-SLUG>--<PROGRAM-SET-SLUG>/
  program-set-core-input-manifest.yaml
  program-set-core-facts.yaml
  program-set-sme-core-review.md
```

The canonical review filename remains stable. The parent folder is the
uniqueness boundary. If no program-set slug is supplied, the builder derives a
readable slug from the sorted normalized program names plus a short stable
hash. A rerun of the same program set updates the same path.

The manifest records program coverage, artifact status, review status, profile,
folder identity, and run policy. The review status is:

- `complete_exploratory` when every requested program has the required evidence;
- `partial_pending_program` when one or more programs or required artifacts are
  still missing.

`program-set-core-facts.yaml` is an evidence-bounded intermediate. It may copy
only explicit rows from upstream Calculation Logic, Validation Logic,
Exception Handling, and Message Inventory artifacts. It must not create
business rules, modernization decisions, call edges, or unsupported lineage.

## Missing program scan queue

If a requested program has missing required artifacts, do not hide it and do
not restart the full scan. Use the targeted queue adapter:

```text
<review-folder>/missing-program-list-batch/
  program-list.csv
  program-list-status.csv
  batch-scan-manifest.yaml
  program-batch-plan.md
  prompt-queue/
  cline-serial-runner-prompt.md
  program-set-scan-queue.yaml
```

Create it with:

Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\create_missing_program_scan_queue.py --manifest <program-set-core-input-manifest.yaml> --source-root <source-repo> --delivery-root <delivery-working-root> --out-dir <review-folder>\missing-program-list-batch
```

macOS/Linux:

```bash
python3 scripts/create_missing_program_scan_queue.py \
  --manifest <program-set-core-input-manifest.yaml> \
  --source-root <source-repo> \
  --delivery-root <delivery-working-root> \
  --out-dir <review-folder>/missing-program-list-batch
```

The adapter reuses `legacy-ibmi-program-list-batch`. It queues only programs
that a fresh source inventory can locate. Programs missing from the inventory,
or programs covered by a stale/unknown inventory, are written to
`blocked-programs.csv` and receive no invented source path.

After the queue finishes, rerun the normal builder and validator. The review
must remain `partial_pending_program` until the artifacts actually exist.

## One-step intake

SMEs do not need to create `program-set-core-input-manifest.yaml` manually.
Use the intake command with the program list, source root, existing artifact
root, profile, and review output directory. It runs the builder first and then
creates the missing-program queue when required:

Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\prepare_program_set_core_review.py --review-name "<review-name>" --programs-file <program-list.csv> --artifact-root <artifact-root> --source-root <source-repo> --profile .agents\skills\legacy-ibmi-flow-analyzer\templates\delivery-profile.yaml --output-dir <review-output> --force
```

macOS/Linux:

```bash
python3 scripts/prepare_program_set_core_review.py \
  --review-name "<review-name>" \
  --programs-file <program-list.csv> \
  --artifact-root <artifact-root> \
  --source-root <source-repo> \
  --profile templates/delivery-profile.yaml \
  --output-dir <review-output> \
  --force
```

`--delivery-root` may be supplied when targeted program scans must write to a
different delivery checkout; otherwise it defaults to `--artifact-root`.

## Merge rules

- Read compact artifacts first; open `program-analysis.md` only for targeted
  human-readable clarification.
- Preserve the SME program order as navigation evidence, not as a confirmed
  call sequence.
- Keep every requested program visible in Sources and the Core Completeness
  Ledger, including missing programs.
- Keep evidence labels and source paths attached to every merged row.
- Keep facts at program level. Include a cross-program relationship only when
  the upstream artifacts explicitly support it; otherwise mark it unresolved.
- Treat upstream reference packs and control files as supporting context, not
  as replacements for source evidence or SME approval.
- Do not add a rule merely because two programs use similarly named fields,
  files, messages, or routines.

## Workflow

1. Read the SME program list and delivery profile.
2. Normalize program names while preserving meaningful prefixes such as `@`.
3. Resolve each program to the current artifact root or explicitly approved
   document repository.
4. Run the one-step intake command, which creates the manifest, bounded facts,
   review skeleton, and targeted queue when artifacts are missing.
5. Stop the merge at `partial_pending_program` until every required artifact is
   present.
6. Fill the six reader-first sections from evidence-bounded upstream rows.
7. Run the validator before SME handoff.
8. After a missing-program queue completes, rerun steps 3-7; do not manually
   patch old pending rows into complete status.

## Validation

The validator must confirm:

- the default or explicitly selected profile's sections are present and ordered;
- every manifest program appears in Sources and the Core Completeness Ledger;
- missing programs are explicitly pending or blocked;
- required calculation, validation, exception, and message rows are not
  placeholders or link-only rows;
- evidence fields and carrier/outcome detail are present;
- the review contains none of the full-flow sections listed in the non-goals.

Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py validate --manifest <program-set-core-input-manifest.yaml> --review <program-set-sme-core-review.md>
```

macOS/Linux:

```bash
python3 scripts/validate-program-set-core-review.py \
  --manifest <program-set-core-input-manifest.yaml> \
  --review <program-set-sme-core-review.md>
```

## Runtime portability

Canonical source: `skills/legacy-ibmi-flow-analyzer/`.

Runtime adapters are synced with `scripts/sync-skills.sh`:

- `.codex/skills/legacy-ibmi-flow-analyzer/`
- `.claude/skills/legacy-ibmi-flow-analyzer/`
- `.opencode/skills/legacy-ibmi-flow-analyzer/`
- `.agents/skills/legacy-ibmi-flow-analyzer/`

Use `python3` on macOS/Linux. On Windows use `py -3`, then retry the same
command once with `python` only when the launcher is unavailable.
