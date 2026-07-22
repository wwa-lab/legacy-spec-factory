# Reader-First Program Analysis Merger E2E Guideline

This guide tests `legacy-ibmi-flow-analyzer` v0.4.0 in an agent runtime such as
Codex or Claude Code. The active workflow is a controlled, reader-first merge
of finalized program analyses. It is not a transaction-flow reconstruction.

For a limited chat runtime, use
[`flow-analysis-copilot-chat-e2e-guideline.md`](flow-analysis-copilot-chat-e2e-guideline.md).
For an interrupted run, use
[`flow-analysis-resume-guideline.md`](flow-analysis-resume-guideline.md).

## Acceptance Contract

A successful E2E run proves all of the following:

- Each requested program passes the upstream
  `legacy-ibmi-program-analyzer` final validator and the merger readiness gate.
- The semantic primary input is the complete content of these five sections in
  every `<PROGRAM>-program-analysis.md`:
  `## Program Reading Summary`, `## Calculation Logic`,
  `## Validation Logic`, `## Exception Handling`, and
  `## Message Inventory`.
- Deterministic tooling prepares the manifest, readiness ledger, lossless
  source pack, normalized facts, and initially `pending` coverage. It does not
  write a review or call an external LLM.
- The LLM already executing the skill performs semantic cross-program
  synthesis and anchor planning, completes coverage with zero pending items,
  and only then writes exactly one `<folder_slug>--sme-core-review.md`.
- The final validator reconciles the manifest, source pack, normalized facts,
  coverage, and formal review.

The SME program order is navigation evidence only. It must never be described
as a confirmed call chain unless separate source evidence proves that chain.

## Test Inputs

Prepare explicit local paths and values:

```text
Review name: <business-readable name>
Programs file: <one program per line or supported CSV>
Program artifact root: <current-run workspace or approved local document repo>
Output parent: <parent directory for review bundles>
Flow slug: <stable flow/navigation label>
Profile: standard_reader_first | minimal_reader_first
Artifact repo mode: current_run | approved_document_repo
Source root: <optional; required only for targeted recovery>
```

`current_run` is the default. Use `approved_document_repo` only when the user
explicitly requests it and supplies the local approved repository path. Never
silently fall back to a prior run, remote branch, or another analyst's output.

`--output-dir` is a parent directory. The resolver appends
`<flow-slug>--<program-set-slug>` exactly once, even when the caller has already
supplied that resolved bundle path.

## One-Run E2E Prompt

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Goal:
Create one controlled Reader-First Program Analysis Merger review and continue
until readiness, LLM synthesis, coverage reconciliation, and final validation
are complete. Do not stop at a plan, skeleton, manifest, or source pack.

Inputs:
- Review name: <REVIEW_NAME>
- Programs file: <PROGRAMS_FILE>
- Program artifact root: <PROGRAM_ARTIFACT_ROOT>
- Output parent: <OUTPUT_PARENT>
- Flow slug: <FLOW_SLUG>
- Profile: standard_reader_first
- Artifact repo mode: current_run
- Source root, only if targeted recovery is needed: <SOURCE_ROOT>

Rules:
1. Preserve exact program identity and requested navigation order. Do not infer
   a call chain from that order.
2. For every distinct program, run or reuse the upstream final program-analysis
   validator. Early intake uses `core_reader_first_lenient`: require the main
   Markdown, correct identity, and meaningful content in all five reader-first
   H2 sections. Terminal approval, pending deep reads, retained batch/RLOG
   coverage, sidecar drift, and unresolved message descriptions are recorded as
   `pending_findings`; strict final validation still gates the formal review.
3. Treat --output-dir as the output parent. Resolve one
   <flow-slug>--<program-set-slug> folder and append it exactly once.
4. If any program is missing, misidentified, or has a meaningless core
   reader-first section, keep status `blocked_artifact_readiness`. Create only
   a targeted missing/invalid-program queue from fresh inventory paths, record
   unresolved items in `blocked-programs.csv`, and write no formal review. A
   program with useful core sections but non-core pending findings remains
   `ready_for_synthesis` and does not enter the recovery queue.
5. When all programs are ready, run deterministic preparation. It may write the
   manifest, readiness ledger, lossless reader-first source pack, normalized
   core facts with stable source_fact_id values, and pending coverage. It must
   not write a review or invoke an external LLM.
6. Then, as the LLM executing this skill, read the complete source pack and
   normalized facts, synthesize cross-program themes in working memory, and
   plan stable row anchors without losing facts.
7. Map every source_fact_id to exactly one coverage status: included, merged,
   excluded_non_core, or pending. included/merged rows require a planned unique
   review anchor. If any item is pending, write no formal review; an unavoidable
   persisted intermediate must be `<folder_slug>--partial-draft.md` without
   final front matter/H1. After zero pending, write exactly:
   <bundle>/<folder_slug>--sme-core-review.md
8. Use standard_reader_first unless minimal_reader_first was explicitly
   requested. Minimal may move exact messages to Message Coverage Control, but
   it must preserve their facts, evidence, IDs, and anchors.
9. Run the five-way validator across manifest, source pack, normalized facts,
   coverage, and formal review. Repair omissions, changed literals, missing
   anchors, count mismatches, and unsupported exclusions before handoff.
10. Reject active headings named Trigger Inventory, Nodes, Edges, Transaction
    Call Map, Replay, Persistence, Lineage, UI Surfaces, Capability Seeds, or
    SME Checklist.

Report:
- resolved bundle and unique review path
- artifact repo mode and profile
- readiness result for every distinct program
- targeted recovery queue/blockers, if any
- source-pack and normalized-fact counts by program and section
- coverage counts by disposition
- five-way validator result
```

## Ready-Path Checks

For a fully ready input set, the bundle contains:

```text
<output-parent>/<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
  <folder_slug>--sme-core-review.md
```

Verify that the source pack contains all five complete H2 sections for every
program. Verify that every normalized fact has a stable `source_fact_id`, every
`included` or `merged` mapping points to an existing review anchor, and no
`pending` mapping remains.

The review must be thematic and self-contained. It may merge compatible facts
only when the review row and coverage mapping retain every source fact ID,
program, routine/carrier, guard, outcome, exact message/status/literal, and
evidence reference.

## Blocked-Path Checks

Test at least one missing/placeholder-only core program and one non-terminal or
`pending_deep_read` program. Expected behavior:

- the missing/placeholder-only core case remains `blocked_artifact_readiness`;
- the non-terminal/pending-deep-read case is `ready_for_synthesis` with exact
  `pending_findings` in the readiness ledger;
- only the blocked case enters `missing-program-list-batch/`;
- queue entries use exact paths from fresh source inventory;
- programs without a verified path appear in `blocked-programs.csv`;
- no whole-repository work queue is created; and
- no `<folder_slug>--sme-core-review.md` exists.

After the targeted artifacts are finalized, rerun preparation from the same
program list. Do not hand-edit readiness to force synthesis.

## Profile Checks

`standard_reader_first` is the default. It keeps Message Inventory in the
primary SME reading path.

`minimal_reader_first` is an explicit opt-in. It may use `Message Coverage
Control` as an audit section, but exact messages, statuses, literals,
`source_fact_id` values, evidence references, and review anchors remain fully
covered. A minimal profile may shorten presentation, never evidence.

## Common Failures

- Treating file existence as final artifact readiness.
- Reading compact sidecars instead of the five complete reader-first sections.
- Letting a deterministic script write a skeleton or synthetic review.
- Calling an external LLM instead of using the LLM executing the skill.
- Writing a generic `program-set-sme-core-review.md` alias.
- Appending `<folder_slug>` twice below the output parent.
- Falling back from `current_run` to older artifacts without explicit approval.
- Producing a partial review while a targeted recovery queue is open.
- Leaving `pending` coverage, missing anchors, or dropped exact messages.
- Presenting the SME program list as a proven execution/call sequence.
- Reintroducing forbidden full-flow headings.
