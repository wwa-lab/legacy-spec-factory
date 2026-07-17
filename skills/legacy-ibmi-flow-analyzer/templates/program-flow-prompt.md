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
请根据以下 IBM i program flow，生成一个 program-set SME core review。

Analysis intent: standalone_exploratory
Flow scan mode: core_review_only
Artifact repo mode: approved_document_repo
Artifact repo root: <approved-artifact-repo-path>

已有 program-analysis artifacts：
请优先复用以下已批准的分析结果，不要重新扫描 source。
只有当某个 program 在 approved artifact repo 中不存在，或缺少必要
artifact 时，才将它标记为 pending_source，并单独提出补扫描建议。

Capability / Module:
Business Event:
Trigger:
Trigger Type: batch_job | interactive_menu | subfile_dispatch | f_key | db_trigger | scheduler | api_remote

Programs in chain:
1. PROGRAM_A
2. PROGRAM_B
3. PROGRAM_C

Known entry / exit conditions:
UI surfaces / files / reports:
Known error scenarios:
SME notes:
SME contact:

要求：
1. 保留我提供的 program 顺序作为 SME navigation evidence。
2. 每个 program 必须映射到已有的 program-analysis artifact。
3. 不要根据 program 名称猜测业务规则。
4. 明确标记缺失 program、缺失 artifact、未确认调用和 TBD。
5. 汇总 Calculation Logic、Validation Logic、Exception Handling、Message Inventory。
6. 生成 Transaction Call Map，但不要把推测内容写成确认事实。
7. 输出 program-set-sme-core-review.md。
8. 不要使用未声明为 approved document repo 的旧目录或历史运行结果作为已批准证据。
9. 不要因为发现缺失 program 就重新扫描整个 source repo；只处理缺失的 program。
```

## Full transaction-flow variant

如果需要从 entry point 开始发现并分析完整交易链，而不仅是合并已有
program analysis，请将模式改为：

```text
请执行 full transaction-flow analysis。
flow_scan_mode: orchestrated
```

此模式要求提供明确的 trigger / entry point，并输出
`flow-<FLOW-SLUG>.md`。触发类型和采集字段请参照
`trigger-checklist.md`。
