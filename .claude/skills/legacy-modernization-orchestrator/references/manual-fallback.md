# Manual Fallback Reference

The reverse chain has 11 skills but only one is implemented today. The
orchestrator must still be useful — it should tell users what to do manually
until each planned skill exists.

## Principle

For every planned skill, produce the **same artifact shape** the implemented
version would produce, following:

- the artifact's defined output contract (see the README artifact chain)
- the schema in `schemas/spec.schema.yaml` for any spec-shaped output
- the ID conventions in `docs/id-conventions.md`
- the taxonomy in `docs/evidence-and-knowledge-taxonomy.md`

This way, downstream skills (when implemented) can consume the manually
produced artifact without rework.

## Per-Skill Fallback

### `legacy-ibmi-program-analyzer` (Planned)

**Goal:** explain RPGLE/CLLE/COBOL-on-IBM-i logic, control flow, data flow.

**Manual workflow:**

1. For each in-scope program, read the source with the team
2. Produce `program-analysis-<program-id>.md` containing:
   - entry points and parameters
   - main control flow (subroutines, jumps, indicators)
   - file I/O (`SETLL`, `READE`, `CHAIN`, etc.) with key fields
   - external calls
   - error handling paths
   - linked evidence IDs (`EV-*`) for each non-trivial behavior
3. Tag each behavior with `evidence_strength` from the taxonomy
4. Create `TBD-*` IDs for anything unclear, do not guess

**Quality bar:** an SME reading the document should be able to predict what
the program does without re-reading the source.

### `legacy-ibmi-call-graph-analyzer` (Planned)

**Manual workflow:**

1. Extract a list of all `CALL` / `CALLP` / `SBMJOB` from each program
2. Build a graph (Mermaid or simple table) showing program → program edges
3. Tag each edge with confidence and evidence
4. Mark unresolved calls (target program not in inventory) as
   `TBD-<SLUG>-<NNN>` and update the inventory's `coverage_gaps`

### `legacy-ibmi-crud-matrix-analyzer` (Planned)

**Manual workflow:**

1. For each program, list each file with the access kind: `reads | writes |
   updates | deletes`
2. Produce a markdown table: rows = programs, columns = files, cells = CRUD
3. Tag each row with evidence IDs

### `legacy-ibmi-dds-schema-analyzer` (Planned)

**Manual workflow:**

1. Read each `PF`, `LF`, `DSPF`, `PRTF` source
2. Produce `data-dictionary.md` (PF/LF fields with type, length, decimals,
   keys) and `screen-map.md` (DSPF/PRTF formats, indicators, function keys)
3. Note CCSID and packed/zoned decimal semantics where relevant
4. Tag inferred semantics with `needs_sme_review`

### `legacy-ibmi-runtime-evidence-miner` (Planned)

**Manual workflow:**

1. Collect redacted job log, spool, and sample transactions per
   `docs/data-collection-and-redaction.md`
2. Build `runtime-evidence.jsonl`, one event per line, with fields:
   `id`, `source_type`, `location`, `summary`, `evidence_strength:
   observed_in_runtime`, `linked_objects: [OBJ-*]`
3. Reference these from program-analysis or business-rules artifacts

### `legacy-business-rule-miner` (Planned)

**Manual workflow:**

1. For each significant behavior found in program analysis or runtime
   evidence, ask: is this a **business rule** or a **technical workaround**?
2. For business rules, write a `BR-<SLUG>-<NNN>` entry with:
   - `knowledge_type: inferred_business_rule` (or `observed_behavior` if it
     is purely behavior with no inference)
   - linked `evidence_ids`
   - `linked_behaviors`
   - `confidence` and `review_status: needs_sme_review`
3. Reject anything that cannot be tied to evidence

### `legacy-capability-mapper` (Planned)

**Manual workflow:**

1. Group rules with common business intent into capabilities
2. Produce `capability-map.md` listing each capability with its constituent
   `BR-*` IDs and its `CAP-<SLUG>-<NNN>` ID
3. Capabilities do not have to align with program boundaries — that is the
   point

### `legacy-spec-writer` (Planned, MVP candidate)

**Manual workflow:**

1. Use `templates/spec.yaml` as the starting point
2. Fill every field defined in `schemas/spec.schema.yaml`
3. Render a `spec.md` view from the same content for human review
4. Set `status: draft` until reviewer pass

### `legacy-spec-reviewer` (Planned)

**Manual workflow:**

1. Run the spec through the gate criteria in
   [references/gates.md](gates.md), Gate 3 + Gate 4 criteria
2. Produce `review-report.md` listing pass / blocking findings per criterion
3. Update `spec.yaml.status: in_review` and add review_notes

### `legacy-equivalence-test-generator` (Planned)

**Manual workflow:**

1. For every business-critical rule, design at least one golden master test
   case
2. Test inputs and expected outputs must come from runtime evidence, not
   guesses
3. Save under `06_quality/golden-master-tests.md` with `TC-*` IDs traceable
   back to `BR-*` IDs

## When to Stop Using a Manual Fallback

Switch back to the orchestrator-recommended skill the moment it becomes
implemented (status moves from `Planned` to `Implemented` in repository
`README.md#target-skill-family`). The manual artifact, if it followed the
contract, drops in unchanged.

If the artifact does not follow the contract, treat the implemented skill as
authoritative and regenerate — do not patch the manual artifact to look like
it came from the skill.
