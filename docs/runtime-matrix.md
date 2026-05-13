# Runtime Matrix

Track where each canonical skill has been synced and tested.

Any change to `skills/` must update this matrix in the same PR or commit.

| Skill | Canonical Version | Codex | Claude Code | OpenCode | Notes |
| --- | --- | --- | --- | --- | --- |
| `legacy-ibmi-inventory` | v0.1.0 | synced | synced | synced | Runtime copies created with `scripts/sync-skills.sh`; loading/execution not yet verified. |
| `legacy-modernization-orchestrator` | v0.1.1 | passed | passed | passed | Routing smoke test passed in Codex CLI (`gpt-5.4-mini`), Claude Code (`haiku` with Read-only tool access), and OpenCode (`opencode/minimax-m2.5-free`). Runtime copies remain synced. |

## Status Values

- `not tested`
- `synced`
- `loaded`
- `executed`
- `passed`
- `failed`

No skill should be marked field-pilot ready until the target runtimes for that
pilot are at least `loaded`, and preferably `executed` or `passed`.
