# Runtime Matrix

Track where each canonical skill has been synced and tested.

Any change to `skills/` must update this matrix in the same PR or commit.

| Skill | Canonical Version | Codex | Claude Code | OpenCode | Notes |
| --- | --- | --- | --- | --- | --- |
| `legacy-ibmi-inventory` | v0.1.0 | synced | synced | synced | Runtime copies created with `scripts/sync-skills.sh`; loading/execution not yet verified. |
| `legacy-modernization-orchestrator` | v0.1.1 | synced | synced | synced | Entry-point router. Runtime copies synced; cross-repo links hardened; loading/execution not yet verified. |

## Status Values

- `not tested`
- `synced`
- `loaded`
- `executed`
- `passed`
- `failed`

No skill should be marked field-pilot ready until the target runtimes for that
pilot are at least `loaded`, and preferably `executed` or `passed`.
