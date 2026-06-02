---
skill: legacy-ibmi-program-analyzer
scorecard_version: v0.2.5
static_score: 9.66
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-program-analyzer v0.2.5

## Change Under Review

v0.2.5 tightens `Routine Logic Details` so material guard-scoped calculation
chains and final message/status outcomes are not lost. RPG fixed-format
conditioning indicators, named condition groups such as `Condition 5`,
IF/ELSE, CASE, loop-guarded calculations, and equivalent guarded chains now
require a `Conditioned calculation blocks` row. Material message/status/error
outcomes also require an outcome reverse trace from the visible code back to
the branch guard, comparison threshold, intermediate variables, source
operands/carriers, final output or error effect, source range, and evidence.
The former error/status code inventory is now the front-loaded `Validation
Logic` section placed immediately after `Routine Logic Details`.

## Decision

**Repo-ready, runtime smoke pending.**

The static contract closes the observed SR120 gap, but the published score
remains capped at 9.0 until three-runtime smoke covers a conditioned
calculation and outcome reverse-trace fixture.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated canonical program analyzer instructions, output contract, template,
  and examples.
- Added validator coverage for conditioned calculation blocks, outcome reverse
  traces, and front-loaded `Validation Logic`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.2.5 conditioned-calculation and outcome
reverse-trace smoke has not yet been executed in Codex CLI, Claude Code, and
OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.8 | 0.98 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.8 | 1.37 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.8 | 0.98 |
| Progressive disclosure | 8% | 9.4 | 0.75 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.8 | 0.98 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.66 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| PROG-REV-070 | Medium | v0.2.5 conditioned calculation block, outcome reverse-trace, and front-loaded Validation Logic coverage has not been smoke-executed across the three target runtimes. | Run program analyzer smoke with a fixed-format RPG fixture containing a named condition group, chained amount/percentage calculations, intermediate variables, and an error/message outcome whose trigger chain must be traced backward into a front-loaded Validation Logic row. |
