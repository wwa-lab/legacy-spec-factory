---
skill: legacy-step-validator
scorecard_version: v0.1.2
static_score: 9.52
decision: repo-ready
status: superseded
last_verified: 2026-06-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-01 }
  claude_code: { status: synced, model: haiku, date: 2026-06-01 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-01 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-step-validator v0.1.2

## Change Under Review

v0.1.2 updates validation checklists for analyzer v0.2.0 contracts. Program
validation now checks key file/field logic, field-level File I/O mutation, and
complete exception closure. Flow validation now checks replay, field lineage,
persistence, and exception chains. Module validation now checks module
readiness summaries and BRD-first handoff coverage.

## Decision

**Repo-ready, runtime smoke pending.**

The prior v0.1.1 runtime smoke evidence remains valid for the validator
framework, but not for the new analyzer v0.2.0 checklist content. The published
score is therefore capped at 9.0 until the updated positive and blocked module
/ flow / program validation cases run across all three runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-step-validator/references/validation-checklists.md`.
- Ran adapter sync and drift checks on 2026-06-01.
- Updated runtime smoke prompts to match analyzer v0.2.0 contracts.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies:

- v0.1.2 has not been smoke-executed in Codex CLI, Claude Code, and OpenCode
- old v0.1.1 field-pilot status is superseded because the checklist contract
  changed materially

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.5 | 1.33 |
| Evidence and anti-hallucination | 12% | 9.7 | 1.16 |
| Output contract | 10% | 9.7 | 0.97 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.6 | 0.96 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.52 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| STEP-VAL-020 | Medium | v0.1.2 checklist changes have not been smoke-executed across the three target runtimes. | Run positive and blocked validations for analyzer v0.2.0 artifacts and update runtime evidence. |
