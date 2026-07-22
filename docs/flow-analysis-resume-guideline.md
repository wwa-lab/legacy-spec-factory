# Reader-First Program Analysis Merger Resume Guideline

Use this guide when a v0.4.0 `legacy-ibmi-flow-analyzer` run is interrupted.
Resume from durable bundle and per-program artifacts, never from chat memory.

## Durable State

Inspect these files in order when they exist:

```text
<output-parent>/<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
  <folder_slug>--sme-core-review.md
  missing-program-list-batch/
    blocked-programs.csv
```

Also inspect each manifest-listed `<PROGRAM>-program-analysis.md` and its
upstream final-validation artifacts. The semantic primary input is the complete
content of `## Program Reading Summary`, `## Calculation Logic`,
`## Validation Logic`, `## Exception Handling`, and `## Message Inventory`.
Sidecars support readiness and normalization; they do not replace those five
sections.

## Resume Rules

- Preserve the manifest's exact program identities and navigation order. Order
  does not prove a call chain.
- Preserve the selected artifact repository mode. `approved_document_repo` is
  the default; resume from `current_run` only when it was explicitly selected.
- Rerun the upstream program final validator and readiness checks for any
  missing, changed, ambiguous, placeholder, pending-deep-read, non-terminal, or
  otherwise invalid artifact. File existence alone is not readiness.
- When any program is not ready, keep `blocked_artifact_readiness`, regenerate
  only its targeted queue from fresh inventory paths, update
  `blocked-programs.csv` for unresolved paths, and ensure no formal review
  exists. Do not launch a whole-repository scan or all-program rerun.
- Treat `--output-dir` as the parent. Reuse the already resolved
  `<flow-slug>--<program-set-slug>` bundle without appending it again.
- Deterministic preparation may recreate the source pack, normalized facts,
  and initially `pending` coverage after all programs pass. It must never write
  the review or invoke an external LLM.
- The LLM executing the skill resumes synthesis only from a complete prepared
  bundle, completes the anchor/coverage plan with zero pending facts, and only
  then writes exactly `<folder_slug>--sme-core-review.md`.
- Every `source_fact_id` must end as `included`, `merged`, or a justified
  `excluded_non_core`; `pending` blocks handoff. Included and merged facts must
  point to anchors that exist in the review.
- Run the five-way validator across manifest, source pack, normalized facts,
  coverage, and review after any resumed synthesis.

The default profile is `standard_reader_first`. Resume
`minimal_reader_first` only when it was explicitly selected; its `Message
Coverage Control` audit section must still retain every exact message/status/
literal, source fact ID, evidence reference, and anchor.

The formal review must not contain active full-flow headings: Trigger
Inventory, Nodes, Edges, Transaction Call Map, Replay, Persistence, Lineage,
UI Surfaces, Capability Seeds, or SME Checklist.

## Resume Decision Table

| Last durable state | Resume action |
| --- | --- |
| A requested program is missing or fails readiness | Repair or rescan only that program, then rerun readiness. Do not write a review. |
| All readiness rows pass, but source pack/facts/coverage are absent or stale | Rerun deterministic preparation in the existing bundle. |
| Coverage is all `pending` and review is absent | The executing skill LLM reads the full prepared bundle and starts synthesis. |
| Explicit `<folder_slug>--partial-draft.md` exists and coverage is partly mapped | Continue the in-memory/draft anchor plan from the first pending source fact; do not create the formal filename yet. |
| Review and coverage are complete but validation failed | Repair the named five-way mismatch and rerun validation. |
| Five-way validation passed | Handoff is complete; do not regenerate artifacts without a new request or changed evidence. |

If a formal review exists while readiness is blocked or coverage is pending,
quarantine it from the active bundle or remove it through the repository's
recoverable workflow. It is not a valid partial deliverable.

## Resume Prompt

```text
Use legacy-ibmi-flow-analyzer v0.4.0 and resume from durable files.

Inputs:
- Existing bundle: <BUNDLE_PATH>
- Program artifact root: <PROGRAM_ARTIFACT_ROOT>
- Artifact repo mode: current_run | approved_document_repo
- Source root, only for targeted recovery: <SOURCE_ROOT>

Read program-list, manifest, readiness, source pack, facts, coverage, review,
and each manifest-listed program analysis. Preserve the existing folder_slug;
do not append it to the output path again.

Resume from the first incomplete gate:
1. upstream final readiness for every program and all five complete
   reader-first H2 sections;
2. targeted missing/invalid-program recovery only;
3. deterministic source-pack/fact/pending-coverage preparation, with no review
   generation and no external LLM call;
4. semantic synthesis and anchor planning by the LLM executing this skill;
5. per-source_fact_id coverage reconciliation using included, merged,
   excluded_non_core, or pending; if zero pending, write exactly
   <folder_slug>--sme-core-review.md, otherwise keep only an explicit
   <folder_slug>--partial-draft.md;
6. five-way validation of manifest, source pack, facts, coverage, and review.

Use standard_reader_first unless minimal_reader_first was explicitly selected.
Treat program order as navigation only, not a confirmed call chain. Reject
Trigger Inventory, Nodes, Edges, Transaction Call Map, Replay, Persistence,
Lineage, UI Surfaces, Capability Seeds, and SME Checklist headings.

Report the resumed gate, repaired programs, bundle/review paths, remaining
pending facts or blockers, and final validator result.
```

## Before Another Interruption

Stop only at a durable boundary. Ensure the manifest/readiness files reflect
the current gate, the targeted queue reflects only unresolved programs, and
coverage persists every completed mapping. Do not create a review skeleton as
a checkpoint; the source pack, normalized facts, and coverage file are the
handoff surface for the next executing-skill LLM session.
