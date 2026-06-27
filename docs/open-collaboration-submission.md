# Atlas Phoenix Lens - Open Collaboration Submission Draft

## Project Summary

**Atlas Phoenix Lens** is the M3 Discovery capability within the Atlas
Engineering Delivery Hub / Seven Mountains SDLC narrative. It scans RPG code
and turns legacy system behavior into structured modernization evidence.

It helps migration teams move from low-level IBM i / AS400 evidence, such as
ARCAD REF / XREF data, program-call relationships, RPG / CL / COBOL / DDS
source, and file/table usage, into a business-readable evidence layer that can
support BRD generation, gap analysis, target-architecture planning, and
application retirement decisions.

## One-Sentence Chinese Summary

Atlas Phoenix Lens 是 Atlas Engineering Delivery Hub / Seven Mountains
SDLC 叙事下的 M3 Discovery 能力，通过 Program Flow Map 和 agent skills
扫描 RPG / IBM i 源码，将遗留系统行为沉淀为结构化、可审查、可复用的现代化证据。

## Problem

Legacy modernization work often starts with code, but the real blocker is
understanding behavior:

- Teams know old systems are important, but not always how programs call each
  other.
- Business logic is scattered across RPG, CL, COBOL, DDS, screens, reports,
  batch jobs, DB2 for i files, and operational conventions.
- Generic code summaries are not enough for migration decisions because they
  often miss source coordinates, evidence strength, open questions, and SME
  review points.
- Different teams repeat discovery work because there is no shared,
  AI-friendly evidence contract.

## Solution

Atlas Phoenix Lens provides a two-stage discovery workflow:

1. **Program-flow discovery**
   - Use an upstream Neo4j Program Flow Map repository to import ARCAD REF /
     XREF relationship data.
   - Preserve authoritative `CALLS` relationships.
   - Export selected program flows, call edges, field traces, and source-member
     hints.

2. **Source-code scanning with skills**
   - Use Program Flow outputs as the navigation map for source-code scanning.
   - Run Legacy Spec Factory skills against RPG / CL / COBOL / DDS programs.
   - Extract observed behavior, calculation logic, validation logic, exception
     handling, data usage, operational evidence, and SME questions.
   - Prepare structured modernization evidence for downstream BRD, spec,
     handoff, or target-architecture work.

## Current Scope

| Area | Status |
| --- | --- |
| Neo4j Program Flow Map app | Company-internal upstream repo, link pending |
| Flow export contract | Defined as the upstream/downstream handoff boundary |
| Legacy Spec Factory skills | Included in this repository |
| Source-code evidence extraction | Included through skills, templates, scripts, and validators |
| BRD/spec/handoff generation | Supported as downstream path after evidence review |

This repository is the evidence and skill layer. It does not currently host the
Neo4j Program Flow Map app.

Related documents:

- Materials index:
  [atlas-phoenix-lens-index.md](atlas-phoenix-lens-index.md)
- Contribution guide:
  [../CONTRIBUTING.md](../CONTRIBUTING.md)
- Chinese one-page submission draft:
  [open-collaboration-submission.zh-CN.md](open-collaboration-submission.zh-CN.md)
- Pitch and speaker notes:
  [atlas-phoenix-lens-pitch.md](atlas-phoenix-lens-pitch.md)
- Program Flow Map export contract:
  [program-flow-map-export-contract.md](program-flow-map-export-contract.md)

## Naming And Positioning

| Name | Meaning |
| --- | --- |
| Atlas Phoenix Lens | M3 Discovery capability narrative under Atlas Engineering Delivery Hub |
| Legacy Spec Factory | Repository skill/tooling package behind the evidence workflow |
| Program Flow Map | Upstream Neo4j application for ARCAD REF / XREF visualization |
| Modernization evidence | Structured evidence output for SME review and migration planning |

## Why Not Direct Code Conversion

The project intentionally does not begin by translating RPG directly to Java or
cloud services. Direct conversion can preserve syntax-level behavior while
missing business meaning, hidden dependencies, obsolete workarounds, and
retirement opportunities.

Atlas Phoenix Lens creates an evidence layer first:

- observed behavior from source, flow, runtime, screen, report, or data
  evidence
- inferred business rule seeds that require SME review
- open `TBD-*` questions for missing or conflicting evidence
- reviewed modernization inputs for BRD, gap analysis, target architecture, or
  application retirement decisions

This makes downstream delivery safer because teams can decide what to preserve,
redesign, retire, or defer before implementation begins.

## Reusable Assets

- Program Flow Map handoff contract
- Agent skills under `skills/`
- Source-code scan prompts and batch-control workflow
- Evidence taxonomy and ID conventions
- Validators and helper scripts
- Runtime portability model for Codex, Claude Code, and OpenCode
- English and Chinese README entries
- Design diagram and promotional visual assets
- Synthetic mini output sample under
  `docs/samples/atlas-phoenix-lens-mini-output/`

## AI-Friendly Design

The project is designed to reduce AI onboarding cost and improve repeatability:

- Markdown, YAML, CSV, and SVG assets are easy for humans and agents to parse.
- Stable IDs such as `BEH-*`, `BR-*`, and `TBD-*` keep evidence traceable.
- Skills separate observed behavior, inferred business rules, SME decisions,
  and modernization decisions.
- Validators make artifact readiness explicit instead of relying on prose.
- The workflow treats Program Flow output as navigation evidence, not final
  truth, so source scanning and SME review remain part of the governance model.

## Business And Engineering Value

Atlas Phoenix Lens helps teams:

- See how legacy programs call each other before reading every source member.
- Reduce repeated discovery effort across teams.
- Turn RPG / IBM i behavior into reviewable modernization evidence.
- Identify open questions earlier in migration planning.
- Support future target architecture, legacy / .NET application retirement,
  and AI-assisted SDLC handoff.
- Preserve SME control over business meaning while using AI for evidence
  extraction and organization.

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

## Roadmap

| Phase | Focus |
| --- | --- |
| Phase 1 | Stabilize README, bilingual docs, design diagram, and submission narrative |
| Phase 2 | Finalize Program Flow Map export contract and add upstream repo link |
| Phase 3 | Expand the current mini sample into a richer redacted demo package |
| Phase 4 | Strengthen E2E demo flow from Program Flow export to modernization evidence |
| Phase 5 | Package stakeholder-facing HTML / slide material for internal adoption |

## Suggested Competition Category Fit

- Future target architecture and legacy / .NET application retirement
- AI-assisted code understanding and modernization discovery
- Cross-team reuse of technical assets, templates, and automation methods
- Data and evidence standardization for migration planning

## Review Notes

Open items before final submission:

- Add the upstream Neo4j Program Flow Map repo name and link.
- Replace or supplement the synthetic mini sample with a redacted internal
  sample when approved.
- Confirm whether any internal names or screenshots need redaction.
