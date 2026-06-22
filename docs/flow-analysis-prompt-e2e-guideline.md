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
- support explicit SME force-rescan requests for approved remote-main programs
- write program artifacts to tier folders
- write one program-set review folder per SME flow under
  `modules/CAP-ID-0004-program_set_reviews/`
- produce `program-set-sme-core-review.md` with only the four core sections
- complete the review with evidence-backed SME content, not just a generated
  skeleton or lookup report
- pass `scripts/validate-program-set-core-review.py`

## Required Test Inputs

Prepare these values before running a prompt:

```text
Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
Delivery working branch: develop-<person>
Delivery working checkout: /path/to/legacy-modernization-delivery
Source repo: /path/to/source-repo
Delivery profile: /path/to/delivery-profile.yaml
Optional force rescan file: /path/to/force-rescan-programs.txt
```

Team setup is not repeated in every prompt. It should already live in the
delivery profile:

```text
delivery_artifact_lookup_profile
delivery_workspace_profile
source_inventory_profile
```

When the prompt asks the agent/operator to run a Python script in the company
Windows environment, use `py -3`, for example
`py -3 scripts\validate-program-set-core-review.py ...`. Use `python3` only on
macOS/Linux development machines.

## Prompt 1: Single Flow Core Review Complete E2E

Use this when the expected result is one completed SME-ready core review, not
only the first manifest/build step.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run one SME-provided program flow all the way to a completed compact SME
program-set core review.
Do not create flow-<FLOW-SLUG>.md.
Do not stop after creating the manifest, skeleton, source lookup report, or
placeholder compact artifacts.

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

Completion rule:
This run is complete only when:
- every SME-provided program appears in the manifest, Sources table, and Core
  Completeness Ledger
- every missing program has been analyzed with enough routine evidence to
  populate the four SME sections or a precise evidence-backed TBD
- program-set-sme-core-review.md contains real rows under Calculation Logic,
  Validation Logic, Exception Handling, and Message Inventory
- there are no generic placeholder statements such as "No explicit CALL literal
  detected" unless they are tied to a specific missing-evidence row and next
  action
- scripts/validate-program-set-core-review.py passes

Phase 1 - access, reuse, and routing:
1. Check delivery repo remote main snapshot/cache first for each exact program
   folder.
2. Treat @CU118 and CU118 as different program identities.
3. If delivery remote main cannot be checked, stop and report
   remote_unavailable. Do not treat remote_unavailable as not_found and do not
   scan source unless the user explicitly authorizes proceeding without central
   reuse.
4. Reuse any found_on_remote_main compact artifacts; do not rescan those
   programs. Exception: only rescan a found_on_remote_main program if the prompt
   provides an explicit force-rescan request with a reason.
5. For only not_found_on_remote_main programs, check source inventory cache at
   <source-root>/outputs/repo-scan/program-list.csv and scan-summary.yaml.
6. If source inventory cache is missing, stale, or the source tree is dirty,
   run repo-level inventory once, then use the refreshed program-list.csv to
   locate each missing program.

Phase 2 - complete missing program analysis before aggregation:
7. Scan only missing programs and write new artifacts to the delivery working
   branch under the tier folder from the delivery profile.
8. For each newly scanned program, run legacy-ibmi-program-analyzer according
   to its tier. Build source-index.yaml first, then analyze the entry/mainline,
   validation, calculation, file I/O or SQL update, exception/message, and
   external-call routines needed for this SME flow. Do not read more than five
   routine bodies per turn; continue in batches until the core SME sections can
   be supported.
9. Each newly scanned program must have at least:
   - program-analysis-summary.yaml
   - source-index.yaml
   - routine-logic-details.yaml
   - message-inventory.yaml
   - optional sidecars when observed or needed: file-io-inventory.yaml,
     field-mutation-matrix.yaml, sql-inventory.yaml
10. Reject placeholder-only program artifacts. If a program artifact only says
    lightweight scan, no CALL literal, no obvious messages, or otherwise lacks
    business logic rows, go back to that program's source-index and deep-read
    the routines needed to explain calculation, validation, exception handling,
    messages, and state changes.

Phase 3 - build and fill the program-set review:
11. After remote-main reuse and all missing program scans are complete, build
    or rebuild:
    modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
      program-set-core-input-manifest.yaml
      program-set-sme-core-review.md
    Do not write the review directly under
    modules/CAP-ID-0004-program_set_reviews/.
12. Fill program-set-sme-core-review.md only from manifest-listed compact
    artifacts and targeted program-analysis.md clarification. Keep rows grouped
    by the SME program order.
13. The four core sections must contain evidence-backed rows:
    - Calculation Logic: assignments, derived values, counters, totals, dates,
      flags, or explicit "no calculation observed" TBD rows with evidence scope
    - Validation Logic: checks, reject conditions, statuses, return codes, and
      outcomes
    - Exception Handling: monitored errors, file or SQL failures, message paths,
      rollback/continue/stop behavior, and unresolved paths
    - Message Inventory: every exact message ID, status, return code, SQLSTATE,
      CPF/MCH/RNX/CPD code, operator text, literal, or shop-local token observed
14. If a section truly has no observed evidence for a program, add a precise
    TBD row naming the program, routine/window inspected, missing artifact or
    evidence type, and next action. Do not replace the section with a generic
    sentence.
15. Run scripts/validate-program-set-core-review.py. If it fails, fix the
    review and rerun until it passes.

Report:
- lookup result by program
- inventory cache freshness/action
- newly scanned programs
- per-program analysis completeness and any routines still indexed_only
- output folder
- validator result
- remaining SME TBDs, if any
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

## Prompt 4: Explicit Program Refresh Override

Use this to test that an SME can intentionally refresh a program even though an
approved artifact already exists on delivery repo remote `main`.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a compact SME program-set core review, but intentionally refresh one
program that already exists on delivery repo remote main. Do not create
flow-<FLOW-SLUG>.md.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
card auth posting refresh test

SME-provided program flow, preserve this order:
- CU257F
- CC050

Force rescan requests:
- CU257F | SME requested refresh after major source or rule change

Expected behavior:
1. Check delivery repo remote main snapshot first for every program.
2. If CU257F is found_on_remote_main, do not reuse the old remote-main artifact
   for this review because an explicit force-rescan request exists.
3. Create a force-rescan file with one row:
   CU257F|SME requested refresh after major source or rule change
4. Run the targeted program analyzer for CU257F with:
   --force-rescan
   --rescan-reason "SME requested refresh after major source or rule change"
5. Write the refreshed CU257F draft artifacts to the delivery working branch
   tier folder.
6. Run the program-set builder with:
   --force-rescan-file <force-rescan-programs.txt>
   --working-root <delivery-working-checkout>
7. Confirm the manifest keeps:
   force_rescan: true
   rescan_reason: SME requested refresh after major source or rule change
   remote_main_artifact_root: <prior CU257F remote-main path>
   artifact_source: delivery_working_branch
8. Fill program-set-sme-core-review.md from the working-branch CU257F artifact
   plus normal remote-main or working artifacts for the other programs.
9. Run the validator before SME handoff.

Report:
- original remote-main artifact path for CU257F
- refreshed working-branch artifact path for CU257F
- manifest force_rescan fields
- validator result
```

## Prompt 5: Validation And PR Summary

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

## Prompt 6: Explicit Full Transaction Flow

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
| Explicit force rescan is honored | Forced programs record `force_rescan: true` and use working-branch artifacts |
| Multiple flows remain separate | One `{review_slug}` folder per flow |
| Repeated programs are not rescanned | Reuse remote-main or working-branch artifact |
| Review shape is compact | Only Calculation, Validation, Exception, Message sections after control tables |
| Review is complete enough for SME handoff | Four core sections contain evidence-backed rows or precise per-program TBD rows |
| Placeholder output is rejected | Generic lightweight-scan/no-CALL/no-message statements are replaced by routine-level evidence or named gaps |
| Output placement is scoped | Review is written under `program_set_review_parent/{review_slug}/`, not the parent folder |
| Validator runs | Each review folder has a pass/fail result |

## Common Test Failures

- The model creates one combined review for multiple unrelated flows.
- The model uses a stale local delivery checkout instead of remote `main`.
- The model strips `@` from a program name.
- The model reruns repo inventory even though `outputs/repo-scan` is fresh.
- The model rescans a program already found on remote `main`.
- The model ignores an explicit force-rescan request or still fills the review
  from the old remote-main artifact.
- The model puts full-flow sections into `program-set-sme-core-review.md`.
- The model writes a review directly under `CAP-ID-0004-program_set_reviews/`
  instead of a `{review_slug}` child folder.
- The model stops after generating `program-set-core-input-manifest.yaml` and a
  review skeleton.
- The model treats `remote_unavailable` as `not_found_on_remote_main` and scans
  source without explicit approval.
- The model creates compact artifacts that only report simple source scan facts
  such as missing CALL literals, then fills the SME review from those
  placeholders instead of completing per-program routine analysis.
