# Translation Prompt

Translate
`docs/atlas-phoenix-lens-project-detail.zh-CN.md` from Simplified Chinese into
publication-quality English.

## Target Style

Write for business leaders, competition judges, modernization SMEs, and
technical reviewers. Use a formal, business-focused, technically precise
voice. The result must read as if it was originally written in English.
Prefer short, direct sentences. Avoid hype, filler, literal Chinese word order,
and unsupported claims.

## Content Background

Atlas Engineering Delivery Hub is the unified competition project. Atlas
Phoenix Lens is the Discovery (M3) capability being demonstrated. The current
implementation combines Program Flow Map, the Legacy Spec Factory Evidence
Core, Dify Knowledge Activation, and SME Governance. The current technology
scope is IBM i / AS400 with RPG, CL, and DDS. COBOL and other legacy platforms
are future extensions, not delivered current capabilities.

## Required Terminology

| Source term | Required English |
|---|---|
| Atlas Engineering Delivery Hub | Atlas Engineering Delivery Hub |
| Atlas Phoenix Lens | Atlas Phoenix Lens |
| Legacy Spec Factory | Legacy Spec Factory |
| Program Flow Map | Program Flow Map |
| Evidence Core | Evidence Core |
| Dify Implementation Layer | Dify Implementation Layer |
| SME Governance | SME Governance |
| Modernization Knowledge Package | Modernization Knowledge Package |
| 事实源 | Source of Truth / Canonical Evidence Source |
| 有边界的检索 | bounded retrieval / metadata-scoped retrieval |
| 不确定性溢价 | uncertainty premium |
| 当前内部实现 | current internal implementation |
| 未来愿景 | future vision |

## Non-Negotiable Accuracy Rules

1. Preserve all facts, scope boundaries, status labels, numbers, metrics,
   tables, code blocks, images, and links.
2. Dify is the current internal implementation layer. It is not the Canonical
   Evidence Source and cannot approve business facts.
3. Current platform scope is IBM i / AS400 with RPG, CL, and DDS.
4. COBOL is a future vision that requires its own adapter, skills, benchmark,
   and SME validation.
5. Program Flow is navigation evidence and cannot automatically become a
   confirmed call chain.
6. BRD generation produces a draft until qualified evidence or a named SME
   decision supports approval.
7. Pilot measures are proposed acceptance targets, not realized benefits.
8. Phoenix Lens does not claim to deliver downstream Build, Testing, or
   Deployment capabilities.

## Formatting

- Preserve Markdown heading levels, tables, lists, blockquotes, code blocks,
  images, and links.
- Add a language switch immediately below the H1:
  `[中文](../atlas-phoenix-lens-project-detail.zh-CN.md) | English`
- Adjust links only where required by the translation output location.
- Do not add translator notes to the final document.
