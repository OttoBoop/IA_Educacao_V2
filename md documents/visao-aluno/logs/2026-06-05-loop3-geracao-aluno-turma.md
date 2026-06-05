# Loop 3 - Geracao Deterministica Aluno-Turma

Data: 2026-06-05

## Objetivo

Criar o primeiro fluxo automatico que gera e salva um relatorio individual de
desempenho para `aluno_id + turma_id`, sem gastar provider real.

## Alteracoes

- `backend/models.py`
  - adicionado `TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA`;
  - adicionado em `documentos_gerados()`;
  - adicionada dependencia minima em `DEPENDENCIAS_DOCUMENTOS`.
- `backend/storage.py`
  - adicionado label legivel para `relatorio_desempenho_aluno_turma`.
- `backend/routes_prompts.py`
  - criado `POST /api/executar/pipeline-desempenho-aluno-turma`;
  - gera Markdown deterministico v1 a partir de `RELATORIO_FINAL` do aluno na turma;
  - salva metadata com `scope`, `aluno_id`, `turma_id`, `materia_id`, `atividade_ids`;
  - bloqueia quando falta `relatorio_final_do_aluno`;
  - evita duplicacao quando ja existe relatorio e `force_reexec` nao foi enviado.
- `backend/tests/integration/test_desempenho_aluno_turma_endpoint.py`
  - cobre salvamento do documento;
  - cobre metadata;
  - cobre idempotencia sem `force_reexec`.

## Evidencia

Comando:

```text
cd /home/otavio/Documents/vscode/prova-ia-v2/backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q
```

Resultado:

```text
41 passed, 1 warning in 1.41s
```

Checagem adicional:

```text
/home/otavio/Documents/vscode/.venv/bin/python -m py_compile models.py storage.py routes_extras.py routes_prompts.py main_v2.py
```

Resultado: passou.

## Fronteira

- Nao foi iniciado servidor local.
- A geracao aluno-turma ainda nao usa provider LLM.
- Ainda nao ha relatorio longitudinal.
