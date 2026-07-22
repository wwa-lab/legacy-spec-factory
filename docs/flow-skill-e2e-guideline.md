# Reader-First Program Analysis Merger E2E Guideline

Use this guide when an SME provides a set/list of IBM i programs and expects
one evidence-complete SME/Dify review of their finalized program analyses.
Despite the historical skill name, the active `legacy-ibmi-flow-analyzer` is a
controlled **Program Analysis Merger**, not a transaction-flow reconstructor.

## Outcome

The workflow produces one stable bundle:

```text
<program-set-review-parent>/<FLOW-SLUG>--<PROGRAM-SET-SLUG>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
  <FLOW-SLUG>--<PROGRAM-SET-SLUG>--sme-core-review.md
```

The final Markdown appears only after all programs are ready and after the LLM
executing the skill performs thematic synthesis. There is no generic
`program-set-sme-core-review.md` alias.

## What The SME Provides

```text
Review name: <business-readable name>
Programs file: <path>
Program artifact root: <approved local clone by default or current-run root when explicitly selected>
Output parent: <program-set review parent>
Artifact repo mode: approved_document_repo
Profile: standard_reader_first
Source root: <optional; targeted recovery only>
```

Preserve exact program identity and meaningful prefixes such as `@`. The list
order is navigation evidence; it is not a source-confirmed execution order or
call chain.

## Evidence Modes

`approved_document_repo` is the default. It resolves only under the supplied
local clone of the approved document/delivery repo. The team's repo contains
only SME-reviewed analyses, so the manifest records this mode and each reused
program as `reused_artifact_repo`.

`current_run` is explicit opt-in for a supplied active working artifact root.
It must not silently reuse remote main, an arbitrary prior run, or another
analyst's output.

## E2E Procedure

### 1. Normalize And Resolve

Normalize programs using the delivery profile while preserving SME order.
Resolve each distinct normalized program once. A repeated program in the same
request may use `reused_same_run`.

### 2. Run Program Artifact Readiness

For every distinct program, invoke or reuse the final validator from
`legacy-ibmi-program-analyzer`. A directory is ready only when:

- the upstream validator passes;
- terminal analysis status is approved or approved with only non-blocking TBDs;
- Program Reading Summary, Calculation Logic, Validation Logic, Exception
  Handling, and Message Inventory are complete and non-placeholder;
- no pending deep read or non-terminal retained batch remains;
- RLOG/main/sidecar coverage agrees; and
- blocking or unresolved message descriptions are closed.

Any failure sets the program set to `blocked_artifact_readiness`. Do not create
a partial formal review.

### 3. Prepare Deterministic Inputs

Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py build
  --review-name "credit check"
  --programs-file C:\work\programs.txt
  --working-root C:\work\legacy-modernization-delivery
  --profile C:\work\delivery-profile.yaml
  --working-branch develop-leo
  --flow-slug credit-check
  --output-dir C:\work\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py build \
  --review-name "credit check" \
  --programs-file /work/programs.txt \
  --working-root /work/legacy-modernization-delivery \
  --profile /work/delivery-profile.yaml \
  --working-branch develop-leo \
  --flow-slug credit-check \
  --output-dir /work/legacy-modernization-delivery/modules/CAP-ID-0004-program_set_reviews
```

`--output-dir` is the parent. The resolver appends the flow/program-set slug
exactly once, including when a rerun is passed the already resolved path.

The deterministic phase validates and prepares the lossless source pack,
normalized stable source facts, and all-`pending` coverage. It does not write a
review skeleton, produce semantic prose, or call an external LLM.

### 4. Recover Only Missing/Invalid Programs

If readiness is blocked, use a fresh source inventory to create a targeted
queue for the affected programs only. Do not restart a whole-repository scan.
Programs absent from fresh inventory, or blocked by stale/missing inventory,
go to `blocked-programs.csv` with no guessed path.

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/create_missing_program_scan_queue.py \
  --manifest <bundle>/program-set-core-input-manifest.yaml \
  --source-root <source-repo-with-fresh-inventory> \
  --delivery-root <program-artifact-working-root> \
  --out-dir <bundle>/missing-program-list-batch
```

The `build` subcommand itself does not create this queue. The one-step
`prepare_program_set_core_review.py` intake runs build and then invokes the
queue adapter when the resolved manifest is blocked.

After each targeted program is finalized, rerun preparation from the original
program list. The formal review must remain absent until the entire manifest is
`ready_for_synthesis`.

### 5. Synthesize With The Executing Skill LLM

The LLM executing `legacy-ibmi-flow-analyzer` must read:

1. the manifest and readiness ledger;
2. the whole source pack, containing all five complete reader-first sections
   for every program;
3. normalized facts; and
4. pending coverage.

It plans one cross-program thematic review in working memory using
`skills/legacy-ibmi-flow-analyzer/templates/sme-core-review.md`. Each material
row retains program, routine, carrier, guard, effect/outcome, evidence, a
stable review anchor, and all mapped `source_fact_id` values. It completes the
anchor/coverage plan before writing the formal file.

Coverage dispositions are `included`, `merged`, `excluded_non_core`, or
`pending`. Any `pending` item prohibits the formal review. Material
calculations, validations, exceptions, exact messages/status/literals/generic-
handler tokens, and material routine outcomes cannot be excluded for brevity.
After zero pending, the LLM writes exactly
`<folder_slug>--sme-core-review.md`. A persisted intermediate, if unavoidable,
must be named `<folder_slug>--partial-draft.md` and is not a deliverable.

`standard_reader_first` includes Message Inventory in the primary reading
path. `minimal_reader_first` is explicit opt-in and moves the complete message
surface to `Message Coverage Control`; evidence coverage is unchanged.

### 6. Validate Five-Way Reconciliation

Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py validate
  --manifest C:\work\...\<folder_slug>\program-set-core-input-manifest.yaml
  --review C:\work\...\<folder_slug>\<folder_slug>--sme-core-review.md
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py validate \
  --manifest /work/.../<folder_slug>/program-set-core-input-manifest.yaml \
  --review /work/.../<folder_slug>/<folder_slug>--sme-core-review.md
```

The validator reconciles manifest, source pack, normalized facts, coverage,
and final review. It must reject missing programs or sections, dropped or
duplicated facts, count mismatches, changed exact messages, pending or
unsupported exclusions, missing anchors, review identity mismatches,
program-order call-chain claims, and forbidden full-flow sections.

### 7. Hand Off

Hand the review to SME/Dify only after validation returns zero findings. Include
the bundle path, program list, evidence mode, readiness result, coverage counts,
and validator result in the delivery/PR summary.

## Pass Criteria

- Every distinct program passes upstream and merger readiness.
- All five primary sections per program are preserved in the source pack.
- The deterministic phase writes no formal review.
- The executing skill LLM writes exactly one uniquely named review.
- Every normalized fact has exactly one final coverage disposition.
- Every included/merged fact points to an existing anchored review row.
- Exact messages/statuses/literals and per-program counts are preserved.
- SME list order is never presented as a confirmed call chain.
- No Trigger Inventory, Nodes, Edges, Transaction Call Map, Replay,
  Persistence, Lineage, UI Surfaces, Capability Seeds, or SME Checklist section
  appears.
- The five-way validator passes.

## Active Examples

- [Ready merge](../skills/legacy-ibmi-flow-analyzer/examples/reader-first-merger-ready/README.md)
- [Blocked targeted recovery](../skills/legacy-ibmi-flow-analyzer/examples/reader-first-merger-blocked/README.md)

Historical transaction-flow diagrams and examples in the repository are
non-active provenance artifacts and do not define this workflow.
