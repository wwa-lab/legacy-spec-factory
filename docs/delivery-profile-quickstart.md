# Delivery Profile Quickstart

Use this guide when a team wants to scan source code from one repo and store
reviewed scan artifacts in a separate delivery repo.

For a full new-team onboarding path, see
[`new-team-flow-scan-quickstart.md`](new-team-flow-scan-quickstart.md). For a
single or batched SME program-flow run, see
[`flow-skill-e2e-guideline.md`](flow-skill-e2e-guideline.md).

## Two Repos

Use the source repo as the read-only code evidence source.

Use the delivery repo for generated analysis artifacts, SME reviews, PR review,
and durable history. For the default program-flow workflow, do not use
remote-main or prior-run artifacts as completion evidence. The current run
creates its own program artifacts on the delivery working branch.

## One Profile

Start from:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Edit these team-owned values once:

```yaml
program_artifact_resolution_profile:
  repo: CH-WPS-LENDING-CARDS/legacy-modernization-delivery
  program_folder_patterns:
    - modules/*/{PROGRAM}
  program_name_normalization:
    case: upper
    preserve_prefixes:
      - "@"
    exact_folder_name_match: true

delivery_workspace_profile:
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
  allowed_branch_patterns:
    - develop-*
  create_from: origin/main
  write_to_main: false
  program_set_review_parent: modules/CAP-ID-0004-program_set_reviews
  program_tier_roots:
    large_extreme_program: modules/CAP-ID-0001-large_extreme_program
    complex_normal_program: modules/CAP-ID-0002-complex_normal_program
    normal_program: modules/CAP-ID-0003-normal_program

source_inventory_profile:
  default_cache_dir: outputs/repo-scan
  program_list_filename: program-list.csv
  scan_summary_filename: scan-summary.yaml
  freshness_policy: clean_git_head_must_match
```

`program_artifact_resolution_profile` controls program folder/name resolution
inside the current-run artifact root. It is not a remote-main lookup step.

If the same profile is also used by older single-program analyzer workflows
that still perform central preflight, keep their
`delivery_artifact_lookup_profile` section in the team config. The program-flow
builder prefers `program_artifact_resolution_profile` and falls back only for
folder/name compatibility.

## Runtime Inputs

The SME or engineer should provide only the work-specific values:

```text
Delivery working branch: develop-leo
Review name: card auth posting core review
Source repo: /path/to/source-repo
Programs:
- @CU118
- CU257F
- CC050
```

The tool may create `develop-leo` from `origin/main` if it does not exist.
New outputs are written to `develop-leo`, never directly to `main`.

## Build Program-Set Review Inputs

The field deployment environment is Windows. Use `py -3` there. Use
`python3` only on macOS/Linux development machines.

Create a program list file:

```text
@CU118
CU257F
CC050
```

Then build the deterministic manifest and review skeleton on Windows after the
current-run program artifacts exist or have precise pending/blocked states:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-flow-analyzer\scripts\invoke-windows-tool.ps1 BuildProgramSetCoreReview `
  --review-name "card auth posting core review" `
  --programs-file programs.txt `
  --working-root C:\path\to\legacy-modernization-delivery `
  --source-root C:\path\to\source-repo `
  --profile C:\path\to\delivery-profile.yaml `
  --working-branch develop-leo `
  --program-first `
  --output-dir C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews\card_auth_posting_core_review
```

macOS/Linux:

```bash
python3 scripts/build-program-set-core-review.py \
  --review-name "card auth posting core review" \
  --programs-file programs.txt \
  --working-root /path/to/legacy-modernization-delivery \
  --source-root /path/to/source-repo \
  --profile path/to/delivery-profile.yaml \
  --working-branch develop-leo \
  --program-first \
  --output-dir /path/to/legacy-modernization-delivery/modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review
```

`--working-root` is the current-run artifact root. Do not pass
`--delivery-root` for the default program-flow workflow.

`--source-root` enables automatic source inventory cache lookup at
`<source-root>/outputs/repo-scan/`. If `program-list.csv` and
`scan-summary.yaml` exist and `scan-summary.yaml.source_revision_key` matches
the current clean Git source HEAD, the builder marks the cache `fresh` and the
skill uses it to target program analysis. If the cache is missing, stale, or
the source worktree has uncommitted source changes, rerun repo inventory on
Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py C:\path\to\source-repo `
  --out-dir C:\path\to\source-repo\outputs\repo-scan
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py /path/to/source-repo \
  --out-dir /path/to/source-repo/outputs/repo-scan
```

Teams with a different cache location can change `source_inventory_profile` or
pass `--inventory-dir`; SMEs should not edit this per run.

The builder writes:

```text
program-set-core-input-manifest.yaml
program-set-sme-core-review.md
```

Fill `program-set-sme-core-review.md` from the manifest-listed compact
artifacts only. The manifest records `run_resolution`, not central lookup
status.

## Validate Before SME Handoff

Windows:

```powershell
powershell -NoProfile -File .agents\skills\legacy-ibmi-flow-analyzer\scripts\invoke-windows-tool.ps1 ValidateProgramSetCoreReview `
  --manifest C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews\card_auth_posting_core_review\program-set-core-input-manifest.yaml `
  --review C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews\card_auth_posting_core_review\program-set-sme-core-review.md
```

macOS/Linux:

```bash
python3 scripts/validate-program-set-core-review.py \
  --manifest /path/to/legacy-modernization-delivery/modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/program-set-core-input-manifest.yaml \
  --review /path/to/legacy-modernization-delivery/modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/program-set-sme-core-review.md
```

Validation failure means the review is structurally unsafe for handoff. Fix the
review rows/sections instead of deleting programs from the manifest.

## Routing Rules

Program-flow routing uses current-run resolution:

```text
analyzed_this_run      -> read compact artifacts from working-root
reused_same_run        -> reuse an artifact produced earlier in the same run
pending_source         -> locate source and run program analysis
blocked_missing_source -> record blocker/TBD; do not fake completion
```

Program artifacts are stored by tier:

```text
modules/CAP-ID-0001-large_extreme_program/<PROGRAM>/
modules/CAP-ID-0002-complex_normal_program/<PROGRAM>/
modules/CAP-ID-0003-normal_program/<PROGRAM>/
```

Program-set reviews are cross-tier and stored under one configured parent:

```text
modules/CAP-ID-0004-program_set_reviews/{review_slug}/
  program-set-core-input-manifest.yaml
  program-set-sme-core-review.md
```

When the SME gives multiple program flows, each flow gets its own
`{review_slug}` child folder under the same parent. Reuse the same delivery
working branch for the batch; do not create one branch per flow unless the team
explicitly wants separate PRs.

## Invariants

- `@CU118` and `CU118` are different program identities unless the profile
  explicitly defines aliases.
- A working branch such as `develop-leo` is the current-run artifact workspace.
- `program_set_review_parent` is a parent folder. Each SME flow/review writes
  to a child `{review_slug}` folder beneath it.
- PR review compares current-run artifacts with older delivery history; the
  default program-flow run does not silently reuse older artifacts.
