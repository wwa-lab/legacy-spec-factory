from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check-portable-links.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_portable_links", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load checker: {SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PortableLinkCheckerTests(unittest.TestCase):
    def test_detects_unsafe_markdown_and_html_links(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "analysis.md"
            doc.write_text(
                "\n".join(
                    [
                        "# Analysis",
                        "[Source](file:///Users/demo/CU101A.RPGLE)",
                        "[Internal](https://file+.vscode-resource.vscode-cdn.net/c%3A/Users/demo/CU101A.RPGLE)",
                        "`file://` appears in guidance only and is not a link.",
                    ]
                ),
                encoding="utf-8",
            )
            html = root / "analysis.html"
            html.write_text('<a href="vscode://file/CU101A.RPGLE">Open</a>', encoding="utf-8")
            manifest = root / "artifact-build-manifest.json"
            manifest.write_text(
                '{"source": "file:///Users/demo/CU101A.RPGLE"}',
                encoding="utf-8",
            )

            findings = checker.collect_findings([root])

            self.assertEqual(len(findings), 4)
            self.assertTrue(any("file://" in finding.target for finding in findings))
            self.assertTrue(any("vscode-resource.vscode-cdn.net" in finding.target for finding in findings))
            self.assertTrue(any("vscode://file" in finding.target for finding in findings))
            self.assertTrue(any(finding.kind == "json-value" for finding in findings))

    def test_accepts_repo_relative_and_web_links(self) -> None:
        checker = load_checker()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "analysis.md"
            doc.write_text(
                "\n".join(
                    [
                        "# Analysis",
                        "[Source](source/CU101A.RPGLE)",
                        "[Section](#routine-cards)",
                        "[Web](https://example.com)",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(checker.collect_findings([root]), [])

    def test_cli_returns_nonzero_for_unsafe_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "bad.md").write_text("[Bad](C:/Users/demo/CU101A.RPGLE)\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), str(root)],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("Unsafe local/runtime-specific links found", result.stdout)
            self.assertIn("C:/Users/demo/CU101A.RPGLE", result.stdout)


if __name__ == "__main__":
    unittest.main()
