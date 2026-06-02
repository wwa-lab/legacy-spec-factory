---
skill: legacy-ibmi-flow-analyzer
scorecard_version: v0.2.1
static_score: 9.60
decision: repo-ready
status: superseded_by_v0.2.2
superseded_by: docs/reviews/legacy-ibmi-flow-analyzer-v0.2.2-scorecard.md
last_verified: 2026-06-02
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-02 }
  claude_code: { status: synced, model: haiku, date: 2026-06-02 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-02 }
evidence_source: docs/runtime-matrix.md
---

# Skill Review Scorecard: legacy-ibmi-flow-analyzer v0.2.1

## Change Under Review

v0.2.1 aligns flow analysis with program-analyzer v0.2.1. It requires flow
outputs to consume and preserve upstream Call Evidence, dynamic-call resolution
status, source identifier + business meaning fields, File I/O Purpose, Error
Code Inventory, Routine / Window Data Flow, and Open Items / Limitations.

## Decision

**Repo-ready, runtime smoke pending.**

The static contract is field-pilot quality, but the published score remains
capped at 9.0 until Codex, Claude Code, and OpenCode smoke execution evidence is
recorded for v0.2.1.

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Updated canonical files under `skills/legacy-ibmi-flow-analyzer/`.
- Updated the flow template, output contract, data-flow/error references, and
  positive batch/menu examples.
- Runtime adapters are expected to be refreshed with `scripts/sync-skills.sh`
  and drift-checked before release.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap still applies because v0.2.1 has not yet been smoke-executed in
Codex CLI, Claude Code, and OpenCode.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.8 | 1.18 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 9.9 | 1.19 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.2 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.7 | 0.97 |
| Engineering handoff value | 8% | 9.9 | 0.79 |
| Maintainability | 6% | 9.4 | 0.56 |

Final score before cap: **9.60 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready, not field-pilot ready**

## Findings

| ID | Severity | Finding | Required Change |
| --- | --- | --- | --- |
| FLOW-REV-030 | Medium | v0.2.1 has not yet been smoke-executed across the three target runtimes. | Run positive and negative no-write flow smoke and update runtime evidence. |

## Improvements Completed In v0.2.1

| ID | Finding | Change Made |
| --- | --- | --- |
| FLOW-REV-031 | Flow edges could discard upstream call-resolution status. | Added Evidence Source and Resolution to edge tables. |
| FLOW-REV-032 | Cross-program data/lineage could collapse field identity into prose. | Required `FIELD_NAME` / `VARIABLE_NAME` plus business meaning preservation. |
| FLOW-REV-033 | Flow persistence could lose why a file/object is accessed. | Added Purpose propagation from program File I/O. |
| FLOW-REV-034 | Error propagation could ignore program Error Code Inventory. | Updated exception-chain requirements to carry error type, output carrier, and evidence status. |
