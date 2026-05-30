---
skill: legacy-brd-writer
scorecard_version: v0.1.6
static_score: 9.48
decision: repo-ready
status: current
last_verified: 2026-05-30
runtimes_tested:
  codex: { status: synced, model: gpt-5.4, date: 2026-05-30 }
  claude_code: { status: synced, model: haiku, date: 2026-05-30 }
  opencode: { status: synced, model: minimax-m2.5-free, date: 2026-05-30 }
evidence_source: static review + adapter drift checks
---

# Skill Review Scorecard: legacy-brd-writer v0.1.6

## Review Focus

v0.1.6 reframes BRD writer as the primary legacy-system discovery artifact. The
BRD records old-system behavior, evidence, SME review, scenario seeds, and
traceability without old-vs-new comparison, target requirements, or SDD handoff
content.

## Decision

**Repo-ready, runtime smoke pending.**

The skill preserves the strong evidence and SME review discipline from v0.1.5
while correcting the stage boundary: an approved BRD is a discovery baseline,
not an automatic spec-writing trigger.

## Blocking For Field Pilot

Run three-runtime positive and negative smoke prompts covering:

- legacy BRD generation with no comparison input
- refusal to add No-gap / Gap1 / Gap2 disposition notes to the BRD Package
- refusal to convert legacy discovery findings into `AC-*`, `DEC-*`,
  implementation tasks, or SDD handoff content

## Static Review Notes

| Category | Score | Notes |
| --- | ---: | --- |
| Purpose and trigger clarity | 9.7 | Clear discovery-first trigger and explicit NOT-to-use conditions for SDD handoff / target-scope decisions. |
| Workflow completeness | 9.5 | Keeps required BRD sections 1-9 intact and makes old-vs-new disposition explicitly post-BRD. |
| Evidence and anti-hallucination | 9.6 | Prevents legacy discovery findings from becoming target requirements without a later gate. |
| Output contract | 9.4 | Four-file BRD package remains stable and legacy-system-only. |
| Runtime portability | 9.3 | Canonical source remains portable; adapter sync pending execution smoke. |

**Final score:** 9.48 / 10.
