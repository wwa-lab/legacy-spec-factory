from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRAM_ANALYZER = REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer" / "SKILL.md"
FLOW_ANALYZER = REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "SKILL.md"
FLOW_OUTPUT_CONTRACT = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "references" / "output-contract.md"
)
FLOW_PROMPT_TEMPLATE = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "templates" / "program-flow-prompt.md"
)
SME_CORE_TEMPLATE = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "templates" / "sme-core-review.md"
)
DELIVERY_PROFILE_TEMPLATE = (
    REPO_ROOT / "skills" / "legacy-ibmi-flow-analyzer" / "templates" / "delivery-profile.yaml"
)
RPG_E2E_GUIDE = REPO_ROOT / "docs" / "rpg-code-scan-e2e-guideline.md"
DELIVERY_PROFILE_QUICKSTART = REPO_ROOT / "docs" / "delivery-profile-quickstart.md"


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

    def test_flow_analyzer_defaults_to_approved_document_repo_evidence(self) -> None:
        skill_text = FLOW_ANALYZER.read_text(encoding="utf-8")
        contract_text = FLOW_OUTPUT_CONTRACT.read_text(encoding="utf-8")
        prompt_text = FLOW_PROMPT_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("program-evidence first", skill_text)
        normalized_skill = " ".join(skill_text.lower().split())
        self.assertIn("approved_document_repo` is the default", normalized_skill)
        self.assertIn("current_run` is explicit opt-in", normalized_skill)
        self.assertIn("Artifact repo mode: approved_document_repo", prompt_text)
        self.assertIn("Artifact repo mode: current_run", prompt_text)
        self.assertIn("generated automatically from the ordered list above", prompt_text)
        self.assertNotIn("Programs file: <PROGRAM-LIST-PATH>", prompt_text)
        for text in (skill_text, contract_text):
            self.assertIn("run_resolution", text)
            self.assertIn("analyzed_this_run", text)
            self.assertIn("reused_same_run", text)
            self.assertIn("pending_source", text)
            self.assertIn("blocked_missing_source", text)
            self.assertIn("Core Completeness Ledger", text)
            self.assertIn("<folder_slug>--sme-core-review.md", text)
            self.assertNotIn("central_lookup_result", text)
            self.assertNotIn("found_on_remote_main", text)
            self.assertNotIn("not_found_on_remote_main", text)
            self.assertNotIn("reuse_approved_artifact", text)

        self.assertIn("program_artifact_resolution_profile", contract_text)
        self.assertIn("current_run", contract_text)
        self.assertIn("approved_document_repo", contract_text)
        self.assertIn("delivery_workspace_profile", skill_text)
        self.assertIn("templates/delivery-profile.yaml", skill_text)

    def test_flow_analyzer_documents_read_only_approved_artifact_requalification(self) -> None:
        skill_text = FLOW_ANALYZER.read_text(encoding="utf-8")
        profile_text = DELIVERY_PROFILE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("Approved Artifact Requalification", skill_text)
        self.assertIn("requalify_approved_program_artifacts.py", skill_text)
        self.assertIn("create_approved_artifact_repair_queue.py", skill_text)
        self.assertIn("one prompt per repairable program", " ".join(skill_text.lower().split()))
        self.assertIn("approved_artifact_requalification_profile", profile_text)
        self.assertIn("profile_folder_patterns_only", profile_text)
        self.assertIn("format_repairable", skill_text)
        self.assertIn("semantic_repair_required", skill_text)

    def test_sme_core_review_template_tracks_omissions_without_full_flow_sections(self) -> None:
        template_text = SME_CORE_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("Core Completeness Ledger", template_text)
        self.assertIn("Calculation Logic", template_text)
        self.assertIn("Validation Logic", template_text)
        self.assertIn("Exception Handling", template_text)
        self.assertIn("Message Inventory", template_text)
        self.assertIn("No program may be omitted", template_text)
        normalized = " ".join(template_text.split())
        self.assertIn("self-contained SME reading surfaces", normalized)
        self.assertIn("traceability only", normalized)
        self.assertIn("Source Fact Refs", template_text)
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
        self.assertIn("delivery_workspace_profile", guide_text)
        self.assertIn("develop-{PERSON}", guide_text)
        self.assertIn("write_to_main: false", guide_text)

    def test_delivery_profile_template_supports_team_onboarding(self) -> None:
        profile_text = DELIVERY_PROFILE_TEMPLATE.read_text(encoding="utf-8")
        quickstart_text = DELIVERY_PROFILE_QUICKSTART.read_text(encoding="utf-8")

        for text in (profile_text, quickstart_text):
            self.assertIn("program_artifact_resolution_profile", text)
            self.assertIn("delivery_workspace_profile", text)
            self.assertIn("program_folder_patterns", text)
            self.assertIn("modules/*/{PROGRAM}", text)
            self.assertIn("use_or_create_provided", text)
            self.assertIn("develop-{PERSON}", text)
            self.assertIn("develop-*", text)
            self.assertIn("origin/main", text)
            self.assertIn("write_to_main: false", text)
            self.assertIn("program_set_review_parent", text)
            self.assertIn("program_tier_roots", text)
            self.assertIn("large_extreme_program", text)
            self.assertIn("complex_normal_program", text)
            self.assertIn("normal_program", text)

        self.assertIn("analyzed_this_run: read_from_working_root", profile_text)
        self.assertIn("reused_same_run: read_same_run_artifact", profile_text)
        self.assertIn("pending_source: scan_source_then_write_to_working_branch", profile_text)
        self.assertIn("blocked_missing_source: record_blocker_tbd", profile_text)
        self.assertNotIn("found_on_remote_main: read_from_remote_main_checkout", profile_text)
        self.assertNotIn("not_found_on_remote_main: scan_source_then_write_to_working_branch", profile_text)


if __name__ == "__main__":
    unittest.main()
