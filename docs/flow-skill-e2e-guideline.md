# Flow Skill E2E Guideline

Use this guide when an SME provides one or more program flows/lists and expects
reviewable output that merges the core logic across each flow's programs.
For copy-ready internal test prompts, see
[`flow-analysis-prompt-e2e-guideline.md`](flow-analysis-prompt-e2e-guideline.md).

Default output:

```text
program-set-sme-core-review.md
```

This workflow does not generate `flow-<FLOW-SLUG>.md` unless the user
explicitly asks for full transaction-flow analysis.

![Program Flow Skill E2E](assets/program-flow-skill-e2e-flow.png)

Editable source: [`assets/program-flow-skill-e2e-flow.drawio`](assets/program-flow-skill-e2e-flow.drawio).

## What The SME Provides

Ask for these work-specific values for a single flow:

```text
Delivery working branch: develop-<person>
Review name: <business-friendly review name>
Source repo: /path/to/source-repo
Programs, in SME order:
- <PROGRAM-1>
- <PROGRAM-2>
- <PROGRAM-3>
Optional context:
- entry/menu/job/API hint
- known files, messages, or exception paths
Optional force rescan requests:
- <PROGRAM>|<why this approved remote-main artifact should be refreshed>
```

Program identity is exact. `@CU118` and `CU118` are different programs unless
the team's delivery profile explicitly defines aliases.

For multiple flows in one request, ask the SME to provide one block per flow:

```text
Delivery working branch: develop-<person>
Source repo: /path/to/source-repo

Flow 1 review name: <business-friendly flow name>
Programs:
- <PROGRAM-1>
- <PROGRAM-2>

Flow 2 review name: <business-friendly flow name>
Programs:
- <PROGRAM-3>
- <PROGRAM-4>
```

Each flow block becomes one independent program-set review folder under
`program_set_review_parent`. Do not merge separate business flows into one
`program-set-sme-core-review.md`.

## Inputs The Agent Loads

- Source repo checkout or approved source export.
- Source inventory cache at `<source-root>/outputs/repo-scan/`, when present.
- Delivery repo remote `main` snapshot/cache for approved artifact reuse.
- Delivery repo working branch checkout, normally `develop-<person>`.
- Team delivery profile, usually copied from
  [`skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml`](../skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml).

Remote `main` is the approved reuse source. The working branch is draft output
only.

## E2E Flow

1. Normalize the SME program list.
2. Load the delivery profile.
3. Prepare or refresh a remote-main snapshot/cache of the delivery repo.
4. Run central artifact lookup for every program.
5. Reuse programs found on remote `main`; do not rescan them unless the SME
   explicitly provides a force-rescan request with a reason.
6. For only `not_found_on_remote_main` programs, check source inventory cache:
   `<source-root>/outputs/repo-scan/program-list.csv` and
   `<source-root>/outputs/repo-scan/scan-summary.yaml`.
7. If cache is fresh, use `program-list.csv` to locate source path and tier; if
   cache is missing/stale/dirty, rerun `legacy-ibmi-inventory` repo scan first.
8. Use `legacy-ibmi-program-analyzer` for missing programs with the appropriate
   normal, complex, or large strategy.
9. Write newly scanned program artifacts to the delivery working branch under
   the configured tier folder.
10. Build the program-set manifest and review skeleton.
11. Fill only Calculation Logic, Validation Logic, Exception Handling, and
   Message Inventory from manifest-listed compact artifacts.
12. Validate the review before SME handoff.
13. Open a PR from the working branch. Merge to `main` only after review.

For multiple flow blocks, run steps 1-12 once per flow block. Reuse the same
remote-main snapshot, source inventory cache, delivery working branch, and PR
when they belong to the same SME batch. If a program appears in more than one
flow, reuse its remote-main artifact or the newly scanned working-branch
artifact; do not rescan it just because it appears in a second flow.

## Commands

The field deployment environment is Windows. Use `py -3` there. Use
`python3` only on macOS/Linux development machines.

Prepare a read-only remote-main snapshot:

```bash
git ls-remote <DELIVERY_REPO_URL> refs/heads/main
git clone --depth 1 --branch main --filter=blob:none --sparse \
  <DELIVERY_REPO_URL> /tmp/legacy-modernization-delivery-main
git -C /tmp/legacy-modernization-delivery-main sparse-checkout set modules
```

Create the program list:

```text
@CU118
CU257F
CC050
```

Build the deterministic program-set inputs on Windows:

```powershell
py -3 scripts/build-program-set-core-review.py `
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

Use `--delivery-root` for approved remote-main lookup. Use `--working-root`
after missing programs have been scanned into the working branch, so the final
manifest can include newly scanned artifacts without marking them as approved
remote-main reuse.

If the SME explicitly wants to refresh an approved remote-main artifact, create
a force-rescan file:

```text
CU257F|SME requested refresh after major source or rule change
```

Pass it to the builder:

```powershell
py -3 scripts\build-program-set-core-review.py `
  --review-name "card auth posting core review" `
  --programs-file programs.txt `
  --delivery-root C:\tmp\legacy-modernization-delivery-main `
  --working-root C:\path\to\legacy-modernization-delivery `
  --source-root C:\path\to\source-repo `
  --profile C:\path\to\delivery-profile.yaml `
  --working-branch develop-leo `
  --force-rescan-file force-rescan-programs.txt `
  --output-dir C:\path\to\legacy-modernization-delivery\modules\CAP-ID-0004-program_set_reviews\card_auth_posting_core_review
```

Then run the single-program analyzer for each forced program with
`--force-rescan --rescan-reason "<why>"` and write the refreshed draft artifact
to the delivery working branch. Rerun the builder with the same
`--force-rescan-file` and `--working-root` after the refreshed artifact exists,
so `program-set-sme-core-review.md` uses the working-branch artifact instead of
the old remote-main artifact.

Use `--source-root` to enable the default source inventory cache lookup at
`<source-root>/outputs/repo-scan/`. Use `--inventory-dir` only when the team
profile or local run stores `program-list.csv` and `scan-summary.yaml` in a
different location.

Repo-level inventory cache, only when needed on Windows:

```powershell
py -3 skills\legacy-ibmi-inventory\scripts\scan_ibmi_repo.py C:\path\to\source-repo `
  --out-dir C:\path\to\source-repo\outputs\repo-scan
```

macOS/Linux:

```bash
python3 skills/legacy-ibmi-inventory/scripts/scan_ibmi_repo.py /path/to/source-repo \
  --out-dir /path/to/source-repo/outputs/repo-scan
```

The builder marks the cache `fresh` only when `scan-summary.yaml` records the
same clean Git source revision. Missing, stale, or dirty source states route to
repo-level inventory before targeted program scan.

Validate before handoff on Windows:

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

For multiple flow blocks, create one `programs.txt` per flow and run the
builder once per flow with a different `--review-name` and `--output-dir`:

```text
modules/CAP-ID-0004-program_set_reviews/
  card_auth_posting/
    program-set-core-input-manifest.yaml
    program-set-sme-core-review.md
  nightly_recon/
    program-set-core-input-manifest.yaml
    program-set-sme-core-review.md
```

## Routing Table

| Lookup result | What it means | Action |
| --- | --- | --- |
| `found_on_remote_main` | Exact program folder exists in delivery repo remote `main`. | Reuse compact artifacts from remote-main snapshot/cache. |
| `found_on_remote_main` + explicit force rescan | Exact program folder exists, but SME requested a refreshed draft with a reason. | Run program analyzer with `--force-rescan --rescan-reason`, write to working branch, and pass `--force-rescan-file` to the builder. |
| `not_found_on_remote_main` | Program was not approved on remote `main`. | Scan source, write artifacts to working branch, include them via `--working-root`. |
| `remote_unavailable` | Remote `main` could not be checked. | Stop for access/context; do not assume missing. |

## Output Placement

Program artifacts:

```text
modules/CAP-ID-0001-large_extreme_program/<PROGRAM>/
modules/CAP-ID-0002-complex_normal_program/<PROGRAM>/
modules/CAP-ID-0003-normal_program/<PROGRAM>/
```

Program-set review:

```text
modules/CAP-ID-0004-program_set_reviews/{review_slug}/
  program-set-core-input-manifest.yaml
  program-set-sme-core-review.md
```

Multiple program flows:

```text
modules/CAP-ID-0004-program_set_reviews/{flow_1_review_slug}/
modules/CAP-ID-0004-program_set_reviews/{flow_2_review_slug}/
modules/CAP-ID-0004-program_set_reviews/{flow_3_review_slug}/
```

## Pass Criteria

- Every SME-provided program appears in the manifest, Sources table, and Core
  Completeness Ledger for its flow.
- Found remote-main programs are not rescanned.
- `remote_unavailable` is treated as an access/context blocker, not as a
  missing-program result.
- Missing programs are scanned once and written to the correct tier folder.
- Source inventory cache is reused only when its source revision is fresh.
- Multiple SME-provided flows produce separate `{review_slug}` folders under
  `program_set_review_parent`; they may share one working branch and PR.
- The review contains only:
  - Calculation Logic
  - Validation Logic
  - Exception Handling
  - Message Inventory
- The four core sections contain routine-level evidence-backed rows or precise
  per-program TBD rows. Placeholder-only statements from lightweight source
  scans are not sufficient for SME handoff.
- `scripts/validate-program-set-core-review.py` passes before SME review.
