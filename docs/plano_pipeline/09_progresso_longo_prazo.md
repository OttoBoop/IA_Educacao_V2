# Painel Vivo Paulo -- NOVO CR

**Atualizado:** 2026-05-16
**Responsavel operacional:** Paulo
**Status geral:** o servico oficial Render
`srv-d5t8gbh4tr6s738fr3s0` (`IA_Educacao_V2`, branch `main`, URL
`https://ia-educacao-v2.onrender.com`) esta em `2cad38a`, confirmado por
`/api/deploy-info` com `source=RENDER_GIT_COMMIT`. O site oficial completou uma
pipeline de 6 etapas em producao com GPT-5.4 Mini (`gpt54mini001`) na atividade
`Smoke Paulo Pipeline 2026-05-16`: task `task_a5f0d734f0b3`, aluna Diana Omega,
hash live `2cad38a`, etapas `extrair_questoes`, `extrair_gabarito`,
`extrair_respostas`, `corrigir`, `analisar_habilidades` e `gerar_relatorio`
marcadas como `completed`. Este e o primeiro smoke full recente em que o mesmo
modelo OpenAI versionado completou as 6 etapas no Render oficial com documentos
e custos medidos. Ele nao substitui a matriz completa de providers nem valida
todos os datasets reais.

A sequencia que destravou esse ponto foi:

- `5a3daca`: alinhou prompts OpenAI para dual-output via tools.
- `92bd095`: afrouxou o schema de `content` para JSON de artefato, sem voltar a
  aceitar sucesso silencioso.
- `f6b040c`: corrigiu o schema OpenAI `array` que faltava `items`.
- `2cad38a`: passou a falhar alto quando `create_document` e chamado mas o
  storage nao persiste o artefato obrigatorio.

Antes do sucesso, tres smokes oficiais falharam por motivos uteis e agora
registrados: `task_04bfc1bbe616` ainda falhava em `analisar_habilidades`;
`task_a1977746ef2f` expôs erro OpenAI 400 por schema invalido; e
`task_200440ba527e` expôs chamadas `create_document` sem artefato persistido.
Esses erros nao foram escondidos por fallback de modelo.

Custos do smoke completo GPT-5.4 Mini aparecem no endpoint live por
`cost_run_id`, provider/modelo e tokens splitados. Evidencia principal:
`extrair_questoes` doc `f65318c550a76842` (`1150/322`, `US$ 0.002312`);
`extrair_gabarito` doc `70df18512be9c617` (`1813/311`, `US$ 0.002759`);
`extrair_respostas` doc `14ca81d800de2648` (`2042/250`, `US$ 0.002657`);
`corrigir` docs `2c7cd4cf9eb85e57`/`769744b6fff6f3b9` (`18480/2731`,
`US$ 0.026149`); `analisar_habilidades` docs `12b24cd992477eab`/
`15579ed3ad2614be` (`10627/2111`, `US$ 0.017470`); `gerar_relatorio` docs
`38686372cb8ea981`/`37b0c86cee879ced` (`16246/3462`, `US$ 0.027763`). O custo
somado das 6 etapas desse smoke e aproximadamente `US$ 0.079110`; o resumo
live com `limit=8` mostrou `runs_precificados=5`, `runs_bloqueados=0` e
`custo_usd=0.076798`, porque a janela nao inclui todas as extracoes.

Bloqueio de custos ainda aberto: o endpoint live continua confirmando que
`public.token_usage` nao existe no Supabase (`PGRST205`), com
`token_usage_backend.durable=false` e `local_record_count=0`. Portanto custo em
documentos recentes esta medido, mas registro duravel de falhas sem documento
ainda depende de aplicar `backend/migrations/002_create_token_usage.sql`.

Inspeção semantica inicial dos JSONs do mesmo smoke tambem passou: 4 questoes,
4 respostas de gabarito, 4 respostas da aluna, correcao `8/10` por erro na
porcentagem da questao 3, analise de habilidades coerente e relatorio alinhado.
Rio 3 segue pausado. O loop ativo e pipeline oficial, providers existentes,
custos, erro alto e deploy confirmado. A checagem dos PDFs confirmou download
HTTP 200 e texto extraivel, mas achou dois ajustes: o PDF de correcao pode
cortar feedback longo em tabela estreita, e o relatorio misturou `8/10` com
`75% de proficiencia geral` de modo potencialmente confuso. O patch local
reforca as instrucoes de `execute_python_code` para PDFs nao truncarem texto e
para nota/proficiencia serem metricas separadas. Proximos alvos reais:
aplicar/validar `token_usage` duravel; revalidar matriz de providers (Gemini,
Nano, Haiku quando houver credito, GPT-4o explicito); deployar/revalidar o patch
PDF; e melhorar UI de erros para que o usuario veja aluno, etapa, provider,
custo e causa sem abrir terminal.

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
| Pipeline | GPT-5.4 Mini (`gpt54mini001`) completou as 6 etapas no site oficial em `task_a5f0d734f0b3`, Render hash `2cad38a`, com documentos, custos e inspeção semantica inicial coerente nos JSONs; PDFs baixam e têm texto, mas o patch local endurece layout/metricas; Gemini 3 Flash segue validado em etapas individuais, mas pipeline sequencial bateu quota `429`; GPT-5 Nano segue validado em `extrair_questoes`, `extrair_gabarito` e smokes de etapas finais, mas `extrair_respostas` Nano continua ❌ por qualidade; `task_bc6cc84d10ef` permanece evidencia historica de que `completed` pode ser semanticamente invalido se gabarito/conteudo falhar | Deployar/revalidar patch PDF, repetir matriz por provider/modelo e manter bloqueio P0: nao aceitar `completed` sem documento, schema, custo e conteudo minimo |
| Schema e avisos | Sprint 2 concluida localmente | Manter schema oficial, defaults e visualizador cobertos por testes |
| Custos/tokens | Metadata de documento, endpoints live, resumo por `cost_run_id`, `TokenUsageRecord` local, migration Supabase dedicada `b2dc88b`; smoke full GPT-5.4 Mini `task_a5f0d734f0b3` registrou custo medido por etapa: `US$ 0.002312`, `US$ 0.002759`, `US$ 0.002657`, `US$ 0.026149`, `US$ 0.017470` e `US$ 0.027763`, total aproximado `US$ 0.079110`; `/api/custos/resumo?limit=8` mostrou `runs_precificados=5`, `runs_bloqueados=0`, `tokens_entrada=49208`, `tokens_saida=8865`, `custo_usd=0.076798`; diagnostico live ainda acusa `PGRST205`, `durable=false` e `local_record_count=0`, provando que o fallback local de `TokenUsageRecord` nao sobrevive deploy | Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase; revalidar ate `token_usage_backend.durable=true`; depois persistir custos de falhas sem documento |
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
- Commit funcional de `TokenUsageRecord` para falhas sem documento: `839968e`.
- Commit funcional de preparo Supabase `token_usage`: `55e168a`.
- Commit funcional de diagnostico backend `token_usage`: `4f27dae`.
- Commit de migration dedicada `token_usage`: `b2dc88b` (GitHub; nao muda o
  runtime do site ate a SQL ser aplicada no Supabase).
- Commit funcional de retry/contexto Nano: `924fd79`.
- Commit funcional de rejeicao de placeholder em analise Nano: `d653c13`.
- Commit funcional de tarefa longa destacada da requisicao: `f55e299`.
- Commit funcional de bloqueio de rotas legadas sincrônicas: `e6060e1`.
- Commit funcional de guard anti-gabarito-tudo-`MISSING_CONTENT` e remocao do
  fallback Markdown em relatorio: `5527e26`.
- Commit funcional de guard anti-respostas-tudo-`ilegivel`: `8dd6c54`
  (insuficiente sozinho; o modelo passou a salvar tudo vazio).
- Commit funcional de guard anti-respostas-sem-conteudo em
  `pipeline_validation`: `c1598b9` (insuficiente sozinho; a validacao Pydantic
  nao cobria o caminho real do executor multimodal).
- Commit funcional de bloqueio anti-respostas-sem-conteudo no executor:
  `01fb04c` (Render live e smoke oficial falhando alto).
- Commit funcional de alinhamento OpenAI dual-output: `5a3daca`.
- Commit funcional de schema flexivel para artefato JSON OpenAI: `92bd095`
  (primeira versao ainda expôs schema 400 por array sem `items`).
- Commit funcional de schema OpenAI array valido: `f6b040c`.
- Commit funcional de falha alta quando tool chama `create_document` mas storage
  nao persiste o artefato obrigatorio: `2cad38a` (Render live e smoke full
  `task_a5f0d734f0b3` completo nas 6 etapas com GPT-5.4 Mini).
- Marker mais novo publicado no GitHub para runtime: `a7dead3`
  (`chore: mark deploy e6060e1`).
- Marker mais novo publicado no GitHub para o guard: `2792d89`
  (`chore: mark deploy 5527e26`).
- Render em 2026-05-16: servico oficial `srv-d5t8gbh4tr6s738fr3s0`, branch
  `main`, repo `https://github.com/OttoBoop/IA_Educacao_V2`, `rootDir=backend`,
  autoDeploy `yes`; `/api/deploy-info` confirmou `2cad38a` com
  `source=RENDER_GIT_COMMIT`.
- Marker HTML pode ficar atrasado em commits de docs/frontend; o gate oficial
  para backend agora e `/api/deploy-info` + smoke live, nao apenas marcador HTML.
- GitHub `origin/main`: alinhado com `2cad38a` antes do ciclo documental atual.
- Render live observado: saiu de `2e1098f` para `b12be9a` e depois confirmou
  marcadores/fixes sucessivos ate `2cad38a`.
- `/api/custos/status` no Render: HTTP 200, confirmando endpoints de custo live.
- GitHub Actions: sem runs recentes observaveis.
- GitHub webhooks/deployments via `gh api`: sem entradas visiveis.
- Render MCP: workspace `tea-d5ruvqu3jp1c73dudl7g` selecionado e lista de
  servicos disponivel. As ferramentas atuais listam deploys e servicos; nao ha
  ferramenta explicita de "trigger deploy".
- Inferencia operacional atualizada: push para `main` dispara deploy de commits
  com impacto em `backend`, mas marker HTML pode ficar atrasado. Aceitar smoke
  oficial somente com deploy Render MCP ou comportamento live equivalente, nao
  apenas com HTML marker.

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
- Persistencia `TokenUsageRecord`: primeira versao local mensal concluida em
  2026-05-15; migracao Supabase/persistencia duravel ainda pendente.

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
- Proximo alvo: migrar `TokenUsageRecord` para persistencia duravel ou entrar
  na Sprint 4 de UI de erros, conforme risco escolhido no proximo ciclo.

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

### 2026-05-15 -- Sprint 3d: `TokenUsageRecord` para falhas sem documento

- Alvo: quando uma chamada tool-use consome tokens e falha antes de salvar
  qualquer documento, o custo nao pode sumir.
- Status: publicado, deployado e smokeado em estrutura; ainda sem amostra real
  de falha sem documento depois do deploy.
- Arquivos tocados: `backend/token_usage.py`, `backend/cost_tracking.py`,
  `backend/routes_costs.py`, `backend/executor.py`,
  `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: falha dual-output sem documento grava `TokenUsageRecord` mensal
  em `data/token_usage/YYYY-MM.json`; falha com documento parcial marca o
  documento como `ERRO` e preenche provider/modelo/tokens/cost_run_id; o resumo
  de custos inclui registros sem documento e deduplica quando record e documento
  compartilham `cost_run_id`.
- Protecao extra: leitura de `documents` malformado no executor nao chama `.get`
  em string.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_cost_tracking.py` passou com 12 testes; `test_warning_system.py` passou
  com 74 testes; `test_erro_pipeline.py` passou com 42 testes. Todos com 1 aviso
  conhecido de config `timeout` desconhecida.
- Git/deploy: commit funcional `839968e`; marker `45c6f97`; Render confirmou
  `839968e` via `wait_deploy.sh` e `check_deploy.sh`; `/api/health` healthy.
- Smoke oficial de custos: `/api/custos/status?limit=500` retornou
  `token_usage_analisados=0`, `runs_analisados=492`, `runs_precificados=5`,
  `runs_bloqueados=487`, `alertas=[]`.
- Interpretacao: `token_usage_analisados=0` significa que ainda nao houve nova
  falha sem documento registrada apos o deploy; o caminho esta pronto e coberto
  por teste local.
- Limite conhecido: `TokenUsageRecord` ainda e arquivo local mensal. Para custo
  historico duravel em producao, o proximo passo e tabela Supabase `token_usage`
  ou mecanismo persistente equivalente.

### 2026-05-15 -- Sprint 3e: preparo Supabase para `token_usage`

- Alvo: deixar o registro de falha sem documento pronto para persistencia duravel
  quando a tabela Supabase existir, sem quebrar o fallback local.
- Status: publicado, deployado e smokeado; migration criada, aplicacao live da
  tabela ainda nao confirmada.
- Arquivos tocados: `backend/token_usage.py`,
  `backend/migrations/001_create_tables.sql`,
  `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: `TokenUsageStore` tenta inserir/listar em Supabase
  `token_usage`; se a tabela nao existir ou o insert falhar, grava no JSON local
  mensal. A migration declara `token_usage` com `cost_run_id`, provider/modelo,
  tokens, status, erro, retry, tentativas, tempo e metadata.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_cost_tracking.py` passou com 12 testes e 1 aviso conhecido de config
  `timeout` desconhecida.
- Git/deploy: commit funcional `55e168a`; marker `9823afb`; Render confirmou
  `55e168a` via `wait_deploy.sh` e `check_deploy.sh`; `/api/health` healthy.
- Smoke oficial de custos: `/api/custos/status?limit=500` retornou
  `token_usage_analisados=0`, `runs_analisados=492`, `runs_precificados=5`,
  `runs_bloqueados=487`, `alertas=[]`.
- Proximo alvo: aplicar/verificar a tabela Supabase `token_usage` ou seguir para
  revalidacao de `analisar_habilidades`/`gerar_relatorio` por provider.

### 2026-05-15 -- Sprint 3f: diagnostico live do backend `token_usage`

- Alvo: o endpoint de custos deve dizer se `TokenUsageRecord` esta duravel em
  Supabase ou apenas em fallback local.
- Status: publicado, deployado e smokeado.
- Arquivos tocados: `backend/token_usage.py`, `backend/cost_tracking.py`,
  `backend/routes_costs.py`, `backend/tests/unit/test_cost_tracking.py`.
- Comportamento: `/api/custos/status` agora retorna `token_usage_backend` com
  `local_record_count`, `supabase.enabled`, `supabase.table_available`,
  `supabase.error` e `durable`.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_cost_tracking.py` passou com 13 testes e 1 aviso conhecido de config
  `timeout` desconhecida.
- Git/deploy: commit funcional `4f27dae`; marker `f0dae61`; Render confirmou
  `4f27dae` via `wait_deploy.sh` e `check_deploy.sh`; `/api/health` healthy.
- Smoke oficial de custos: `/api/custos/status?limit=500` retornou
  `token_usage_backend.supabase.enabled=true`,
  `token_usage_backend.supabase.table_available=false`,
  `token_usage_backend.durable=false`, `token_usage_analisados=0`,
  `runs_analisados=492`, `runs_precificados=5`, `runs_bloqueados=487`.
- Bloqueio confirmado: erro Supabase/PostgREST `PGRST205`, com mensagem
  "Could not find the table 'public.token_usage' in the schema cache".
- Proximo alvo: aplicar a migration `backend/migrations/001_create_tables.sql`
  no Supabase ou criar uma migration dedicada so de `token_usage`, depois
  revalidar o endpoint ate `table_available=true`.

### 2026-05-15 -- Sprint 3g: migration dedicada `token_usage`

- Alvo: separar a SQL minima de `token_usage` para aplicacao segura no Supabase
  sem depender da migration inicial completa.
- Status: publicado no GitHub; aplicacao no banco ainda pendente.
- Arquivo tocado: `backend/migrations/002_create_token_usage.sql`.
- Git/deploy: commit `b2dc88b`; sem marker novo porque nao houve mudanca de
  runtime do site. O site oficial continua corretamente confirmado em
  `4f27dae`.
- Bloqueio/gate: aplicar SQL em banco de producao e mudanca sensivel. O loop
  nao deve fingir sucesso: enquanto `/api/custos/status` devolver
  `token_usage_backend.supabase.table_available=false`, custo de falha sem
  documento continua nao-duravel em producao.
- Proximo alvo: aplicar `backend/migrations/002_create_token_usage.sql` por
  caminho seguro de banco ou, enquanto esse gate nao ocorrer, continuar
  revalidacao de providers nas etapas `analisar_habilidades` e `gerar_relatorio`.

### 2026-05-15 -- Provider smoke: Gemini etapas finais do aluno

- Alvo: tirar Gemini 3 Flash do estado parcial nas etapas finais do aluno.
- Status: smoke oficial passou no Render live `4f27dae`.
- `analisar_habilidades`: task `task_a78369e23e5c`, status `completed`.
  Gerou JSON `7904a6a1aa34131f` e PDF `245970da4cc42c02`, provider/modelo
  `google/gemini-3-flash-preview`, tokens `15993/3874`, custo estimado
  `US$ 0.009447`, `cost_run_id=tool_894f18eb3d5d`.
- `gerar_relatorio`: task `task_58fb48fc8324`, status `completed`.
  Gerou JSON `fe6ad549481a0ed9` e PDF `b815d1faa5aeab77`, provider/modelo
  `google/gemini-3-flash-preview`, tokens `9215/2796`, custo estimado
  `US$ 0.006120`, `cost_run_id=tool_c80e7fc2af97`.
- `/api/custos/status?limit=500`: `runs_precificados=7`,
  `runs_bloqueados=483`; `token_usage_backend.durable=false` segue bloqueado
  por `PGRST205`.
- Interpretacao: Gemini 3 Flash esta confirmado para as tres etapas finais do
  aluno com metadata/custo. Isso nao valida as tres etapas de extracao nem
  remove o bloqueio de custo duravel.
- Proximo alvo: rodar GPT-5 Nano em `analisar_habilidades` e
  `gerar_relatorio`, esperando erro alto se schema/output quebrar.

### 2026-05-15 -- Provider smoke: GPT-5 Nano `analisar_habilidades`

- Alvo: verificar se GPT-5 Nano avanca alem de `corrigir` nas etapas finais do
  aluno.
- Status: falhou corretamente no Render live `4f27dae`; sem fallback.
- Task: `task_43d48d9deea2`, status `failed`, etapa
  `analisar_habilidades=failed`.
- Erro exposto: "Saida obrigatoria incompleta: PDF persistido via
  execute_python_code. Nenhum PDF/JSON sera inventado por fallback automatico".
  Detalhes da task: `create_document` com erro em multiplas chamadas e
  `execute_python_code` rodou sem arquivo gerado.
- Artefatos parciais: JSONs `3648e6629e7d6b04` e `a67c0f394f0133e7`, ambos
  `status=erro`, provider/modelo `openai/gpt-5-nano`, tokens `25237/8024`,
  custo `US$ 0.004471`, `cost_run_id=tool_58b8188d8fad`.
- Problema novo: os artefatos de erro usam nome generico
  `analise_habilidades_student123.json_1db5.json`, sinal de placeholder do
  modelo ou prompt insuficiente. Isso nao pode virar sucesso pedagogico.
- Interpretacao: custo de falha com documento parcial esta visivel; como houve
  documento parcial em erro, `token_usage_analisados` continua `0`. O bloqueio
  de Supabase `token_usage` ainda vale para falhas sem documento algum.
- Proximo alvo: diagnosticar o contrato/prompt/tool-use de
  `analisar_habilidades` com GPT-5 Nano para exigir PDF real e nomes/contexto
  corretos, sem aceitar JSON parcial como conclusao.

### 2026-05-15 -- Patch Nano retry/contexto, placeholder e bloqueio Render

- Alvo: reduzir a falha do GPT-5 Nano em `analisar_habilidades`, onde o retry
  do PDF recebia mensagem curta demais e podia inventar placeholder `student123`.
- Status: codigo e testes publicados no GitHub; deploy oficial nao confirmado.
- Arquivos tocados: `backend/executor.py`,
  `backend/tests/unit/test_e_t2_retry_partial_output.py`,
  `backend/tests/unit/test_cost_tracking.py`.
- Mudanca: o retry de output parcial agora inclui o contexto original truncado
  da etapa, proibe placeholders e exige que `execute_python_code` grave um PDF
  real em disco com `output_files`. As instrucoes de `ANALISAR_HABILIDADES`
  tambem proibem valores ficticios. O segundo patch faz JSON persistido de
  `ANALISAR_HABILIDADES` falhar alto quando contem placeholders proibidos ou
  nao traz `habilidades`.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_e_t2_retry_partial_output.py` passou com 16 testes; `test_cost_tracking.py`
  passou com 14 testes; `test_f_t2_analisar_tool_migration.py` passou com 9
  testes. Aviso conhecido: `pytest.ini` tem opcao `timeout` desconhecida.
- Git: commits funcionais `924fd79` e `d653c13`; markers `0dfdbbe` e
  `2947178`; todos publicados em `origin/main`.
- Bloqueio de deploy/smoke: `curl --max-time 20` para `/` e `/api/health`
  retornou timeout (`HTTP_STATUS=000`) em duas tentativas; em seguida, uma
  janela controlada de 6 tentativas com `curl --max-time 10` para `/api/health`
  tambem retornou `http=000` em todas. Render MCP falhou com erro de transporte
  para `https://mcp.render.com/mcp`. Portanto o site oficial continua aceito
  apenas ate `4f27dae` ate nova confirmacao.
- Retomada posterior: site voltou com `/api/health` healthy e marker live
  `novocr-deploy=924fd79`; `check_deploy.sh 924fd79` passou, mas
  `check_deploy.sh d653c13` falhou porque encontrou `924fd79`. Cinco leituras
  consecutivas do HTML mantiveram `924fd79`. Render MCP voltou a responder, mas
  sem workspace selecionado ("no workspace set"), entao nao foi possivel listar
  ou acionar deploy por MCP sem gate do usuario.
- Proximo alvo: quando Render responder, rodar `wait_deploy/check_deploy` para
  `d653c13`, `/api/health`, e novo smoke GPT-5 Nano em
  `analisar_habilidades`.

### 2026-05-16 -- Provider smoke: GPT-5 Nano etapas finais no marker `924fd79`

- Alvo: verificar se o patch live `924fd79` destravou GPT-5 Nano em
  `analisar_habilidades` e `gerar_relatorio`, sem aceitar placeholder ou
  artefato falso.
- Status: smoke oficial passou no Render live `924fd79`; `d653c13` segue
  pendente de deploy e nao deve ser tratado como live.
- Deploy/saude: `check_deploy.sh 924fd79` passou; `check_deploy.sh d653c13`
  falhou encontrando `924fd79`; `/api/health` retornou
  `{"status":"healthy","supabase":true}`.
- `analisar_habilidades`: task `task_020ba25bdb2b`, status `completed`.
  Gerou JSON `ba5dec781e46e665` e PDF `385f6b78018b8c07`,
  provider/modelo `openai/gpt-5-nano`, tokens `22817/5969`, custo
  `US$ 0.003528`, `cost_run_id=tool_8948b7aa5731`.
- Verificacao de qualidade da analise: JSON novo usa aluno real
  "Eric Manoel Ribeiro de Sousa", nao contem `student123`, `aluno_teste`,
  `nome_do_aluno`, `<str>` ou `student_name`, e traz `habilidades` estruturado.
- `gerar_relatorio`: task `task_aec830b85c03`, status `completed`.
  Gerou JSON `200c1b5272ba10f1` e PDF `a629dee567b10274`,
  provider/modelo `openai/gpt-5-nano`, tokens `24520/5305`, custo
  `US$ 0.003348`, `cost_run_id=tool_9ce5bf31c005`.
- Verificacao de qualidade do relatorio: JSON novo nao contem placeholders
  proibidos; traz `nota_final=1.43`, `resumo_geral`, `recomendacoes`,
  `_avisos_documento`, `_avisos_questao`, `_avisos_stage` e fontes usadas.
- Verificacao de arquivo: debug do PDF `a629dee567b10274` retornou
  `resolver_caminho.sucesso=true` e arquivo existente em disco.
- Custos live: `/api/custos/status?limit=500` retornou
  `runs_precificados=10`, `runs_bloqueados=477`; `/api/custos/resumo?limit=20`
  agregou o novo run uma vez, com `documentos_contagem=2`.
- Bloqueio persistente: `token_usage_backend.supabase.table_available=false`,
  `durable=false`, erro `PGRST205`; custo de falha sem documento ainda nao e
  duravel em producao.
- Interpretacao: Nano esta confirmado nas tres etapas finais do aluno no marker
  `924fd79`, mas ainda nao esta pipeline-ready porque faltam as tres etapas de
  extracao, schema minimo por etapa, UI de erro e persistencia duravel de
  `token_usage`.
- Proximo alvo: resolver o deploy pendente de `d653c13` ou, se Render continuar
  sem workspace/hook, seguir para smoke das etapas de extracao e/ou ciclo de UI
  de erro sem aceitar progresso local como oficial.

### 2026-05-16 -- Provider smoke: Gemini `extrair_questoes` e bug de request longa

- Alvo: comecar a fechar a lacuna das tres etapas de extracao no site oficial.
- Status do smoke: Gemini 3 Flash passou em `extrair_questoes` no Render live
  `924fd79`, mas o fluxo de requisicao mostrou bug operacional.
- Observacao critica: a chamada inicial de `pipeline-completo` nao devolveu
  `task_id` antes do timeout de cliente; uma tentativa alternativa pela rota
  legada `/api/pipeline/executar` tambem deu timeout. Mesmo assim, o servidor
  continuou processando, o site ficou sem `/api/health` por cerca de 90s, e
  depois apareceu a task `task_737c8d45befc` concluida.
- Artefatos: foram criados dois documentos `extracao_questoes` com Gemini,
  `3f1ca7eed14f5d37` e `9d61dcb36e6ca4b5`. A duplicacao veio do retry
  operacional antes de provar que a primeira requisicao tinha sido aceita; regra
  nova: timeout de cliente nao significa cancelamento no servidor.
- Conteudo: ambos trazem JSON parseado com `questoes`, `total_questoes`,
  `pontuacao_total`, `_avisos_documento` e `_avisos_questao`.
- Custos: documentos novos registraram provider/modelo e tokens splitados:
  `1602/1938` e `1602/1934`. `/api/custos/resumo?limit=20` mostrou custos
  `US$ 0.002806` e `US$ 0.002801` como runs separados.
- Bloqueio persistente: `token_usage` Supabase segue ausente (`PGRST205`).
- Interpretacao: Gemini esta confirmado em `extrair_questoes`, mas o executor
  HTTP ainda precisava separar execucao longa do ciclo da requisicao para evitar
  timeout, site indisponivel e retry duplicado.

### 2026-05-16 -- Sprint 4e: tarefas longas destacadas da requisicao

- Alvo: corrigir o bloqueio operacional reproduzido no smoke de
  `extrair_questoes`.
- Status: publicado no GitHub; deploy oficial pendente.
- Arquivos tocados: `backend/routes_prompts.py`,
  `backend/tests/unit/test_backend_async_pipeline.py`,
  `backend/tests/unit/test_backend_async_turma.py`,
  `backend/tests/unit/test_executor_stage_progress.py`.
- Mudanca: endpoints longos de `routes_prompts.py` mantem o registro sincrono
  do `task_id`, mas iniciam o trabalho pesado com `_start_detached_task()` em
  thread daemon, fora do ciclo de vida da requisicao. Se o worker destacado
  levanta excecao e houver `task_id`, a task e marcada como `failed`.
- Validacoes locais: `py_compile` passou; `git diff --check` passou;
  `test_backend_async_pipeline.py`, `test_backend_async_turma.py` e
  `test_executor_stage_progress.py` passaram com 25 testes e 1 aviso conhecido
  de `pytest.ini` (`timeout` desconhecido).
- Git/deploy: commit funcional `f55e299`; marker `5f10651`; ambos publicados
  em `origin/main`. Depois o alvo de runtime foi supersedido por `e6060e1`.
- Proximo alvo: quando o patch de execucao longa estiver live, repetir uma etapa curta com
  `pipeline-completo` e exigir resposta imediata com `task_id`, `/api/health`
  responsivo durante execucao e sem documento duplicado.

### 2026-05-16 -- Sprint 4f: bloquear rotas legadas sincrônicas

- Alvo: impedir que endpoints antigos de IA, fora do fluxo com `task_id`,
  bloqueiem o worker e incentivem retry duplicado.
- Status: publicado no GitHub; deploy oficial pendente.
- Arquivos tocados: `backend/routes_pipeline.py`,
  `backend/tests/unit/test_legacy_pipeline_routes.py`.
- Mudanca: `/api/pipeline/executar` e `/api/pipeline/executar-com-tools`
  agora retornam `410 Gone` com mensagem explicita apontando para o fluxo
  assíncrono com `pipeline-completo` e `/api/task-progress/{task_id}`.
- Validacoes locais: `py_compile` passou; `git diff --check` passou; suite
  focada de 27 testes passou (`test_legacy_pipeline_routes.py`,
  `test_backend_async_pipeline.py`, `test_backend_async_turma.py`,
  `test_executor_stage_progress.py`) com o aviso conhecido de `pytest.ini`.
- Git/deploy: commit funcional `e6060e1`; marker `a7dead3`; ambos publicados
  em `origin/main`. Monitor `wait_deploy.sh e6060e1` iniciado, mas ainda nao
  confirmado no Render neste registro.
- Proximo alvo: confirmar o comportamento em producao e depois resolver a
  divergencia do marker HTML.

### 2026-05-16 -- Provider smoke: Gemini `extrair_gabarito` com runner destacado

- Alvo: validar a segunda etapa de extracao e provar que `f55e299` evita
  timeout/indisponibilidade durante uma etapa longa.
- Status: smoke oficial passou. A chamada de `pipeline-completo` retornou
  `task_id` em `1.155s`; `/api/health` respondeu 20 vezes durante a execucao.
- Task: `task_094c921eb038`, status `completed`, etapa
  `extrair_gabarito=completed`.
- Artefato: JSON `36d1fdd0a453e2f5`, status `concluido`, provider/modelo
  `google/gemini-3-flash-preview`, tokens `65018/727`, custo
  `US$ 0.020378`.
- Conteudo: JSON parseado com `respostas`, `_avisos_documento` e
  `_avisos_questao`; reclassificacao posterior mostrou que todas as respostas
  ficaram `MISSING_CONTENT`, apesar de o PDF base ter texto extraivel de Q5.
- Custo live: `/api/custos/status?limit=500` subiu para
  `runs_precificados=13`, `runs_bloqueados=474`; `token_usage` duravel segue
  bloqueado por `PGRST205`.
- Interpretacao atualizada: essa execucao prova runner destacado, health e
  custo, mas nao valida conteudo de `extrair_gabarito`. A etapa precisa rerun
  apos o guard anti-tudo-`MISSING_CONTENT`.

### 2026-05-16 -- Provider smoke: Gemini `extrair_respostas`

- Alvo: fechar a terceira etapa de extracao com Gemini 3 Flash no site oficial.
- Status: smoke oficial passou. A chamada de `pipeline-completo` retornou
  `task_id` em `1.002s`; `/api/health` respondeu saudavel durante a execucao.
- Task: `task_7d357943288d`, status `completed`, etapa
  `extrair_respostas=completed`.
- Artefato: JSON `59cb3e341515d745`, status `concluido`, provider/modelo
  `google/gemini-3-flash-preview`, tokens `70414/1791`, custo
  `US$ 0.023273`.
- Conteudo: JSON parseado com `aluno`, `respostas`, `questoes_em_branco`,
  `questoes_respondidas`, `_avisos_documento` e `_avisos_questao`. O documento
  marca questoes ausentes como `em_branco=true` em vez de inventar resposta.
- Custo live: `/api/custos/status?limit=500` subiu para
  `runs_precificados=14`, `runs_bloqueados=473`; `token_usage` duravel segue
  bloqueado por `PGRST205`.
- Interpretacao atualizada: Gemini 3 Flash esta validado em
  `extrair_questoes`, `extrair_respostas` e nas tres etapas finais; a etapa
  `extrair_gabarito` foi reclassificada como invalida por tudo
  `MISSING_CONTENT`. Isso ainda nao e o mesmo que uma pipeline sequencial
  completa em uma unica chamada.

### 2026-05-16 -- Smoke de rotas legadas bloqueadas

- Alvo: confirmar em producao o comportamento de `e6060e1`, mesmo antes do
  marker HTML `a7dead3` aparecer.
- Status: comportamento backend confirmado; marker HTML ainda atrasado.
- `/api/pipeline/executar`: retornou HTTP `410` com mensagem explicita
  direcionando para `/api/executar/pipeline-completo` e
  `/api/task-progress/{task_id}`.
- `/api/pipeline/executar-com-tools`: retornou HTTP `410` com mensagem
  explicita indicando que tool-use sincrono foi desativado.
- Deploy: `check_deploy.sh e6060e1` ainda falha porque o HTML marker encontrado
  e `f55e299`; isso e divergencia de marcador, nao ausencia do comportamento
  backend observado. `wait_deploy.sh e6060e1` deu timeout apos 600s e
  `/api/health` permaneceu healthy.
- Proximo alvo: continuar monitorando o marker `a7dead3`; se ele nao entrar,
  registrar bloqueio de marcador/deploy parcial e seguir para `extrair_respostas`
  apenas pelo fluxo `pipeline-completo`.

### 2026-05-16 -- Provider smoke: Gemini pipeline sequencial completa

- Alvo: confirmar se Gemini 3 Flash aguenta a pipeline do aluno em uma unica
  task sequencial, agora com runner destacado e rotas legadas bloqueadas.
- Status: falhou corretamente, alto e visivel, sem fallback. A falha nao foi na
  resposta inicial nem na saude do site: a chamada retornou `task_id` em `1.06s`
  e `/api/health` permaneceu healthy durante a execucao.
- Task: `task_5e97bbee896e`, status final `failed`.
- Etapas: `extrair_questoes=completed`, `extrair_gabarito=completed`,
  `extrair_respostas=completed`, `corrigir=failed`,
  `analisar_habilidades=pending`, `gerar_relatorio=pending`.
- Causa registrada pela API: Google/Gemini `429 RESOURCE_EXHAUSTED`, quota do
  free tier excedida para `generate_content_free_tier_requests`, limite `20`,
  modelo `gemini-3-flash`, com `retry-after` em segundos. O erro apareceu em
  `/api/task-progress/{task_id}`; nao ficou silencioso.
- Artefatos bons da task: `extracao_questoes` JSON `025e065ceca92237` com
  tokens `1602/1944`; `extracao_gabarito` JSON `9188bd504796f767` com tokens
  `67192/730`; `extracao_respostas` JSON `ea25e7d9d9a0f9a0` com tokens
  `72588/1290`. Todos ficaram `status=concluido`, provider/modelo
  `google/gemini-3-flash-preview`, metadata splitada e custo calculavel.
- Artefatos de erro: a etapa `corrigir` deixou documentos `12cd14c89e21177d`,
  `bb2c700482505e5e` e `6ee1ce82fdeb68de` com `status=erro`, provider/modelo
  Gemini, `tokens_usados=0` e `metadata.erro_pipeline` com a quota `429`. Dois
  JSONs contem conteudo de correcao, mas por contrato devem ser tratados como
  erro, nao como resultado pedagogico aproveitavel.
- Custo live depois do ciclo: `/api/custos/status?limit=500` retornou
  `runs_precificados=17`, `runs_bloqueados=469`, `token_usage_analisados=0`.
  `/api/custos/resumo?limit=20` mostrou as tres extracoes da pipeline como
  custos OK e as correcoes de erro bloqueadas por `token_split_missing`.
- Interpretacao: Gemini nao esta reprovado em conteudo; esta bloqueado por
  quota na pipeline sequencial completa. Nao rerodar Gemini imediatamente para
  evitar duplicacao/ruido. O proximo smoke sem segredo deve mirar outro provider
  configurado, como GPT-5 Nano nas extracoes, ou esperar janela/credito Gemini.

### 2026-05-16 -- Provider smoke: GPT-5 Nano `extrair_questoes`

- Alvo: com Gemini bloqueado por quota, comecar a revalidacao de extracoes do
  GPT-5 Nano sem trocar de modelo.
- Status: smoke oficial passou. A task `task_ae679b5c3fee` terminou
  `completed`; `/api/health` permaneceu healthy durante a execucao.
- Artefato: JSON `946e66708fd72643`, tipo `extracao_questoes`,
  `status=concluido`, provider/modelo `openai/gpt-5-nano`, tokens
  `2148/12147`, custo `US$ 0.004966`.
- Conteudo: JSON parseado com `questoes`, `total_questoes=7`,
  `pontuacao_total=7.0`, `_avisos_documento` e `_avisos_questao`. As primeiras
  questoes vieram com enunciado, itens, tipo, pontuacao, habilidades e
  `tipo_raciocinio`.
- Custo live: `/api/custos/status?limit=500` subiu para
  `runs_precificados=18`, `runs_bloqueados=468`, `token_usage_analisados=0`.
- Interpretacao: GPT-5 Nano sai de nao testado em `extrair_questoes` para
  validado nessa etapa. Ainda faltam `extrair_gabarito` e `extrair_respostas`
  antes de tentar pipeline completa de 6 etapas com Nano.

### 2026-05-16 -- Bug P0: `extrair_gabarito` aceitava tudo `MISSING_CONTENT`

- Alvo: continuar Nano nas extracoes, agora em `extrair_gabarito`, e checar se
  o status verde correspondia a conteudo real.
- Status do smoke Nano: a task `task_2da0fb90c3fb` terminou `completed`, gerou
  JSON `61fb077d746c2a55`, provider/modelo `openai/gpt-5-nano`, tokens
  `78104/3635`, custo `US$ 0.005359`, e health permaneceu saudavel.
- Problema: o JSON veio com 7 respostas, mas todas tinham
  `resposta_correta=MISSING_CONTENT`.
- Evidencia contra o status verde: o PDF base `dbfe3a77a631489f` foi baixado e
  `pdftotext` extraiu texto real: "Gabarito -- Lista 0, Exercicio 5" e a
  solucao do sistema homogeneo. Portanto, "todas missing" nao e uma extracao
  aceitavel.
- Reclassificacao: os smokes Gemini de `extrair_gabarito` tambem tinham todas
  as respostas `MISSING_CONTENT`; logo a matriz anterior estava otimista. A
  etapa tinha schema parseavel e custo, mas conteudo invalido.
- Patch local aplicado: `pipeline_validation.ExtracaoGabarito` agora rejeita
  gabarito em que todas as respostas sao `MISSING_CONTENT`; `executor.py`
  transforma `_validation_warning`, `_validation_error` e `_error` de parse em
  falha bloqueante antes de salvar documento verde, e registra custo de resposta
  invalida via `TokenUsageRecord` quando houver tokens. O fallback antigo que
  aceitava Markdown como `gerar_relatorio` valido quando JSON falhava tambem foi
  removido.
- Validacoes locais: `python -m py_compile backend/executor.py
  backend/pipeline_validation.py backend/tests/unit/test_pipeline_validation.py`,
  `git diff --check` e `pytest backend/tests/unit/test_pipeline_validation.py
  backend/tests/unit/test_erro_pipeline.py -q` passaram (`68 passed`,
  `3 skipped`, aviso conhecido de `timeout`).
- Proximo alvo: commitar/pushar o guard, criar marker de deploy, esperar Render
  e rerodar `extrair_gabarito`. So depois a etapa pode voltar a ✅.

### 2026-05-16 -- Deploy gate do guard `5527e26`

- Alvo: publicar oficialmente o guard anti-gabarito-tudo-`MISSING_CONTENT` antes
  de qualquer novo smoke de `extrair_gabarito`.
- GitHub: commit funcional `5527e26` e marker `2792d89` publicados em
  `origin/main`.
- Validacoes locais do commit funcional: `py_compile`, `git diff --check` e
  `pytest backend/tests/unit/test_pipeline_validation.py
  backend/tests/unit/test_erro_pipeline.py -q` passaram (`68 passed`,
  `3 skipped`, aviso conhecido de `timeout`).
- Render: `wait_deploy.sh 5527e26` deu timeout apos 600s. Durante o gate o HTML
  avancou de `f55e299` para `e6060e1`, mas nao chegou em `5527e26`; polls
  adicionais mantiveram `e6060e1`.
- Render MCP: apos `list_workspaces`, um unico workspace foi selecionado
  automaticamente (`tea-d5ruvqu3jp1c73dudl7g`), mas as ferramentas disponiveis
  nesta sessao nao listam servicos nem disparam deploy. `list_deploys` com
  `serviceId=prova-ai` retornou 404, entao o service id real ainda nao foi
  descoberto por MCP.
- Status: guard publicado no GitHub, nao confirmado no site oficial. Nao rerodar
  `extrair_gabarito` como validacao oficial enquanto o marker live nao mostrar
  `5527e26` ou comportamento equivalente for comprovado com seguranca.
- Proximo alvo: continuar monitorando `check_deploy.sh 5527e26`; se Render
  permanecer travado, usar canal seguro de deploy manual/API e registrar o gate.

### 2026-05-16 -- Render MCP confirmou `5527e26` e Nano gabarito passou

- Alvo: reconectar o loop depois de interrupcao e diferenciar deploy real de
  marker HTML atrasado.
- Render MCP: `list_services` encontrou o servico oficial
  `srv-d5t8gbh4tr6s738fr3s0` (`IA_Educacao_V2`), branch `main`,
  `rootDir=backend`, URL `https://ia-educacao-v2.onrender.com`. `list_deploys`
  marcou `5527e2651fa47e6258610d0470ca060e2921d663` como `live`, deploy
  `dep-d83spamq1p3s73f0ks20`.
- Correcao de interpretacao: `check_deploy.sh 5527e26` falha porque o HTML
  ainda contem `novocr-deploy=e6060e1`; isso e stale marker, nao prova de
  backend antigo. Como o Render usa `rootDir=backend`, commits de marker em
  frontend/docs podem nao disparar novo deploy.
- Smoke oficial: `pipeline-completo`, aluno Eric
  (`660e9421b246ad3f`), atividade Lista0 (`126e8b5ad7dd6d59`), modelo
  `gpt5nano001`, `selected_steps=["extrair_gabarito"]`, `force_rerun=true`.
- Task: `task_dc719eeea626` terminou `completed` e marcou
  `extrair_gabarito=completed`.
- Artefato: JSON `5f433f9a1bc30842`, tipo `extracao_gabarito`,
  `status=concluido`, provider/modelo `openai/gpt-5-nano`, tokens
  `78104/8353`, total `86457`, custo `/api/custos/resumo?limit=30`
  `US$ 0.007246`.
- Conteudo: 7 respostas reais; nenhuma resposta veio `MISSING_CONTENT`. O smoke
  nao prova qualidade matematica fina de cada justificativa, mas prova que o
  erro P0 "tudo missing com status verde" nao ocorreu nesta execucao.
- Observacao operacional: durante a task, logs Render registraram timeout do
  Supabase em `resolver_caminho` e "Arquivo nao encontrado", mas o documento
  final foi salvo e lido via `/api/documentos/{id}/conteudo`. Isso fica como
  ruido/risco de storage a acompanhar, nao bloqueio deste smoke.
- Custo live apos o smoke: `/api/custos/status` retornou
  `runs_precificados=20`, `runs_bloqueados=466`, `token_usage_analisados=0`.
- Status: GPT-5 Nano `extrair_gabarito` volta a ✅ para este exemplo oficial.
  Gemini `extrair_gabarito` continua ❌ ate rerun pos-guard/quota.
- Proximo alvo: rodar `extrair_respostas` Nano no site oficial; se passar,
  tentar pipeline Nano completa de 6 etapas. Em paralelo, abrir ciclo pequeno
  para corrigir o mecanismo de deploy marker/verificador.

### 2026-05-16 -- Bug P0: `extrair_respostas` aceitava tudo ilegivel

- Alvo: validar `extrair_respostas` com GPT-5 Nano no site oficial apos o
  gabarito Nano passar.
- Smoke oficial: `pipeline-completo`, aluno Eric
  (`660e9421b246ad3f`), atividade Lista0 (`126e8b5ad7dd6d59`), modelo
  `gpt5nano001`, `selected_steps=["extrair_respostas"]`, `force_rerun=true`.
- Task: `task_a9ff0d69d5e9` terminou `completed` e marcou
  `extrair_respostas=completed`.
- Artefato: JSON `b968c9539f277deb`, provider/modelo `openai/gpt-5-nano`,
  tokens `85774/3002`, custo `US$ 0.005489`, `status=concluido`.
- Problema: o JSON marcou as 7 respostas com `ilegivel=true`, `em_branco=false`
  e `resposta_aluno=null`.
- Evidencia contra o status verde: a prova respondida `f60d37284d616ca4`
  (`Eric Manoel Ribeiro de Sousa - ALA-Lista0.pdf_16e6.pdf`) tem texto extraivel
  via `pdftotext`, incluindo "Questao 7 - Lista 0" e codigo Julia/resposta da
  questao 7. Portanto, "tudo ilegivel" nao pode ser aceito como sucesso.
- Reclassificacao: `extrair_respostas` Nano fica ❌ nesta amostra, apesar de
  schema/custo/metadata. Gemini tinha produzido o mesmo padrao de tudo ilegivel
  em smokes anteriores; isso tambem deve ser tratado como risco de conteudo.
- Patch `8dd6c54` aplicado: `pipeline_validation.ExtracaoRespostas` agora rejeita
  respostas em que todos os itens tenham `ilegivel=true`; a funcao publica
  `validar_json_pipeline("extrair_respostas", ...)` retorna erro estruturado.
- Validacoes locais: `python -m py_compile backend/pipeline_validation.py
  backend/tests/unit/test_pipeline_validation.py`, `git diff --check`,
  `pytest backend/tests/unit/test_pipeline_validation.py -q` (`27 passed`,
  `3 skipped`) e `pytest backend/tests/unit/test_pipeline_validation.py
  backend/tests/unit/test_erro_pipeline.py -q` (`70 passed`, `3 skipped`) passaram,
  com o aviso conhecido de config `timeout`.
- Status posterior: este guard foi necessario, mas nao suficiente. Em producao,
  o modelo passou a retornar tudo `em_branco=true`, e depois ficou claro que a
  validacao Pydantic nao cobria o caminho real do executor.

### 2026-05-16 -- Guard `8dd6c54` insuficiente: tudo vazio ainda passava

- Alvo: confirmar se o guard anti-tudo-`ilegivel` bastava em producao.
- Deploy: Render MCP marcou `8dd6c541218e0a46f9ad1585004a2cbff46e1f1b`
  como live no deploy `dep-d83tji77f7vs73da55d0`; depois foi desativado por
  commits posteriores.
- Smoke oficial: GPT-5 Nano em `extrair_respostas`, task
  `task_03ae99db3006`.
- Resultado: a task terminou verde e salvou JSON `2a518dfb6b2a03ef`; o conteudo
  veio com todas as 7 respostas `em_branco=true`, `ilegivel=false` e
  `resposta_aluno` vazia. Isso ainda e falso sucesso.
- Interpretacao: bloquear apenas "tudo ilegivel" nao basta. O contrato correto
  para `EXTRAIR_RESPOSTAS` e: se todas as respostas nao tem conteudo extraido
  por `ilegivel`, `em_branco` ou texto vazio, a etapa deve falhar alto.
- Proximo alvo: ampliar a regra para todo output sem conteudo.

### 2026-05-16 -- Guard `c1598b9` correto no schema, mas fora do caminho real

- Alvo: rejeitar `EXTRAIR_RESPOSTAS` quando todas as respostas nao tiverem
  conteudo extraido, independentemente de serem `ilegivel`, `em_branco` ou
  `resposta_aluno` vazia.
- Deploy: Render MCP marcou `c1598b9d283c85504c0bd7a1db1a2a7de5f4d708`
  como live no deploy `dep-d83tm7uq1p3s73f10evg`; depois foi desativado por
  `01fb04c`.
- Smoke oficial: GPT-5 Nano em `extrair_respostas`, task
  `task_6772978a20c4`.
- Resultado: a task terminou verde e salvou JSON `10d1c1d9741a6273`; todas as
  respostas continuaram sem conteudo real, com `em_branco=true` e mensagens
  genericas.
- Causa descoberta: `pipeline_validation.py` estava correto, mas o caminho real
  do executor multimodal nao aplicava essa validacao antes de salvar. O flag
  `HAS_VALIDATION=False` deixava `_parsear_resposta` dependente de validacao
  que nao era carregada para esse fluxo.
- Interpretacao: validacao de schema em modulo separado nao pode ser assumida
  como gate de produto se o executor nao a chama no caminho real.
- Proximo alvo: bloquear no executor antes de salvar documento verde.

### 2026-05-16 -- Guard `01fb04c`: `extrair_respostas` falha alto no site

- Alvo: bloquear diretamente no executor qualquer `EXTRAIR_RESPOSTAS` em que
  todas as respostas estejam sem conteudo extraido.
- Arquivos tocados no commit: `backend/executor.py`,
  `backend/tests/unit/test_erro_pipeline.py`.
- Deploy: Render MCP marcou `01fb04c060f1a88c0f8ea4b09f64a9191d43c291` como
  live no deploy `dep-d83tp2m7r5hc73d7o7d0`.
- Smoke oficial: GPT-5 Nano em `extrair_respostas`, task
  `task_b511641dfa52`.
- Resultado esperado e observado: a task terminou `failed`, com
  `stages.extrair_respostas=failed` e erro explicito:
  `EXTRAIR_RESPOSTAS retornou todas as respostas sem conteudo extraido (em branco, ilegiveis ou vazias). Isso nao pode ser tratado como sucesso.`
- Verificacao de artefato: a listagem de documentos mostrou que o ultimo
  `extracao_respostas` verde ainda e `10d1c1d9741a6273`, criado antes do
  `01fb04c`; a task `task_b511641dfa52` nao criou novo documento verde.
- Custos: `/api/custos/status?limit=500` retornou `runs_precificados=24`,
  `runs_bloqueados=463`, `token_usage_analisados=1`, mas
  `token_usage_backend.supabase.table_available=false` e `durable=false`
  continuam com erro `PGRST205`.
- Validacoes locais antes do deploy: `python -m py_compile backend/executor.py
  backend/pipeline_validation.py backend/tests/unit/test_pipeline_validation.py
  backend/tests/unit/test_erro_pipeline.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_pipeline_validation.py backend/tests/unit/test_erro_pipeline.py -q`
  (`74 passed`, `3 skipped`, aviso conhecido de config `timeout`).
- Status: o falso sucesso foi corrigido. A etapa `extrair_respostas` com GPT-5
  Nano continua ❌ enquanto o modelo/prompt/entrada nao extrairem conteudo real,
  mas agora a falha aparece para o usuario e bloqueia a conclusao falsa.
- Proximo alvo tecnico: corrigir a causa da extracao vazia e/ou ativar a
  validacao central no executor de forma consistente, sem depender de guard
  ad hoc por etapa.

### 2026-05-16 -- `extrair_respostas` Nano: scans visiveis, inferencia proibida, falha alta final

- Alvo: continuar o loop real depois de `01fb04c`; corrigir a causa de
  `extrair_respostas` vazia sem voltar a aceitar documento verde ruim.
- Commits/deploys oficiais:
  - `6b57ef1` (`dep-d83u02j7uimc73fqps80`): colocou `questoes_extraidas` no
    prompt de `EXTRAIR_RESPOSTAS`; smoke `task_8b1664516042` ainda falhou alto.
  - `3b9eedc` (`dep-d8411cnavr4c73bdv9j0`): colocou texto extraido do PDF no
    prompt; smoke `task_71ac163c7f13` completou e criou JSON `6b28875e8a9fdc73`,
    mas so extraiu conteudo real da questao 7.
  - `b8b8693` (`dep-d8417kpo3t8c73f6k51g`): removeu bloqueio local de imagens
    para GPT-5 Nano/OpenAI, anexou paginas PDF sem texto como PNG e rejeitou scan
    majoritariamente vazio; smoke `task_fd9d2beaefac` completou e criou JSON
    `893987838fd275bd` com 7/7 respostas preenchidas, mas algumas pareciam
    inferidas do enunciado.
  - `283e8c6` (`dep-d841b2po3t8c73f6lllg`): prompt proibiu inferir resposta do
    enunciado/gabarito/conhecimento externo; smoke `task_96691474acdd` criou
    JSON `ff0882e8db71e79d`, mais honesto, mas ainda verde com campos vazios
    inconsistentes e maioria sem conteudo.
  - `1ce3d23` (`dep-d841f437uimc73fs60lg`): executor passou a rejeitar
    `resposta_aluno` vazia sem `em_branco=true`/`ilegivel=true` e scans com 70%
    ou mais de respostas sem conteudo.
- Smoke oficial final: `task_3d5feaf0da71`, `gpt5nano001`,
  `selected_steps=["extrair_respostas"]`, `force_rerun=true`.
- Resultado final: `status=failed`, `extrair_respostas=failed`, erro explicito:
  `EXTRAIR_RESPOSTAS marcou 6 de 7 respostas como sem conteudo mesmo com paginas escaneadas anexadas como imagem. Isso e suspeito demais para concluir a etapa; revise OCR/vision do modelo ou use outro provider explicitamente.`
- Verificacao de artefato: a listagem de `extracao_respostas` mostra que o ultimo
  documento verde continua `ff0882e8db71e79d` de `2026-05-16T07:04:27`; a task
  final `task_3d5feaf0da71` nao criou novo documento verde.
- Custos: `/api/custos/resumo?limit=60` mostrou `TokenUsageRecord`
  `usage_52590d55d210459e`, `cost_run_id=validation_c1e429bc06ee`,
  provider/modelo `openai/gpt-5-nano`, tokens `100188/8863`, custo
  `US$ 0.008555`, `status=erro`, `source=executar_multimodal`.
- Status: produto protegido contra falso sucesso nesta amostra. A qualidade real
  de `extrair_respostas` com GPT-5 Nano em prova manuscrita continua nao
  confirmada; Doc 12 deve manter Nano ❌ nessa fase.
- Proximo alvo tecnico: revalidar `extrair_respostas` com provider/modelo mais
  forte em OCR/handwriting ou melhorar o caminho OpenAI para preservar melhor
  evidencia por pagina; nao rodar pipeline completa Nano enquanto essa etapa
  estiver ❌.

### 2026-05-16 -- GPT-5.4 Mini candidato para `extrair_respostas`

- Alvo: testar um modelo OpenAI mais forte que Nano para a etapa de prova
  manuscrita, sem fallback silencioso e sem rodar pipeline completa.
- Fonte oficial de modelo/preco: docs OpenAI em 2026-05-16 indicam `gpt-5.5`
  como flagship e `gpt-5.4-mini`/`gpt-5.4-nano` para menor custo/latencia; o
  catalogo live do site lista `gpt-5.4-mini` com vision/tools/reasoning e preco
  `US$ 0.75/US$ 4.50` por 1M tokens.
- Bug de settings descoberto antes do patch: `POST /api/settings/models/from-catalog`
  retornou 500 ao criar `openai/gpt-5.4-mini`; `POST /api/settings/models`
  criou o modelo mas ignorou capabilities no create (`tools=false`,
  `suporta_temperature=true`). Foi necessario corrigir via `PUT` no site oficial
  antes do smoke.
- Patch de settings: commit `b16e051` fez `ModelManager.adicionar()` mesclar
  capabilities sem `TypeError` e `ModelCreate` preservar
  `suporta_vision`/`suporta_function_calling`/`suporta_streaming`/
  `suporta_temperature`; Render `dep-d841ruu8bjmc73dbn030` confirmou esse patch
  live, e `from-catalog` passou depois do deploy.
- Durabilidade de modelo: o modelo criado por API antes do deploy (`04b31001cf81`)
  sumiu apos o deploy, provando que settings em disco do Render nao bastam para
  modelos oficiais. `from-catalog` pos-deploy criou `d1e2d1851836` e o teste de
  conexao retornou `OK`, mas o candidato duravel deve ser versionado como
  `gpt54mini001` em `backend/data/models.json`.
- Smoke oficial: `task_9c10e3752bcb`, `selected_steps=["extrair_respostas"]`,
  `force_rerun=true`.
- Resultado: task `completed`; documento `a39d26fcc621c7a8`, status
  `concluido`, provider/modelo `openai/gpt-5.4-mini`, tokens `97004/1942`,
  custo `US$ 0.081492`, tempo `40546.4ms`.
- Qualidade observada: 4/7 respostas extraidas com conteudo real; questoes 1, 2
  e 4 marcadas explicitamente como `MISSING_CONTENT`/sem resposta visivel. Isso
  e melhor que Nano para esta amostra, mas ainda precisa validacao em mais provas
  e pipeline completa com per-phase model.
- Teste focado do patch de settings: `backend/tests/unit/test_model_manager.py`
  com `14 passed`.
- Proximo alvo tecnico: commitar/deployar `gpt54mini001` em `models.json`,
  confirmar que aparece no site apos deploy, e depois rodar pipeline com
  `gpt-5.4-mini` somente em `EXTRAIR_RESPOSTAS` ou em mais amostras dessa etapa.

### 2026-05-16 -- `gpt54mini001` versionado e gate de deploy por backend

- Alvo: confirmar que o candidato GPT-5.4 Mini sobrevive deploy como modelo
  versionado, registrar o smoke oficial e corrigir o gate de deploy que dependia
  demais do marker HTML stale.
- Git/deploy observado antes do novo gate: commit `be19b7e` live no Render como
  `dep-d84359favr4c73beqb0g`; `/api/health` healthy; `/api/settings/models/gpt54mini001`
  retornou o modelo com `suporta_vision=true`, `suporta_function_calling=true`,
  `suporta_streaming=true`, `suporta_temperature=false` e
  `catalog_ref=openai/gpt-5.4-mini`.
- Teste de conexao: `/api/settings/models/gpt54mini001/testar` retornou
  `success=true`, `resposta=OK`, modelo `gpt-5.4-mini`, `tokens=44`.
- Smoke oficial versionado: `task_706931a94555`,
  `selected_steps=["extrair_respostas"]`, `force_rerun=true`.
- Resultado: task `completed`; documento `fec100a2e41eabcf`, status
  `concluido`, provider/modelo `openai/gpt-5.4-mini`, tokens `97004/1737`,
  custo `US$ 0.080570`, tempo `53469.7ms`.
- Qualidade observada: 5/7 respostas extraidas com conteudo real; Q1 e Q2 foram
  marcadas como `MISSING_CONTENT`; Q3 recebeu `LOW_CONFIDENCE`; Q4 passou a
  conter uma observacao mais honesta de possivel mistura com questao 5. Isso
  reforca GPT-5.4 Mini como candidato melhor que Nano para handwriting/OCR, mas
  ainda nao valida pipeline completa nem todas as materias.
- Segunda amostra oficial: Alvaro, `task_19062336eb8b`,
  `selected_steps=["extrair_respostas"]`, `force_rerun=true`.
- Resultado da segunda amostra: task `completed`; documento `4a82ddf1d2118ff0`,
  status `concluido`, provider/modelo `openai/gpt-5.4-mini`, tokens
  `90588/2813`, custo `US$ 0.0806`, tempo `46109ms`.
- Qualidade da segunda amostra: 7/7 respostas extraidas com conteudo real,
  `questoes_em_branco=0`, avisos `LOW_CONFIDENCE` em Q2 e Q3. A resposta
  inclui conteudo matematico extenso e sinais de leitura de codigo/figuras na
  Q7. Ainda precisa revisao humana de fidelidade, mas nao parece o falso sucesso
  vazio/inferido que ocorria no Nano.
- Custos/durabilidade: `/api/custos/status?limit=500` retornou
  `runs_precificados=28`, `runs_bloqueados=458`, `token_usage_analisados=0`,
  `token_usage_backend.supabase.table_available=false`, erro `PGRST205`,
  `local_record_count=0` e `durable=false`. Interpretacao: custos de documento
  seguem medidos; custo de falha sem documento nao e duravel entre deploys ate
  a migration `002_create_token_usage.sql` ser aplicada no Supabase.
- Gate de deploy: commit `2d72c6b` adicionou `/api/deploy-info`, testes unitarios
  e `check_deploy.sh` priorizando o endpoint backend antes do HTML marker; em
  `render.yaml`, foi registrada a tentativa de gravar `deploy_sha.txt`, mas o
  servico real no Dashboard ainda mostra build command proprio. O endpoint deve
  funcionar se o Render expuser `RENDER_GIT_COMMIT`; se voltar `unknown`, o
  proximo patch deve usar marker versionado dentro de `backend/`, nao
  `frontend/index_v2.html`.
- Validacoes locais do gate: `python -m py_compile backend/main_v2.py
  backend/tests/unit/test_health_endpoint.py`; `bash -n scripts/check_deploy.sh`;
  `git diff --check`; `PYTHONPATH=backend
  /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_health_endpoint.py -q` (`6 passed`); testes de custo
  `backend/tests/unit/test_cost_tracking.py` (`14 passed`); testes de settings
  `backend/tests/unit/test_model_manager.py
  backend/tests/unit/test_gpt5_nano_registration.py` (`21 passed`).
- Status do deploy do gate: `2d72c6b` publicado no GitHub; Render MCP confirmou
  `dep-d84bjopo3t8c73fbshug` como `live`, finalizado em
  `2026-05-16T18:42:15Z`; `/api/deploy-info` retornou commit
  `2d72c6bf2c8d3eda1a4c5219603d5c2e58527127`, `source=RENDER_GIT_COMMIT`;
  `check_deploy.sh 2d72c6b` passou; `/api/health` continuou healthy.
- Proximo alvo tecnico: decidir o proximo ciclo entre aplicar migration Supabase
  de `token_usage` (gate alto) e ampliar smokes `gpt54mini001` por amostra/fase.

### 2026-05-16 -- Higiene de artefatos e smoke per-phase pos-patch

- Alvo: rodar uma pipeline oficial por fase, usando Nano nas etapas estruturais
  e `gpt54mini001` em `extrair_respostas`, sem Rio 3 e sem fallback silencioso.
- Smoke antes do patch: `task_ea1ac75c9459`, runtime `2d72c6b`, Pablo
  (`f2828766a2a91e9a`). `extrair_questoes` concluiu com JSON
  `153c240d3bb59029` (`2178/7682`, custo `US$ 0.003182`), mas
  `extrair_gabarito` falhou alto: `EXTRAIR_GABARITO retornou todas as respostas
  como MISSING_CONTENT`. A falha registrou custo sem documento final em
  `usage_c1129eb1c465417d` (`89035/3420`, custo `US$ 0.005820`), local e nao
  duravel porque Supabase `token_usage` ainda nao existe.
- Diagnostico: `storage.listar_documentos()` retorna documentos em ordem mais
  recente primeiro, mas `_preparar_variaveis_texto()` sobrescrevia variaveis ao
  percorrer todos os documentos; o valor final podia ser um JSON antigo. Alem
  disso, `_coletar_arquivos_para_etapa()` anexava todos os JSONs historicos da
  atividade, inflando tokens e confundindo o modelo.
- Patch: `f2211bb` (`fix: use latest pipeline artifacts explicitly`) seleciona
  o documento mais recente por tipo para JSONs processados, impede recuo para
  artefatos antigos e remove o uso de gabarito original como substituto de
  `EXTRACAO_GABARITO` em `corrigir`.
- Validacoes locais: `python -m py_compile backend/executor.py
  backend/tests/unit/test_erro_pipeline.py`; `PYTHONPATH=backend
  /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_erro_pipeline.py -q` (`57 passed`);
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_pipeline_validation.py backend/tests/unit/test_cost_tracking.py -q`
  (`43 passed`, `3 skipped`); `git diff --check`.
- Deploy: `f2211bb897dd6d4a3ae0264dd48cf6d7970a64b2` publicado no GitHub;
  Render MCP confirmou `dep-d84bsou8bjmc73dgr12g` como `live`; `/api/deploy-info`
  retornou `f2211bb` por `RENDER_GIT_COMMIT`; `/api/health` ficou healthy.
- Smoke pos-patch: `task_19ee59ac1881`, mesmos providers por fase,
  `force_rerun=true`.
- Resultado pos-patch por etapa:
  - `extrair_questoes`: ✅ JSON `d50f3b909e6773e7`, Nano, `2178/8678`, custo
    `US$ 0.003580`.
  - `extrair_gabarito`: ✅ JSON `8dd414ee1617c3a5`, Nano, `6918/5497`, custo
    `US$ 0.002545`; antes a mesma etapa chegava a `78104/8353` ou falhava com
    custo alto por contexto contaminado.
  - `extrair_respostas`: ✅ JSON `1e5db36f3ab9aa0e`, `gpt-5.4-mini`,
    `18176/2081`, custo `US$ 0.022996`.
  - `corrigir`: ✅ JSON `f0302debf41ae58f` e PDF `31794fc784905c00`, Nano,
    `19614/4566`, custo `US$ 0.002807`.
  - `analisar_habilidades`: ❌ falhou alto; doc parcial `b5f17f2d1a980a3d`
    ficou `status=erro`, Nano, `21193/7884`, custo `US$ 0.004213`; erro:
    `Saída obrigatória incompleta: JSON persistido via create_document... tools
    com erro: create_document, create_document, create_document; execute_python_code
    rodou sem arquivo gerado.`
  - `gerar_relatorio`: pendente, nao executou.
- Status: o patch corrigiu contaminacao de artefatos e reduziu custo/latencia,
  mas a pipeline oficial ainda nao esta completa. O maior bloqueador reproduzido
  agora e `analisar_habilidades` com GPT-5 Nano em tool-use integrado.
- Proximo alvo tecnico: corrigir `analisar_habilidades` para produzir exatamente
  os artefatos obrigatorios ou configurar modelo per-phase explicito para essa
  etapa; depois repetir o smoke ate `gerar_relatorio`.

### 2026-05-16 -- Retry multimodal, full smoke e bloqueio de gabarito incompleto

- Alvo: continuar o loop de provider/pipeline depois de `f2211bb`, sem Rio 3,
  testando o maior bloqueador reproduzido no site oficial.
- Patch `6b20d43` (`fix: retry invalid multimodal extractions`): adicionou
  retry explicito de validação multimodal no mesmo provider/modelo para
  extrações com JSON inválido, tudo `MISSING_CONTENT`, respostas vazias ou
  questões vazias. Isso nao e fallback: se a segunda tentativa falhar, a etapa
  continua falhando alto e registra tokens somados.
- Validações locais de `6b20d43`: `py_compile` de `backend/executor.py` e
  `backend/tests/unit/test_erro_pipeline.py`; `test_erro_pipeline.py`
  (`62 passed`); `test_cost_tracking.py` + `test_pipeline_validation.py`
  (`43 passed`, `3 skipped`); `git diff --check`.
- Deploy: Render publicou `6b20d43` (`dep-d84cg4b7uimc7381srog`) e
  `/api/deploy-info` confirmou o hash. Durante o gate foi descoberto que
  `deploy-info` podia ser servido de cache; o commit `3406f8a` ajustou
  `check_deploy.sh` e `wait_deploy.sh` para usar `Cache-Control: no-cache` e
  cache buster.
- Smoke full oficial: `task_bc6cc84d10ef`, Pablo, `force_rerun=true`, Nano em
  `extrair_questoes`, `corrigir`, `analisar_habilidades`, `gerar_relatorio` e
  `gpt54mini001` em `extrair_gabarito`/`extrair_respostas`. A task ficou
  `completed` nas 6 etapas.
- Evidência por etapa do smoke full:
  - `extrair_questoes`: JSON `136f58a9fa213ea4`, Nano, `2178/11152`, custo
    `US$ 0.004570`.
  - `extrair_gabarito`: JSON `17573f1218bd6c39`, `gpt-5.4-mini`, `6496/1070`,
    custo `US$ 0.009687`; conteudo indicou apenas Q5 com resposta real e
    avisos `MISSING_CONTENT` para Q1, Q2, Q3, Q4, Q6 e Q7.
  - `extrair_respostas`: JSON `f10a6ef8a8ca0897`, `gpt-5.4-mini`,
    `17787/1836`, custo `US$ 0.021602`; 7/7 respostas reais, com
    `LOW_CONFIDENCE` na Q3.
  - `corrigir`: primeira versão pós-`d4bb2bd` usou o JSON estruturado e melhorou
    a correção, mas ainda gerou nota `3.5` apesar do gabarito incompleto. Isso
    foi reclassificado como falso sucesso.
  - `analisar_habilidades` e `gerar_relatorio`: completaram, mas ficaram
    invalidados como prova de pipeline porque dependeram de correção sem
    gabarito completo.
- Patch `d4bb2bd` (`fix: use structured answers in correction prompt`): fez
  `CORRIGIR` preferir os JSONs `questoes_extraidas`, `gabarito_extraido` e
  `respostas_aluno` aos textos crus dos uploads.
- Patch `3a7dfea` (`fix: block correction with incomplete answer key`): bloqueia
  `CORRIGIR` antes de chamar IA quando `gabarito_extraido` tem
  `MISSING_CONTENT`/`ILLEGIBLE_*` bloqueante. O smoke isolado
  `task_5894e6d5858e` falhou alto em `corrigir` com a mensagem correta e nao
  criou novo documento verde.
- Custos: o smoke full antes do bloqueio registrou custo medido por documento/run
  de aproximadamente `US$ 0.045389` para as 6 etapas. O smoke bloqueado por
  gabarito incompleto nao chamou IA e, corretamente, nao criou custo novo.
  `token_usage_backend.supabase.table_available=false` (`PGRST205`) continua
  bloqueando durabilidade de falhas sem documento.
- Status: a pipeline com esses arquivos da Lista0 nao deve ser chamada de
  validada; ela agora falha no ponto certo porque o gabarito da atividade esta
  incompleto. O ciclo seguinte escolheu uma fixture limpa diferente para validar
  o fluxo OpenAI completo.

### 2026-05-16 -- OpenAI Responses/tool-use e smoke completo GPT-5.4 Mini

- Alvo: destravar pipeline oficial no Render para modelo OpenAI com tools, sem
  fallback de provider/modelo e sem tratar tool-call sem arquivo persistido como
  sucesso.
- Commits: `5a3daca` alinhou prompt/tool-use; `92bd095` permitiu conteudo JSON
  estruturado em `create_document`; `f6b040c` corrigiu schema OpenAI `array`
  sem `items`; `2cad38a` fez `handle_create_document` retornar erro quando o
  storage nao persiste artefato obrigatorio de pipeline.
- Falhas uteis antes do sucesso: `task_04bfc1bbe616` ainda falhou em
  `analisar_habilidades`; `task_a1977746ef2f` falhou por schema OpenAI 400;
  `task_200440ba527e` provou que o modelo chamava `create_document`, mas nada
  ficava persistido. Essas falhas viraram patches, nao fallback silencioso.
- Validacoes locais do ciclo: `py_compile` dos arquivos tocados; `git diff
  --check`; testes focados `97 passed`; bateria ampla focada em pipeline/custos
  `254 passed, 3 skipped`.
- Deploy: `/api/deploy-info` no Render confirmou `2cad38a` e `/api/health`
  continuou healthy.
- Smoke oficial: `task_a5f0d734f0b3`, atividade `Smoke Paulo Pipeline
  2026-05-16`, aluna Diana Omega, modelo `gpt54mini001`, completou as 6 etapas:
  `extrair_questoes`, `extrair_gabarito`, `extrair_respostas`, `corrigir`,
  `analisar_habilidades` e `gerar_relatorio`.
- Evidencia de documentos/custos:
  - `extrair_questoes`: `f65318c550a76842`, `1150/322`, `US$ 0.002312`.
  - `extrair_gabarito`: `70df18512be9c617`, `1813/311`, `US$ 0.002759`.
  - `extrair_respostas`: `14ca81d800de2648`, `2042/250`, `US$ 0.002657`.
  - `corrigir`: `2c7cd4cf9eb85e57` e `769744b6fff6f3b9`, `18480/2731`,
    `US$ 0.026149`.
  - `analisar_habilidades`: `12b24cd992477eab` e `15579ed3ad2614be`,
    `10627/2111`, `US$ 0.017470`.
  - `gerar_relatorio`: `38686372cb8ea981` e `37b0c86cee879ced`,
    `16246/3462`, `US$ 0.027763`.
- Custo total aproximado das 6 etapas: `US$ 0.079110`. O endpoint
  `/api/custos/resumo?limit=8` mostrou uma janela parcial com
  `runs_precificados=5`, `runs_bloqueados=0`, `tokens_entrada=49208`,
  `tokens_saida=8865` e `custo_usd=0.076798`.
- Bloqueio persistente: `token_usage_backend.supabase.table_available=false`,
  `durable=false`, erro `PGRST205`. Custos em documentos existem, mas falhas sem
  documento ainda precisam de `backend/migrations/002_create_token_usage.sql`
  aplicada no Supabase.
- Status: GPT-5.4 Mini agora tem um smoke full oficial positivo nessa fixture
  simples.
- Inspeção semantica inicial dos JSONs:
  - `extracao_questoes`: 4 questoes, pontuacao total `10.0`.
  - `extracao_gabarito`: 4 respostas completas, sem `MISSING_CONTENT`.
  - `extracao_respostas`: 4 respostas da aluna, nenhuma em branco/ilegivel.
  - `correcao`: nota final `8`, acertos nas questoes 1, 2 e 4, erro na questao
    3 por calcular `15% de 200` como `25` em vez de `30`.
  - `analise_habilidades` e `relatorio_final`: coerentes com a correcao e com
    recomendacao focada em porcentagem.
- Status atualizado: a fixture simples GPT-5.4 Mini passou em status, documentos,
  custos e inspeção semantica inicial. Isso nao valida Gemini/Nano/Haiku/GPT-4o
  nem datasets maiores.
- Checagem PDF: `correcao`, `analise_habilidades` e `relatorio_final` retornam
  HTTP 200, sao PDFs reais e têm texto extraivel. Achados: o PDF de correcao
  truncou feedback longo em tabela estreita; o relatorio exibiu `Nota final:
  8/10 (75% de proficiência geral)`, que mistura metricas diferentes.
- Patch local: `backend/executor.py` agora instrui os PDFs de `CORRIGIR`,
  `ANALISAR_HABILIDADES` e `GERAR_RELATORIO` a usar word-wrap/blocos sem cortar
  texto; `GERAR_RELATORIO` deve rotular `nota_final` e `proficiencia_geral` como
  metricas separadas e nunca escrever `8/10 (75%)`.
- Validações locais do patch PDF: `py_compile`; `git diff --check`;
  `test_stage_tool_pdf_quality.py`, `test_f_t1_corrigir_tool_migration.py`,
  `test_f_t2_analisar_tool_use.py` e `test_f_t3_relatorio_tool_migration.py`
  com `41 passed` e o aviso conhecido de pytest `timeout`.
- Proximo alvo: commitar/deployar o patch PDF, aplicar `token_usage` duravel,
  revalidar providers restantes e atacar UI de erros.

## Riscos Abertos

1. Creditos Anthropic insuficientes ainda bloqueiam validacao Haiku.
2. Schema drift pode fazer modelos gerarem formatos diferentes.
3. Schema minimo ainda nao esta validado para todas as etapas; JSON parseavel e
   necessario, mas nao prova qualidade pedagogica.
4. A tabela Supabase `token_usage` tem migration dedicada em `b2dc88b`, mas o
   live confirmou que ela ainda nao existe no schema cache (`PGRST205`).
5. O gate oficial de deploy precisa continuar usando `/api/deploy-info` e smoke
   live; marker HTML pode ficar atrasado em servico `rootDir=backend`.
6. Gemini 3 Flash bateu quota `429` em pipeline sequencial completa; nao tratar
   isso como bug silencioso da pipeline, mas tambem nao chamar de pipeline
   completa validada.
7. `extrair_gabarito` parseavel pode ser conteudo invalido quando todas as
   respostas viram `MISSING_CONTENT`; Nano passou no smoke pos-`5527e26`, mas
   Gemini ainda precisa rerun antes de voltar a ✅.
8. `extrair_respostas` parseavel pode ser conteudo invalido quando as respostas
   ficam sem conteudo, inferidas ou inconsistentes; Nano ainda e ❌ nessa etapa,
   enquanto GPT-5.4 Mini passou em amostras e em um smoke full simples.
9. Cadastro via settings no Render pode nao sobreviver deploy; modelos oficiais
   precisam estar versionados em `backend/data/models.json` ou em storage
   duravel real.
10. Artefatos com `status=erro` podem ter arquivo/conteudo parcial; UI e docs
   devem ensinar o usuario a obedecer o status, nao o simples fato de existir
   arquivo.
11. Rio 3 nao deve voltar ao fluxo ativo sem nova decisao e nova chave segura.
12. Status `completed` da task nao basta; a correção precisa ser semanticamente
    compativel com `extracao_respostas` e `gabarito_extraido`. O caso
    `task_bc6cc84d10ef` provou falso positivo semantico, e o caso
    `task_a5f0d734f0b3` passou na inspeção JSON inicial, mas ainda precisa
    checagem de PDFs/UI e repeticao alem da fixture simples.
