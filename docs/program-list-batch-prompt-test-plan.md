# Program List Batch Prompt Test Plan

This plan tests `legacy-ibmi-program-list-batch` through prompts in a
Copilot Chat-only environment. It assumes the team cannot automatically create
new chats or run a true concurrent agent batch worker.

中文摘要: 这份测试计划用于公司内部 Copilot Chat 环境。目标不是测试模型能否
自动全量跑完，而是验证: program list 能否变成一组单 program prompt、每个
program 是否能独立处理、状态文件是否能支撑中断恢复和人工接力。

## Scope

Skill under test:

```text
legacy-ibmi-program-list-batch
```

Companion skill expected in each per-program prompt:

```text
legacy-ibmi-program-analyzer
```

Do not test large full-project batches first. Start with 3-5 programs:

- 2-3 `normal_program`
- 1 non-program row if available, such as DDS / PF / LF
- Optional: 1 row with intentionally missing source path

## Preconditions

- Source material is redacted or approved for internal analysis.
- Company internal test environment is Windows 11 and uses `py -3` as the only
  Python launcher.
- `program-list.csv` exists and has at least:
  `member`, `object_type`, `source_kind`, `path`, `total_lines`, `size_tier`,
  `tier_reason`.
- The operator can open fresh Copilot Chat sessions manually.
- The repository has the new skill synced under the runtime used by the team.

## Setup

Run the initializer locally or ask the agent to run it:

```powershell
py -3 skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.py `
  --program-list <path-to-program-list.csv> `
  --out-dir outputs\program-list-batch-test `
  --source-root <path-to-source-root> `
  --delivery-root <path-to-delivery-working-root> `
  --review-name "copilot prompt dry run"
```

Expected setup output:

```text
outputs/program-list-batch-test/
  program-batch-plan.md
  program-list-status.csv
  batch-scan-manifest.yaml
  prompt-queue/
```

Run:

```powershell
py -3 skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.py `
  --batch-dir outputs\program-list-batch-test
```

Expected result:

```text
Batch status validation passed
```

## Test Case 1: Prompt Queue Initialization

Purpose: confirm the skill creates one prompt per program row and skips
non-program rows.

Prompt to Copilot Chat:

```text
Use skill: legacy-ibmi-program-list-batch.

Review this generated batch queue:
- Batch directory: outputs/program-list-batch-test
- Program status list: outputs/program-list-batch-test/program-list-status.csv
- Prompt queue: outputs/program-list-batch-test/prompt-queue

Confirm:
- each prompt file names exactly one program
- non-program rows are marked skipped_not_program
- program-batch-plan.md, program-list-status.csv, and batch-scan-manifest.yaml
  agree on queued/skipped counts
- no two queued programs share the same output directory

Do not analyze source code in this test.
```

Pass criteria:

- Copilot does not start source analysis.
- It reports one prompt per `object_type = program` row.
- It reports non-program rows as skipped.
- It flags duplicate output directories if present.

## Test Case 2: Single Program Fresh Chat

Purpose: confirm a per-program prompt keeps the model scoped to one program.

Operator action:

1. Open a fresh Copilot Chat.
2. Paste the first file from `prompt-queue/`.
3. Let Copilot proceed.

Expected behavior:

- Copilot uses `legacy-ibmi-program-analyzer`.
- It analyzes only the named program.
- It does not mention or load other program rows unless checking shared status
  files.
- It writes or requests writes only under that program's output directory.
- It runs or instructs the operator to run the program-analysis validator.
- It updates or instructs updates to:
  - `program-batch-plan.md`
  - `program-list-status.csv`
  - `batch-scan-manifest.yaml`

Pass criteria:

- Required per-program artifacts exist, or the row is explicitly blocked or
  failed with `last_error` and `next_action`.
- `program-list-status.csv` records the row status.
- No other program's output directory is modified.

## Test Case 3: Copilot Chat Concurrency Negative

Purpose: confirm the skill refuses unsafe single-chat concurrency.

Prompt:

```text
Use skill: legacy-ibmi-program-list-batch.

Please run @CC080, @CC081, and @CC138T concurrently inside this one Copilot Chat
session and update all artifacts together.
```

Expected behavior:

- Copilot refuses or corrects the concurrent-in-one-chat request.
- It explains that Copilot Chat does not provide isolated workers inside one
  chat.
- It offers separate prompt files / separate chats instead.

Pass criteria:

- It does not start analyzing multiple source programs in the same response.
- It preserves the rule: one program per chat.

## Test Case 4: Resume In A New Chat

Purpose: confirm durable files, not chat memory, drive resume.

Operator action:

1. Complete or partially complete one program.
2. Open a new Copilot Chat.
3. Use this prompt:

```text
Use skill: legacy-ibmi-program-list-batch.
Task: resume a program-list batch from durable files.

Batch directory: outputs/program-list-batch-test
Program batch plan: outputs/program-list-batch-test/program-batch-plan.md
Program status list: outputs/program-list-batch-test/program-list-status.csv
Batch manifest: outputs/program-list-batch-test/batch-scan-manifest.yaml

Do not rely on previous chat history.
Identify the next row to process and tell me which prompt file to open next.
If an in_progress row exists, validate whether it can be trusted or must be
rechecked.
```

Expected behavior:

- Copilot reads durable state.
- It identifies next queued / unresolved row.
- It does not rely on memory from the previous chat.

Pass criteria:

- It names the correct next prompt file.
- It does not rescan a completed + validator pass row.

## Test Case 5: Missing Source Path

Purpose: confirm missing input becomes a blocker, not hallucinated analysis.

Setup:

- Include one program row whose `path` does not exist under `source-root`.

Prompt:

```text
Use skill: legacy-ibmi-program-list-batch.
Use the prompt file for the intentionally missing-source program.

If the source path is missing, do not infer program behavior. Mark the row
blocked_missing_source with last_error and next_action.
```

Expected behavior:

- Copilot does not invent behavior.
- Status becomes `blocked_missing_source`.
- `last_error` states the missing path.
- `next_action` asks for corrected source path or source root.

Pass criteria:

- No `program-analysis.md` is fabricated for the missing source.
- Batch status validator passes or reports only the expected blocker.

## Test Case 6: Completed Row Consistency

Purpose: confirm the batch validator catches false completion.

Setup:

- Manually set a row to `completed` and `validator_status=pass` while leaving
  required artifacts absent.

Command:

```powershell
py -3 skills\legacy-ibmi-program-list-batch\scripts\validate_program_batch_status.py `
  --batch-dir outputs\program-list-batch-test
```

Expected behavior:

- Validator fails.
- It reports missing output directory or missing required artifacts.

Pass criteria:

- False completion is caught before the batch can be treated as done.

## Test Case 7: Final Batch Readiness

Purpose: confirm the batch is ready for program-set SME review only after all
rows are classified.

Prompt:

```text
Use skill: legacy-ibmi-program-list-batch.

Review outputs/program-list-batch-test and tell me whether this batch is ready
for program-set SME review.

Check:
- every program row is completed, completed_with_warnings, reused_remote_main,
  skipped_not_program, blocked_*, or failed_*
- no row is queued or in_progress
- completed rows have validator pass
- blocked/failed rows have last_error and next_action
- no two completed rows share the same output directory

Do not generate the program-set review unless the readiness check passes.
```

Pass criteria:

- Copilot blocks final review if unresolved queued/in-progress rows remain.
- Copilot allows final review only when every row is classified.

## Evidence To Capture

For the dry run, archive:

- Input `program-list.csv`.
- Generated `program-batch-plan.md`.
- Generated `program-list-status.csv`.
- Generated `batch-scan-manifest.yaml`.
- Prompt files used.
- Copilot Chat transcript snippets for each test case.
- Validator output.
- Any generated per-program artifact directories.

## Exit Criteria

Repo dry-run passes when:

- Queue initialization passes.
- Single-program prompt stays scoped to one program.
- Single-chat concurrency request is refused or corrected.
- Resume prompt selects the correct next row from files.
- Missing source is blocked honestly.
- False completion is caught by validator.
- Final readiness is blocked until all rows are classified.

Field-pilot readiness is not claimed until the team records successful
Copilot Chat prompt smoke on representative internal data and completes the
normal Legacy Spec Factory skill review gate.
