# 创建一个 Skill 的复盘：不是写提示词，而是沉淀一套可复用的工作系统

最近我们围绕 Legacy Spec Factory 这个 repo，复盘了一次“怎么创建一个 skill”。

一开始我以为这个问题很简单：不就是写一个 `SKILL.md`，告诉 AI 什么时候用、怎么做、输出什么吗？

但真正在这个 repo 里做过几轮之后，会发现事情没有这么轻。一个好 skill 不是一段提示词，也不是一篇说明文。它更像是一份给“下一位 AI 工作者”的上岗手册。

这位同事很聪明，但也有弱点：容易被上下文带偏，容易在证据不足时补全，容易把一次临场判断包装成稳定规则。所以 skill 的价值，不是让 AI “知道更多”，而是让它在重复任务里少走偏路。

一句话总结：

> 创建 skill，就是把一次成功经验，压缩成下一次可以稳定复用、可审查、可迁移的执行系统。

## 1. Skill 不是文档，是工作流

在 Legacy Spec Factory 里，一个 skill 的目标很明确：帮助 AI 完成某一类稳定任务。

比如：

- `legacy-ibmi-program-analyzer`：分析单个 IBM i 程序。
- `legacy-ibmi-flow-analyzer`：把多个程序的分析结果合并成 program-set review。
- `legacy-spec-writer`：把证据和 SME 确认后的规则整理成规格。
- `legacy-brd-writer`：面向业务侧写 BRD。

这些 skill 不是泛泛而谈“如何分析遗留系统”。它们各自站在一段链路上，接上游的输入，产出下游能消费的结果。

这点非常关键。

如果一个 skill 只写原则，比如“要重视证据”“要避免幻觉”“要保持输出清晰”，那它最多是一篇好看的指南。但真正执行时，AI 还是要临场发挥。

一个可用的 skill 必须回答这些问题：

- 什么时候触发？
- 输入是什么？
- 输出是什么？
- 哪些情况可以继续？
- 哪些情况必须停止？
- 哪些结论必须标记为 TBD？
- 哪些地方需要 SME 审核？
- 哪些文件、模板、脚本可以复用？

换句话说，skill 要把“怎么做”写到足够具体。

## 2. 先从真实任务倒推，不要从抽象能力开始

创建 skill 最容易犯的错，是从能力名称开始。

比如：“我们要做一个 flow analyzer。”

这句话太大了。

更好的起点是具体任务：

> SME 给了一个程序列表，希望我们把这些程序的 Calculation Logic、Validation Logic、Exception Handling、Message Inventory 合并成一个紧凑的 review 文档，同时不能丢掉任何 SME 点名的程序。

这就清楚多了。

从这个真实任务出发，我们能推导出 skill 的边界：

- 它不是重新分析每个程序。
- 它应该优先复用已有 program analysis artifact。
- 它不能因为某个 artifact 缺失就静默跳过程序。
- 它要产出 `program-set-sme-core-review.md`。
- 它要保留 completeness ledger。
- 它不能默认生成 full transaction flow，除非用户明确要求。

这就是 `legacy-ibmi-flow-analyzer` 这类 skill 的核心经验：不是让 AI “多分析一点”，而是让 AI 在正确的层级上做正确的事。

## 3. 一个好 Skill 的第一性原理：控制自由度

AI 很强，但不是所有场景都应该给它高自由度。

我现在会把 skill 设计里的自由度分成三类。

高自由度适合写作、整理、解释、SME 对话。比如如何表达一个业务限制，可以允许一定风格变化。

中自由度适合结构化分析。比如 program review 的章节顺序可以固定，但具体内容需要根据证据填充。

低自由度适合容易出错、需要稳定结果的动作。比如校验 artifact 完整性、生成 ledger、合并 YAML、检查输出结构。这些最好交给脚本。

所以创建 skill 时要问：

> 这一步如果让 AI 每次自由发挥，会不会出错？

如果答案是会，就不要只写自然语言说明。要么放模板，要么放脚本，要么写成明确的 stop condition。

## 4. `SKILL.md` 不应该写成百科全书

这个 repo 的经验很明显：`SKILL.md` 越大，不一定越好。

Skill 有一个很重要的设计原则，叫渐进披露。

也就是：

- 入口信息要短。
- 主流程要清晰。
- 细节按需加载。
- 大块参考资料放到 `references/`。
- 固定输出形状放到 `templates/`。
- 稳定重复动作放到 `scripts/`。

理想结构大概是：

```text
skills/<skill-name>/
  SKILL.md
  references/
  templates/
  scripts/
  assets/
  agents/openai.yaml
```

其中 `SKILL.md` 负责告诉 AI：

- 我是谁。
- 我什么时候用。
- 我接收什么。
- 我输出什么。
- 我按什么步骤做。
- 我遇到什么情况要停。
- 我该去读哪些 reference。

而不是把所有细节都塞进主文件。

这背后的逻辑很简单：上下文窗口是公共资源。主文件越啰嗦，真正执行任务时留给证据、代码、输出的空间就越少。

## 5. Frontmatter 是触发器，不是装饰

每个 skill 的开头都有 frontmatter：

```yaml
---
name: legacy-ibmi-flow-analyzer
description: ...
---
```

其中最重要的是 `description`。

因为 AI 在决定是否使用某个 skill 时，最先看的就是它。正文里的“什么时候使用本 skill”其实已经晚了，因为正文只有 skill 被触发后才会加载。

所以 description 不能写得太虚。

坏的 description：

> Analyze IBM i flows.

好的 description 应该包含：

- 做什么
- 什么场景使用
- 默认行为
- 关键例外
- 在整个链路中的位置

比如 flow analyzer 的 description 会明确说：用于把多个 IBM i program-analysis artifacts 合并成 SME program-set core review；默认是 program-evidence first；支持 artifact reuse、force refresh、lookup status；full transaction-flow analysis 只在单独明确请求时使用。

这不是啰嗦，这是在降低误触发和误执行的风险。

## 6. 在 IBM i 现代化里，证据治理是 skill 的底线

Legacy Spec Factory 不是普通代码生成项目。它处理的是 IBM i / AS400 现代化。

这里最大的风险不是语法写错，而是业务理解错。

尤其是：

- 把源代码里的技术分支误读成业务规则。
- 把推断写成事实。
- 把缺失证据隐藏掉。
- 把 SME 尚未确认的内容下放给后续 Java/cloud 设计。
- 根据程序名或调用关系过度连接业务流程。

所以这个 repo 的 skill 必须坚持几个分离：

- observed behavior：代码或 artifact 明确观察到的行为。
- inferred rule：根据证据推断出来的规则。
- modernization decision：面向新系统做出的设计决策。
- SME approval：业务专家确认后的结论。

这也是为什么 skill review gate 里会特别检查 evidence、anti-hallucination、SME governance。

一个 IBM i skill 如果鼓励 AI “根据上下文补全业务规则”，那它即使写得再漂亮，也不应该过审。

## 7. 输出契约比漂亮文本更重要

很多人写 skill 时会关注“让 AI 输出得更好看”。

但在这个 repo 里，更重要的是输出能不能被下一环节消费。

比如一个 program-set review 不能只是自然语言总结。它必须有稳定结构：

- Core Completeness Ledger
- Calculation Logic
- Validation Logic
- Exception Handling
- Message Inventory
- Missing artifact / next action
- Evidence status
- TBD / SME follow-up

为什么？

因为下游可能是：

- `legacy-ibmi-module-analyzer`
- `legacy-brd-writer`
- `legacy-spec-writer`
- SME review
- Java/cloud SDLC

如果每次输出结构都不同，后续就无法自动化，也无法可靠审查。

所以创建 skill 时，一定要定义 output contract。

输出契约回答的是：

> 这个 skill 产出的东西，别人凭什么敢继续用？

## 8. 可移植性不是加分项，是基本要求

这个 repo 有一个非常明确的规则：

> canonical skill source 在 `skills/<skill-name>/`。

`.codex/skills/`、`.claude/skills/`、`.opencode/skills/`、`.agents/skills/` 都是 runtime adapter 或同步副本，不是源头。

这条规则解决的是长期维护问题。

如果今天在 Codex 里改一份，明天在 Claude Code 里改一份，后天 OpenCode 又有一份，skill 很快就会漂移。最后你以为大家在用同一套流程，其实每个 runtime 都在执行不同版本。

所以创建或修改 skill 时，要记住：

- 改 canonical source。
- runtime-specific 内容放 adapter 或 override。
- 不要把某个 IDE 的私有路径写进通用 skill。
- 同步副本前后要检查 drift。

这也是 Legacy Spec Factory 的工程化特点：skill 不是某个工具的小玩具，而是跨工具复用的知识资产。

## 9. Review Gate 让 Skill 从“能用”变成“敢用”

这个 repo 里有 `docs/skill-review-gate.md`，它很值得保留。

它不是形式主义。

它逼我们回答几个硬问题：

- 触发条件清楚吗？
- 工作流完整吗？
- IBM i domain 正确吗？
- 会不会诱导幻觉？
- 输出契约稳定吗？
- 是否支持渐进披露？
- 是否跨 runtime 可移植？
- 是否有 review 和 test 的入口？
- 是否对工程交接有价值？

分数也很明确：

- 9.5-10.0：field-pilot ready
- 9.0-9.4：repo-ready，但还不能用于 field pilot
- 8.0-8.9：需要修改
- 低于 8.0：重写或拒绝

我最喜欢里面一句话：

> 不要因为 skill “听起来不错”就批准它。要因为它可执行、可审计、可移植，才批准它。

这句话很准确。

## 10. 最小可行流程

如果现在要从 0 创建一个 skill，我会按这个顺序来：

第一步，写 3 个真实用户请求。

不要先写抽象目标。先写用户真的会怎么说。

第二步，定义 skill 名称和 description。

名称要短，动词导向，lowercase hyphen。description 要写清楚触发场景。

第三步，画出输入、处理、输出。

特别是输出文件名、章节结构、必填字段、TBD 处理。

第四步，创建 canonical skill 目录。

放在：

```text
skills/<skill-name>/
```

第五步，写 `SKILL.md`。

至少包括：

- Skill Card
- Purpose
- Inputs
- Workflow
- Output Contract
- Stop Conditions
- Validation
- Handoff

第六步，拆资源。

- 长规则进 `references/`
- 固定形状进 `templates/`
- 重复稳定逻辑进 `scripts/`
- 输出素材进 `assets/`

第七步，验证。

检查 frontmatter、结构、路径、可移植性、输出契约。

第八步，用 review gate 打分。

低于 9.0 就不要合。9.0 到 9.4 可以进 repo，但还不应该 field pilot。9.5 以上才算真正能拿去给真实 SME/工程团队使用。

## 最后复盘

这次复盘后，我对 skill 的理解变了。

以前容易把 skill 理解成“更长、更专业的 prompt”。

现在更准确的理解是：

> Skill 是把人和 AI 一起跑通的经验，固化成下一次可复用的操作系统。

它不追求无所不能。它追求边界清楚。

它不鼓励 AI 编得更完整。它要求 AI 在证据不足时停下来。

它不只是为了让当前任务完成。它是为了让下一次、下下次、不同 runtime、不同执行者，都能沿着同一条可靠路径完成。

这对 Legacy Spec Factory 尤其重要。

因为我们做的不是“把 RPG 代码翻译成 Java”。我们是在 IBM i SME、证据链、业务规则、现代化设计之间，建立一个可靠的中间层。

Skill 的作用，就是把这个中间层变得可执行、可审查、可传递。
