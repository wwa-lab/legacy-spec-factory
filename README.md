# Atlas Phoenix Lens

English | [中文](README.zh-CN.md)

![Atlas Engineering Delivery Hub highlighting Atlas Phoenix Lens in Discovery](docs/assets/atlas-engineering-delivery-hub-discovery-desktop.png)

> **Atlas Phoenix Lens is the Discovery capability of Atlas Engineering
> Delivery Hub: understand the legacy estate before deciding how to modernize
> it.**

**Atlas Engineering Delivery Hub** is the unified engineering delivery system
across Planning, Estimation, Discovery, Build, Testing, Deployment, and
Maintenance. **Atlas Phoenix Lens** is its **Discovery (M3)** capability, not a
separate project alongside the Delivery Hub.

Phoenix Lens starts from ARCAD REF / XREF, program flows, legacy documents, and
source code. It recovers what a legacy system actually does and turns that
knowledge into traceable, reviewable modernization evidence. The current
internal implementation uses **Dify** for bounded retrieval, business
questions, and orchestration. The **Legacy Spec Factory** in this repository is
the Evidence Core behind that experience, providing source scanning, evidence
governance, SME gates, and traceability.

> **Map the flow. Scan the code. Activate the knowledge.**

Phoenix Lens does **not** directly translate legacy source into Java or cloud
services. It first separates observed behavior, inferred rules, open questions,
and named SME decisions. Only reviewed knowledge moves into the downstream
Build, Testing, and Deployment stages of Atlas Engineering Delivery Hub.

For the full historical README and deeper design notes, see
[docs/full-reference-readme.md](docs/full-reference-readme.md).

## Delivery Hub Positioning

```text
Atlas Engineering Delivery Hub
  Planning -> Estimation -> Discovery -> Build -> Testing -> Deployment -> Maintenance
                            |
                            `-- Atlas Phoenix Lens
                                Program Flow Map
                                + Evidence Core
                                + Dify Knowledge Activation
                                + SME Governance
```

This repository and the roadshow focus only on Atlas Phoenix Lens. Build Agent
and Deployment Agent are other lifecycle capabilities within Atlas Engineering
Delivery Hub; they are not presented as capabilities already delivered by
Phoenix Lens.

![Atlas Phoenix Lens position in Atlas Engineering Delivery Hub](docs/assets/atlas-phoenix-lens-delivery-hub-position.svg)

Editable source:
[docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd](docs/assets/atlas-phoenix-lens-delivery-hub-position.mmd).

## Why It Matters

The largest unknown in legacy modernization is rarely whether new code can be
generated. It is whether the organization has a complete, current, traceable
model of existing behavior:

- business rules are distributed across RPG, CL, DDS, database access, batch,
  screens, reports, and runtime conventions;
- documents may be outdated or disconnected from the source snapshot being
  modernized;
- one business flow can cross programs, files, interfaces, exceptions, and
  restart paths;
- critical knowledge is concentrated in a small number of experienced SMEs;
- an AI summary can look complete while mixing observed facts, inference, and
  unsupported assumptions.

Every missed rule or dependency can become requirements rework, a testing gap,
a delayed migration, an unsafe retirement, or a production incident.

> The greatest risk is not that the team cannot generate new code. It is that
> the team generates the wrong system without fully understanding the old one.

## Current Implementation: One Capability, Three Layers

| Phoenix Lens component | Current responsibility | Implementation boundary |
| --- | --- | --- |
| **Program Flow Map** | Establish cross-program navigation and business scope from ARCAD REF / XREF | The Neo4j application lives in an upstream company-internal repository; a flow is navigation evidence, not an automatically approved business fact |
| **Evidence Core** | Scan source and extract behavior, rules, data, exceptions, and TBDs while enforcing SME gates and traceability | Implemented in this repository through Legacy Spec Factory skills, contracts, templates, and validators |
| **Dify Implementation Layer** | Provide bounded retrieval, business Q&A, orchestration, and BRD draft generation over documents and program-analysis results | The current internal implementation route; Dify is not the Canonical Evidence Source and cannot approve business facts |

The end-to-end path is:

```text
ARCAD REF / XREF + legacy documents + source
  -> Program Flow Map: select a bounded business flow
  -> Evidence Core: RPG / CL / DDS scanning and evidence governance
  -> Module Context / Evidence Map: separate fact, inference, contradiction, and TBD
  -> Dify: metadata-scoped retrieval, business Q&A, and BRD draft
  -> SME Review / Decision / Write-back
  -> reviewed Modernization Knowledge Package
  -> downstream Atlas Engineering Delivery Hub stages
```

### The Current Role of Dify

The current internal implementation places legacy documents and program
analysis results into Dify knowledge bases. An SME Program Flow constrains the
retrieval scope before business questions or BRD drafts are generated. This
supports rapid validation of retrieval strategies, prompts, response formats,
and SME readability.

Dify operates within three boundaries:

1. Dify stores searchable copies; Canonical Evidence remains in versioned,
   structured artifacts.
2. Retrieval must be constrained by metadata such as capability, module,
   program, source version, snapshot, and evidence strength.
3. Generated content remains `candidate`, `poc_draft`, or `in_review` until
   supported by qualified evidence or a named SME decision.

## Current Capability And Future Vision

| Area | Status |
| --- | --- |
| IBM i / AS400 discovery method | Current focus |
| RPG, CL, and DDS source and context analysis | Current implementation |
| Program Flow Map navigation | Current internal capability |
| Legacy Spec Factory Evidence Core | Available in this repository |
| Dify retrieval, Q&A, and orchestration | Current internal implementation route |
| Dify metadata governance, decision write-back, and scaled evaluation | Being strengthened / pilot control |
| COBOL analysis | Future vision; not delivered as a current capability |
| Other legacy platforms | Future extension through platform adapters, skills, benchmarks, and SME validation |

The reusable method is broader than one language. Scope discovery, evidence
contracts, knowledge classification, SME governance, traceability, and
metadata-scoped retrieval can be shared across platforms. Every new legacy
technology still requires its own adapter, scanning skills, benchmark, and SME
validation; method portability does not mean that platform support already
exists.

## Implementation Design Overview

![Atlas Phoenix Lens implementation design overview](docs/assets/atlas-phoenix-lens-design.svg)

Editable source:
[docs/assets/atlas-phoenix-lens-design.mmd](docs/assets/atlas-phoenix-lens-design.mmd).

## Roadshow Demo

The primary demo uses Dify as the user-facing entry point and repository
artifacts to prove the evidence governance behind it:

1. Export ARCAD REF / XREF relationship data from the IBM i estate.
2. Select a business-relevant Program Flow in the Program Flow Map.
3. Show Evidence Core outputs for RPG, CL, and DDS, including source
   coordinates and TBDs.
4. Apply metadata filters for the same flow in Dify.
5. Ask business questions about behavior, rules, data impact, and exceptions.
6. Trace Dify responses back to Evidence IDs, source coordinates, and the
   source snapshot.
7. Generate a BRD draft with `poc_draft` or `in_review` status.
8. Show how SME review and the decision log prevent AI inference from being
   promoted automatically into business fact.

## Sample Output Package

A small synthetic sample is available at
[docs/samples/atlas-phoenix-lens-mini-output/](docs/samples/atlas-phoenix-lens-mini-output/).
It shows the expected handoff shape from Program Flow Map export to
source-backed modernization evidence:

- `program-flow-export.sample.csv`
- `program-analysis.sample.md`
- `flow-analysis.sample.md`
- `modernization-evidence.sample.yaml`

## Upstream Program Flow Map Contract

The upstream Neo4j Program Flow Map repository is expected to provide a small,
stable handoff package. The exact repo link and file names are still pending,
but the contract should include:

| Artifact | Purpose |
| --- | --- |
| Flow metadata | Flow name, business area, source system, export timestamp, and source snapshot |
| Program list | Ordered or grouped programs included in the selected flow |
| Call edges | Caller, callee, relationship type, and ARCAD / XREF evidence reference |
| Source-member mapping | Program name to library, source file, member, path, or repo location when known |
| Field trace | Optional field movement, file/table access, key fields, and persistence hints |
| Review notes | Known gaps, unresolved calls, confidence notes, and SME hints |

Preferred export formats are CSV, JSON, YAML, or Markdown. The downstream
skills should treat the Program Flow Map export as navigation evidence, not as
final business truth. Source scanning and SME review remain required before
modernization decisions are approved.

Template:
[docs/program-flow-map-export-contract.md](docs/program-flow-map-export-contract.md).

## Main Capabilities

### 1. Program-Flow Discovery

- Import ARCAD REF / XREF relationship data.
- Load relationship data into Neo4j through a separate internal Program Flow
  Map repository (`TBD: add repo name/link`).
- Preserve authoritative `CALLS` relationships.
- Generate Program Flow Map exports for human review and downstream discovery.
- Enrich flows with screen, report, API, T&C, batch, advice, and DB-field
  evidence when available.
- Provide a shared navigation map for migration teams, SMEs, and AI agents.

### 2. Business-Logic Discovery From Source Code

- Use Program Flow outputs as the guide for source-code scanning.
- Analyze RPG, CL, and DDS one program or one flow at a time.
- Extract observed behavior, calculations, validations, file I/O, dependencies,
  exception paths, and operational evidence.
- Produce structured evidence with stable IDs, source coordinates, coverage
  gaps, and SME review questions.
- Feed downstream module analysis, BRD generation, spec writing, and migration
  planning only after review gates pass.

### 3. Dify Knowledge Activation

- Store documents and program-analysis results as metadata-rich searchable
  copies.
- Use the SME Program Flow to constrain capability, module, and program scope.
- Support business Q&A, evidence drill-down, and BRD draft generation.
- Keep Canonical Evidence, approval state, and downstream contracts under
  independent control.

## Company Impact And Commercial Value

Atlas Phoenix Lens is not valuable merely because it can produce a document
faster. Its value is reducing uncertainty and evidence risk across a
modernization portfolio:

- **Release delivery capacity:** reduce repeated code reading, context
  reconstruction, and broad SME explanation.
- **Avoid downstream rework:** reduce requirements, design, testing, and
  migration rework caused by misunderstood legacy behavior.
- **Preserve institutional knowledge:** retain critical behavior, evidence, and
  named SME decisions as maintainable organizational assets.
- **Reuse at portfolio scale:** share flow contracts, evidence models, review
  gates, and Dify orchestration rather than rebuilding discovery methods.
- **Support reliable retirement:** distinguish behavior that must be preserved,
  redesigned, consolidated, or safely retired.

```text
Annual measurable net value
  = released Discovery and SME capacity
  + avoided evidence-related rework
  + avoided duplicate solution build
  + validated early-retirement value
  - annual Phoenix Lens operating cost
```

Benefits must be validated through an owned baseline, comparable pilot data,
and Finance-approved unit costs. Targets and scenario calculations must not be
presented as realized savings.

## Roadshow And Collaboration Materials

- Confluence-ready English project detail:
  [docs/atlas-phoenix-lens-confluence-project-detail.md](docs/atlas-phoenix-lens-confluence-project-detail.md)
- Confluence-ready Chinese project detail:
  [docs/atlas-phoenix-lens-confluence-project-detail.zh-CN.md](docs/atlas-phoenix-lens-confluence-project-detail.zh-CN.md)
- English project detail:
  [docs/atlas-phoenix-lens-project-detail.md](docs/atlas-phoenix-lens-project-detail.md)
- Chinese project detail:
  [docs/atlas-phoenix-lens-project-detail.zh-CN.md](docs/atlas-phoenix-lens-project-detail.zh-CN.md)
- Chinese roadshow script:
  [docs/atlas-phoenix-lens-pitch.zh-CN.md](docs/atlas-phoenix-lens-pitch.zh-CN.md)
- English pitch and speaker notes:
  [docs/atlas-phoenix-lens-pitch.md](docs/atlas-phoenix-lens-pitch.md)
- Materials index:
  [docs/atlas-phoenix-lens-index.md](docs/atlas-phoenix-lens-index.md)
- Historical submission draft:
  [docs/open-collaboration-submission.md](docs/open-collaboration-submission.md)
- Contribution guide:
  [CONTRIBUTING.md](CONTRIBUTING.md)

## Roadmap

| Phase | Focus |
| --- | --- |
| P0 | Complete the evidence, metadata, state, and approval mapping across Program Flow Map, Evidence Core, and Dify |
| P1 | Strengthen the SME Decision Log, BRD gate, write-back, and retrieval/generation evaluation set |
| P1 | Validate completeness and traceability with a real 10K+ line RPG program and a 5-10 program chain |
| P2 | Expand the redacted demo, roadshow materials, and portfolio-adoption measures |
| Future | Add COBOL and other legacy adapters, skills, and benchmarks only after the current-platform baseline passes |

## Repository Layout

> Note: the Neo4j Program Flow Map application is currently maintained in a
> separate company-internal repository and is listed here as an upstream
> dependency placeholder. Add the repo link and setup notes when they are ready.

```text
skills/       canonical agent skills, templates, references, and scripts
docs/         design notes, quickstarts, scorecards, diagrams, and examples
scripts/      validation and helper utilities
tests/        regression tests for contracts and skill helper scripts
templates/    shared output templates
schemas/      structured artifact schemas
outputs/      generated or local run outputs
```

Runtime-specific folders such as `.claude/`, `.opencode/`, `.agents/`, and
`.codex/` are adapters or synced copies. The canonical skill source is
`skills/<skill-name>/`.

## Key Skills

| Skill | Purpose |
| --- | --- |
| `legacy-ibmi-program-list-batch` | Prepare resumable program-list scan batches and one-program prompt queues. |
| `legacy-current-state-discovery` | Extract document/RAG-backed current-state functional discovery reports and catalogs. |
| `legacy-ibmi-program-analyzer` | Analyze one IBM i program and extract source-backed behavior evidence. |
| `legacy-ibmi-flow-analyzer` | Validate finalized reader-first program analyses, prepare lossless facts/coverage controls, and let the executing LLM synthesize one uniquely named SME/Dify Core Review; it does not reconstruct a transaction flow. |
| `legacy-ibmi-module-analyzer` | Assemble reviewed program / flow evidence into module-level context. |
| `legacy-brd-writer` | Produce evidence-backed BRD packages from approved module context. |
| `legacy-step-validator` | Validate whether an artifact can move forward, move with warnings, or must block. |
| `legacy-html-exporter` | Export stable Markdown artifacts to stakeholder-friendly HTML. |

See [docs/skill-card-index.md](docs/skill-card-index.md) and
[docs/skill-families.md](docs/skill-families.md) for the broader skill family.

## Quick Start

Start with:

- [QUICKSTART.md](QUICKSTART.md) for a short walkthrough.
- [docs/new-team-flow-scan-quickstart.md](docs/new-team-flow-scan-quickstart.md)
  for a flow-scan adoption path.
- [docs/flow-analysis-prompt-e2e-guideline.md](docs/flow-analysis-prompt-e2e-guideline.md)
  for Codex / Claude Code flow prompt testing.
- [docs/flow-analysis-copilot-chat-e2e-guideline.md](docs/flow-analysis-copilot-chat-e2e-guideline.md)
  for GitHub Copilot Chat segmented flow testing.
- [docs/rpg-code-scan-e2e-guideline.md](docs/rpg-code-scan-e2e-guideline.md)
  for the current RPG source-code scan E2E path.
- [docs/EXAMPLE-tutorial/](docs/EXAMPLE-tutorial/) for a populated minimal
  example.
- [docs/review-workspace.md](docs/review-workspace.md) for the interactive
  review workspace shape used by the example tutorial.

Useful validation commands:

```bash
python3 -m pytest
scripts/sync-skills.sh --target all --check
```

On Windows, use `py -3` before falling back to `python` for Python scripts.

## Evidence And Governance

The project keeps four things separate:

- **Observed behavior**: what the legacy system does, backed by source,
  runtime, screen, report, or data evidence.
- **Inferred business rules**: likely business meaning that still needs SME
  review.
- **SME decisions**: confirmed, rejected, or unresolved business meaning.
- **Modernization decisions**: follow, redesign, retire, or defer choices made
  after review.

Every approved rule should carry source evidence or SME approval. Ambiguous or
missing evidence becomes a `TBD-*` item instead of being hidden in polished
prose.

## Status

Atlas Phoenix Lens is backed by a production-oriented skill family under active
development for IBM i / AS400 modernization discovery. Reviewed skill
scorecards live under
[docs/reviews/](docs/reviews/), and the runtime matrix is tracked in
[docs/runtime-matrix.md](docs/runtime-matrix.md).

## License

See [LICENSE](LICENSE), [NOTICE](NOTICE), and [AUTHORS.md](AUTHORS.md).
