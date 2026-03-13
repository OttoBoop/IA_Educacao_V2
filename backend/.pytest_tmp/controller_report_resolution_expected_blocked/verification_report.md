# Pipeline Verification Report
**Generated:** 2026-03-11 05:53:53
**Persona:** tester | **Viewport:** desktop | **Models:** 4

---

## Pipeline Triggers

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| pipeline-trigger-gpt4o | Trigger pipeline run for model gpt-4o and confirm task panel shows all 4 stages | OBSERVED | Model trigger observed in the run artifact manifest. |
| pipeline-trigger-gpt5-nano | Trigger pipeline run for model gpt-5-nano and confirm task panel shows all 4 stages | OBSERVED | Model trigger observed in the run artifact manifest. |
| pipeline-trigger-claude-haiku | Trigger pipeline run for model claude-haiku-4-5-20251001 and confirm task panel shows all 4 stages | BLOCKED | Model marked expected blocked for this proof run scope. |
| pipeline-trigger-gemini-flash | Trigger pipeline run for model gemini-3-flash-preview and confirm task panel shows all 4 stages | OBSERVED | Model trigger observed in the run artifact manifest. |

## Downloads

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| download-json-outputs | Download JSON output for each model and each pipeline stage; confirm files are non-empty | OBSERVED | JSON artifacts were downloaded for every requested non-blocked model and pipeline stage. |
| download-pdf-reports | Download PDF report for each model; confirm PDF exists and is readable | OBSERVED | PDF artifacts were downloaded for every requested non-blocked model and pipeline stage. |

## Content Validation

### Checklist: validation-json-fields

**Description:** Open downloaded JSON files and verify required fields are present (questao_id, nota, habilidades)

| Status | Observations |
|--------|-------------|
| OBSERVED | Required JSON fields were observed across all pipeline stages. |

### Checklist: validation-origem-id-chain

**Description:** Verify origem_id chain is consistent across extrair_questoes → corrigir → analisar_habilidades outputs

| Status | Observations |
|--------|-------------|
| OBSERVED | Shared origem_id present. |

### Checklist: validation-student-name

**Description:** Confirm student name appears correctly in each model's PDF and JSON output

| Status | Observations |
|--------|-------------|
| UNVERIFIED | Shared student artifact. |

## Stage Validation Rules

### Stage: extrair_questoes

*Questions extracted from the exam PDF, including the list and count.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: questoes, total_questoes | Present | OBSERVED | Required JSON fields observed in downloaded artifact. |
| PDF size | >= 1000 bytes | OBSERVED | PDF size 1100 bytes meets the minimum threshold. |

### Stage: corrigir

*Student grading results with per-student scores and answer key.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: alunos, notas, gabarito | Present | OBSERVED | Required JSON fields observed in downloaded artifact. |
| PDF size | >= 2000 bytes | OBSERVED | PDF size 2100 bytes meets the minimum threshold. |

### Stage: analisar_habilidades

*Skill analysis per student based on graded responses.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: habilidades, analise | Present | OBSERVED | Required JSON fields observed in downloaded artifact. |
| PDF size | >= 2000 bytes | OBSERVED | PDF size 2100 bytes meets the minimum threshold. |

### Stage: gerar_relatorio

*Final report with full summary of results and skill analysis.*

| Check | Expected | Status | Observations |
|-------|----------|--------|-------------|
| JSON fields: relatorio, resumo | Present | OBSERVED | Required JSON fields observed in downloaded artifact. |
| PDF size | >= 5000 bytes | OBSERVED | PDF size 5100 bytes meets the minimum threshold. |

## Desempenho Cascade

### Checklist

| ID | Description | Status | Observations |
|----|-------------|--------|-------------|
| desempenho-cascade-trigger | Navigate to Desempenho tab and trigger the cascade for the test turma; confirm loading state appears | OBSERVED | Downloaded desempenho artifacts show that the cascade path was exercised. |
| desempenho-auto-creation | Verify Desempenho reports are auto-created for all 4 models after cascade completes | OBSERVED | Tarefa, turma, and materia desempenho artifacts were all downloaded. |
| desempenho-report-content | Open each auto-created Desempenho report and confirm habilidades breakdown is populated | OBSERVED | Content populated. |

### Cascade Steps

| Step | Action | Level | Status | Observations |
|------|--------|-------|--------|-------------|
| D1 | Trigger materia-level desempenho by submitting graded provas for all tarefas in a materia | materia | OBSERVED | Materia-level desempenho artifact observed. |
| D2 | Fetch the materia desempenho report from the API and download the generated PDF | materia | OBSERVED | Materia JSON and PDF artifacts were both downloaded. |
| D3 | Verify that turma-level reports were automatically created by the cascade from materia | turma | OBSERVED | Turma desempenho artifacts were observed. |
| D4 | Verify that tarefa-level reports were automatically created by the cascade from materia | tarefa | OBSERVED | Tarefa desempenho artifacts were observed. |
| D5 | Check report content integrity: materia report references the correct turma and tarefa sub-reports | materia | OBSERVED | Content populated. |

---

## Summary

- Total checks: 25
- OBSERVED: 23
- FAILED: 0
- BLOCKED: 1
- UNVERIFIED: 1
- PENDING: 0
