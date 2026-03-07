"""
Journey scenario configuration for F6-T1: Full Pipeline Verification.

Defines the constants the investor journey agent uses to run the complete
Prova AI grading pipeline verification across all 4 supported AI models.
"""

MODELS: list = [
    "gpt-4o",
    "gpt-5-nano",
    "claude-haiku-4-5-20251001",
    "gemini-3-flash-preview",
]

PIPELINE_STAGES: list = [
    "extrair_questoes",
    "corrigir",
    "analisar_habilidades",
    "gerar_relatorio",
]

VERIFICATION_GOAL: str = (
    "Verify the full Prova AI grading pipeline end-to-end across 4 AI models "
    "(gpt-4o, gpt-5-nano, claude-haiku-4-5-20251001, gemini-3-flash-preview). "
    "For each model: trigger the pipeline, monitor all 4 stages in the task panel, "
    "download JSON and PDF outputs, validate content integrity, and trigger the "
    "desempenho cascade to confirm auto-creation of performance reports."
)

CHECKLIST: list = [
    {
        "id": "pipeline-trigger-gpt4o",
        "description": "Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages",
        "category": "pipeline",
    },
    {
        "id": "pipeline-trigger-gpt5-nano",
        "description": "Trigger pipeline run for model gpt-5-nano and confirm task panel shows all 4 stages",
        "category": "pipeline",
    },
    {
        "id": "pipeline-trigger-claude-haiku",
        "description": "Trigger pipeline run for model claude-haiku-4-5-20251001 and confirm task panel shows all 4 stages",
        "category": "pipeline",
    },
    {
        "id": "pipeline-trigger-gemini-flash",
        "description": "Trigger pipeline run for model gemini-3-flash-preview and confirm task panel shows all 4 stages",
        "category": "pipeline",
    },
    {
        "id": "download-json-outputs",
        "description": "Download JSON output for each model and each pipeline stage; confirm files are non-empty",
        "category": "download",
    },
    {
        "id": "download-pdf-reports",
        "description": "Download PDF report for each model; confirm PDF exists and is readable",
        "category": "download",
    },
    {
        "id": "validation-json-fields",
        "description": "Open downloaded JSON files and verify required fields are present (questao_id, nota, habilidades)",
        "category": "validation",
    },
    {
        "id": "validation-origem-id-chain",
        "description": "Verify origem_id chain is consistent across extrair_questoes → corrigir → analisar_habilidades outputs",
        "category": "validation",
    },
    {
        "id": "validation-student-name",
        "description": "Confirm student name appears correctly in each model's PDF and JSON output",
        "category": "validation",
    },
    {
        "id": "desempenho-cascade-trigger",
        "description": "Navigate to Desempenho tab and trigger the cascade for the test turma; confirm loading state appears",
        "category": "desempenho",
    },
    {
        "id": "desempenho-auto-creation",
        "description": "Verify Desempenho reports are auto-created for all 4 models after cascade completes",
        "category": "desempenho",
    },
    {
        "id": "desempenho-report-content",
        "description": "Open each auto-created Desempenho report and confirm habilidades breakdown is populated",
        "category": "desempenho",
    },
]
