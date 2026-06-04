# Expected Output: Incomplete Module (Negative Case)

## Input

A module definition for `MODULE-ORDER-MGMT-001` with three flows
in scope:

- FLOW-ORDER-INTAKE-001 — ✅ approved flow analysis
- FLOW-ORDER-VALIDATE-001 — ❌ no flow analysis yet (only program analyses exist)
- FLOW-ORDER-FULFILL-001 — ✅ approved

Plus: SME contact for the module is **not yet assigned**.

## Expected Module-Analyzer Behavior

The skill must **refuse to produce the default evidence views** and instead produce a
`module-overview.md` marked `blocked_pending_source` with explicit
routing back to upstream skills.

### Correct module-overview.md

```markdown
# Module: Order Management (MODULE-ORDER-MGMT-001) — BLOCKED

## Metadata
- **Module ID:** MODULE-ORDER-MGMT-001
- **Business Name:** Order Management
- **Scope Statement:** (pending — no SME contact)
- **Module Owner:** **NOT YET ASSIGNED**
- **In-scope Flows:**
  - FLOW-ORDER-INTAKE-001 ✅
  - FLOW-ORDER-VALIDATE-001 ❌ NO FLOW ANALYSIS
  - FLOW-ORDER-FULFILL-001 ✅
- **Status:** **blocked_pending_source**

## Evidence View Index
| View | File | Status |
| --- | --- | --- |
| Program Flow | (not produced) | blocked — flow missing |
| Data Flow | (not produced) | blocked — flow missing |

## Blocking TBDs

### Pending Source (routes back to upstream skills)

- **TBD-ORDER-MGMT-001:** FLOW-ORDER-VALIDATE-001 lacks an approved flow analysis
  - Blocking: pending_source
  - Routes to: `legacy-ibmi-flow-analyzer`
  - Action: produce `flow-ORDER-VALIDATE-001.md` first

### Pending SME Judgment

- **TBD-ORDER-MGMT-002:** No SME contact assigned for this module
  - Blocking: pending_sme_judgment
  - Routes to: SME assignment process
  - Action: identify module owner; module scope and BRD crosswalk cannot be
    approved without SME input

## Why The Module Cannot Be Synthesized Yet

- Program Flow requires all in-scope flow analyses to aggregate.
  Missing FLOW-ORDER-VALIDATE-001 means Program Flow would have a gap of
  unknown size.
- Data Flow depends on every flow's data-flow section. Missing
  flow → missing data exchanges → incomplete picture.
- Business/system context can be carried only as source-backed overview notes
  or TBDs; it must not become standalone generated flow files.

## Routing Decision

The orchestrator should:

1. Route to `legacy-ibmi-flow-analyzer` for FLOW-ORDER-VALIDATE-001
2. In parallel, escalate SME assignment
3. After both unblock, re-run module-analyzer with the same input

## Sign-Off
- **Module Owner:** NOT YET ASSIGNED
- **Decision:** blocked_pending_source
```

## Why This Output Is Correct

- ✅ Refuses to produce Program Flow / Data Flow with missing inputs
- ✅ Does not invent business scope, actors, or BAU
- ✅ Does not produce a partial Program Flow omitting the missing flow silently
- ✅ Explicit routing to flow-analyzer for the missing flow
- ✅ Escalates SME assignment as a separate blocker

## What the Analyzer Must NOT Do

- ❌ Produce a "best-effort" module overview by ignoring FLOW-ORDER-VALIDATE
- ❌ Invent business actors or BAU from program names
- ❌ Write Data Flow with only the data objects visible in the 2 available flows
- ❌ Approve the module despite blocking TBDs

## The Anti-Hallucination Test

Delete one in-scope flow analysis and re-run. If the module-analyzer
produces any output other than a `blocked_pending_source` overview with
explicit routing, something is wrong.

This example exists to make blocked output the obvious, documented
expected behavior — preventing module syntheses from quietly papering
over upstream gaps.
