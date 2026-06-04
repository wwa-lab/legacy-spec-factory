# Reference Pack Lookup

Program analysis may consume project/company reference packs when the user
provides control files, message catalogs, code tables, or data dictionaries.
The original material may be Markdown, CSV, Excel, Word, PDF, or another
authorized enterprise document format. The analyzer should prefer normalized
Markdown/CSV/text lookup outputs, while preserving links back to the original
file coordinates. These files are lookup evidence, not a replacement for
source analysis.

## Recommended Location

Do not store company-private reference content inside the portable skill
directory. Keep it in the project workspace and pass the path to the skill.

Recommended shapes:

```text
00_reference_packs/
  <PACK-SLUG>/
    reference-pack-index.yaml
    source/
      messages.xlsx
      data-dictionary.docx
      control-file-guide.pdf
    normalized/
      messages.md
      messages.csv
      fields.md
      control-values.md
      data-dictionary.md
```

or, for module-specific context:

```text
00_context_packages/
  <MODULE-SLUG>/
    field-dictionary-context.md
    message-catalog-context.md
    control-file-context.md
    document-intake/<DOCSET-SLUG>/
```

If the reference material is still raw Office/PDF/image form, first run
`legacy-document-evidence-intake` or otherwise provide normalized exports with
evidence coordinates. Program analyzer may use already-readable normalized
outputs directly; it should not treat failed or unavailable binary conversion
as proof that a lookup value does not exist.

## Index Contract

Each pack should have a small index so every runtime can discover the same
files without relying on IDE-specific folder conventions.

```yaml
schema_version: "0.1"
pack_id: "REF-CREDIT-CHECK-001"
pack_slug: "CREDIT-CHECK-CONTROL-FILES"
owner: "Credit Operations / Data Steward"
version: "2026-06-04"
authorization_status: "approved_for_analysis" # approved_for_analysis | internal_reference | synthetic | blocked | unknown
document_intake_manifest: "00_context_packages/CREDIT-CHECK/document-intake/CONTROL-FILES/intake.manifest.yaml"
files:
  - path: "normalized/messages.md"
    source_path: "source/messages.xlsx"
    source_format: "xlsx" # md | csv | xlsx | xlsm | xls | docx | doc | pdf | txt
    type: "message_catalog" # message_catalog | field_dictionary | control_file | code_table | data_dictionary | interface_dictionary
    key_columns: ["message_id", "status_code", "description"]
    evidence_coordinate_kind: "workbook / sheet / row / column"
  - path: "normalized/fields.md"
    source_path: "source/data-dictionary.docx"
    source_format: "docx"
    type: "field_dictionary"
    key_columns: ["legacy_field", "standard_field_id", "business_meaning"]
    evidence_coordinate_kind: "heading / paragraph / table"
  - path: "normalized/control-values.md"
    source_path: "source/control-file-guide.pdf"
    source_format: "pdf"
    type: "control_file"
    key_columns: ["file", "field", "value", "meaning"]
    evidence_coordinate_kind: "page / table / row"
```

If there is no YAML index yet, the user may pass explicit Markdown/CSV/text
file paths. For Excel, Word, PDF, image, or scanned files, provide either a
document-intake package or a normalized export path. The analyzer should record
the source file, normalized file, conversion/intake manifest, and version in
Metadata.

## Raw Office / PDF Handling

Use this rule set for non-Markdown inputs:

| Input shape | Analyzer behavior |
| --- | --- |
| `.md`, `.csv`, `.txt` lookup file | Use directly when authorized and indexed. |
| `.xlsx`, `.xlsm`, `.xls` | Prefer normalized Markdown/CSV per sheet from `legacy-document-evidence-intake`; cite workbook/sheet/row/cell coordinates. Never execute macros. |
| `.docx`, `.doc` | Prefer normalized Markdown and table coordinates; cite heading/paragraph/table. |
| `.pdf` | Prefer normalized Markdown/table CSV plus page coordinates; if only a model-visible authorized PDF is available, use visible text/table review with low-confidence warnings. |
| image or scanned document | Use OCR/visual-review Markdown only with confidence warnings and page/region coordinates. |
| conversion unavailable | Record a lookup limitation/TBD; do not claim the code has no matching dictionary/message entry. |

## Markdown Row Patterns

Message catalog rows should support exact lookup by message ID, status code,
return code, SQLSTATE, CPF/MCH/RNX/CPD ID, or shop-local code.

```markdown
| message_id | description | severity | owner | source |
| --- | --- | --- | --- | --- |
| UCC1852 | Account exceeds available credit limit | reject | Credit Ops | MSGF UCCMSGF |
```

Field dictionary rows should support exact lookup by source field, alias,
record format, or standard dictionary ID.

```markdown
| legacy_field | record_format | standard_field_id | business_meaning | domain | version |
| --- | --- | --- | --- | --- | --- |
| CAACLT | CUSTREC | DD-CREDIT-AVAILABLE-LIMIT | Available credit limit | Credit | 2026-06 |
```

Control-file or code-table rows should support exact lookup by file, field,
and value.

```markdown
| file | field | value | meaning | effect |
| --- | --- | --- | --- | --- |
| CRDCTL | RISK_CD | H | High risk customer | route to manual review |
```

## Lookup Rules

1. Read only reference packs explicitly provided by the user, inventory,
   context package, or workspace convention. Do not scan arbitrary private
   folders.
2. Require authorization status `approved_for_analysis`, `internal_reference`,
   or `synthetic` before using content. If authorization is `unknown`, ask for
   approval or mark the lookup unresolved.
3. Use exact identifiers first: message ID, status code, return code,
   SQLSTATE, CPF/MCH/RNX/CPD ID, file name, record format, field name, alias,
   or control-file value.
4. Preserve source identifiers. Write `FIELD_NAME` (business meaning) and,
   when known, carry `standard_field_id`.
5. Record source as `reference pack: <pack_id>/<file>#<anchor-or-row>`.
6. If dictionary/control-file meaning conflicts with code behavior, preserve
   both and create a contradiction TBD. Do not silently choose the prettier
   explanation.
7. If a field or message cannot be matched, mark it unresolved and create an
   Open Item routed to the data steward, message-file owner, or SME.

## How To Use Results

- **Message Inventory**: populate Message Description and Message Source from
  exact message catalog matches.
- **Validation Logic**: use message/control-file definitions to explain the
  meaning of observed status or return codes, while keeping the trigger chain
  source-backed.
- **Key File & Field Logic**: attach business meaning and
  `standard_field_id` to source fields when exact or steward-approved mapping
  exists.
- **File I/O / Field Mutation Matrix**: use dictionary/control-file meaning
  to clarify fields being read, written, updated, or used as keys.
- **TBDs & Blocking Status**: route unmapped fields, unknown message IDs, and
  dictionary/code contradictions to the correct owner.

Reference packs increase understanding quality, but they do not by themselves
prove that a branch, file mutation, or call path exists. Source, runtime, or
SME evidence still controls behavior claims.
