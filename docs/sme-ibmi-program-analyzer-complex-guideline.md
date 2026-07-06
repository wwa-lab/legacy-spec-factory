# SME Guideline: Complex Normal Program Code Scan

This guideline is for SMEs and analysts running `legacy-ibmi-program-analyzer`
against a `complex_normal_program`. A complex normal program is usually under
10,000 lines but dense enough to need selective sidecars or more than one
five-routine deep-read batch.

中文说明: 这份手册适用于没有超过 1 万行、但逻辑密集的 IBM i program。目标
是让 SME 按 batch 逐步完成 code scan，并清楚知道每一步需要检查哪些输出。

## When To Use

Use this guideline when the program has one or more triggers:

- More than one five-routine batch is needed.
- Dense validation, calculation, exception, message, or status handling.
- Dense file I/O, SQL, field mutation, commit, rollback, or lock behavior.
- Many external calls or unclear handoffs.
- A normal scan exposes too many `indexed_only` claims for SME review.

## Required Input Package

Prepare these files before starting:

- Source member path.
- Program name and object ID, if available.
- Copybooks/includes.
- Message file, message catalog, reference pack, or SME-approved message
  descriptions.
- Inventory/object evidence when `chain_ready` is requested.
- SME business question and any known transaction path.
- Existing normal-program artifacts, if this is an escalation from a normal
  scan.

## E2E Steps

### Step 1: Start Complex Program Scan

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a complex_normal_program code scan.

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
- Read at most 5 routine bodies in this turn.
- Prioritize entry/dispatch, validation, calculation, persistence, exception,
  message/status, SQL, and external-call boundary routines.
- Generate only sidecars triggered by observed evidence.
- Do not paste real source-code snippets into narrative output.
- Do not claim confirmed behavior from indexed_only routines.

Required core output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 complex_normal_program code scan。

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
- 本轮最多读取 5 个 routine body。
- 优先 entry / dispatch、validation、calculation、persistence、
  exception、message/status、SQL、external-call boundary routines。
- 只生成被证据触发的 sidecars。
- narrative 输出中不要粘贴真实 source-code snippets。
- 不要根据 indexed_only routines 声称 confirmed behavior。

核心产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
```

Output Checkpoint:

- Core artifacts exist.
- `program-analysis.md` uses the stable SME-first layout.
- `source-index.yaml` identifies the program as `complex_normal_program`.
- The first batch reads no more than five routine bodies.
- Any density trigger is named in `program-analysis-summary.yaml`.

### Step 2: Confirm Triggered Sidecars

English Prompt:

```text
Review triggered sidecars for complex_normal_program.

Use:
- source-index.yaml
- program-analysis-summary.yaml
- routine-logic-details.yaml
- message-inventory.yaml

Create or update only the sidecars justified by observed evidence:
- deep-read-plan.md and all-routine-coverage-ledger.md when more than one
  five-routine batch is needed.
- file-io-inventory.yaml when file I/O is dense or state-changing.
- field-mutation-matrix.yaml when persisted field mutation is observed.
- sql-inventory.yaml when embedded SQL / SQLRPGLE evidence is observed.
- message-inventory.md when messages need SME-facing review.

For each sidecar, record the evidence trigger and the SME question it supports.
```

中文 Prompt:

```text
请检查 complex_normal_program 需要触发哪些 sidecars。

使用:
- source-index.yaml
- program-analysis-summary.yaml
- routine-logic-details.yaml
- message-inventory.yaml

只创建或更新有证据触发的 sidecars:
- deep-read-plan.md / all-routine-coverage-ledger.md:
  当需要超过一轮 5 个 routine batch 时生成。
- file-io-inventory.yaml:
  当 file I/O 密集，或存在 state-changing operation 时生成。
- field-mutation-matrix.yaml:
  当发现 persisted field mutation 时生成。
- sql-inventory.yaml:
  当发现 embedded SQL / SQLRPGLE evidence 时生成。
- message-inventory.md:
  当 messages 需要 SME-facing review 时生成。

每个 sidecar 都要记录 evidence trigger 和它支持的 SME question。
```

Output Checkpoint:

- Every generated sidecar has a visible trigger.
- Untriggered sidecars are not required.
- If more than one batch is needed, both `deep-read-plan.md` and
  `all-routine-coverage-ledger.md` exist.
- SQL, field mutation, file I/O, and message outputs are present only when
  evidence requires them.

### Step 3: Run The Next Deep-Read Batch

English Prompt:

```text
Continue complex_normal_program deep-read.

Program: <PROGRAM_NAME>
Use existing artifacts:
- source-index.yaml: <path>
- deep-read-plan.md: <path if present>
- all-routine-coverage-ledger.md: <path if present>
- routine-logic-details.yaml: <path>
- message-inventory.yaml: <path>
- file-io-inventory.yaml: <path if triggered>
- field-mutation-matrix.yaml: <path if triggered>
- sql-inventory.yaml: <path if triggered>

Analyze the next batch of at most 5 routine bodies.
Choose routines that unblock the SME question first.

Update compact artifacts and list:
- newly deep_read routines
- routines still indexed_only
- blocked routines
- claims now supported
- claims still unsafe
- next batch candidates
```

中文 Prompt:

```text
请继续 complex_normal_program deep-read。

Program: <PROGRAM_NAME>
使用已有 artifacts:
- source-index.yaml: <路径>
- deep-read-plan.md: <路径，如果存在>
- all-routine-coverage-ledger.md: <路径，如果存在>
- routine-logic-details.yaml: <路径>
- message-inventory.yaml: <路径>
- file-io-inventory.yaml: <路径，如果已触发>
- field-mutation-matrix.yaml: <路径，如果已触发>
- sql-inventory.yaml: <路径，如果已触发>

本轮最多分析 5 个 routine body。
优先选择能解除 SME question 的 routines。

请更新 compact artifacts，并列出:
- 本轮新增 deep_read 的 routines
- 仍然 indexed_only 的 routines
- blocked routines
- 现在已经有证据支持的 claims
- 仍然不安全的 claims
- 下一轮 batch candidates
```

Output Checkpoint:

- Only routines actually read move to `deep_read`.
- `all-routine-coverage-ledger.md` matches the batch result when present.
- `routine-logic-details.md` and `routine-logic-details.yaml` agree.
- Updated claims point to RLOG IDs and source ranges.
- The next batch is limited to five routines.

### Step 4: Check Sidecar Consistency

English Prompt:

```text
Check complex_normal_program sidecar consistency.

Use all generated artifacts and confirm:
- program-analysis.md remains reader-first and contains Program Reading Summary.
- Calculation / Validation / Exception routine indexes cover every RLOG in
  routine-logic-details.yaml.
- Routine Logic Details in program-analysis.md contain continuous, ordered RLOG
  headings for every RLOG in routine-logic-details.yaml.
- routine-logic-details.yaml covers every deep_read routine.
- message-inventory.yaml lists observed message/status/code values.
- file-io-inventory.yaml covers state-changing file operations, if triggered.
- field-mutation-matrix.yaml covers persisted field mutations, if triggered.
- sql-inventory.yaml covers embedded SQL, host variables, SQLCODE, and
  SQLSTATE, if triggered.

List contradictions, missing IDs, missing descriptions, and unsupported claims.
```

中文 Prompt:

```text
请检查 complex_normal_program sidecar consistency。

使用所有已生成 artifacts，并确认:
- program-analysis.md 仍然是 reader-first，并包含 Program Reading Summary。
- Calculation / Validation / Exception routine indexes 覆盖
  routine-logic-details.yaml 中的全部 RLOG。
- program-analysis.md 里的 Routine Logic Details headings 连续、有序，并覆盖
  routine-logic-details.yaml 中的全部 RLOG。
- routine-logic-details.yaml 覆盖所有 deep_read routines。
- message-inventory.yaml 列出 observed message/status/code。
- 如果触发 file-io-inventory.yaml，它覆盖 state-changing file operations。
- 如果触发 field-mutation-matrix.yaml，它覆盖 persisted field mutations。
- 如果触发 sql-inventory.yaml，它覆盖 embedded SQL、host variables、
  SQLCODE、SQLSTATE。

请列出矛盾、缺失 ID、缺失 description、以及 unsupported claims。
```

Output Checkpoint:

- Sidecars do not disagree on routine IDs, file names, field names, or message
  IDs.
- Missing message descriptions are explicit blockers.
- `program-analysis.md` is the SME reading surface; sidecars remain
  audit/checkpoint and machine-readable evidence.
- SME can identify whether the next action is another batch or a data/source
  gap.

### Step 5: Final Complex Program Readiness

English Prompt:

```text
Prepare final readiness for complex_normal_program.

Use:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- routine-logic-details.yaml
- message-inventory.yaml
- triggered sidecars
- all-routine-coverage-ledger.md, if present

Decide one status:
- final_ready
- draft_exploratory
- blocked

Show:
- supported calculation, validation, exception, message, file I/O, SQL, and
  handoff claims
- routines still indexed_only
- sidecars triggered and why
- unresolved message descriptions
- blocked evidence
- SME decisions required
- confirmation that program-analysis.md, routine-logic-details.yaml, and
  message-inventory.yaml are synchronized
```

中文 Prompt:

```text
请准备 complex_normal_program final readiness。

使用:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- routine-logic-details.yaml
- message-inventory.yaml
- 已触发的 sidecars
- all-routine-coverage-ledger.md，如果存在

请选择一个状态:
- final_ready
- draft_exploratory
- blocked

请展示:
- 有证据支持的 calculation、validation、exception、message、file I/O、
  SQL、handoff claims
- 仍然 indexed_only 的 routines
- 哪些 sidecars 被触发以及原因
- 未解决的 message descriptions
- blocked evidence
- 需要 SME 决策的事项
- 确认 program-analysis.md、routine-logic-details.yaml、
  message-inventory.yaml 已同步
```

Output Checkpoint:

- `final_ready` requires resolved message descriptions and no critical
  unsupported claim.
- `chain_ready` requires object/inventory IDs and downstream evidence
  completeness.
- Remaining `indexed_only` routines are acceptable only when they are not used
  for final claims.
- The final output tells the SME whether to approve, provide missing evidence,
  or run another batch.
