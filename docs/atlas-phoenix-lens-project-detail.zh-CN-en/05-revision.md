# Project Detail: Atlas Phoenix Lens

[中文原文](../atlas-phoenix-lens-project-detail.zh-CN.md) | English

- **Unified competition project:** Atlas Engineering Delivery Hub
- **Capability demonstrated:** Atlas Phoenix Lens
- **Lifecycle role:** Discovery (M3) - Legacy reverse engineering and discovery
- **Current technical focus:** IBM i / AS400, RPG, CL, and DDS
- **Current internal implementation:** Program Flow Map + Evidence Core + Dify + SME Governance
- **Evidence Core repository:** [wwa-lab/legacy-spec-factory](https://github.com/wwa-lab/legacy-spec-factory)

> **Modernization begins with understanding, not translation.**

Atlas Engineering Delivery Hub is a unified engineering delivery system
spanning Planning, Estimation, Discovery, Build, Testing, Deployment, and
Maintenance. Atlas Phoenix Lens is its core Discovery capability.

Before teams choose a target architecture, development approach, migration
strategy, or retirement plan, Phoenix Lens helps them recover what the legacy
system actually does. It turns knowledge scattered across source code, program
relationships, documents, runtime evidence, and SME experience into
evidence-backed, reviewable, reusable modernization knowledge.

This roadshow demonstrates Atlas Phoenix Lens only. Build Agent and Deployment
Agent are other lifecycle capabilities within Atlas Engineering Delivery Hub;
they are not presented as functionality already delivered by Phoenix Lens.

## 1. Where Phoenix Lens Fits In Atlas Engineering Delivery Hub

![Atlas Engineering Delivery Hub highlighting Atlas Phoenix Lens in Discovery](../assets/atlas-engineering-delivery-hub-discovery-desktop.png)

```text
Atlas Engineering Delivery Hub

Planning → Estimation → Discovery → Build → Testing → Deployment → Maintenance
                          │
                          └── Atlas Phoenix Lens
                              Program Flow Map
                              + Evidence Core
                              + Dify Knowledge Activation
                              + SME Governance
```

Phoenix Lens recovers the current system and delivers reviewed Discovery
knowledge. Downstream Build creates the future system only after the evidence
and business decisions have been approved. This boundary prevents teams from
treating AI inference about the old system as a formal requirement for the new
one.

Phoenix Lens Discovery outputs include:

- observed legacy-system behavior;
- inferred business rules that require SME review;
- evidence covering programs, data, exceptions, persistence, and restart
  behavior;
- contradictions, evidence gaps, and `TBD-*` items;
- Evidence IDs, source coordinates, snapshots, and review states;
- a reviewed Modernization Knowledge Package that can be handed downstream.

## 2. The Core Challenge In Legacy Modernization

Legacy modernization is often treated as a technical conversion. Yet the
largest unknown is not whether the code can be converted. It is whether the
organization has a complete, current, reviewable model of how the existing
system behaves.

- Critical business rules are scattered across RPG, CL, DDS, database access,
  batch processing, screens, reports, and runtime conventions.
- Documentation may be outdated or may not correspond to the source snapshot
  used for the modernization effort.
- One business process may span multiple programs, files, interfaces,
  exceptions, persistence paths, and restart paths.
- Large programs may exceed 10K lines, and incomplete reading can silently hide
  critical behavior.
- Critical knowledge is concentrated among a small number of senior SMEs.
- AI summaries may look complete while mixing observed facts, inference, and
  unsupported assumptions.

As a result, teams repeatedly read code, interview SMEs, analyze spreadsheets,
and perform manual cross-checks before forward delivery can begin. Any missed
rule or dependency can later become requirements rework, a testing gap, a
migration delay, a failed retirement, or a production risk.

> The greatest risk is not that the team cannot generate new code. It is that
> the team generates the wrong new system without fully understanding the old
> one.

## 3. The Current Solution: One Capability, Three Implementation Layers, And One Governance Loop

Atlas Phoenix Lens is not a stitched-together demonstration of three
repositories. It is one Discovery capability delivered through three
coordinated implementation layers and a closed SME governance loop:

| Component | Current responsibility | Governance or implementation boundary |
|---|---|---|
| **Program Flow Map** | Builds cross-program relationships from ARCAD REF / XREF and helps SMEs select a business-relevant Program Flow | A Flow establishes scope and navigation; it does not automatically become an Approved Business Fact |
| **Evidence Core** | Scans RPG, CL, and DDS to extract behavior, rules, data, exceptions, source coordinates, and evidence gaps | Implemented through the Legacy Spec Factory skills, contracts, templates, and validators in this repository |
| **Dify Implementation Layer** | Provides metadata-scoped retrieval, business Q&A, orchestration, and BRD draft generation over documents and program-analysis results | The current internal implementation layer; Dify stores searchable copies but is not the Canonical Evidence Source |
| **SME Governance** | Reviews evidence, resolves TBD items, records named decisions, and writes back approval states | AI-generated content cannot bypass the Review Gate and be promoted automatically to an Approved Business Fact |

![Atlas Phoenix Lens implementation design](../assets/atlas-phoenix-lens-design.svg)

The unified product formula is:

> **Atlas Phoenix Lens = Program Flow Map + Evidence Core + Dify Knowledge
> Activation + SME Governance**

## 4. How It Works

```text
ARCAD REF / XREF + legacy documents + RPG / CL / DDS source code
                              ↓
                     Program Flow Map
              Select a bounded business Flow and Snapshot
                              ↓
                       Evidence Core
          Program / Flow / Data Analysis + Evidence Governance
                              ↓
                 Module Context / Evidence Map
       Observed / Inferred / Contradiction / TBD / Review State
                              ↓
                 Dify Knowledge Activation
        Metadata-scoped Retrieval / Business Q&A / BRD Draft
                              ↓
             SME Review / Decision Log / Write-back
                              ↓
             Reviewed Modernization Knowledge Package
                              ↓
      Downstream design and engineering delivery through
               Atlas Engineering Delivery Hub
```

### 4.1 Map The Flow

ARCAD REF / XREF relationships expose callers, callees, objects, and data
dependencies, allowing reviewers to select a business-relevant Program Flow.

The map first answers, "Where should we look?" It uses the program list, call
edges, source members, snapshot, and optional field traces to define the
analysis boundary. It does not promote an SME's navigation order directly into
a confirmed call chain. Every Confirmed Call Edge still requires source-code or
runtime evidence.

### 4.2 Scan The Code

Evidence Core performs controlled analysis of RPG, CL, and DDS within the
defined scope. It extracts:

- source-supported program behavior;
- calculations, validations, and business-rule seeds;
- files, tables, fields, and external dependencies;
- exception, persistence, and restart paths;
- source coordinates, coverage gaps, and evidence strength;
- `Observed`, `Inferred`, `Contradiction`, and `TBD` items.

The output is not a black-box summary. It is a set of structured artifacts that
can be reviewed, validated, and rerun.

### 4.3 Preserve The Evidence

Canonical Evidence is stored in version-controlled artifacts and includes:

- stable Evidence IDs;
- source paths, source versions, and source coordinates;
- snapshots, hashes, and analysis scope;
- sensitivity, authorization, and redaction states;
- knowledge types, evidence strength, and review states.

Approved conclusions can therefore be traced back to the original evidence
even when prompts, models, Dify collections, or downstream implementations
change.

### 4.4 Activate The Knowledge Through Dify

The current internal implementation uses Dify to maintain a document knowledge
base and a program-analysis knowledge base. An SME-selected Program Flow then
constrains retrieval by capability, module, program, and snapshot.

Dify is used to:

- query program and Flow behavior in business language;
- connect document knowledge with source-code analysis results;
- display supporting evidence and open questions;
- generate BRD content with a status of `candidate`, `poc_draft`, or
  `in_review`;
- rapidly validate retrieval, prompts, response formats, and SME readability.

Dify is not used to:

- replace Canonical Evidence;
- infer business boundaries on its own across the entire legacy estate;
- promote AI inference automatically to business fact;
- bypass SME Review to generate an Approved BRD;
- promote a BRD draft directly into Build, Testing, or SDD.

### 4.5 Review And Decide

SME Review confirms:

- whether a conclusion has sufficient evidence;
- whether an AI inference reflects the correct business meaning;
- how a contradiction should be resolved;
- whether a `TBD-*` item should be confirmed, rejected, or investigated
  further;
- which behaviors should be retained, redesigned, consolidated, or retired.

Only content supported by qualified evidence or a named SME decision can enter
the Approved Knowledge Package.

## 5. What Phoenix Lens Changes

| Before Phoenix Lens | With Phoenix Lens |
|---|---|
| Start with an unbounded codebase | Start with an SME-selected Program Flow and an explicit snapshot |
| Read programs one by one in isolation | Analyze program, data, exception, persistence, and restart evidence within a defined scope |
| Produce narrative summaries that cannot be validated | Produce structured facts, inference, contradictions, Evidence Links, and TBD items |
| Ask SMEs to explain the entire implementation again | Focus SME attention on reviewing evidence and unresolved business decisions |
| Allow RAG to infer scope across a global knowledge base | Use capability, module, program, and snapshot metadata to scope Dify retrieval |
| Insert AI-generated content directly into documents | Require every draft to pass the Evidence Gate and SME Review |
| Rebuild the Discovery method for every project | Reuse the Flow Contract, skills, Evidence Schema, review states, and evaluation cases |

The final output is not an isolated document. It is a human-reviewed
Modernization Knowledge Package that can support requirements, target design,
migration planning, testing scope, and retirement decisions.

## 6. Current Capabilities, Evidence, And Actual Boundaries

| Capability | Current status | Evidence or boundary |
|---|---|---|
| Atlas Engineering Delivery Hub positioning | **Unified** | Phoenix Lens is presented only as the Discovery capability |
| Program Flow Map navigation | **Current internal capability / Demo Ready** | Used to scope the Program Flow and snapshot; the internal access URL is not published in this repository |
| RPG, CL, and DDS analysis | **Current implementation** | Evidence Core skills, templates, validators, and sample artifacts are available in this repository |
| Evidence Package | **Available in the repository** | [Phoenix Lens Mini Output](../samples/atlas-phoenix-lens-mini-output/) |
| Dify retrieval, Q&A, and orchestration | **Current internal implementation** | Uses a scoped document knowledge base and program-analysis knowledge base; Demo output remains subject to the Review Gate |
| Dify Metadata Governance | **Being strengthened / Pilot Control** | Critical fields must be verified against silent loss during import, retrieval, and export |
| SME Decision Write-back | **Being strengthened / Pilot Control** | Owner, date, evidence, decision, and status history must be recorded consistently |
| BRD generation | **Draft supported** | Output can only be `candidate`, `poc_draft`, or `in_review`; it cannot become `approved` automatically |
| Handoff to Build, Testing, and Deployment | **Not demonstrated in this roadshow** | Phoenix Lens output can serve as trusted input, but this repository does not claim to implement the downstream stages |
| COBOL analysis | **Future vision** | Not yet delivered as a current capability; it requires a dedicated adapter, skills, benchmark, and SME validation |
| Other legacy platforms | **Reusable method / Future Pilot** | Each platform requires an Inventory Adapter, Scanning Skills, Benchmark Evidence, and SME validation |

Current capability maturity, the local engineering state of Evidence Core, Dify
deployment maturity, and complete Field Pilot results must be described
separately. An existing design does not mean that every production scenario has
been validated.

## 7. Why This Method Can Be Reused Across Legacy Systems

The current implementation focuses on RPG, CL, and DDS on IBM i / AS400.
Phoenix Lens can be extended because it separates platform-specific analysis
from shared evidence governance:

| Reusable layer | What different legacy systems can share | What a new platform must adapt |
|---|---|---|
| Scope Discovery | Start with a bounded business Flow and an explicit snapshot | Inventory and Dependency Adapter |
| Source Scanning | Coverage, evidence coordinates, uncertainty, and Batch Control | Platform-specific parsers, prompts, and Scanning Skills |
| Evidence Contract | Stable IDs, source coordinates, states, sensitivity, and review states | Source Types and platform metadata |
| Knowledge Activation | Dify metadata-scoped retrieval over reviewed artifacts | Collection Design, Chunk Strategy, and filters |
| Human Governance | SME approval, contradictions, TBD items, and decision history | Domain Owners and Acceptance Benchmarks |
| Evaluation | Evidence Links, Unsupported Claims, coverage, and repeatability | Platform-specific Golden Samples and Challenge Cases |

The rollout path should be validated incrementally:

1. First validate one real business Flow containing 5-10 programs.
2. Expand to one application or capability.
3. Add an adapter, skills, and benchmark for each new legacy technology.
4. Claim platform support only after SME and security review.
5. Reuse the same governance method across the modernization portfolio.

Phoenix Lens is not a universal parser that claims to support every platform
today. It is a Discovery Operating Model that can expand through adapters and
benchmarks. COBOL is a potential next area of extension, but it is not promoted
as a current implemented capability.

## 8. Company Impact And Commercial Value

Phoenix Lens delivers far more than faster document generation. It can reduce
the "uncertainty premium" built into every modernization estimate and decision.

- **Release delivery capacity:** Reduce repeated code reading, context
  reconstruction, and broad SME explanation.
- **Avoid downstream rework:** Reduce requirements, target-design, testing, and
  migration rework caused by misunderstood legacy behavior.
- **Preserve institutional knowledge:** Retain critical evidence and decisions
  after a project ends or a senior SME leaves.
- **Enable portfolio reuse:** Stop different teams from rebuilding Flows,
  prompts, Evidence Schemas, and governance processes for every application.
- **Support reliable retirement:** Distinguish behavior that must be retained,
  redesigned, consolidated, or retired safely.
- **Reduce AI risk:** Keep evidence, uncertainty, and approval states visible
  so black-box answers do not contaminate formal requirements and downstream
  design.

```text
Annual quantifiable net value
  = Value of released Discovery and SME delivery capacity
  + Avoided cost of evidence-related rework
  + Avoided cost of rebuilding the same Discovery solution
  + Validated value of earlier retirement
  - Annual Phoenix Lens operating cost
```

At the portfolio level:

```text
Validated value for each adoption scope
  × Number of adoptable applications / capabilities
  × Validated adoption rate
  = Portfolio Value Opportunity
```

Actual benefits must be validated using an owned baseline, comparable Pilot
data, and unit costs accepted by Finance. Targets, illustrative estimates, and
Capacity Release must not be presented automatically as realized Cash Savings.

## 9. Roadshow Demo Path

This roadshow uses Dify as the user entry point. The Program Flow Map and the
artifacts in this repository demonstrate the scope controls and evidence
governance behind it.

```text
Program Flow Map
  → Select a business-relevant Flow and Source Snapshot
  → View Evidence Core Program Analysis and Source Coordinates
  → Use the same scope for business Q&A in Dify
  → Trace the response back to an Evidence ID and the original evidence
  → Generate a BRD Draft
  → Show the SME Review, Decision Log, and Approval Boundary
  → Produce a Reviewed Modernization Knowledge Package
```

The demonstration should emphasize:

1. one explicit SME Program Flow;
2. one Observed Behavior with a source coordinate;
3. one `TBD-*` item that AI cannot close silently;
4. the metadata scope in Dify;
5. one drill-down from an answer to its Evidence ID;
6. one BRD excerpt marked `poc_draft` or `in_review`;
7. how an SME decision confirms or rejects content, or keeps it open for
   further investigation.

## 10. Pilot Success Metrics And Next Steps

The following metrics are proposed acceptance targets, not claims of benefits
already realized:

- at least a 95% success rate for sampled Evidence Links;
- no more than 5% Unsupported Claims;
- an SME correction rate for Observed Behavior no higher than the agreed
  threshold;
- core results that are consistent when the same snapshot is rerun, or whose
  differences can be explained;
- a verifiable reduction in SME Review time relative to the baseline after two
  rounds;
- qualified evidence or a named SME decision for all Approved content;
- no silent truncation of RPG programs exceeding 10K lines, with a processing
  state recorded for every source range;
- source-code or runtime evidence for every Confirmed Call Edge in the Program
  Chain;
- security approval for sensitive data handling, model use, retention, and
  deletion policies.

Next-step priorities:

1. Complete the metadata, state, and approval mappings across Program Flow Map,
   Evidence Core, and Dify.
2. Verify that Dify import, retrieval, and export do not silently drop evidence
   fields.
3. Strengthen the SME Decision Log, Write-back, and BRD Approval Gate.
4. Establish a Golden Evaluation Set for retrieval and generation.
5. Complete the Challenge Case using a real RPG program exceeding 10K lines and
   a 5-10 Program Chain.
6. Begin extending to COBOL or another legacy platform only after the current
   platform benchmark has passed.

## 11. Alignment With Company Values

- **We Get It Done:** Turn an opaque legacy estate into reviewable
  modernization input.
- **We Take Responsibility:** Keep evidence, uncertainty, sensitivity, and
  approval states visible instead of hiding them behind an AI-generated answer.
- **We Succeed Together:** Turn individual SME and engineering knowledge into
  reusable organizational assets.
- **We Value Difference:** Combine source-code evidence, engineering analysis,
  business knowledge, and human judgment.

## In One Sentence

> **Map the flow. Scan the code. Activate the knowledge.** Atlas Phoenix Lens
> enables teams to modernize legacy systems based on evidence rather than
> assumptions.

## Related Materials

- [Chinese source](../atlas-phoenix-lens-project-detail.zh-CN.md)
- [English README](../../README.md)
- [English roadshow script](../atlas-phoenix-lens-pitch.md)
- [Roadshow and review materials index](../atlas-phoenix-lens-index.md)
- [Program Flow Map Export Contract](../program-flow-map-export-contract.md)
- [Phoenix Lens Mini Output](../samples/atlas-phoenix-lens-mini-output/)
- [Vendor BRD AI POC vs. Atlas Phoenix Lens: Comparison and Implementation Improvement Plan (Chinese)](../vendor-vs-atlas-phoenix-lens-comparison-improvement-2026-07-23.zh-CN.md)
