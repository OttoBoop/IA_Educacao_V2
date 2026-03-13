"""Tests for controller-facing Phase 3 artifact validation."""

import json
from pathlib import Path
from uuid import uuid4

from tests.ui.investor_journey_agent.pipeline_verification import (
    evaluate_downloaded_artifacts,
)


def _workspace_tmp(name: str) -> Path:
    """Create a writable scratch directory inside the repo workspace."""
    path = Path(__file__).resolve().parents[3] / ".pytest_tmp" / name / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_pdf(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n" + (b"x" * size))


def test_missing_downloads_reports_missing_downloads_status():
    downloads_dir = _workspace_tmp("phase3_runtime_missing") / "downloads"

    summary = evaluate_downloaded_artifacts(downloads_dir)

    assert summary["overall_status"] == "missing_downloads"
    assert summary["counts"]["json"] == 0
    assert summary["counts"]["pdf"] == 0
    assert summary["coverage"]["complete_stage_count"] == 0


def test_downloaded_artifacts_validate_all_stages_but_keep_model_scope_unverified():
    downloads_dir = _workspace_tmp("phase3_runtime_complete") / "downloads"

    _write_json(
        downloads_dir / "extracao_questoes_output.json",
        {"questoes": [], "total_questoes": 0, "pontuacao_total": 10},
    )
    _write_pdf(downloads_dir / "extracao_questoes_output.pdf", 1500)

    _write_json(
        downloads_dir / "correcao_output.json",
        {"alunos": [], "notas": {}, "gabarito": {}},
    )
    _write_pdf(downloads_dir / "correcao_output.pdf", 2500)

    _write_json(
        downloads_dir / "analise_habilidades_output.json",
        {"habilidades": [], "analise": {}},
    )
    _write_pdf(downloads_dir / "analise_habilidades_output.pdf", 2500)

    _write_json(
        downloads_dir / "relatorio_final_output.json",
        {"relatorio": "ok", "resumo": "ok"},
    )
    _write_pdf(downloads_dir / "relatorio_final_output.pdf", 6000)

    _write_json(
        downloads_dir / "desempenho" / "tarefa" / "relatorio_desempenho_tarefa.json",
        {"habilidades": {"dominio": ["fractions"]}},
    )
    _write_pdf(
        downloads_dir / "desempenho" / "tarefa" / "relatorio_desempenho_tarefa.pdf",
        1500,
    )
    _write_json(
        downloads_dir / "desempenho" / "turma" / "relatorio_desempenho_turma.json",
        {"habilidades": {"dominio": ["algebra"]}},
    )
    _write_pdf(
        downloads_dir / "desempenho" / "turma" / "relatorio_desempenho_turma.pdf",
        1500,
    )
    _write_json(
        downloads_dir / "desempenho" / "materia" / "relatorio_desempenho_materia.json",
        {"habilidades": {"dominio": ["geometry"]}},
    )
    _write_pdf(
        downloads_dir / "desempenho" / "materia" / "relatorio_desempenho_materia.pdf",
        1500,
    )

    summary = evaluate_downloaded_artifacts(downloads_dir)

    assert summary["validation"]["valid"] is True
    assert summary["coverage"]["missing_stages"] == []
    assert summary["coverage"]["complete_stage_count"] == 4
    assert summary["overall_status"] == "unverified_model_scope"
    assert summary["stage_artifacts"]["corrigir"]["status"] == "pass"
    assert summary["desempenho"]["tarefa"]["json"] is True
    assert summary["desempenho"]["turma"]["pdf"] is True
    assert summary["desempenho_report_content"]["status"] == "pass"


def test_stage_can_be_inferred_from_json_content_and_paired_pdf():
    downloads_dir = _workspace_tmp("phase3_runtime_inference") / "downloads"

    _write_json(
        downloads_dir / "artifact_01.json",
        {"questoes": [{"numero": 1}], "total_questoes": 1, "pontuacao_total": 10},
    )
    _write_pdf(downloads_dir / "artifact_01.pdf", 1500)

    summary = evaluate_downloaded_artifacts(downloads_dir)
    stage = summary["stage_artifacts"]["extrair_questoes"]

    assert stage["json_stage_source"] == "content"
    assert stage["pdf_stage_source"] == "paired_stem"
    assert stage["status"] == "pass"


def test_manifest_backed_model_coverage_can_confirm_all_models():
    downloads_dir = _workspace_tmp("phase3_runtime_manifest") / "downloads"
    manifest_path = downloads_dir.parent / "artifact_manifest.jsonl"
    manifest_lines = []

    stage_payloads = {
        "extracao_questoes": ({"questoes": [], "total_questoes": 0, "pontuacao_total": 10}, 1500),
        "correcao": ({"alunos": [], "notas": {}, "gabarito": {}}, 2500),
        "analise_habilidades": ({"habilidades": [], "analise": {}}, 2500),
        "relatorio_final": ({"relatorio": "ok", "resumo": "ok"}, 6000),
    }

    for model in (
        "gpt-4o",
        "gpt-5-nano",
        "claude-haiku-4-5-20251001",
        "gemini-3-flash-preview",
    ):
        manifest_lines.append(json.dumps({
            "event_type": "pipeline_trigger",
            "model_context": model,
        }))
        for stage_name, (payload, pdf_size) in stage_payloads.items():
            stem = f"run_{stage_name}_{model.replace('-', '_')}"
            json_path = downloads_dir / f"{stem}.json"
            pdf_path = downloads_dir / f"{stem}.pdf"
            _write_json(json_path, payload)
            _write_pdf(pdf_path, pdf_size)
            manifest_lines.append(json.dumps({
                "event_type": "download_saved",
                "saved_path": str(json_path),
                "model_context": model,
            }))
            manifest_lines.append(json.dumps({
                "event_type": "download_saved",
                "saved_path": str(pdf_path),
                "model_context": model,
            }))

    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    summary = evaluate_downloaded_artifacts(downloads_dir, manifest_path=manifest_path)

    assert summary["triggered_models"] == [
        "gpt-4o",
        "gpt-5-nano",
        "claude-haiku-4-5-20251001",
        "gemini-3-flash-preview",
    ]
    assert summary["downloads_with_explicit_model"] == 32
    assert summary["model_scope_confirmed"] is True
    assert summary["overall_status"] == "validated"
    assert summary["model_coverage"]["gpt-4o"]["complete_stage_count"] == 4


def test_downloads_are_normalized_into_model_stage_student_hierarchy():
    downloads_dir = _workspace_tmp("phase3_runtime_normalized") / "downloads"
    incoming_dir = downloads_dir / "_incoming"
    manifest_path = downloads_dir.parent / "artifact_manifest.jsonl"

    json_path = incoming_dir / "extracao_questoes_gpt4o.json"
    pdf_path = incoming_dir / "extracao_questoes_gpt4o.pdf"
    _write_json(json_path, {"questoes": [], "total_questoes": 0, "pontuacao_total": 10})
    _write_pdf(pdf_path, 1500)
    manifest_path.write_text(
        "\n".join(
            [
                json.dumps({
                    "event_type": "pipeline_trigger",
                    "model_context": "gpt-4o",
                }),
                json.dumps({
                    "event_type": "download_saved",
                    "saved_path": str(json_path),
                    "model_context": "gpt-4o",
                }),
                json.dumps({
                    "event_type": "download_saved",
                    "saved_path": str(pdf_path),
                    "model_context": "gpt-4o",
                }),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    summary = evaluate_downloaded_artifacts(downloads_dir, manifest_path=manifest_path)

    expected_json = downloads_dir / "gpt-4o" / "extrair_questoes" / "_shared" / "extracao_questoes_gpt4o.json"
    expected_pdf = downloads_dir / "gpt-4o" / "extrair_questoes" / "_shared" / "extracao_questoes_gpt4o.pdf"
    assert expected_json.exists()
    assert expected_pdf.exists()
    assert summary["normalization"]["normalized_file_count"] >= 2
    assert summary["normalized_download_entries"] >= 2
    assert "gpt-4o" in summary["stage_artifacts"]["extrair_questoes"]["json_path"]


def test_expected_blocked_models_do_not_prevent_scoped_validation():
    downloads_dir = _workspace_tmp("phase3_runtime_expected_blocked") / "downloads"
    manifest_path = downloads_dir.parent / "artifact_manifest.jsonl"
    manifest_lines = []

    stage_payloads = {
        "extracao_questoes": ({"questoes": [], "total_questoes": 0, "pontuacao_total": 10}, 1500),
        "correcao": ({"alunos": [], "notas": {}, "gabarito": {}}, 2500),
        "analise_habilidades": ({"habilidades": [], "analise": {}}, 2500),
        "relatorio_final": ({"relatorio": "ok", "resumo": "ok"}, 6000),
    }

    runnable_models = (
        "gpt-4o",
        "gpt-5-nano",
        "gemini-3-flash-preview",
    )
    for model in runnable_models:
        manifest_lines.append(json.dumps({
            "event_type": "pipeline_trigger",
            "model_context": model,
        }))
        for stage_name, (payload, pdf_size) in stage_payloads.items():
            stem = f"run_{stage_name}_{model.replace('-', '_')}"
            json_path = downloads_dir / f"{stem}.json"
            pdf_path = downloads_dir / f"{stem}.pdf"
            _write_json(json_path, payload)
            _write_pdf(pdf_path, pdf_size)
            manifest_lines.append(json.dumps({
                "event_type": "download_saved",
                "saved_path": str(json_path),
                "model_context": model,
            }))
            manifest_lines.append(json.dumps({
                "event_type": "download_saved",
                "saved_path": str(pdf_path),
                "model_context": model,
            }))

    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="utf-8")

    summary = evaluate_downloaded_artifacts(
        downloads_dir,
        manifest_path=manifest_path,
        requested_models=[
            "gpt-4o",
            "gpt-5-nano",
            "claude-haiku-4-5-20251001",
            "gemini-3-flash-preview",
        ],
        expected_blocked_models=["claude-haiku-4-5-20251001"],
    )

    assert summary["model_scope_confirmed"] is True
    assert summary["overall_status"] == "validated_with_expected_blockers"
    assert summary["b5_eligible"] is False
    assert summary["missing_trigger_models"] == []
    assert summary["model_status"]["claude-haiku-4-5-20251001"]["status"] == "expected_blocked"
    assert summary["model_status"]["gpt-4o"]["status"] == "validated"
