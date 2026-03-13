"""
F6-T4: Pipeline Verification — Integration module.

Combines scenario.py, validation_rules.py, and cascade_steps.py into a unified
verification orchestrator for the journey agent.

Exports:
- build_verification_goal()          -> str
- build_runtime_goal(...)            -> str
- build_startup_instruction(...)     -> str
- build_phase3_instruction()         -> str
- build_full_checklist()             -> list[dict]
- validate_pipeline_outputs(outputs) -> dict
- generate_verification_report(results) -> str
"""

import json
import re
import shutil
import unicodedata
from pathlib import Path

from .scenario import MODELS, PIPELINE_STAGES, VERIFICATION_GOAL, CHECKLIST
from .validation_rules import STAGE_RULES, validate_stage_output
from .cascade_steps import CASCADE_STEPS


_STAGE_FILENAME_ALIASES = {
    "extrair_questoes": ("extrair_questoes", "extracao_questoes", "questoes_extraidas"),
    "corrigir": ("corrigir", "correcao"),
    "analisar_habilidades": ("analisar_habilidades", "analise_habilidades"),
    "gerar_relatorio": ("gerar_relatorio", "relatorio_final"),
}

_STAGE_JSON_HINTS = {
    "extrair_questoes": ("questoes", "total_questoes", "pontuacao_total"),
    "corrigir": ("alunos", "notas", "gabarito", "nota", "feedback", "correcoes", "status"),
    "analisar_habilidades": ("habilidades", "analise", "recomendacoes", "pontos_fortes", "resumo_desempenho"),
    "gerar_relatorio": ("relatorio", "resumo", "conteudo", "resumo_executivo", "nota_final"),
}

_SOURCE_RANK = {"filename": 3, "content": 2, "paired_stem": 1, None: 0}


def _stage_field_lines() -> list[str]:
    """Return shared per-stage JSON field expectations."""
    return [
        f"- {stage_name}: {', '.join(rule['expected_json_fields'])}"
        for stage_name, rule in STAGE_RULES.items()
    ]


def _cascade_level_lines() -> list[str]:
    """Return shared cascade verification summaries."""
    return [
        f"- {step['step_id']}: {step['level']} -> {step['verify']}"
        for step in CASCADE_STEPS
    ]


def build_verification_goal() -> str:
    """Build a comprehensive goal string for the journey agent's --goal flag.

    Combines VERIFICATION_GOAL with model names, pipeline stages, checklist
    summary, and desempenho cascade references.
    """
    models_str = ", ".join(MODELS)
    stages_str = ", ".join(PIPELINE_STAGES)

    checklist_summary = "\n".join(
        f"  - [{item['category']}] {item['description']}" for item in CHECKLIST
    )

    cascade_summary = "\n".join(
        f"  - {step['step_id']}: {step['action']}" for step in CASCADE_STEPS
    )

    return (
        f"{VERIFICATION_GOAL}\n\n"
        f"Models: {models_str}\n"
        f"Pipeline stages: {stages_str}\n\n"
        f"Checklist:\n{checklist_summary}\n\n"
        f"Desempenho cascade verification:\n{cascade_summary}"
    )


def _normalize_model_scope(
    requested_models: list[str] | None = None,
    expected_blocked_models: list[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Return a validated, de-duplicated model scope for a proof run."""
    if requested_models:
        seen = set()
        resolved_requested = []
        for model in requested_models:
            if model in MODELS and model not in seen:
                seen.add(model)
                resolved_requested.append(model)
    else:
        resolved_requested = list(MODELS)

    expected_blocked = []
    seen_blocked = set()
    for model in expected_blocked_models or []:
        if model in resolved_requested and model not in seen_blocked:
            seen_blocked.add(model)
            expected_blocked.append(model)

    return resolved_requested, expected_blocked


def _normalize_token(value: str) -> str:
    """Normalize filenames and keys for resilient matching."""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().replace("-", "_")
    return re.sub(r"[^a-z0-9_]+", "_", normalized).strip("_")


def _infer_stage_from_name(name: str) -> tuple[str | None, str | None]:
    """Infer a scenario stage from a filename or path fragment."""
    normalized = _normalize_token(name)
    if not normalized or "desempenho" in normalized:
        return None, None

    best_stage = None
    best_score = 0
    for stage, aliases in _STAGE_FILENAME_ALIASES.items():
        for alias in aliases:
            alias_token = _normalize_token(alias)
            if alias_token and alias_token in normalized:
                score = len(alias_token)
                if score > best_score:
                    best_stage = stage
                    best_score = score
    if best_stage:
        return best_stage, "filename"
    return None, None


def _infer_stage_from_json(data: dict) -> tuple[str | None, str | None]:
    """Infer a scenario stage from top-level JSON keys."""
    if not isinstance(data, dict):
        return None, None

    keys = {_normalize_token(key) for key in data.keys()}
    best_stage = None
    best_score = 0
    for stage, hints in _STAGE_JSON_HINTS.items():
        score = sum(1 for hint in hints if _normalize_token(hint) in keys)
        if score > best_score:
            best_stage = stage
            best_score = score
    if best_stage and best_score > 0:
        return best_stage, "content"
    return None, None


def _infer_models_from_text(value: str) -> list[str]:
    """Infer model names from a filename or metadata string."""
    normalized = _normalize_token(value)
    compact = normalized.replace("_", "")
    matches = []
    for model in MODELS:
        alias = _normalize_token(model)
        if alias in normalized or alias.replace("_", "") in compact:
            matches.append(model)
    return matches


def _recursive_values(data, target_key: str) -> list[str]:
    """Collect recursive values for a normalized JSON key."""
    results = []
    normalized_target = _normalize_token(target_key)

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if _normalize_token(str(key)) == normalized_target:
                    if isinstance(value, str) and value.strip():
                        results.append(value.strip())
                    elif isinstance(value, (int, float)):
                        results.append(str(value))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return results


def _contains_recursive_key(data, target_key: str) -> bool:
    """Return True if a key appears anywhere inside the JSON structure."""
    normalized_target = _normalize_token(target_key)

    def walk(node) -> bool:
        if isinstance(node, dict):
            for key, value in node.items():
                if _normalize_token(str(key)) == normalized_target:
                    return True
                if walk(value):
                    return True
        elif isinstance(node, list):
            for item in node:
                if walk(item):
                    return True
        return False

    return walk(data)


def _infer_desempenho_level(value: str) -> str | None:
    normalized = _normalize_token(value)
    for level in ("tarefa", "turma", "materia"):
        if level in normalized:
            return level
    return None


def _infer_student_name(data: dict) -> str | None:
    """Best-effort student-name extraction for download normalization."""
    if not isinstance(data, dict):
        return None

    candidate_keys = ("aluno", "aluno_nome", "nome_aluno", "student_name")
    names = []
    for key in candidate_keys:
        names.extend(_recursive_values(data, key))

    normalized = []
    seen = set()
    for name in names:
        token = _normalize_token(name)
        if token and token not in seen:
            seen.add(token)
            normalized.append(name.strip())

    if len(normalized) == 1:
        return normalized[0]
    return None


def _next_available_artifact_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    counter = 2
    while True:
        candidate = path.with_name(f"{stem}_{counter}{suffix}")
        if not candidate.exists():
            return candidate
        counter += 1


def _is_normalized_download_path(relative: Path) -> bool:
    parts = list(relative.parts)
    if not parts:
        return False
    if parts[0] == "desempenho" and len(parts) >= 3 and parts[1] in ("tarefa", "turma", "materia"):
        return True
    if len(parts) >= 4 and (
        parts[0] in MODELS or parts[0] == "_unverified_model"
    ) and (
        parts[1] in PIPELINE_STAGES or parts[1] == "_unknown_stage"
    ):
        return True
    return False


def _append_manifest_line(manifest_path: Path | None, entry: dict) -> None:
    if manifest_path is None:
        return
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _record_stage_json(
    stage_records: dict,
    *,
    stage: str,
    path: Path,
    stage_source: str | None,
    data: dict,
    parse_error: str | None,
    model_hits: list[str],
) -> None:
    """Store the best JSON artifact candidate for a stage."""
    record = stage_records[stage]
    new_rank = _SOURCE_RANK.get(stage_source, 0)
    new_size = path.stat().st_size if path.exists() else 0
    current_rank = record.get("_json_rank", 0)
    current_size = record.get("_json_size", -1)

    if new_rank > current_rank or (new_rank == current_rank and new_size >= current_size):
        record["_json_rank"] = new_rank
        record["_json_size"] = new_size
        record["_json_data"] = data if isinstance(data, dict) else {}
        record["json_path"] = str(path)
        record["json_stage_source"] = stage_source
        record["json_top_level_keys"] = sorted(data.keys()) if isinstance(data, dict) else []
        record["json_parse_error"] = parse_error

    record["_model_hits"].update(model_hits)


def _record_stage_pdf(
    stage_records: dict,
    *,
    stage: str,
    path: Path,
    stage_source: str | None,
    model_hits: list[str],
) -> None:
    """Store the best PDF artifact candidate for a stage."""
    record = stage_records[stage]
    new_rank = _SOURCE_RANK.get(stage_source, 0)
    new_size = path.stat().st_size if path.exists() else 0
    current_rank = record.get("_pdf_rank", 0)
    current_size = record.get("pdf_size", -1)

    if new_rank > current_rank or (new_rank == current_rank and new_size >= current_size):
        record["_pdf_rank"] = new_rank
        record["pdf_path"] = str(path)
        record["pdf_stage_source"] = stage_source
        record["pdf_size"] = new_size

    record["_model_hits"].update(model_hits)


def _evaluate_origem_id_chain(stage_records: dict) -> dict:
    """Best-effort origem_id chain check across the pipeline JSON stages."""
    required = ("extrair_questoes", "corrigir", "analisar_habilidades")
    missing = [stage for stage in required if not stage_records[stage].get("_json_data")]
    if missing:
        return {
            "status": "unverified",
            "reason": f"Missing JSON artifacts for: {', '.join(missing)}",
        }

    values = {
        stage: set(_recursive_values(stage_records[stage]["_json_data"], "origem_id"))
        for stage in required
    }
    if any(not stage_values for stage_values in values.values()):
        return {
            "status": "unverified",
            "reason": "One or more stage JSON artifacts do not expose origem_id values.",
        }

    shared = set.intersection(*values.values())
    if shared:
        return {
            "status": "pass",
            "reason": f"Shared origem_id values observed: {', '.join(sorted(shared)[:3])}",
        }
    return {
        "status": "fail",
        "reason": "No shared origem_id values were found across extrair_questoes, corrigir, and analisar_habilidades.",
    }


def _evaluate_student_name_consistency(stage_records: dict) -> dict:
    """Best-effort student-name consistency check using top-level JSON fields."""
    candidate_keys = ("aluno", "aluno_nome", "nome_aluno", "student_name")
    names = {}
    for stage in ("corrigir", "analisar_habilidades", "gerar_relatorio"):
        data = stage_records[stage].get("_json_data") or {}
        if not isinstance(data, dict):
            continue
        for key in candidate_keys:
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                names[stage] = value.strip()
                break

    if len(names) < 2:
        return {
            "status": "unverified",
            "reason": "Fewer than two stage JSON artifacts expose a top-level student name field.",
        }

    normalized = {_normalize_token(value) for value in names.values()}
    if len(normalized) == 1:
        return {
            "status": "pass",
            "reason": f"Consistent student name observed across stages: {', '.join(sorted(set(names.values())))}",
        }
    return {
        "status": "fail",
        "reason": "Conflicting student name values were found across stage JSON artifacts.",
    }


def _load_artifact_manifest(manifest_path: Path | None) -> dict:
    """Load per-run artifact manifest entries, tolerating missing or invalid files."""
    result = {
        "download_models_by_path": {},
        "triggered_models": [],
        "download_entries": 0,
        "downloads_with_explicit_model": 0,
        "normalized_entries": 0,
    }
    if manifest_path is None:
        return result

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return result

    triggered_models = []
    download_models_by_path = {}
    for raw_line in manifest_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = entry.get("event_type")
        if event_type == "pipeline_trigger":
            model = entry.get("model_context")
            if model in MODELS and model not in triggered_models:
                triggered_models.append(model)
        elif event_type == "download_saved":
            result["download_entries"] += 1
            saved_path = entry.get("saved_path")
            model = entry.get("model_context")
            if saved_path and model in MODELS:
                result["downloads_with_explicit_model"] += 1
                normalized_path = _normalize_token(str(saved_path))
                normalized_name = _normalize_token(Path(saved_path).name)
                download_models_by_path.setdefault(normalized_path, set()).add(model)
                download_models_by_path.setdefault(normalized_name, set()).add(model)
        elif event_type == "download_normalized":
            result["normalized_entries"] += 1
            normalized_path = entry.get("normalized_path")
            model = entry.get("model_context")
            if normalized_path and model in MODELS:
                normalized_rel = _normalize_token(str(normalized_path))
                normalized_name = _normalize_token(Path(normalized_path).name)
                download_models_by_path.setdefault(normalized_rel, set()).add(model)
                download_models_by_path.setdefault(normalized_name, set()).add(model)

    result["triggered_models"] = triggered_models
    result["download_models_by_path"] = {
        key: sorted(values) for key, values in download_models_by_path.items()
    }
    return result


def build_runtime_goal(
    *,
    navigation_steps: list[str],
    activity_label: str,
    open_modal_script: str,
    trigger_script: str = "executarPipelineCompleto()",
    models: list[str] | None = None,
) -> str:
    """Build the controller-facing runtime goal from the shared verification spec."""
    requested_models = models or list(MODELS)
    navigation_block = "\n".join(
        f"  {index}. {step}" for index, step in enumerate(navigation_steps, start=1)
    )
    stage_field_block = "\n".join(f"  {line}" for line in _stage_field_lines())
    cascade_block = "\n".join(f"  {line}" for line in _cascade_level_lines())

    return (
        "THIS IS A JAVASCRIPT SINGLE-PAGE APP (SPA). URL always stays at '/'. DO NOT reload.\n\n"
        f"{build_verification_goal()}\n\n"
        "=== COMPLETE STEP-BY-STEP INSTRUCTIONS ===\n\n"
        "PHASE 1 - NAVIGATE (use evaluate_js for all navigation, do not click):\n"
        f"{navigation_block}\n"
        f"You are now on the {activity_label}.\n\n"
        f"PHASE 2 - TRIGGER PIPELINE FOR EACH OF {len(requested_models)} MODELS ({', '.join(requested_models)}):\n"
        f"  1. evaluate_js -> {open_modal_script}\n"
        "  2. wait 2 seconds for the modal to load\n"
        "  3. select_option -> choose the target model in the 'Modelo de IA' dropdown inside the modal\n"
        f"  4. evaluate_js -> {trigger_script}\n"
        "  5. wait 90 seconds for pipeline completion; if still running, wait another 60 seconds\n"
        "  6. repeat until all models above have been triggered\n\n"
        "PHASE 3 - DOWNLOAD AND VALIDATE:\n"
        "  1. Use download_file for PDF and JSON artifacts in 'Documentos da Atividade'\n"
        "  2. Validate these JSON fields per stage:\n"
        f"{stage_field_block}\n"
        "  3. Confirm shared validation expectations from the checklist, including questao_id, nota, habilidades, origem_id chain, and student name integrity\n"
        "  4. Confirm desempenho cascade evidence across the expected levels:\n"
        f"{cascade_block}\n\n"
        "KEY RULES:\n"
        f"- Never click the pipeline trigger button directly; always use evaluate_js -> {trigger_script}\n"
        "- Never scroll the main page looking for the model dropdown; it exists only inside the modal\n"
        "- Human review owns PASS/FAIL; automated output is evidence only"
    )


def build_startup_instruction(
    *,
    navigation_steps: list[str],
    open_modal_script: str,
    trigger_script: str = "executarPipelineCompleto()",
    models: list[str] | None = None,
) -> str:
    """Build the startup guidance from the shared model list and runtime steps."""
    requested_models = models or list(MODELS)
    lines = [
        "STARTUP INSTRUCTIONS - follow exactly:",
        "Step 1: If you see the welcome modal, close it via evaluate_js: closeWelcome()",
    ]
    for index, step in enumerate(navigation_steps, start=2):
        lines.append(f"Step {index}: {step}")
    lines.extend(
        [
            f"Step {len(navigation_steps) + 2}: evaluate_js -> {open_modal_script} -> wait 2 seconds",
            f"Step {len(navigation_steps) + 3}: select_option -> choose the first model ({requested_models[0]}) in the 'Modelo de IA' dropdown",
            f"Step {len(navigation_steps) + 4}: evaluate_js -> {trigger_script}",
            f"Step {len(navigation_steps) + 5}: wait 90 seconds",
            f"Step {len(navigation_steps) + 6}: repeat the modal-open, select_option, trigger, and wait flow for the remaining models: {', '.join(requested_models[1:])}",
            f"CRITICAL: do not click the trigger button directly; always use evaluate_js -> {trigger_script}",
        ]
    )
    return "\n".join(lines)


def build_phase3_instruction(models: list[str] | None = None) -> str:
    """Build the Phase 3 guidance from checklist, rules, and cascade steps."""
    requested_models = models or list(MODELS)
    validation_items = [
        item["description"] for item in CHECKLIST if item["category"] == "validation"
    ]
    download_items = [
        item["description"] for item in CHECKLIST if item["category"] == "download"
    ]
    cascade_items = _cascade_level_lines()

    lines = [
        f"PHASE 3 - all {len(requested_models)} requested pipeline triggers were observed. Do not trigger more pipelines.",
        "1. Download the available JSON and PDF artifacts from 'Documentos da Atividade'.",
    ]
    for description in download_items:
        lines.append(f"2. {description}")
    lines.append("3. Validate the required JSON fields per stage:")
    for stage_line in _stage_field_lines():
        lines.append(f"   {stage_line}")
    for description in validation_items:
        lines.append(f"4. {description}")
    lines.append("5. Verify desempenho cascade evidence:")
    for cascade_line in cascade_items:
        lines.append(f"   {cascade_line}")
    lines.append("IMPORTANT: if any artifact or report is missing, record exactly what was found and stop claiming completion.")
    return "\n".join(lines)


def build_full_checklist() -> list:
    """Merge CHECKLIST from scenario.py with CASCADE_STEPS from cascade_steps.py.

    CASCADE_STEPS items are mapped to checklist format with
    category='desempenho_cascade' and step_id as 'id'.
    """
    result = list(CHECKLIST)

    for step in CASCADE_STEPS:
        result.append({
            "id": step["step_id"],
            "description": step["action"],
            "category": "desempenho_cascade",
        })

    return result


def _load_json_with_error(path: Path) -> tuple[dict, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
        loaded = json.loads(text)
        return (loaded if isinstance(loaded, dict) else {"root": loaded}), None
    except Exception as exc:
        return {}, str(exc)


def normalize_download_artifacts(downloads_dir: Path, manifest_path: Path | None = None) -> list[dict]:
    """Move raw download artifacts into the canonical hierarchy used for proof review."""
    downloads_dir = Path(downloads_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)
    manifest_data = _load_artifact_manifest(manifest_path)
    normalized_records: list[dict] = []

    all_files = sorted(path for path in downloads_dir.rglob("*") if path.is_file())
    candidate_files = []
    for path in all_files:
        relative = path.relative_to(downloads_dir)
        if relative.parts and relative.parts[0] == "_incoming":
            candidate_files.append(path)
            continue
        if not _is_normalized_download_path(relative):
            candidate_files.append(path)

    json_metadata_by_stem: dict[str, dict] = {}
    file_metadata: dict[Path, dict] = {}

    for path in candidate_files:
        relative = path.relative_to(downloads_dir)
        normalized_rel = _normalize_token(str(relative))
        model_hits = _infer_models_from_text(str(relative))
        model_hits.extend(manifest_data["download_models_by_path"].get(normalized_rel, []))
        model_hits.extend(manifest_data["download_models_by_path"].get(_normalize_token(path.name), []))
        model_hits = sorted(set(model_hits))
        level = _infer_desempenho_level(str(relative))

        metadata = {
            "relative": str(relative),
            "model_hits": model_hits,
            "level": level,
            "stage": None,
            "student": None,
        }

        if path.suffix.lower() == ".json":
            data, _ = _load_json_with_error(path)
            stage, _ = _infer_stage_from_name(relative.name)
            if not stage:
                stage, _ = _infer_stage_from_json(data)
            metadata["stage"] = stage
            metadata["student"] = _infer_student_name(data)
            metadata["json_data"] = data
            json_metadata_by_stem[_normalize_token(path.stem)] = metadata

        file_metadata[path] = metadata

    for path in candidate_files:
        relative = path.relative_to(downloads_dir)
        metadata = dict(file_metadata.get(path, {}))
        stem_metadata = json_metadata_by_stem.get(_normalize_token(path.stem), {})
        level = metadata.get("level") or stem_metadata.get("level")
        stage = metadata.get("stage") or stem_metadata.get("stage")
        student = metadata.get("student") or stem_metadata.get("student") or "_shared"
        model_hits = metadata.get("model_hits") or stem_metadata.get("model_hits") or []
        model = model_hits[0] if len(model_hits) == 1 else "_unverified_model"

        if level:
            destination = downloads_dir / "desempenho" / level / path.name
        else:
            destination = downloads_dir / model / (stage or "_unknown_stage") / student / path.name

        if path == destination:
            continue

        destination.parent.mkdir(parents=True, exist_ok=True)
        destination = _next_available_artifact_path(destination)
        original_path = str(path)
        shutil.move(str(path), str(destination))

        record = {
            "original_path": original_path,
            "normalized_path": str(destination),
            "model_context": model if model in MODELS else None,
            "stage": stage,
            "student_context": None if level else student,
            "desempenho_level": level,
        }
        normalized_records.append(record)
        _append_manifest_line(
            manifest_path,
            {
                "event_type": "download_normalized",
                **record,
            },
        )

    return normalized_records


def evaluate_downloaded_artifacts(
    downloads_dir: Path,
    manifest_path: Path | None = None,
    requested_models: list[str] | None = None,
    expected_blocked_models: list[str] | None = None,
) -> dict:
    """Scan a run's downloads directory and validate the discovered pipeline artifacts."""
    downloads_dir = Path(downloads_dir)
    requested_models, expected_blocked_models = _normalize_model_scope(
        requested_models=requested_models,
        expected_blocked_models=expected_blocked_models,
    )
    normalization_records = normalize_download_artifacts(downloads_dir, manifest_path=manifest_path)
    manifest_data = _load_artifact_manifest(manifest_path)
    stage_records = {
        stage: {
            "json_path": None,
            "json_stage_source": None,
            "json_top_level_keys": [],
            "json_parse_error": None,
            "pdf_path": None,
            "pdf_stage_source": None,
            "pdf_size": 0,
            "_json_rank": 0,
            "_json_size": -1,
            "_json_data": {},
            "_pdf_rank": 0,
            "_model_hits": set(),
        }
        for stage in PIPELINE_STAGES
    }
    desempenho = {
        level: {"json": False, "pdf": False, "content_populated": False}
        for level in ("tarefa", "turma", "materia")
    }
    counts = {"json": 0, "pdf": 0, "other": 0}
    unknown_files = []
    recognized_models = set()
    stem_to_stage = {}
    model_stage_artifacts = {
        model: {
            stage: {"json": False, "pdf": False}
            for stage in PIPELINE_STAGES
        }
        for model in MODELS
    }

    if downloads_dir.exists():
        files = sorted(path for path in downloads_dir.rglob("*") if path.is_file())
    else:
        files = []

    json_files = [path for path in files if path.suffix.lower() == ".json"]
    pdf_files = [path for path in files if path.suffix.lower() == ".pdf"]
    counts["json"] = len(json_files)
    counts["pdf"] = len(pdf_files)
    counts["other"] = len(files) - counts["json"] - counts["pdf"]

    for path in json_files:
        relative = path.relative_to(downloads_dir)
        model_hits = _infer_models_from_text(str(relative))
        normalized_rel = _normalize_token(str(relative))
        model_hits.extend(manifest_data["download_models_by_path"].get(normalized_rel, []))
        model_hits.extend(manifest_data["download_models_by_path"].get(_normalize_token(path.name), []))
        model_hits = sorted(set(model_hits))
        recognized_models.update(model_hits)

        parse_error = None
        try:
            text = path.read_text(encoding="utf-8")
            loaded = json.loads(text)
            data = loaded if isinstance(loaded, dict) else {"root": loaded}
        except Exception as exc:
            parse_error = str(exc)
            data = {}

        if "desempenho" in normalized_rel:
            for level in desempenho:
                if level in normalized_rel:
                    desempenho[level]["json"] = True
                    desempenho[level]["content_populated"] = desempenho[level]["content_populated"] or _contains_recursive_key(
                        data, "habilidades"
                    )
            continue

        stage, source = _infer_stage_from_name(relative.name)
        if not stage:
            stage, source = _infer_stage_from_json(data)
        if not stage:
            unknown_files.append(str(relative))
            continue

        stem_to_stage[_normalize_token(path.stem)] = stage
        _record_stage_json(
            stage_records,
            stage=stage,
            path=path,
            stage_source=source,
            data=data,
            parse_error=parse_error,
            model_hits=model_hits,
        )
        for model in model_hits:
            model_stage_artifacts[model][stage]["json"] = True

    for path in pdf_files:
        relative = path.relative_to(downloads_dir)
        model_hits = _infer_models_from_text(str(relative))
        normalized_rel = _normalize_token(str(relative))
        model_hits.extend(manifest_data["download_models_by_path"].get(normalized_rel, []))
        model_hits.extend(manifest_data["download_models_by_path"].get(_normalize_token(path.name), []))
        model_hits = sorted(set(model_hits))
        recognized_models.update(model_hits)

        if "desempenho" in normalized_rel:
            for level in desempenho:
                if level in normalized_rel:
                    desempenho[level]["pdf"] = True
            continue

        stage, source = _infer_stage_from_name(relative.name)
        if not stage:
            stage = stem_to_stage.get(_normalize_token(path.stem))
            source = "paired_stem" if stage else None
        if not stage:
            unknown_files.append(str(relative))
            continue

        _record_stage_pdf(
            stage_records,
            stage=stage,
            path=path,
            stage_source=source,
            model_hits=model_hits,
        )
        for model in model_hits:
            model_stage_artifacts[model][stage]["pdf"] = True

    outputs = {}
    for stage in PIPELINE_STAGES:
        record = stage_records[stage]
        if record["json_path"] or record["pdf_path"]:
            outputs[stage] = {
                "json": record.get("_json_data") or {},
                "pdf_size": record.get("pdf_size", 0) or 0,
            }

    validation = validate_pipeline_outputs(outputs)

    stages_with_json = [stage for stage in PIPELINE_STAGES if stage_records[stage]["json_path"]]
    stages_with_pdf = [stage for stage in PIPELINE_STAGES if stage_records[stage]["pdf_path"]]
    missing_json_stages = [stage for stage in PIPELINE_STAGES if stage not in stages_with_json]
    missing_pdf_stages = [stage for stage in PIPELINE_STAGES if stage not in stages_with_pdf]
    missing_stages = [stage for stage in PIPELINE_STAGES if stage in missing_json_stages or stage in missing_pdf_stages]
    triggered_models = manifest_data["triggered_models"]
    required_models = [
        model for model in requested_models if model not in expected_blocked_models
    ]
    missing_trigger_models = [model for model in required_models if model not in triggered_models]
    model_coverage = {}
    for model in MODELS:
        stage_flags = model_stage_artifacts[model]
        model_stages_with_json = [stage for stage in PIPELINE_STAGES if stage_flags[stage]["json"]]
        model_stages_with_pdf = [stage for stage in PIPELINE_STAGES if stage_flags[stage]["pdf"]]
        model_coverage[model] = {
            "stages_with_json": model_stages_with_json,
            "stages_with_pdf": model_stages_with_pdf,
            "complete_stage_count": sum(
                1 for stage in PIPELINE_STAGES if stage_flags[stage]["json"] and stage_flags[stage]["pdf"]
            ),
        }
    model_scope_confirmed = bool(required_models) and all(
        model_coverage[model]["complete_stage_count"] == len(PIPELINE_STAGES)
        for model in required_models
    )

    model_status = {}
    for model in MODELS:
        coverage = model_coverage[model]
        observed = bool(
            coverage["stages_with_json"]
            or coverage["stages_with_pdf"]
            or model in triggered_models
        )
        if model not in requested_models:
            status = "not_requested"
        elif model in expected_blocked_models:
            status = "expected_blocked_observed" if observed else "expected_blocked"
        elif coverage["complete_stage_count"] == len(PIPELINE_STAGES):
            status = "validated"
        elif observed:
            status = "partial"
        else:
            status = "missing"
        model_status[model] = {
            "status": status,
            **coverage,
        }

    if counts["json"] == 0 and counts["pdf"] == 0:
        overall_status = "missing_downloads"
    elif missing_stages:
        overall_status = "incomplete_artifacts"
    elif not validation["valid"]:
        overall_status = "validation_failed"
    elif not model_scope_confirmed:
        overall_status = "unverified_model_scope"
    elif expected_blocked_models:
        overall_status = "validated_with_expected_blockers"
    else:
        overall_status = "validated"

    origem_id_chain = _evaluate_origem_id_chain(stage_records)
    student_name_consistency = _evaluate_student_name_consistency(stage_records)
    any_desempenho_json = any(details["json"] for details in desempenho.values())
    desempenho_content_status = {
        "status": "pass" if all(
            details["content_populated"] for details in desempenho.values() if details["json"]
        ) and any_desempenho_json else (
            "unverified" if not any_desempenho_json else "fail"
        ),
        "reason": (
            "At least one downloaded desempenho JSON file exposed habilidades content."
            if any(details["content_populated"] for details in desempenho.values())
            else "No downloaded desempenho JSON file exposed habilidades content."
        ),
    }

    stage_artifacts = {}
    for stage in PIPELINE_STAGES:
        record = stage_records[stage]
        stage_result = validation["results"].get(stage)
        errors = list(stage_result["errors"]) if stage_result else []
        if not record["json_path"] and not record["pdf_path"]:
            stage_status = "missing"
        elif stage_result and stage_result["valid"]:
            stage_status = "pass"
        else:
            stage_status = "fail"
        stage_artifacts[stage] = {
            "status": stage_status,
            "json_path": record["json_path"],
            "json_stage_source": record["json_stage_source"],
            "json_top_level_keys": record["json_top_level_keys"],
            "json_parse_error": record["json_parse_error"],
            "pdf_path": record["pdf_path"],
            "pdf_stage_source": record["pdf_stage_source"],
            "pdf_size": record["pdf_size"],
            "recognized_models": sorted(record["_model_hits"]),
            "valid": bool(stage_result["valid"]) if stage_result else False,
            "errors": errors,
        }

    return {
        "downloads_dir": str(downloads_dir),
        "manifest_path": str(manifest_path) if manifest_path else None,
        "requested_models": requested_models,
        "expected_blocked_models": expected_blocked_models,
        "counts": counts,
        "overall_status": overall_status,
        "recognized_models": sorted(recognized_models),
        "model_scope_confirmed": model_scope_confirmed,
        "triggered_models": triggered_models,
        "missing_trigger_models": missing_trigger_models,
        "download_manifest_entries": manifest_data["download_entries"],
        "downloads_with_explicit_model": manifest_data["downloads_with_explicit_model"],
        "normalized_download_entries": manifest_data["normalized_entries"],
        "normalization": {
            "normalized_file_count": len(normalization_records),
            "normalized_files": normalization_records,
        },
        "b5_eligible": requested_models == list(MODELS) and not expected_blocked_models,
        "coverage": {
            "stages_with_json": stages_with_json,
            "stages_with_pdf": stages_with_pdf,
            "missing_json_stages": missing_json_stages,
            "missing_pdf_stages": missing_pdf_stages,
            "missing_stages": missing_stages,
            "complete_stage_count": sum(
                1 for stage in PIPELINE_STAGES if stage in stages_with_json and stage in stages_with_pdf
            ),
        },
        "model_coverage": model_coverage,
        "model_status": model_status,
        "stage_artifacts": stage_artifacts,
        "validation": validation,
        "origem_id_chain": origem_id_chain,
        "student_name_consistency": student_name_consistency,
        "desempenho": {
            level: {
                "json": details["json"],
                "pdf": details["pdf"],
                "content_populated": details["content_populated"],
            }
            for level, details in desempenho.items()
        },
        "desempenho_report_content": desempenho_content_status,
        "unknown_files": sorted(set(unknown_files)),
    }


def validate_pipeline_outputs(outputs: dict) -> dict:
    """Validate pipeline stage outputs using validation_rules.

    Args:
        outputs: {stage_name: {"json": dict, "pdf_size": int}}

    Returns:
        {"valid": bool, "results": {stage_name: {"valid": bool, "errors": list}}}
    """
    results = {}

    for stage_name, data in outputs.items():
        if stage_name not in STAGE_RULES:
            continue
        stage_result = validate_stage_output(
            stage_name, data.get("json", {}), data.get("pdf_size", 0)
        )
        results[stage_name] = stage_result

    overall_valid = all(r["valid"] for r in results.values()) if results else True

    return {"valid": overall_valid, "results": results}


def generate_verification_report(results: dict) -> str:
    """Generate a markdown verification report from validation results.

    Args:
        results: Output from validate_pipeline_outputs(), optionally with a
                 'model' key for the model name.

    Returns:
        Markdown string with summary table and error details.
    """
    model = results.get("model", "")
    overall = results.get("valid", True)
    stage_results = results.get("results", {})

    lines = []

    # Header
    title = "Pipeline Verification Report"
    if model:
        title += f" — {model}"
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Overall: {'PASS' if overall else 'FAIL'}**")
    lines.append("")

    # Summary table
    lines.append("| Stage | Status |")
    lines.append("|-------|--------|")
    for stage_name, sr in stage_results.items():
        status = "PASS" if sr["valid"] else "FAIL"
        lines.append(f"| {stage_name} | {status} |")
    lines.append("")

    # Error details
    failures = {k: v for k, v in stage_results.items() if not v["valid"]}
    if failures:
        lines.append("## Errors")
        lines.append("")
        for stage_name, sr in failures.items():
            lines.append(f"### {stage_name}")
            for err in sr["errors"]:
                lines.append(f"- {err}")
            lines.append("")

    return "\n".join(lines)
