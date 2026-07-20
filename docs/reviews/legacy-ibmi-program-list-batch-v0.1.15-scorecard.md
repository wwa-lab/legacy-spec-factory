# Skill Review Scorecard

## Metadata

- skill_name: legacy-ibmi-program-list-batch
- skill_path: skills/legacy-ibmi-program-list-batch/
- reviewed_version: v0.1.15
- generated_by: Codex
- reviewed_by: Codex multi-agent review
- review_date: 2026-07-20
- target_runtime:
  - [x] Codex
  - [x] Claude Code
  - [x] OpenCode
- decision:
  - [ ] reject
  - [ ] revise
  - [x] repo-ready
  - [ ] field-pilot ready

## Mandatory Stop Conditions

No mandatory stop condition applies. The generated per-program prompt now
requires every retained deep-read batch to be completed, persisted, mirrored
into both YAML collections, consolidated, and validated before closure.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.7 | 0.97 |
| Workflow completeness | 12% | 9.8 | 1.176 |
| IBM i / domain correctness | 14% | 9.4 | 1.316 |
| Evidence and anti-hallucination | 12% | 9.5 | 1.14 |
| Output contract | 10% | 9.7 | 0.97 |
| Progressive disclosure | 8% | 9.4 | 0.752 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.7 | 0.97 |
| Engineering handoff value | 8% | 9.8 | 0.784 |
| Maintainability | 6% | 9.4 | 0.564 |

Raw weighted score: **9.54 / 10**.

Final score: **9.0 / 10**, capped pending successful Windows PowerShell 5.1
execution and three-runtime smoke evidence.

## Findings

### Blocking Findings

None for repository integration.

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| IMP-001 | The new PowerShell batch-status parity fixtures are skipped on the macOS development host because no PowerShell runtime is installed. | Require the Windows PowerShell 5.1 CI job to pass before field pilot. |
| IMP-002 | Codex, Claude Code, and OpenCode execution smoke evidence has not yet been recorded for v0.1.15. | Run `docs/runtime-smoke-tests.md` for all three runtimes before field pilot. |
| IMP-003 | The corrected multi-batch loop has not yet been exercised in the company Cline environment with an SS380-sized program. | Run a `001 -> 002 -> 003 -> consolidation -> terminal validation` field scenario before field pilot. |

## SME Review

- [x] SME governance is explicit
- [x] Observed behavior, inferred rule, and modernization decision are separate
- [x] Evidence tags are required
- [x] IBM i-specific failure modes are covered
- [x] Open questions / TBDs are carried forward instead of hidden

## Runtime Portability Review

- [x] canonical source under `skills/<skill-name>/`
- [x] Claude Code adapter synced
- [x] OpenCode adapter synced
- [x] Codex adapter synced
- [x] `.agents` adapter synced
- [x] runtime-specific metadata isolated from canonical skill

The canonical and four runtime copies pass the repository drift check. The
workflow and validators are repository-ready; field-pilot approval remains
blocked until Windows runtime, three-runtime smoke, and company Cline evidence
are recorded.
