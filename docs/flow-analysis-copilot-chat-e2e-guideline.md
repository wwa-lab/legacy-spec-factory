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
Reference paths, optional:
- /path/to/reference-pack.md
- /path/to/message-catalog.csv
Control files, optional:
- /path/to/status-code-table.csv
SME program flow:
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>
```

Save the SME program flow to a small `programs.txt` file before Phase 1, for
example:

```text
<PROGRAM-A> -> <PROGRAM-B> -> <PROGRAM-C>
```

or:

```text
<PROGRAM-A>
<PROGRAM-B>
<PROGRAM-C>
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

Windows path rendering warning:

- Keep Windows paths in code spans or fenced code blocks when reporting them.
- Markdown can render raw `\@` as `@`, hiding the separator before program names
  such as `@CU400P`.
- A planned output directory for an `@` program must keep the separator:
  `C:\sandbox\project\legacy-modernization-delivery\modules\CAP-ID-0003-normal_program\@CU400P`
- Treat this as wrong because the tier folder and program folder were
  concatenated:
  `C:\sandbox\project\legacy-modernization-delivery\modules\CAP-ID-0003-normal_program@CU400P`
- Build output paths by joining path components, not by string concatenation.

Company Windows/Cline environment:

- Use `scripts\invoke-windows-tool.ps1` for repository tools. The router tries
  `py -3`, then `python`, then the native Windows PowerShell implementation.
- Use `python3` only on macOS/Linux development machines.

Reference and control input rule:

- Pass reference packs, dictionaries, message catalogs, code tables, and
  control files into Phase 1 with `--reference-path` / `--control-file`.
- If none are available for the test, omit those arguments instead of passing
  placeholder values.
- The generated per-program prompts will carry those paths into each fresh
  Copilot Chat session.
- Treat reference/control inputs as supporting evidence for message meanings,
  status values, control-file lookups, field meanings, or validation rules.
  They do not replace source evidence or SME approval.

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

Use one Copilot Chat session for this phase. The goal is to create a durable
one-program-per-chat prompt queue; after this phase, the operator should copy
the generated `prompt-queue/*.md` files into fresh Copilot Chat sessions.

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
- Reference paths, optional:
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files, optional:
  - <CONTROL_FILE_OR_CODE_TABLE>

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
   legacy-ibmi-program-list-batch or equivalent manual queue files. Prefer the
   batch initializer so the operator can copy generated prompt files instead of
   hand-writing each program prompt.
8. When reporting planned output directories, wrap the full path in backticks
   and keep the separator before any program beginning with @.

Batch prompt generation command on Windows/Cline:

powershell -NoProfile -File scripts\invoke-windows-tool.ps1 `
  InitializeProgramBatch `
  --program-list <SOURCE_REPO>\outputs\repo-scan\program-list.csv `
  --programs-file <PROGRAMS_TXT_WITH_SME_FLOW> `
  --out-dir <DELIVERY_WORKING_CHECKOUT>\outputs\program-list-batch\<REVIEW_SLUG> `
  --source-root <SOURCE_REPO> `
  --delivery-root <DELIVERY_WORKING_CHECKOUT> `
  --reference-path <REFERENCE_PACK_OR_MESSAGE_CATALOG> `
  --control-file <CONTROL_FILE_OR_CODE_TABLE> `
  --review-name "<REVIEW_NAME>"

Omit `--reference-path` and `--control-file` when the run has no reference
pack or control file.

macOS/Linux:

python3 skills/legacy-ibmi-program-list-batch/scripts/initialize_program_batch.py \
  --program-list <SOURCE_REPO>/outputs/repo-scan/program-list.csv \
  --programs-file <PROGRAMS_TXT_WITH_SME_FLOW> \
  --out-dir <DELIVERY_WORKING_CHECKOUT>/outputs/program-list-batch/<REVIEW_SLUG> \
  --source-root <SOURCE_REPO> \
  --delivery-root <DELIVERY_WORKING_CHECKOUT> \
  --reference-path <REFERENCE_PACK_OR_MESSAGE_CATALOG> \
  --control-file <CONTROL_FILE_OR_CODE_TABLE> \
  --review-name "<REVIEW_NAME>"

Return:
- ordered SME flow
- distinct current-run program worklist
- source path and tier for each program
- source_inventory freshness/action
- output directory planned for each program
- reference/control paths carried into generated prompts
- prompt queue folder
- next prompt/file to copy for each program-analysis chat
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

Reference and control inputs:
- Reference paths:
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files:
  - <CONTROL_FILE_OR_CODE_TABLE>

Output directory:
`<PROGRAM_OUTPUT_DIR_IN_DELIVERY_WORKING_CHECKOUT>`

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
9. Read reference/control inputs when they are relevant to observed messages,
   status values, control-file lookups, field meanings, or validation rules.
   Treat them as supporting evidence only; do not invent behavior absent from
   source or SME-approved evidence.
10. Reject placeholder-only output. If evidence is genuinely unavailable, write
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

Program batch folder from Phase 1:
<DELIVERY_WORKING_CHECKOUT>/outputs/program-list-batch/<REVIEW_SLUG>/

The batch folder must contain:
- program-list-status.csv
- batch-scan-manifest.yaml
- program-batch-plan.md

Only if no batch folder exists, provide a manual fallback:
- <PROGRAM-A>: <PROGRAM_A_OUTPUT_DIR>
- <PROGRAM-B>: <PROGRAM_B_OUTPUT_DIR>
- <PROGRAM-C>: <PROGRAM_C_OUTPUT_DIR>

Reference and control inputs used during per-program analysis:
- Reference paths:
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files:
  - <CONTROL_FILE_OR_CODE_TABLE>

Instructions:
1. Read program-list-status.csv and batch-scan-manifest.yaml from the Phase 1
   program batch folder. Derive each current-run program artifact folder from
   the status row's output_dir. Do not ask the operator to paste one folder per
   program when the batch files are present.
2. Confirm every SME-provided program appears in the batch files and either has
   a completed/current-run artifact folder or a precise blocked/pending state.
3. Build or rebuild:
   modules/CAP-ID-0004-program_set_reviews/<REVIEW_SLUG>/
     program-set-core-input-manifest.yaml
     program-set-sme-core-review.md
4. Use the program-set builder with --program-first and --working-root only.
   Do not pass --delivery-root to the program-set builder.
5. Confirm manifest run_resolution values are only:
   analyzed_this_run, reused_same_run, pending_source, blocked_missing_source.
6. Confirm the manifest does not contain central_lookup_result,
   found_on_remote_main, force_rescan, or remote_main_artifact_root.
7. Fill program-set-sme-core-review.md from current-run compact artifacts.
   Prefer program-analysis-summary.yaml, source-index.yaml,
   message-inventory.yaml, routine-logic-details.yaml when required/present,
   and optional sidecars when needed.
8. Use program-analysis.md only for targeted clarification.
9. Keep the review self-contained. The SME must not need to open per-program
   docs to understand Calculation Logic, Validation Logic, Exception Handling,
   or Message Inventory.
10. Use reference/control inputs only to clarify message/status/control-table
   meanings already observed in current-run program artifacts. Do not add new
   behavior that is not backed by source evidence or SME approval.
11. Include evidence-backed rows or precise per-program TBD rows in all four
   core sections.
12. Keep rows grouped by SME flow order when possible.
13. Do not include Nodes, Edges, Replay, Persistence, Lineage, UI Surfaces,
   Capability Seeds, or SME Checklist.

Return:
- manifest path
- review path
- program batch folder used
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

Validation on Windows/Cline:
Run the repository router against:
- program-set-core-input-manifest.yaml
- program-set-sme-core-review.md

```powershell
powershell -NoProfile -File scripts\invoke-windows-tool.ps1 `
  ValidateProgramSetCoreReview `
  --manifest <program-set-core-input-manifest.yaml> `
  --review <program-set-sme-core-review.md>
```

On macOS/Linux, use `python3 scripts/validate-program-set-core-review.py`
with the same `--manifest` and `--review` arguments.

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

## 中文可复制 Prompts

下面是给 GitHub Copilot Chat 使用的中文版本。使用方式和英文版一致：

1. Phase 1 用一个 chat 建立 worklist 和 prompt queue。
2. Phase 2 每个 program 单独开一个 fresh chat。
3. Phase 3 用新的 chat 组装 `program-set-sme-core-review.md`。
4. Phase 4 用新的 chat 校验并准备 PR summary。

如果 Phase 1 已经生成 `prompt-queue/*.md`，Phase 2 优先复制对应的
prompt 文件；下面的 Phase 2 中文 prompt 只作为没有 prompt queue 时的
手工 fallback。

### 中文 Phase 0：可选 Delivery Profile 准备

只有团队还没有 delivery profile 时才使用这一段。

```text
/legacy-ibmi-flow-analyzer

如果这个 slash command 不可用，请按
skills/legacy-ibmi-flow-analyzer/SKILL.md 执行。

任务：
为 program-flow core review 测试准备一份 delivery profile。

输入：
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Review name: <REVIEW_NAME>

预期 delivery folder layout：
- modules/CAP-ID-0001-large_extreme_program
- modules/CAP-ID-0002-complex_normal_program
- modules/CAP-ID-0003-normal_program
- modules/CAP-ID-0004-program_set_reviews

执行规则：
1. 如果还没有 delivery profile，把
   skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml
   复制到团队配置路径。
2. 只更新本次测试需要的 repo/folder 值。
3. 除非团队明确配置 alias，否则必须保留 program 的精确身份。
   默认 profile 里 @CU118 和 CU118 是两个不同 program。
4. 本次 program-flow 测试不要配置 remote-main 或 prior-run reuse。

返回：
- delivery profile 路径
- normal、complex、large、program-set review 的输出根目录
- 仍需人工确认的值
```

### 中文 Phase 1：Flow Worklist 和 Inventory Preflight

用一个 Copilot Chat session 执行这一段。目标是生成持久的
one-program-per-chat prompt queue；不要在这个 chat 里分析 program body，
也不要生成 `program-set-sme-core-review.md`。

```text
/legacy-ibmi-flow-analyzer

如果这个 slash command 不可用，请按
skills/legacy-ibmi-flow-analyzer/SKILL.md 执行。

任务：
根据 SME 提供的 program flow 建立本次 current-run worklist。
不要在这个 chat 分析 program body。
不要在这个 chat 组装 program-set-sme-core-review.md。
不要检查 remote main、prior-run cache 或其他分析人员的 artifacts。

Runtime inputs：
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Delivery profile: <DELIVERY_PROFILE>
- Reference paths，可选：
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files，可选：
  - <CONTROL_FILE_OR_CODE_TABLE>

Review name：
<REVIEW_NAME>

SME 提供的 program flow，必须保留顺序：
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>

执行规则：
1. 把 SME list 当成有顺序的 program flow。
2. 只对本批次内完全相同的 normalized program name 去重。
3. 后续 assembly 必须保留原始 SME 顺序。
4. 检查 source inventory cache：
   <source-root>/outputs/repo-scan/program-list.csv
   <source-root>/outputs/repo-scan/scan-summary.yaml
5. 如果 cache 缺失、过期，或 source tree 是 dirty 状态，先运行一次
   repo-level legacy-ibmi-inventory，然后使用刷新后的 program-list.csv。
6. 确认每个 distinct program 的 source path 和 size tier：
   normal_program、complex_normal_program 或 large_extreme_program。
7. 使用 legacy-ibmi-program-list-batch 或等价方式准备
   one-program-per-chat queue。优先使用 batch initializer，让 operator 可以
   复制生成的 prompt 文件，而不是手写每个 program prompt。
8. 报告 planned output directory 时，完整路径必须放在反引号里；如果
   program 以 @ 开头，必须保留 tier folder 和 program folder 之间的路径分隔符。

Windows/Cline 批量生成 prompt 命令：

powershell -NoProfile -File scripts\invoke-windows-tool.ps1 `
  InitializeProgramBatch `
  --program-list <SOURCE_REPO>\outputs\repo-scan\program-list.csv `
  --programs-file <PROGRAMS_TXT_WITH_SME_FLOW> `
  --out-dir <DELIVERY_WORKING_CHECKOUT>\outputs\program-list-batch\<REVIEW_SLUG> `
  --source-root <SOURCE_REPO> `
  --delivery-root <DELIVERY_WORKING_CHECKOUT> `
  --reference-path <REFERENCE_PACK_OR_MESSAGE_CATALOG> `
  --control-file <CONTROL_FILE_OR_CODE_TABLE> `
  --review-name "<REVIEW_NAME>"

如果本次没有 reference pack 或 control file，请直接省略
--reference-path 和 --control-file，不要传 placeholder。

macOS/Linux：

python3 skills/legacy-ibmi-program-list-batch/scripts/initialize_program_batch.py \
  --program-list <SOURCE_REPO>/outputs/repo-scan/program-list.csv \
  --programs-file <PROGRAMS_TXT_WITH_SME_FLOW> \
  --out-dir <DELIVERY_WORKING_CHECKOUT>/outputs/program-list-batch/<REVIEW_SLUG> \
  --source-root <SOURCE_REPO> \
  --delivery-root <DELIVERY_WORKING_CHECKOUT> \
  --reference-path <REFERENCE_PACK_OR_MESSAGE_CATALOG> \
  --control-file <CONTROL_FILE_OR_CODE_TABLE> \
  --review-name "<REVIEW_NAME>"

返回：
- ordered SME flow
- distinct current-run program worklist
- 每个 program 的 source path 和 tier
- source_inventory freshness/action
- 每个 program 的 planned output directory
- 已带入 generated prompts 的 reference/control paths
- prompt queue folder
- 每个 program-analysis chat 下一步要复制的 prompt/file
```

### 中文 Phase 2：每个 Program 一个 Fresh Chat

每个 distinct program 都单独运行一次。每次都新开 Copilot Chat。

```text
/legacy-ibmi-program-analyzer

如果这个 slash command 不可用，请按
skills/legacy-ibmi-program-analyzer/SKILL.md 执行。

任务：
只分析本次 program-flow run 里的一个 IBM i program。

不要依赖之前的 chat history。
这是一个 fresh Copilot Chat session，只处理一个 program。
不要导入其他 program 的 source、之前 chat 的总结，或旧 delivery artifacts。

Program：
<PROGRAM>

Source path：
<SOURCE_PATH>

Language：
<SOURCE_KIND>

Initial size tier：
<SIZE_TIER>

Source repo：
<SOURCE_REPO>

Reference and control inputs：
- Reference paths：
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files：
  - <CONTROL_FILE_OR_CODE_TABLE>

Output directory：
`<PROGRAM_OUTPUT_DIR_IN_DELIVERY_WORKING_CHECKOUT>`

执行规则：
1. 先建立 deterministic indexes。
2. 只分析这个 program。
3. 如果 output directory 已经有这个 program 的旧 artifacts，用本次输出覆盖。
   不要因为旧 artifacts 存在就跳过。
4. 每一轮最多读取 5 个 routine body。
5. normal_program 保持轻量，除非触发 density / complexity 升级。
6. 对 normal_program，不要生成 routine-logic-details.md、
   routine-logic-details.yaml、deep-read-plan.md 或 batch deep-read files，
   除非 tier 被提升或明确要求 deep-read。
7. 只有 complex_normal_program、large_extreme_program 或明确 deep-read 时，
   才生成 routine-logic-details.md 和 routine-logic-details.yaml。
8. 不要把 indexed_only routines 当成已经确认的 business logic。
9. 当 observed messages、status values、control-file lookups、field
   meanings 或 validation rules 需要解释时，读取 reference/control inputs。
   它们只能作为 supporting evidence；不能凭 reference/control 输入发明
   source 或 SME-approved evidence 中不存在的行为。
10. 拒绝 placeholder-only 输出。如果证据确实不可用，必须写 precise TBD，
    包含已检查的 routine/window、缺失的 evidence type、next action。

必须输出：
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml

条件输出：
- routine-logic-details.md 和 routine-logic-details.yaml：只在
  complex_normal_program、large_extreme_program 或 explicit deep-read
  continuation 时输出。
- file-io-inventory.yaml、field-mutation-matrix.yaml、sql-inventory.yaml：
  只在观察到，或 flow claim 需要时输出。
- deep-read-plan.md、all-routine-coverage-ledger.md、
  routine-logic-details/deep-read-batch-*.md：
  只在 complex/large tier 或 retained batch evidence 触发时输出。

Validation：
标记完成前运行 program-analysis validator。

返回：
- output directory
- generated artifacts
- final size tier
- validator result
- 仍影响 Calculation Logic、Validation Logic、Exception Handling 或
  Message Inventory 的 indexed_only routines
- precise TBDs
```

### 中文 Phase 3：组装 Program-Set Review

所有 program chat 完成后，用新的 Copilot Chat 执行这一段。

```text
/legacy-ibmi-flow-analyzer

如果这个 slash command 不可用，请按
skills/legacy-ibmi-flow-analyzer/SKILL.md 执行。

任务：
只从 current-run program-analysis artifacts 组装一份完整、紧凑、可交给 SME
review 的 program-set core review。

不要创建 flow-<FLOW-SLUG>.md。
不要使用 remote main、prior-run cache 或旧 delivery artifacts。
不要从 placeholder-only 或 incomplete program-analysis artifacts 组装。

Runtime inputs：
- Delivery working checkout: <DELIVERY_WORKING_CHECKOUT>
- Delivery working branch: <DEVELOP_PERSON_BRANCH>
- Source repo: <SOURCE_REPO>
- Delivery profile: <DELIVERY_PROFILE>

Review name：
<REVIEW_NAME>

SME 提供的 program flow，必须保留顺序：
- <PROGRAM-A>
- <PROGRAM-B>
- <PROGRAM-C>

Phase 1 生成的 Program batch folder：
<DELIVERY_WORKING_CHECKOUT>/outputs/program-list-batch/<REVIEW_SLUG>/

这个 batch folder 必须包含：
- program-list-status.csv
- batch-scan-manifest.yaml
- program-batch-plan.md

只有没有 batch folder 时，才使用手工 fallback：
- <PROGRAM-A>: <PROGRAM_A_OUTPUT_DIR>
- <PROGRAM-B>: <PROGRAM_B_OUTPUT_DIR>
- <PROGRAM-C>: <PROGRAM_C_OUTPUT_DIR>

Per-program analysis 使用过的 reference/control inputs：
- Reference paths：
  - <REFERENCE_PACK_OR_MESSAGE_CATALOG>
- Control files：
  - <CONTROL_FILE_OR_CODE_TABLE>

执行规则：
1. 读取 Phase 1 program batch folder 里的 program-list-status.csv 和
   batch-scan-manifest.yaml。每个 current-run program artifact folder 从 status
   row 的 output_dir 推导。只要 batch files 存在，就不要要求 operator 为每个
   program 手动复制一个 folder。
2. 确认 SME 提供的每个 program 都出现在 batch files 里，并且有 completed
   current-run artifact folder，或有明确的 blocked/pending state。
3. Build 或 rebuild：
   modules/CAP-ID-0004-program_set_reviews/<REVIEW_SLUG>/
     program-set-core-input-manifest.yaml
     program-set-sme-core-review.md
4. 使用 program-set builder 时必须带 --program-first 和 --working-root。
   不要给 program-set builder 传 --delivery-root。
5. 确认 manifest 的 run_resolution 只能是：
   analyzed_this_run、reused_same_run、pending_source、blocked_missing_source。
6. 确认 manifest 不包含 central_lookup_result、found_on_remote_main、
   force_rescan 或 remote_main_artifact_root。
7. program-set-sme-core-review.md 必须从 current-run compact artifacts 填充。
   优先使用 program-analysis-summary.yaml、source-index.yaml、
   message-inventory.yaml、需要且存在时的 routine-logic-details.yaml，
   必要时再使用 optional sidecars。
8. program-analysis.md 只用于 targeted clarification。
9. review 必须 self-contained。SME 不应该为了理解 Calculation Logic、
   Validation Logic、Exception Handling 或 Message Inventory 再去打开每个
   per-program doc。
10. reference/control inputs 只能用于澄清 current-run program artifacts 中已经
   观察到的 message/status/control-table 含义。不要加入没有 source evidence
   或 SME approval 支撑的新行为。
11. 四个 core sections 都必须包含 evidence-backed rows，或 precise
    per-program TBD rows。
12. 尽量按 SME flow order 分组 rows。
13. 不要包含 Nodes、Edges、Replay、Persistence、Lineage、UI Surfaces、
    Capability Seeds 或 SME Checklist。

返回：
- manifest path
- review path
- 使用的 program batch folder
- 每个 program 的 run_resolution
- Core Completeness Ledger status
- remaining SME TBDs
```

### 中文 Phase 4：校验并准备 PR Summary

用最后一个 Copilot Chat session 执行这一段。

```text
/legacy-ibmi-flow-analyzer

如果这个 slash command 不可用，请按
skills/legacy-ibmi-flow-analyzer/SKILL.md 执行。

任务：
校验已经生成的 program-set SME core review，并准备 PR-ready summary。

Review folder：
<DELIVERY_WORKING_CHECKOUT>/modules/CAP-ID-0004-program_set_reviews/<REVIEW_SLUG>/

Validation：
对以下文件运行 scripts/validate-program-set-core-review.py：
- program-set-core-input-manifest.yaml
- program-set-sme-core-review.md

检查项：
1. manifest 里的每个 program 都出现在 Sources 和 Core Completeness Ledger。
2. Core Completeness Ledger 使用当前列：
   Routine Logic Evidence 和 Message Inventory。
3. manifest 使用 run_resolution，不使用 central_lookup_result。
4. review 只包含 compact SME core sections：
   Calculation Logic、Validation Logic、Exception Handling、Message Inventory。
5. review 不包含 Nodes、Edges、Replay、Persistence、Lineage、UI Surfaces、
   Capability Seeds 或 SME Checklist。
6. 四个 core sections 必须包含 evidence-backed rows，或 precise
   per-program TBD rows。

返回：
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
