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
                        "program": "MISSING",
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
                    "normalized_name": "MISSING",
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
            self.assertFalse((output_dir / "prompt-queue" / "0002-MISSING.md").exists())
            self.assertIn("MISSING", (output_dir / "blocked-programs.csv").read_text(encoding="utf-8"))
            self.assertTrue((output_dir / "program-list-status.csv").is_file())
            queue_state = (output_dir / "program-set-scan-queue.yaml").read_text(encoding="utf-8")
            self.assertIn("queue_created_with_blocked_programs", queue_state)
            self.assertIn("CU106", queue_state)
            self.assertIn("MISSING", queue_state)

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
            self.assertIn("rerun legacy-ibmi-inventory first", blocked)


if __name__ == "__main__":
    unittest.main()
