from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "render_stakeholder_html.py"
CANONICAL_SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-html-exporter"
    / "scripts"
    / "render_stakeholder_html.py"
)


class RenderStakeholderHtmlTests(unittest.TestCase):
    def test_render_markdown_supports_tables_lists_links_and_code(self) -> None:
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(
            "render_stakeholder_html", CANONICAL_SCRIPT_PATH
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        html = module.render_markdown(
            """# Demo Title

## Section One

- [x] approved item
- [ ] pending item

| Column | Value |
| --- | --- |
| Link | [Open](https://example.com) |

```text
hello world
```
""",
            source_name="demo.md",
        )

        self.assertIn("<title>Demo Title</title>", html)
        self.assertIn('<nav class="toc">', html)
        self.assertIn('<input type="checkbox" checked disabled>', html)
        self.assertIn('<input type="checkbox" disabled>', html)
        self.assertIn("<table>", html)
        self.assertIn('<a href="https://example.com">Open</a>', html)
        self.assertIn('<pre><code class="language-text">hello world', html)

    def test_cli_renders_directory_and_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            docs_dir = tmp_path / "docs"
            docs_dir.mkdir()
            first = docs_dir / "spec.md"
            second = docs_dir / "question-pack.md"
            first.write_text("# Spec\n\n## Scope\n\nHello team.\n", encoding="utf-8")
            second.write_text("# Questions\n\n- first\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(docs_dir),
                    "--recursive",
                    "--index-title",
                    "Pilot Docs",
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((docs_dir / "spec.html").exists())
            self.assertTrue((docs_dir / "question-pack.html").exists())
            index_path = docs_dir / "index.html"
            self.assertTrue(index_path.exists())
            index_html = index_path.read_text(encoding="utf-8")
            self.assertIn("Pilot Docs", index_html)
            self.assertIn("spec.html", index_html)


if __name__ == "__main__":
    unittest.main()
