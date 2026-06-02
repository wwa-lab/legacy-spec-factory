---
skill: legacy-spec-writer
scorecard_version: v0.1.6
static_score: 9.49
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-spec-writer v0.1.6

## Change Under Review

v0.1.6 aligns spec synthesis with program-analyzer v0.2.4 routine-local
evidence. Observed behaviors, data model fields, outputs, and exceptions now
preserve Routine Logic Details, routine-local carrier/lineage rows, and
routine-local exception closure.

## Decision

**Repo-ready, runtime smoke pending.**

The published score remains capped at 9.0 until the updated spec-writing
contract is smoke-executed in all three target runtimes.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-spec-writer/SKILL.md`.
- Updated `references/synthesis-rules.md`.
- Ran sync, skill-claim, Markdown table, and whitespace checks.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.6 has not yet been smoke-executed across Codex
CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.5 | 0.95 |
| Workflow completeness | 12% | 9.6 | 1.15 |
| IBM i / domain correctness | 14% | 9.6 | 1.34 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.7 | 0.97 |
| Progressive disclosure | 8% | 9.1 | 0.73 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.8 | 0.98 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.4 | 0.56 |

Final score before cap: **9.49 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| SPEC-REV-040 | Medium | v0.1.6 routine-local evidence synthesis has not been smoke-executed across the three target runtimes. | Run spec smoke with approved module/flow/program evidence that includes routine-local carrier and exception rows. |
