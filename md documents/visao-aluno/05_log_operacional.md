# 05 — Log Operacional

Timeline viva da frente.

| Timestamp | Acao | Resultado |
|---|---|---|
| 2026-06-05 10:51 BRT | Criado pacote `md documents/visao-aluno/` | Base documental inicial criada. Nenhum codigo de produto alterado. |
| 2026-06-05 10:55 BRT | Compactados os documentos | Conteudo reduzido, mas ainda com documentos demais. |
| 2026-06-05 11:00 BRT | Consolidado em documento-mestre unico | `00_indice_e_estado.md` virou a fonte principal do loop; documentos 01-04 removidos. |
| 2026-06-05 16:45 BRT | Documento-mestre convertido em painel de execucao | Topo agora define objetivo, proximo passo, primeiro patch, nao fazer ainda e checklist executavel. |
| 2026-06-05 17:00 BRT | Implementado MVP backend da visao aluno | `StorageManager.get_visao_aluno()` e `GET /api/alunos/{aluno_id}/visao` criados. A resposta preserva `aluno + turma`, agrupa por materia e filtra documentos do proprio aluno. |
| 2026-06-05 17:00 BRT | Implementada UI basica da visao aluno | `showAluno()` agora usa `/api/alunos/{aluno_id}/visao` e renderiza materia > turma > atividade > status individual. |
| 2026-06-05 17:00 BRT | Validacao focada do Loop 1 | `cd backend && /home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py -q` passou com 8 testes. Checagem JS por runtime nao rodou porque nao ha `node`, `nodejs`, `deno`, `bun` ou `qjs` instalado. |
| 2026-06-05 17:05 BRT | Implementada base de leitura aluno-turma | Criado `GET /api/desempenho/aluno/{aluno_id}/turma/{turma_id}` em `routes_extras.py`. O endpoint valida vinculo, filtra atividades da turma, filtra documentos do proprio aluno e retorna `base_minima`. |
| 2026-06-05 17:05 BRT | Validacao focada do Loop 2 | `cd backend && /home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q` passou com 39 testes. |
| 2026-06-05 17:06 BRT | Ajustada visao aluno para historico | `get_visao_aluno()` passou a usar `get_turmas_do_aluno(apenas_ativas=False)`, mantendo turmas historicas/inativas que o aluno participou. Teste novo cobre esse caso. |
| 2026-06-05 17:12 BRT | Implementada geracao deterministica aluno-turma | Adicionado `TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA` e `POST /api/executar/pipeline-desempenho-aluno-turma`. O endpoint salva Markdown com metadata `scope/aluno_id/turma_id/materia_id/atividade_ids`, bloqueia sem `relatorio_final` e nao duplica sem `force_reexec`. |
| 2026-06-05 17:12 BRT | Validacao focada do Loop 3 | `cd backend && /home/otavio/Documents/vscode/.venv/bin/python -m pytest tests/integration/test_visao_aluno_endpoint.py tests/unit/test_visao_aluno_frontend.py tests/integration/test_desempenho_aluno_turma_endpoint.py tests/unit/test_desempenho_api_endpoints.py -q` passou com 41 testes. `py_compile` tambem passou para `models.py`, `storage.py`, `routes_extras.py`, `routes_prompts.py`, `main_v2.py`. |

## Regra Do Log

Cada nova entrada deve ter timestamp, acao concreta, resultado e evidencia quando existir.
