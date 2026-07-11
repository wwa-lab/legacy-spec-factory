# Program-List Batch Scan Guideline

This guideline is for GitHub Copilot, Codex, Claude Code, OpenCode, or any
runtime that needs to execute Legacy Spec Factory analysis from a prepared
program list.

中文摘要: 这份文档用于按 `program-list.csv` 批量执行 IBM i program scan。
核心原则是外层按清单批量调度，内层仍然使用
`legacy-ibmi-program-analyzer` 一次分析一个 program。不要把多个 program
合并进同一个 `<PROGRAM>-program-analysis.md`。

Canonical skill entry: `legacy-ibmi-program-list-batch`.

Prompt-driven test plan:
[`program-list-batch-prompt-test-plan.md`](program-list-batch-prompt-test-plan.md).

## When To Use

Use this guideline when:

- You already have a program list from repo scan or inventory.
- The list contains columns such as `member`, `object_type`, `source_kind`,
  `path`, `total_lines`, `size_tier`, and `tier_reason`.
- You want to prepare one Copilot Chat prompt per program, scan each program
  independently, and produce durable per-program artifacts for later flow or
  module work.

Do not use this guideline when:

- You only need to analyze one program. Use
  `docs/sme-ibmi-program-analyzer-normal-guideline.md`,
  `docs/sme-ibmi-program-analyzer-complex-guideline.md`, or
  `docs/sme-ibmi-program-analyzer-large-guideline.md`.
- The source has not been redacted or approved for analysis.
- You need approved central artifact reuse from delivery remote `main`; use the
  flow/program-set guidance for that heavier workflow instead.

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
Program-set SME review is not part of this batch step. It is a downstream
`legacy-ibmi-flow-analyzer` step only after a specific flow/list or discovered
call-flow defines a meaningful program set.

For faster Cline batch scans, use the two-phase mode:

1. Initialize with `--scaffold-mode precreate --validation-mode deferred`.
   This creates the prompt queue, status files, manifest, and deterministic
   per-program scaffold artifacts up front.
2. If the runtime supports isolated workers, add `--subagent-mode prepare` and
   launch workers from `subagent-dispatch-plan.md`. Otherwise paste the
   generated prompt files into Cline/Copilot serially.
3. Each prompt starts from the existing scaffold and fills semantic
   reader-first details from source. Final validation is deferred until
   downstream use or handoff.

Deferred mode skips the expensive program-analysis validator inside each
per-program prompt and writes `batch_status=scanned_unvalidated` /
`validator_status=deferred` after the artifacts and scaffold guard are clean.
Run the validator later before any downstream flow review, BRD/spec
generation, SME signoff, or central delivery handoff. Use the default
`--validation-mode immediate` when every row must be validator-clean during the
scan.

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
- Output root: <path to generated per-program artifacts>
- Reference paths: <optional reference pack, dictionary, message catalog paths>
- Control files: <optional control file, code table, lookup file paths>
- Review name: <business-friendly review name>
- Intent: standalone_exploratory
- Output mode: Copilot Chat-only one-program prompt queue

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
- Do not check out or inspect a delivery remote-main snapshot in this mode.
- Include the provided reference paths and control file paths in every
  generated prompt-queue item because each program runs in a fresh Copilot Chat
  session.
- Read reference and control inputs when they are relevant to observed
  messages, statuses, control-file lookups, field meanings, or validation
  rules. Treat them as supporting evidence only.
- Run legacy-ibmi-program-analyzer for each queued program row.
- If the batch was initialized with `--scaffold-mode precreate`, treat the
  generated scaffold as phase-1 setup only. Start each prompt by reading the
  existing source index, routine index, and routine logic YAML, then fill the
  source-backed semantic detail.
- Treat deterministic indexes as pre-analysis scaffolds only. After index
  generation, read the source-index, routine-logic YAML, and source routine
  bodies; replace pending/thin scaffold content with source-backed semantic
  analysis before marking the row complete.
- Do not combine multiple programs into one <PROGRAM>-program-analysis.md.
- Each program must have its own output folder.
- Read at most 5 routine bodies per program-analysis turn.
- Keep normal_program output lightweight unless a density trigger appears:
  concise main-file content and no large-program-only sidecars by default, but
  still include reader-first Calculation / Validation / Exception overview and
  named theme subsections before each routine index.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Record skipped, scanned, failed, and blocked programs in a batch manifest.
- Continue from the next unprocessed row if interrupted or resumed.

Per-program required output:
- <PROGRAM>-program-analysis.md
- <PROGRAM>-source-index.yaml
- <PROGRAM>-program-analysis-summary.yaml
- <PROGRAM>-routine-index.md
- <PROGRAM>-message-inventory.yaml
- <PROGRAM>-routine-logic-details.md
- <PROGRAM>-routine-logic-details.yaml

Conditional per-program output:
- <PROGRAM>-deep-read-plan.md, <PROGRAM>-all-routine-coverage-ledger.md, and
  retained routine-logic-details/<PROGRAM>-deep-read-batch-*.md only when
  complex/large tier or explicit deep-read continuation triggers require them.

Batch required output:
- batch-scan-manifest.yaml
- skipped/scanned/failed summary
- program-batch-plan.md
- program-list-status.csv
- prompt-queue/*.md

Recommended initialization command:

```text
py -3 .agents\skills\legacy-ibmi-program-list-batch\scripts\initialize_program_batch.py --program-list outputs\repo-scan\program-list.csv --programs-file programs.txt --out-dir outputs\program-list-batch --source-root C:\path\to\source-repo --delivery-root C:\path\to\delivery-work --scaffold-mode precreate --validation-mode deferred --subagent-mode prepare --max-parallel-agents 4
```

After isolated sub-agents finish, merge their result JSON files:

```text
py -3 .agents\skills\legacy-ibmi-program-list-batch\scripts\merge_subagent_results.py --batch-dir outputs\program-list-batch
```

Output folder rules:
- normal_program outputs go under the configured normal_program tier root.
- complex_normal_program outputs go under the configured
  complex_normal_program tier root.
- large_extreme_program outputs go under the configured large_extreme_program
  tier root.

Quality gates:
- Do not mark a program complete only because files were generated.
- A program is complete only when required artifacts exist and the
  program-analysis validator passes.
- In fast deferred-validation scans, use `batch_status=scanned_unvalidated`
  and `validator_status=deferred` instead of `completed`; run final validation
  before downstream use.
- Do not mark a program complete if <PROGRAM>-program-analysis.md or
  <PROGRAM>-routine-logic-details.md still contains scaffold wording such as
  `Draft wrapper seed generated`, `pending semantic deep-read`,
  `pending semantic detail`, `placeholder`, `not-yet-deep-read`, or
  `not deep-read`.
- Validate each generated program-analysis artifact before marking that program
  complete.
- Do not mark the batch complete if required per-program artifacts are missing.
- Do not generate a repo-wide program-set SME review from this whole batch.
  Later use `legacy-ibmi-flow-analyzer` only for a selected flow/program set.
- Every non-trivial behavior claim must cite a source range, evidence ID,
  RLOG ID, runtime evidence, reference pack, or SME approval.
- indexed_only routines are inventory only, not confirmed behavior.
- Missing source, missing copybook, unresolved message description,
  unresolved dynamic call, or unsupported business meaning must become a TBD
  or blocker.
- Unresolved message/status/code descriptions must be listed as TBDs or
  blockers.
- The batch is complete only when every requested program is classified as
  completed, completed_with_warnings, scanned_unvalidated,
  skipped_not_program, blocked_missing_source, failed_validator, or
  failed_runtime. `scanned_unvalidated` closes the fast scan ledger only; it is
  not downstream-ready.

Retry / exit budget:
- Do not build an unbounded retry loop around Cline, model, network, tool, or
  validator failures.
- Cline may show its own bounded Auto-Retry cycle. If that visible cycle is
  exhausted, or the same transient error repeats, stop the current program and
  update durable batch state instead of starting a new ad hoc attempt.
- For Windows Python launch, run `py -3 ...` once. If the Python Launcher is
  unavailable, rerun the same command once with `python` replacing `py -3`. If
  Python starts and the script exits non-zero, treat it as the tool result.
- If model/network/tool execution fails before stable artifacts exist, set
  `batch_status=failed_runtime`, `validator_status=not_run`, record
  `last_error` such as
  `cline_auto_retry_exhausted: net::ERR_INCOMPLETE_CHUNKED_ENCODING`, and set
  `next_action` to resume the same program after the environment is stable.
- In deferred validation mode, do not run the validator inside the per-program
  prompt. Mark successful fast scans as `batch_status=scanned_unvalidated`,
  `validator_status=deferred`, with `next_action` pointing to final validation.
- If the program-analysis validator fails, perform at most one targeted repair
  pass for that program. If validation still fails, set
  `batch_status=failed_validator`, preserve the validator finding in
  `last_error`, and write a concrete `next_action`.

Validation commands:
- In the company Windows 11 Copilot/Cline environment, invoke the validator
  directly with `py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py`.
  If `py -3` is unavailable, rerun the same command with `python`. Do not use
  PowerShell, `.cmd`, `.ps1`, or `py ... || python ...`.
- For local macOS/Linux development, use `python3`.
- Do not install Python, create a virtual environment, or configure PATH.

Per-program validation:
py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py
  --analysis-dir <program-output-dir>

Final response:
- Report total programs requested.
- Report programs newly scanned.
- Report programs skipped or blocked.
- Report failed programs with reason.
- Report validator status.
- Provide paths to the batch manifest, status CSV, batch plan, prompt queue,
  and generated per-program artifact folders.
```

## 中文 Copilot Prompt

```text
使用 skill: legacy-ibmi-program-list-batch
任务: 按 program list 批量执行 program scan，并编排 Copilot Chat prompt queue。

如果目标是快速跑 Cline batch scan，初始化 queue 时使用
--validation-mode deferred。deferred 模式下，每个 program prompt 不在
Cline 内立即运行昂贵的 program-analysis validator；artifact 和 scaffold
检查干净后，写入 batch_status=scanned_unvalidated、
validator_status=deferred。后续真正用于 flow review、BRD/spec、SME signoff
或 central delivery handoff 前，再统一运行 final validation。

每处理一行 program 时，使用 skill: legacy-ibmi-program-analyzer
目的: 一次分析一个 IBM i program，并为每个 program 生成有 evidence 支撑的
独立分析产物。

输入:
- Program list: <program-list.csv 路径>
- Source root: <source repo 根目录>
- Output root: <每个 program 分析产物的输出根目录>
- Reference paths: <可选 reference pack、dictionary、message catalog 路径>
- Control files: <可选 control file、code table、lookup file 路径>
- Review name: <业务可读的 review 名称>
- Intent: standalone_exploratory
- Output mode: Copilot Chat-only one-program prompt queue

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
- 这个模式下不要 checkout 或检查 delivery remote-main snapshot。
- 把提供的 reference paths 和 control file paths 写入每一个
  prompt-queue item，因为每个 program 都会在新的 Copilot Chat session
  中独立运行。
- 当这些 reference/control inputs 和当前 program 观察到的 message、
  status、control-file lookup、field meaning 或 validation rule 有关时，
  读取它们作为 supporting evidence。
- 对每个 queued program row 执行 legacy-ibmi-program-analyzer。
- deterministic source index 只是 pre-analysis scaffold。index 生成后必须
  继续读取 source-index、routine-logic YAML 和 source routine bodies，把
  pending/thin scaffold 内容替换成有 source evidence 的 semantic analysis，
  然后才能把该 row 标记为 complete。
- 不要把多个 program 合并进同一个 <PROGRAM>-program-analysis.md。
- 每个 program 必须有自己的输出目录。
- 每一轮 program-analysis 最多读取 5 个 routine body。
- 如果是 normal_program，且没有密集度触发，保持轻量输出。
- 不要在输出中粘贴大段真实 source code。
- 不要把 indexed_only routines 当成 confirmed business logic。
- 在 batch manifest 中记录 skipped、scanned、failed、blocked 的 program。
- 如果执行中断或恢复，从下一个未处理的 program 继续。

每个 program 必须产出:
- <PROGRAM>-program-analysis.md
- <PROGRAM>-source-index.yaml
- <PROGRAM>-program-analysis-summary.yaml
- <PROGRAM>-routine-index.md
- <PROGRAM>-message-inventory.yaml
- <PROGRAM>-routine-logic-details.md
- <PROGRAM>-routine-logic-details.yaml

条件性产出:
- <PROGRAM>-deep-read-plan.md、<PROGRAM>-all-routine-coverage-ledger.md，以及
  保留的 routine-logic-details/<PROGRAM>-deep-read-batch-*.md 只在
  complex/large tier 或明确 deep-read continuation 触发时产出。

批量执行必须产出:
- batch-scan-manifest.yaml
- skipped/scanned/failed summary
- program-batch-plan.md
- program-list-status.csv
- prompt-queue/*.md

输出目录规则:
- normal_program 输出到配置里的 normal_program tier root。
- complex_normal_program 输出到配置里的 complex_normal_program tier root。
- large_extreme_program 输出到配置里的 large_extreme_program tier root。

质量门禁:
- 不要因为文件生成了，就把 program 标记为 complete。
- 只有 required artifacts 存在，并且 program-analysis validator 通过时，
  该 program 才算 complete。
- 快速 deferred-validation scan 使用 `batch_status=scanned_unvalidated` 和
  `validator_status=deferred`，不要伪装成 completed；后续真正使用前必须
  再运行 final validation。
- 如果 <PROGRAM>-program-analysis.md 或 <PROGRAM>-routine-logic-details.md
  仍包含 `Draft wrapper seed generated`、`pending semantic deep-read`、
  `pending semantic detail`、`placeholder`、`not-yet-deep-read` 或
  `not deep-read`，不要标记为 complete。
- 每个 program 生成后，先验证 program-analysis artifact，再标记该
  program complete。
- 如果缺少 required per-program artifacts，不要标记 batch complete。
- 不要从整个 repo-wide batch 直接生成 program-set SME review。后续只有在
  已经选定具体 flow/program set 时，才交给 `legacy-ibmi-flow-analyzer` 汇总。
- 每个非平凡 behavior claim 都必须引用 source range、evidence ID、
  RLOG ID、runtime evidence、reference pack 或 SME approval。
- indexed_only routines 只能表示已经索引，不能表示 confirmed behavior。
- 缺失 source、缺失 copybook、未解析 message description、未解析
  dynamic call、没有证据支持的 business meaning，都必须标记为 TBD 或
  blocker。
- 未解析的 message/status/code description 必须列为 TBD 或 blocker。
- 只有当每个请求的 program 都被分类为 completed、
  completed_with_warnings、scanned_unvalidated、skipped_not_program、
  blocked_missing_source、failed_validator 或 failed_runtime 时，batch 才算
  complete。`scanned_unvalidated` 只表示 fast scan ledger 可关闭，不表示
  downstream-ready。

重试 / 退出预算:
- 不要围绕 Cline、model、network、tool 或 validator 失败构造无限重试。
- Cline 可能会显示自己的有上限 Auto-Retry。这个可见重试周期用尽后，
  或同一个 transient error 重复出现时，停止当前 program，把失败写入
  durable batch state，不要重新发起新的临时尝试。
- Windows Python 启动只允许 `py -3 ...` 一次；只有 Python Launcher
  不可用时，才把同一条命令开头替换成 `python` 再执行一次。如果 Python
  已经启动但脚本返回 non-zero，把它当作 tool result。
- 如果 model/network/tool 失败导致稳定 artifacts 尚未生成，设置
  `batch_status=failed_runtime`、`validator_status=not_run`，在
  `last_error` 记录类似
  `cline_auto_retry_exhausted: net::ERR_INCOMPLETE_CHUNKED_ENCODING`，并在
  `next_action` 写明等 Cline/network 稳定后继续同一个 program。
- deferred validation 模式下，不在 per-program prompt 里运行 validator。
  成功快扫后写 `batch_status=scanned_unvalidated`、
  `validator_status=deferred`，并在 `next_action` 写明下游使用前运行 final
  validation。
- 如果 program-analysis validator 失败，同一个 program 最多做一次
  targeted repair。仍然失败时，设置 `batch_status=failed_validator`，
  在 `last_error` 保留 validator finding，并写清楚 `next_action`。

验证命令:
- 公司 Windows 11 Copilot/Cline 环境直接运行
  `py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py`。
  如果 `py -3` 不可用，再把命令开头替换成 `python` 单独执行。不要使用
  PowerShell、`.cmd`、`.ps1`，也不要拼接 `py ... || python ...`。
- macOS/Linux 本地开发可以使用 `python3`。
- 不要安装 Python、创建 virtual environment 或配置 PATH。

单个 program 验证:
py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py
  --analysis-dir <program-output-dir>

最终回复:
- 报告本次请求的 program 总数。
- 报告本次新扫描的 programs。
- 报告 skipped 或 blocked 的 programs。
- 报告 failed programs 及失败原因。
- 报告 validator 状态。
- 提供 batch manifest、status CSV、batch plan、prompt queue 和各个
  per-program artifact folder 的路径。
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
output_root: /path/to/generated-artifacts
reference_paths:
  - /path/to/reference-pack.md
  - /path/to/message-catalog.csv
control_files:
  - /path/to/status-code-table.csv
validation_mode: deferred
status: in_progress
programs:
  - member: "@CC080"
    object_type: program
    source_kind: RPGLE
    source_path: HCCILERPG/@CC080.RPGLE
    initial_size_tier: normal_program
    final_size_tier: normal_program
    scan_status: completed
    validator_status: pass
    output_dir: modules/CAP-ID-0003-normal_program/@CC080
    blockers: []
    warnings: []
  - member: "@CC080A"
    object_type: program
    source_kind: RPGLE
    source_path: HCCILERPG/@CC080A.RPGLE
    initial_size_tier: normal_program
    final_size_tier: normal_program
    scan_status: scanned_unvalidated
    validator_status: deferred
    output_dir: modules/CAP-ID-0003-normal_program/@CC080A
    blockers: []
    warnings:
      - final validator deferred until downstream use
  - member: "@CC081"
    object_type: program
    source_kind: RPGLE
    source_path: HCCILERPG/@CC081.RPGLE
    initial_size_tier: normal_program
    final_size_tier: null
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
| `completed` | Source scan finished and validator passed. |
| `completed_with_warnings` | Required artifacts exist, but review warnings or non-blocking TBDs remain. |
| `blocked_missing_source` | The source path could not be resolved. |
| `failed_validator` | Files were generated, but validation still failed after the allowed targeted repair pass. |
| `failed_runtime` | Tooling, Python runtime, Cline Auto-Retry exhaustion, model/network interruption, or edit/tool-call failure prevented a valid artifact. |
| `skipped_not_program` | Row was ignored because `object_type` was not `program`. |

## Resume After Interruption

If the batch is interrupted or a new chat/session must continue the work, do
not rely on conversation memory. Resume only from durable files.

Durable resume inputs:

- `batch-scan-manifest.yaml`
- Original `program-list.csv`
- Source root
- Output root
- Reference paths, if used by the batch
- Control files, if used by the batch
- Existing per-program output folders

Resume rules:

- Read `batch-scan-manifest.yaml` first.
- Reconcile the manifest against the original program list.
- Default resume starts from unfinished or failed rows.
- If an operator intentionally reruns a `completed` row, overwrite that
  program's generated analysis artifacts with the current skill output and
  rerun validation before keeping the row `completed`.
- Resume at the first row whose status is missing, `in_progress`,
  `failed_runtime`, `failed_validator`, or any blocker that has now been
  resolved.
- If a row is `blocked_missing_source`, retry only when the source path or
  source root has changed.
- If a row is `failed_runtime` because of Cline Auto-Retry exhaustion,
  Python-runtime unavailability, or a network/model/tool interruption, retry
  only after that environment issue is resolved. Do not keep the same row
  `in_progress` while launching fresh attempts.
- If a row is `failed_validator`, retry only after reviewing the validator
  output or making a deliberate targeted repair plan.
- If a program output folder exists but the manifest does not record it, do not
  treat it as authoritative cache. Rerun the selected program and overwrite the
  generated analysis artifacts.
- After all rows are classified, close the batch with the status CSV, manifest,
  and per-program artifact paths. Build a program-set review later only through
  `legacy-ibmi-flow-analyzer` when a specific flow/program set is selected.

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
  `batch-scan-manifest.yaml`, `<PROGRAM>-program-analysis-summary.yaml`,
  `<PROGRAM>-source-index.yaml`, `<PROGRAM>-routine-index.md`,
  `<PROGRAM>-message-inventory.yaml`, conditional
  `<PROGRAM>-routine-logic-details.yaml`, deep-read checkpoint files, and
  validator output.
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
    - <PROGRAM>-routine-logic-details.md / <PROGRAM>-routine-logic-details.yaml
      only when this is complex_normal_program, large_extreme_program, or
      explicit deep-read
    - <PROGRAM>-program-analysis-summary.yaml
    - <PROGRAM>-message-inventory.yaml
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
- If Cline/model/network/tool Auto-Retry is exhausted, stop advancing, update
  durable state with `failed_runtime`, and leave a concrete resume action.
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
  - <PROGRAM>-routine-logic-details.md / <PROGRAM>-routine-logic-details.yaml
    only when this is complex_normal_program, large_extreme_program, or
    explicit deep-read
  - <PROGRAM>-program-analysis-summary.yaml
  - <PROGRAM>-message-inventory.yaml
  - batch-scan-manifest.yaml

## Copy-Ready Resume Prompt

Use skill: legacy-ibmi-program-list-batch
Task: resume an interrupted program-list driven batch scan.

For each unfinished program row, use skill: legacy-ibmi-program-analyzer.

Resume from these durable files:
- Batch manifest: <path to batch-scan-manifest.yaml>
- Original program list: <path to program-list.csv>
- Source root: <path>
- Output root: <path>
- Reference paths:
  - <path to reference pack or message catalog>
- Control files:
  - <path to control file or code table>

Rules:
- Do not rely on previous chat history.
- Trust only the durable files and validator results.
- Continue from the next unfinished row named in this handoff.
- Do not skip a selected row only because its output directory already exists.
  When rerunning a row, overwrite that program's generated analysis artifacts
  with the current skill output.
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
10. Close the batch; defer any program-set review to a later flow-analyzer
    step with an explicit flow/list.

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

Reference and control inputs:
- Reference paths:
  - <path to reference pack or message catalog>
- Control files:
  - <path to control file or code table>

Rules:
- Build deterministic indexes first.
- Deterministic indexes are pre-analysis scaffolds only. The generated
  <PROGRAM>-program-analysis.md seed, source index, and routine sidecars are
  not final analysis until semantic deep-read replaces pending/thin content
  with source-backed reader-first detail.
- Do not stop after deterministic indexing. Read the generated
  <PROGRAM>-source-index.yaml, <PROGRAM>-routine-logic-details.yaml, and the
  source routine bodies; then fill <PROGRAM>-program-analysis.md and
  <PROGRAM>-routine-logic-details.md with the actual calculation, validation,
  exception, data movement, and outcome-trace details.
- Analyze only this program.
- Read the listed reference and control inputs when they are relevant to this
  program's observed messages, status values, control-file lookups, field
  meanings, or validation rules. Treat them as supporting evidence only.
- Do not import prior program source or prior chat summaries.
- Read at most 5 routine bodies per turn.
- Keep normal_program output lightweight unless density triggers appear:
  concise main-file content and no large-program-only sidecars by default, but
  still include reader-first Calculation / Validation / Exception overview and
  named theme subsections before each routine index.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.
- Every RLOG declared in <PROGRAM>-routine-logic-details.yaml must have
  reader-useful detail in both <PROGRAM>-program-analysis.md and
  <PROGRAM>-routine-logic-details.md before this row can be marked complete.
- Write required artifacts to the output directory.
- For fast batch scans, skip the program-analysis validator in this prompt and
  mark the row `scanned_unvalidated` / `deferred` after artifacts and scaffold
  checks are clean. For strict scans, run the validator before marking
  `completed`.
- Before writing `batch_status=completed`, open the generated
  <PROGRAM>-program-analysis.md and <PROGRAM>-routine-logic-details.md and
  confirm they do not contain scaffold language such as `Draft wrapper seed
  generated`, `pending semantic deep-read`, `pending semantic detail`,
  `placeholder`, `not-yet-deep-read`, or `not deep-read`.
- Update program-batch-plan.md, program-list-status.csv, and
  batch-scan-manifest.yaml with scanned, blocked, or failed status.

Required output:
- <PROGRAM>-program-analysis.md
- <PROGRAM>-source-index.yaml
- <PROGRAM>-program-analysis-summary.yaml
- <PROGRAM>-routine-index.md
- <PROGRAM>-message-inventory.yaml
- <PROGRAM>-routine-logic-details.md
- <PROGRAM>-routine-logic-details.yaml

Conditional output:
- <PROGRAM>-deep-read-plan.md, <PROGRAM>-all-routine-coverage-ledger.md, and
  retained routine-logic-details/<PROGRAM>-deep-read-batch-*.md only for
  complex_normal_program, large_extreme_program, or explicit deep-read
  continuation.

Validation on Windows/Cline:
Fast deferred-validation batch prompt: do not run now. Run later before
downstream use:

py -3 .agents\skills\legacy-ibmi-program-analyzer\scripts\validate_program_analysis_contract.py
  --analysis-dir <output directory>

Validation on macOS/Linux:
python3 scripts/validate-program-analysis-contract.py \
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

This is not fully automatic in a limited Copilot Chat environment, but it
preserves quality because each program starts with a clean chat context.

### Sub-Agent Parallel Mode

When the runtime supports isolated workers, initialize with
`--subagent-mode prepare`. The initializer writes:

- `subagent-dispatch-plan.md`
- `subagent-queue/*.md`
- `subagent-results/`

Launch rules:

- Start at most the configured `--max-parallel-agents` workers at a time.
- Give each worker exactly one file from `subagent-queue/`.
- Do not assign the same prompt file twice.
- Each worker writes only its program output directory and its own result JSON.
- Workers do not edit `program-list-status.csv`, `program-batch-plan.md`, or
  `batch-scan-manifest.yaml` directly.
- After workers finish, run `merge_subagent_results.py --batch-dir <batch-dir>`
  and then run the batch status validator.

This mode is the preferred way to parallelize in Codex/Claude/OpenCode-style
agent runtimes because it avoids multiple workers racing on the same CSV and
manifest files.

### Copilot Chat Concurrency Rule

Do not ask one Copilot Chat session to process multiple programs concurrently.
Copilot Chat does not provide reliable isolated workers inside one chat. A
single chat shares context, source snippets, plans, and file state across all
requested work, which makes evidence-heavy program analysis prone to drift.

Safe concurrency means separate chats or isolated sub-agents, not concurrent
tasks inside one chat:

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
For agent runtimes, prefer the generated `subagent-queue` + result JSON merge
pattern over manual row claiming.

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
| `validator_status` | `not_run`, `deferred`, `pass`, `pass_with_warnings`, or `failed`. |
| `output_dir` | Per-program output folder. |
| `subagent_prompt_path` | Optional sub-agent-safe prompt path. |
| `subagent_result_path` | Optional result JSON path for parallel worker output. |
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
| `completed` | Scan completed and validator passed. |
| `completed_with_warnings` | Required artifacts exist, with warnings or non-blocking TBDs. |
| `scanned_unvalidated` | Fast scan artifacts exist, but final validator is deferred. |
| `blocked_missing_source` | Source path cannot be resolved. |
| `failed_validator` | Validator failed after the allowed targeted repair pass. |
| `failed_runtime` | Runtime/tooling, Python availability, Cline Auto-Retry, or model/network/tool-call failure prevented valid output. |
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
- Source root: <path>
- Output root: <path>
- Reference paths: <paths or none>
- Control files: <paths or none>
- Mode: Copilot Chat-only / one program per chat

## Progress

| Status | Count |
| --- | ---: |
| queued | <N> |
| in_progress | <N> |
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
Reference paths: <paths or none>
Control files: <paths or none>

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
- Output root: <path to generated per-program artifacts>
- Reference paths:
  - <path to reference pack or message catalog>
- Control files:
  - <path to control file or code table>
- Review name: <business-friendly review name>

Resume rules:
- Do not rely on previous chat history.
- Treat batch-scan-manifest.yaml as the durable execution state.
- Reconcile the manifest against the original program list.
- Default resume starts from unfinished or failed rows.
- If rerunning a completed row, overwrite that program's generated analysis
  artifacts with the current skill output and rerun validation.
- Continue from the first row whose status is missing, in_progress,
  failed_runtime, failed_validator, or resolved blocker.
- For blocked_missing_source rows, retry only if source root or path has changed.
- Update the manifest after each program.
- When all rows are classified, close the scan batch. Do not rebuild or refresh
  a program-set SME review in this resume step.

Final response:
- Report which rows were already complete.
- Report which rows were resumed.
- Report which rows remain blocked or failed.
- Report validator status.
- Provide paths to the updated manifest, status CSV, batch plan, and
  per-program artifact folders.
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
- Output root: <每个 program 分析产物的输出根目录>
- Reference paths:
  - <reference pack 或 message catalog 路径>
- Control files:
  - <control file 或 code table 路径>
- Review name: <业务可读的 review 名称>

恢复规则:
- 不要依赖上一段 chat history。
- 把 batch-scan-manifest.yaml 当成 durable execution state。
- 先把 manifest 和原始 program list 对齐检查。
- 默认从未完成或失败的 row 继续。
- 如果选择重跑 completed row，用当前 skill 输出覆盖该 program 的生成分析产物，
  并重新运行 validator 后才能继续标记为 completed。
- 从第一个 status 缺失、in_progress、failed_runtime、failed_validator、
  或 blocker 已解决的 row 继续。
- blocked_missing_source 只有在 source root 或 path 改过时才重试。
- 每完成一个 program 后立即更新 manifest。
- 所有 row 都分类完成后，关闭本次 scan batch。不要在恢复步骤里生成或刷新
  program-set SME review。

最终回复:
- 报告哪些 rows 已经完成。
- 报告哪些 rows 本次恢复处理了。
- 报告哪些 rows 仍然 blocked 或 failed。
- 报告 validator 状态。
- 提供更新后的 manifest、status CSV、batch plan 和 per-program artifact
  folders 路径。
```

## Quality Checklist

Before marking the batch complete:

- Every requested program row is represented in the manifest.
- Every `object_type = program` row is classified as scanned, skipped, failed,
  or blocked.
- Every scanned program has its own output folder.
- No output folder mixes multiple programs.
- Required per-program artifacts exist for each completed scan.
- `validate-program-analysis-contract.py` passed for every completed scan.
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
