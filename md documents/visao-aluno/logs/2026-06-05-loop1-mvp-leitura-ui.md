# Loop 1 - MVP Leitura/UI Da Visao Aluno

Data: 2026-06-05

## Objetivo

Fechar o primeiro loop executavel da visao aluno:

- endpoint de leitura;
- isolamento por aluno;
- preservacao de turmas repetidas na mesma materia;
- UI basica usando o novo contrato.

## Alteracoes

- `backend/storage.py`
  - criado `StorageManager.get_visao_aluno(aluno_id)`;
  - retorno agrupa por materia, mas mantem cada turma separada;
  - atividades carregam status apenas dos documentos daquele aluno.
- `backend/main_v2.py`
  - criado `GET /api/alunos/{aluno_id}/visao`.
- `frontend/index_v2.html`
  - `showAluno()` passou a consumir `/api/alunos/{aluno_id}/visao`;
  - renderizacao agora mostra materia > turma > atividade > status.
- `backend/tests/integration/test_visao_aluno_endpoint.py`
  - cobre repetencia/multiplas turmas, aluno sem documentos, documento de outro aluno e 404.
- `backend/tests/unit/test_visao_aluno_frontend.py`
  - trava o contrato estatico da UI.

## Evidencia

Comando:

```text
cd /home/otavio/Documents/vscode/prova-ia-v2/backend
/home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py -q
```

Resultado:

```text
8 passed, 1 warning in 0.90s
```

## Observacoes

- Nao foi iniciado servidor local.
- Tentativa de checagem de sintaxe JS por runtime foi bloqueada porque `node`,
  `nodejs`, `deno`, `bun` e `qjs` nao estao instalados.
- Proximo loop deve tratar relatorio aluno-turma sem perder a regra central:
  a unidade correta e `aluno_id + turma_id`.
