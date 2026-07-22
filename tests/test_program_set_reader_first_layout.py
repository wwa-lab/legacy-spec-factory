from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.fixtures.program_analysis_artifacts import (
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


def load_builder():
    spec = importlib.util.spec_from_file_location("reader_first_layout_builder", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load merger: {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


def require_public_seam(name: str):
    seam = getattr(BUILDER, name, None)
    if not callable(seam):
        raise AssertionError(f"program-set merger is missing public seam {name}()")
    return seam


class ProgramSetReaderFirstLayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.artifact_root = self.root / "artifacts"
        for program in ("CU106", "CU101A", "CCB11"):
            write_finalized_program_artifacts(
                self.artifact_root / "modules" / "normal" / program,
                program,
                routines=("MAIN", "VALIDATE"),
            )

    def run_build(
        self,
        *,
        review_name: str,
        programs: tuple[str, ...],
        output_parent: Path | None = None,
        project_root: Path | None = None,
        flow_slug: str,
    ) -> subprocess.CompletedProcess[str]:
        if (output_parent is None) == (project_root is None):
            raise ValueError("provide exactly one of output_parent or project_root")
        programs_file = self.root / (
            "programs-" + "-".join(program.lower() for program in programs) + ".txt"
        )
        programs_file.write_text("\n".join(programs) + "\n", encoding="utf-8")
        command = [
            sys.executable,
            str(SCRIPT),
            "build",
            "--review-name",
            review_name,
            "--programs-file",
            str(programs_file),
            "--working-root",
            str(self.artifact_root),
            "--profile",
            str(PROFILE),
            "--flow-slug",
            flow_slug,
        ]
        if project_root is not None:
            command.extend(["--project-root", str(project_root)])
        else:
            command.extend(["--output-dir", str(output_parent)])
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_cli_treats_output_dir_as_parent_and_writes_one_preparation_bundle(self) -> None:
        output_parent = self.root / "outputs"
        programs = ("CU106", "CU101A")

        result = self.run_build(
            review_name="Credit Check Review",
            programs=programs,
            output_parent=output_parent,
            flow_slug="credit-check",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        folder_slug = (
            f"{BUILDER.flow_identity_slug('credit-check')}--"
            f"{BUILDER.program_set_identity_slug(list(programs))}"
        )
        folder_dir = output_parent / folder_slug
        self.assertEqual(
            [path.name for path in output_parent.iterdir()],
            [folder_slug],
            "the output parent must contain only the flow/program-set bundle",
        )

        manifest_path = folder_dir / "program-set-core-input-manifest.yaml"
        self.assertTrue(manifest_path.is_file())
        manifest = BUILDER.load_yaml(manifest_path)
        layout = require_public_seam("resolve_output_layout")(output_parent, manifest)

        self.assertEqual(layout.folder_dir, folder_dir)
        for path in (
            layout.program_list_path,
            layout.manifest_path,
            layout.readiness_path,
            layout.source_pack_path,
            layout.core_facts_path,
            layout.coverage_path,
        ):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.parent, folder_dir)

        self.assertEqual(
            layout.review_path.name,
            f"{folder_slug}--sme-core-review.md",
        )
        self.assertFalse(
            layout.review_path.exists(),
            "the deterministic builder must not impersonate LLM synthesis",
        )
        self.assertFalse((folder_dir / "program-set-sme-core-review.md").exists())
        self.assertFalse(layout.queue_dir.exists(), "ready programs need no missing queue")
        for forbidden_name in (
            "program-set-core-input-manifest.yaml",
            "program-set-reader-first-source-pack.md",
            "program-set-core-facts.yaml",
            "program-set-core-coverage.yaml",
            "program-set-sme-core-review.md",
        ):
            self.assertFalse((output_parent / forbidden_name).exists())

        rerun = self.run_build(
            review_name="Credit Check Review",
            programs=programs,
            output_parent=folder_dir,
            flow_slug="credit-check",
        )
        self.assertEqual(rerun.returncode, 0, rerun.stderr)
        self.assertFalse(
            (folder_dir / folder_slug).exists(),
            "an already resolved bundle path must not be appended a second time",
        )

    def test_cli_places_project_root_outputs_in_a_reusable_bundle(self) -> None:
        project_root = self.root / "legacy-modernization-delivery"
        project_root.mkdir()
        programs = ("CU106", "CU101A")
        flow_slug = "credit-check"
        folder_slug = (
            f"{BUILDER.flow_identity_slug(flow_slug)}--"
            f"{BUILDER.program_set_identity_slug(list(programs))}"
        )

        first_run = self.run_build(
            review_name="Credit Check Review",
            programs=programs,
            project_root=project_root,
            flow_slug=flow_slug,
        )

        self.assertEqual(first_run.returncode, 0, first_run.stderr)
        output_parent = project_root / "outputs"
        folder_dir = output_parent / folder_slug
        self.assertTrue(folder_dir.is_dir())
        self.assertTrue((folder_dir / "program-set-core-input-manifest.yaml").is_file())
        self.assertFalse((project_root / folder_slug).exists())
        self.assertFalse((project_root / "program-set-core-input-manifest.yaml").exists())

        rerun = self.run_build(
            review_name="Credit Check Review",
            programs=programs,
            project_root=project_root,
            flow_slug=flow_slug,
        )

        self.assertEqual(rerun.returncode, 0, rerun.stderr)
        self.assertTrue(folder_dir.is_dir())
        self.assertFalse((folder_dir / folder_slug).exists())

    def test_layout_identity_is_stable_and_unique_by_flow_and_program_set(self) -> None:
        resolve_output_layout = require_public_seam("resolve_output_layout")
        config = BUILDER.load_yaml(PROFILE)

        def manifest(flow: str, programs: list[str]):
            return BUILDER.build_manifest(
                review_name=f"{flow} review",
                programs=programs,
                artifact_root=self.artifact_root,
                config=config,
                working_branch="fixture",
                flow_slug=flow,
            )

        same_a = manifest("credit-check", ["CU106", "CU101A"])
        same_b = manifest("credit-check", ["CU101A", "CU106"])
        other_flow = manifest("account-maintenance", ["CU106", "CU101A"])
        other_set = manifest("credit-check", ["CU106", "CCB11"])
        output_parent = self.root / "outputs"

        layout_a = resolve_output_layout(output_parent, same_a)
        layout_b = resolve_output_layout(output_parent, same_b)
        flow_layout = resolve_output_layout(output_parent, other_flow)
        set_layout = resolve_output_layout(output_parent, other_set)

        self.assertEqual(layout_a.folder_dir, layout_b.folder_dir)
        self.assertEqual(layout_a.review_path, layout_b.review_path)
        self.assertEqual(same_a["review_id"], same_b["review_id"])
        self.assertNotEqual(layout_a.folder_dir, flow_layout.folder_dir)
        self.assertNotEqual(layout_a.review_path.name, flow_layout.review_path.name)
        self.assertNotEqual(layout_a.folder_dir, set_layout.folder_dir)
        self.assertNotEqual(layout_a.review_path.name, set_layout.review_path.name)

    def test_default_flow_identity_distinguishes_readable_slug_collisions(self) -> None:
        config = BUILDER.load_yaml(PROFILE)
        raw_identities = (
            "Payments Review",
            "payments-review",
            "payments_review",
        )
        manifests = [
            BUILDER.build_manifest(
                review_name=identity,
                programs=["CU106"],
                artifact_root=self.artifact_root,
                config=config,
                working_branch="fixture",
            )
            for identity in raw_identities
        ]
        repeated = BUILDER.build_manifest(
            review_name=raw_identities[0],
            programs=["CU106"],
            artifact_root=self.artifact_root,
            config=config,
            working_branch="fixture",
        )

        expected_flow_slugs = {
            "payments_review_"
            + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:8]
            for identity in raw_identities
        }
        self.assertEqual(
            {manifest["flow_slug"] for manifest in manifests},
            expected_flow_slugs,
        )
        for key in ("flow_slug", "folder_slug", "document_id", "canonical_filename"):
            self.assertEqual(manifests[0][key], repeated[key])
            self.assertEqual(len({manifest[key] for manifest in manifests}), 3)

    def test_explicit_flow_identity_hashes_the_exact_original_value(self) -> None:
        config = BUILDER.load_yaml(PROFILE)
        values = ("Payments Review", "payments-review", "payments_review")
        manifests = [
            BUILDER.build_manifest(
                review_name="Shared display name",
                programs=["CU106"],
                artifact_root=self.artifact_root,
                config=config,
                working_branch="fixture",
                flow_slug=value,
            )
            for value in values
        ]

        self.assertEqual(len({manifest["flow_slug"] for manifest in manifests}), 3)
        for value, manifest in zip(values, manifests):
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]
            self.assertEqual(manifest["flow_slug"], f"payments_review_{digest}")

    def test_explicit_program_set_label_still_includes_set_identity(self) -> None:
        config = BUILDER.load_yaml(PROFILE)
        first = BUILDER.build_manifest(
            review_name="credit check",
            programs=["CU106"],
            artifact_root=self.artifact_root,
            config=config,
            working_branch="fixture",
            program_set_slug="selected-programs",
        )
        second = BUILDER.build_manifest(
            review_name="credit check",
            programs=["CU101A"],
            artifact_root=self.artifact_root,
            config=config,
            working_branch="fixture",
            program_set_slug="selected-programs",
        )

        self.assertTrue(first["program_set_slug"].startswith("selected_programs_"))
        self.assertNotEqual(first["program_set_slug"], second["program_set_slug"])
        self.assertNotEqual(first["canonical_filename"], second["canonical_filename"])

    def test_existing_bundle_with_different_identity_is_not_overwritten(self) -> None:
        config = BUILDER.load_yaml(PROFILE)
        manifest = BUILDER.build_manifest(
            review_name="credit check",
            programs=["CU106"],
            artifact_root=self.artifact_root,
            config=config,
            working_branch="fixture",
            flow_slug="credit-check",
        )
        layout = require_public_seam("resolve_output_layout")(
            self.root / "outputs", manifest
        )
        layout.folder_dir.mkdir(parents=True)
        conflicting = {
            **manifest,
            "document_id": "review-for-a-different-program-set",
            "review_id": "review-for-a-different-program-set",
        }
        original = BUILDER.dump_yaml(conflicting)
        layout.manifest_path.write_text(original, encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "identity does not match"):
            BUILDER.write_build_outputs(manifest, self.root / "outputs")

        self.assertEqual(layout.manifest_path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
