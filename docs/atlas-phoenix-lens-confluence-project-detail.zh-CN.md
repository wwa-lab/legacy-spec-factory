# Atlas Engineering Delivery Hub - Atlas Phoenix Lens

https://github.com/wwa-lab/legacy-spec-factory

## Atlas Phoenix Lens 是什么

**Atlas Engineering Delivery Hub** 是本次统一参赛项目。它将 Planning、
Estimation、Discovery、Build、Testing、Deployment 和 Maintenance 连接成
一个完整的工程交付体系。

**Atlas Phoenix Lens** 是 Hub 中 **Discovery（M3）**阶段的一项重要能力，
也是本次路演集中展示的能力。它帮助团队在重新设计、重建、迁移或退役 Legacy
系统之前，先理解现有系统真正做了什么。它恢复有证据支撑的知识，而不是直接
进行 Legacy Code Conversion。

当前内部实现由 **Program Flow Map**、**Evidence Core**、**Dify Knowledge
Activation** 和 **SME Governance** 组成。当前技术范围是 IBM i / AS400 的
RPG、CL 和 DDS。

Build Agent 和 Deployment Agent 是 Atlas Engineering Delivery Hub 的下游
能力，不作为 Atlas Phoenix Lens 已经交付的功能进行展示。

## 1）我们解决的问题

Legacy Modernization 往往从不完整的系统知识开始：

- 关键业务规则分散在 RPG、CL、DDS、数据库访问、Batch、Screen、Report 和
  运行约定中；
- 一条业务流程可能跨越多个程序、文件、接口、异常路径、持久化路径和重启
  路径；
- 现有文档可能已经过期，或者无法对应本次 Modernization 使用的 Source
  Snapshot；
- 关键知识集中在少数资深 SME 身上；
- 团队需要反复阅读源码、重建上下文、访谈 SME 并人工交叉核对；
- 通用 AI 总结可能看起来很完整，却混合了 Observed Fact、Inference 和没有
  证据支持的假设。

这使 Discovery 工作耗时、难以规模化，也容易遗漏关键规则和依赖。这些缺口
可能在下游变成需求返工、测试缺口、迁移延期、错误的退役决策或生产风险。

## 2）带来的改变

Atlas Phoenix Lens 将没有边界的人工调查，转变为有明确范围、受证据治理的
Discovery 工作流。

实际影响：

- **从有业务意义的 Program Flow 开始：**由 SME 选择明确的业务范围和 Source
  Snapshot，而不是让工具在整个 Legacy Estate 中自行猜测边界；
- **把源码转化为可评审知识：**对 RPG、CL 和 DDS 的分析明确区分 Observed
  Behavior、Inferred Rule、Contradiction 和 Open Question；
- **通过 Dify 激活知识：**团队可以使用 Capability、Module、Program 和
  Snapshot Metadata 限定检索范围，进行业务问答和 BRD 草稿生成；
- **保留可追溯性：**结论携带 Evidence ID、Source Coordinate、Evidence
  Strength 和 Review State；
- **让 SME 保持控制权：**AI 生成内容没有 Supporting Evidence 或具名 SME
  Decision，就不能成为 Approved Business Fact；
- **形成更安全的下游交付：**经过评审的 Discovery Knowledge 可以支持 Atlas
  Engineering Delivery Hub 后续的设计、Build、Testing、迁移和退役决策。

对公司的意义和商业价值：

- **释放稀缺的 Discovery 和 SME 产能：**减少重复读码、上下文重建和大范围
  解释工作；
- **避免下游返工：**降低因错误理解 Legacy 行为造成的需求、设计、测试和
  迁移返工；
- **保护组织知识：**将关键行为、证据和具名 SME 决策沉淀为可维护的组织
  资产；
- **支持 Portfolio 级复用：**不同应用可以复用同一套 Discovery Operating
  Model，而不必重复建设方法；
- **支持更安全的改造和退役决策：**明确哪些行为必须保留、重新设计、合并或
  安全退役。

这套能力具有很高的商业潜力。实际收益应通过有 Owner 的 Pilot Baseline、
可比较的测量数据和认可的单位成本进行验证。

## 3）如何工作

核心能力：

- **Program Flow Map：**使用 ARCAD REF / XREF 关系展示 Caller、Callee、对象
  和数据依赖，帮助 SME 选择一条有明确边界的业务 Flow；
- **Evidence Core：**在限定范围内扫描 RPG、CL 和 DDS，提取行为、规则、
  数据使用、异常、Source Coordinate、Evidence Gap 和 Review State；
- **Dify Knowledge Activation：**作为当前内部实现路线，提供 Metadata-scoped
  Retrieval、业务问答、工作流编排、证据下钻和 BRD 草稿生成；
- **SME Governance：**评审证据、解决 Contradiction 和 TBD、记录具名决策并
  控制审批；
- **Modernization Knowledge Package：**将经过评审的知识打包，交付给下游
  设计和工程团队。

整体工作流是：

**Program Flow 选择 -> Evidence 提取 -> Dify Knowledge Activation -> SME
评审和决策 -> 已评审的 Modernization Knowledge -> 下游交付**

Dify 让知识更容易使用，但它不是 Source of Truth。Canonical Evidence、
Source Coordinate、Approval State 和 Decision Record 继续由独立、可版本化
的机制进行治理。

## 4）为什么可以规模化

- **可复用的 Operating Model：**Scope、Evidence Extraction、Knowledge
  Activation、SME Review 和 Downstream Handoff 可以在不同团队和应用中重复
  使用；
- **可移植的 Evidence Model：**稳定的 Evidence Contract、Review State 和
  Traceability Rule，减少对单一模型、Prompt 或用户界面的依赖；
- **有边界的检索：**Dify 使用 Metadata 限定检索范围，降低跨系统知识污染，
  也让答案更容易评审；
- **渐进式采用：**团队可以从一条高价值 Program Flow 开始，验证后再按
  Module、Application 或 Portfolio 扩展；
- **可扩展的架构：**新的 Legacy 平台可以复用治理模型，再增加平台专用的
  Parser、Skill、Benchmark 和 SME Validation；
- **Portfolio 价值：**可复用的 Discovery 资产可以减少重复方案建设，并为
  Modernization 决策提供一致的证据基础。

当前实现支持 IBM i / AS400 的 RPG、CL 和 DDS。**COBOL 和其他 Legacy 平台
属于未来扩展愿景，不是当前已经交付的能力。**方法可以复用，不代表可以省略
每个平台专用的实现和验证。

## 5）与 HSBC Values 的对应

- **We Get It Done：**把困难、开放式的 Discovery 工作转化为能够产出可用
  Modernization Knowledge 的实际工作流；
- **We Take Responsibility：**让 Evidence、Uncertainty、Review State 和
  具名决策保持可见，降低把 AI 输出误当成事实的风险；
- **We Succeed Together：**把工程分析和 SME 专业知识结合起来，为下游团队
  形成可复用的共同知识；
- **We Value Difference：**用业务语言提升专业 Legacy Knowledge 的可访问
  性，同时保留不同观点、Contradiction 和 Evidence Gap 供评审。

**一句话总结：**Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub 中受
证据治理的 Discovery 核心能力，它把难以理解的 Legacy 系统转化为可评审、
可追溯、可复用的 Modernization Knowledge。
