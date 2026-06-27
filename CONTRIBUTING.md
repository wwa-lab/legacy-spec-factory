# Contributing To Atlas Phoenix Lens

Thank you for helping improve Atlas Phoenix Lens, the M3 Discovery capability
within the Atlas Engineering Delivery Hub / Seven Mountains SDLC narrative.

This repository contains the Legacy Spec Factory skill/tooling package behind
that capability. Contributions should help teams turn IBM i / AS400 legacy
evidence into structured, reviewable modernization evidence.

## What To Contribute

Good contribution areas include:

- Program Flow Map export contract improvements
- RPG / CL / COBOL / DDS source-scan prompts and examples
- Legacy Spec Factory skill improvements under `skills/`
- Validation scripts and test coverage
- Synthetic or approved redacted samples
- Evidence taxonomy, ID conventions, and review guidance
- Documentation, diagrams, pitch material, and onboarding guides
- Cross-runtime portability fixes for Codex, Claude Code, and OpenCode

Avoid contributions that:

- include customer data, internal secrets, credentials, or unredacted source
- bypass SME review for business meaning
- convert legacy code directly into target implementation without the evidence
  layer
- modify runtime adapter copies without updating canonical skill sources
- introduce tool-specific behavior that only works in one IDE/runtime

## Contribution Workflow

1. Open or find an issue describing the change.
2. Keep the change focused and small enough to review.
3. Update or add docs/tests/samples when behavior or contracts change.
4. Run the relevant checks.
5. Open a pull request with a clear summary and test plan.

For larger changes, include:

- problem statement
- proposed behavior
- affected skills/docs/scripts
- migration or compatibility notes
- verification evidence

## Canonical Skill Source

The canonical skill source lives under:

```text
skills/<skill-name>/SKILL.md
skills/<skill-name>/references/
skills/<skill-name>/templates/
skills/<skill-name>/scripts/
```

Runtime-specific folders are adapters or synced copies:

```text
.claude/skills/
.opencode/skills/
.agents/skills/
.codex/skills/
```

Do not edit adapter `SKILL.md` files directly. If a runtime copy must change,
port the change back to `skills/<skill-name>/` before finishing.

Use the sync script to refresh or check adapter copies:

```bash
scripts/sync-skills.sh --target all
scripts/sync-skills.sh --target all --check
```

## Evidence And Governance Rules

Atlas Phoenix Lens is not a direct code conversion tool. Contributions should
preserve the evidence-first workflow:

- Observed behavior must point to source, runtime, screen, report, data, or
  SME evidence.
- Inferred business rules must remain review candidates until SME approval.
- Missing or conflicting evidence should become `TBD-*` items.
- Modernization decisions should remain separate from source observations.
- Program Flow Map exports are navigation evidence, not final business truth.

Stable ID families should remain consistent:

- `EV-*` for evidence
- `BEH-*` for observed behavior
- `BR-*` for business rule seeds
- `TBD-*` for open questions or missing evidence
- `VAL-*` for BRD-stage validation scenario seeds

## Data Safety And Redaction

Before contributing artifacts, confirm they do not contain:

- customer names, account numbers, card numbers, IDs, or addresses
- credentials, tokens, API keys, URLs with secrets, or passwords
- production logs with sensitive data
- proprietary source code that is not approved for this repository
- screenshots containing internal systems, user names, or unapproved repo names

Prefer synthetic examples. If a real sample is useful, it must be explicitly
approved and redacted before contribution.

See:

- [docs/data-collection-and-redaction.md](docs/data-collection-and-redaction.md)
- [docs/evidence-and-knowledge-taxonomy.md](docs/evidence-and-knowledge-taxonomy.md)
- [docs/id-conventions.md](docs/id-conventions.md)

## Program Flow Map Contributions

The upstream Neo4j Program Flow Map application currently lives in a separate
company-internal repository. Contributions in this repository should focus on
the handoff contract and downstream consumption behavior.

Use:

- [docs/program-flow-map-export-contract.md](docs/program-flow-map-export-contract.md)
- [docs/samples/atlas-phoenix-lens-mini-output/](docs/samples/atlas-phoenix-lens-mini-output/)

When changing the export contract, update:

- README / Chinese README if the public boundary changes
- sample output package
- downstream docs or validators that consume the export
- pitch/submission docs if the narrative changes

## Documentation Contributions

Documentation should be clear, AI-friendly, and easy to reuse:

- Prefer Markdown tables, YAML, CSV, and stable file paths.
- Keep English README as the default repo entry.
- Keep Chinese README aligned when user-facing positioning changes.
- Use diagrams when they clarify architecture or workflow.
- Preserve the distinction between Delivery Hub positioning and implementation
  design.

Key docs:

- [README.md](README.md)
- [README.zh-CN.md](README.zh-CN.md)
- [docs/atlas-phoenix-lens-index.md](docs/atlas-phoenix-lens-index.md)
- [docs/atlas-phoenix-lens-pitch.md](docs/atlas-phoenix-lens-pitch.md)

## Testing And Validation

Run the lightest checks that match your change. For docs-only changes:

```bash
git diff --check
```

For Python scripts and sample YAML/CSV changes, use `python3` on macOS/Linux.
On Windows, use `py -3` first, then fall back to `python`.

For skill sync changes:

```bash
scripts/sync-skills.sh --target all --check
```

For broader repository validation:

```bash
python3 -m pytest
```

If Python is unavailable, stop and report:

```text
Python runtime unavailable. Install Python 3 and ensure `py -3` (Windows)
or `python3` (macOS/Linux) is accessible, then retry.
```

## Pull Request Checklist

Before opening a PR:

- [ ] The change has a clear purpose and scope.
- [ ] No secrets, credentials, customer data, or unredacted internal data are
      included.
- [ ] Canonical skill sources under `skills/` were updated before runtime
      adapter copies.
- [ ] Relevant docs, samples, contracts, or tests were updated.
- [ ] Evidence IDs and governance terminology remain consistent.
- [ ] Validation commands were run and noted in the PR.
- [ ] Any remaining open questions are listed clearly.

## Commit Style

Use conventional commits when possible:

```text
docs: add Program Flow Map contract guidance
test: cover program analysis validator edge case
fix: correct sample evidence reference
feat: add source scan prompt template
```

## Questions

If you are unsure whether a change belongs here, start with an issue or draft
PR. For ambiguous business meaning, route the question to the relevant SME
instead of encoding assumptions as approved requirements.
