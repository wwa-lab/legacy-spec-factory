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
and future reuse. Only delivery repo remote `main` is treated as the approved
central artifact source.

## One Profile

Start from:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Edit these team-owned values once:

```yaml
delivery_artifact_lookup_profile:
  repo: CH-WPS-LENDING-CARDS/legacy-modernization-delivery
  branch: main
  program_folder_patterns:
    - modules/*/{PROGRAM}

delivery_workspace_profile:
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
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

## Prepare Remote Main Snapshot

Lookup must use delivery repo remote `main`, not a stale local branch. The
agent may prepare a temporary sparse checkout/cache with Git method 2:

```bash
git ls-remote <DELIVERY_REPO_URL> refs/heads/main
git clone --depth 1 --branch main --filter=blob:none --sparse <DELIVERY_REPO_URL> /tmp/legacy-modernization-delivery-main
git -C /tmp/legacy-modernization-delivery-main sparse-checkout set modules
```

Use that path as `--delivery-root` for the builder. If a cache already exists,
refresh and verify it against `origin/main` before use.

## Build Program-Set Review Inputs

The field deployment environment is Windows. Use `py -3` there. Use
`python3` only on macOS/Linux development machines.

Create a program list file:

```text
@CU118
CU257F
CC050
```

Then build the deterministic manifest and review skeleton on Windows:

```powershell
py -3 scripts\build-program-set-core-review.py `
  --review-name "card auth posting core review" `
  --programs-file programs.txt `
  --delivery-root C:\tmp\legacy-modernization-delivery-main `
  --working-root C:\path\to\legacy-modernization-delivery `
  --source-root C:\path\to\source-repo `
  --profile C:\path\to\delivery-profile.yaml `
  --working-branch develop-leo `
  --output-dir C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews\card_auth_posting_core_review
```

macOS/Linux:

```bash
python3 scripts/build-program-set-core-review.py \
  --review-name "card auth posting core review" \
  --programs-file programs.txt \
  --delivery-root /tmp/legacy-modernization-delivery-main \
  --working-root /path/to/legacy-modernization-delivery \
  --source-root /path/to/source-repo \
  --profile path/to/delivery-profile.yaml \
  --working-branch develop-leo \
  --output-dir /path/to/legacy-modernization-delivery/modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review
```

`--delivery-root` is the remote-main snapshot/cache used for approved reuse
lookup. `--working-root` is optional during the first preflight; after missing
programs are scanned into `develop-leo`, pass the working-branch checkout so
the final manifest can include those new artifacts without marking them as
remote-main approved.

For a direct single-program analyzer run, use the same lookup profile and
remote-main snapshot:

```powershell
py -3 scripts\index-rpg-source.py C:\path\to\source\CU257F.RPGLE `
  --program CU257F `
  --out-dir C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0002-complex_normal_program\CU257F `
  --delivery-root C:\tmp\legacy-modernization-delivery-main `
  --delivery-profile C:\path\to\delivery-profile.yaml
```

When the helper prints `central_lookup_result: found_on_remote_main`, do not
scan source. Return the reported central `artifact_root` to the SME. When it
prints `central_lookup_result: not_found_on_remote_main`, the helper continues
and writes the normal draft analysis seed to `--out-dir`.

To intentionally refresh an existing approved artifact, add a reasoned override:

```powershell
py -3 scripts\index-rpg-source.py C:\path\to\source\CU257F.RPGLE `
  --program CU257F `
  --out-dir C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0002-complex_normal_program\CU257F `
  --delivery-root C:\tmp\legacy-modernization-delivery-main `
  --delivery-profile C:\path\to\delivery-profile.yaml `
  --force-rescan `
  --rescan-reason "SME requested refresh after major source or rule change"
```

Use this only when the SME deliberately wants a new draft for review. The
output records the remote-main artifact that was bypassed; it still needs the
normal delivery branch review before becoming reusable from `main`.

`--source-root` enables automatic source inventory cache lookup at
`<source-root>/outputs/repo-scan/`. If `program-list.csv` and
`scan-summary.yaml` exist and `scan-summary.yaml.source_revision_key` matches
the current clean Git source HEAD, the builder marks the cache `fresh` and the
skill uses it to target only missing programs. If the cache is missing, stale,
or the source worktree has uncommitted source changes, rerun repo inventory on
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
artifacts only.

## Validate Before SME Handoff

Windows:

```powershell
py -3 scripts\validate-program-set-core-review.py `
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

Lookup always reads delivery repo remote `main`:

```text
found_on_remote_main      -> read compact artifacts from remote-main checkout
not_found_on_remote_main  -> scan source repo and write output to develop-*
remote_unavailable        -> stop for access/context
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
- A working branch such as `develop-leo` is draft output only; it is not an
  approved reuse source.
- `program_set_review_parent` is a parent folder. Each SME flow/review writes
  to a child `{review_slug}` folder beneath it.
- PR merge to `main` promotes artifacts into the central reusable snapshot.
