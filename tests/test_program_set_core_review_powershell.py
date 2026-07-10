from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "scripts"
BUILD_SCRIPT = SCRIPT_DIR / "build-program-set-core-review.ps1"
VALIDATE_SCRIPT = SCRIPT_DIR / "validate-program-set-core-review.ps1"
MODULE_DIR = SCRIPT_DIR / "powershell"
PYTHON_SCRIPT = SCRIPT_DIR / "program_set_core_review.py"
PROFILE = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "templates"
    / "delivery-profile.yaml"
)
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
ROUTER = REPO_ROOT / "scripts" / "invoke-windows-tool.ps1"


def load_python_builder():
    spec = importlib.util.spec_from_file_location("flow_core_review", PYTHON_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Python parity implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules["flow_core_review"] = module
    spec.loader.exec_module(module)
    return module


PYTHON_BUILDER = load_python_builder()


def write_artifacts(root: Path) -> None:
    root.mkdir(parents=True)
    for name in (
        PYTHON_BUILDER.REQUIRED_COMPACT_ARTIFACTS
        + PYTHON_BUILDER.OPTIONAL_COMPACT_ARTIFACTS
    ):
        (root / name).write_text("schema_version: '0.1'\n", encoding="utf-8")


class ProgramSetCoreReviewPowerShellTests(unittest.TestCase):
    def test_native_scripts_and_focused_modules_are_present(self) -> None:
        self.assertTrue(BUILD_SCRIPT.is_file())
        self.assertTrue(VALIDATE_SCRIPT.is_file())
        expected = {
            "FlowYaml.psm1",
            "ProgramSetCoreReview.Builder.psm1",
            "ProgramSetCoreReview.Validator.psm1",
        }
        self.assertTrue(expected.issubset({path.name for path in MODULE_DIR.glob("*.psm1")}))

        for path in [BUILD_SCRIPT, VALIDATE_SCRIPT, *MODULE_DIR.glob("*.psm1")]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("Copyright 2026 Leo L Zhang", text)
            self.assertLessEqual(len(text.splitlines()), 800, path)
            self.assertNotRegex(text, r"(?i)(?:^|[&\s])(py(?:thon)?(?:\.exe)?)(?:\s|$)")
            self.assertNotIn("ConvertFrom-Yaml", text)

    def test_cli_contract_and_identity_rules_are_explicit(self) -> None:
        build = BUILD_SCRIPT.read_text(encoding="utf-8")
        validator = VALIDATE_SCRIPT.read_text(encoding="utf-8")
        builder_module = (MODULE_DIR / "ProgramSetCoreReview.Builder.psm1").read_text(
            encoding="utf-8"
        )
        for option in (
            "review-name",
            "programs-file",
            "working-root",
            "output-root",
            "artifact-repo-mode",
            "source-root",
            "inventory-dir",
            "program-first",
            "profile",
            "output-dir",
            "working-branch",
            "delivery-root",
            "force-rescan-file",
        ):
            self.assertIn(option, build + builder_module)
        self.assertIn("manifest", validator)
        self.assertIn("review", validator)
        self.assertIn("ToUpperInvariant", builder_module)
        self.assertNotIn("TrimStart('@')", builder_module)
        self.assertIn("StringComparer]::Ordinal", builder_module)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_preserves_case_sensitive_identity_for_custom_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            profile = temp / "delivery-profile.yaml"
            working.mkdir()
            programs.write_text("abc\nABC\n", encoding="utf-8")
            profile.write_text(
                PROFILE.read_text(encoding="utf-8").replace(
                    "case: upper", "case: preserve"
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Case-sensitive identity",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(profile),
                    "--output-dir",
                    str(output),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = PYTHON_BUILDER.load_yaml(
                output / "program-set-core-input-manifest.yaml"
            )
            self.assertEqual(
                [entry["normalized_name"] for entry in manifest["programs"]],
                ["abc", "ABC"],
            )
            self.assertEqual(
                [entry["run_resolution"] for entry in manifest["programs"]],
                ["pending_source", "pending_source"],
            )

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_router_falls_back_to_native_builder_without_python(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            shims = temp / "shims"
            shims.mkdir()
            for command in ("py.cmd", "python.cmd"):
                (shims / command).write_text("@exit /b 9009\r\n", encoding="ascii")
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            write_artifacts(
                working / "modules" / "CAP-ID-0003-normal_program" / "CC050"
            )
            programs.write_text("CC050\n", encoding="utf-8")
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get("PATH", "")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "BuildProgramSetCoreReview",
                    "--review-name",
                    "Router fallback",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--program-first",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue((output / "program-set-core-input-manifest.yaml").is_file())

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_router_passes_build_prefix_to_py_launcher(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            shims = temp / "shims"
            shims.mkdir()
            log = temp / "py-arguments.log"
            (shims / "py.cmd").write_text(
                '@echo %*>>"%ROUTER_LOG%"\r\n@exit /b 0\r\n',
                encoding="ascii",
            )
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get(
                "PATH", ""
            )
            environment["ROUTER_LOG"] = str(log)

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "BuildProgramSetCoreReview",
                    "--review-name",
                    "Prefix probe",
                ],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            invocations = log.read_text(encoding="ascii").splitlines()
            self.assertGreaterEqual(len(invocations), 2)
            self.assertIn("program_set_core_review.py build --review-name", invocations[-1])

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_matches_python_manifest_contract_without_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            working = temp / "delivery"
            output = temp / "review"
            programs = temp / "programs.txt"
            write_artifacts(
                working / "modules" / "CAP-ID-0003-normal_program" / "@CU118"
            )
            programs.write_text("@cu118\nCU118\n@cu118\n", encoding="utf-8")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Card Auth",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(working),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--working-branch",
                    "develop-leo",
                    "--program-first",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = PYTHON_BUILDER.load_yaml(
                output / "program-set-core-input-manifest.yaml"
            )
            entries = manifest["programs"]
            self.assertEqual(entries[0]["normalized_name"], "@CU118")
            self.assertEqual(entries[0]["run_resolution"], "analyzed_this_run")
            self.assertEqual(entries[1]["normalized_name"], "CU118")
            self.assertEqual(entries[1]["run_resolution"], "pending_source")
            self.assertEqual(entries[2]["run_resolution"], "reused_same_run")
            self.assertTrue(manifest["run_profile"]["program_first"])
            self.assertIn("## Program Set Reading Summary", (output / "program-set-sme-core-review.md").read_text(encoding="utf-8"))

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_validator_exit_and_findings_match_python(self) -> None:
        from tests.test_program_set_core_review_builder import build_review_fixture

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest, review, _ = build_review_fixture(Path(temp_dir))
            valid = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT), "--manifest", str(manifest), "--review", str(review)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertIn("OK: program-set SME core review contract passed", valid.stdout)

            review.write_text(review.read_text(encoding="utf-8") + "\n## Nodes\n\nForbidden.\n", encoding="utf-8")
            invalid = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT), "--manifest", str(manifest), "--review", str(review)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertIn("forbidden full-flow section: Nodes", invalid.stderr)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_validator_rejects_trailing_yaml_and_classifies_runtime_errors(self) -> None:
        from tests.test_program_set_core_review_builder import build_review_fixture

        with tempfile.TemporaryDirectory() as temp_dir:
            manifest, review, _ = build_review_fixture(Path(temp_dir))
            manifest.write_text(
                manifest.read_text(encoding="utf-8") + "\n- unexpected-root-item\n",
                encoding="utf-8",
            )
            malformed = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(VALIDATE_SCRIPT),
                    "--manifest",
                    str(manifest),
                    "--review",
                    str(review),
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(malformed.returncode, 1)
            self.assertIn("Unexpected trailing YAML content", malformed.stderr)

            usage = subprocess.run(
                [POWERSHELL, "-NoProfile", "-File", str(VALIDATE_SCRIPT)],
                text=True,
                capture_output=True,
            )
            self.assertEqual(usage.returncode, 2)

    @unittest.skipUnless(POWERSHELL, "PowerShell runtime unavailable")
    def test_builder_preserves_git_inventory_freshness_and_approved_repo_mode(self) -> None:
        from tests.test_program_set_core_review_builder import (
            init_clean_git_source_root,
            write_inventory_cache,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            document_repo = temp / "document-repo"
            document_repo.mkdir()
            source = temp / "source"
            output = temp / "review"
            programs = temp / "programs.txt"
            init_clean_git_source_root(source)
            write_inventory_cache(source)
            programs.write_text("CU257F\nMISSINGPGM\nMISSINGPGM\n", encoding="utf-8")

            result = subprocess.run(
                [
                    POWERSHELL,
                    "-NoProfile",
                    "-File",
                    str(BUILD_SCRIPT),
                    "--review-name",
                    "Inventory Review",
                    "--programs-file",
                    str(programs),
                    "--working-root",
                    str(document_repo),
                    "--source-root",
                    str(source),
                    "--profile",
                    str(PROFILE),
                    "--output-dir",
                    str(output),
                    "--artifact-repo-mode",
                    "approved_document_repo",
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            manifest = PYTHON_BUILDER.load_yaml(
                output / "program-set-core-input-manifest.yaml"
            )
            self.assertEqual(manifest["source_inventory"]["freshness"], "fresh")
            self.assertEqual(
                manifest["source_inventory"]["programs"][0]["inventory_status"],
                "found",
            )
            self.assertTrue(
                manifest["source_inventory"]["programs"][0]["targeted_scan_allowed"]
            )
            self.assertEqual(
                manifest["programs"][1]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["programs"][2]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["source_inventory"]["programs"][-1]["run_resolution"],
                "blocked_missing_source",
            )
            self.assertEqual(
                manifest["run_profile"]["artifact_repo_mode"],
                "approved_document_repo",
            )


if __name__ == "__main__":
    unittest.main()
