from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "skills/legacy-ibmi-flow-analyzer/scripts/program_set_core_review.py"
PROFILE = REPO_ROOT / "skills/legacy-ibmi-flow-analyzer/templates/delivery-profile.yaml"


def load_builder():
    spec = importlib.util.spec_from_file_location("profile_core_review", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load program-set builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules["profile_core_review"] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


def write_artifacts(root: Path, program: str) -> None:
    root.mkdir(parents=True)
    for filename in BUILDER.REQUIRED_COMPACT_ARTIFACTS:
        (root / BUILDER.program_artifact_filename(program, filename)).write_text(
            "schema_version: '0.1'\n", encoding="utf-8"
        )


class ProgramSetCoreReviewProfileTests(unittest.TestCase):
    def test_minimal_and_standard_profiles_have_distinct_primary_sections(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working = root / "working"
            write_artifacts(working / "modules" / "tier" / "CU106", "CU106")
            (working / "modules" / "tier" / "CU106" / "CU106-program-analysis.md").write_text(
                """## Calculation Logic\n\n| Calculation / Assignment | Target Field / Variable | Source Operands / Carriers | Guard / Branch | Output / Business Effect | Supporting Detail Link | Evidence |\n| --- | --- | --- | --- | --- | --- | --- |\n| derive response | RESPONSE | REQUEST | valid branch | output handoff | RLOG-CU106-001 | EV-CU106-001 |\n\n## Validation Logic\n\n| Message / Status Code | Message Description | Validation / Error Type | Set By / Source Lines | Trigger Condition | Reverse Trigger Chain / Routine Logic Link | Output Carrier | Downstream Effect | Evidence Status |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n| OK | valid | status | STATUS | request present | request -> status | return status | continue | confirmed |\n\n## Exception Handling\n\n| Exception / Error Path | Trigger | Detection Mechanism | Fields / Messages Set | Handling Action | Downstream Effect | Supporting Detail Link | Evidence |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| missing request | absent | IF | ERROR_STATUS | return | output suppressed | RLOG-CU106-002 | EV-CU106-002 |\n""",
                encoding="utf-8",
            )
            write_artifacts(working / "modules" / "tier" / "CU101A", "CU101A")
            config = BUILDER.load_yaml(PROFILE)

            minimal = BUILDER.build_manifest(
                review_name="Synthetic Review",
                programs=["CU106", "CU101A"],
                artifact_root=working,
                config=config,
                working_branch="test",
            )
            _, standard_default_review = BUILDER.write_build_outputs(minimal, root / "standard-default")
            standard_default_text = standard_default_review.read_text(encoding="utf-8")
            self.assertIn("## Message Inventory", standard_default_text)
            self.assertEqual(minimal["core_review_profile"]["name"], "standard_reader_first")
            self.assertEqual(minimal["review_status"], "complete_exploratory")
            self.assertEqual(minimal["canonical_filename"], "program-set-sme-core-review.md")
            self.assertTrue(
                minimal["folder_slug"].startswith(
                    "synthetic_review--program_set_cu101a_cu106_"
                )
            )
            self.assertEqual(
                minimal["review_id"], f"review-{minimal['folder_slug']}"
            )
            self.assertTrue((root / "standard-default" / "program-set-core-facts.yaml").is_file())
            facts = BUILDER.load_yaml(root / "standard-default" / "program-set-core-facts.yaml")
            cu106 = next(item for item in facts["programs"] if item["program"] == "CU106")
            self.assertEqual(cu106["facts"]["calculations"][0]["target_carrier"], "RESPONSE")
            self.assertEqual(cu106["facts"]["validations"][0]["exact_code_status"], "OK")

            minimal = BUILDER.build_manifest(
                review_name="Synthetic Review",
                programs=["CU106", "CU101A"],
                artifact_root=working,
                config=config,
                working_branch="test",
                core_review_profile="minimal_reader_first",
            )
            _, minimal_review = BUILDER.write_build_outputs(minimal, root / "minimal")
            self.assertNotIn("## Message Inventory", minimal_review.read_text(encoding="utf-8"))

            standard = BUILDER.build_manifest(
                review_name="Synthetic Review",
                programs=["CU106", "CU101A"],
                artifact_root=working,
                config=config,
                working_branch="test",
                core_review_profile="standard_reader_first",
            )
            _, standard_review = BUILDER.write_build_outputs(standard, root / "standard")
            self.assertIn("## Message Inventory", standard_review.read_text(encoding="utf-8"))
            self.assertTrue(standard["core_review_profile"]["include_message_inventory"])

            different_program_set = BUILDER.build_manifest(
                review_name="Synthetic Review",
                programs=["CU106", "CU101B"],
                artifact_root=working,
                config=config,
                working_branch="test",
            )
            self.assertNotEqual(minimal["folder_slug"], different_program_set["folder_slug"])
            self.assertNotEqual(minimal["review_id"], different_program_set["review_id"])

    def test_missing_program_is_partial_and_facts_are_evidence_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working = root / "working"
            write_artifacts(working / "modules" / "tier" / "CU106", "CU106")
            config = BUILDER.load_yaml(PROFILE)
            manifest = BUILDER.build_manifest(
                review_name="Partial Synthetic Review",
                programs=["CCB11", "CU106"],
                artifact_root=working,
                config=config,
                working_branch="test",
            )
            output = root / "partial"
            BUILDER.write_build_outputs(manifest, output)
            facts = BUILDER.load_yaml(output / "program-set-core-facts.yaml")
            self.assertEqual(manifest["review_status"], "partial_pending_program")
            missing = next(item for item in facts["programs"] if item["program"] == "CCB11")
            self.assertIn("unavailable", missing["unresolved_reason"])
            self.assertNotIn("business_rule", BUILDER.dump_yaml(facts))
            self.assertNotIn("modernization_decision", BUILDER.dump_yaml(facts))
            self.assertNotIn("call_edges", BUILDER.dump_yaml(facts))

    def test_existing_partial_artifact_folder_is_pending_and_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            working = root / "working"
            partial_folder = working / "modules" / "tier" / "CCB11"
            write_artifacts(partial_folder, "CCB11")
            (partial_folder / "CCB11-program-analysis.md").unlink()
            config = BUILDER.load_yaml(PROFILE)

            manifest = BUILDER.build_manifest(
                review_name="Partial Artifact Review",
                programs=["CCB11"],
                artifact_root=working,
                config=config,
                working_branch="test",
            )

            entry = manifest["programs"][0]
            self.assertEqual(entry["run_resolution"], "pending_source")
            self.assertIsNone(entry["artifact_root"])
            self.assertEqual(manifest["review_status"], "partial_pending_program")
            self.assertEqual(
                entry["compact_artifacts"][BUILDER.artifact_key("program-analysis.md")]["status"],
                "missing",
            )

    def test_validator_rejects_legacy_rollup_and_call_map_forms(self) -> None:
        manifest = {
            "review_status": "complete_exploratory",
            "core_review_profile": {
                "name": "minimal_reader_first",
                "core_sections": list(BUILDER.CORE_READING_SECTIONS),
                "include_message_inventory": False,
                "include_audit_sections": True,
            },
            "programs": [{"normalized_name": "CU106", "run_resolution": "pending_source"}],
        }
        markdown = "## Program-Level SME Core Review\n\n## Transaction Call Map\n"
        findings = BUILDER.validate_review(markdown, manifest)
        self.assertTrue(any("forbidden legacy form" in finding for finding in findings))
        self.assertTrue(any("forbidden full-flow section: Transaction Call Map" in finding for finding in findings))


if __name__ == "__main__":
    unittest.main()
