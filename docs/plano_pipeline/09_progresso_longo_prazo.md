# Painel Vivo Paulo -- NOVO CR

**Atualizado:** 2026-05-15
**Responsavel operacional:** Paulo
**Status geral:** Render oficial confirmou o marker `9e1aee5`, que aponta para
o commit funcional `7ed8b8b`. Gemini `corrigir` passou com custo medido; GPT-5
Nano agora tambem passou em `corrigir` no site oficial com JSON parseavel, PDF
via `execute_python_code`, tokens splitados e custo medido, sem PDF extra via
`create_document`. O resumo de custos agora agrega por `cost_run_id`, entao
JSON+PDF do mesmo run contam uma vez. Ainda nao ha pipeline completa validada
para Nano.

Este e o ponto de entrada do plano. O objetivo deste arquivo e dizer, em poucas
linhas, onde estamos, qual e a proxima fila e quais frentes estao pausadas.
Detalhes historicos ficam em anexos, nao aqui.

## Como Ler Esta Pasta

Leia primeiro este arquivo. Use os demais apenas quando precisar de detalhe:

- [05_visao_longo_prazo.md](05_visao_longo_prazo.md): estrategia, custos e
  roadmap tecnico.
- [12_matriz_provider_fase.md](12_matriz_provider_fase.md): testes por modelo e
  fase.
- [04_fontes_dados_governanca.md](04_fontes_dados_governanca.md): catalogo de
  dados, schemas e fontes.
- [13_plano_curto_paulo_rio3_render.md](13_plano_curto_paulo_rio3_render.md):
  plano Rio 3 preservado, mas pausado.
- [arquivo_2026_04_17](arquivo_2026_04_17): relatorios, testes e investigacoes
  historicas.
- [notas](notas): notas tecnicas pequenas.
- [rio3_pausado](rio3_pausado): pesquisa Rio 3 congelada ate nova decisao.

## Objetivo Atual

Estabilizar o NOVO CR para que a pipeline:

- rode com confiabilidade em multiplos modelos;
- gere documentos corretos e com avisos de qualidade;
- registre tokens e custos por materia/atividade/aluno;
- mostre erros de forma compreensivel na interface;
- mantenha documentacao curta o bastante para orientar decisao.

## Estado Das Frentes

| Frente | Estado | Proximo passo |
|--------|--------|---------------|
| Docs e plano | Sprint 0 concluida | Manter este painel como fonte oficial e anexos fora do fluxo diario |
| Pipeline | `corrigir` validado oficialmente para Gemini 3 Flash e GPT-5 Nano com JSON/PDF/custo | Expandir para `analisar_habilidades` e `gerar_relatorio`; validar schema minimo por etapa |
| Schema e avisos | Sprint 2 concluida localmente | Manter schema oficial, defaults e visualizador cobertos por testes |
| Custos/tokens | Metadata de documento e endpoints de custo live no deploy `7ed8b8b`; resumo agrega por `cost_run_id` | Registrar falhas sem documento final; avançar custo por contexto educacional |
| UI de erros | Pendente | Mostrar falha por aluno/etapa sem depender de terminal |
| Limpeza de dados | Pendente | Reclassificar "fantasmas" antes de qualquer delecao |
| Rio 3 | Pausada | Nao pedir chave, nao rodar smoke, nao deployar Rio sem nova decisao |

## Estado Git/Deploy Oficial

- Local funcional anterior validado: `b12be9a`.
- Commit funcional de custos/docs: `f67055c`.
- Commit funcional de erro visivel: `b4d7ee6`.
- Commit funcional de retryability: `f505be6`.
- Commit funcional de docs parciais em erro: `97a7c79`.
- Commit funcional OpenAI tool-choice/GPT-5 Nano: `ff7b92a`.
- Commit funcional de validacao de artefato persistido: `c75af88`.
- Commit funcional de JSON valido/artefato por extensao: `39aa50a`.
- Commit funcional de restricao de artefato por tool: `b24f03e`.
- Commit funcional de payload malformado em `create_document`: `eab7d90`.
- Commit funcional de resumo de custos por run: `7ed8b8b`.
- Marker mais novo publicado: `9e1aee5` (`chore: mark deploy 7ed8b8b`).
- Marker atual visto no Render: `9e1aee5`, HTML com `novocr-deploy=7ed8b8b`.
- GitHub `origin/main`: pode conter commits documentais posteriores; o ultimo
  marker funcional publicado e `9e1aee5`, e Render live esta confirmado em
  `7ed8b8b`.
- Render live observado: saiu de `2e1098f` para `b12be9a` e depois confirmou
  marcadores `b4d7ee6`, `f505be6`, `97a7c79`, `c75af88`, `39aa50a`,
  `b24f03e`, `eab7d90` e `7ed8b8b`.
- `/api/custos/status` no Render: HTTP 200, confirmando endpoints de custo live.
- GitHub Actions: sem runs recentes observaveis.
- GitHub webhooks/deployments via `gh api`: sem entradas visiveis.
- Render MCP: bloqueado por workspace nao selecionado ("no workspace set").
- Evidencia documental adicional: Doc 11 e o tutorial arquivado registram que o
  auto-deploy do Git nao funciona porque o Render foi conectado via URL publica,
  nao GitHub OAuth; o canal oficial era deploy hook, que precisa estar rotacionado
  antes de qualquer uso.
- Inferencia operacional: o deploy nao sai de forma confiavel apenas por push;
  usar deploy API/Dashboard e so aceitar smoke oficial quando o HTML live
  mostrar o marker funcional esperado.

## Loop Operacional

Cada ciclo deve seguir esta ordem:

1. Orientar: ler este painel, `git status`, matriz de providers e problema-alvo.
2. Escolher alvo: uma tese por ciclo.
3. Diagnosticar: reproduzir ou localizar causa com teste/leitura focada.
4. Corrigir: menor mudanca suficiente.
5. Validar: teste focado, `git diff --check`, `py_compile` quando Python mudar.
6. Registrar: bloco curto neste arquivo, sem criar novo doc.
7. Git/deploy: stage explicito, sem `.pytest_tmp`; deploy e segredo exigem gate.

## Fila Priorizada

### Sprint 0 -- Painel Doc 09

Objetivo: deixar o projeto navegavel antes de corrigir codigo.

Critérios de pronto:

- este arquivo e a entrada unica do plano;
- historicos estao em [arquivo_2026_04_17](arquivo_2026_04_17);
- notas pequenas estao em [notas](notas);
- Rio esta em [rio3_pausado](rio3_pausado) e marcado como pausado;
- lote Rio/codigo fica congelado e fora do commit de docs;
- links locais e `git diff --check` passam.

### Sprint 1 -- Confiabilidade Da Pipeline

Prioridade: P4, P5 e P6.

- P4: barrar `EXTRAIR_RESPOSTAS` sem `prova_respondida` valida. **Concluido em 2026-05-12.**
- P5: contencao temporaria de `nota_final`. **Concluido em 2026-05-13; nao e
  regra final aceitavel se mascarar nota ausente.**
- P6: nao descartar `_documentos_faltantes` em `gerar_relatorio`. **Concluido em 2026-05-13.**

Critério de pronto: falha clara e rastreavel, sem output silencioso ruim.

### Sprint 2 -- Schema E Avisos

Prioridade: P1, P2 e P3.

- P1: unificar schemas `PROMPTS_PADRAO` vs `STAGE_TOOL_INSTRUCTIONS`. **Concluido em 2026-05-14.**
- P2: garantir defaults `_avisos_*` no handler `create_document`. **Concluido em 2026-05-14.**
- P3: fazer o visualizador ler avisos de ANALISAR/GERAR. **Concluido em 2026-05-14.**

Critério de pronto: documentos gerados ficam consistentes e legiveis.

### Sprint 3 -- Custos/Tokens

Prioridade: corrigir medicao antes de criar dashboard.

- `ChatClient` deve retornar `input_tokens` e `output_tokens`. **Concluido em 2026-05-14.**
- `executar_com_tools` deve preencher `tokens_entrada` e `tokens_saida`. **Concluido em 2026-05-14.**
- Persistencia `TokenUsageRecord` entra so depois disso. **Proximo subciclo, nao iniciado.**

Critério de pronto: custo pode ser calculado com input/output separados.

### Sprint 4 -- UI De Erros

- Mostrar falhas por aluno e etapa.
- Exibir mensagens claras para credito insuficiente, documento faltante, modelo
  sem tools e falhas de provider.

Critério de pronto: usuario entende o que falhou sem abrir terminal.

### Sprint 5 -- Limpeza De Dados

- Reclassificar a lista historica de "fantasmas".
- Nunca deletar `prova_respondida` PDF so por `conteudo=null`.

Critério de pronto: lista de limpeza segura e revisada.

## Separacoes Importantes

### `prova_respondida`

- PDF com `conteudo=null` em `/api/documentos/{id}/conteudo` e limitacao do
  endpoint, documentada em [nota_tecnica_conteudo_pdf.md](notas/nota_tecnica_conteudo_pdf.md).
- Pipeline rodar para aluno sem `prova_respondida` valida e bug real de fluxo.
- Limpeza de dados deve verificar `download/view` e storage antes de delecao.

### Rio 3

- Rio 3 esta pausado por decisao do usuario.
- A tentativa de usar chave em chat deve ser tratada como chave exposta.
- O teste seguro feito via popup retornou `401 Token invalido ou expirado`; nenhuma
  pipeline de matematica rodou com Rio 3.
- O endpoint oficial observado usa contrato eAI Gateway, nao OpenAI-compatible
  direto; a retomada provavelmente exige adaptador.
- Arquivos de codigo/Rio ja preparados ficam congelados fora da Sprint 0.

### Git E Workspace

- O workspace esta sujo e contem muito ruido em `backend/.pytest_tmp`.
- O commit da Sprint 0 deve ser apenas documental.
- Nunca usar `git add .`.
- Antes de qualquer commit, stagear explicitamente so os arquivos do ciclo.

## Registro De Ciclos

### 2026-05-06 -- Sprint 0: Painel Doc 09

- Alvo: transformar o Doc 09 no painel vivo oficial.
- Status: concluida.
- Decisoes: docs primeiro; Rio 3 congelado; ciclos registrados somente aqui.
- Validacoes: links Markdown locais passaram; `git diff --check --cached` passou;
  raiz de `docs/plano_pipeline` ficou limitada aos docs vivos.
- Git: lote staged agora e documental; codigo/Rio permanece no worktree, fora do
  stage da Sprint 0.
- Proximo alvo depois da Sprint 0: Sprint 1, confiabilidade da pipeline.

### 2026-05-12 -- Sprint 1/P4: prova_respondida valida

- Alvo: impedir `EXTRAIR_RESPOSTAS` sem `prova_respondida` com arquivo resolvivel.
- Status: concluido localmente.
- Arquivos tocados: `backend/executor.py`, `backend/tests/unit/test_erro_pipeline.py`.
- Comportamento: fluxo completo e fluxo direto falham cedo sem prova valida; PDF
  existente e aceito sem depender de `/conteudo`; etapas nao selecionadas nao sao
  bloqueadas por falta de prova.
- Validacoes: `python -m py_compile backend/executor.py backend/tests/unit/test_erro_pipeline.py`;
  `git diff --check`; `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest backend/tests/unit/test_erro_pipeline.py -q`
  passou com 32 testes e 1 aviso de config `timeout` desconhecida.
- Git: Sprint 0 documental foi commitada em `7e4b852` antes do ciclo P4.
- Proximo alvo: Sprint 1/P5, contencao temporaria de `nota_final`.

### 2026-05-13 -- Sprint 1/P5-P6: nota_final e documentos faltantes

- Alvo: robustecer `nota_final` em `GERAR_RELATORIO` e preservar
  `_documentos_faltantes` quando o relatório não puder rodar.
- Status: concluido localmente.
- Arquivos tocados: `backend/executor.py`, `backend/tests/unit/test_erro_pipeline.py`.
- Comportamento: nota usa contencao ordenada (`nota_final`, `nota`, soma de
  `questoes[].nota`, soma de `correcoes[].nota`, `N/A`); erro de relatório
  retorna `_erro_pipeline`, `_documentos_faltantes` e `_documentos_carregados`.
- Ressalva P0: `N/A` nao pode virar sucesso silencioso no produto final; proximo
  ciclo de relatorio deve transformar nota nao confiavel em erro alto quando a
  etapa exigir nota.
- Validacoes: `python -m py_compile backend/executor.py backend/tests/unit/test_erro_pipeline.py`;
  `git diff --check`; `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest backend/tests/unit/test_erro_pipeline.py -q`
  passou com 41 testes e 1 aviso de config `timeout` desconhecida.
- Proximo alvo: Sprint 2, schema e avisos.

### 2026-05-14 -- Sprint 2/P1-P3: schema e avisos

- Alvo: alinhar o schema oficial da pipeline aos formatos reais de prompt/tool-use
  e garantir que avisos entrem no visualizador de forma consistente.
- Status: concluido localmente.
- Arquivos tocados: `backend/pipeline_validation.py`,
  `backend/visualizador.py`, `backend/tests/unit/test_pipeline_validation.py`,
  `backend/tests/unit/test_warning_system.py`,
  `backend/tests/unit/test_warning_visualizador.py`.
- Comportamento: schemas oficiais agora incluem `_avisos_*`, aceitam os formatos
  tool-use de CORRIGIR/ANALISAR/GERAR e expõem `_fontes_utilizadas`; o
  visualizador acumula avisos vindos de correção, análise e relatório, preservando
  a etapa de origem para severidade.
- Validacoes: `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest backend/tests/unit/test_pipeline_validation.py backend/tests/unit/test_schemas_narrativos.py backend/tests/unit/test_warning_system.py backend/tests/unit/test_warning_visualizador.py backend/tests/unit/test_warning_badge_ui.py -q`
  passou com 130 testes, 3 skipped e 1 aviso de config `timeout` desconhecida.
- Proximo alvo: Sprint 3, custos/tokens.

### 2026-05-14 -- Sprint 3: tokens input/output

- Alvo: separar tokens de entrada e saida antes de qualquer calculo/persistencia de custo.
- Status: concluido localmente no nivel de medicao.
- Arquivos tocados: `backend/chat_service.py`, `backend/executor.py`,
  `backend/tests/unit/test_api_keys.py`,
  `backend/tests/unit/test_d_t1_openai_tool_use.py`,
  `backend/tests/unit/test_d_t2_google_tool_use.py`,
  `backend/tests/unit/test_f2_desempenho_resposta_raw.py`.
- Comportamento: `ChatClient` preserva `tokens` total e tambem retorna
  `input_tokens`/`output_tokens` para OpenAI, Anthropic, Google, Ollama e
  endpoints OpenAI-compatible; tool-use acumula input/output por iteracao;
  `executar_com_tools` popula `tokens_entrada` e `tokens_saida`.
- Validacoes: `python -m py_compile` dos arquivos Python tocados; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest backend/tests/unit/test_api_keys.py::TestChatClientTokenUsage backend/tests/unit/test_d_t1_openai_tool_use.py backend/tests/unit/test_d_t2_google_tool_use.py backend/tests/unit/test_f2_desempenho_resposta_raw.py -q`
  passou com 24 testes e 1 aviso de config `timeout` desconhecida.
- Proximo alvo: planejar persistencia `TokenUsageRecord` ou entrar na Sprint 4
  de UI de erros, conforme risco escolhido no proximo ciclo.

### 2026-05-15 -- Oficializacao parcial + Sprint 3b: metadata/custos

- Alvo: parar de tratar local como oficial, publicar commits locais e iniciar
  custo medido consultavel.
- Status: GitHub atualizado; Render ainda bloqueado/stale; codigo de custos
  validado localmente.
- Git: `b12be9a` foi empurrado; depois `f67055c` adicionou custos/metadata; o
  marcador `462ea1d` aponta o HTML para `f67055c`; registros documentais podem
  estar acima dele sem mudar o marcador.
- Deploy: `wait_deploy.sh b12be9a` deu timeout apos 900s, mas depois o live
  avancou para marcador `b12be9a`; checks diretos para `f67055c` ainda falham.
  O backend ja responde `/api/custos/status`, entao ha deploy parcial/atraso de
  marcador. Sem Actions, webhooks ou deployments GitHub visiveis; Render MCP sem
  workspace.
- Arquivos tocados: `backend/storage.py`, `backend/executor.py`,
  `backend/tool_handlers.py`, `backend/tools.py`, `backend/model_catalog.py`,
  `backend/cost_tracking.py`, `backend/routes_costs.py`, `backend/main_v2.py`,
  `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: documentos de IA passam a receber provider/modelo/prompt,
  `tokens_usados`, tempo e metadata com `tokens_entrada`/`tokens_saida`;
  documentos criados por tools compartilham `cost_run_id`; `/api/custos/status`
  e `/api/custos/resumo` expõem custo medido somente quando ha split real e
  precificacao no catalogo.
- Regra P0 aplicada: PDF obrigatorio ausente em dual-output agora falha alto;
  o backend nao gera PDF automatico para fingir sucesso.
- Smoke live de chat: Gemini 3 Flash respondeu JSON simples com 585 tokens;
  GPT-5 Nano respondeu JSON simples com 526 tokens; Claude Haiku 4.5 falhou por
  credito Anthropic baixo. Estes smokes confirmam conexao de chat, nao pipeline.
- Smoke live de pipeline: `pipeline-completo` com Gemini 3 Flash, aluno Eric,
  `selected_steps=["corrigir"]`, task `task_e22dbdbffe4d`, falhou com
  `corrigir=failed`. A rota `/api/task-progress/{task_id}` nao trouxe campo
  `error`, entao o usuario veria falha sem causa. Isso rebaixa Gemini para
  "chat OK, pipeline pos-fix nao confirmado" e cria bloqueador de UI/observabilidade.
- Smoke live de custos: `/api/custos/status` HTTP 200 com Supabase/postgresql e
  catalogo carregado; resumo apontou 500 documentos bloqueados para custo
  medido porque historico antigo nao tem split ou provider/modelo.
- Validacoes: `py_compile` dos arquivos tocados passou; `git diff --check`
  passou; `pytest backend/tests/unit/test_cost_tracking.py -q` passou com 4
  testes; suite focada ampliada passou com 171 testes, 5 skipped e 1 aviso de
  config `timeout` desconhecida; TestClient confirmou `/api/custos/status` e
  `/api/custos/resumo` com HTTP 200 local.
- Proximo alvo: esperar/acionar o marcador `f67055c` e rodar smoke provider que
  gere documento novo, para confirmar metadata/custo de execucao fresca.

### 2026-05-15 -- Sprint 4a: erro visivel em task-progress

- Alvo: corrigir o bloqueador descoberto no smoke live de pipeline: task marcada
  como `failed` sem causa visivel para a UI.
- Status: patch local pronto para validacao/commit.
- Arquivos tocados: `backend/executor.py`, `frontend/index_v2.html`,
  `backend/tests/unit/test_erro_pipeline.py`,
  `backend/tests/unit/test_notification_wiring.py`,
  `backend/tests/unit/test_a4_render_tarefas_tree.py`.
- Comportamento: falhas de etapa agora chamam `complete_pipeline_task(...,
  error=...)`; o toast de pipeline falho usa `data.error`; a arvore de tarefas
  mostra `task.error` em bloco vermelho. Falha ao carregar documentos tambem
  encerra a task como erro, em vez de deixa-la silenciosa.
- Git: commit funcional `b4d7ee6`; marker `99483d1`; ambos publicados em
  `origin/main`.
- Deploy: `wait_deploy.sh b4d7ee6` encontrou o marker apos cerca de 140s;
  `check_deploy.sh b4d7ee6` passou; `/api/health` retornou healthy/Supabase true;
  `/api/custos/status` retornou HTTP 200.
- Smoke oficial: `pipeline-completo` com Gemini 3 Flash, aluno Eric,
  `selected_steps=["corrigir"]`, task `task_08d4648d7053`, falhou alto em
  `corrigir` com `error` exposto: Google API 503 `UNAVAILABLE`, modelo em alta
  demanda temporaria.
- Validacoes: `py_compile` dos arquivos Python tocados passou; `git diff --check`
  passou; suite focada de executor/task/progresso/UI/custo passou com 88 testes
  e 1 aviso de config `timeout` desconhecida.
- Proximo alvo: corrigir/classificar retry visivel para 429/5xx no caminho
  tool-use ou repetir smoke quando a sobrecarga Gemini passar; nao promover
  Gemini pipeline enquanto `corrigir` falhar.

### 2026-05-15 -- Sprint 4b: retryability de provider no tool-use

- Alvo: transformar o 503 Google descoberto no smoke em erro retryable, sem
  trocar de modelo/provider e sem mascarar a falha.
- Status: publicado e deployado.
- Arquivos tocados: `backend/chat_service.py`, `backend/executor.py`,
  `backend/tests/unit/test_cost_tracking.py`,
  `backend/tests/unit/test_d_t2_google_tool_use.py`.
- Comportamento: erros HTTP de tool-use agora usam `ProviderAPIError` com
  `status_code` e `retryable`; Google/OpenAI/Anthropic preservam 429/5xx como
  retryable; `executar_com_tools` devolve `ResultadoExecucao` com
  `erro_codigo=503` e `retryable=True`, permitindo que o orquestrador retente no
  mesmo modelo de forma visivel.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada de
  executor/task/progresso/UI/custo/Google tool-use passou com 99 testes e 1
  aviso de config `timeout` desconhecida.
- Git/deploy: commit funcional `f505be6`; marker `d75b05a`; Render confirmou
  `f505be6`.
- Smoke oficial: Gemini 3 Flash em `corrigir`, task `task_8f53987c57c4`,
  completou; criou JSON `6396c4feb3d5b92b` e PDF `6c62faa4ce6df137` com
  provider/modelo/tokens/custo.
- Custo medido: 16.639 tokens entrada, 2.449 saida, 19.088 total,
  custo estimado/medido `US$ 0.007931` para `google/gemini-3-flash-preview`.
- Proximo alvo: expandir smoke para `analisar_habilidades`/`gerar_relatorio` e
  confirmar custo/metadata por etapa.

### 2026-05-15 -- Sprint 4c: docs parciais de tool-use em erro

- Alvo: impedir que documentos criados por tools fiquem `concluido` quando uma
  chamada posterior do provider falha antes da etapa terminar.
- Evidencia: o smoke anterior gerou documentos `correcao` com provider/modelo,
  mas `tokens_usados=0`, status `concluido` e custo bloqueado por
  `token_split_missing`; isso pode acontecer quando tools salvam JSON/PDF e a
  chamada final do provider falha.
- Status: publicado e deployado.
- Arquivos tocados: `backend/executor.py`, `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: se `ProviderAPIError` acontecer depois de tools criarem
  documentos, o executor marca cada `created_document_id` como
  `StatusProcessamento.ERRO` e grava `erro_pipeline`/`cost_run_id` no metadata.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada de
  executor/task/progresso/UI/custo/Google tool-use passou com 99 testes e 1
  aviso de config `timeout` desconhecida.
- Git/deploy: commit funcional `97a7c79`; marker `ec95193`; Render confirmou
  `97a7c79`.
- Smoke relacionado: GPT-5 Nano em `corrigir`, task `task_49b7ada546d4`, falhou
  alto com "Saida obrigatoria incompleta: JSON via create_document, PDF via
  execute_python_code"; nenhum fallback de PDF/JSON foi inventado.
- Proximo alvo: registrar custos de falhas que consomem tokens mesmo quando nao
  ha documento final criado.

### 2026-05-15 -- Sprint 4d: OpenAI tool-choice para GPT-5 Nano

- Alvo: corrigir a falha do GPT-5 Nano em `corrigir`, onde o modelo respondia
  sem produzir JSON+PDF obrigatorios por tools.
- Status: publicado no GitHub, **nao deployado oficialmente**.
- Arquivos tocados: `backend/chat_service.py`, `backend/executor.py`,
  `backend/ai_providers.py`, `backend/anexos.py`, `backend/data/model_catalog.json`,
  `backend/docs/MODELS_REFERENCE.md` e testes unitarios de OpenAI/tool-use/P0.
- Comportamento: chamadas OpenAI de dual-output agora iniciam com
  `tool_choice="required"`; o retry explicito no mesmo modelo forca a tool
  faltante quando ela e conhecida; se mesmo assim faltar JSON/PDF, a etapa falha
  alto, sem fallback automatico. Catalogo/listas de reasoning receberam
  `gpt-5.4*` e `gpt-5.5*` com referencias oficiais OpenAI documentadas.
- Validacoes locais: `py_compile` passou; `git diff --check` passou; JSON do
  catalogo validou; suite focada passou com 147 testes e 1 aviso de config
  `timeout` desconhecida.
- Git: commit funcional `ff7b92a`; marker `68ebe51`; ambos publicados em
  `origin/main`.
- Deploy: `check_deploy.sh ff7b92a` falhou; Render live ainda mostra `97a7c79`.
  `GET /api/health` segue healthy/Supabase true, mas no codigo antigo.
- Evidencia do bloqueio: `gh run list` sem runs; `gh api deployments` e
  `gh api hooks` retornaram listas vazias; Render MCP respondeu "no workspace
  set" e nao permitiu listar/acessar o servico `prova-ai`; docs antigos dizem
  que auto-deploy Git nao funciona e que o hook seguro precisa estar rotacionado.
- Proximo alvo: desbloquear deploy Render por Dashboard/workspace/hook seguro.
  Nao rodar smoke GPT-5 Nano como oficial ate o marker live mostrar `ff7b92a`.

### 2026-05-15 -- Sprint 4e: artefato persistido obrigatorio

- Alvo: corrigir o falso sucesso descoberto no smoke live do GPT-5 Nano, onde a
  task completou com JSON novo, mas sem PDF persistido.
- Status: publicado, deployado e smokeado.
- Arquivos tocados: `backend/chat_service.py`, `backend/executor.py`,
  `backend/tools.py`, `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: `chat_with_tools` registra `is_error` e `files_generated` das
  tools sem ecoar base64; `executar_com_tools` nao aceita mais apenas o nome da
  tool. Para etapa dual-output, precisa haver artefato persistido por
  `create_document` e por `execute_python_code`; se faltar, ha retry explicito
  no mesmo modelo e depois erro alto.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada
  passou com 180 testes e 1 aviso de config `timeout` desconhecida. Suite
  unitária ampla continua vermelha por 49 falhas antigas/stale fora deste ciclo.
- Git/deploy: commit funcional `c75af88`; marker `45d543a`; Render confirmou
  `c75af88` via `wait_deploy.sh`/`check_deploy.sh`; `/api/health` healthy.
- Smoke oficial: GPT-5 Nano em `corrigir`, task `task_edb822810ddc`, completou
  e criou PDF por `execute_python_code` (`a2533557b2ef2712`), mas o JSON
  principal `2a272f58b1f5ecce` nao era parseavel (`Invalid control character`).
  Isso revelou o proximo bloqueador: artefato existe nao basta; JSON precisa
  validar antes de sucesso.

### 2026-05-15 -- Sprint 4f: JSON invalido nao entra no storage

- Alvo: impedir `completed` quando `create_document` salva `.json` invalido.
- Status: publicado, deployado e smokeado.
- Arquivos tocados: `backend/tool_handlers.py`, `backend/executor.py`,
  `backend/tests/unit/test_warning_system.py`,
  `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: `handle_create_document` valida `.json` com `json.loads` antes
  de salvar; erro de JSON torna a tool `is_error=True`; o executor exige
  `create_document` com extensao `.json` e `execute_python_code` com extensao
  `.pdf` para concluir etapa dual-output.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada
  passou com 180 testes e 1 aviso de config `timeout` desconhecida.
- Git/deploy: commit funcional `39aa50a`; marker `3ddf6c5`; Render confirmou
  `39aa50a`; `/api/health` healthy.
- Smoke oficial: GPT-5 Nano em `corrigir`, task `task_1a7857360267`, completou.
  Run `tool_e42200b613f0` criou JSON parseavel `d3a4be288960e301` via
  `create_document` e PDF `3e0d534238dc0067` via `execute_python_code`.
  Tokens/custo: 20.127 entrada, 6.817 saida, 26.944 total, custo estimado
  `US$ 0.003733` para `openai/gpt-5-nano`.
- Observacao: o Nano tambem criou um PDF extra via `create_document`
  (`29d20245529f26a7`). Nao bloqueou o smoke porque o PDF obrigatorio veio pela
  tool correta, mas o proximo ciclo deve decidir se `create_document` fica
  restrito a `.json` nas etapas dual-output.
- Custos live apos smoke: `/api/custos/status` retornou `runs_precificados=4`,
  `runs_bloqueados=491`, com bloqueios `token_split_missing=165` e
  `provider_model_missing=326`.
- Proximo alvo: expandir smoke para `analisar_habilidades`/`gerar_relatorio`
  com Gemini e Nano, ou antes endurecer a regra de artefato extra em
  `create_document`.

### 2026-05-15 -- Sprint 4g: `create_document` restrito a JSON em pipeline

- Alvo: impedir que `create_document` crie PDF/artefato extra em etapas
  dual-output; PDF obrigatorio deve vir de `execute_python_code`.
- Status: publicado, deployado e smokeado; revelou novo bug.
- Arquivos tocados: `backend/chat_service.py`, `backend/tool_handlers.py`,
  `backend/tests/unit/test_warning_system.py`.
- Comportamento: quando `ToolContext.expected_document_type` esta ativo,
  `create_document` rejeita documento nao-JSON; artefatos gerados por tools
  carregam `is_error` e resumo de arquivos para o executor decidir sem ler base64.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada
  passou com 99 testes e 1 aviso de config `timeout` desconhecida.
- Git/deploy: commit funcional `b24f03e`; marker `6ed31a4`; Render confirmou
  `b24f03e`; `/api/health` healthy.
- Smoke oficial: GPT-5 Nano em `corrigir`, task `task_c460627779fc`, falhou sem
  falso sucesso. A falha exposta foi interna demais: `tools: 'str' object has no
  attribute 'get'`, causada por payload malformado em `documents`.
- Proximo alvo: transformar payload malformado em erro estruturado da tool, nao
  excecao Python crua.

### 2026-05-15 -- Sprint 4h: payload malformado vira erro seguro

- Alvo: `create_document` nao pode quebrar com `.get` em string quando o modelo
  manda `documents` fora do contrato; deve falhar alto, estruturado e rastreavel.
- Status: publicado, deployado e smokeado.
- Arquivos tocados: `backend/tool_handlers.py`,
  `backend/tests/unit/test_warning_system.py`.
- Comportamento: `handle_create_document` normaliza `documents`, rejeita array
  com item nao-objeto, marca `is_error=True` e devolve erro claro sem salvar lixo.
- Validacoes: `py_compile` passou; `git diff --check` passou; suite focada
  passou com 100 testes e 1 aviso de config `timeout` desconhecida.
- Git/deploy: commit funcional `eab7d90`; marker `dcecdfa`; Render confirmou
  `eab7d90` via `wait_deploy.sh`, `check_deploy.sh` e `/api/health`.
- Smoke oficial: GPT-5 Nano em `corrigir`, task `task_a591421ab84b`, completou.
  Run `tool_056e2e1f7179` criou JSON parseavel `42dc1fcd758e913b` via
  `create_document` e PDF `cd72e7233ee061ad` via `execute_python_code`.
  Nao houve PDF extra via `create_document`.
- Tokens/custo do run: 16.081 entrada, 3.470 saida, 19.551 total, custo estimado
  `US$ 0.002192` para `openai/gpt-5-nano`.
- Custos live apos smoke: `/api/custos/status` retornou `runs_precificados=5`,
  `runs_bloqueados=489`, com bloqueios `token_split_missing=166` e
  `provider_model_missing=323`.
- Novo achado: `/api/custos/resumo` lista o JSON e o PDF do mesmo
  `cost_run_id=tool_056e2e1f7179`, ambos com o mesmo custo. O proximo ciclo deve
  auditar se o resumo soma por documento ou por run, para nao duplicar custo.

### 2026-05-15 -- Sprint 3c: custo agrupado por `cost_run_id`

- Alvo: impedir que o resumo de custos exponha JSON e PDF do mesmo run como se
  fossem duas execucoes separadas.
- Status: publicado, deployado e smokeado.
- Arquivos tocados: `backend/cost_tracking.py`, `backend/routes_costs.py`,
  `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: `build_cost_summary()` agrupa documentos por `cost_run_id`;
  JSON+PDF de um run contam uma vez; `amostras` agora trazem `documentos_ids`,
  `documentos_contagem` e um custo por run; conflitos de metadata no mesmo run
  viram bloqueio `run_metadata_conflict`.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_cost_tracking.py` passou com 9 testes e 1 aviso de config `timeout`
  desconhecida.
- Git/deploy: commit funcional `7ed8b8b`; marker `9e1aee5`; Render confirmou
  `7ed8b8b` via `wait_deploy.sh` e `check_deploy.sh`; `/api/health` healthy.
- Smoke oficial de custos: `/api/custos/status?limit=500` retornou
  `runs_analisados=492`, `runs_precificados=5`, `runs_bloqueados=487` e
  `alertas=[]`.
- Smoke oficial de resumo: `/api/custos/resumo?limit=500` retornou
  `documentos_analisados=500`, `runs_analisados=492`, `tokens_entrada=86252`,
  `tokens_saida=19786` e `custo_usd=0.018347`.
- Evidencia do ultimo Nano: `cost_run_id=tool_056e2e1f7179` aparece uma vez com
  `documentos_contagem=2`, documentos `cd72e7233ee061ad` e
  `42dc1fcd758e913b`, custo `US$ 0.002192`.
- Proximo alvo: registrar custos de falhas sem documento final e/ou avançar
  revalidacao de `analisar_habilidades`/`gerar_relatorio` por provider.

## Riscos Abertos

1. Creditos Anthropic insuficientes ainda bloqueiam validacao Haiku.
2. Schema drift pode fazer modelos gerarem formatos diferentes.
3. Schema minimo ainda nao esta validado para todas as etapas; JSON parseavel e
   necessario, mas nao prova qualidade pedagogica.
4. Falhas sem documento final ainda nao entram no resumo de custos; precisamos
   de registro proprio de run/custo para erro sem artefato.
5. Rio 3 nao deve voltar ao fluxo ativo sem nova decisao e nova chave segura.
