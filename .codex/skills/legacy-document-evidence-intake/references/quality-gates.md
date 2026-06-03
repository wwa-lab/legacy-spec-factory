# Quality Gates

Gate rubric and required fields for `legacy-document-evidence-intake`. The
package-level gate in `intake.manifest.yaml` is the single source of truth for
handoff; per-document gates roll up into it.

## Gate Definitions

| Gate | Meaning | Handoff |
| --- | --- | --- |
| `ready` | Every document extracted cleanly; no macro/security flags; no unresolved authorization or sensitivity issues. | `legacy-module-context-intake` |
| `ready_with_warnings` | Usable output exists, but some documents carry warnings (macros statically extracted, low-confidence OCR, visual review needed, partial conversion, optional binary/converter-dependent source skipped). Warnings travel forward. | `legacy-module-context-intake` |
| `blocked` | At least one hard issue: unauthorized / unknown sensitivity, required redaction missing, or every supplied document is unreadable/skipped with no usable extraction. | `legacy-ibmi-evidence-intake` for auth/sensitivity; tooling-only blocks may feed `legacy-module-context-intake` as degraded metadata |

## Roll-Up Rule

- Any document with `document_gate: blocked` for an authorization or sensitivity
  reason ⇒ package `gate: blocked`, route to `legacy-ibmi-evidence-intake`.
- A document with `document_gate: blocked` only because optional binary,
  converter, OCR, or hosted-agent tooling is unavailable does not by itself
  block the package when at least one other authorized document produced usable
  `FRAG-*` evidence. Roll up to `ready_with_warnings` and carry the skipped
  document in `extraction-warnings.md`.
- If every authorized source is unreadable/skipped only because optional
  tooling, OCR, Python, preview, or readable-export support is unavailable,
  the package may remain `blocked` as an extraction package, but it is not a
  workflow blocker. Carry `DOC-*` metadata, hashes/paths, conversion attempts,
  and warnings forward to `legacy-module-context-intake` as degraded source
  metadata with no strong extracted `FRAG-*` evidence.
- Any document with `security_review_required: true` ⇒ package `gate` capped at
  `ready_with_warnings` until a named reviewer signs off.
- Any warning (OCR, visual-review, partial conversion) on an otherwise usable
  document ⇒ package `gate: ready_with_warnings`.
- Only when every document is `ready` with no warnings ⇒ package `gate: ready`.

## Required Fields (mechanical check)

`intake.manifest.yaml` must declare:

- `package_type: document_evidence_intake`
- `gate` ∈ {`ready`, `ready_with_warnings`, `blocked`}
- `module_slug`, `docset_slug`
- `run_validation.structural_status` ∈ {`pass`, `pass_with_warnings`,
  `blocked`, `not_run`, `tool_unavailable`,
  `tool_unavailable_hosted_agent`}
- `run_validation.artifact_preview_status` ∈ {`not_requested`,
  `skipped_large_docset`, `passed`, `failed`, `timed_out`}
- `run_validation.completion_boundary: stop_after_writeback`
- at least one `documents[]` entry, each with `doc_id`, `path`, `family`,
  `file_type`, `size_bytes`, `sha256`, `sensitivity`, `authorization_status`,
  and `document_gate`
- an `outputs` index listing every package-level file present on disk

Each `documents/<DOC-SLUG>/document.manifest.yaml` must declare its `doc_id`,
`structure` block for its family, `fragments[]` with coordinates, and
`document_gate`. Macro-enabled files must carry a `macro_findings` block with
`executed: false`.

For `ready` / `ready_with_warnings` documents, every path listed in
`normalized_outputs` must exist under the package directory. A skipped optional
binary/converter-dependent document should use `document_gate: blocked`, no
`normalized_outputs`, and a warning explaining the skipped source and manual
remediation.

## Forbidden In `ready` / `ready_with_warnings`

- Any document with `sensitivity: unknown` or `authorization_status: unauthorized`.
- Any conversion recorded `succeeded` without a tool having run.
- Any macro-enabled file missing a security flag.
- Any flow-view classification, business rule, or BRD/spec content.

## Preview And Completion Boundary

Rendered previews of normalized Markdown, CSV, PDF, PNG, SVG, spreadsheet, or
OCR outputs are optional review aids. They are not part of the package gate.
For large docsets, generated page images, or hosted-agent runs, set
`run_validation.artifact_preview_status: skipped_large_docset` or
`not_requested`, then finish after the manifest, quality/warning files,
coordinates, per-document manifests, normalized output list, and validation
status are written.

Do not open every generated page/sheet/slide, do not reopen the same preview,
and do not continue polling changed files after `completion_boundary:
stop_after_writeback` is recorded. Re-enter the package only when a validator
finding names a concrete file to fix.
