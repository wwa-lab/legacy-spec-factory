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
| Claude Code | `.claude/skills/<name>/SKILL.md` | `claude -p "<prompt>" --model <model> --permission-mode dontAsk --tools Read` |
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

#### Scenario (Positive — Program Analysis Done)

```text
Use /legacy-modernization-orchestrator.

User input:
I have approved program analyses for all programs in the NIGHTLY-RECON scope:
RECONCL, RECON01R, RECON02R, and RECONSQL. Inventory is approved with no
blocking coverage gaps. I need to understand the complete scheduler-submitted
business transaction end-to-end. What should I run next?

Return only:
- current stage
- recommended next skill
- gate check
- next artifact expected
```

#### Pass Criteria (Positive — Program Analysis Done)

- current stage is `Program Analysis Done` or equivalent Stage 3b wording
- recommended next skill is `legacy-ibmi-flow-analyzer`
- Inventory Completeness Gate is reported as passed
- next artifact expected is a `flow-<FLOW-SLUG>.md` / `flow.md` style artifact
- no files are created or edited

#### Scenario (Positive — Flow Analysis Done)

```text
Use /legacy-modernization-orchestrator.

User input:
I have approved flow analyses for AUTH-ONUS, AUTH-BATCH, and AUTH-MANUAL.
All referenced program analyses are approved, inventory is approved, and the
module owner has provided BAU notes for the CARD-AUTH module. I want to
synthesize the business module. What should I run next?

Return only:
- current stage
- recommended next skill
- gate check
- next artifact expected
```

#### Pass Criteria (Positive — Flow Analysis Done)

- current stage is `Flow Analysis Done` or equivalent Stage 3d wording
- recommended next skill is `legacy-ibmi-module-analyzer`
- Inventory Completeness Gate is reported as passed
- next artifact expected mentions `module-overview.md` or the four module views
- no files are created or edited

#### Scenario (Positive — Module Analysis Done)

```text
Use /legacy-modernization-orchestrator.

User input:
I have an approved CARD-AUTH module analysis with all four views approved,
approved flow analyses, approved program analyses, approved inventory, and a
capability seed CAP-CREDIT-LIMIT-ENFORCEMENT. I need a modernization-ready
spec package. What should I run next?

Return only:
- current stage
- recommended next skill
- gate check
- next artifact expected
```

#### Pass Criteria (Positive — Module Analysis Done)

- current stage is `Module Analysis Done` or equivalent Stage 3f wording
- recommended next skill is `legacy-spec-writer`
- gate check names the Evidence Approval Gate or says it is ready to check
- next artifact expected mentions `spec.yaml` and `spec.md`
- no files are created or edited

#### Scenario (Negative — Forward Handoff Blocked)

```text
Use /legacy-modernization-orchestrator.

User input:
I have spec.yaml for CAP-CREDIT-LIMIT-ENFORCEMENT, but status is in_review.
One critical BR still has review_status: needs_sme_review, and one blocking
open question remains. Can I hand this to build-agent-skill now?

Return only:
- current stage
- gate status
- next skill (or "stop")
```

#### Pass Criteria (Negative — Forward Handoff Blocked)

- refuses forward SDLC handoff
- reports Forward Handoff Gate as blocked
- cites the unapproved critical BR and blocking open question
- routes back to `legacy-spec-writer`, `legacy-spec-reviewer` manual fallback,
  or SME approval/remediation rather than `build-agent-skill`
- no files are created or edited

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

### `legacy-ibmi-evidence-intake`

#### Scenario (Positive — Redacted Evidence Manifest)

```text
Use /legacy-ibmi-evidence-intake.

User input:
I have redacted RPGLE source CREDITCHK, redacted DDS CUSTPF, and a redacted
spool sample for capability CREDIT-CHECK. Data owner export approval is
recorded. Redaction owner approval is recorded with date 2026-05-15. SME
approval by Credit Operations is recorded with date 2026-05-16.
Help me prepare the evidence manifest.

Return only:
- required output files
- whether downstream inventory may run
- compact status

Do not create or edit files.
```

#### Pass Criteria (Positive)

- lists `evidence-manifest.yaml`, `redaction-log.md`, and
  `evidence-intake-review-checklist.md`
- reports that downstream inventory may run only after redaction owner and SME
  approval are recorded
- returns `status: pass` or `pass_with_warnings` only if approvals are named
- does not inspect or quote raw unredacted evidence
- no files are created or edited

#### Scenario (Negative — Unknown Sensitivity)

```text
Use /legacy-ibmi-evidence-intake.

User input:
I have a transaction sample for CREDIT-CHECK, but sensitivity is unknown and
no redaction owner has reviewed it yet. Can I give this to inventory now?

Return only:
- status
- blocking reason
- remediation_step

Do not create or edit files.
```

#### Pass Criteria (Negative)

- reports status as `blocked`
- states that unknown sensitivity blocks inventory
- routes remediation to redaction owner / evidence-intake rework
- does not inspect, summarize, or quote raw transaction content
- no files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-evidence-intake. User input: I have redacted RPGLE source CREDITCHK, redacted DDS CUSTPF, and a redacted spool sample for capability CREDIT-CHECK. Data owner export approval is recorded. Redaction owner approval is recorded with date 2026-05-15. SME approval by Credit Operations is recorded with date 2026-05-16. Help me prepare the evidence manifest. Return only: required output files; whether downstream inventory may run; compact status. Do not create or edit files."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-evidence-intake. User input: I have redacted RPGLE source CREDITCHK, redacted DDS CUSTPF, and a redacted spool sample for capability CREDIT-CHECK. Data owner export approval is recorded. Redaction owner approval is recorded with date 2026-05-15. SME approval by Credit Operations is recorded with date 2026-05-16. Help me prepare the evidence manifest. Return only: required output files; whether downstream inventory may run; compact status. Do not create or edit files."
```

OpenCode does not expose a read-only flag in `opencode run --help`. Run OpenCode
smoke in a disposable copy or worktree, then verify the real repository stayed
clean. Example:

```bash
tmpdir="$(mktemp -d /tmp/lsf-evidence-intake-smoke.XXXXXX)"
rsync -a --delete --exclude .git ./ "$tmpdir/"
opencode run --dir "$tmpdir" -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-evidence-intake. User input: I have redacted RPGLE source CREDITCHK, redacted DDS CUSTPF, and a redacted spool sample for capability CREDIT-CHECK. Data owner export approval is recorded. Redaction owner approval is recorded with date 2026-05-15. SME approval by Credit Operations is recorded with date 2026-05-16. Help me prepare the evidence manifest. Return only: required output files; whether downstream inventory may run; compact status. Do not create or edit files."
rm -rf "$tmpdir"
git status --short
```

For the negative scenario, substitute the unknown-sensitivity prompt above into
the same `codex exec` / `claude -p` commands and the disposable OpenCode command.

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

### `legacy-ibmi-flow-analyzer`

#### Scenario (Positive — Scheduler + Batch Job Flow)

```text
Use /legacy-ibmi-flow-analyzer.

User input:
I have a scheduler entry NIGHTLY-RECON that fires daily at 22:00 and submits
a batch job. The batch calls four RPG programs in sequence: RECONCL (CL entry,
orchestrator), RECON01R (validates transactions), RECON02R (builds exception
report), RECONSQL (final cross-check with GL ledger via SQL). All four program
analyses are approved. Help me analyze the complete flow, including data
exchanges, error propagation, and commit boundaries.

Return the flow analysis with all 9 sections populated.
```

#### Pass Criteria (Positive)

The response must include all of the following:

- **Metadata section:** Flow ID (FLOW-NIGHTLY-RECON-001 or similar), Trigger Model correctly identified as Scheduler or Scheduler + SBMJOB, all 4 nodes listed
- **Trigger Context:** Scheduler entry name, frequency (daily 22:00), SBMJOB command details, SLA (must complete before 06:00)
- **Sequence Diagram:** Scheduler entry → SBMJOB → 4 nodes in sequence, all edges traced
- **Nodes section:** 4 programs with roles (orchestrator, worker, reporter, data-access), all marked as approved program-analyses
- **Edges section:** 5 edges including scheduler-fire edge and CALL edges between nodes, all with call sites and conditions
- **Cross-Program Data Flow:** RUNDATE parameter, shared file TXNLOGPF, shared file GLPOSTPF, spool RECONPRT, DTAQ message, data area with completion flag
- **Branch Points:** RC-driven conditional branches in orchestrator CL program
- **Error Propagation & Commit Boundaries:** 3 commit boundaries clearly identified, vulnerable windows documented
- **Business Capability Seeds:** SEED-* IDs (not BR-*) for candidate rules like "all transactions for a run date must be reconciled before GL consolidation"
- **TBDs & Review Checklist:** All blocking TBDs resolved; SME review checklist complete; status = draft or approved (not blocked)
- No files are created or edited

#### Scenario (Negative — Missing Program Analysis)

```text
Use /legacy-ibmi-flow-analyzer.

User input:
I have a flow definition for WEB-ORDER. The entry point is an MQ queue
WEBORDER.IN. The flow calls WEBORDIN → ORDVAL → ORDPRICE → ORDPERSIST → WEBORDOUT.
Program analyses exist for WEBORDIN, ORDVAL, and ORDPERSIST, but ORDPRICE and
WEBORDOUT have no program-analysis yet. What should I do?

Return the flow analysis output showing the correct stop/blocking behavior.
```

#### Pass Criteria (Negative)

- **Status:** blocked_pending_source (not draft; analysis cannot proceed)
- **Does NOT complete** full 9-section analysis
- **Creates blocking TBDs** for each missing program-analysis:
  - TBD-WEB-ORDER-001: ORDPRICE lacks approved program-analysis; routes to legacy-ibmi-program-analyzer
  - TBD-WEB-ORDER-002: WEBORDOUT lacks approved program-analysis; routes to legacy-ibmi-program-analyzer
- **Sequence Diagram:** Shows 5 nodes; marks 2 as ❌ MISSING
- **Refuses to guess** ORDPRICE or WEBORDOUT behavior
- **Nodes table:** Shows all 5; marks ORDPRICE and WEBORDOUT with MISSING status
- **TBDs section:** Clearly distinguishes `blocking: pending_source` from non-blocking TBDs
- **Routing decision:** Routes to program-analyzer, not to next skill
- No files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-flow-analyzer. User input: I have a scheduler entry NIGHTLY-RECON that fires daily at 22:00 and submits a batch job. The batch calls four RPG programs in sequence: RECONCL (CL entry, orchestrator), RECON01R (validates transactions), RECON02R (builds exception report), RECONSQL (final cross-check with GL ledger via SQL). All four program analyses are approved. Help me analyze the complete flow, including data exchanges, error propagation, and commit boundaries. Return the flow analysis with all 9 sections populated."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-flow-analyzer. User input: I have a scheduler entry NIGHTLY-RECON that fires daily at 22:00 and submits a batch job. The batch calls four RPG programs in sequence: RECONCL (CL entry, orchestrator), RECON01R (validates transactions), RECON02R (builds exception report), RECONSQL (final cross-check with GL ledger via SQL). All four program analyses are approved. Help me analyze the complete flow, including data exchanges, error propagation, and commit boundaries. Return the flow analysis with all 9 sections populated."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-flow-analyzer. User input: I have a scheduler entry NIGHTLY-RECON that fires daily at 22:00 and submits a batch job. The batch calls four RPG programs in sequence: RECONCL (CL entry, orchestrator), RECON01R (validates transactions), RECON02R (builds exception report), RECONSQL (final cross-check with GL ledger via SQL). All four program analyses are approved. Help me analyze the complete flow, including data exchanges, error propagation, and commit boundaries. Return the flow analysis with all 9 sections populated."
```

For the negative scenario, substitute the missing-program-analysis prompt above into
the same commands.

### `legacy-ibmi-module-analyzer`

#### Scenario (Positive — Complete Module)

```text
Use /legacy-ibmi-module-analyzer.

User input:
I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001),
approved program analyses for all programs, an approved inventory with the
AUTH-MODULE scope confirmed, and BAU notes from the Module Owner.
Module slug is AUTH-MODULE, business name is "Authorization Processing". Help me
synthesize the four-view module analysis.

Return the module-overview.md and all four views (01-operation-flow.md through
04-data-flow.md) following the output contract format.
```

#### Pass Criteria (Positive)

The response must include all of the following:

- **Module-overview.md:** MODULE-AUTH-MODULE-001 ID, Scope Statement, In-scope Flows list with FLOW-* links, View Index table showing all 4 views with status, at least one CAP-* capability seed, Module Review Checklist with cross-view consistency checks, no blocking TBDs (or only non-blocking TBDs)
- **01-operation-flow.md:** Business Scope, Business Actors (ACTOR-*), Business Events (EVENT-*), BAU Rhythm, Manual Intervention Points, Exception Lifecycle, Business Rule Seeds (BR-*), evidence linking to SME or BAU source
- **02-system-flow.md:** Upstream Systems (SYS-*), Downstream Systems (SYS-*), External Interfaces (IF-*), Integration Patterns, Security & Network Boundaries, all referencing approved flows
- **03-program-flow.md:** Flow Inventory (all 3 flows), Cross-Flow Dependencies (shared file), Shared Sub-Programs, Call Topology, evidence from approved program/flow analyses
- **04-data-flow.md:** Data Objects (with OBJ-* and Coupling Score), Lifecycle per object, Coupling Hotspots, DB Table Relationships, Cross-Module Dependencies, evidence from program analyses
- **Status values:** All views marked as `draft` or `approved_with_non_blocking_tbd` (no blocked status; all required evidence present)
- **All four views present:** No view is marked blocked or missing
- **Evidence tagged:** All major actors, systems, programs, data objects, and lifecycle phases link to EV-*, OBJ-*, FLOW-*, or SME confirmation
- No files are created or edited

#### Scenario (Negative — Missing Flow Analysis)

```text
Use /legacy-ibmi-module-analyzer.

User input:
I have approved flow analyses for FLOW-AUTH-001 and FLOW-MANUAL-001, but FLOW-BATCH-001
has no approved flow analysis yet. Module scope includes all three flows.
Inventory is approved. BAU notes are complete. What should the output look like?

Return only:
- the module-overview.md
- the blocked status and reason
```

#### Pass Criteria (Negative)

- **Status:** blocked_pending_source (one required flow analysis is missing)
- **Module-overview.md:** Identifies MODULE-AUTH-MODULE-001 and the three flows; shows FLOW-BATCH-001 marked as MISSING
- **Does NOT produce** any of the four views
- **Creates blocking TBD:** TBD-AUTH-MODULE-001: FLOW-BATCH-001 lacks approved flow-analysis; routes to legacy-ibmi-flow-analyzer
- **View Index:** Shows all 4 views but marks View 1–4 as blocked or incomplete due to missing flow
- **Refuses to synthesize** views without complete flow and program evidence
- No files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-ibmi-module-analyzer. User input: I have three approved flow analyses (FLOW-AUTH-001, FLOW-BATCH-001, FLOW-MANUAL-001), approved program analyses for all programs, an approved inventory with the AUTH-MODULE scope confirmed, and BAU notes from the Module Owner. Module slug is AUTH-MODULE, business name is \"Authorization Processing\". Help me synthesize the four-view module analysis. Return the module-overview.md and all four views (01-operation-flow.md through 04-data-flow.md) following the output contract format."
```

For the negative scenario, substitute the missing-flow-analysis prompt above into
the same commands.

### `legacy-spec-writer`

#### Scenario (Positive — All Analyses Approved)

```text
Use /legacy-spec-writer.

User input:
I have:
- Approved module analysis (CARD-AUTH module, all four views approved)
- Approved flow analyses: ONUS-AUTH, NIGHTLY-RECON, MANUAL-AUTH (all approved)
- Approved program analyses for all 8 programs referenced by those flows
- Approved inventory with CARD-AUTH scope confirmed
- SME owner: Anna Chen (capability owner)
- Capability seed: CAP-CREDIT-LIMIT-ENFORCEMENT
- Target platform: Java 21 + Spring Boot 3 + PostgreSQL

Help me write the spec for credit limit enforcement. Return the spec.yaml structure, spec.md outline, and indication that spec-review.md and traceability.md will be produced.
```

#### Pass Criteria (Positive)

The response must include all of the following:

- **spec.yaml structure:** SPEC-CREDIT-LIMIT-ENFORCEMENT-001 ID, CAP-CREDIT-LIMIT-ENFORCEMENT ownership, all top-level keys from schemas/spec.schema.yaml
- **Capability & scope:** capability.owner = Anna Chen, scope.in_scope lists credit limit validation, scope.out_of_scope excludes card issuance
- **Evidence section:** All EV-* IDs referenced by the three flows and eight programs are listed with evidence_strength (confirmed_from_code / confirmed_by_sme)
- **Observed Behaviors (BEH-*):** At least 3 behaviors (e.g., "validates transaction against customer credit limit", "propagates hold decision to downstream") each tracing to ≥1 EV-*
- **Business Rules (BR-*):** At least 2 business rules lifted from module View 1 seeds, each with review_status (draft or approved based on SME confirmation), linked to supporting BEH-*
- **Modernization Decisions (DEC-*):** At least 1 decision (e.g., "store transaction audit in append-only table"), referencing BR-* or target_platform
- **Data model:** Target entities (e.g., CreditTransaction, CustomerCreditLimit) mapped to legacy OBJ-* with field mappings
- **Process flow & I/O:** process_flow.steps from the ONUS-AUTH flow analysis, inputs (e.g., transaction), outputs (e.g., hold_decision)
- **Acceptance criteria:** AC-* items validating approved BRs; no ACs for draft or needs_sme_review BRs
- **Open questions:** No blocking TBDs for a complete spec; status = draft or in_review (not blocked)
- **spec.md outline:** Human-readable rendering of the same content
- **References to spec-review.md and traceability.md:** Output acknowledges these will be produced
- No files are created or edited

#### Scenario (Negative — Incomplete Upstream Analysis)

```text
Use /legacy-spec-writer.

User input:
I have approved module analysis (CARD-AUTH), approved flow for ONUS-AUTH, but
NIGHTLY-RECON flow analysis is still in draft status. I also have approved
program analyses for 7 of the 8 programs. Inventory is approved, SME is Anna Chen.
Can I produce the spec anyway?

Return:
- the blocking TBD(s) and reason
- where the analysis is incomplete
```

#### Pass Criteria (Negative)

- **Status:** blocked_pending_source (incomplete upstream analyses block spec synthesis)
- **Does NOT produce** a complete spec.yaml
- **Creates blocking TBDs:**
  - TBD-CREDIT-LIMIT-ENFORCEMENT-001: NIGHTLY-RECON flow analysis is draft; needs approval (routes to legacy-ibmi-flow-analyzer)
  - TBD-CREDIT-LIMIT-ENFORCEMENT-002: One program analysis missing or draft (routes to legacy-ibmi-program-analyzer)
- **Refuses to invent** missing behavior or business rules from incomplete analyses
- **Identifies what IS available:** Lists ONUS-AUTH, 7 complete programs, and notes what blocks proceeding
- **Routing:** Routes to flow-analyzer for NIGHTLY-RECON and program-analyzer for the 8th program
- No files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-spec-writer. User input: I have: - Approved module analysis (CARD-AUTH module, all four views approved) - Approved flow analyses: ONUS-AUTH, NIGHTLY-RECON, MANUAL-AUTH (all approved) - Approved program analyses for all 8 programs referenced by those flows - Approved inventory with CARD-AUTH scope confirmed - SME owner: Anna Chen (capability owner) - Capability seed: CAP-CREDIT-LIMIT-ENFORCEMENT - Target platform: Java 21 + Spring Boot 3 + PostgreSQL. Help me write the spec for credit limit enforcement. Return the spec.yaml structure, spec.md outline, and indication that spec-review.md and traceability.md will be produced."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-spec-writer. User input: I have: - Approved module analysis (CARD-AUTH module, all four views approved) - Approved flow analyses: ONUS-AUTH, NIGHTLY-RECON, MANUAL-AUTH (all approved) - Approved program analyses for all 8 programs referenced by those flows - Approved inventory with CARD-AUTH scope confirmed - SME owner: Anna Chen (capability owner) - Capability seed: CAP-CREDIT-LIMIT-ENFORCEMENT - Target platform: Java 21 + Spring Boot 3 + PostgreSQL. Help me write the spec for credit limit enforcement. Return the spec.yaml structure, spec.md outline, and indication that spec-review.md and traceability.md will be produced."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-spec-writer. User input: I have: - Approved module analysis (CARD-AUTH module, all four views approved) - Approved flow analyses: ONUS-AUTH, NIGHTLY-RECON, MANUAL-AUTH (all approved) - Approved program analyses for all 8 programs referenced by those flows - Approved inventory with CARD-AUTH scope confirmed - SME owner: Anna Chen (capability owner) - Capability seed: CAP-CREDIT-LIMIT-ENFORCEMENT - Target platform: Java 21 + Spring Boot 3 + PostgreSQL. Help me write the spec for credit limit enforcement. Return the spec.yaml structure, spec.md outline, and indication that spec-review.md and traceability.md will be produced."
```

For the negative scenario, substitute the incomplete-upstream-analysis prompt above into
the same commands.

### `legacy-brd-to-sdd-handoff`

#### Scenario (Positive — Approved BRD And Spec)

```text
Use /legacy-brd-to-sdd-handoff.

User input:
The CREDIT-CHECK capability has approved BRD and spec packages, no unresolved
blocking TBDs, all approved BR-* have approved AC-*, evidence manifest
package_state is approved_for_inventory with all referenced EV-* resolved and
approved, and the capability owner John Smith is available to sign off on the
handoff.

Return only:
- detected skill
- status
- required output files
- evidence gate result
- signoff requirement

Do not create or edit files.
```

#### Pass Criteria (Positive)

The response must include all of the following:

- detected skill is `legacy-brd-to-sdd-handoff`
- status is `approved`, `pass`, or `approved_with_non_blocking_tbd` /
  `pass_with_warnings` only when the response explicitly carries a
  non-blocking TBD forward
- required output files are exactly `sdd-handoff.yaml`, `sdd-handoff.md`,
  `atlas-context-pack.json`, `handoff-review.md`, and `traceability.md`
- evidence gate is reported as passed against the evidence-intake manifest
  contract
- signoff requirement names a responsible SME / owner and requires name, role,
  and ISO date
- no files are created or edited

#### Scenario (Negative — Missing Spec)

```text
Use /legacy-brd-to-sdd-handoff.

Contract-only no-write smoke test. Do not inspect or rely on the actual
workspace filesystem. Report the files the skill contract would emit, not
actual created files.

User input:
The CUST-ONBOARD capability has an approved BRD with SME sign-off, but
05_specs/CUST-ONBOARD/spec.yaml does not exist. A stakeholder asks to package
the BRD for Atlas anyway.

Return exactly these labels, one per line:
- detected skill
- status
- blocking finding
- would_write_files
- would_not_write_files
- next skill
```

#### Pass Criteria (Negative)

- status is `blocked`
- blocking finding identifies the missing approved `spec.yaml`
- next skill is `legacy-spec-writer`
- `would_write_files` contains only `handoff-review.md` and
  `blocking-finding.yaml`
- `would_not_write_files` contains `sdd-handoff.yaml`, `sdd-handoff.md`,
  `atlas-context-pack.json`, and `traceability.md`
- refuses to package the BRD directly for Atlas
- no files are created or edited

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-brd-to-sdd-handoff. User input: The CREDIT-CHECK capability has approved BRD and spec packages, no unresolved blocking TBDs, all approved BR-* have approved AC-*, evidence manifest package_state is approved_for_inventory with all referenced EV-* resolved and approved, and the capability owner John Smith is available to sign off on the handoff. Return only: detected skill; status; required output files; evidence gate result; signoff requirement. Do not create or edit files."
```

```bash
claude -p "Use /legacy-brd-to-sdd-handoff. User input: The CREDIT-CHECK capability has approved BRD and spec packages, no unresolved blocking TBDs, all approved BR-* have approved AC-*, evidence manifest package_state is approved_for_inventory with all referenced EV-* resolved and approved, and the capability owner John Smith is available to sign off on the handoff. Return only: detected skill; status; required output files; evidence gate result; signoff requirement. Do not create or edit files." \
  --model haiku --permission-mode dontAsk --tools Read
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-brd-to-sdd-handoff. User input: The CREDIT-CHECK capability has approved BRD and spec packages, no unresolved blocking TBDs, all approved BR-* have approved AC-*, evidence manifest package_state is approved_for_inventory with all referenced EV-* resolved and approved, and the capability owner John Smith is available to sign off on the handoff. Return only: detected skill; status; required output files; evidence gate result; signoff requirement. Do not create or edit files."
```

For the negative scenario, substitute the missing-spec contract-only prompt
above into the same commands.

### `legacy-step-contract`

#### Scenario (Positive — Review A Filled Step Contract)

```text
Use /legacy-step-contract.

User input:
Review the filled Step Contract example at
skills/legacy-step-contract/examples/inventory-pass/step-contract-block.md.
Return only:
- whether the INPUT, EXECUTION, OUTPUT, and VALIDATION sections are present
- compact validation result status
- downstream_next_step
- remediation_step
```

#### Pass Criteria (Positive)

The response must include all of the following:

- identifies all four sections: INPUT, EXECUTION, OUTPUT, VALIDATION
- reports status as `pass`
- reports `downstream_next_step: legacy-ibmi-program-analyzer`
- reports `remediation_step: none`
- does not invent IBM i objects or business rules
- does not edit files

#### Scenario (Negative — Missing SME Owner)

```text
Use /legacy-step-contract.

User input:
I am authoring a Step Contract for inventory. The redaction gate is clear and
the evidence scope has EV-CREDIT-CHECK-001, but sme_required is yes and
sme_owner is blank. Can the inventory step execute?

Return only:
- status
- blocking category
- required remediation_step
```

#### Pass Criteria (Negative)

- reports status as `blocked`
- classifies the blocker under `sme_questions` or equivalent SME-owner missing category
- says the step must not execute until an SME owner is assigned
- does not route downstream to program analysis
- does not edit files

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-step-contract. User input: Review the filled Step Contract example at skills/legacy-step-contract/examples/inventory-pass/step-contract-block.md. Return only: whether the INPUT, EXECUTION, OUTPUT, and VALIDATION sections are present; compact validation result status; downstream_next_step; remediation_step."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-step-contract. User input: Review the filled Step Contract example at skills/legacy-step-contract/examples/inventory-pass/step-contract-block.md. Return only: whether the INPUT, EXECUTION, OUTPUT, and VALIDATION sections are present; compact validation result status; downstream_next_step; remediation_step."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-step-contract. User input: Review the filled Step Contract example at skills/legacy-step-contract/examples/inventory-pass/step-contract-block.md. Return only: whether the INPUT, EXECUTION, OUTPUT, and VALIDATION sections are present; compact validation result status; downstream_next_step; remediation_step."
```

For the negative scenario, substitute the missing-SME-owner prompt above into
the same commands.

### `legacy-step-validator`

#### Scenario (Positive — Validate Pass Example)

```text
Use /legacy-step-validator.

User input:
Validate the example package at
skills/legacy-step-validator/examples/pass/step-validation-report.md.
Return only:
- detected step_type
- status
- blocking_items
- downstream_next_step
- remediation_step
```

#### Pass Criteria (Positive)

The response must include all of the following:

- detects or reports step type as `inventory`
- reports status as `pass`
- reports `blocking_items: []`
- reports `downstream_next_step: legacy-ibmi-program-analyzer`
- reports `remediation_step: none`
- does not approve any new SME decision beyond the recorded example
- does not edit files

#### Scenario (Negative — Validate Blocked Example)

```text
Use /legacy-step-validator.

User input:
Validate the blocked example package at
skills/legacy-step-validator/examples/blocked/.
Return only:
- detected step_type
- status
- blocking_items
- downstream_next_step
- remediation_step
```

#### Pass Criteria (Negative)

- detects or reports step type as `module`
- reports status as `blocked`
- lists exactly four blocking findings:
  - `FIND-CARD-AUTH-001`
  - `FIND-CARD-AUTH-002`
  - `FIND-CARD-AUTH-003`
  - `FIND-CARD-AUTH-004`
- reports `downstream_next_step: none`
- reports `remediation_step: legacy-ibmi-flow-analyzer`
- does not edit files

#### Reference Commands

```bash
codex exec -C . -s read-only --ephemeral -m gpt-5.4-mini \
  "Use /legacy-step-validator. User input: Validate the example package at skills/legacy-step-validator/examples/pass/step-validation-report.md. Return only: detected step_type; status; blocking_items; downstream_next_step; remediation_step."
```

```bash
claude -p --model haiku --permission-mode dontAsk --tools Read --max-budget-usd 0.20 \
  "Use /legacy-step-validator. User input: Validate the example package at skills/legacy-step-validator/examples/pass/step-validation-report.md. Return only: detected step_type; status; blocking_items; downstream_next_step; remediation_step."
```

```bash
opencode run -m opencode/minimax-m2.5-free \
  "Use /legacy-step-validator. User input: Validate the example package at skills/legacy-step-validator/examples/pass/step-validation-report.md. Return only: detected step_type; status; blocking_items; downstream_next_step; remediation_step."
```

For the negative scenario, substitute the blocked-example prompt above into the
same commands.

## Pass Example — `legacy-step-contract` v0.1.1

| Runtime | Model | Discovery | Trigger | Outcome |
| --- | --- | --- | --- | --- |
| Codex CLI | `gpt-5.4-mini` | loaded | positive and negative scenarios executed | passed |
| Claude Code | `haiku` (Read-only tools) | loaded | positive and negative scenarios executed | passed |
| OpenCode | `opencode/minimax-m2.5-free` | loaded | positive and negative scenarios executed | passed |

Positive smoke confirmed all four sections were present and returned
`status: pass`, `downstream_next_step: legacy-ibmi-program-analyzer`, and
`remediation_step: none`.

Negative smoke confirmed `sme_required: yes` with empty `sme_owner` blocks
execution and requires SME owner assignment before inventory can run.

Recorded in `docs/runtime-matrix.md`. The refreshed v0.1.1 scorecard is
recorded at
`docs/reviews/legacy-step-contract-v0.1.1-scorecard.md`.

## Pass Example — `legacy-step-validator` v0.1.1

| Runtime | Model | Discovery | Trigger | Outcome |
| --- | --- | --- | --- | --- |
| Codex CLI | `gpt-5.4-mini` | loaded | positive and negative scenarios executed | passed |
| Claude Code | `haiku` (Read-only tools) | loaded | positive and negative scenarios executed | passed |
| OpenCode | `opencode/minimax-m2.5-free` | loaded | positive and negative scenarios executed | passed |

Positive smoke confirmed inventory pass output with no blocking findings and
`downstream_next_step: legacy-ibmi-program-analyzer`.

Negative smoke confirmed module blocked output with exactly four blocking
findings (`FIND-CARD-AUTH-001` through `FIND-CARD-AUTH-004`),
`downstream_next_step: none`, and
`remediation_step: legacy-ibmi-flow-analyzer`.

Recorded in `docs/runtime-matrix.md`. The refreshed v0.1.1 scorecard is
recorded at
`docs/reviews/legacy-step-validator-v0.1.1-scorecard.md`.

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
