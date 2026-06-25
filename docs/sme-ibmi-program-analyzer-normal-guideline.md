# SME Guideline: Normal Program Code Scan

This guideline is for SMEs and analysts running `legacy-ibmi-program-analyzer`
against a `normal_program`. A normal program is usually under 10,000 lines and
has no dense routine, SQL, file I/O, message, mutation, or external-call
trigger.

中文说明: 这份手册适用于普通 IBM i program code scan。目标是让 SME 用最少
轮次看到 calculation logic、validation logic、exception handling、
message inventory、file I/O / SQL，以及明确的 TBD。

## When To Use

Use this guideline when:

- The source is under 10,000 lines.
- The first scan does not show high routine density or many state-changing
  operations.
- SME needs a focused review of one program.
- The output does not need multiple retained deep-read batches.

Do not use this guideline if the program is over 10,000 lines or needs repeated
five-routine batches. Use the complex or large guideline instead.

## Required Input Package

Prepare these files before starting:

- Source member path, such as RPGLE, SQLRPGLE, CLLE, or COBOL.
- Program name and object ID, if available.
- Copybooks/includes, if the source references them.
- Message file, message catalog, reference pack, or SME-approved message
  descriptions when message/status/code values may appear.
- Inventory/object evidence when `chain_ready` is requested.
- SME business question or review scope.

If message IDs are present but no message description source is supplied, the
run may be useful as a draft but must not be final-ready.

## E2E Steps

### Step 1: Start Normal Program Scan

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a normal_program code scan.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: <standalone_exploratory | chain_ready>
Output directory: <analysis output directory>

SME question:
<question>

Rules:
- Build deterministic indexes first.
- Classify the program tier.
- Read at most 5 routine bodies in this turn.
- Keep the output lightweight if no density trigger appears.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed business logic.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml

Do not create `routine-logic-details.md`, `routine-logic-details.yaml`,
`deep-read-plan.md`, or retained batch files for a normal program unless a
density trigger promotes the row to `complex_normal_program` /
`large_extreme_program` or the SME explicitly asks for deep-read continuation.
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 normal_program code scan。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: <standalone_exploratory | chain_ready>
Output directory: <analysis 输出目录>

SME 这次关心的问题:
<问题>

规则:
- 先建立确定性的 indexes。
- 判断 program tier。
- 本轮最多读取 5 个 routine body。
- 如果没有密集度触发，保持轻量输出。
- 输出中不要粘贴大段真实 source code。
- 不要把 indexed_only routines 当成 confirmed business logic。

必须产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- message-inventory.yaml

普通程序默认不要创建 `routine-logic-details.md`、
`routine-logic-details.yaml`、`deep-read-plan.md` 或 retained batch files；
只有密集度触发升级到 `complex_normal_program` / `large_extreme_program`，或
SME 明确要求继续 deep-read 时才创建。
```

Output Checkpoint:

- `program-analysis.md` exists.
- `source-index.yaml` exists and records `normal_program` unless a trigger
  changes the tier.
- `program-analysis-summary.yaml` exists.
- `routine-index.md` exists.
- `routine-logic-details.md` and `routine-logic-details.yaml` are absent for
  lightweight `normal_program`, unless a density trigger or explicit deep-read
  continuation is recorded.
- `message-inventory.yaml` exists, even if no messages are observed.
- No full source body is copied into the analysis output.

### Step 2: Check The Main Review Layout

English Prompt:

```text
Check the normal_program output layout.

Review these files:
- program-analysis.md
- program-analysis-summary.yaml
- message-inventory.yaml

Confirm that program-analysis.md is concise and uses a stable SME review
layout with:
- Program Overview
- Calculation Logic
- Validation Logic
- Exception Handling
- Message Inventory
- File I/O and SQL
- External Calls and Handoffs
- Evidence Coverage
- Open TBDs and SME Questions

List any missing section, duplicated section, or unsupported business claim.
```

中文 Prompt:

```text
请检查 normal_program 输出 layout。

检查这些文件:
- program-analysis.md
- program-analysis-summary.yaml
- message-inventory.yaml

确认 program-analysis.md 简洁，并使用稳定的 SME review layout:
- Program Overview
- Calculation Logic
- Validation Logic
- Exception Handling
- Message Inventory
- File I/O and SQL
- External Calls and Handoffs
- Evidence Coverage
- Open TBDs and SME Questions

请列出缺失章节、重复章节、以及没有证据支持的 business claim。
```

Output Checkpoint:

- The main review is readable on the first screen by an SME.
- Calculation, validation, exception, message, and file I/O / SQL sections are
  present, even when they say no evidence observed.
- Claims cite source ranges, evidence IDs, routine IDs, runtime evidence, or
  SME approval.
- `indexed_only` routines are not used as confirmed behavior.

### Step 3: Deep-Read The Top Routines If Needed

English Prompt:

```text
Continue legacy-ibmi-program-analyzer for normal_program deep-read.

Program: <PROGRAM_NAME>
Use existing artifacts:
- source-index.yaml: <path>
- routine-index.md: <path>
- routine-logic-details.yaml: <path>
- message-inventory.yaml: <path>

Read at most 5 routine bodies.
Prioritize entry, validation, calculation, persistence, exception, and
message/status routines.

Update:
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- program-analysis.md summary sections only
- message-inventory.yaml if messages/status/code values are found
```

中文 Prompt:

```text
请继续使用 legacy-ibmi-program-analyzer 做 normal_program deep-read。

Program: <PROGRAM_NAME>
使用已有 artifacts:
- source-index.yaml: <路径>
- routine-index.md: <路径>
- routine-logic-details.yaml: <路径>
- message-inventory.yaml: <路径>

本轮最多读取 5 个 routine body。
优先 entry、validation、calculation、persistence、exception、
message/status routines。

请更新:
- routine-logic-details.md
- routine-logic-details.yaml
- program-analysis-summary.yaml
- program-analysis.md 的摘要章节
- 如果发现 message/status/code，更新 message-inventory.yaml
```

Output Checkpoint:

- Every routine read in this step is marked `deep_read`.
- Routines not read remain `indexed_only`.
- `program-analysis.md` is updated at summary level only.
- No routine body is copied into `program-analysis.md`.
- If another batch is required, the program should be reclassified as
  `complex_normal_program`.

### Step 4: Check Message Descriptions

English Prompt:

```text
Validate message inventory for normal_program review.

Review message-inventory.yaml and program-analysis.md.

For every observed message/status/code value, confirm:
- code or ID
- trigger condition
- routine or source range
- user or downstream recipient, if visible
- real description source

If the description is missing, mark it unresolved and request the message
file, message catalog, reference pack, source literal/comment, runtime
evidence, or SME-approved description.
```

中文 Prompt:

```text
请检查 normal_program 的 message inventory。

检查 message-inventory.yaml 和 program-analysis.md。

每个 observed message/status/code 都要确认:
- code 或 ID
- 触发条件
- routine 或 source range
- 可见的用户或 downstream recipient
- 真实 description source

如果 description 缺失，请标记 unresolved，并要求补充 message file、
message catalog、reference pack、source literal/comment、runtime evidence，
或 SME-approved description。
```

Output Checkpoint:

- No message ID is presented as meaningful without a description.
- Missing descriptions are explicit blockers for final-ready / chain-ready.
- SME knows exactly which message file or description source is missing.

### Step 5: Final Readiness Decision

English Prompt:

```text
Prepare the normal_program final readiness check.

Use:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- message-inventory.yaml

Decide one status:
- final_ready
- draft_exploratory
- blocked

Show:
- confirmed calculation logic
- confirmed validation logic
- confirmed exception handling
- confirmed messages
- confirmed file I/O / SQL behavior
- indexed_only routines
- unresolved TBDs
- required SME decisions
```

中文 Prompt:

```text
请准备 normal_program final readiness check。

使用:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- message-inventory.yaml

请选择一个状态:
- final_ready
- draft_exploratory
- blocked

请展示:
- 已确认的 calculation logic
- 已确认的 validation logic
- 已确认的 exception handling
- 已确认的 messages
- 已确认的 file I/O / SQL behavior
- indexed_only routines
- unresolved TBDs
- 需要 SME 决策的事项
```

Output Checkpoint:

- `final_ready` is allowed only when required evidence and message
  descriptions are present.
- `draft_exploratory` is acceptable for early SME review.
- `blocked` is used when missing input prevents meaningful interpretation.
- The next action is specific: SME decision, message file, copybook, or
  reclassify to complex analysis.
