# Vendor BRD AI POC 与 Atlas Phoenix Lens 对比及落地改进方案

## 1. Executive Summary

本次评估的两个对比主体是 **Vendor BRD AI POC** 与我方 **Atlas Phoenix Lens**，不是 Vendor 与某个内部 repo 的简单二选一。

**Atlas Phoenix Lens** 是 Atlas Engineering Delivery Hub 下的 M3 Discovery 能力。本报告将其当前实现拆分为三个协同部分：

1. **Program Flow Map**：基于 ARCAD REF/XREF 关系生成程序调用与导航视图；Neo4j application 位于上游公司内部 repo。
2. **Legacy Spec Factory 核心层**：本 repo 承载的 Skill-driven 源码扫描、证据契约、SME Gate、Traceability 和下游交付能力。
3. **Dify 实施层**：当前规划的知识库与编排路径，将 6000+ 文档和 6000+ Program 扫描结果纳入检索范围，再由 SME Program Flow 导航生成 BRD 草稿。

Atlas Phoenix Lens 的 Legacy Spec Factory 核心层已经设计了 Evidence → Program → Flow → Module → BRD → SME Review → Spec → Traceability → SDD Handoff 链路。当前真正需要改进的不是重新设计这条链路，而是打通 Program Flow Map、Legacy Spec Factory 与 Dify 之间的证据、状态和审批契约，并验证 Vendor POC 能否作为 Atlas Phoenix Lens 的自动建模与交互适配器接入。

管理层初步 Review 进一步明确：按大模块描述提取基础需求可能不是 Vendor 的核心差异化能力；Vendor 的主要产品优势体现在自动建模、BPMN、需求生成、自动澄清和语义对话。最终技术判断应集中在 10K+ 行大型程序和跨程序 Program Chain 两类复杂场景，而不能仅依据 UI 完整度或生成文档页数。

**建议方向：**先完成 Atlas Phoenix Lens 内部 Program Flow Map → Legacy Spec Factory → Dify 的证据和状态映射，再开展 Vendor + Atlas Phoenix Lens 的受控集成 Pilot；暂不采用 Vendor Standalone 作为正式 BRD 生产链路。

## 2. Assessment Scope

本次评估范围包括：

- 管理层和 SME 对有限 POC 功能展示的功能观察；
- Atlas Phoenix Lens 当前 README、Legacy Spec Factory `skills/`、`docs/`、验证脚本和状态表；
- 用户提供的三步 Dify 实施思路；
- 2026-07-23 在当前工作区执行的结构、同步、链接和测试检查。

本次评估不包括：

- 实际操作 Vendor POC；
- 在同一业务输入上运行 Vendor 和 Atlas Phoenix Lens；
- 验证当前 Dify 知识库的 metadata、检索过滤和输出 Schema；
- 使用客户真实数据完成端到端 Pilot；
- 验证 Vendor 的商业条款、DPA、模型训练政策或私有化部署能力。

因此本文是**设计与部署评估**，不是基于相同数据集的产品 Benchmark。对 Dify 当前实施状态标记为“待确认”的内容，不应自动视为已缺失或已完成。

## 3. 两方方案现状

### 3.1 Vendor POC 层

POC 展示的主要链路为：

```text
源码/扫描结果
    ↓
自动语义抽取与建模
    ↓
业务对象、实体、接口、任务、规则和流程
    ↓
自动需求澄清与语义对话
    ↓
BRS/FRS 类文档预览
```

已展示能力不等于已验证能力。证据坐标、SME 决策历史、安全控制、重跑一致性和结构化导出仍需 Pilot 证明。

### 3.2 Atlas Phoenix Lens 当前方案

Atlas Phoenix Lens 以 Program Flow Map 作为跨程序导航入口，以 Legacy Spec Factory 作为源码扫描、证据治理和 SME Review 核心，并在当前落地方案中使用 Dify 承担有边界的知识检索与编排。

```text
ARCAD REF / XREF
    ↓
Program Flow Map
    ↓
Legacy Spec Factory 源码扫描与证据治理
    ↓
SME Review / BRD / Spec / Handoff
```

#### 3.2.1 Legacy Spec Factory 核心层

Legacy Spec Factory 的目标设计是 Orchestrator 路由的可分支链路，不是固定线性流水线：

```text
Evidence Intake / Document Intake
    ↓
Inventory
    ↓
Program Analysis / Program Batch
    ↓
Flow Analysis / Data Model Analysis
    ↓
Module Analysis 或 Module-first Context
    ↓
Legacy BRD
    ↓
SME Conversation Review
    ↓
Spec / Decision / Golden Master
    ↓
Traceability / SDD Handoff
```

该核心层同时支持标准 code-backed 路径、内部 `poc_draft`、`daily_delivery` 和 module-first 等模式。`workflow-state.yaml` 用于跨会话状态和历史记录。

#### 3.2.2 Atlas Phoenix Lens 当前 Dify 实施层

当前用户描述的实施思路是：

```text
6000+ 文档 → Dify 文档知识库
6000+ Program 扫描结果 → Dify 代码/分析知识库
SME Program Flow
    ↓
检索文档和代码知识库
    ↓
生成 BRD
```

这条路线适合快速验证检索和生成价值，但它只是 **Atlas Phoenix Lens 当前 Dify 实施层的简化路线**，不是 Atlas Phoenix Lens 的完整能力边界。后续改进的重点是把 Program Flow Map 与 Legacy Spec Factory 已有契约映射进这条实施路线。

## 4. 核心能力对比

| 能力 | Vendor POC | Atlas Phoenix Lens 核心能力 | Atlas Phoenix Lens 当前 Dify 实施 | 判断 |
|---|---|---|---|---|
| 自动建模 | UI-driven；展示实体、接口、规则、任务、流程和 BPMN | Program Flow Map + Skill-driven Program、Flow、Data Model、Module 分析；无同等级交互 UI | 已有扫描结果，自动建模深度待确认 | Vendor 交互更强；Atlas Phoenix Lens 跨程序导航和批量治理更强 |
| SME 参与 | 有问题与回答界面，审批留痕未证明 | SME 是业务事实与规则控制点，已有 Conversation Review/Decision Log 设计 | SME Flow 已作为输入，决策闭环待确认 | 需要打通 UI 与治理记录 |
| 证据追溯 | 有来源概念，逐条可重复追溯未证明 | Legacy Spec Factory 已设计 Evidence ID、知识类型、强度、TBD 和 Traceability | Chunk 是否保留坐标、版本和授权待确认 | Atlas Phoenix Lens 证据契约应成为 Dify/Vendor 接口基线 |
| BRD 边界 | 容易混合 BRD、FRS、技术分析和验收内容 | BRD、Spec、AC、TC、Decision 和 SDD 分层 | Prompt 是否严格执行边界待确认 | 必须在生成和审批两端控制 |
| 可视化交互 | 实体、流程、规则、问答和文档预览较强 | Mermaid、Markdown 和静态 HTML；不等同于交互建模 UI | 主要依赖 Dify UI | Vendor 可补强前端体验 |
| 批处理语义 | 展示部分流程，重跑、恢复、对账等未充分证明 | Program/Flow 分析已设计这些语义，但真实 Pilot 覆盖有限 | 扫描结果是否包含异常/运行时证据待确认 | 三方均需真实样本验证 |
| 数据治理 | 模型边界、保留、训练和租户隔离未证明 | 已有授权、脱敏和敏感性原则 | 原则是否在 Dify 实际执行待确认 | 设计强不等于部署已执行 |
| 可移植性 | 可能依赖 Vendor 平台 | Canonical Skill + runtime adapters | 依赖 Dify Schema 和导出能力 | 需要可逆的数据/Schema 契约 |
| 成熟度证据 | 有限 POC 功能展示 | Skill scorecard、runtime matrix 和测试；仍有 runtime/drift gap | 缺少当前部署验证材料 | 不应将设计状态当作生产成熟度 |
| 10K+ 行大型程序 | 尚未展示分段覆盖、跨段语义或防静默截断 | Legacy Spec Factory 已设计分批 Deep Read、Routine Index、读取计划和防截断验证；真实 Pilot 覆盖仍有限 | 扫描结果是否完整保留大程序结构待确认 | Atlas Phoenix Lens 设计更深入，但双方均须用真实大程序证明 |
| Program Chain 需求提取 | 展示任务关系/BPMN，未证明完整跨程序证据链 | Program Flow Map 提供导航边界；Legacy Spec Factory 已设计源码支撑的调用边、字段血缘、异常、持久化和重启分析 | SME Flow 已作为导航输入，但不能自动视为真实调用链 | 必须以同一真实业务链进行 Benchmark |

Atlas Phoenix Lens 当前的 `legacy-html-exporter` 只负责将 Markdown 生成静态浏览器页面，不提供 Vendor POC 所展示的实体关系探索、BPMN 交互、语义对话或证据钻取，因此不构成 Vendor 可视化层的替代品。

### 4.1 管理层关注点与差异化判断

| 管理层观察 | SME 判断 | 对方案的影响 |
|---|---|---|
| 可以按大模块描述提取基础需求 | Vendor 和 Atlas Phoenix Lens 都可能做到；但描述生成只能形成 `candidate/poc_draft`，不能直接成为 approved BRD | 不作为采购或架构选型的决定性指标 |
| 模块 2-6 的概念较好 | 自动建模、BPMN、需求生成、自动澄清和语义对话是 Vendor 的主要产品化优势 | 建议吸收这些交互理念，或将 Vendor 作为可视化/交互适配器评估 |
| 未看到 10K+ 行大型程序处理方式 | 这是遗留系统分析的决定性可扩展性问题；演示证据不足 | 设置 10K-20K 行真实程序为强制 Challenge Case |
| 未看到 Program Chain 需求提取方式 | 单程序局部正确不能保证端到端业务正确；Program 顺序也不能替代源码调用证据 | 设置 5-10 程序真实链路为强制 Challenge Case |

当前差异化判断是：Vendor 在“问得好、看得清”方面更强；Atlas Phoenix Lens 通过 Program Flow Map 和 Legacy Spec Factory，在“跨程序范围如何建立、证据如何分层、复杂程序如何受控拆解、跨程序结论如何审查”方面设计更严格。Atlas Phoenix Lens 的这些优势仍属于设计与本地验证优势，必须通过与 Vendor 相同数据集的 Field Pilot 才能升级为生产能力结论。

## 5. Atlas Phoenix Lens 当前 Dify 实施路线的优点与风险

### 5.1 优点

- SME Program Flow 能限定业务范围，降低模型从 6000+ 程序中自行猜测边界的风险。
- 文档和代码分析结果同时参与检索，可以互相补充业务背景和实际实现。
- Dify 适合快速验证 Prompt、检索策略、回答格式和 SME 可读性。
- 不需要等待完整治理平台实现，就可以先形成 `poc_draft` 供内部讨论。

### 5.2 风险

#### Dify 知识库不是 Evidence Source of Truth

如果原始材料只以 Chunk 形式进入知识库，后续回答可能无法稳定说明原始文件、版本、页码/行号、OCR 质量、授权、脱敏和知识类型。Dify 应保存可检索副本，Canonical Evidence Package 应保留在可版本化的结构化制品中。

#### 全局知识库可能跨模块串线

所有检索至少需要 capability/module、program、source type、evidence strength、artifact status、source version、snapshot 和 SME scope 等过滤条件。

#### SME Flow 不是自动批准的事实

SME Flow 可能是 confirmed、working draft、inferred 或 needs review。它可以限定范围和导航检索，但不能自动覆盖代码证据或成为完整 BRD 流程。

#### 从 RAG 直接跳到 BRD 会丢失中间语义

RAG 输出需要先进入 Module Context/Evidence Map，区分 observed behavior、inferred rule、candidate object、contradiction、retrieval gap 和 TBD，再进入 BRD。

#### 检索结果不能自动成为 approved BRD fact

代码推断的业务目的、候选对象、AI 流程图、变量名语义、角色权限和未经运行时验证的预期结果，只能进入候选项、开放问题或 SME Review。

## 6. 建议目标架构

```text
原始文档 / 源码 / 日志
          ↓
Canonical Evidence Intake
授权 / 脱敏 / 坐标 / Hash / 质量
          ↓
Atlas Phoenix Lens Program Flow Map
ARCAD REF/XREF / Program Chain 导航
          ↓
Legacy Spec Factory Program / Flow / Data Analysis
Atlas Phoenix Lens 核心 Skill，可选 Vendor 自动建模
          ↓
Module Context Package
Evidence Map / Candidate / TBD / Contradiction
          ↓
SME Program Flow 导航与范围确认
          ↓
Dify Retrieval / Vendor UI / 问题与草稿生成
          ↓
SME Review / Decision Log / Write-back
          ↓
BRD Package / Traceability Gate
          ↓
Spec / Golden Master / SDD Handoff
```

Vendor 是可选的分析/交互适配器，Dify 是 Atlas Phoenix Lens 当前可替换的检索与编排实施层；Canonical Evidence、审批状态和下游契约继续由 Atlas Phoenix Lens 的 Legacy Spec Factory 核心层控制。

## 7. Atlas Phoenix Lens 设计到 Dify 部署的映射

以下不是重新设计 Atlas Phoenix Lens，而是将 Program Flow Map 和 Legacy Spec Factory 已有设计映射到具体 Dify 部署。

| 能力 | Atlas Phoenix Lens 已设计 | Dify 状态 | Vendor 可提供 | 部署需要补充 |
|---|---|---|---|---|
| Evidence Intake | 是 | 待确认 | 部分 | Manifest、Hash、授权、脱敏、证据坐标 |
| Program/Object Index | 是 | 扫描结果已计划上传 | 是 | 稳定 Program/Object ID 和关系 Schema |
| Flow Analysis | 是 | SME Flow 驱动 | 是 | confirmed/observed/inferred/unresolved 分层 |
| Module Context | 是 | 待确认 | 部分 | 范围、Evidence Map、矛盾和 TBD 中间包 |
| SME Decision Log | 是 | 待确认 | 有交互 UI | 决策导出、身份、日期、证据和回写 |
| BRD Draft | 是 | 已规划 | 是 | `poc_draft/in_review/approved` Gate |
| Traceability | 是 | 待确认 | 未证明 | 双向 ID、Snapshot、版本和差异 |
| Spec/Test/SDD 边界 | 是 | 当前阶段未覆盖 | 未证明 | 禁止 BRD 草稿越权进入下游 |

### 7.1 Dify Evidence Metadata 最低要求

```yaml
evidence_id:
source_path:
source_version:
sha256:
coordinate:
sensitivity:
authorization:
redaction_status:
knowledge_type:
evidence_strength:
artifact_status:
capability_id:
module_id:
program_id:
snapshot_id:
```

### 7.2 Vendor/Atlas Phoenix Lens 互操作记录

```yaml
claim_id:
statement:
knowledge_type:
status:
evidence_ids: []
source_coordinates: []
open_questions: []
sme_decision:
model_version:
prompt_version:
snapshot_hash:
```

映射测试必须证明字段不被静默丢弃、降级或自动提升为 approved。

## 8. Atlas Phoenix Lens 核心层当前验证快照

以下是 2026-07-23 对 Atlas Phoenix Lens 的 Legacy Spec Factory 核心层重新执行检查的结果，用于区分“设计能力”与“当前工程状态”：

| 检查 | 当前结果 | 影响 |
|---|---|---|
| `python3 -m unittest discover -s tests -q` | 397 tests passed，47 skipped | 本地 unittest 基线通过 |
| PyYAML | 6.0.3 可用 | 当前不存在 PyYAML 缺失错误 |
| `verify-skill-claims.py` | 3 项 drift | Flow Analyzer v0.4.0/9.51 与 scorecard v0.4.1/9.58 不一致 |
| `sync-skills.sh --check` | Module Context 四个 adapter drift | 需要从 canonical source 重新同步；Inventory 当前通过 |
| `check-portable-links.py` | 失败 | 失败集中在生成的演示 PPT manifest 绝对路径，需区分 generated output 与 canonical skill docs |
| Skill Status Truth Table | 9 field-pilot ready；15 repo-ready/provisional；24 total | 不能把所有 Skill 都描述为已 field-pilot 验证 |

Legacy Spec Factory 的 Skill Review Gate 只适用于新增或修改的 Skill。Vendor 产品、Atlas Phoenix Lens 整体能力、Dify 部署和本报告应分别使用适合自身对象的评估标准。

## 9. 落地路线、Owner 与完成标准

### P0：Dify Evidence 基础

| 项目 | 内容 |
|---|---|
| Owner | Atlas Phoenix Lens Platform Team |
| 依赖 | 文档 Intake、Program 扫描输出、Dify metadata/filter 能力 |
| 交付 | Evidence Schema、Chunk metadata、snapshot、授权/脱敏检查、范围过滤 |
| Done | 抽样声明能从 Dify 回到原始文件和精确坐标；跨 module 污染测试通过 |

### P1：SME Review 与 BRD Gate

| 项目 | 内容 |
|---|---|
| Owner | BA/SME Workflow Team |
| 依赖 | Module Context、Evidence Map、SME owner |
| 交付 | Decision Log、TBD、知识类型、BRD 状态、审计历史 |
| Done | 任何 approved statement 都有合格证据或具名 SME 决定；未决项不能静默关闭 |

### P1：检索与生成评测集

| 项目 | 内容 |
|---|---|
| Owner | QA/Evaluation Team + IBM i SME |
| 依赖 | 一个 bounded capability 和标注样本 |
| 交付 | observed/inferred/candidate/exception 的黄金样本和评测脚本 |
| Done | 可报告召回率、unsupported claim、SME 修正率、证据链接成功率和重跑一致性 |

### P1：大型程序与 Program Chain 同数据集 Benchmark

| 项目 | 内容 |
|---|---|
| Owner | QA/Evaluation Team + IBM i SME + Vendor/Atlas Phoenix Lens 技术负责人 |
| 依赖 | 安全批准的源码 Snapshot、黄金调用链和 SME 标注基线 |
| 输入 A | 同一个 10K-20K 行 RPG/COBOL 程序，包含正常、异常和文件访问路径 |
| 输入 B | 同一条 5-10 Program Chain，包含 CL、RPG/COBOL、数据库、外部接口和重启路径 |
| 执行 | Vendor 与 Atlas Phoenix Lens 独立分析；不得共享对方结果，再由 SME 盲评 |
| 指标 | 源码范围登记、Routine/分支覆盖、调用边准确性、字段血缘、异常/重启覆盖、Evidence Link、SME 修正率、重跑一致性和总评审时间 |
| Done | 两个方案均能说明已覆盖、未覆盖和 unresolved 范围；所有 confirmed 调用边和关键 BRD 步骤均有证据 |
| Decision | 任一方案在大型程序或 Program Chain 强制用例失败，不得成为正式 BRD 语义来源 |

### P2：Vendor Integration Pilot

| 项目 | 内容 |
|---|---|
| Owner | Vendor + Atlas Phoenix Lens Integration Team |
| 依赖 | P0/P1 契约稳定、安全和采购审批 |
| 交付 | Schema adapter、可视化入口、问题回写、版本 diff 和导出验证 |
| Done | Vendor 输出无损进入 Module Context/BRD Review；安全、证据和审批 Gate 均通过 |

## 10. 成功指标与 Abort Criteria

### 成功指标

- 抽样 Evidence Link 成功率达到至少 95%；
- unsupported claim 不超过 5%；
- observed behavior 的 SME 修正率不超过约 15%；
- 相同 Snapshot 重跑的核心结果一致或差异可解释；
- 两轮后 SME Review 时间相对基线减少至少 30%；
- 所有 approved 内容具备证据或具名 SME 决定；
- 敏感数据、模型训练和保留策略通过安全审查。
- 10K+ 行程序不存在静默截断，全部源码区间都在读取/处理清单中登记为已分析、受限或 unresolved；
- Program Chain 中 100% 的 confirmed 调用边具有源码或运行时证据，SME 导航顺序未被直接提升为调用事实；
- 关键跨程序字段传递、异常传播、持久化和重启结果达到 Pilot kickoff 时冻结的 SME 覆盖阈值。

### Abort Criteria

- 未授权数据出域或无法确认删除/训练政策；
- 系统隐藏矛盾、伪造来源或自动提升审批状态；
- Vendor/Dify 无法保留并导出关键证据和决策字段；
- 核心语义准确性连续两轮低于约定阈值；
- 10K+ 行程序出现静默截断、未登记源码范围或跨段关键语义丢失；
- Program Chain 生成无证据调用边，或遗漏影响业务结果的关键异常、持久化或重启路径；
- 集成成本超过约定上限且没有可量化效率收益。

指标阈值应在 Pilot kickoff 时冻结并记录版本，避免完成后重新解释成功标准。

## 11. 决策选项

| 方案 | 优点 | 主要风险 | 建议 |
|---|---|---|---|
| Atlas Phoenix Lens Baseline（Program Flow Map + Legacy Spec Factory + Dify） | 可控、可移植、跨程序导航和证据治理边界清晰 | 可视化和交互探索能力较弱，三层契约仍需打通 | 作为我方基础路线继续完成 P0/P1 |
| Vendor + Atlas Phoenix Lens Governance | 自动建模、交互体验、Program Flow 和证据治理可以互补 | Schema 集成、二次开发、采购和锁定成本 | **推荐进入受控集成 Pilot** |
| Vendor Standalone | 上手快、演示效果强 | 证据、审批、数据安全、可移植性和下游污染风险 | 当前不建议用于正式 BRD |

## 12. 最终建议

Atlas Phoenix Lens 应继续坚持：

1. AI 推断不能等同于业务事实；
2. SME 是业务意图和规则的最终控制点；
3. observed behavior、inferred rule 和 modernization decision 必须分层；
4. BRD 结论必须可追溯到证据或 SME 决定；
5. RAG/Vendor 候选内容不能自动升级为 approved；
6. Dify 和 Vendor 都不是唯一 Source of Truth；
7. BRD、Spec、测试和 SDD 必须保持边界；
8. Atlas Phoenix Lens 的整体设计成熟度、Legacy Spec Factory 核心层工程状态与实际部署/Field Pilot 成熟度必须分别陈述。

产品策略上，应优先吸收 Vendor 模块 2-6 的产品化理念，补强自动建模展示、BPMN、需求澄清和语义对话体验。Vendor 是否进入正式方案，则取决于其能否通过 10K+ 行大型程序和 Program Chain 两项强制测试。若不能通过，可将 Vendor 限定为可视化与交互辅助层，但不能作为业务语义或正式 BRD 的 Source of Truth。

**最终判断：**先完成 Atlas Phoenix Lens 内部 Program Flow Map → Legacy Spec Factory → Dify 的证据、状态和审批映射，再验证 Vendor 是否能作为自动建模与交互适配器接入。Vendor 负责增强“问得好、看得清”的体验；Atlas Phoenix Lens 负责“链路看得全、证据记得住、结论审得过”，其中 Dify 负责在有边界的范围内检索和编排。
