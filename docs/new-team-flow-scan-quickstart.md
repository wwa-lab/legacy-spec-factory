# New Team Flow Scan Quickstart

Use this when a new department wants to adopt the source-repo plus delivery-repo
program-flow workflow from zero.
For internal prompt testing, use
[`flow-analysis-prompt-e2e-guideline.md`](flow-analysis-prompt-e2e-guideline.md)
with Codex / Claude Code style agents, or
[`flow-analysis-copilot-chat-e2e-guideline.md`](flow-analysis-copilot-chat-e2e-guideline.md)
with GitHub Copilot Chat.

![Program Flow Skill E2E](assets/program-flow-skill-e2e-flow.png)

Editable source: [`assets/program-flow-skill-e2e-flow.drawio`](assets/program-flow-skill-e2e-flow.drawio).

## Target Setup

Each team needs two repos:

```text
source repo    = read-only legacy code evidence
delivery repo  = generated analysis artifacts, SME review, PR review
```

For the default program-flow workflow, every distinct SME-provided program is
analyzed for the current run. Working branches such as `develop-leo` are draft
workspaces and the program-set builder reads current-run artifacts from that
working branch only.

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
program_artifact_resolution_profile:
  repo: <ORG>/<DELIVERY_REPO>
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
`scan-summary.yaml` to locate each program and determine its tier. If that cache
is missing or stale, run `legacy-ibmi-inventory` once for the source repo and
then continue with targeted per-program scans.

The first run should prove:

- source inventory cache freshness is recorded
- every distinct SME-provided program is analyzed from source for the current run
- repeated programs in the same batch reuse the current-run artifact
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
- run_resolution summary
- programs analyzed this run
- repeated programs reused from the same run/batch
- output folders touched
- validator result
- SME review focus

After review and merge to `main`, those artifacts become durable delivery
history. Future program-flow runs still analyze their own current-run artifacts
by default, but an SME-local review can clone the document/delivery repo and
run the program-set builder with `--artifact-repo-mode approved_document_repo`
to assemble a selected program flow from approved existing artifacts.
Differences are reviewed through Git/PR.

## Common Mistakes

- Treating older delivery artifacts as completion evidence for this run.
- Stripping `@` from program names when the profile says exact match.
- Creating one delivery branch per program scan.
- Combining unrelated SME flow blocks into one program-set review.
- Putting a program-set review inside one program tier folder instead of the
  configured `program_set_review_parent`.
- Letting the LLM omit a requested program because its current-run artifact was
  missing.
