# Runtime Smoke Tests

Use these smoke tests before marking a skill `loaded`, `executed`, or `passed`
in `docs/runtime-matrix.md`.

The goal is not to benchmark model quality. The goal is to confirm that each
runtime can discover the synced skill copy, apply its trigger/output contract,
and complete a no-write routing task.

## Orchestrator Routing Smoke Test

### Scenario

```text
Use /legacy-modernization-orchestrator.

User input:
I have redacted RPGLE source, DDS, a spool sample, redacted sample
transactions, and an SME contact for a CREDIT-CHECK capability. What should I
do next?

Return only:
- current stage
- recommended next skill
- gate check
```

### Pass Criteria

The response must include all of the following:

- current stage is `Evidence Ready` or equivalent Stage 1 wording
- recommended next skill is `legacy-ibmi-inventory`
- Redaction Gate is treated as passed or ready to check from the supplied
  redaction statement
- no downstream planned skill is recommended before inventory
- no files are created or edited

### Suggested Commands

Run commands from the repository root. Add model or auth flags required by the
local environment.

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

## Recording Results

Update `docs/runtime-matrix.md` only after recording the result:

- `loaded`: runtime discovered the skill but did not complete the scenario
- `executed`: runtime completed the scenario with the right shape
- `passed`: runtime completed the scenario and met every pass criterion
- `failed`: runtime could not discover the skill or violated a hard gate

If a command hangs, errors, or requires unavailable credentials, leave the
runtime at `synced` and record the issue in the relevant review scorecard.
