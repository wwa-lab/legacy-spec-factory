# 旧系统现代化：基于证据的 BRD 草稿生成方法

## 一句话定位

我们不是让 AI 一键生成最终 BRD。

我们要做的是：从 IBM i / AS400 旧系统代码、运行证据、历史文档、RAG / code graph 输出和 SME 片段中，生成一份**有证据链、可追溯、可审阅、可由 SME 和业务方确认的 BRD 草稿**。

AI 的作用是降低 discovery 成本、结构化旧系统知识、提前暴露规则缺口和不确定信息；最终正式 BRD 必须由人审阅、由人批准。

## 面向谁讲

### 面向内部 SME

SME 最关心的是：

- AI 到底怎么看代码；
- 业务规则是怎么从 RPGLE、CLLE、DDS、DB2、job flow、program call relationship、screen/report logic 里提取出来的；
- SME 不一定能一开始提供完整四视图或四条 flow，AI 会如何把碎片材料整理成 coverage、缺口和问题；
- 每条规则能不能追溯到原始 source 或运行证据；
- 有歧义的逻辑怎么处理；
- AI 会不会乱编；
- SME 需要怎么 review。

核心表达：

> AI 不替代 SME。  
> SME 的角色从“从零翻代码写 BRD”，变成“基于证据审阅、纠正、确认和补充缺失信息”。

### 面向业务方

业务方最关心的是：

- 这套方法能不能帮助他们理解当前系统行为；
- 能不能帮助他们确认业务流程和业务规则；
- 能不能帮助他们发现规则缺口、异常场景和未来改造影响；
- 输出结果是不是可信、可解释、可审阅。

核心表达：

> 业务方看到的不是一份黑盒 AI 结论，而是一份带证据、带置信度、带开放问题、可逐项确认的当前状态 BRD 草稿。

### 面向管理层和交付负责人

管理层和交付负责人最关心的是：

- 能不能提速 discovery；
- 能不能降低人工整理成本；
- 能不能规模化复制到更多 legacy program；
- 风险是否可控；
- 结果是否可重复；
- 有没有治理机制；
- 能不能支撑后续 spec generation 和 Java / Cloud modernization。

核心表达：

> 这是一套可治理的 legacy discovery 方法，不是一次性的 prompt demo。

## 当前痛点

IBM i / AS400 旧系统里的业务知识通常不是集中在一份文档里，而是散落在很多地方：

- RPGLE、CLLE、COBOL、SQL 代码；
- DDS 物理文件、逻辑文件、显示文件、打印文件；
- DB2 for i 表结构、字段、索引、控制表；
- program call relationship、batch job、scheduler、job log、message queue；
- screen、report、spool output、sample transaction；
- 历史功能规格、技术设计、程序规格、文件规格、数据字典；
- RAG / code graph 输出、ARCAD REF relationship、source snippet、字段字典映射；
- SME 的经验、历史 workaround、人工操作流程。

传统人工 discovery 往往会遇到几个问题：

- 需要大量 SME 时间从源代码里还原业务逻辑；
- 文档写出来后，很难证明每条规则来自哪里；
- 业务规则、技术实现、历史补丁、异常处理容易混在一起；
- 异常场景、边界条件、报表和批处理逻辑容易漏掉；
- 后续新旧系统对比、spec generation、测试设计都会继承这些不确定性。

因此，我们真正要解决的不是“让 AI 多写几页 BRD”，而是让旧系统知识变成一套**可验证、可审阅、可追溯的业务理解资产**。

## 方法概览

Legacy Spec Factory 的核心思路是：

```text
旧系统证据 + 历史文档 + RAG / code graph + SME 片段
  -> 四视图 coverage、缺口和 SME 问题
  -> 观察到的系统行为
  -> 推断出的业务规则候选
  -> 业务验证场景种子
  -> BRD 章节和追溯矩阵
  -> SME / 业务方 review
  -> 经人工批准的旧系统 BRD baseline
```

这套方法强调五个关键词：

- **基于证据**：关键结论必须能追到 source、runtime evidence、document evidence 或 SME 确认；
- **可审阅**：不确定内容不被润色成事实，而是进入 Open Questions；
- **可追溯**：证据、行为、规则、问题、验证场景都有稳定 ID；
- **人工批准**：AI 可以提取、组织、起草，但不能替代 SME 和业务方判断。
- **BRD 事实门控**：四视图 coverage 可以帮助 review，但只有 `confirmed_by_sme`、`code_backed` 或明确批准的证据才能进入 BRD 事实正文。

## repo 里的真实设计支撑

这个 repo 已经不是一个单 prompt 的原型，而是一套 skill-based pipeline。

主要设计包括：

- `legacy-ibmi-evidence-intake`：登记 source、DDS、job log、spool、report、sample transaction 等证据；
- `legacy-document-evidence-intake`：把 Office、Visio、PDF、图片等历史材料转成带坐标的文档证据；
- `legacy-flow-context-normalizer`：把散落文档、RAG 摘要和 SME note 整理成四视图 coverage、缺口和 SME 问题；它不是 flow 生成器，也不产出 BRD-ready 事实；
- `legacy-module-context-intake`：把 RAG、source snippet、字段字典、SME 片段或已 review 的四视图上下文打包，并为每个 claim 标注 BRD source eligibility；
- `legacy-ibmi-inventory`：识别 program、file、screen、report、job、object relationship；
- `legacy-ibmi-program-analyzer`：分析单个程序的 call map、data touch、routine logic、file I/O、validation logic、error handling、coverage；
- `legacy-ibmi-flow-analyzer`：把多个 program 连接成一个业务 transaction flow；
- `legacy-ibmi-data-model-analyzer`：分析 DDS / DB2 数据模型和访问路径；
- `legacy-ibmi-screen-report-analyzer`：分析 DSPF、PRTF、screen、report 逻辑；
- `legacy-ibmi-runtime-evidence-miner`：从 job log、spool 等运行证据中提取 runtime observation；
- `legacy-ibmi-module-analyzer`：组装 module 级别的四视图 coverage，并生成 BRD Source Eligibility Crosswalk；
- `legacy-brd-writer`：生成 capability 级别的 legacy BRD Package；
- `legacy-sme-review-facilitator`：组织 SME review 问题包，并记录决策；
- `legacy-step-contract`：规定每一步的输入、执行、输出和验证契约；
- `legacy-step-validator`：做机械校验、语义校验和 SME readiness 校验；
- `legacy-traceability-packager`：打包证据、BRD、spec、测试和决策之间的追溯关系。

这说明 repo 的主线不是“一次性让 AI 看全部代码然后写 BRD”，而是把 discovery 拆成多个可检查、可验证、可回滚的步骤。

## 粒度模型

repo 里的 BRD Factory 是 module-first、program-grounded、capability-output。

可以这样理解：

```text
Module      = 业务理解边界，可以来自 reviewed context、SME 片段和/或 approved flow evidence
Flow        = 一条交易或行为链
Program     = 证据分析粒度
Capability  = BRD 输出粒度
```

这意味着：

- 不应该每个 program 写一个小 BRD，再机械合并；
- 也不应该把整个 module 一次性扔给 AI 生成 BRD；
- program analysis 和 flow analysis 的作用是提供 code-backed / runtime-backed 证据；
- 历史文档、RAG 输出和 SME 片段可以先形成四视图 coverage，但不能自动变成 BRD 事实；
- module analysis 负责形成业务边界、四视图 coverage 和 BRD source eligibility；
- BRD writer 根据一个明确的 capability 生成业务可读的 BRD Package，只把 eligible evidence 写成事实正文。

## BRD Package 是什么

repo 里定义的主要近期输出是一个 reviewable BRD Package：

```text
05_brds/<CAPABILITY-SLUG>/
  brd.md
  brd-review.md
  validation-scenarios.md
  traceability.md
  review-decision.yaml
```

其中：

- `brd.md` 是业务可读的 BRD 草稿；
- `brd-review.md` 是 SME review checklist 和 sign-off 页面；
- `validation-scenarios.md` 是 BRD 阶段的业务验证场景种子，不是正式测试用例；
- `traceability.md` 展示 BRD 元素和证据之间的追溯关系；
- `review-decision.yaml` 记录 SME review 决策。

BRD 必须覆盖的核心章节包括：

1. 功能目的；
2. 业务场景和用例；
3. 渠道；
4. 用户界面或用户触点；
5. 系统接口；
6. 当前状态流程；
7. 校验规则；
8. 异常处理；
9. 依赖关系。

可选章节包括安全 / 认证要求、补充流程或设计说明、source document mapping。可选章节只有在证据或 SME 输入支持时才写，不能为了填模板而编造。由 AI 整理出的候选流程、候选节点或缺口说明只能作为 review surface，不能直接写成 BRD 事实。

## BRD 不是什么

这份 BRD 只描述当前 legacy system。

它不做这些事情：

- 不做 old-vs-new gap classification；
- 不判断 No-gap、Gap1、Gap2；
- 不决定目标系统是否保留某个旧系统行为；
- 不生成 Java / Cloud 架构；
- 不生成正式 acceptance criteria；
- 不生成正式 test cases；
- 不生成 SDD handoff package；
- 不把所有观察到的旧系统行为自动当成未来系统需求。

正式 BRD 是一个经过人工 review 的 legacy baseline。后续如果要进入 spec generation、gap analysis、golden-master testing 或 Java / Cloud modernization，需要单独的下游 gate。

## 证据到 BRD 的转换链路

repo 里的主链路可以概括为：

```text
EV-*  证据
  + SME fragment / RAG context / historical document fragment
  -> coverage item / TBD-* / SME question
  -> BEH-*  观察到的系统行为
  -> BR-*  业务规则候选
  -> VAL-*  业务验证场景种子
  -> BRD section + traceability
```

这里最重要的是区分：

- 代码和 runtime evidence 可以证明“旧系统做了什么”；
- 但它们不能自动证明“业务上应该这样做”；
- 因此，观察行为可以由证据支持；
- 业务规则候选必须等待 SME 确认；
- 无法确认的信息必须进入 Open Questions。
- `candidate_only`、`generated_draft`、`questions_only`、`missing` 只能进入 `TBD-*`、SME 问题或 source enrichment，不能进入 BRD 事实正文。

例如：

- 代码中出现一个 credit limit check，可以作为观察到的系统行为；
- 但它是否代表正式业务政策，还是历史补丁、技术 workaround、临时控制，需要 SME 判断；
- 在 SME 确认前，它只能是 `needs_sme_review` 的业务规则候选。

## 如何防止 AI 乱编

repo 里的防幻觉机制不是靠一句“请不要编”，而是靠结构和 gate。

主要控制点包括：

### 证据绑定

每个关键 claim 都应该绑定到证据 ID，例如：

- `EV-*`：证据；
- `OBJ-*`：对象；
- `BEH-*`：观察到的行为；
- `BR-*`：业务规则候选或已批准规则；
- `TBD-*`：开放问题；
- `VAL-*`：业务验证场景种子。

如果一个说法无法绑定到证据或 SME 确认，就不能写成事实。

### 知识类型区分

repo 区分不同类型的知识：

- `observed_behavior`：观察到的系统行为；
- `inferred_business_rule`：从行为中推断出的业务规则；
- `modernization_decision`：目标系统设计决策；
- `unknown_tbd`：未知或待确认事项。

这些不能混在一起。

### 证据强度区分

repo 也区分证据强度：

- `confirmed_from_code`：由代码直接确认；
- `observed_in_runtime`：由运行证据观察到；
- `confirmed_by_sme`：由 SME 确认；
- `strongly_inferred`：由多个证据点强推断；
- `weakly_inferred`：弱推断；
- `needs_sme_review`：需要 SME review；
- `contradictory`：证据矛盾；
- `missing`：证据缺失。

弱证据不能被写成强事实。高置信度也不能绕过 SME review。

### BRD Source Eligibility Firewall

为了避免四视图 coverage 影响 BRD 质量，repo 现在额外要求每个上游 claim 带上 BRD source eligibility：

- `confirmed_by_sme`：可以进入 BRD 事实正文；
- `code_backed`：可以进入 BRD 事实正文；
- `source_documented`：只能支持 source mapping 或 SME 问题，除非该文档 claim 已被 SME 或 code 证据确认；
- `candidate_only`：只能作为问题或候选 seed；
- `generated_draft`：只能作为 coverage gap 或 review question；
- `missing`：必须进入 `TBD-*` 或 source enrichment。

因此，BRD 不是“看起来完整的 flow 文档”。BRD 是经过证据门控后的当前系统业务 baseline。四视图 coverage 可以帮助 SME review，但不能替代证据。

### Open Questions 机制

代码、SME 或已批准文档中无法确认的信息不能写成事实，必须进入 Open Questions。

典型情况包括：

- source 缺失；
- DDS / PRTF / DSPF 缺失；
- job log 或 spool 不完整；
- 字段语义不清楚；
- 多个 program 实现不一致；
- SME note 和代码冲突；
- RAG 或 AI 整理出来的 flow 看起来合理，但没有 source、runtime 或 SME 确认；
- 无法判断某个行为是业务规则、bug、历史补丁还是 workaround。

这些情况应该生成 `TBD-*`，并标记：

- 问题类型；
- 相关证据；
- resolver；
- 是否 blocking；
- 需要什么补充证据或 SME 决策。

### 分层验证

repo 的 Step Contract 和 Step Validator 把验证分成三层：

1. **机械验证**：文件是否存在、ID 是否解析、schema 是否匹配、敏感数据是否处理、traceability 是否完整；
2. **AI 语义复核**：claim 是否真的被证据支持、是否夸大证据、是否有 scope creep、是否隐藏假设；
3. **SME / 人工审批**：业务含义、规则意图、边界、例外、开放问题和最终批准。

只有这三层都通过，输出才有资格进入下一步。

## 如何处理 30,000 行以上的大程序

repo 里已经有 large-program analysis 设计。

核心原则是：

> 不要把 30,000 行 RPG 程序当成“大文本摘要问题”。  
> 要把它当成“基于证据的程序理解问题”。

### 为什么不能固定切块

把一个大 RPG member 按 1,000 行一段切开，然后分别总结，看起来很快，但很危险。

原因是：

- 一个 routine 可能被很多远处的地方调用；
- 一个字段可能在一处读取、另一处修改、再通过参数返回；
- 错误路径、indicator、return code 常常跨越 routine；
- 工具型 subroutine 在局部看起来不重要，但可能处在关键业务路径上；
- chunk summary 可能写得很流畅，但遗漏 caller、callee、data carrier 和状态变化。

这种错误最危险，因为它看起来合理，但很难被业务方发现。

### 正确做法

large-program mode 先建立结构，再做语义分析：

1. source size 和 structure preflight；
2. deterministic source index；
3. routine-level cards；
4. Program Call Map；
5. Logic Decomposition Ledger；
6. Data Touch Map；
7. Key File & Field Logic；
8. field-level File I/O mutation matrix；
9. Exception Closure Ledger；
10. deep-read windows；
11. Coverage Ledger；
12. evidence-backed synthesis。

### coverage 机制

每个 routine 或 source window 要标记 coverage：

- `indexed_only`：结构已识别，但还不能支持强业务结论；
- `deep_read`：相关 source window 已经深读，可以支持证据化 claim；
- `blocked`：证据缺失、矛盾或不足，不能安全下游使用。

如果一个 coverage item 或 flow claim 依赖某个会改变状态的 routine，而这个 routine 只是 `indexed_only`，那么不能把它写成确定业务事实。要么回到 program analysis 做 deep-read，要么记录 SME waiver 或 open question。

## 如何保证多次运行一致性和可重复性

repo 里已有的支撑包括：

- canonical skill source 放在 `skills/`；
- runtime adapter 通过 sync 保持一致；
- skill review scorecard；
- runtime matrix；
- workflow-state contract；
- stable ID convention；
- Step Contract 里的 idempotency 字段；
- synthetic corpus 用于内部 repeatable pilot；
- traceability package 支持稳定 package ID。

这些设计可以帮助不同会话、不同工具、不同 runtime 之间保持一致。

不过，为了生产级可重复性，还建议增强：

- 为每次运行记录标准 run metadata；
- 为输入 evidence bundle 生成版本号；
- 对 source、DDS、runtime evidence、RAG bundle、SME notes 计算 input hash；
- 在输出中记录 skill version；
- 在输出中记录 model version；
- 记录运行时间、operator、环境、证据清单、redaction 状态和 validation 结果；
- 多次 rerun 后做 output diff comparison；
- 对比 claim 是否变化、confidence 是否变化、ID 是否新增或删除、证据链接是否变化、TBD 是否变化。

这里要注意：一致性不等于每次生成的自然语言完全一样。真正要保证的是：

- 同一批输入下，核心 claim 稳定；
- stable ID 不乱变；
- 证据链稳定；
- open questions 稳定或变化可解释；
- 输出差异能被 review。

## 如何证明 BRD 可信、可追溯、可审阅

我们不应该用“AI 准确率很高”作为主要说法。

更可靠的证明方式是一条完整的治理链：

1. **证据登记**：source、DDS、job log、spool、screen、report、sample transaction、SME note 都有 evidence ID 和 sensitivity 状态；
2. **对象盘点**：program、file、screen、report、job、object relationship 被 inventory 记录；
3. **程序分析**：call map、routine logic、data touch、file I/O、validation logic、error handling 和 coverage 被记录；
4. **流程分析或上下文覆盖**：多个 program 之间的 transaction flow、data lineage、persistence、exception chain 被连接；若 SME 暂时无法提供完整 flow，则先形成四视图 coverage、缺口和 SME 问题；
5. **module coverage assembly**：四视图 module coverage 形成 capability、rule seed 和 BRD Source Eligibility Crosswalk；
6. **BRD traceability**：BRD 里的行为、规则、验证场景、开放问题都链接到 eligible evidence 或明确的 `TBD-*`；
7. **机械验证**：检查 ID、文件、schema、敏感数据、traceability；
8. **语义复核**：检查 claim 是否真的匹配证据，是否夸大，是否隐藏假设；
9. **SME validation**：SME 确认、拒绝、延期或要求补证；
10. **业务确认**：业务方确认当前状态流程、场景、规则和异常是否可理解、可用于后续对比；
11. **review trail**：所有决策、sign-off、open question 和 follow-up 都被记录。

这比单纯说“AI 很准”更有说服力。因为任何人都可以检查这份 BRD：

- 这条规则来自哪里；
- 哪个代码、日志或 SME note 支持它；
- 证据强度是什么；
- 置信度是什么；
- 是否需要 SME review；
- 是否还有 open question；
- 谁在什么时候批准了它。

## SME 怎么 review

SME review 的目标不是读一大篇 AI 生成文本，而是基于证据做决策。

review 问题包应该包括：

- BRD 必填章节是否完整；
- 每个 `TBD-*` 是否 blocking；
- 每个 `BR-*` 规则候选是否符合业务意图；
- 是否存在 contradiction；
- observed behavior 是业务规则、技术实现、bug、历史补丁，还是 workaround；
- validation scenario 是否覆盖 happy path、exception path、boundary condition；
- `questions_only` / `needs_sme_review` 的内容是否应该补证、确认、延期或删除；
- 是否需要更多 source、runtime evidence 或业务确认。

repo 里的 review workflow 建议一次给 SME 3 到 7 个问题，并按风险排序：

1. blocking TBD；
2. contradiction；
3. low-confidence rule；
4. high-risk business rule；
5. validation scenario boundary；
6. remaining behavior confirmation。

每个问题都应该带上：

- target ID；
- 当前 claim；
- evidence ID；
- evidence strength；
- confidence；
- AI suggestion；
- SME answer；
- decision outcome。

SME 的决策结果可以是：

- confirmed；
- rejected；
- deferred；
- marked non-blocking；
- marked blocking；
- split into follow-ups；
- needs more evidence。

SME 的回答要记录原话或明确决策，不要由 AI 自行改写成新的事实。

## 业务方怎么 review

业务方不需要看底层 call graph 或 source line。

业务方重点 review：

- 当前业务流程是否讲得通；
- 业务场景是否完整；
- 渠道、用户触点、系统接口是否符合实际；
- 校验规则是否符合业务政策；
- 异常处理是否符合实际操作；
- 报表、通知、人工处理、运营控制点是否遗漏；
- Open Questions 是否清楚；
- 哪些问题会影响后续新旧系统对比和迁移决策。

业务方看到的应该是业务语言：

- 触发事件；
- 参与角色；
- 业务对象；
- 状态变化；
- 正常路径；
- 异常路径；
- 控制点；
- 依赖；
- 需要确认的问题。

program name、file name、library、commit、rollback、copybook 等技术细节可以放在 traceability 或 appendix 里，而不是作为 BRD 主叙事。

## 管理层应该关注的价值

这套方法对管理层的价值不是“AI 自动写文档”，而是：

- 缩短 discovery 周期；
- 降低 SME 从零整理的负担；
- 提高旧系统知识的结构化程度；
- 更早暴露规则缺口和异常场景；
- 让 discovery 输出可以被 review 和审计；
- 让多个 legacy program 的分析方式更一致；
- 为后续 spec generation、old-vs-new comparison、golden-master test、Java / Cloud modernization 打基础；
- 降低下游团队接收不确定需求的风险。

管理层可以把它理解为一个 discovery control plane：

```text
证据收集
  -> 结构化分析
  -> coverage / source eligibility
  -> BRD 草稿
  -> SME review
  -> 业务确认
  -> 批准后的 legacy baseline
  -> 后续 gap analysis / spec / handoff
```

## 当前边界和限制

需要主动说明的限制包括：

- AI 不保证天然正确；
- AI 不替代 SME；
- AI 不替代业务方决策；
- 不能把 RAG 输出当最终事实；
- 不能把 context-only claim 标成 code-confirmed；
- 不能把 AI 整理的四视图 coverage、RAG 候选或 generated draft 当成 BRD 事实；
- 不能把代码行为自动当成业务意图；
- 不能把高置信度推断自动当成 approved rule；
- 不能把缺失或矛盾证据藏在漂亮文字里；
- 不能用固定切块摘要处理超大 RPG 程序；
- 不能在 BRD 阶段直接决定目标系统实现；
- 不能在 BRD 阶段直接做 No-gap / Gap1 / Gap2 分类。

这些边界不是缺点，而是可信治理的一部分。

## 建议增强项

repo 里已经有很多治理设计，但如果要进入更严肃的 pilot 或生产环境，建议继续增强：

### 运行元数据

每次运行记录：

- run ID；
- timestamp；
- operator；
- input evidence bundle；
- source version；
- input hash；
- skill version；
- model version；
- runtime；
- validation result；
- output artifact path。

### 输入版本和 hash

对以下输入计算 hash：

- RPGLE / CLLE / COBOL source；
- DDS；
- DB2 metadata；
- job log；
- spool；
- screen/report evidence；
- RAG bundle；
- SME notes；
- historical documents。
- flow-normalization coverage package。

这样可以证明多次运行是否使用同一批输入。

### 输出 diff comparison

多次运行后比较：

- 新增或删除的 claim；
- confidence 变化；
- evidence link 变化；
- open question 变化；
- rule status 变化；
- validation finding 变化。

这可以帮助团队判断变化是输入变化导致的，还是模型不稳定导致的。

### pilot dashboard

建议为 pilot 记录：

- discovery 用时；
- SME review 用时；
- 生成 claim 数量；
- 有证据支持的 claim 比例；
- open question 数量；
- blocking TBD 数量；
- SME confirmed / rejected / deferred 数量；
- rerun diff 数量；
- traceability coverage；
- downstream readiness。

## 建议 pilot 路线

建议选择一个业务上有代表性但范围可控的 capability。

理想 pilot 条件：

- 有明确业务 owner；
- 有明确 IBM i SME；
- source、DDS、DB2 metadata 可获取；
- 有 program call relationship 或 RAG / code graph 输出；
- 有 SME 片段或历史文档可以帮助建立 module context；不要求 SME 一开始就能提供完整四条 flow；
- 至少有一类 runtime evidence，例如 job log、spool 或 sample transaction；
- 敏感数据可 redaction；
- SME 有时间参与 review；
- 业务方愿意确认当前状态流程和规则。

不要一开始选择最大、最复杂、最没有边界的系统；也不要选择过于 toy 的例子。最好选择一个真实、有业务价值、但能在有限时间内完成闭环的 capability。

## pilot 成功标准

建议用这些指标评估：

- 是否比人工从零整理更快；
- 是否生成了业务方能读懂的当前状态流程或清楚标注缺口的 coverage；
- 每条关键规则是否有 evidence link；
- open questions 是否被清楚暴露；
- SME 是否能高效 review；
- SME reject / correction 是否被记录；
- 业务方是否能确认流程、规则，并理解哪些内容仍是问题或待补证；
- traceability 是否完整；
- rerun 是否稳定；
- 输出是否能支撑后续 gap analysis 或 spec generation。

注意，不建议把“AI 写了多少页”作为成功指标。

真正的成功是：

- discovery 成本下降；
- 旧系统知识更结构化；
- 证据链更清楚；
- 不确定性更早暴露；
- SME 和业务方 review 更高效；
- 下游 modernization 风险更可控。

## 可用于汇报的主叙事

可以按这个顺序讲：

1. 旧系统 discovery 的难点不是代码语言，而是业务知识散落且不可追溯；
2. 我们不追求一键最终 BRD，而是生成 evidence-backed、reviewable 的 BRD 草稿；
3. AI 的角色是提取、组织、起草和提出问题；
4. SME 的角色是基于证据确认、纠正和补充；
5. 业务方的角色是确认当前流程、业务规则和异常场景，同时理解哪些内容仍然是 `TBD-*` 或 `questions_only`；
6. 管理层获得的是更快、更一致、更可治理的 discovery 方法；
7. repo 里已经有 skill-based pipeline、schema、workflow、review gate 和 traceability 设计；
8. 大程序通过 source index、routine cards、call map、data touch map、deep-read windows 和 coverage ledger 处理；
9. 无证据或有歧义的信息进入 Open Questions；
10. 最终正式 BRD 必须 human-reviewed、human-approved。

## 可用于结尾的一段话

这套方法的重点不是让大家盲目信任 AI。

相反，它是为了避免大家盲目信任 AI。

我们让 AI 做它擅长的事情：快速读取大量材料、提取结构、整理证据、提出规则候选和问题。

我们让 SME 和业务方做他们必须做的事情：判断业务含义、确认规则、识别例外、批准正式产物。

最终产出的 BRD 不是黑盒答案，而是一份可以被追溯、可以被挑战、可以被修正、可以被批准的 legacy business baseline。

这才是 AI 在 Legacy System Modernization 中更可靠、更可落地的角色。
