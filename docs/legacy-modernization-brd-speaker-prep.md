# AI-Assisted Legacy BRD Discovery from IBM i / AS400 Source

## 1. Executive Summary

Legacy Spec Factory is designed to help modernization teams turn IBM i / AS400 legacy evidence, historical documents, RAG/code graph output, and SME fragments into an evidence-backed, reviewable BRD draft. The method is intentionally not a one-click final BRD generator. Its purpose is to reduce discovery effort, structure legacy knowledge, expose uncertainty, and give SMEs and Business stakeholders a better starting point for review.

The core operating principle is simple: AI may extract, organize, and draft, but it does not replace SME or Business judgment. A final BRD must be human-reviewed and human-approved before it becomes the formal legacy baseline for later gap analysis, spec generation, golden-master planning, or Java/cloud modernization.

中文讲法：
这套方法的定位一定要先讲清楚：我们不是让 AI 一键生成最终 BRD，也不是让业务盲信 AI。我们是让 AI 先把旧系统里的证据、历史文档、RAG/code graph、SME 片段、行为、规则候选、问题点整理成一份可审阅的 BRD 草稿，让 SME 和 Business 在证据链上确认、纠正和补充。

## 2. Why Legacy Discovery Is Hard

IBM i modernization discovery is difficult because business behavior is rarely located in one clean source. It is distributed across RPGLE, CLLE, DDS, DB2 access patterns, batch jobs, program call relationships, screens, reports, job logs, spool output, control files, exception handling, and undocumented operational practice.

Traditional manual discovery often depends on a small number of experts reading source code, reconstructing flows, and writing business language from scratch. This creates predictable risks: slow cycle time, inconsistent coverage, weak traceability, late discovery of exception paths, and uncertainty about whether a documented rule is true business policy or merely an implementation artifact.

The repo's design responds to this by treating legacy discovery as an evidence-backed pipeline. Code and runtime evidence can show what the system does. SME and Business review determine what that behavior means and whether it should become an approved business rule.

中文讲法：
旧系统难不是因为代码看不懂这么简单，而是业务知识散落在很多地方：代码、DDS、DB2、批处理、报表、job log、spool、屏幕、控制表、历史文档、RAG/code graph 和 SME 记忆里。SME 很多时候一开始给不出完整四条 flow，AI 的价值不是替代专家，而是把这些材料结构化成 coverage、缺口和问题，让专家不用从零开始翻。

## 3. Target Audiences and Value

For IBM i SMEs, the value is a shift in work mode. Instead of starting from raw source and manually drafting the BRD, SMEs review evidence-backed findings, validate whether observed behavior is intentional business policy, resolve contradictions, and identify missing evidence.

For Business stakeholders, the value is a clearer current-state story. The BRD draft explains the process, scenarios, validation rules, error handling, dependencies, and open questions in business language. It also makes uncertainty visible, rather than hiding it in polished but unsupported prose.

For Management and delivery leads, the value is discovery acceleration with governance. A skill-based pipeline, stable IDs, evidence links, validation gates, workflow state, and traceability packages make the approach more repeatable and scalable than ad hoc prompting.

中文讲法：
三类人各自关心点不同。SME 关心 AI 怎么看代码、证据在哪里、有没有乱编；Business 关心能不能理解流程和规则，能不能看到问题和不确定性；管理层关心能不能提速、降本、规模化、风险可控。我们要把这套方法同时讲给这三类人听。

## 4. Repository Design Observed

The repository already contains a strong methodology for this use case. The README describes Legacy Spec Factory as a migration-discovery and modernization pipeline that turns IBM i / AS400 system behavior into evidence-backed, reviewable BRDs first, and only later into implementation-ready specifications after stakeholder promotion or gap-analysis decisions.

The repo's preferred operating model is module-first, program-grounded, and capability-output:

```text
Module      = business understanding boundary
Flow        = transaction / behavior-chain slice
Program     = evidence granularity
Capability  = BRD output unit
```

A module can start from reviewed context, SME fragments, historical documents, or approved flow evidence. Flow analysis is still valuable evidence, but complete flow diagrams or a finished module package are not prerequisites for starting discovery.

The main evidence-to-BRD transformation is:

```text
EV-* evidence
  + SME fragment / RAG context / historical document fragment
  -> coverage item / TBD-* / SME question
  -> BEH-* observed behavior
  -> BR-* business rule seed
  -> VAL-* validation scenario seed
  -> BRD section + traceability
```

The repo also distinguishes the default enterprise path from selective source verification:

- Document and flow context normalization when historical materials are scattered; this produces coverage, gaps, and SME questions, not BRD-ready flow facts.
- Module context intake when RAG/code graph evidence, SME fragments, or reviewed module context are available.
- Selective program, flow, runtime, data model, screen, or report analysis when evidence is missing, conflicting, or high risk.
- BRD writing after module coverage carries a BRD Source Eligibility Crosswalk; only eligible evidence becomes factual prose.
- SME review and decision write-back before final BRD approval.

中文讲法：
repo 里不是一个 prompt，而是一套分层 workflow。它先把证据和文档材料登记或规范化，再把 RAG/SME/context 变成可审阅的 coverage 和问题；需要补证时再做 inventory、program、flow、module 分析，最后才写 BRD。BRD 是 capability 级别的输出，不是每个 program 写一个小 BRD 再拼起来。

## 5. Skill-Based Pipeline

The current skill family supports the BRD discovery chain through specialized roles:

| Pipeline Area | Existing Repo Support | Role |
| --- | --- | --- |
| Evidence intake | `legacy-ibmi-evidence-intake`, `legacy-document-evidence-intake` | Register source, DDS, logs, spool, reports, screenshots, documents, and evidence coordinates |
| Context intake | `legacy-module-context-intake` | Organize scattered docs/RAG/SME fragments into coverage, gaps, SME questions, and BRD source eligibility |
| Inventory | `legacy-ibmi-inventory` | Identify programs, files, reports, screens, jobs, and object relationships |
| Program analysis | `legacy-ibmi-program-analyzer` | Extract call maps, data touch maps, routine logic, file I/O, validation logic, error handling, and coverage |
| Flow analysis | `legacy-ibmi-flow-analyzer` | Connect multiple programs into transaction flows, replay paths, persistence, lineage, and exception chains |
| Data / UI / runtime support | `legacy-ibmi-data-model-analyzer`, `legacy-ibmi-screen-report-analyzer`, `legacy-ibmi-runtime-evidence-miner` | Add DB2/DDS, DSPF/PRTF, job log, spool, and runtime observations |
| Module coverage | `legacy-ibmi-module-analyzer` | Assemble the focused module package, capability/rule seeds, and a BRD Source Eligibility Crosswalk |
| BRD drafting | `legacy-brd-writer` | Produce capability-level BRD package with observed behaviors, inferred rules, TBDs, traceability, and validation scenario seeds |
| Review | `legacy-sme-review-facilitator` | Convert open items into SME questions and record decisions |
| Governance | `legacy-step-contract`, `legacy-step-validator`, `legacy-traceability-packager` | Enforce input/output/validation contracts and traceability coverage |

This separation is important. A single large prompt would be more vulnerable to context drift, untraceable synthesis, and unsupported claims. The skill-based pipeline constrains each step to a defined responsibility and output contract.

中文讲法：
这里可以强调“不是一个大模型从头猜到尾”。每个 skill 只做一段事情，并且有输入、输出、不能做什么、怎么验证。这种拆分本身就是风控。

## 6. BRD Package Design

The repo's `legacy-brd-writer` defines the BRD as the primary near-term old-system discovery artifact. The expected package is:

```text
05_brds/<CAPABILITY-SLUG>/
  brd.md
  brd-review.md
  validation-scenarios.md
  traceability.md
  review-decision.yaml
```

The BRD body is business-facing and must cover the SME-required functional analysis shape:

1. Function Purpose
2. Business Scenarios / Use Cases
3. Channels
4. User Interface / User Touchpoints
5. System Interfaces
6. Process Flow
7. Validation Rules
8. Error Handling
9. Dependencies

Optional sections may cover security/authentication, supporting workflow/design notes, and source document mapping only when evidence or SME input supports them.

Generated context, RAG candidates, and coverage-only rows do not become BRD prose by default. They become `TBD-*`, SME questions, or source-enrichment tasks unless confirmed by SME, code-backed evidence, or explicitly approved source documentation.

The BRD explicitly does not produce formal acceptance criteria, test cases, target architecture, modernization decisions, SDD handoff, or old-vs-new No-gap / Gap1 / Gap2 classification. Those are downstream activities after BRD approval and after new-system context is available.

中文讲法：
BRD 不是技术分析报告，也不是目标系统设计。它要用业务语言讲清楚当前旧系统怎么运作，但每个关键点都能回到证据。不能为了把模板填满就编界面、接口、安全要求或业务规则；AI 整理出来的 coverage 也不能直接写成事实。

## 7. Review Workflow

The SME review workflow is designed as a decision process, not a passive sign-off. The facilitator prepares a question pack from the BRD package:

- required BRD section coverage
- `TBD-*` open questions
- `questions_only` and `needs_sme_review` rows from the source eligibility crosswalk
- `BR-*` rule seeds needing review
- contradictions
- behavior claims needing confirmation
- validation scenario seeds

Each question includes linked evidence IDs, evidence strength, confidence, current claim, and optional AI suggestion. The default conversation mode presents 3-7 questions per batch, sorted by blocking risk. SME answers are recorded verbatim and transcribed into a decision log with outcomes such as confirmed, rejected, deferred, marked blocking, marked non-blocking, or needs more evidence.

Business review then focuses on whether the current-state process, scenarios, exception paths, and validation seeds are understandable and complete enough for later comparison and modernization planning.

中文讲法：
SME review 不是最后盖章，而是整套方法的控制点。AI 准备问题、coverage 和证据，SME 决定这个行为是不是业务规则、是不是 bug、是不是历史 workaround、哪些问题阻塞。Business 则确认流程、规则和异常场景是不是能代表真实业务，并理解哪些内容仍然是 `TBD-*` 或 `questions_only`。

## 8. Trust and Traceability Design

The repo separates knowledge type from evidence strength:

| Dimension | Examples |
| --- | --- |
| Knowledge type | `observed_behavior`, `inferred_business_rule`, `modernization_decision`, `unknown_tbd` |
| Evidence strength | `confirmed_from_code`, `observed_in_runtime`, `confirmed_by_sme`, `strongly_inferred`, `weakly_inferred`, `needs_sme_review`, `contradictory`, `missing` |
| BRD source eligibility | `confirmed_by_sme`, `code_backed`, `source_documented`, `candidate_only`, `generated_draft`, `missing` |

This distinction prevents a common failure: treating a plausible inference as a confirmed rule. A code branch may prove that the legacy system behaves a certain way, but it does not automatically prove the intended business policy. Business rule seeds remain `needs_sme_review` until a human confirms them.

The BRD traceability template requires:

- observed behaviors mapped to evidence
- inferred business rules mapped to behaviors and evidence
- validation scenarios mapped to existing rules/behaviors and evidence
- open questions categorized with resolver and blocking status
- evidence items listed with source, sensitivity, redaction status, strength, and usage

The BRD writer only turns `confirmed_by_sme`, `code_backed`, or explicitly approved source-documented claims into factual prose. `candidate_only`, `generated_draft`, `questions_only`, and `missing` remain questions or gaps.

中文讲法：
可信度设计的关键是“分开”。观察到的行为、推断的业务规则、未来系统决策、未知问题，不能混在一起。证据强度也要分清楚：代码确认、运行时观察、SME 确认、强推断、弱推断、缺失或矛盾。现在还要再分一层 BRD source eligibility：哪些能写成事实，哪些只能是问题。

## 9. Risk Control Question 1: How Do We Prevent AI Hallucination and Context Drift?

The repo's answer is evidence binding plus staged validation.

Existing controls include:

- **Source reference binding:** claims use stable IDs such as `EV-*`, `OBJ-*`, `BEH-*`, `BR-*`, `TBD-*`, and `VAL-*`.
- **Evidence strength:** every evidence item is classified so weak evidence cannot masquerade as direct code confirmation.
- **Knowledge-type separation:** observed behavior, inferred rule, modernization decision, and unknown/TBD are treated as different claim types.
- **Anti-hallucination rules:** if a claim cannot link to Tier 1 evidence or named SME confirmation, it must become a TBD, not a confident BRD statement.
- **BRD source eligibility firewall:** candidate/generated/questions-only context cannot become factual BRD prose.
- **Step Contract:** each skill declares inputs, allowed actions, forbidden actions, outputs, and validation requirements.
- **Mechanical validation:** required files, schemas, ID resolution, sensitivity, and traceability can be checked deterministically.
- **AI semantic review:** reviewers check whether claims actually match linked evidence.
- **SME/human approval:** business meaning and rule promotion require human decision.

Proposed enhancements:

- require every generated package to include standardized run metadata
- record model version, skill version, input bundle version, and input hash
- introduce output diff comparison for reruns
- add a reproducibility report that highlights changed claims, changed confidence, new TBDs, and removed evidence links

中文讲法：
防 hallucination 不是靠一句“请不要编”。repo 的设计是让 AI 每说一个关键事实都要能指回证据；不能确认的内容进入 TBD；弱证据不能写成强事实；generated/candidate/questions-only context 不能进入 BRD 事实正文；最后还要经过机械校验、语义复核和 SME 审批。建议增强项是把每次运行的输入 hash、模型版本、skill 版本和输出 diff 标准化。

## 10. Risk Control Question 2: How Do We Handle Very Large Legacy Programs?

The repo already contains a large-program analysis strategy for 20,000-30,000+ line RPG programs.

The principle is: do not treat a large RPG member as a large text summarization problem. Treat it as an evidence-backed program-understanding problem.

Existing controls include:

- size and structure preflight
- deterministic source index
- routine cards for subroutines, procedures, and mainline segments
- Program Call Map
- Logic Decomposition Ledger
- Data Touch Map
- Key File & Field Logic and field-level mutation matrix
- Exception Closure Ledger
- deep-read windows for hot paths, state changers, external boundaries, and error handling
- coverage ledger showing `indexed_only`, `deep_read`, and `blocked`

The repo explicitly forbids fixed line chunk summaries as the source of business facts. If chunking is required, the chunks should follow semantic units: routines, procedures, copybooks, object clusters, or call/data-flow paths.

Cross-chunk stitching happens through the call map, data touch map, field lineage, routine cards, and coverage ledger. Downstream flow or module analysis must not turn an `indexed_only` state-changing routine into a business fact without deeper evidence or a named waiver.

中文讲法：
30,000 行 RPG 不能简单按 1000 行切块摘要。那样会打断调用关系、字段流转和错误路径。正确做法是先建结构索引，再按 routine、调用路径、数据流、状态变更和异常路径做深读。没读到的地方要标 coverage gap，不能假装全懂。

## 11. Risk Control Question 3: How Do We Ensure Consistency and Repeatability?

Existing repo support includes:

- canonical skill source under `skills/`, with runtime adapters synced from it
- skill review scorecards and status matrix
- runtime smoke testing across Codex, Claude Code, and OpenCode for selected skills
- `workflow-state.yaml` as a cross-session state contract
- stable ID conventions for evidence, objects, flows, modules, capabilities, rules, TBDs, scenarios, specs, and traceability packages
- Step Contract idempotency guidance
- synthetic corpus fixtures for repeatable pilot runs, including credit check, blocked credit check, batch AR reconciliation, and screen subfile inquiry
- traceability package IDs stable across reruns of the same package instance

Recommended governance enhancements:

- version every input evidence bundle
- compute an input hash for source, DDS, runtime evidence, RAG bundle, and SME notes
- record skill version and model version in every generated package
- preserve run metadata: timestamp, operator, environment, evidence manifest, source paths, redaction status, and validation result
- compare outputs across reruns and report changed claims, confidence changes, added/removed IDs, and changed evidence links
- define pilot repeatability metrics: same inputs should produce the same stable IDs, equivalent claims, and explainable diffs

中文讲法：
一致性不是要求模型每次文字一模一样，而是要求同一批输入下，ID、证据链、核心结论、开放问题和状态变化可解释。现在 repo 已经有 stable ID、workflow-state、runtime matrix、synthetic fixtures；建议下一步加 input hash、model version、run metadata 和 output diff。

## 12. Risk Control Question 4: How Do We Prove the BRD Is Credible, Traceable, and Reviewable?

The proof is not a single accuracy percentage. It is a chain of controls:

1. **Evidence registration:** every source, DDS, runtime artifact, SME note, or sample transaction is assigned an evidence ID and sensitivity status.
2. **Analysis artifacts:** program, flow, data, screen/report, and module analyses preserve evidence references and coverage gaps.
3. **BRD source eligibility:** module coverage separates BRD-eligible evidence from questions-only or needs-review context.
4. **BRD traceability:** BRD sections link observed behaviors, inferred rules, validation scenario seeds, and open questions back to evidence.
5. **Validation gates:** mechanical validation catches missing files, unresolved IDs, schema issues, sensitivity problems, and non-output violations.
6. **Semantic review:** the artifact is checked against evidence to detect overstated claims, invented facts, scope creep, and hidden assumptions.
7. **SME validation:** SMEs confirm, reject, defer, or request more evidence for business rules and ambiguous behaviors.
8. **Business confirmation:** Business stakeholders confirm whether the current-state process and scenarios are understandable and fit for later comparison.
9. **Review trail:** decisions, sign-offs, open questions, and follow-ups are recorded in review artifacts and decision logs.

This is stronger than claiming high AI accuracy. It shows why a reader can inspect the result, challenge it, and understand exactly what evidence supports each claim.

中文讲法：
我们不应该说“AI 准确率多少所以可信”。更可靠的说法是：这份 BRD 可以被审计。每条关键规则都能追到 evidence；不能确认的进入 open questions；只有 source-eligible 的内容进入 BRD 事实正文；SME 的确认、拒绝、延期和补证要求都有记录。可信来自证据链和 review trail。

## 13. Current Boundaries and Limitations

The current method has clear boundaries:

- It does not produce a one-click final BRD.
- It does not replace SME or Business approval.
- It does not claim that all inferred rules are business policy.
- It does not decide future-state scope or target architecture inside the BRD.
- It does not perform No-gap / Gap1 / Gap2 classification before the BRD is approved and new-system context is available.
- It does not allow context-only or RAG-only claims to be labeled as `confirmed_from_code`.
- It does not require SMEs to provide complete flow diagrams or a finished module package before discovery can start.
- It does not promote generated or candidate coverage into factual BRD prose.
- It does not make a large program safe by summarizing fixed chunks.

Known maturity notes from the repo:

- Several skills are repo-ready but still note pending or partial smoke testing before field-pilot readiness.
- Some governance features requested for production repeatability, such as input hashes, model versions, and standardized output diff comparison, should be treated as proposed enhancements unless implemented in the project artifacts for a given pilot.

中文讲法：
边界要主动讲出来，这样 Business 和管理层才会信任我们没有夸大。尤其要说：RAG 是 evidence context，不是最终事实；SME 不需要一开始就提供完整四条 flow；代码能证明系统行为，但不能自动证明业务意图；最终 BRD 必须人工 review 和 approve。

## 14. Pilot Recommendation

A controlled pilot should use a narrow but business-relevant capability, ideally one with:

- a clear business owner and IBM i SME owner
- available RPGLE/CLLE source and DDS
- known program call relationships or RAG/code graph output
- SME fragments or historical documents sufficient to establish initial module coverage
- at least one runtime artifact such as job log, spool file, or sample transaction
- enough SME availability for review and sign-off
- manageable sensitivity/redaction requirements

Pilot success should be measured by:

- discovery cycle time compared with manual drafting
- number and quality of evidence-linked BRD claims
- number of open questions surfaced early
- SME correction rate and review effort
- Business readability and usefulness
- traceability completeness
- BRD source eligibility coverage: how much is conclusion-ready vs questions-only
- rerun consistency and diff explainability
- downstream readiness for spec generation or gap analysis

中文讲法：
建议 pilot 不要选最大最复杂的系统，也不要选太 toy 的例子。要选一个业务上有价值、范围可控、有 SME、证据可拿到、能看到规则和异常路径的 capability。不要求 SME 一开始提供完整四条 flow，但要有足够片段或历史材料帮助建立初始 coverage。衡量指标不是“AI 写了多少页”，而是节省了多少 discovery 时间，暴露了多少问题，SME review 是否更高效，证据链和 source eligibility 是否完整。

## 15. Suggested Talk Track Close

The modernization risk is not that AI will be too conservative. The risk is that teams may accept polished AI output without knowing what evidence supports it. Legacy Spec Factory is designed to avoid that failure mode.

The method gives us a disciplined way to move from legacy code and operational artifacts to a reviewed business baseline:

```text
AI drafts from evidence.
SME validates meaning.
Business confirms process and rules.
Management gets scalable governance.
Only approved outputs move downstream.
```

That is the right role for AI in legacy modernization: not final authority, but a force multiplier for discovery, structure, traceability, and review.

中文讲法：
最后可以这样收：AI 的价值不是替人做最终判断，而是把旧系统知识从“难以审阅的代码和零散材料”变成“有证据、有问题、有 review trail 的草稿”。最后能进入正式 BRD 的，必须是 human-reviewed、human-approved 的内容。
