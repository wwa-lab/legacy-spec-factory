from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ANALYZER = REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer" / "SKILL.md"
FLOW_ANALYZER = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "SKILL.md"
FLOW_OUTPUT_CONTRACT = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "references" / "output-contract.md"
)
SME_CORE_TEMPLATE = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "templates" / "sme-core-review.md"
)
RPG_E2E_GUIDE = REPO_ROOT / "docs" / "rpg-code-scan-e2e-guideline.md"


class CentralArtifactReuseGuidanceTests(unittest.TestCase):
    def test_program_analyzer_checks_central_artifacts_before_scan(self) -> None:
        skill_text = PROGRAM_ANALYZER.read_text(encoding="utf-8")

        self.assertIn("Central Artifact Reuse Preflight", skill_text)
        self.assertIn("legacy-modernization-delivery", skill_text)
        self.assertIn("central_lookup_result", skill_text)
        self.assertIn("found_on_remote_main", skill_text)
        self.assertIn("not_found_on_remote_main", skill_text)
        self.assertIn("remote_unavailable", skill_text)
        self.assertIn("GitHub remote `main`", skill_text)
        self.assertIn("origin/main", skill_text)
        self.assertIn("git ls-remote", skill_text)
        self.assertIn("temporary shallow clone", skill_text)
        self.assertNotIn("gh api", skill_text)
        self.assertIn("delivery_artifact_lookup_profile", skill_text)
        self.assertIn("program_folder_patterns", skill_text)
        self.assertIn("modules/*/{PROGRAM}", skill_text)
        self.assertIn('preserve_prefixes: ["@"]', skill_text)
        self.assertIn("exact_folder_name_match: true", skill_text)
        self.assertIn("`@CU118` and `CU118` are distinct programs", skill_text)
        self.assertNotIn('strip_prefixes: ["@"]', skill_text)
        self.assertIn("The delivery repo name is configurable", skill_text)
        self.assertIn("Do not run deterministic source indexing", skill_text)

    def test_flow_analyzer_reuses_existing_program_artifacts_for_sme_flow_input(self) -> None:
        skill_text = FLOW_ANALYZER.read_text(encoding="utf-8")
        contract_text = FLOW_OUTPUT_CONTRACT.read_text(encoding="utf-8")

        for text in (skill_text, contract_text):
            self.assertIn("central artifact reuse", text.lower())
            self.assertIn("SME provides a program flow", text)
            self.assertIn("central_lookup_result", text)
            self.assertIn("found_on_remote_main", text)
            self.assertIn("not_found_on_remote_main", text)
            self.assertIn("Core Completeness Ledger", text)
            self.assertIn("GitHub remote `main`", text)
            self.assertIn("delivery_artifact_lookup_profile", text)
            self.assertIn("program-set-sme-core-review.md", text)
            self.assertIn("remote-main sparse checkout", text)
            self.assertNotIn("reuse_approved_artifact", text)

    def test_sme_core_review_template_tracks_omissions_without_full_flow_sections(self) -> None:
        template_text = SME_CORE_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("Core Completeness Ledger", template_text)
        self.assertIn("Calculation Logic", template_text)
        self.assertIn("Validation Logic", template_text)
        self.assertIn("Exception Handling", template_text)
        self.assertIn("Message Inventory", template_text)
        self.assertIn("No program may be omitted", template_text)
        self.assertNotIn("## Nodes", template_text)
        self.assertNotIn("## Edges", template_text)
        self.assertNotIn("## Flow Replay Path", template_text)

    def test_e2e_guide_starts_with_central_repo_lookup(self) -> None:
        guide_text = RPG_E2E_GUIDE.read_text(encoding="utf-8")

        self.assertIn("Check Central Delivery Repo Before Scanning", guide_text)
        self.assertIn("Do not rerun program analysis when the central delivery repo remote `main`", guide_text)
        self.assertIn("legacy-modernization-delivery", guide_text)
        self.assertIn("GitHub remote `main`", guide_text)
        self.assertIn("git ls-remote", guide_text)
        self.assertIn("temporary shallow clone", guide_text)
        self.assertNotIn("gh api", guide_text)
        self.assertIn("stale local checkout", guide_text)
        self.assertIn("Delivery Artifact Lookup Profile", guide_text)
        self.assertIn("modules/*/{PROGRAM}", guide_text)
        self.assertIn('preserve_prefixes: ["@"]', guide_text)
        self.assertIn("exact_folder_name_match: true", guide_text)
        self.assertIn("`@CU118` and `CU118` are different programs", guide_text)
        self.assertNotIn('strip_prefixes: ["@"]', guide_text)
        self.assertIn("Other departments can override", guide_text)
        self.assertIn("program-analysis-summary.yaml", guide_text)


if __name__ == "__main__":
    unittest.main()
