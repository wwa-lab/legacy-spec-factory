<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# IBM i Program Flow Prompt

Use this prompt when an SME provides an ordered or partial list of IBM i
programs and wants a compact program-set review.

```text
请根据以下 IBM i program list / flow，合并已有分析结果，生成一个
program-set SME core review。

Artifact repo mode: current_run
Artifact root: <program-analysis-artifact-root>
Source root (optional, for missing-program queue): <source-repo-path>
Review output root: <review-output-path>
Core review profile: standard_reader_first
Flow slug: <REVIEW-SLUG>
Program-set slug: <PROGRAM-SET-SLUG>

已有 program-analysis artifacts：
请优先复用以下已有的分析结果，不要重新扫描 source。
只有当某个 program 缺少必要 artifact 时，才将它标记为 pending_source，
并为该 program 生成 targeted scan queue；不要重新扫描整个 source repo。

Programs to merge:
1. PROGRAM_A
2. PROGRAM_B
3. PROGRAM_C

Review scope / expected outcome:
UI surfaces / files / reports:
Known error scenarios:
SME notes:
SME contact:

要求：
1. 保留我提供的 program 顺序作为 SME navigation evidence。
2. 每个 program 必须映射到已有的 program-analysis artifact。
3. 不要根据 program 名称猜测业务规则。
4. 明确标记缺失 program、缺失 artifact、未确认 evidence 和 TBD。
5. Calculation Logic、Validation Logic、Exception Handling 必须是跨程序自包含的阅读面；每行保留 Program、Routine、carrier/guard/effect、Supporting Detail 和 Evidence Status 等字段。
6. 只合并 artifact 明确给出的 calculation、validation、exception 和 message facts；不得从 SME 顺序、program name 或相似字段名推断跨程序关系。
7. 缺失 program 必须保留在 manifest、Sources 和 Core Completeness Ledger，review status 设为 `partial_pending_program`，核心行明确标记 unresolved/pending，不得补造逻辑。
8. 生成 `program-set-core-input-manifest.yaml`、`program-set-core-facts.yaml` 和固定文件名 `program-set-sme-core-review.md`。
9. 不要使用未声明为 approved document repo 的旧目录或历史运行结果作为已批准证据。
10. 不要因为发现缺失 program 就重新扫描整个 source repo；只处理缺失的 program。
11. 如果 manifest 不存在，先使用
`prepare_program_set_core_review.py` 根据 program list、artifact root、source root
和 review output root 生成 manifest；如果 manifest 中存在 pending/blocked program，使用
`create_missing_program_scan_queue.py` 生成
`missing-program-list-batch/prompt-queue/`。SME 只需提供 program list/input
path、source root、artifact/delivery output root 和 review output path；source path
必须来自 fresh source inventory，不得自行猜测。
12. 扫描队列完成后重新运行 builder 和 validator；在对应 artifacts 存在前，
review 必须保持 `partial_pending_program`。
13. 不要输出 Program-Level SME Core Review、Program-Set Logic Rollup、Transaction Call Map、Nodes、Edges、Replay、Persistence、Lineage、Capability Seeds 或 SME Checklist。

如需精简阅读面，才显式将 profile 改为 `minimal_reader_first`。
```
