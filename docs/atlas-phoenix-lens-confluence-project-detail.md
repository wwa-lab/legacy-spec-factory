# Atlas Engineering Delivery Hub - Atlas Phoenix Lens

https://github.com/wwa-lab/legacy-spec-factory

## What is Atlas Phoenix Lens

**Atlas Engineering Delivery Hub** is the unified competition project. It
connects Planning, Estimation, Discovery, Build, Testing, Deployment, and
Maintenance into one engineering delivery system.

**Atlas Phoenix Lens** is an important capability in the Hub's **Discovery
(M3)** stage, and it is the capability demonstrated in this roadshow. It helps
teams understand what a legacy system actually does before they redesign,
rebuild, migrate, or retire it. It recovers evidence-backed knowledge rather
than converting legacy code directly.

The current internal implementation combines a **Program Flow Map**, an
**Evidence Core**, **Dify Knowledge Activation**, and **SME Governance**. The
current technical scope is IBM i / AS400 with RPG, CL, and DDS.

Build Agent and Deployment Agent are downstream capabilities within Atlas
Engineering Delivery Hub. They are not presented as functionality already
delivered by Atlas Phoenix Lens.

## 1) The problem we solve

Legacy modernization often starts with incomplete knowledge:

- Critical business rules are scattered across RPG, CL, DDS, database access,
  batch processing, screens, reports, and operational conventions.
- One business process can span many programs, files, interfaces, exception
  paths, persistence paths, and restart paths.
- Existing documentation may be outdated or may not match the source snapshot
  selected for modernization.
- Critical knowledge is concentrated among a small number of experienced SMEs.
- Teams repeatedly read code, reconstruct context, conduct interviews, and
  manually cross-check findings.
- Generic AI summaries can appear complete while mixing observed facts,
  inference, and unsupported assumptions.

This makes Discovery time-consuming, difficult to scale, and vulnerable to
missed rules or dependencies. Those gaps can later become requirements rework,
testing gaps, migration delays, failed retirement decisions, or production
risk.

## 2) What changed

Atlas Phoenix Lens changes Discovery from unbounded manual investigation into
a bounded, evidence-governed workflow.

Practical impact:

- **Start from a business-relevant Program Flow:** SMEs select a defined scope
  and source snapshot instead of asking the tool to infer a boundary across the
  whole legacy estate.
- **Convert source into reviewable knowledge:** RPG, CL, and DDS analysis
  separates observed behavior, inferred rules, contradictions, and open
  questions.
- **Make knowledge usable through Dify:** Teams can ask business questions and
  create BRD drafts using retrieval constrained by capability, module, program,
  and snapshot metadata.
- **Preserve traceability:** Findings retain Evidence IDs, source coordinates,
  evidence strength, and review state.
- **Keep SMEs in control:** AI-generated content cannot become an approved
  business fact without supporting evidence or a named SME decision.
- **Create a safer downstream handoff:** Reviewed Discovery knowledge can
  support design, Build, Testing, migration, and retirement decisions across
  Atlas Engineering Delivery Hub.

Company impact and commercial value:

- **Free up scarce Discovery and SME capacity** by reducing repeated code
  reading, context reconstruction, and broad explanation work.
- **Avoid downstream rework** caused by misunderstood legacy behavior.
- **Preserve institutional knowledge** as maintainable, evidence-backed
  organizational assets.
- **Reuse the operating model across a modernization portfolio** instead of
  rebuilding the Discovery method for every application.
- **Support safer modernization and retirement decisions** by identifying what
  must be preserved, redesigned, consolidated, or retired.

These benefits represent strong commercial potential. Realized savings should
be confirmed through owned Pilot baselines, comparable measurements, and
approved unit costs.

## 3) How it works

Key capabilities:

- **Program Flow Map:** Uses ARCAD REF / XREF relationships to expose callers,
  callees, objects, and data dependencies, helping SMEs select a bounded
  business flow.
- **Evidence Core:** Scans RPG, CL, and DDS within that scope to extract
  behavior, rules, data usage, exceptions, source coordinates, evidence gaps,
  and review states.
- **Dify Knowledge Activation:** Provides the current internal route for
  metadata-scoped retrieval, business Q&A, workflow orchestration, evidence
  drill-down, and BRD draft generation.
- **SME Governance:** Reviews evidence, resolves contradictions and TBD items,
  records named decisions, and controls approval.
- **Modernization Knowledge Package:** Packages reviewed knowledge for
  downstream design and engineering delivery.

The operating flow is:

**Program Flow selection -> Evidence extraction -> Dify knowledge activation
-> SME review and decision -> Reviewed modernization knowledge -> Downstream
delivery**

Dify makes the knowledge easier to use, but it is not the source of truth.
Canonical Evidence, source coordinates, approval states, and decision records
remain under independent, version-controlled governance.

## 4) Why it scales

- **Reusable operating model:** The sequence of scoping, evidence extraction,
  knowledge activation, SME review, and downstream handoff can be repeated
  across teams and applications.
- **Portable evidence model:** Stable evidence contracts, review states, and
  traceability rules reduce dependence on one model, prompt, or user interface.
- **Bounded retrieval:** Metadata-scoped Dify retrieval reduces cross-system
  contamination and makes answers easier to review.
- **Progressive adoption:** Teams can begin with one high-value Program Flow,
  validate the result, and expand by module, application, or portfolio.
- **Extensible architecture:** New legacy platforms can reuse the governance
  model while adding platform-specific parsers, skills, benchmarks, and SME
  validation.
- **Portfolio value:** Reusable Discovery assets reduce duplicate solution
  design and create a consistent evidence foundation for modernization
  decisions.

The current implementation supports IBM i / AS400 with RPG, CL, and DDS.
**COBOL and other legacy platforms are future extensions, not current
delivered capabilities.** Method portability does not remove the need for
platform-specific implementation and validation.

## 5) Alignment to HSBC values

- **We Get It Done:** Turns a difficult, open-ended Discovery activity into a
  practical workflow that produces usable modernization knowledge.
- **We Take Responsibility:** Keeps evidence, uncertainty, review state, and
  named decisions visible, reducing the risk of treating AI output as fact.
- **We Succeed Together:** Combines engineering analysis with SME expertise and
  creates reusable knowledge for downstream teams.
- **We Value Difference:** Makes specialist legacy knowledge accessible in
  business language while preserving different viewpoints, contradictions, and
  evidence gaps for review.

**In one sentence:** Atlas Phoenix Lens is the evidence-governed Discovery
capability within Atlas Engineering Delivery Hub that turns hard-to-understand
legacy systems into reviewable, reusable modernization knowledge.
