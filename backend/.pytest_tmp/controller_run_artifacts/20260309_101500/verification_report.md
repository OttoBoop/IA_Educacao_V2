# Pipeline Verification Report
**Generated:** 2026-03-11 05:53:53
**Persona:** tester | **Viewport:** desktop | **Models:** 4

---

## Pipeline Triggers

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| pipeline-trigger-gpt4o | Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages | PENDING | |
| pipeline-trigger-gpt5-nano | Trigger pipeline run for model gpt-5-nano and confirm task panel shows all 4 stages | PENDING | |
| pipeline-trigger-claude-haiku | Trigger pipeline run for model claude-haiku-4-5-20251001 and confirm task panel shows all 4 stages | PENDING | |
| pipeline-trigger-gemini-flash | Trigger pipeline run for model gemini-3-flash-preview and confirm task panel shows all 4 stages | PENDING | |

## Downloads

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| download-json-outputs | Download JSON output for each model and each pipeline stage; confirm files are non-empty | PENDING | |
| download-pdf-reports | Download PDF report for each model; confirm PDF exists and is readable | PENDING | |

## Content Validation

### Checklist: validation-json-fields

**Description:** Open downloaded JSON files and verify required fields are present (questao_id, nota, habilidades)

| Status | Observations |
|--------|-------------|
| PENDING | |

### Checklist: validation-origem-id-chain

**Description:** Verify origem_id chain is consistent across extrair_questoes → corrigir → analisar_habilidades outputs

| Status | Observations |
|--------|-------------|
| PENDING | |

### Checklist: validation-student-name

**Description:** Confirm student name appears correctly in each model's PDF and JSON output

| Status | Observations |
|--------|-------------|
| PENDING | |

## Stage Validation Rules

### Stage: extrair_questoes

*Questions extracted from the exam PDF, including the list and count.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: questoes, total_questoes | Present | PENDING | |
| PDF size | >= 1000 bytes | PENDING | |

### Stage: corrigir

*Student grading results with per-student scores and answer key.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: alunos, notas, gabarito | Present | PENDING | |
| PDF size | >= 2000 bytes | PENDING | |

### Stage: analisar_habilidades

*Skill analysis per student based on graded responses.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: habilidades, analise | Present | PENDING | |
| PDF size | >= 2000 bytes | PENDING | |

### Stage: gerar_relatorio

*Final report with full summary of results and skill analysis.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: relatorio, resumo | Present | PENDING | |
| PDF size | >= 5000 bytes | PENDING | |

## Desempenho Cascade

### Checklist

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| desempenho-cascade-trigger | Navigate to Desempenho tab and trigger the cascade for the test turma; confirm loading state appears | PENDING | |
| desempenho-auto-creation | Verify Desempenho reports are auto-created for all 4 models after cascade completes | PENDING | |
| desempenho-report-content | Open each auto-created Desempenho report and confirm habilidades breakdown is populated | PENDING | |

### Cascade Steps

| Step | Action | Level | Status | Observations |
|------|--------|-------|--------|-------------|
| D1 | Trigger materia-level desempenho by submitting graded provas for all tarefas in a materia | materia | PENDING | |
| D2 | Fetch the materia desempenho report from the API and download the generated PDF | materia | PENDING | |
| D3 | Verify that turma-level reports were automatically created by the cascade from materia | turma | PENDING | |
| D4 | Verify that tarefa-level reports were automatically created by the cascade from materia | tarefa | PENDING | |
| D5 | Check report content integrity: materia report references the correct turma and tarefa sub-reports | materia | PENDING | |

---

## Summary

- Total checks: 25
- OBSERVED: 0
- FAILED: 0
- BLOCKED: 0
- UNVERIFIED: 0
- PENDING: 25
