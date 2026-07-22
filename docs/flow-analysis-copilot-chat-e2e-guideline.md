# Reader-First Merger E2E Guideline For Copilot Chat

Use this v0.4.0 guide for GitHub Copilot Chat or another limited chat UI. Split
the work at durable artifact boundaries:

1. preflight and readiness
2. one fresh chat for each targeted program repair, when needed
3. deterministic bundle preparation
4. one synthesis chat executed under `legacy-ibmi-flow-analyzer`
5. one coverage-validation chat

The workflow produces a controlled SME core review, not a reconstructed
transaction flow.

## Shared Inputs

```text
Review name: <business-readable name>
Programs in SME navigation order: PROGRAM_A, PROGRAM_B, PROGRAM_C
Program artifact root: <current-run workspace or approved local document repo>
Output parent: <parent directory for review bundles>
Flow slug: <stable flow/navigation label>
Profile: standard_reader_first | minimal_reader_first
Artifact repo mode: current_run | approved_document_repo
Source root: <optional; targeted recovery only>
```

Use `approved_document_repo` by default. `current_run` is valid only when the
user explicitly chooses it for an active delivery workspace.
Never import evidence from chat history, an arbitrary prior run, remote main,
or another analyst's workspace.

`--output-dir` is a parent. The builder appends
`<flow-slug>--<program-set-slug>` exactly once; subsequent chats must reuse that
resolved bundle path without nesting it again.

## Phase 1: Preflight And Final Readiness

Use one chat to resolve exact program identities and run the readiness gate.

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Prepare readiness for this program set. Preserve the SME list as navigation
order only; do not infer a call chain.

Inputs:
- Review name: <REVIEW_NAME>
- Programs in SME navigation order: PROGRAM_A, PROGRAM_B, PROGRAM_C
- Program artifact root: <PROGRAM_ARTIFACT_ROOT>
- Output parent: <OUTPUT_PARENT>
- Flow slug: <FLOW_SLUG>
- Profile: standard_reader_first
- Artifact repo mode: approved_document_repo
- Source root, if targeted recovery is required: <SOURCE_ROOT>

For every distinct program, run or reuse the legacy-ibmi-program-analyzer final
validator. Require terminal approval and the complete content of these five H2
sections in <PROGRAM>-program-analysis.md:
- ## Program Reading Summary
- ## Calculation Logic
- ## Validation Logic
- ## Exception Handling
- ## Message Inventory

Reject placeholders, pending_deep_read, incomplete/non-terminal retained
batches, missing required RLOG coverage, unresolved blocking facts, and
unresolved required message descriptions. File existence is not readiness.

If any program is missing or invalid, leave blocked_artifact_readiness, create
only its targeted queue from fresh inventory paths, put unresolved paths in
blocked-programs.csv, and write no formal review. Do not queue or scan the whole
repository.

Generate `program-list.txt` from the inline navigation order; do not ask for a
separate Programs file path. Return the resolved bundle, readiness result per program, targeted queue files,
blocked-programs.csv rows, and the exact next program-repair chat.
```

If all programs are ready, skip Phase 2.

## Phase 2: Repair One Program Per Fresh Chat

Open one new chat for each program in the targeted queue. Do not carry source
or conclusions between chats.

```text
Use legacy-ibmi-program-analyzer.

Finalize exactly one queued program analysis:
- Program: <PROGRAM>
- Verified source path: <SOURCE_PATH_FROM_FRESH_INVENTORY>
- Output artifact directory: <PROGRAM_ARTIFACT_DIR>

Produce and validate a terminal reader-first program analysis. Its
program-analysis.md must contain complete Program Reading Summary, Calculation
Logic, Validation Logic, Exception Handling, and Message Inventory H2 sections.
Complete all required RLOG/deep-read batches and resolve blocking message
descriptions. Do not analyze any other program.

Return the upstream final-validator result and terminal analysis status.
```

After all targeted repairs finish, rerun Phase 1. Do not bypass or manually
edit the readiness gate. A blocked set has no legal formal review.

## Phase 3: Deterministic Bundle Preparation

Use one chat after every readiness row is `ready`.

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Run deterministic preparation for the ready program set in the already
resolved <folder_slug> bundle. Preserve the full five reader-first H2 sections
for every program in program-set-reader-first-source-pack.md. Normalize facts
with stable source_fact_id values and initialize every semantic coverage item
as pending.

The deterministic script may write only:
- program-list.txt
- program-set-core-input-manifest.yaml
- program-set-artifact-readiness.yaml
- program-set-reader-first-source-pack.md
- program-set-core-facts.yaml
- program-set-core-coverage.yaml

It must not write a review or skeleton, must not perform semantic synthesis,
and must not call an external LLM.

Return artifact paths plus program/section/source-fact counts. Stop if readiness
changed or any five-section input is incomplete.
```

Expected bundle path:

```text
<output-parent>/<flow-slug>--<program-set-slug>/
```

## Phase 4: Executing-Skill LLM Synthesis

Open a fresh chat and supply access to the complete prepared bundle. This
Copilot Chat session is the LLM executing the skill; it plans synthesis and
coverage first and is the only component that may write the formal review after
the zero-pending gate.

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Act as the executing skill LLM. Read the complete manifest, readiness ledger,
reader-first source pack, normalized facts, and pending coverage file in:
<BUNDLE_PATH>

Synthesize one thematic, self-contained SME/Dify review in working memory.
Preserve every
material calculation, validation, exception, routine outcome, exact message/
status/literal, evidence reference, program identity, and source_fact_id. Do
not merely concatenate program documents.

For each source_fact_id, set exactly one coverage disposition: included,
merged, excluded_non_core, or pending. included and merged require a planned
unique review anchor; merged rows must list every merged source fact ID. Use
excluded_non_core only with a specific contract reason. If anything remains
pending, do not write the formal review. If an intermediate file is unavoidable,
write only <folder_slug>--partial-draft.md without final front matter/H1.

After coverage has zero pending items, write exactly:
<BUNDLE_PATH>/<folder_slug>--sme-core-review.md

Do not create program-set-sme-core-review.md or another alias.

Use standard_reader_first unless minimal_reader_first was explicitly selected.
Minimal may move messages to Message Coverage Control, but every exact message,
status, literal, fact ID, evidence reference, and anchor remains required.

Treat program order only as navigation. Do not state or imply a confirmed call
chain without independent source evidence. Do not use active headings named
Trigger Inventory, Nodes, Edges, Transaction Call Map, Replay, Persistence,
Lineage, UI Surfaces, Capability Seeds, or SME Checklist.

Return the formal review path only when zero pending; otherwise return the
partial-draft path and pending items. Do not claim completion until the next
phase passes.
```

## Phase 5: Five-Way Coverage Validation

Use a final chat to validate and repair the bundle.

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Validate this completed bundle:
<BUNDLE_PATH>

Run the five-way reconciliation:
manifest <-> source pack <-> normalized facts <-> coverage <-> formal review

Fail and repair any missing program/section/fact, duplicate or changed exact
literal, count mismatch, unsupported exclusion, pending item, missing review
anchor, stale metadata, inferred call chain, or forbidden full-flow heading.

A pass requires every source_fact_id to be included, losslessly merged, or
specifically excluded_non_core; zero pending mappings; and every included or
merged anchor to exist in <folder_slug>--sme-core-review.md.

Return the validator result, unique review path, fact and coverage counts, and
remaining blockers. Do not prepare SME/Dify handoff on failure.
```

## Expected Evidence

| Check | Expected result |
| --- | --- |
| Reader-first input | Every program contributes all five complete H2 sections from `program-analysis.md`. |
| Upstream gate | Every distinct program passes final validation and merger readiness. |
| Deterministic boundary | Preparation creates source pack, facts, and pending coverage but no review and makes no external LLM call. |
| Unique placement | The parent receives one `<folder_slug>` child exactly once and one `<folder_slug>--sme-core-review.md`. |
| Repository mode | `approved_document_repo` is default; current-run use is explicit. |
| Blocked behavior | Only affected programs are queued; no review exists while blocked. |
| Coverage | Every stable `source_fact_id` has one legal disposition and required anchor. |
| Profiles | Standard is default; explicit minimal retains message audit coverage. |
| Navigation safety | Program order is never promoted to a call chain. |
| Final gate | Five-way validation passes with zero pending facts and no forbidden headings. |

## Resume Rule

When a Copilot Chat session stops, start a new chat and read the durable bundle
files first. Continue from the earliest incomplete phase. Never use a review
skeleton as a checkpoint and never infer completion from chat history. See
[`flow-analysis-resume-guideline.md`](flow-analysis-resume-guideline.md) for the
full decision table.
