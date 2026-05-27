from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-flow-context-normalizer"
    / "scripts"
    / "extract_excel_fragments.py"
)


def inline_cell(ref: str, value: str) -> str:
    return (
        f'<c r="{ref}" t="inlineStr">'
        f"<is><t>{escape(value)}</t></is>"
        "</c>"
    )


def sheet_xml(rows: list[list[str]]) -> str:
    row_xml = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row):
            col = chr(ord("A") + col_index)
            cells.append(inline_cell(f"{col}{row_index}", value))
        row_xml.append(f'<row r="{row_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(row_xml)}</sheetData>'
        "</worksheet>"
    )


def create_workbook(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet3.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet4.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        )
        zf.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        zf.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Function Spec" sheetId="1" r:id="rId1"/>
    <sheet name="Technical Design" sheetId="2" r:id="rId2"/>
    <sheet name="Program Spec" sheetId="3" r:id="rId3"/>
    <sheet name="File Spec" sheetId="4" r:id="rId4"/>
  </sheets>
</workbook>""",
        )
        zf.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet3.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet4.xml"/>
</Relationships>""",
        )
        zf.writestr(
            "xl/worksheets/sheet1.xml",
            sheet_xml(
                [
                    ["Function", "Actor", "Action"],
                    ["Credit application", "Branch staff", "Submit credit application"],
                ]
            ),
        )
        zf.writestr(
            "xl/worksheets/sheet2.xml",
            sheet_xml(
                [
                    ["System", "Interface", "Direction"],
                    ["Branch portal", "Host credit check", "outbound"],
                ]
            ),
        )
        zf.writestr(
            "xl/worksheets/sheet3.xml",
            sheet_xml(
                [
                    ["Program", "Trigger", "Called Program"],
                    ["CCHK100", "credit request", "CCHK200"],
                ]
            ),
        )
        zf.writestr(
            "xl/worksheets/sheet4.xml",
            sheet_xml(
                [
                    ["File", "Field", "Update"],
                    ["APPSTAT", "STATUS", "approve or decline"],
                ]
            ),
        )


class FlowContextExcelExtractorTests(unittest.TestCase):
    def test_extracts_multiple_sheets_into_fragments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook = Path(tmp) / "credit-check.xlsx"
            create_workbook(workbook)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(workbook),
                    "--module-slug",
                    "CREDIT-CHECK",
                    "--title",
                    "Credit Check Workbook",
                    "--owner",
                    "Credit Operations",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                'pages_or_sheets: "Function Spec, Technical Design, Program Spec, File Spec"',
                result.stdout,
            )
            self.assertIn("fragment_id: FRAG-CREDIT-CHECK-001", result.stdout)
            self.assertIn('locator: "Function Spec row 2"', result.stdout)
            self.assertIn("candidate_view: operation_business_flow", result.stdout)
            self.assertIn("candidate_view: system_flow", result.stdout)
            self.assertIn("candidate_view: program_flow", result.stdout)
            self.assertIn("candidate_view: data_flow", result.stdout)

    def test_writes_output_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workbook = Path(tmp) / "credit-check.xlsx"
            output = Path(tmp) / "source-document-index.yaml"
            create_workbook(workbook)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(workbook),
                    "--module-slug",
                    "CREDIT-CHECK",
                    "--output",
                    str(output),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            text = output.read_text(encoding="utf-8")
            self.assertIn("doc_id: DOC-CREDIT-CHECK-001", text)
            self.assertIn("Extracted 4 non-empty data rows across 4 sheet(s).", text)


if __name__ == "__main__":
    unittest.main()
