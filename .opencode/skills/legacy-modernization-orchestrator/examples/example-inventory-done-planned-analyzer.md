# Example Routing: Inventory Done -> Planned Analyzer Manual Fallback

## User Input

> "The inventory for CREDIT-CHECK is SME-approved. `inventory.yaml` has
> `sme_review.decision: approved`, `object-map.md` is complete, and the main
> program is ORDENTR. I want to understand ORDENTR's logic next. Which skill
> should I use?"

## Orchestrator Output

```markdown
## Workflow Decision

- **Current Stage:** Inventory Done (Stage 2c)
- **Desired Outcome:** Program Analysis
- **Recommended Next Skill:** `legacy-ibmi-program-analyzer` (status: planned)
- **Why:** Inventory has passed the completeness gate, so the next safest
  step is program-level analysis for ORDENTR. The analyzer skill is not
  implemented yet, so use the manual fallback and keep the output shape stable.

## Routing Notes

- **Stage skip safe?** No. Jumping directly to business rules would skip the
  source-backed behavior analysis needed to separate observed behavior from
  inferred business rules.
- **Gate check:** Inventory Completeness Gate — pass, based on
  `sme_review.decision: approved` and no unresolved blocking coverage gaps.
- **Minimum input needed next:** ORDENTR source member, referenced copybooks or
  service-program interfaces, file list from `inventory.yaml`, linked evidence
  IDs, and SME owner for ambiguous branches.
- **Route confidence:** High.
- **Next artifact expected:**
  `02_static-analysis/program-analysis-ORDENTR.md`.

## Next Step

- **Invoke:** Manual fallback for `legacy-ibmi-program-analyzer` from
  `references/manual-fallback.md`.
- **Produce:** `program-analysis-ORDENTR.md` with entry points, parameters,
  control flow, file I/O, external calls, error handling, evidence IDs, and
  `TBD-*` IDs for unclear behavior.
- **Save reminder:** Save the analysis under `02_static-analysis/`; it will be
  consumed later by `legacy-business-rule-miner`.
- **SME reminder:** Ask the SME to validate any branch affecting money,
  inventory, compliance, customer status, or posting before treating it as a
  confirmed rule.
- **Manual fallback:** Read ORDENTR with the team, tag each non-trivial
  behavior with evidence strength from `docs/evidence-and-knowledge-taxonomy.md`,
  and do not infer missing business intent without SME review.
```

## Expected Manual Artifact Skeleton

```markdown
# Program Analysis: ORDENTR

## Metadata

- program_id: OBJ-CREDIT-CHECK-ORDENTR
- source_member:
- inventory_source: 01_inventory/inventory.yaml
- review_status: draft

## Entry Points And Parameters

| Entry Point | Parameters | Evidence IDs | Notes |
| --- | --- | --- | --- |

## Control Flow

| Step ID | Description | Evidence IDs | Confidence |
| --- | --- | --- | --- |

## File I/O

| File | Operation | Key Fields | Evidence IDs | Notes |
| --- | --- | --- | --- | --- |

## External Calls

| Target | Call Type | Inputs | Outputs | Evidence IDs | TBD |
| --- | --- | --- | --- | --- | --- |

## Error Handling

| Condition | Legacy Behavior | Evidence IDs | Review Status |
| --- | --- | --- | --- |

## Open Questions

| TBD ID | Question | Blocking | Owner |
| --- | --- | --- | --- |
```
