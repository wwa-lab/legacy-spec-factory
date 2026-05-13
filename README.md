# Legacy Spec Factory

Legacy Spec Factory is an end-to-end modernization pipeline for turning IBM i
(AS/400) legacy system behavior into evidence-backed, reviewable, and
implementation-ready specifications.

The goal is not to translate RPG, CL, COBOL, or DDS source directly into Java.
The goal is to recover the business intent hidden inside the legacy system,
produce a trusted `spec.yaml` / `spec.md` pair, and then use that spec package
as the source of truth for AI-native SDLC on the new cloud platform.

```text
IBM i / AS/400 Evidence
  RPGLE / CLLE / COBOL / DDS / DB2 / jobs / screens / reports / logs
        |
        v
Legacy Understanding Layer
  inventory, call graph, CRUD matrix, data dictionary, runtime evidence
        |
        v
Business Capability Map
  program-level logic grouped into business capabilities
        |
        v
Evidence-backed spec package
  requirements, rules, acceptance criteria, traceability, open questions
        |
        v
Human Review Gate
  SME validation, confidence levels, modernization decisions
        |
        v
AI-native SDLC
  Java services, APIs, tests, migration scripts, deployment artifacts
```

## Why This Exists

Many IBM i modernization efforts fail because they treat the legacy system as a
code conversion problem. In practice, the most valuable asset is not the old
source code format. It is the accumulated business knowledge encoded across:

- RPGLE, CLLE, COBOL, and SQL logic
- DDS physical files, logical files, display files, and printer files
- DB2 for i data relationships and control tables
- batch jobs, schedulers, job logs, and message queues
- interactive screens, spool files, reports, and operational workarounds
- SME knowledge that was never written down

Legacy Spec Factory turns those assets into a structured specification layer.
That layer becomes the bridge from legacy modernization to AI-native software
delivery.

## Design Principles

- **Spec as source of truth**: `spec.yaml` is the structured source of truth
  for agents and automation; `spec.md` is the human-readable review view.
- **Evidence over guesses**: every extracted rule should point to source code,
  data, logs, screens, reports, or SME confirmation.
- **Observed vs inferred vs decided**: legacy behavior, inferred business rules,
  and modernization decisions must not be mixed together.
- **Traceability by default**: requirements, business rules, tests, and
  generated code should carry stable IDs across the chain.
- **SME-led governance**: IBM i / AS400 SMEs define the quality bar for legacy
  understanding and approve what can safely move into the spec package.
- **Human approval gates**: AI can extract, organize, and draft, but ambiguous
  business meaning must be reviewed by humans.
- **AI-native from day 1**: the new Java/cloud system should start with
  structured specs, quality contracts, executable tests, and agent-readable
  context instead of recreating documentation debt.

## Relationship to `build-agent-skill`

This project is the reverse-modernization companion to
[`wwa-lab/build-agent-skill`](https://github.com/wwa-lab/build-agent-skill).

`build-agent-skill` focuses on the forward IBM i delivery chain:

```text
Requirement -> Functional Spec -> Technical Design -> Program/File Spec
            -> RPGLE/CLLE/DDS generation -> review -> test scaffold
```

Legacy Spec Factory focuses on the reverse chain:

```text
Existing IBM i system -> evidence model -> business capability spec
                     -> reviewed spec.yaml/spec.md -> Java/cloud SDLC
```

The two projects share the same core ideas:

- layered artifacts
- BR-xx business rule continuity
- review gates
- task-based orchestration
- anti-hallucination rules
- test generation as part of the delivery chain

## Baseline Lessons From Reverse-Code Evaluation

A prior A/B reverse-code comparison is useful as a symptom list, but it is not
the acceptance authority for IBM i modernization. The comparison highlights the
right failure modes: missing artifacts, weak traceability, uncertain mappings,
and low automation readiness. The final judgment still needs to come from IBM i
SMEs who understand RPGLE, CLLE, DDS, DB2 for i, job execution, screens,
reports, and shop-specific conventions.

The useful output is not the one that produces more text. It is the one that is
complete, explicitly traceable, directly mapped to source, technically accurate
from an IBM i perspective, and machine-consumable enough for downstream agents.

| Evaluation Area | Observed Failure Mode | Legacy Spec Factory Standard |
| --- | --- | --- |
| Program coverage | Top-level programs may be listed, but secondary artifacts can be missed | Inventory must report complete program coverage and list unresolved objects explicitly |
| PRTF / report coverage | Missing printer files reduce traceability for reports and outputs | PRTF, spool, and report artifacts are first-class evidence sources |
| Deep subroutines | Missed internal routines create gaps in call graph and behavior analysis | Deep subroutine discovery is a required gate before spec generation |
| Evidence traceability | Tentative language such as "appears" or "likely" makes output hard to audit | Every rule must carry evidence tags such as `Confirmed from Code`, `Observed in Runtime`, `Strongly Inferred`, or `Needs SME Review` |
| Code-to-doc mapping | Ambiguous or reversed mappings create maintenance risk | Each rule, field, and behavior should map directly to source locations or runtime evidence IDs |
| Signature and interface extraction | Incorrect parameters and entry points hurt refactoring and automation | Entry points, parameters, return values, file I/O, and external calls must be extracted into structured contracts |
| Engineering specificity | Generic narrative is not enough for developers or agents | Output must contain actionable engineering notes, dependencies, edge cases, and downstream implementation hints |
| AI consumability | Ambiguous prose blocks reliable automation | Artifacts must be structured, stable-ID based, and friendly to automated parsing |
| Engineering handoff | Manual validation load remains high | Approved specs should be ready for SDLC agents with minimal rework |

This turns the A/B comparison into a reusable evaluation rubric: reverse
engineering is only successful when the output can be audited by humans and
consumed by agents.

## SME Governance Model

Legacy Spec Factory treats the IBM i SME as the control point for the reverse
engineering chain. The SME is not only a final reviewer. The SME defines what
evidence is valid, which extracted facts are trustworthy, and which legacy
behaviors should become modern requirements.

| Stage | SME Responsibility | Required Judgment |
| --- | --- | --- |
| Scope selection | Choose a representative business slice and identify critical programs, files, jobs, screens, and reports | Is this slice narrow enough to finish but important enough to prove the approach? |
| Evidence intake | Confirm source members, DDS, DB2 metadata, job logs, spool files, and sample transactions are sufficient | Are we missing hidden dependencies such as data areas, control files, submitted jobs, or external calls? |
| Inventory review | Validate program, PRTF, DSPF, PF/LF, batch job, and subroutine coverage | Did the analyzer miss any objects an IBM i developer would expect? |
| Static analysis review | Check call graph, CRUD matrix, file usage, indicators, record formats, and subroutine signatures | Does the report reflect how the program actually runs on IBM i? |
| Business rule review | Separate true business rules from technical workarounds, defensive coding, and historical patches | Should this behavior be preserved, redesigned, or retired? |
| Spec approval | Approve `Observed Behavior`, confirm or reject `Inferred Business Rule`, and sign off `Modernization Decision` | Is the spec package safe to feed into the Java/cloud SDLC agent? |
| Equivalence validation | Select golden master cases and edge cases for old-vs-new comparison | Do the selected tests protect the important legacy behavior? |

SME review should explicitly cover IBM i details that generic code-reverse
approaches often miss:

- fixed-format and free-format RPGLE idioms
- CL command flow, submitted jobs, overrides, and message handling
- DDS record formats, indicators, function keys, subfiles, and display-file
  behavior
- PRTF layouts, spool output, and report control breaks
- PF/LF access paths, keyed reads, `SETLL` / `READE` patterns, and join logical
  files
- data areas, data queues, message queues, control tables, and job scheduler
  dependencies
- commitment control, locking, update/delete semantics, and error recovery
- shop-specific naming, copybooks, service programs, and coding conventions

The default rule is simple: if a finding cannot survive SME review, it should
not become an approved requirement.

## Multi-Runtime Skill Portability

The skills in this project should be portable across Codex, Claude Code, and
OpenCode. Different IDEs and agents discover skills from different folders, so
the project should not treat any one runtime directory as the only source of
truth.

Recommended layout:

```text
skills/
  legacy-spec-writer/
    SKILL.md              # canonical skill source
    references/
    templates/
    scripts/

.claude/
  skills/
    legacy-spec-writer/   # Claude Code adapter/copy

.opencode/
  skills/
    legacy-spec-writer/   # OpenCode adapter/copy when not using Claude fallback

.agents/
  skills/
    legacy-spec-writer/   # Open Agent Skills compatible local adapter

.codex/
  skills/
    legacy-spec-writer/   # Codex-specific local adapter, if used by the team setup
```

Runtime guidance:

| Runtime | Recommended Project Folder | Notes |
| --- | --- | --- |
| Codex | `skills/` as canonical source, then install/link into the Codex-supported skill location used by the team | Keep `SKILL.md` compatible with the open Agent Skills shape. Use Codex-specific metadata only in an adapter when needed. |
| Claude Code | `.claude/skills/<skill-name>/SKILL.md` | Claude Code discovers project skills from `.claude/skills/` and personal skills from `~/.claude/skills/`. |
| OpenCode | `.opencode/skills/<skill-name>/SKILL.md`, `.agents/skills/<skill-name>/SKILL.md`, or `.claude/skills/<skill-name>/SKILL.md` | OpenCode supports its native project skill folder and Claude-compatible skill folders. Use `AGENTS.md` for project rules. |

Portability rules:

- Keep the canonical version of each skill under `skills/<skill-name>/`.
- Treat `.claude/`, `.opencode/`, `.agents/`, and `.codex/` as runtime
  adapters or synced copies.
- Do not hand-edit runtime copies without back-porting the change to
  `skills/<skill-name>/`.
- Keep shared `SKILL.md` frontmatter conservative: `name`, `description`, and
  portable metadata first.
- Do not modify adapter `SKILL.md` files directly. Put runtime-only notes under
  `runtime-overrides/` or in files named `*.adapter.md`; the sync script
  preserves those files.
- When validating a skill, test it in all target runtimes before calling it
  release-ready.
- Document the tested runtime matrix in each skill's version history.

Use [scripts/sync-skills.sh](scripts/sync-skills.sh) to copy canonical skills
into runtime adapter folders or check for drift:

```bash
scripts/sync-skills.sh --target all
scripts/sync-skills.sh --target all --check
```

Track validation in [docs/runtime-matrix.md](docs/runtime-matrix.md). Use
[docs/runtime-smoke-tests.md](docs/runtime-smoke-tests.md) before promoting a
runtime from `synced` to `loaded`, `executed`, or `passed`.

The portability goal is simple: one skill design, multiple execution surfaces.
Team members can use Codex, Claude Code, or OpenCode without changing the
business logic, SME governance, evidence model, or spec contract.

## Skill Review Quality Gate

Skills generated for this project must pass a Codex review gate before they are
used by the team.

Quality thresholds:

- **9.5 / 10 or higher**: field-pilot ready
- **9.0 - 9.4**: repo-ready, but not ready for internal field pilot
- **below 9.0**: return to Claude Code for revision

Claude Code may generate or revise skills. Codex reviews them using
[docs/skill-review-gate.md](docs/skill-review-gate.md) and records the result
with [templates/skill-review-scorecard.md](templates/skill-review-scorecard.md).
Calibration examples live under [docs/calibration](docs/calibration).
Actual review records live under [docs/reviews](docs/reviews).

The review focuses on:

- trigger clarity
- workflow completeness
- IBM i / AS400 SME correctness
- evidence discipline and anti-hallucination
- output contract quality
- progressive disclosure
- Codex / Claude Code / OpenCode portability
- reviewability and testability
- engineering handoff value
- maintainability

Any skill below 9.0 must iterate. Any skill below 9.5 should not be used in a
field pilot unless the gap is explicitly accepted by the project owner.

### Current Skill Scores

The scores below are the current repository-facing quality signal. They are
deliberately conservative: the review gate caps a skill at **9.0** when it has
not yet passed the runtime smoke protocol in Codex, Claude Code, and OpenCode,
even if the static review score is higher.

| Skill | Review Record | Static Score | Current Score | Status | Main Reason It Is Not Higher |
| --- | --- | ---: | ---: | --- | --- |
| `legacy-ibmi-inventory` | [v0.1.0 scorecard](docs/reviews/legacy-ibmi-inventory-v0.1.0-scorecard.md) | 9.35 | 9.0 | Repo-ready | Runtime load/execution validation still pending |
| `legacy-ibmi-program-analyzer` | [v0.1.0 scorecard](docs/reviews/legacy-ibmi-program-analyzer-v0.1.0-scorecard.md) | 9.39 | 9.0 | Repo-ready | Runtime smoke prompts exist, but three-runtime execution evidence is pending |
| `legacy-ibmi-flow-analyzer` | [v0.1.1 provisional scorecard](docs/reviews/legacy-ibmi-flow-analyzer-v0.1.1-scorecard.md) | 9.61 expected | 9.0 | Repo-ready; provisional field-pilot after smoke | Three-runtime smoke execution has not been recorded |
| `legacy-ibmi-module-analyzer` | [v0.1.0 scorecard](docs/reviews/legacy-ibmi-module-analyzer-v0.1.0-scorecard.md) | 9.15 | 9.0 | Repo-ready | Runtime smoke pending; output contract and view-reference hardening still needed |
| `legacy-spec-writer` | [v0.1.0 scorecard](docs/reviews/legacy-spec-writer-v0.1.0-scorecard.md) | 9.24 | 9.0 | Repo-ready | Runtime smoke pending; schema/template/checker enforceability still needs one pass |
| `legacy-modernization-orchestrator` | [v0.1.1 scorecard](docs/reviews/legacy-modernization-orchestrator-v0.1.1-scorecard.md) | 9.50 for v0.1.1 | 9.0 for current v0.2.0 scope | v0.1.1 field-pilot ready; current expanded scope needs re-smoke | v0.2.0 added flow/module/spec routing and needs refreshed runtime evidence |

For public trust, scorecards should show both the score before caps and the
score after caps. A 9.0 here should usually be read as "repo-ready and
structurally strong, but not yet proven across all runtime surfaces."

### What the Scores Are Based On

Each review uses [docs/skill-review-gate.md](docs/skill-review-gate.md) and
[templates/skill-review-scorecard.md](templates/skill-review-scorecard.md).
The weighted rubric evaluates:

- purpose and trigger clarity
- workflow completeness
- IBM i / AS400 domain correctness
- evidence and anti-hallucination discipline
- output contract quality
- progressive disclosure
- Codex / Claude Code / OpenCode portability
- reviewability and testability
- engineering handoff value
- maintainability

The reviewer checks these evidence sources:

- **Canonical skill source:** `skills/<skill-name>/SKILL.md`
- **Bundled skill assets:** `references/`, `templates/`, `examples/`, and
  `scripts/` under each skill folder
- **Repository governance docs:** [docs/id-conventions.md](docs/id-conventions.md),
  [docs/evidence-and-knowledge-taxonomy.md](docs/evidence-and-knowledge-taxonomy.md),
  [docs/code-as-ground-truth.md](docs/code-as-ground-truth.md), and
  [docs/data-collection-and-redaction.md](docs/data-collection-and-redaction.md)
- **Runtime portability evidence:** [scripts/sync-skills.sh](scripts/sync-skills.sh),
  [docs/runtime-matrix.md](docs/runtime-matrix.md), and
  [docs/runtime-smoke-tests.md](docs/runtime-smoke-tests.md)
- **Spec contract evidence:** [schemas/spec.schema.yaml](schemas/spec.schema.yaml),
  [templates/spec.yaml](templates/spec.yaml),
  [skills/legacy-spec-writer/templates/spec.yaml](skills/legacy-spec-writer/templates/spec.yaml),
  and [scripts/check-spec-contract.py](scripts/check-spec-contract.py)
- **Review records:** concrete scorecards under [docs/reviews](docs/reviews)
  rather than informal claims in prose

Mandatory stop conditions can cap a skill at 8.0. Runtime portability that is
synced but not smoke-tested caps a skill at 9.0. A skill should only be called
field-pilot ready when the scorecard, runtime matrix, and smoke-test evidence
all agree.

## Target Skill Family

The skill family is split into two layers:

- **Layer 1 — Platform-specific extraction.** Each Layer 1 skill targets one
  legacy platform (IBM i first; COBOL/JCL planned). Skills here read source
  code and runtime artifacts whose syntax and idioms are platform-bound.
- **Layer 2 — Platform-agnostic synthesis.** Layer 2 skills consume the
  structured outputs of Layer 1 and never read raw legacy source. Adding a
  new legacy platform means adding a new Layer 1 family; Layer 2 is reused.

Naming convention:

```
legacy-<platform>-<extractor>    # Layer 1, e.g. legacy-ibmi-inventory
legacy-<synthesizer>             # Layer 2, e.g. legacy-spec-writer
```

The `legacy-` prefix distinguishes this reverse chain from the forward chain
at [`wwa-lab/build-agent-skill`](https://github.com/wwa-lab/build-agent-skill),
which uses `ibm-i-*`.

### Layer 1 — IBM i extraction (`legacy-ibmi-*`)

| Skill | Purpose | Primary Output | Status |
| --- | --- | --- | --- |
| `legacy-ibmi-inventory` | Discover programs, files, tables, jobs, screens, and reports | `inventory.yaml`, object map | Reference implementation |
| `legacy-ibmi-program-analyzer` | Explain RPGLE/CLLE/COBOL-on-IBM-i logic, control flow, and data flow | `program-analysis.md` | MVP candidate |
| `legacy-ibmi-call-graph-analyzer` | Extract program calls, job flow, service boundaries, and dependencies | `call-graph.md`, `call-graph.json` | Planned |
| `legacy-ibmi-crud-matrix-analyzer` | Map programs to physical/logical files and DB2 operations | `crud-matrix.md` | Planned |
| `legacy-ibmi-dds-schema-analyzer` | Analyze PF, LF, DSPF, PRTF definitions and field semantics | `data-dictionary.md`, `screen-map.md` | Planned |
| `legacy-ibmi-runtime-evidence-miner` | Mine job logs, spool files, transaction samples, and test data | `runtime-evidence.jsonl` | Planned |

### Layer 1 — Other platforms (`legacy-<platform>-*`)

| Family | Status |
| --- | --- |
| `legacy-cobol-*` (z/OS COBOL, JCL, copybooks) | Future |
| `legacy-mainframe-*` (CICS, DB2, IMS) | Future |

These are not yet planned in detail; the slot is reserved so that Layer 2
contracts remain platform-agnostic from day one.

### Layer 2 — Platform-agnostic synthesis (`legacy-*`)

| Skill | Purpose | Primary Output | Status |
| --- | --- | --- | --- |
| `legacy-modernization-orchestrator` | Route users through the reverse chain; identify current stage, next safest skill, and required gates | routing decision | Implemented (v0.1.1, repo-ready; not field-pilot ready) |
| `legacy-business-rule-miner` | Convert code paths and runtime evidence into business rules | `business-rules.md` | Planned |
| `legacy-capability-mapper` | Group program-level behavior into business capabilities | `capability-map.md` | Planned |
| `legacy-spec-writer` | Produce the modernization-ready `spec.yaml` and `spec.md` | `spec.yaml`, `spec.md` | MVP candidate |
| `legacy-spec-reviewer` | Validate traceability, completeness, ambiguity, and testability | `review-report.md` | Planned |
| `legacy-equivalence-test-generator` | Generate old-vs-new comparison tests from observed behavior | golden master test pack | Planned |

## Artifact Chain

```text
01_inventory/
  inventory.yaml
  object-map.md
  inventory-review-checklist.md

02_static-analysis/
  call-graph.md
  crud-matrix.md
  data-dictionary.md
  screen-map.md
  program-analysis.md

03_runtime-evidence/
  runtime-evidence.jsonl
  sample-transactions/
  spool-samples/
  job-log-samples/

04_business-understanding/
  business-rules.md
  capability-map.md
  open-questions.md

05_specs/
  spec.yaml
  spec.md
  traceability-matrix.md
  modernization-decisions.md

06_quality/
  golden-master-tests.md
  acceptance-tests.feature
  review-report.md

07_forward-sdlc/
  java-service-plan.md
  api-contracts/
  migration-plan.md
  deployment-notes.md
```

## Spec Package Contract

The generated spec has two views:

- `spec.yaml`: canonical structured contract for agents and automation.
- `spec.md`: human-readable review view rendered from the same information.

Use [schemas/spec.schema.yaml](schemas/spec.schema.yaml) as the structured
contract and [templates/spec.yaml](templates/spec.yaml) as the starting
template. `spec.md` should describe what the new system must do, while keeping
a clear record of where the knowledge came from.

Recommended sections:

```markdown
# Capability: <Business Capability Name>

## Metadata
- spec_id:
- status: draft | in_review | approved
- source_system:
- target_platform:
- owner:

## Business Goal

## Scope
### In Scope
### Out of Scope

## Legacy Evidence
| Evidence ID | Source Type | Location | Summary |
| --- | --- | --- | --- |

## Observed Behavior
| Behavior ID | Description | Evidence | Confidence |
| --- | --- | --- | --- |

## Business Rules
| Rule ID | Rule | Evidence | Confidence | Review Status |
| --- | --- | --- | --- | --- |

## Data Model
| Entity | Legacy Source | Target Concept | Notes |
| --- | --- | --- | --- |

## Process Flow
| Step ID | Description | Evidence |
| --- | --- | --- |

## Inputs
| Input ID | Name | Source | Required | Validation | Evidence |
| --- | --- | --- | --- | --- | --- |

## Outputs
| Output ID | Name | Target | Description | Evidence |
| --- | --- | --- | --- | --- |

## Exceptions
| Exception ID | Condition | Expected Behavior | Severity | Evidence |
| --- | --- | --- | --- | --- |

## Acceptance Criteria

## Modernization Decisions
| Decision ID | Decision | Rationale | Impact |
| --- | --- | --- | --- |

## Open Questions

## Traceability Matrix
```

## Evidence Classification

Each requirement or business rule should be classified before it is used to
generate new-system code. Evidence strength and knowledge type are separate
dimensions; see
[docs/evidence-and-knowledge-taxonomy.md](docs/evidence-and-knowledge-taxonomy.md)
for the canonical taxonomy.

Quick mental model:

- `knowledge_type` classifies the claim: `observed_behavior`,
  `inferred_business_rule`, `modernization_decision`, or `unknown_tbd`.
- `evidence_strength` classifies each linked evidence item:
  `confirmed_from_code`, `observed_in_runtime`, `confirmed_by_sme`,
  `strongly_inferred`, `weakly_inferred`, `needs_sme_review`,
  `contradictory`, or `missing`.
- Claims do not duplicate `evidence_strength`; they link to evidence records and
  derive support from those records.

## Review Gates

The pipeline should stop or request human review when:

- a business rule has no evidence
- program, PRTF, report, or deep subroutine coverage is incomplete
- evidence conflicts across programs, data, or runtime samples
- the rule looks like a technical workaround instead of business intent
- code-to-document mappings are ambiguous, reversed, or missing
- subroutine signatures, parameters, file I/O, or external interfaces cannot be
  extracted confidently
- a field or table has unclear business meaning
- a behavior affects money, inventory, compliance, customer status, or posting
- acceptance criteria cannot be generated
- new-system behavior intentionally differs from legacy behavior

## E2E Modernization Flow

1. **Select a business slice**
   Pick a high-value but bounded flow, such as order entry, credit check,
   inventory allocation, invoicing, settlement, or reconciliation.

2. **Ingest legacy evidence**
   Collect source members, DDS, DB2 metadata, job descriptions, scheduler
   definitions, sample data, logs, spool files, and screen/report samples.

3. **Build the legacy knowledge model**
   Generate inventory, call graph, CRUD matrix, data dictionary, screen map,
   report map, and runtime evidence index.

4. **Extract business capabilities**
   Move from program-level analysis to capability-level understanding. Avoid
   letting old program boundaries dictate new service boundaries.

5. **Generate the spec package**
   Write a spec that includes business goals, rules, data contracts,
   exceptions, acceptance criteria, traceability, and open questions.

6. **Review and approve**
   SMEs and engineers review confidence levels, TBDs, modernization decisions,
   and acceptance criteria.

7. **Generate Java/cloud artifacts**
   Feed the approved `spec.yaml` / `spec.md` pair into the forward SDLC agent
   chain to generate Java services, API contracts, tests, migration scripts,
   and deployment artifacts.

8. **Run equivalence validation**
   Compare legacy outputs and new-system outputs using golden master tests for
   representative and edge-case transactions.

9. **Promote the spec**
   Once validated, the spec becomes the new system's ongoing source of truth.

## MVP Plan

The first milestone should be narrower than the full target pipeline. See
[docs/mvp-scope.md](docs/mvp-scope.md) for the current MVP definition.

Minimum MVP:

- one business capability
- three skills: `legacy-ibmi-inventory`, `legacy-ibmi-program-analyzer`, and
  `legacy-spec-writer`, with `legacy-modernization-orchestrator` as the entry
  point
- one reviewed `spec.yaml` / `spec.md`
- one SME approval pass

The broader roadmap remains:

| Phase | Duration | Goal | Output |
| --- | --- | --- | --- |
| Phase 0 | 1 week | Select target capability and collect evidence | source bundle, data samples, SME list |
| Phase 1 | 1 week | Generate inventory and static analysis | object map, call graph, CRUD matrix |
| Phase 2 | 1 week | Extract data, screen, report, and runtime evidence | data dictionary, screen map, evidence index |
| Phase 3 | 1 week | Draft capability-level spec | first `spec.yaml` / `spec.md`, open questions |
| Phase 4 | 1 week | Human review and golden master design | approved rules, acceptance tests |
| Phase 5 | 1-2 weeks | Forward generation into Java/cloud POC | service skeleton, APIs, tests, validation report |

Success criteria:

- at least one end-to-end business capability is represented as an approved
  `spec.yaml` / `spec.md` pair
- every approved business rule has evidence or SME approval
- the generated Java/cloud POC can run acceptance tests derived from the spec
- golden master tests can compare selected legacy and new-system behavior
- unresolved questions are explicit and tracked, not hidden in generated code

## Data Safety

Raw production evidence should not be committed to this repository. Job logs,
spool output, transaction samples, and DB extracts may contain sensitive
customer, financial, employee, or operational data. Follow
[docs/data-collection-and-redaction.md](docs/data-collection-and-redaction.md)
before using evidence with any agent workflow.

## What This Is Not

- It is not a direct RPG-to-Java transpiler.
- It is not a one-shot LLM prompt.
- It is not a replacement for SME review.
- It is not a reason to preserve every legacy workaround.
- It is not only a migration tool; it is a way to establish an AI-native SDLC
  foundation for the new system.

## Authorship, Copyright, and License

Original author: **Leo L Zhang**

Copyright 2026 Leo L Zhang.

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE)
for the full license text and [NOTICE](NOTICE) for attribution details.

Recommended header for future skill files:

```markdown
<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->
```

The license allows reuse and modification under the Apache-2.0 terms, while the
author and notice files preserve attribution for the original skill design,
documentation patterns, workflow model, and modernization approach.

## Current Status

This repository is in the MVP hardening stage. It now contains the architecture,
governance model, quality gate, scorecard templates, structured spec contract,
ID conventions, data safety guidance, runtime sync script, and the core Legacy
Spec Factory skill set:

- `skills/legacy-modernization-orchestrator`
- `skills/legacy-ibmi-inventory`
- `skills/legacy-ibmi-program-analyzer`
- `skills/legacy-ibmi-flow-analyzer`
- `skills/legacy-ibmi-module-analyzer`
- `skills/legacy-spec-writer`

The canonical skills have author/copyright notices and are synced to Codex,
Claude Code, OpenCode, and `.agents` adapter folders. Current review posture:
repo-ready at 9.0 across the skill family, with one prior 9.5 field-pilot
scorecard for `legacy-modernization-orchestrator` v0.1.1. The expanded current
scope still needs runtime smoke execution and a small hardening pass before the
whole family should be called field-pilot ready.

The next implementation steps are:

1. Run the smoke protocol in Codex, Claude Code, and OpenCode for each core
   skill, then update [docs/runtime-matrix.md](docs/runtime-matrix.md).
2. Close the remaining hardening items in the module analyzer and spec writer
   scorecards.
3. Refresh the scorecards after the smoke runs so field-pilot readiness is
   backed by evidence, not just intent.
