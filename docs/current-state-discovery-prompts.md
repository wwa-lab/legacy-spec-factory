# Current-State Functional Discovery Prompts

This document provides reusable prompts for extracting evidence-backed
current-state functional discovery from RAG documents, input folders, diagrams,
and SME notes.

The key instruction is to extract behavior claims first, then generate the
functional discovery report. This helps avoid outputs that have the right
section headings but only contain high-level or low-value summaries.

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
