# Atlas Phoenix Lens Mini Output Sample

This folder contains a synthetic, redacted sample that shows the shape of an
Atlas Phoenix Lens discovery handoff.

It is not customer data and does not represent a real production system. The
sample is intentionally small so reviewers can see how a Program Flow Map export
turns into source-backed modernization evidence.

## Scenario

**Flow:** Card account status update

The synthetic flow starts with an account maintenance entry program, calls a
validation program, updates card account status, and writes an audit record.

```text
ARCAD REF / XREF sample
  -> Neo4j Program Flow Map export
  -> program source scan
  -> flow behavior analysis
  -> modernization evidence YAML
```

## Files

| File | Purpose |
| --- | --- |
| `program-flow-export.sample.csv` | Minimal Program Flow Map handoff export |
| `program-analysis.sample.md` | Example single-program evidence summary |
| `flow-analysis.sample.md` | Example cross-program behavior chain |
| `modernization-evidence.sample.yaml` | Machine-readable evidence summary |

## How To Read This Sample

1. Start with `program-flow-export.sample.csv` to see the upstream handoff.
2. Read `program-analysis.sample.md` to see how one program becomes
   source-backed evidence.
3. Read `flow-analysis.sample.md` to see how multiple program findings become a
   business-readable flow.
4. Inspect `modernization-evidence.sample.yaml` to see stable IDs, confidence,
   SME questions, and downstream readiness.

## Boundaries

- Program names, fields, and file names are synthetic.
- Line numbers are illustrative.
- Business rules are marked as `needs_sme_review` unless explicitly confirmed.
- This sample demonstrates artifact shape, not complete IBM i analysis depth.
