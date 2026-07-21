# Skill Status Truth Table

**This is the single source of truth** for each skill's verified status,
score, and runtime evidence. README and `docs/runtime-matrix.md` should
agree with this table; if they don't, this table wins.

The table is built from scorecard frontmatter under `docs/reviews/`. Run
`scripts/verify-skill-claims.py` to detect drift between this table,
README, runtime-matrix, and scorecard frontmatter. The **Version** column is
the latest reviewed scorecard version; `docs/runtime-matrix.md` may list a
newer synced runtime version only when that row explicitly says the updated
scorecard is pending.

Last regenerated: 2026-07-21

## How to Read This Table

- **Static Score**: scorecard score before runtime cap (from rubric).
- **Decision**: `field-pilot ready` requires all three runtimes at `passed`
  AND the scorecard explicitly approved. `repo-ready` means structurally
  sound but runtime cap (9.0) still applies.
- **Runtime Status**: copied from scorecard `runtimes_tested:` block.
  - `passed` → invoked, output met contract, no side effects
  - `executed` → invoked, output produced but not all pass criteria met
  - `loaded` → discovered, not yet invoked
  - `synced` → adapter copy exists, not yet loaded
  - `not tested` → adapter not synced
- **Last Verified**: most recent date the runtime status was confirmed.
  `not-yet-tested` for skills with all `synced` rows.
- **Scorecard**: link to the current reviewed scorecard file.

## Current State

| Skill | Version | Static | Decision | Codex | Claude Code | OpenCode | Last Verified | Scorecard |
| --- | --- | ---: | --- | --- | --- | --- | --- | --- |
| `legacy-modernization-orchestrator` | v0.2.11 | 9.56 | repo-ready (provisional) | synced | synced | synced | 2026-06-03 | [link](reviews/legacy-modernization-orchestrator-v0.2.11-scorecard.md) |
| `legacy-module-context-intake` | v0.1.7 | 9.48 | repo-ready (provisional) | synced | synced | synced | 2026-06-03 | [link](reviews/legacy-module-context-intake-v0.1.7-scorecard.md) |
| `legacy-document-evidence-intake` | v0.1.0 | 9.42 | repo-ready | synced | synced | synced | not-yet-tested | [link](reviews/legacy-document-evidence-intake-v0.1.0-scorecard.md) |
| `legacy-current-state-discovery` | v0.1.0 | 9.12 | repo-ready (provisional) | synced | synced | synced | 2026-07-01 | [link](reviews/legacy-current-state-discovery-v0.1.0-scorecard.md) |
| `legacy-ibmi-evidence-intake` | v0.1.0 | 9.16 | repo-ready | passed | passed | passed | 2026-05-15 | [link](reviews/legacy-ibmi-evidence-intake-v0.1.0-scorecard.md) |
| `legacy-ibmi-inventory` | v0.1.0 | 9.35 | repo-ready | synced | synced | synced | not-yet-tested | [link](reviews/legacy-ibmi-inventory-v0.1.0-scorecard.md) |
| `legacy-ibmi-runtime-evidence-miner` | v0.1.0 | 9.57 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-ibmi-runtime-evidence-miner-v0.1.0-scorecard.md) |
| `legacy-ibmi-program-analyzer` | v0.2.5 | 9.66 | repo-ready | synced | synced | synced | 2026-06-02 | [link](reviews/legacy-ibmi-program-analyzer-v0.2.5-scorecard.md) |
| `legacy-ibmi-program-list-batch` | v0.1.0 | 9.34 | repo-ready | synced | synced | synced | 2026-06-25 | [link](reviews/legacy-ibmi-program-list-batch-v0.1.0-scorecard.md) |
| `legacy-ibmi-data-model-analyzer` | v0.1.0 | 9.32 | repo-ready | passed | synced | passed | 2026-05-16 | [link](reviews/legacy-ibmi-data-model-analyzer-v0.1.0-scorecard.md) |
| `legacy-ibmi-screen-report-analyzer` | v0.1.0 | 9.38 | repo-ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-ibmi-screen-report-analyzer-v0.1.0-scorecard.md) |
| `legacy-ibmi-flow-analyzer` | v0.4.0 | 9.51 | repo-ready | synced | synced | synced | 2026-07-21 | [link](reviews/legacy-ibmi-flow-analyzer-v0.4.0-scorecard.md) |
| `legacy-ibmi-module-analyzer` | v0.2.3 | 9.62 | repo-ready (provisional) | synced | synced | synced | 2026-06-04 | [link](reviews/legacy-ibmi-module-analyzer-v0.2.3-scorecard.md) |
| `legacy-brd-writer` | v0.1.8 | 9.52 | repo-ready (provisional) | synced | synced | synced | 2026-06-03 | [link](reviews/legacy-brd-writer-v0.1.8-scorecard.md) |
| `legacy-spec-writer` | v0.1.6 | 9.49 | repo-ready | synced | synced | synced | 2026-06-02 | [link](reviews/legacy-spec-writer-v0.1.6-scorecard.md) |
| `legacy-modernization-decision-writer` | v0.1.0 | 9.56 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-modernization-decision-writer-v0.1.0-scorecard.md) |
| `legacy-sme-review-facilitator` | v0.1.2 | 9.40 | repo-ready | synced | synced | synced | 2026-05-26 | [link](reviews/legacy-sme-review-facilitator-v0.1.2-scorecard.md) |
| `legacy-brd-to-sdd-handoff` | v0.1.0 | 9.63 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-brd-to-sdd-handoff-v0.1.0-scorecard.md) |
| `legacy-traceability-packager` | v0.1.1 | 9.51 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-traceability-packager-v0.1.1-scorecard.md) |
| `legacy-runtime-matrix-tester` | v0.1.0 | 9.56 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-runtime-matrix-tester-v0.1.0-scorecard.md) |
| `legacy-golden-master-test-planner` | v0.1.0 | 9.59 | field-pilot ready | passed | passed | passed | 2026-05-16 | [link](reviews/legacy-golden-master-test-planner-v0.1.0-scorecard.md) |
| `legacy-step-contract` | v0.1.2 | 9.52 | field-pilot ready | passed | passed | passed | 2026-05-29 | [link](reviews/legacy-step-contract-v0.1.2-scorecard.md) |
| `legacy-step-validator` | v0.1.8 | 9.60 | repo-ready | synced | synced | synced | 2026-06-02 | [link](reviews/legacy-step-validator-v0.1.8-scorecard.md) |
| `legacy-html-exporter` | v0.1.0 | 9.31 | repo-ready | passed | failed | passed | 2026-05-19 | [link](reviews/legacy-html-exporter-v0.1.0-scorecard.md) |

## Summary

| Decision | Count |
| --- | ---: |
| `field-pilot ready` (all three runtimes `passed`) | 9 |
| `repo-ready` / `repo-ready (provisional)` (runtime cap or partial coverage) | 15 |

**24 skills total** in canonical source; **37 superseded scorecards** kept
under `docs/reviews/` for historical reference.

## Verification

Run `py -3 scripts/verify-skill-claims.py` (macOS: `python3`) to check that:

1. Every skill listed here has a current scorecard with frontmatter
2. README "Current Skill Scores" matches this table
3. `docs/runtime-matrix.md` runtime statuses match the scorecard frontmatter;
   newer synced runtime versions are allowed only when marked scorecard-pending
4. No `field-pilot ready` decision exists for a skill with any non-`passed`
   runtime status

The script exits non-zero if drift is detected.
