# Flow Analysis Copilot Chat E2E Guideline

Use this guide when the runtime is GitHub Copilot Chat or another limited chat
UI. Copilot Chat should not be asked to complete a whole multi-program flow in
one chat. Use a segmented workflow:

1. one setup/preflight chat for the SME program flow
2. one fresh chat per program analysis
3. one assembly chat for `program-set-sme-core-review.md`
4. one validation/PR-summary chat

For Codex or Claude Code, use the single-agent prompt guide instead:
[`flow-analysis-prompt-e2e-guideline.md`](flow-analysis-prompt-e2e-guideline.md).

For interrupted runs or new-session handoff, use
[`flow-analysis-resume-guideline.md`](flow-analysis-resume-guideline.md).

## Why This Is Split

GitHub Copilot Chat does not provide reliable isolated workers inside one chat.
For program flow such as:

```text
Program A -> Program B -> Program C
```

do not ask one chat to analyze A, B, C, and assemble the review all at once.
Instead:

```text
Chat 1: prepare worklist and queue
Chat 2: analyze Program A
Chat 3: analyze Program B
Chat 4: analyze Program C
Chat 5: assemble program-set-sme-core-review.md
Chat 6: validate and summarize
```

Each program-analysis chat must be fresh. Do not carry source excerpts or
prior program summaries into the next program chat.

## Required Inputs

Before starting, prepare:

```text
Delivery working checkout: /path/to/legacy-modernization-delivery
Delivery working branch: develop-<person>
Source repo: /path/to/source-repo
Delivery profile: /path/to/delivery-profile.yaml
Review name: <business-friendly review name>
SME program flow:
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>
```

If the team does not yet have a delivery profile, copy:

```text
skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
```

to a team config location, update the repo/folder values, and use that copied
file for the run.

Parameter naming warning:

- `legacy-ibmi-program-list-batch` may use `--delivery-root` to mean the output
  root for generated per-program artifacts.
- `scripts/build-program-set-core-review.py` must not use `--delivery-root`.
  For the program-set builder, use `--working-root`.

Company Windows environment:

- Use `py -3` for Python commands.
- Use `python3` only on macOS/Linux development machines.

## Phase 0: Optional Delivery Profile Setup

Use this only if the team does not have a delivery profile yet.

```text
/legacy-ibmi-flow-analyzer

If this slash command is unavailable, follow
skills/legacy-ibmi-flow-analyzer/SKILL.md.

Task:
Prepare a delivery profile for a program-flow core review test.

Inputs:
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Review name: <REVIEW_NAME>

Expected delivery folder layout:
- modules/CAP-ID-0001-large_extreme_program
- modules/CAP-ID-0002-complex_normal_program
- modules/CAP-ID-0003-normal_program
- modules/CAP-ID-0004-program_set_reviews

Instructions:
1. If no delivery profile exists, copy
   skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml to a team
   config path.
2. Update only the repo/folder values needed for this test.
3. Preserve exact program identity unless the team explicitly defines aliases.
   In the default profile, @CU118 and CU118 are different programs.
4. Do not configure remote-main or prior-run reuse for this program-flow test.

Return:
- delivery profile path
- folder roots that will receive normal, complex, large, and program-set
  review outputs
- any values still needing human confirmation
```

## Phase 1: Flow Worklist And Inventory Preflight

Use one Copilot Chat session for this phase.

```text
/legacy-ibmi-flow-analyzer

If this slash command is unavailable, follow
skills/legacy-ibmi-flow-analyzer/SKILL.md.

Task:
Prepare the current-run worklist for one SME-provided program flow.
Do not analyze program bodies in this chat.
Do not assemble program-set-sme-core-review.md in this chat.
Do not check remote main, prior-run cache, or another analyst's artifacts.

Runtime inputs:
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Delivery profile: <DELIVERY_PROFILE>

Review name:
<REVIEW_NAME>

SME-provided program flow, preserve this order:
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>

Rules:
1. Treat the SME list as an ordered program flow.
2. Deduplicate only exact normalized repeats within this same batch.
3. Preserve the original SME order for later assembly.
4. Check source inventory cache:
   <source-root>/outputs/repo-scan/program-list.csv
   <source-root>/outputs/repo-scan/scan-summary.yaml
5. If the cache is missing, stale, or the source tree is dirty, run repo-level
   legacy-ibmi-inventory once, then use the refreshed program-list.csv.
6. Determine each distinct program's source path and size tier:
   normal_program, complex_normal_program, or large_extreme_program.
7. Prepare one-program-per-chat queue inputs for
   legacy-ibmi-program-list-batch or equivalent manual queue files.

Return:
- ordered SME flow
- distinct current-run program worklist
- source path and tier for each program
- source_inventory freshness/action
- output directory planned for each program
- next prompt/file to use for each program-analysis chat
```

## Phase 2: Analyze One Program Per Fresh Chat

Run this phase once per distinct program. Open a new Copilot Chat each time.
If Phase 1 generated `prompt-queue/*.md`, paste the matching prompt file
instead of the generic prompt below.

```text
/legacy-ibmi-program-analyzer

If this slash command is unavailable, follow
skills/legacy-ibmi-program-analyzer/SKILL.md.

Task:
Analyze exactly one IBM i program for the current program-flow run.

Do not rely on previous chat history.
This is a fresh Copilot Chat session for one program only.
Do not import prior program source, prior chat summaries, or older delivery
artifacts.

Program:
<PROGRAM>

Source path:
<SOURCE_PATH>

Language:
<SOURCE_KIND>

Initial size tier:
<SIZE_TIER>

Source repo:
<SOURCE_REPO>

Output directory:
<PROGRAM_OUTPUT_DIR_IN_DELIVERY_WORKING_CHECKOUT>

Rules:
1. Build deterministic indexes first.
2. Analyze only this program.
3. If the output directory already contains prior artifacts for this program,
   overwrite this program's generated analysis artifacts with the current
   output. Do not skip because old artifacts exist.
4. Read at most five routine bodies per turn.
5. Keep normal_program output lightweight unless density triggers appear.
6. For normal_program, do not create routine-logic-details.md,
   routine-logic-details.yaml, deep-read-plan.md, or batch deep-read files
   unless the tier is promoted or deep-read is explicitly requested.
7. Create routine-logic-details.md and routine-logic-details.yaml only when the
   program is complex_normal_program, large_extreme_program, or explicitly
   deep-read.
8. Do not treat indexed_only routines as confirmed business logic.
9. Reject placeholder-only output. If evidence is genuinely unavailable, write
   a precise TBD with inspected routine/window, missing evidence type, and next
   action.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml

Conditional output:
- routine-logic-details.md and routine-logic-details.yaml only for
  complex_normal_program, large_extreme_program, or explicit deep-read
  continuation.
- file-io-inventory.yaml, field-mutation-matrix.yaml, and sql-inventory.yaml
  only when observed or needed by the flow claim.
- deep-read-plan.md, all-routine-coverage-ledger.md, and
  routine-logic-details/deep-read-batch-*.md only when triggered by
  complex/large tier or retained batch evidence.

Validation:
Run the program-analysis validator before marking complete.

Return:
- output directory
- generated artifacts
- final size tier
- validator result
- any indexed_only routines that still affect Calculation Logic, Validation
  Logic, Exception Handling, or Message Inventory
- any precise TBDs
```

Repeat Phase 2 until every distinct program in the SME flow has completed
current-run artifacts or a precise blocked state.

## Phase 3: Assemble The Program-Set Review

Use a new Copilot Chat after all program chats are done.

```text
/legacy-ibmi-flow-analyzer

If this slash command is unavailable, follow
skills/legacy-ibmi-flow-analyzer/SKILL.md.

Task:
Assemble one completed compact SME program-set core review from current-run
program-analysis artifacts.

Do not create flow-<FLOW-SLUG>.md.
Do not use remote main, prior-run cache, or older delivery artifacts.
Do not assemble from placeholder-only or incomplete program-analysis artifacts.

Runtime inputs:
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Delivery profile: <DELIVERY_PROFILE>

Review name:
<REVIEW_NAME>

SME-provided program flow, preserve this order:
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>

Current-run program artifact folders:
- <PROGRAM-A>: <PROGRAM_A_OUTPUT_DIR>
- <PROGRAM-B>: <PROGRAM_B_OUTPUT_DIR>
- <PROGRAM-C>: <PROGRAM_C_OUTPUT_DIR>

Instructions:
1. Confirm every SME-provided program appears in the current-run artifact
   folders or has a precise blocked/pending state.
2. Build or rebuild:
   modules/CAP-ID-0004-program_set_reviews/<REVIEW_SLUG>/
     program-set-core-input-manifest.yaml
     program-set-sme-core-review.md
3. Use the program-set builder with --program-first and --working-root only.
   Do not pass --delivery-root to the program-set builder.
4. Confirm manifest run_resolution values are only:
   analyzed_this_run, reused_same_run, pending_source, blocked_missing_source.
5. Confirm the manifest does not contain central_lookup_result,
   found_on_remote_main, force_rescan, or remote_main_artifact_root.
6. Fill program-set-sme-core-review.md from current-run compact artifacts.
   Prefer program-analysis-summary.yaml, source-index.yaml,
   message-inventory.yaml, routine-logic-details.yaml when required/present,
   and optional sidecars when needed.
7. Use program-analysis.md only for targeted clarification.
8. Keep the review self-contained. The SME must not need to open per-program
   docs to understand Calculation Logic, Validation Logic, Exception Handling,
   or Message Inventory.
9. Include evidence-backed rows or precise per-program TBD rows in all four
   core sections.
10. Keep rows grouped by SME flow order when possible.
11. Do not include Nodes, Edges, Replay, Persistence, Lineage, UI Surfaces,
   Capability Seeds, or SME Checklist.

Return:
- manifest path
- review path
- run_resolution by program
- Core Completeness Ledger status
- remaining SME TBDs
```

## Phase 4: Validate And Prepare PR Summary

Use one final Copilot Chat session.

```text
/legacy-ibmi-flow-analyzer

If this slash command is unavailable, follow
skills/legacy-ibmi-flow-analyzer/SKILL.md.

Task:
Validate the generated program-set SME core review and prepare a PR-ready
summary.

Review folder:
<DELIVERY_WORKING_CHECKOUT>/modules/CAP-ID-0004-program_set_reviews/<REVIEW_SLUG>/

Validation:
Run scripts/validate-program-set-core-review.py against:
- program-set-core-input-manifest.yaml
- program-set-sme-core-review.md

Checks:
1. Every manifest program appears in Sources and Core Completeness Ledger.
2. Core Completeness Ledger uses current columns:
   Routine Logic Evidence and Message Inventory.
3. The manifest uses run_resolution, not central_lookup_result.
4. The review contains only the compact SME core sections:
   Calculation Logic, Validation Logic, Exception Handling, Message Inventory.
5. The review does not contain Nodes, Edges, Replay, Persistence, Lineage,
   UI Surfaces, Capability Seeds, or SME Checklist.
6. The four core sections contain evidence-backed rows or precise
   per-program TBD rows.

Return:
- validator result
- output folder
- program artifact folders used
- source inventory cache status
- run_resolution summary
- remaining SME TBDs
- PR summary bullets
```

## Resume Rules

If a Copilot Chat session stops or context fills up:

1. Start a new chat.
2. Do not rely on chat history.
3. Read durable files first:
   - program-list-status.csv
   - batch-scan-manifest.yaml
   - program-batch-plan.md
   - generated program artifact folders
   - program-set-core-input-manifest.yaml, if it already exists
4. Continue from the first incomplete queued, in_progress, failed, blocked, or
   validator-failed item.
5. Do not skip a program because an older artifact exists. Reruns overwrite the
   current program's generated artifacts and must validate again.

## Expected Evidence

| Check | Expected result |
| --- | --- |
| One chat per program | Each program-analysis chat names exactly one program |
| Program-first analysis | Every distinct SME program has current-run artifacts before assembly |
| Exact identity | `@CU118` and `CU118` remain different unless aliases are configured |
| No cross-run reuse | Older artifacts do not satisfy the current evidence gate |
| Normal output stays lightweight | normal_program does not create routine-logic-details unless promoted or explicitly deep-read |
| Complex/large retains detail | complex_normal_program and large_extreme_program keep routine-logic-details and retained batch evidence when needed |
| Review is self-contained | SME can read four core sections without opening per-program docs |
| Ledger uses current columns | Core Completeness Ledger has `Routine Logic Evidence` and `Message Inventory` |
| Validator runs | program-set validator result is recorded before SME handoff |

## Common Copilot Chat Failures

- Asking one chat to analyze multiple programs at once.
- Carrying previous program source into the next program chat.
- Treating old delivery artifacts as reusable cache.
- Forcing normal_program deep-read only because output is lightweight.
- Stopping after manifest/skeleton generation.
- Filling `program-set-sme-core-review.md` with generic "no CALL literal"
  placeholder text instead of evidence-backed rows or precise TBDs.
- Passing `--delivery-root` to `scripts/build-program-set-core-review.py`.
