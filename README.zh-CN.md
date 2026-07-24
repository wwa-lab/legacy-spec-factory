# Atlas Phoenix Lens

[English](README.md) | 中文

![Atlas Engineering Delivery Hub highlighting Atlas Phoenix Lens in Discovery](docs/assets/atlas-engineering-delivery-hub-discovery-desktop.png)

> **Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub 在 Discovery
> 阶段的核心工具：先看清遗留系统，再决定如何现代化。**

**Atlas Engineering Delivery Hub** 是覆盖 Planning、Estimation、Discovery、
Build、Testing、Deployment 和 Maintenance 的统一工程交付体系。
**Atlas Phoenix Lens** 是其中聚焦 **Discovery（M3）** 的能力，不是一个与
Delivery Hub 并列的独立项目。

Phoenix Lens 从 ARCAD REF / XREF、Program Flow、遗留文档和源码出发，恢复
Legacy 系统真正做了什么，并把结果转化为带证据、可评审、可复用的
Modernization Knowledge。当前内部实现使用 **Dify** 承担有边界的知识检索、
问答和编排；本仓库中的 **Legacy Spec Factory** 是其 Evidence Core，负责
源码扫描、证据治理、SME Gate 和 Traceability。

> **Map the flow. Scan the code. Activate the knowledge.**

Phoenix Lens **不是**把 Legacy 源码直接翻译成 Java 或云服务。它先让团队
确认哪些行为是已观察事实、哪些规则仍是推断、哪些问题需要 SME 决策，再把
经过评审的知识交给 Atlas Engineering Delivery Hub 的后续 Build、Testing
和 Deployment 阶段。

完整历史 README 和更深入的设计说明保存在
[docs/full-reference-readme.md](docs/full-reference-readme.md)。

## Delivery Hub 定位

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

本次仓库和路演只展示 Atlas Phoenix Lens。Build Agent 和 Deployment Agent
属于 Atlas Engineering Delivery Hub 的其他生命周期能力，不作为 Phoenix
Lens 已经实现的功能进行展示。

![Atlas Phoenix Lens position in Atlas Engineering Delivery Hub](docs/assets/atlas-phoenix-lens-delivery-hub-position.svg)

可编辑源文件：
[docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd](docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd)。

## 为什么需要它

Legacy Modernization 最大的未知通常不是“新代码能不能生成”，而是团队没有
一份完整、最新、可追溯的现状行为模型：

- 业务规则散落在 RPG、CL、DDS、数据库访问、Batch、Screen、Report 和
  Runtime 约定中；
- 文档可能过期，或无法对应本次改造使用的源码 Snapshot；
- 一条业务流程可能跨越多个程序、文件、接口、异常和重启路径；
- 关键知识集中在少数资深 SME 身上；
- AI 总结可能看起来完整，却混合 Observed Fact、Inference 和无证据假设。

任何被遗漏的规则或依赖，都会在后续变成需求返工、测试缺口、迁移延期、退役
失败或生产风险。

> 最大的风险不是团队无法生成新代码，而是团队在没有完整理解旧系统的情况下，
> 生成了错误的新系统。

## 当前实现：一个能力，三个协同层

| Phoenix Lens 组成 | 当前职责 | 实现边界 |
| --- | --- | --- |
| **Program Flow Map** | 基于 ARCAD REF / XREF 建立跨程序导航和业务范围 | Neo4j application 位于公司内部上游 repo；Flow 是导航证据，不自动成为业务事实 |
| **Evidence Core** | 扫描源码，提取行为、规则、数据、异常、TBD，并执行 SME Gate 和 Traceability | 本仓库以 Legacy Spec Factory skills、contracts、templates 和 validators 实现 |
| **Dify Implementation Layer** | 对文档和 Program 扫描结果进行有边界的检索、问答、编排和 BRD 草稿生成 | 当前内部实现路线；Dify 不是 Canonical Evidence Source，也不能自动批准业务事实 |

整体工作流是：

```text
ARCAD REF / XREF + 遗留文档 + 源码
  → Program Flow Map：选择有边界的业务 Flow
  → Evidence Core：RPG / CL / DDS 扫描和证据治理
  → Module Context / Evidence Map：区分事实、推断、矛盾和 TBD
  → Dify：Metadata-scoped Retrieval、业务问答和 BRD Draft
  → SME Review / Decision / Write-back
  → 审核后的 Modernization Knowledge Package
  → Atlas Engineering Delivery Hub 后续工程阶段
```

### Dify 的当前定位

当前内部实现把遗留文档和 Program 扫描结果纳入 Dify 知识库，由 SME
Program Flow 限定检索范围，再进行知识问答和 BRD 草稿生成。这让团队可以
快速验证检索策略、Prompt、回答格式和 SME 可读性。

Dify 同时遵守三条边界：

1. Dify 保存的是可检索副本，Canonical Evidence 继续保存在可版本化制品中；
2. 检索必须使用 Capability、Module、Program、Source Version、Snapshot 和
   Evidence Strength 等 Metadata 控制范围；
3. Dify 生成的内容只能是 `candidate`、`poc_draft` 或 `in_review`，必须经过
   证据验证或具名 SME 决策后才能成为 `approved`。

## 当前能力和未来愿景

| 范围 | 状态 |
| --- | --- |
| IBM i / AS400 Discovery 方法 | 当前重点 |
| RPG、CL、DDS 源码和上下文分析 | 当前实现 |
| Program Flow Map 导航 | 当前内部能力 |
| Legacy Spec Factory Evidence Core | 本仓库已有能力 |
| Dify 检索、问答和编排 | 当前内部实现路线 |
| Dify Metadata Governance、Decision Write-back 和规模化评测 | 持续完善 / Pilot Control |
| COBOL 分析 | 未来愿景，尚未作为当前能力交付 |
| 其他 Legacy 平台 | 未来通过 Adapter、Skills、Benchmark 和 SME 验证逐步扩展 |

Phoenix Lens 的可复用价值并不依赖某一种语言：Scope Discovery、Evidence
Contract、知识分类、SME Governance、Traceability 和 Dify 范围控制可以跨
平台复用；但每一种新 Legacy 技术都必须增加专用 Adapter、Scanning Skills、
测试基准和 SME 验证，不能把方法可复用等同于平台能力已经实现。

## 实现设计概览

![Atlas Phoenix Lens implementation design overview](docs/assets/atlas-phoenix-lens-design.svg)

可编辑源文件：
[docs/assets/atlas-phoenix-lens-design.mmd](docs/assets/atlas-phoenix-lens-design.mmd)。

## 路演 Demo

给评审展示的主路径以 Dify 为用户入口，以本仓库制品证明其背后的证据治理：

1. 从 IBM i estate 导出 ARCAD REF / XREF 关系数据。
2. 通过 Program Flow Map 选择一条有业务意义的 Program Flow。
3. 展示 Evidence Core 对 RPG、CL 和 DDS 的扫描结果、源码坐标和 TBD。
4. 在 Dify 中使用同一 Flow 的 Metadata 限定检索范围。
5. 用业务语言查询 Program 行为、业务规则、数据影响和异常路径。
6. 展示 Dify 回到原始 Evidence ID、Source Coordinate 和 Snapshot。
7. 生成 `poc_draft` 或 `in_review` 状态的 BRD 草稿。
8. 用 SME Review 和 Decision Log 说明草稿如何经过审批，避免 AI 推断自动升级
   为业务事实。

## Sample Output Package

一个合成的 mini sample 位于
[docs/samples/atlas-phoenix-lens-mini-output/](docs/samples/atlas-phoenix-lens-mini-output/)。
它展示了从 Program Flow Map export 到 source-backed modernization evidence
的 handoff 形态：

- `program-flow-export.sample.csv`
- `program-analysis.sample.md`
- `flow-analysis.sample.md`
- `modernization-evidence.sample.yaml`

## 上游 Program Flow Map Contract

上游 Neo4j Program Flow Map repo 预期提供一个小而稳定的 handoff package。
具体 repo link 和文件名待补，但 contract 应包含：

| Artifact | 用途 |
| --- | --- |
| Flow metadata | Flow name、business area、source system、export timestamp 和 source snapshot |
| Program list | 选中 flow 中包含的 programs，可按顺序或分组 |
| Call edges | Caller、callee、relationship type 和 ARCAD / XREF evidence reference |
| Source-member mapping | Program name 到 library、source file、member、path 或 repo location 的映射 |
| Field trace | 可选 field movement、file/table access、key fields 和 persistence hints |
| Review notes | 已知 gap、unresolved calls、confidence notes 和 SME hints |

推荐导出格式为 CSV、JSON、YAML 或 Markdown。下游 skills 应把 Program Flow
Map export 作为导航证据，而不是最终业务真相。现代化决策获得批准前，仍需要
source scanning 和 SME review。

模板见：
[docs/program-flow-map-export-contract.md](docs/program-flow-map-export-contract.md)。

## 核心能力

### 1. Program Flow 发现

- 导入 ARCAD REF / XREF 关系数据。
- 通过另一个内部 Program Flow Map repo 将关系数据加载到 Neo4j
  （`TBD: add repo name/link`）。
- 保留权威的 `CALLS` 调用关系。
- 生成可供人工审查和后续分析使用的 Program Flow Map。
- 在证据可用时，补充 screen、report、API、T&C、batch、advice、DB field
  等信息。
- 为迁移团队、SME 和 AI agents 提供共享的系统导航图。

### 2. 基于源码的业务逻辑发现

- 使用 Program Flow 输出作为源码扫描导航。
- 按单个 program 或单个 flow 分析 RPG、CL 和 DDS。
- 提取 observed behavior、calculation、validation、file I/O、dependencies、
  exception path 和 operational evidence。
- 产出带稳定 ID、源码坐标、覆盖缺口和 SME 问题的结构化证据。
- 只有通过审查门禁后，才进入 module analysis、BRD generation、spec writing
  和 migration planning。

### 3. Dify 知识激活

- 将文档和 Program 扫描结果作为有 Metadata 的可检索副本。
- 用 SME Program Flow 限定 Capability、Module 和 Program 范围。
- 支持业务问答、证据钻取和 BRD 草稿生成。
- 保留 Canonical Evidence、审批状态和下游契约的独立控制。

## 对公司的意义和商业价值

Atlas Phoenix Lens 的价值不是“更快写一份文档”，而是降低每个
Modernization 项目承担的不确定性和证据风险：

- **释放交付产能：**减少重复代码阅读、上下文重建和大范围 SME 解释；
- **避免下游返工：**降低因错误理解 Legacy 行为产生的需求、设计、测试和
  迁移返工；
- **保留机构知识：**将关键行为、证据和 SME 决策转化为可持续维护的组织资产；
- **Portfolio 复用：**不同团队复用同一套 Flow、Evidence Contract、
  Review Gate 和 Dify 编排方法；
- **支持可靠退役：**更清楚地区分必须保留、重新设计、合并或可安全退役的行为。

```text
年度可量化净价值
  = 释放的 Discovery 和 SME 交付产能价值
  + 避免的证据相关返工成本
  + 避免的重复建设成本
  + 经验证的提前退役价值
  - Phoenix Lens 年度运行成本
```

实际收益必须通过有 Owner 的 Baseline、可比较的 Pilot 数据和 Finance 认可的
单位成本验证，不能把目标或场景测算写成已经兑现的收益。

## 路演和协作材料

- 可直接复制到 Confluence 的中文项目介绍：
  [docs/atlas-phoenix-lens-confluence-project-detail.zh-CN.md](docs/atlas-phoenix-lens-confluence-project-detail.zh-CN.md)。
- 可直接复制到 Confluence 的英文项目介绍：
  [docs/atlas-phoenix-lens-confluence-project-detail.md](docs/atlas-phoenix-lens-confluence-project-detail.md)。
- 中文项目详细介绍：
  [docs/atlas-phoenix-lens-project-detail.zh-CN.md](docs/atlas-phoenix-lens-project-detail.zh-CN.md)。
- 英文 Project Detail：
  [docs/atlas-phoenix-lens-project-detail.md](docs/atlas-phoenix-lens-project-detail.md)。
- 中文路演稿：
  [docs/atlas-phoenix-lens-pitch.zh-CN.md](docs/atlas-phoenix-lens-pitch.zh-CN.md)。
- 英文 Pitch 和 Speaker Notes：
  [docs/atlas-phoenix-lens-pitch.md](docs/atlas-phoenix-lens-pitch.md)。
- 材料导航页：
[docs/atlas-phoenix-lens-index.md](docs/atlas-phoenix-lens-index.md)。
- 历史申报稿：
  [docs/open-collaboration-submission.zh-CN.md](docs/open-collaboration-submission.zh-CN.md)。
- 贡献指南：
  [CONTRIBUTING.md](CONTRIBUTING.md)。

## Roadmap

| Phase | Focus |
| --- | --- |
| P0 | 打通 Program Flow Map、Evidence Core 与 Dify 的 Evidence、Metadata、状态和审批映射 |
| P1 | 完善 SME Decision Log、BRD Gate、Write-back 和检索/生成评测集 |
| P1 | 使用真实 10K+ 行 RPG 程序和 5–10 Program Chain 验证完整性与证据追溯 |
| P2 | 扩展脱敏 Demo、路演材料和 Portfolio Adoption 指标 |
| Future | 在当前平台基准通过后，为 COBOL 和其他 Legacy 技术增加 Adapter、Skills 与 Benchmark |

## 仓库结构

> 说明：Neo4j Program Flow Map application 目前维护在另一个公司内部 repo
> 中，这里先作为上游依赖占位。等 repo 信息确认后，再补充链接和 setup notes。

```text
skills/       规范 agent skills、模板、参考资料和脚本
docs/         设计说明、quickstarts、scorecards、图和示例
scripts/      校验脚本和辅助工具
tests/        contract 和 skill helper scripts 的回归测试
templates/    共享输出模板
schemas/      结构化 artifact schemas
outputs/      生成结果或本地运行输出
```

`.claude/`、`.opencode/`、`.agents/`、`.codex/` 等运行时目录只是 adapters
或同步副本。规范 skill 源位于 `skills/<skill-name>/`。

## 关键 Skills

| Skill | 用途 |
| --- | --- |
| `legacy-ibmi-program-list-batch` | 准备可恢复的 program-list 扫描批次和 one-program prompt 队列。 |
| `legacy-current-state-discovery` | 从文档/RAG 证据抽取 current-state functional discovery 报告和 catalogs。 |
| `legacy-ibmi-program-analyzer` | 分析单个 IBM i program，并提取 source-backed behavior evidence。 |
| `legacy-ibmi-flow-analyzer` | 把 finalized reader-first program analyses 受控合并为一份 coverage-complete SME/Dify Core Review；不重建 transaction flow。 |
| `legacy-ibmi-module-analyzer` | 将已审查的 program / flow evidence 组装成 module-level context。 |
| `legacy-brd-writer` | 基于已批准 module context 生成 evidence-backed BRD package。 |
| `legacy-step-validator` | 判断 artifact 是否可以继续、带 warning 继续，或必须阻塞。 |
| `legacy-html-exporter` | 将稳定 Markdown artifacts 导出为便于 stakeholder 阅读的 HTML。 |

更多 skill family 信息见
[docs/skill-card-index.md](docs/skill-card-index.md) 和
[docs/skill-families.md](docs/skill-families.md)。

## 快速开始

建议先看：

- [QUICKSTART.md](QUICKSTART.md)：短 walkthrough。
- [docs/new-team-flow-scan-quickstart.md](docs/new-team-flow-scan-quickstart.md)：
  flow-scan adoption path。
- [docs/flow-analysis-prompt-e2e-guideline.md](docs/flow-analysis-prompt-e2e-guideline.md)：
  Codex / Claude Code flow prompt 测试。
- [docs/flow-analysis-copilot-chat-e2e-guideline.md](docs/flow-analysis-copilot-chat-e2e-guideline.md)：
  GitHub Copilot Chat 分段式 flow 测试。
- [docs/rpg-code-scan-e2e-guideline.md](docs/rpg-code-scan-e2e-guideline.md)：
  当前 RPG source-code scan 端到端流程。
- [docs/EXAMPLE-tutorial/](docs/EXAMPLE-tutorial/)：完整 minimal example。

常用校验命令：

```bash
python3 -m pytest
scripts/sync-skills.sh --target all --check
```

Windows 环境运行 Python 脚本时，先使用 `py -3`，再 fallback 到 `python`。

## 证据与治理原则

项目严格区分四类内容：

- **Observed behavior**：legacy 系统实际做了什么，由源码、运行日志、screen、
  report 或数据证据支撑。
- **Inferred business rules**：可能的业务含义，但仍需 SME 审查。
- **SME decisions**：业务含义被确认、拒绝或仍待解决。
- **Modernization decisions**：审查后做出的保留、重构、退役或延后决策。

每条被批准的规则都应该带有来源证据或 SME approval。证据不清、缺失或冲突时，
生成 `TBD-*`，而不是把不确定内容包装成漂亮但不可审计的文字。

## 当前状态

Atlas Phoenix Lens 背后是一套面向生产使用的 IBM i / AS400 现代化发现
skill family，目前仍在持续演进。已审查 skill scorecards 位于
[docs/reviews/](docs/reviews/)，运行时矩阵见
[docs/runtime-matrix.md](docs/runtime-matrix.md)。

## License

见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 和 [AUTHORS.md](AUTHORS.md)。
