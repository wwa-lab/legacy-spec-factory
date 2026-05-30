# Format Strategy

Per-format conversion and extraction procedure for
`legacy-document-evidence-intake`. Deterministic structural extraction plus
manifests is the canonical output. Docling is an optional enhancer, never the
sole source of truth. Legacy binary conversion, OCR, and visual extraction are
optional enhancements: use them only when tooling is already available and
authorized. If unavailable, skip the affected source honestly and continue with
other readable documents.

## General Order Of Operations

1. Detect family from extension and file header.
2. If a legacy binary or OCR/converter-dependent source can be processed with
   already-available tooling, convert or extract it and log the attempt in
   `conversion-log.md`. If no converter/OCR tool is available, record the gap
   honestly, gate that document `blocked`, add a skip warning, and continue with
   other readable documents.
3. Run deterministic structural extraction on the modern container.
4. Optionally enhance with Docling, recording it as one method among others.
5. Mint `FRAG-*` coordinates; record method, coverage, and confidence.

## Excel — `.xlsx`, `.xlsm`, `.xls`

- `.xls` → `.xlsx` via LibreOffice before extraction when LibreOffice is
  already available; otherwise skip the document as optional binary input and
  request `.xlsx` / CSV export.
- Extract: every sheet (including hidden), used ranges, tables, formulas, merged
  cells, hyperlinks, and cross-sheet references.
- Emit Markdown tables plus one CSV per sheet under `normalized/`.
- Coordinate shape: `workbook / sheet / row / column / cell-range`.
- `.xlsm` and macro-enabled files: see Macro Security Policy in `SKILL.md`.
  Never execute. Statically list VBA module names if tooling permits, set
  `security_review_required: true`, and cap the gate at `ready_with_warnings`.

## Word — `.docx`, `.doc`

- `.doc` → `.docx` via LibreOffice before extraction when available; otherwise
  skip the document as optional binary input and request `.docx` / Markdown /
  text export.
- Extract: headings, paragraphs, tables, embedded images, sections.
- Emit Markdown plus extracted images under `normalized/`.
- Coordinate shape: `section / heading / paragraph / table`.

## PowerPoint — `.pptx`, `.ppt`

- `.ppt` → `.pptx` and/or PDF via LibreOffice before extraction when available;
  otherwise skip the document as optional binary input and request `.pptx`, PDF,
  or slide text export.
- Extract: slide titles, text boxes, tables, speaker notes, embedded images.
- Emit Markdown plus per-slide PNG (and optional combined PDF) under
  `normalized/`.
- Coordinate shape: `slide / shape / table / note`.

## Visio — `.vsdx`, `.vsd`

- Export to PDF / SVG / PNG via LibreOffice (or documented converter) when
  available; otherwise skip the diagram as optional binary input and request a
  PDF/SVG/PNG export.
- Extract shape text and connectors where the format allows; many diagrams need
  OCR or visual review for connectors — record a visual-review warning.
- Emit shape-text Markdown plus visual exports under `normalized/`.
- Coordinate shape: `page / shape / connector / OCR-region`.

## PDF — `.pdf`

- Extract text and tables; emit Markdown plus per-page PNG and table CSVs.
- For scanned/image PDFs, run OCR only when OCR tooling is already available and
  authorized; otherwise skip OCR and request a text or image-reviewed export.
- Coordinate shape: `page / region / table`.

## Images / Screenshots / Scanned — `.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`

- Run OCR only when OCR tooling is already available and authorized; otherwise
  skip the image as optional OCR input and request a manual transcription or
  readable export.
- Emit OCR Markdown plus the page PNG under `normalized/`.
- Never invent text for unreadable regions — record a low-confidence warning.
- Coordinate shape: `page / OCR-region`.

## Honest-Conversion Rule

If a converter/OCR tool is unavailable, write "tool unavailable" in
`conversion-log.md`, set the affected document gate to `blocked` (or
`ready_with_warnings` when partial extraction still produced usable output),
record a skip warning, and continue with other readable documents. Never mark a
conversion `succeeded` when no tool ran.
