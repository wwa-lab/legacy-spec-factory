# Translation Analysis

## Content Summary

The source is the current long-form project detail for Atlas Phoenix Lens. It
positions Atlas Engineering Delivery Hub as the unified competition project
and Atlas Phoenix Lens as its Discovery (M3) capability. It explains the
legacy-modernization problem, the current Program Flow Map + Evidence Core +
Dify + SME Governance implementation, capability boundaries, reusable method,
company value, roadshow flow, and pilot acceptance targets.

The source is written for internal management review, competition judges,
modernization leaders, SMEs, and technical reviewers. Its stance is
evidence-led and deliberately avoids presenting a design, pilot target, or
future platform vision as an already delivered production capability.

## Terminology

| Source term | English term | Usage rule |
|---|---|---|
| Atlas Engineering Delivery Hub | Atlas Engineering Delivery Hub | Official parent project name |
| Atlas Phoenix Lens | Atlas Phoenix Lens | Official Discovery capability name |
| Legacy Spec Factory | Legacy Spec Factory | Use only as the technical Evidence Core implementation name |
| 逆向发现 | reverse discovery | Use within the Discovery lifecycle context |
| Program Flow Map | Program Flow Map | Keep title case |
| Evidence Core | Evidence Core | Keep title case |
| Dify Implementation Layer | Dify Implementation Layer | State explicitly that it is the current internal implementation |
| SME Governance | SME Governance | Keep title case |
| 事实源 | Source of Truth | Prefer “Canonical Evidence Source” when discussing Dify boundaries |
| 有边界的检索 | bounded retrieval | Use “metadata-scoped retrieval” where metadata control is the emphasis |
| 证据坐标 | source coordinate / evidence coordinate | Use “source coordinate” for code and “evidence coordinate” generically |
| 现代化知识包 | Modernization Knowledge Package | Keep title case when referring to the formal output |
| 当前实现 | current implementation | Do not weaken this to “planned” |
| 持续完善 | being strengthened | Avoid implying completion |
| 未来愿景 | future vision | Especially for COBOL |
| 已批准业务事实 | Approved Business Fact | Formal governed status |
| 当前能力 | current capability | RPG, CL, DDS only |
| 未来扩展 | future extension | COBOL and other legacy platforms |

## Tone And Style

- Formal, concise, and business-focused.
- Technically precise enough for architects and engineers.
- Direct rather than promotional; avoid hype and generic corporate filler.
- Preserve short paragraphs, tables, code blocks, pull quotes, status labels,
  and explicit boundary language.
- Use natural international English rather than a literal Chinese sentence
  structure.

## Translation Challenges

- “Modernization 的起点是理解，而不是翻译” should remain a strong, concise
  positioning line: “Modernization begins with understanding, not
  translation.”
- Keep the distinction between the unified project, displayed capability,
  technical repository, and downstream lifecycle stages unambiguous.
- Preserve “current implementation” for Dify while retaining the caveat that
  metadata governance, write-back, and scaled evaluation are still being
  strengthened.
- Never describe COBOL as currently delivered. It is a future vision requiring
  a platform-specific adapter, skills, benchmark, and SME validation.
- Translate “不确定性溢价” as “uncertainty premium,” which is concise and
  suitable for management audiences.
- Preserve Pilot metrics as proposed acceptance targets, not realized outcomes.
- Keep technical status values such as `candidate`, `poc_draft`, `in_review`,
  and `approved` unchanged.
