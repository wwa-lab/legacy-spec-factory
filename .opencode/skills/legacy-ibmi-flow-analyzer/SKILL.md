---
name: legacy-ibmi-flow-analyzer
description: Prepare and validate a controlled, reader-first merge of finalized IBM i program-analysis artifacts, then let the executing skill LLM synthesize one evidence-complete SME core review without inventing a call chain.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Reader-First Program Analysis Merger

## Skill Card

| Field | Contract |
| --- | --- |
| Problem solved | Merge several finalized, reader-first program analyses into one SME/Dify-ready core review without losing program facts. |
| Required user input | Merge mode: review name, ordered program list, program artifact root, and delivery project root. Requalification mode: approved artifact root, profile, and separate output directory. Source root is required only for targeted missing-program recovery. |
| Primary evidence | The complete content of five `##` sections in every `<PROGRAM>-program-analysis.md`: Program Reading Summary, Calculation Logic, Validation Logic, Exception Handling, and Message Inventory. |
| Preparation output | Readiness ledger, lossless source pack, normalized source facts, and pending coverage control. |
| Formal output | Exactly one `<folder_slug>--sme-core-review.md`, written by the LLM executing this skill only after every program is ready and coverage has zero pending facts. |
| Default policy | `approved_document_repo`; `current_run` is explicit opt-in. |
| Default profile | `standard_reader_first`; `minimal_reader_first` is explicit opt-in. |
| Upstream gate | `legacy-ibmi-program-analyzer` final contract validator plus merger readiness checks. |
| Downstream boundary | SME/Dify review. Module/BRD/spec routing requires a separately migrated compatibility contract and is not implied by this output. |
| Main safety risk | Omitting a material per-program fact or presenting SME list order as a confirmed call chain. |

## Purpose And Boundary

This skill is a controlled **Program Analysis Merger**, not a transaction-flow
reconstructor. It uses deterministic tooling to make the input complete and
auditable, then uses the LLM already executing the skill to perform the only
semantic step: a thematic cross-program synthesis for SME reading.

In short: merge existing IBM i program-analysis artifacts through a
program-evidence first workflow. The approved document/delivery repository is
the default source of truth because artifacts enter it only after SME review;
`current_run` is an explicit opt-in for active scan branches.

```text
SME program list + explicit paths
  -> resolve one finalized analysis per distinct program
  -> run upstream finalization/readiness gate
  -> prepare lossless reader-first source pack
  -> normalize stable source facts and pending coverage
  -> executing skill LLM synthesizes one review
  -> reconcile manifest + source pack + facts + coverage + review
  -> validate before SME/Dify handoff
```

The deterministic scripts must never:

- write a review skeleton or formal SME review;
- impersonate semantic synthesis;
- invoke an external LLM service; or
- mark coverage complete before the executing skill LLM maps the facts.

The executing skill LLM must not bypass the preparation artifacts or readiness
gate. It writes the formal review only after the manifest reaches
`ready_for_synthesis`, every program readiness row says `ready`, and the LLM's
anchor/coverage plan contains zero pending facts.

## Explicit Non-Goals

Do not use this skill to discover or assert a full transaction flow. The formal
review must not contain active sections named:

- Trigger Inventory
- Nodes
- Edges
- Transaction Call Map
- Replay
- Persistence or a transaction-level Persistence Matrix
- Lineage
- UI Surfaces
- Capability Seeds
- SME Checklist

Do not infer calls, execution order, data lineage, business rules,
modernization decisions, or service boundaries from program names, similar
fields, or SME list order. The supplied order is navigation evidence only.

The former trigger/data-flow/error-propagation references, full-flow templates,
and transaction-flow examples are retained as historical, non-active material;
they are not inputs or outputs of this merger.

## Required Inputs

Collect these values before preparation:

```text
Review name: <business-readable name>
Programs in SME navigation order: <ordered program names supplied inline>
Program artifact root: <approved local document-repo clone by default, or current-run root when explicitly selected>
Project root: <delivery project root; writes under its outputs/ folder>
Output parent: <optional explicit override; parent that will contain the generated bundle folder>
Profile: standard_reader_first | minimal_reader_first
Artifact repo mode: current_run | approved_document_repo
Source root: <optional; needed only for targeted missing-program recovery>
```

Program identity is exact after configured normalization. Preserve meaningful
prefixes such as `@`. Resolve each distinct normalized program once; duplicate
list entries may reuse the same artifact only within the same request/run.
Artifact folder/name resolution comes from
`program_artifact_resolution_profile`; output workspace placement comes from
`delivery_workspace_profile` in `templates/delivery-profile.yaml`.

### Artifact Repository Modes

- `approved_document_repo` is the default. Resolve only from the supplied local
  clone of the approved document/delivery repository. In this workflow,
  artifacts in that repository have completed SME review; record
  `reused_artifact_repo` in the manifest.
- `current_run` is explicit opt-in. Resolve only under
  the supplied current working artifact root. An arbitrary prior run, remote
  branch, or another analyst's output is not evidence for that run.

Record the resulting value in each program's `run_resolution`, using
`analyzed_this_run`, `reused_same_run`, `reused_artifact_repo`,
`pending_source`, or `blocked_missing_source` as applicable.

There is no implicit fallback between the approved repository and current-run
artifact modes.

The SME navigation order is the only required program-list input. Preparation
generates the bundle-local `program-list.txt` in that exact order and records
its SHA-256 in `run_profile.program_list_source` with
`kind: generated_from_navigation_order`. Final validation reconciles that
generated snapshot with the manifest's ordered inputs and normalized distinct
program identities. The legacy `--programs-file` option remains supported for
backward-compatible callers and records the external source path and digest.

## Reader-First Primary Input

For each program, the merger reads the complete content—not a shortened
summary—of these five sections from `<PROGRAM>-program-analysis.md`:

1. `## Program Reading Summary`
2. `## Calculation Logic`
3. `## Validation Logic`
4. `## Exception Handling`
5. `## Message Inventory`

The source pack preserves each section verbatim within an identified program
boundary so an SME fact cannot disappear through early compression. The main
Markdown is the semantic primary input. Machine-readable sidecars such as
`program-analysis-summary.yaml`, `source-index.yaml`,
`routine-logic-details.yaml`, and `message-inventory.yaml` support validation,
normalization, and reconciliation;
they do not replace the five reader-first sections.

See [`references/source-pack-and-coverage-contract.md`](references/source-pack-and-coverage-contract.md)
for the extraction and source-fact rules.

## Upstream Artifact Readiness Gate

An artifact directory is not ready merely because files exist. Before source
pack creation, invoke or reuse the final validator from
`legacy-ibmi-program-analyzer` for every distinct program analysis. A program's
`programs[].artifact_readiness.status` is `ready` when the primary
`program-analysis.md` belongs to the requested program and its five
reader-first sections are present and meaningful (not an empty or placeholder
shell). `Message Inventory` may be absent or empty when the scan has observed
no messages/status literals; that condition is recorded as a pending
no-observed-message finding. The artifact path must also be unambiguous and
remain inside the supplied artifact root.

The merger uses a **core-first lenient readiness policy** for early scans. The
upstream final validator still runs when possible, but pending deep reads,
incomplete retained batches, non-terminal status fields, missing non-core
sidecars, RLOG/detail drift, and unresolved message descriptions are retained
as `pending_findings`; they do not block source-pack preparation while the five
reader-first sections remain useful. These pending items still prevent a
formal review until the LLM resolves coverage and final validation passes.

A canonical `large_extreme_program` artifact root remains immutable readiness
context: the upstream validator is called with that expected tier, so a
rewritten normal summary cannot erase the discrepancy. The discrepancy is
pending during early intake and enforced at final delivery. When a program was
completed through `legacy-ibmi-program-list-batch`, consume only its terminal
batch state after its precreated locks have been checked; an unvalidated raw
large artifact folder remains exploratory.

Record each check in `program-set-artifact-readiness.yaml` and in the manifest.
Each row includes `blocking_findings`, `pending_findings`, and
`readiness_policy: core_reader_first_lenient`.
The manifest program-set state is:

- `review_status: ready_for_synthesis`, `artifact_readiness: ready`, and
  `merge_coverage: pending` when every distinct program passes the core
  reader-first gate, even if its readiness row contains pending non-core work;
- `review_status: blocked_artifact_readiness`,
  `artifact_readiness: not_ready`, and `merge_coverage: blocked` when any
  requested program is missing, invalid, ambiguous, incomplete, or
  non-terminal.

The legacy `partial_pending_program` formal-review state is retired: blocked
readiness now means no formal review.

Do not downgrade a semantic failure to “file present.” Do not synthesize a
partial formal review.

## Deterministic Preparation Contract

Run the preparation command from the canonical skill or a synced runtime
adapter. The normal project-root form writes under `<project-root>/outputs/` and
creates that directory when necessary:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py build \
  --review-name "<review name>" \
  --program <PROGRAM_A> \
  --program <PROGRAM_B> \
  --program <PROGRAM_C> \
  --working-root <program-artifact-root> \
  --profile skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml \
  --project-root <delivery-project-root>
```

The default assumes that `<program-artifact-root>` is a local clone of the
SME-reviewed approved document/delivery repository. For an active scan branch,
pass `--artifact-repo-mode current_run` explicitly.

Append `--flow-slug <raw-flow-identity>` only when the caller needs an explicit
flow identity distinct from the review name. The default raw flow identity is
the exact `--review-name` value; when `--flow-slug` is present, its exact value
is the raw identity instead. Resolve the stable flow slug as:

```text
readable = slugify(raw_identity)[:64].rstrip("_")
FLOW-SLUG = readable + "_" + sha256_utf8(raw_identity)[:8]
```

`slugify` lowercases the raw identity, replaces each non-alphanumeric run with
`_`, and trims surrounding `_`; an empty readable part uses
`program_set_review`. The hash is calculated from the unmodified raw identity,
so two labels that normalize to the same readable text do not collide.

On Windows use `py -3` and the synced `.agents\skills\...` path. If that
launcher is unavailable, retry once with `python`.

`scripts/prepare_program_set_core_review.py` remains the one-step deterministic
intake adapter when the caller also wants automatic targeted-queue setup. It is
subject to the same readiness and no-formal-review boundary.

The resolver appends the stable, hash-suffixed
`<FLOW-SLUG>--<PROGRAM-SET-SLUG>` exactly once. If the caller already supplies
that resolved bundle path, it must not append it a second time.

Use `--output-dir <program-set-review-parent>` only for an explicit custom
parent. It remains a backward-compatible advanced override and is not changed
to `<parent>/outputs/` automatically.

When the same flow/program-set identity is prepared again, the resolver reuses
its existing bundle directory. A completed formal review is never overwritten:
archive it explicitly before rebuilding that bundle.

For a ready set, deterministic preparation writes:

```text
<project-root>/outputs/<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml       # all semantic mappings initially pending
```

It deliberately does **not** write the formal review. The only legal formal
review path is:

```text
<project-root>/outputs/<folder_slug>/<folder_slug>--sme-core-review.md
```

There is no default `program-set-sme-core-review.md` alias. The folder slug and
review filename are stable for the same normalized program set and distinct
for a different flow or program set.

When readiness is blocked, preparation writes the control/readiness artifacts
needed to explain the block, creates a targeted queue only when recovery is
possible, and writes no formal review. Do not treat a partial source pack as a
synthesis input.

## Missing And Invalid Program Recovery

Missing or semantically invalid programs form a targeted worklist. Never restart
an all-program or whole-repository analysis because one member is not ready.

Run `scripts/create_missing_program_scan_queue.py` against a blocked manifest.
The adapter writes recovery control under:

```text
<bundle>/missing-program-list-batch/
```

After a blocked build, create that queue explicitly:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/create_missing_program_scan_queue.py \
  --manifest <bundle>/program-set-core-input-manifest.yaml \
  --source-root <source-repo-with-fresh-inventory> \
  --delivery-root <program-artifact-working-root> \
  --out-dir <bundle>/missing-program-list-batch
```

On Windows, use `py -3` with the synced `.agents\skills\...` script path.
Alternatively, use `prepare_program_set_core_review.py` as the one-step intake;
it runs the builder, reads the resolved `OUTPUT_DIR`, and invokes this queue
adapter only when the manifest is blocked.

The recovery directory is an actionable handoff, not merely an error list:

```text
missing-program-list-batch/
  recovery-plan.md
  recovery-status.yaml
  program-list.csv                    # only repairable programs
  prompt-queue/                       # Cline serial repair prompts
  blocked-programs.csv                # programs without an approved source mapping
  message-evidence-requests/          # only when message descriptions need evidence
```

`recovery-plan.md` preserves the upstream validator findings and classifies
each program into one or more precise actions: rebuild required artifacts,
repair reader-first structure, resume semantic deep-read, resolve message
evidence, obtain the terminal approval, or refresh only that program. A
message-evidence action requests a catalog, reference/control file, source
literal/comment, runtime evidence, or SME-approved description; it must not
invent a meaning for an observed code.

The one-step intake defaults to `--recovery-runner cline_serial`. To prepare
isolated Kiro workers instead, pass:

```text
--recovery-runner kiro_parallel --recovery-max-parallel-agents <n>
```

That mode forces immediate validation and deterministic scaffold precreation,
then adds `subagent-queue/`, `subagent-results/`,
`subagent-dispatch-plan.md`, and `kiro-parallel-runner-prompt.md` to the same
recovery package. Both runner modes receive the same retained validator
findings and recovery actions.

Only a program with a fresh, exact source mapping enters
`program-list.csv`/`prompt-queue/`. Programs not found by fresh inventory, or
blocked by missing/stale inventory, are written only to
`missing-program-list-batch/blocked-programs.csv` with the
`source_mapping_required` action; never invent a path or create a prompt.
When every program is ready, do not create `missing-program-list-batch/` at all.
After targeted scans/fixes finish, rerun normal preparation from the program
list. If that rerun makes the program set ready, it removes only the
known generated recovery files. It refuses to delete unrecognized analyst or
SME evidence inside `missing-program-list-batch/`; archive that evidence first
instead of relying on a recursive cleanup.
Until all readiness rows pass:

- manifest status remains `blocked_artifact_readiness`;
- coverage cannot become complete; and
- `<folder_slug>--sme-core-review.md` must not exist.

## Approved Artifact Requalification

When the approved document repository contains artifacts created before the
current analyzer contract matured, first run a read-only whole-repository
requalification. This is separate from a flow merge and does not require a
program list. Discovery is constrained by the profile's `module_roots`,
`program_folder_patterns`, and `artifact_file_patterns`; ordinary repository
folders and flow outputs are not scanned.

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/requalify_approved_program_artifacts.py \
  --artifact-root <approved-document-repo-clone> \
  --profile skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml \
  --output-dir <requalification-output>
```

On Windows, use `py -3` with the synced `.agents\skills\...` path. The command
only reads the approved root and writes
`approved-artifact-requalification.yaml` to the separate output directory.
Every discovered program is classified as one of:

- `final_ready`: final program-analyzer contract and reader-first readiness pass;
- `core_reader_ready_pending`: the reader-first surface is usable, but non-core
  sidecars, deep-read batches, message/RLOG evidence, or terminal status remain;
- `format_repairable`: deterministic YAML/hash/serialization repair is needed;
- `semantic_repair_required`: source-backed reader-first or routine analysis
  work is needed; or
- `blocked`: identity, trust, path, or artifact ambiguity prevents safe repair.

The report records findings, stable finding codes, tier, artifact path, source
index/execution-plan hashes, validator status, and repository revision. It is a
measurement of the current approved repository, not an approval override.

Generate a program-level repair queue only after reviewing that report:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/create_approved_artifact_repair_queue.py \
  --report <requalification-output>/approved-artifact-requalification.yaml \
  --out-dir <repair-queue-output>
```

The queue creates exactly one prompt per repairable program. It creates no
prompt for `final_ready` programs and leaves `blocked` rows in
`blocked-programs.csv` until a human resolves the ambiguity. Large programs
remain one repair unit, but their prompt must resume deterministic source
index/deep-read batches in small checkpoints (at most five routines/windows per
checkpoint); it must not rescan the repository or compress a 30,000-line
program into one prompt. Repairs happen in an isolated branch or clone, never
by silently mutating the approved repository.

## LLM Synthesis Procedure

Once preparation reports `ready_for_synthesis`, the LLM executing this skill:

1. Reads the manifest and every readiness row.
2. Reads the entire source pack, including all five sections for every program.
3. Reads normalized facts and pending coverage controls.
4. Groups facts by SME-readable themes across programs while retaining each
   program, routine, carrier, guard, effect/outcome, exact message/status/
   literal/generic-handler token, evidence, and `source_fact_id`.
5. Builds the review rows and stable anchor plan in working memory, including
   anchored program-summary and thematic-overview contributions.
6. Replaces each pending coverage item with exactly one disposition and its
   planned review mapping.
7. Confirms that coverage has zero pending items and that every included or
   merged item has one unique planned anchor. If persistence is necessary before
   this gate, write only an explicitly non-formal
   `<folder_slug>--partial-draft.md`; it must not use final front matter/H1.
8. Writes the single formal review from
   [`templates/sme-core-review.md`](templates/sme-core-review.md) only after the
   zero-pending gate passes, then writes the completed coverage mapping and
   records manifest `review_status: complete_exploratory`,
   `artifact_readiness: ready`, and `merge_coverage: complete`; coverage and
   formal review also record `review_status: complete_exploratory`.
9. Runs the five-way coverage validator and repairs omissions before handoff.

The review must synthesize; it must not concatenate program files. Merging
several source facts into one row is legal only when the row stays lossless and
the coverage item lists every merged `source_fact_id`.

## Coverage Dispositions

Every normalized source fact has one and only one status:

- `included` — represented directly by one anchored review row;
- `merged` — represented losslessly in an anchored row with all merged source
  fact IDs recorded;
- `excluded_non_core` — outside the core review by contract, with a specific
  reason; or
- `pending` — not yet reconciled.

`pending` prohibits the formal review as well as final validation. Material
calculations, validations, exceptions, exact messages/status/literals,
generic-handler tokens, and material routine outcomes may not be excluded
merely to shorten the review. Every `included` or `merged` item must name an
anchor that exists in the review and the review row must list the mapped source
fact IDs.

The final validator reconciles five artifacts:

```text
manifest <-> source pack <-> normalized facts <-> coverage <-> formal review
```

It rejects missing programs, missing source sections, dropped or duplicated
facts, count mismatches, changed exact literals or generic-handler tokens,
unsupported exclusions, pending mappings, missing anchors, stale review
metadata, placeholder/scaffold content, link-only core rows, definitive claims
without evidence, forbidden full-flow sections, and language that converts
navigation order into a confirmed call chain.

The reconciliation is bidirectional and semantic. It re-extracts facts from
the lossless source pack, compares their full IDs/content with normalized
facts, uses token-aware exact matching, requires typed routine/carrier/guard/
effect/evidence values on the same mapped row, verifies one anchor definition
(except a fully declared merged group), and requires identical final coverage
mirrors with `coverage_status: complete`. Overview rows must carry unique
anchors and known source fact refs; untracked call or sequence claims fail.

An evidence-bounded unresolved row or `TBD-*` carried from an allowed
`approved_with_non_blocking_tbd` artifact is not a scaffold placeholder. It
must retain its concrete source, known condition/carrier/outcome, and precise
unresolved point. Blank examples, TODO text, and generic “details unavailable”
rows are placeholders and fail.

## Review Profiles

`standard_reader_first` is the default and keeps Message Inventory in the
primary reading path after Exception Handling.

Its formal review section order is:

1. `## Program Set Reading Summary`
2. `## Cross-Program Processing Overview`
3. `## Calculation Logic`
4. `## Validation Logic`
5. `## Exception Handling`
6. `## Message Inventory`
7. `## Core Completeness Ledger`
8. `## Coverage Reconciliation`
9. `## Sources`
10. `## Run Profile`
11. `## Source Inventory Cache`

`minimal_reader_first` is legal only when the user selects it explicitly. It
may move Message Inventory to an audit section named `Message Coverage
Control`, but it must still preserve every exact message/status/literal, source
fact ID, generic-handler token, carrier/destination, evidence reference, and
review anchor. Minimal means a shorter reading path, not reduced evidence
coverage.

For `minimal_reader_first`, use the same order through Exception Handling,
then Core Completeness Ledger, Coverage Reconciliation, Message Coverage
Control, Sources, Run Profile, and Source Inventory Cache.

Both profiles retain audit/control sections after the core:

- Core Completeness Ledger
- Coverage Reconciliation
- Sources
- Run Profile
- Source Inventory Cache

## Validation And Handoff

Validate the sibling bundle before SME/Dify handoff:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py validate \
  --manifest <bundle>/program-set-core-input-manifest.yaml \
  --review <bundle>/<folder_slug>--sme-core-review.md
```

The validator discovers the sibling source pack, facts, and coverage files; an
operator may also pass explicit paths when supported. A successful handoff
requires all-program readiness, final review metadata, zero pending coverage,
all source-fact anchors present, and no forbidden section.

For an active ready example, see
[`examples/reader-first-merger-ready/README.md`](examples/reader-first-merger-ready/README.md).
For blocked recovery behavior, see
[`examples/reader-first-merger-blocked/README.md`](examples/reader-first-merger-blocked/README.md).

## Runtime Portability

Canonical source is `skills/legacy-ibmi-flow-analyzer/`. Runtime directories
are synced adapters:

- `.codex/skills/legacy-ibmi-flow-analyzer/`
- `.claude/skills/legacy-ibmi-flow-analyzer/`
- `.opencode/skills/legacy-ibmi-flow-analyzer/`
- `.agents/skills/legacy-ibmi-flow-analyzer/`

Do not edit an adapter `SKILL.md` directly. After canonical changes, use
`scripts/sync-skills.sh` and its drift check according to repository policy.
