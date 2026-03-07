"""
F6-T2: Content Validation Rules Per Stage.

Defines STAGE_RULES and validate_stage_output for checking pipeline stage output.
"""

STAGE_RULES = {
    "extrair_questoes": {
        "expected_json_fields": ["questoes", "total_questoes"],
        "pdf_min_bytes": 1000,
        "description": "Questions extracted from the exam PDF, including the list and count.",
    },
    "corrigir": {
        "expected_json_fields": ["alunos", "notas", "gabarito"],
        "pdf_min_bytes": 2000,
        "description": "Student grading results with per-student scores and answer key.",
    },
    "analisar_habilidades": {
        "expected_json_fields": ["habilidades", "analise"],
        "pdf_min_bytes": 2000,
        "description": "Skill analysis per student based on graded responses.",
    },
    "gerar_relatorio": {
        "expected_json_fields": ["relatorio", "resumo"],
        "pdf_min_bytes": 5000,
        "description": "Final report with full summary of results and skill analysis.",
    },
}


def validate_stage_output(stage: str, json_content: dict, pdf_size: int) -> dict:
    """Validate the output of a pipeline stage.

    Args:
        stage: Name of the pipeline stage.
        json_content: JSON output dict from the stage.
        pdf_size: Size in bytes of the generated PDF.

    Returns:
        dict with keys:
            "valid" (bool): True if all checks pass.
            "errors" (list[str]): Descriptive error messages, empty when valid.

    Raises:
        KeyError: If stage is not in STAGE_RULES.
    """
    if stage not in STAGE_RULES:
        raise KeyError(f"Unknown stage: '{stage}'. Valid stages: {list(STAGE_RULES.keys())}")

    rule = STAGE_RULES[stage]
    errors = []

    for field in rule["expected_json_fields"]:
        if field not in json_content:
            errors.append(f"Missing required JSON field '{field}' in stage '{stage}' output.")

    if pdf_size < rule["pdf_min_bytes"]:
        errors.append(
            f"PDF size {pdf_size} bytes is below the minimum {rule['pdf_min_bytes']} bytes for stage '{stage}'."
        )

    return {"valid": len(errors) == 0, "errors": errors}
