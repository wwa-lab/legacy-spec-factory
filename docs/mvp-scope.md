# MVP Scope

The first MVP should prove the reverse-modernization model with the smallest
credible slice.

## Narrow MVP

Target:

- one business capability
- three minimum skills
- one reviewed `spec.yaml` / `spec.md`
- one SME approval pass

Minimum skills:

1. `legacy-ibmi-inventory` (Layer 1, platform-specific)
2. `legacy-ibmi-program-analyzer` (Layer 1, platform-specific)
3. `legacy-spec-writer` (Layer 2, platform-agnostic)

A fourth entry-point skill, `legacy-modernization-orchestrator`, sits above
these to guide users through the chain.

## Success Criteria

- legacy objects for the capability are inventoried
- one or more programs are analyzed with source evidence
- `spec.yaml` follows `schemas/spec.schema.yaml`
- `spec.md` renders the same information for human review
- every approved rule has evidence or SME approval
- at least one acceptance criterion traces to a business rule
- blocking TBDs are explicit

## Deferred From MVP

- full runtime evidence miner
- full equivalence test generator
- automated Java/cloud generation
- complete parser coverage for all IBM i source variants
- broad multi-capability modernization

The goal is to calibrate the skill quality gate and prove the evidence-backed
spec contract before scaling the skill family.

