# SME Guideline: Large / Extreme Program Code Scan

This guideline is for SMEs and analysts running `legacy-ibmi-program-analyzer`
against a `large_extreme_program`. A large/extreme program is over 10,000
lines, has very high routine/object density, or cannot be safely reviewed in
one context.

中文说明: 这份手册适用于超大 IBM i program。目标是用自动分批方式完成 code
scan，每轮最多 5 个 routine/window，并保留
`routine-logic-details/deep-read-batch-xxx.md` 检查点。

## When To Use

Use this guideline when:

- Source is over 10,000 lines.
- The program has more than 25 routines, many object dependencies, or many
  external calls.
- One context cannot safely hold the source and analysis.
- SME needs a retained batch-by-batch audit trail.
- The program is needed for downstream flow/module/BRD/spec work.

## Required Input Package

Prepare these files before starting:

- Source member path.
- Program name and object ID, if available.
- Copybooks/includes and externally referenced definitions.
- Message file, message catalog, reference pack, or SME-approved message
  descriptions.
- Inventory/object evidence when `chain_ready` is requested.
- Known entry point, trigger model, transaction path, or SME question.
- Runtime evidence or sample transactions, if available and redacted.

Missing message descriptions, copybooks, or external program semantics do not
prevent draft scanning, but they block final-ready / chain-ready status.

## E2E Steps

### Step 1: Start Large Program Index

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a large_extreme_program index pass.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <analysis output directory>

SME question:
<question>

Rules:
- Do not paste or re-read the full source in one turn.
- Build deterministic indexes first.
- Classify the program as large_extreme_program when thresholds are met.
- Prepare a deep-read plan with windows of at most 5 routines.
- Generate retained batch checkpoint structure under routine-logic-details/.
- Do not mark chain_ready during initial indexing.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
- deep-read-plan.md
- all-routine-coverage-ledger.md
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 large_extreme_program index pass。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <analysis 输出目录>

SME 这次关心的问题:
<问题>

规则:
- 不要在一轮里粘贴或重读完整 source。
- 先建立确定性的 indexes。
- 达到阈值时，分类为 large_extreme_program。
- 准备 deep-read plan，每个 window 最多 5 个 routines。
- 在 routine-logic-details/ 下准备保留式 batch checkpoint structure。
- 初始 index 阶段不要标记 chain_ready。

必须产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
- deep-read-plan.md
- all-routine-coverage-ledger.md
```

Output Checkpoint:

- `source-index.yaml` exists and marks `large_extreme_program`.
- `deep-read-plan.md` exists and uses batches/windows of at most five routines.
- `all-routine-coverage-ledger.md` exists.
- `program-analysis.md` exists as a summary wrapper, not a full analysis dump.
- Missing copybooks, external semantics, or message catalogs are listed as
  blockers or TBDs.

### Step 2: Run Deep-Read Batch 001

English Prompt:

```text
Run large_extreme_program deep-read batch 001.

Program: <PROGRAM_NAME>
Use existing artifacts:
- source-index.yaml: <path>
- deep-read-plan.md: <path>
- all-routine-coverage-ledger.md: <path>
- routine-logic-details.yaml: <path>
- message-inventory.yaml: <path>
- source file: <path>

Analyze at most 5 routine/window bodies.
Prioritize entry/dispatch, validation, calculation, persistence, exception,
message/status, SQL, and external-call boundary routines.

Create:
- routine-logic-details/deep-read-batch-001.md

Update:
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- all-routine-coverage-ledger.md
- message-inventory.yaml
- triggered file I/O, field mutation, and SQL sidecars

Do not paste real source-code snippets in the batch core logic sections.
Use source ranges, evidence IDs, and RLOG-* links instead.
```

中文 Prompt:

```text
请执行 large_extreme_program deep-read batch 001。

Program: <PROGRAM_NAME>
使用已有 artifacts:
- source-index.yaml: <路径>
- deep-read-plan.md: <路径>
- all-routine-coverage-ledger.md: <路径>
- routine-logic-details.yaml: <路径>
- message-inventory.yaml: <路径>
- source file: <路径>

本轮最多分析 5 个 routine/window body。
优先 entry / dispatch、validation、calculation、persistence、exception、
message/status、SQL、external-call boundary routines。

创建:
- routine-logic-details/deep-read-batch-001.md

更新:
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- all-routine-coverage-ledger.md
- message-inventory.yaml
- 已触发的 file I/O、field mutation、SQL sidecars

batch 核心逻辑章节不要粘贴真实 source-code snippets。
请使用 source ranges、evidence IDs、RLOG-* links。
```

Output Checkpoint:

- `routine-logic-details/deep-read-batch-001.md` exists.
- The batch file uses top-level sections:
  Calculation Logic, Validation Logic, Exception Handling, Scope,
  Batch Coverage Summary, Message Inventory, Routine Details.
- Batch core logic sections contain no pasted source-code snippets.
- Batch 001 records actual source line ranges read.
- Only routines/windows read in this batch move to `deep_read`.

### Step 3: Continue Automatic Batches

English Prompt:

```text
Continue large_extreme_program automatic deep-read batches.

Program: <PROGRAM_NAME>
Previous batch: <deep-read-batch-xxx.md>
Use:
- deep-read-plan.md
- all-routine-coverage-ledger.md
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- message-inventory.yaml
- triggered sidecars
- source file

Process the next batch of at most 5 routine/window bodies.
Continue until no processable deep-read window remains or a blocker prevents
safe progress.

For each batch:
- create routine-logic-details/deep-read-batch-xxx.md
- use the required batch layout
- record source line ranges read
- update compact artifacts incrementally
- list gaps closed
- list blockers retained
- list next batch candidates
- do not mark chain_ready
```

中文 Prompt:

```text
请继续 large_extreme_program automatic deep-read batches。

Program: <PROGRAM_NAME>
上一轮 batch: <deep-read-batch-xxx.md>
使用:
- deep-read-plan.md
- all-routine-coverage-ledger.md
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- message-inventory.yaml
- 已触发的 sidecars
- source file

处理下一轮最多 5 个 routine/window body。
一直继续，直到没有可处理的 deep-read window，或遇到阻止安全推进的 blocker。

每个 batch 都要:
- 创建 routine-logic-details/deep-read-batch-xxx.md
- 使用必需的 batch layout
- 记录本轮读取的 source line ranges
- 增量更新 compact artifacts
- 列出关闭的 gaps
- 列出保留的 blockers
- 列出下一轮 batch candidates
- 不要标记 chain_ready
```

Output Checkpoint:

- Batch numbers are sequential.
- Each batch covers at most five routines/windows.
- Every batch has the same required layout.
- `all-routine-coverage-ledger.md` matches actual processed batches.
- No previously reviewed SME notes or TBDs are deleted without explanation.
- The process stops only for completion, missing source lines, missing
  external evidence, validation failure, or context limit.

### Step 4: Validate Messages And Sidecars

English Prompt:

```text
Validate large_extreme_program messages and sidecars.

Use:
- message-inventory.yaml
- message-inventory.md
- file-io-inventory.yaml, if present
- field-mutation-matrix.yaml, if present
- sql-inventory.yaml, if present
- all deep-read-batch files

Confirm:
- every observed message/status/code has a description source or unresolved
  blocker
- file I/O sidecar covers state-changing operations
- field mutation sidecar covers persisted field changes and carriers
- SQL sidecar covers embedded SQL, host variables, SQLCODE, and SQLSTATE
- sidecars cite RLOG IDs, source ranges, or evidence IDs
```

中文 Prompt:

```text
请验证 large_extreme_program 的 messages 和 sidecars。

使用:
- message-inventory.yaml
- message-inventory.md
- file-io-inventory.yaml，如果存在
- field-mutation-matrix.yaml，如果存在
- sql-inventory.yaml，如果存在
- 所有 deep-read-batch files

请确认:
- 每个 observed message/status/code 都有 description source，或明确的
  unresolved blocker
- file I/O sidecar 覆盖 state-changing operations
- field mutation sidecar 覆盖 persisted field changes 和 carriers
- SQL sidecar 覆盖 embedded SQL、host variables、SQLCODE、SQLSTATE
- sidecars 引用 RLOG IDs、source ranges 或 evidence IDs
```

Output Checkpoint:

- No ID-only message inventory is treated as meaningful SME review.
- Unresolved message descriptions block final-ready / chain-ready.
- Sidecars agree on routine IDs, files/tables, fields, and message IDs.
- Every state-changing claim has evidence or is marked unsafe.

### Step 5: Consolidate Program Review

English Prompt:

```text
Consolidate large_extreme_program review.

Use:
- program-analysis.md
- program-analysis-summary.yaml
- routine-logic-details.md
- routine-logic-details.yaml
- all deep-read-batch files
- all-routine-coverage-ledger.md
- message-inventory.yaml
- triggered sidecars

Update program-analysis.md as the reader-first final wrapper.
Do not paste raw source snippets, but do merge completed RLOG semantic detail
into the main file so SMEs can understand the program without opening sidecar
links. Sidecars remain audit/checkpoint sources.

Show:
- Program Reading Summary
- confirmed calculation logic
- confirmed validation logic
- confirmed exception handling
- confirmed messages
- Routine Index For Calculation Logic / Validation Logic / Exception Handling,
  each covering every RLOG in routine-logic-details.yaml
- Routine Logic Details headings for every RLOG, continuous and ordered
- confirmed file I/O / SQL behavior
- external calls and unresolved handoffs
- precise indexed_only or blocked routines, if any
- final SME questions
```

中文 Prompt:

```text
请整合 large_extreme_program review。

使用:
- program-analysis.md
- program-analysis-summary.yaml
- routine-logic-details.md
- routine-logic-details.yaml
- 所有 deep-read-batch files
- all-routine-coverage-ledger.md
- message-inventory.yaml
- 已触发的 sidecars

请把 program-analysis.md 更新成 reader-first final wrapper。
不要粘贴 raw source snippets，但必须把已完成的 RLOG 语义明细合并到主文件，
让 SME 不用打开 sidecar links 也能理解 program。sidecars 只作为 audit/checkpoint 来源。

请展示:
- Program Reading Summary
- 已确认的 calculation logic
- 已确认的 validation logic
- 已确认的 exception handling
- 已确认的 messages
- Routine Index For Calculation Logic / Validation Logic / Exception Handling，
  每个都覆盖 routine-logic-details.yaml 里的全部 RLOG
- Routine Logic Details headings 覆盖全部 RLOG，编号连续有序
- 已确认的 file I/O / SQL behavior
- external calls 和 unresolved handoffs
- 精确的 indexed_only 或 blocked routines（如仍存在）
- final SME questions
```

Output Checkpoint:

- `program-analysis.md` starts with Program Reading Summary and follows the
  required H2 order.
- Calculation / Validation / Exception routine indexes each cover every RLOG.
- Routine Logic Details in the main file have the same RLOG count/order as
  `routine-logic-details.yaml`.
- Batch details remain in `routine-logic-details/deep-read-batch-*.md` as
  audit checkpoints.
- `program-analysis-summary.yaml` lists only precise downstream-readiness gaps.
- SME can review the program without opening sidecars or full source.

### Step 6: Final Large Program Readiness

English Prompt:

```text
Prepare final readiness for large_extreme_program.

Use all program artifacts and decide one status:
- draft_exploratory
- final_ready
- blocked
- not_chain_ready

Do not mark chain_ready unless:
- required inventory/object IDs are present
- critical routines for downstream claims are deep_read
- message descriptions are resolved
- copybooks/includes required for claims are available
- external program semantics are either evidenced or explicitly waived by SME

List:
- completed batches
- routines/windows still indexed_only, only if coverage/source-index still
  marks them that way
- blockers using precise gap types such as helper contract semantics, message
  catalog semantics, copybook/DS definitions, or inventory/source linkage
- unresolved SME questions
- evidence needed before chain_ready
- confirmation that `program-analysis.md`, message inventory, and validation
  warnings are synchronized
```

中文 Prompt:

```text
请准备 large_extreme_program final readiness。

使用所有 program artifacts，并选择一个状态:
- draft_exploratory
- final_ready
- blocked
- not_chain_ready

除非满足以下条件，否则不要标记 chain_ready:
- 必需的 inventory/object IDs 已存在
- downstream claims 依赖的 critical routines 已 deep_read
- message descriptions 已解决
- 支持 claims 所需的 copybooks/includes 已提供
- external program semantics 有证据，或 SME 明确批准 waiver

请列出:
- 已完成的 batches
- 仍然 indexed_only 的 routines/windows（仅当 coverage/source-index 当前仍如此）
- blockers，使用精确 gap 类型，例如 helper contract semantics、
  message catalog semantics、copybook/DS definitions、inventory/source linkage
- unresolved SME questions
- chain_ready 之前还需要哪些 evidence
- 确认 program-analysis.md、message inventory、validation warnings 已同步
```

Output Checkpoint:

- Final status is explicit.
- `chain_ready` is not used as a default for large scans.
- Remaining blockers are precise and assigned to SME, message catalog,
  copybook/DS, helper contract, external program evidence, runtime evidence, or
  inventory/source linkage.
- The package is reviewable from `program-analysis.md` without reading sidecars
  or the full source member.
