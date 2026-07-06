from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SCRIPT_PATH = (
    REPO_ROOT
    / "skills"
    / "legacy-ibmi-program-analyzer"
    / "scripts"
    / "index_rpg_source.py"
)
WRAPPER_SCRIPT_PATH = REPO_ROOT / "scripts" / "index-rpg-source.py"


def load_indexer():
    spec = importlib.util.spec_from_file_location("index_rpg_source", CANONICAL_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load indexer: {CANONICAL_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SAMPLE_RPG = """H DFTACTGRP(*NO)
FCUSTPF    UF   E           K DISK
FAUTHLOG   O    E             DISK
DCL-F MSGDSPF WORKSTN;
C                   EXSR      SR100
C                   CALL      'AUTHREQ'
C                   SETON                                        LR
C     SR100         BEGSR
C     CUSTID        CHAIN     CUSTPF
C                   IF        %FOUND(CUSTPF)
C                   EVAL      AUTHSTS = 'P'
C                   UPDATE    CUSTREC
C                   ENDIF
C                   ENDSR
DCL-PROC SR200;
  SNDPGMMSG MSGID(UCC1852);
END-PROC;
"""


class RpgSourceIndexerTests(unittest.TestCase):
    def test_large_program_guidance_documents_windows_python_launcher(self) -> None:
        skill_text = (
            REPO_ROOT / "skills" / "legacy-ibmi-program-analyzer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        large_program_text = (
            REPO_ROOT
            / "skills"
            / "legacy-ibmi-program-analyzer"
            / "references"
            / "large-program-analysis.md"
        ).read_text(encoding="utf-8")
        output_contract_text = (
            REPO_ROOT
            / "skills"
            / "legacy-ibmi-program-analyzer"
            / "references"
            / "output-contract.md"
        ).read_text(encoding="utf-8")

        for text in (skill_text, large_program_text, output_contract_text):
            self.assertIn("py -3", text)
            self.assertIn("scripts\\index-rpg-source.py", text)
            self.assertIn("python3 scripts/index-rpg-source.py", text)
            self.assertIn("validate-program-analysis-contract.py", text)
            self.assertIn("program-analysis-summary.yaml", text)
            self.assertIn("program-analysis.md", text)
            self.assertIn("routine-logic-details.md", text)
            self.assertIn("routine-logic-details.yaml", text)
            self.assertIn("routine-logic-details/deep-read-batch-001.md", text)
            self.assertIn("temporary consistency checks", text)
            self.assertIn("YAML", text)
            self.assertIn("readability checks", text)
            self.assertIn("file-io-inventory.md", text)
            self.assertIn("file-io-inventory.yaml", text)
            self.assertIn("field-mutation-matrix.md", text)
            self.assertIn("field-mutation-matrix.yaml", text)
            self.assertIn("sql-inventory.md", text)
            self.assertIn("sql-inventory.yaml", text)
            self.assertIn("normal_program", text)
            self.assertIn("complex_normal_program", text)
            self.assertIn("large_extreme_program", text)
            self.assertIn("optional", text)

    def test_analyze_source_extracts_structure_without_business_summary(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            SAMPLE_RPG.splitlines(),
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        self.assertEqual(source_index["program"], "CU106")
        self.assertEqual(source_index["source"]["line_count"], 17)
        self.assertIn("SR100", {routine["name"] for routine in source_index["routines"]})
        self.assertIn("SR200", {routine["name"] for routine in source_index["routines"]})
        self.assertIn("AUTHREQ", {call["target"] for call in source_index["external_calls"]})
        self.assertIn("CUSTPF", {operation["object"] for operation in source_index["file_operations"]})
        self.assertIn("UCC1852", {message["code"] for message in source_index["messages"]})
        self.assertEqual(source_index["counts"]["unique_messages"], 1)
        self.assertEqual(
            source_index["message_inventory"]["summary"][0]["short_description"],
            "unresolved - message description not available",
        )
        self.assertEqual(source_index["routine_logic_inventory"]["summary"][0]["routine"], "MAIN")
        self.assertEqual(source_index["routine_logic_inventory"]["summary"][0]["detail_ref"], "RLOG-CU106-001")
        self.assertEqual(
            source_index["routine_logic_inventory"]["summary"][0]["semantic_status"],
            "pending_deep_read",
        )
        self.assertEqual(source_index["program_size_tier"], "normal_program")
        self.assertEqual(source_index["default_output_profile"], "reader_first_lightweight_review")
        self.assertIn("optional_sidecar_triggers", source_index)

        sr100 = next(routine for routine in source_index["routines"] if routine["name"] == "SR100")
        self.assertEqual(sr100["coverage"], "indexed_only")
        self.assertTrue(sr100["recommended_deep_read"])
        self.assertIn("state-changing file operation", sr100["deep_read_reasons"])

    def test_cli_keeps_simple_normal_program_reader_first_without_extra_sidecars(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
C                   SETON                                        LR
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "SIMPLE.RPGLE"
            output_dir = temp_path / "out"
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "SIMPLE",
                    "--out-dir",
                    str(output_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("source-index.yaml", result.stdout)
            expected_present = {
                "program-analysis.md",
                "source-index.yaml",
                "program-analysis-summary.yaml",
                "routine-index.md",
                "routine-logic-details.md",
                "routine-logic-details.yaml",
                "message-inventory.yaml",
            }
            expected_absent = {
                "all-routine-coverage-ledger.md",
                "deep-read-plan.md",
                "message-inventory.md",
                "file-io-inventory.md",
                "file-io-inventory.yaml",
                "field-mutation-matrix.md",
                "field-mutation-matrix.yaml",
                "sql-inventory.md",
                "sql-inventory.yaml",
            }
            for artifact in expected_present:
                self.assertTrue((output_dir / artifact).exists(), artifact)
            for artifact in expected_absent:
                self.assertFalse((output_dir / artifact).exists(), artifact)
            self.assertFalse((output_dir / "routine-logic-details").exists())

            source_index = (output_dir / "source-index.yaml").read_text(encoding="utf-8")
            summary = (output_dir / "program-analysis-summary.yaml").read_text(encoding="utf-8")
            program_analysis = (output_dir / "program-analysis.md").read_text(encoding="utf-8")
            self.assertIn("program_size_tier: normal_program", source_index)
            self.assertIn("default_output_profile: reader_first_lightweight_review", summary)
            self.assertIn("program_analysis:", summary)
            self.assertIn("routine_logic_details:", summary)
            self.assertIn("routine_logic_details_yaml:", summary)
            self.assertIn("status: present", summary)
            self.assertIn("validate-program-analysis-contract.py", summary)
            self.assertIn("## Program Reading Summary", program_analysis)
            self.assertIn("## Calculation Logic", program_analysis)
            self.assertIn("### Routine Index For Calculation Logic", program_analysis)
            self.assertIn("## Routine Logic Details", program_analysis)
            self.assertIn("RLOG-SIMPLE-001", program_analysis)
            self.assertIn("## Review Checklist", program_analysis)

    def test_cli_reuses_central_artifact_before_source_scan(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "CU257F.RPGLE"
            output_dir = temp_path / "out"
            delivery_root = temp_path / "delivery-main"
            artifact_root = delivery_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            artifact_root.mkdir(parents=True)
            (artifact_root / "program-analysis-summary.yaml").write_text(
                "schema_version: '0.1'\nprogram: CU257F\n",
                encoding="utf-8",
            )
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU257F",
                    "--out-dir",
                    str(output_dir),
                    "--delivery-root",
                    str(delivery_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("central_lookup_result: found_on_remote_main", result.stdout)
            self.assertIn("artifact_root: modules/CAP-ID-0002-complex_normal_program/CU257F", result.stdout)
            self.assertIn("action: reuse_existing_program_artifacts", result.stdout)
            self.assertFalse((output_dir / "source-index.yaml").exists())
            self.assertFalse((output_dir / "program-analysis.md").exists())

    def test_cli_force_rescan_writes_artifacts_with_central_reuse_trace(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "CU257F.RPGLE"
            output_dir = temp_path / "out"
            delivery_root = temp_path / "delivery-main"
            artifact_root = delivery_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F"
            artifact_root.mkdir(parents=True)
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU257F",
                    "--out-dir",
                    str(output_dir),
                    "--delivery-root",
                    str(delivery_root),
                    "--force-rescan",
                    "--rescan-reason",
                    "SME requested refresh after major source change",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("central_lookup_result: found_on_remote_main", result.stdout)
            self.assertIn("action: force_rescan_requested", result.stdout)
            self.assertTrue((output_dir / "source-index.yaml").exists())
            self.assertTrue((output_dir / "program-analysis-summary.yaml").exists())
            source_index = (output_dir / "source-index.yaml").read_text(encoding="utf-8")
            summary = (output_dir / "program-analysis-summary.yaml").read_text(encoding="utf-8")
            self.assertIn("central_artifact_reuse:", source_index)
            self.assertIn("reuse_decision: force_rescan_requested", source_index)
            self.assertIn("artifact_root: modules/CAP-ID-0002-complex_normal_program/CU257F", source_index)
            self.assertIn('rescan_reason: "SME requested refresh after major source change"', summary)

    def test_cli_force_rescan_requires_reason(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "CU257F.RPGLE"
            output_dir = temp_path / "out"
            delivery_root = temp_path / "delivery-main"
            (delivery_root / "modules" / "CAP-ID-0002-complex_normal_program" / "CU257F").mkdir(parents=True)
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU257F",
                    "--out-dir",
                    str(output_dir),
                    "--delivery-root",
                    str(delivery_root),
                    "--force-rescan",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 4)
            self.assertIn("rescan_reason_required", result.stderr)
            self.assertFalse((output_dir / "source-index.yaml").exists())

    def test_cli_continues_source_scan_when_central_artifact_missing(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "CU999.RPGLE"
            output_dir = temp_path / "out"
            delivery_root = temp_path / "delivery-main"
            (delivery_root / "modules").mkdir(parents=True)
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU999",
                    "--out-dir",
                    str(output_dir),
                    "--delivery-root",
                    str(delivery_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("central_lookup_result: not_found_on_remote_main", result.stdout)
            self.assertIn("action: proceed_to_source_scan", result.stdout)
            self.assertTrue((output_dir / "source-index.yaml").exists())
            self.assertTrue((output_dir / "program-analysis.md").exists())

    def test_cli_keeps_at_prefixed_programs_distinct_in_central_lookup(self) -> None:
        source = """H DFTACTGRP(*NO)
C                   EVAL      RESULT = 'Y'
"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "CU118.RPGLE"
            output_dir = temp_path / "out"
            delivery_root = temp_path / "delivery-main"
            prefixed_root = delivery_root / "modules" / "CAP-ID-0001-large_extreme_program" / "@CU118"
            prefixed_root.mkdir(parents=True)
            source_path.write_text(source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(CANONICAL_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU118",
                    "--out-dir",
                    str(output_dir),
                    "--delivery-root",
                    str(delivery_root),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("central_lookup_result: not_found_on_remote_main", result.stdout)
            self.assertIn("action: proceed_to_source_scan", result.stdout)
            self.assertTrue((output_dir / "source-index.yaml").exists())

    def test_fixed_format_begsr_uses_factor_before_opcode_with_source_prefix(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "LMH1 C                   EXSR      SR960",
                "LMH1 C****************************************************************",
                "LMH1 C     SR960         BEGSR",
                "LMH1 C* Field 44 Additional response data",
                "LMH1 C                   Z-ADD     9             WFARDL",
                "LMH1 C                   MOVE      GHO034733      W1CVVI",
                "LMH1 C     SR960E        ENDSR",
            ],
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        routine_names = {routine["name"] for routine in source_index["routines"]}
        self.assertIn("SR960", routine_names)
        self.assertNotIn("GHO034733", routine_names)
        sr960 = next(routine for routine in source_index["routines"] if routine["name"] == "SR960")
        self.assertEqual(sr960["start_line"], 3)
        self.assertEqual(sr960["end_line"], 7)
        self.assertIn("MAIN line 1", sr960["called_by"])

    def test_fixed_format_begsr_ignores_trailing_member_identifier(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "CSY C                   EXSR      SR931",
                "CSY C**************************************************************** GHO003380",
                "CSY C     SR931         BEGSR                          GHO003380",
                "CSY C* Format program parameters                         GHO003380",
                "CSY C                   CLEAR                   WS122D   GHO003380",
                "CSY C                   MOVE      WAHCCM        WNHCCM   GHO003380",
                "CSY C     SR931E        ENDSR                          GHO003380",
            ],
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        routine_names = {routine["name"] for routine in source_index["routines"]}
        self.assertIn("SR931", routine_names)
        self.assertNotIn("GHO003380", routine_names)
        sr931 = next(routine for routine in source_index["routines"] if routine["name"] == "SR931")
        self.assertEqual(sr931["start_line"], 3)
        self.assertEqual(sr931["end_line"], 7)
        self.assertIn("MAIN line 1", sr931["called_by"])

    def test_fixed_format_begsr_accepts_change_tag_joined_to_spec(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "WKS02C                  EXSR      SR170",
                "26191C                  EXSR      SR620",
                "WKS02C* This comment mentions CALL UPDATE COMMIT SR999 BEGSR",
                "WKS02C    SR170         BEGSR",
                "WKS02C                  MOVE      *BLANK        W1ARDT",
                "WKS02C    SR170E        ENDSR",
                "26191C    SR620         BEGSR",
                "26191C                  Z-ADD     1             WCOUNT",
                "26191C    SR620E        ENDSR",
            ],
            program_name="CU101A",
            source_path=Path("fixtures/CU101A.rpgle"),
        )

        routine_names = {routine["name"] for routine in source_index["routines"]}
        self.assertIn("SR170", routine_names)
        self.assertIn("SR620", routine_names)
        self.assertNotIn("WKS02C", routine_names)
        self.assertNotIn("26191C", routine_names)
        self.assertNotIn("SR999", routine_names)
        sr170 = next(routine for routine in source_index["routines"] if routine["name"] == "SR170")
        sr620 = next(routine for routine in source_index["routines"] if routine["name"] == "SR620")
        self.assertEqual(sr170["start_line"], 4)
        self.assertEqual(sr170["end_line"], 6)
        self.assertEqual(sr620["start_line"], 7)
        self.assertEqual(sr620["end_line"], 9)
        self.assertIn("MAIN line 1", sr170["called_by"])
        self.assertIn("MAIN line 2", sr620["called_by"])

    def test_fixed_format_c_spec_with_f_prefix_is_not_false_f_spec(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "FN01 C                  EXSR      SRA00",
                "FN01 C                  EXSR      SR100",
                "FN01 C* Comment mentions WRITE NEWREC and CALL TRIAD",
                "FN01 C    SRA00         BEGSR",
                "FN01 C                  MOVE      'A'           WSTATUS",
                "FN01 C    SRA00E        ENDSR",
                "FN01 C    SR100         BEGSR",
                "FN01 C                  MOVE      'B'           WSTATUS",
                "FN01 C    SR100E        ENDSR",
            ],
            program_name="CU101A",
            source_path=Path("fixtures/CU101A.rpgle"),
        )

        self.assertNotIn("N01", source_index["declared_files"])
        routine_names = {routine["name"] for routine in source_index["routines"]}
        self.assertIn("SRA00", routine_names)
        self.assertIn("SR100", routine_names)
        self.assertNotIn("TRIAD", {call["target"] for call in source_index["calls"]})
        sra00 = next(routine for routine in source_index["routines"] if routine["name"] == "SRA00")
        self.assertIn("MAIN line 1", sra00["called_by"])

    def test_fixed_format_routine_boundaries_require_non_comment_sr_factor(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "CSY C                   EXSR      SR931",
                "CSY C     SR931         BEGSR                          GHO003380",
                "CSY C* This comment says ENDSR but is not executable     GHO003380",
                "CSY C     GHO003380      ENDSR                          GHO003380",
                "CSY C**VC1              Z-ADD     W3CDEX        WNCDEX   GHO003380",
                "CSY C                   MOVE      WAHCCM        WNHCCM   GHO003380",
                "CSY C     SR931E        ENDSR                          GHO003380",
            ],
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        routine_names = {routine["name"] for routine in source_index["routines"]}
        self.assertIn("SR931", routine_names)
        self.assertNotIn("GHO003380", routine_names)
        sr931 = next(routine for routine in source_index["routines"] if routine["name"] == "SR931")
        self.assertEqual(sr931["start_line"], 2)
        self.assertEqual(sr931["end_line"], 7)

    def test_deep_read_reasons_include_rpg_branch_and_outcome_signals(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "C                   EXSR      SR300",
                "C                   EXSR      SR400",
                "C                   EXSR      SR500",
                "C                   EXSR      SR600",
                "C     SR300         BEGSR",
                "C     CUSTID        CHAIN     CUSTPF",
                "C                   IF        %FOUND(CUSTPF)",
                "C                   ENDIF",
                "C     SR300E        ENDSR",
                "C     SR400         BEGSR",
                "C                   EXFMT     AUTHDSP",
                "C     SR400E        ENDSR",
                "C     SR500         BEGSR",
                "C                   MOVE      'D'           AUTHSTS",
                "C     SR500E        ENDSR",
                "C     SR600         BEGSR",
                "C                   MONITOR",
                "C                   ON-ERROR",
                "C     SR600E        ENDSR",
            ],
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        routines = {routine["name"]: routine for routine in source_index["routines"]}
        self.assertIn("mainline dispatch target", routines["SR300"]["deep_read_reasons"])
        self.assertIn("read-conditioned branch", routines["SR300"]["deep_read_reasons"])
        self.assertIn("screen/report boundary", routines["SR400"]["deep_read_reasons"])
        self.assertIn("outcome/status carrier assignment", routines["SR500"]["deep_read_reasons"])
        self.assertIn("message/status handling", routines["SR600"]["deep_read_reasons"])

    def test_message_inventory_groups_repeated_codes_for_sidecar_detail(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "C                   SNDPGMMSG MSGID(UCC1852)",
                "C                   EXSR      SR100",
                "C     SR100         BEGSR",
                "C                   SNDPGMMSG MSGID(UCC1852)",
                "C                   SNDPGMMSG MSGID(CPF9898)",
                "C     SR100E        ENDSR",
            ],
            program_name="CU106",
            source_path=Path("fixtures/CU106.rpgle"),
        )

        summary = source_index["message_inventory"]["summary"]
        by_message = {item["message"]: item for item in summary}
        self.assertEqual(len(summary), 2)
        self.assertEqual(by_message["UCC1852"]["occurrence_count"], 2)
        self.assertEqual(by_message["UCC1852"]["detail_ref"], "MSG-CU106-001")
        self.assertEqual(by_message["CPF9898"]["detail_ref"], "MSG-CU106-002")

    def test_sqlrpgle_free_format_profile_sql_and_assignment_indexing(self) -> None:
        indexer = load_indexer()

        source_index = indexer.analyze_source(
            [
                "**free",
                "ctl-opt dftactgrp(*no);",
                "dcl-pi *n;",
                "  request likeds(RequestDs) const;",
                "  response likeds(ResponseDs);",
                "end-pi;",
                "dcl-proc HandleRequest;",
                "  exec sql",
                "    select status, balance",
                "      into :CustStatus, :Balance",
                "      from CUSTMAST",
                "      where CUSTNO = :Request.CustNo;",
                "  if SQLCODE <> 0;",
                "     Response.Code = 'NF';",
                "     Response.Message = 'Customer not found';",
                "     return;",
                "  endif;",
                "  ApprovedAmt = Balance - Request.Amount;",
                "  exec sql",
                "     update CUSTMAST",
                "        set LAST_AUTH_AMT = :ApprovedAmt",
                "      where CUSTNO = :Request.CustNo;",
                "  if SQLSTATE <> '00000';",
                "     Response.Code = 'ER';",
                "  else;",
                "     BuildResponse(Request: Response);",
                "  endif;",
                "end-proc;",
            ],
            program_name="APIORD",
            source_path=Path("fixtures/APIORD.SQLRPGLE"),
        )

        self.assertEqual(source_index["program_profile"]["program_type"], "SQLRPGLE")
        self.assertEqual(source_index["program_profile"]["syntax_mode"], "free_format")
        self.assertIn(
            source_index["program_profile"]["interface_profile"],
            {"api_remote", "callable_program"},
        )
        self.assertEqual(source_index["counts"]["sql_statements"], 2)
        self.assertGreaterEqual(source_index["counts"]["free_format_assignments"], 3)

        sql_details = source_index["sql_inventory"]["details"]
        self.assertEqual({detail["statement_type"] for detail in sql_details}, {"SELECT", "UPDATE"})
        self.assertIn("CUSTMAST", {detail["table_or_view"] for detail in sql_details})
        host_variables = {
            host_var
            for detail in sql_details
            for host_var in detail["host_variables"]
        }
        self.assertIn(":CUSTSTATUS", host_variables)
        self.assertIn(":APPROVEDAMT", host_variables)

        assignment_targets = {assignment["target"] for assignment in source_index["assignments"]}
        self.assertIn("RESPONSE.CODE", assignment_targets)
        self.assertIn("APPROVEDAMT", assignment_targets)

        by_message = {
            item["message"]: item
            for item in source_index["message_inventory"]["summary"]
        }
        self.assertIn("SQLCODE", by_message)
        self.assertIn("SQLSTATE", by_message)

        routine = next(r for r in source_index["routines"] if r["name"] == "HANDLEREQUEST")
        self.assertIn("sql data access", routine["deep_read_reasons"])
        self.assertIn("outcome/status carrier assignment", routine["deep_read_reasons"])

        mutation_summary = source_index["field_mutation_inventory"]["summary"]
        self.assertIn("CUSTMAST", {item["object"] for item in mutation_summary})

    def test_cli_writes_large_program_artifacts(self) -> None:
        large_source = SAMPLE_RPG + "\n".join("* filler" for _ in range(10000))

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_path = tmp_path / "CU106.rpgle"
            output_dir = tmp_path / "analysis"
            source_path.write_text(large_source, encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER_SCRIPT_PATH),
                    str(source_path),
                    "--program",
                    "CU106",
                    "--out-dir",
                    str(output_dir),
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            for name in (
                "source-index.yaml",
                "program-analysis.md",
                "program-analysis-summary.yaml",
                "routine-index.md",
                "all-routine-coverage-ledger.md",
                "deep-read-plan.md",
                "routine-logic-details.md",
                "routine-logic-details.yaml",
                "message-inventory.md",
                "message-inventory.yaml",
                "file-io-inventory.md",
                "file-io-inventory.yaml",
                "field-mutation-matrix.md",
                "field-mutation-matrix.yaml",
                "sql-inventory.md",
                "sql-inventory.yaml",
                "routine-logic-details/deep-read-batch-001.md",
            ):
                self.assertTrue((output_dir / name).exists(), name)

            source_index = (output_dir / "source-index.yaml").read_text(encoding="utf-8")
            self.assertIn("analysis_mode: large_program", source_index)
            self.assertIn("program: CU106", source_index)

            deep_read_plan = (output_dir / "deep-read-plan.md").read_text(encoding="utf-8")
            self.assertIn("| SR100 |", deep_read_plan)
            self.assertIn("state-changing file operation", deep_read_plan)

            routine_logic = (output_dir / "routine-logic-details.md").read_text(encoding="utf-8")
            self.assertIn("RLOG-CU106-001", routine_logic)
            self.assertIn("pending_deep_read", routine_logic)
            self.assertIn("Calculation Logic", routine_logic)
            self.assertIn("Exception Handling", routine_logic)
            self.assertIn("Batch Coverage Summary", routine_logic)
            self.assertIn("pasted source-code snippets", routine_logic)
            self.assertIn("must list every exact message/status/literal", routine_logic)
            self.assertIn("reader-first `program-analysis.md`", routine_logic)
            self.assertIn("consolidated `routine-logic-details.md` audit document", routine_logic)
            self.assertIn("reader-useful detail for every YAML RLOG", routine_logic)

            program_analysis = (output_dir / "program-analysis.md").read_text(encoding="utf-8")
            self.assertIn("Draft wrapper seed generated", program_analysis)
            self.assertIn("## Calculation Logic", program_analysis)
            self.assertIn("## Metadata", program_analysis)
            self.assertIn("## Review Checklist", program_analysis)

            routine_logic_yaml = (output_dir / "routine-logic-details.yaml").read_text(encoding="utf-8")
            self.assertIn("routine_logic_inventory:", routine_logic_yaml)
            self.assertIn("semantic_status: pending_deep_read", routine_logic_yaml)
            self.assertIn("part_file_front_matter:", routine_logic_yaml)
            self.assertIn("Batch Coverage Summary", routine_logic_yaml)
            self.assertIn("Core logic must not contain", routine_logic_yaml)
            self.assertIn("final_consolidation_required:", routine_logic_yaml)
            self.assertIn("Batch files are retained audit surfaces", routine_logic_yaml)

            program_summary = (output_dir / "program-analysis-summary.yaml").read_text(encoding="utf-8")
            self.assertIn("routine_summary:", program_summary)
            self.assertIn("message_summary:", program_summary)
            self.assertIn("routine_logic_deep_read_batch_001:", program_summary)
            self.assertIn("routine-logic-details/deep-read-batch-001.md", program_summary)

            batch = (output_dir / "routine-logic-details" / "deep-read-batch-001.md").read_text(encoding="utf-8")
            self.assertIn("# Routine Logic Details: CU106 - Deep Read Batch 001", batch)
            self.assertIn("## Calculation Logic", batch)
            self.assertIn("## Validation Logic", batch)
            self.assertIn("## Exception Handling", batch)
            self.assertIn("## Scope", batch)
            self.assertIn("## Batch Coverage Summary", batch)
            self.assertIn("## Message Inventory", batch)
            self.assertIn("## Routine Details", batch)
            self.assertIn("RLOG-CU106-001", batch)

            message_inventory = (output_dir / "message-inventory.md").read_text(encoding="utf-8")
            self.assertIn("MSG-CU106-001", message_inventory)
            self.assertIn("UCC1852", message_inventory)
            self.assertIn("unresolved - message description not available", message_inventory)

            message_inventory_yaml = (output_dir / "message-inventory.yaml").read_text(encoding="utf-8")
            self.assertIn("message_inventory:", message_inventory_yaml)
            self.assertIn("message: UCC1852", message_inventory_yaml)

            file_io_inventory_yaml = (output_dir / "file-io-inventory.yaml").read_text(encoding="utf-8")
            self.assertIn("file_io_inventory:", file_io_inventory_yaml)
            self.assertIn("object: CUSTPF", file_io_inventory_yaml)

            mutation_yaml = (output_dir / "field-mutation-matrix.yaml").read_text(encoding="utf-8")
            self.assertIn("field_mutation_inventory:", mutation_yaml)
            self.assertIn("operation: UPDATE", mutation_yaml)

            sql_inventory_yaml = (output_dir / "sql-inventory.yaml").read_text(encoding="utf-8")
            self.assertIn("sql_inventory:", sql_inventory_yaml)


if __name__ == "__main__":
    unittest.main()
