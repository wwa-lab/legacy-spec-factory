# Flow Analysis Agent Prompt E2E Guideline

Use this guide to test `legacy-ibmi-flow-analyzer` internally with agent
runtimes that can keep state, run tools, inspect files, and continue through
multiple gates in one conversation, such as Codex or Claude Code.

For GitHub Copilot Chat, use the segmented guide instead:
[`flow-analysis-copilot-chat-e2e-guideline.md`](flow-analysis-copilot-chat-e2e-guideline.md).

The default test path is the compact SME program-set core review, not a full
transaction-flow artifact.

For interrupted runs or new-session handoff, use
[`flow-analysis-resume-guideline.md`](flow-analysis-resume-guideline.md).

## Test Objective

Validate that the skill can:

- accept one SME program flow or multiple named program-flow blocks
- use fresh source inventory cache before repo-level source scan
- analyze every distinct SME-provided program for the current run before
  assembling the program-set review
- reuse only artifacts produced earlier in the same run/batch when a program is
  repeated
- handle normal, complex, and large programs with tier-appropriate retained
  routine evidence
- write program artifacts to tier folders on the delivery working branch
- write one program-set review folder per SME flow under
  `modules/CAP-ID-0004-program_set_reviews/`
- produce `program-set-sme-core-review.md` with only the four core sections
- complete the review with evidence-backed SME content, not just a generated
  skeleton or lookup report
- pass `scripts/validate-program-set-core-review.py`

## Required Test Inputs

Prepare these values before running a prompt:

```text
Delivery working branch: develop-<person>
Delivery working checkout: /path/to/legacy-modernization-delivery
Source repo: /path/to/source-repo
Delivery profile: /path/to/delivery-profile.yaml
Reference paths, optional:
- /path/to/reference-pack.md
- /path/to/message-catalog.csv
Control files, optional:
- /path/to/status-code-table.csv
```

Team setup is not repeated in every prompt. It should already live in the
delivery profile:

```text
program_artifact_resolution_profile
delivery_workspace_profile
source_inventory_profile
```

For program-flow core review, do not provide or use a remote-main snapshot,
prior-run cache, or force-rescan file. If an older artifact matters, let Git
diff/PR review compare it after this run creates the current-run artifact.

Runtime trigger note:

- This guide assumes an agent runtime such as Codex or Claude Code.
- Give the complete prompt to the agent once.
- The phases inside the prompt are ordered gates inside one agent run, not
  separate user prompts.
- For Copilot Chat, do not use this document as a single prompt; use the
  segmented Copilot guide.

Parameter naming note:

- `legacy-ibmi-program-list-batch` may still use `--delivery-root` to mean the
  output root for generated per-program artifacts.
- `scripts/build-program-set-core-review.py` must not use `--delivery-root`.
  For the program-set builder, use `--working-root` as the current-run artifact
  root.
- When reporting Windows paths in Markdown, wrap full paths in backticks or
  fenced code blocks. A raw `\@` can render as `@`, hiding the separator before
  program names such as `@CU400P`; output directories must be path-joined as
  `...\normal_program\@CU400P`, not concatenated as
  `...\normal_program@CU400P`.
- Pass reference packs, dictionaries, message catalogs, code tables, and
  control files into per-program analysis prompts with `--reference-path` /
  `--control-file` when using program-list-batch. Treat them as supporting
  evidence for message/status/control-table meanings; they do not replace
  source evidence or SME approval.

When the prompt asks the agent/operator to build or validate a program-set core
review in the company Windows environment, use the installed flow skill router:
`py -3 .agents\skills\legacy-ibmi-flow-analyzer\scripts\program_set_core_review.py validate ...`.
If `py -3` is unavailable, rerun the same command with `python`. Use `python3` only on
macOS/Linux development machines.

## Prompt 1: Program-Evidence-First Single Flow Core Review Complete E2E

Use this when the expected result is one completed SME-ready core review, not
only the first manifest/build step.

This is one prompt. The phases below are ordered gates inside one run, not
three separate user questions.

### English

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run one SME-provided program flow all the way to a completed compact SME
program-set core review.
Do not create flow-<FLOW-SLUG>.md.
Do not stop after creating the manifest, review skeleton, source lookup report,
or placeholder compact artifacts.

This is a program-evidence-first run with no cross-run reuse:
1. First analyze every distinct program named in the SME flow from the current
   source repo and write current-run program-analysis artifacts to the delivery
   working branch.
2. If the same normalized program appears again in this same run/batch, reuse
   only the artifact already produced earlier in this run.
3. Then assemble those current-run program-analysis results into
   program-set-sme-core-review.md.

Do not check remote main, clone a remote-main snapshot, use older delivery
artifacts, or satisfy a program from another analyst's prior run. Git/PR review
can compare differences later.
Do not assemble the program-set review from placeholders or incomplete
program-analysis artifacts.

Runtime inputs:
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml
- Reference paths, optional:
  - /path/to/reference-pack.md
  - /path/to/message-catalog.csv
- Control files, optional:
  - /path/to/status-code-table.csv

Review name:
card auth posting core review

SME-provided program flow, preserve this order:
- @CU118
- CU257F
- CC050

Completion rule:
This run is complete only when:
- every SME-provided program appears in the manifest, Sources table, and Core
  Completeness Ledger
- every distinct SME-provided program has current-run completed program-analysis
  artifacts with enough routine evidence to populate the four SME sections, or
  a precise evidence-backed TBD
- repeated programs, if any, are marked reused_same_run only after an earlier
  current-run artifact exists
- every program has the required tier-appropriate program-level files: normal
  programs have lightweight validated artifacts; complex or large programs also
  have retained routine detail
- program-set-sme-core-review.md contains real rows under Calculation Logic,
  Validation Logic, Exception Handling, and Message Inventory
- there are no generic placeholder statements such as "No explicit CALL literal
  detected" unless they are tied to a specific missing-evidence row and next
  action
- scripts/validate-program-set-core-review.py passes

Phase 1 - build the current-run program worklist:
1. Treat @CU118 and CU118 as different program identities.
2. Deduplicate only exact normalized program repeats within this same SME
   batch; preserve the original SME order for assembly.
3. Do not check delivery remote main or any prior-run artifact cache.
4. Check source inventory cache:
   <source-root>/outputs/repo-scan/program-list.csv and scan-summary.yaml.
5. If source inventory cache is missing, stale, or the source tree is dirty,
   run repo-level inventory once, then use the refreshed program-list.csv to
   locate each program.
6. Classify every distinct program as normal_program, complex_normal_program,
   or large_extreme_program before writing final summaries.

Phase 2 - analyze every distinct program:
7. Use legacy-ibmi-program-list-batch when there is more than one distinct
   program and the runtime cannot safely process all programs in one continuous
   agent run. Otherwise, route each distinct program through
   legacy-ibmi-program-analyzer directly as needed.
8. Write artifacts to the delivery working branch under the tier folder from
   the delivery profile.
9. Build source-index.yaml first, then analyze the entry/mainline, validation,
   calculation, file I/O or SQL update, exception/message, and external-call
   routines needed for this SME flow.
10. Do not read more than five routine bodies per turn. For complex or large
    programs, continue in retained batches until the core SME sections can be
    supported.
11. Normal programs must keep:
   - program-analysis.md
   - program-analysis-summary.yaml
   - source-index.yaml
   - routine-index.md
   - message-inventory.yaml
   - optional sidecars when observed or needed: file-io-inventory.yaml,
     field-mutation-matrix.yaml, sql-inventory.yaml
12. Complex or large programs, or programs explicitly promoted for deep-read,
    must also keep routine-logic-details.md, routine-logic-details.yaml, and
    enough retained routine detail for weak-LLM handoff stability, such as
    deep-read-plan.md, all-routine-coverage-ledger.md, and
    routine-logic-details/deep-read-batch-*.md when more than one five-routine
    batch is needed.
13. Reject placeholder-only program artifacts. If a program artifact only says
    lightweight scan, no CALL literal, no obvious messages, or otherwise lacks
    business logic rows, first check whether the program is normal_program and
    whether the required lightweight artifacts validate with precise evidence
    scope. Do not force routine-logic-details or retained deep-read files for a
    normal_program solely because it is lightweight. Promote or continue
    deep-read only when density triggers appear, the program is complex/large,
    the user explicitly requests deep-read, or the four SME core sections cannot
    be filled with evidence-backed rows or precise per-program TBDs.
14. Read reference/control inputs when they are relevant to observed messages,
    status values, control-file lookups, field meanings, or validation rules.
    Treat them as supporting evidence only; do not invent behavior absent from
    source or SME-approved evidence.
15. Do not proceed to program-set assembly while any program needed by the SME
    flow only has index-level or placeholder-level analysis. If evidence is
    genuinely unavailable, record a precise per-program TBD and reason.

Phase 3 - build and fill the program-set review:
16. After every distinct SME-provided program has current-run completed
    artifacts or a precise blocked/pending state, build or rebuild:
    modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
      program-set-core-input-manifest.yaml
      program-set-sme-core-review.md
    Do not write the review directly under
    modules/CAP-ID-0004-program_set_reviews/.
    Use the program-set builder with --program-first and --working-root only.
    Do not pass --delivery-root to the program-set builder.
17. Confirm the manifest uses run_resolution values:
    analyzed_this_run, reused_same_run, pending_source, or
    blocked_missing_source. It must not contain central_lookup_result or
    found_on_remote_main.
18. Fill program-set-sme-core-review.md from the current-run per-program
    artifacts. Prefer compact artifacts, and use program-analysis.md only for
    targeted clarification. Keep rows grouped by the SME program order.
19. The review must be self-contained for SME reading: do not make the SME jump
    to per-program documents to understand Calculation Logic, Validation Logic,
    Exception Handling, or Message Inventory.
20. The four core sections must contain evidence-backed rows:
    - Calculation Logic: assignments, derived values, counters, totals, dates,
      flags, or explicit "no calculation observed" TBD rows with evidence scope
    - Validation Logic: checks, reject conditions, statuses, return codes, and
      outcomes
    - Exception Handling: monitored errors, file or SQL failures, message paths,
      rollback/continue/stop behavior, and unresolved paths
    - Message Inventory: every exact message ID, status, return code, SQLSTATE,
      CPF/MCH/RNX/CPD code, operator text, literal, or shop-local token observed
21. Each core row must include the actual logic, condition, carrier, outcome,
    and message/status text needed to understand the behavior inside
    program-set-sme-core-review.md. Evidence IDs, source lines, and artifact
    names may appear in Supporting Detail / Detail Refs, but they must not
    replace the explanation.
22. If a section truly has no observed evidence for a program, add a precise
    TBD row naming the program, routine/window inspected, missing artifact or
    evidence type, and next action. Do not replace the section with a generic
    sentence.
23. Run scripts/validate-program-set-core-review.py. If it fails, fix the
    review and rerun until it passes.

Report:
- run_resolution by program
- source inventory cache freshness/action
- analyzed programs and output artifact folders
- repeated programs reused_same_run, if any
- per-program analysis completeness and any routines still indexed_only
- output folder
- validator result
- remaining SME TBDs, if any
```

### 中文

```text
请使用 legacy-ibmi-flow-analyzer。

目标:
请把一个 SME 提供的 program flow 完整跑完，产出一份可交给 SME review 的
compact program-set core review。
不要生成 flow-<FLOW-SLUG>.md。
不要在生成 manifest、review skeleton、source lookup report，或 placeholder
compact artifacts 之后就停止。

这是 no cross-run reuse 的 program-evidence-first 运行:
1. 先从当前 source repo 分析 SME flow 里每一个 distinct program，并把本次
   program-analysis artifacts 写到 delivery working branch。
2. 如果同一个 normalized program 在同一次 run/batch 里再次出现，只能复用本次
   前面已经产出的 artifact。
3. 然后把这些 current-run program-analysis 结果组装成
   program-set-sme-core-review.md。

不要检查 remote main，不要 clone remote-main snapshot，不要使用旧 delivery
artifact，也不要用其他 analyst 之前的运行结果来满足本次 evidence gate。旧差异
留给 Git/PR review 比较。
不要用 placeholder 或 incomplete program-analysis artifact 直接组装 review。

Runtime inputs:
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml
- Reference paths，可选:
  - /path/to/reference-pack.md
  - /path/to/message-catalog.csv
- Control files，可选:
  - /path/to/status-code-table.csv

Review name:
card auth posting core review

SME 提供的 program flow，请保留这个顺序:
- @CU118
- CU257F
- CC050

完成标准:
这次运行只有在下面条件全部满足时才算完成:
- 每一个 SME 提供的 program 都出现在 manifest、Sources table 和 Core
  Completeness Ledger 里
- 每一个 distinct SME-provided program 都有本次完成的 program-analysis
  artifacts，并且有足够 routine evidence 支撑四个 SME 核心区；如果确实无法
  获取证据，必须留下精确的 evidence-backed TBD
- 重复 program 只有在本次前面已经产出 artifact 后，才能标成 reused_same_run
- 每个 program 都有按 tier 要求的 program-level 文件：normal program 保持
  lightweight validated artifacts；complex 或 large program 还必须有 retained
  routine detail
- program-set-sme-core-review.md 的 Calculation Logic、Validation Logic、
  Exception Handling 和 Message Inventory 下面都有真实内容行
- 不允许只有泛泛的 placeholder，例如 "No explicit CALL literal detected"；
  除非它绑定到具体缺失证据行和下一步动作
- scripts/validate-program-set-core-review.py 通过

Phase 1 - 建本次 program worklist:
1. @CU118 和 CU118 是不同 program identity，不要互相匹配。
2. 只对同一个 SME batch 内 exact normalized program 的重复项去重；assembly
   时仍保留 SME 原始顺序。
3. 不检查 delivery remote main，也不检查任何 prior-run artifact cache。
4. 检查 source inventory cache:
   <source-root>/outputs/repo-scan/program-list.csv 和 scan-summary.yaml。
5. 如果 source inventory cache 缺失、stale，或 source tree dirty，先跑一次
   repo-level inventory，再用刷新后的 program-list.csv 定位每个 program。
6. 写最终总结前，先把每个 distinct program 分类为 normal_program、
   complex_normal_program 或 large_extreme_program。

Phase 2 - 分析每一个 distinct program:
7. 如果有多个 distinct program，且当前 runtime 不能在一个连续 agent run 里稳定
   处理所有 program，则使用 legacy-ibmi-program-list-batch 生成队列；否则按需
   直接把每个 distinct program 路由给 legacy-ibmi-program-analyzer。
8. 按 delivery profile 的 tier folder 写入 delivery working branch。
9. 先生成 source-index.yaml，然后分析这个 SME flow 需要的 entry/mainline、
   validation、calculation、file I/O 或 SQL update、exception/message、
   external-call routines。
10. 每轮不要读取超过 5 个 routine body。对于 complex 或 large program，要用
    retained batches 持续分析，直到四个 SME 核心区有足够证据支撑。
11. normal program 至少需要:
   - program-analysis.md
   - program-analysis-summary.yaml
   - source-index.yaml
   - routine-index.md
   - message-inventory.yaml
   - 如观察到或本次需要，还要有 optional sidecars:
     file-io-inventory.yaml、field-mutation-matrix.yaml、sql-inventory.yaml
12. complex、large program，或明确触发 deep-read continuation 的 program，
    还必须有 routine-logic-details.md、routine-logic-details.yaml，并保留足够
    routine detail，保证弱 LLM 或不同执行者交接时输出稳定；如果超过一个
    five-routine batch，需要保留 deep-read-plan.md、
    all-routine-coverage-ledger.md 和
    routine-logic-details/deep-read-batch-*.md。
13. 拒绝 placeholder-only program artifacts。如果某个 program artifact 只写了
    lightweight scan、no CALL literal、no obvious messages，或没有业务逻辑行，
    先判断它是否是 normal_program，且 required lightweight artifacts 是否已经
    validate，并且 evidence scope 是否写清楚。不要仅仅因为 normal_program 是
    lightweight，就强制生成 routine-logic-details 或 retained deep-read 文件。
    只有出现 density trigger、program 是 complex/large、用户明确要求 deep-read，
    或四个 SME 核心区无法用 evidence-backed rows / 精确 per-program TBD 填写时，
    才 promote 或继续 deep-read。
14. 当 reference/control inputs 与已观察到的 message、status、control-file
    lookup、field meaning 或 validation rule 有关时，要读取它们；但它们只能作为
    supporting evidence，不能替代 source evidence 或 SME approval，也不能用来发明
    源码里没有的行为。
15. 只要 SME flow 需要的任何 program 还只有 index-level 或 placeholder-level
    analysis，就不要进入 program-set assembly。如果证据确实拿不到，必须记录
    精确的 per-program TBD 和原因。

Phase 3 - build 并填完整 program-set review:
16. 每一个 distinct SME-provided program 都有本次完成的 artifacts，或有精确
    blocked/pending state 后，build 或 rebuild:
    modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
      program-set-core-input-manifest.yaml
      program-set-sme-core-review.md
    不要直接写到 modules/CAP-ID-0004-program_set_reviews/ 根目录。
    运行 program-set builder 时只使用 --program-first 和 --working-root。
    不要把 --delivery-root 传给 program-set builder。
17. 确认 manifest 使用 run_resolution:
    analyzed_this_run、reused_same_run、pending_source、
    blocked_missing_source。manifest 里不能有 central_lookup_result 或
    found_on_remote_main。
18. 从 current-run per-program artifacts 填写 program-set-sme-core-review.md。
    优先使用 compact artifacts，只在定点澄清时打开 program-analysis.md。
    行顺序要按 SME 提供的 program flow 分组。
19. 这个 review 必须让 SME 能直接读懂，不需要跳到各个 program 文档才能理解
    Calculation Logic、Validation Logic、Exception Handling 或 Message
    Inventory。
20. 四个核心区必须包含 evidence-backed rows:
    - Calculation Logic: assignments、derived values、counters、totals、dates、
      flags，或带 evidence scope 的明确 "no calculation observed" TBD 行
    - Validation Logic: checks、reject conditions、statuses、return codes 和
      outcomes
    - Exception Handling: monitored errors、file 或 SQL failures、message
      paths、rollback/continue/stop behavior 和 unresolved paths
    - Message Inventory: 每个观察到的 exact message ID、status、return code、
      SQLSTATE、CPF/MCH/RNX/CPD code、operator text、literal 或 shop-local token
21. 每个核心区的 row 都必须在 program-set-sme-core-review.md 里写出实际
    logic、condition、carrier、outcome 和 message/status text。Evidence ID、
    source line、artifact name 可以放在 Supporting Detail / Detail Refs 里，
    但不能用它们替代正文解释。
22. 如果某个 program 在某个 section 确实没有观察到证据，添加精确 TBD 行，
    写清 program、已检查的 routine/window、缺失 artifact 或 evidence type、
    以及下一步动作。不要用泛泛一句话替代整个 section。
23. 运行 scripts/validate-program-set-core-review.py。如果失败，修复 review
    并重新运行，直到通过。

Report:
- 每个 program 的 run_resolution
- inventory cache freshness/action
- analyzed programs 和 output artifact folders
- 如有重复 program，列出 reused_same_run
- 每个 program 的 analysis completeness，以及仍然 indexed_only 的 routines
- output folder
- validator result
- remaining SME TBDs，如有
```

## Prompt 2: Multiple Flow Core Review Batch

Use this to test whether the skill can process multiple SME flow blocks without
mixing them together.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Process multiple SME-provided program flows as a single working-branch batch.
Do not create flow-<FLOW-SLUG>.md.
Create one program-set review folder per flow.
Analyze each distinct SME-provided program first, then assemble each flow's
program-set review from those current-run completed program-analysis artifacts.
Do not use remote main or prior-run artifacts.

Runtime inputs:
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Flow 1 review name:
card auth posting core review
Programs, preserve order:
- @CU118
- CU257F
- CC050

Flow 2 review name:
nightly recon core review
Programs, preserve order:
- CC221
- CC224
- CC226

Flow 3 review name:
manual adjustment core review
Programs, preserve order:
- CU257F
- CC586
- CC779

Expected behavior:
1. Split this input into three independent flow blocks.
2. Build one distinct program analysis worklist across all flow blocks while
   preserving each flow's SME order for assembly.
3. Reuse one source inventory cache for all flows.
4. Reuse one delivery working branch, develop-leo, for the batch.
5. Analyze each distinct program once, using legacy-ibmi-program-list-batch
   only when the runtime needs durable queue control; otherwise route programs
   directly through legacy-ibmi-program-analyzer as needed. Write each
   program-level artifact set to the correct tier folder.
6. For repeated programs such as CU257F, reuse the newly generated current-run
   program-analysis artifact when assembling each flow; do not rescan it just
   because it appears in a second flow.
7. Generate one folder per flow:
   modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
   modules/CAP-ID-0004-program_set_reviews/nightly_recon_core_review/
   modules/CAP-ID-0004-program_set_reviews/manual_adjustment_core_review/
8. Each folder must contain its own program-set-core-input-manifest.yaml and
   program-set-sme-core-review.md.
9. Validate every generated review independently.

Report:
- per-flow output folder
- per-flow validator result
- distinct programs analyzed
- repeated programs reused_same_run from current-run artifacts
- source inventory cache status
- any flow blocked by stale inventory, missing source, or incomplete
  per-program analysis
```

## Prompt 3: Source Inventory Cache Gate Test

Use this when testing the rule that repo-level inventory should not rerun when
`outputs/repo-scan` is fresh. This is a preflight-only smoke test; it is not a
completed SME program-set review test.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run source inventory cache preflight for this program flow before any source
scan. Do not check remote main or prior-run artifacts. This test may stop after
reporting source_inventory and next action; Prompt 1 is the completed-review
test.

Runtime inputs:
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
inventory cache gate smoke test

Programs:
- <PROGRAM-1>
- <PROGRAM-2>

Expected behavior:
1. Build the current-run worklist from the SME program list.
2. Check:
   <source-root>/outputs/repo-scan/program-list.csv
   <source-root>/outputs/repo-scan/scan-summary.yaml
3. If scan-summary.yaml.source_revision_key matches the current clean Git
   source HEAD, report source_inventory.action = reuse_inventory.
4. If missing, stale, or dirty, report source_inventory.action =
   rerun_repo_inventory_scan and rerun repo inventory before targeted program
   scan.
5. The manifest should mark programs without current-run artifacts as
   pending_source or blocked_missing_source, not found/not-found on remote main.

Report the manifest source_inventory section and the next action.
```

## Prompt 4: No Cross-Run Reuse Guard Test

Use this to test that an older delivery artifact does not short-circuit the
program-flow run.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a compact SME program-set core review while ignoring any older
delivery artifacts for these programs. Do not create flow-<FLOW-SLUG>.md.

Runtime inputs:
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
card auth posting no cross-run reuse test

SME-provided program flow, preserve this order:
- CU257F
- CC050

Known condition:
CU257F may already have an older artifact on another branch or in a prior run.

Expected behavior:
1. Do not check or reuse the older artifact during program-flow assembly.
2. Analyze CU257F from the current source repo and write the current-run
   artifact to the delivery working branch.
3. Analyze CC050 from the current source repo and write the current-run
   artifact to the delivery working branch.
4. Run the program-set builder with --working-root only.
5. Confirm the manifest records run_resolution: analyzed_this_run for both
   programs, unless a source/evidence blocker is recorded.
6. Confirm the manifest does not contain central_lookup_result,
   found_on_remote_main, force_rescan, or remote_main_artifact_root.
7. Fill the four core SME sections from current-run artifacts.
8. Run the validator before SME handoff.

Report:
- current-run artifact path for each program
- manifest run_resolution fields
- validator result
```

## Prompt 5: Validation And PR Summary

Use this after the reviews are generated and filled.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Validate generated program-set SME core reviews and prepare a PR-ready summary.

Review folders:
- modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
- modules/CAP-ID-0004-program_set_reviews/nightly_recon_core_review/

For each folder:
1. Run scripts/validate-program-set-core-review.py against:
   - program-set-core-input-manifest.yaml
   - program-set-sme-core-review.md
2. Confirm every manifest program appears in Sources and Core Completeness
   Ledger.
3. Confirm the review does not contain Nodes, Edges, Replay, Persistence,
   Lineage, UI Surfaces, Capability Seeds, or SME Checklist.
4. Confirm the manifest uses run_resolution, not central_lookup_result.

Return:
- validation result per review folder
- summary of current-run analyzed program artifacts used by each review
- source inventory cache status
- SME review focus
- PR summary bullets
```

## Prompt 6: Explicit Full Transaction Flow

Use this only when the internal test intentionally wants the full
`flow-<FLOW-SLUG>.md` artifact. This is not the default SME core-review path.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a full transaction-flow analysis for one business event.
This request explicitly asks for flow-<FLOW-SLUG>.md.

Analysis intent:
standalone_exploratory

Trigger context:
- Trigger model: <batch/menu/subfile/f-key/db-trigger/scheduler/api>
- Business event name: <SME business event name>
- Entry program/object: <PROGRAM or config object>

Approved compact program analysis inputs:
- <program artifact folder 1>
- <program artifact folder 2>

Required behavior:
1. Do not infer calls, data flow, persistence, or exception propagation without
   upstream compact artifacts or SME/config evidence.
2. Include Transaction Call Map, Nodes, Edges, Cross-Program Data Flow, Replay,
   Field Lineage, Persistence Matrix, Branch Points, UI Surfaces when
   applicable, Error Propagation, Exception Chain, Capability Seeds, and Review
   Checklist.
3. Keep capability seeds as SME questions, not approved business rules.

Return the generated flow artifact path, blocking TBDs, and SME review focus.
```

## Expected Internal Test Evidence

Capture these results for each test run:

| Check | Expected result |
| --- | --- |
| Program-first analysis happens before assembly | Every distinct SME-provided program has current-run program-analysis artifacts before review fill |
| Exact program identity is preserved | `@CU118` and `CU118` do not match each other unless aliases are configured |
| Source inventory cache gate is visible | Manifest has `source_inventory.freshness` and `source_inventory.action` |
| Distinct programs are analyzed once per batch | Repeated programs reuse current-run artifacts during assembly |
| Cross-run reuse is off | Manifest has `run_profile.cross_run_reuse: false` and no `central_lookup_result` |
| Multiple flows remain separate | One `{review_slug}` folder per flow |
| Review shape is compact | Only Calculation, Validation, Exception, Message sections after control tables |
| Completeness ledger uses current columns | Core Completeness Ledger includes `Routine Logic Evidence` and `Message Inventory`, not the old `Calculation Logic / Validation Logic / Exception Handling` ledger columns |
| Review is complete enough for SME handoff | Four core sections contain evidence-backed rows or precise per-program TBD rows |
| Placeholder output is rejected | Generic lightweight-scan/no-CALL/no-message statements are replaced by routine-level evidence or named gaps |
| Output placement is scoped | Review is written under `program_set_review_parent/{review_slug}/`, not the parent folder |
| Validator runs | Each review folder has a pass/fail result |

## Common Test Failures

- The model creates one combined review for multiple unrelated flows.
- The model strips `@` from a program name.
- The model reruns repo inventory even though `outputs/repo-scan` is fresh.
- The model skips per-program analysis because an older artifact exists.
- The model puts full-flow sections into `program-set-sme-core-review.md`.
- The model writes a review directly under `CAP-ID-0004-program_set_reviews/`
  instead of a `{review_slug}` child folder.
- The model stops after generating `program-set-core-input-manifest.yaml` and a
  review skeleton.
- The model creates compact artifacts that only report simple source scan facts
  such as missing CALL literals, then fills the SME review from those
  placeholders instead of completing per-program routine analysis.
