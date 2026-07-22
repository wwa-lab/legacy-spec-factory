# Targeted approved-artifact repair: {{PROGRAM}}

Use `legacy-ibmi-program-analyzer` to repair only program `{{PROGRAM}}` in an
isolated repair branch or working clone.

## Scope

- Artifact repository mode: `approved_document_repo`.
- Artifact root: `{{ARTIFACT_ROOT}}`.
- Size tier: `{{TIER}}`.
- Requalification status: `{{STATUS}}`.
- Finding codes: `{{FINDING_CODES}}`.
- Source-index SHA-256 before repair: `{{SOURCE_INDEX_SHA256}}`.
- Deep-read execution-plan SHA-256 before repair: `{{EXECUTION_PLAN_SHA256}}`.

## Evidence and safety rules

1. Own this one program only. Do not edit another program's artifact folder.
2. Do not rescan the whole approved repository and do not send a large program's
   complete source to one prompt.
3. Preserve all valid source-backed facts, exact literals, program identity,
   provenance, and hashes. Do not invent message meanings, call chains, or
   execution order.
4. Do not edit approved `main` in place. Produce the repair in the controlled
   repair workspace and retain before/after hashes and an audit note.
5. If the exact source mapping, reference inputs, or artifact identity is not
   available, stop this prompt as blocked and record the missing input. Do not
   guess a path or synthesize evidence.

## Observed findings

{{FINDINGS}}

## Required targeted actions

{{REPAIR_ACTIONS}}

## Large-program rule

If this is `large_extreme_program`, reuse the existing source index and
deep-read execution plan when their hashes are valid. Otherwise regenerate the
deterministic source index/plan first, then repair retained routine windows in
small checkpoints (at most five routines/windows per checkpoint). Complete all
retained batches and update the routine cards, Program Reading Summary,
Message Inventory, terminal status, execution-plan hash, and batch locks. Do
not replace the program's 30,000+ source lines with a single free-form summary.

## Exit criteria

Run the canonical program-analysis validator for `{{PROGRAM}}` with its
expected size tier. The repair is complete only when the validator and the
reader-first readiness checks pass, all required hashes/locks are consistent,
and the output records the exact source-backed evidence changed. If any check
still fails, leave the row non-terminal and report the remaining finding rather
than claiming completion.
