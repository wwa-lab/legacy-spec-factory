# Atlas Phoenix Lens - 内部开源共创申报稿

## 项目一句话

Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub / Seven Mountains
SDLC 叙事下的 M3 Discovery 能力，通过 Program Flow Map 和 agent skills
扫描 RPG / IBM i 源码，将遗留系统行为沉淀为结构化、可审查、可复用的现代化证据。

## 项目简介

Atlas Phoenix Lens 不是直接把 RPG 代码翻译成 Java，而是作为 Atlas
Engineering Delivery Hub 的 M3 Discovery 能力，先帮助团队理解 legacy system
behavior。它从 ARCAD REF / XREF、program call relationships、RPG / CL /
COBOL / DDS source evidence 等低层证据出发，先通过上游 Neo4j Program Flow
Map 形成程序调用视图，再用 Legacy Spec Factory skills 沿着 flow 扫描源码，
提取 observed behavior、calculation logic、validation logic、exception
handling、data usage、operational evidence 和 SME review questions。

最终输出是一层 structured modernization evidence，可用于 BRD generation、gap
analysis、future target architecture planning、legacy / .NET application
retirement 和 AI-native SDLC handoff。

## 解决的问题

在 legacy modernization 中，最大的难点往往不是“代码能不能转”，而是：

- 团队不知道旧系统中的 programs 如何互相调用。
- 业务逻辑分散在 RPG、CL、COBOL、DDS、screens、reports、batch jobs、DB2 for i
  files 和运行约定中。
- 通用 AI 代码总结缺少 source coordinates、evidence strength、SME questions
  和 review gates，难以直接支撑迁移决策。
- 不同团队会重复做 discovery，缺少统一的 AI-friendly evidence contract。

## 方案设计

Atlas Phoenix Lens 采用两段式 discovery workflow：

1. **Program Flow discovery**
   - 上游 Neo4j Program Flow Map repo 导入 ARCAD REF / XREF 关系数据。
   - 保留权威 `CALLS` relationships。
   - 导出 selected flow、program list、call edges、field trace 和 source-member
     hints。

2. **Source-code scanning with skills**
   - 本 repo 使用 Program Flow output 作为源码扫描导航图。
   - 通过 `legacy-ibmi-program-list-batch`、`legacy-ibmi-program-analyzer`、
     `legacy-ibmi-flow-analyzer` 等 skills 逐步分析 program 和 flow。
   - 产出可审查的 `BEH-*`、`BR-*`、`TBD-*` evidence。
   - 通过 SME review 后，再进入 BRD、gap analysis、target architecture 或
     application retirement decision。

## 可复用资产

- Program Flow Map handoff contract
- Legacy Spec Factory agent skills
- Source-code scan prompts 和 batch-control workflow
- Evidence taxonomy、ID conventions、review gates
- Validators 和 helper scripts
- Codex、Claude Code、OpenCode 多运行时 portable skill model
- 双语 README、设计图、项目宣传图
- Synthetic mini output sample：
  `docs/samples/atlas-phoenix-lens-mini-output/`

## AI-Friendly 特性

- 使用 Markdown、YAML、CSV、SVG 等易读、易解析格式。
- 使用稳定 ID，例如 `BEH-*`、`BR-*`、`TBD-*`，保障 traceability。
- 明确区分 observed behavior、inferred business rules、SME decisions 和
  modernization decisions。
- 用 validators 显式判断 artifact 是否可进入下一阶段。
- 将 Program Flow output 视为 navigation evidence，而不是 final business truth，
  保留 source scanning 和 SME review 作为治理门禁。

## 对公司的价值

- 让团队在阅读大量源码前，先看清 program flow。
- 降低 legacy discovery 重复劳动。
- 把 RPG / IBM i 行为转化为可审查、可追踪的 modernization evidence。
- 更早暴露 migration planning 中的 open questions。
- 支撑 future target architecture、legacy / .NET application retirement 和
  AI-assisted SDLC。
- 在 AI 提效的同时，保留 SME 对业务含义的最终控制权。

## 当前边界

| 范围 | 状态 |
| --- | --- |
| Neo4j Program Flow Map app | 上游公司内部 repo，链接待补 |
| Flow export contract | 本 repo 已定义 handoff boundary |
| Legacy Spec Factory skills | 本 repo 已包含 |
| Source-code evidence extraction | 本 repo 已通过 skills/templates/scripts/validators 支持 |
| BRD/spec/handoff generation | 作为下游路径支持，需要 evidence review 后进入 |

## Demo Path

```text
ARCAD REF / XREF data
  -> internal Neo4j Program Flow Map repo
  -> selected Program Flow Map export
  -> legacy-ibmi-program-list-batch
  -> legacy-ibmi-program-analyzer
  -> legacy-ibmi-flow-analyzer
  -> structured modernization evidence
  -> SME review / BRD / gap analysis / target architecture planning
```

## 后续计划

| 阶段 | 目标 |
| --- | --- |
| Phase 1 | 稳定双语 README、设计图、宣传图和申报材料 |
| Phase 2 | 补充上游 Neo4j Program Flow Map repo link，并固化 export contract |
| Phase 3 | 将当前 synthetic mini sample 扩展为脱敏 internal demo package |
| Phase 4 | 打通从 Program Flow export 到 modernization evidence 的 E2E demo |
| Phase 5 | 输出 HTML / slide material，支持内部推广和复用 |

## 待补事项

- 补充上游 Neo4j Program Flow Map repo 名称和链接。
- 用批准后的脱敏样例替换或补充 synthetic mini sample。
- 确认截图、repo 名称、业务字段是否需要进一步 redaction。

## 相关材料

- 材料导航页：
  [atlas-phoenix-lens-index.md](atlas-phoenix-lens-index.md)
- 贡献指南：
  [../CONTRIBUTING.md](../CONTRIBUTING.md)
- 3 分钟讲解稿和 speaker notes：
  [atlas-phoenix-lens-pitch.md](atlas-phoenix-lens-pitch.md)
- Program Flow Map export contract：
  [program-flow-map-export-contract.md](program-flow-map-export-contract.md)
- Mini output sample：
  [samples/atlas-phoenix-lens-mini-output/](samples/atlas-phoenix-lens-mini-output/)
