# Runtime Matrix

Track where each canonical skill has been synced and tested.

Any change to `skills/` must update this matrix in the same PR or commit.

| Skill | Canonical Version | Codex | Claude Code | OpenCode | Notes |
| --- | --- | --- | --- | --- | --- |
| `legacy-ibmi-inventory` | v0.1.0 | synced | synced | synced | Runtime copies created with `scripts/sync-skills.sh`; loading/execution not yet verified. |
| `legacy-ibmi-program-analyzer` | v0.1.0 | synced | synced | synced | All 5 review findings fixed in `99e27f4`; smoke test prompts added to `docs/runtime-smoke-tests.md`. Ready for smoke test execution in three runtimes. |
| `legacy-ibmi-flow-analyzer` | v0.1.1 | synced | synced | synced | All 5 v0.1.0 blockers resolved: trigger model clarified, blocked status values added, seed IDs standardized, evidence taxonomy (4 types) added, smoke test prompts added to `docs/runtime-smoke-tests.md` (2026-05-14). Ready for smoke test execution in three runtimes. Expected score 9.6/10, field-pilot ready upon passing smoke tests. |
| `legacy-ibmi-module-analyzer` | v0.1.1 | synced | synced | synced | Static review fixes are in place (MOD-REV-001 prompts added; MOD-REV-002 through 005 fixed). Current score remains 9.0 capped until three-runtime smoke execution is recorded. See `docs/reviews/legacy-ibmi-module-analyzer-v0.1.1-scorecard.md`. |
| `legacy-spec-writer` | v0.1.0 | synced | synced | synced | Reviewed at 9.0 capped. Post-review hardening committed: smoke prompts added, AC/template rule fixed, field evidence status added, spec-review/traceability templates added, skill-local contract check enabled. Needs three-runtime smoke execution and post-smoke re-score. |
| `legacy-modernization-orchestrator` | v0.2.0 | synced | synced | synced | MVP scope expansion added flow/module/spec routing. v0.1.1 was field-pilot ready; v0.2.0 has not been re-reviewed or re-smoked yet. |

## Status Values

- `not tested`
- `synced`
- `loaded`
- `executed`
- `passed`
- `failed`

No skill should be marked field-pilot ready until the target runtimes for that
pilot are at least `loaded`, and preferably `executed` or `passed`.
