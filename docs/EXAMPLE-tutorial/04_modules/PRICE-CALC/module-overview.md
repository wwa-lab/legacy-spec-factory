# Module Overview: PRICE-CALC

## Metadata

- module_slug: PRICE-CALC
- review_status: approved
- evidence_ids: [EV-SRC-001, EV-DDS-001, EV-SME-001]

## In-Scope Artifacts

- Inventory: [`01_inventory/inventory.yaml`](../../01_inventory/inventory.yaml)
- Programs: [PRICECALC](../../02_programs/PRICE-CALC/PRICECALC/program-analysis.md)
- Flows: [calculate-price](../../03_flows/PRICE-CALC/flow-calculate-price.md)

## Evidence View Index

| View | File | Status |
| --- | --- | --- |
| Program Flow | [`03-program-flow.md`](03-program-flow.md) | approved |
| Data Flow | [`04-data-flow.md`](04-data-flow.md) | approved |

## Capability Seeds

| CAP ID | Display Name | Primary Flows |
| --- | --- | --- |
| CAP-PRICE-CALCULATION | Calculate final unit price for one order line | FLOW-PRICE-CALCULATE-LINE |

## Business Rule Seeds

| BR ID | Rule | Evidence IDs | Knowledge Type | Review Status |
| --- | --- | --- | --- | --- |
| BR-PRICE-001 | Final price = base × qty × (1 - tier_discount) × (1 - promo_discount), rounded to 2dp | EV-SRC-001 | confirmed_from_code | approved |
| BR-PRICE-002 | Promo codes: `SUMMR`/`WINTR` → 5% off; `VIP10` → 10% off; anything else → no promo discount, silent | EV-SRC-001, EV-SME-001 | confirmed_from_code (silent-skip behavior SME-confirmed as intentional) | approved |

## SME Review

- **Decision:** approved (2026-05-16, Jane Doe)
- **Notes:** Both BR seeds confirmed. Promo stacking is hard-coded — any
  future promo type must update PRICECALC source.

## Capability Mapping

```
CAP-PRICE-CALCULATION
   ├── FLOW-PRICE-CALCULATE-LINE
   │       └── PRICECALC
   │              └── reads PRICEFL
   ├── BR-PRICE-001 (formula)
   └── BR-PRICE-002 (promo stacking)
```
