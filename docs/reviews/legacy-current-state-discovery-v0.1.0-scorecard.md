---
skill: legacy-current-state-discovery
scorecard_version: v0.1.0
static_score: 9.12
decision: repo-ready (provisional)
status: current
last_verified: 2026-07-01
runtimes_tested:
  codex: { status: synced, model: gpt-5.4, date: 2026-07-01 }
  claude_code: { status: synced, model: not-run, date: 2026-07-01 }
  opencode: { status: synced, model: not-run, date: 2026-07-01 }
evidence_source: static review + quick_validate + local validator smoke + adapter drift checks
---

# Skill Review Scorecard: legacy-current-state-discovery v0.1.0

## Change Under Review

New document-first current-state discovery skill. It converts selected RAG or
document evidence, SME prompts, spreadsheets, and project folders into an
evidence-backed current-state functional discovery package. The package
contains both structured catalogs and an SME/BA-facing functional discovery
report.

The skill explicitly separates:

- document-first current-state extraction,
- project-derived features,
- code-grounded follow-up work for IBM i program/flow analyzers, and
- final handoff generation.

## Decision

**Repo-ready provisional, not field-pilot ready.**

The skill is structurally sound, portable, synced to runtime adapter folders,
and locally validated. The score remains capped at 9.0 for published use until
the team adds a filled golden output sample, runs one document-first pilot, runs
one code-grounded follow-up pilot, and completes three-runtime smoke execution.

Static score before cap: **9.12 / 10**

Current score after cap: **9.0 / 10**

## Review Evidence

- Created canonical skill under `skills/legacy-current-state-discovery/`.
- Added `SKILL.md` with explicit boundaries for RAG/document extraction,
  code-grounded analysis, SME review, and final output generation.
- Added references:
  - `output-contract.md`
  - `evidence-confidence-rules.md`
  - `document-vs-code-routing.md`
- Added templates for the full discovery package:
  - `discovery-index.yaml`
  - `document-master-index.md`
  - `functional-discovery-report.md`
  - `function-catalog.yaml`
  - `project-derived-feature-index.yaml`
  - `validation-catalog.yaml`
  - `calculation-catalog.yaml`
  - `interface-register.yaml`
  - `channel-ui-report-catalog.md`
  - `accounting-gl-ie-index.yaml`
  - `traceability-matrix.csv`
  - `open-questions-and-gaps.md`
- Added standard-library validator:
  - `scripts/validate_current_state_discovery_package.py`
- Synced runtime adapters to `.claude/skills/`, `.opencode/skills/`,
  `.agents/skills/`, and `.codex/skills/`.

## Mandatory Stop Conditions

No mandatory 8.0 cap conditions found.

A 9.0 cap applies because:

- no filled expected output / golden sample exists yet,
- no real RAG document pilot has been reviewed by an SME,
- no code-grounded follow-up pilot has been run through existing IBM i analyzers,
- three-runtime execution smoke has not been completed.

## Weighted Score

| Category | Weight | Score | Weighted |
| --- | ---: | ---: | ---: |
| Purpose and trigger clarity | 10% | 9.4 | 0.94 |
| Workflow completeness | 12% | 9.1 | 1.09 |
| IBM i / domain correctness | 14% | 9.0 | 1.26 |
| Evidence and anti-hallucination | 12% | 9.3 | 1.12 |
| Output contract | 10% | 9.2 | 0.92 |
| Progressive disclosure | 8% | 9.3 | 0.74 |
| Runtime portability | 10% | 9.0 | 0.90 |
| Reviewability and testability | 10% | 9.1 | 0.91 |
| Engineering handoff value | 8% | 9.0 | 0.72 |
| Maintainability | 6% | 8.8 | 0.53 |

Final score before cap: **9.12 / 10**

Final score after cap: **9.0 / 10**

Decision: **repo-ready provisional, not field-pilot ready**

## Blocking For 9.5

| ID | Finding | Required Change |
| --- | --- | --- |
| LCSD-V010-REV-001 | No filled expected output exists. | Create one approved golden sample for `Report Lost` or `Issuer Authorization`, including report, catalogs, traceability, and gaps. |
| LCSD-V010-REV-002 | Document-first extraction has not been field-tested against a real RAG evidence pack. | Run the skill on 10-30 selected RAG documents and collect SME review notes. |
| LCSD-V010-REV-003 | Code-grounded routing has not been validated end to end. | Use an Authorization program-flow/key-program example and confirm it routes detailed validation/transaction logic to existing IBM i analyzers. |
| LCSD-V010-REV-004 | Runtime execution evidence is missing. | Run positive and negative smoke in Codex, Claude Code, and OpenCode after the golden sample exists. |

## Verification

```bash
python3 /Users/leo/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/legacy-current-state-discovery
python3 -m py_compile \
  skills/legacy-current-state-discovery/scripts/validate_current_state_discovery_package.py
python3 skills/legacy-current-state-discovery/scripts/validate_current_state_discovery_package.py \
  --allow-placeholders /tmp/legacy-current-state-discovery-sample
scripts/sync-skills.sh --skill legacy-current-state-discovery
scripts/sync-skills.sh --skill legacy-current-state-discovery --check
```

All local structural checks above passed on 2026-07-01.
