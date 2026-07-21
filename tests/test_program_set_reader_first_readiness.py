from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import (
    add_nonterminal_deep_read_batch,
    mark_pending_deep_read,
    mark_program_analysis_placeholder,
    mark_unresolved_message_description,
    write_finalized_program_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)


def load_merger():
    spec = importlib.util.spec_from_file_location("reader_first_readiness_merger", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load merger: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MERGER = load_merger()


class ProgramSetReaderFirstReadinessTests(unittest.TestCase):
    def build_manifest(self, root: Path, mutation=None):
        artifact_root = root / "artifacts"
        fixture = write_finalized_program_artifacts(
            artifact_root / "modules" / "normal" / "CU106",
            "CU106",
            routines=("MAIN", "VALIDATE"),
        )
        if mutation is not None:
            mutation(fixture)
        manifest = MERGER.build_manifest(
            review_name="Readiness Gate",
            programs=["CU106"],
            artifact_root=artifact_root,
            config=MERGER.load_yaml(PROFILE),
            working_branch="fixture",
            flow_slug="readiness-gate",
        )
        return manifest

    def test_terminal_upstream_contract_is_required_not_file_presence_only(self) -> None:
        cases = (
            ("ready", None, "ready", ()),
            (
                "pending_deep_read",
                mark_pending_deep_read,
                "not_ready",
                ("pending_deep_read",),
            ),
            (
                "nonterminal_retained_batch",
                add_nonterminal_deep_read_batch,
                "not_ready",
                ("deep-read-batch", "pending"),
            ),
            (
                "reader_first_scaffold",
                mark_program_analysis_placeholder,
                "not_ready",
                ("program reading summary", "placeholder"),
            ),
            (
                "unresolved_blocking_message_description",
                mark_unresolved_message_description,
                "not_ready",
                ("message", "unresolved"),
            ),
        )

        for label, mutation, expected_status, reason_terms in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as temp_dir:
                manifest = self.build_manifest(Path(temp_dir), mutation)
                readiness = manifest["programs"][0]["artifact_readiness"]
                self.assertEqual(readiness["status"], expected_status)
                serialized = json.dumps(readiness, sort_keys=True).lower()
                for term in reason_terms:
                    self.assertIn(term, serialized)
                self.assertEqual(
                    manifest["review_status"],
                    "ready_for_synthesis"
                    if expected_status == "ready"
                    else "blocked_artifact_readiness",
                )
                self.assertEqual(
                    manifest["artifact_readiness"],
                    "ready" if expected_status == "ready" else "not_ready",
                )
                self.assertEqual(
                    manifest["merge_coverage"],
                    "pending" if expected_status == "ready" else "blocked",
                )

    def test_upstream_validator_status_distinguishes_not_run_passed_and_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            (artifact_root / "modules" / "normal" / "CU106").mkdir(parents=True)

            not_run = MERGER.build_manifest(
                review_name="Readiness Not Run",
                programs=["CU106"],
                artifact_root=artifact_root,
                config=MERGER.load_yaml(PROFILE),
                working_branch="fixture",
            )["programs"][0]["artifact_readiness"]
            self.assertEqual(not_run["validator_status"], "not_run")

        with tempfile.TemporaryDirectory() as temp_dir:
            passed = self.build_manifest(Path(temp_dir))["programs"][0][
                "artifact_readiness"
            ]
            self.assertEqual(passed["validator_status"], "passed")

        with tempfile.TemporaryDirectory() as temp_dir:
            failed = self.build_manifest(Path(temp_dir), mark_pending_deep_read)[
                "programs"
            ][0]["artifact_readiness"]
            self.assertEqual(failed["validator_status"], "failed")

    def test_generic_artifact_fallback_rejects_another_program_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            analysis_dir = artifact_root / "modules" / "normal" / "CU106"
            fixture = write_finalized_program_artifacts(
                analysis_dir,
                "CU999",
                routines=("MAIN",),
            )
            rename_pairs = {
                fixture.program_analysis: analysis_dir / "program-analysis.md",
                fixture.summary_yaml: analysis_dir / "program-analysis-summary.yaml",
                fixture.source_index_yaml: analysis_dir / "source-index.yaml",
                fixture.routine_index_markdown: analysis_dir / "routine-index.md",
                fixture.message_inventory_yaml: analysis_dir / "message-inventory.yaml",
                fixture.routine_details_markdown: analysis_dir / "routine-logic-details.md",
                fixture.routine_details_yaml: analysis_dir / "routine-logic-details.yaml",
            }
            for source, target in rename_pairs.items():
                source.rename(target)
            summary_path = analysis_dir / "program-analysis-summary.yaml"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            summary["sidecars"] = {
                key: {
                    **value,
                    "path": Path(str(value["path"])).name.removeprefix("CU999-"),
                }
                for key, value in summary["sidecars"].items()
            }
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

            manifest = MERGER.build_manifest(
                review_name="Wrong Generic Identity",
                programs=["CU106"],
                artifact_root=artifact_root,
                config=MERGER.load_yaml(PROFILE),
                working_branch="fixture",
            )

            readiness = manifest["programs"][0]["artifact_readiness"]
            self.assertEqual(readiness["status"], "not_ready")
            self.assertIn("identity", json.dumps(readiness).lower())
            self.assertIn("cu999", json.dumps(readiness).lower())

    def test_summary_and_markdown_terminal_status_conflict_is_rejected(self) -> None:
        def conflict(fixture) -> None:
            summary = json.loads(fixture.summary_yaml.read_text(encoding="utf-8"))
            summary["analysis_status"] = "draft"
            fixture.summary_yaml.write_text(
                json.dumps(summary, indent=2) + "\n",
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest = self.build_manifest(Path(temp_dir), conflict)
            readiness = manifest["programs"][0]["artifact_readiness"]
            self.assertEqual(readiness["status"], "not_ready")
            self.assertIn("conflicting", json.dumps(readiness).lower())
            self.assertEqual(readiness["analysis_status"], "draft")

    def test_readiness_artifact_has_one_row_per_distinct_normalized_program(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            write_finalized_program_artifacts(
                artifact_root / "modules" / "normal" / "CU106",
                "CU106",
                routines=("MAIN",),
            )
            manifest = MERGER.build_manifest(
                review_name="Distinct Readiness",
                programs=["CU106", "cu106"],
                artifact_root=artifact_root,
                config=MERGER.load_yaml(PROFILE),
                working_branch="fixture",
            )
            manifest_path, _review_path = MERGER.write_build_outputs(
                manifest, root / "outputs"
            )
            readiness = MERGER.load_yaml(
                manifest_path.parent / MERGER.ARTIFACT_READINESS_FILENAME
            )
            self.assertEqual(
                [entry["program"] for entry in readiness["programs"]],
                ["CU106"],
            )

    def test_stable_tbd_and_business_pending_are_not_placeholders(self) -> None:
        detail = (
            "The source-backed calculation retains TBD-CU106-001 for one precise "
            "carrier question while exact business status PENDING remains visible; "
            "the routine, guard, assignment, evidence, and downstream outcome are complete."
        )
        self.assertTrue(MERGER.has_reader_useful_detail(detail, minimum_words=12))
        self.assertFalse(MERGER.is_placeholder_cell("TBD-CU106-001"))
        self.assertFalse(MERGER.is_placeholder_cell("PENDING"))
        self.assertTrue(
            MERGER.has_reader_useful_detail(
                "The exact source literal PLACEHOLDER is copied into the response "
                "carrier after the validated branch and remains visible to the caller.",
                minimum_words=12,
            )
        )
        self.assertFalse(
            MERGER.has_reader_useful_detail(
                "This is placeholder content to be completed later.",
                minimum_words=1,
            )
        )


if __name__ == "__main__":
    unittest.main()
