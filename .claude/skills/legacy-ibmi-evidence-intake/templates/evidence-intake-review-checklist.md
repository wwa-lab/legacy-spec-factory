# Evidence Intake Review Checklist

## Scope

- capability_slug:
- manifest_path:
- redaction_log_path:
- package_state: draft | blocked | approved_for_inventory
- reviewer:
- review_date:

## Checklist

- [ ] Capability scope is narrow enough for inventory analysis.
- [ ] Data owner approved evidence export.
- [ ] Every evidence item has an `EV-<SLUG>-NNN` ID.
- [ ] Every evidence item has a type and source location.
- [ ] No item has `sensitivity: unknown`.
- [ ] Confidential items have redaction status `approved`.
- [ ] Redaction log records strategy without exposing raw sensitive values.
- [ ] Rule-critical constants, thresholds, coefficients, and amounts are
      preserved or explicitly labeled as synthetic.
- [ ] Field shape, control flow, timestamps, and error codes are preserved where
      downstream analysis needs them.
- [ ] Missing evidence is recorded as `TBD-*`.
- [ ] Contradictory evidence is recorded and routed to SME decision.
- [ ] SME owner and redaction owner are named.
- [ ] Manifest package state and intake decision allow or block
      `legacy-ibmi-inventory` consistently.

## Findings

| ID | Severity | Evidence ID | Finding | Required Action | Blocking |
| --- | --- | --- | --- | --- | --- |
| FIND-<SLUG>-001 | blocking | EV-<SLUG>-001 | <finding> | <action> | yes |

## Inventory Gate Decision

- decision: pass | pass_with_warnings | blocked
- downstream_inventory_allowed: yes | no
- blocking_items:
- non_blocking_items:
- next_step: legacy-ibmi-inventory | evidence-intake rework
