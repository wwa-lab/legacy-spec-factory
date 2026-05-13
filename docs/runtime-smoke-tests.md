# Runtime Smoke Tests

Use this protocol before marking a skill `loaded`, `executed`, or `passed` in
`docs/runtime-matrix.md`. It is the reusable test that lifts the 9.0
"portability has been considered but not tested" cap from
[docs/skill-review-gate.md](skill-review-gate.md).

The goal is not to benchmark model quality. The goal is to confirm that each
runtime can discover the synced skill copy, apply its trigger and output
contract, and complete a no-write routing or extraction task.

## When to Run

Run this protocol when:

- a new skill is added under `skills/` and needs to move from `synced` to
  `passed` in `docs/runtime-matrix.md`
- an existing skill is bumped to a new version that materially changes
  trigger, workflow, output contract, or runtime portability
- a skill review scorecard explicitly lists a runtime-validation blocker

Do not run it for cosmetic edits (typos, formatting). Record those as a
version-history note without rerunning the protocol.

## Target Runtimes

Every skill must pass in all three runtimes before lifting the cap:

| Runtime | Discovery Path | Reference Invocation |
| --- | --- | --- |
| Codex (CLI) | `.codex/skills/<name>/SKILL.md` | `codex exec -C . -s read-only --ephemeral -m <model>` |
| Claude Code | `.claude/skills/<name>/SKILL.md` | `claude -p --model <model> --permission-mode dontAsk --tools Read` |
| OpenCode | `.opencode/skills/<name>/SKILL.md` (or `.agents/skills/...`) | `opencode run -m <model>` |

Use the same project root for all three so adapter folders are picked up
consistently.

## Pre-Test Checks

Before running the test, confirm:

- [ ] `scripts/sync-skills.sh --target all --check` returns exit 0 (no drift)
- [ ] `python3 scripts/check-spec-contract.py` returns exit 0 (if the skill
      touches `spec.yaml` shape)
- [ ] The canonical `SKILL.md` is the version being tested (no uncommitted
      changes that would not be in the synced adapter copies)

If any check fails, fix it before testing.

## Per-Runtime Test Phases

Each runtime gets the same two-phase test: **Discovery** and **Trigger**.

### Phase 1 — Discovery

Confirm the runtime can find and load the skill. Success criteria:

- the skill name appears in the runtime's skill list when project skills are
  enumerated
- the skill's `description` is visible to the runtime
- loading does not error on frontmatter, file paths, or unsupported metadata

Recorded as: `loaded`.

### Phase 2 — Trigger

Confirm the skill actually fires on its declared trigger condition. Each
skill must declare a **canonical trigger prompt** in its `examples/` folder
(usually the simplest positive example). For the test, use the prompt
listed under "Test Prompts" below.

Success criteria:

- the skill is invoked by the runtime (not a sibling skill, not ignored)
- the skill produces output following the structure declared in its
  `SKILL.md` Output Contract / Output Structure section
- the output references the artifact filenames, ID prefixes, or gate names
  the skill is supposed to emit
- no required gate is skipped (e.g., a router skill should call out gate
  failures when the example is a blocked case)
- no files are created or edited during the test

Recorded as: `executed` if produced output, `passed` if the output also
meets the canonical example's expected shape and pass criteria.

### Phase 3 (Optional) — Adversarial

For skills that have an `examples/<name>-negative-case/` example, also run
that prompt and confirm the skill blocks or refuses correctly. Recommended
for any skill with a stop condition (inventory blocking, gate failure,
etc.).

A negative-case pass is not required for 9.5, but it strengthens the
evidence base.

## Recording Results

Update `docs/runtime-matrix.md` only after running the test:

1. Bump the skill's canonical version column (`vX.Y.Z`) — the version that
   was tested
2. Set each runtime column to the highest status reached
3. Add a Notes cell with the exact runtime + model alias used and the date
4. Same-PR or same-commit rule applies (see file header)

Status values:

- `not tested` — sync not yet attempted
- `synced` — adapter folder created, content matches canonical
- `loaded` — runtime discovered the skill but did not complete the scenario
- `executed` — runtime completed the scenario with the right shape
- `passed` — runtime completed the scenario and met every pass criterion
- `failed` — runtime could not discover the skill or violated a hard gate

If a command hangs, errors, or requires unavailable credentials, leave the
runtime at `synced` and record the issue in the relevant review scorecard.

Update or create the skill's review scorecard:

1. If the previous scorecard listed a runtime-validation blocker, the
   blocker is now resolved — note it under "Blocking For 9.5" with the
   matrix row that proves it
2. Create a new scorecard file at `docs/reviews/<skill>-vX.Y.Z-scorecard.md`
   showing the final post-cap score
3. Decision goes from `repo-ready` to `field-pilot ready`

Update the skill's `SKILL.md` Version History:

```markdown
- vX.Y.Z (YYYY-MM-DD): Runtime smoke test passed in Codex CLI (<model>),
  Claude Code (<model>), and OpenCode (<model>). Lifted from 9.0 to 9.5.
```

## Test Prompts For Currently-Implemented Skills

The exact canonical prompts to use per skill. Use them verbatim across all
three runtimes.

### `legacy-modernization-orchestrator`

#### Scenario (Positive — Evidence Ready)

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

#### Pass Criteria (Positive)

The response must include all of the following:

- current stage is `Evidence Ready` or equivalent Stage 1 wording
- recommended next skill is `legacy-ibmi-inventory`
- Redaction Gate is treated as passed or ready to check from the supplied
  redaction statement
- no downstream planned skill is recommended before inventory
- no files are created or edited

#### Scenario (Negative — Inventory Blocked)

```text
Use /legacy-modernization-orchestrator.

User input:
I ran legacy-ibmi-inventory on the credit-check capability. The inventory
lists ORDENTR, but it references CRHOLDP (a PRTF) and CRCHKSRV (a service
program) and we don't have source for either. The inventory.yaml has
sme_review.decision: blocked. Can I just run the program analyzer next
anyway? We're under time pressure.

Return only:
- current stage
- gate status
- next skill (or "stop")
```

#### Pass Criteria (Negative)

- refuses to advance to program analyzer
- explicitly lists `TBD-CREDIT-CHECK-001` and `TBD-CREDIT-CHECK-002` (or the
  equivalent missing-artifact TBDs)
- routes back to inventory resume or SME waiver path
- Inventory Completeness Gate is reported as blocked

#### Reference Commands

Run from the repository root. Add model or auth flags required by your
local environment.

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-modernization-orchestrator. User input: I have redacted RPGLE source, DDS, a spool sample, redacted sample transactions, and an SME contact for a CREDIT-CHECK capability. What should I do next? Return only: current stage, recommended next skill, gate check."
```

For the negative scenario, substitute the inventory-blocked prompt above
into the same `codex exec` / `claude -p` / `opencode run` commands.

### `legacy-ibmi-inventory`

#### Scenario (Positive — Redacted Bundle)

```text
Use /legacy-ibmi-inventory.

User input:
I have redacted RPGLE source for ORDENTR and ORDSUBMIT, DDS for CUSTPF and
CRHOLDP, and a sample spool from the credit-hold report. SME contact is from
credit operations. Capability slug is CREDIT-CHECK. Help me build the
inventory.

Return only:
- the inventory.yaml skeleton (top-level keys and evidence IDs)
- the next prompt for missing required fields, if any
- whether sme_review.decision should be approved or pending
```

#### Pass Criteria (Positive)

- produces an `inventory.yaml` skeleton with top-level keys matching
  `skills/legacy-ibmi-inventory/templates/inventory.yaml`
- classifies each named artifact with an `EV-CREDIT-CHECK-NNN` ID
- does not invent objects, programs, or files not named in the input
- emits or references `inventory-review-checklist.md`
- if any required field is missing (collection date, library name), asks
  rather than guessing
- does not mark `sme_review.decision: approved` without an explicit SME
  decision

#### Scenario (Negative — Missing Artifact)

```text
Use /legacy-ibmi-inventory.

User input:
ORDENTR's source references CRHOLDP and CRCHKSRV but neither artifact is in
the bundle. Continue and produce the inventory.

Return only:
- the inventory.yaml entries for OBJ-CREDIT-CHECK-001 (ORDENTR),
  OBJ-CREDIT-CHECK-002 (CRHOLDP), OBJ-CREDIT-CHECK-003 (CRCHKSRV)
- the blocking TBDs
- the sme_review.decision value
```

#### Pass Criteria (Negative)

- records `OBJ-CREDIT-CHECK-002` and `OBJ-CREDIT-CHECK-003` with
  `source_member:` empty and `sensitivity: unknown`
- creates blocking TBDs (`TBD-CREDIT-CHECK-001` for CRHOLDP,
  `TBD-CREDIT-CHECK-002` for CRCHKSRV) with `blocking: yes`
- sets `sme_review.decision: blocked`
- refuses to mark `approved` or recommend downstream analyzer

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-inventory. User input: I have redacted RPGLE source for ORDENTR and ORDSUBMIT, DDS for CUSTPF and CRHOLDP, and a sample spool from the credit-hold report. SME contact is from credit operations. Capability slug is CREDIT-CHECK. Help me build the inventory. Return only the inventory.yaml skeleton (top-level keys and evidence IDs), the next prompt for missing required fields, and whether sme_review.decision should be approved or pending."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-inventory. User input: I have redacted RPGLE source for ORDENTR and ORDSUBMIT, DDS for CUSTPF and CRHOLDP, and a sample spool from the credit-hold report. SME contact is from credit operations. Capability slug is CREDIT-CHECK. Help me build the inventory. Return only the inventory.yaml skeleton, the next prompt for missing required fields, and whether sme_review.decision should be approved or pending."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-inventory. User input: I have redacted RPGLE source for ORDENTR and ORDSUBMIT, DDS for CUSTPF and CRHOLDP, and a sample spool from the credit-hold report. SME contact is from credit operations. Capability slug is CREDIT-CHECK. Help me build the inventory. Return only the inventory.yaml skeleton, the next prompt for missing required fields, and whether sme_review.decision should be approved or pending."
```

For the negative scenario, substitute the missing-artifact prompt above into
the same commands.

### `legacy-ibmi-program-analyzer`

#### Scenario (Positive — Simple RPGLE CRUD)

```text
Use /legacy-ibmi-program-analyzer.

User input:
I have RPGLE source for CREDITCHK (OBJ-CREDIT-VALIDATION-001). It validates
customer credit limits. Analyze its control flow, file I/O, entry points,
and external calls.

Provide the analysis in the output contract format.
```

#### Pass Criteria (Positive)

The response must include all of the following:

- **Metadata section:** Program ID (OBJ-CREDIT-VALIDATION-001), Program Type (RPGLE), entry points list
- **Entry Points & Parameters:** CreditChk procedure with (CustID, RequestAmount) parameters and return decision code
- **Control Flow:** CHAIN operation on CREDFILE, IF/ELSE branching on credit limit check
- **File I/O:** CREDFILE with CHAIN operation; CUSTFILE marked as declared but unused
- **External Calls:** None (correctly identifies no external CALLs)
- **Evidence tagging:** All major behaviors tagged with `confirmed_from_code` or evidence IDs
- **Status:** draft or needs_sme_review (not blocked_pending_source; source is complete)
- **No TBDs created for complete source sections** (though "confirm CREDFILE DDS field list" may appear as non-blocking pending)
- No files are created or edited

#### Scenario (Negative — Incomplete Source)

```text
Use /legacy-ibmi-program-analyzer.

User input:
I have a COBOL program with incomplete source. The COMPUTE-RATE paragraph has
a comment saying it calls GET-BASE-RATE, but the CALL statement is not in the
extract. The LOOKUP-ADJUSTMENT-TABLE paragraph is declared but the body is
missing. What should the analysis look like?

Analyze this source and show me the correct TBD handling.
```

#### Pass Criteria (Negative)

- **Status:** blocked_pending_source (source incompleteness blocks analysis)
- **Does NOT invent** missing procedures, subroutine bodies, or CALL statements
- **Creates blocking TBDs** for each missing source fragment:
  - TBD-*: COMPUTE-RATE paragraph incomplete; CALL statement not provided
  - TBD-*: LOOKUP-ADJUSTMENT-TABLE body missing
- **Documents what IS visible** (e.g., comment indicates GET-BASE-RATE call but code not shown)
- **Refuses to guess** procedure behavior without source
- **Entry Points & Control Flow** sections clearly marked as incomplete
- No files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-program-analyzer. User input: I have RPGLE source for CREDITCHK (OBJ-CREDIT-VALIDATION-001). It validates customer credit limits. Analyze its control flow, file I/O, entry points, and external calls. Provide the analysis in the output contract format."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-program-analyzer. User input: I have RPGLE source for CREDITCHK (OBJ-CREDIT-VALIDATION-001). It validates customer credit limits. Analyze its control flow, file I/O, entry points, and external calls. Provide the analysis in the output contract format."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-program-analyzer. User input: I have RPGLE source for CREDITCHK (OBJ-CREDIT-VALIDATION-001). It validates customer credit limits. Analyze its control flow, file I/O, entry points, and external calls. Provide the analysis in the output contract format."
```

For the negative scenario, substitute the incomplete-source prompt above into
the same commands.

## Pass Example — `legacy-modernization-orchestrator` v0.1.1

| Runtime | Model | Discovery | Trigger | Outcome |
| --- | --- | --- | --- | --- |
| Codex CLI | `gpt-5.4-mini` | loaded | executed + matched pass criteria for positive and negative scenarios | passed |
| Claude Code | `haiku` (Read-only tools) | loaded | executed + matched pass criteria | passed |
| OpenCode | `opencode/minimax-m2.5-free` | loaded | executed + matched pass criteria | passed |

Recorded in `docs/runtime-matrix.md`. Scorecard moved from v0.1.0 (9.0 cap)
to v0.1.1 (9.5, field-pilot ready) at
[docs/reviews/legacy-modernization-orchestrator-v0.1.1-scorecard.md](reviews/legacy-modernization-orchestrator-v0.1.1-scorecard.md).

## Adding A New Skill

When a new skill is added:

1. Append a positive trigger prompt to the "Test Prompts For
   Currently-Implemented Skills" section in the same PR that introduces the
   skill
2. Include a negative-case prompt if the skill has a stop condition
3. Run the protocol in all three runtimes before the skill is merged with
   `passed` status

This keeps the protocol authoritative and prevents per-skill drift.
