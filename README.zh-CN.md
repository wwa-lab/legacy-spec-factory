# Atlas Phoenix Lens

[English](README.md) | 中文

![Atlas Phoenix Lens promotional visual](docs/assets/atlas-phoenix-lens-promo.png)

**Atlas Phoenix Lens** 是 **Atlas Engineering Delivery Hub** / Seven
Mountains SDLC 叙事下的 **M3 Discovery** 能力，用于扫描 RPG code，并把
legacy system behavior 转换为结构化的 modernization evidence。

这个仓库承载该能力背后的 **Legacy Spec Factory** skills、tooling、
evidence contracts、templates 和 documentation。它帮助团队把底层 ARCAD
REF / XREF 数据、程序调用关系，以及 RPG / CL / COBOL / DDS 源码证据，
转换为结构化、可审查、可复用的现代化知识资产。

当前仓库聚焦两个连续能力：

1. **生成 Program Flow**：基于 ARCAD REF / XREF 数据生成 Program Flow
   Map，让团队看清 legacy programs 之间的调用关系。Neo4j import 和
   Program Flow Map application 目前在另一个公司内部 repo 中维护
   （`TBD: internal Program Flow Map repo link`）。
2. **用 skills 扫描源码**：把 Program Flow 作为导航图，让 agent skills
   沿着 flow 检查源码，提取业务行为、计算逻辑、校验逻辑、异常处理、
   数据使用和运行证据。

这个项目**不是**把 legacy 源码直接翻译成 Java 或云服务。它的目标是恢复
遗留系统中隐藏的业务意图，保留证据链，暴露需要 SME 判断的问题，并为后续
BRD、差异分析、目标架构规划、应用退役和 AI-native SDLC 交付准备可信输入。

完整历史 README 和更深入的设计说明保存在
[docs/full-reference-readme.md](docs/full-reference-readme.md)。

## Delivery Hub 定位

Atlas Phoenix Lens 位于 Atlas Engineering Delivery Hub 的 Discovery 阶段，
连接前置 planning/estimation 和后续 build、testing、deployment、
maintenance 工作。

![Atlas Engineering Delivery Hub Seven Mountains SDLC static visual](docs/assets/atlas-engineering-delivery-hub-static.png)

![Atlas Phoenix Lens position in Atlas Engineering Delivery Hub](docs/assets/atlas-phoenix-lens-delivery-hub-position.svg)

可编辑源文件：
[docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd](docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd)。

## 当前范围

Atlas Phoenix Lens 目前以两个 repo 协同的方式交付：

| 范围 | 状态 |
| --- | --- |
| Neo4j Program Flow Map application | 上游公司内部 repo，链接待补 |
| Program Flow Map export contract | 在本 repo 中作为 handoff boundary 先行定义 |
| Legacy Spec Factory skills | 已包含在本 repo 的 `skills/` 下 |
| RPG / CL / COBOL / DDS 源码扫描 | 通过 agent skills、templates、validators 和 guidance 支持 |
| BRD / spec / handoff generation | 作为审查门禁后的下游输出支持 |

本 repo 是 evidence 和 skill 层。它消费 Program Flow Map 输出，沿着 flow
扫描源码，并产出结构化 modernization evidence。Neo4j application 本身暂不在
这个 repo 中维护。

## 命名关系

| 名称 | 含义 |
| --- | --- |
| **Atlas Phoenix Lens** | Atlas Engineering Delivery Hub 下的 M3 Discovery capability 叙事 |
| **Legacy Spec Factory** | 支撑 evidence workflow 的 repo skill/tooling package |
| **Program Flow Map** | 上游 Neo4j application，用于可视化 ARCAD REF / XREF 关系 |
| **Modernization evidence** | 用于 SME review、BRD/gap analysis 和 target-architecture planning 的结构化输出 |

## 为什么需要它

很多遗留系统现代化失败，并不是因为代码不能转换，而是因为团队没有真正弄清：
旧系统到底做了什么、哪些行为是真正的业务规则、哪些功能应该保留、重构、退役
或重新设计。

所以 Atlas Phoenix Lens 不从“把 RPG 转成 Java”开始。它先建立 evidence
layer：哪些行为来自源码或运行证据，哪些只是推断，哪些已经由 SME 确认，
哪些现代化决策仍然开放。只有在行为和业务含义被理解之后，代码转换或目标架构
交付才有可靠基础。

Atlas Phoenix Lens 在 legacy 系统和现代化交付之间提供一层可复用的证据层：

```text
ARCAD REF / XREF data
  -> internal Neo4j Program Flow Map repo (TBD)
  -> Program Flow Map
  -> targeted source-code scan with skills
  -> evidence-backed program / flow analysis
  -> SME questions and modernization-ready business evidence
  -> BRD / spec / handoff packages when approved
```

## 实现设计概览

![Atlas Phoenix Lens implementation design overview](docs/assets/atlas-phoenix-lens-design.svg)

可编辑源文件：
[docs/assets/atlas-phoenix-lens-design.mmd](docs/assets/atlas-phoenix-lens-design.mmd)。

## Demo Scenario

给评审看的短路径：

1. 从 IBM i estate 导出 ARCAD REF / XREF 关系数据。
2. 将关系数据加载到上游 Neo4j Program Flow Map repo。
3. 选择一个代表性 transaction flow，例如 account update、card
   adjudication、nightly batch 或 customer journey step。
4. 导出 flow package：program list、call edges、可选 field trace 和
   source-member hints。
5. 使用 `legacy-ibmi-program-list-batch` 准备可恢复的 code-scan queue。
6. 对 flow 上的每个 program 使用 `legacy-ibmi-program-analyzer`。
7. 使用 `legacy-ibmi-flow-analyzer` 将 program findings 连接成一条业务可读的
   behavior chain。
8. 与 SME 审查生成的 `BEH-*`、`BR-*` 和 `TBD-*` evidence，再进入 BRD、
   gap analysis 或 target-architecture planning。

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
- 按单个 program 或单个 flow 分析 RPG / CL / COBOL / DDS。
- 提取 observed behavior、calculation、validation、file I/O、dependencies、
  exception path 和 operational evidence。
- 产出带稳定 ID、源码坐标、覆盖缺口和 SME 问题的结构化证据。
- 只有通过审查门禁后，才进入 module analysis、BRD generation、spec writing
  和 migration planning。

## 内部开源共创价值

Atlas Phoenix Lens 被设计为内部开源共创能力，而不是一次性项目脚本。它支持：

- **AI-friendly 复用**：清晰的 Markdown、YAML、CSV、示例、validators 和
  稳定证据 ID。
- **跨团队标准化**：用统一方式描述 program flow、源码发现、证据强度和
  SME 决策。
- **可移植 agent skills**：规范源位于 `skills/`，可以同步到 Codex、
  Claude Code 和 OpenCode 适配目录。
- **加速现代化发现**：团队可以复用 flow map、code-scan prompts、
  evidence contracts 和 review checklists，而不是重复建设发现方法。
- **支撑目标架构**：输出可用于未来目标架构规划、legacy / .NET 应用退役、
  以及 AI-assisted SDLC handoff。

参赛报名材料草稿见：
[docs/open-collaboration-submission.md](docs/open-collaboration-submission.md)。
中文一页申报稿见：
[docs/open-collaboration-submission.zh-CN.md](docs/open-collaboration-submission.zh-CN.md)。
3 分钟讲解稿和 speaker notes 见：
[docs/atlas-phoenix-lens-pitch.md](docs/atlas-phoenix-lens-pitch.md)。
材料导航页见：
[docs/atlas-phoenix-lens-index.md](docs/atlas-phoenix-lens-index.md)。
贡献指南见：
[CONTRIBUTING.md](CONTRIBUTING.md)。

## Roadmap

| Phase | Focus |
| --- | --- |
| Phase 1 | 稳定 bilingual README、design diagram、promotional visual 和 submission narrative |
| Phase 2 | 完成上游 Program Flow Map export contract，并补充内部 repo link |
| Phase 3 | 将当前 mini sample 扩展为更完整的脱敏 demo package |
| Phase 4 | 强化从 Program Flow export 到 modernization evidence 的 E2E demo |
| Phase 5 | 打包 stakeholder-facing HTML / slide material，便于内部推广 |

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
| `legacy-ibmi-program-analyzer` | 分析单个 IBM i program，并提取 source-backed behavior evidence。 |
| `legacy-ibmi-flow-analyzer` | 分析跨多个 programs 的端到端 transaction flow。 |
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
