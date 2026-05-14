# Painel Vivo Paulo -- NOVO CR

**Atualizado:** 2026-05-15
**Responsavel operacional:** Paulo
**Status geral:** fixes de pipeline/custos publicados no GitHub; Render oficial
ainda bloqueado/stale; Sprint 3b de metadata/custos testada localmente e ainda
nao visivel no site.

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
| Pipeline | Fixes locais publicados no GitHub; Render ainda stale | Confirmar deploy oficial antes de chamar qualquer fix de pronto |
| Schema e avisos | Sprint 2 concluida localmente | Manter schema oficial, defaults e visualizador cobertos por testes |
| Custos/tokens | Metadata de documento e endpoints de custo implementados localmente | Publicar, deployar e validar `/api/custos/*` no site oficial |
| UI de erros | Pendente | Mostrar falha por aluno/etapa sem depender de terminal |
| Limpeza de dados | Pendente | Reclassificar "fantasmas" antes de qualquer delecao |
| Rio 3 | Pausada | Nao pedir chave, nao rodar smoke, nao deployar Rio sem nova decisao |

## Estado Git/Deploy Oficial

- Local funcional anterior validado: `b12be9a`.
- Commit funcional de custos/docs: `f67055c`.
- GitHub `origin/main`: `462ea1d` (`chore: mark deploy f67055c`) apos push.
- Render live observado: ainda `2e1098f` apos polling de 900s e check direto.
- `/api/custos/status` no Render: HTTP 404, confirmando que o site ainda nao tem
  os endpoints de custo do commit `f67055c`.
- GitHub Actions: sem runs recentes observaveis.
- GitHub webhooks/deployments via `gh api`: sem entradas visiveis.
- Render MCP: bloqueado por workspace nao selecionado.
- Inferencia operacional: auto-deploy nao esta funcionando; docs historicos ja
  dizem que o caminho oficial era deploy hook/manual. Como o hook foi
  redigido/precisa rotacao, deploy oficial esta bloqueado ate haver canal seguro.

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
  marcador `462ea1d` aponta o HTML para `f67055c`.
- Deploy: `wait_deploy.sh b12be9a` deu timeout apos 900s e checks diretos para
  `f67055c` continuaram vendo `2e1098f`; sem Actions, webhooks ou deployments
  GitHub visiveis; Render MCP sem workspace. Isto e bloqueio real de deploy
  oficial, nao sucesso local.
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
- Validacoes: `py_compile` dos arquivos tocados passou; `git diff --check`
  passou; `pytest backend/tests/unit/test_cost_tracking.py -q` passou com 4
  testes; suite focada ampliada passou com 171 testes, 5 skipped e 1 aviso de
  config `timeout` desconhecida; TestClient confirmou `/api/custos/status` e
  `/api/custos/resumo` com HTTP 200 local.
- Proximo alvo: desbloquear deploy oficial via Render hook/manual seguro; depois
  validar `/api/custos/*`, smoke provider e metadata no site oficial.

## Riscos Abertos

1. Creditos Anthropic insuficientes ainda bloqueiam validacao Haiku.
2. Schema drift pode fazer modelos gerarem formatos diferentes.
3. Metadata de tokens/modelo foi corrigida localmente para documentos de IA e
   tools, mas ainda precisa deploy/smoke oficial.
4. UI ainda nao comunica falhas da pipeline com clareza suficiente.
5. Rio 3 nao deve voltar ao fluxo ativo sem nova decisao e nova chave segura.
