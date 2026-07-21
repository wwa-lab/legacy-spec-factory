from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)


def load_builder():
    spec = importlib.util.spec_from_file_location("output_layout_core_review", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load program-set builder: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["output_layout_core_review"] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


class ProgramSetOutputLayoutContractTests(unittest.TestCase):
    def manifest(self, flow_slug: str = "card_auth", program_set_slug: str = "program_set_cu106_ab12"):
        folder_slug = f"{flow_slug}--{program_set_slug}"
        return {
            "flow_slug": flow_slug,
            "program_set_slug": program_set_slug,
            "folder_slug": folder_slug,
            "document_id": f"sme-core-review-{folder_slug}",
            "canonical_filename": f"{folder_slug}--sme-core-review.md",
        }

    def test_output_parent_gets_stable_flow_folder_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir) / "outputs"
            manifest = self.manifest()

            first = BUILDER.resolve_output_layout(parent, manifest)
            second = BUILDER.resolve_output_layout(first.folder_dir, manifest)

            self.assertEqual(first.folder_dir, parent / manifest["folder_slug"])
            self.assertEqual(second.folder_dir, first.folder_dir)
            self.assertEqual(first.review_path.name, manifest["canonical_filename"])
            self.assertNotEqual(first.review_path.name, "program-set-sme-core-review.md")

    def test_different_flow_or_program_set_changes_dify_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir) / "outputs"
            base = BUILDER.resolve_output_layout(parent, self.manifest())
            other_flow = BUILDER.resolve_output_layout(
                parent, self.manifest(flow_slug="settlement")
            )
            other_set = BUILDER.resolve_output_layout(
                parent, self.manifest(program_set_slug="program_set_cu101a_cd34")
            )

            self.assertEqual(len({base.review_path.name, other_flow.review_path.name, other_set.review_path.name}), 3)
            self.assertEqual(len({base.folder_dir, other_flow.folder_dir, other_set.folder_dir}), 3)

    def test_existing_formal_review_must_be_archived_before_rebuild(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir) / "outputs"
            manifest = {
                **self.manifest(),
                "review_status": "blocked_artifact_readiness",
                "programs": [
                    {"input_name": "CU106", "normalized_name": "CU106"}
                ],
            }
            layout = BUILDER.resolve_output_layout(parent, manifest)
            layout.folder_dir.mkdir(parents=True)
            layout.review_path.write_text("protected SME review\n", encoding="utf-8")

            with self.assertRaisesRegex(
                ValueError, "must be explicitly archived before rebuilding"
            ):
                BUILDER.write_build_outputs(manifest, parent)

            self.assertEqual(
                layout.review_path.read_text(encoding="utf-8"),
                "protected SME review\n",
            )
            self.assertFalse(layout.manifest_path.exists())


if __name__ == "__main__":
    unittest.main()
