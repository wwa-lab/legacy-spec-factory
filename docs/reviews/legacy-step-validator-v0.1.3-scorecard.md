---
skill: legacy-step-validator
scorecard_version: v0.1.3
static_score: 9.54
decision: repo-ready
status: superseded_by_v0.1.4
superseded_by: docs/reviews/legacy-step-validator-v0.1.4-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-step-validator v0.1.3

## Change Under Review

v0.1.3 updates validation checklists for program-analyzer v0.2.1 and
flow-analyzer v0.2.1. Program validation now checks Call Evidence, source
identifier + business meaning preservation, File I/O Purpose, dynamic-call
resolution status, Error Code Inventory, Routine / Window Data Flow, and Open
Items / Limitations. Flow validation now checks Evidence Source / Resolution,
lineage preservation, File I/O Purpose propagation, and Error Code Inventory
consumption.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated checklist content
is smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-step-validator/references/validation-checklists.md`.
- Updated `skills/legacy-step-validator/SKILL.md` version history.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.3 checklist changes have not yet been
smoke-executed in Codex CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.6 | 1.15 |
| IBM i / domain correctness | 14% | 9.6 | 1.34 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.7 | 0.97 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.7 | 0.97 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.54 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| STEP-VAL-030 | Medium | v0.1.3 checklist changes have not been smoke-executed across the three target runtimes. | Run positive and blocked validations for analyzer v0.2.1 artifacts and update runtime evidence. |
