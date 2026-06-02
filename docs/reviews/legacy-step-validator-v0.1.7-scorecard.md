---
skill: legacy-step-validator
scorecard_version: v0.1.7
static_score: 9.59
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-step-validator v0.1.7

## Change Under Review

v0.1.7 tightens downstream validation for program-analyzer v0.2.4 consumption.
Flow validation now checks that Cross-Program Field Lineage consumes
routine-local carrier rows where available and Exception Propagation Chain
consumes routine-local exception closure.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated checklist content
is smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-step-validator/references/validation-checklists.md`.
- Updated `skills/legacy-step-validator/SKILL.md` version history.
- Ran sync, skill-claim, Markdown table, and whitespace checks.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.7 checklist changes have not yet been
smoke-executed in Codex CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.9 | 0.99 |
| Engineering handoff value | 8% | 10.0 | 0.80 |
| Maintainability | 6% | 9.7 | 0.58 |

Final score before cap: **9.59 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| STEP-VAL-070 | Medium | v0.1.7 downstream routine-local evidence validation has not been smoke-executed across the three target runtimes. | Run positive and blocked validations against flow artifacts that include or omit routine-local carrier/exception consumption. |
