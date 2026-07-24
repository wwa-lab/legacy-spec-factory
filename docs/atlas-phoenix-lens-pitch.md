# Atlas Phoenix Lens - Roadshow Pitch And Speaker Notes

[中文路演稿](atlas-phoenix-lens-pitch.zh-CN.md) | English

## Positioning Guardrail

Use the names in this order:

1. **Atlas Engineering Delivery Hub** - the unified project and lifecycle
   system.
2. **Discovery (M3)** - the lifecycle stage being demonstrated.
3. **Atlas Phoenix Lens** - the Discovery capability in the spotlight.
4. **Legacy Spec Factory** - the technical name of the Evidence Core in this
   repository; use it only when implementation detail matters.

Do not present Phoenix Lens as a fourth project beside the Hub. Do not present
Build Agent or Deployment Agent as features already delivered by Phoenix Lens.

## One-Slide Summary

> **Atlas Phoenix Lens is the Discovery capability of Atlas Engineering
> Delivery Hub: understand the legacy estate before deciding how to modernize
> it.**

Phoenix Lens combines three working layers:

- **Program Flow Map** establishes cross-program scope from ARCAD REF / XREF.
- **Evidence Core** scans RPG, CL, and DDS, preserves source coordinates, and
  separates observed facts, inference, contradictions, and TBDs.
- **Dify Implementation Layer** provides metadata-scoped retrieval, business
  Q&A, orchestration, and BRD draft generation.

SMEs remain the control point. Dify is the current internal experience layer,
not the Canonical Evidence Source and not an automatic approval authority.

## 30-Second Pitch

Legacy modernization does not begin with code conversion. It begins with
understanding what the existing system actually does. Atlas Phoenix Lens is the
Discovery capability of Atlas Engineering Delivery Hub. It maps program flows,
scans RPG, CL, and DDS through an evidence-governed core, and activates the
reviewed results through Dify. Teams can ask business questions and generate a
BRD draft within a bounded program scope, while every approved conclusion
remains tied to evidence or a named SME decision.

## 3-Minute Talk Track

### 1. Start With The Risk

The biggest risk in legacy modernization is not whether a team can generate new
code. It is whether the team builds the wrong system because it never fully
understood the old one.

Legacy behavior is distributed across source, program calls, files, batch
processing, screens, reports, runtime conventions, and the knowledge of a small
number of experienced SMEs. A polished AI summary of one file is not enough to
support a modernization decision.

### 2. Place Phoenix Lens Inside The Hub

Atlas Engineering Delivery Hub is the unified project across Planning,
Estimation, Discovery, Build, Testing, Deployment, and Maintenance.

Today we are showing one capability: **Atlas Phoenix Lens in Discovery**. Its
job is to recover evidence-backed current-state knowledge before the Hub moves
into target design and implementation.

### 3. Explain The Three Layers

First, the Program Flow Map uses ARCAD REF / XREF to establish a bounded
cross-program scope. It answers, "Where should we look?"

Second, the Evidence Core in this repository scans RPG, CL, and DDS and records
behavior, data access, exception paths, source coordinates, contradictions, and
open questions. It answers, "What does the evidence show?"

Third, the current internal implementation uses Dify to retrieve documents and
program-analysis results within that bounded scope. It supports business
questions, knowledge orchestration, and BRD draft generation. It answers, "How
can an SME use the knowledge?"

### 4. Show The Governance

Dify does not become the source of truth. Canonical Evidence remains in
versioned structured artifacts. A generated statement remains `candidate`,
`poc_draft`, or `in_review` until it is supported by qualified evidence or
approved by a named SME.

The system keeps observed behavior, inferred rules, SME decisions, and future
modernization decisions separate. That separation is what makes the output
usable downstream.

### 5. Close With The Value

Phoenix Lens reduces repeated discovery work, limits downstream rework, and
preserves institutional knowledge. The method can be reused across a
modernization portfolio.

The current implementation focuses on IBM i / AS400 with RPG, CL, and DDS.
COBOL and other legacy platforms are future extensions that require their own
adapters, scanning skills, benchmarks, and SME validation.

> **Map the flow. Scan the code. Activate the knowledge.**

## Suggested Five-Slide Story

### Slide 1 - One Hub, One Discovery Capability

**Message:** Atlas Engineering Delivery Hub is the unified project. Atlas
Phoenix Lens is its Discovery capability.

**Visual:** `assets/atlas-engineering-delivery-hub-discovery-desktop.png`

**Speaker note:** Establish the parent-child relationship before discussing
repositories or technology.

### Slide 2 - Modernization Starts With Understanding

**Message:** The greatest risk is modernizing an incomplete or incorrect model
of the legacy system.

**Show:**

- distributed business rules;
- outdated documents;
- cross-program behavior;
- concentrated SME knowledge;
- unsupported AI inference.

### Slide 3 - How Phoenix Lens Works

**Message:** One capability combines flow discovery, evidence governance, and
knowledge activation.

**Visual:** `assets/atlas-phoenix-lens-design.svg`

**Flow:**

```text
Program Flow Map
  -> Evidence Core
  -> Dify Knowledge Activation
  -> SME Review
  -> reviewed Modernization Knowledge Package
```

### Slide 4 - Dify Demo And Evidence Drill-Down

**Message:** Dify makes the evidence usable without replacing the evidence.

**Show:**

- one SME-selected Program Flow;
- metadata-scoped retrieval;
- a business question;
- the supporting Evidence ID and source coordinate;
- a BRD draft marked `poc_draft` or `in_review`;
- the SME approval boundary.

### Slide 5 - Company And Portfolio Value

**Message:** Phoenix Lens reduces uncertainty before expensive downstream work
begins.

**Value themes:**

- released Discovery and SME capacity;
- avoided requirements, design, testing, and migration rework;
- institutional knowledge retention;
- repeatable evidence governance across applications;
- safer application-retirement decisions.

Do not claim realized savings without an owned baseline and comparable pilot
data.

## Dify Demo Narration

1. Open the Program Flow Map and select one business-relevant flow.
2. Show the bounded program list and the source snapshot.
3. Open one Evidence Core program analysis and point to a source coordinate,
   an observed behavior, and a `TBD-*`.
4. Open Dify with the same capability, module, program, and snapshot scope.
5. Ask a business question about behavior, data impact, or an exception path.
6. Trace the answer back to its Evidence ID and source coordinate.
7. Generate a BRD section and show its `poc_draft` or `in_review` state.
8. Explain that a named SME decision or qualified evidence is required before
   the statement can become `approved`.
9. Close by showing the reviewed knowledge package as the Discovery output for
   downstream Atlas Engineering Delivery Hub stages.

## Likely Questions And Answers

### Is Atlas Phoenix Lens the overall competition project?

No. Atlas Engineering Delivery Hub is the unified project. Atlas Phoenix Lens
is the Discovery capability being demonstrated.

### Is this repository the product?

This repository contains the Evidence Core implementation package. The
user-facing Phoenix Lens capability also includes the Program Flow Map and the
current Dify implementation layer.

### Why use Dify?

Dify provides the current internal route for bounded knowledge retrieval,
business Q&A, prompt orchestration, and BRD draft generation. It lets the team
activate reviewed program and document knowledge without first building a
complete bespoke interaction platform.

### Is Dify the source of truth?

No. Dify stores searchable copies. Canonical Evidence, source coordinates,
snapshots, approval state, and downstream contracts remain in versioned
artifacts controlled by the Phoenix Lens Evidence Core.

### Is this a code converter?

No. Phoenix Lens is a Discovery and evidence capability. It determines what the
legacy system does before the organization decides what to preserve, redesign,
replace, or retire.

### What is supported today?

The current focus is IBM i / AS400 with RPG, CL, and DDS analysis, Program Flow
Map navigation, the Legacy Spec Factory Evidence Core, and the internal Dify
retrieval and orchestration route.

### Is COBOL supported?

Not as a current delivered capability. COBOL is a future extension that needs
its own adapter, scanning skills, benchmark, and SME validation.

### Can the method support other legacy platforms?

The shared operating model can: bounded scope, evidence coordinates, knowledge
classification, SME governance, traceability, and metadata-scoped retrieval.
Platform support is only claimed after a platform-specific implementation and
benchmark pass.

### What still needs to be strengthened?

The highest priorities are end-to-end metadata preservation across Program Flow
Map, Evidence Core, and Dify; SME decision write-back; retrieval and generation
evaluation; and challenge cases for a real 10K+ line RPG program and a
5-10-program chain.

## Claim Guardrails

| Topic | Approved wording |
| --- | --- |
| Dify | Current internal retrieval and orchestration implementation layer |
| Dify maturity | Current route with metadata governance, write-back, and scaled evaluation still being strengthened |
| Source of truth | Canonical Evidence remains in versioned structured artifacts |
| Current language scope | RPG, CL, and DDS |
| COBOL | Future vision, not a current delivered capability |
| Cross-platform value | Reusable method; each platform requires its own implementation and validation |
| BRD | Draft generation is supported; approval requires evidence or a named SME decision |
| Commercial value | Portfolio opportunity to be validated against pilot baselines; not realized savings |

## Links

- Chinese roadshow script:
  [atlas-phoenix-lens-pitch.zh-CN.md](atlas-phoenix-lens-pitch.zh-CN.md)
- Materials index:
  [atlas-phoenix-lens-index.md](atlas-phoenix-lens-index.md)
- English README:
  [../README.md](../README.md)
- Chinese README:
  [../README.zh-CN.md](../README.zh-CN.md)
- Program Flow Map export contract:
  [program-flow-map-export-contract.md](program-flow-map-export-contract.md)
- Mini output sample:
  [samples/atlas-phoenix-lens-mini-output/](samples/atlas-phoenix-lens-mini-output/)
