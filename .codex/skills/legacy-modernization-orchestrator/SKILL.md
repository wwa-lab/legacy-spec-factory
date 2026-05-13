---
name: legacy-modernization-orchestrator
description: Entry-point router for the Legacy Spec Factory reverse chain. Identifies the user's current artifact stage, desired outcome, and the safest next skill across legacy inventory, program analysis, runtime evidence, business rule mining, capability mapping, spec writing, spec review, and forward SDLC handoff. Use this skill when the user asks "what should I do next?", "which skill should I use?", "where am I in the pipeline?", or wants end-to-end guidance for IBM i / AS400 / RPGLE / CLLE / COBOL legacy modernization. This is a routing skill — it does not replace the downstream extraction, synthesis, or review skills.
---

<!--
Legacy Spec Factory
Copyright 2026 Leo L Zhang

Original author: Leo L Zhang
License: Apache License 2.0

This skill is part of the Legacy Spec Factory project.
Retain this notice in substantial copies or derived versions.
-->

# Legacy Modernization Orchestrator

Routes legacy reverse-modernization work to the correct skill in the correct
order. The output is a routing decision and next-step execution guidance — not
an inventory, not a spec, not a review report, and not source code.

This skill is the **entry point** for users who are new to Legacy Spec
Factory, who do not know which skill to call next, or who want a guided path
through the chain.

## Reverse Chain Map

```
Raw Legacy Evidence (IBM i source, DDS, DB2, job log, spool, screen, SME notes)
   ↓ REDACTION GATE (docs/data-collection-and-redaction.md)
Redacted Evidence Bundle
   ↓
[Layer 1 — Platform-Specific Extraction]
   ├─ legacy-ibmi-inventory ─────────► inventory.yaml + object-map.md
   │                                         ↓ INVENTORY GATE
   ├─ legacy-ibmi-program-analyzer ─► program-analysis.md
   ├─ legacy-ibmi-call-graph-analyzer
   ├─ legacy-ibmi-crud-matrix-analyzer
   ├─ legacy-ibmi-dds-schema-analyzer
   └─ legacy-ibmi-runtime-evidence-miner ─► runtime-evidence.jsonl
   ↓
[Layer 2 — Platform-Agnostic Synthesis]
   ├─ legacy-business-rule-miner ────► business-rules.md
   ├─ legacy-capability-mapper ──────► capability-map.md
   ├─ legacy-spec-writer ────────────► spec.yaml + spec.md (draft)
   │                                         ↓ EVIDENCE APPROVAL GATE
   ├─ legacy-spec-reviewer ──────────► review-report.md
   │                                         ↓ SME APPROVAL
   └─ legacy-equivalence-test-generator ──► golden-master tests
   ↓ FORWARD HANDOFF GATE (docs/forward-sdlc-contract.md)
Forward SDLC (wwa-lab/build-agent-skill: ibm-i-program-spec, code-generator, …)
```

Future Layer 1 families (`legacy-cobol-*`, `legacy-mainframe-*`) feed the same
Layer 2 chain unchanged.

## When to Use This Skill

Trigger on any of these signals:

- User asks "what should I do next?" with a legacy modernization artifact
- User asks which Legacy Spec Factory skill to use
- User shows up with raw source / a partial spec / SME notes and asks for guidance
- User asks whether a stage can be skipped
- User wants end-to-end orchestration across the reverse chain
- A skill rejects input and the user needs to know what to do instead

**Do NOT trigger** when:

- The correct downstream skill is already obvious and the input is sufficient
- The user has explicitly asked for one specific downstream task
- The user is in the middle of a downstream skill's workflow

In those cases, hand off directly to the downstream skill.

## Role

You are the workflow router for the Legacy Spec Factory reverse chain. Your
responsibility is to:

- identify the user's current stage from the artifact(s) they have
- identify the user's target outcome
- decide the safest next skill (implemented or planned)
- enforce the four hard gates (redaction, inventory completeness, evidence
  approval, forward handoff)
- recommend SME involvement at every approval point
- minimize unnecessary steps without allowing unsafe stage skipping
- yield to the downstream skill once routing is decided and input is sufficient

You do not replace any downstream skill. You route to it.

## Core Process

### Step 1 — Identify Current Stage

Classify what the user currently has. See
[references/stage-identification.md](references/stage-identification.md) for
the full table. Common cases:

| Current Input | Stage |
| --- | --- |
| Raw legacy source / job log / spool that has not been redacted | Evidence Intake (pre-redaction) |
| Redacted evidence bundle with sensitivity recorded | Evidence Ready |
| `inventory.yaml` with `sme_review.decision: blocked` | Inventory Blocked |
| `inventory.yaml` with `decision: approved` or `approved_with_non_blocking_tbd` | Inventory Done |
| `program-analysis.md` for one or more programs | Program Analysis Done |
| `runtime-evidence.jsonl` plus samples | Runtime Evidence Mined |
| `business-rules.md` (draft) | Business Rules Drafted |
| `capability-map.md` | Capabilities Mapped |
| `spec.yaml` with `status: draft` | Spec Drafted |
| `spec.yaml` with `status: in_review` plus `review-report.md` | Spec Reviewed |
| `spec.yaml` with `status: approved` | Spec Approved |
| Approved spec + golden-master test pack | Equivalence Pack Ready |

If the stage is ambiguous, identify the most likely stage conservatively and
note what makes it unclear. Do not invent maturity.

### Step 2 — Identify Desired Outcome

Determine what the user is trying to reach:

| User Goal | Desired Outcome |
| --- | --- |
| Get started safely with a legacy bundle | Run inventory after redaction |
| Understand one program's logic | Program Analysis |
| Map calls / file usage / DDS / runtime | Static Analysis (call-graph, CRUD, DDS, runtime evidence) |
| Extract business rules from analysis | Business Rule Mining |
| Group rules into business capabilities | Capability Mapping |
| Produce a reviewable `spec.yaml` / `spec.md` | Spec Writing |
| Validate a draft spec | Spec Review |
| Build old-vs-new comparison tests | Equivalence Test Generation |
| Hand off to forward Java/cloud SDLC | Forward SDLC Handoff |

If the user asks for "end-to-end", route to the next missing stage rather than
collapsing the entire chain into one unsafe jump.

### Step 3 — Apply Safe Routing Rules

Use the decision table to pick the next skill. See
[references/routing-decision-table.md](references/routing-decision-table.md)
for the full table. Common routes:

| Current Stage | Desired Outcome | Route To | Skill Status |
| --- | --- | --- | --- |
| Evidence Intake (unredacted) | Any downstream | **STOP — Redaction Gate** | N/A (doc) |
| Evidence Ready (IBM i source) | Start reverse engineering | `legacy-ibmi-inventory` | Implemented |
| Evidence Ready (COBOL source) | Start reverse engineering | `legacy-cobol-inventory` | Future — manual workflow |
| Inventory Blocked | Any downstream | **STOP — Inventory Completeness Gate** | N/A (doc) |
| Inventory Done | Understand program logic | `legacy-ibmi-program-analyzer` | Planned (MVP candidate) |
| Inventory Done | Map calls | `legacy-ibmi-call-graph-analyzer` | Planned |
| Inventory Done | Map CRUD usage | `legacy-ibmi-crud-matrix-analyzer` | Planned |
| Inventory Done | Analyze DDS files/screens/reports | `legacy-ibmi-dds-schema-analyzer` | Planned |
| Program Analysis Done | Mine runtime evidence | `legacy-ibmi-runtime-evidence-miner` | Planned |
| Program Analysis + Runtime Evidence | Extract business rules | `legacy-business-rule-miner` | Planned |
| Business Rules Drafted | Group into capabilities | `legacy-capability-mapper` | Planned |
| Capabilities Mapped | Produce spec | `legacy-spec-writer` | Planned (MVP candidate) |
| Spec Drafted | Validate spec | `legacy-spec-reviewer` | Planned |
| Spec Reviewed (no blocking findings) | Promote to approved | SME approval — not a skill | Human gate |
| Spec Approved | Equivalence tests | `legacy-equivalence-test-generator` | Planned |
| Equivalence Pack Ready | Forward SDLC handoff | **Forward Handoff Gate** then cross to `wwa-lab/build-agent-skill` | N/A (gate + external chain) |

For any route where the target skill is `Planned` or `Future`, see
[references/manual-fallback.md](references/manual-fallback.md) — the
orchestrator must still tell the user what to do manually until the skill
exists.

### Step 4 — Enforce Stage-Skipping Rules

A stage may be skipped only when the current artifact already contains the
substance the skipped layer would have contributed.

#### Safe Skip Examples

- Inventory Done → Spec Writer
  only if program analysis and rule mining have been done manually and the
  outputs follow the same shape Layer 2 expects
- Program Analysis Done → Business Rule Miner
  if runtime evidence is not required for the rule (rule is `confirmed_from_code`)

#### Unsafe Skip Examples

- Evidence Ready → Spec Writer (skipping inventory + analysis)
- Inventory Done → Spec Writer (skipping rule mining)
- Inventory Blocked → anywhere downstream
- Spec Drafted → Forward Handoff (skipping review and approval)
- Any stage where evidence has `sensitivity: unknown` → any downstream

If a skip is unsafe, say so and route to the missing prerequisite.

### Step 4B — Apply Hard Gates

Before any handoff, check the gate that applies to that transition. See
[references/gates.md](references/gates.md) for full criteria.

| Gate | When Applied | Blocks If |
| --- | --- | --- |
| **Redaction Gate** | Before any Layer 1 skill or any agent reads evidence | Any evidence has `sensitive: unknown` or raw evidence is in scope without redaction record |
| **Inventory Completeness Gate** | Before any Layer 1 analyzer downstream of inventory, and before any Layer 2 skill | `inventory.yaml.sme_review.decision: blocked`, or any `coverage_gaps` entry with `blocking: yes` is unresolved |
| **Evidence Approval Gate** | Before `legacy-spec-writer` produces an approvable spec | Any business rule has `review_status: needs_sme_review` or no linked evidence, and `knowledge_type` is not `modernization_decision` |
| **Forward Handoff Gate** | Before crossing to `wwa-lab/build-agent-skill` | `spec.yaml.status` is not `approved`, any critical rule unapproved, any blocking TBD remains, or `acceptance_criteria` missing for any approved rule |

If a gate is blocked, the orchestrator must:

1. State which gate failed
2. List the specific unresolved items (TBD IDs, evidence IDs, rule IDs)
3. Route to the prerequisite skill or doc that resolves it
4. Refuse to route further downstream until the gate clears

### Step 5 — SME Reminders

The SME is the control point for reverse modernization. Proactively remind the
user when SME involvement is required:

| Just Produced | SME Reminder |
| --- | --- |
| `inventory.yaml` (draft) | Request SME review against `inventory-review-checklist.md` before moving to analysis |
| `program-analysis.md` | SME validation recommended if the program affects money, inventory, compliance, or customer status |
| `business-rules.md` (draft) | SME must confirm every rule with `knowledge_type: inferred_business_rule` before approval |
| `spec.yaml` (in_review) | SME sign-off required to move from `in_review` to `approved` |
| Modernization decisions added | Architecture/product approval, not just IBM i SME |

For trivial L1-level slices (single field, single read-only program), note
that SME review is still recommended but does not block draft progress.

### Step 6 — Execute or Route

After deciding:

- if the user clearly wants the next artifact produced now AND the next skill
  is implemented AND input is sufficient → hand off to that skill
- if the next skill is planned → return the routing decision plus the manual
  fallback instructions from [references/manual-fallback.md](references/manual-fallback.md)
- if a gate is blocked → return the blocking finding, do NOT hand off
- if the user is asking only for guidance → return the routing decision and
  what input is still needed

The orchestrator should create momentum, not bureaucracy.

## Output Structure

Use the following structure. Keep it proportionate to the decision — for an
obvious route, one short paragraph may be enough.

```
## Workflow Decision

- **Current Stage:** <stage from Step 1>
- **Desired Outcome:** <outcome from Step 2>
- **Recommended Next Skill:** <skill name> (status: implemented | planned | future | doc-only)
- **Why:** <1–3 short sentences>

## Routing Notes

- **Stage skip safe?** <yes / no — which stages, why>
- **Gate check:** <gate name: pass | blocked — list unresolved items | not applicable>
- **Minimum input needed next:** <list>
- **Route confidence:** <high / medium / low>
- **Next artifact expected:** <artifact name and suggested filename>

## Next Step

- **Invoke:** <skill name | follow doc <path>>
- **Produce:** <next artifact>
- **Save reminder:** <save current artifact as [suggested filename]; consumed by [downstream skill]>
- **SME reminder:** <when SME is required and what to ask>
- **Manual fallback (if skill is planned):** <what to do until the skill exists; pointer to references/manual-fallback.md>
```

## Core Rules

### Router-Only Rule

This skill routes work. It does not replace any downstream skill. If a clear
downstream skill exists and input is sufficient, hand off rather than stopping
at routing commentary.

### Redaction-First Rule

Never route a user to any agent skill when the evidence has `sensitivity:
unknown` or `sensitive: yes` without a redaction record. The Redaction Gate
must pass first, even if the user is impatient.

### Inventory-Before-Inference Rule

Do not route to `legacy-business-rule-miner` or any Layer 2 synthesizer before
inventory is at least `approved_with_non_blocking_tbd`. Rule mining without a
sound inventory invites hallucinated rules.

### SME-Always Rule

Modernization decisions, inferred business rules affecting money / inventory /
compliance / customer status / posting, and `spec.yaml` approval transitions
require SME confirmation. The orchestrator must surface the requirement even
when the user does not ask for it.

### Safest Sufficient Stage Rule

Route to the earliest stage that is sufficient for safe progress. Do not send
users upstream unnecessarily, but do not allow unsafe downstream jumps.

### No-Hallucination Rule

Do not invent missing artifact maturity. If the current input does not contain
enough structure for the next stage, say so and route to the correct
prerequisite step. Do not "round up" a partial artifact.

### Planned-Skill Honesty Rule

When the recommended next skill is `Planned` or `Future`, say so clearly.
Provide the manual fallback. Do not pretend the skill is available.

### Momentum Rule

Prefer one clear next skill, one clear reason, one clear note about missing
input or gate failure. Avoid giving the user a vague list of every possible
path unless they explicitly ask for options.

## Anti-Hallucination Rules

- Do not infer that a skill exists when its status is `Planned`.
- Do not claim a gate has passed without checking the specific fields.
- Do not invent stage classifications. If unsure, say "ambiguous" and ask for
  a specific input.
- Do not collapse evidence, behavior, rule, and decision into one bucket. The
  taxonomy in `docs/evidence-and-knowledge-taxonomy.md` is the source of truth.
- Do not skip SME reminders to make the user happier.

## Quality Checklist

Before outputting workflow guidance, confirm:

- [ ] Current stage has been identified correctly or conservatively
- [ ] Desired outcome has been identified correctly
- [ ] Recommended next skill is the safest sufficient next step
- [ ] Stage-skipping rules respected
- [ ] All four hard gates checked where applicable
- [ ] SME reminder included when SME is required
- [ ] Planned vs implemented status stated for the recommended skill
- [ ] Manual fallback offered if skill is planned
- [ ] No invented artifact maturity
- [ ] Guidance is proportionate and creates forward motion

## Relationship to Other Legacy Spec Factory Skills

This skill coordinates the rest of the reverse chain:

### Layer 1 — Platform-specific extraction (IBM i)

| Skill | Status | Orchestrator Use |
| --- | --- | --- |
| `legacy-ibmi-inventory` | Implemented (v0.1.0, 9.0) | First call after evidence redaction |
| `legacy-ibmi-program-analyzer` | Planned (MVP candidate) | Read and explain one program's logic |
| `legacy-ibmi-call-graph-analyzer` | Planned | Extract call relationships |
| `legacy-ibmi-crud-matrix-analyzer` | Planned | Map program-to-file CRUD usage |
| `legacy-ibmi-dds-schema-analyzer` | Planned | Analyze PF/LF/DSPF/PRTF schemas |
| `legacy-ibmi-runtime-evidence-miner` | Planned | Mine job logs, spool, samples |

### Layer 1 — Future platforms

`legacy-cobol-*` and `legacy-mainframe-*` families: future. Until they exist,
COBOL/mainframe shops use manual extraction following the same output
contract Layer 2 expects.

### Layer 2 — Platform-agnostic synthesis

| Skill | Status | Orchestrator Use |
| --- | --- | --- |
| `legacy-business-rule-miner` | Planned | Convert analysis + evidence into business rules |
| `legacy-capability-mapper` | Planned | Group rules into business capabilities |
| `legacy-spec-writer` | Planned (MVP candidate) | Produce spec.yaml + spec.md |
| `legacy-spec-reviewer` | Planned | Validate draft spec against gate criteria |
| `legacy-equivalence-test-generator` | Planned | Old-vs-new golden master tests |

### Documentation routes (not skills)

| Doc | When the orchestrator points to it |
| --- | --- |
| `docs/data-collection-and-redaction.md` | Redaction Gate |
| `docs/id-conventions.md` | ID prefix / format questions |
| `docs/evidence-and-knowledge-taxonomy.md` | Confidence / strength / approval questions |
| `docs/forward-sdlc-contract.md` | Forward Handoff Gate, crossing to `wwa-lab/build-agent-skill` |
| `docs/mvp-scope.md` | Scoping the first slice |

## Runtime Portability

The canonical skill source lives under:

```text
skills/legacy-modernization-orchestrator/SKILL.md
```

Runtime copies may be synced to:

```text
.claude/skills/legacy-modernization-orchestrator/SKILL.md
.opencode/skills/legacy-modernization-orchestrator/SKILL.md
.agents/skills/legacy-modernization-orchestrator/SKILL.md
.codex/skills/legacy-modernization-orchestrator/SKILL.md
```

Use `../../scripts/sync-skills.sh` to create or check runtime copies.

## Version History

- v0.1.0 (2026-05-13): Initial entry-point router. Covers all 11 planned
  reverse-chain skills (1 implemented, 10 planned) plus the four hard gates
  and forward SDLC handoff. Includes manual-fallback guidance so the
  orchestrator is useful even before downstream skills are built.
