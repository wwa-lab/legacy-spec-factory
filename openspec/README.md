# OpenSpec in This Repository

This repository uses OpenSpec as a lightweight change-entry layer.

## Boundary

- OpenSpec is used to frame change intent, scope, requirements deltas, and work planning.
- The repository's existing workflow remains the deeper implementation layer.
- Do not use OpenSpec to replace the canonical IBM i modernization artifacts already defined by this repository.

## Source of Truth

Use exactly one primary source of truth per change:

- If a change is being tracked in `openspec/changes/<change-name>/`, that OpenSpec change is the source of truth for the change request's intent and scope.
- Repository-native artifacts such as `spec.yaml`, `spec.md`, BRDs, decision packages, and SDD handoff packages should refine or operationalize that change instead of redefining it.

Avoid parallel planning tracks. Do not keep an OpenSpec proposal/design/tasks set and a separate unrelated master task list that silently diverges.

## When OpenSpec Fits Here

OpenSpec fits best for repository engineering work such as:

- multi-file feature work
- larger refactors
- cross-runtime integration changes
- workflow or tooling changes that benefit from explicit proposal/design/tasks artifacts

OpenSpec is usually not worth the overhead for:

- tiny copy edits
- small metadata cleanups
- one-off adapter syncs
- narrow fixes that are cheap to reason about directly

## Runtime Adapters

Canonical OpenSpec skills live under `skills/openspec-*/`.
Runtime copies are synced into `.claude/skills/`, `.opencode/skills/`, `.agents/skills/`, and `.codex/skills/` using `scripts/sync-skills.sh`.
