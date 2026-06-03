---
skill: legacy-flow-context-normalizer
scorecard_version: v0.1.12
static_score: 9.50
decision: repo-ready (retired)
status: superseded
last_verified: 2026-06-03
runtimes_tested:
  codex: { status: synced, model: gpt-5.4-mini, date: 2026-06-03 }
  claude_code: { status: synced, model: haiku, date: 2026-06-03 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-06-03 }
evidence_source: static review + adapter drift checks; retired from active skill surface on 2026-06-03
---

# Skill Review Scorecard: legacy-flow-context-normalizer v0.1.12

## Change Under Review

v0.1.12 recasts flow normalization as evidence-bounded elicitation and coverage.
The skill may organize source fragments into four-view coverage, gaps, and SME
questions, but it must not generate missing flow logic or BRD-ready facts.

## Decision

**Repo-ready (provisional), runtime smoke pending.**

The direction lowers hallucination risk by preventing generated/candidate
context from becoming approved flow or BRD content.

## Review Notes

| Category | Score | Notes |
| --- | ---: | --- |
| Purpose and trigger clarity | 9.6 | Clear shift from flow generation to coverage and questions. |
| Evidence and anti-hallucination | 9.8 | Explicitly forbids BRD fact promotion from AI-organized context. |
| Output contract | 9.4 | Existing package shape preserved; semantics tightened. |
| Runtime portability | 9.0 | Adapter sync required; execution smoke pending. |
| Maintainability | 9.5 | Keeps helper scripts and templates while changing behavior contract. |

**Final score:** 9.50 / 10. Current score capped at 9.0 until runtime smoke.
