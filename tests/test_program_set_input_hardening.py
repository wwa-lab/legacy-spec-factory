from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "scripts"
PYTHON_SCRIPT = SCRIPT_DIR / "program_set_core_review.py"
POWERSHELL_BUILDER = SCRIPT_DIR / "powershell" / "ProgramSetCoreReview.Builder.psm1"
POWERSHELL_INPUT = SCRIPT_DIR / "powershell" / "ProgramSetCoreReview.Input.psm1"


def load_builder():
    spec = importlib.util.spec_from_file_location(
        "program_set_input_hardening_builder", PYTHON_SCRIPT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {PYTHON_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


class ProgramSetInputHardeningTests(unittest.TestCase):
    def test_text_reader_preserves_ibmi_special_prefixes_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            program_list = Path(temp_dir) / "programs.txt"
            program_list.write_text(
                "# operator note\n@CU118\n#JOB1\n#\n$PAY1\nA_B2\n",
                encoding="utf-8",
            )

            self.assertEqual(
                BUILDER.read_programs_file(program_list),
                ["@CU118", "#JOB1", "#", "$PAY1", "A_B2"],
            )

    def test_csv_reader_uses_first_column_and_skips_compatible_header(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            program_list = Path(temp_dir) / "programs.csv"
            program_list.write_text(
                "\ufeffmember,object_type,path\n"
                "@CU118,program,src/@CU118.RPGLE\n"
                '"#JOB1",program,"src/with,comma/#JOB1.CLLE"\n'
                "$PAY1,program,src/$PAY1.RPGLE\n",
                encoding="utf-8",
            )

            self.assertEqual(
                BUILDER.read_programs_file(program_list),
                ["@CU118", "#JOB1", "$PAY1"],
            )

    def test_headerless_csv_keeps_its_first_program(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            program_list = Path(temp_dir) / "programs.csv"
            program_list.write_text(
                "CU106,program,src/CU106.RPGLE\nCU101A,program,src/CU101A.RPGLE\n",
                encoding="utf-8",
            )

            self.assertEqual(
                BUILDER.read_programs_file(program_list), ["CU106", "CU101A"]
            )

    def test_normalization_accepts_safe_ibmi_object_tokens(self) -> None:
        profile = {"program_name_normalization": {"case": "upper"}}
        for raw, expected in (
            ("@cu118", "@CU118"),
            ("#job1", "#JOB1"),
            ("$pay1", "$PAY1"),
            ("a_b2", "A_B2"),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(BUILDER.normalize_program_name(raw, profile), expected)

    def test_normalization_rejects_path_control_and_non_object_tokens(self) -> None:
        profile = {"program_name_normalization": {"case": "upper"}}
        for raw in (
            "../ESCAPE",
            r"..\ESCAPE",
            ".",
            "A/B",
            r"A\B",
            "A.B",
            "A B",
            "A\x00B",
            "1START",
            "-OPTION",
            "PROGRAMNAME1",
        ):
            with self.subTest(raw=raw):
                with self.assertRaisesRegex(
                    ValueError, "invalid normalized program name.*IBM i object token"
                ):
                    BUILDER.normalize_program_name(raw, profile)

    def test_artifact_resolution_rejects_program_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "modules" / "tier" / "SAFE").mkdir(parents=True)
            lookup = {"program_folder_patterns": ["modules/*/{PROGRAM}"]}

            with self.assertRaisesRegex(ValueError, "invalid normalized program name"):
                BUILDER.find_program_artifact_root(root, "../../outside", lookup)

    def test_cli_rejects_unsafe_program_before_writing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            artifact_root.mkdir()
            output_parent = root / "reviews"
            programs_file = root / "programs.txt"
            programs_file.write_text("../ESCAPE\n", encoding="utf-8")
            profile = (
                REPO_ROOT
                / "skills"
                / "legacy-ibmi-flow-analyzer"
                / "templates"
                / "delivery-profile.yaml"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(PYTHON_SCRIPT),
                    "build",
                    "--review-name",
                    "unsafe input",
                    "--programs-file",
                    str(programs_file),
                    "--working-root",
                    str(artifact_root),
                    "--profile",
                    str(profile),
                    "--output-dir",
                    str(output_parent),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid normalized program name", result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertFalse(output_parent.exists())

    def test_cli_reports_malformed_csv_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            artifact_root = root / "artifacts"
            artifact_root.mkdir()
            programs_file = root / "programs.csv"
            programs_file.write_text('"CU106,program\n', encoding="utf-8")
            profile = (
                REPO_ROOT
                / "skills"
                / "legacy-ibmi-flow-analyzer"
                / "templates"
                / "delivery-profile.yaml"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(PYTHON_SCRIPT),
                    "build",
                    "--review-name",
                    "malformed CSV",
                    "--programs-file",
                    str(programs_file),
                    "--working-root",
                    str(artifact_root),
                    "--profile",
                    str(profile),
                    "--output-dir",
                    str(root / "reviews"),
                ],
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot read programs file", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_powershell_input_module_has_csv_and_token_validation_parity(self) -> None:
        builder = POWERSHELL_BUILDER.read_text(encoding="utf-8")
        self.assertIn("ProgramSetCoreReview.Input.psm1", builder)
        self.assertTrue(POWERSHELL_INPUT.is_file())
        input_module = POWERSHELL_INPUT.read_text(encoding="utf-8")
        self.assertIn("TextFieldParser", input_module)
        self.assertIn("program_name", input_module)
        self.assertIn("object_name", input_module)
        self.assertIn("IBM i object token", input_module)
        self.assertIn("[A-Za-z@#$]", input_module)
        self.assertIn("Normalize-FlowProgramName", input_module)


if __name__ == "__main__":
    unittest.main()
