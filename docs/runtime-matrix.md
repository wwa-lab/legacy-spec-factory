# Runtime Matrix

Track where each canonical skill has been synced and tested.

Any change to `skills/` must update this matrix in the same PR or commit.

| Skill | Canonical Version | Codex | Claude Code | OpenCode | Notes |
| --- | --- | --- | --- | --- | --- |
| `legacy-brd-writer` | v0.1.1 | passed | passed | passed | Smoke tests passed on 2026-05-16 in a disposable synced workspace to avoid touching dirty adapter directories in the main worktree. Codex CLI (gpt-5.4-mini, read-only ephemeral), Claude Code (haiku, Read-only tools), and OpenCode (minimax-m2.5-free) all invoked `/legacy-brd-writer`, returned `05_brds/CREDIT-LIMIT/` with `brd.md`, `brd-review.md`, and `traceability.md`, preserved `BR-*` as `needs_sme_review`, refused new `BR-*` minting, used repository evidence-strength names, and confirmed no writes. |
| `legacy-ibmi-evidence-intake` | v0.1.0 | passed | passed | passed | Full positive and negative smoke rerun on 2026-05-15. Codex CLI (gpt-5.4-mini, read-only ephemeral) passed both scenarios without file writes. OpenCode (minimax-m2.5-free) passed both scenarios in disposable copies without writing `evidence/` to the real repository. Claude Code (haiku) initially hung in the default Codex execution sandbox; debug logs showed EPERM on Claude config/telemetry writes. Rerun with Claude auth/config/network access passed: positive returned `pass_with_warnings` with inventory allowed, negative blocked unknown-sensitivity evidence. |
| `legacy-ibmi-inventory` | v0.1.0 | synced | synced | synced | Runtime copies created with `scripts/sync-skills.sh`; loading/execution not yet verified. |
| `legacy-ibmi-program-analyzer` | v0.1.0 | synced | synced | synced | All 5 review findings fixed in `99e27f4`; smoke test prompts added to `docs/runtime-smoke-tests.md`. Ready for smoke test execution in three runtimes. |
| `legacy-ibmi-flow-analyzer` | v0.1.1 | synced | passed | synced | Positive (scheduler batch flow with 4 programs) and negative (missing program-analysis) scenarios passed on 2026-05-14 (Claude Code/haiku). Both scenarios correctly handled input validation, blocking TBDs, and routing decisions. Codex and OpenCode smoke execution still needed. |
| `legacy-ibmi-module-analyzer` | v0.1.1 | executed | executed | executed | Automated smoke script executed 2026-05-14 with Codex (gpt-5.4-mini), Claude Code (haiku), and OpenCode (minimax-m2.5-free). Script reported all `passed`, but strict manual review records `executed`: Codex produced a four-view scaffold with source caveats/blocking TBDs, Claude requested missing upstream evidence instead of producing artifacts, and OpenCode attempted workspace writes with partial output. Field-pilot pass remains pending; see `docs/reviews/legacy-ibmi-module-analyzer-v0.1.1-scorecard.md`. |
| `legacy-spec-writer` | v0.1.0 | synced | passed | synced | Positive (all upstream analyses approved, 8 programs) and negative (missing/draft flow analysis) scenarios passed on 2026-05-14 (Claude Code/haiku). Both scenarios correctly identified blocking conditions and refused to produce incomplete specs. Codex and OpenCode smoke execution still needed. |
| `legacy-modernization-orchestrator` | v0.2.0 | synced | passed | synced | Evidence-ready and inventory-blocked scenarios passed on 2026-05-14 (Claude Code/haiku). Expanded v0.2.0 prompts now cover program -> flow, flow -> module, module -> spec, and blocked forward handoff; Codex/OpenCode and expanded-route execution still needed. |
| `legacy-step-contract` | v0.1.1 | passed | passed | passed | Positive and negative smoke tests passed on 2026-05-14 (Codex/gpt-5.4-mini, Claude Code/haiku, OpenCode/minimax-m2.5-free). Refreshed v0.1.1 scorecard records field-pilot readiness at 9.52. |
| `legacy-step-validator` | v0.1.1 | passed | passed | passed | Positive and negative smoke tests passed on 2026-05-14 (Codex/gpt-5.4-mini, Claude Code/haiku, OpenCode/minimax-m2.5-free). Refreshed v0.1.1 scorecard records field-pilot readiness at 9.53. |

## Status Values

- `not tested`
- `synced`
- `loaded`
- `executed`
- `passed`
- `failed`

No skill should be marked field-pilot ready until the target runtimes for that
pilot are at least `loaded`, and preferably `executed` or `passed`.
