# Skill Review Scorecard

## Metadata

- skill_name: legacy-ibmi-program-analyzer
- skill_path: skills/legacy-ibmi-program-analyzer/
- reviewed_version: v0.2.23
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

No mandatory stop condition applies. The retained-batch workflow now enforces
source-backed semantic completion, evidence governance, synchronized YAML
review surfaces, bounded batches, and terminal validation.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.8 | 0.98 |
| Workflow completeness | 12% | 9.9 | 1.188 |
| IBM i / domain correctness | 14% | 9.8 | 1.372 |
| Evidence and anti-hallucination | 12% | 9.8 | 1.176 |
| Output contract | 10% | 9.9 | 0.99 |
| Progressive disclosure | 8% | 9.3 | 0.744 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.7 | 0.97 |
| Engineering handoff value | 8% | 9.9 | 0.792 |
| Maintainability | 6% | 9.2 | 0.552 |

Raw weighted score: **9.66 / 10**.

Final score: **9.0 / 10**, capped pending successful Windows PowerShell 5.1
execution and three-runtime smoke evidence.

## Findings

### Blocking Findings

None for repository integration.

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| IMP-001 | The new PowerShell semantic parity fixtures are skipped on the macOS development host because no PowerShell runtime is installed. | Require the Windows PowerShell 5.1 CI job to pass before field pilot. |
| IMP-002 | Codex, Claude Code, and OpenCode execution smoke evidence has not yet been recorded for v0.2.23. | Run `docs/runtime-smoke-tests.md` for all three runtimes before field pilot. |
| IMP-003 | `ProgramAnalysisContract.Common.psm1` is 638 lines and `ProgramAnalysisContract.Validation.psm1` is 773 lines. | Extract a semantic-validation module before the next substantial rule expansion. |

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

The canonical and four runtime copies pass the repository drift check. Static
inspection and Python tests cover the Python/PowerShell contract parity, but
field-pilot approval remains blocked until the native Windows tests and all
three runtime smoke tests pass.
