---
skill: legacy-spec-writer
scorecard_version: v0.1.5
static_score: 9.47
decision: repo-ready
status: current
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-spec-writer v0.1.5

## Change Under Review

v0.1.5 aligns spec synthesis inputs with analyzer v0.2.1 evidence. It preserves
edge Evidence Source / Resolution, source identifier + business meaning fields,
File I/O Purpose, Error Code Inventory, and exception-chain evidence when
lifting observed behaviors, outputs, data fields, and exceptions into
`spec.yaml` and `spec.md`.

## Decision

**Repo-ready, runtime smoke pending.**

The static contract is repo-ready, but the published score remains capped at
9.0 until v0.1.5 is smoke-executed in Codex CLI, Claude Code, and OpenCode.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-spec-writer/SKILL.md`.
- Updated `skills/legacy-spec-writer/references/synthesis-rules.md`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.5 three-runtime smoke evidence is pending.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.5 | 0.95 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.4 | 1.32 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.18 |
| Output contract | 10% | 9.6 | 0.96 |
| Progressive disclosure | 8% | 9.4 | 0.75 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.5 | 0.95 |
| Engineering handoff value | 8% | 9.8 | 0.78 |
| Maintainability | 6% | 9.3 | 0.56 |

Final score before cap: **9.47 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| SPEC-REV-030 | Medium | v0.1.5 has not yet been smoke-executed across Codex, Claude Code, and OpenCode. | Run positive and negative spec-writing smoke and update runtime evidence. |

