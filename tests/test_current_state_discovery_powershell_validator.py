from __future__ import annotations

import importlib.util
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_MODULE_PATH = REPO_ROOT / "tests" / "test_current_state_discovery_validator.py"
FIXTURE_SPEC = importlib.util.spec_from_file_location(
    "current_state_discovery_fixtures", FIXTURE_MODULE_PATH
)
if FIXTURE_SPEC is None or FIXTURE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load fixture module: {FIXTURE_MODULE_PATH}")
fixtures = importlib.util.module_from_spec(FIXTURE_SPEC)
FIXTURE_SPEC.loader.exec_module(fixtures)

SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-current-state-discovery"
    / "scripts"
    / "validate_current_state_discovery_package.ps1"
)
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
ROUTER = REPO_ROOT / "scripts" / "invoke-windows-tool.ps1"


def run_powershell_validator(*arguments: str) -> subprocess.CompletedProcess[str]:
    if POWERSHELL is None:
        raise RuntimeError("PowerShell runtime unavailable")
    return subprocess.run(
        [
            str(POWERSHELL),
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(SCRIPT_PATH),
            *arguments,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@unittest.skipUnless(POWERSHELL, "PowerShell runtime is not installed")
class CurrentStateDiscoveryPowerShellRuntimeTests(unittest.TestCase):
    def assert_python_parity(self, *arguments: str) -> None:
        python_result = fixtures.run_python_validator(*arguments)
        powershell_result = run_powershell_validator(*arguments)
        self.assertEqual(
            powershell_result.returncode,
            python_result.returncode,
            powershell_result.stderr,
        )
        self.assertEqual(
            powershell_result.stdout.splitlines(), python_result.stdout.splitlines()
        )
        self.assertEqual(
            powershell_result.stderr.splitlines(), python_result.stderr.splitlines()
        )

    def test_complete_package_matches_python_strict_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            self.assert_python_parity(
                "--quality-gate", "--require-ready", str(package)
            )

    def test_router_falls_back_to_native_validator_without_python(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows command shims require a Windows host")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            shims = root / "shims"
            shims.mkdir()
            for command in ("py.cmd", "python.cmd"):
                (shims / command).write_text("@exit /b 9009\r\n", encoding="ascii")
            package = root / "package"
            fixtures.write_valid_package(package)
            environment = dict(os.environ)
            environment["PATH"] = str(shims) + os.pathsep + environment.get("PATH", "")
            result = subprocess.run(
                [
                    str(POWERSHELL),
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(ROUTER),
                    "ValidateCurrentStateDiscovery",
                    "--quality-gate",
                    "--require-ready",
                    str(package),
                ],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PASS: current-state discovery package structure is valid", result.stdout)

    def test_invalid_package_path_matches_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assert_python_parity(str(Path(temp_dir) / "missing"))

    def test_negative_finding_order_and_exit_code_match_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            (package / "discovery-index.yaml").write_text(
                "package_type: current_state_discovery\n"
                "status: draft\noutputs:\n  report: <REPORT>\n",
                encoding="utf-8",
            )
            (package / "behavior-claim-ledger.csv").write_text(
                "\n".join(
                    (
                        fixtures.BEHAVIOR_HEADER,
                        "CLM-001,function,CLM-002,Payments,Folder contains a program,"
                        ",,DOC-001,unknown,EV-001,weak,Gap,needs_sme_review,CLM-003,,",
                    )
                ),
                encoding="utf-8",
            )
            self.assert_python_parity(
                "--quality-gate", "--require-ready", str(package)
            )

    def test_missing_files_and_structural_findings_match_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            (package / "document-master-index.md").unlink()
            (package / "function-catalog.yaml").write_text(
                "catalog_type: wrong\n", encoding="utf-8"
            )
            (package / "functional-discovery-report.md").write_text(
                "# Functional Discovery Report\n", encoding="utf-8"
            )
            (package / "traceability-matrix.csv").write_text(
                "wrong,header\nvalue,row\n", encoding="utf-8"
            )
            self.assert_python_parity(str(package))

    def test_non_gap_quality_findings_match_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            (package / "behavior-claim-ledger.csv").write_text(
                "\n".join(
                    (
                        fixtures.BEHAVIOR_HEADER,
                        "BCL-PAY-001,function,CAND-PAY-001,Payments,Meaning,,,,,"
                        ",documented,Confirmed,needs_sme_review,,,",
                        "BCL-PAY-002,function,CAND-PAY-002,Payments,Folder contains "
                        "a program,Customer submits,System records,DOC-001,unknown,"
                        "EV-001,documented,Confirmed,needs_sme_review,,,",
                    )
                ),
                encoding="utf-8",
            )
            report = (package / "functional-discovery-report.md").read_text(
                encoding="utf-8"
            )
            (package / "functional-discovery-report.md").write_text(
                report.replace(
                    "| Gap ID | Area | Missing / Unclear Evidence | Impact | "
                    "Owner / Route | Next Action | Status |",
                    "CLM-001",
                ),
                encoding="utf-8",
            )
            self.assert_python_parity("--quality-gate", str(package))

    def test_allow_placeholders_matches_python(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            (package / "document-master-index.md").write_text(
                "# Document Master Index\n<MODULE-SLUG>\n", encoding="utf-8"
            )
            self.assert_python_parity("--allow-placeholders", str(package))

    def test_utf8_bom_csv_header_matches_python_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            ledger = package / "behavior-claim-ledger.csv"
            ledger.write_bytes(b"\xef\xbb\xbf" + ledger.read_bytes())
            self.assert_python_parity("--quality-gate", str(package))

    def test_cli_help_and_usage_errors_have_argparse_exit_codes(self) -> None:
        help_result = run_powershell_validator("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        self.assertIn("--allow-placeholders", help_result.stdout)
        self.assertIn("--require-ready", help_result.stdout)
        self.assertIn("--quality-gate", help_result.stdout)

        for arguments, expected in (
            ((), "the following arguments are required: package"),
            (("--unknown",), "unrecognized arguments: --unknown"),
            (("first", "second"), "unrecognized arguments: second"),
        ):
            with self.subTest(arguments=arguments):
                result = run_powershell_validator(*arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(expected, result.stderr)

    def test_double_dash_preserves_positional_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            package = Path(temp_dir) / "package"
            fixtures.write_valid_package(package)
            self.assert_python_parity("--", str(package))


class CurrentStateDiscoveryPowerShellStaticTests(unittest.TestCase):
    def test_native_validator_is_portable_and_bounded(self) -> None:
        self.assertTrue(SCRIPT_PATH.is_file(), SCRIPT_PATH)
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        self.assertIn("#requires -version 5.1", text.lower())
        self.assertIn("Copyright 2026 Leo L Zhang", text)
        self.assertLessEqual(len(text.splitlines()), 800)

    def test_native_validator_preserves_python_cli(self) -> None:
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        for option in (
            "--allow-placeholders",
            "--require-ready",
            "--quality-gate",
        ):
            self.assertIn(option, text)
        self.assertIn("package path is not a directory", text)

    def test_native_fallback_does_not_execute_python_or_third_party_modules(self) -> None:
        text = SCRIPT_PATH.read_text(encoding="utf-8")
        python_command = re.compile(
            r"^\s*(?:&\s*)?(?:py|python)(?:\.exe)?\b", re.IGNORECASE | re.MULTILINE
        )
        self.assertIsNone(python_command.search(text))
        self.assertNotIn("ConvertFrom-Yaml", text)
        self.assertNotIn("ImportExcel", text)


if __name__ == "__main__":
    unittest.main()
