# Delivery Profile Quickstart

Use this guide to configure where finalized program analyses are resolved and
where controlled reader-first program-set review bundles are written.

## Two Repositories, Two Evidence Modes

The source repository is read-only evidence and inventory. The delivery
repository contains finalized per-program analyses and SME review bundles.

- `current_run` (default) resolves only from the supplied working artifact
  root. No remote-main or arbitrary prior-run fallback is allowed.
- `approved_document_repo` is explicit opt-in and resolves only from the
  supplied local approved document/delivery clone.

## Start From The Canonical Profile

Copy:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Edit team-owned values once:

```yaml
program_artifact_resolution_profile:
  repo: <ORG>/<DELIVERY-REPO>
  program_folder_patterns:
    - modules/*/{PROGRAM}
  program_name_normalization:
    case: upper
    preserve_prefixes: ["@"]
    exact_folder_name_match: true

delivery_workspace_profile:
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
  allowed_branch_patterns:
    - develop-*
  create_from: origin/main
  write_to_main: false
  program_set_review_parent: modules/CAP-ID-0004-program_set_reviews
  program_set_review_path_pattern: "{FLOW_SLUG}--{PROGRAM_SET_SLUG}"
  program_tier_roots:
    large_extreme_program: modules/CAP-ID-0001-large_extreme_program
    complex_normal_program: modules/CAP-ID-0002-complex_normal_program
    normal_program: modules/CAP-ID-0003-normal_program

source_inventory_profile:
  default_cache_dir: outputs/repo-scan
  freshness_policy: clean_git_head_must_match
```

Keep the merger controls that require the upstream program final validator,
all five reader-first main sections, a unique final filename, no deterministic
review generation, and complete fact coverage.

## Per-Run Inputs

```text
Working branch: develop-leo
Review name: credit check
Programs file: /path/to/programs.txt
Program artifact root: /path/to/delivery-working-checkout
Output parent: /path/to/delivery/modules/CAP-ID-0004-program_set_reviews
Artifact repo mode: current_run
Profile: standard_reader_first
Optional source root: /path/to/source-repo
```

The source root is used only to locate affected programs for targeted recovery.
It does not authorize a whole-repository rescan.

## Build The Preparation Bundle

On Windows:

```text
py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py build
  --review-name "credit check"
  --programs-file C:\work\programs.txt
  --working-root C:\work\delivery
  --profile C:\work\delivery-profile.yaml
  --working-branch develop-leo
  --flow-slug credit-check
  --output-dir C:\work\delivery\modules\CAP-ID-0004-program_set_reviews
```

On macOS/Linux:

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py build \
  --review-name "credit check" \
  --programs-file /work/programs.txt \
  --working-root /work/delivery \
  --profile /work/delivery-profile.yaml \
  --working-branch develop-leo \
  --flow-slug credit-check \
  --output-dir /work/delivery/modules/CAP-ID-0004-program_set_reviews
```

`--output-dir` is a parent. The builder appends
`<FLOW-SLUG>--<PROGRAM-SET-SLUG>` exactly once. A rerun passed that resolved
path must reuse it, not create a nested duplicate.

When every program passes readiness, deterministic output is:

```text
<folder_slug>/
  program-list.txt
  program-set-core-input-manifest.yaml
  program-set-artifact-readiness.yaml
  program-set-reader-first-source-pack.md
  program-set-core-facts.yaml
  program-set-core-coverage.yaml
```

The builder does not write a review skeleton. The LLM executing the skill reads
the full source pack, performs thematic synthesis and anchor planning, and
completes fact coverage. Only after coverage has zero pending items does it
write the formal file:

```text
<folder_slug>/<folder_slug>--sme-core-review.md
```

## Readiness And Recovery

File existence is insufficient. Every program must pass the upstream final
validator and have terminal, non-placeholder, fully synchronized reader-first
content. Pending deep reads, non-terminal batches, missing RLOGs, and unresolved
blocking messages set `blocked_artifact_readiness` and prohibit a formal review.

With a fresh source inventory, queue only affected programs. Put programs that
cannot be mapped in `blocked-programs.csv` without inventing source paths. Rerun
the normal builder after recovery.

## Profiles

`standard_reader_first` is the default and includes Message Inventory in the
primary reading path. `minimal_reader_first` is explicit opt-in and moves all
exact message facts to `Message Coverage Control`; it does not reduce coverage.

## Validate Before Handoff

```bash
python3 skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py validate \
  --manifest <bundle>/program-set-core-input-manifest.yaml \
  --review <bundle>/<folder_slug>--sme-core-review.md
```

Validation reconciles manifest, source pack, facts, coverage, and review. It
must pass before SME/Dify handoff.

## Invariants

- `@CU118` and `CU118` remain distinct unless explicit aliases exist.
- Program order is SME navigation, not confirmed execution order.
- The complete main `program-analysis.md` reader-first sections are semantic
  primary input; compact sidecars validate and reconcile them.
- Every source fact has one final included/merged/excluded_non_core disposition;
  no pending fact is deliverable.
- No generic review alias or partial review is created.
- No full transaction-flow section appears in the formal core review.

See [the E2E guideline](flow-skill-e2e-guideline.md) for the complete workflow.
