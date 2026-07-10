# Current-State Functional Discovery Prompts

This document provides reusable prompts for extracting evidence-backed
current-state functional discovery from RAG documents, input folders, diagrams,
and SME notes.

The key instruction is to extract behavior claims first, then generate the
functional discovery report. This helps avoid outputs that have the right
section headings but only contain high-level or low-value summaries.

## GitHub Copilot Slash Prompt - Chinese

Use this version when the team invokes the skill in GitHub Copilot with the
slash command.

```text
/legacy-current-state-discovery

请基于我提供的 input folder / RAG 文档 / diagrams / SME notes，生成一份 evidence-backed current-state functional discovery package。

Discovery Focus:
<填写 function / process / module / business event，例如 Report Lost / Issuer Authorization>

Scope:
<填写地区、系统、产品、业务范围，例如 AMH Hong Kong credit card current-state>

请不要直接写报告。请先抽取 behavior-claim-ledger，然后再基于 behavior claims 生成 functional-discovery-report 和 supporting catalogs。

ID rule:
- behavior claim 使用 `BCL-*`
- function candidate 使用 `CAND-*`
- open question / gap 使用 `TBD-*`
- source evidence 使用 `SRC-*` 或输入材料已有的 source ID
- 不要只用一个通用 `CLM-*` 同时表示 claim、gap、source 和 function。

每一条非 Gap 的 behavior claim 必须包含：
1. business meaning：这个行为对业务意味着什么
2. trigger / condition：什么事件、用户动作、系统条件会触发
3. system behavior：当前系统实际做了什么
4. evidence source：文档名、section/page/chunk/file/path
5. confidence：Confirmed / Strongly Indicated / Inferred / Gap / Not Reviewed
6. review route：SME review / evidence retrieval / code analysis

关键规则：
- 不要把“folder contains program X”、“diagram has node Y”、“document mentions API Z”直接当作 functional。
- 如果材料只证明有文件、图节点、程序名、接口名，但没有说明业务行为，请把它记录为 Gap 或 Code Analysis Required。
- 不要使用 “likely exists”, “suggests”, “appears related” 作为 functional 结论，除非同时说明缺少什么证据、下一步由谁确认。
- 不要发明 exact formula、status code、transaction type、GL/IE account、threshold、field-level validation、program behavior。
- 如果 exact detail 不在材料里，请写 “Not found in reviewed evidence” 或创建 Gap。
- Documents and diagrams are context/navigation evidence. Code/runtime/SME approval is required for detailed behavior claims.

Expected output:
1. document-master-index
2. behavior-claim-ledger
3. functional-discovery-report
4. function-catalog
5. validation-catalog
6. calculation-catalog
7. interface-register
8. accounting-gl-ie-index
9. traceability-matrix
10. open-questions-and-gaps

Report formatting rule:
- functional-discovery-report 的主要章节请优先使用表格，不要只用 bullet summary。
- 每条 material statement 必须显示相关 `BCL-*` / `CAND-*`、confidence、source locator、gap 或 next action。
- Gap Analysis 必须使用表格，至少包含 Gap ID、Area、Missing Evidence、Impact、Owner / Route、Next Action、Status。
- 如果一个 section 只能写高层总结，请把它降级为 Gap 或 Code Analysis Required，不要写成 confirmed functional。

Validation command rule:
- 如果需要运行 validator，并且当前环境是 Windows / Windows 11，请使用已安装
  current-state skill 的本地 launcher；它内部会依次尝试 `py -3`、`python`、
  原生 PowerShell validator。
- 不要拼接 `py ... || python ...`，Windows PowerShell 5.1 不支持。
- Windows 示例：
  `py -3 .agents\skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.py <package-path>`
- Windows strict quality gate 示例：
  `py -3 .agents\skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.py --quality-gate --require-ready <package-path>`
- 只有在 macOS / Linux 环境下才使用 `python3`。

Quality gate:
最终输出前，请检查每个 populated section：
- SME 是否能判断这条内容是正确、错误、不完整，还是需要 code verification？
- 每个非 Gap claim 是否有明确 evidence？
- 是否存在只有 high-level summary、没有业务行为的内容？

如果不能通过，请不要美化成报告结论；请降级为 Gap、SME question 或 Code Analysis Required。
```

## GitHub Copilot Slash Prompt - English

Use this version when the team invokes the skill in GitHub Copilot with the
slash command.

```text
/legacy-current-state-discovery

Generate an evidence-backed current-state functional discovery package from the provided input folder / RAG documents / diagrams / SME notes.

Discovery Focus:
<function / process / module / business event, e.g. Report Lost / Issuer Authorization>

Scope:
<region, system, product, and business scope, e.g. AMH Hong Kong credit card current state>

Do not write the report directly. First extract a behavior-claim-ledger, then generate the functional-discovery-report and supporting catalogs from those behavior claims.

ID rule:
- Use `BCL-*` for behavior claims.
- Use `CAND-*` for function candidates.
- Use `TBD-*` for open questions and gaps.
- Use `SRC-*` or the provided source ID for source evidence.
- Do not use one generic `CLM-*` namespace for claims, gaps, sources, and functions.

Every non-Gap behavior claim must include:
1. business meaning: what this behavior means for the business
2. trigger / condition: event, user action, or system condition that triggers it
3. system behavior: what the current system actually does
4. evidence source: document name, section/page/chunk/file/path
5. confidence: Confirmed / Strongly Indicated / Inferred / Gap / Not Reviewed
6. review route: SME review / evidence retrieval / code analysis

Key rules:
- Do not treat “folder contains program X”, “diagram has node Y”, or “document mentions API Z” as functional behavior.
- If the material only proves the existence of a file, diagram node, program name, or interface name, but does not describe business behavior, record it as a Gap or Code Analysis Required.
- Do not use “likely exists”, “suggests”, or “appears related” as functional conclusions unless the missing evidence and next review route are also stated.
- Do not invent exact formulas, status codes, transaction types, GL/IE accounts, thresholds, field-level validations, or program behavior.
- If an exact detail is not present in the reviewed evidence, write “Not found in reviewed evidence” or create a Gap.
- Documents and diagrams are context/navigation evidence. Code, runtime evidence, or SME approval is required for detailed behavior claims.

Expected output:
1. document-master-index
2. behavior-claim-ledger
3. functional-discovery-report
4. function-catalog
5. validation-catalog
6. calculation-catalog
7. interface-register
8. accounting-gl-ie-index
9. traceability-matrix
10. open-questions-and-gaps

Report formatting rule:
- Use tables for the main sections in functional-discovery-report instead of bullet-only summaries.
- Every material statement must show the related `BCL-*` / `CAND-*`, confidence, source locator, and gap or next action.
- Gap Analysis must be a table with at least Gap ID, Area, Missing Evidence, Impact, Owner / Route, Next Action, and Status.
- If a section can only contain a high-level summary, downgrade it to Gap or Code Analysis Required instead of writing it as confirmed functional behavior.

Validation command rule:
- If a validator must be run and the environment is Windows / Windows 11, use
  the installed current-state skill's local launcher; it tries `py -3`, then
  `python`, then fails clearly when Python is unavailable.
- Do not synthesize `py ... || python ...`; Windows PowerShell 5.1 does not
  support `||`.
- Windows example:
  `py -3 .agents\skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.py <package-path>`
- Windows strict quality gate example:
  `py -3 .agents\skills\legacy-current-state-discovery\scripts\validate_current_state_discovery_package.py --quality-gate --require-ready <package-path>`
- Use `python3` only on macOS / Linux.

Quality gate:
Before finalizing, check every populated section:
- Can an SME decide whether this content is correct, wrong, incomplete, or needs code verification?
- Does every non-Gap claim have clear evidence?
- Is there any high-level summary without actual business behavior?

If the output cannot pass this gate, do not polish it into a conclusion. Downgrade it to a Gap, SME question, or Code Analysis Required item.
```

## Chinese Prompt

```text
请使用 legacy-current-state-discovery skill，基于我提供的 input folder / RAG 文档 / diagrams / SME notes，生成一份 evidence-backed current-state functional discovery package。

目标不是简单总结文档，也不是只生成章节标题。请先从材料中抽取“可被 SME review 的 current-state behavior claims”，再基于这些 claims 生成 functional discovery report。

Discovery Focus:
<填写 function / process / module / business event，例如 Report Lost / Issuer Authorization>

Scope:
<填写地区、系统、产品、业务范围，例如 AMH Hong Kong credit card current-state>

Required behavior-claim extraction rule:
在写报告前，请先建立 behavior-claim-ledger。每一条非 Gap 的 claim 必须包含：
1. business meaning：这个行为对业务意味着什么
2. trigger / condition：什么事件、用户动作、系统条件会触发
3. system behavior：当前系统实际做了什么
4. evidence source：文档名、section/page/chunk/file/path
5. confidence：Confirmed / Strongly Indicated / Inferred / Gap / Not Reviewed
6. review route：SME review / evidence retrieval / code analysis

Important rules:
- 不要把“folder contains program X”、“diagram has node Y”、“document mentions API Z”直接当作 functional。
- 如果材料只证明有文件、图节点、程序名、接口名，但没有说明业务行为，请把它记录为 Gap 或 Code Analysis Required。
- 不要使用 “likely exists”, “suggests”, “appears related” 作为 functional 结论，除非同时说明缺少什么证据、下一步由谁确认。
- 不要发明 exact formula、status code、transaction type、GL/IE account、threshold、field-level validation、program behavior。
- 如果 exact detail 不在材料里，请写 “Not found in reviewed evidence” 或创建 Gap。
- Documents and diagrams are context/navigation evidence. Code/runtime/SME approval is required for detailed behavior claims.

Expected output:
1. document-master-index
2. behavior-claim-ledger
3. functional-discovery-report，包含以下章节：
   - Existing Functionality
   - Process Flow
   - Upstream / Downstream Applications
   - System Configuration / Parameter
   - Channels
   - Report
   - Customer Communication, Triggers and Associated Requirement
   - Operational Procedure
   - Current Limitation / Pain Point
   - Gap Analysis
   - Cross Reference BRD
4. function-catalog
5. validation-catalog
6. calculation-catalog
7. interface-register
8. accounting-gl-ie-index
9. traceability-matrix
10. open-questions-and-gaps

Quality gate:
在最终输出前，请检查每个 populated section：
- SME 是否能判断这条内容是正确、错误、不完整，还是需要 code verification？
- 每个非 Gap claim 是否有明确 evidence？
- 是否存在只有 high-level summary、没有业务行为的内容？

如果不能通过，请不要美化成报告结论；请降级为 Gap、SME question 或 Code Analysis Required。
```

## English Prompt

```text
Use the legacy-current-state-discovery skill to generate an evidence-backed current-state functional discovery package from the provided input folder / RAG documents / diagrams / SME notes.

The goal is not to summarize documents or merely fill report sections. First extract SME-reviewable current-state behavior claims, then generate the functional discovery report from those claims.

Discovery Focus:
<function / process / module / business event, e.g. Report Lost / Issuer Authorization>

Scope:
<region, system, product, and business scope, e.g. AMH Hong Kong credit card current state>

Required behavior-claim extraction rule:
Before writing the report, create a behavior-claim ledger. Every non-Gap claim must include:
1. business meaning: what this behavior means for the business
2. trigger / condition: event, user action, or system condition that triggers it
3. system behavior: what the current system actually does
4. evidence source: document name, section/page/chunk/file/path
5. confidence: Confirmed / Strongly Indicated / Inferred / Gap / Not Reviewed
6. review route: SME review / evidence retrieval / code analysis

Important rules:
- Do not treat “folder contains program X”, “diagram has node Y”, or “document mentions API Z” as functional behavior.
- If the material only proves the existence of a file, diagram node, program name, or interface name, but does not describe business behavior, record it as a Gap or Code Analysis Required.
- Do not use “likely exists”, “suggests”, or “appears related” as functional conclusions unless the missing evidence and next review route are also stated.
- Do not invent exact formulas, status codes, transaction types, GL/IE accounts, thresholds, field-level validations, or program behavior.
- If an exact detail is not present in the reviewed evidence, write “Not found in reviewed evidence” or create a Gap.
- Documents and diagrams are context/navigation evidence. Code, runtime evidence, or SME approval is required for detailed behavior claims.

Expected output:
1. document-master-index
2. behavior-claim-ledger
3. functional-discovery-report with these sections:
   - Existing Functionality
   - Process Flow
   - Upstream / Downstream Applications
   - System Configuration / Parameter
   - Channels
   - Report
   - Customer Communication, Triggers and Associated Requirement
   - Operational Procedure
   - Current Limitation / Pain Point
   - Gap Analysis
   - Cross Reference BRD
4. function-catalog
5. validation-catalog
6. calculation-catalog
7. interface-register
8. accounting-gl-ie-index
9. traceability-matrix
10. open-questions-and-gaps

Quality gate:
Before finalizing, check every populated section:
- Can an SME decide whether this content is correct, wrong, incomplete, or needs code verification?
- Does every non-Gap claim have clear evidence?
- Is there any high-level summary without actual business behavior?

If the output cannot pass this gate, do not polish it into a conclusion. Downgrade it to a Gap, SME question, or Code Analysis Required item.
```
