# Pipeline Verification Report
**Generated:** 2026-03-11 05:53:53
**Persona:** tester | **Viewport:** desktop | **Models:** 4

---

## Pipeline Triggers

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| pipeline-trigger-gpt4o | Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages | BLOCKED | Run blocked before trigger evidence for this model was recorded. |
| pipeline-trigger-gpt5-nano | Trigger pipeline run for model gpt-5-nano and confirm task panel shows all 4 stages | BLOCKED | Run blocked before trigger evidence for this model was recorded. |
| pipeline-trigger-claude-haiku | Trigger pipeline run for model claude-haiku-4-5-20251001 and confirm task panel shows all 4 stages | BLOCKED | Run blocked before trigger evidence for this model was recorded. |
| pipeline-trigger-gemini-flash | Trigger pipeline run for model gemini-3-flash-preview and confirm task panel shows all 4 stages | BLOCKED | Run blocked before trigger evidence for this model was recorded. |

## Downloads

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| download-json-outputs | Download JSON output for each model and each pipeline stage; confirm files are non-empty | BLOCKED | Run blocked before JSON downloads were collected. |
| download-pdf-reports | Download PDF report for each model; confirm PDF exists and is readable | BLOCKED | Run blocked before PDF downloads were collected. |

## Content Validation

### Checklist: validation-json-fields

**Description:** Open downloaded JSON files and verify required fields are present (questao_id, nota, habilidades)

| Status | Observations |
|--------|-------------|
| BLOCKED | Run blocked before enough evidence was collected. |

### Checklist: validation-origem-id-chain

**Description:** Verify origem_id chain is consistent across extrair_questoes → corrigir → analisar_habilidades outputs

| Status | Observations |
|--------|-------------|
| BLOCKED | No artifacts downloaded. |

### Checklist: validation-student-name

**Description:** Confirm student name appears correctly in each model's PDF and JSON output

| Status | Observations |
|--------|-------------|
| BLOCKED | No artifacts downloaded. |

## Stage Validation Rules

### Stage: extrair_questoes

*Questions extracted from the exam PDF, including the list and count.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: questoes, total_questoes | Present | BLOCKED | Run blocked before JSON artifact was collected. |
| PDF size | >= 1000 bytes | BLOCKED | Run blocked before PDF artifact was collected. |

### Stage: corrigir

*Student grading results with per-student scores and answer key.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: alunos, notas, gabarito | Present | BLOCKED | Run blocked before JSON artifact was collected. |
| PDF size | >= 2000 bytes | BLOCKED | Run blocked before PDF artifact was collected. |

### Stage: analisar_habilidades

*Skill analysis per student based on graded responses.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: habilidades, analise | Present | BLOCKED | Run blocked before JSON artifact was collected. |
| PDF size | >= 2000 bytes | BLOCKED | Run blocked before PDF artifact was collected. |

### Stage: gerar_relatorio

*Final report with full summary of results and skill analysis.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: relatorio, resumo | Present | BLOCKED | Run blocked before JSON artifact was collected. |
| PDF size | >= 5000 bytes | BLOCKED | Run blocked before PDF artifact was collected. |

## Desempenho Cascade

### Checklist

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| desempenho-cascade-trigger | Navigate to Desempenho tab and trigger the cascade for the test turma; confirm loading state appears | BLOCKED | Run blocked before desempenho artifact evidence was collected. |
| desempenho-auto-creation | Verify Desempenho reports are auto-created for all 4 models after cascade completes | BLOCKED | Run blocked before desempenho auto-creation could be verified. |
| desempenho-report-content | Open each auto-created Desempenho report and confirm habilidades breakdown is populated | BLOCKED | No artifacts downloaded. |

### Cascade Steps

| Step | Action | Level | Status | Observations |
|------|--------|-------|--------|-------------|
| D1 | Trigger materia-level desempenho by submitting graded provas for all tarefas in a materia | materia | BLOCKED | Run blocked before materia-level desempenho was verified. |
| D2 | Fetch the materia desempenho report from the API and download the generated PDF | materia | BLOCKED | Run blocked before materia report download was verified. |
| D3 | Verify that turma-level reports were automatically created by the cascade from materia | turma | BLOCKED | Run blocked before turma auto-creation was verified. |
| D4 | Verify that tarefa-level reports were automatically created by the cascade from materia | tarefa | BLOCKED | Run blocked before tarefa auto-creation was verified. |
| D5 | Check report content integrity: materia report references the correct turma and tarefa sub-reports | materia | BLOCKED | No artifacts downloaded. |

---

## Summary

- Total checks: 25
- OBSERVED: 0
- FAILED: 0
- BLOCKED: 25
- UNVERIFIED: 0
- PENDING: 0
