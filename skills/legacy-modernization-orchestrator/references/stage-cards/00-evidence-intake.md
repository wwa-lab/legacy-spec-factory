# Stage 00: Evidence Intake

**You are here if:** you have raw IBM i artifacts (RPGLE / CLLE / DDS / DB2
metadata / job logs / spool / screen samples / SME notes) and **any** of the
following is true:

- no `evidence-manifest.yaml` exists yet
- any item has `sensitivity: unknown`
- any item is marked `sensitive: yes` without a recorded redaction note

This stage is non-bypassable. The **Redaction Gate** blocks every downstream
skill until it clears.

## Need before starting

- Raw source / metadata / runtime evidence collected from the IBM i system
- Permission from the data owner to redact and store the evidence
- An SME contact for the module under review (name + role)

## Run

- **Skill:** `legacy-ibmi-evidence-intake` (Implemented v0.1.0)
- **Manual fallback:** Follow `docs/data-collection-and-redaction.md`
  step-by-step if the skill is not available in your runtime

## Produce

- **Artifact:** `evidence-manifest.yaml` + `redaction-log.md` + redacted bundle
- **Save under:** `evidence/redacted/` *(relative to your `project.root`,
  e.g. `docs/XXX260004-demo/evidence/redacted/`)* — raw evidence is
  **never** committed
- **Consumed by:** `legacy-ibmi-inventory`

Each evidence item must carry:

- `evidence_id` (e.g. `EV-SRC-001`, `EV-JOBLOG-014`)
- `sensitivity` set to `no` or `redacted` (never `unknown` after intake)
- `redaction_note` if data was masked / replaced

## Gate before advancing

- **Name:** Redaction Gate
- **Check:** every item in `evidence-manifest.yaml` has
  `sensitivity ∈ {no, redacted}` and a recorded SME approval
- **Blocks if:** any item has `sensitivity: unknown` OR raw evidence is in
  scope without a redaction record

## SME action

- **Required:** yes — for sensitivity classification of business data
- **Ask:** "Is field X / dataset Y safe to commit redacted? What must be
  masked or removed?"
- **Recorded in:** `evidence-manifest.yaml[].sme_approval`

## Next card

[`01-evidence-ready.md`](01-evidence-ready.md) — start inventory once
redaction is approved.
