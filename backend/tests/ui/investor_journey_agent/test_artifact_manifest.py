"""Tests for per-run artifact manifest generation in the journey agent."""

import json
from pathlib import Path
from uuid import uuid4

from tests.ui.investor_journey_agent.agent import InvestorJourneyAgent
from tests.ui.investor_journey_agent.config import AgentConfig
from tests.ui.investor_journey_agent.llm_brain import Action, ActionType, JourneyStep


def _workspace_tmp(name: str) -> Path:
    """Create a writable scratch directory inside the repo workspace."""
    path = Path(__file__).resolve().parents[3] / ".pytest_tmp" / name / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _make_step(step_number: int, action: Action) -> JourneyStep:
    return JourneyStep(
        step_number=step_number,
        url="https://example.com",
        screenshot_path=f"screenshots/step_{step_number:02d}.png",
        action=action,
        success=True,
        error_message=None,
    )


def test_agent_writes_model_selection_trigger_and_download_manifest_entries():
    run_dir = _workspace_tmp("artifact_manifest_agent")
    manifest_path = run_dir / "artifact_manifest.jsonl"
    agent = InvestorJourneyAgent(
        persona="investor",
        viewport="desktop",
        config=AgentConfig(anthropic_api_key="test-key"),
    )
    agent._artifact_manifest_path = manifest_path
    agent._selected_model = None
    agent._triggered_models = []

    select_action = Action(
        action_type=ActionType.SELECT_OPTION,
        target="Modelo de IA dropdown",
        thought="Pick gpt-4o in the modal",
        frustration_level=0.1,
        confidence=0.9,
        select_value="gpt-4o",
    )
    agent._last_action_result = {"selected_value": "gpt-4o"}
    agent._record_step_artifact_event(_make_step(1, select_action))

    trigger_action = Action(
        action_type=ActionType.EVALUATE_JS,
        target="Pipeline modal trigger",
        thought="Run the full pipeline for the selected model",
        frustration_level=0.1,
        confidence=0.9,
        eval_script="executarPipelineCompleto()",
    )
    agent._last_action_result = {"eval_script": "executarPipelineCompleto()"}
    agent._record_step_artifact_event(_make_step(2, trigger_action))

    download_path = run_dir / "downloads" / "gpt-4o_relatorio_final.pdf"
    download_path.parent.mkdir(parents=True, exist_ok=True)
    download_path.write_bytes(b"%PDF")
    download_action = Action(
        action_type=ActionType.DOWNLOAD_FILE,
        target="Download gpt-4o relatorio final PDF",
        thought="Save the gpt-4o report locally",
        frustration_level=0.1,
        confidence=0.9,
    )
    agent._last_action_result = {
        "download_path": str(download_path),
        "download_filename": download_path.name,
    }
    agent._record_step_artifact_event(_make_step(3, download_action))

    entries = [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert [entry["event_type"] for entry in entries] == [
        "model_selected",
        "pipeline_trigger",
        "download_saved",
    ]
    assert entries[1]["model_context"] == "gpt-4o"
    assert entries[1]["triggered_models_so_far"] == ["gpt-4o"]
    assert entries[2]["model_context"] == "gpt-4o"
    assert entries[2]["saved_filename"] == "gpt-4o_relatorio_final.pdf"
