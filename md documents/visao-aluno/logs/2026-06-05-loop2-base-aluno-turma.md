# Loop 2 - Base De Leitura Aluno-Turma

Data: 2026-06-05

## Objetivo

Criar o contrato de leitura que prepara a futura geracao de relatorio de
desempenho individual para um aluno em uma turma especifica.

## Alteracoes

- `backend/routes_extras.py`
  - criado `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}`;
  - valida aluno, turma e vinculo aluno-turma;
  - lista apenas atividades da turma informada;
  - filtra documentos pelo `aluno_id`;
  - retorna `base_minima` com bloqueio quando falta `relatorio_final_do_aluno`;
  - explicita `tipo_documento_futuro: relatorio_desempenho_aluno_turma`.
- `backend/tests/integration/test_desempenho_aluno_turma_endpoint.py`
  - cobre filtro aluno+turma;
  - cobre outra turma da mesma materia;
  - cobre documento de outro aluno;
  - cobre bloqueio sem relatorio final;
  - cobre aluno sem vinculo.

## Evidencia

Comando:

```text
cd /home/otavio/Documents/vscode/prova-ia-v2/backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q
```

Resultado:

```text
39 passed, 1 warning in 2.14s
```

## Fronteira

- Nao foi iniciado servidor local.
- Ainda nao ha geracao real de `relatorio_desempenho_aluno_turma`.
- Ainda nao ha relatorio longitudinal.
- A visao aluno inclui turmas historicas/inativas via `apenas_ativas=False`.
