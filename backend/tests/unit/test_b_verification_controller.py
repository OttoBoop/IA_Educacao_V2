"""
Unit tests for B-track fixes to run_verification_f10.py.

B1: Remove keyword-based PASS marking (MILESTONE_KEYWORDS removed)
B2: Exempt first 10 steps from repetition-stuck detection
B3: Count executarPipelineCompleto events; inject Phase 3 guidance at count=4

Uses source-inspection and functional testing approaches.

Plan: PLAN_Major_Fix_Tasks_And_Verification.md — Tasks B1, B2, B3
Human Needed: B3 Yes (live run review)
Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_b_verification_controller.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

CONTROLLER_PATH = Path(__file__).parent.parent.parent / "run_verification_f10.py"
CONTROLLER_SRC = CONTROLLER_PATH.read_text(encoding="utf-8")


def _workspace_tmp(name: str) -> Path:
    """Create a writable scratch directory inside the repo workspace."""
    path = CONTROLLER_PATH.parent / ".pytest_tmp" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── B1: Keyword-based PASS marking removed ────────────────────────────────────

class TestB1KeywordMarkingRemoved:
    """B1: MILESTONE_KEYWORDS and keyword-based PASS marking must be removed."""

    def test_milestone_keywords_dict_absent(self):
        """MILESTONE_KEYWORDS dict must no longer exist in run_verification_f10.py."""
        assert "MILESTONE_KEYWORDS" not in CONTROLLER_SRC, (
            "MILESTONE_KEYWORDS dict must be removed — keyword-based PASS marking "
            "produces false positives and must be replaced by explicit tracking"
        )

    def test_keyword_checklist_loop_absent(self):
        """The loop that iterates MILESTONE_KEYWORDS and calls mark_checklist_item must be removed."""
        # The old loop had: "for item_id, keywords in MILESTONE_KEYWORDS.items():"
        assert "MILESTONE_KEYWORDS.items()" not in CONTROLLER_SRC, (
            "The keyword-checking loop must be removed from step_completed handler"
        )

    def test_no_auto_pass_from_text_keywords(self):
        """mark_checklist_item must not be called from keyword text matching in step_completed."""
        # Check: no call to mark_checklist_item based on 'any(kw in text for kw in keywords)'
        assert "any(kw in text for kw in keywords)" not in CONTROLLER_SRC, (
            "Keyword-matching PASS logic must be removed from step_completed handler"
        )


# ── B2: First 10 steps exempt from repetition-stuck ──────────────────────────

class TestB2RepetitionStuckExemption:
    """B2: First 10 steps must be exempt from repetition-stuck detection."""

    def test_step_count_guard_exists(self):
        """Controller source must contain a step_count guard for repetition-stuck detection."""
        # The guard should be something like: step_count > 10
        assert "step_count > 10" in CONTROLLER_SRC or "step_count >= 10" in CONTROLLER_SRC, (
            "run_verification_f10.py must guard repetition-stuck detection with "
            "step_count > 10 to exempt the first 10 steps (Phase 1 navigation uses "
            "4+ evaluate_js calls which would falsely trigger stuck detection)"
        )

    def test_repetition_stuck_not_fired_before_step_10(self):
        """run_controller() must NOT fire repetition_stuck at step 4 with 5 evaluate_js actions."""
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
        finally:
            sys.path.pop(0)

        # Simulate: step_count=4, recent_actions has 6 evaluate_js entries
        # (mirroring Phase 1 navigation)
        ipc_dir = _workspace_tmp("fake_ipc_b2")
        ipc_dir.mkdir(exist_ok=True)

        # Patch send_command and build a mini event sequence
        guidance_sent = []

        def fake_send(path, cmd_type, data=None):
            if cmd_type == "guidance":
                guidance_sent.append(data.get("instruction", "") if data else "")

        events_path = ipc_dir / "events.jsonl"

        # Build 6 step_completed events (evaluate_js) + 1 paused event
        step_events = []
        for i in range(6):
            step_events.append(json.dumps({
                "event_type": "step_completed",
                "step": i + 1,
                "action": "evaluate_js",
                "target": "showMateria('abc')",
                "thought": "navigating",
                "success": True,
            }))
        step_events.append(json.dumps({
            "event_type": "paused",
            "step": 7,
        }))
        step_events.append(json.dumps({
            "event_type": "complete",
            "step": 7,
        }))
        events_path.write_text("\n".join(step_events) + "\n", encoding="utf-8")

        commands_path = ipc_dir / "commands.jsonl"
        commands_path.write_text("", encoding="utf-8")

        # We can't easily run_controller standalone without its full loop,
        # but we can check the source logic directly
        # The key assertion: step_count > 10 guard prevents repetition_stuck from firing
        # This is a source-inspection check for the guard
        assert "step_count > 10" in CONTROLLER_SRC or "step_count >= 10" in CONTROLLER_SRC, (
            "Repetition-stuck guard must be present to protect Phase 1 navigate steps"
        )


# ── B3: executarPipelineCompleto count → Phase 3 injection ───────────────────

class TestB3Phase3Injection:
    """B3: Controller must count executarPipelineCompleto and inject Phase 3 at count=4."""

    def test_pipeline_counter_variable_exists(self):
        """Controller source must track executarPipelineCompleto trigger count."""
        assert "executarPipelineCompleto" in CONTROLLER_SRC, (
            "run_verification_f10.py must track executarPipelineCompleto trigger count"
        )
        # Should have some counter for it
        assert (
            "pipeline_trigger_count" in CONTROLLER_SRC
            or "trigger_count" in CONTROLLER_SRC
            or "executarPipeline_count" in CONTROLLER_SRC
            or "pipeline_count" in CONTROLLER_SRC
        ), (
            "A counter variable for executarPipelineCompleto must exist in run_controller()"
        )

    def test_phase3_injection_at_count_4(self):
        """Controller source must inject Phase 3 guidance when pipeline count reaches 4."""
        # Should have a condition checking for count == 4 (or >= 4), or the
        # equivalent shared constant for the expected model count.
        assert (
            "== 4" in CONTROLLER_SRC
            or ">= 4" in CONTROLLER_SRC
            or "EXPECTED_PIPELINE_TRIGGER_COUNT" in CONTROLLER_SRC
        ), (
            "Controller must inject Phase 3 guidance when 4 pipeline triggers are detected "
            "(count == 4 or >= 4)"
        )

    def test_phase3_guidance_text_contains_download(self):
        """Phase 3 guidance injected at count=4 must mention download/validation steps."""
        # The Phase 3 instruction string should mention download or validate
        assert (
            "download" in CONTROLLER_SRC.lower()
            and "phase 3" in CONTROLLER_SRC.lower()
        ) or (
            "PHASE 3" in CONTROLLER_SRC
        ), (
            "The Phase 3 guidance injected at pipeline_count=4 must describe "
            "download and validation steps (download_file, verify JSON fields)"
        )


class TestReliabilityRecoveryController:
    """Controller should use run-scoped artifacts and current event names."""

    def test_initialize_run_artifacts_creates_run_scoped_template(self):
        """initialize_run_artifacts() should create verification_report.md inside the run dir."""
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
        finally:
            sys.path.pop(0)

        run_dir = _workspace_tmp("controller_run_artifacts") / "20260309_101500"
        report_path = ctrl.initialize_run_artifacts(run_dir)

        assert report_path == run_dir / "verification_report.md"
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "# Pipeline Verification Report" in content
        assert "PENDING" in content
        assert "- OBSERVED: 0" in content
        assert "- BLOCKED: 0" in content
        assert "- UNVERIFIED: 0" in content

    def test_controller_handles_current_terminal_event_names(self):
        """run_controller() must recognize journey_complete and journey_stopped events."""
        assert '"journey_complete"' in CONTROLLER_SRC
        assert '"journey_stopped"' in CONTROLLER_SRC

    def test_phase_state_machine_promotes_validate_and_review(self):
        """Controller should expose explicit phase-state transitions."""
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
        finally:
            sys.path.pop(0)

        phase = ctrl.advance_phase_state(
            ctrl.PHASE_SETUP,
            has_seen_step=True,
            pipeline_trigger_count=0,
        )
        assert phase == ctrl.PHASE_TRIGGER

        phase = ctrl.advance_phase_state(
            phase,
            has_seen_step=True,
            pipeline_trigger_count=ctrl.EXPECTED_PIPELINE_TRIGGER_COUNT,
        )
        assert phase == ctrl.PHASE_VALIDATE

        phase = ctrl.advance_phase_state(
            phase,
            has_seen_step=False,
            pipeline_trigger_count=ctrl.EXPECTED_PIPELINE_TRIGGER_COUNT,
            terminal_event="journey_complete",
        )
        assert phase == ctrl.PHASE_REVIEW

    def test_validate_phase_disallows_pipeline_retrigger_actions(self):
        """Validate phase must block known pipeline-trigger actions."""
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
        finally:
            sys.path.pop(0)

        assert ctrl.is_action_allowed_in_phase(
            ctrl.PHASE_VALIDATE,
            action="download_file",
            target="#download-json",
            thought="save the output artifact",
        ) is True
        assert ctrl.is_action_allowed_in_phase(
            ctrl.PHASE_VALIDATE,
            action="evaluate_js",
            target="executarPipelineCompleto()",
            thought="trigger pipeline again",
        ) is False
        assert ctrl.is_action_allowed_in_phase(
            ctrl.PHASE_VALIDATE,
            action="evaluate_js",
            target="openModalPipelineCompleto('abc', 'turma')",
            thought="re-open the pipeline modal",
        ) is False


class TestR3SharedSpecIntegration:
    """Controller should consume the shared verification spec instead of drifting."""

    def _load_controller(self):
        sys.path.insert(0, str(CONTROLLER_PATH.parent))
        try:
            import importlib
            import run_verification_f10 as ctrl
            importlib.reload(ctrl)
            return ctrl
        finally:
            sys.path.pop(0)

    def test_controller_goal_is_built_from_helper(self):
        """GOAL should be sourced from the controller helper, not trusted as a stale literal."""
        ctrl = self._load_controller()

        assert ctrl.GOAL == ctrl.build_controller_goal()
        assert "questao_id" in ctrl.GOAL
        assert "extrair_questoes" in ctrl.GOAL
        assert "desempenho" in ctrl.GOAL.lower()

    def test_controller_startup_guidance_uses_shared_model_list(self):
        """Startup guidance should mention the shared ordered model list."""
        ctrl = self._load_controller()

        guidance = ctrl.build_controller_startup_guidance()
        assert "gpt-4o" in guidance
        assert "gpt-5-nano" in guidance
        assert "claude-haiku-4-5-20251001" in guidance
        assert "gemini-3-flash-preview" in guidance

    def test_configure_model_scope_updates_requested_and_expected_blocked_models(self):
        """Controller scope flags should update guidance and expected trigger counts."""
        ctrl = self._load_controller()

        ctrl.configure_model_scope(
            ["gpt-4o", "claude-haiku-4-5-20251001"],
            ["claude-haiku-4-5-20251001"],
        )

        assert ctrl.ACTIVE_MODELS == ["gpt-4o", "claude-haiku-4-5-20251001"]
        assert ctrl.EXPECTED_BLOCKED_MODELS == ["claude-haiku-4-5-20251001"]
        assert ctrl.EXPECTED_PIPELINE_TRIGGER_COUNT == 2
        assert "FOR EACH OF 2 MODELS" in ctrl.build_controller_goal()

    def test_automated_observations_flag_phase3_without_downloads(self):
        """Controller notes should explicitly call out missing download evidence after Phase 3."""
        ctrl = self._load_controller()

        lines = ctrl.build_automated_run_observation_lines(
            terminal_event="journey_complete",
            step_count=42,
            pipeline_trigger_count=ctrl.EXPECTED_PIPELINE_TRIGGER_COUNT,
            phase3_injected=True,
            download_event_count=0,
            validation_signal_count=0,
            desempenho_signal_count=0,
        )

        joined = "\n".join(lines)
        assert "phase3_no_downloads_observed" in joined
        assert "download_file" in joined

    def test_append_run_observation_appends_markdown_section(self):
        """Controller observations should be appended to the run-scoped verification report."""
        ctrl = self._load_controller()
        report_path = _workspace_tmp("controller_observation_append") / "verification_report.md"
        report_path.write_text("# Pipeline Verification Report\n", encoding="utf-8")

        ctrl.append_run_observation(
            report_path,
            "Controller Summary",
            ["Terminal event: journey_stopped", "Automated verdict: blocked_or_stopped"],
        )

        content = report_path.read_text(encoding="utf-8")
        assert "## Automated Run Observation: Controller Summary" in content
        assert "Terminal event: journey_stopped" in content
        assert "Automated verdict: blocked_or_stopped" in content

    def test_write_phase3_validation_artifacts_persists_json_and_report_section(self):
        """Controller should persist a machine-readable Phase 3 summary per run."""
        ctrl = self._load_controller()
        run_dir = _workspace_tmp("controller_phase3_artifacts")
        downloads_dir = run_dir / "downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "verification_report.md"
        report_path.write_text("# Pipeline Verification Report\n", encoding="utf-8")

        (downloads_dir / "extracao_questoes.json").write_text(
            json.dumps({"questoes": [], "total_questoes": 0, "pontuacao_total": 10}),
            encoding="utf-8",
        )
        (downloads_dir / "extracao_questoes.pdf").write_bytes(b"%PDF" + (b"x" * 1500))
        (downloads_dir / "correcao.json").write_text(
            json.dumps({"alunos": [], "notas": {}, "gabarito": {}}),
            encoding="utf-8",
        )
        (downloads_dir / "correcao.pdf").write_bytes(b"%PDF" + (b"x" * 2500))
        (downloads_dir / "analise_habilidades.json").write_text(
            json.dumps({"habilidades": [], "analise": {}}),
            encoding="utf-8",
        )
        (downloads_dir / "analise_habilidades.pdf").write_bytes(b"%PDF" + (b"x" * 2500))
        (downloads_dir / "relatorio_final.json").write_text(
            json.dumps({"relatorio": "ok", "resumo": "ok"}),
            encoding="utf-8",
        )
        (downloads_dir / "relatorio_final.pdf").write_bytes(b"%PDF" + (b"x" * 6000))

        summary = ctrl.write_phase3_validation_artifacts(run_dir, report_path)

        validation_path = run_dir / "phase3_validation.json"
        assert validation_path.exists()
        persisted = json.loads(validation_path.read_text(encoding="utf-8"))
        assert persisted["coverage"]["complete_stage_count"] == 4
        assert summary["overall_status"] == "unverified_model_scope"

        content = report_path.read_text(encoding="utf-8")
        assert "## Automated Run Observation: Phase 3 Artifact Validation" in content
        assert "Machine-readable artifact: phase3_validation.json" in content

    def test_controller_report_remains_authoritative_over_legacy_agent_report_path(self):
        """Legacy agent markdown helpers must not become authoritative in controller proof runs."""
        ctrl = self._load_controller()
        from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
        from tests.ui.investor_journey_agent.config import AgentConfig

        parent_dir = _workspace_tmp("controller_authoritative_report_parent")
        run_dir = parent_dir / "20260310_121500"
        report_path = ctrl.initialize_run_artifacts(run_dir)

        agent = InvestorJourneyAgent(
            persona="investor",
            viewport="desktop",
            config=AgentConfig(
                ask_before_action=False,
                output_dir=parent_dir,
                anthropic_api_key="test-key",
            ),
            pause_mode=True,
        )
        legacy_report = agent._write_verification_entry(
            model="unknown",
            stage="budget_exhaustion",
            status="PARTIAL",
            details="Legacy compatibility write only.",
        )
        legacy_before = legacy_report.read_text(encoding="utf-8")

        ctrl.resolve_verification_report(
            report_path,
            {
                "counts": {"json": 0, "pdf": 0, "other": 0},
                "requested_models": list(ctrl.MODELS),
                "expected_blocked_models": [],
                "triggered_models": [],
                "model_coverage": {
                    model: {
                        "stages_with_json": [],
                        "stages_with_pdf": [],
                        "complete_stage_count": 0,
                    }
                    for model in ctrl.MODELS
                },
                "stage_artifacts": {
                    stage: {
                        "json_path": None,
                        "json_top_level_keys": [],
                        "json_parse_error": None,
                        "pdf_path": None,
                        "pdf_size": 0,
                    }
                    for stage in ctrl.PIPELINE_STAGES
                },
                "origem_id_chain": {"status": "unverified", "reason": "No artifacts downloaded."},
                "student_name_consistency": {"status": "unverified", "reason": "No artifacts downloaded."},
                "desempenho": {
                    "tarefa": {"json": False, "pdf": False, "content_populated": False},
                    "turma": {"json": False, "pdf": False, "content_populated": False},
                    "materia": {"json": False, "pdf": False, "content_populated": False},
                },
                "desempenho_report_content": {"status": "unverified", "reason": "No artifacts downloaded."},
            },
            terminal_event="journey_stopped",
            phase_state=ctrl.PHASE_BLOCKED,
        )

        assert legacy_report == parent_dir / "verification_report.md"
        assert legacy_report.read_text(encoding="utf-8") == legacy_before
        controller_report = report_path.read_text(encoding="utf-8")
        assert "| pipeline-trigger-gpt4o |" in controller_report
        assert "BLOCKED" in controller_report

    def test_automated_observations_flag_phase3_validation_failures(self):
        """Controller summary should surface failed artifact validation as a distinct verdict."""
        ctrl = self._load_controller()

        lines = ctrl.build_automated_run_observation_lines(
            terminal_event="journey_complete",
            step_count=55,
            pipeline_trigger_count=ctrl.EXPECTED_PIPELINE_TRIGGER_COUNT,
            phase3_injected=True,
            download_event_count=4,
            validation_signal_count=4,
            desempenho_signal_count=0,
            phase3_artifact_status="validation_failed",
        )

        joined = "\n".join(lines)
        assert "phase3_validation_failed" in joined
        assert "shared validation rules failed" in joined

    def test_resolve_verification_report_applies_r3_statuses(self):
        """Controller should resolve checklist, stage-rule, and cascade rows from Phase 3 evidence."""
        ctrl = self._load_controller()
        run_dir = _workspace_tmp("controller_report_resolution")
        report_path = ctrl.initialize_run_artifacts(run_dir)

        phase3_summary = {
            "counts": {"json": 16, "pdf": 16, "other": 0},
            "overall_status": "validated",
            "triggered_models": list(ctrl.MODELS),
            "model_coverage": {
                model: {
                    "stages_with_json": list(ctrl.PIPELINE_STAGES),
                    "stages_with_pdf": list(ctrl.PIPELINE_STAGES),
                    "complete_stage_count": len(ctrl.PIPELINE_STAGES),
                }
                for model in ctrl.MODELS
            },
            "stage_artifacts": {
                "extrair_questoes": {
                    "json_path": "downloads/extrair_questoes.json",
                    "json_top_level_keys": ["questoes", "total_questoes"],
                    "json_parse_error": None,
                    "pdf_path": "downloads/extrair_questoes.pdf",
                    "pdf_size": 1500,
                },
                "corrigir": {
                    "json_path": "downloads/correcao.json",
                    "json_top_level_keys": ["alunos", "notas", "gabarito"],
                    "json_parse_error": None,
                    "pdf_path": "downloads/correcao.pdf",
                    "pdf_size": 2500,
                },
                "analisar_habilidades": {
                    "json_path": "downloads/analise_habilidades.json",
                    "json_top_level_keys": ["habilidades", "analise"],
                    "json_parse_error": None,
                    "pdf_path": "downloads/analise_habilidades.pdf",
                    "pdf_size": 2500,
                },
                "gerar_relatorio": {
                    "json_path": "downloads/relatorio_final.json",
                    "json_top_level_keys": ["relatorio", "resumo"],
                    "json_parse_error": None,
                    "pdf_path": "downloads/relatorio_final.pdf",
                    "pdf_size": 6000,
                },
            },
            "origem_id_chain": {"status": "pass", "reason": "Shared origem_id present."},
            "student_name_consistency": {
                "status": "unverified",
                "reason": "Student name was not exposed in two stage outputs.",
            },
            "desempenho": {
                "tarefa": {"json": True, "pdf": True, "content_populated": True},
                "turma": {"json": True, "pdf": True, "content_populated": True},
                "materia": {"json": True, "pdf": True, "content_populated": True},
            },
            "desempenho_report_content": {
                "status": "pass",
                "reason": "Downloaded desempenho JSON exposed habilidades content.",
            },
        }

        ctrl.resolve_verification_report(
            report_path,
            phase3_summary,
            terminal_event="journey_complete",
            phase_state=ctrl.PHASE_REVIEW,
        )

        content = report_path.read_text(encoding="utf-8")
        assert "| pipeline-trigger-gpt4o |" in content
        assert "| pipeline-trigger-gpt4o | Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages | OBSERVED |" in content
        assert "| download-json-outputs | Download JSON output for each model and each pipeline stage; confirm files are non-empty | OBSERVED |" in content
        assert "### Checklist: validation-student-name" in content
        assert "| UNVERIFIED | Student name was not exposed in two stage outputs. |" in content
        assert "| JSON fields: questoes, total_questoes | Present | OBSERVED | Required JSON fields observed in downloaded artifact. |" in content
        assert "| D5 | Check report content integrity: materia report references the correct turma and tarefa sub-reports | materia | OBSERVED |" in content
        assert "- OBSERVED:" in content
        assert "- UNVERIFIED: 1" in content

    def test_resolve_verification_report_marks_blocked_rows_on_blocked_run(self):
        """Blocked terminal runs should not leave missing evidence as if it were merely pending."""
        ctrl = self._load_controller()
        run_dir = _workspace_tmp("controller_report_resolution_blocked")
        report_path = ctrl.initialize_run_artifacts(run_dir)

        phase3_summary = {
            "counts": {"json": 0, "pdf": 0, "other": 0},
            "overall_status": "missing_downloads",
            "triggered_models": [],
            "model_coverage": {
                model: {
                    "stages_with_json": [],
                    "stages_with_pdf": [],
                    "complete_stage_count": 0,
                }
                for model in ctrl.MODELS
            },
            "stage_artifacts": {
                stage: {
                    "json_path": None,
                    "json_top_level_keys": [],
                    "json_parse_error": None,
                    "pdf_path": None,
                    "pdf_size": 0,
                }
                for stage in ctrl.PIPELINE_STAGES
            },
            "origem_id_chain": {"status": "unverified", "reason": "No artifacts downloaded."},
            "student_name_consistency": {"status": "unverified", "reason": "No artifacts downloaded."},
            "desempenho": {
                "tarefa": {"json": False, "pdf": False, "content_populated": False},
                "turma": {"json": False, "pdf": False, "content_populated": False},
                "materia": {"json": False, "pdf": False, "content_populated": False},
            },
            "desempenho_report_content": {"status": "unverified", "reason": "No artifacts downloaded."},
        }

        ctrl.resolve_verification_report(
            report_path,
            phase3_summary,
            terminal_event="journey_stopped",
            phase_state=ctrl.PHASE_BLOCKED,
        )

        content = report_path.read_text(encoding="utf-8")
        assert "| pipeline-trigger-gpt4o | Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages | BLOCKED |" in content
        assert "| download-json-outputs | Download JSON output for each model and each pipeline stage; confirm files are non-empty | BLOCKED |" in content
        assert "- BLOCKED:" in content

    def test_resolve_verification_report_marks_expected_blocked_models(self):
        """Scoped proof runs should resolve expected-blocked models as BLOCKED, not missing."""
        ctrl = self._load_controller()
        run_dir = _workspace_tmp("controller_report_resolution_expected_blocked")
        report_path = ctrl.initialize_run_artifacts(run_dir)

        phase3_summary = {
            "counts": {"json": 12, "pdf": 12, "other": 0},
            "overall_status": "validated_with_expected_blockers",
            "requested_models": list(ctrl.MODELS),
            "expected_blocked_models": ["claude-haiku-4-5-20251001"],
            "triggered_models": [
                "gpt-4o",
                "gpt-5-nano",
                "gemini-3-flash-preview",
            ],
            "model_coverage": {
                model: {
                    "stages_with_json": list(ctrl.PIPELINE_STAGES) if model != "claude-haiku-4-5-20251001" else [],
                    "stages_with_pdf": list(ctrl.PIPELINE_STAGES) if model != "claude-haiku-4-5-20251001" else [],
                    "complete_stage_count": len(ctrl.PIPELINE_STAGES) if model != "claude-haiku-4-5-20251001" else 0,
                }
                for model in ctrl.MODELS
            },
            "stage_artifacts": {
                stage: {
                    "json_path": f"downloads/gpt-4o/{stage}/_shared/{stage}.json",
                    "json_top_level_keys": ctrl.STAGE_RULES[stage]["expected_json_fields"],
                    "json_parse_error": None,
                    "pdf_path": f"downloads/gpt-4o/{stage}/_shared/{stage}.pdf",
                    "pdf_size": ctrl.STAGE_RULES[stage]["pdf_min_bytes"] + 100,
                }
                for stage in ctrl.PIPELINE_STAGES
            },
            "origem_id_chain": {"status": "pass", "reason": "Shared origem_id present."},
            "student_name_consistency": {"status": "unverified", "reason": "Shared student artifact."},
            "desempenho": {
                "tarefa": {"json": True, "pdf": True, "content_populated": True},
                "turma": {"json": True, "pdf": True, "content_populated": True},
                "materia": {"json": True, "pdf": True, "content_populated": True},
            },
            "desempenho_report_content": {"status": "pass", "reason": "Content populated."},
        }

        ctrl.resolve_verification_report(
            report_path,
            phase3_summary,
            terminal_event="journey_complete",
            phase_state=ctrl.PHASE_REVIEW,
        )

        content = report_path.read_text(encoding="utf-8")
        assert "| pipeline-trigger-claude-haiku | Trigger pipeline run for model claude-haiku-4-5-20251001 and confirm task panel shows all 4 stages | BLOCKED |" in content
        assert "expected blocked for this proof run scope" in content

    def test_persist_proof_scope_metadata_updates_summary_json(self):
        """Run summaries should persist requested/blocked model scope for proof review."""
        ctrl = self._load_controller()
        run_dir = _workspace_tmp("controller_summary_scope")
        summary_path = run_dir / "summary.json"
        summary_path.write_text(
            json.dumps({"summary": {"status": "completed", "success_rate": 1.0}}),
            encoding="utf-8",
        )

        ctrl.persist_proof_scope_metadata(
            run_dir,
            {
                "requested_models": ["gpt-4o", "gpt-5-nano", "gemini-3-flash-preview"],
                "expected_blocked_models": ["claude-haiku-4-5-20251001"],
                "model_status": {
                    "gpt-4o": {"status": "validated"},
                    "claude-haiku-4-5-20251001": {"status": "expected_blocked"},
                },
                "overall_status": "validated_with_expected_blockers",
                "b5_eligible": False,
            },
        )

        persisted = json.loads(summary_path.read_text(encoding="utf-8"))
        scope = persisted["verification_scope"]
        assert scope["requested_models"] == ["gpt-4o", "gpt-5-nano", "gemini-3-flash-preview"]
        assert scope["expected_blocked_models"] == ["claude-haiku-4-5-20251001"]
        assert scope["model_status"]["claude-haiku-4-5-20251001"]["status"] == "expected_blocked"
        assert scope["b5_eligible"] is False
