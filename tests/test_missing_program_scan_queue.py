from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QUEUE_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "create_missing_program_scan_queue.py"
)
BUILDER_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-flow-analyzer"
    / "scripts"
    / "program_set_core_review.py"
)


def load_builder():
    import importlib.util

    spec = importlib.util.spec_from_file_location("queue_test_builder", BUILDER_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load builder")
    module = importlib.util.module_from_spec(spec)
    sys.modules["queue_test_builder"] = module
    spec.loader.exec_module(module)
    return module


BUILDER = load_builder()


def compact_status(status: str = "missing") -> dict[str, dict[str, str]]:
    return {
        BUILDER.artifact_key(filename): {"status": status}
        for filename in BUILDER.REQUIRED_COMPACT_ARTIFACTS
    }


class MissingProgramScanQueueTests(unittest.TestCase):
    def write_manifest(self, root: Path, freshness: str = "fresh") -> Path:
        source_file = root / "source" / "src" / "CU106.RPGLE"
        source_file.parent.mkdir(parents=True)
        source_file.write_text("**FREE\nRETURN;\n", encoding="utf-8")
        inventory_list = root / "source" / "outputs" / "repo-scan" / "program-list.csv"
        inventory_list.parent.mkdir(parents=True)
        inventory_list.write_text(
            "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
            "CU106,program,RPGLE,src/CU106.RPGLE,100,normal_program,test\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": "0.2",
            "review_id": "review-auth--program-set-cu106",
            "review_name": "Auth flow",
            "workspace_profile": {
                "program_tier_roots": {
                    "normal_program": "modules/custom-normal",
                }
            },
            "source_inventory": {
                "freshness": freshness,
                "program_list": {"path": str(inventory_list), "status": "present"},
                "programs": [
                    {
                        "program": "CU106",
                        "inventory_status": "found",
                        "source_path": "src/CU106.RPGLE",
                        "source_kind": "RPGLE",
                        "size_tier": "normal_program",
                        "targeted_scan_allowed": freshness == "fresh",
                    },
                    {
                        "program": "CCB11",
                        "inventory_status": "missing_from_inventory",
                        "source_path": None,
                        "targeted_scan_allowed": False,
                    },
                ],
            },
            "programs": [
                {
                    "normalized_name": "CU106",
                    "run_resolution": "pending_source",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status(),
                },
                {
                    "normalized_name": "CCB11",
                    "run_resolution": "blocked_missing_source",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status(),
                },
                {
                    "normalized_name": "COMPLETE",
                    "run_resolution": "analyzed_this_run",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status("present"),
                },
            ],
        }
        manifest_path = root / "program-set-core-input-manifest.yaml"
        manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
        return manifest_path

    def test_creates_queue_for_resolvable_missing_programs_and_blocks_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = self.write_manifest(root)
            source_root = root / "source"
            delivery_root = root / "delivery"
            output_dir = root / "missing-program-list-batch"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest),
                    "--source-root",
                    str(source_root),
                    "--delivery-root",
                    str(delivery_root),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("queue_created_with_blocked_programs", result.stdout)
            prompt = output_dir / "prompt-queue" / "0001-CU106.md"
            self.assertTrue(prompt.is_file())
            prompt_text = prompt.read_text(encoding="utf-8")
            self.assertIn(
                f"Source path: `{source_root.resolve()}/src/CU106.RPGLE`", prompt_text
            )
            self.assertIn(
                f"Output directory: `{delivery_root}/modules/custom-normal/CU106`",
                prompt_text,
            )
            self.assertFalse((output_dir / "prompt-queue" / "0002-CCB11.md").exists())
            self.assertIn("CCB11", (output_dir / "blocked-programs.csv").read_text(encoding="utf-8"))
            self.assertTrue((output_dir / "program-list-status.csv").is_file())
            queue_state = (output_dir / "program-set-scan-queue.yaml").read_text(encoding="utf-8")
            self.assertIn("queue_created_with_blocked_programs", queue_state)
            self.assertIn("CU106", queue_state)
            self.assertIn("CCB11", queue_state)

    def test_stale_inventory_does_not_create_source_scan_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = self.write_manifest(root, freshness="stale")
            output_dir = root / "missing-program-list-batch"
            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest),
                    "--source-root",
                    str(root / "source"),
                    "--delivery-root",
                    str(root / "delivery"),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn("blocked_missing_source", result.stdout)
            self.assertFalse((output_dir / "prompt-queue").exists())
            blocked = (output_dir / "blocked-programs.csv").read_text(encoding="utf-8")
            self.assertIn("provide a fresh inventory or an exact approved source mapping", blocked)
            queue_state = (output_dir / "program-set-scan-queue.yaml").read_text(
                encoding="utf-8"
            )
            self.assertIn("fresh externally prepared inventory", queue_state)
            self.assertNotIn("rerun inventory", queue_state.lower())

    def test_semantically_invalid_complete_file_set_is_targeted_for_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = self.write_manifest(root)
            manifest = BUILDER.load_yaml(manifest_path)
            cu106 = manifest["programs"][0]
            cu106["compact_artifacts"] = compact_status("present")
            cu106["artifact_readiness"] = {
                "status": "not_ready",
                "findings": ["pending_deep_read remains in routine detail batch"],
            }
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
            output_dir = root / "missing-program-list-batch"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--source-root",
                    str(root / "source"),
                    "--delivery-root",
                    str(root / "delivery"),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            prompt = output_dir / "prompt-queue" / "0001-CU106.md"
            self.assertTrue(prompt.is_file())
            queue_csv = (output_dir / "program-list.csv").read_text(encoding="utf-8")
            self.assertIn("CU106", queue_csv)
            self.assertNotIn("COMPLETE", queue_csv)

    def test_v04_queue_uses_frozen_inventory_snapshot_not_mutated_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = self.write_manifest(root)
            manifest = BUILDER.load_yaml(manifest_path)
            manifest["schema_version"] = "0.4"
            manifest["programs"] = [manifest["programs"][0]]
            manifest["source_inventory"]["programs"] = [
                manifest["source_inventory"]["programs"][0]
            ]
            inventory_path = Path(
                manifest["source_inventory"]["program_list"]["path"]
            )
            (root / "source" / "src" / "ATTACK.RPGLE").write_text(
                "**FREE\nRETURN;\n", encoding="utf-8"
            )
            inventory_path.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CU106,program,RPGLE,src/ATTACK.RPGLE,5,normal_program,mutated\n",
                encoding="utf-8",
            )
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
            output_dir = root / "missing-program-list-batch"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--source-root",
                    str(root / "source"),
                    "--delivery-root",
                    str(root / "delivery"),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            queue_csv = (output_dir / "program-list.csv").read_text(encoding="utf-8")
            self.assertIn("src/CU106.RPGLE", queue_csv)
            self.assertNotIn("ATTACK.RPGLE", queue_csv)

    def test_only_missing_ccb11_is_queued_when_other_programs_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = self.write_manifest(root)
            manifest = BUILDER.load_yaml(manifest_path)
            inventory_path = Path(manifest["source_inventory"]["program_list"]["path"])
            inventory_path.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CCB11,program,RPGLE,src/CCB11.RPGLE,80,normal_program,test\n",
                encoding="utf-8",
            )
            (root / "source" / "src" / "CCB11.RPGLE").write_text(
                "**FREE\nRETURN;\n", encoding="utf-8"
            )
            manifest["source_inventory"]["programs"] = [
                {
                    "program": "CCB11",
                    "inventory_status": "found",
                    "source_path": "src/CCB11.RPGLE",
                    "source_kind": "RPGLE",
                    "size_tier": "normal_program",
                    "targeted_scan_allowed": True,
                }
            ]
            manifest["programs"] = [
                {
                    "normalized_name": "CU106",
                    "run_resolution": "analyzed_this_run",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status("present"),
                    "artifact_readiness": {"status": "ready", "findings": []},
                },
                {
                    "normalized_name": "CCB11",
                    "run_resolution": "pending_source",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status(),
                    "artifact_readiness": {
                        "status": "not_ready",
                        "findings": ["required artifacts are missing"],
                    },
                },
            ]
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
            output_dir = root / "missing-program-list-batch"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--source-root",
                    str(root / "source"),
                    "--delivery-root",
                    str(root / "delivery"),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            prompts = sorted(path.name for path in (output_dir / "prompt-queue").glob("*.md"))
            self.assertEqual(prompts, ["0001-CCB11.md"])
            queue_csv = (output_dir / "program-list.csv").read_text(encoding="utf-8")
            self.assertIn("CCB11", queue_csv)
            self.assertNotIn("CU106", queue_csv)

    def test_blocks_absolute_escaping_and_missing_inventory_source_paths(self) -> None:
        cases = {
            "absolute": None,
            "escape": "../outside/CU106.RPGLE",
            "missing": "src/DOES-NOT-EXIST.RPGLE",
        }
        for label, source_path in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                manifest_path = self.write_manifest(root)
                manifest = BUILDER.load_yaml(manifest_path)
                manifest["programs"] = [manifest["programs"][0]]
                if source_path is None:
                    source_path = str((root / "outside" / "CU106.RPGLE").resolve())
                manifest["source_inventory"]["programs"][0]["source_path"] = source_path
                inventory_path = Path(
                    manifest["source_inventory"]["program_list"]["path"]
                )
                inventory_path.write_text(
                    "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                    f"CU106,program,RPGLE,{source_path},100,normal_program,test\n",
                    encoding="utf-8",
                )
                manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
                output_dir = root / "missing-program-list-batch"

                result = subprocess.run(
                    [
                        sys.executable,
                        str(QUEUE_SCRIPT),
                        "--manifest",
                        str(manifest_path),
                        "--source-root",
                        str(root / "source"),
                        "--delivery-root",
                        str(root / "delivery"),
                        "--out-dir",
                        str(output_dir),
                    ],
                    text=True,
                    capture_output=True,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("blocked_missing_source", result.stdout)
                self.assertFalse((output_dir / "prompt-queue").exists())
                blocked = (output_dir / "blocked-programs.csv").read_text(
                    encoding="utf-8"
                )
                self.assertIn("CU106", blocked)
                self.assertRegex(
                    blocked,
                    "absolute|escapes source root|does not exist or is not a file",
                )

    def test_blocks_symlinked_inventory_source_that_resolves_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = self.write_manifest(root)
            manifest = BUILDER.load_yaml(manifest_path)
            manifest["programs"] = [manifest["programs"][0]]
            outside = root / "outside.RPGLE"
            outside.write_text("**FREE\nRETURN;\n", encoding="utf-8")
            link = root / "source" / "src" / "LINK.RPGLE"
            link.symlink_to(outside)
            manifest["source_inventory"]["programs"][0]["source_path"] = (
                "src/LINK.RPGLE"
            )
            inventory_path = Path(manifest["source_inventory"]["program_list"]["path"])
            inventory_path.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CU106,program,RPGLE,src/LINK.RPGLE,100,normal_program,test\n",
                encoding="utf-8",
            )
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
            output_dir = root / "missing-program-list-batch"

            result = subprocess.run(
                [
                    sys.executable,
                    str(QUEUE_SCRIPT),
                    "--manifest",
                    str(manifest_path),
                    "--source-root",
                    str(root / "source"),
                    "--delivery-root",
                    str(root / "delivery"),
                    "--out-dir",
                    str(output_dir),
                ],
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            blocked = (output_dir / "blocked-programs.csv").read_text(encoding="utf-8")
            self.assertIn("escapes source root", blocked)
            self.assertFalse((output_dir / "prompt-queue").exists())

    def test_force_regeneration_removes_stale_prompts_and_generated_csvs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest_path = self.write_manifest(root)
            manifest = BUILDER.load_yaml(manifest_path)
            manifest["programs"] = [manifest["programs"][0]]
            manifest["source_inventory"]["programs"] = [
                manifest["source_inventory"]["programs"][0]
            ]
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")
            output_dir = root / "missing-program-list-batch"
            command = [
                sys.executable,
                str(QUEUE_SCRIPT),
                "--manifest",
                str(manifest_path),
                "--source-root",
                str(root / "source"),
                "--delivery-root",
                str(root / "delivery"),
                "--out-dir",
                str(output_dir),
                "--force",
            ]

            first = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue((output_dir / "prompt-queue" / "0001-CU106.md").is_file())
            (output_dir / "blocked-programs.csv").write_text(
                "member,reason\nOLD,stale\n", encoding="utf-8"
            )

            source_file = root / "source" / "src" / "CCB11.RPGLE"
            source_file.write_text("**FREE\nRETURN;\n", encoding="utf-8")
            manifest["programs"] = [
                {
                    "normalized_name": "CCB11",
                    "run_resolution": "pending_source",
                    "tier": "normal_program",
                    "compact_artifacts": compact_status(),
                }
            ]
            manifest["source_inventory"]["programs"] = [
                {
                    "program": "CCB11",
                    "inventory_status": "found",
                    "source_path": "src/CCB11.RPGLE",
                    "source_kind": "RPGLE",
                    "size_tier": "normal_program",
                    "targeted_scan_allowed": True,
                }
            ]
            inventory_path = Path(manifest["source_inventory"]["program_list"]["path"])
            inventory_path.write_text(
                "member,object_type,source_kind,path,total_lines,size_tier,tier_reason\n"
                "CCB11,program,RPGLE,src/CCB11.RPGLE,80,normal_program,test\n",
                encoding="utf-8",
            )
            manifest_path.write_text(BUILDER.dump_yaml(manifest), encoding="utf-8")

            second = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(second.returncode, 0, second.stderr)
            prompts = sorted(
                path.name for path in (output_dir / "prompt-queue").glob("*.md")
            )
            self.assertEqual(prompts, ["0001-CCB11.md"])
            queue_csv = (output_dir / "program-list.csv").read_text(encoding="utf-8")
            self.assertIn("CCB11", queue_csv)
            self.assertNotIn("CU106", queue_csv)
            self.assertFalse((output_dir / "blocked-programs.csv").exists())


if __name__ == "__main__":
    unittest.main()
