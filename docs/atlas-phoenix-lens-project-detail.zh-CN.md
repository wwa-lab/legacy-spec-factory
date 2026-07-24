# 项目详细介绍：Atlas Phoenix Lens

[English](atlas-phoenix-lens-project-detail.md) | 中文

- **统一参赛项目：**Atlas Engineering Delivery Hub
- **本次展示能力：**Atlas Phoenix Lens
- **生命周期定位：**Discovery（M3）— Legacy 逆向发现
- **当前技术重点：**IBM i / AS400，RPG、CL、DDS
- **当前内部实现：**Program Flow Map + Evidence Core + Dify + SME Governance
- **Evidence Core 源码：**[wwa-lab/legacy-spec-factory](https://github.com/wwa-lab/legacy-spec-factory)

> **Modernization 的起点是理解，而不是翻译。**

Atlas Engineering Delivery Hub 是覆盖 Planning、Estimation、Discovery、
Build、Testing、Deployment 和 Maintenance 的统一工程交付体系。
Atlas Phoenix Lens 是其中聚焦 Discovery 阶段的核心工具。

它帮助团队在确定目标架构、开发、迁移或退役方案之前，先恢复 Legacy 系统
真正做了什么，把分散在源码、程序关系、文档、运行证据和 SME 经验中的知识，
转化为有证据、可评审、可复用的 Modernization Knowledge。

本次路演只展示 Atlas Phoenix Lens。Build Agent 和 Deployment Agent 属于
Atlas Engineering Delivery Hub 的其他生命周期能力，不作为 Phoenix Lens
已经实现的功能进行展示。

## 1. Phoenix Lens 在 Atlas Engineering Delivery Hub 中的位置

![Atlas Engineering Delivery Hub highlighting Atlas Phoenix Lens in Discovery](assets/atlas-engineering-delivery-hub-discovery-desktop.png)

```text
Atlas Engineering Delivery Hub

Planning → Estimation → Discovery → Build → Testing → Deployment → Maintenance
                          │
                          └── Atlas Phoenix Lens
                              Program Flow Map
                              + Evidence Core
                              + Dify Knowledge Activation
                              + SME Governance
```

Phoenix Lens 恢复现有系统并交付经过评审的 Discovery Knowledge。后续 Build
在这些证据和业务决策获得批准后创建未来系统。这个边界避免团队把“对旧系统的
AI 推断”直接当成“新系统的正式需求”。

Phoenix Lens 的 Discovery 输出包括：

- Legacy 系统的 Observed Behavior；
- 需要 SME 评审的 Inferred Business Rule；
- 程序、数据、异常、持久化和重启证据；
- Contradiction、Evidence Gap 和 `TBD-*`；
- Evidence ID、Source Coordinate、Snapshot 和 Review State；
- 经过评审后可交付给下游的 Modernization Knowledge Package。

## 2. Legacy Modernization 的核心痛点

Legacy Modernization 经常被当成一次技术转换，但最大的未知不是“代码能不能
转”，而是组织缺少一份完整、最新、可以评审的现有系统行为模型。

- 关键业务规则分散在 RPG、CL、DDS、数据库访问、Batch、Screen、Report 和
  Runtime 约定中；
- 文档可能过期，或者无法对应本次改造使用的 Source Snapshot；
- 一条业务流程可能跨越多个程序、文件、接口、异常、持久化和重启路径；
- 大型程序可能超过 10K 行，不完整读取会静默隐藏关键行为；
- 关键知识集中在少数资深 SME 身上；
- AI 总结可能看起来完整，却混合 Observed Fact、Inference 和无证据假设。

因此，团队在正向交付开始前不断重复代码阅读、SME 访谈、表格分析和人工
核对。任何被遗漏的规则或依赖，都可能在后续变成需求返工、测试缺口、迁移
延期、退役失败或生产风险。

> 最大的风险不是团队无法生成新代码，而是团队在没有完整理解旧系统的
> 情况下，生成了错误的新系统。

## 3. 当前解决方案：一个能力，三个实现层和一个治理闭环

Atlas Phoenix Lens 不是三个 Repo 的拼接展示，而是一个 Discovery 能力。
它通过三个协同实现层和一个 SME 治理闭环完成工作：

| 组成 | 当前职责 | 真实边界 |
|---|---|---|
| **Program Flow Map** | 从 ARCAD REF / XREF 建立跨程序关系，帮助 SME 选择有业务意义的 Program Flow | Flow 是范围和导航证据，不会自动成为已批准的业务事实 |
| **Evidence Core** | 扫描 RPG、CL、DDS，提取行为、规则、数据、异常、源码坐标和证据缺口 | 本仓库中的 Legacy Spec Factory skills、contracts、templates 和 validators |
| **Dify Implementation Layer** | 对文档和 Program 扫描结果进行 Metadata-scoped Retrieval、业务问答、编排和 BRD 草稿生成 | 当前内部实现层；Dify 保存可检索副本，不是 Canonical Evidence Source |
| **SME Governance** | 评审证据、解决 TBD、记录具名决策并回写审批状态 | AI 内容不能跳过 Review Gate 自动升级为 Approved Business Fact |

![Atlas Phoenix Lens implementation design](assets/atlas-phoenix-lens-design.svg)

统一产品公式是：

> **Atlas Phoenix Lens = Program Flow Map + Evidence Core + Dify Knowledge
> Activation + SME Governance**

## 4. How It Works

```text
ARCAD REF / XREF + 遗留文档 + RPG / CL / DDS 源码
                              ↓
                     Program Flow Map
                选择有边界的业务 Flow 和 Snapshot
                              ↓
                       Evidence Core
          Program / Flow / Data Analysis + Evidence Governance
                              ↓
                 Module Context / Evidence Map
       Observed / Inferred / Contradiction / TBD / Review State
                              ↓
                 Dify Knowledge Activation
        Metadata-scoped Retrieval / 业务问答 / BRD Draft
                              ↓
             SME Review / Decision Log / Write-back
                              ↓
           已评审的 Modernization Knowledge Package
                              ↓
      Atlas Engineering Delivery Hub 后续设计和工程交付
```

### 4.1 Map The Flow

ARCAD REF / XREF 关系展示 Caller、Callee、对象和数据依赖，让评审者选择一条
有业务意义的 Program Flow。

图谱首先回答“应该看哪里”。它用 Program List、Call Edge、Source Member、
Snapshot 和可选 Field Trace 确定分析边界，但不会把 SME 导航顺序直接提升为
真实调用链。每一条 Confirmed Call Edge 仍然需要源码或运行时证据。

### 4.2 Scan The Code

Evidence Core 对限定范围内的 RPG、CL 和 DDS 进行受控分析，提取：

- 有源码支持的 Program Behavior；
- Calculation、Validation 和 Business Rule Seed；
- File、Table、Field 和 External Dependency；
- Exception、Persistence 和 Restart Path；
- Source Coordinate、Coverage Gap 和 Evidence Strength；
- `Observed`、`Inferred`、`Contradiction` 和 `TBD`。

输出不是一份黑盒总结，而是一组可以审查、验证和重新运行的结构化制品。

### 4.3 Preserve The Evidence

Canonical Evidence 保存在可版本化制品中，并携带：

- 稳定 Evidence ID；
- Source Path、Source Version 和 Source Coordinate；
- Snapshot、Hash 和分析范围；
- Sensitivity、Authorization 和 Redaction State；
- Knowledge Type、Evidence Strength 和 Review State。

这样即使 Prompt、模型、Dify Collection 或下游实现发生变化，已经批准的
结论仍然可以回到原始证据。

### 4.4 Activate The Knowledge Through Dify

当前内部实现使用 Dify 建立文档知识库和 Program 扫描结果知识库，再由 SME
Program Flow 限定 Capability、Module、Program 和 Snapshot 范围。

Dify 用于：

- 使用业务语言查询 Program 和 Flow 行为；
- 关联文档知识和源码分析结果；
- 展示 Supporting Evidence 和开放问题；
- 生成 `candidate`、`poc_draft` 或 `in_review` 状态的 BRD 内容；
- 快速验证 Retrieval、Prompt、回答格式和 SME 可读性。

Dify 不用于：

- 替代 Canonical Evidence；
- 从整个 Legacy Estate 中自行猜测业务边界；
- 把 AI 推断自动升级为业务事实；
- 绕过 SME Review 直接生成 Approved BRD；
- 把 BRD 草稿越权推进到 Build、Test 或 SDD。

### 4.5 Review And Decide

SME Review 负责确认：

- 结论是否有足够证据；
- AI 推断是否符合业务含义；
- Contradiction 应如何解决；
- `TBD-*` 应确认、拒绝还是继续调查；
- 哪些行为需要保留、重新设计、合并或退役。

只有具备合格证据或具名 SME 决策的内容，才能进入 Approved Knowledge
Package。

## 5. Phoenix Lens 带来的改变

| Phoenix Lens 之前 | 使用 Phoenix Lens |
|---|---|
| 从没有边界的代码库开始 | 从 SME 选择的 Program Flow 和明确 Snapshot 开始 |
| 逐个独立阅读程序 | 在限定范围内分析程序、数据、异常、持久化和重启证据 |
| 输出无法验证的叙述性总结 | 输出结构化事实、推断、矛盾、Evidence Link 和 TBD |
| 让 SME 重新解释完整实现 | 让 SME 集中评审证据和未决业务决定 |
| RAG 在全局知识库中自行猜测范围 | Dify 使用 Capability、Module、Program 和 Snapshot Metadata 限定检索 |
| AI 生成内容直接进入文档 | Draft 必须经过 Evidence Gate 和 SME Review |
| 每个项目重新建设 Discovery 方法 | 复用 Flow Contract、Skills、Evidence Schema、Review State 和 Evaluation Case |

最终产物不是一份孤立文档，而是一套经过人工评审、可以支持需求、目标设计、
迁移计划、测试范围和退役决策的 Modernization Knowledge Package。

## 6. 当前能力、证据和真实边界

| 能力 | 当前状态 | 证据或边界 |
|---|---|---|
| Atlas Engineering Delivery Hub 定位 | **已统一** | Phoenix Lens 只作为 Discovery 能力展示 |
| Program Flow Map 导航 | **当前内部能力 / Demo Ready** | 用于限定 Program Flow 和 Snapshot；实际内部访问地址不在本仓库公开 |
| RPG、CL、DDS 分析 | **当前实现** | Evidence Core skills、templates、validators 和示例制品已在本仓库 |
| Evidence Package | **仓库已有能力** | [Phoenix Lens Mini Output](samples/atlas-phoenix-lens-mini-output/) |
| Dify 检索、问答和编排 | **当前内部实现路线** | 使用限定范围的文档和 Program 扫描知识；Demo 输出仍需遵守 Review Gate |
| Dify Metadata Governance | **持续完善 / Pilot Control** | 需要验证关键字段不会在导入、检索和导出中静默丢失 |
| SME Decision Write-back | **持续完善 / Pilot Control** | 需要稳定记录 Owner、日期、Evidence、决定和状态历史 |
| BRD 生成 | **支持 Draft** | 输出只能是 `candidate`、`poc_draft` 或 `in_review`，不能自动成为 `approved` |
| 与 Build、Testing、Deployment 的交接 | **本次不展示** | Phoenix Lens 输出可作为可信输入，但不声称本仓库实现了后续阶段 |
| COBOL 分析 | **未来愿景** | 尚未作为当前能力交付，需要专用 Adapter、Skills、Benchmark 和 SME 验证 |
| 其他 Legacy 平台 | **方法可复用 / Future Pilot** | 每个平台都需要 Inventory Adapter、Scanning Skills、Benchmark Evidence 和 SME 验证 |

当前能力成熟度、Evidence Core 的本地工程状态、Dify 部署成熟度和完整 Field
Pilot 结果必须分别陈述。设计已经存在，不等于所有生产场景已经验证。

## 7. 为什么这套方法可以跨 Legacy 系统复用

当前实现聚焦 IBM i / AS400 的 RPG、CL 和 DDS。Phoenix Lens 的可扩展价值
来自它把“平台相关分析”与“公共证据治理”分开：

| 可复用层 | 不同 Legacy 系统可以共享的部分 | 新平台需要适配的部分 |
|---|---|---|
| Scope Discovery | 从有边界的业务 Flow 和明确 Snapshot 开始 | Inventory 和 Dependency Adapter |
| Source Scanning | Coverage、Evidence Coordinate、不确定性和 Batch Control | 平台相关 Parser、Prompts 和 Scanning Skills |
| Evidence Contract | 稳定 ID、源码坐标、状态、敏感性和 Review State | Source Type 和平台 Metadata |
| Knowledge Activation | Dify 对评审制品进行 Metadata-scoped Retrieval | Collection Design、Chunk Strategy 和 Filters |
| Human Governance | SME 审批、Contradiction、TBD 和 Decision History | Domain Owner 和 Acceptance Benchmark |
| Evaluation | Evidence Link、Unsupported Claim、Coverage 和 Repeatability | 平台相关 Golden Sample 和 Challenge Case |

推广路径应逐步验证：

1. 先验证一条包含 5-10 个程序的真实业务 Flow；
2. 再扩展到一个 Application 或 Capability；
3. 为新的 Legacy Technology 增加 Adapter、Skills 和 Benchmark；
4. 通过 SME 和安全评审后再声明平台支持；
5. 最终在 Modernization Portfolio 中复用同一套治理方法。

所以 Phoenix Lens 不是一个声称已经支持所有平台的万能 Parser，而是一套可以
通过 Adapter 和 Benchmark 持续扩展的 Discovery Operating Model。COBOL 是
下一类潜在扩展方向，但当前不作为已实现能力宣传。

## 8. 对公司的意义和商业价值

Phoenix Lens 的价值远不只是更快地生成文档。它可以降低每一个
Modernization 估算和决策所承担的“不确定性溢价”。

- **释放交付产能：**减少重复代码阅读、上下文重建和大范围 SME 解释；
- **避免下游返工：**减少因错误理解 Legacy 行为产生的需求、目标设计、测试
  和迁移返工；
- **保留机构知识：**即使项目结束或资深 SME 离开，关键证据和决策仍然存在；
- **Portfolio 复用：**不同团队不再为每个应用重新建设 Flow、Prompt、
  Evidence Schema 和治理流程；
- **支持可靠退役：**区分哪些行为必须保留、重新设计、合并或可以安全退役；
- **降低 AI 风险：**让证据、不确定性和审批状态保持可见，避免黑盒答案污染
  正式需求和下游设计。

```text
年度可量化净价值
  = 释放的 Discovery 和 SME 交付产能价值
  + 避免的证据相关返工成本
  + 避免的项目重复建设成本
  + 经验证的提前退役价值
  - Phoenix Lens 年度运行成本
```

在 Portfolio 层面：

```text
每个采用范围经验证的价值
  × 可采用的 Application / Capability 数量
  × 经验证的 Adoption Rate
  = Portfolio Value Opportunity
```

实际收益必须使用有 Owner 的 Baseline、可比较的 Pilot 数据和 Finance 认可的
单位成本验证。目标、示例测算和 Capacity Release 不能自动写成已经兑现的
Cash Saving。

## 9. 路演 Demo 路径

本次路演以 Dify 为用户入口，以 Program Flow Map 和本仓库制品证明其背后的
范围控制与证据治理。

```text
Program Flow Map
  → 选择一条有业务意义的 Flow 和 Source Snapshot
  → 查看 Evidence Core 的 Program Analysis 和 Source Coordinate
  → 在 Dify 中使用相同 Scope 进行业务问答
  → 将回答追溯到 Evidence ID 和原始证据
  → 生成 BRD Draft
  → 展示 SME Review、Decision Log 和 Approval Boundary
  → 输出 Reviewed Modernization Knowledge Package
```

建议重点展示：

1. 一条明确的 SME Program Flow；
2. 一个带 Source Coordinate 的 Observed Behavior；
3. 一个不能被 AI 静默关闭的 `TBD-*`；
4. Dify 中的 Metadata Scope；
5. 一次从回答回到 Evidence ID 的钻取；
6. 一个标记为 `poc_draft` 或 `in_review` 的 BRD 片段；
7. 一次 SME Decision 如何将内容确认、拒绝或继续保留为开放问题。

## 10. Pilot 成功指标和下一步

以下指标是建议验收目标，不是已经实现的收益声明：

- 抽样 Evidence Link 成功率至少 95%；
- Unsupported Claim 不超过 5%；
- Observed Behavior 的 SME 修正率不超过约定阈值；
- 相同 Snapshot 重跑时，核心结果一致或差异可以解释；
- 两轮后 SME Review 时间相对 Baseline 有可验证下降；
- 所有 Approved 内容都具有合格证据或具名 SME 决定；
- 10K+ 行 RPG 程序不存在静默截断，所有源码区间都有处理状态；
- Program Chain 中每一条 Confirmed Call Edge 都具有源码或运行时证据；
- 敏感数据、模型使用、保留和删除策略通过安全审查。

下一步优先级：

1. 完成 Program Flow Map、Evidence Core 与 Dify 的 Metadata、状态和审批映射；
2. 验证 Dify 导入、检索和导出不会静默丢失 Evidence 字段；
3. 完善 SME Decision Log、Write-back 和 BRD Approval Gate；
4. 建立检索与生成 Golden Evaluation Set；
5. 使用真实 10K+ 行 RPG 程序和 5-10 Program Chain 完成 Challenge Case；
6. 在当前平台基准通过后，再启动 COBOL 或其他 Legacy 平台扩展。

## 11. 与公司价值观的对应

- **We Get It Done：**把不透明的 Legacy Estate 转换成可以评审的
  Modernization Input；
- **We Take Responsibility：**让证据、不确定性、敏感性和审批状态保持
  可见，而不是隐藏在一个 AI 答案后面；
- **We Succeed Together：**把个人 SME 和工程知识变成组织可以复用的资产；
- **We Value Difference：**结合源码证据、工程分析、业务知识和人工判断。

## 一句话总结

> **Map the flow. Scan the code. Activate the knowledge.** Atlas Phoenix Lens
> 让团队基于证据而不是假设去 Modernize Legacy Systems。

## 相关材料

- [English Project Detail](atlas-phoenix-lens-project-detail.md)
- [中文 README](../README.zh-CN.md)
- [中文路演稿](atlas-phoenix-lens-pitch.zh-CN.md)
- [路演和评审材料索引](atlas-phoenix-lens-index.md)
- [Program Flow Map Export Contract](program-flow-map-export-contract.md)
- [Phoenix Lens Mini Output](samples/atlas-phoenix-lens-mini-output/)
- [Vendor BRD AI POC 与 Atlas Phoenix Lens 对比及落地改进方案](vendor-vs-atlas-phoenix-lens-comparison-improvement-2026-07-23.zh-CN.md)
