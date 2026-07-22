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

## 3. Reader-First Program Analysis Merger

Use this after every requested program has a finalized `program-analysis.md`
and the SME wants one evidence-complete review of the selected program set.
This v0.4.0 workflow does not reconstruct a transaction flow.

### English

```text
Use legacy-ibmi-flow-analyzer v0.4.0.

Prepare and complete one Reader-First Program Analysis Merger run.

Review name: <business-readable review name>
Programs in SME navigation order: PROGRAM_A, PROGRAM_B, PROGRAM_C
Program artifact root: <current-run delivery workspace or approved local clone>
Output parent: <parent directory for the generated bundle>
Profile: standard_reader_first
Artifact repo mode: approved_document_repo
Source root: <optional; only for targeted recovery of missing programs>

Input and readiness rules:
- Resolve each distinct requested program exactly once and run the upstream
  final contract validator for each artifact.
- For every program, use the complete content of these five H2 sections in
  program-analysis.md as the semantic primary input:
  1. Program Reading Summary
  2. Calculation Logic
  3. Validation Logic
  4. Exception Handling
  5. Message Inventory
- Sidecars support readiness and reconciliation; they do not replace those
  five complete sections.
- Use approved_document_repo by default. Use current_run only when I explicitly
  select an active delivery workspace. Never fall back to arbitrary
  historical or remote output.
- If any requested program is missing, ambiguous, incomplete, non-terminal, or
  invalid, write no formal review. Create a targeted missing-program queue only
  for exact paths from fresh inventory; put unresolved paths in
  blocked-programs.csv. Do not launch a whole-repository scan.

Preparation and synthesis rules:
- Deterministic tooling prepares the manifest, readiness ledger, lossless
  reader-first source pack, normalized source facts, and pending coverage. It
  must not write a review skeleton, claim semantic completion, or call an
  external LLM service.
- As the LLM executing this skill, read the entire source pack and synthesize
  cross-program themes while preserving program, routine, carrier, guard,
  effect/outcome, exact messages/status/literals, evidence, and source_fact_id.
- The bundle folder and formal filename must use the unique flow-plus-program-
  set identity. Write exactly one
  <folder_slug>/<folder_slug>--sme-core-review.md and no generic alias.
- Before writing the formal review, reconcile every fact as included, merged,
  or specifically justified excluded_non_core. Final coverage must contain
  zero pending items, and every included/merged fact must appear on the same
  visible anchored review row as its source fact reference and typed values.
- Run final five-way manifest/source-pack/facts/coverage/review validation and
  repair every finding before SME/Dify handoff.

Safety rules:
- Treat the SME program order as navigation only, never as a confirmed call or
  execution sequence.
- Do not reconstruct or invent a full flow, calls, business rules, service
  boundaries, or modernization decisions.
- Do not add Trigger Inventory, Nodes, Edges, Transaction Call Map, Replay,
  Persistence, Lineage, UI Surfaces, Capability Seeds, or SME Checklist.
- Preserve every exact message ID, status value, return code, response literal,
  SQLSTATE, CPF/MCH/RNX/CPD message, operator text, and shop-local token.
```

### 中文

```text
请使用 legacy-ibmi-flow-analyzer v0.4.0。

请准备并完成一次 Reader-First Program Analysis Merger。

Review name: <业务可读的 review 名称>
Programs in SME navigation order: PROGRAM_A, PROGRAM_B, PROGRAM_C
Program artifact root: <本轮 delivery workspace 或 approved local clone>
Output parent: <生成 bundle 的父目录>
Profile: standard_reader_first
Artifact repo mode: approved_document_repo
Source root: <可选；仅用于缺失 program 的 targeted recovery>

输入与 readiness 规则:
- 每个 distinct requested program 只解析一次，并对每份 artifact 运行 upstream
  final contract validator。
- 每个 program 都要把 program-analysis.md 中以下五个 H2 的完整内容作为主要
  语义输入：
  1. Program Reading Summary
  2. Calculation Logic
  3. Validation Logic
  4. Exception Handling
  5. Message Inventory
- Sidecars 只支持 readiness 与 reconciliation，不能替代这五个完整 section。
- 默认使用 current_run。只有我显式选择 approved_document_repo 并提供 approved
  local clone 时才允许复用；不得回退到任意历史或 remote output。
- 任一 requested program 缺失、歧义、不完整、未达到 terminal status 或校验
  失败时，不得写 formal review。只能根据 fresh inventory 中的 exact path 创建
  targeted missing-program queue；无法确认路径的写入 blocked-programs.csv，
  不得触发 whole-repository scan。

准备与综合规则:
- Deterministic tooling 只准备 manifest、readiness ledger、无损 reader-first
  source pack、normalized source facts 和 pending coverage；不得写 review
  skeleton、声称语义完成或调用 external LLM service。
- 由当前执行这个 skill 的 LLM 读取完整 source pack，按跨程序主题综合，同时
  保留 program、routine、carrier、guard、effect/outcome、exact message/status/
  literal、evidence 和 source_fact_id。
- Bundle folder 与 formal filename 必须使用唯一的 flow-plus-program-set identity。
  只写一份 <folder_slug>/<folder_slug>--sme-core-review.md，不创建 generic alias。
- 写 formal review 前，每个 fact 必须被标记为 included、merged 或有具体理由的
  excluded_non_core。最终 coverage 必须 zero pending；每个 included/merged fact
  必须与 source fact reference 及 typed values 一起出现在同一个可见、带 anchor
  的 review row 中。
- SME/Dify handoff 前运行 manifest/source-pack/facts/coverage/review 五方 final
  validation，并修复全部 finding。

安全规则:
- SME program 顺序只用于 navigation，不能写成 confirmed call 或执行顺序。
- 不得重建或编造 full flow、calls、business rules、service boundaries 或
  modernization decisions。
- 不得加入 Trigger Inventory、Nodes、Edges、Transaction Call Map、Replay、
  Persistence、Lineage、UI Surfaces、Capability Seeds 或 SME Checklist。
- 保留每个 exact message ID、status value、return code、response literal、
  SQLSTATE、CPF/MCH/RNX/CPD message、operator text 和 shop-local token。
```
