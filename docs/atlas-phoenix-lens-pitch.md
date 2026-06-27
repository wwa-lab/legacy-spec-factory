# Atlas Phoenix Lens - Pitch And Speaker Notes

## One-Slide Summary

**Atlas Phoenix Lens** is the M3 Discovery capability within the Atlas
Engineering Delivery Hub / Seven Mountains SDLC narrative. It scans RPG code
and turns legacy system behavior into structured modernization evidence.

It connects two worlds:

- **Upstream Program Flow Map**: ARCAD REF / XREF data is loaded into Neo4j so
  teams can see how IBM i programs call each other.
- **Legacy Spec Factory skills**: agent skills use those flows as a navigation
  map, scan RPG / CL / COBOL / DDS source, and produce traceable modernization
  evidence.

The goal is not direct code conversion. The goal is to recover business
behavior first, keep it evidence-backed, and prepare it for SME review, BRD/gap
analysis, target architecture, and application retirement decisions.

## 30-Second Pitch

Atlas Phoenix Lens helps modernization teams understand legacy IBM i behavior
before they decide what to rebuild, retire, or redesign. It starts from ARCAD
REF / XREF data, creates a Program Flow Map through an upstream Neo4j repo, and
then uses Legacy Spec Factory skills to scan source code along the discovered
flow. The output is structured modernization evidence: observed behaviors,
candidate business rules, open SME questions, and downstream-ready inputs for
BRD, gap analysis, and target architecture planning.

## 3-Minute Talk Track

### 1. Open With The Problem

Most legacy modernization work does not fail because the code cannot be
translated. It fails because teams do not fully understand what the old system
does, which behaviors are still business-critical, and which parts should be
retired or redesigned.

In IBM i systems, the logic is spread across RPG, CL, COBOL, DDS, DB2 for i
files, reports, screens, batch jobs, and operational conventions. A generic AI
summary of one source file is not enough for migration planning.

### 2. Introduce The Capability

Atlas Phoenix Lens is the M3 Discovery capability within the Atlas Engineering
Delivery Hub / Seven Mountains SDLC narrative. It scans RPG code and turns
legacy system behavior into structured modernization evidence.

The capability has two parts:

1. An upstream Neo4j Program Flow Map repo that turns ARCAD REF / XREF data into
   a visible program-call map.
2. This Legacy Spec Factory repo, which provides the skills, prompts,
   contracts, validators, and sample outputs for scanning source code along
   those flows.

### 3. Explain The Flow

The team starts with ARCAD REF / XREF data. That data goes into Neo4j and
becomes a Program Flow Map. A reviewer selects one flow, exports the program
list, call edges, source-member hints, and optional field trace. Then the
Legacy Spec Factory skills scan each program and assemble the flow behavior.

The output is not just prose. It is structured evidence:

- `BEH-*` observed behaviors
- `BR-*` candidate business rules
- `TBD-*` open questions
- source coordinates and evidence references
- downstream readiness notes

### 4. Make The Value Clear

This gives teams a reusable way to understand legacy behavior before
modernization decisions are made. It reduces repeated discovery work, makes AI
outputs easier to review, and keeps SMEs in control of business meaning.

It is especially relevant for future target architecture, legacy / .NET
application retirement, and AI-assisted SDLC handoff.

### 5. Close With Current Status

The current repo includes the skill layer, export contract, bilingual README,
design diagram, promotional visual, submission drafts, and a synthetic mini
sample output package. The remaining work is to add the internal Neo4j repo
link, replace the synthetic sample with an approved redacted example, and
strengthen the E2E demo path.

## Suggested 5-Slide Outline

### Slide 1 - What Is Atlas Phoenix Lens?

Message:

Atlas Phoenix Lens is the M3 Discovery capability in Atlas Engineering Delivery
Hub. It scans RPG code and turns legacy behavior into structured modernization
evidence.

Visual:

Use `docs/assets/atlas-engineering-delivery-hub-discovery-desktop.png` for the
Delivery Hub narrative, or `docs/assets/atlas-phoenix-lens-promo.png` for a
more focused capability visual.

Speaker note:

Start with the capability narrative, not the repo name. Explain that Legacy
Spec Factory is the repository package behind the capability.

### Slide 2 - Why Direct Code Conversion Is Not Enough

Message:

Modernization requires understanding behavior, not only translating syntax.

Key points:

- Program calls are hidden across legacy assets.
- Business rules are mixed with technical workarounds.
- AI summaries need evidence, confidence, and review gates.
- SME review remains the control point.

### Slide 3 - Design Overview

Message:

M3 Discovery connects Program Flow Map navigation to Legacy Spec Factory
evidence generation.

Visual:

Use `docs/assets/atlas-engineering-delivery-hub-discovery-desktop.png` first
for the desktop narrative, then
`docs/assets/atlas-phoenix-lens-delivery-hub-position.svg` and
`docs/assets/atlas-phoenix-lens-design.svg` for structure and implementation
detail.

Speaker note:

Call out the upstream Neo4j repo as a dependency placeholder and this repo as
the evidence/skill layer inside the Discovery stage.

### Slide 4 - Sample Output

Message:

The output is structured evidence, not a loose summary.

Show:

- `program-flow-export.sample.csv`
- `program-analysis.sample.md`
- `flow-analysis.sample.md`
- `modernization-evidence.sample.yaml`

Speaker note:

Point to `docs/samples/atlas-phoenix-lens-mini-output/` and explain the stable
IDs: `BEH-*`, `BR-*`, and `TBD-*`.

### Slide 5 - Reuse And Roadmap

Message:

Atlas Phoenix Lens is built for cross-team reuse.

Key points:

- AI-friendly Markdown/YAML/CSV contracts
- portable skills for Codex, Claude Code, and OpenCode
- Program Flow Map export contract
- next steps: upstream repo link, redacted demo package, E2E demo, HTML/slides

## Demo Narration

Use this sequence when walking through the repo:

1. Open `README.md` and show the capability statement.
2. Show `docs/assets/atlas-engineering-delivery-hub-discovery-desktop.png` and
   explain the Seven Mountains SDLC / M3 Discovery positioning.
3. Show `docs/assets/atlas-phoenix-lens-delivery-hub-position.svg` and position
   the capability under M3 Discovery.
4. Open `docs/program-flow-map-export-contract.md` and explain the upstream
   Neo4j handoff.
5. Open `docs/samples/atlas-phoenix-lens-mini-output/program-flow-export.sample.csv`
   to show a flow export.
6. Open `program-analysis.sample.md` and explain source-backed observed
   behavior.
7. Open `flow-analysis.sample.md` and explain cross-program behavior.
8. Open `modernization-evidence.sample.yaml` and show how evidence becomes
   machine-readable.
9. Close with `docs/open-collaboration-submission.zh-CN.md` for the internal
   open collaboration story.

## Likely Questions And Answers

### Is this a code converter?

No. Atlas Phoenix Lens is a discovery and evidence capability. It helps teams
understand legacy behavior before deciding what should be rebuilt, retired, or
redesigned.

### Why does it need Neo4j?

Neo4j is used by the upstream Program Flow Map repo to represent program-call
relationships from ARCAD REF / XREF data. This repository consumes the exported
flow as navigation evidence.

### What is reusable across teams?

The flow export contract, source-scan skills, evidence IDs, templates,
validators, review rules, bilingual docs, and sample output structure.

### How does this stay AI-friendly?

It uses Markdown, YAML, CSV, stable IDs, explicit evidence strength, and
validation gates. AI can parse the artifacts, but SMEs remain responsible for
approving business meaning.

### What is still pending?

The internal Neo4j repo link, an approved redacted sample from a real flow, and
a stronger E2E demo from Program Flow export to modernization evidence.

## Links

- Materials index: [atlas-phoenix-lens-index.md](atlas-phoenix-lens-index.md)
- Main README: [../README.md](../README.md)
- Chinese README: [../README.zh-CN.md](../README.zh-CN.md)
- Chinese submission draft:
  [open-collaboration-submission.zh-CN.md](open-collaboration-submission.zh-CN.md)
- Program Flow Map export contract:
  [program-flow-map-export-contract.md](program-flow-map-export-contract.md)
- Mini output sample:
  [samples/atlas-phoenix-lens-mini-output/](samples/atlas-phoenix-lens-mini-output/)
