# AGENTS.md

This repository contains the Legacy Spec Factory skill family and supporting
templates for IBM i / AS400 modernization.

## Core Rule

The skills must remain portable across Codex, Claude Code, and OpenCode. Do not
design a skill that only works because one IDE has a private folder convention.

## Canonical Skill Source

Use this repository-owned layout as the canonical source when skills are added:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/references/
skills/<skill-name>/templates/
skills/<skill-name>/scripts/
```

Runtime-specific directories are adapters or synced copies, not the source of
truth:

```text
.claude/skills/<skill-name>/SKILL.md
.opencode/skills/<skill-name>/SKILL.md
.agents/skills/<skill-name>/SKILL.md
.codex/skills/<skill-name>/SKILL.md
```

If a runtime copy is edited, port the change back to `skills/<skill-name>/`
before finishing the task.

Use `scripts/sync-skills.sh` to create runtime copies or check drift. Do not
edit adapter `SKILL.md` files directly. Runtime-only notes must live under
`runtime-overrides/` or in files named `*.adapter.md`; the sync script preserves
those files.

## Runtime Notes

- Claude Code project skills live under `.claude/skills/<skill-name>/SKILL.md`.
- OpenCode can use `.opencode/skills/`, `.agents/skills/`, or Claude-compatible
  `.claude/skills/`, depending on team setup.
- Codex should consume the same open Agent Skills structure. If a Codex-specific
  local adapter is used, keep it synced from `skills/`.
- Keep shared `SKILL.md` frontmatter portable. Put runtime-specific settings in
  adapter-only files only when required.

## Authorship

Preserve copyright and author notices.

Original author: Leo L Zhang

Copyright 2026 Leo L Zhang.

Use the header recommended in `README.md` for future skill files.

## Modernization Principles

- Treat IBM i SMEs as the control point for legacy understanding.
- Keep observed behavior, inferred rules, and modernization decisions separate.
- Every approved rule should carry source evidence or SME approval.
- `spec.yaml` is the structured source of truth for downstream Java/cloud SDLC;
  `spec.md` is the human-readable review view.
- Do not convert legacy code directly to Java without the evidence-backed spec
  layer.
- Follow `docs/id-conventions.md` for IDs.
- Follow `docs/evidence-and-knowledge-taxonomy.md` for knowledge type and
  evidence strength.
- Follow `docs/data-collection-and-redaction.md` before using logs, spool,
  sample transactions, or DB extracts.

## Skill Review Gate

Claude Code may generate or revise skills, but generated skills are not accepted
until reviewed against `docs/skill-review-gate.md`.

- Minimum score for repository acceptance: 9.0 / 10
- Preferred score for internal field pilot: 9.5 / 10
- Use `templates/skill-review-scorecard.md` for review records
- Below 9.0: return to Claude Code for revision
- 9.0-9.4: repo-ready only, not field-pilot ready
- 9.5 or higher: field-pilot ready
