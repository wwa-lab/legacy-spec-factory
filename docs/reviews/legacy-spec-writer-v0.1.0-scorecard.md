# Skill Review Scorecard: legacy-spec-writer v0.1.0

## Metadata

- skill_name: legacy-spec-writer
- skill_path: skills/legacy-spec-writer
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
- Checked canonical source under `skills/legacy-spec-writer/`.
- Checked `SKILL.md`, `references/`, `templates/`, `examples/spec-positive/`,
  `schemas/spec.schema.yaml`, `docs/forward-sdlc-contract.md`,
  `docs/evidence-and-knowledge-taxonomy.md`, and
  `docs/runtime-smoke-tests.md`.
- Ran `scripts/sync-skills.sh --target all --check`; all runtime adapter copies
  reported `OK`.
- Ran `python3 scripts/check-spec-contract.py`; spec contract alignment passed
  for the root `templates/spec.yaml` and `schemas/spec.schema.yaml`.
- Parsed `skills/legacy-spec-writer/templates/spec.yaml`,
  `skills/legacy-spec-writer/examples/spec-positive/spec.yaml`,
  `templates/spec.yaml`, and `schemas/spec.schema.yaml` as YAML; all parsed.
- Checked `docs/runtime-matrix.md`; `legacy-spec-writer` is still `synced` in
  Codex, Claude Code, and OpenCode, not `loaded`, `executed`, or `passed`.
- Checked `docs/runtime-smoke-tests.md`; no `legacy-spec-writer` prompt has
  been added yet, so the reusable smoke protocol cannot be run verbatim for
  this skill.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies under the review gate:

- portability has been considered and adapter drift has been checked, but the
  skill has not been loaded or executed in Codex CLI, Claude Code, and OpenCode
- the runtime-smoke-test prompt set does not yet include `legacy-spec-writer`
- several validation gates are described in prose but are not yet represented
  in the schema/template/script contract strongly enough to be enforceable

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.5 | 0.95 |
| Workflow completeness | 12% | 9.4 | 1.13 |
| IBM i / domain correctness | 14% | 9.2 | 1.29 |
| Evidence and anti-hallucination | 12% | 9.5 | 1.14 |
| Output contract | 10% | 9.1 | 0.91 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 8.8 | 0.88 |
| Engineering handoff value | 8% | 9.3 | 0.74 |
| Maintainability | 6% | 9.3 | 0.56 |

Final score before cap: **9.24 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

### Blocking For 9.5

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| SPEC-REV-001 | High | Runtime portability is structurally clean but not tested. `docs/runtime-matrix.md` records this skill as `synced` only, and `docs/runtime-smoke-tests.md` has no positive or negative prompt for it. | Add `legacy-spec-writer` smoke prompts and pass criteria, run the protocol in Codex CLI, Claude Code, and OpenCode, then update `docs/runtime-matrix.md` and this scorecard. | Runtime portability, reviewability |
| SPEC-REV-002 | High | The skill says no AC may be generated for a draft or `needs_sme_review` BR, but the skill-local `templates/spec.yaml` includes an `acceptance_criteria` item validating the placeholder BR while that BR is marked `review_status: needs_sme_review`. | Change the template so `acceptance_criteria: []` by default, or mark the placeholder BR as `approved` only inside an explicitly approved example block. Add a template comment saying ACs are emitted only after BR approval. | Evidence integrity, anti-hallucination |
| SPEC-REV-003 | High | The forward-handoff gate requires checking that no data-model field has `evidence_strength: missing`, but `schemas/spec.schema.yaml` and the skill-local template do not define `evidence_strength` or `review_status` at `data_model.entities[].fields[]`. The gate is therefore not machine-checkable from `spec.yaml`. | Add field-level evidence status or an equivalent evidence-derived validation rule to the schema, templates, example, and contract checker. Alternatively rewrite the gate to validate only through linked `evidence[]` records and make the checker enforce that link. | Output contract, downstream automation |
| SPEC-REV-004 | Medium | `spec-review.md` and `traceability.md` are required outputs, but only `spec.yaml` and `spec.md` have templates. The positive example shows good shape, but field users and runtimes do not have canonical starting files for two required artifacts. | Add `templates/spec-review.md` and `templates/traceability.md`; link them from `SKILL.md`; update examples if needed. | Reviewability, SME governance |
| SPEC-REV-005 | Medium | `scripts/check-spec-contract.py` validates the root `templates/spec.yaml`, while `legacy-spec-writer` instructs users to start from `skills/legacy-spec-writer/templates/spec.yaml`. Drift between the actual skill template and the checked root template can pass unnoticed. | Either make the checker validate the skill-local template, or make `SKILL.md` explicitly point to the root template and keep only one canonical spec template. | Maintainability, output contract |
| SPEC-REV-006 | Medium | The positive traceability example marks the "No blocking TBD without SME waiver" row as `[X]` while the text says `NO` and identifies an unresolved blocking TBD. | Change the checkbox to unchecked or split pass/fail rows so the example cannot be read as approving a blocked handoff. | Reviewability, downstream automation |

### Strengths

- The skill has excellent layer discipline: it consumes approved inventory,
  module, flow, and program analyses instead of re-reading IBM i source or
  jumping directly to Java/cloud code.
- The rule-extraction protocol is strong and appropriately conservative:
  Class A/B/C/D handling keeps observed behavior, inferred business rules, SME
  approval, and speculation separate.
- Anti-hallucination guidance is concrete and operational, especially around
  not inventing BRs, data field semantics, target architecture, ACs, or hidden
  TBD resolution.
- The output package is the right handoff shape for forward SDLC:
  `spec.yaml`, `spec.md`, `spec-review.md`, and `traceability.md`.
- The positive example is realistic and demonstrates the correct `in_review`
  posture when a BR and modernization decision remain unresolved.

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

SME control is one of this skill's strongest areas. The skill requires a named
capability owner, blocks rule approval without SME confirmation, separates
observed behaviors from BRs and DECs, and keeps unresolved ambiguity in
`TBD-*` records. Before field-pilot use, the templates and schema need to
mirror that discipline so agents do not accidentally generate ACs or handoff
checks that the prose forbids.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

Adapter drift check passes. The field-pilot cap remains because no runtime has
yet loaded or executed this skill through the reusable smoke-test protocol.

## Adversarial Pass

| Scenario | Expected Behavior | Result |
| --- | --- | --- |
| Module analysis is not approved | Stop and route back to module analyzer | Covered |
| Capability seed has blocking TBDs | Stop and require clarification | Covered |
| No capability owner SME exists | Stop; BRs cannot move beyond draft | Covered |
| Evidence has `sensitive: unknown` | Stop for redaction review | Covered |
| BR candidate has no SME confirmation | Keep as `needs_sme_review`; do not generate AC | Covered in prose; template needs alignment |
| AC validates a draft or unapproved BR | Flag as orphan/invalid; remove or block | Covered in prose; template currently violates |
| Data model field lacks evidence | Create field-level TBD / block handoff | Covered in prose; schema/template do not expose enough structure |
| Blocking TBD remains at handoff | Spec remains `in_review`; no forward SDLC handoff | Covered; example checkbox needs correction |
| Runtime adapter folder differs from canonical path depth | Should keep relative links portable after sync | Structurally covered; smoke not run |

## Requested Revision Prompt For Claude Code

```text
Revise legacy-spec-writer to address the following review findings.

Current score: 9.0/10 after the runtime-testing and enforceability cap.
Target score: 9.5/10.

Blocking issues:
1. Runtime smoke prompts and three-runtime execution evidence are missing.
2. The skill-local spec.yaml template generates an AC for a BR marked
   needs_sme_review, contradicting the anti-hallucination rules.
3. The forward-handoff data-model evidence gate is not represented in
   schemas/spec.schema.yaml or the skill-local template.
4. Required outputs spec-review.md and traceability.md lack templates.
5. Contract checking validates the root template but not the skill-local
   template used by this skill.

Required changes:
- Add legacy-spec-writer positive and negative prompts to
  docs/runtime-smoke-tests.md, including pass criteria for a valid in-review
  spec and a blocked case with unapproved BRs or sensitive unknown evidence.
- Run the smoke protocol in Codex CLI, Claude Code, and OpenCode; update
  docs/runtime-matrix.md with exact runtime/model/date notes.
- Change skills/legacy-spec-writer/templates/spec.yaml so ACs are empty by
  default unless the validated BR is approved; add comments reinforcing that
  ACs are generated only for approved BRs.
- Add enforceable data-model field evidence handling to schemas/spec.schema.yaml,
  templates, examples, and the contract checker, or rewrite the gate so it can
  be checked from linked evidence records.
- Add templates/spec-review.md and templates/traceability.md under
  skills/legacy-spec-writer/templates/ and link them from SKILL.md.
- Align scripts/check-spec-contract.py with the actual skill-local template or
  consolidate the root and skill-local spec templates into one canonical source.
- Fix the positive traceability example checkbox for unresolved blocking TBDs.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-spec-writer/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
