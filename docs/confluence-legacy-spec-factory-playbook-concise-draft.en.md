# Legacy Spec Factory Internal Knowledge Base Draft

> Sync note: This English concise draft is maintained in lockstep with the Chinese concise draft [`confluence-legacy-spec-factory-playbook-concise-draft.md`](confluence-legacy-spec-factory-playbook-concise-draft.md). Any future change to structure, tables, headings, or content must be applied to both files.

## 1. Goal

Legacy Spec Factory is an evidence-backed method for IBM i / AS400 modernization. Its goal is not to directly translate RPGLE, CLLE, COBOL, or DDS code into Java. Its goal is to recover the real business intent embedded in the legacy system and produce auditable, reviewable specifications that can be handed off to downstream SDLC teams.

Core principles:

- Center the work on business capabilities, not individual programs.
- RAG / code knowledge graphs provide evidence context, but they are not final truth.
- Legacy behavior, inferred business rules, and modernization decisions must be managed separately.
- Key rules must be backed by evidence or reviewed by SMEs.
- `spec.yaml` / `spec.md` are the main downstream delivery inputs.

## 2. Recommended Page Structure

| No. | Page | Purpose |
|---:|---|---|
| 01 | Method, Principles & Delivery Process | Explain the methodology, core principles, and delivery process |
| 02 | Scope, Non-Goals & Assumptions | Define scope, non-goals, assumptions, and risks |
| 03 | Evidence Model, SME Review & Traceability | Define the evidence model, SME review rules, and traceability chain |
| 04 | System Context & Architecture | Describe legacy systems, target systems, and upstream/downstream relationships |
| 05 | As-Is Business Processes | Capture business, system, program, and data flows |
| 06 | Functional Requirements Catalogue | Consolidate functional requirements for downstream teams |
| 07 | Business Rules Catalogue | Manage business rules, evidence, confidence, and SME decisions |
| 08 | Data Model & Data Dictionary | Capture data objects, field meanings, relationships, and data quality issues |
| 09 | Integrations, Batch Jobs & Scheduling | Record interfaces, batch jobs, scheduling, reports, and rerun mechanisms |
| 10 | NFRs, Controls & Observability | Capture non-functional requirements, controls, audit, and monitoring needs |
| 11 | Delivery Packaging, Gates & Handoff | Define delivery packages, quality gates, and downstream handoff standards |

## 3. Standard Page Template

Each page should use the same structure:

| Section | Content |
|---|---|
| Purpose | What problem this page solves |
| Scope | What is covered and not covered |
| Inputs | Required input materials |
| Outputs | Expected page outputs |
| Evidence Required | Evidence that must be linked |
| Open Questions / TBDs | Unconfirmed questions |
| Review Owner | Who owns review |
| Approval Gate | Conditions required before moving forward |

## 4. Evidence and Review Model

Knowledge types:

| Type | Meaning |
|---|---|
| `observed_behavior` | Real legacy behavior proven by code, runtime logs, reports, or samples |
| `inferred_business_rule` | Business rule inferred from behavior, code, or data |
| `modernization_decision` | Target-system design decision or tradeoff |
| `unknown_tbd` | Issue with missing evidence, unclear meaning, or conflicting evidence |

Evidence strength:

| Strength | Meaning |
|---|---|
| `confirmed_from_code` | Directly proven by source code |
| `observed_in_runtime` | Proven by job logs, spool files, sample transactions, or reports |
| `confirmed_by_sme` | Explicitly confirmed by an SME |
| `strongly_inferred` | Strongly inferred from multiple evidence points, but still needs review |
| `weakly_inferred` | Weak inference; cannot directly become a requirement |
| `contradictory` | Evidence conflicts |
| `missing` | Required evidence is missing |

Approval rules:

- Content without evidence cannot become a formal requirement.
- Inferred business rules must be confirmed by SMEs.
- Modernization decisions must be confirmed by product, architecture, or delivery owners.
- All `TBD-*` items must be resolved or explicitly marked as non-blocking.

## 5. Recommended Adoption Path

```text
RAG / Code Knowledge Graph / Source Evidence
  -> Module Context
  -> As-Is Process
  -> Business Rules
  -> Functional Requirements
  -> spec.yaml / spec.md
  -> Traceability Package
  -> SDLC Handoff
```

Start from the module view by default. If module boundaries, flows, and RAG evidence are already available, a full source-code excavation is not required first. Source-level analysis is mainly used to repair missing evidence, resolve conflicts, verify high-risk rules, and close TBDs.

## 6. Action Plan

| Phase | Timeline | Objective | Key Actions | Deliverables |
|---|---:|---|---|---|
| 1. Build Structure | Week 1 | Establish the Confluence page structure | Create the homepage and 11 child pages; apply the standard page template | Page tree and blank templates |
| 2. Align Methodology | Week 1 | Build shared methodology alignment | Clarify the goal, principles, evidence model, SME role, and delivery path | Methodology homepage and evidence model page |
| 3. Create Templates | Week 2 | Enable the team to execute from templates | Create Scope, Process, Rule, Requirement, Data, Integration, Traceability, and Handoff templates | Reusable page templates |
| 4. Select Pilot Module | Week 2 | Select one real module for pilot | Confirm module boundary, input materials, owner, and SME | Pilot scope and input checklist |
| 5. Populate Pilot | Week 3 | Validate the structure with real content | Populate flows, rules, data, integrations, batch jobs, and TBDs | Pilot module draft |
| 6. Run SME Review | Week 3-4 | Review high-risk rules and open questions | Run SME review; confirm, reject, or mark rules | SME decision log and approved rules |
| 7. Build Traceability | Week 4 | Build the chain from evidence to delivery | Link evidence -> behavior -> rule -> requirement -> acceptance criteria | Traceability matrix |
| 8. Standardize & Roll Out | Ongoing | Make this a repeatable team workflow | Review pilot lessons; capture good examples and anti-patterns; roll out to more modules | Team playbook and example library |

## 7. Execution Tracker

| Task | Priority | Owner | Target | Status |
|---|---:|---|---|---|
| Create Confluence homepage | High | Modernization Lead | Week 1 | Not Started |
| Create 11 child pages | High | BA | Week 1 | Not Started |
| Draft methodology summary | High | Modernization Lead / Architect | Week 1 | Not Started |
| Define evidence taxonomy | High | BA / SME / Architect | Week 1 | Not Started |
| Create business rule template | High | BA | Week 2 | Not Started |
| Create traceability template | High | BA / Architect | Week 2 | Not Started |
| Select pilot module | High | Product Owner / SME | Week 2 | Not Started |
| Populate pilot pages | High | BA / Engineer | Week 3 | Not Started |
| Run SME review | High | SME / BA | Week 4 | Not Started |
| Finalize handoff checklist | Medium | Delivery Lead / Architect | Week 4 | Not Started |
| Publish pilot as reference | Medium | Modernization Lead | Week 4+ | Not Started |

## 8. Definition of Done

The first version of the knowledge base is done when:

- The 11 core pages have been created.
- Each page has purpose, inputs, outputs, owner, and approval gate.
- The evidence model and SME review rules have been defined.
- At least one pilot module has been populated.
- At least one SME review has been completed.
- At least one complete chain can be demonstrated: evidence -> behavior -> business rule -> requirement -> acceptance criteria.
- The team knows which template to use when starting the next module.

