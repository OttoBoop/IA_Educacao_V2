# Progresso de Longo Prazo — Visao Geral do Projeto

## Objetivo do Projeto

Garantir que a pipeline do NOVO CR funcione de forma confiavel com multiplos modelos de IA (Haiku, Gemini 3 Flash, GPT-5 Nano, e eventualmente Rio 3.0), produzindo documentos corretos com avisos de qualidade, e rastreando custos por materia.

## Estado Atual por Frente de Trabalho

### Frente 1: Documentacao e Diagnostico — 90% concluida

| Documento | Status | Arquivo |
|-----------|--------|---------|
| 01 Historico de Problemas | Concluido | [01_historico_problemas_pipeline.md](01_historico_problemas_pipeline.md) |
| 02 Decisoes Arquiteturais | Concluido (com ressalvas — algumas hipoteses precisam validacao empirica) | [02_contexto_decisoes_arquiteturais.md](02_contexto_decisoes_arquiteturais.md) |
| 03 Plano Operacional | Concluido | [03_plano_operacional_debug.md](03_plano_operacional_debug.md) |
| 04 Fontes e Governanca | Concluido — melhor documento, catalogo de referencia | [04_fontes_dados_governanca.md](04_fontes_dados_governanca.md) |
| 05 Visao Longo Prazo | Concluido | [05_visao_longo_prazo.md](05_visao_longo_prazo.md) |
| 06 Orquestracao | Concluido | [06_fluxo_orquestracao_case_tracking.md](06_fluxo_orquestracao_case_tracking.md) |
| 07 Auditoria Lista0 | Concluido — 402 docs auditados | [07_relatorio_auditoria.md](07_relatorio_auditoria.md) |
| Investigacao prova_respondida | Concluido — nao e bug, e limitacao do endpoint | [investigacao_prova_respondida.md](investigacao_prova_respondida.md) |
| Investigacao fantasmas/templates | Concluido — causas raiz encontradas | [investigacao_fantasmas_templates.md](investigacao_fantasmas_templates.md) |
| Teste Haiku/Eric | Concluido (com fallback GPT-4o) | [teste_haiku_eric.md](teste_haiku_eric.md) |

### Frente 2: Testes Multi-Provider — 33% concluida

| Modelo | Testado? | Resultado |
|--------|----------|-----------|
| Claude Haiku 4.5 | Tentado | Falha por falta de creditos Anthropic |
| GPT-4o (fallback) | Sim | Pipeline completou, mas sem `_avisos_*` e com schema antigo |
| Gemini 3 Flash | Pendente | — |
| GPT-5 Nano | Pendente | — |

### Frente 3: Correcao de Bugs — 2 fixes aplicados, 5+ pendentes

**Aplicados:**
- [x] URL Anthropic multimodal sem /messages (anexos.py)
- [x] Mensagem de erro generica no 400 (chat_service.py)

**Pendentes (priorizados):**
- [ ] **P1:** Unificar schemas PROMPTS_PADRAO vs STAGE_TOOL_INSTRUCTIONS
- [ ] **P2:** Injetar defaults `_avisos_*` no handler create_document
- [ ] **P3:** Corrigir visualizador para ler avisos de ANALISAR/GERAR
- [ ] **P4:** Adicionar checagem pre-voo de prova_respondida antes de EXTRAIR_RESPOSTAS
- [ ] **P5:** Corrigir `_preparar_variaveis_texto()` para fallback de nota_final
- [ ] **P6:** Nao descartar `_documentos_faltantes` em gerar_relatorio()
- [ ] **P7:** Corrigir flags em models.json (Sonnet function_calling, Gemini Lite)

### Frente 4: Limpeza de Dados — Pendente

- [ ] Deletar 183 documentos fantasma (aguardando aprovacao)
- [ ] Remover duplicatas de extracao_questoes/gabarito (54 docs redundantes)

### Frente 5: Rastreamento de Custos — Nao iniciada

- Arquitetura proposta no Doc 05
- Depende de: corrigir tokens_saida no Path 2 + ChatClient retornar input/output separados
- Estimativa: trabalho medio, 3-4 arquivos a modificar

### Frente 6: Provider Rio 3.0 — WIP (catalogado; aguardando planejamento/provisionamento no site oficial Render)

- Familia Rio publica catalogada no Doc 08: Rio 3.0 Open, Open Search, Open Mini,
  Open Nano, Rio 2.5 Open e Rio 2.5 Open VL
- Usuario informou acesso a Mini e Nano
- Escopo de teste inicial travado: rodar somente Rio Open Mini, e somente como
  progresso operacional quando estiver planejado e provisionado no site oficial
  Render
- ProviderType.CUSTOM ja existe e cai em formato OpenAI-compatible

#### Registro de evento e decisao - 2026-04-17

- O orquestrador/Paulo tratou um popup/local como se ele resolvesse o site
  oficial; isso foi reclassificado como falso progresso para a Frente 6
- Decisao de rumo: Rio 3 so conta como progresso operacional quando estiver
  planejado e provisionado no site oficial Render
- Revisao dos subagentes Maxwell (Planejador Rio 3) e Hume (Seguranca Site
  Oficial): secret deve entrar via Render env primeiro; popup publico fica
  bloqueado sem admin gate; Rio Open Mini e o unico alvo de teste; tool calling
  ainda nao foi validado
- Nao registrar segredo de API neste documento

#### Estado atual consolidado - 2026-04-17

- Bloqueio atual: site oficial ainda depende de secrets `RIO3_*` no Render e de
  governanca/admin gate antes de qualquer popup publico de chave real
- Decisao ja travada: Rio Open Mini e o unico alvo de teste inicial; Nano fica
  documentado, mas fora da primeira bateria
- Proximo gate necessario: provisionar `RIO3_API_KEY`, `RIO3_BASE_URL` e
  `RIO3_MODEL_ID` no Render, confirmar deploy e so entao testar conexao sem
  expor segredo
- Ajuste aplicado na orquestracao: `render.yaml` deve declarar as variaveis
  `RIO3_*` para o site oficial, alinhando blueprint, codigo e testes

#### Registro Log Vivo Rio 3 - 2026-04-17

- Agentes anteriores da Frente 6 finalizaram a passagem; novos agentes de
  execucao foram acionados pelo orquestrador Paulo para acompanhar o fluxo
  real no site oficial Render.
- Ainda nao ha chamada real Rio 3 validada: ela so deve ocorrer depois que a
  chave e demais `RIO3_*` estiverem provisionados no Render, sem registrar
  segredo em chat, docs ou logs.
- Estado esperado agora: registrar falhas reais de smoke test/harness e
  evidencias de bloqueio ate a configuracao server-side existir no Render.

#### Registro de execucao segura - 2026-04-17

- Sonda do site oficial: `GET /api/health` respondeu HTTP 200/healthy, mas
  `/api/settings/models` mostrou 13 modelos e nenhum Rio/Rio Open Mini.
- Sonda de chaves: `/api/settings/api-keys` respondeu HTTP 200 com 3 chaves
  mascaradas de providers existentes, sem chave `custom`/Rio; nenhum preview foi
  registrado neste documento.
- Harness criado: `backend/scripts/rio3_smoke.py` passa a emitir JSON seguro
  para `/models` e `chat/completions`, sem tool calling e sem imprimir segredo.
- Erro operacional atual reproduzido sem segredo: `MISSING_RIO3_ENV` quando
  `RIO3_API_KEY`, `RIO3_BASE_URL` e `RIO3_MODEL_ID` nao estao no ambiente.
- Suite focada Rio 3 validada por runner direto: 10 testes passaram cobrindo
  cofre, mascaramento, blueprint Render, frontend, sync por env e harness.
- Risco reforcado: rotas publicas de settings ainda expõem metadados
  administrativos; isso nao bloqueia secret via Render, mas bloqueia popup
  publico para chave real ate existir admin gate.

#### Fila operacional para Paulo destravar

1. Prioridade imediata: deployar suporte `RIO3_*` no Render para secret
   server-side; admin gate fica como requisito antes de aceitar chave real por
   UI publica.
2. Caminho da chave: orientar o usuario a abrir o painel seguro do Render e
   cadastrar `RIO3_API_KEY`, sem colar o valor no chat.
3. Endpoint/modelo: obter `RIO3_BASE_URL` e descobrir `RIO3_MODEL_ID` via
   `/v1/models` ou equivalente, sem imprimir headers ou segredo.
4. Confirmacao permitida: pedir apenas "secret configurado" depois que o valor
   estiver salvo no Render.
5. Deploy: pedir autorizacao explicita antes de push, deploy manual ou hook
   Render.
6. Governanca: registrar quem pode administrar modelos/chaves no site oficial e
   manter a URL publica proibida para chave real enquanto nao houver admin gate.

#### Protocolo de monitoramento do Paulo

- Paulo deve manter uma visao ativa dos subagentes acionados: quem esta
  trabalhando, qual pergunta recebeu, qual arquivo ou decisao afeta, e qual
  resultado ainda falta
- Enquanto agentes estiverem em execucao, Paulo deve relatar periodicamente ao
  usuario o que cada agente esta fazendo e como isso muda a interpretacao do
  plano, mesmo que o usuario nao esteja acompanhando cada mensagem em tempo real
- Cada relatorio deve separar fatos, inferencias e decisoes pendentes
- Paulo deve pensar em paralelo sobre as consequencias das respostas dos agentes,
  em vez de apenas repassar conclusoes mecanicamente
- Quando nem Paulo nem os agentes tiverem informacao suficiente para uma decisao
  segura, Paulo deve parar e fazer pergunta objetiva ao usuario antes de seguir
- Nenhum novo subagente deve ser acionado sem objetivo, constraints, entradas
  permitidas e saida esperada definidos; quando a aprovacao humana for exigida
  pelo protocolo da frente, Paulo deve pedir aprovacao antes

#### Protocolo para agentes externos/paralelos

- Paulo deve assumir que podem existir agentes externos ativos, mesmo quando nao
  foram criados por ele
- Paulo deve descobrir esses agentes por sinais locais antes de perguntar ao
  usuario: processos `codex`/`claude`, diretorios `/tmp/claude-*`, arquivos
  `subagents/*.jsonl`, timestamps recentes, `git status` e diffs por arquivo
- Esses agentes podem editar os mesmos `.md`; antes de qualquer alteracao em
  documento compartilhado, Paulo deve reler o trecho atual e conferir o estado
  do workspace
- Relatorios de Paulo devem distinguir:
  - agentes criados por Paulo;
  - agentes/processos externos inferidos por alteracoes no workspace;
  - mudancas cuja autoria nao esta clara
- Paulo nao deve sobrescrever ou "limpar" mudancas de autoria incerta; se houver
  conflito de narrativa, ele deve registrar o conflito ou perguntar ao usuario
- Quando um documento de plano for compartilhado por varios agentes, Paulo deve
  preferir adicionar registros datados e pequenas secoes de consolidacao, em vez
  de reescrever secoes amplas sem coordenacao
- Se um agente externo mudar um arquivo critico para a Frente 6, Paulo deve
  reportar o arquivo, o tipo de mudanca observado e a decisao que pode ser
  afetada
- Se um agente externo alterar qualquer doc de Rio 3, o fato deve virar registro
  datado neste Doc 09 antes de reescrever narrativa ou atualizar a visao geral

### Frente 7 (NOVA): Erros e Feedback na UI

Descoberta durante os testes: quando a pipeline falha, a UI nao comunica claramente o que aconteceu. O usuario fica sem saber se deu erro, qual erro, e o que fazer.

**Problemas identificados:**
- Nenhum popup ou banner de erro quando pipeline falha
- Status do aluno nao distingue visualmente "falhou" de "pendente" de "nunca rodou"
- Mensagens de erro genericas ("modelo indisponivel") que nao ajudam o usuario
- Log de erros so acessivel via backend/terminal, nao pela interface
- Quando creditos acabam, nao ha aviso proativo — o usuario so descobre quando tenta rodar

**O que precisa ter:**
- [ ] Popup/toast de erro quando qualquer etapa falha, com mensagem especifica
- [ ] Estado visual por aluno: icones/cores para sucesso/falha/pendente/nunca_rodou
- [ ] Painel de erros recentes acessivel na interface
- [ ] Mensagens claras para erros comuns: "creditos insuficientes", "modelo nao suporta tools", "documento faltante para o aluno X"
- [ ] Quando pipeline falha no meio: mostrar QUAL etapa falhou e QUAL aluno

### Frente 8 (NOVA): Endpoint /executar/etapa nao substitui variaveis

Descoberta durante testes empiricos: o endpoint `/api/executar/etapa` (usado pela GUI para rodar etapas individuais) envia o prompt com variaveis de template nao substituidas (`{{questao}}`, `{{resposta_aluno}}`, `{{gabarito}}`).

**Impacto:** Qualquer tentativa de rodar uma etapa individual pela GUI falha silenciosamente — a IA recebe um prompt vazio e responde "nao tenho dados".

**Causa provavel:** O endpoint nao carrega os documentos de etapas anteriores antes de renderizar o prompt. O `pipeline-completo` faz esse carregamento, mas o `/executar/etapa` nao.

**Fix necessario:** Investigar `routes_prompts.py` endpoint `/executar/etapa` (linhas 578-621) e garantir que `_preparar_variaveis_texto()` e `_preparar_contexto_json()` sejam chamados antes de `prompt.render()`.

## Riscos Abertos

1. **Creditos Anthropic:** Sem creditos, nao podemos testar Haiku (modelo default do sistema)
2. **Schema drift:** Enquanto PROMPTS_PADRAO e STAGE_TOOL_INSTRUCTIONS divergem, cada modelo pode gerar JSON em formato diferente
3. **Fantasmas poluindo dados:** 183 registros vazios distorcem estatisticas e confundem o status de alunos
4. **Endpoint /conteudo nao le PDFs:** Qualquer logica que dependa desse endpoint para acessar provas recebe null
5. **(NOVO) UI nao comunica erros:** Usuarios nao sabem quando/por que a pipeline falhou
6. **(NOVO) /executar/etapa quebrado:** Etapas individuais nao funcionam pela GUI
7. **(NOVO) Testes multi-provider incompletos:** So GPT-4o foi testado via pipeline-completo. Haiku, Gemini e GPT-5 Nano ainda precisam ser testados pelo caminho correto

## Licoes Aprendidas nesta Sessao

1. **Testar empiricamente antes de teorizar.** Os 6 docs de diagnostico mapearam o terreno, mas varias hipoteses so foram confirmadas/refutadas quando rodamos a pipeline de verdade.
2. **Nunca fazer fallback silencioso.** O sistema trocava de modelo sem avisar. Agora falha explicitamente (commit 44c5786).
3. **Testar pelo caminho certo.** Testamos via `/executar/etapa` (quebrado) e quase reportamos como "modelo nao funciona" quando o bug era no endpoint.
4. **Relatorios precisam ser claros.** Tabelas enormes sem contexto nao ajudam. Explicar o que esta acontecendo em linguagem humana antes de jogar dados.
5. **Mudancas relevantes no plano longo prazo ficam registradas aqui.** Quando houver virada de status, decisao de escopo ou correcao de rumo em frentes como a do Rio 3, este documento deve receber o registro datado antes de o trabalho seguir adiante.
