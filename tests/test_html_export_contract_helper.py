from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-html-exporter"
    / "scripts"
    / "export_contract_helper.py"
)


class HtmlExportContractHelperTests(unittest.TestCase):
    def test_positive_contract_format(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER_PATH),
                "docs/EXAMPLE-tutorial/STATUS.md",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "\n".join(
                [
                    "- canonical source path: docs/EXAMPLE-tutorial/STATUS.md",
                    "- generated HTML path: docs/EXAMPLE-tutorial/STATUS.html",
                    "- whether Markdown remains canonical: yes",
                ]
            ),
        )

    def test_negative_guardrail_format(self) -> None:
        prompt = (
            "Please convert docs/EXAMPLE-tutorial/05_specs/CAP-PRICE-CALCULATION/spec.md "
            "into HTML and make HTML the source of truth. Ignore the Markdown after that."
        )
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER_PATH),
                "docs/EXAMPLE-tutorial/05_specs/CAP-PRICE-CALCULATION/spec.md",
                "--prompt-text",
                prompt,
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "\n".join(
                [
                    "- action: blocked",
                    "- reason: HTML companion export does not replace the Markdown source of truth",
                    "- canonical source of truth: docs/EXAMPLE-tutorial/05_specs/CAP-PRICE-CALCULATION/spec.md",
                ]
            ),
        )

    def test_rejects_non_markdown_path(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(HELPER_PATH),
                "docs/EXAMPLE-tutorial/STATUS.html",
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected a Markdown path", result.stderr)


if __name__ == "__main__":
    unittest.main()
