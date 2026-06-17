# SME IBM i Analysis Prompt Cards

These copy-ready prompts help SMEs and analysts start common IBM i analysis
runs quickly:

- normal / general program analysis
- large program analysis with automatic five-routine batches
- merging multiple program results into one core SME review

Use the Chinese or English version directly in Codex, Claude Code, OpenCode, or
another runtime where the Legacy Spec Factory skills are available.

## Usage Notes

- Use `standalone_exploratory` for quick SME validation.
- Use `chain_ready` only when inventory/object linkage and required evidence are
  approved.
- Do not paste entire large source members into chat. Provide paths.
- For large programs, allow the skill to build indexes first, then deep-read at
  most five routines per turn.
- On Windows validation runs, prefer `py -3`; on macOS/Linux, use `python3`.
- Do not install packages or configure a Python environment during field runs.

---

## 1. General Program Analysis

Use this for a normal program or first-pass program review.

### English

```text
Use legacy-ibmi-program-analyzer.

Analyze one IBM i program for SME review.

Program: <PROGRAM_NAME>
Source path: <source file path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <program analysis output directory>

Rules:
- Start by building deterministic indexes and classifying the program tier.
- If the program is normal and no density trigger appears, keep the output
  lightweight.
- Do not deep-read more than 5 routine bodies in one turn.
- Do not produce a confident whole-program business narrative before coverage
  is visible.
- Use compact artifacts first.
- Mark missing message descriptions, copybooks, external program semantics, or
  SME-only meanings as TBD.
- If message/status/code values are observed and no message file/catalog,
  reference pack, source literal/comment, runtime evidence, or SME-approved
  description is supplied, mark the analysis not final-review-ready.

Required SME-first output:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory
5. File I/O / SQL state changes, if observed

Required artifacts:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
- message-inventory.md, only when message/status/code density triggers it
```

### 中文

```text
请使用 legacy-ibmi-program-analyzer。

请分析一个 IBM i program，目标是给 SME 快速 review。

Program: <PROGRAM_NAME>
Source path: <source 文件路径>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <program analysis 输出目录>

规则:
- 先建立确定性的 source index，并判断 program tier。
- 如果是普通 program，且没有密集度触发，请保持轻量输出。
- 每轮不要 deep-read 超过 5 个 routine body。
- 在 coverage 可见前，不要生成看起来很确定的 whole-program business narrative。
- 优先使用 compact artifacts。
- 缺失 message description、copybook、外部程序语义、只能由 SME 判断的含义，
  都要标记为 TBD。
- 如果发现 message/status/code，但没有提供 message file/catalog、
  reference pack、source literal/comment、runtime evidence 或 SME-approved
  description，请标记为 not final-review-ready。

SME 第一屏必须优先展示:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory
5. File I/O / SQL state changes，如果有观察到

必须产出:
- program-analysis.md
- program-analysis-summary.yaml
- source-index.yaml
- routine-index.md
- routine-logic-details.md
- routine-logic-details.yaml
- message-inventory.yaml
- message-inventory.md，只有 message/status/code 密集度触发时才需要
```

---

## 2. Large Program Analysis

Use this for 10,000+ line programs or programs with many routines, calls,
messages, file operations, SQL, or mutations. This prompt asks the agent to keep
going in five-routine batches without requiring the SME to type "continue" each
time.

### English

```text
Use legacy-ibmi-program-analyzer.

Analyze this large IBM i program in automatic five-routine batches.

Program: <PROGRAM_NAME>
Source path: <source file path>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <program analysis output directory>

Execution rules:
- Do not configure a Python environment.
- Do not install packages.
- For temporary validation on Windows, use py -3 first.
- On macOS/Linux, use python3.
- If Python is unavailable, stop and report the error.

Large-program rules:
- First build program-analysis.md, source-index.yaml, routine-index.md,
  all-routine-coverage-ledger.md, and deep-read-plan.md.
- Create `routine-logic-details/deep-read-batch-001.md` as the first retained
  checkpoint; continue with `deep-read-batch-002.md` and later files as needed.
- Every `deep-read-batch-*.md` file must use the same top-level layout:
  Calculation Logic, Validation Logic, Exception Handling, Scope,
  Batch Coverage Summary, Message Inventory, Routine Details.
- Do not paste real source code snippets into batch core logic sections. Use
  source identifiers, source ranges, evidence IDs, and RLOG links instead.
- Classify the program tier before writing the final narrative.
- Do not read the whole source into context.
- Each turn may deep-read at most 5 routine/window bodies.
- Continue automatically batch by batch until all actionable deep-read windows
  are processed, or until an external blocker prevents progress.
- Do not ask me to type "continue" after every batch.
- Do not mark chain_ready; keep status draft_exploratory unless I explicitly ask
  for chain_ready and provide approved inventory/evidence linkage.

Deep-read priority:
1. entry / mainline / dispatch
2. validation
3. calculation
4. file I/O, SQL, update/delete/write/commit/rollback
5. exception and message handling
6. external calls and queue/report handoffs

For each batch:
- Read only the selected source line windows.
- Update routine-logic-details.md and routine-logic-details.yaml.
- Update message-inventory.md/yaml when messages/status/codes are observed.
- Do not leave observed message/status/code rows as ID-only output. If message
  descriptions are unresolved, stop final delivery and request message
  file/catalog/reference pack or SME-approved descriptions.
- Update file-io-inventory, field-mutation-matrix, or sql-inventory only when
  triggered by observed evidence.
- Update all-routine-coverage-ledger.md.
- Keep program-analysis.md compact and SME-first; do not copy routine bodies
  into it.
- Report processed routines, updated artifacts, closed gaps, remaining
  indexed_only routines, and blockers.

Final SME-first output must show:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory with every exact message/code/literal
5. File I/O / SQL state changes, if observed
6. Open TBDs and SME questions
```

### 中文

```text
请使用 legacy-ibmi-program-analyzer。

请用自动分批模式分析这个 large IBM i program。

Program: <PROGRAM_NAME>
Source path: <source 文件路径>
Language: <RPGLE | SQLRPGLE | CLLE | COBOL | unknown>
Intent: standalone_exploratory
Output directory: <program analysis 输出目录>

执行规则:
- 不要配置 Python environment。
- 不要安装 packages。
- Windows 临时校验优先使用 py -3。
- macOS/Linux 使用 python3。
- 如果 Python 不可用，请停止并报告错误。

Large-program 规则:
- 先生成 program-analysis.md、source-index.yaml、routine-index.md、
  all-routine-coverage-ledger.md、deep-read-plan.md。
- 创建 `routine-logic-details/deep-read-batch-001.md` 作为第一批保留的
  checkpoint；需要时继续生成 `deep-read-batch-002.md` 等后续文件。
- 每个 `deep-read-batch-*.md` 必须使用同一个顶层 layout:
  Calculation Logic、Validation Logic、Exception Handling、Scope、
  Batch Coverage Summary、Message Inventory、Routine Details。
- 不要在 batch 核心逻辑区粘贴真实源码片段；使用 source identifiers、
  source ranges、evidence IDs 和 RLOG links。
- 先判断 program tier，再写最终 narrative。
- 不要把完整 source 读进上下文。
- 每轮最多 deep-read 5 个 routine/window body。
- 自动一批接一批处理，直到所有可处理 deep-read window 完成，或遇到外部
  blocker。
- 不要让我每批都输入“继续”。
- 不要标记 chain_ready；除非我明确要求 chain_ready，并提供 approved
  inventory/evidence linkage，否则保持 draft_exploratory。

Deep-read 优先级:
1. entry / mainline / dispatch
2. validation
3. calculation
4. file I/O、SQL、update/delete/write/commit/rollback
5. exception and message handling
6. external calls、queue/report handoff

每一批:
- 只读取被选中的 source line windows。
- 更新 routine-logic-details.md 和 routine-logic-details.yaml。
- 发现 message/status/code 时更新 message-inventory.md/yaml。
- 不要交付只有 message ID、没有描述的输出。如果 message description 仍未解析，
  停止 final delivery，并要求补充 message file/catalog/reference pack 或
  SME-approved descriptions。
- 只有观察到证据时，才按需更新 file-io-inventory、
  field-mutation-matrix、sql-inventory。
- 更新 all-routine-coverage-ledger.md。
- program-analysis.md 保持 compact 和 SME-first；不要把 routine body 复制进去。
- 汇报本批处理的 routines、更新的 artifacts、关闭的 gaps、仍然
  indexed_only 的 routines、以及 blockers。

最终 SME 第一屏必须展示:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory，包含 every exact message/code/literal
5. File I/O / SQL state changes，如果有观察到
6. Open TBDs and SME questions
```

---

## 3. Merge Multiple Program Results Into One Core SME Review

Use this after several programs have already been analyzed and the SME wants a
single compact review that contains only the core information.

### English

```text
Use legacy-ibmi-flow-analyzer.

Merge these existing program-analysis results into one compact SME core review.

Review name: <business flow or program set name>
Programs / analysis directories:
- <PROGRAM_A analysis directory>
- <PROGRAM_B analysis directory>
- <PROGRAM_C analysis directory>

Intent: standalone_exploratory

Rules:
- Do not re-read full source members.
- Do not concatenate full program-analysis.md files.
- Use compact artifacts first:
  program-analysis-summary.yaml,
  routine-logic-details.yaml,
  message-inventory.yaml,
  source-index.yaml,
  and optional sidecars only when they already exist and are needed.
- Use program-analysis.md only for targeted clarification.
- Create program-set-sme-core-review.md.
- Preserve the SME-provided order as navigation evidence, but do not generate
  flow-<FLOW-SLUG>.md unless full transaction-flow analysis is explicitly
  requested.

The output must contain only these sections:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory

Do not include:
- Nodes
- Edges
- Transaction Call Map
- Flow Replay Path
- Persistence Matrix
- Field Lineage
- UI Surfaces
- Capability Seeds
- SME Checklist

Message Inventory rule:
- Include every exact message ID, status value, return code, response literal,
  SQLSTATE, CPF/MCH/RNX/CPD message, operator text, or shop-local token observed.
- Do not replace individual messages with grouped labels.
- If the same exact message appears in multiple programs with the same meaning
  and trigger, one row may list all sources.
- If trigger, handling, carrier, or meaning differs, split into separate rows.
```

### 中文

```text
请使用 legacy-ibmi-flow-analyzer。

请把这些已经生成的 program-analysis 结果合并成一份 compact SME core review。

Review name: <business flow 或 program set 名称>
Programs / analysis directories:
- <PROGRAM_A analysis 目录>
- <PROGRAM_B analysis 目录>
- <PROGRAM_C analysis 目录>

Intent: standalone_exploratory

规则:
- 不要重新读取完整 source。
- 不要拼接完整 program-analysis.md。
- 优先使用 compact artifacts:
  program-analysis-summary.yaml、
  routine-logic-details.yaml、
  message-inventory.yaml、
  source-index.yaml、
  以及已经存在且本次确实需要的 optional sidecars。
- program-analysis.md 只允许用于定点澄清。
- 生成 program-set-sme-core-review.md。
- 保留 SME 输入顺序作为 navigation evidence，但除非明确要求 full
  transaction-flow analysis，不生成 flow-<FLOW-SLUG>.md。

输出只能包含这四个 section:
1. Calculation Logic
2. Validation Logic
3. Exception Handling
4. Message Inventory

不要包含:
- Nodes
- Edges
- Transaction Call Map
- Flow Replay Path
- Persistence Matrix
- Field Lineage
- UI Surfaces
- Capability Seeds
- SME Checklist

Message Inventory 规则:
- 必须包含 every exact message ID、status value、return code、response
  literal、SQLSTATE、CPF/MCH/RNX/CPD message、operator text、shop-local token。
- 不要用 grouped labels 代替每条 message。
- 如果同一条 exact message 在多个 program 中含义和触发条件相同，可以合并成
  一行并列出全部来源。
- 如果 trigger、handling、carrier、meaning 不同，必须拆成多行。
```
