# New Team Reader-First Merger Quickstart

Use this quickstart to adopt the source-repo plus delivery-repo workflow for
program analysis and controlled program-set SME reviews. The active
`legacy-ibmi-flow-analyzer` merges finalized program analyses; it does not
reconstruct an end-to-end transaction flow.

## 1. Establish The Two Repositories

```text
source repo    = read-only IBM i source evidence and fresh inventory
delivery repo  = finalized per-program analyses and program-set review bundles
```

Use a working branch for current-run analysis. Do not write directly to main.

## 2. Configure The Delivery Profile

Copy:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Set the team's program folder patterns, name normalization, program tier roots,
program-set review parent, source inventory cache, and allowed working branch
patterns. Keep these v0.4.0 controls intact:

- `approved_document_repo` as default artifact mode because the delivery repo
  contains only SME-reviewed analyses;
- explicit `current_run` opt-in only for active scan branches;
- all five program-analysis reader-first sections required;
- upstream program final validator reused;
- output directory interpreted as a parent;
- one stable `<FLOW-SLUG>--<PROGRAM-SET-SLUG>` bundle;
- one `<folder_slug>--sme-core-review.md` final file; and
- included/merged/excluded_non_core/pending fact coverage.

## 3. Finalize Per-Program Analyses

Run `legacy-ibmi-program-analyzer` for each distinct requested program. The
final `<PROGRAM>-program-analysis.md` must provide complete:

1. Program Reading Summary
2. Calculation Logic
3. Validation Logic
4. Exception Handling
5. Message Inventory

The upstream validator must pass. A program remains not ready when it contains
placeholders, pending deep reads, non-terminal retained batches, missing RLOG
coverage, sidecar mismatches, or unresolved blocking message descriptions.

## 4. Ask The SME For A Program Set

```text
Review name: <business-readable name>
Programs in navigation order:
- <PROGRAM-1>
- <PROGRAM-2>
- <PROGRAM-3>
Program artifact root: <local approved document/delivery repo clone>
Artifact repo mode: approved_document_repo
Output parent: <program_set_review_parent>
Optional source root: <needed only for targeted recovery>
```

The list order helps reading; it does not prove execution order or a call
chain.

## 5. Run Deterministic Preparation

The builder resolves every distinct program, runs readiness validation, and—
when all are ready—writes the lossless source pack, normalized source facts,
and pending coverage into one bundle. It must not write the formal review or
call any external LLM.

Example on macOS/Linux:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py build \
  --review-name "credit check" \
  --program PROGRAM_A --program PROGRAM_B --program PROGRAM_C \
  --working-root /work/delivery \
  --profile /work/delivery-profile.yaml \
  --working-branch develop-leo \
  --flow-slug credit-check \
  --output-dir /work/delivery/modules/CAP-ID-0004-program_set_reviews
```

Use `py -3` and the synced `.agents\skills\...` path on Windows. The output
parent must contain one child bundle; passing that child on a rerun must not
create a duplicate nested slug.

## 6. Recover A Blocked Set

If any program is missing or invalid, the program-set status is
`blocked_artifact_readiness` and there is no formal review. Use fresh repo
inventory to queue only affected programs. Never rerun the entire repository
because one member is blocked. Programs with no inventory match go to
`blocked-programs.csv`; do not guess their source paths.

Rerun preparation after those program analyses pass their upstream validator.

## 7. Let The Executing Skill LLM Synthesize

At `ready_for_synthesis`, the LLM executing the skill reads the complete source
pack and plans an SME-readable thematic merge. Every material review row has a
stable anchor and `source_fact_id` references. It completes coverage as
included, merged, or justified excluded_non_core. Only after no pending facts
remain does it write the uniquely named formal review. An optional persisted
intermediate must be explicitly named `--partial-draft.md` and is not a formal
deliverable.

The default `standard_reader_first` profile keeps exact messages in the primary
reading path. `minimal_reader_first` is explicit and moves, but never drops,
message coverage.

## 8. Validate And Hand Off

Run the merger validator against the manifest and uniquely named review. It
reconciles manifest, source pack, facts, coverage, and formal review. Hand off
to SME/Dify only after it reports zero findings.

Expected ready result:

```text
modules/CAP-ID-0004-program_set_reviews/
  <FLOW-SLUG>--<PROGRAM-SET-SLUG>/
    program-list.txt
    program-set-core-input-manifest.yaml
    program-set-artifact-readiness.yaml
    program-set-reader-first-source-pack.md
    program-set-core-facts.yaml
    program-set-core-coverage.yaml
    <FLOW-SLUG>--<PROGRAM-SET-SLUG>--sme-core-review.md
```

## Common Mistakes

- Treating file existence as upstream readiness.
- Reading compact sidecars instead of the five complete primary sections.
- Allowing the deterministic builder to emit a review skeleton.
- Passing a resolved bundle as output parent and appending the slug twice.
- Reusing historical artifacts without explicit approved-document mode.
- Writing a partial review while one program is blocked.
- Rescanning the entire repo instead of a targeted missing/invalid queue.
- Omitting an exact message or fact to make the review shorter.
- Calling the SME list a source-confirmed call chain.
- Reintroducing full-flow sections into the core review.

For the complete procedure, see
[`flow-skill-e2e-guideline.md`](flow-skill-e2e-guideline.md).
