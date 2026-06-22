# Flow Analysis Prompt E2E Guideline

Use this guide to test `legacy-ibmi-flow-analyzer` internally with realistic
SME inputs. The default test path is the compact SME program-set core review,
not a full transaction-flow artifact.

For interrupted runs or new-session handoff, use
[`flow-analysis-resume-guideline.md`](flow-analysis-resume-guideline.md).

## Test Objective

Validate that the skill can:

- accept one SME program flow or multiple named program-flow blocks
- use fresh source inventory cache before repo-level source scan
- resolve every SME-provided program to current program-analysis evidence
  before assembling the program-set review
- handle normal, complex, and large programs with tier-appropriate retained
  routine evidence
- reuse approved remote-main program-analysis artifacts when complete/current
  and support explicit force-rescan requests when refresh is needed
- write program artifacts to tier folders
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
Optional explicit approved reuse snapshot/cache: /tmp/legacy-modernization-delivery-main
Optional force rescan file: /path/to/force-rescan-programs.txt
```

Team setup is not repeated in every prompt. It should already live in the
delivery profile:

```text
delivery_artifact_lookup_profile
delivery_workspace_profile
source_inventory_profile
```

When the prompt asks the agent/operator to run a Python script in the company
Windows environment, use `py -3`, for example
`py -3 scripts\validate-program-set-core-review.py ...`. Use `python3` only on
macOS/Linux development machines.

## Prompt 1: Program-Evidence-First Single Flow Core Review Complete E2E

Use this when the expected result is one completed SME-ready core review, not
only the first manifest/build step.

This is the default field prompt for a new SME-provided program flow. It is a
two-stage workflow:

1. Resolve every program in the SME-provided flow to a current program-analysis
   result: reuse approved remote-main artifacts when they are complete/current,
   or analyze from source when they are missing, incomplete, stale, or explicitly
   refreshed.
2. Assemble those program-level results into one
   `program-set-sme-core-review.md`.

Central artifact reuse is part of this prompt. It is safe only when the reused
artifact is an approved program-analysis result with the required core files.

### English

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run one SME-provided program flow all the way to a completed compact SME
program-set core review.
Do not create flow-<FLOW-SLUG>.md.
Do not stop after creating the manifest, skeleton, source lookup report, or
placeholder compact artifacts.
This is a program-evidence-first run:
1. First resolve every program named in the SME flow to a completed
   program-analysis result. Reuse approved remote-main artifacts when they are
   complete/current; otherwise analyze the program from source.
2. Then assemble those resolved program-analysis results into
   program-set-sme-core-review.md.
Do not assemble the program-set review from placeholders or incomplete
program-analysis artifacts.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

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
- every SME-provided program has a completed or approved reusable
  program-analysis result with enough routine evidence to populate the four SME
  sections or a precise evidence-backed TBD
- every SME-provided program has the required program-level files:
  program-analysis.md, program-analysis-summary.yaml, source-index.yaml,
  routine-logic-details.yaml, message-inventory.yaml, and
  routine-logic-details.md / retained deep-read batch files when the program is
  complex or large
- program-set-sme-core-review.md contains real rows under Calculation Logic,
  Validation Logic, Exception Handling, and Message Inventory
- there are no generic placeholder statements such as "No explicit CALL literal
  detected" unless they are tied to a specific missing-evidence row and next
  action
- scripts/validate-program-set-core-review.py passes

Phase 1 - resolve every program to program-analysis evidence:
1. Treat @CU118 and CU118 as different program identities.
2. Check delivery repo remote main snapshot/cache for each exact program
   folder.
3. For found_on_remote_main programs, reuse the approved remote-main
   program-analysis artifacts only if the required core files are present and
   complete enough for SME handoff. Do not rescan those programs.
4. If a remote-main artifact is missing required core files, is known stale, or
   has an explicit force-rescan request, route only that program to source
   analysis.
5. For programs that need source analysis, check source inventory cache:
   <source-root>/outputs/repo-scan/program-list.csv and scan-summary.yaml.
6. If source inventory cache is missing, stale, or the source tree is dirty,
   run repo-level inventory once, then use the refreshed program-list.csv to
   locate each program that needs source analysis.
7. Classify every source-analyzed program as normal_program,
   complex_normal_program, or large_extreme_program before writing final
   summaries.

Phase 2 - analyze only programs not resolved by approved reuse:
8. For each program not resolved by approved remote-main reuse, run
   legacy-ibmi-program-analyzer according to its tier and write its artifacts to
   the delivery working branch under the tier folder from the delivery profile.
9. Build source-index.yaml first, then analyze the entry/mainline, validation,
   calculation, file I/O or SQL update, exception/message, and external-call
   routines needed for this SME flow.
10. Do not read more than five routine bodies per turn. For complex or large
   programs, continue in retained batches until the core SME sections can be
   supported.
11. Every program, whether reused from remote-main or analyzed in this run, must
    have at least:
   - program-analysis.md
   - program-analysis-summary.yaml
   - source-index.yaml
   - routine-logic-details.md
   - routine-logic-details.yaml
   - message-inventory.yaml
   - optional sidecars when observed or needed: file-io-inventory.yaml,
     field-mutation-matrix.yaml, sql-inventory.yaml
12. Complex or large programs must also keep enough retained routine detail for
    weak-LLM handoff stability, such as deep-read-plan.md,
    all-routine-coverage-ledger.md, and routine-logic-details/deep-read-batch-*.md
    when more than one five-routine batch is needed.
13. Reject placeholder-only program artifacts. If a program artifact only says
    lightweight scan, no CALL literal, no obvious messages, or otherwise lacks
    business logic rows, go back to that program's source-index and deep-read
    the routines needed to explain calculation, validation, exception handling,
    messages, and state changes.
14. Do not proceed to program-set assembly while any program needed by the SME
    flow only has index-level or placeholder-level analysis. If evidence is
    genuinely unavailable, record a precise per-program TBD and reason.

Phase 3 - build and fill the program-set review:
15. After every SME-provided program has been resolved to approved remote-main
    artifacts or completed working-branch program-analysis artifacts, build or
    rebuild:
    modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
      program-set-core-input-manifest.yaml
      program-set-sme-core-review.md
    Do not write the review directly under
    modules/CAP-ID-0004-program_set_reviews/.
    Use the builder with --program-first and --working-root. The builder should
    reuse approved remote-main artifacts for found_on_remote_main programs and
    use working-branch artifacts for newly analyzed or force-rescanned programs.
16. Fill program-set-sme-core-review.md from the resolved per-program artifacts.
    Prefer compact artifacts, and use program-analysis.md only for targeted
    clarification. Keep rows grouped by the SME program order.
17. The four core sections must contain evidence-backed rows:
    - Calculation Logic: assignments, derived values, counters, totals, dates,
      flags, or explicit "no calculation observed" TBD rows with evidence scope
    - Validation Logic: checks, reject conditions, statuses, return codes, and
      outcomes
    - Exception Handling: monitored errors, file or SQL failures, message paths,
      rollback/continue/stop behavior, and unresolved paths
    - Message Inventory: every exact message ID, status, return code, SQLSTATE,
      CPF/MCH/RNX/CPD code, operator text, literal, or shop-local token observed
18. If a section truly has no observed evidence for a program, add a precise
    TBD row naming the program, routine/window inspected, missing artifact or
    evidence type, and next action. Do not replace the section with a generic
    sentence.
19. Run scripts/validate-program-set-core-review.py. If it fails, fix the
    review and rerun until it passes.

Report:
- lookup result by program
- remote-main artifacts reused
- inventory cache freshness/action
- analyzed programs and output artifact folders
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
这是 program-evidence-first 的运行:
1. 先把 SME flow 里列出的每一个 program resolve 成完成的 program-analysis
   结果。remote-main 上有完整且当前有效的 approved artifact 就复用；否则从
   source repo 分析该 program。
2. 然后把这些 resolved program-analysis 结果组装成
   program-set-sme-core-review.md。
不要用 placeholder 或 incomplete program-analysis artifact 直接组装
program-set review。

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

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
- 每一个 SME 提供的 program 都已经有 completed 或 approved reusable
  program-analysis 结果，并且有足够的 routine evidence 支撑四个 SME 核心区，
  或者留下精确的 evidence-backed TBD
- 每一个 SME 提供的 program 都有必需的 program-level 文件:
  program-analysis.md、program-analysis-summary.yaml、source-index.yaml、
  routine-logic-details.yaml、message-inventory.yaml；如果是 complex 或 large
  program，还要保留 routine-logic-details.md 或 retained deep-read batch 文件
- program-set-sme-core-review.md 的 Calculation Logic、Validation Logic、
  Exception Handling 和 Message Inventory 下面都有真实内容行
- 不允许只有泛泛的 placeholder，例如 "No explicit CALL literal detected"；
  除非它绑定到具体缺失证据行和下一步动作
- scripts/validate-program-set-core-review.py 通过

Phase 1 - 把每一个 program resolve 成 program-analysis evidence:
1. @CU118 和 CU118 是不同 program identity，不要互相匹配。
2. 先检查 delivery repo remote main snapshot/cache，逐个查 exact program
   folder。
3. 对 found_on_remote_main 的 program，只有在 required core files 都存在，
   且足够支撑 SME handoff 时，才复用 approved remote-main program-analysis
   artifacts。不要重扫这些 program。
4. 如果 remote-main artifact 缺少 required core files、已知 stale，或有明确
   force-rescan request，只把对应 program 路由到 source analysis。
5. 对需要 source analysis 的 program 检查 source inventory cache:
   <source-root>/outputs/repo-scan/program-list.csv 和 scan-summary.yaml。
6. 如果 source inventory cache 缺失、stale，或 source tree dirty，先跑一次
   repo-level inventory，再用刷新后的 program-list.csv 定位 flow 里的每个
   需要 source analysis 的 program。
7. 在写最终总结前，先把每个 source-analyzed program 分类为 normal_program、
   complex_normal_program 或 large_extreme_program。

Phase 2 - 只分析没有被 approved reuse resolve 的 program:
8. 对每个没有被 approved remote-main reuse resolve 的 program，按 tier 运行
   legacy-ibmi-program-analyzer，并按 delivery profile 的 tier folder 写入
   delivery working branch。
9. 先生成 source-index.yaml，然后分析这个 SME flow 需要的 entry/mainline、
   validation、calculation、file I/O 或 SQL update、exception/message、
   external-call routines。
10. 每轮不要读取超过 5 个 routine body。对于 complex 或 large program，要用
   retained batches 持续分析，直到四个 SME 核心区有足够证据支撑。
11. 每个 program，不管是 remote-main 复用还是本次分析，都至少必须有:
   - program-analysis.md
   - program-analysis-summary.yaml
   - source-index.yaml
   - routine-logic-details.md
   - routine-logic-details.yaml
   - message-inventory.yaml
   - 如观察到或本次需要，还要有 optional sidecars:
     file-io-inventory.yaml、field-mutation-matrix.yaml、sql-inventory.yaml
12. complex 或 large program 必须保留足够 routine detail，保证弱 LLM 或
    不同执行者交接时输出稳定；如果超过一个 five-routine batch，需要保留
    deep-read-plan.md、all-routine-coverage-ledger.md 和
    routine-logic-details/deep-read-batch-*.md。
13. 拒绝 placeholder-only program artifacts。如果某个 program artifact 只写了
    lightweight scan、no CALL literal、no obvious messages，或没有业务逻辑行，
    回到该 program 的 source-index，继续 deep-read 能解释 calculation、
    validation、exception handling、messages 和 state changes 的 routines。
14. 只要 SME flow 需要的任何 program 还只有 index-level 或 placeholder-level
    analysis，就不要进入 program-set assembly。如果证据确实拿不到，必须记录
    精确的 per-program TBD 和原因。

Phase 3 - build 并填完整 program-set review:
15. 每一个 SME-provided program 都被 resolve 成 approved remote-main artifacts
    或 completed working-branch program-analysis artifacts 后，build 或 rebuild:
    modules/CAP-ID-0004-program_set_reviews/card_auth_posting_core_review/
      program-set-core-input-manifest.yaml
      program-set-sme-core-review.md
    不要直接写到 modules/CAP-ID-0004-program_set_reviews/ 根目录。
    运行 builder 时使用 --program-first 和 --working-root。builder 应该对
    found_on_remote_main programs 复用 approved remote-main artifacts，对 newly
    analyzed 或 force-rescanned programs 使用 working-branch artifacts。
16. 从 resolved per-program artifacts 填写 program-set-sme-core-review.md。
    优先使用 compact artifacts，只在定点澄清时打开 program-analysis.md。
    行顺序要按 SME 提供的 program flow 分组。
17. 四个核心区必须包含 evidence-backed rows:
    - Calculation Logic: assignments、derived values、counters、totals、dates、
      flags，或带 evidence scope 的明确 "no calculation observed" TBD 行
    - Validation Logic: checks、reject conditions、statuses、return codes 和
      outcomes
    - Exception Handling: monitored errors、file 或 SQL failures、message
      paths、rollback/continue/stop behavior 和 unresolved paths
    - Message Inventory: 每个观察到的 exact message ID、status、return code、
      SQLSTATE、CPF/MCH/RNX/CPD code、operator text、literal 或 shop-local token
18. 如果某个 program 在某个 section 确实没有观察到证据，添加精确 TBD 行，
    写清 program、已检查的 routine/window、缺失 artifact 或 evidence type、
    以及下一步动作。不要用泛泛一句话替代整个 section。
19. 运行 scripts/validate-program-set-core-review.py。如果失败，修复 review
    并重新运行，直到通过。

Report:
- 每个 program 的 lookup result
- remote-main artifacts reused
- inventory cache freshness/action
- analyzed programs 和 output artifact folders
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
program-set review from those completed program-analysis artifacts.

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
5. Analyze each distinct program once with legacy-ibmi-program-analyzer and
   write its program-level artifacts to the correct tier folder.
6. For repeated programs such as CU257F, reuse the newly generated
   working-branch program-analysis artifacts when assembling each flow; do not
   rescan it just because it appears in a second flow.
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
- repeated programs reused from the current working-branch artifacts
- source inventory cache status
- any flow blocked by stale inventory, missing source, or incomplete
  per-program analysis
```

## Prompt 3: Source Inventory Cache Gate Test

Use this when testing the rule that repo-level inventory should not rerun when
`outputs/repo-scan` is fresh.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Run central artifact lookup and source inventory cache preflight for this
program flow before any source scan.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
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
1. Check delivery remote main first.
2. For not_found_on_remote_main programs, check:
   <source-root>/outputs/repo-scan/program-list.csv
   <source-root>/outputs/repo-scan/scan-summary.yaml
3. If scan-summary.yaml.source_revision_key matches the current clean Git
   source HEAD, report source_inventory.action = reuse_inventory.
4. If missing, stale, or dirty, report source_inventory.action =
   rerun_repo_inventory_scan and rerun repo inventory before targeted program
   scan.

Report the manifest source_inventory section and the next action.
```

## Prompt 4: Explicit Program Refresh Override

Use this to test that an SME can intentionally refresh a program even though an
approved artifact already exists on delivery repo remote `main`.

```text
Use legacy-ibmi-flow-analyzer.

Goal:
Create a compact SME program-set core review, but intentionally refresh one
program that already exists on delivery repo remote main. Do not create
flow-<FLOW-SLUG>.md.

Runtime inputs:
- Delivery repo remote main snapshot/cache: /tmp/legacy-modernization-delivery-main
- Delivery working checkout: /path/to/legacy-modernization-delivery
- Delivery working branch: develop-leo
- Source repo: /path/to/source-repo
- Delivery profile: /path/to/delivery-profile.yaml

Review name:
card auth posting refresh test

SME-provided program flow, preserve this order:
- CU257F
- CC050

Force rescan requests:
- CU257F | SME requested refresh after major source or rule change

Expected behavior:
1. Check delivery repo remote main snapshot first for every program.
2. If CU257F is found_on_remote_main, do not reuse the old remote-main artifact
   for this review because an explicit force-rescan request exists.
3. Create a force-rescan file with one row:
   CU257F|SME requested refresh after major source or rule change
4. Run the targeted program analyzer for CU257F with:
   --force-rescan
   --rescan-reason "SME requested refresh after major source or rule change"
5. Write the refreshed CU257F draft artifacts to the delivery working branch
   tier folder.
6. Run the program-set builder with:
   --force-rescan-file <force-rescan-programs.txt>
   --working-root <delivery-working-checkout>
7. Confirm the manifest keeps:
   force_rescan: true
   rescan_reason: SME requested refresh after major source or rule change
   remote_main_artifact_root: <prior CU257F remote-main path>
   artifact_source: delivery_working_branch
8. Fill program-set-sme-core-review.md from the working-branch CU257F artifact
   plus normal remote-main or working artifacts for the other programs.
9. Run the validator before SME handoff.

Report:
- original remote-main artifact path for CU257F
- refreshed working-branch artifact path for CU257F
- manifest force_rescan fields
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

Return:
- validation result per review folder
- summary of analyzed program artifacts used by each review
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
| Program-first analysis happens before assembly | Every SME-provided program has program-analysis artifacts before review fill |
| Exact program identity is preserved | `@CU118` and `CU118` do not match each other unless aliases are configured |
| Source inventory cache gate is visible | Manifest has `source_inventory.freshness` and `source_inventory.action` |
| Distinct programs are analyzed once per batch | Repeated programs reuse current working-branch artifacts during assembly |
| Explicit force rescan is honored | Forced reuse/refresh tests record `force_rescan: true` and use working-branch artifacts |
| Multiple flows remain separate | One `{review_slug}` folder per flow |
| Review shape is compact | Only Calculation, Validation, Exception, Message sections after control tables |
| Review is complete enough for SME handoff | Four core sections contain evidence-backed rows or precise per-program TBD rows |
| Placeholder output is rejected | Generic lightweight-scan/no-CALL/no-message statements are replaced by routine-level evidence or named gaps |
| Output placement is scoped | Review is written under `program_set_review_parent/{review_slug}/`, not the parent folder |
| Validator runs | Each review folder has a pass/fail result |

## Common Test Failures

- The model creates one combined review for multiple unrelated flows.
- The model strips `@` from a program name.
- The model reruns repo inventory even though `outputs/repo-scan` is fresh.
- The model skips per-program analysis because an older remote-main artifact
  exists, even though the prompt did not explicitly authorize reuse.
- The model ignores an explicit force-rescan request or still fills the review
  from the old remote-main artifact.
- The model puts full-flow sections into `program-set-sme-core-review.md`.
- The model writes a review directly under `CAP-ID-0004-program_set_reviews/`
  instead of a `{review_slug}` child folder.
- The model stops after generating `program-set-core-input-manifest.yaml` and a
  review skeleton.
- The model creates compact artifacts that only report simple source scan facts
  such as missing CALL literals, then fills the SME review from those
  placeholders instead of completing per-program routine analysis.
