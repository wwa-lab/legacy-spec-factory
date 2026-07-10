# Skill Review Scorecard

## Metadata

- skill_name: legacy-ibmi-flow-analyzer
- skill_path: skills/legacy-ibmi-flow-analyzer/
- reviewed_version: v0.2.10
- generated_by: Codex
- reviewed_by: Codex
- review_date: 2026-07-10
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

No mandatory stop condition applies. Reader-first output, evidence strength,
SME control, program identity, source-inventory freshness, and downstream
handoff rules remain explicit and enforceable.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 10.0 | 1.00 |
| Workflow completeness | 12% | 9.4 | 1.13 |
| IBM i / domain correctness | 14% | 9.7 | 1.36 |
| Evidence and anti-hallucination | 12% | 10.0 | 1.20 |
| Output contract | 10% | 9.5 | 0.95 |
| Progressive disclosure | 8% | 8.7 | 0.70 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.4 | 0.94 |
| Engineering handoff value | 8% | 9.6 | 0.77 |
| Maintainability | 6% | 9.0 | 0.54 |

Raw weighted score: 9.48 / 10.

Final score: **9.0 / 10**, capped pending successful Windows PowerShell 5.1
runtime execution in CI/Cline.

## Findings

### Blocking Findings

None for repository integration.

### Improvement Findings

| ID | Finding | Suggested Change |
| --- | --- | --- |
| IMP-001 | Native builder, validator, routing, and parity cases are skipped on the macOS development host. | Require the Windows CI job and company Cline smoke test to pass before field pilot. |
| IMP-002 | The native YAML reader deliberately supports the deterministic block-style subset used by repository profiles and generated manifests, not the full YAML language. | Keep flow profiles within the documented subset or use Python/PyYAML for advanced YAML features. |
| IMP-003 | A missing, stale, or dirty repository inventory still needs the separate Python-based inventory scanner. | Port `legacy-ibmi-inventory` separately; until then, retain `blocked_pending_inventory_runtime` instead of treating stale evidence as fresh. |
| IMP-004 | Git freshness parity focuses on clean/fresh fixtures. | Add Windows cases for dirty, stale, non-Git, and Git-command failure states before field pilot. |

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
- [x] runtime-specific behavior implemented as portable repository scripts

The native builder and validator require only Windows PowerShell 5.1 and
built-in .NET APIs. The shared launcher preserves `py -3`, `python`, then
native PowerShell routing, including the Python `build` and `validate`
subcommands. Program identity remains case-sensitive when a custom profile does
not request uppercase normalization.
