# CLAUDE.md

Read `AGENTS.md` first for shared project rules.

Claude Code project skills may live under `.claude/skills/<skill-name>/`, but
the canonical source is `skills/<skill-name>/`.

When generating or revising a skill, target the review gate in
`docs/skill-review-gate.md`: 9.0 / 10 minimum, 9.5 / 10 for internal field
pilot.

## Workflow Before Implementation

Before starting any skill implementation:
1. Check latest repo state with `git status` and `git log`
2. Review related documentation (MVP scope, skill review gate, runtime matrix)
3. Check existing skills for patterns and conventions
4. Verify no conflicts with ongoing work

