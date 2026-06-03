import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class WorkflowStateDeliveryModeTest(unittest.TestCase):
    def test_check_workflow_state_accepts_daily_delivery_mode(self):
        checker = load_script("check_workflow_state", "scripts/check-workflow-state.py")
        state_text = """
version: 1
project:
  name: XXX260004-demo
  root: docs/XXX260004-demo/
  started_at: 2026-06-04
  last_updated_at: 2026-06-04
  last_updated_by: legacy-modernization-orchestrator
current_focus:
  capability_id: CAP-CARD-REPLACEMENT
  module_slug: CARD-REPLACEMENT
  delivery_mode: daily_delivery
  stage_id: 3f Module Analysis Done
  next_skill: legacy-brd-writer
  next_artifact: 05_brds/CARD-REPLACEMENT/brd.md
  stage_card: skills/legacy-modernization-orchestrator/references/stage-cards/05a-brd-writing.md
  open_gates: []
capabilities:
  - id: CAP-CARD-REPLACEMENT
    module_slug: CARD-REPLACEMENT
    delivery_mode: daily_delivery
    stage_id: 3f Module Analysis Done
    last_artifact: 04_modules/CARD-REPLACEMENT/module-overview.md
    last_skill: legacy-ibmi-module-analyzer
    last_updated: 2026-06-04
    blocking:
      tbds: []
      sme_pending: []
      gates: []
    archived: false
history: []
"""
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "workflow-state.yaml"
            state_path.write_text(state_text)
            self.assertEqual(checker.validate(state_path), [])

    def test_generate_status_renders_delivery_mode(self):
        generator = load_script("generate_status", "scripts/generate-status.py")
        rendered = generator.render(
            {
                "project": {
                    "name": "XXX260004-demo",
                    "root": "docs/XXX260004-demo/",
                    "last_updated_at": "2026-06-04",
                    "last_updated_by": "legacy-modernization-orchestrator",
                },
                "current_focus": {
                    "capability_id": "CAP-CARD-REPLACEMENT",
                    "module_slug": "CARD-REPLACEMENT",
                    "delivery_mode": "daily_delivery",
                    "stage_id": "3f Module Analysis Done",
                    "next_skill": "legacy-brd-writer",
                    "next_artifact": "05_brds/CARD-REPLACEMENT/brd.md",
                    "open_gates": [],
                },
                "capabilities": [
                    {
                        "id": "CAP-CARD-REPLACEMENT",
                        "module_slug": "CARD-REPLACEMENT",
                        "delivery_mode": "daily_delivery",
                        "stage_id": "3f Module Analysis Done",
                        "last_updated": "2026-06-04",
                        "blocking": {"tbds": [], "sme_pending": [], "gates": []},
                    }
                ],
                "history": [],
            }
        )
        self.assertIn("**Delivery Mode:** `daily_delivery`", rendered)
        self.assertIn("| CAP-CARD-REPLACEMENT | CARD-REPLACEMENT | daily_delivery |", rendered)


if __name__ == "__main__":
    unittest.main()
