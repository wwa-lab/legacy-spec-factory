---
skill: legacy-spec-writer
scorecard_version: v0.1.4
static_score: 9.45
decision: repo-ready
status: superseded
last_verified: 2026-06-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-01 }
  claude_code: { status: synced, model: haiku, date: 2026-06-01 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-01 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-spec-writer v0.1.4

## Change Under Review

v0.1.4 aligns spec synthesis with analyzer v0.2.0. The spec writer now prefers
module / flow / program replay, field-lineage, persistence, and exception-chain
evidence when deriving observed behaviors, outputs, data model fields, and
exceptions.

## Decision

**Repo-ready, runtime smoke pending.**

The change strengthens downstream evidence preservation without changing
`schemas/spec.schema.yaml`. Runtime smoke remains required before field-pilot
readiness because v0.1.4 changes source selection for core spec fields.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated `skills/legacy-spec-writer/SKILL.md`.
- Updated `skills/legacy-spec-writer/references/synthesis-rules.md`.
- Ran adapter sync and drift checks on 2026-06-01.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because v0.1.4 has not been smoke-executed across Codex CLI,
Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.5 | 0.95 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.4 | 1.32 |
| Evidence and anti-hallucination | 12% | 9.7 | 1.16 |
| Output contract | 10% | 9.4 | 0.94 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.4 | 0.94 |
| Engineering handoff value | 8% | 9.7 | 0.78 |
| Maintainability | 6% | 9.6 | 0.58 |

Final score before cap: **9.45 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| SPEC-REV-020 | Medium | v0.1.4 has not yet been smoke-executed using analyzer v0.2.0 upstream evidence. | Run positive and negative spec-writing smoke with BRD-approved replay / lineage / persistence / exception-chain evidence. |
