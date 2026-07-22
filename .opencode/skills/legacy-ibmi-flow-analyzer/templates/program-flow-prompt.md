<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0
-->

# Reader-First Program Analysis Merger Prompt

Use this prompt when an SME supplies a program list and wants one evidence-
complete core review. The program order is for navigation; this request does
not authorize transaction-flow reconstruction.

```text
请使用 legacy-ibmi-flow-analyzer，把以下已完成的 IBM i program analyses
合并成一份可供 SME / Dify 阅读的 reader-first SME Core Review。

Review name: <REVIEW-NAME>
Programs file: <PROGRAM-LIST-PATH>
Program artifact root: <CURRENT-RUN-ARTIFACT-ROOT>
Project root (default output location): <DELIVERY-PROJECT-ROOT>
Output parent (仅需覆盖默认 `<项目根目录>/outputs/` 时填写): <CUSTOM-OUTPUT-PARENT-OR-N/A>
Source root (仅缺失程序定向恢复时需要): <SOURCE-ROOT-OR-N/A>
Artifact repo mode: current_run
Profile: standard_reader_first
Flow slug: <FLOW-SLUG>
Program-set slug (可省略，由工具稳定派生): <PROGRAM-SET-SLUG>

Programs in SME navigation order:
1. PROGRAM_A
2. PROGRAM_B
3. PROGRAM_C

Optional SME context:
- Review scope / expected outcome:
- Known files, reports, messages, or exception cases:
- Approved terminology / notes:

执行要求：

1. 先运行 deterministic preparation。默认传入 `--project-root`，将产物写到
   `<项目根目录>/outputs/<FLOW-SLUG>--<PROGRAM-SET-SLUG>/`；`outputs/` 不存在时
   创建，存在时复用同 identity 的 preparation bundle。若该 bundle 已有正式 review，
   不得覆盖，必须先显式 archive。仅在明确给出 custom output parent 时使用
   `--output-dir`。只追加一次 `<FLOW-SLUG>--<PROGRAM-SET-SLUG>`，不要产生重复嵌套目录。
2. 对每个 distinct program 调用/复用 legacy-ibmi-program-analyzer 的 final
   validator。早期 scan 使用 `core_reader_first_lenient`：只有主
   `program-analysis.md` 缺失、身份错误，或五个 reader-first 核心 H2 为空/
   placeholder 才阻断。pending_deep_read、非终态 batch、缺少 RLOG、未解决的
   message description、sidecar drift 或其它 validator failure 要原样写入
   `pending_findings`，先让 source pack 进入综合准备；正式 review 仍须等严格
   final validator 和 zero-pending coverage。若程序确实没有观察到 message/
   status literal，`Message Inventory` 可以为空或缺失，但必须记录为
   no-observed-message pending，而不能伪造一条 message。
3. 默认只读取 current_run artifact。只有我明确改为
   `approved_document_repo` 时，才可读取指定的 approved local repo clone；
   不要静默复用历史 run、remote main 或他人的 output。
4. 每个 program 的主要语义输入必须是完整的 `<PROGRAM>-program-analysis.md`
   中五个 H2：Program Reading Summary、Calculation Logic、Validation Logic、
   Exception Handling、Message Inventory。source pack 必须无损保留，不能先压缩。
5. Deterministic scripts 只能准备 manifest、readiness、lossless source pack、
   normalized facts 和 pending coverage；不得生成 skeleton/formal review，
   不得调用外部 LLM，不得假装已经完成跨程序综合。
6. 只有每个 program 的 `artifact_readiness.status=ready`，且 manifest 为
   `review_status=ready_for_synthesis`、`artifact_readiness=ready`、
   `merge_coverage=pending` 后，才由正在执行本 skill 的 LLM 阅读完整 source
   pack，并在 working memory 中按跨程序主题进行综合与 anchor planning。
   不要简单拼接 program files。
7. 每个 normalized fact 都要保留稳定 `source_fact_id`。每个 planned material
   row 要有唯一 anchor / Review Row ID 和 Source Fact Refs；只有 coverage 中
   完整互相声明的 `merged` fact group 才能共用一个且只定义一次的 anchor。
   Overview 每行也必须有唯一 anchor 和已知 Source Fact Refs。
8. Coverage 中每个 fact 必须且只能是 included、merged、excluded_non_core、
   pending 之一。最终不得有 pending；material calculation、validation、
   exception、exact message/status/literal/generic handler token 不得以“精简”
   为由排除。有任何 pending 时不得写正式 review；如必须保存中间稿，只能用
   `<folder_slug>--partial-draft.md`，且不得使用 final front matter/H1。
9. Coverage 零 pending 后，Review 唯一正式文件名必须是
   `<folder_slug>--sme-core-review.md`。不要创建通用
   `program-set-sme-core-review.md` alias。写入完成时，将 manifest 更新为
   `review_status=complete_exploratory`、`artifact_readiness=ready`、
   `merge_coverage=complete`，并将 coverage/formal review 的 `review_status`
   统一设为 `complete_exploratory`。Coverage 同时必须设置
   `coverage_status=complete`，保持 `items` 与 `coverage_items` 完全一致，并
   重算 expected/item/status/per-program/per-section/RLOG counts。
10. standard_reader_first 默认把 Message Inventory 放在主阅读路径。
    minimal_reader_first 只能显式选择；它可以把 messages 移到 audit 的
    Message Coverage Control，但所有 exact message facts 和 coverage 必须保留。
11. Program 顺序仅是 SME navigation evidence。不得写成 confirmed execution
    order / call chain；只有上游 evidence 明确支持时才能陈述关系。
12. 若有 missing/invalid program，对 blocked manifest 运行 targeted adapter。
    只有 fresh exact source mapping 才进入 `program-list.csv`/`prompt-queue/`；
    missing/stale/unmapped 项只写
    `missing-program-list-batch/blocked-programs.csv`。全 ready 时不创建该目录。
    不要扫描整个 repo，blocked 时不得生成正式 review。
13. Review 不得包含 Trigger Inventory、Nodes、Edges、Transaction Call Map、
    Replay、Persistence、Lineage、UI Surfaces、Capability Seeds 或 SME Checklist。
14. 最后对 manifest、source pack、facts、coverage、formal review 做五方对账；
    validator 会从 source pack 反向重提 facts，并在同一 mapped row 核对
    routine、carrier、guard/condition、action/effect、evidence 与 token-aware
    exact value；有 program/fact/message/semantic/anchor/count 遗漏或
    unsupported call/sequence/exclusion 时必须修复，validator 零 finding 后才可
    交给 SME / Dify。
```

To use approved evidence, change only the explicit mode and root:

```text
Artifact repo mode: approved_document_repo
Program artifact root: <LOCAL-APPROVED-DOCUMENT-REPO-CLONE>
```

That mode change must be visible in the manifest and Run Profile.
