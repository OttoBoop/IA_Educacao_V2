"""
cascade_steps.py — F6-T3: Desempenho Cascade Verification Steps.

Defines the structural constants used to drive desempenho cascade verification:
when materia-level desempenho is triggered, it should auto-create tarefa and
turma reports.
"""

CASCADE_LEVELS = ["tarefa", "turma", "materia"]

CASCADE_STEPS = [
    {
        "step_id": "D1",
        "action": "Trigger materia-level desempenho by submitting graded provas for all tarefas in a materia",
        "level": "materia",
        "verify": "POST /api/desempenho/materia returns 200 and creates a materia report entry",
        "expected_outputs": ["json", "pdf"],
    },
    {
        "step_id": "D2",
        "action": "Fetch the materia desempenho report from the API and download the generated PDF",
        "level": "materia",
        "verify": "GET /api/desempenho/materia/{id} returns report JSON with pdf_url populated",
        "expected_outputs": ["json", "pdf"],
    },
    {
        "step_id": "D3",
        "action": "Verify that turma-level reports were automatically created by the cascade from materia",
        "level": "turma",
        "verify": "GET /api/desempenho/turma lists at least one report auto-created after materia trigger",
        "expected_outputs": ["json", "pdf"],
    },
    {
        "step_id": "D4",
        "action": "Verify that tarefa-level reports were automatically created by the cascade from materia",
        "level": "tarefa",
        "verify": "GET /api/desempenho/tarefa lists at least one report auto-created after materia trigger",
        "expected_outputs": ["json", "pdf"],
    },
    {
        "step_id": "D5",
        "action": "Check report content integrity: materia report references the correct turma and tarefa sub-reports",
        "level": "materia",
        "verify": "Materia report JSON contains turma_ids and tarefa_ids arrays with at least one entry each",
        "expected_outputs": ["json"],
    },
]

EXPECTED_REPORTS_PER_LEVEL = {
    "tarefa": {
        "auto_creates": [],
        "expected_count": 1,
        "must_have_pdf": True,
    },
    "turma": {
        "auto_creates": [],
        "expected_count": 1,
        "must_have_pdf": True,
    },
    "materia": {
        "auto_creates": ["tarefa", "turma"],
        "expected_count": 1,
        "must_have_pdf": True,
    },
}
