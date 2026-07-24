# Atlas Phoenix Lens 中文路演稿与讲解说明

[English](atlas-phoenix-lens-pitch.md) | 中文

## 统一定位

路演中始终按以下顺序介绍：

1. **Atlas Engineering Delivery Hub**：统一参赛项目和全生命周期工程交付体系；
2. **Discovery（M3）**：本次重点展示的生命周期阶段；
3. **Atlas Phoenix Lens**：Discovery 阶段的核心能力；
4. **Legacy Spec Factory**：本仓库承载的 Evidence Core 技术实现名，仅在解释
   技术细节时使用。

不要把 Phoenix Lens 讲成与 Delivery Hub 并列的第四个项目，也不要把 Build
Agent 或 Deployment Agent 讲成 Phoenix Lens 已经实现的功能。

## 一页总结

> **Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub 在 Discovery
> 阶段的核心工具：先看清遗留系统，再决定如何现代化。**

Phoenix Lens 由三个协同层组成：

- **Program Flow Map：**从 ARCAD REF / XREF 建立跨程序范围和导航；
- **Evidence Core：**扫描 RPG、CL 和 DDS，保留源码坐标，并区分事实、推断、
  矛盾和 TBD；
- **Dify Implementation Layer：**提供有 Metadata 范围控制的检索、业务问答、
  编排和 BRD 草稿生成。

SME 始终是业务事实的控制点。Dify 是当前内部交互与编排实现层，不是
Canonical Evidence Source，也不能自动批准业务事实。

## 30 秒介绍

Legacy Modernization 的起点不是代码转换，而是先理解现有系统真正做了什么。
Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub 的 Discovery 能力。
它先通过 Program Flow Map 看清跨程序范围，再通过 Evidence Core 扫描 RPG、
CL 和 DDS、保留证据坐标，最后在 Dify 中进行有边界的业务问答和 BRD 草稿
生成。每一条最终批准的结论都必须能够回到证据，或者具有具名 SME 的决策。

## 3 分钟路演稿

### 1. 从真正的风险开始

Legacy Modernization 最大的风险，不是团队无法生成新代码，而是团队没有完整
理解旧系统，就生成了错误的新系统。

遗留系统的业务行为分散在源码、程序调用、文件、Batch、Screen、Report、
Runtime 约定和少数资深 SME 的知识中。只对一个程序做一份看起来完整的 AI
总结，不足以支撑现代化决策。

### 2. 把 Phoenix Lens 放回 Delivery Hub

Atlas Engineering Delivery Hub 是覆盖 Planning、Estimation、Discovery、
Build、Testing、Deployment 和 Maintenance 的统一项目。

今天我们只展示其中一个能力：**Discovery 阶段的 Atlas Phoenix Lens**。
它的任务是在目标设计和开发开始之前，恢复一份有证据、可评审的现状知识模型。

### 3. 解释三个协同层

第一层是 Program Flow Map。它使用 ARCAD REF / XREF 建立有边界的跨程序
范围，回答“应该看哪里”。

第二层是本仓库中的 Evidence Core。它分析 RPG、CL 和 DDS，记录程序行为、
数据访问、异常路径、源码坐标、矛盾和开放问题，回答“证据实际说明了什么”。

第三层是当前内部使用的 Dify 实现层。Dify 在同一 Program Flow 的 Metadata
范围内检索文档和 Program 扫描结果，支持业务问答、知识编排和 BRD 草稿生成，
回答“SME 如何使用这些知识”。

### 4. 强调治理边界

Dify 不会取代事实源。Canonical Evidence 继续保存在结构化、可版本化的
制品中。AI 生成的内容只能是 `candidate`、`poc_draft` 或 `in_review`；
只有具备合格证据或具名 SME 决策后，才能成为 `approved`。

Phoenix Lens 始终把 Observed Behavior、Inferred Rule、SME Decision 和
Modernization Decision 分开。这种分层让输出能够可靠地进入后续工程阶段。

### 5. 以公司价值收尾

Phoenix Lens 可以减少重复 Discovery、降低下游返工，并把个人 SME 知识转化
为可以持续维护的组织资产。同一套 Flow、Evidence Contract、Review Gate 和
Dify 编排方法可以在 Modernization Portfolio 中复用。

当前实现聚焦 IBM i / AS400 的 RPG、CL 和 DDS。COBOL 及其他 Legacy 平台
属于未来扩展，必须分别完成 Adapter、Scanning Skills、Benchmark 和 SME
验证后才能对外声明支持。

> **Map the flow. Scan the code. Activate the knowledge.**

## 建议的五页路演结构

### 第 1 页：一个 Hub，一个 Discovery 核心能力

**核心信息：**Atlas Engineering Delivery Hub 是统一项目，Atlas Phoenix
Lens 是其中的 Discovery 能力。

**建议视觉：**`assets/atlas-engineering-delivery-hub-discovery-desktop.png`

**讲解提醒：**先建立总项目和子能力关系，再提 Repo 或技术实现。

### 第 2 页：Modernization 从理解开始

**核心信息：**真正的风险是团队基于错误或不完整的 Legacy 理解开始建设。

展示五个问题：

- 分散的业务规则；
- 过期或无法对应 Snapshot 的文档；
- 跨程序业务行为；
- 集中在少数 SME 身上的知识；
- 缺少证据坐标的 AI 推断。

### 第 3 页：Phoenix Lens 如何工作

**核心信息：**一个能力把 Flow Discovery、Evidence Governance 和 Knowledge
Activation 连接起来。

**建议视觉：**`assets/atlas-phoenix-lens-design.svg`

```text
Program Flow Map
  → Evidence Core
  → Dify Knowledge Activation
  → SME Review
  → 已评审的 Modernization Knowledge Package
```

### 第 4 页：Dify Demo 与证据钻取

**核心信息：**Dify 让证据变得容易使用，但不会取代证据。

展示：

- 一条 SME 选择的 Program Flow；
- 带 Metadata 的限定范围检索；
- 一个业务问题；
- 支撑答案的 Evidence ID 和 Source Coordinate；
- 标记为 `poc_draft` 或 `in_review` 的 BRD 草稿；
- SME Approval Boundary。

### 第 5 页：公司和 Portfolio 价值

**核心信息：**Phoenix Lens 在昂贵的下游工作开始前降低不确定性。

价值主题：

- 释放 Discovery 和 SME 产能；
- 避免需求、设计、测试和迁移返工；
- 保存机构知识；
- 跨应用复用证据治理方法；
- 支持更可靠的 Application Retirement。

没有 Baseline 和可比较的 Pilot 数据时，不把价值目标写成已实现收益。

## Dify Demo 串词

1. 打开 Program Flow Map，选择一条有业务意义的 Flow。
2. 展示该 Flow 包含的 Program List 和 Source Snapshot。
3. 打开一个 Evidence Core Program Analysis，展示 Source Coordinate、
   Observed Behavior 和一个 `TBD-*`。
4. 在 Dify 中使用相同 Capability、Module、Program 和 Snapshot 作为检索范围。
5. 提问一个关于业务行为、数据影响或异常路径的问题。
6. 将回答追溯到 Evidence ID 和 Source Coordinate。
7. 生成一段 BRD，并展示其 `poc_draft` 或 `in_review` 状态。
8. 说明只有合格证据或具名 SME 决策才能把内容提升为 `approved`。
9. 最后展示已评审的 Knowledge Package 如何进入 Atlas Engineering Delivery
   Hub 的后续阶段。

## 常见问题与回答

### Atlas Phoenix Lens 是整个参赛项目吗？

不是。Atlas Engineering Delivery Hub 是统一参赛项目，Atlas Phoenix Lens
是本次重点展示的 Discovery 能力。

### 这个 Repo 就是完整产品吗？

这个 Repo 承载 Evidence Core。完整的 Phoenix Lens 还包括 Program Flow Map
以及当前使用的 Dify 实施层。

### 为什么使用 Dify？

Dify 是当前内部用于限定范围知识检索、业务问答、Prompt 编排和 BRD 草稿生成
的实现路线。团队可以先激活已经扫描和评审的知识，而不必等待一套完整的定制
交互平台。

### Dify 是 Source of Truth 吗？

不是。Dify 保存可检索副本。Canonical Evidence、Source Coordinate、
Snapshot、审批状态和下游契约继续保存在 Phoenix Lens Evidence Core 控制的
可版本化制品中。

### 这是代码转换工具吗？

不是。Phoenix Lens 是 Discovery 和 Evidence 工具。它先确认旧系统做了什么，
再支持组织决定哪些能力需要保留、重新设计、替换或退役。

### 当前支持哪些技术？

当前聚焦 IBM i / AS400，支持 RPG、CL 和 DDS 分析、Program Flow Map 导航、
Legacy Spec Factory Evidence Core，以及内部 Dify 检索和编排路线。

### 当前支持 COBOL 吗？

尚未作为当前能力交付。COBOL 是未来扩展愿景，需要独立的 Adapter、Scanning
Skills、Benchmark 和 SME 验证。

### 这套方法能否用于其他 Legacy 平台？

公共方法可以复用，包括有边界的 Scope、Evidence Coordinate、知识分类、
SME Governance、Traceability 和 Metadata-scoped Retrieval。但只有完成
平台相关实现和 Benchmark 后，才能声明支持该平台。

### 当前还需要加强什么？

最高优先级是打通 Program Flow Map、Evidence Core 与 Dify 之间的 Metadata
和状态映射；完成 SME Decision Write-back；建立检索与生成评测集；并使用
真实 10K+ 行 RPG 程序和 5–10 Program Chain 进行强制验证。

## 能力声明护栏

| 主题 | 统一说法 |
| --- | --- |
| Dify | 当前内部检索与编排实现层 |
| Dify 成熟度 | 当前路线已确定，Metadata Governance、Write-back 和规模化评测仍在加强 |
| Source of Truth | Canonical Evidence 保存在可版本化的结构化制品中 |
| 当前语言范围 | RPG、CL、DDS |
| COBOL | 未来愿景，不是当前已交付能力 |
| 跨平台价值 | 方法可复用；每个平台必须独立实现和验证 |
| BRD | 当前支持草稿生成；批准必须具有证据或具名 SME 决策 |
| 商业价值 | 通过 Pilot Baseline 验证的 Portfolio Opportunity，不写成已兑现收益 |

## 相关材料

- 英文 Pitch：
  [atlas-phoenix-lens-pitch.md](atlas-phoenix-lens-pitch.md)
- 材料索引：
  [atlas-phoenix-lens-index.md](atlas-phoenix-lens-index.md)
- 中文 README：
  [../README.zh-CN.md](../README.zh-CN.md)
- 英文 README：
  [../README.md](../README.md)
- Program Flow Map Export Contract：
  [program-flow-map-export-contract.md](program-flow-map-export-contract.md)
- Mini Output Sample：
  [samples/atlas-phoenix-lens-mini-output/](samples/atlas-phoenix-lens-mini-output/)
