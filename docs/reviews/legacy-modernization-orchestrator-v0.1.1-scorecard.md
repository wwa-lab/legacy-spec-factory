# Skill Review Scorecard: legacy-modernization-orchestrator v0.1.1

## Metadata

- skill_name: legacy-modernization-orchestrator
- skill_path: skills/legacy-modernization-orchestrator
- reviewed_version: v0.1.1
- generated_by: Claude Code, revised by Codex for portability hardening
- reviewed_by: Codex
- review_date: 2026-05-13
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Review Evidence

- Reviewed against `docs/skill-review-gate.md`.
- Checked canonical source under `skills/legacy-modernization-orchestrator/`.
- Checked adapter copies under `.claude/`, `.opencode/`, `.agents/`, and
  `.codex/`.
- Ran `scripts/sync-skills.sh --target all`, then
  `scripts/sync-skills.sh --target all --check`; all runtime copies reported
  `OK`.
- Removed canonical-depth-dependent cross-repository links from the
  orchestrator references before scoring v0.1.1.
- Added a planned-skill manual-fallback routing example for Inventory Done to
  program analysis.
- Added `docs/runtime-smoke-tests.md` so future runtime execution checks are
  repeatable.
- Codex CLI smoke test passed with `gpt-5.4-mini`; output matched Stage 1,
  `legacy-ibmi-inventory`, and Redaction Gate pass criteria.
- Claude Code non-interactive smoke test for the same routing scenario
  produced no output before timeout. This is not counted as runtime `loaded`
  or `executed`.
- OpenCode smoke test failed during local DB startup with
  `Failed to run the query 'PRAGMA wal_checkpoint(PASSIVE)'`. This is not
  counted as runtime `loaded` or `executed`.

## Mandatory Stop Conditions

No 8.0 cap conditions found.

9.0 cap applies because:

- portability has been structurally checked and drift-tested; Codex CLI passed
  the smoke test, but loading / execution is not verified in Claude Code and
  OpenCode
- most downstream routes still target planned skills, so the manual-fallback
  chain has not been exercised end-to-end through a real Layer 2 implementation

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.6 | 0.96 |
| Workflow completeness | 12% | 9.5 | 1.14 |
| IBM i / domain correctness | 14% | 9.3 | 1.30 |
| Evidence and anti-hallucination | 12% | 9.6 | 1.15 |
| Output contract | 10% | 9.5 | 0.95 |
| Progressive disclosure | 8% | 9.6 | 0.77 |
| Runtime portability | 10% | 9.3 | 0.93 |
| Reviewability and testability | 10% | 9.5 | 0.95 |
| Engineering handoff value | 8% | 9.4 | 0.75 |
| Maintainability | 6% | 9.5 | 0.57 |

Final score before cap: **9.47 / 10**

Final score after cap: **9.0 / 10**

## Findings

### Blocking Findings

| ID | Severity | Finding | Required Change | Affects |
| --- | --- | --- | --- | --- |
| ORCH-REV-101 | P1 | Runtime copies are synced and structurally portable. Codex CLI has passed, but Claude Code and OpenCode are not yet loaded or executed. | Resolve Claude Code non-interactive timeout and OpenCode DB startup failure, then rerun `docs/runtime-smoke-tests.md` and update `docs/runtime-matrix.md` to at least `loaded`, preferably `executed` or `passed`. | Runtime portability |
| ORCH-REV-102 | P1 | The orchestrator's planned-skill routing is well specified, but the full manual-fallback chain has not been exercised through a representative capability into Layer 2 artifacts. | Walk one redacted IBM i capability from Evidence Ready through inventory, manual fallbacks, `spec.yaml`/`spec.md`, review, and forward handoff gate; capture the results as a calibration record. | Workflow completeness, downstream automation |

### Improvement Findings

No non-blocking improvement findings remain after the v0.1.1 hardening pass.

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

Notes:

The orchestrator keeps IBM i SMEs as the approval authority and blocks unsafe
downstream movement on redaction, inventory coverage, evidence approval, and
forward handoff gates. The skill is especially strong on refusing stage skips
that would turn missing artifacts into invented business rules.

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter or copy defined if needed
- [x] OpenCode adapter or copy defined if needed
- [x] Codex adapter or copy defined if needed
- [x] runtime-specific metadata isolated from canonical skill

Notes:

The v0.1.1 pass fixed cross-repository links that were correct from the
canonical skill directory but fragile after syncing into runtime adapter
folders. Adapter drift check now passes. Codex CLI passed the routing smoke
test. The remaining runtime gaps are Claude Code and OpenCode execution, not
file layout.

## Adversarial Pass

| Scenario | Expected Behavior | Result |
| --- | --- | --- |
| Raw evidence with unknown sensitivity | Stop at Redaction Gate | Covered |
| Inventory with blocking coverage gaps | Stop at Inventory Completeness Gate and list TBD IDs | Covered |
| User asks to skip from draft spec to forward SDLC | Refuse skip; require review, approval, and Forward Handoff Gate | Covered |
| Planned downstream skill selected | State `Planned` clearly and provide manual fallback | Covered |
| Mixed-stage artifacts with incomplete upstream coverage | Classify current stage as earliest unmet stage | Covered |

## Requested Revision Prompt For Claude Code

```text
Revise legacy-modernization-orchestrator to address the remaining 9.5 blockers.

Target score: 9.5/10.

Blocking issues:
1. Runtime copies are synced, and Codex CLI has passed, but Claude Code and
   OpenCode have not loaded/executed successfully.
2. Planned-skill manual fallback routing has not been exercised through a
   representative capability into Layer 2 artifacts.

Required changes:
- Run the smoke tests in docs/runtime-smoke-tests.md and update
  docs/runtime-matrix.md with loaded/executed status and notes.
- Capture one end-to-end manual fallback walk from Evidence Ready to draft
  spec package once the representative artifacts are available, and save it as
  a calibration record.

Do not remove author/copyright notices.
Keep the canonical skill under skills/legacy-modernization-orchestrator/.
Maintain compatibility with Codex, Claude Code, and OpenCode.
```
