# Flow Analysis Prompt E2E Guideline

Use this guide to test `legacy-ibmi-flow-analyzer` internally with realistic
SME inputs. The default test path is the compact SME program-set core review,
not a full transaction-flow artifact.

## Test Objective

Validate that the skill can:

- accept one SME program flow or multiple named program-flow blocks
- reuse delivery repo remote `main` artifacts before scanning source
- use fresh source inventory cache before repo-level source scan
- scan only missing programs
- write program artifacts to tier folders
- write one program-set review folder per SME flow under
  `modules/CAP-ID-0004-program_set_reviews/`
- produce `program-set-sme-core-review.md` with only the four core sections
- pass `scripts/validate-program-set-core-review.py`

## Required Test Inputs

Prepare these values before running a prompt:

```text
Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
Delivery working branch: develop-<person>
Delivery working checkout: /path/to/legacy-modernization-delivery
Source repo: /path/to/source-repo
Delivery profile: /path/to/delivery-profile.yaml
```

Team setup is not repeated in every prompt. It should already live in the
delivery profile:

```text
delivery_artifact_lookup_profile
delivery_workspace_profile
source_inventory_profile
```

## Prompt 1: Single Flow Core Review

Use this for the first internal smoke test.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a compact SME program-set core review for one SME-provided program flow.
Do not create flow-<FLOW-SLUG>.md.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
card auth posting core review

SME-provided program flow, preserve this order:
- @CU118
- CU257F
- CC050

Expected behavior:
1. Check delivery repo remote main snapshot first for each exact program folder.
2. Treat @CU118 and CU118 as different program identities.
3. Reuse any found_on_remote_main compact artifacts; do not rescan those programs.
4. For only not_found_on_remote_main programs, check source inventory cache at
   <source-root>/outputs/repo-scan/program-list.csv and scan-summary.yaml.
5. If source inventory cache is missing or stale, run repo-level inventory once.
6. Scan only missing programs and write new artifacts to the delivery working branch.
7. Build:
   modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
     program-set-core-input-manifest.yaml
     program-set-sme-core-review.md
8. Fill only Calculation Logic, Validation Logic, Exception Handling, and
   Message Inventory from manifest-listed compact artifacts.
9. Run the program-set validator before SME handoff.

Report:
- lookup result by program
- inventory cache freshness/action
- newly scanned programs
- output folder
- validator result
```

## Prompt 2: Multiple Flow Core Review Batch

Use this to test whether the skill can process multiple SME flow blocks without
mixing them together.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Process multiple SME-provided program flows as a single working-branch batch.
Do not create flow-<FLOW-SLUG>.md.
Create one program-set review folder per flow.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Flow 1 review name:
card auth posting core review
Programs, preserve order:
- @CU118
- CU257F
- CC050

Flow 2 review name:
nightly recon core review
Programs, preserve order:
- CC221
- CC224
- CC226

Flow 3 review name:
manual adjustment core review
Programs, preserve order:
- CU257F
- CC586
- CC779

Expected behavior:
1. Split this input into three independent flow blocks.
2. Reuse one delivery remote-main snapshot/cache for all flows.
3. Reuse one source inventory cache for all flows.
4. Reuse one delivery working branch, develop-leo, for the batch.
5. For repeated programs such as CU257F, do not rescan if already found on
   remote main or already generated in the working branch.
6. Generate one folder per flow:
   modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
   modules/CAP-ID-0004-program_set_reviews/nightly_recon_core_review/
   modules/CAP-ID-0004-program_set_reviews/manual_adjustment_core_review/
7. Each folder must contain its own program-set-core-input-manifest.yaml and
   program-set-sme-core-review.md.
8. Validate every generated review independently.

Report:
- per-flow output folder
- per-flow validator result
- programs reused from remote main
- programs reused from working branch
- programs newly scanned
- any flow blocked by remote_unavailable, stale inventory, or missing source
```

## Prompt 3: Source Inventory Cache Gate Test

Use this when testing the rule that repo-level inventory should not rerun when
`outputs/repo-scan` is fresh.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run central artifact lookup and source inventory cache preflight for this
program flow before any source scan.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
inventory cache gate smoke test

Programs:
- <PROGRAM-1>
- <PROGRAM-2>

Expected behavior:
1. Check delivery remote main first.
2. For not_found_on_remote_main programs, check:
   <source-root>/outputs/repo-scan/program-list.csv
   <source-root>/outputs/repo-scan/scan-summary.yaml
3. If scan-summary.yaml.source_revision_key matches the current clean Git
   source HEAD, report source_inventory.action = reuse_inventory.
4. If missing, stale, or dirty, report source_inventory.action =
   rerun_repo_inventory_scan and rerun repo inventory before targeted program
   scan.

Report the manifest source_inventory section and the next action.
```

## Prompt 4: Validation And PR Summary

Use this after the reviews are generated and filled.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Validate generated program-set SME core reviews and prepare a PR-ready summary.

Review folders:
- modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
- modules/CAP-ID-0004-program_set_reviews/nightly_recon_core_review/

For each folder:
1. Run scripts/validate-program-set-core-review.py against:
   - program-set-core-input-manifest.yaml
   - program-set-sme-core-review.md
2. Confirm every manifest program appears in Sources and Core Completeness
   Ledger.
3. Confirm the review does not contain Nodes, Edges, Replay, Persistence,
   Lineage, UI Surfaces, Capability Seeds, or SME Checklist.

Return:
- validation result per review folder
- summary of remote-main reused programs
- summary of newly scanned programs
- source inventory cache status
- SME review focus
- PR summary bullets
```

## Prompt 5: Explicit Full Transaction Flow

Use this only when the internal test intentionally wants the full
`flow-<FLOW-SLUG>.md` artifact. This is not the default SME core-review path.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a full transaction-flow analysis for one business event.
This request explicitly asks for flow-<FLOW-SLUG>.md.

Analysis intent:
standalone_exploratory

Trigger context:
- Trigger model: <batch/menu/subfile/f-key/db-trigger/scheduler/api>
- Business event name: <SME business event name>
- Entry program/object: <PROGRAM or config object>

Approved compact program analysis inputs:
- <program artifact folder 1>
- <program artifact folder 2>

Required behavior:
1. Do not infer calls, data flow, persistence, or exception propagation without
   upstream compact artifacts or SME/config evidence.
2. Include Transaction Call Map, Nodes, Edges, Cross-Program Data Flow, Replay,
   Field Lineage, Persistence Matrix, Branch Points, UI Surfaces when
   applicable, Error Propagation, Exception Chain, Capability Seeds, and Review
   Checklist.
3. Keep capability seeds as SME questions, not approved business rules.

Return the generated flow artifact path, blocking TBDs, and SME review focus.
```

## Expected Internal Test Evidence

Capture these results for each test run:

| Check | Expected result |
| --- | --- |
| Remote-main lookup happens before source scan | `found_on_remote_main` programs are not rescanned |
| Exact program identity is preserved | `@CU118` and `CU118` do not match each other unless aliases are configured |
| Source inventory cache gate is visible | Manifest has `source_inventory.freshness` and `source_inventory.action` |
| Missing programs are targeted | Only `not_found_on_remote_main` programs are scanned |
| Multiple flows remain separate | One `{review_slug}` folder per flow |
| Repeated programs are not rescanned | Reuse remote-main or working-branch artifact |
| Review shape is compact | Only Calculation, Validation, Exception, Message sections after control tables |
| Validator runs | Each review folder has a pass/fail result |

## Common Test Failures

- The model creates one combined review for multiple unrelated flows.
- The model uses a stale local delivery checkout instead of remote `main`.
- The model strips `@` from a program name.
- The model reruns repo inventory even though `outputs/repo-scan` is fresh.
- The model rescans a program already found on remote `main`.
- The model puts full-flow sections into `program-set-sme-core-review.md`.
- The model writes a review directly under `CAP-ID-0004-program_set_reviews/`
  instead of a `{review_slug}` child folder.
