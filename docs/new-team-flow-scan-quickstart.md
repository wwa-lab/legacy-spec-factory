# New Team Flow Scan Quickstart

Use this when a new department wants to adopt the source-repo plus delivery-repo
program-flow workflow from zero.
For internal prompt testing, see
[`flow-analysis-prompt-e2e-guideline.md`](flow-analysis-prompt-e2e-guideline.md).

![Program Flow Skill E2E](assets/program-flow-skill-e2e-flow.png)

Editable source: [`assets/program-flow-skill-e2e-flow.drawio`](assets/program-flow-skill-e2e-flow.drawio).

## Target Setup

Each team needs two repos:

```text
source repo    = read-only legacy code evidence
delivery repo  = generated analysis artifacts, SME review, PR review, reuse
```

Only delivery repo remote `main` is treated as approved reusable knowledge.
Working branches such as `develop-leo` are draft workspaces.

## 1. Create Delivery Repo Folders

Create or confirm these folder groups in the delivery repo:

```text
00_intake/
99_archive/
docs/
modules/
  CAP-ID-0001-large_extreme_program/
  CAP-ID-0002-complex_normal_program/
  CAP-ID-0003-normal_program/
  CAP-ID-0004-program_set_reviews/
```

The `CAP-ID-*` names are team-owned. The skill does not require these exact
IDs, but the delivery profile must describe whatever names the team chooses.

## 2. Create Team Delivery Profile

Copy the template:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

Save it in the team's normal config location, then edit:

```yaml
delivery_artifact_lookup_profile:
  repo: <ORG>/<DELIVERY_REPO>
  branch: main
  program_folder_patterns:
    - modules/*/{PROGRAM}
  program_name_normalization:
    case: upper
    preserve_prefixes:
      - "@"
    exact_folder_name_match: true

delivery_workspace_profile:
  repo: <ORG>/<DELIVERY_REPO>
  branch_mode: use_or_create_provided
  working_branch_pattern: develop-{PERSON}
  allowed_branch_patterns:
    - develop-*
  create_from: origin/main
  write_to_main: false
  program_tier_roots:
    large_extreme_program: modules/CAP-ID-0001-large_extreme_program
    complex_normal_program: modules/CAP-ID-0002-complex_normal_program
    normal_program: modules/CAP-ID-0003-normal_program
  program_set_review_parent: modules/CAP-ID-0004-program_set_reviews

source_inventory_profile:
  default_cache_dir: outputs/repo-scan
  program_list_filename: program-list.csv
  scan_summary_filename: scan-summary.yaml
  freshness_policy: clean_git_head_must_match
```

If another team stores programs under a different layout, change
`program_folder_patterns`, `program_tier_roots`, and
`program_set_review_parent`. If their source inventory cache is not under
`outputs/repo-scan`, change `source_inventory_profile`. SMEs should not edit
this every run; the team sets it once.

## 3. Confirm Access

The operator or agent needs:

- read access to the source repo
- read access to delivery repo remote `main`
- write access to the delivery working branch
- permission to open a PR back to delivery repo `main`

Do not write directly to `main`.

## 4. First Working Branch

Use the team's naming convention, for example:

```text
Delivery working branch: develop-leo
```

If the branch does not exist, create it from `origin/main`. Reuse one working
branch for the person's batch of programs instead of creating a branch per
scan.

## 5. First Program Flow Run

Ask the SME for:

```text
Delivery working branch: develop-leo
Review name: <business-friendly name>
Source repo: /path/to/source-repo
Programs:
- <PROGRAM-1>
- <PROGRAM-2>
- <PROGRAM-3>
```

Then follow [`flow-skill-e2e-guideline.md`](flow-skill-e2e-guideline.md).
The skill first checks `<source-repo>/outputs/repo-scan/program-list.csv` and
`scan-summary.yaml` for programs not found on delivery remote `main`. If that
cache is missing or stale, run `legacy-ibmi-inventory` once for the source repo
and then continue with targeted per-program scans.

The first run should prove:

- central repo lookup works against remote `main`
- source inventory cache freshness is recorded
- existing program artifacts are reused
- missing programs are scanned from source
- program artifacts land in the configured tier folders
- the program-set review lands under `program_set_review_parent`
- validator passes before SME handoff

If the SME provides multiple program flows at once, keep them as separate flow
blocks. Run the program-set builder once per flow block and write each result
to its own folder under `program_set_review_parent`. Reuse the same
`develop-<person>` branch and one PR for the batch.

## 6. Expected Delivery Repo Result

After one mixed program-flow run, the working branch may contain:

```text
modules/CAP-ID-0001-large_extreme_program/@CU118/
  program-analysis-summary.yaml
  source-index.yaml
  routine-logic-details.yaml
  message-inventory.yaml

modules/CAP-ID-0002-complex_normal_program/CU257F/
  program-analysis-summary.yaml
  source-index.yaml
  routine-logic-details.yaml
  message-inventory.yaml
  file-io-inventory.yaml

modules/CAP-ID-0003-normal_program/CC050/
  program-analysis-summary.yaml
  source-index.yaml
  routine-logic-details.yaml
  message-inventory.yaml

modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
  program-set-core-input-manifest.yaml
  program-set-sme-core-review.md
```

The exact sidecars depend on program tier and triggered evidence needs.
For multiple flows, expect sibling folders such as:

```text
modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
modules/CAP-ID-0004-program_set_reviews/nightly_recon_core_review/
modules/CAP-ID-0004-program_set_reviews/manual_adjustment_core_review/
```

## 7. PR And Promotion

Open one PR for the batch. Include:

- SME-provided program list
- lookup result summary
- programs reused from remote `main`
- programs newly scanned
- output folders touched
- validator result
- SME review focus

After review and merge to `main`, those artifacts become reusable by future
flow scans.

## Common Mistakes

- Using a stale local delivery checkout as proof that a program is missing.
- Treating `develop-<person>` as approved reuse source.
- Stripping `@` from program names when the profile says exact match.
- Creating one delivery branch per program scan.
- Combining unrelated SME flow blocks into one program-set review.
- Putting a program-set review inside one program tier folder instead of the
  configured `program_set_review_parent`.
- Letting the LLM omit a requested program because its artifact was missing.
