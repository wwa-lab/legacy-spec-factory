from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import write_finalized_program_artifacts


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py"
PROFILE = REPO_ROOT / "skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml"


def load_builder():
    spec = importlib.util.spec_from_file_location("profile_core_review", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load program-set builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


class ProgramSetCoreReviewProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.working = self.root / "working"
        for program in ("CU106", "CU101A"):
            write_finalized_program_artifacts(
                self.working / "modules" / "tier" / program, program
            )
        self.config = BUILDER.load_yaml(PROFILE)

    def manifest(self, profile: str | None = None) -> dict:
        return BUILDER.build_manifest(
            review_name="Synthetic Review",
            programs=["CU106", "CU101A"],
            artifact_root=self.working,
            config=self.config,
            working_branch="test",
            core_review_profile=profile,
        )

    def test_standard_is_default_and_minimal_is_explicit_without_losing_message_facts(self) -> None:
        standard = self.manifest()
        standard_manifest, standard_review = BUILDER.write_build_outputs(
            standard, self.root / "standard"
        )
        minimal = self.manifest("minimal_reader_first")
        minimal_manifest, minimal_review = BUILDER.write_build_outputs(
            minimal, self.root / "minimal"
        )

        self.assertEqual(standard["core_review_profile"]["name"], "standard_reader_first")
        self.assertEqual(
            standard["run_profile"]["artifact_repo_mode"],  # type: ignore[index]
            "approved_document_repo",
        )
        self.assertTrue(
            all(
                entry["run_resolution"] == "reused_artifact_repo"
                for entry in standard["programs"]  # type: ignore[index]
            )
        )
        self.assertTrue(standard["core_review_profile"]["include_message_inventory"])
        self.assertEqual(minimal["core_review_profile"]["name"], "minimal_reader_first")
        self.assertFalse(minimal["core_review_profile"]["include_message_inventory"])
        self.assertEqual(standard["review_status"], "ready_for_synthesis")
        self.assertEqual(standard["artifact_readiness"], "ready")
        self.assertEqual(standard["merge_coverage"], "pending")
        self.assertFalse(standard_review.exists())
        self.assertFalse(minimal_review.exists())
        self.assertEqual(
            standard["canonical_filename"],
            f"{standard['folder_slug']}--sme-core-review.md",
        )
        self.assertNotEqual(standard["canonical_filename"], "program-set-sme-core-review.md")

        for manifest_path in (standard_manifest, minimal_manifest):
            facts = BUILDER.load_yaml(manifest_path.parent / "program-set-core-facts.yaml")
            self.assertTrue(
                any(fact.get("fact_type") == "message" for fact in facts["source_facts"])
            )
            coverage = BUILDER.load_yaml(
                manifest_path.parent / "program-set-core-coverage.yaml"
            )
            self.assertTrue(all(item["status"] == "pending" for item in coverage["items"]))

    def test_profile_identity_is_stable_and_program_set_sensitive(self) -> None:
        first = self.manifest()
        reordered = BUILDER.build_manifest(
            review_name="Synthetic Review",
            programs=["CU101A", "CU106"],
            artifact_root=self.working,
            config=self.config,
            working_branch="test",
        )
        different = BUILDER.build_manifest(
            review_name="Synthetic Review",
            programs=["CU106"],
            artifact_root=self.working,
            config=self.config,
            working_branch="test",
        )
        self.assertEqual(first["folder_slug"], reordered["folder_slug"])
        self.assertEqual(first["review_id"], reordered["review_id"])
        self.assertNotEqual(first["folder_slug"], different["folder_slug"])

    def test_missing_program_keeps_scan_merge_inputs_but_blocks_formal_review(self) -> None:
        manifest = BUILDER.build_manifest(
            review_name="Blocked Synthetic Review",
            programs=["CCB11", "CU106"],
            artifact_root=self.working,
            config=self.config,
            working_branch="test",
        )
        manifest_path, review_path = BUILDER.write_build_outputs(
            manifest, self.root / "blocked"
        )
        missing = next(
            entry for entry in manifest["programs"] if entry["normalized_name"] == "CCB11"
        )

        self.assertEqual(manifest["review_status"], "blocked_artifact_readiness")
        self.assertEqual(manifest["artifact_readiness"], "not_ready")
        self.assertEqual(manifest["merge_coverage"], "blocked")
        self.assertEqual(missing["artifact_readiness"]["status"], "not_ready")
        self.assertFalse(review_path.exists())
        source_pack = manifest_path.parent / "program-set-reader-first-source-pack.md"
        facts_path = manifest_path.parent / "program-set-core-facts.yaml"
        self.assertTrue(source_pack.exists())
        self.assertTrue(facts_path.exists())
        self.assertIn("Scan result is unavailable for this requested program", source_pack.read_text(encoding="utf-8"))
        coverage = BUILDER.load_yaml(manifest_path.parent / "program-set-core-coverage.yaml")
        self.assertEqual(coverage["coverage_status"], "pending")

    def test_validator_rejects_legacy_rollup_and_call_map_forms(self) -> None:
        manifest = {
            "review_status": "ready_for_synthesis",
            "core_review_profile": {
                "name": "minimal_reader_first",
                "core_sections": list(BUILDER.CORE_READING_SECTIONS),
                "include_message_inventory": False,
                "include_audit_sections": True,
            },
            "programs": [{"normalized_name": "CU106", "run_resolution": "pending_source"}],
        }
        findings = BUILDER.validate_review(
            "## Program-Level SME Core Review\n\n## Transaction Call Map\n", manifest
        )
        self.assertTrue(any("forbidden legacy form" in finding for finding in findings))
        self.assertTrue(
            any("forbidden full-flow section: Transaction Call Map" in finding for finding in findings)
        )

    def test_minimal_profile_routes_message_facts_to_control_section(self) -> None:
        manifest = self.manifest("minimal_reader_first")
        message_fact = {"section": "Message Inventory", "fact_type": "message"}
        self.assertEqual(
            BUILDER._review_section_for_fact(message_fact, manifest),
            "Message Coverage Control",
        )


if __name__ == "__main__":
    unittest.main()
