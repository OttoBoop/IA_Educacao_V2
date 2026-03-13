"""
F10-T1: Verification suite outer loop controller.

Starts the journey agent in pause-mode, acts as Claude Code outer loop:
- Auto-sends "continue" after each normal step
- Sends "guidance" when stuck events are detected
- Tracks CHECKLIST milestones and marks them PASS/FAIL in verification_report.md
- Runs until agent completes, gives up, or user interrupts

Usage:
    cd IA_Educacao_V2/backend
    python run_verification_f10.py
"""

import argparse
import json
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

from tests.ui.investor_journey_agent.cascade_steps import CASCADE_STEPS
from tests.ui.investor_journey_agent.pipeline_verification import (
    build_phase3_instruction,
    build_runtime_goal,
    build_startup_instruction,
    evaluate_downloaded_artifacts,
)
from tests.ui.investor_journey_agent.scenario import MODELS, PIPELINE_STAGES
from tests.ui.investor_journey_agent.validation_rules import STAGE_RULES
from tests.ui.investor_journey_agent.verification_template import (
    generate_verification_template,
)

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).parent
AGENT_MODULE = "tests.ui.investor_journey_agent"
LIVE_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_BASE = BACKEND_DIR / "investor_journey_reports" / "verification_run_F10"
MAX_STEPS = 400
VIEWPORT = "desktop"
PERSONA = "tester"
MATERIA_ID = "f95445ace30e7dc5"
TURMA_ID = "6b5dc44c08aaf375"
ATIVIDADE_ID = "effad48d128c7083"
ATIVIDADE_LABEL = "A1 - Calculo 1 atividade page"
ACTIVE_MODELS = list(MODELS)
EXPECTED_BLOCKED_MODELS: list[str] = []
EXPECTED_PIPELINE_TRIGGER_COUNT = len(ACTIVE_MODELS)

REPORT_STATUS_PENDING = "PENDING"
REPORT_STATUS_OBSERVED = "OBSERVED"
REPORT_STATUS_FAILED = "FAILED"
REPORT_STATUS_BLOCKED = "BLOCKED"
REPORT_STATUS_UNVERIFIED = "UNVERIFIED"
SUMMARY_STATUSES = (
    REPORT_STATUS_OBSERVED,
    REPORT_STATUS_FAILED,
    REPORT_STATUS_BLOCKED,
    REPORT_STATUS_UNVERIFIED,
    REPORT_STATUS_PENDING,
)

PHASE_SETUP = "setup"
PHASE_TRIGGER = "trigger"
PHASE_VALIDATE = "validate"
PHASE_REVIEW = "review"
PHASE_BLOCKED = "blocked"
PHASE_FAILED = "failed"
BLOCKING_TERMINAL_EVENTS = {"error", "journey_stopped", "stopped", "controller_interrupted"}
FAILED_TERMINAL_EVENTS = {"gave_up"}
PHASE3_FORBIDDEN_ACTION_PATTERNS = ("executarpipelinecompleto", "openmodalpipelinecompleto")
PIPELINE_CHECKLIST_IDS = {
    "gpt-4o": "pipeline-trigger-gpt4o",
    "gpt-5-nano": "pipeline-trigger-gpt5-nano",
    "claude-haiku-4-5-20251001": "pipeline-trigger-claude-haiku",
    "gemini-3-flash-preview": "pipeline-trigger-gemini-flash",
}

LEGACY_GOAL = (
    "THIS IS A JAVASCRIPT SINGLE-PAGE APP (SPA). URL always stays at '/'. DO NOT reload.\n\n"
    "=== COMPLETE STEP-BY-STEP INSTRUCTIONS ===\n\n"
    "PHASE 1 — NAVIGATE (use evaluate_js for ALL steps, do NOT click):\n"
    "  1a: evaluate_js → showMateria('f95445ace30e7dc5') — wait 5 seconds\n"
    "  1b: evaluate_js → showTurma('6b5dc44c08aaf375') — wait 8 seconds\n"
    "  1c: evaluate_js → showAtividade('effad48d128c7083') — wait 5 seconds\n"
    "You are now on the A1 - Cálculo 1 atividade page.\n\n"
    "PHASE 2 — TRIGGER PIPELINE FOR EACH OF 4 MODELS. "
    "For each model (gpt-4o, gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview):\n"
    "  2a: evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma')\n"
    "      (This opens a modal dialog)\n"
    "  2b: wait 2 seconds for modal to load\n"
    "  2c: select_option → select from the Modelo de IA dropdown "
    "(element with text containing 'gpt-4o' or 'haiku' or 'gemini' etc.)\n"
    "  2d: evaluate_js → executarPipelineCompleto()\n"
    "      (This is the function that the Executar button calls — do NOT try to click the button)\n"
    "  2e: wait 90 seconds (wait_duration_seconds=90) for pipeline to complete\n"
    "  2f: if still running, wait another 60 seconds\n"
    "  Repeat 2a-2f for all 4 models.\n\n"
    "PHASE 3 — DOWNLOAD & VALIDATE:\n"
    "  After pipelines complete, download_file for PDF and JSON from Documentos da Atividade.\n"
    "  Verify JSON contains: questao_id, nota, habilidades.\n"
    "  Check desempenho cascade reports exist (tarefa, turma, materia levels).\n\n"
    "KEY RULE: NEVER click any button to trigger the pipeline — use evaluate_js → executarPipelineCompleto() instead. "
    "NEVER scroll looking for a model dropdown on the main page — the dropdown is INSIDE the modal only. "
    "NEVER reload. NEVER re-navigate if you are already on the A1 page."
)

# B1: Keyword-based PASS marking removed — caused false positives.
def build_navigation_steps() -> list[str]:
    """Shared live-target navigation steps for the F10 controller."""
    return [
        f"evaluate_js -> showMateria('{MATERIA_ID}') -> wait 5 seconds",
        f"evaluate_js -> showTurma('{TURMA_ID}') -> wait 8 seconds",
        f"evaluate_js -> showAtividade('{ATIVIDADE_ID}') -> wait 5 seconds",
    ]


def build_navigation_recovery_block(*, numbered: bool = False) -> str:
    """Format navigation steps for guidance messages."""
    steps = build_navigation_steps()
    if numbered:
        return "\n".join(f"  Step {index}: {step}" for index, step in enumerate(steps, start=1))
    return "\n".join(f"  {step}" for step in steps)


def build_modal_trigger_script() -> str:
    """Return the shared pipeline modal-opening JS call."""
    return f"openModalPipelineCompleto('{ATIVIDADE_ID}', 'turma')"


def build_controller_goal() -> str:
    """Build the runtime goal from the shared pipeline verification spec."""
    return build_runtime_goal(
        navigation_steps=build_navigation_steps(),
        activity_label=ATIVIDADE_LABEL,
        open_modal_script=build_modal_trigger_script(),
        models=ACTIVE_MODELS,
    )


def build_controller_startup_guidance() -> str:
    """Build startup guidance from the shared spec."""
    return build_startup_instruction(
        navigation_steps=build_navigation_steps(),
        open_modal_script=build_modal_trigger_script(),
        models=ACTIVE_MODELS,
    )


def _parse_model_scope_arg(raw_value: str) -> list[str]:
    values = []
    seen = set()
    for chunk in (raw_value or "").split(","):
        model = chunk.strip()
        if not model:
            continue
        if model not in MODELS:
            raise ValueError(f"Unknown model '{model}'. Valid options: {', '.join(MODELS)}")
        if model not in seen:
            seen.add(model)
            values.append(model)
    return values


def configure_model_scope(
    active_models: list[str] | None,
    expected_blocked_models: list[str] | None,
) -> None:
    """Apply proof-run scope globally for controller guidance and validation."""
    global ACTIVE_MODELS, EXPECTED_BLOCKED_MODELS, EXPECTED_PIPELINE_TRIGGER_COUNT, GOAL

    requested_models = active_models or list(MODELS)
    blocked_models = [model for model in (expected_blocked_models or []) if model in requested_models]
    runnable_models = [model for model in requested_models if model not in blocked_models]
    ACTIVE_MODELS = runnable_models + blocked_models
    EXPECTED_BLOCKED_MODELS = blocked_models
    EXPECTED_PIPELINE_TRIGGER_COUNT = len(ACTIVE_MODELS)
    GOAL = build_controller_goal()


def advance_phase_state(
    current_phase: str,
    *,
    has_seen_step: bool,
    pipeline_trigger_count: int,
    terminal_event: str | None = None,
) -> str:
    """Advance the controller's explicit phase state."""
    if current_phase in (PHASE_BLOCKED, PHASE_FAILED):
        return current_phase
    if terminal_event in BLOCKING_TERMINAL_EVENTS:
        return PHASE_BLOCKED
    if terminal_event in FAILED_TERMINAL_EVENTS:
        return PHASE_FAILED
    if terminal_event:
        return PHASE_REVIEW
    if pipeline_trigger_count >= EXPECTED_PIPELINE_TRIGGER_COUNT:
        return PHASE_VALIDATE
    if has_seen_step and current_phase == PHASE_SETUP:
        return PHASE_TRIGGER
    return current_phase


def is_action_allowed_in_phase(
    phase_state: str,
    *,
    action: str = "",
    target: str = "",
    thought: str = "",
) -> bool:
    """Return whether the observed action is allowed in the current phase."""
    if phase_state != PHASE_VALIDATE:
        return True
    text = f"{action} {target} {thought}".lower()
    return not any(pattern in text for pattern in PHASE3_FORBIDDEN_ACTION_PATTERNS)


def build_automated_run_observation_lines(
    *,
    terminal_event: str,
    step_count: int,
    pipeline_trigger_count: int,
    phase3_injected: bool,
    download_event_count: int,
    validation_signal_count: int,
    desempenho_signal_count: int,
    phase_state: str | None = None,
    phase3_artifact_status: str | None = None,
    terminal_reason: str | None = None,
) -> list[str]:
    """Summarize controller-side evidence without claiming PASS/FAIL."""
    lines = [
        f"Terminal event: {terminal_event}",
        f"Steps completed: {step_count}",
        f"Pipeline triggers observed: {pipeline_trigger_count}/{EXPECTED_PIPELINE_TRIGGER_COUNT}",
        "Requested models: " + ", ".join(ACTIVE_MODELS),
        "Expected blocked models: " + (", ".join(EXPECTED_BLOCKED_MODELS) or "none"),
        f"Phase 3 guidance injected: {'yes' if phase3_injected else 'no'}",
        f"Download actions observed: {download_event_count}",
        f"Validation signals observed: {validation_signal_count}",
        f"Desempenho-related signals observed: {desempenho_signal_count}",
    ]
    if phase_state:
        lines.append(f"Final controller phase: {phase_state}")
    if phase3_artifact_status:
        lines.append(f"Phase 3 artifact status: {phase3_artifact_status}")
    if terminal_reason:
        lines.append(f"Terminal reason: {terminal_reason}")

    if phase_state == PHASE_BLOCKED or terminal_event in ("error", "journey_stopped", "stopped"):
        verdict = "blocked_or_stopped"
    elif pipeline_trigger_count < EXPECTED_PIPELINE_TRIGGER_COUNT:
        verdict = "phase2_incomplete"
    elif phase3_artifact_status == "missing_downloads":
        verdict = "phase3_no_downloads_observed"
    elif phase3_artifact_status == "incomplete_artifacts":
        verdict = "phase3_artifacts_incomplete"
    elif phase3_artifact_status == "validation_failed":
        verdict = "phase3_validation_failed"
    elif phase3_artifact_status == "unverified_model_scope":
        verdict = "phase3_model_scope_unverified"
    elif phase3_artifact_status == "validated_with_expected_blockers":
        verdict = "phase3_validated_with_expected_blockers"
    elif phase3_injected and download_event_count == 0:
        verdict = "phase3_no_downloads_observed"
    elif phase3_injected and validation_signal_count == 0:
        verdict = "phase3_no_validation_observed"
    else:
        verdict = "review_required"
    lines.append(f"Automated verdict: {verdict}")

    if verdict == "phase2_incomplete":
        lines.append("Human review note: the controller did not observe all expected pipeline triggers.")
    elif verdict == "phase3_no_downloads_observed":
        lines.append("Human review note: Phase 3 guidance was injected, but no successful download_file action was observed.")
    elif verdict == "phase3_artifacts_incomplete":
        lines.append("Human review note: some required JSON or PDF pipeline artifacts were still missing in the run downloads folder.")
    elif verdict == "phase3_validation_failed":
        lines.append("Human review note: artifacts were downloaded, but shared validation rules failed on one or more stages.")
    elif verdict == "phase3_model_scope_unverified":
        lines.append("Human review note: artifacts look structurally complete, but the downloads do not prove model-by-model coverage.")
    elif verdict == "phase3_validated_with_expected_blockers":
        lines.append("Human review note: requested artifacts validated for the runnable models, but this proof scope still contains explicitly blocked models and cannot close B5.")
    elif verdict == "phase3_no_validation_observed":
        lines.append("Human review note: downloads may have started, but no validation evidence was observed after Phase 3 guidance.")
    elif verdict == "blocked_or_stopped":
        lines.append("Human review note: external failure or operator stop prevented trustworthy completion.")
    else:
        lines.append("Human review note: PASS/FAIL still requires manual verification of the generated artifacts.")

    return lines


def append_run_observation(report_path: Path, title: str, lines: list[str]) -> None:
    """Append controller observations to the run-scoped verification report."""
    if not report_path.exists():
        return
    with open(report_path, "a", encoding="utf-8") as f:
        f.write("\n## Automated Run Observation: ")
        f.write(title)
        f.write("\n\n")
        for line in lines:
            f.write(f"- {line}\n")


def build_phase3_validation_observation_lines(phase3_summary: dict) -> list[str]:
    """Format the machine-readable Phase 3 validation summary for the markdown report."""
    counts = phase3_summary.get("counts", {})
    coverage = phase3_summary.get("coverage", {})
    lines = [
        f"Overall artifact status: {phase3_summary.get('overall_status', 'unknown')}",
        f"Downloads directory: {phase3_summary.get('downloads_dir', '')}",
        "Requested models: " + (", ".join(phase3_summary.get("requested_models", [])) or "none"),
        "Expected blocked models: " + (", ".join(phase3_summary.get("expected_blocked_models", [])) or "none"),
        f"B5 eligible: {'yes' if phase3_summary.get('b5_eligible') else 'no'}",
        f"Files found: json={counts.get('json', 0)}, pdf={counts.get('pdf', 0)}, other={counts.get('other', 0)}",
        f"Model scope confirmed: {'yes' if phase3_summary.get('model_scope_confirmed') else 'no'}",
        "Recognized models in artifacts: "
        + (", ".join(phase3_summary.get("recognized_models", [])) or "none"),
        "Triggered models from manifest: "
        + (", ".join(phase3_summary.get("triggered_models", [])) or "none"),
        "Missing triggered models: "
        + (", ".join(phase3_summary.get("missing_trigger_models", [])) or "none"),
        f"Download manifest entries: {phase3_summary.get('download_manifest_entries', 0)}",
        f"Downloads with explicit model context: {phase3_summary.get('downloads_with_explicit_model', 0)}",
        f"Normalized download entries: {phase3_summary.get('normalized_download_entries', 0)}",
        "Missing JSON stages: "
        + (", ".join(coverage.get("missing_json_stages", [])) or "none"),
        "Missing PDF stages: "
        + (", ".join(coverage.get("missing_pdf_stages", [])) or "none"),
        f"origem_id chain: {phase3_summary.get('origem_id_chain', {}).get('status', 'unknown')} - "
        f"{phase3_summary.get('origem_id_chain', {}).get('reason', '')}",
        f"Student name consistency: {phase3_summary.get('student_name_consistency', {}).get('status', 'unknown')} - "
        f"{phase3_summary.get('student_name_consistency', {}).get('reason', '')}",
        f"Desempenho report content: {phase3_summary.get('desempenho_report_content', {}).get('status', 'unknown')} - "
        f"{phase3_summary.get('desempenho_report_content', {}).get('reason', '')}",
    ]

    desempenho = phase3_summary.get("desempenho", {})
    for level in ("tarefa", "turma", "materia"):
        level_data = desempenho.get(level, {})
        lines.append(
            f"desempenho {level}: json={'yes' if level_data.get('json') else 'no'}, "
            f"pdf={'yes' if level_data.get('pdf') else 'no'}, "
            f"content={'yes' if level_data.get('content_populated') else 'no'}"
        )

    stage_artifacts = phase3_summary.get("stage_artifacts", {})
    for stage in ("extrair_questoes", "corrigir", "analisar_habilidades", "gerar_relatorio"):
        stage_data = stage_artifacts.get(stage, {})
        errors = stage_data.get("errors") or []
        line = (
            f"{stage}: {stage_data.get('status', 'missing')} | "
            f"json={'yes' if stage_data.get('json_path') else 'no'} | "
            f"pdf={'yes' if stage_data.get('pdf_path') else 'no'} | "
            f"models={', '.join(stage_data.get('recognized_models', [])) or 'none'}"
        )
        if errors:
            line += f" | errors: {'; '.join(errors)}"
        elif stage_data.get("json_parse_error"):
            line += f" | json_parse_error: {stage_data['json_parse_error']}"
        lines.append(line)

    unknown_files = phase3_summary.get("unknown_files") or []
    if unknown_files:
        lines.append("Unclassified downloaded files: " + ", ".join(unknown_files[:10]))

    normalization = phase3_summary.get("normalization", {})
    for record in normalization.get("normalized_files", [])[:10]:
        lines.append(
            "normalized: "
            f"{record.get('original_path', '')} -> {record.get('normalized_path', '')}"
        )

    model_status = phase3_summary.get("model_status", {})
    for model, status_data in model_status.items():
        lines.append(
            f"{model}: status={status_data.get('status', 'unknown')} "
            f"| complete_stages={status_data.get('complete_stage_count', 0)}/4"
        )

    model_coverage = phase3_summary.get("model_coverage", {})
    for model, coverage_data in model_coverage.items():
        lines.append(
            f"{model}: json_stages={len(coverage_data.get('stages_with_json', []))}/4, "
            f"pdf_stages={len(coverage_data.get('stages_with_pdf', []))}/4"
        )

    lines.append("Machine-readable artifact: phase3_validation.json")
    return lines


def write_phase3_validation_artifacts(run_dir: Path, verification_report: Path) -> dict:
    """Persist controller-side Phase 3 validation outputs for the current run."""
    phase3_summary = evaluate_downloaded_artifacts(
        run_dir / "downloads",
        manifest_path=run_dir / "artifact_manifest.jsonl",
        requested_models=ACTIVE_MODELS,
        expected_blocked_models=EXPECTED_BLOCKED_MODELS,
    )
    validation_path = run_dir / "phase3_validation.json"
    validation_path.write_text(
        json.dumps(phase3_summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    append_run_observation(
        verification_report,
        "Phase 3 Artifact Validation",
        build_phase3_validation_observation_lines(phase3_summary),
    )
    return phase3_summary


GOAL = build_controller_goal()

# Checklist items must be marked by human review after the run, not auto-detected.


# ---------------------------------------------------------------------------
# Event reading
# ---------------------------------------------------------------------------


def read_new_events(events_path: Path, last_count: int) -> tuple[list[dict], int]:
    """Read events added since last_count lines."""
    if not events_path.exists():
        return [], last_count
    try:
        lines = events_path.read_text(encoding="utf-8").strip().split("\n")
        new_lines = lines[last_count:]
        events = []
        for line in new_lines:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return events, len(lines)
    except Exception:
        return [], last_count


# ---------------------------------------------------------------------------
# Command sending
# ---------------------------------------------------------------------------


def send_command(commands_path: Path, command_type: str, data: dict | None = None):
    """Append a command to commands.jsonl."""
    cmd = {"command_type": command_type, "data": data or {}, "timestamp": datetime.utcnow().isoformat()}
    with open(commands_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(cmd) + "\n")
    print(f"[CTRL] → {command_type.upper()}" + (f": {data.get('instruction', '')[:60]}" if data and "instruction" in data else ""))


# ---------------------------------------------------------------------------
# Verification report updater
# ---------------------------------------------------------------------------


def _legacy_mark_checklist_item(report_path: Path, item_id: str, status: str, observation: str = ""):
    """Update a CHECKLIST item's status in the verification report."""
    if not report_path.exists():
        return
    content = report_path.read_text(encoding="utf-8")

    # Format 1: table row with item_id in it — e.g. "| pipeline-trigger-gpt4o | desc | PENDING | |"
    # After group1 ends at "|", the literal " PENDING " is consumed, leaving "| obs |" (no leading space).
    pattern = rf"(\| {re.escape(item_id)} \|[^|]*\|) PENDING (\|[^|]*\|)"
    replacement = rf"\1 {status} \2"
    new_content = re.sub(pattern, replacement, content)

    # Format 2: section-header item — "### Checklist: item_id" followed by "| PENDING | |"
    if new_content == content:
        # Find the section for this item_id and replace the next PENDING in its table
        header_pattern = rf"(### Checklist: {re.escape(item_id)}.*?)\| PENDING \|"
        new_content = re.sub(header_pattern, rf"\1| {status} |", content, count=1, flags=re.DOTALL)

    if new_content != content:
        report_path.write_text(new_content, encoding="utf-8")
        print(f"[CTRL] PASS: Marked {item_id} -> {status}")


def _legacy_update_summary(report_path: Path):
    """Update PASS/FAIL/PENDING counts in Summary section."""
    if not report_path.exists():
        return
    content = report_path.read_text(encoding="utf-8")
    pass_count = content.count(" PASS ")
    fail_count = content.count(" FAIL ")
    pending_count = content.count(" PENDING ")
    content = re.sub(r"- PASS: \d+", f"- PASS: {pass_count}", content)
    content = re.sub(r"- FAIL: \d+", f"- FAIL: {fail_count}", content)
    content = re.sub(r"- PENDING: \d+", f"- PENDING: {pending_count}", content)
    report_path.write_text(content, encoding="utf-8")


_STATUS_ROW_RE = re.compile(r"^\|\s*(PENDING|OBSERVED|FAILED|BLOCKED|UNVERIFIED)\s*\|")


def _sanitize_observation(observation: str) -> str:
    return " ".join(str(observation).replace("|", "/").split()) if observation else ""


def _read_report_lines(report_path: Path) -> list[str]:
    return report_path.read_text(encoding="utf-8").splitlines()


def _write_report_lines(report_path: Path, lines: list[str]) -> None:
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _set_table_status_line(
    line: str,
    *,
    status_index: int,
    observation_index: int,
    status: str,
    observation: str,
) -> str:
    parts = line.split("|")
    if len(parts) <= observation_index + 1:
        return line
    parts[status_index] = f" {status} "
    parts[observation_index] = f" {_sanitize_observation(observation)} "
    return "|".join(parts)


def _mark_checklist_item_lines(lines: list[str], item_id: str, status: str, observation: str = "") -> bool:
    row_prefix = f"| {item_id} |"
    for index, line in enumerate(lines):
        if line.startswith(row_prefix):
            lines[index] = _set_table_status_line(
                line,
                status_index=3,
                observation_index=4,
                status=status,
                observation=observation,
            )
            return True

    header = f"### Checklist: {item_id}"
    for index, line in enumerate(lines):
        if line.strip() != header:
            continue
        for nested_index in range(index + 1, min(index + 8, len(lines))):
            if _STATUS_ROW_RE.match(lines[nested_index]):
                lines[nested_index] = _set_table_status_line(
                    lines[nested_index],
                    status_index=1,
                    observation_index=2,
                    status=status,
                    observation=observation,
                )
                return True
    return False


def _mark_stage_rule_lines(
    lines: list[str],
    stage_name: str,
    check_prefix: str,
    status: str,
    observation: str = "",
) -> bool:
    header = f"### Stage: {stage_name}"
    in_section = False
    for index, line in enumerate(lines):
        if line.strip() == header:
            in_section = True
            continue
        if in_section and line.startswith("### "):
            break
        if in_section and line.startswith(f"| {check_prefix}"):
            lines[index] = _set_table_status_line(
                line,
                status_index=3,
                observation_index=4,
                status=status,
                observation=observation,
            )
            return True
    return False


def _mark_cascade_step_lines(lines: list[str], step_id: str, status: str, observation: str = "") -> bool:
    row_prefix = f"| {step_id} |"
    for index, line in enumerate(lines):
        if line.startswith(row_prefix):
            lines[index] = _set_table_status_line(
                line,
                status_index=4,
                observation_index=5,
                status=status,
                observation=observation,
            )
            return True
    return False


def mark_checklist_item(report_path: Path, item_id: str, status: str, observation: str = ""):
    """Update a CHECKLIST item's status in the verification report."""
    if not report_path.exists():
        return
    lines = _read_report_lines(report_path)
    if _mark_checklist_item_lines(lines, item_id, status, observation):
        _write_report_lines(report_path, lines)
        print(f"[CTRL] STATUS: Marked {item_id} -> {status}")


def _map_phase3_status(source_status: str | None, reason: str, *, blocked_run: bool) -> tuple[str, str]:
    if source_status == "pass":
        return REPORT_STATUS_OBSERVED, reason
    if source_status == "fail":
        return REPORT_STATUS_FAILED, reason
    if blocked_run:
        return REPORT_STATUS_BLOCKED, reason or "Run blocked before this evidence was fully collected."
    return REPORT_STATUS_UNVERIFIED, reason or "Evidence remains unverified."


def _aggregate_status(
    statuses: list[str],
    *,
    blocked_run: bool,
    success_reason: str,
    partial_reason: str,
    failure_reason: str,
) -> tuple[str, str]:
    if statuses and all(status == REPORT_STATUS_OBSERVED for status in statuses):
        return REPORT_STATUS_OBSERVED, success_reason
    if any(status == REPORT_STATUS_FAILED for status in statuses):
        return REPORT_STATUS_FAILED, failure_reason
    if blocked_run and not any(status == REPORT_STATUS_OBSERVED for status in statuses):
        return REPORT_STATUS_BLOCKED, "Run blocked before enough evidence was collected."
    return REPORT_STATUS_UNVERIFIED, partial_reason


def resolve_verification_report(
    report_path: Path,
    phase3_summary: dict,
    *,
    terminal_event: str,
    phase_state: str,
) -> None:
    """Resolve checklist, stage-rule, and cascade rows from Phase 3 evidence."""
    if not report_path.exists():
        return

    lines = _read_report_lines(report_path)
    blocked_run = phase_state == PHASE_BLOCKED or terminal_event in BLOCKING_TERMINAL_EVENTS
    counts = phase3_summary.get("counts", {})
    stage_artifacts = phase3_summary.get("stage_artifacts", {})
    model_coverage = phase3_summary.get("model_coverage", {})
    requested_models = phase3_summary.get("requested_models", ACTIVE_MODELS)
    expected_blocked_models = set(
        phase3_summary.get("expected_blocked_models", EXPECTED_BLOCKED_MODELS)
    )
    triggered_models = set(phase3_summary.get("triggered_models", []))
    desempenho = phase3_summary.get("desempenho", {})

    for model, item_id in PIPELINE_CHECKLIST_IDS.items():
        if model not in requested_models:
            status = REPORT_STATUS_UNVERIFIED
            observation = "Model excluded from this proof run scope."
        elif model in expected_blocked_models:
            status = REPORT_STATUS_BLOCKED
            observation = "Model marked expected blocked for this proof run scope."
        elif model in triggered_models:
            status = REPORT_STATUS_OBSERVED
            observation = "Model trigger observed in the run artifact manifest."
        elif blocked_run:
            status = REPORT_STATUS_BLOCKED
            observation = "Run blocked before trigger evidence for this model was recorded."
        else:
            status = REPORT_STATUS_UNVERIFIED
            observation = "No trigger evidence for this model was recorded."
        _mark_checklist_item_lines(lines, item_id, status, observation)

    json_statuses: list[str] = []
    pdf_statuses: list[str] = []
    for stage_name in PIPELINE_STAGES:
        rule = STAGE_RULES[stage_name]
        stage_data = stage_artifacts.get(stage_name, {})
        json_path = stage_data.get("json_path")
        json_keys = set(stage_data.get("json_top_level_keys") or [])
        json_parse_error = stage_data.get("json_parse_error")
        missing_fields = [field for field in rule["expected_json_fields"] if field not in json_keys]

        if json_path:
            if json_parse_error:
                json_status = REPORT_STATUS_FAILED
                json_observation = f"JSON parse error: {json_parse_error}"
            elif missing_fields:
                json_status = REPORT_STATUS_FAILED
                json_observation = f"Missing JSON fields: {', '.join(missing_fields)}."
            else:
                json_status = REPORT_STATUS_OBSERVED
                json_observation = "Required JSON fields observed in downloaded artifact."
        elif blocked_run:
            json_status = REPORT_STATUS_BLOCKED
            json_observation = "Run blocked before JSON artifact was collected."
        else:
            json_status = REPORT_STATUS_UNVERIFIED
            json_observation = "No JSON artifact was downloaded for this stage."
        json_statuses.append(json_status)
        _mark_stage_rule_lines(lines, stage_name, "JSON fields:", json_status, json_observation)

        pdf_path = stage_data.get("pdf_path")
        pdf_size = stage_data.get("pdf_size", 0) or 0
        if pdf_path:
            if pdf_size >= rule["pdf_min_bytes"]:
                pdf_status = REPORT_STATUS_OBSERVED
                pdf_observation = f"PDF size {pdf_size} bytes meets the minimum threshold."
            else:
                pdf_status = REPORT_STATUS_FAILED
                pdf_observation = f"PDF size {pdf_size} bytes is below the minimum {rule['pdf_min_bytes']}."
        elif blocked_run:
            pdf_status = REPORT_STATUS_BLOCKED
            pdf_observation = "Run blocked before PDF artifact was collected."
        else:
            pdf_status = REPORT_STATUS_UNVERIFIED
            pdf_observation = "No PDF artifact was downloaded for this stage."
        pdf_statuses.append(pdf_status)
        _mark_stage_rule_lines(lines, stage_name, "PDF size", pdf_status, pdf_observation)

    required_models = [
        model for model in requested_models if model not in expected_blocked_models
    ]
    json_download_complete = all(
        len(model_coverage.get(model, {}).get("stages_with_json", [])) == len(PIPELINE_STAGES)
        for model in required_models
    )
    pdf_download_complete = all(
        len(model_coverage.get(model, {}).get("stages_with_pdf", [])) == len(PIPELINE_STAGES)
        for model in required_models
    )

    if json_download_complete and counts.get("json", 0) > 0:
        download_json_status = REPORT_STATUS_OBSERVED
        download_json_observation = "JSON artifacts were downloaded for every requested non-blocked model and pipeline stage."
    elif blocked_run and counts.get("json", 0) == 0:
        download_json_status = REPORT_STATUS_BLOCKED
        download_json_observation = "Run blocked before JSON downloads were collected."
    else:
        download_json_status = REPORT_STATUS_UNVERIFIED
        download_json_observation = (
            f"Observed {counts.get('json', 0)} JSON downloads; expected full "
            "requested model/stage coverage."
        )
    _mark_checklist_item_lines(lines, "download-json-outputs", download_json_status, download_json_observation)

    if pdf_download_complete and counts.get("pdf", 0) > 0:
        download_pdf_status = REPORT_STATUS_OBSERVED
        download_pdf_observation = "PDF artifacts were downloaded for every requested non-blocked model and pipeline stage."
    elif blocked_run and counts.get("pdf", 0) == 0:
        download_pdf_status = REPORT_STATUS_BLOCKED
        download_pdf_observation = "Run blocked before PDF downloads were collected."
    else:
        download_pdf_status = REPORT_STATUS_UNVERIFIED
        download_pdf_observation = (
            f"Observed {counts.get('pdf', 0)} PDF downloads; expected full "
            "requested model/stage coverage."
        )
    _mark_checklist_item_lines(lines, "download-pdf-reports", download_pdf_status, download_pdf_observation)

    validation_json_status, validation_json_observation = _aggregate_status(
        json_statuses,
        blocked_run=blocked_run,
        success_reason="Required JSON fields were observed across all pipeline stages.",
        partial_reason="Some JSON field checks remain incomplete.",
        failure_reason="One or more stage JSON artifacts failed the required-field checks.",
    )
    _mark_checklist_item_lines(lines, "validation-json-fields", validation_json_status, validation_json_observation)

    origem_status, origem_observation = _map_phase3_status(
        phase3_summary.get("origem_id_chain", {}).get("status"),
        phase3_summary.get("origem_id_chain", {}).get("reason", ""),
        blocked_run=blocked_run,
    )
    _mark_checklist_item_lines(lines, "validation-origem-id-chain", origem_status, origem_observation)

    student_status, student_observation = _map_phase3_status(
        phase3_summary.get("student_name_consistency", {}).get("status"),
        phase3_summary.get("student_name_consistency", {}).get("reason", ""),
        blocked_run=blocked_run,
    )
    _mark_checklist_item_lines(lines, "validation-student-name", student_status, student_observation)

    any_desempenho_artifact = any(
        level_data.get("json") or level_data.get("pdf")
        for level_data in desempenho.values()
    )
    if any_desempenho_artifact:
        desempenho_trigger_status = REPORT_STATUS_OBSERVED
        desempenho_trigger_observation = "Downloaded desempenho artifacts show that the cascade path was exercised."
    elif blocked_run:
        desempenho_trigger_status = REPORT_STATUS_BLOCKED
        desempenho_trigger_observation = "Run blocked before desempenho artifact evidence was collected."
    else:
        desempenho_trigger_status = REPORT_STATUS_UNVERIFIED
        desempenho_trigger_observation = "No desempenho artifact evidence was collected."
    _mark_checklist_item_lines(lines, "desempenho-cascade-trigger", desempenho_trigger_status, desempenho_trigger_observation)

    missing_desempenho_levels = [
        level
        for level in ("tarefa", "turma", "materia")
        if not (desempenho.get(level, {}).get("json") and desempenho.get(level, {}).get("pdf"))
    ]
    if not missing_desempenho_levels and any_desempenho_artifact:
        desempenho_creation_status = REPORT_STATUS_OBSERVED
        desempenho_creation_observation = "Tarefa, turma, and materia desempenho artifacts were all downloaded."
    elif blocked_run and not any_desempenho_artifact:
        desempenho_creation_status = REPORT_STATUS_BLOCKED
        desempenho_creation_observation = "Run blocked before desempenho auto-creation could be verified."
    else:
        desempenho_creation_status = REPORT_STATUS_UNVERIFIED
        desempenho_creation_observation = "Missing desempenho evidence for levels: " + ", ".join(missing_desempenho_levels)
    _mark_checklist_item_lines(lines, "desempenho-auto-creation", desempenho_creation_status, desempenho_creation_observation)

    desempenho_content_status, desempenho_content_observation = _map_phase3_status(
        phase3_summary.get("desempenho_report_content", {}).get("status"),
        phase3_summary.get("desempenho_report_content", {}).get("reason", ""),
        blocked_run=blocked_run,
    )
    _mark_checklist_item_lines(lines, "desempenho-report-content", desempenho_content_status, desempenho_content_observation)

    cascade_resolutions = {
        "D1": (
            REPORT_STATUS_OBSERVED if desempenho.get("materia", {}).get("json") or desempenho.get("materia", {}).get("pdf")
            else (REPORT_STATUS_BLOCKED if blocked_run else REPORT_STATUS_UNVERIFIED),
            "Materia-level desempenho artifact observed."
            if desempenho.get("materia", {}).get("json") or desempenho.get("materia", {}).get("pdf")
            else ("Run blocked before materia-level desempenho was verified." if blocked_run else "Materia-level desempenho evidence was not downloaded."),
        ),
        "D2": (
            REPORT_STATUS_OBSERVED if desempenho.get("materia", {}).get("json") and desempenho.get("materia", {}).get("pdf")
            else (REPORT_STATUS_BLOCKED if blocked_run and not any_desempenho_artifact else REPORT_STATUS_UNVERIFIED),
            "Materia JSON and PDF artifacts were both downloaded."
            if desempenho.get("materia", {}).get("json") and desempenho.get("materia", {}).get("pdf")
            else ("Run blocked before materia report download was verified." if blocked_run and not any_desempenho_artifact else "Materia report download evidence remains incomplete."),
        ),
        "D3": (
            REPORT_STATUS_OBSERVED if desempenho.get("turma", {}).get("json") and desempenho.get("turma", {}).get("pdf")
            else (REPORT_STATUS_BLOCKED if blocked_run and not any_desempenho_artifact else REPORT_STATUS_UNVERIFIED),
            "Turma desempenho artifacts were observed."
            if desempenho.get("turma", {}).get("json") and desempenho.get("turma", {}).get("pdf")
            else ("Run blocked before turma auto-creation was verified." if blocked_run and not any_desempenho_artifact else "Turma desempenho evidence remains incomplete."),
        ),
        "D4": (
            REPORT_STATUS_OBSERVED if desempenho.get("tarefa", {}).get("json") and desempenho.get("tarefa", {}).get("pdf")
            else (REPORT_STATUS_BLOCKED if blocked_run and not any_desempenho_artifact else REPORT_STATUS_UNVERIFIED),
            "Tarefa desempenho artifacts were observed."
            if desempenho.get("tarefa", {}).get("json") and desempenho.get("tarefa", {}).get("pdf")
            else ("Run blocked before tarefa auto-creation was verified." if blocked_run and not any_desempenho_artifact else "Tarefa desempenho evidence remains incomplete."),
        ),
        "D5": (desempenho_content_status, desempenho_content_observation),
    }
    for step in CASCADE_STEPS:
        status, observation = cascade_resolutions.get(
            step["step_id"],
            (REPORT_STATUS_UNVERIFIED, "No evidence mapping is defined for this cascade step."),
        )
        _mark_cascade_step_lines(lines, step["step_id"], status, observation)

    _write_report_lines(report_path, lines)
    update_summary(report_path)


def update_summary(report_path: Path):
    """Update report summary counts for the controller-owned status vocabulary."""
    if not report_path.exists():
        return
    lines = _read_report_lines(report_path)
    cell_pattern = re.compile(r"\|\s*(PENDING|OBSERVED|FAILED|BLOCKED|UNVERIFIED)\s*\|")
    counts = {status: 0 for status in SUMMARY_STATUSES}
    for line in lines:
        for status in cell_pattern.findall(line):
            counts[status] += 1

    replacements = {
        "- OBSERVED:": f"- OBSERVED: {counts[REPORT_STATUS_OBSERVED]}",
        "- FAILED:": f"- FAILED: {counts[REPORT_STATUS_FAILED]}",
        "- BLOCKED:": f"- BLOCKED: {counts[REPORT_STATUS_BLOCKED]}",
        "- UNVERIFIED:": f"- UNVERIFIED: {counts[REPORT_STATUS_UNVERIFIED]}",
        "- PENDING:": f"- PENDING: {counts[REPORT_STATUS_PENDING]}",
    }
    for index, line in enumerate(lines):
        for prefix, replacement in replacements.items():
            if line.startswith(prefix):
                lines[index] = replacement
                break
    _write_report_lines(report_path, lines)


def persist_proof_scope_metadata(run_dir: Path, phase3_summary: dict | None) -> None:
    """Attach proof-scope metadata to the run summary after the agent process exits."""
    if not phase3_summary:
        return

    summary_path = Path(run_dir) / "summary.json"
    if not summary_path.exists():
        return

    data = json.loads(summary_path.read_text(encoding="utf-8"))
    data["verification_scope"] = {
        "requested_models": phase3_summary.get("requested_models", []),
        "expected_blocked_models": phase3_summary.get("expected_blocked_models", []),
        "model_status": phase3_summary.get("model_status", {}),
        "phase3_overall_status": phase3_summary.get("overall_status"),
        "b5_eligible": phase3_summary.get("b5_eligible", False),
    }
    summary_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def initialize_run_artifacts(run_dir: Path) -> Path:
    """Create the run-scoped verification report from the shared template."""
    run_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "verification_report.md"
    generate_verification_template(report_path)
    return report_path


# ---------------------------------------------------------------------------
# Main controller loop
# ---------------------------------------------------------------------------


def run_controller(ipc_dir: Path, verification_report: Path):
    events_path = ipc_dir / "events.jsonl"
    commands_path = ipc_dir / "commands.jsonl"

    print(f"[CTRL] IPC directory: {ipc_dir}")
    print(f"[CTRL] Verification report: {verification_report}")
    print(f"[CTRL] Press Ctrl+C to stop the run gracefully\n")

    last_event_count = 0
    stuck_pending = False
    step_count = 0
    running = True
    # Track recent actions for repetition-based stuck detection
    recent_actions: list[tuple[str, str]] = []  # (action_type, target_prefix)
    guidance_cooldown = 0  # Steps to wait before sending another guidance
    phase_state = PHASE_SETUP
    # B3: count executarPipelineCompleto triggers to detect when Phase 3 should start
    pipeline_trigger_count = 0
    phase3_injected = False
    download_event_count = 0
    validation_signal_count = 0
    desempenho_signal_count = 0
    final_state = {
        "phase3_summary": None,
        "terminal_event": None,
        "phase_state": phase_state,
    }

    while running:
        try:
            new_events, last_event_count = read_new_events(events_path, last_event_count)

            for event in new_events:
                etype = event.get("event_type")

                if etype == "step_completed":
                    step_count += 1
                    action = event.get("action", "")
                    target = event.get("target", "")
                    thought = event.get("thought", "")
                    success = event.get("success", False)
                    text = (thought + " " + action + " " + target).lower()

                    status_char = "OK" if success else "!!"
                    print(
                        f"[CTRL] Step {event.get('step'):>3}/{MAX_STEPS} "
                        f"[{status_char}] {action[:40]} | {target[:40]}..."
                    )

                    # Track recent actions for repetition detection
                    recent_actions.append((action, target[:40]))
                    if len(recent_actions) > 10:
                        recent_actions.pop(0)
                    if guidance_cooldown > 0:
                        guidance_cooldown -= 1

                    # B3: count executarPipelineCompleto triggers
                    if "executarPipelineCompleto" in (action + " " + target + " " + thought) and success:
                        pipeline_trigger_count += 1
                        print(f"[CTRL] PIPELINE TRIGGER #{pipeline_trigger_count} detected")
                    phase_state = advance_phase_state(
                        phase_state,
                        has_seen_step=True,
                        pipeline_trigger_count=pipeline_trigger_count,
                    )
                    if success and not is_action_allowed_in_phase(
                        phase_state,
                        action=action,
                        target=target,
                        thought=thought,
                    ):
                        phase_state = PHASE_BLOCKED
                        stop_reason = (
                            f"Phase lockout violation: '{action}' is not allowed after validation started."
                        )
                        print(f"[CTRL] PHASE LOCKOUT: {stop_reason}")
                        send_command(commands_path, "stop", {"reason": stop_reason})
                    if action == "download_file" and success:
                        download_event_count += 1
                        validation_signal_count += 1
                    if action == "read_page_text" and success:
                        validation_signal_count += 1
                    if "desempenho" in text and success:
                        desempenho_signal_count += 1

                elif etype == "stuck":
                    stuck_pending = True
                    print(
                        f"[CTRL] STUCK: {event.get('action_type')} on '{event.get('target')}'"
                    )

                elif etype == "paused":
                    step = event.get("step", "?")
                    phase_state = advance_phase_state(
                        phase_state,
                        has_seen_step=False,
                        pipeline_trigger_count=pipeline_trigger_count,
                    )

                    # Detect repetition-based stuck: same action_type 5+ times in last 8 steps
                    # Excludes "scroll" (normal page exploration) and single-shot actions
                    repetition_stuck = False
                    reload_stuck = False
                    no_progress_stuck = False
                    if guidance_cooldown == 0:
                        action_types = [a for a, _ in recent_actions[-8:]]
                        non_scroll = [a for a in action_types if a not in ("scroll", "wait")]
                        # B2: Exempt first 10 steps — Phase 1 navigation uses 4+ evaluate_js calls
                        if step_count > 10 and len(non_scroll) >= 5:
                            most_common = max(set(non_scroll), key=non_scroll.count)
                            if non_scroll.count(most_common) >= 5:
                                repetition_stuck = True
                                stuck_action_type = most_common
                                print(f"[CTRL] REPEAT-STUCK: '{stuck_action_type}' x{non_scroll.count(most_common)} in last 8 steps")

                        # Detect reload in recent actions (harmful in SPA)
                        if action_types and action_types[-1] == "reload":
                            reload_stuck = True
                            print("[CTRL] RELOAD-STUCK: agent just reloaded (harmful in SPA)")

                        # No-progress stuck: 80+ steps with 0 pipeline triggers
                        if step_count >= 80 and pipeline_trigger_count == 0:
                            no_progress_stuck = True
                            print(f"[CTRL] NO-PROGRESS: {step_count} steps with 0 pipeline triggers")

                    # B3: Inject Phase 3 guidance when all 4 pipelines have been triggered
                    if phase_state == PHASE_VALIDATE and not phase3_injected:
                        phase3_injected = True
                        phase3_instruction = (
                            "PHASE 3 — All 4 pipeline triggers detected. Now download and validate:\n"
                            "1. Locate the Documentos da Atividade section on the page.\n"
                            "2. Use download_file for each PDF report and JSON output available.\n"
                            "3. For each JSON file downloaded, verify it contains: questao_id, nota, habilidades.\n"
                            "4. Check that desempenho cascade reports exist at tarefa, turma, and materia levels.\n"
                            "5. If desempenho reports are missing, report what was found instead.\n"
                            "IMPORTANT: Do NOT trigger any more pipelines. Download and inspect outputs only."
                        )
                        phase3_instruction = build_phase3_instruction(models=ACTIVE_MODELS)
                        send_command(commands_path, "guidance", {"instruction": phase3_instruction})
                        print(f"[CTRL] PHASE 3 guidance injected - all {EXPECTED_PIPELINE_TRIGGER_COUNT} requested pipelines triggered")

                    if stuck_pending or repetition_stuck or reload_stuck or no_progress_stuck:
                        if reload_stuck:
                            instruction = (
                                "STOP! Do NOT reload the page. Reloading in this SPA takes you back "
                                "to the home screen, losing all navigation progress. "
                                "If you just reloaded, the page is now back to home. "
                                "Navigate again using evaluate_js (NOT clicks):\n"
                                "  evaluate_js: showMateria('f95445ace30e7dc5') → wait 5s\n"
                                "  evaluate_js: showTurma('6b5dc44c08aaf375') → wait 8s\n"
                                "  evaluate_js: showAtividade('effad48d128c7083') → wait 5s\n"
                                "Console 404 errors are NORMAL background API calls — they are NOT "
                                "a reason to reload. Ignore them and continue navigating."
                            )
                        elif repetition_stuck:
                            instruction = (
                                f"STOP! You've been repeating '{stuck_action_type}' actions with no progress. "
                                "IMPORTANT: Look at the current screenshot carefully.\n"
                                "If you see pipeline buttons (Executar Etapa, Pipeline Aluno, Pipeline Todos os Alunos): "
                                "you are ALREADY on the A1 atividade page! Stop re-navigating. "
                                "Use evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma'), "
                                "wait 2s, select the model from the dropdown, "
                                "then evaluate_js → executarPipelineCompleto(). "
                                "NEVER click the Executar button directly — always call executarPipelineCompleto() via evaluate_js.\n"
                                "If you do NOT see pipeline buttons: re-navigate using evaluate_js:\n"
                                "  evaluate_js: showMateria('f95445ace30e7dc5') → wait 5s\n"
                                "  evaluate_js: showTurma('6b5dc44c08aaf375') → wait 8s\n"
                                "  evaluate_js: showAtividade('effad48d128c7083') → wait 5s"
                            )
                        elif no_progress_stuck:
                            instruction = (
                                f"After {step_count} steps, no pipeline verification has started. "
                                "Navigate directly using evaluate_js:\n"
                                "  Step 1: evaluate_js: showMateria('f95445ace30e7dc5') → then wait 5 seconds\n"
                                "  Step 2: evaluate_js: showTurma('6b5dc44c08aaf375') → then wait 8 seconds\n"
                                "  Step 3: evaluate_js: showAtividade('effad48d128c7083') → then wait 5 seconds\n"
                                "After step 3 you should see the A1 atividade page with pipeline controls. "
                                "DO NOT use click for navigation. DO NOT reload."
                            )
                        else:
                            instruction = (
                                "You seem stuck. Are you on the A1 atividade page? "
                                "If YES: run evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma'), "
                                "wait 2s, select gpt-4o from dropdown, "
                                "then evaluate_js → executarPipelineCompleto(), then wait 90s. "
                                "If NO: navigate → showMateria('f95445ace30e7dc5') → showTurma('6b5dc44c08aaf375') "
                                "→ showAtividade('effad48d128c7083'). "
                                "NEVER reload. NEVER click the Executar button — always use evaluate_js instead."
                            )
                        send_command(commands_path, "guidance", {"instruction": instruction})
                        stuck_pending = False
                        guidance_cooldown = 6  # Don't send guidance again for 6 steps
                        recent_actions.clear()
                        no_progress_stuck = False
                    else:
                        send_command(commands_path, "continue")

                elif etype in ("complete", "journey_complete", "gave_up", "stopped", "journey_stopped", "error"):
                    phase_state = advance_phase_state(
                        phase_state,
                        has_seen_step=False,
                        pipeline_trigger_count=pipeline_trigger_count,
                        terminal_event=etype,
                    )
                    print(f"\n[CTRL] Journey ended: {etype}")
                    print(f"[CTRL] Total steps completed: {step_count}")
                    print(f"[CTRL] Pipeline triggers detected: {pipeline_trigger_count}")
                    print(f"[CTRL] Phase 3 injected: {phase3_injected}")
                    phase3_summary = write_phase3_validation_artifacts(ipc_dir, verification_report)
                    resolve_verification_report(
                        verification_report,
                        phase3_summary,
                        terminal_event=etype,
                        phase_state=phase_state,
                    )
                    append_run_observation(
                        verification_report,
                        "Controller Summary",
                        build_automated_run_observation_lines(
                            terminal_event=etype,
                            step_count=step_count,
                            pipeline_trigger_count=pipeline_trigger_count,
                            phase3_injected=phase3_injected,
                            download_event_count=download_event_count,
                            validation_signal_count=validation_signal_count,
                            desempenho_signal_count=desempenho_signal_count,
                            phase_state=phase_state,
                            phase3_artifact_status=phase3_summary.get("overall_status"),
                            terminal_reason=event.get("reason") or event.get("error"),
                        ),
                    )
                    update_summary(verification_report)
                    final_state = {
                        "phase3_summary": phase3_summary,
                        "terminal_event": etype,
                        "phase_state": phase_state,
                    }
                    running = False
                    break

            time.sleep(0.3)

        except KeyboardInterrupt:
            print("\n[CTRL] Interrupted by user. Sending stop command...")
            send_command(commands_path, "stop", {"reason": "User interrupted controller"})
            phase_state = advance_phase_state(
                phase_state,
                has_seen_step=False,
                pipeline_trigger_count=pipeline_trigger_count,
                terminal_event="controller_interrupted",
            )
            phase3_summary = write_phase3_validation_artifacts(ipc_dir, verification_report)
            resolve_verification_report(
                verification_report,
                phase3_summary,
                terminal_event="controller_interrupted",
                phase_state=phase_state,
            )
            append_run_observation(
                verification_report,
                "Controller Summary",
                build_automated_run_observation_lines(
                    terminal_event="controller_interrupted",
                    step_count=step_count,
                    pipeline_trigger_count=pipeline_trigger_count,
                    phase3_injected=phase3_injected,
                    download_event_count=download_event_count,
                    validation_signal_count=validation_signal_count,
                    desempenho_signal_count=desempenho_signal_count,
                    phase_state=phase_state,
                    phase3_artifact_status=phase3_summary.get("overall_status"),
                    terminal_reason="User interrupted controller",
                ),
            )
            update_summary(verification_report)
            running = False
            final_state = {
                "phase3_summary": phase3_summary,
                "terminal_event": "controller_interrupted",
                "phase_state": phase_state,
            }

    return final_state


# ---------------------------------------------------------------------------
# Entry point — start agent and controller together
# ---------------------------------------------------------------------------


def warmup_server(url: str, max_attempts: int = 5) -> bool:
    """Pre-warm the Render server to avoid cold-start errors during the run."""
    print(f"[CTRL] Pre-warming server: {url}/api/materias ...")
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.urlopen(f"{url}/api/materias", timeout=30)
            data = req.read()
            if b"materias" in data:
                print(f"[CTRL] Server warm! (attempt {attempt})")
                return True
        except Exception as e:
            print(f"[CTRL] Warmup attempt {attempt}/{max_attempts} failed: {e}")
            time.sleep(5)
    print("[CTRL] WARNING: Server may still be cold — proceeding anyway")
    return False


def main():
    parser = argparse.ArgumentParser(description="Run the F10 journey-agent verification controller.")
    parser.add_argument(
        "--active-models",
        default=",".join(MODELS),
        help="Comma-separated model ids to request during the run.",
    )
    parser.add_argument(
        "--expected-blocked-models",
        default="",
        help="Comma-separated requested model ids that are expected to remain blocked in this proof run.",
    )
    args = parser.parse_args()

    active_models = _parse_model_scope_arg(args.active_models)
    expected_blocked_models = _parse_model_scope_arg(args.expected_blocked_models)
    if not active_models:
        parser.error("--active-models must contain at least one valid model.")
    invalid_blocked = [model for model in expected_blocked_models if model not in active_models]
    if invalid_blocked:
        parser.error(
            "--expected-blocked-models must be a subset of --active-models. "
            f"Invalid values: {', '.join(invalid_blocked)}"
        )

    configure_model_scope(active_models, expected_blocked_models)
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    # Pre-warm the Render server to avoid cold-start errors in the agent
    warmup_server(LIVE_URL)

    # Build agent command
    cmd = [
        sys.executable, "-m", AGENT_MODULE,
        "--persona", PERSONA,
        "--viewport", VIEWPORT,
        "--pause-mode",
        "--no-headless",
        "--max-steps", str(MAX_STEPS),
        "--url", LIVE_URL,
        "--output", str(OUTPUT_BASE),
        "--no-open",
        "--no-narrate",
        "--goal", GOAL,
    ]

    print("=" * 60)
    print("F10-T1: VERIFICATION SUITE OUTER LOOP CONTROLLER")
    print("=" * 60)
    print(f"Persona:  {PERSONA}")
    print(f"Viewport: {VIEWPORT}")
    print(f"Max steps: {MAX_STEPS}")
    print(f"URL: {LIVE_URL}")
    print(f"Requested models: {', '.join(ACTIVE_MODELS)}")
    print(
        "Expected blocked models: "
        + (", ".join(EXPECTED_BLOCKED_MODELS) or "none")
    )
    print("=" * 60)
    print("\nStarting agent...")

    # Start agent subprocess
    proc = subprocess.Popen(
        cmd,
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    # Read first lines to get IPC_DIR
    ipc_dir = None
    for _ in range(30):  # Wait up to 15 seconds for IPC_DIR
        line = proc.stdout.readline()
        if line:
            print(f"[AGENT] {line.rstrip()}")
            if line.startswith("IPC_DIR="):
                ipc_dir_str = line.strip().removeprefix("IPC_DIR=")
                ipc_dir = BACKEND_DIR / ipc_dir_str
                break
        time.sleep(0.5)

    if not ipc_dir:
        print("[CTRL] ERROR: Could not get IPC_DIR from agent. Killing process.")
        proc.terminate()
        sys.exit(1)

    print(f"\n[CTRL] IPC directory: {ipc_dir}")
    verification_report = initialize_run_artifacts(ipc_dir)
    print(f"[CTRL] Verification report initialized: {verification_report}")

    # Pre-inject startup guidance into commands.jsonl before the agent's first pause.
    # This tells the agent to use evaluate_js for navigation (avoids click resolution issues).
    commands_path = ipc_dir / "commands.jsonl"
    ipc_dir.mkdir(parents=True, exist_ok=True)
    startup_instruction = (
        "STARTUP INSTRUCTIONS — follow exactly:\n"
        "Step 1: If you see 'Bem-vindo ao NOVO CR' modal → evaluate_js: closeWelcome()\n"
        "Step 2: evaluate_js → showMateria('f95445ace30e7dc5') — wait 5s\n"
        "Step 3: evaluate_js → showTurma('6b5dc44c08aaf375') — wait 8s\n"
        "Step 4: evaluate_js → showAtividade('effad48d128c7083') — wait 5s\n"
        "Step 5: evaluate_js → openModalPipelineCompleto('effad48d128c7083', 'turma') — wait 2s\n"
        "Step 6: select_option → pick the gpt-4o option from the Modelo de IA dropdown\n"
        "Step 7: evaluate_js → executarPipelineCompleto()\n"
        "Step 8: wait 90 seconds (wait_duration_seconds=90)\n"
        "Step 9: Repeat steps 5-8 for gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview\n"
        "CRITICAL: Do NOT click any button to trigger the pipeline. "
        "Use evaluate_js → executarPipelineCompleto() instead. "
        "Do NOT scroll the main page looking for a model dropdown. "
        "The model dropdown only exists INSIDE the modal (step 6)."
    )
    startup_instruction = build_controller_startup_guidance()
    send_command(commands_path, "guidance", {"instruction": startup_instruction})
    print("[CTRL] Startup guidance pre-injected into commands.jsonl")

    # Print remaining agent startup output in a background thread
    import threading

    def print_agent_output():
        for line in proc.stdout:
            if line.strip():
                print(f"[AGENT] {line.rstrip()}")

    thread = threading.Thread(target=print_agent_output, daemon=True)
    thread.start()

    # Wait for events.jsonl to appear
    events_path = ipc_dir / "events.jsonl"
    print("[CTRL] Waiting for first event...")
    for _ in range(60):
        if events_path.exists():
            break
        time.sleep(0.5)

    # Run the outer loop
    final_state = {"phase3_summary": None}
    try:
        final_state = run_controller(ipc_dir, verification_report)
    finally:
        # Wait for agent to finish
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.terminate()

    persist_proof_scope_metadata(ipc_dir, final_state.get("phase3_summary"))

    print("\n[CTRL] Verification run complete.")
    print(f"[CTRL] Report: {verification_report}")
    print(f"[CTRL] IPC dir: {ipc_dir}")


if __name__ == "__main__":
    main()
