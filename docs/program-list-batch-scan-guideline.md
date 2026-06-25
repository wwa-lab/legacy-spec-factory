# Program-List Batch Scan Guideline

This guideline is for GitHub Copilot, Codex, Claude Code, OpenCode, or any
runtime that needs to execute Legacy Spec Factory analysis from a prepared
program list.

中文摘要: 这份文档用于按 `program-list.csv` 批量执行 IBM i program scan。
核心原则是外层按清单批量调度，内层仍然使用
`legacy-ibmi-program-analyzer` 一次分析一个 program。不要把多个 program
合并进同一个 `program-analysis.md`。

Canonical skill entry: `legacy-ibmi-program-list-batch`.

Prompt-driven test plan:
[`program-list-batch-prompt-test-plan.md`](program-list-batch-prompt-test-plan.md).

## When To Use

Use this guideline when:

- You already have a program list from repo scan or inventory.
- The list contains columns such as `member`, `object_type`, `source_kind`,
  `path`, `total_lines`, `size_tier`, and `tier_reason`.
- You want to scan missing programs, reuse already accepted central artifacts,
  and then generate one SME-facing program-set review.

Do not use this guideline when:

- You only need to analyze one program. Use
  `docs/sme-ibmi-program-analyzer-normal-guideline.md`,
  `docs/sme-ibmi-program-analyzer-complex-guideline.md`, or
  `docs/sme-ibmi-program-analyzer-large-guideline.md`.
- The source has not been redacted or approved for analysis.
- The delivery remote-main snapshot cannot be checked.

## Skill Routing

Use these skill names explicitly in GitHub Copilot prompts:

```text
Use skill: legacy-ibmi-program-list-batch
Task: program-list driven batch scan and Copilot Chat prompt queue orchestration.

For each program row, use skill: legacy-ibmi-program-analyzer
Purpose: analyze one IBM i program at a time and generate evidence-backed
per-program artifacts.
```

The program-list batch skill is responsible for orchestration, prompt queue
generation, status tracking, manifest tracking, and resume/handoff control.
The program analyzer remains responsible for the actual per-program analysis.
Final program-set SME review is a downstream step after rows are classified.

## Input List Contract

Minimum useful columns:

| Column | Meaning |
| --- | --- |
| `member` | Program/member name, for example `@CC080`. |
| `object_type` | Process only rows where this value is `program`. |
| `source_kind` | Language hint such as `RPGLE`, `SQLRPGLE`, `CLLE`, or `COBOL`. |
| `path` | Source path relative to the source repo root. |
| `total_lines` | Line count from repo scan. |
| `size_tier` | Initial tier such as `normal_program`, `complex_normal_program`, or `large_extreme_program`. |
| `tier_reason` | Scanner explanation for the initial tier. |

Input checks before scanning:

- `member` is present.
- `object_type` is `program`.
- `source_kind` is one of the supported program languages or is explicitly
  marked unknown.
- `path` resolves under the source root.
- Duplicate normalized member names are reported.
- Names such as `@CC080` and `CC080` are treated as distinct unless a reviewed
  delivery profile explicitly defines aliases.

## English Copilot Prompt

```text
Use skill: legacy-ibmi-program-list-batch
Task: program-list driven batch scan and Copilot Chat prompt queue orchestration.

For each program row, use skill: legacy-ibmi-program-analyzer
Purpose: analyze one IBM i program at a time and generate evidence-backed
per-program artifacts.

Input:
- Program list: <path to program-list.csv>
- Source root: <path to source repository root>
- Delivery working root: <path to delivery repo working checkout>
- Delivery remote-main snapshot: <path to verified remote-main snapshot>
- Delivery profile: <path to delivery-profile.yaml>
- Delivery working branch: <develop-name>
- Review name: <business-friendly review name>
- Intent: standalone_exploratory
- Output mode: scan_missing_only

Program list columns:
- member
- object_type
- source_kind
- path
- total_lines
- size_tier
- tier_reason

Execution rules:
- Read the program list row by row.
- Process only rows where object_type = program.
- Use member as the Program name.
- Resolve source path as Source root + path.
- Use source_kind as the language hint.
- Use size_tier as the initial program tier, but allow
  legacy-ibmi-program-analyzer to reclassify if density triggers appear.
- Before scanning each program, check the central delivery remote-main
  snapshot.
- If central_lookup_result = found_on_remote_main, reuse the existing central
  artifact and skip source scan.
- If central_lookup_result = not_found_on_remote_main, run
  legacy-ibmi-program-analyzer for that program.
- If central_lookup_result = remote_unavailable, stop and report access or
  context needed.
- Do not combine multiple programs into one program-analysis.md.
- Each program must have its own output folder.
- Read at most 5 routine bodies per program-analysis turn.
- Keep normal_program output lightweight unless a density trigger appears.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Record skipped, reused, scanned, failed, and blocked programs in a batch
  manifest.
- Continue from the next unprocessed row if interrupted or resumed.

Per-program required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

Batch required output:
- batch-scan-manifest.yaml
- skipped/reused/scanned/failed summary
- program-set-core-input-manifest.yaml
- program-set-sme-core-review.md

Output folder rules:
- normal_program outputs go under the configured normal_program tier root.
- complex_normal_program outputs go under the configured
  complex_normal_program tier root.
- large_extreme_program outputs go under the configured large_extreme_program
  tier root.
- program-set SME review goes under the configured program_set_review_parent.

Quality gates:
- Do not mark a program complete only because files were generated.
- A program is complete only when required artifacts exist and the
  program-analysis validator passes.
- Validate each generated program-analysis artifact before marking that program
  complete.
- Validate the final program-set SME review before SME handoff.
- Do not mark the batch complete if required per-program artifacts are missing.
- Every non-trivial behavior claim must cite a source range, evidence ID,
  RLOG ID, runtime evidence, reference pack, or SME approval.
- indexed_only routines are inventory only, not confirmed behavior.
- Missing source, missing copybook, unresolved message description,
  unresolved dynamic call, or unsupported business meaning must become a TBD
  or blocker.
- Unresolved message/status/code descriptions must be listed as TBDs or
  blockers.
- The batch is complete only when every requested program is classified as
  reused, scanned, skipped, failed, or blocked, and the final program-set review
  validator passes.

Validation commands:
- In the company Windows 11 Copilot environment, use `py -3` only.
- For local macOS/Linux development, use `python3`.
- Do not install Python, create a virtual environment, or configure PATH.

Per-program validation:
py -3 scripts\validate-program-analysis-contract.py `
  --analysis-dir <program-output-dir>

Program-set validation:
py -3 scripts\validate-program-set-core-review.py `
  --manifest <program-set-core-input-manifest.yaml> `
  --review <program-set-sme-core-review.md>

Final response:
- Report total programs requested.
- Report programs reused from remote main.
- Report programs newly scanned.
- Report programs skipped or blocked.
- Report failed programs with reason.
- Report validator status.
- Provide paths to the batch manifest and program-set SME review.
```

## 中文 Copilot Prompt

```text
使用 skill: legacy-ibmi-program-list-batch
任务: 按 program list 批量执行 program scan，并编排 Copilot Chat prompt queue。

每处理一行 program 时，使用 skill: legacy-ibmi-program-analyzer
目的: 一次分析一个 IBM i program，并为每个 program 生成有 evidence 支撑的
独立分析产物。

输入:
- Program list: <program-list.csv 路径>
- Source root: <source repo 根目录>
- Delivery working root: <delivery repo 工作分支 checkout 路径>
- Delivery remote-main snapshot: <已验证的 remote main snapshot 路径>
- Delivery profile: <delivery-profile.yaml 路径>
- Delivery working branch: <develop-name>
- Review name: <业务可读的 review 名称>
- Intent: standalone_exploratory
- Output mode: scan_missing_only

Program list 字段:
- member
- object_type
- source_kind
- path
- total_lines
- size_tier
- tier_reason

执行规则:
- 按 program list 逐行读取。
- 只处理 object_type = program 的行。
- 使用 member 作为 Program name。
- 使用 Source root + path 解析真实 source path。
- 使用 source_kind 作为语言提示。
- 使用 size_tier 作为初始 program tier，但允许
  legacy-ibmi-program-analyzer 根据密集度触发重新分类。
- 每个 program 扫描前，先检查 central delivery remote-main snapshot。
- 如果 central_lookup_result = found_on_remote_main，复用已有 central
  artifact，跳过 source scan。
- 如果 central_lookup_result = not_found_on_remote_main，对该 program 执行
  legacy-ibmi-program-analyzer。
- 如果 central_lookup_result = remote_unavailable，停止并报告需要访问权限或
  上下文。
- 不要把多个 program 合并进同一个 program-analysis.md。
- 每个 program 必须有自己的输出目录。
- 每一轮 program-analysis 最多读取 5 个 routine body。
- 如果是 normal_program，且没有密集度触发，保持轻量输出。
- 不要在输出中粘贴大段真实 source code。
- 不要把 indexed_only routines 当成 confirmed business logic。
- 在 batch manifest 中记录 skipped、reused、scanned、failed、blocked 的
  program。
- 如果执行中断或恢复，从下一个未处理的 program 继续。

每个 program 必须产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

批量执行必须产出:
- batch-scan-manifest.yaml
- skipped/reused/scanned/failed summary
- program-set-core-input-manifest.yaml
- program-set-sme-core-review.md

输出目录规则:
- normal_program 输出到配置里的 normal_program tier root。
- complex_normal_program 输出到配置里的 complex_normal_program tier root。
- large_extreme_program 输出到配置里的 large_extreme_program tier root。
- program-set SME review 输出到配置里的 program_set_review_parent。

质量门禁:
- 不要因为文件生成了，就把 program 标记为 complete。
- 只有 required artifacts 存在，并且 program-analysis validator 通过时，
  该 program 才算 complete。
- 每个 program 生成后，先验证 program-analysis artifact，再标记该
  program complete。
- 最终 program-set SME review 在交给 SME 前必须验证。
- 如果缺少 required per-program artifacts，不要标记 batch complete。
- 每个非平凡 behavior claim 都必须引用 source range、evidence ID、
  RLOG ID、runtime evidence、reference pack 或 SME approval。
- indexed_only routines 只能表示已经索引，不能表示 confirmed behavior。
- 缺失 source、缺失 copybook、未解析 message description、未解析
  dynamic call、没有证据支持的 business meaning，都必须标记为 TBD 或
  blocker。
- 未解析的 message/status/code description 必须列为 TBD 或 blocker。
- 只有当每个请求的 program 都被分类为 reused、scanned、skipped、
  failed 或 blocked，并且最终 program-set review validator 通过时，batch
  才算 complete。

验证命令:
- 公司 Windows 11 Copilot 环境只使用 `py -3`。
- macOS/Linux 本地开发可以使用 `python3`。
- 不要安装 Python、创建 virtual environment 或配置 PATH。

单个 program 验证:
py -3 scripts\validate-program-analysis-contract.py `
  --analysis-dir <program-output-dir>

Program-set 验证:
py -3 scripts\validate-program-set-core-review.py `
  --manifest <program-set-core-input-manifest.yaml> `
  --review <program-set-sme-core-review.md>

最终回复:
- 报告本次请求的 program 总数。
- 报告从 remote main 复用的 programs。
- 报告本次新扫描的 programs。
- 报告 skipped 或 blocked 的 programs。
- 报告 failed programs 及失败原因。
- 报告 validator 状态。
- 提供 batch manifest 和 program-set SME review 的路径。
```

## Batch Manifest Quality Standard

The batch manifest is the resumable audit record. It should make the execution
state obvious without opening every generated artifact.

Recommended shape:

```yaml
batch_id: normal-program-scan-001
review_name: normal program batch
program_list: outputs/repo-scan/program-list.csv
source_root: /path/to/source-repo
delivery_working_root: /path/to/delivery-work
delivery_remote_main_snapshot: /tmp/delivery-main
status: in_progress
programs:
  - member: "@CC080"
    object_type: program
    source_kind: RPGLE
    source_path: HCCILERPG/@CC080.RPGLE
    initial_size_tier: normal_program
    final_size_tier: normal_program
    central_lookup_result: not_found_on_remote_main
    scan_status: completed
    validator_status: pass
    output_dir: modules/CAP-ID-0003-normal_program/@CC080
    blockers: []
    warnings: []
  - member: "@CC081"
    object_type: program
    source_kind: RPGLE
    source_path: HCCILERPG/@CC081.RPGLE
    initial_size_tier: normal_program
    final_size_tier: null
    central_lookup_result: not_found_on_remote_main
    scan_status: blocked_missing_source
    validator_status: not_run
    output_dir: null
    blockers:
      - source file not found under Source root + path
    warnings: []
```

Allowed program states:

| State | Meaning |
| --- | --- |
| `reused_remote_main` | Accepted central artifact exists and was reused. |
| `completed` | Source scan finished and validator passed. |
| `completed_with_warnings` | Required artifacts exist, but review warnings or non-blocking TBDs remain. |
| `blocked_missing_source` | The source path could not be resolved. |
| `blocked_remote_unavailable` | Remote-main lookup could not be checked. |
| `failed_validator` | Files were generated but validation failed. |
| `failed_runtime` | Tooling or runtime failed before a valid artifact could be produced. |
| `skipped_not_program` | Row was ignored because `object_type` was not `program`. |

## Resume After Interruption

If the batch is interrupted or a new chat/session must continue the work, do
not rely on conversation memory. Resume only from durable files.

Durable resume inputs:

- `batch-scan-manifest.yaml`
- Original `program-list.csv`
- Delivery profile
- Source root
- Delivery working root
- Delivery remote-main snapshot or a freshly verified replacement snapshot
- Existing per-program output folders
- Existing `program-set-core-input-manifest.yaml` and
  `program-set-sme-core-review.md`, if already generated

Resume rules:

- Read `batch-scan-manifest.yaml` first.
- Reconcile the manifest against the original program list.
- Re-check that each `completed` program has required artifacts and a passing
  validator result. If validation status is missing or stale, rerun validation.
- Do not rescan programs with `reused_remote_main` unless an explicit
  force-rescan request and reason is provided.
- Do not rescan programs with `completed` and `validator_status: pass`.
- Resume at the first row whose status is missing, `in_progress`,
  `failed_runtime`, `failed_validator`, or any blocker that has now been
  resolved.
- If a row is `blocked_missing_source`, retry only when the source path or
  source root has changed.
- If a row is `blocked_remote_unavailable`, refresh or recreate the
  remote-main snapshot before continuing.
- If a program output folder exists but the manifest does not record it, inspect
  and validate it before deciding whether to mark it complete or rescan.
- After all rows are classified, regenerate or refresh the program-set review
  from the manifest and compact artifacts.

## Context-Budget Continuation Strategy

Company-hosted models may have limited context windows. The workflow should not
stop early merely because the current chat is getting long. It should continue
while the current session can still safely read the next bounded source window,
write artifacts, and run validation. If the session cannot safely continue, it
must leave a clean checkpoint for the next session.

Core rule:

```text
If validation passed and the current session can still process the next bounded
batch, continue directly to the next batch. Do not stop early only because the
context budget is approaching a soft limit.
```

Additional safeguards:

- Keep each batch small and bounded: one program at a time, and at most five
  routine bodies or source windows per program-analysis turn.
- Never carry full source text, full prior batch details, or long generated
  artifacts forward in chat. Read only the next required source window and the
  compact state files.
- Treat these files as the memory layer:
  `batch-scan-manifest.yaml`, `program-analysis-summary.yaml`,
  `source-index.yaml`, `routine-index.md`, `routine-logic-details.yaml`,
  `message-inventory.yaml`, deep-read checkpoint files, and validator output.
- After every successful batch, update the manifest and the relevant compact
  sidecars before doing more reading.
- Before continuing, run the smallest useful validation or consistency check.
  If it passes, proceed to the next bounded batch in the same session.
- If validation fails, stop advancing and fix the current batch. Do not pile
  additional batches on top of a failed state.
- If the session is too full to safely read and patch the next batch, write a
  checkpoint that names the next exact program/routine/window and then stop.
- The next session should resume from the checkpoint files, not from a summary
  of the previous chat.

Recommended checkpoint fields:

```yaml
checkpoint:
  current_status: validated_checkpoint
  last_completed_program: "@CC080"
  last_completed_round: 13
  last_validator_status: pass
  next_action: continue_next_batch
  next_program: "@CC081"
  next_routines:
    - SR441
    - SR442
    - SR443
    - SR444
    - SR445
  required_reads:
    - source_path: HCCILERPG/@CC081.RPGLE
      line_range: "16659-17400"
  required_updates:
    - routine-logic-details.md
    - routine-logic-details.yaml
    - program-analysis-summary.yaml
    - message-inventory.yaml
    - batch-scan-manifest.yaml
  resume_instruction: >
    Validation passed for the previous batch. Continue with the next bounded
    batch if the current session can still safely read, patch, and validate it.
```

### English Auto-Continue Rule

Add this block to long-running batch prompts:

```text
Auto-continuation rule:
- Keep going while the current session can safely process the next bounded
  batch and validation is passing.
- Do not stop early only because the context budget is approaching a soft
  limit.
- Each continuation must be bounded to one program and at most 5 routine bodies
  or source windows.
- After each batch, update durable checkpoint files before reading more source.
- If validation passes, continue directly to the next bounded batch in the same
  session.
- If validation fails, stop advancing and fix the current batch.
- If the session cannot safely continue, write an explicit checkpoint with the
  next program, next routines/windows, required reads, required updates, and
  validator status. The next session must resume from those files.
- Do not carry long source excerpts or full prior artifacts in chat. Use compact
  state files as memory.
```

### 中文自动续跑规则

把这一段加到长时间批量 prompt 里:

```text
自动续跑规则:
- 只要当前 session 还能安全处理下一批 bounded batch，且上一批 validation
  通过，就直接继续。
- 不要仅仅因为上下文预算接近 soft limit 就提前收手。
- 每次续跑必须有边界: 一次只处理一个 program，并且最多 5 个 routine body
  或 source window。
- 每一批完成后，先更新 durable checkpoint files，再读取更多 source。
- 如果 validation 通过，就在当前 session 直接进入下一批 bounded batch。
- 如果 validation 失败，停止推进，先修当前批次。
- 如果当前 session 已经无法安全继续，必须写出明确 checkpoint，包括下一个
  program、下一个 routines/windows、需要读取的 source 范围、需要更新的文件、
  validator 状态。新 session 必须从这些文件恢复。
- 不要在 chat 里携带大段 source 或完整历史 artifact。把 compact state files
  当成记忆层。
```

## New Session Handoff Model

Most chat runtimes cannot let the model create a brand-new chat by prompt alone.
GitHub Copilot Chat should be treated this way unless your internal harness
adds a separate orchestration layer. The safe default is:

```text
The current session writes a handoff file and a copy-ready resume prompt. A
human or external runner opens the next session and pastes that prompt.
```

If the runtime has explicit thread, automation, or job orchestration tools, the
same checkpoint can be used by that runner to open the next session
automatically. Do not depend on this behavior unless it is actually available
in the deployed environment.

Recommended handoff file:

```text
batch-session-handoff.md
```

Recommended handoff content:

```markdown
# Batch Session Handoff

## Current Status

- Batch manifest: <path to batch-scan-manifest.yaml>
- Program list: <path to program-list.csv>
- Last completed program: <PROGRAM>
- Last validator status: pass / warning / failed
- Current blocker: <none or blocker>

## Next Action

- Next program: <PROGRAM>
- Next routines/windows: <SR441-SR445 or source windows>
- Required source reads:
  - <source path>:<line range>
- Required artifact updates:
  - routine-logic-details.md
  - routine-logic-details.yaml
  - program-analysis-summary.yaml
  - message-inventory.yaml
  - batch-scan-manifest.yaml

## Copy-Ready Resume Prompt

Use skill: legacy-ibmi-program-list-batch
Task: resume an interrupted program-list driven batch scan.

For each unfinished program row, use skill: legacy-ibmi-program-analyzer.

Resume from these durable files:
- Batch manifest: <path to batch-scan-manifest.yaml>
- Original program list: <path to program-list.csv>
- Source root: <path>
- Delivery working root: <path>
- Delivery remote-main snapshot: <path>
- Delivery profile: <path>

Rules:
- Do not rely on previous chat history.
- Trust only the durable files and validator results.
- Continue from the next unfinished row named in this handoff.
- Validate existing completed outputs before trusting them.
- Update the manifest after each program.
- If validation passes and this session can safely continue, proceed to the
  next bounded batch.
- If this session cannot safely continue, write a new batch-session-handoff.md.
```

Operational choices:

| Option | Use when | How it works |
| --- | --- | --- |
| Manual handoff | GitHub Copilot Chat or limited internal model UI. | Agent writes `batch-session-handoff.md`; human opens a new chat and pastes the copy-ready prompt. |
| External runner | Team has scripts, CI, or an internal harness. | Runner watches manifest/checkpoint files, starts the next job/session, and injects the resume prompt. |
| Native thread tool | Runtime explicitly supports creating or waking sessions. | Agent or runner opens the next thread using the runtime tool and passes the handoff prompt. |

The prompt should never claim it can open a new session unless the runtime has
a real tool for that action. Without such a tool, the correct behavior is to
leave a complete handoff packet that makes the next session mechanical.

## Copilot Chat-Only Operating Model

If the team can only use GitHub Copilot Chat, use a human-in-the-loop session
queue. The model cannot clear its own context, cannot open a new chat by
itself, and usually cannot run as a background batch worker. The reliable
pattern is:

```text
One program = one Copilot Chat session
One session prompt = one generated prompt file
Progress tracking = batch-scan-manifest.yaml
```

Recommended flow:

1. Generate a queue of per-program prompt files from `program-list.csv`.
2. Open a new Copilot Chat for the first prompt.
3. Paste only that program's prompt.
4. Let Copilot analyze the single program and write artifacts.
5. Run or ask Copilot to run the validator.
6. Update `batch-scan-manifest.yaml`.
7. Close or ignore that chat.
8. Open a fresh Copilot Chat for the next prompt.
9. Repeat until all rows are classified.
10. Generate or refresh `program-set-sme-core-review.md`.

Suggested queue layout:

```text
outputs/program-list-batch/
  program-batch-plan.md
  program-list-status.csv
  batch-scan-manifest.yaml
  prompt-queue/
    0001-@CC080.md
    0002-@CC081.md
    0003-@CC138T.md
  completed/
  blocked/
  failed/
```

Each prompt file should include only the current program and durable context
paths:

```text
Use skill: legacy-ibmi-program-analyzer
Task: analyze one IBM i program from a program-list batch.

Do not rely on previous chat history.
This is a fresh Copilot Chat session for one program only.

Program list: <path to program-list.csv>
Program batch plan: <path to program-batch-plan.md>
Program status list: <path to program-list-status.csv>
Batch manifest: <path to batch-scan-manifest.yaml>
Program: <member>
Source path: <source-root>/<path>
Language: <source_kind>
Initial size tier: <size_tier>
Intent: standalone_exploratory
Output directory: <delivery-root>/<tier-root>/<member>

Rules:
- Build deterministic indexes first.
- Analyze only this program.
- Do not import prior program source or prior chat summaries.
- Read at most 5 routine bodies per turn.
- Keep normal_program output lightweight unless density triggers appear.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Write required artifacts to the output directory.
- Run the program-analysis validator before marking complete.
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml with scanned, blocked, or failed status.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

Validation:
py -3 scripts\validate-program-analysis-contract.py `
  --analysis-dir <output directory>
```

Manual operator checklist for each Copilot Chat session:

- Confirm the prompt names exactly one program.
- Confirm the source path exists.
- Confirm the output directory is unique to that program.
- Confirm required artifacts were produced.
- Confirm validator status was recorded.
- Confirm `program-batch-plan.md`, `program-list-status.csv`, and
  `batch-scan-manifest.yaml` were updated before moving to the next prompt.

This is not fully automatic, but it preserves quality under a limited Copilot
Chat environment because each program starts with a clean chat context.

### Copilot Chat Concurrency Rule

Do not ask one Copilot Chat session to process multiple programs concurrently.
Copilot Chat does not provide reliable isolated workers inside one chat. A
single chat shares context, source snippets, plans, and file state across all
requested work, which makes evidence-heavy program analysis prone to drift.

Safe concurrency means separate chats, not concurrent tasks inside one chat:

```text
Operator A / Chat A -> @CC080
Operator B / Chat B -> @CC081
Operator C / Chat C -> @CC138T
```

Parallel Copilot Chat rules:

- One Copilot Chat session handles exactly one program at a time.
- Each parallel session must use a different prompt file.
- Each parallel session must write to a unique output directory.
- Before starting, mark the row as `in_progress` in `program-list-status.csv`
  and record `owner` / `session_id`.
- After finishing, record validator status before marking the row complete.
- Do not let two sessions edit the same program row or output folder.
- Merge statuses into `batch-scan-manifest.yaml` only after validation passes
  or a blocker/failure is clearly recorded.

If the team cannot coordinate row claiming safely, run programs serially.

## Program Batch Plan And Status List

Use three durable state files:

| File | Audience | Purpose |
| --- | --- | --- |
| `program-batch-plan.md` | Humans / operators / SMEs | Human-readable queue, next actions, current progress, and blockers. |
| `program-list-status.csv` | Excel / spreadsheet users | Working copy of the program list with status columns added. |
| `batch-scan-manifest.yaml` | Tools / validators / resume logic | Machine-readable execution state and audit record. |

Keep the original `program-list.csv` or source Excel export read-only when
possible. Create `program-list-status.csv` as a working copy with added status
columns. If the team must work directly in Excel, add the status columns to a
separate reviewed copy, not the original inventory export.

Recommended `program-list-status.csv` columns:

| Column | Meaning |
| --- | --- |
| `member` | Program/member name from the original list. |
| `object_type` | Original object type. |
| `source_kind` | Original source kind. |
| `path` | Original source path. |
| `total_lines` | Original line count. |
| `size_tier` | Initial tier from repo scan. |
| `tier_reason` | Initial tier reason from repo scan. |
| `batch_status` | Current row status. |
| `central_lookup_result` | `found_on_remote_main`, `not_found_on_remote_main`, or `remote_unavailable`. |
| `validator_status` | `not_run`, `pass`, `pass_with_warnings`, or `failed`. |
| `output_dir` | Per-program output folder. |
| `owner` | Person/session currently working the row. |
| `session_id` | Optional Copilot Chat/session identifier or manual label. |
| `started_at` | ISO timestamp when work started. |
| `completed_at` | ISO timestamp when work completed or blocked. |
| `last_error` | Short failure/blocker reason. |
| `next_action` | What the next session/operator should do. |
| `handoff_path` | Path to `batch-session-handoff.md` when needed. |

Allowed `batch_status` values:

| Status | Meaning |
| --- | --- |
| `queued` | Not started. |
| `in_progress` | Claimed by an operator/session. |
| `reused_remote_main` | Accepted central artifact was reused. |
| `completed` | Scan completed and validator passed. |
| `completed_with_warnings` | Required artifacts exist, with warnings or non-blocking TBDs. |
| `blocked_missing_source` | Source path cannot be resolved. |
| `blocked_remote_unavailable` | Remote-main lookup cannot be verified. |
| `failed_validator` | Validator failed. |
| `failed_runtime` | Runtime/tooling failed before valid output. |
| `skipped_not_program` | Row is not a program. |

Update rule:

```text
After every program, update program-batch-plan.md, program-list-status.csv, and
batch-scan-manifest.yaml before starting the next program.
```

Recommended `program-batch-plan.md` shape:

```markdown
# Program Batch Plan

## Batch

- Review name: <review name>
- Program list: <path to original program-list.csv>
- Status list: <path to program-list-status.csv>
- Manifest: <path to batch-scan-manifest.yaml>
- Delivery profile: <path to delivery-profile.yaml>
- Source root: <path>
- Delivery working root: <path>
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | <N> |
| in_progress | <N> |
| reused_remote_main | <N> |
| completed | <N> |
| completed_with_warnings | <N> |
| blocked | <N> |
| failed | <N> |

## Current / Next

- Current program: <PROGRAM or none>
- Current owner/session: <owner/session_id or none>
- Next program: <PROGRAM>
- Next prompt: <path to prompt-queue/000N-PROGRAM.md>
- Next action: <scan / validate / fix blocker / generate review>

## Program Queue

| # | Program | Source | Tier | Status | Validator | Owner | Output | Next action |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | @CC080 | HCCILERPG/@CC080.RPGLE | normal_program | completed | pass | leo | modules/.../@CC080 | none |
| 2 | @CC081 | HCCILERPG/@CC081.RPGLE | normal_program | queued | not_run |  |  | start scan |

## Blockers

| Program | Blocker | Needed to unblock |
| --- | --- | --- |
| <PROGRAM> | <reason> | <next evidence/action> |
```

Per-program prompt files should include the plan and status paths:

```text
Program batch plan: <path to program-batch-plan.md>
Program status list: <path to program-list-status.csv>
Batch manifest: <path to batch-scan-manifest.yaml>

After this program is validated or blocked, update all three files before
starting another program.
```

### English Resume Prompt

```text
Use skill: legacy-ibmi-program-list-batch
Task: resume an interrupted program-list driven batch scan.

For each unfinished program row, use skill: legacy-ibmi-program-analyzer.

Resume inputs:
- Batch manifest: <path to batch-scan-manifest.yaml>
- Original program list: <path to program-list.csv>
- Source root: <path to source repository root>
- Delivery working root: <path to delivery repo working checkout>
- Delivery remote-main snapshot: <path to verified remote-main snapshot>
- Delivery profile: <path to delivery-profile.yaml>
- Review name: <business-friendly review name>

Resume rules:
- Do not rely on previous chat history.
- Treat batch-scan-manifest.yaml as the durable execution state.
- Reconcile the manifest against the original program list.
- Validate existing completed program folders before trusting them.
- Do not rescan reused_remote_main programs.
- Do not rescan completed programs with validator_status = pass.
- Continue from the first row whose status is missing, in_progress,
  failed_runtime, failed_validator, or resolved blocker.
- For blocked_missing_source rows, retry only if source root or path has changed.
- For blocked_remote_unavailable rows, refresh the remote-main snapshot before
  continuing.
- Update the manifest after each program.
- When all rows are classified, rebuild or refresh the program-set SME review
  and run the program-set validator.

Final response:
- Report which rows were already complete.
- Report which rows were resumed.
- Report which rows remain blocked or failed.
- Report validator status.
- Provide paths to the updated manifest and program-set SME review.
```

### 中文恢复 Prompt

```text
使用 skill: legacy-ibmi-program-list-batch
任务: 恢复一个中断的 program-list 批量 scan。

对于每一个未完成的 program row，使用 skill: legacy-ibmi-program-analyzer。

恢复输入:
- Batch manifest: <batch-scan-manifest.yaml 路径>
- Original program list: <program-list.csv 路径>
- Source root: <source repo 根目录>
- Delivery working root: <delivery repo 工作分支 checkout 路径>
- Delivery remote-main snapshot: <已验证的 remote-main snapshot 路径>
- Delivery profile: <delivery-profile.yaml 路径>
- Review name: <业务可读的 review 名称>

恢复规则:
- 不要依赖上一段 chat history。
- 把 batch-scan-manifest.yaml 当成 durable execution state。
- 先把 manifest 和原始 program list 对齐检查。
- 已存在的 completed program folder 必须重新验证后才能信任。
- 不要重新扫描 reused_remote_main 的 program。
- 不要重新扫描 validator_status = pass 的 completed program。
- 从第一个 status 缺失、in_progress、failed_runtime、failed_validator、
  或 blocker 已解决的 row 继续。
- blocked_missing_source 只有在 source root 或 path 改过时才重试。
- blocked_remote_unavailable 必须先刷新 remote-main snapshot 再继续。
- 每完成一个 program 后立即更新 manifest。
- 所有 row 都分类完成后，重新生成或刷新 program-set SME review，并运行
  program-set validator。

最终回复:
- 报告哪些 rows 已经完成。
- 报告哪些 rows 本次恢复处理了。
- 报告哪些 rows 仍然 blocked 或 failed。
- 报告 validator 状态。
- 提供更新后的 manifest 和 program-set SME review 路径。
```

## Quality Checklist

Before marking the batch complete:

- Every requested program row is represented in the manifest.
- Every `object_type = program` row is classified as reused, scanned, skipped,
  failed, or blocked.
- Every scanned program has its own output folder.
- No output folder mixes multiple programs.
- Required per-program artifacts exist for each completed scan.
- `validate-program-analysis-contract.py` passed for every completed scan.
- `program-set-core-input-manifest.yaml` exists.
- `program-set-sme-core-review.md` exists.
- `validate-program-set-core-review.py` passed.
- Every unsupported business claim is removed, downgraded, or converted to
  `TBD-*`.
- Every unresolved message/status/code description is listed as a gap, TBD, or
  blocker.

The quality target is not "many Markdown files were generated." The quality
target is:

```text
Every program has traceable evidence, validator-checked artifacts, resumable
execution state, and one SME-readable batch review.
```
