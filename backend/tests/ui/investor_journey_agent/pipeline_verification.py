"""
F6-T4: Pipeline Verification — Integration module.

Combines scenario.py, validation_rules.py, and cascade_steps.py into a unified
verification orchestrator for the journey agent.

Exports:
- build_verification_goal()          -> str
- build_full_checklist()             -> list[dict]
- validate_pipeline_outputs(outputs) -> dict
- generate_verification_report(results) -> str
"""

from .scenario import MODELS, PIPELINE_STAGES, VERIFICATION_GOAL, CHECKLIST
from .validation_rules import STAGE_RULES, validate_stage_output
from .cascade_steps import CASCADE_STEPS


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
