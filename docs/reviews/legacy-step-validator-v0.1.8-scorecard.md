---
skill: legacy-step-validator
scorecard_version: v0.1.8
static_score: 9.60
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-step-validator v0.1.8

## Change Under Review

v0.1.8 aligns validation with program-analyzer v0.2.5. Program-analysis
validation now treats missing conditioned calculation block rows or missing
outcome reverse trace rows as blocking when material guarded calculations
affect money, percentage, quantity, status, return values, message/error codes,
persisted fields, display/report fields, queue payloads, or downstream
branches.
It also requires the current program-analysis artifact to place `Validation
Logic` immediately after `Routine Logic Details` and before `Deep Read
Windows`.

## Decision

**Repo-ready, updated smoke pending.**

The checklist is precise enough for repository use. The published score remains
capped at 9.0 until validator smoke includes positive and blocked fixtures for
conditioned calculation block, outcome reverse-trace coverage, and front-loaded
Validation Logic coverage.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated validation checklist and skill version history.
- Synced runtime adapters.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.8 validator smoke has not yet been executed in
Codex CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.6 | 1.15 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.6 | 0.96 |
| Progressive disclosure | 8% | 9.4 | 0.75 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.9 | 0.99 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.5 | 0.57 |

Final score before cap: **9.60 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| STEP-VAL-080 | Medium | v0.1.8 conditioned calculation block, outcome reverse-trace, and front-loaded Validation Logic validation has not been smoke-executed across the three target runtimes. | Run positive and blocked validations against program-analysis artifacts that include or omit conditioned calculation block rows, reverse trigger links, and the required Validation Logic placement for a material guard-scoped calculation chain. |
