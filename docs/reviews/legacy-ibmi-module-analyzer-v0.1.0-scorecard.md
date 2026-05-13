# Skill Review Scorecard: legacy-ibmi-module-analyzer v0.1.0

## Metadata

- skill_name: legacy-ibmi-module-analyzer
- skill_path: skills/legacy-ibmi-module-analyzer
- reviewed_version: v0.1.0
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-05-14
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Checked canonical source under `skills/legacy-ibmi-module-analyzer/`.
- Checked `SKILL.md`, templates, references, positive example, and negative
  incomplete-module example.
- Checked `docs/module-analysis-model.md`, `docs/code-as-ground-truth.md`,
  `docs/evidence-and-knowledge-taxonomy.md`, and `docs/id-conventions.md` for
  model and evidence alignment.
- Ran `scripts/sync-skills.sh --target all --check`; all runtime adapter copies
  reported `OK`.
- Checked `docs/runtime-matrix.md`; all target runtimes are still `synced`, not
  `loaded`, `executed`, or `passed`.
- Checked `docs/runtime-smoke-tests.md`; no module-analyzer prompt has been
  added yet, so the reusable smoke protocol cannot be run verbatim for this
  skill.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies under the review gate:

- portability has been considered and adapter drift has been checked, but the
  skill has not been loaded or executed in Codex CLI, Claude Code, and OpenCode
- the runtime-smoke-test prompt set does not yet include
  `legacy-ibmi-module-analyzer`
- `SKILL.md` links several per-view methodology files and a wildcard view
  template that do not exist in the canonical folder, so progressive disclosure
  is not clean enough for 9.5 field-pilot use

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.2 | 1.10 |
| IBM i / domain correctness | 14% | 9.3 | 1.30 |
| Evidence and anti-hallucination | 12% | 9.4 | 1.13 |
| Output contract | 10% | 8.9 | 0.89 |
| Progressive disclosure | 8% | 8.7 | 0.70 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.1 | 0.91 |
| Engineering handoff value | 8% | 9.2 | 0.74 |
| Maintainability | 6% | 8.8 | 0.53 |

Final score before cap: **9.15 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For 9.5

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| MOD-REV-001 | High | Runtime portability is structurally clean but not tested. `docs/runtime-matrix.md` records this skill as `synced` only, and `docs/runtime-smoke-tests.md` has no positive or negative prompt for it. | Add module-analyzer smoke prompts and pass criteria, run the protocol in Codex CLI, Claude Code, and OpenCode, then update `docs/runtime-matrix.md` and the scorecard. | Runtime portability, reviewability |
| MOD-REV-002 | High | `SKILL.md` points to files that do not exist: `templates/view-*.md` and `references/view-1-operation-flow.md` through `references/view-4-data-flow.md`. The actual template is `templates/view-template.md`, and per-view methodology currently lives inside `references/synthesis-rules.md` / `references/output-contract.md`. | Either add the four per-view reference files and split view templates, or update `SKILL.md` to link only existing canonical files. Afterward run `scripts/sync-skills.sh --target all` and re-check drift. | Progressive disclosure, maintainability, runtime portability |
| MOD-REV-003 | Medium | Blocked-module status is inconsistent. The negative example correctly uses `blocked_pending_source`, but `SKILL.md`, `templates/module-overview.md`, `templates/view-template.md`, and `references/output-contract.md` list only draft/review/approved-style statuses. | Add blocked statuses such as `blocked_pending_source` and `blocked_pending_sme` to the output contract and templates, and state exactly when the analyzer emits a blocked overview instead of all four views. | Output contract, downstream automation |
| MOD-REV-004 | Medium | Evidence traceability is asserted but not enforceable enough in the artifact contract. Several tables use generic `Source` or `Evidence` prose, while `docs/evidence-and-knowledge-taxonomy.md` requires linked `evidence_ids`, knowledge type, confidence, and review status for approved claims. | Add required evidence columns or a per-view evidence register so every actor, event, system, interface, cross-flow dependency, data object, lifecycle claim, and rule seed can point to concrete `EV-*`, `FLOW-*`, `OBJ-*`, SME note, and TBD IDs. | Evidence integrity, SME correctness, downstream automation |
| MOD-REV-005 | Medium | Per-view review checklists are not fully materialized. `templates/view-template.md` says to see per-view checklists in `references/output-contract.md`, but the output contract mostly uses placeholders like `TBDs / Checklist / Sign-Off`; measurable per-view acceptance items live only as prose in `SKILL.md`. | Add explicit per-view checklist sections to the output contract/template, covering the View 1/2/3/4 SME questions and cross-view mapping checks. | Reviewability, SME governance |

### Strengths

- The skill has a clear layer boundary: it synthesizes approved inventory,
  program analyses, flow analyses, and BAU notes instead of re-analyzing code.
- The four-view model is well aligned with `docs/module-analysis-model.md` and
  separates business, system, program, and data concerns cleanly.
- Stop conditions are strong: missing flow analyses, ambiguous module boundary,
  missing SME scope confirmation, and missing BAU notes all block synthesis.
- Anti-hallucination language is specific and operational, especially for
  business actors, BAU rhythm, system interfaces, regulatory claims, and
  business-rule seeds.
- The negative example is valuable: it shows the analyzer refusing partial
  synthesis when a flow and SME owner are missing.
- Cross-view consistency checks create useful handoff pressure before
  `legacy-spec-writer` consumes capability seeds.

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

The skill treats SMEs as the authority for module boundaries, BAU rhythm,
manual procedures, operational exception handling, integration intent, and
approval. It also correctly keeps business rules as seeds for `legacy-spec-writer`
rather than promoting them inside the module layer.

Before field-pilot use, the output artifacts should force evidence IDs and
per-view checklist items more explicitly so SME review can reject individual
claims without relying on prose memory.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

Adapter drift check passes. The field-pilot cap remains because no runtime has
yet loaded or executed this skill through the reusable smoke-test protocol.
The broken canonical links should be fixed before running smoke tests, because
they may produce runtime-dependent behavior when an agent tries to follow the
referenced per-view files.

## Adversarial Pass

| Scenario | Expected Behavior | Result |
| --- | --- | --- |
| One in-scope flow lacks approved analysis | Stop, produce blocked overview, route to flow-analyzer | Covered by negative example |
| SME owner / BAU notes missing | Stop, do not invent Operation Flow | Covered |
| Flow belongs to multiple modules | Create SME-boundary TBD | Covered |
| Program or object inventory gap appears during aggregation | Create pending-source TBD and block as needed | Covered |
| SME says a path is dead but flow analysis found code/config evidence | Record conflict and create TBD; code wins on behavior | Covered |
| Cross-flow dependency inferred from shared file | Must trace to flow data sections / object dependencies | Covered |
| System/interface detail is absent from flow or integration docs | Create pending-source or SME TBD | Covered |
| Per-view methodology file is followed from `SKILL.md` | Currently fails because linked files do not exist | Needs hardening |
| Runtime adapter folder differs from canonical path depth | Sync strategy works structurally; smoke not run | Structurally covered |

## Requested Revision Prompt For Claude Code

```text
Revise legacy-ibmi-module-analyzer to address the following review findings.

Current score: 9.0/10 after the runtime-testing and broken-reference caps.
Target score: 9.5/10.

Blocking issues:
1. Runtime smoke prompts and three-runtime execution evidence are missing.
2. SKILL.md links nonexistent per-view reference files and a nonexistent view-template wildcard.
3. Blocked-module status values are not aligned across SKILL.md, output contract, templates, and negative example.
4. Evidence traceability is required in principle but not enforceable enough in the output artifacts.
5. Per-view review checklists are referenced but not fully specified as measurable artifact sections.

Required changes:
- Add `legacy-ibmi-module-analyzer` positive and negative prompts to `docs/runtime-smoke-tests.md`, including pass criteria for complete four-view synthesis and a missing-flow / missing-SME blocked case.
- Fix progressive-disclosure links by either adding `references/view-1-operation-flow.md` through `references/view-4-data-flow.md` plus matching templates, or updating `SKILL.md` to reference only existing `references/synthesis-rules.md`, `references/output-contract.md`, and `templates/view-template.md`.
- Add blocked statuses such as `blocked_pending_source` and `blocked_pending_sme` to the output contract and templates, and define when only `module-overview.md` should be produced.
- Add required `evidence_ids`, source/TBD references, and review-status fields or columns for module overview and all four views.
- Add measurable per-view review checklist sections to the output contract and template.
- Run `scripts/sync-skills.sh --target all`, then `scripts/sync-skills.sh --target all --check`.
- Run the smoke protocol in Codex CLI, Claude Code, and OpenCode; update `docs/runtime-matrix.md` with exact runtime/model/date notes.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-ibmi-module-analyzer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
