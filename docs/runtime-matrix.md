# Runtime Matrix

Track where each canonical skill has been synced and tested.

Any change to `skills/` must update this matrix in the same PR or commit.

| Skill | Canonical Version | Codex | Claude Code | OpenCode | Notes |
| --- | --- | --- | --- | --- | --- |
| `legacy-ibmi-inventory` | v0.1.0 | synced | synced | synced | Runtime copies created with `scripts/sync-skills.sh`; loading/execution not yet verified. |
| `legacy-ibmi-program-analyzer` | v0.1.0 | synced | synced | synced | Initial release; runtime copies created with `scripts/sync-skills.sh`; awaiting Codex review for 9.5/10 field-pilot readiness. |
| `legacy-ibmi-flow-analyzer` | v0.1.0 | synced | synced | synced | Initial release; 9-step workflow, 7 trigger models (batch/menu/subfile/F-key/trigger/scheduler/API); cross-program data flow + error propagation + commit boundaries; runtime copies created with `scripts/sync-skills.sh`; awaiting Codex review. |
| `legacy-ibmi-module-analyzer` | v0.1.0 | synced | synced | synced | Initial release; 9-step workflow producing 4-view module synthesis (Operation/System/Program/Data) per `docs/module-analysis-model.md`; aggregates multiple flows + BAU + SME context; awaiting Codex review. |
| `legacy-spec-writer` | v0.1.0 | synced | synced | synced | Initial release; Layer 2 platform-agnostic; 11-step workflow producing `spec.yaml` + `spec.md` + `spec-review.md` + `traceability.md` per `schemas/spec.schema.yaml`; rule-extraction protocol with strict anti-hallucination at BR promotion; example: Credit Limit Enforcement; awaiting Codex review. |
| `legacy-modernization-orchestrator` | v0.2.0 | synced | synced | synced | MVP scope expansion: added stages 3c–3f (flow / module) and routed to new skills (flow-analyzer / module-analyzer / spec-writer all `Implemented v0.1.0`). Smoke test from v0.1.1 covers the routing core; new stages need a fresh smoke test before field-pilot. |

## Status Values

- `not tested`
- `synced`
- `loaded`
- `executed`
- `passed`
- `failed`

No skill should be marked field-pilot ready until the target runtimes for that
pilot are at least `loaded`, and preferably `executed` or `passed`.
