# Atlas Phoenix Lens Roadshow And Review Materials

This page is the current navigation hub for the Atlas Phoenix Lens roadshow,
demo, and technical review materials.

## Positioning

```text
Atlas Engineering Delivery Hub
  -> Discovery (M3)
     -> Atlas Phoenix Lens
        -> Program Flow Map
        -> Evidence Core
        -> Dify Knowledge Activation
        -> SME Governance
```

Atlas Engineering Delivery Hub is the unified project. Atlas Phoenix Lens is
the Discovery capability being demonstrated. Legacy Spec Factory is the
technical implementation name of the Evidence Core in this repository.

## Roadshow Fast Path

For a short review:

1. Open the Chinese or English repository landing page.
2. Use the matching roadshow pitch and speaker notes.
3. Show the Delivery Hub-to-Discovery positioning visual.
4. Walk through the Dify demo using one bounded SME Program Flow.
5. Drill from a Dify response to an Evidence ID and source coordinate.
6. Close with the company-value and cross-platform method story.

## Current Entrypoints

| Material | Purpose |
| --- | --- |
| [Chinese README](../README.zh-CN.md) | Primary Chinese capability and implementation overview |
| [English README](../README.md) | Primary English capability and implementation overview |
| [中文 Confluence 项目介绍](atlas-phoenix-lens-confluence-project-detail.zh-CN.md) | One-page Chinese project detail designed for direct copy into Confluence |
| [English Confluence project detail](atlas-phoenix-lens-confluence-project-detail.md) | One-page English project detail designed for direct copy into Confluence |
| [中文项目详细介绍](atlas-phoenix-lens-project-detail.zh-CN.md) | Current long-form project detail for management review and roadshow preparation |
| [English Project Detail](atlas-phoenix-lens-project-detail.md) | English long-form project detail for management review and roadshow preparation |
| [中文路演稿](atlas-phoenix-lens-pitch.zh-CN.md) | 30-second pitch, 3-minute talk track, five-slide story, Dify demo narration, and Q&A |
| [English pitch](atlas-phoenix-lens-pitch.md) | English roadshow script, demo narration, Q&A, and claim guardrails |
| [Contribution guide](../CONTRIBUTING.md) | How to contribute docs, skills, samples, contracts, and validation changes |

## Demo Evidence

| Material | Purpose |
| --- | --- |
| [Program Flow Map export contract](program-flow-map-export-contract.md) | Defines the bounded upstream navigation package |
| [Mini output sample](samples/atlas-phoenix-lens-mini-output/) | Synthetic sample from Program Flow export to modernization evidence |
| [Program Flow export sample](samples/atlas-phoenix-lens-mini-output/program-flow-export.sample.csv) | Minimal upstream handoff CSV |
| [Program analysis sample](samples/atlas-phoenix-lens-mini-output/program-analysis.sample.md) | Single-program evidence with reviewable findings |
| [Flow analysis sample](samples/atlas-phoenix-lens-mini-output/flow-analysis.sample.md) | Multi-program synthesis sample |
| [Modernization evidence sample](samples/atlas-phoenix-lens-mini-output/modernization-evidence.sample.yaml) | Machine-readable evidence package |

## Visual Assets

| Asset | Purpose |
| --- | --- |
| [Delivery Hub Discovery visual](assets/atlas-engineering-delivery-hub-discovery-desktop.png) | Primary roadshow visual showing Atlas Phoenix Lens under Discovery |
| [Delivery Hub positioning SVG](assets/atlas-phoenix-lens-delivery-hub-position.svg) | Compact lifecycle positioning diagram |
| [Delivery Hub positioning source](assets/atlas-phoenix-lens-delivery-hub-position.mmd) | Editable Mermaid source |
| [Phoenix Lens design SVG](assets/atlas-phoenix-lens-design.svg) | Three-layer implementation and governance diagram |
| [Phoenix Lens design source](assets/atlas-phoenix-lens-design.mmd) | Editable Mermaid source |
| [Phoenix Lens technical promotional visual](assets/atlas-phoenix-lens-promo.png) | Secondary technical visual for the program-flow and evidence story |

## Technical Adoption Materials

| Material | Purpose |
| --- | --- |
| [RPG code scan E2E guideline](rpg-code-scan-e2e-guideline.md) | Current RPG source-code scan path |
| [New team flow scan quickstart](new-team-flow-scan-quickstart.md) | Adoption path for a new team |
| [Flow analysis prompt E2E guideline](flow-analysis-prompt-e2e-guideline.md) | Agent-based flow-analysis test path |
| [Flow analysis Copilot Chat guideline](flow-analysis-copilot-chat-e2e-guideline.md) | Segmented one-program-per-chat test path |
| [Skill card index](skill-card-index.md) | Current skill catalog |
| [Skill families](skill-families.md) | Skill relationships and workflow map |

## Current Claim Baseline

Use these statements consistently:

- **Atlas Engineering Delivery Hub:** the unified project and lifecycle system.
- **Atlas Phoenix Lens:** the Discovery capability being demonstrated.
- **Program Flow Map:** the cross-program scope and navigation layer.
- **Legacy Spec Factory:** the Evidence Core implementation package in this
  repository.
- **Dify:** the current internal bounded-retrieval and orchestration
  implementation layer.
- **Current technology focus:** IBM i / AS400 with RPG, CL, and DDS.
- **COBOL:** future vision, not a current delivered capability.
- **Cross-platform value:** the method is reusable, while each new platform
  requires its own adapter, skills, benchmark, and SME validation.
- **BRD output:** a draft until supported by qualified evidence or a named SME
  decision.

## Historical Materials

The following files preserve earlier submission wording. They are reference
history, not the current roadshow source of truth:

- [English open-collaboration submission](open-collaboration-submission.md)
- [中文内部开源共创申报稿](open-collaboration-submission.zh-CN.md)
- [Full historical README](full-reference-readme.md)

When current roadshow wording conflicts with these historical materials, use
the current README and roadshow pitch.

## Open Validation Items

- Verify end-to-end evidence and state mapping across Program Flow Map,
  Evidence Core, and Dify.
- Confirm that Dify preserves required metadata and can return a claim to an
  Evidence ID, source coordinate, version, and snapshot.
- Complete SME decision write-back and BRD approval-state controls.
- Run challenge cases for a real 10K+ line RPG program and a 5-10-program
  chain.
- Replace or supplement the synthetic sample with an approved redacted
  internal example.
- Confirm final redaction of screenshots, repository names, source names, and
  business fields before the roadshow.
