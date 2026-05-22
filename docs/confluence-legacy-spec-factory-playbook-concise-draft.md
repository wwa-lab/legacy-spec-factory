# Legacy Spec Factory 内部知识库草稿

> 同步说明：本中文精简稿与英文精简稿 [`confluence-legacy-spec-factory-playbook-concise-draft.en.md`](confluence-legacy-spec-factory-playbook-concise-draft.en.md) 保持同步。后续任何结构、表格、标题或内容调整，都需要同时更新两份文件。

## 1. 目标

Legacy Spec Factory 是一套面向 IBM i / AS400 现代化的证据驱动方法。它的目标不是把 RPGLE、CLLE、COBOL 或 DDS 代码直接翻译成 Java，而是从遗留系统中恢复真实业务意图，形成可审计、可评审、可交付给下游 SDLC 的规格说明。

核心原则：

- 以业务能力为中心，而不是以程序为中心。
- RAG / 代码知识图谱提供证据上下文，但不是最终真相。
- 遗留系统行为、推导出的业务规则、现代化设计决策必须分开管理。
- 所有关键规则必须有证据或 SME 审核。
- `spec.yaml` / `spec.md` 是下游交付的主要输入。

## 2. 推荐页面结构

| No. | Page | Purpose |
|---:|---|---|
| 01 | Method, Principles & Delivery Process | 说明方法论、核心原则和整体交付流程 |
| 02 | Scope, Non-Goals & Assumptions | 定义范围、不做什么、关键假设和风险 |
| 03 | Evidence Model, SME Review & Traceability | 定义证据模型、SME 审核规则和追踪链路 |
| 04 | System Context & Architecture | 描述遗留系统、目标系统和上下游系统关系 |
| 05 | As-Is Business Processes | 沉淀当前业务流程、系统流程、程序流程和数据流程 |
| 06 | Functional Requirements Catalogue | 汇总可交付给下游团队的功能需求 |
| 07 | Business Rules Catalogue | 管理业务规则、证据、置信度和 SME 决策 |
| 08 | Data Model & Data Dictionary | 整理数据对象、字段含义、关系和数据质量问题 |
| 09 | Integrations, Batch Jobs & Scheduling | 记录接口、批处理、调度、报表和补跑机制 |
| 10 | NFRs, Controls & Observability | 沉淀非功能需求、控制点、审计和监控要求 |
| 11 | Delivery Packaging, Gates & Handoff | 定义交付包、质量门禁和下游 handoff 标准 |

## 3. 标准页面模板

每个页面建议使用同一套结构：

| Section | Content |
|---|---|
| Purpose | 这个页面解决什么问题 |
| Scope | 覆盖和不覆盖的范围 |
| Inputs | 需要哪些输入材料 |
| Outputs | 该页面应产出什么内容 |
| Evidence Required | 需要关联哪些证据 |
| Open Questions / TBDs | 尚未确认的问题 |
| Review Owner | 谁负责审核 |
| Approval Gate | 什么条件下可以进入下一步 |

## 4. 证据与审核模型

知识类型：

| Type | Meaning |
|---|---|
| `observed_behavior` | 遗留系统被代码、运行日志、报表或样例证明的真实行为 |
| `inferred_business_rule` | 从行为、代码或数据中推导出的业务规则 |
| `modernization_decision` | 面向目标系统的设计或取舍决策 |
| `unknown_tbd` | 证据不足、含义不清或存在冲突的问题 |

证据强度：

| Strength | Meaning |
|---|---|
| `confirmed_from_code` | 源代码直接证明 |
| `observed_in_runtime` | 运行日志、spool、样例交易或报表证明 |
| `confirmed_by_sme` | SME 明确确认 |
| `strongly_inferred` | 多个证据点强推断，但仍需审核 |
| `weakly_inferred` | 弱推断，不能直接进入需求 |
| `contradictory` | 证据之间存在冲突 |
| `missing` | 关键证据缺失 |

审批规则：

- 没有证据的内容不能成为正式需求。
- 推导出的业务规则必须经过 SME 确认。
- 现代化决策需要产品、架构或交付负责人确认。
- 所有 `TBD-*` 必须被解决，或被明确标记为 non-blocking。

## 5. 推荐落地路径

```text
RAG / Code Knowledge Graph / Source Evidence
  -> Module Context
  -> As-Is Process
  -> Business Rules
  -> Functional Requirements
  -> spec.yaml / spec.md
  -> Traceability Package
  -> SDLC Handoff
```

默认从模块视角开始。如果模块边界、流程和 RAG 证据已经具备，不需要先做全量源码挖掘。源码级分析主要用于补证、查冲突、验证高风险规则和解决 TBD。

## 6. Action Plan

| Phase | Timeline | Objective | Key Actions | Deliverables |
|---|---:|---|---|---|
| 1. Build Structure | Week 1 | 建立 Confluence 页面骨架 | 创建首页和 11 个子页面；套用标准页面模板 | 页面树和空白模板 |
| 2. Align Methodology | Week 1 | 形成方法论共识 | 写清楚目标、原则、证据模型、SME 角色和交付路径 | 方法论首页和证据模型页面 |
| 3. Create Templates | Week 2 | 让团队可以按模板执行 | 建立 Scope、Process、Rule、Requirement、Data、Integration、Traceability、Handoff 模板 | 可复制的页面模板 |
| 4. Select Pilot Module | Week 2 | 选择一个真实模块试点 | 确认模块边界、输入材料、owner 和 SME | 试点范围和输入清单 |
| 5. Populate Pilot | Week 3 | 用真实内容验证结构 | 填充流程、规则、数据、接口、批处理和 TBD | 试点模块草稿 |
| 6. Run SME Review | Week 3-4 | 审核高风险规则和不确定项 | 组织 SME review；确认、驳回或标记规则 | SME 决策记录和 approved rules |
| 7. Build Traceability | Week 4 | 建立从证据到交付的链路 | 连接 evidence -> behavior -> rule -> requirement -> acceptance criteria | Traceability matrix |
| 8. Standardize & Roll Out | Ongoing | 固化为团队工作方式 | 复盘试点；沉淀好例子和反模式；推广到更多模块 | 团队 playbook 和样例库 |

## 7. Execution Tracker

| Task | Priority | Owner | Target | Status |
|---|---:|---|---|---|
| Create Confluence homepage | High | Modernization Lead | Week 1 | Not Started |
| Create 11 child pages | High | BA | Week 1 | Not Started |
| Draft methodology summary | High | Modernization Lead / Architect | Week 1 | Not Started |
| Define evidence taxonomy | High | BA / SME / Architect | Week 1 | Not Started |
| Create business rule template | High | BA | Week 2 | Not Started |
| Create traceability template | High | BA / Architect | Week 2 | Not Started |
| Select pilot module | High | Product Owner / SME | Week 2 | Not Started |
| Populate pilot pages | High | BA / Engineer | Week 3 | Not Started |
| Run SME review | High | SME / BA | Week 4 | Not Started |
| Finalize handoff checklist | Medium | Delivery Lead / Architect | Week 4 | Not Started |
| Publish pilot as reference | Medium | Modernization Lead | Week 4+ | Not Started |

## 8. Definition of Done

第一版知识库完成标准：

- 11 个核心页面已创建。
- 每页都有 purpose、inputs、outputs、owner 和 approval gate。
- 证据模型和 SME 审核规则已定义。
- 至少一个试点模块已填充。
- 至少完成一次 SME review。
- 至少能展示一条完整链路：evidence -> behavior -> business rule -> requirement -> acceptance criteria。
- 团队知道下一个模块应该从哪个模板开始。

