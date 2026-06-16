# SME IBM i Program / Flow / Module Review Guideline

This guideline explains how SMEs and analysts should use
`legacy-ibmi-program-analyzer`, `legacy-ibmi-flow-analyzer`, and
`legacy-ibmi-module-analyzer` when company LLM token budget is limited and one
LLM turn may read at most five routines.

For copy-ready bilingual prompts, see
[`sme-ibmi-analysis-prompts.md`](sme-ibmi-analysis-prompts.md). It includes
general program analysis, large-program automatic batch analysis, and compact
multi-program SME core review prompts.

## 中文摘要

这份 guideline 给 SME / BA / analyst 使用。核心用法是：

- 常用中英双语提示词请直接看
  [`sme-ibmi-analysis-prompts.md`](sme-ibmi-analysis-prompts.md)，里面包含
  普通 program、large program 自动分批、以及多个 program 结果合并成核心
  SME review 的 prompt。
- 只看一个程序，就跑 `legacy-ibmi-program-analyzer`。
- 看一个业务交易从入口到落库，就跑 `legacy-ibmi-flow-analyzer`。
- 看多个 flow 是否能组成一个可交付业务模块，就跑
  `legacy-ibmi-module-analyzer`。
- 内部 LLM 一次最多读 5 个 routine，所以必须先建 `source-index.yaml`
  并判断 `normal_program` / `complex_normal_program` /
  `large_extreme_program`。普通程序默认轻量产出；只有复杂或极限场景才加
  sidecars 和分批 deep read。
- flow 和 module 不重新吞源码，也不拼多个完整 Markdown；它们只消费
  program/flow 的 compact artifacts。
- SME review 的第一屏要能看到 calculation logic、validation logic、
  exception handling、message inventory、file I/O / SQL state changes，以及
  哪些地方仍然是 TBD。

## One-Sentence Rule

Do not ask the LLM to understand a whole IBM i system at once. Build a source
index first, classify the program tier, keep normal programs lightweight, and
deep-read at most five routines per turn only when density or downstream
evidence needs require it.

## When To Use Each Skill

| Scenario | Use | SME question it answers | Main review surface |
| --- | --- | --- | --- |
| One program needs review | `legacy-ibmi-program-analyzer` | What does this program calculate, validate, update, call, and message? | `program-analysis.md` plus core artifacts; optional sidecars only when triggered |
| One transaction spans programs | `legacy-ibmi-flow-analyzer` | How does one business event move across programs, files, SQL, messages, and error paths? | `flow-<FLOW-SLUG>.md` |
| Multiple flows form a module | `legacy-ibmi-module-analyzer` | Is this business module covered enough for BRD/spec handoff? | `module-overview.md`, `03-program-flow.md`, `04-data-flow.md`, `module-review-checklist.md` |

Use the smallest layer that answers the SME question. Do not start at module
level when the actual question is about one program or one transaction.

## Token Budget Rules

1. Read no more than five routine bodies in one LLM turn.
2. Never paste a full large RPGLE / SQLRPGLE source member into a prompt.
3. Never concatenate multiple full `program-analysis.md` or `flow.md` files.
4. Use core compact artifacts first:
   - `program-analysis-summary.yaml`
   - `source-index.yaml`
   - `routine-logic-details.yaml`
   - `message-inventory.yaml`
5. Add optional sidecars only when triggered:
   - `deep-read-plan.md` and `all-routine-coverage-ledger.md` when more than
     one five-routine batch is needed.
   - `file-io-inventory.yaml` when file I/O is dense or state-changing.
   - `field-mutation-matrix.yaml` when persisted field mutations are observed.
   - `sql-inventory.yaml` when embedded SQL / SQLRPGLE evidence is observed.
6. Open human-readable Markdown only for targeted SME clarification.
7. Treat `indexed_only` as structure evidence, not confirmed behavior.
8. Treat `deep_read` as the minimum evidence level for strong logic claims.
9. If a flow or module needs a routine that is still `indexed_only`, route
   back to program analysis for the next five-routine batch.

## Program Tier Rules

| Tier | Default use | Output behavior |
| --- | --- | --- |
| `normal_program` | Most programs under 10,000 lines with no density trigger. | Concise `program-analysis.md` plus core artifacts only. |
| `complex_normal_program` | Under 10,000 lines but dense in routines, file I/O, SQL, messages, mutations, external calls, or more than one five-routine batch. | Same SME-first review plus only triggered sidecars. |
| `large_extreme_program` | Over 10,000 lines, more than 25 routines, more than 20 external calls, more than 25 object dependencies, or unsafe to fit in context. | Full source index, all sidecars, coverage ledger, deep-read plan, retained `routine-logic-details/deep-read-batch-001.md` style checkpoints, and automatic loop when possible. |

## Tier-Specific Prompts And Output Checkpoints

Use these copy-ready prompts after the first source index identifies the
program tier. Each prompt has a matching output checkpoint so analysts can
quickly verify whether the run is ready for SME review or needs another
five-routine batch.

### Tier 1: `normal_program`

Use this when the program is under 10,000 lines and has no density trigger.
The target is a concise SME review surface, not a large sidecar package.

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a normal_program review.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Intent: <standalone_exploratory | chain_ready>
Tier: normal_program

Token rules:
- Build or reuse source-index.yaml first.
- Read at most 5 routine bodies in this turn.
- Keep the review lightweight unless a density trigger is discovered.
- Do not paste long source excerpts into the output.
- Do not treat indexed_only routines as confirmed logic.

Produce a concise program-analysis.md with stable sections:
- Program Overview
- Calculation Logic
- Validation Logic
- Exception Handling
- Message Inventory
- File I/O and SQL
- External Calls and Handoffs
- Evidence Coverage
- Open TBDs and SME Questions

Also produce or update the core compact artifacts:
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

If message/status/code values are observed but descriptions are missing,
mark them unresolved and do not mark the review final-ready.
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 normal_program review。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Intent: <standalone_exploratory | chain_ready>
Tier: normal_program

Token 规则:
- 先建立或复用 source-index.yaml。
- 本轮最多读取 5 个 routine body。
- 没有密集度触发时，保持轻量 review，不要生成大量 sidecar。
- 输出中不要粘贴大段真实 source code。
- 不要把 indexed_only routines 当成 confirmed logic。

请生成简洁、layout 稳定的 program-analysis.md，包含这些章节:
- Program Overview
- Calculation Logic
- Validation Logic
- Exception Handling
- Message Inventory
- File I/O and SQL
- External Calls and Handoffs
- Evidence Coverage
- Open TBDs and SME Questions

同时生成或更新核心 compact artifacts:
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

如果发现 message/status/code，但没有对应描述，请标记 unresolved，
不要把 review 标记为 final-ready。
```

Output Checkpoint:

- `program-analysis.md` exists and uses the stable section order above.
- Core compact artifacts exist and are internally consistent.
- No optional sidecar is required unless the run discovered a density trigger.
- `routine-logic-details.yaml` distinguishes `deep_read` from `indexed_only`.
- Message IDs without descriptions are marked unresolved and block final-ready
  status.
- No confident business claim is based only on `indexed_only` evidence.

### Tier 2: `complex_normal_program`

Use this when the source is still below large-program size but has dense
routines, messages, file I/O, SQL, field mutation, or external-call behavior.
The target is selective sidecar generation, not automatic full expansion.

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a complex_normal_program review.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Intent: <standalone_exploratory | chain_ready>
Tier: complex_normal_program

Token rules:
- Build or reuse source-index.yaml first.
- Read at most 5 routine bodies in this turn.
- Prioritize entry/dispatch, validation, calculation, persistence, exception,
  message/status handling, SQL, and external-call boundary routines.
- Generate only the sidecars triggered by observed evidence.
- Do not paste real source-code snippets into narrative output.
- Do not claim behavior from indexed_only routines.

Required core output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

Triggered sidecars:
- deep-read-plan.md and all-routine-coverage-ledger.md when more than one
  five-routine batch is needed.
- file-io-inventory.yaml when file I/O is dense or state-changing.
- field-mutation-matrix.yaml when persisted field mutation is observed.
- sql-inventory.yaml when embedded SQL / SQLRPGLE evidence is observed.
- message-inventory.md when message behavior needs SME-facing review.

End the run with a checkpoint listing:
- routines deep_read in this turn
- routines still indexed_only
- triggered sidecars created or updated
- supported claims
- unsafe claims
- unresolved message descriptions
- next five-routine batch candidates
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 complex_normal_program review。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Intent: <standalone_exploratory | chain_ready>
Tier: complex_normal_program

Token 规则:
- 先建立或复用 source-index.yaml。
- 本轮最多读取 5 个 routine body。
- 优先读取 entry / dispatch、validation、calculation、persistence、
  exception、message/status handling、SQL、external-call boundary routines。
- 只生成被证据触发的 sidecars。
- narrative 输出中不要粘贴真实 source-code snippets。
- 不要根据 indexed_only routine 声称 confirmed behavior。

核心产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

按需触发的 sidecars:
- deep-read-plan.md / all-routine-coverage-ledger.md:
  当需要超过一轮 5 个 routine batch 时生成。
- file-io-inventory.yaml:
  当 file I/O 密集，或存在 write/update/delete/commit/rollback 时生成。
- field-mutation-matrix.yaml:
  当发现 persisted field mutation 时生成。
- sql-inventory.yaml:
  当发现 embedded SQL / SQLRPGLE evidence 时生成。
- message-inventory.md:
  当 message 行为需要 SME review 时生成。

本轮结束时输出 checkpoint，列出:
- 本轮 deep_read 的 routines
- 仍然 indexed_only 的 routines
- 本轮创建或更新的 triggered sidecars
- 已有证据支持的 claims
- 仍然不安全的 claims
- 未解决的 message descriptions
- 下一轮最多 5 个 routine 的候选列表
```

Output Checkpoint:

- `program-analysis.md` exists and keeps the stable SME-first section layout.
- Core compact artifacts exist for the program.
- Every triggered sidecar has a clear evidence trigger; untriggered sidecars
  are not required.
- `deep-read-plan.md` and `all-routine-coverage-ledger.md` exist when more
  than one five-routine batch is needed.
- Coverage status remains explicit: `deep_read`, `indexed_only`, `blocked`, or
  `pending_sme_judgment`.
- Message IDs have descriptions or are marked unresolved with a requested
  message file/catalog/reference pack or SME-approved text.
- The next action is specific: another routine batch, a missing artifact, or
  an SME decision.

### Tier 3: `large_extreme_program`

Use this when the source is over 10,000 lines, has very high routine/object
density, or cannot be safely reviewed in one context. The target is automatic
batchable progress with retained checkpoints.

English Prompt:

```text
Use legacy-ibmi-program-analyzer for a large_extreme_program review.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Intent: <standalone_exploratory | chain_ready>
Tier: large_extreme_program

Token rules:
- Never paste or re-read the full source in one turn.
- Build or reuse source-index.yaml first.
- Read at most 5 routine/window bodies in each turn.
- Generate retained deep-read batch checkpoints under routine-logic-details/.
- Do not paste real source-code snippets in deep-read-batch core logic
  sections; cite source ranges, evidence IDs, and RLOG-* links instead.
- Do not mark chain_ready while message descriptions, copybooks, external
  program semantics, or critical state-changing routines remain unresolved.

Required output:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.md
- message-inventory.yaml
- file-io-inventory.md
- file-io-inventory.yaml
- field-mutation-matrix.md
- field-mutation-matrix.yaml
- sql-inventory.md when SQL evidence exists
- sql-inventory.yaml when SQL evidence exists
- deep-read-plan.md
- all-routine-coverage-ledger.md
- routine-logic-details/deep-read-batch-001.md
- additional routine-logic-details/deep-read-batch-*.md files for later
  five-routine batches

Every deep-read-batch-*.md must use this top-level layout:
- Calculation Logic
- Validation Logic
- Exception Handling
- Scope
- Batch Coverage Summary
- Message Inventory
- Routine Details

End every batch with a checkpoint listing:
- batch number
- routines/windows actually read
- source line ranges read
- artifacts updated
- gaps closed
- blockers added or retained
- unresolved message descriptions
- next batch candidates
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 large_extreme_program review。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Intent: <standalone_exploratory | chain_ready>
Tier: large_extreme_program

Token 规则:
- 不要在一轮里粘贴或重读完整 source。
- 先建立或复用 source-index.yaml。
- 每轮最多读取 5 个 routine/window body。
- 必须在 routine-logic-details/ 下保留 deep-read batch checkpoints。
- deep-read-batch 的核心逻辑章节不要粘贴真实 source-code snippets；
  用 source ranges、evidence IDs、RLOG-* links 代替。
- 只要 message descriptions、copybooks、external program semantics、
  critical state-changing routines 仍未解决，就不要标记 chain_ready。

必须产出:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.md
- message-inventory.yaml
- file-io-inventory.md
- file-io-inventory.yaml
- field-mutation-matrix.md
- field-mutation-matrix.yaml
- sql-inventory.md，如果存在 SQL evidence
- sql-inventory.yaml，如果存在 SQL evidence
- deep-read-plan.md
- all-routine-coverage-ledger.md
- routine-logic-details/deep-read-batch-001.md
- 后续每轮 5 个 routine batch 对应的
  routine-logic-details/deep-read-batch-*.md

每个 deep-read-batch-*.md 必须使用这些顶层章节:
- Calculation Logic
- Validation Logic
- Exception Handling
- Scope
- Batch Coverage Summary
- Message Inventory
- Routine Details

每个 batch 结束时输出 checkpoint，列出:
- batch number
- 本轮实际读取的 routines/windows
- 本轮读取的 source line ranges
- 本轮更新的 artifacts
- 本轮关闭的 gaps
- 本轮新增或保留的 blockers
- 未解决的 message descriptions
- 下一轮 batch candidates
```

Output Checkpoint:

- `program-analysis.md` exists and remains summary-level, not a full source
  rewrite.
- `deep-read-plan.md` and `all-routine-coverage-ledger.md` exist.
- `routine-logic-details/deep-read-batch-001.md` exists after the first batch.
- Every `deep-read-batch-*.md` uses the required top-level layout.
- Batch core logic sections contain no pasted source-code snippets.
- Each batch records the actual source line ranges read.
- Core and triggered sidecars are updated incrementally, not regenerated from
  unsupported assumptions.
- `program-analysis-summary.yaml` shows remaining downstream-readiness gaps.
- Unresolved message IDs block final-ready / chain-ready status until a
  message file/catalog/reference pack, source literal/comment, runtime
  evidence, or SME-approved description is provided.

## SME Review Priorities

When token budget is tight, prioritize routines in this order:

| Priority | Routine type | Why it matters |
| --- | --- | --- |
| 1 | Entry, mainline, dispatch, menu option, API entry | Defines the path being reviewed |
| 2 | Validation routines | Drives reject/accept decisions and messages |
| 3 | Calculation routines | Carries business formulas, totals, rates, limits, fees, dates |
| 4 | File I/O, SQL, update, delete, commit, rollback | Changes persistent state |
| 5 | Exception and message handling | Explains abnormal outcomes and SME support behavior |
| 6 | External call wrappers | Handoff to other programs, APIs, queues, reports |
| 7 | Utility routines | Usually lower priority unless they change business state |

For every SME review, the first visible sections should answer:

- Calculation Logic: what is calculated, from which inputs, with which
  conditions.
- Validation Logic: what is checked, what fails, and what happens on failure.
- Exception Handling: what error is caught, how processing continues/stops,
  and whether rollback/commit/message behavior is visible.
- Message Inventory: which messages are emitted, when, and to whom.
- File I/O and SQL: which files/tables are read or changed, by which routine.

If message/status/code values are observed, the program analysis is not
final-review-ready until each row has a real description source: message file,
message catalog, approved reference pack, source literal/comment, runtime
evidence, or SME-approved text. ID-only Message Inventory output is a blocking
gap, not useful SME review material.

## End-To-End Workflow

### Step 0: Choose Intent And Scope

Decide whether the run is exploratory or chain-ready.

- Use `standalone_exploratory` for quick SME review, incomplete evidence, or
  early discovery.
- Use `chain_ready` only when the output must feed flow/module/BRD/spec work
  and inventory/evidence IDs are available.

Prompt:

```text
Use Legacy Spec Factory IBM i analysis in token-limited mode.

Intent: <standalone_exploratory | chain_ready>
Scope: <one program | one flow | one module>
Token rule: read at most 5 routine bodies per LLM turn.
Do not concatenate full source or full analysis Markdown.
Use compact artifacts first and mark missing evidence as TBD.

Business question from SME:
<question>

Available evidence:
- Inventory: <path or missing>
- Source/program artifacts: <paths>
- Flow/module artifacts: <paths>
- SME notes: <paths or notes>
```

中文 Prompt:

```text
请使用 Legacy Spec Factory 的 IBM i 分析流程，并启用 token 受限模式。

分析意图: <standalone_exploratory | chain_ready>
分析范围: <一个 program | 一个 flow | 一个 module>
Token 规则: 每轮最多读取 5 个 routine body。
不要拼接完整 source，也不要拼接完整 analysis Markdown。
优先使用 compact artifacts；缺失证据必须标记为 TBD。

SME 这次关心的问题:
<问题>

当前可用证据:
- Inventory: <路径或缺失>
- Source / program artifacts: <路径列表>
- Flow / module artifacts: <路径列表>
- SME notes: <路径或备注>
```

### Step 1: Program Index Preflight

Run this before any deep program review. For most programs, this should simply
classify the program as `normal_program` and prepare a lightweight SME review.
For dense or large programs, it triggers only the extra sidecars that are
needed.

Core output for every tier:

- `program-analysis.md`
- `source-index.yaml`
- `program-analysis-summary.yaml`
- `routine-index.md`
- `routine-logic-details.md`
- `routine-logic-details.yaml`
- `message-inventory.yaml`

Optional output when triggered:

- `deep-read-plan.md`
- `all-routine-coverage-ledger.md`
- `message-inventory.md`
- `file-io-inventory.md`
- `file-io-inventory.yaml`
- `field-mutation-matrix.md`
- `field-mutation-matrix.yaml`
- `sql-inventory.md`
- `sql-inventory.yaml`

Required extra output for `large_extreme_program`:

- `routine-logic-details/deep-read-batch-001.md`
- additional `routine-logic-details/deep-read-batch-*.md` files when more
  than five selected routines/windows are processed

Every `deep-read-batch-*.md` file uses the same top-level layout:
`Calculation Logic`, `Validation Logic`, `Exception Handling`, `Scope`,
`Batch Coverage Summary`, `Message Inventory`, `Routine Details`. The core
logic sections must not contain pasted source code snippets; cite source
ranges, evidence IDs, and `RLOG-*` links instead.

Prompt:

```text
Use legacy-ibmi-program-analyzer for program index preflight.

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID or missing>
Source path: <source path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: <standalone_exploratory | chain_ready>

Token constraint:
- Do not deep-read more than 5 routines in this turn.
- First build deterministic indexes and classify the program tier:
  normal_program, complex_normal_program, or large_extreme_program.
- Default to normal_program lightweight output when no density trigger appears.
- If the source is SQLRPGLE/free-format, still index SQL statements, host
  variables, SQLCODE/SQLSTATE, routines, file I/O, field mutations, messages,
  and external calls. Generate SQL sidecar only when embedded SQL is present.

Core output required:
- program-analysis.md
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml

Optional sidecars:
- deep-read-plan.md and all-routine-coverage-ledger.md only when more than one
  five-routine batch is needed, or tier is complex/large.
- file-io-inventory.yaml only when file I/O is dense or state-changing.
- field-mutation-matrix.yaml only when persisted field mutations are observed.
- sql-inventory.yaml only when embedded SQL / SQLRPGLE evidence is observed.

Do not produce a confident whole-program business narrative until coverage is
visible.
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 program index preflight。

Program: <PROGRAM_NAME>
Program ID: <OBJ-ID 或 missing>
Source path: <source 路径>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: <standalone_exploratory | chain_ready>

Token 限制:
- 本轮不要 deep-read 超过 5 个 routine。
- 先建立确定性的 source index，并判断 program tier:
  normal_program、complex_normal_program、large_extreme_program。
- 没有密集度触发时，默认走 normal_program 轻量产出。
- 如果是 SQLRPGLE / free-format，也要正确索引 SQL statements、host
  variables、SQLCODE / SQLSTATE、routines、file I/O、field mutations、
  messages、external calls。有 embedded SQL 时才触发 SQL sidecar。

核心产出:
- source-index.yaml
- program-analysis-summary.yaml
- routine-index.md
- routine-logic-details.yaml
- message-inventory.yaml

按需触发的 sidecars:
- deep-read-plan.md / all-routine-coverage-ledger.md:
  只有超过一轮 5 个 routine/window，或 tier 是 complex/large 时才需要。
- file-io-inventory.yaml:
  只有 file I/O 密集，或有 write/update/delete/commit/rollback 时才需要。
- field-mutation-matrix.yaml:
  只有读到 persisted field mutation 时才需要。
- sql-inventory.yaml:
  只有存在 embedded SQL / SQLRPGLE evidence 时才需要。

在 coverage 可见之前，不要生成看起来很确定的 whole-program business
narrative。
```

### Step 2: Program Deep-Read Batch 1

Read only the top five routines selected by the priority rules.

Prompt:

```text
Use legacy-ibmi-program-analyzer for program deep-read batch 1.

Program: <PROGRAM_NAME>
Use existing artifacts:
- source-index.yaml: <path>
- deep-read-plan.md: <path>
- all-routine-coverage-ledger.md: <path>
- routine-logic-details.yaml: <path>
- message-inventory.yaml: <path>
- file-io-inventory.yaml: <path if triggered>
- field-mutation-matrix.yaml: <path if triggered>
- sql-inventory.yaml: <path if triggered>

Token constraint:
- Analyze at most 5 routine bodies in this turn.
- Prefer entry/dispatch, validation, calculation, persistence, and exception
  routines.
- Do not claim behavior from routines that remain indexed_only.

For each deep-read routine, update:
- routine purpose
- calculation logic
- validation logic
- file I/O and SQL behavior
- field mutations and handoffs
- messages
- exception handling
- coverage status
- SME questions
```

中文 Prompt:

```text
请使用 legacy-ibmi-program-analyzer 做 program deep-read batch 1。

Program: <PROGRAM_NAME>
使用已有 artifacts:
- source-index.yaml: <路径>
- deep-read-plan.md: <路径>
- all-routine-coverage-ledger.md: <路径>
- routine-logic-details.yaml: <路径>
- message-inventory.yaml: <路径>
- file-io-inventory.yaml: <路径，如果已触发>
- field-mutation-matrix.yaml: <路径，如果已触发>
- sql-inventory.yaml: <路径，如果已触发>

Token 限制:
- 本轮最多分析 5 个 routine body。
- 优先选择 entry / dispatch、validation、calculation、persistence、
  exception routines。
- 不要把仍然是 indexed_only 的 routine 当成已确认逻辑。

每个 deep-read routine 都要更新:
- routine purpose
- calculation logic
- validation logic
- file I/O and SQL behavior
- field mutations and handoffs
- messages
- exception handling
- coverage status
- SME questions
```

### Step 3: Program Deep-Read Continuation

Repeat this step until the SME-critical routines are covered. The goal is not
to deep-read every utility routine; the goal is to support the claims needed by
the current program, flow, or module review.

Prompt:

```text
Continue legacy-ibmi-program-analyzer in token-limited mode.

Program: <PROGRAM_NAME>
Previous coverage ledger: <path>
Current SME question or downstream need:
<question or missing flow/module claim>

Analyze the next batch of at most 5 routines.
Choose routines that unblock the SME question first.

Do not re-read already deep_read routines unless a contradiction or missing
field/message/error detail requires it.

Update compact artifacts and list:
- newly deep_read routines
- routines still indexed_only
- blocked routines
- claims now supported
- claims still unsafe
- SME questions
```

中文 Prompt:

```text
请继续用 legacy-ibmi-program-analyzer 的 token-limited mode。

Program: <PROGRAM_NAME>
上一轮 coverage ledger: <路径>
当前 SME 问题或 downstream 需要补证据的点:
<问题或缺失的 flow/module claim>

本轮最多分析接下来的 5 个 routine。
优先选择能解除当前 SME 问题或 downstream gap 的 routines。

除非出现矛盾、字段缺失、message 缺失、error detail 缺失，否则不要重复读取
已经 deep_read 的 routines。

请更新 compact artifacts，并列出:
- 本轮新增 deep_read 的 routines
- 仍然 indexed_only 的 routines
- blocked routines
- 现在已经有证据支持的 claims
- 仍然不安全的 claims
- SME questions
```

### Step 3A: Automatic Program Deep-Read Loop

Use this after the first source index is complete and the team wants the agent
to continue routine batches without asking the SME to type "continue" after
each turn. This mode is useful for large RPGLE / SQLRPGLE programs, but it must
still preserve the five-routine limit, evidence boundaries, and
`standalone_exploratory` status.

中文 Prompt:

```text
继续 <PROGRAM_NAME> standalone_exploratory deep-read，进入自动分批循环模式。

目标:
- 处理完 deep-read-plan.md 中所有可处理、需要 deep-read 的 routine/window。
- 每轮最多处理 5 个 routine/window。
- 不要让我反复发送“继续”；你需要一轮接一轮自动推进。
- 直到没有可处理的 deep-read window，或遇到无法自行继续的 blocker 才停止。

保持状态:
- analysis_intent = standalone_exploratory
- status = draft_exploratory
- downstream_readiness = not_chain_ready
- 不要标记 chain_ready

严禁:
- 不要重新读取完整源码。
- 不要把 program-analysis.md 扩展成大而全正文。
- 不要凭字段名猜业务规则。
- 不要把 indexed_only 改成 deep_read，除非本轮实际读取了对应源码窗口。
- 不要覆盖已有人工 review 或前轮 deep-read 结果；只能增量更新。
- 不要删除已有 TBD、SME questions、人工备注；只能补充、关闭或解释。
- 不要跨过缺失 copybook、缺失 message catalog、缺失外部程序语义来编造结论。

使用这些文件:
- deep-read-plan.md
- source-index.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.md
- message-inventory.yaml
- all-routine-coverage-ledger.md
- program-analysis-summary.yaml
- program-analysis.md
- <PROGRAM_NAME>.RPGLE 或实际 source 文件

执行策略:

1. 读取 deep-read-plan.md、all-routine-coverage-ledger.md、
   routine-logic-details.yaml、program-analysis-summary.yaml。
2. 找出尚未 deep_read、且有 source_lines 范围的 deep-read windows。
3. 如果存在 blocking / downstream-readiness gap，优先选择能关闭 gap 的
   routine/window。
4. 每轮最多选择 5 个 routine/window。
5. 选择优先级如下:
   - 当前 blocking / downstream-readiness gap 涉及的 routine
   - entry / mainline dispatch
   - state-changing file operation
   - SQL insert/update/delete/select into 或 cursor/fetch 影响的 routine
   - external call boundary
   - message/status handling
   - outcome/status carrier assignment
   - read-conditioned branch
   - screen/report boundary
   - calculation / validation hot path
6. 对每个选中的 routine/window:
   - 只读取 source 文件中对应 source_lines 范围。
   - 更新对应 RLOG-* 到 routine-logic-details.md。
   - 更新对应 RLOG-* 到 routine-logic-details.yaml。
   - 补充 execution trigger。
   - 补充 step-by-step logic。
   - 补充 field calculations / assignments。
   - 补充 conditioned calculation blocks。
   - 补充 outcome reverse traces。
   - 补充 field lineage / carriers。
   - 补充分支结果 branch outcomes。
   - 补充 routine exception closure。
   - 补充 unresolved routine logic。
   - 如发现 file I/O、SQL、message/status/code、external call、commit /
     rollback、indicator 状态影响，同步更新相应 compact artifact。
7. 更新 all-routine-coverage-ledger.md:
   - 只有本轮实际读取过源码窗口的 routine/window 才能从 indexed_only 改为
     deep_read。
   - 保留未读 routine/window 为 indexed_only。
   - 对缺少 source_lines、缺失 copybook、缺失外部资料、需要 SME 判断的项，
     标记 blocked 或 pending_sme_judgment，并写明原因。
8. 更新 program-analysis-summary.yaml:
   - 更新 routine_summary 中对应 RLOG-* 的 semantic_status、coverage、
     deep_read 状态。
   - 更新仍未解决的 downstream-readiness gap。
   - 已关闭的 gap 要说明由哪些 RLOG-* 和 source_lines 支持。
9. 更新 message-inventory.md / message-inventory.yaml:
   - 仅当本轮发现、解释或影响了 message/status/code 时更新。
   - 找不到 description 时写:
     unresolved - message description not available。
   - 如果仍有 unresolved description，不要标记 final-review-ready；要求补充
     message file/catalog/reference pack 或 SME-approved description。
10. 更新 file-io-inventory.md / file-io-inventory.yaml:
    - 仅当本轮发现或确认 read/write/update/delete、commit、rollback、
      lock、chain/setll/reade、SQL persistence 行为时更新。
11. 更新 field-mutation-matrix.md / field-mutation-matrix.yaml:
    - 仅当本轮实际读到 assignment、calculation、parameter handoff、
      status carrier、indicator carrier、SQL host variable 变化时更新。
12. 更新 sql-inventory.md / sql-inventory.yaml:
    - 仅当本轮实际读到 embedded SQL、cursor、host variable、SQLCODE /
      SQLSTATE、table/view reference 时更新。
13. 更新 program-analysis.md:
    - 只允许摘要级更新。
    - 只更新顶部 Calculation Logic、Validation Logic、Exception Handling、
      Message Inventory、File I/O / SQL 中确实受本轮影响的行。
    - 不要把 routine 正文复制进 program-analysis.md。
14. 每轮结束后做轻量验证:
    - 检查 Markdown 表格基本完整。
    - 检查 YAML 可读。
    - 检查本轮 updated RLOG-* 在 md/yaml 中一致。
    - 检查 coverage ledger 与本轮实际处理 routine/window 一致。
    - 临时验证优先使用 py -3；不要安装 Python、不要改 PATH。
15. 写入本轮 checkpoint:
    - 本轮编号
    - 本轮处理的 RLOG-* / routine/window
    - 本轮实际读取的 source_lines
    - 本轮更新的 artifact
    - 本轮关闭的 gap
    - 本轮新增或保留的 blocker
    - 下一轮候选 routine/window
16. 自动进入下一轮，继续处理下最多 5 个 routine/window。

停止条件:
- deep-read-plan.md 中所有可处理 windows 都已 deep_read。
- 剩余 windows 缺少 source_lines 或 source 不可访问。
- 剩余 windows 需要 SME、message catalog、copybook、外部程序、运行日志等外部资料。
- 连续 2 轮没有任何 routine/window 能从 indexed_only 变为 deep_read。
- YAML 或 Markdown 校验失败，且无法在不猜测的情况下修复。
- 上下文接近上限，且必须先交还控制权；此时先写入 checkpoint 和进度摘要。

如果上下文接近上限:
- 先把当前轮结果完整写入 artifacts。
- 写入 deep-read-loop-progress.md，记录已处理、未处理、blocker、下一轮候选。
- 不要丢失已完成状态。
- 如果当前执行环境支持继续自动推进，则读取 checkpoint 后继续下一轮。

最终完成后输出总结:
- 总共处理了多少轮。
- 总共 deep_read 了多少 routine/window。
- 哪些 RLOG-* 被更新。
- 哪些 routine/window 仍保持 indexed_only，以及原因。
- 哪些 downstream-readiness gap 已关闭。
- 哪些 gap 仍然存在。
- 哪些 blocker 需要 SME / copybook / message catalog / 外部程序 / runtime evidence。
- program-analysis.md 是否只做了摘要级更新。
- 明确说明没有标记 chain_ready。
```

### Step 4: Program SME Review

Use this when the SME wants to review one program without moving to flow yet.

Prompt:

```text
Prepare a focused SME review for one IBM i program.

Program: <PROGRAM_NAME>
Use compact artifacts first:
- program-analysis-summary.yaml
- routine-logic-details.yaml
- message-inventory.yaml
- file-io-inventory.yaml, if triggered
- field-mutation-matrix.yaml, if triggered
- sql-inventory.yaml, if triggered

Do not include long source excerpts.
Do not treat indexed_only routines as confirmed logic.

SME review layout must show:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory
5. File I/O and SQL state changes
6. External calls and unresolved handoffs
7. Open SME questions

Keep the review concise and decision-oriented.
```

中文 Prompt:

```text
请为一个 IBM i program 准备聚焦 SME review。

Program: <PROGRAM_NAME>
优先使用 compact artifacts:
- program-analysis-summary.yaml
- routine-logic-details.yaml
- message-inventory.yaml
- file-io-inventory.yaml，如果已触发
- field-mutation-matrix.yaml，如果已触发
- sql-inventory.yaml，如果已触发

不要包含大段 source 摘录。
不要把 indexed_only routines 当成 confirmed logic。

SME review layout 必须优先展示:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory
5. File I/O and SQL state changes
6. External calls and unresolved handoffs
7. Open SME questions

请保持简洁，重点支持 SME 做判断。
```

### Step 5: Flow Assembly

Use this after every in-scope program has at least enough compact artifacts to
support the flow path.

Prompt:

```text
Use legacy-ibmi-flow-analyzer to assemble one business transaction flow.

Flow slug: <FLOW-SLUG>
Trigger model: <batch job | menu | subfile | F-key | DB trigger | scheduler | API/remote>
Entry point: <program/menu/job/API>
Intent: <standalone_exploratory | chain_ready>

Use present compact program artifacts only. For normal programs, the core
artifacts may be enough; optional sidecars are required only when triggered or
when the flow claim needs them:
<list program artifact directories>

Token constraint:
- Do not concatenate full program-analysis Markdown.
- Do not re-analyze routine bodies inline.
- If a flow edge depends on an indexed_only routine, record the gap and route
  only that program/routine batch back to program analyzer.

Output must include:
- Transaction Call Map
- Flow Replay Path
- Cross-Program Field Lineage
- Flow Persistence Matrix
- Exception Propagation Chain
- Message carry-forward
- Missing program/routine artifact list
- SME questions
```

中文 Prompt:

```text
请使用 legacy-ibmi-flow-analyzer 组装一个 business transaction flow。

Flow slug: <FLOW-SLUG>
Trigger model: <batch job | menu | subfile | F-key | DB trigger | scheduler | API/remote>
Entry point: <program/menu/job/API>
Intent: <standalone_exploratory | chain_ready>

只使用已经存在的 compact program artifacts。对于 normal program，核心
artifacts 通常就够；optional sidecars 只有被触发，或 flow claim 需要时才
必须提供:
<program artifact directories 列表>

Token 限制:
- 不要拼接完整 program-analysis Markdown。
- 不要在 flow 层重新分析 routine body。
- 如果某个 flow edge 依赖 indexed_only routine，请记录 gap，并只把那个
  program / routine batch 路由回 program analyzer。

输出必须包含:
- Transaction Call Map
- Flow Replay Path
- Cross-Program Field Lineage
- Flow Persistence Matrix
- Exception Propagation Chain
- Message carry-forward
- Missing program/routine artifact list
- SME questions
```

### Step 6: Flow Repair Batch

Use this when flow assembly exposes missing routine evidence.

Prompt:

```text
Repair only the missing evidence for this flow.

Flow: <FLOW-SLUG>
Missing or unsafe claim:
<claim>

Affected program: <PROGRAM_NAME>
Affected routines from flow analyzer:
<routine names>

Run legacy-ibmi-program-analyzer for at most 5 routine bodies.
Update compact program artifacts.
Then update the flow only for the affected edge/data/error/message claim.

Do not restart the whole flow.
```

中文 Prompt:

```text
请只修复这个 flow 缺失的证据，不要重跑整个 flow。

Flow: <FLOW-SLUG>
缺失或不安全的 claim:
<claim>

受影响 program: <PROGRAM_NAME>
flow analyzer 指出的受影响 routines:
<routine names>

请运行 legacy-ibmi-program-analyzer，本轮最多读取 5 个 routine body。
更新 compact program artifacts。
然后只更新这个 flow 里受影响的 edge / data / error / message claim。

不要重启整个 flow analysis。
```

### Step 7: Module Assembly

Use this when multiple approved or reviewable flows belong to one business
module.

Prompt:

```text
Use legacy-ibmi-module-analyzer to assemble a module review package.

Module slug: <MODULE-SLUG>
Business name: <module business name>
Scope statement: <scope>
In-scope flows:
<flow artifact paths>

Use flow artifacts and present compact program artifacts first. Optional
program sidecars are required only when triggered or when module evidence needs
them.
Do not concatenate full flow Markdown or full program-analysis Markdown.

Token constraint:
- Do not read routine bodies at module level.
- If a module claim depends on missing routine evidence, route back through
  flow repair and program deep-read batches.

Output required:
- module-overview.md
- 03-program-flow.md
- 04-data-flow.md
- module-review-checklist.md

SME review must clearly separate:
- confirmed_from_code
- confirmed_by_sme
- inferred_with_evidence
- needs_sme_review
- TBD / blocked
```

中文 Prompt:

```text
请使用 legacy-ibmi-module-analyzer 组装 module review package。

Module slug: <MODULE-SLUG>
Business name: <module business name>
Scope statement: <scope>
In-scope flows:
<flow artifact paths>

优先使用 flow artifacts 和已经存在的 compact program artifacts。optional
program sidecars 只有被触发，或 module evidence 需要时才必须提供。
不要拼接完整 flow Markdown，也不要拼接完整 program-analysis Markdown。

Token 限制:
- module 层不要读取 routine body。
- 如果某个 module claim 依赖缺失的 routine evidence，请通过 flow repair
  和 program deep-read batches 回补。

必须产出:
- module-overview.md
- 03-program-flow.md
- 04-data-flow.md
- module-review-checklist.md

SME review 必须清楚区分:
- confirmed_from_code
- confirmed_by_sme
- inferred_with_evidence
- needs_sme_review
- TBD / blocked
```

### Step 8: Module SME Sign-Off

Prompt:

```text
Prepare SME sign-off questions for this module.

Use:
- module-overview.md
- 03-program-flow.md
- 04-data-flow.md
- module-review-checklist.md
- flow TBDs
- program coverage ledgers

Do not introduce new business claims.
Group questions by:
1. Module scope
2. Program Flow coverage
3. Data Flow and persistence
4. Calculation / validation rules
5. Exception handling and messages
6. BRD eligibility

For each question, show:
- evidence source
- why SME decision is needed
- impact if unresolved
```

中文 Prompt:

```text
请为这个 module 准备 SME sign-off questions。

使用:
- module-overview.md
- 03-program-flow.md
- 04-data-flow.md
- module-review-checklist.md
- flow TBDs
- program coverage ledgers

不要引入新的 business claims。
请按以下主题分组问题:
1. Module scope
2. Program Flow coverage
3. Data Flow and persistence
4. Calculation / validation rules
5. Exception handling and messages
6. BRD eligibility

每个问题都要展示:
- evidence source
- 为什么需要 SME 决策
- 如果不解决，会影响什么
```

## Phased Rollout For Token-Limited Teams

### Phase 1: One Program Pilot

Goal: prove that SMEs can review one program without reading the whole source.

Run:

1. Program index preflight.
2. One five-routine deep-read batch.
3. Program SME review.

Exit criteria:

- SME can see calculation, validation, exception, messages, and file I/O.
- Coverage ledger clearly shows `deep_read` vs `indexed_only`.
- No full-source prompt is needed.

### Phase 2: One Flow Pilot

Goal: prove that one transaction can be assembled without re-reading all
program source.

Run:

1. Core program artifacts for each involved program, plus triggered sidecars
   only when a flow claim needs them.
2. Flow assembly.
3. Flow repair batches only for missing critical routines.

Exit criteria:

- Transaction path is visible.
- Cross-program field lineage is visible.
- Persistence and error propagation are tied to compact evidence.
- Missing evidence routes back to specific routine batches, not the whole flow.

### Phase 3: One Module Pilot

Goal: prove that module review can aggregate several flows without exploding
token usage.

Run:

1. Module assembly from flow artifacts.
2. Module SME sign-off questions.
3. BRD eligibility review.

Exit criteria:

- Program Flow and Data Flow are consistent.
- SME can see coverage gaps by flow/program/data object.
- BRD-eligible claims are separated from TBDs and context-only claims.

### Phase 4: Standard Operating Procedure

Goal: make the process repeatable.

Add team rules:

- Every program run starts with source index and tier classification. Normal
  programs stay lightweight; complex/large programs add triggered sidecars.
- Every LLM turn has a five-routine maximum.
- Every flow claim must cite compact program artifacts or a named SME waiver.
- Every module claim must cite flow artifacts, compact program artifacts, or a
  named SME decision.
- No BRD/spec handoff from `indexed_only` behavior.

## What Should Block

Block or route back when:

- source is missing or incomplete;
- raw unredacted production data is present;
- `chain_ready` was requested but inventory/object IDs are missing;
- trigger model is unclear for a flow;
- module boundary is unclear;
- a state-changing routine needed by a flow/module is still `indexed_only`;
- calculation, validation, exception, message, file I/O, or SQL behavior is
  claimed without source evidence, runtime evidence, or SME approval.

Do not block exploratory review just because the whole system is not complete.
Mark gaps visibly and keep moving in small batches.

## SME Quick Checklist

Before approving a program, flow, or module review, the SME should be able to
answer:

- Do I understand which code path this review covers?
- Are calculation rules visible and evidence-backed?
- Are validation failures and messages visible?
- Are exception paths and rollback/commit behavior visible where relevant?
- Are file/table reads and writes visible?
- Are SQLRPGLE/free-format statements indexed when present?
- Are open TBDs named clearly?
- Are unreviewed routines marked `indexed_only` instead of silently treated as
  confirmed?
- Is the next action a specific routine batch, flow repair, module question, or
  BRD handoff decision?
