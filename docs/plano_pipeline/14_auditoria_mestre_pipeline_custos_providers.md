# Auditoria Mestre -- Pipeline, Custos, Providers e Fallbacks

**Data:** 2026-05-14
**Responsavel operacional:** Paulo
**Status:** mapa grande de auditoria; o Doc 09 continua sendo o painel vivo curto

Este documento existe porque a pasta de planejamento ficou grande demais para ser
lida de memoria. Ele nao substitui os documentos originais: ele explica como cada
um deve ser lido, o que ainda vale, o que ficou historico, e quais fatos precisam
guiar os proximos ciclos.

## Indice

Use este indice como mapa de navegacao. O valor desta auditoria nao e quantidade
de linhas: e conseguir sair de uma pergunta para a evidencia certa sem reler a
pasta inteira.

### Entrada Rapida

| Se voce quer entender... | Leia primeiro |
|---|---|
| Como retomar apos compactar | [Fontes De Verdade E Loop Pos-Compactacao](#fontes-de-verdade-e-loop-pos-compactacao) |
| O estado inteiro do projeto | [Estado Do Projeto Em Uma Pagina](#estado-do-projeto-em-uma-pagina) |
| A resposta completa que uma IA deve dar | [Resposta Modelo Do Estado Do Projeto](#resposta-modelo-do-estado-do-projeto) |
| As tarefas claras herdadas do Doc 02 | [Checklist Executavel Do Doc 02](#checklist-executavel-do-doc-02) |
| Como resolver os problemas em loop | [Loop De Resolucao Dos Problemas](#loop-de-resolucao-dos-problemas) |
| Como uma IA deve retomar o trabalho | [Guia Para Qualquer IA Retomar](#guia-para-qualquer-ia-retomar) |
| O que falta no longo prazo | [Lacunas Do Documento De Longo Prazo](#lacunas-do-documento-de-longo-prazo) |
| A tese central do projeto | [Notas Gerais](#notas-gerais) |
| O que esta quebrado agora | [Diagnostico Executivo](#diagnostico-executivo) e [Mapa Geral Das Travas](#mapa-geral-das-travas) |
| A regra mais urgente | [P0 -- Jamais Usar Fallback Silencioso](#p0----jamais-usar-fallback-silencioso) |
| O estado de custos | [Custos -- Estado Correto](#custos----estado-correto) |
| O estado dos providers | [Providers -- Estado Correto](#providers----estado-correto) |
| O que cada documento significa | [Mapa Dos Documentos](#mapa-dos-documentos) |
| O que fazer a seguir | [Proximos Ciclos Recomendados](#proximos-ciclos-recomendados) e [Trabalho Aberto Desta Auditoria](#trabalho-aberto-desta-auditoria) |

### Indice Geral

1. [Fontes De Verdade E Loop Pos-Compactacao](#fontes-de-verdade-e-loop-pos-compactacao)
2. [Estado Do Projeto Em Uma Pagina](#estado-do-projeto-em-uma-pagina)
3. [Resposta Modelo Do Estado Do Projeto](#resposta-modelo-do-estado-do-projeto)
4. [Checklist Executavel Do Doc 02](#checklist-executavel-do-doc-02)
5. [Loop De Resolucao Dos Problemas](#loop-de-resolucao-dos-problemas)
6. [Guia Para Qualquer IA Retomar](#guia-para-qualquer-ia-retomar)
7. [Lacunas Do Documento De Longo Prazo](#lacunas-do-documento-de-longo-prazo)
8. [Como Ler Esta Auditoria](#como-ler-esta-auditoria)
9. [Notas Gerais](#notas-gerais)
10. [Diagnostico Executivo](#diagnostico-executivo)
11. [P0 -- Jamais Usar Fallback Silencioso](#p0----jamais-usar-fallback-silencioso)
12. [Estado Real Resumido](#estado-real-resumido)
13. [Mapa Geral Das Travas](#mapa-geral-das-travas)
14. [O Que O Plano Longo Ainda Nao Diz Bem](#o-que-o-plano-longo-ainda-nao-diz-bem)
15. [Perguntas Que O Proximo Ciclo Deve Responder](#perguntas-que-o-proximo-ciclo-deve-responder)
16. [Inventario Inicial De Fallbacks A Auditar](#inventario-inicial-de-fallbacks-a-auditar)
17. [Cobertura Total De `docs/`](#cobertura-total-de-docs)
18. [Indice De Quotes Obrigatorias](#indice-de-quotes-obrigatorias)
19. [Mapa Dos Documentos](#mapa-dos-documentos)
20. [Docs Vivos](#docs-vivos)
21. [Historicos Fundamentais](#historicos-fundamentais)
22. [Evidencias De Teste](#evidencias-de-teste)
23. [Nota Tecnica Sobre PDFs](#nota-tecnica-sobre-pdfs)
24. [Rio 3 Pausado](#rio-3-pausado)
25. [Docs Meta Do Loop](#docs-meta-do-loop)
26. [Fontes Complementares De `docs/`](#fontes-complementares-de-docs)
27. [Custos -- Estado Correto](#custos----estado-correto)
28. [Providers -- Estado Correto](#providers----estado-correto)
29. [Fallbacks A Remover Ou Converter Em Erro](#fallbacks-a-remover-ou-converter-em-erro)
30. [Feito, Falta, Bloqueios](#feito-falta-bloqueios)
31. [Proximos Ciclos Recomendados](#proximos-ciclos-recomendados)
32. [Criterios Para Dizer "Pronto"](#criterios-para-dizer-pronto)
33. [Validacao Desta Auditoria](#validacao-desta-auditoria)
34. [Trabalho Aberto Desta Auditoria](#trabalho-aberto-desta-auditoria)
35. [Fechamento](#fechamento)

## Fontes De Verdade E Loop Pos-Compactacao

Esta secao e o contrato para o Paulo continuar funcionando depois que a conversa
compactar. Se houver duvida entre memoria da conversa e estes arquivos, os
arquivos vencem. Se os arquivos estiverem contraditorios, registre a contradicao
no Doc 09 e corrija a fonte adequada antes de agir como se estivesse tudo claro.

### Onde Registrar O Que

| Fonte | Papel | Atualizar quando | Nao usar para |
|---|---|---|---|
| [09_progresso_longo_prazo.md](09_progresso_longo_prazo.md) | Painel vivo curto: estado, ciclo atual, validacoes, bloqueios e proximo alvo | Todo ciclo que muda estado real | Narrativa longa, quotes extensas ou investigacao historica |
| Este Doc 14 | Mapa mestre: leitura pos-compactacao, evidencias, interpretacoes, fila sistemica e regras de loop | Mudanca de interpretacao, arquitetura, ordem dos ciclos ou regra geral | Log detalhado de cada microciclo |
| [05_visao_longo_prazo.md](05_visao_longo_prazo.md) | Roadmap tecnico de longo prazo: custos, providers, metadata, escala e otimizacoes | Quando mudar prioridade estrategica, desenho de custos ou provider roadmap | Status minuto-a-minuto do workspace |
| [12_matriz_provider_fase.md](12_matriz_provider_fase.md) | Matriz por provider/modelo/rota/etapa/ambiente/commit | Apenas depois de teste ou smoke com evidencia | Opiniao teorica sobre modelos |
| [04_fontes_dados_governanca.md](04_fontes_dados_governanca.md) | Catalogo de dados, schemas, fontes e regra de exposicao | Quando schema/fonte de dados mudar de verdade | Registro de ciclos |
| [docs/missao.md](../missao.md) | Missao pedagogica e tese de produto de alto nivel | Quando a direcao do produto mudar e o arquivo for aprovado/versionado | Debug tecnico de pipeline |
| [arquivo_2026_04_17/02_contexto_decisoes_arquiteturais.md](arquivo_2026_04_17/02_contexto_decisoes_arquiteturais.md) | Contratos herdados do Path 1/Path 2, schemas, avisos, metadata e tokens | Em geral, nao editar; usar como evidencia historica | Estado atual sem confirmar no codigo |
| [arquivo_2026_04_17/03_plano_operacional_debug.md](arquivo_2026_04_17/03_plano_operacional_debug.md) | Plano antigo de debug, custos e providers | Em geral, nao editar; converter tarefas vivas para Doc 09/14/05 | Progresso atual |
| [arquivo_2026_04_17/06_fluxo_orquestracao_case_tracking.md](arquivo_2026_04_17/06_fluxo_orquestracao_case_tracking.md) | Metodo de acompanhar caso por aluno/etapa/provider | Em geral, nao editar; usar quando desenhar UI/log de erro | Roadmap geral |
| [notas](notas) | Notas tecnicas estreitas, como PDF com `conteudo=null` | Quando houver fato pequeno, estavel e reutilizavel | Novo planejamento amplo |
| [rio3_pausado](rio3_pausado) | Pesquisa Rio 3 congelada | Somente apos decisao explicita de retomar Rio 3 | Ciclo ativo de pipeline/custos gerais |
| [11_decisoes_otavio.md](11_decisoes_otavio.md) | Evidencia historica de disciplina de auditoria | Raramente; hoje e meta/historico | Plano ativo principal da pipeline |

### Retomada Apos Compactacao

Ao retomar depois de compactar, execute sempre esta sequencia:

1. Leia o Doc 09 do topo ate `Riscos Abertos`.
2. Leia neste Doc 14: esta secao, `Estado Do Projeto Em Uma Pagina`, `Resposta
   Modelo Do Estado Do Projeto`, `Checklist Executavel Do Doc 02` e `Loop De
   Resolucao Dos Problemas`.
3. Se o alvo toca custo, provider, metadata ou escala, leia o Doc 05.
4. Se o alvo toca provider real, smoke ou status de modelo, leia o Doc 12 e as
   evidencias de teste correspondentes em `arquivo_2026_04_17`.
5. Se o alvo toca Path 2, tool-use, schema, avisos, tokens ou custo, leia os
   Docs 02/03/06 arquivados antes de editar codigo.
6. Rode `git status --short` e, quando necessario, `git diff --name-only` para
   separar arquivos do ciclo, alteracoes de outros agentes e ruido local.
7. Diga ao usuario, em comentario curto, qual e a tese do ciclo, quais docs
   foram lidos, quais arquivos provavelmente entram e quais gates param o loop.
8. Trabalhe ate encontrar um gate real: segredo, deploy, comando destrutivo,
   decisao de produto ambigua, custo pago relevante ou conflito com outro agente.
9. Registre no Doc 09 antes de finalizar: data, alvo, arquivos tocados em alto
   nivel, validacoes, status e proximo alvo.

### Perguntas Que Paulo Deve Responder A Si Mesmo

Antes de editar, o Paulo deve conseguir responder sem improviso:

- Qual e o objetivo atual do NOVO CR neste ciclo?
- Qual contrato do Doc 02, risco de provider ou lacuna de custo esta sendo
  fechado?
- O trabalho e local, commitado, publicado, deployado ou smoke validado?
- Qual documento registra o status curto e qual registra a interpretacao longa?
- Quais arquivos sao provaveis e quais mudancas existentes sao de outros agentes?
- Quais testes provam o comportamento e quais validacoes documentais bastam?
- Qual gate obrigaria parar para perguntar ao usuario?

### Regras Anti-Perda De Loop

- Nao encerrar dizendo apenas "esta tudo planejado" se ainda existe alvo tecnico
  aberto e nenhum gate apareceu.
- Nao criar documento novo se Doc 09, Doc 14, Doc 05 ou Doc 12 ja comportam a
  informacao.
- Nao atualizar Doc 12 com "parece funcionar"; so entra evidencia por provider,
  rota, etapa, commit e ambiente.
- Nao registrar custo como real sem token medido, preco aplicado e contexto
  educacional persistido.
- Nao tratar Rio 3 como parte do loop ativo enquanto estiver pausado.
- Nao chamar fallback de robustez. Se mascara falha, e bug P0.

## Estado Do Projeto Em Uma Pagina

Esta e a secao de controle. Se o Paulo ler apenas isto, ele deve conseguir dizer
o estado do projeto do comeco ao fim. As secoes posteriores existem para provar,
detalhar e auditar estas linhas.

### Estado Em 10 Linhas

1. O objetivo do NOVO CR e gerar documentos pedagogicos confiaveis, nao apenas
   chamar modelos de IA.
2. A pipeline tem 6 etapas por aluno: 3 de extracao multimodal e 3 de analise
   por tool-use, alem de relatorios agregados.
3. O Doc 02 mostrou que o maior risco arquitetural esta no Path 2: schemas
   conflitantes, JSON opaco, avisos/metadata/tokens incompletos e tools parciais.
4. Os fixes foram publicados no GitHub; Render avancou do marcador `2e1098f`
   para `b12be9a` e o backend ja responde `/api/custos/*`, mas o HTML ainda nao
   mostra o marcador `f67055c`.
5. P4 foi corrigido localmente: `EXTRAIR_RESPOSTAS` nao deve rodar sem
   `prova_respondida` valida.
6. P5/P6 melhoraram relatorio e documentos faltantes, mas `nota_final=N/A` e
   apenas contencao temporaria e precisa virar erro alto.
7. Sprint 2 melhorou schema/defaults/visualizador, mas nao fechou o contrato do
   Doc 02 porque Path 2 ainda precisa validar schema antes de sucesso.
8. Sprint 3 separou `input_tokens`/`output_tokens`; Sprint 3b iniciou metadata
   persistida em documentos e endpoints `/api/custos/*`, ainda pendentes de
   deploy/smoke oficial.
9. Gemini 3 Flash e o melhor positivo parcial; GPT-5 Nano falhou grave;
   Haiku esta bloqueado por creditos; Rio 3 esta pausado. Em chat simples live,
   Gemini e GPT-5 Nano responderam JSON corretamente em 2026-05-15.
10. O proximo eixo correto e desbloquear deploy oficial e revalidar no site;
    depois vem anti-fallback/Path 2, providers e custos medidos em producao.

### O Que Temos

| Frente | Temos hoje | Limite da afirmacao |
|---|---|---|
| Documentacao | Doc 09 como painel curto; Doc 14 como auditoria mestre; Doc 05/12 com notas de status | Doc 14 ainda precisa revisao humana e commit. |
| Git/GitHub | Commits `7e4b852`, `3b3291f`, `a695db4`, `76c8467`, `b12be9a`, `f67055c` publicados; marcador `462ea1d` em `origin/main` | Render refletiu API de custos, mas HTML ainda marca `b12be9a`; docs podem ter commits acima do marcador. |
| Pipeline P4 | Bloqueio local de extracao de respostas sem prova valida | Precisa push/deploy/smoke para virar oficial. |
| Pipeline P5/P6 | Contencao de nota e preservacao de `_documentos_faltantes` | `N/A` ainda e fallback proibido como estado final. |
| Schema/avisos | Defaults `_avisos_*`, visualizador melhorado e schemas mais permissivos | Permissividade nao e contrato forte; pode aceitar legado demais. |
| Tokens/custos | Split input/output; metadata de documento; endpoints `/api/custos/status` e `/api/custos/resumo` respondendo live | Falta gerar documento novo pos-fix para provar metadata/custo em execucao fresca e persistir falhas com tokens. |
| Providers | Gemini e GPT-5 Nano passaram em chat simples live; Haiku bloqueado por credito; pipeline ainda depende de revalidacao | Chat simples nao prova pipeline/tool-use. |
| Seguranca Rio | Regra de nao usar chave em chat e Rio pausado | Arquivos Rio/untracked continuam fora do ciclo ativo. |

### O Que Falta

| Frente | Falta | Por que importa |
|---|---|---|
| Path 2/tool-use | Parsear e validar JSON salvo por `create_document`; retornar etapa real, documento principal e `resposta_parsed` | Sem isso, documento ruim pode parecer etapa concluida. |
| Anti-fallback | Remover sucesso verde para PDF auto-fallback, `nota_final=N/A`, JSON permissivo e provider/model swap | Fallback silencioso engana o usuario. |
| Prompts/schema | Resolver conflito entre `PROMPTS_PADRAO` legado e `STAGE_TOOL_INSTRUCTIONS` | Modelos pequenos podem seguir o schema errado. |
| Custos | Confirmar `/api/custos/*` em producao e registrar falhas que consomem tokens | Sem deploy, o custo ainda nao e oficial. |
| Metadata | Revalidar provider/modelo/tokens/tempo em documentos gerados no site | A correcao existe localmente, mas precisa smoke oficial. |
| Providers | Revalidar Gemini, Nano, Haiku e GPT-4o depois dos fixes locais | Resultado historico nao prova estado atual. |
| UI de erro | Mostrar aluno, etapa, provider, causa e artefato real/parcial/erro | Backend falhar alto nao basta se a UI traduz mal. |
| Dados | Reclassificar "fantasmas" sem deletar PDF valido por `/conteudo=null` | Evita apagar prova respondida real. |
| Git/deploy | Acionar Render por canal seguro e confirmar hash `b12be9a`/marcador | Sem isso, progresso no GitHub nao vira produto. |

### Bloqueios E Alertas

| Item | Estado | Acao correta |
|---|---|---|
| Render/site oficial | Bloqueado/stale em `2e1098f` | Usar deploy hook rotacionado/manual seguro; Render MCP sem workspace. |
| Anthropic Haiku | Bloqueado por creditos | Testar apenas quando houver credito; erro deve aparecer claro. |
| Rio 3 | Pausado | Nao pedir chave, nao rodar smoke, nao misturar no ciclo atual. |
| `.pytest_tmp` e assets soltos | Muito ruido no worktree | Nao stagear por acidente; nunca usar `git add .`. |
| Segredos | Chave em chat e sempre exposta | Nunca registrar valor; usar Render/env/admin gate quando retomar. |

### Ordem Correta Agora

1. Desbloquear deploy oficial e provar o hash no Render.
2. Revalidar `/api/custos/*` e metadata no site oficial.
3. Rodar ciclo anti-fallback/Doc 02 no Path 2.
4. Revalidar providers por rota/etapa/commit/ambiente.
5. Melhorar UI de erros.
6. Reclassificar dados "fantasma".
7. Retomar Rio 3 apenas por decisao explicita.

## Resposta Modelo Do Estado Do Projeto

Esta e a resposta que uma IA deve conseguir dar depois de ler este documento.
Ela nao substitui a auditoria; ela prova que a auditoria esta legivel.

### Do Comeco Ao Fim

O NOVO CR e uma pipeline pedagogica que transforma provas, gabaritos e respostas
em documentos uteis para professor e aluno. O produto nao e "rodar IA"; e gerar
correcao, analise de habilidades, relatorio individual, relatorios agregados e
chat/consulta com rastreabilidade.

A pipeline historica tem 6 etapas por aluno. As tres primeiras
(`EXTRAIR_QUESTOES`, `EXTRAIR_GABARITO`, `EXTRAIR_RESPOSTAS`) usam Path 1
multimodal: modelo recebe arquivos, retorna texto JSON, o executor parseia e
salva dict. As tres ultimas (`CORRIGIR`, `ANALISAR_HABILIDADES`,
`GERAR_RELATORIO`) usam Path 2 tool-use: modelo deve chamar `create_document` e
`execute_python_code`. O Doc 02 mostrou que esse segundo caminho e o gargalo:
ele salvava `content` como texto opaco, nao validava schema, podia perder avisos,
nao retornava `resposta_parsed`/`documento_id`, misturava schemas e nao media
tokens corretamente.

Desde entao houve progresso local. P4 bloqueou extracao de respostas sem
`prova_respondida` valida. P5/P6 preservaram documentos faltantes e evitaram
template literal de nota, mas a solucao `N/A` ainda e contencao temporaria. A
Sprint 2 melhorou schemas, defaults de `_avisos_*` e visualizador, mas ainda nao
fechou o contrato do Doc 02 porque defaults/permissividade nao sao prova de JSON
correto. A Sprint 3 separou `input_tokens` e `output_tokens` localmente, mas
custo real persistido ainda nao existe.

O estado oficial e mais fraco que o estado local. O `main` local tem commits que
`origin/main` ainda nao tem, e Render/site oficial nao foram confirmados nesses
commits. Portanto a palavra "feito" significa, por enquanto, "feito localmente"
para esses ciclos.

Provider por provider: Gemini 3 Flash e o melhor positivo parcial historico,
mas precisa revalidacao pos-fix; GPT-5 Nano falhou grave no pipeline-completo e
deve falhar alto ou ser corrigido antes de promocao; Haiku esta bloqueado por
creditos Anthropic; GPT-4o e referencia historica, nao fallback automatico; Rio
3 esta pausado e nao deve entrar em ciclo ativo nem receber chave em chat.

Custos estao em tres camadas: estimativas no Doc 05/catalogo, medicao local de
tokens apos `b12be9a`, e custo real persistido ainda ausente. Sem
`TokenUsageRecord`, metadata confiavel e precificacao aplicada na pipeline, nao
da para responder "quanto custou esta atividade/turma/aluno".

O proximo ciclo tecnico correto e cumprir o Doc 02 no Path 2 e remover fallback
silencioso: JSON invalido deve falhar na etapa original; PDF auto-fallback nao
pode virar sucesso verde; nota ausente nao pode virar `N/A`; provider/modelo
solicitado deve rodar ou falhar; metadata e documento principal precisam ser
retornados e persistidos. So depois faz sentido persistir custo real, revalidar
providers, melhorar UI de erro e limpar dados.

### Estado Em Tabela

| Area | Estado real | Proxima tarefa clara |
|---|---|---|
| Produto | Objetivo pedagogico definido | Manter qualidade/erro visivel acima de velocidade. |
| Docs | Doc 09 painel; Doc 14 auditoria; Doc 05 roadmap com lacunas | Revisar/commitir docs explicitamente. |
| Git/producao | Local a frente de `origin/main`; Render nao confirmado | Gate de commit/push/deploy/smoke quando autorizado. |
| Path 1 | Melhor estruturado; P4 protege `prova_respondida` | Revalidar em site oficial. |
| Path 2 | Melhorou, mas contrato Doc 02 aberto | Validar schema/tool outputs antes de sucesso. |
| Fallbacks | P0 definido, mas codigo ainda tem riscos | Ciclo anti-fallback com testes. |
| Custos | Token split local; custo real ausente | `TokenUsageRecord` + metadata + precificacao. |
| Providers | Matriz historica/stale | Revalidar por rota/etapa/commit/ambiente. |
| UI | Erros ainda pouco claros | Mostrar aluno, etapa, provider e causa. |
| Dados | "Fantasmas" precisam reclassificacao | Nunca deletar PDF valido por `/conteudo=null`. |

## Checklist Executavel Do Doc 02

Esta e a parte que faltava: o Doc 02 nao e apenas contexto historico. Ele vira
fila de tarefas. Cada item abaixo deve ser entendido como contrato herdado.

| # | Tarefa clara herdada do Doc 02 | Status real | Evidencia/observacao | Proximo ciclo/teste |
|---|---|---|---|---|
| D02-1 | Path 2 deve parsear e validar JSON de `create_document` antes de sucesso | Aberto P0 | Handler ainda trabalha com `content` textual; defaults ajudam, mas nao provam schema valido | Teste: JSON malformado em CORRIGIR falha a etapa original e nao salva resultado real. |
| D02-2 | `executar_com_tools()` deve retornar etapa real, `resposta_parsed` e `documento_id` | Aberto | Token split melhorou, mas retorno ainda nao e equivalente ao Path 1 | Teste: CORRIGIR retorna `etapa=CORRIGIR`, doc principal e parsed JSON validado. |
| D02-3 | Resolver conflito `PROMPTS_PADRAO` vs `STAGE_TOOL_INSTRUCTIONS` | Aberto | Validacao aceita formatos, mas prompt legado ainda pode orientar modelo ao schema errado | Teste: prompt ativo de Path 2 contem apenas contrato esperado ou marca legado como fora do caminho ativo. |
| D02-4 | `_avisos_documento`, `_avisos_questao`, `_avisos_stage` devem ser confiaveis | Parcial | Defaults foram injetados; visualizador melhorou; ainda falta distinguir default de output real do modelo | Teste: ausencia de `_avisos_*` em JSON de IA gera alerta de schema/default, nao sucesso silencioso. |
| D02-5 | Tokens do Path 2 precisam de input/output separados | Feito localmente | `b12be9a` corrige medicao local | Revalidar apos push/deploy; manter teste de `ChatClient` e `executar_com_tools`. |
| D02-6 | Tokens precisam virar custo persistido por contexto educacional | Aberto | `TokenUsageRecord` ainda nao existe operacionalmente | Teste: etapa real cria registro com materia/turma/atividade/aluno/etapa/provider/modelo/custo. |
| D02-7 | Metadata dos documentos deve ter provider/modelo/tokens/tempo | Aberto | Storage tem campos, mas tool handler salva `pipeline_tool` sem metadata suficiente | Teste: documento gerado por IA tem `ia_provider`, `ia_modelo`, `tokens_usados`, `tempo_processamento_ms`. |
| D02-8 | Provider sem tools nao pode cair em chat simples | Parcialmente fechado | `chat_service.py` agora falha explicitamente; manter contrato | Teste: provider sem function calling em etapa tool-use falha antes de criar artefato. |
| D02-9 | PDF obrigatorio ausente nao pode virar sucesso enganoso | Aberto P0 | PDF auto-fallback ainda pode salvar PDF e retornar `sucesso=True` | Teste: modelo que nao chama `execute_python_code` falha ou retorna parcial bloqueante, nunca verde. |
| D02-10 | Retry dual-output nao pode duplicar/mascarar documentos | Aberto | Doc 02 apontou risco de duplicatas no retry | Teste: retry cria no maximo um JSON principal por etapa ou marca duplicata como erro. |
| D02-11 | GPT-5 Nano-like output lixo deve falhar cedo | Aberto P0 | Historico mostra documentos lixo no pipeline-completo | Teste fixture Nano-like falha em CORRIGIR antes de ANALISAR/GERAR. |
| D02-12 | `GERAR_RELATORIO` precisa de schema unico e nota confiavel | Aberto P0 | `nota_final=N/A` e formatos legado/tool-use coexistem | Teste: relatorio sem nota confiavel falha alto; schema ativo e unico. |

### Ordem De Execucao Do Checklist

1. Fechar D02-1, D02-2, D02-9, D02-11 e D02-12 juntos como ciclo
   **Path 2 anti-fallback**.
2. Fechar D02-3 e D02-4 como ciclo **contrato de schema/avisos**.
3. Fechar D02-7 e D02-6 como ciclo **metadata e custo real**.
4. Revalidar D02-5 e D02-8 em producao.
5. So depois atualizar matriz de providers e UI de erro.

## Loop De Resolucao Dos Problemas

Este e o plano operacional que faltava. Ele existe para evitar ciclos vagos do
tipo "melhorar docs" ou "corrigir pipeline". Cada ciclo precisa ter uma tese,
um conjunto pequeno de arquivos, testes focados, registro no Doc 09 e um criterio
de aceite que impeça progresso falso.

### Principio Do Loop

O loop nao fecha "o projeto" de uma vez. Ele fecha contratos pequenos, em ordem.
Cada contrato sai de:

`identificado -> reproduzido -> teste falhando -> corrigido localmente -> validado
localmente -> registrado -> commitado -> publicado -> smoke validado`.

Enquanto um item esta antes de `smoke validado`, ele nao e produto pronto. Ele e,
no maximo, progresso local.

### Template Obrigatorio De Cada Ciclo

| Etapa | O que fazer | Saida obrigatoria |
|---|---|---|
| 0. Snapshot | Ler Doc 09, esta secao, `git status`, arquivos provaveis e testes existentes | Lista curta de fatos, nao inferencias. |
| 1. Tese | Escolher uma unica frase de alvo | Exemplo: "Path 2 nao pode salvar JSON invalido como sucesso". |
| 2. Reproducao | Criar ou localizar teste que demonstre o bug | Teste falhando ou evidencia concreta de codigo. |
| 3. Correcao minima | Alterar o menor conjunto de arquivos necessario | Patch sem refatoracao lateral. |
| 4. Validacao local | Rodar teste focado, `py_compile` se Python mudou e `git diff --check` | Comandos e resultado registrados. |
| 5. Registro | Atualizar Doc 09 com bloco curto e, se a historia for grande, este Doc 14 | Data, alvo, arquivos, validacoes, status, proximo item. |
| 6. Gate Git | Stage explicito, nunca `git add .`; commit somente do ciclo | Commit pequeno e rastreavel, quando autorizado. |
| 7. Gate Producao | Push/deploy/smoke somente com autorizacao | Commit no `origin/main`, Render no hash esperado, smoke real. |
| 8. Matriz | Atualizar provider/custo/UI apenas se o ciclo afetar essas matrizes | Status por modelo/rota/etapa/ambiente, sem generalizar. |

### Estados Permitidos

| Estado | Significado | Pode dizer pronto? |
|---|---|---|
| Planejado | Tese e testes definidos | Nao. |
| Reproduzido | Bug demonstrado por teste/evidencia | Nao. |
| Corrigido localmente | Patch aplicado e teste focado passa | Nao como produto; sim como local. |
| Commitado localmente | Commit existe no `main` local | Nao como site oficial. |
| Publicado | `origin/main` aponta para o commit | Ainda nao sem deploy/smoke. |
| Deploy confirmado | Render/site esta no hash esperado | Ainda precisa smoke do fluxo afetado. |
| Smoke validado | Endpoint/fluxo real provou o comportamento | Sim, com escopo claro. |

### Fila De Ciclos

#### Ciclo 1 -- Path 2 Anti-Fallback

**Tese:** etapas tool-use nao podem marcar sucesso quando JSON, PDF ou nota
obrigatoria falham.

**Contratos Doc 02 cobertos:** D02-1, D02-2, D02-9, D02-11, D02-12.

**Arquivos provaveis:**

- `backend/executor.py`
- `backend/tool_handlers.py`
- `backend/pipeline_validation.py`
- `backend/tests/unit/test_erro_pipeline.py`
- `backend/tests/unit/test_f7_t1_pdf_auto_fallback.py`
- novo teste focado se necessario, por exemplo `backend/tests/unit/test_path2_contract.py`

**Trabalho tecnico:**

- Fazer `create_document` produzir ou expor JSON parseavel para o executor.
- Validar schema minimo da etapa antes de `ResultadoExecucao(sucesso=True)`.
- Fazer `executar_com_tools()` retornar etapa real, `resposta_parsed` e
  `documento_id` principal quando houver sucesso.
- Trocar PDF auto-fallback verde por erro alto ou sucesso parcial bloqueante,
  conforme decisao de produto documentada no teste.
- Remover `nota_final=N/A` como aceite final de `GERAR_RELATORIO`.
- Criar fixture "Nano-like" com JSON malformado/nome alucinado/texto natural em
  `.json` e provar falha cedo em CORRIGIR.

**Testes minimos:**

- JSON malformado em `create_document` falha CORRIGIR.
- `create_document` com texto narrativo salvo como `.json` falha CORRIGIR.
- Ausencia de `execute_python_code` quando PDF e obrigatorio nao retorna sucesso
  verde.
- Relatorio sem nota confiavel falha alto.
- `executar_com_tools()` em sucesso retorna etapa real, doc principal e parsed.
- Nenhuma etapa seguinte precisa descobrir documento lixo.

**Aceite:** nenhum output invalido pode virar `completed`; nenhum fallback de
produto pode parecer sucesso.

#### Ciclo 2 -- Contrato De Schema E Avisos

**Tese:** o modelo deve receber um unico contrato ativo por etapa, e avisos
devem ser distinguiveis entre "gerados pelo modelo" e "default injetado".

**Contratos Doc 02 cobertos:** D02-3, D02-4, D02-10.

**Arquivos provaveis:**

- `backend/prompts.py`
- `backend/executor.py`
- `backend/tool_handlers.py`
- `backend/pipeline_validation.py`
- `backend/visualizador.py`
- testes de schema e warnings

**Trabalho tecnico:**

- Decidir se `PROMPTS_PADRAO` de Path 2 vira legado explicito ou e alinhado ao
  mesmo schema de `STAGE_TOOL_INSTRUCTIONS`.
- Marcar `_avisos_*` injetados como default tecnico, sem fingir que vieram da IA.
- Garantir `_avisos_stage` correto por tipo de documento.
- Evitar duplicatas no retry dual-output.

**Testes minimos:**

- Prompt final de CORRIGIR nao contem dois schemas conflitantes.
- Documento sem `_avisos_*` recebe default com alerta interno rastreavel.
- `_avisos_stage` e correto em CORRIGIR, ANALISAR e GERAR.
- Retry nao cria dois JSONs principais para a mesma etapa.

**Aceite:** schema ativo e unico por etapa; avisos legiveis e honestos.

#### Ciclo 3 -- Metadata E Custo Real

**Tese:** custo so existe quando tokens, provider, modelo, etapa e contexto
educacional sao persistidos em sucesso e falha.

**Contratos Doc 02 cobertos:** D02-5, D02-6, D02-7.

**Arquivos provaveis:**

- `backend/executor.py`
- `backend/storage.py`
- `backend/model_catalog.py`
- possivel novo `backend/token_usage.py`
- rotas de custo se ja existirem ou novo modulo focado
- testes unitarios de storage/custo

**Trabalho tecnico:**

- Passar `tokens_usados`, `tempo_processamento_ms`, `ia_provider`, `ia_modelo`
  e `prompt_usado` ate o documento persistido.
- Criar `TokenUsageRecord` mensal/local com materia/turma/atividade/aluno/etapa.
- Chamar `ModelCatalogManager.calculate_cost()` no fim de cada etapa validada.
- Registrar custo de falhas com `sucesso=false`, `erro_tipo` e `tentativas`.

**Testes minimos:**

- Documento gerado por IA salva provider/modelo/tokens/tempo.
- Etapa com sucesso cria registro de custo.
- Etapa com falha apos chamada de IA tambem cria registro de custo.
- Endpoint/resumo de custo retorna valor nao-zero depois de execucao controlada.

**Aceite:** responder "quanto custou esta etapa/aluno/atividade" sem abrir log.

#### Ciclo 4 -- Revalidacao De Providers

**Tese:** provider so tem status por modelo + rota + etapa + commit + ambiente.

**Pre-condicao:** ciclos 1 a 3 fechados localmente e publicados.

**Trabalho tecnico:**

- Confirmar commit no `origin/main`.
- Confirmar Render no hash esperado.
- Rodar smokes pequenos por provider sem trocar modelo automaticamente.
- Atualizar Doc 12 por evidencia, nao por expectativa.

**Testes/smokes minimos:**

- Gemini 3 Flash: duas execucoes pequenas com metadata/custo.
- GPT-5 Nano: falha alta confirmada ou schema/tool-use corrigido.
- Haiku: somente quando houver credito.
- GPT-4o: explicitamente selecionado, nunca fallback.

**Aceite:** matriz provider deixa de ser stale para o commit testado.

#### Ciclo 5 -- UI De Erros

**Tese:** se o backend falha alto, a UI precisa mostrar isso sem terminal.

**Trabalho tecnico:**

- Mostrar aluno, etapa, modelo/provider e causa.
- Separar documento real, parcial, erro e bloqueado.
- Toast verde nunca pode representar fallback proibido.

**Testes minimos:**

- Falha de schema aparece como erro da etapa.
- Credito insuficiente aparece como credito, nao "modelo invalido".
- Documento faltante aponta o aluno/atividade.
- Modelo sem tools mostra incompatibilidade de function calling.

**Aceite:** usuario entende o que falhou e qual acao tomar.

#### Ciclo 6 -- Limpeza De Dados

**Tese:** dados "fantasma" precisam ser reclassificados, nao deletados por
heuristica fraca.

**Trabalho tecnico:**

- Separar JSON de erro, documento real, PDF valido com `/conteudo=null`,
  duplicata e artefato temporario.
- Nunca deletar `prova_respondida` PDF so por `/conteudo=null`.

**Testes/validacoes minimas:**

- Lista de candidatos a limpeza com motivo e evidencia.
- Amostra revisada antes de qualquer delete.
- Operacao destrutiva so com gate explicito.

**Aceite:** limpeza segura e reversivel sempre que possivel.

### Como Registrar Cada Ciclo No Doc 09

Use sempre este formato curto:

```md
### YYYY-MM-DD -- Ciclo X: nome curto

- Alvo: uma frase com a tese.
- Status: planejado | reproduzido | corrigido localmente | commitado | publicado | smoke validado.
- Contratos: D02-n, D02-n.
- Arquivos tocados: lista curta.
- Validacoes: comandos e resultado.
- Fatos: o que foi provado.
- Bloqueios: segredo, deploy, credito, decisao de produto ou teste faltante.
- Proximo alvo: uma frase.
```

### Gates Que Param O Loop

Paulo deve parar e pedir autorizacao quando houver:

- segredo, chave, token, hook ou credential;
- deploy, push ou uso de hook Render;
- comando destrutivo, limpeza ou delete;
- decisao de produto ambigua, por exemplo erro vs sucesso parcial;
- risco de mexer em arquivos de outro agente;
- teste real com custo relevante.

Fora desses gates, o ciclo deve continuar ate pelo menos registrar teste,
resultado e proximo passo.

## Guia Para Qualquer IA Retomar

Esta secao existe para impedir que uma nova IA precise reconstruir o projeto a
partir de conversa solta. Antes de planejar ou executar, siga este roteiro.

### Primeira Leitura Obrigatoria

1. Leia [09_progresso_longo_prazo.md](09_progresso_longo_prazo.md) para estado
   vivo curto.
2. Leia `Fontes De Verdade E Loop Pos-Compactacao`.
3. Leia `Estado Do Projeto Em Uma Pagina`.
4. Leia `Resposta Modelo Do Estado Do Projeto`.
5. Leia `Checklist Executavel Do Doc 02`.
6. Leia `Loop De Resolucao Dos Problemas`.
7. Leia `Lacunas Do Documento De Longo Prazo`.
8. Leia `Contrato Do Doc 02 Que Ainda Nao Estamos Seguindo`.
9. So depois leia secoes finas de custos, providers, fallbacks e documentos.

### O Que A IA Deve Dizer Ao Retomar

Ao responder "qual e o estado do projeto?", a IA deve separar exatamente:

| Categoria | Deve conter |
|---|---|
| Feito localmente | Commits, testes locais e docs alterados no workspace. |
| Nao oficial | Tudo que ainda nao foi para `origin/main`, Render ou smoke real. |
| Bloqueado | Creditos, segredo, deploy, decisao de produto ou provider indisponivel. |
| Risco P0 | Fallback silencioso, schema invalido, PDF inventado, nota fake, modelo trocado. |
| Proximo ciclo | Uma tese unica, com arquivos provaveis e validacoes. |

### Regras De Operacao

- Nao declarar "pronto" sem dizer pronto em qual nivel: local, commitado,
  publicado, deployado ou smoke validado.
- Nao transformar melhoria local em conclusao de produto.
- Nao usar "fallback robusto" para comportamento que esconde falha.
- Nao criar outro documento pequeno quando Doc 09 ou Doc 14 bastam.
- Nao misturar Rio 3, deploy, segredo, custo e anti-fallback no mesmo ciclo.
- Registrar acontecimentos no Doc 09; registrar narrativa/evidencia grande aqui.
- Se um documento antigo contradiz a regra P0 atual, preservar a quote e
  reclassificar a interpretacao, sem apagar a historia.

### Estado Que Uma IA Deve Ser Capaz De Reproduzir

Depois de ler esta auditoria, qualquer IA deve conseguir dizer:

- o objetivo pedagogico do NOVO CR;
- como a pipeline de 6 etapas se divide em Path 1 e Path 2;
- por que o Path 2 e o gargalo central;
- quais commits locais existem e por que ainda nao sao site oficial;
- quais providers funcionaram, falharam, bloquearam ou estao stale;
- por que custo real ainda nao existe;
- quais fallbacks sao P0;
- qual e a ordem correta dos proximos ciclos.

## Lacunas Do Documento De Longo Prazo

O Doc 05 e o documento de estrategia. Ele ainda tem valor, mas precisa ser lido
como roadmap parcialmente stale. Esta auditoria registra o que falta para ele
virar um plano longo que qualquer IA consiga seguir sem interpretar demais.

| Lacuna no Doc 05 | Estado atual | Atualizacao necessaria |
|---|---|---|
| Nao distingue bem estimativa, medicao e custo persistido | Token split local existe, custo persistido nao | Manter as tres camadas separadas no topo do Doc 05. |
| Ordem antiga puxa custo antes de anti-fallback | Regra P0 mudou a prioridade | Declarar que Path 2/anti-fallback vem antes de dashboard de custo. |
| Provider roadmap mistura capacidade teorica e validacao real | Doc 12 esta stale | Exigir matriz por modelo + rota + etapa + commit + ambiente + metadata + custo. |
| Rio 3 aparece como frente futura longa | Rio esta pausado por decisao explicita | Manter Rio fora do loop ativo ate nova decisao e segredo seguro. |
| Otimizacoes de escala aparecem antes de confiabilidade base | Cache/batching/modelo por etapa sao uteis, mas prematuros | Marcar como "depois de schema, metadata, custo e UI de erro". |
| Custo de falha nao esta desenhado com forca suficiente | Falhas tambem gastam tokens | Incluir `sucesso`, `erro_tipo`, `tentativas` e custo de falha em `TokenUsageRecord`. |
| Metadata de documento aparece como detalhe, mas e fundacao | DB tem campos, mas alimentacao ainda falha | Tratar metadata como pre-requisito para custo e auditoria de provider. |

Resumo: o Doc 05 precisa deixar de ser apenas roadmap de custos/providers e virar
roadmap de **confiabilidade antes de escala**. O custo so e util quando o
documento gerado e valido, rastreavel e honesto.

## Como Ler Esta Auditoria

Esta auditoria deve ser lida **do geral para o fino**. A primeira versao estava
util, mas comeca rapido demais nos detalhes. A ordem correta para humanos e:

1. **Notas gerais:** qual e a tese do projeto, o que esta acontecendo, quais
   riscos mandam no resto.
2. **Estado real:** o que esta feito localmente, o que ainda nao foi para GitHub
   ou producao, e quais frentes estao pausadas.
3. **Temas transversais:** pipeline, custos, providers, UI, dados, seguranca e
   processo.
4. **Documentos individuais:** para que serve cada `.md`, qual quote importa e
   como ele deve orientar o proximo ciclo.
5. **Evidencia fina:** testes, linhas de codigo, comandos de validacao e gaps
   que viram tarefas.

Se voce estiver tentando entender o projeto sem mergulhar em tudo, leia nesta
ordem: `Notas Gerais`, `Diagnostico Executivo`, `Feito/Falta/Bloqueios`,
`Custos`, `Providers`, `Fallbacks`, e so depois o mapa documento por documento.

## Notas Gerais

### Nota Geral 1 -- O Produto Nao E "Rodar IA"

O objetivo do NOVO CR nao e chamar modelos por chamar. O produto existe para
gerar documentos pedagogicos confiaveis: correcao, analise, relatorio final,
relatorios agregados, e depois conversa/consulta sobre esses documentos.

Quotes que ancoram essa leitura:

> "rode com confiabilidade em multiplos modelos"

> "gere documentos corretos e com avisos de qualidade"

> "registre tokens e custos por materia/atividade/aluno"

> "O NOVO CR não é só um corretor automático"

Leitura geral:

- Provider bom e meio, nao fim.
- Custo so importa se o output e correto.
- UI so esta boa se o professor entende o que foi gerado, o que falhou e por que.
- Documento verde com conteudo ruim e pior que erro vermelho, porque engana.

### Nota Geral 2 -- A Pipeline E Uma Cadeia De Documentos

A pipeline principal tem 6 etapas sequenciais. As primeiras etapas preparam
documentos-base; as ultimas geram documentos por aluno. Quando uma etapa salva
um artefato ruim, o erro se espalha.

Modelo mental:

| Grupo | Etapas | Risco principal |
|---|---|---|
| Atividade | `EXTRAIR_QUESTOES`, `EXTRAIR_GABARITO` | Se o enunciado/gabarito vier ruim, todos os alunos herdam o problema. |
| Aluno | `EXTRAIR_RESPOSTAS` | Sem `prova_respondida` valida, a pipeline nao deve inventar resposta. |
| Correcao | `CORRIGIR`, `ANALISAR_HABILIDADES`, `GERAR_RELATORIO` | Tool-use/schema/PDF podem parecer sucesso mesmo quando o artefato esta errado. |
| Agregados | tarefa, turma, materia | So valem depois que os relatorios individuais sao confiaveis. |

Consequencia:

- O ciclo anti-fallback vem antes de dashboard de custo.
- O ciclo de custo real vem antes de UI bonita de custo.
- A UI de erro precisa mostrar aluno + etapa + provider + causa.

### Nota Geral 3 -- Existem Tres Tipos De "Funcionou"

Muitos conflitos vieram de tratar niveis diferentes de sucesso como se fossem a
mesma coisa.

| Tipo de sucesso | Exemplo | Pode chamar de pronto? |
|---|---|---|
| Sucesso local | Teste unitario passou no workspace | Nao, ainda falta GitHub/producao se afeta site. |
| Sucesso de endpoint | API retornou 200/task completed | Nao, ainda precisa validar documento/schema/metadata. |
| Sucesso de produto | Documento correto, schema valido, provider certo, erro visivel, custo rastreavel | Sim, se tambem estiver no site esperado. |

Regra:

- `HTTP 200` nao prova que a pipeline funcionou.
- `completed` nao prova que o documento presta.
- `tokens` na resposta nao prova que custo foi persistido.
- `Gemini passou uma vez` nao prova confiabilidade geral.

### Nota Geral 4 -- Custos Estao Em Tres Camadas Diferentes

O projeto tem tres camadas que estavam sendo misturadas:

| Camada | Estado | O que significa |
|---|---|---|
| Estimativa | Existe no Doc 05/catalogo | Serve para planejar, nao para auditar gasto real. |
| Medicao de tokens | Melhorou localmente em `b12be9a` | Permite calcular depois, mas ainda nao e custo persistido. |
| Persistencia de custo | Ainda falta | Necessaria para responder "quanto custou por materia/turma/aluno". |

Leitura geral:

- O projeto esta mais perto de custo real, mas ainda nao chegou nele.
- `input_tokens`/`output_tokens` separados sao pre-requisito, nao meta final.
- Sem `TokenUsageRecord`, custo por periodo ainda e projeto futuro.
- Sem metadata no documento, auditoria por artefato continua fraca.

### Nota Geral 5 -- Provider E Matriz, Nao Ranking

Provider nao deve ser classificado como "bom" ou "ruim" de forma absoluta. O
estado correto e por rota, etapa, schema, tool-use, custo e producao.

Leitura geral atual:

| Provider/modelo | Leitura curta |
|---|---|
| Gemini 3 Flash | Melhor evidencia positiva, mas parcial e com retry/metadata pendente. |
| GPT-5 Nano | Falhou no pipeline-completo; deve falhar alto ou ficar bloqueado. |
| Claude Haiku 4.5 | Bloqueado por creditos Anthropic; erro real precisa aparecer sem wrapper enganoso. |
| GPT-4o | Referencia historica, nao fallback automatico aceitavel. |
| Rio 3 | Pausado; nao entra neste loop. |

Regra:

- Chat OK nao vira pipeline OK.
- Etapa isolada OK nao vira pipeline-completo OK.
- Pipeline OK sem metadata nao vira custo OK.
- Modelo escolhido deve rodar ou falhar; nao trocar por outro.

### Nota Geral 6 -- Fallback Silencioso E O Tema Central

A palavra "fallback" apareceu em docs antigos como robustez. A interpretacao
nova e mais dura:

- Retry explicito no mesmo modelo pode ser bom.
- Resolver chave por env server-side pode ser bom.
- Sanitizar config interna corrompida pode ser aceitavel se visivel e antes da
  execucao.
- Trocar provider, aceitar JSON ruim, gerar PDF automatico, inventar nota ou
  marcar erro como documento final e bug de produto.

O erro central nao e "a IA errou"; IA errar e esperado. O erro central e o
sistema transformar esse erro em sucesso.

### Nota Geral 7 -- Dados "Fantasmas" Precisam De Reclassificacao, Nao Delecao

O caso `conteudo=null` provou que um nome de campo ruim pode induzir decisao
perigosa. PDF com `conteudo=null` nao significa arquivo vazio.

Regra:

- Nao deletar `prova_respondida` PDF por `/conteudo` retornar null.
- Verificar arquivo por storage/download/view.
- Separar "documento de erro" de "documento real".
- Status de aluno nao pode contar JSON de `_erro_pipeline` como correcao real.

### Nota Geral 8 -- UI De Erro E Parte Da Confiabilidade

O sistema nao esta confiavel se so o terminal explica a falha. A interface precisa
mostrar onde, para quem e por que a pipeline parou.

Casos obrigatorios:

- Creditos insuficientes.
- Documento obrigatorio faltando.
- Modelo sem tools.
- Schema invalido.
- Provider overload/transiente.
- PDF/JSON esperado ausente.

UI boa aqui nao e cosmetica. E a diferenca entre professor confiar no resultado
ou achar que deu tudo certo quando nao deu.

### Nota Geral 9 -- O Plano Longo Precisa Separar Fato, Inferencia E Decisao

Muitos documentos antigos misturam "foi observado", "provavelmente a causa e" e
"vamos fazer". Esta auditoria precisa separar:

| Tipo | Exemplo | Como usar |
|---|---|---|
| Fato | `tokens_usados=0` em teste Gemini | Base para bug. |
| Inferencia | Metadata nao esta sendo populada no caminho tool-use | Hipotese a confirmar no codigo/teste. |
| Decisao | Fallback silencioso e proibido | Regra para proximos ciclos. |
| Bloqueio | Creditos Anthropic insuficientes | Nao testar ate mudar condicao externa. |

Quando um documento antigo diz "resolvido", ainda precisamos perguntar:
resolvido localmente, no commit, no site oficial, com teste, com UI, ou com
custo?

### Nota Geral 10 -- O Loop De Trabalho Tambem E Um Produto

O projeto travou varias vezes porque o loop de trabalho falhou: rapido demais,
sem quotes, sem verificar producao, sem explicar feito/falta, ou criando docs
demais. Isso nao e detalhe emocional: afeta qualidade tecnica.

Regras de loop para Paulo:

- Comecar pelo geral, depois ir ao fino.
- Citar fontes antes de concluir.
- Registrar feito/falta/bloqueio.
- Nao chamar local de oficial.
- Nao esperar deploy parado; monitorar e continuar.
- Nao criar novo doc pequeno se Doc 09/14 bastam.
- Perguntar quando uma decisao de produto estiver ambigua.

## Diagnostico Executivo

| Pergunta | Resposta honesta |
|---|---|
| Qual e o objetivo agora? | Confiabilidade da pipeline e custo real para providers gerais; Rio 3 pausado. |
| O que esta melhor do que antes? | P4, P5/P6, schema/avisos e split de tokens foram corrigidos localmente. |
| O que ainda nao pode ser vendido como pronto? | Producao nao recebeu os 5 commits locais; custo nao e persistido; providers nao foram revalidados pos-fix. |
| Qual e o maior risco tecnico? | Fallback silencioso e output invalido parecerem sucesso. |
| Qual e o maior risco de produto? | Professor ver documento/status verde e nao entender que houve falha real. |
| Qual e o maior risco de processo? | Paulo resumir demais, pular fonte original e declarar pronto rapido. |
| Proximo ciclo recomendado | Auditoria anti-fallback, depois metadata/custo real, depois provider revalidation e UI de erro. |

## P0 -- Jamais Usar Fallback Silencioso

Regra urgente: **fallback silencioso e bug de produto**.

O NOVO CR nao pode trocar modelo, aceitar JSON ruim, inventar PDF, mascarar falta
de nota, ou marcar etapa como `completed` quando a saida real nao serve para a
proxima etapa. Isso faz o usuario achar que esta tudo bem quando o sistema acabou
de produzir lixo ou resultado incerto.

Linguagem nova para o plano:

- Nao dizer "fallback robusto" quando o comportamento esconde erro.
- Dizer "erro explicito, alto, visivel e bloqueante".
- Um modelo escolhido pelo usuario deve rodar com aquele modelo ou falhar em voz
  alta.
- Um artefato exigido pela pipeline deve existir no formato esperado ou a etapa
  deve falhar ali mesmo.
- Um documento com schema invalido nao pode virar sucesso para a etapa seguinte
  descobrir o problema depois.

Diferenças importantes:

| Comportamento | Permitido? | Regra |
|---|---:|---|
| Retry explicito no mesmo modelo | Sim, com cuidado | Pode tentar novamente o mesmo provider/modelo quando houver erro transiente, mas o resultado final precisa registrar a tentativa e falhar visivelmente se nao passar. |
| Trocar para outro modelo sem o usuario perceber | Nao | Se `gem3flash001` falhou, nao virar `gpt5nano001` automaticamente e chamar isso de sucesso. |
| Aceitar Markdown quando JSON era obrigatorio | Nao | O JSON obrigatorio deve parsear e validar schema. |
| Gerar PDF automatico quando a IA nao chamou a tool de PDF | Nao como sucesso | Pode ser ferramenta de diagnostico, mas deve virar alerta bloqueante ou etapa falha ate decidirmos outra coisa. |
| Preencher nota com `N/A` para evitar `{{nota_final}}` | Apenas contencao historica | O correto e falhar alto se a nota confiavel nao existe. |
| Env var como fonte alternativa de chave server-side | Sim, se explicito | Chave no cofre ou env server-side nao e fallback de modelo; e resolucao de segredo. Nao pode vazar valor. |

## Estado Real Resumido

Fatos oficiais observados em 2026-05-15:

- `origin/main` contem `ec95193` e registros documentais posteriores.
- `462ea1d` e apenas marcador de deploy; o hash funcional de custos/docs e
  `f67055c`.
- Render live saiu de `2e1098f` para `b12be9a` e depois confirmou marcadores
  `b4d7ee6`, `f505be6` e `97a7c79`.
- `/api/custos/status` no Render retornou HTTP 200, confirmando que o endpoint
  novo esta no backend live.
- Smokes live de chat em 2026-05-15: Gemini 3 Flash e GPT-5 Nano responderam
  JSON simples; Haiku falhou por credito Anthropic baixo.
- Smoke live de pipeline em 2026-05-15: Gemini 3 Flash em `pipeline-completo`
  com apenas `corrigir` falhou (`task_e22dbdbffe4d`) e `/api/task-progress`
  nao expos `error`. Depois do deploy `b4d7ee6`, a repeticao
  `task_08d4648d7053` falhou alto com `error`: Google API 503 `UNAVAILABLE`,
  alta demanda temporaria do modelo.
- `GET /api/health` no Render respondeu healthy/Supabase true, mas no codigo
  antigo, nao no hash esperado.
- GitHub Actions nao mostrou runs; GitHub API nao mostrou webhooks/deployments
  visiveis; Render MCP retornou workspace nao selecionado.
- Ha muito ruido em `backend/.pytest_tmp` e arquivos Rio/UI no worktree.
- Rio 3 continua pausado e fora do ciclo ativo.

O que foi feito localmente:

- P4: bloqueio de `EXTRAIR_RESPOSTAS` sem `prova_respondida` valida.
- P5/P6: contencao de `nota_final` e preservacao de `_documentos_faltantes`.
- Sprint 2: schema e `_avisos_*` alinhados em testes locais.
- Sprint 3: `input_tokens` e `output_tokens` separados em memoria no caminho de
  chat/tool-use.
- Sprint 3b: documentos de IA agora podem receber provider/modelo/prompt,
  tokens/tempo e metadata de custo; tool-use marca documentos com `cost_run_id`;
  `/api/custos/status` e `/api/custos/resumo` existem localmente; PDF obrigatorio
  ausente em dual-output falha alto em vez de ser inventado por fallback.
- Sprint 4a: falha de etapa agora deve popular `task.error`; frontend usa essa
  mensagem no toast e na arvore de tarefas. Commit funcional `b4d7ee6`, marker
  `99483d1`, publicados no GitHub e confirmados no Render; smoke repetido
  descobriu a causa real da falha Gemini: 503 Google por alta demanda.
- Sprint 4b: erros HTTP de tool-use agora usam `ProviderAPIError`, preservando
  `status_code` e `retryable` para 429/5xx. Isso permite retry no mesmo modelo,
  visivel e rastreavel, sem fallback de provider.
- Sprint 4c: se tools criarem documentos e uma chamada posterior do provider
  falhar, esses documentos parciais devem ser marcados `ERRO`, nao `concluido`
  com tokens zerados.
- Deploy final do bloco: Render confirmou `97a7c79`. Gemini 3 Flash em
  `corrigir` completou com custo medido; GPT-5 Nano em `corrigir` falhou alto
  sem fallback automatico.

Mapa dos commits publicados ou preparados:

| Commit | Escopo | Leitura correta |
|---|---|---|
| `7e4b852` | Consolida docs e painel de planejamento | Publicado no GitHub; precisa Render para ser produto. |
| `3b3291f` | P4: prova respondida valida antes de extrair respostas | Publicado no GitHub; precisa smoke oficial. |
| `a695db4` | P5/P6: nota e documentos faltantes | Contencao publicada; `N/A` ainda deve virar erro alto no ciclo P0. |
| `76c8467` | Sprint 2: schema e avisos | Publicado; matriz provider precisa revalidacao pos-fix. |
| `b12be9a` | Sprint 3: split de tokens | Publicado; Render nao confirmou. |
| `301eba6` | Marcador `novocr-deploy` para `b12be9a` | Publicado; Render continuou stale. |
| `f67055c` | Sprint 3b metadata/custos | Publicado no GitHub; `/api/custos/*` ja responde live. |
| `462ea1d` | Marcador `novocr-deploy` para `f67055c` | Publicado; HTML live ainda mostra `b12be9a`. |
| `b4d7ee6` | Sprint 4a erro visivel em task-progress | Publicado no GitHub e confirmado no Render; smoke repetido expôs Google 503. |
| `99483d1` | Marcador `novocr-deploy` para `b4d7ee6` | Publicado; `check_deploy.sh b4d7ee6` passou. |
| `d24623b` | Registro documental pos-deploy | Publicado no GitHub; nao altera marker funcional. |
| `f505be6` | Sprint 4b retryability em tool-use | Publicado e confirmado no Render; smoke Gemini passou depois. |
| `d75b05a` | Marcador `novocr-deploy` para `f505be6` | Publicado; `check_deploy.sh f505be6` passou. |
| `97a7c79` | Sprint 4c docs parciais em erro | Publicado e confirmado no Render. |
| `ec95193` | Marcador `novocr-deploy` para `97a7c79` | Publicado; `check_deploy.sh 97a7c79` passou. |
| `ff7b92a` | OpenAI tool-choice para dual-output/GPT-5 Nano + catalogo OpenAI atualizado | Publicado no GitHub; validado localmente; ainda nao confirmado no Render. |
| `68ebe51` | Marcador `novocr-deploy` para `ff7b92a` | Publicado; `check_deploy.sh ff7b92a` falhou porque o live ainda mostra `97a7c79`. |

Estado do worktree no momento desta auditoria:

- Ha alteracoes de outros agentes/rodadas em `backend/chat_service.py`,
  `backend/routes_chat.py`, `frontend/index_v2.html`, `render.yaml` e muitos
  artefatos `.pytest_tmp`.
- Ha arquivos Rio/scripts/assets untracked que nao pertencem a este ciclo.
- O ciclo atual esta sendo executado em worktree limpo para nao misturar ruido
  do workspace principal.

O que ainda falta:

- Acionar deploy oficial por hook rotacionado/manual seguro.
- Provar em producao que `ff7b92a` chegou ao site; no momento Render esta stale
  em `97a7c79`, apesar de `origin/main=68ebe51`.
- Confirmar custo real por etapa/aluno/atividade no site oficial.
- Popular metadata de documento (`tokens_usados`, `ia_modelo`, `ia_provider`) de
  forma confiavel.
- Revalidar providers depois dos fixes locais.
- Remover ou converter fallbacks silenciosos restantes em erro alto.
- Corrigir UI para explicar falhas por aluno/etapa.
- Reclassificar dados "fantasma" sem deletar PDF valido por `conteudo=null`.

## Mapa Geral Das Travas

Esta secao fica antes do mapa de documentos porque ela responde a pergunta
"onde o projeto esta travando?" sem obrigar leitura arquivo por arquivo.

| Trava | O que significa | Evidencia | Proximo movimento |
|---|---|---|---|
| Local diferente de oficial | O workspace tem fixes que `origin/main` e Render ainda nao provaram ter. | `main` local 5 commits a frente de `origin/main`. | Commit/push/deploy em ciclo proprio, com gate. |
| Fallbacks ainda misturados com robustez | Alguns docs/testes antigos tratam fallback como comportamento bom. | PDF auto-fallback, `nota_final=N/A`, parsing permissivo. | Ciclo anti-fallback antes de custo/dashboard. |
| Custo nao e persistido | Tokens existem em memoria/resposta, mas nao ha historico consultavel. | Doc 05 e codigo mostram `calculate_cost` sem chamada operacional. | `TokenUsageRecord` + metadata em documento. |
| Provider matrix esta stale | Matriz reflete testes antes dos fixes locais mais recentes. | Doc 12 e testes de abril; commits locais de maio nao revalidados. | Smoke por provider/rota depois de deploy. |
| UI nao explica falhas suficientes | Usuario pode ver status/documento sem entender falha real. | Riscos do Doc 09 e logs antigos de UI/deploy. | Sprint 4 com mensagens por aluno/etapa/provider. |
| Dados fantasmas ainda confundem status | JSON de erro e PDF com `/conteudo=null` podem ser interpretados errado. | Doc 07 + nota tecnica PDF + historico de fantasmas. | Reclassificacao segura antes de limpeza. |
| Rio 3 rouba foco se reabrir agora | Rio nao resolve custo/provider geral nem confiabilidade base. | Doc 13 e `rio3_pausado`. | Manter pausado ate decisao explicita. |

## Contrato Do Doc 02 Que Ainda Nao Estamos Seguindo

O Doc 02 e historico, mas nao e irrelevante. Ele descreveu a arquitetura real da
pipeline em abril e apontou tarefas que ainda nao foram fechadas de ponta a
ponta. A leitura correta agora e:

> o Doc 02 deixou de estar no caminho vivo, mas suas travas tecnicas continuam
> governando o sucesso do produto.

| Contrato do Doc 02 | Estado atual | O que falta fazer |
|---|---|---|
| Path 1 e Path 2 precisam gerar JSON validado e confiavel | Path 1 passa por `_parsear_resposta`; Path 2 ainda salva `content` via tool handler e so injeta defaults de avisos quando o JSON ja e valido. | Path 2 precisa parsear, validar schema e falhar a etapa original quando o JSON for invalido. |
| A LLM nao pode escolher entre dois schemas conflitantes | `pipeline_validation.py` ficou mais permissivo e aceita formatos legados/tool-use; `PROMPTS_PADRAO` de CORRIGIR/ANALISAR/GERAR ainda mantem schema legado sem `_avisos_*`. | Unificar o contrato de prompt/tool-use ou deixar o legado explicitamente fora do caminho ativo. |
| `_avisos_documento`, `_avisos_questao` e `_avisos_stage` precisam sobreviver | Sprint 2 injeta defaults e melhora visualizador, mas default vazio pode mascarar que o modelo nao produziu aviso esperado. | Diferenciar "modelo declarou sem avisos" de "sistema preencheu default porque faltou campo". |
| `executar_com_tools()` deve retornar metadados uteis | Token split foi corrigido localmente; `etapa` ainda volta como `"tools"` e `resposta_parsed`/`documento_id` continuam ausentes nesse retorno. | Retornar etapa real, documento principal e JSON parseado/validado no `ResultadoExecucao`. |
| Tokens do Path 2 precisam virar custo auditavel | `input_tokens`/`output_tokens` existem localmente em memoria. | Persistir `TokenUsageRecord`, custo por etapa/aluno/atividade e custo de falhas. |
| Provider sem tools nao pode cair em chat simples | `chat_service.py` agora falha explicitamente para provider sem tool-use. | Manter teste cobrindo esse contrato e revalidar providers no site oficial. |
| PDF/artefato faltante nao pode virar sucesso enganoso | `executar_com_tools()` ainda usa PDF auto-fallback e retorna `sucesso=True`. | Converter PDF auto-fallback em erro alto ou sucesso parcial bloqueante com UI vermelha. |
| Modelos pequenos que geram lixo precisam falhar cedo | GPT-5 Nano historicamente gerou documentos ruins; alguns testes locais cobrem partes. | Schema invalido deve falhar em CORRIGIR, antes de ANALISAR/GERAR descobrir o estrago. |

Conclusao operacional: dizer "Sprint 2 concluida" so e aceitavel como
**melhoria local de schema/avisos**, nao como "Doc 02 cumprido". O proximo ciclo
anti-fallback deve ser tratado tambem como ciclo de cumprimento do Doc 02.

## O Que O Plano Longo Ainda Nao Diz Bem

O plano longo melhorou, mas ainda deixa algumas perguntas grandes mal
respondidas. Estas lacunas devem virar ajustes no Doc 09 depois que este Doc 14
for revisado.

### 1. "Concluido localmente" precisa aparecer como categoria fraca

Quando o Doc 09 diz que uma sprint esta concluida localmente, isso nao deve ser
lido como "site oficial pronto". Falta uma taxonomia simples:

| Status sugerido | Significado |
|---|---|
| Planejado | Existe tese, mas nao ha codigo/doc alterado. |
| Implementado localmente | O workspace tem mudanca e teste local. |
| Commitado localmente | Existe commit local, mas nao foi para `origin/main`. |
| Publicado no GitHub | `origin/main` aponta para o commit esperado. |
| Deploy confirmado | Render/site oficial esta no commit esperado. |
| Smoke validado | Endpoint/fluxo real provou o comportamento em producao. |

Sem essa taxonomia, "feito" vira uma palavra escorregadia.

### 2. Sprint 1/P5 foi renomeada nesta auditoria

O Doc 09 falava em "fallback robusto de `nota_final`". Pela regra P0, o nome
correto nao era esse. Nesta rodada, o painel vivo foi ajustado para chamar P5 de
contencao temporaria e debito P0. A leitura nova deve continuar sendo:

- **Antes:** fallback de nota para evitar template literal.
- **Agora:** contencao temporaria para impedir `{{nota_final}}`, mas proximo
  ciclo deve transformar ausencia de nota confiavel em erro explicito.

Nome sugerido:

> P5: bloquear relatorio sem nota confiavel; remover contencao `N/A`.

### 3. Sprint 3 precisa dizer "medicao", nao "custo"

O split `input_tokens`/`output_tokens` e importante, mas ainda nao responde:

- Quanto custou a atividade?
- Quanto custou por aluno?
- Quanto custou por provider?
- Qual etapa foi mais cara?
- Quanto custou uma falha?

Nome sugerido:

> Sprint 3a: medicao de tokens em memoria.

E depois:

> Sprint 3b: persistencia e precificacao de custo real.

### 4. Provider precisa ser revalidado por rota

O Doc 12 ja tenta fazer isso, mas a leitura geral ainda pode induzir erro. O
estado de um provider deve ser sempre:

`modelo + rota + etapa + commit + ambiente + schema + metadata + custo`

Exemplo:

- Gemini 3 Flash no chat: OK historico.
- Gemini 3 Flash no pipeline-completo downstream: positivo parcial.
- Gemini 3 Flash com custo real persistido: nao testado.
- GPT-5 Nano em `/executar/etapa`: parcial historico.
- GPT-5 Nano em `pipeline-completo`: falha grave.

### 5. UI de erro deve virar criterio de aceite, nao fase cosmetica

Hoje a UI aparece como Sprint 4, mas ela e parte da confiabilidade. Se o backend
falha alto e a UI traduz mal, o usuario ainda perde.

Aceite minimo para UI:

- Mostrar aluno afetado.
- Mostrar etapa afetada.
- Mostrar modelo/provider solicitado.
- Mostrar causa: credito, documento, schema, tools, provider, deploy/storage.
- Mostrar se o documento salvo e real, parcial ou erro.
- Nunca esconder fallback proibido em toast verde.

### 6. O custo de falhas tambem precisa ser registrado

Um erro de provider pode gastar tokens antes de falhar. Um retry explicito tambem
custa. Se o custo so registra sucesso, o sistema subestima gasto e nao ajuda a
decidir provider.

Campos minimos:

- `sucesso`
- `erro_tipo`
- `erro_mensagem_segura`
- `tentativas`
- `tokens_entrada`
- `tokens_saida`
- `custo_total_usd`
- `provider`
- `modelo`
- `etapa`
- `atividade_id`
- `aluno_id`

## Perguntas Que O Proximo Ciclo Deve Responder

Estas perguntas nao precisam parar a auditoria, mas devem orientar a proxima
rodada de trabalho.

| Pergunta | Por que importa | Como responder |
|---|---|---|
| Quais fallbacks ainda existem no codigo de pipeline? | Define P0 real, nao so retorico. | `rg fallback`, leitura de executor/chat/tools, testes focados. |
| Qual fallback pode continuar? | Nem todo fallback e ruim; env server-side e display visual podem ser aceitaveis. | Classificar permitido/proibido/permitido com alerta. |
| O PDF auto-fallback deve virar erro ou sucesso parcial? | Decide comportamento e testes. | Decisao de produto + teste de `executar_com_tools`. |
| `nota_final=N/A` deve bloquear em qual ponto? | Evita relatorio enganoso. | Teste de `GERAR_RELATORIO` sem nota confiavel. |
| Onde tokens se perdem antes de persistir? | Necessario para custo real. | Teste de `_salvar_resultado` e `storage.salvar_documento`. |
| Render esta em qual commit? | Sem isso nao ha progresso oficial. | `check_deploy`/health depois de push/deploy autorizado. |
| Quais providers passam pos-fix? | Matriz atual esta stale. | Smokes por rota/etapa, sem fallback de modelo. |

## Inventario Inicial De Fallbacks A Auditar

Este inventario nao substitui uma auditoria de codigo completa, mas ja mostra
onde o proximo ciclo deve olhar primeiro. A palavra fallback aparece em varias
classes diferentes; algumas sao aceitaveis, outras sao P0.

### Fallbacks provavelmente aceitaveis

| Area | Evidencia | Por que pode ser aceitavel |
|---|---|---|
| Env vars para API key server-side | `backend/executor.py:2403-2414`, `backend/chat_service.py:1934`, `backend/tests/unit/test_api_keys.py:128-190` | Resolver segredo via env do Render nao troca modelo nem mascara output; e caminho operacional de producao. |
| Mimetype do Python | `backend/routes_chat.py:175` | Fallback tecnico de content-type, baixo risco de produto. |
| Display name/visual local | testes frontend de display name | Pode evitar UI quebrada, desde que nao esconda falha de pipeline. |
| Logging basico | `backend/executor.py:44` | Nao afeta artefato final. |
| Pasta generica de chat output | `backend/chat_service.py:2108-2117` | Precisa confirmar, mas parece storage tecnico, nao provider/model fallback. |

### Fallbacks P0 ou suspeitos

| Area | Evidencia | Por que e perigoso |
|---|---|---|
| `nota_final=N/A` | `backend/executor.py:1755-1757`, `backend/tests/unit/test_erro_pipeline.py:655-657` | Pode gerar relatorio sem nota confiavel e parecer resultado final. |
| Markdown aceito como relatorio valido | `backend/executor.py:2012-2025` | Pode aceitar formato errado quando JSON/schema era obrigatorio. |
| Regex para extrair JSON | `backend/executor.py:1964-2008` | Pode capturar trecho errado e transformar resposta ruim em estrutura aparentemente valida. |
| PDF auto-fallback | `backend/executor.py:2580-2677` | Modelo nao produziu PDF esperado, mas sistema cria PDF e retorna `sucesso=True`. |
| Gabarito original se extracao falta | `backend/executor.py:1736` | Pode mascarar pipeline incompleta se nao for explicito. |
| Teste de PDF fallback esperando sucesso | `backend/tests/unit/test_f7_t1_pdf_auto_fallback.py:226-238` | Codifica comportamento agora considerado errado pelo P0. |
| Teste E-T2 aceita parcial como sucesso | `backend/tests/unit/test_e_t2_retry_partial_output.py` | Precisa reclassificar sucesso parcial vs erro bloqueante. |

### Fallbacks ja corrigidos ou parcialmente protegidos

| Area | Evidencia | Estado |
|---|---|---|
| Provider sem tools cair em chat simples | `backend/chat_service.py:914-923` | Agora ha erro explicito no `chat_with_tools`. |
| Modelo nao registrado no pipeline tool-use | `backend/executor.py:2394` | Mensagem diz que nenhum fallback sera usado; precisa manter teste. |
| Non-tool model com tools | `backend/tests/unit/test_e_t1_tool_capability_gate.py:189-210` | Teste explicita `sucesso=False`; manter como gate. |

Regra para o ciclo anti-fallback:

- Nao remover fallback tecnico sem entender impacto.
- Nao manter fallback de produto sem UI/erro alto.
- Todo fallback mantido precisa ter nome, teste e justificativa.
- Todo fallback proibido precisa virar falha no ponto original.

## Cobertura Total De `docs/`

Leitura de cobertura feita nesta auditoria:

- `docs/plano_pipeline`: 21 arquivos de plano, historico, nota e Rio pausado.
- `docs/logs`: 4 arquivos de logs de bug antigos.
- `docs/prompts/sessao_5caa6b6b.md`: log bruto de prompts da sessao tutorial.
- `docs/tutorial_arquivado_v1.html`: snapshot do tutorial antigo.
- `docs/tutorial_arquivado_v1_assets`: 14 imagens do tutorial antigo.
- `docs/audit_quotes_vs_implementation.md`, `docs/skill_audit_loop.md`,
  `docs/workflow_analysis.md`, `docs/plano_geral_novo_tutorial.md`: meta-docs
  que explicam o loop e a filosofia do produto.

Classificacao de autoridade:

| Fonte | Autoridade para pipeline/custos atual? | Como usar |
|---|---:|---|
| Doc 09 | Alta | Painel curto e fila operacional. |
| Doc 05 | Alta, stale em partes | Roadmap de custos; atualizar onde token split ja foi feito. |
| Doc 12 | Media/alta, stale | Evidencia de provider ate revalidar pos-fixes. |
| Docs 01-03 | Alta como diagnostico historico | Origem dos bugs e criterios de teste. |
| Doc 04 | Alta como inventario | Fonte de schemas, modelos, catalogo e seguranca. |
| Doc 11 + prompt log | Alta para processo | Regras de loop, quotes do usuario e cuidados com segredo. |
| Docs logs jan/2026 | Media como memoria tecnica | Lessons learned; nao guiam diretamente a Sprint atual. |
| Tutorial arquivado/assets | Baixa para pipeline | Referencia de produto/UX, nao fonte tecnica de execucao. |

Legenda de status usada neste documento:

| Status | Significado |
|---|---|
| Vivo | Ainda deve orientar o trabalho atual. |
| Vivo/stale | Continua importante, mas contem fatos que precisam ser atualizados contra codigo/teste atual. |
| Historico fundamental | Nao e fila ativa, mas explica a causa dos bugs e decisoes. |
| Evidencia de teste | Prova um comportamento observado em uma data/commit; nao deve ser extrapolado sem revalidacao. |
| Pausado | Guardado para futuro; nao deve guiar o ciclo ativo. |
| Meta | Ensina o processo de trabalho, nao a regra tecnica da pipeline. |
| Log bruto sensivel | Pode conter quotes uteis e tambem segredo; precisa ser lido com filtro de seguranca. |

Regra de seguranca sobre o prompt log: ele e fonte historica bruta, mas nao deve
ser republicado cegamente. Ele contem material sensivel ja sanitizado no Doc 11.
Qualquer deploy hook, token, chave ou URL com segredo que apareca em log bruto
deve ser tratado como exposto e rotacionado, nunca copiado para docs novos.

## Indice De Quotes Obrigatorias

Esta tabela existe para a auditoria nao depender de memoria. As linhas sao as
linhas observadas nos documentos originais no momento desta revisao.

| Quote curta | Fonte |
|---|---|
| "A pipeline de correcao do NOVO CR processa provas/atividades em 6 etapas sequenciais" | `01_historico_problemas_pipeline.md:13` |
| "Parsing de JSON com fallbacks frageis" | `01_historico_problemas_pipeline.md:166` |
| "O fallback #4 aceita Markdown como resposta valida para relatorios" | `01_historico_problemas_pipeline.md:175` |
| "PDF fallback automatico" | `01_historico_problemas_pipeline.md:177` |
| "O pipeline possui **6 etapas por aluno** divididas em dois grupos" | `02_contexto_decisoes_arquiteturais.md:9` |
| "A LLM pode seguir qualquer um dos dois schemas" | `02_contexto_decisoes_arquiteturais.md:161` |
| "Tokens nao sao rastreados no Path 2" | `02_contexto_decisoes_arquiteturais.md:370` |
| "Risco de falha silenciosa por provider" | `03_plano_operacional_debug.md:19` |
| "Endpoint de custos retorna valores nao-zero" | `03_plano_operacional_debug.md:206` |
| "Catalogo exaustivo de todas as fontes de dados" | `04_fontes_dados_governanca.md:3` |
| "Catalogo datado de 2026-01-28" | `04_fontes_dados_governanca.md:631` |
| "O que NUNCA Expor" | `04_fontes_dados_governanca.md:820` |
| "Nenhum registro persistente de custos" | `05_visao_longo_prazo.md:48` |
| "Precificacao nao e aplicada automaticamente" | `05_visao_longo_prazo.md:52` |
| "rode com confiabilidade em multiplos modelos" | `09_progresso_longo_prazo.md:32` |
| "registre tokens e custos por materia/atividade/aluno" | `09_progresso_longo_prazo.md:34` |
| "Metadata de tokens/modelo ainda falha" | `09_progresso_longo_prazo.md:229` |
| "RELER o plano mestre no início de cada iteração" | `11_decisoes_otavio.md:301` |
| "QUOTES EXATAS" | `11_decisoes_otavio.md:302` |
| "Velocidade alta é sinal de que pulou etapas" | `11_decisoes_otavio.md:303` |
| "Gemini 3 Flash via `pipeline-completo`: VALIDADO" | `12_matriz_provider_fase.md:152` |
| "GPT-5 Nano via `pipeline-completo`: QUEBRADO" | `12_matriz_provider_fase.md:153` |
| "conteudo: null ... nao prova que o documento esta vazio" | `nota_tecnica_conteudo_pdf.md:10-12` |
| "Tentativa 1 falhou sem diagnóstico acessível via API" | `teste_gemini_pipeline_completo.md:98` |
| "Status final: FALHA" | `teste_gpt5nano_pipeline_completo.md:13` |
| "Creditos Anthropic insuficientes" | `12_matriz_provider_fase.md:60` |
| "Two models were marked as `is_default: true`" | `docs/logs/2026-01-30_default_model_bug.md:11` |
| "Always test the LIVE endpoint, not just local" | `docs/logs/2026-01-30_chat_documents_not_loading.md:148` |
| "isso tá rápido demais pra vcc ter feito tudo" | `docs/prompts/sessao_5caa6b6b.md:218` |
| "Your loop lacked in a lot of details" | `docs/prompts/sessao_5caa6b6b.md:230` |
| "create a new .md with exact quotes" | `docs/prompts/sessao_5caa6b6b.md:232` |
| "não tenha a capacidade de modificar o plano" | `docs/prompts/sessao_5caa6b6b.md:256` |
| "Create institutional memory for debugging" | `docs/logs/README.md:7` |
| "NÃO é exposto ao usuário final" | `docs/tutorial_arquivado_v1.html:99` |
| "O NOVO CR não é só um corretor automático" | `docs/tutorial_arquivado_v1.html:121` |

## Mapa Dos Documentos

| Documento | Status | Papel |
|---|---|---|
| `04_fontes_dados_governanca.md` | Vivo, mas precisa atualizar catalogo | Fonte de dados, schemas, modelos, precos e seguranca. |
| `05_visao_longo_prazo.md` | Vivo/stale em partes | Estrategia de custos, providers e otimizacao. |
| `09_progresso_longo_prazo.md` | Vivo curto | Painel operacional resumido. |
| `11_decisoes_otavio.md` | Vivo/meta | Regras de trabalho, quotes do Otavio e erros que Paulo nao pode repetir. |
| `12_matriz_provider_fase.md` | Vivo, mas stale pos-fixes | Matriz de evidencias por provider/fase. |
| `13_plano_curto_paulo_rio3_render.md` | Pausado | Plano Rio 3, preservado mas fora do loop atual. |
| `arquivo_2026_04_17/01_historico_problemas_pipeline.md` | Historico fundamental | Origem dos problemas da pipeline e dos fallbacks. |
| `arquivo_2026_04_17/02_contexto_decisoes_arquiteturais.md` | Historico fundamental | Explica Path 1 multimodal e Path 2 tool-use. |
| `arquivo_2026_04_17/03_plano_operacional_debug.md` | Historico/fila original | Prioridades P1-P7 e testes esperados. |
| `arquivo_2026_04_17/06_fluxo_orquestracao_case_tracking.md` | Historico/meta | Protocolo de orquestracao e cases. |
| `arquivo_2026_04_17/07_relatorio_auditoria_lista0.md` | Evidencia historica/stale | Auditoria de 402 documentos, com correcao importante sobre PDFs. |
| `arquivo_2026_04_17/10_triagem_testes_preexistentes.md` | Historico | Classificacao de falhas antigas de teste. |
| `arquivo_2026_04_17/investigacao_fantasmas_templates.md` | Evidencia causal | Causa raiz de alunos fantasma e `{{nota_final}}`. |
| `arquivo_2026_04_17/resumo_sessao_2026_04_17.md` | Historico de rodada | Resumo de sucesso, fracasso e agentes. |
| `arquivo_2026_04_17/teste_chat_gemini.md` | Evidencia de teste | Chat Gemini 3 Flash funcionou com ressalva de prompt errado. |
| `arquivo_2026_04_17/teste_executar_etapa_corrigido.md` | Evidencia de teste | `/executar/etapa` passou em um cenario e falhou corretamente em outro. |
| `arquivo_2026_04_17/teste_gemini_pipeline_completo.md` | Evidencia de teste | Gemini 3 Flash passou pipeline downstream na segunda tentativa. |
| `arquivo_2026_04_17/teste_gpt5nano_pipeline_completo.md` | Evidencia de falha | GPT-5 Nano quebrou pipeline-completo com documentos lixo. |
| `arquivo_2026_04_17/teste_haiku_eric.md` | Evidencia de bloqueio | Haiku bloqueado por creditos Anthropic; GPT-4o usado como referencia anterior. |
| `notas/nota_tecnica_conteudo_pdf.md` | Nota tecnica viva | `conteudo=null` nao invalida PDF. |
| `rio3_pausado/rio3_provider_research.md` | Pausado | Pesquisa Rio 3 congelada. |
| `docs/workflow_analysis.md` | Meta vivo | Como o loop deveria funcionar com fonte de verdade. |
| `docs/skill_audit_loop.md` | Meta vivo | Padrao de auditoria com quotes e tabela de gaps. |
| `docs/audit_quotes_vs_implementation.md` | Meta historico | Exemplo de audit doc que funcionou no tutorial. |
| `docs/plano_geral_novo_tutorial.md` | Plano tutorial | Relevante para filosofia do produto e problemas de UX, nao para executar pipeline agora. |
| `docs/prompts/sessao_5caa6b6b.md` | Log bruto sensivel | Fonte de quotes do usuario; nao republicar segredos. |
| `docs/logs/*.md` | Memoria tecnica antiga | Bugs ja resolvidos que ensinam padroes de verificacao. |
| `docs/tutorial_arquivado_v1.html` | Arquivo de referencia | Tutorial antigo, nao exposto ao usuario final. |
| `docs/tutorial_arquivado_v1_assets/*.png` | Assets historicos | Imagens do tutorial antigo; nao guiam pipeline atual. |

## Docs Vivos

### Doc 04 -- Fontes de Dados e Governanca

**Arquivo:** `docs/plano_pipeline/04_fontes_dados_governanca.md`
**Status:** vivo, mas com catalogo/modelos possivelmente stale.
**Serve para:** explicar banco, storage, schemas, modelos configurados, catalogo,
precos, capabilities, chaves e governanca.

Quotes relevantes:

> "Catalogo exaustivo de todas as fontes de dados, schemas, configuracoes de modelos e regras de governanca do NOVO CR."

> "Catalogo datado de 2026-01-28"

> "O que NUNCA Expor"

> "Valores reais de API keys"

O que prova:

- Existe um modelo de dados para documentos com `ia_provider`, `ia_modelo`,
  `tokens_usados` e `tempo_processamento_ms`.
- Existe catalogo de modelos com precos por 1M tokens.
- Existe lista de inconsistencias entre `models.json`, `model_catalog.json` e
  `chat_service.py`.
- A seguranca de chaves ja estava documentada: API keys nao devem aparecer em
  docs, logs ou chat.

O que ficou desatualizado:

- A tabela de modelos ativos e capabilities precisa ser revalidada contra o
  estado atual de `models.json`.
- Sonnet e Flash Lite tiveram fixes historicos, mas o doc ainda e uma fotografia.
- Precos do catalogo sao de janeiro de 2026; estamos usando o doc como referencia
  interna, nao como verdade financeira atual.

Como orientar o proximo loop:

- Antes de qualquer dashboard de custo, atualizar a fonte de precos ou marcar que
  custos sao estimativas.
- Antes de testar provider, validar `supports_tools`, `vision`, `reasoning` e
  `catalog_ref`.
- Nunca registrar segredo real; qualquer chave em chat e tratada como exposta.

### Doc 05 -- Visao de Longo Prazo

**Arquivo:** `docs/plano_pipeline/05_visao_longo_prazo.md`
**Status:** vivo, mas stale em partes porque token split ja foi feito localmente.
**Serve para:** roadmap de custos, providers e otimizacoes.

Quotes relevantes:

> "Nenhum registro persistente de custos."

> "Precificacao nao e aplicada automaticamente."

> "Dados do `model_catalog.json` (versao 2026.01, atualizado 2026-01-28)."

> "Custo estimado"

O que prova:

- O objetivo de custo e explicito: consultar custo por materia, turma, atividade,
  provider, modelo e periodo.
- A arquitetura proposta e `TokenUsageRecord`, inicialmente em JSON mensal.
- O catalogo consegue calcular custo, mas a pipeline ainda nao chama isso como
  registro operacional.
- As estimativas existem, mas nao substituem medicao real.

Estado atualizado pela leitura:

- O gap "ChatClient retorna apenas tokens total" foi corrigido localmente em
  `b12be9a`.
- O gap "executar_com_tools nao popula tokens_saida" foi corrigido localmente em
  `b12be9a`.
- Ainda falta persistencia de custo.
- Ainda falta aplicar precificacao automaticamente por etapa.
- Ainda falta capturar cached tokens.
- Ainda falta garantir metadata em documento salvo.

Estimativas documentadas no Doc 05:

| Cenario | Modelo pipeline | Estimativa |
|---|---|---:|
| Ultra-economico | GPT-5 Nano em todas etapas | ~$0.04 |
| Economico | Gemini Flash + Gemini 3 Flash | ~$0.12 |
| Equilibrado | Haiku + Sonnet + Haiku | ~$0.55 |
| Premium | GPT-5 em todas etapas | ~$1.05 |

Leitura correta:

- Esses valores sao estimativas pedagogicas de planejamento.
- Eles nao sao custo medido do sistema.
- A proxima auditoria de custo deve produzir numero real por etapa e provider.

Como orientar o proximo loop:

- Implementar registro real de `TokenUsageRecord`.
- Registrar provider/modelo/tokens/tempo/sucesso por etapa.
- So depois construir endpoint/dashboard de custo.

### Doc 09 -- Painel Vivo Paulo

**Arquivo:** `docs/plano_pipeline/09_progresso_longo_prazo.md`
**Status:** vivo curto, mas insuficiente como auditoria detalhada.
**Serve para:** dizer rapidamente onde estamos e qual e a fila.

Quotes relevantes:

> "rode com confiabilidade em multiplos modelos"

> "registre tokens e custos por materia/atividade/aluno"

> "Metadata de tokens/modelo ainda falha ou fica incompleta em caminhos testados."

> "UI ainda nao comunica falhas da pipeline com clareza suficiente."

O que prova:

- O objetivo atual nao e Rio; e pipeline confiavel, custos e erros legiveis.
- As sprints 0 a 3 foram registradas como concluidas localmente.
- O proprio painel admite riscos que ainda impedem chamar o projeto de resolvido.

O que ficou ruim:

- O painel diz "Sprint 3 concluida localmente no nivel de medicao", mas nao deixa
  claro para usuario qual parte ainda nao e custo real.
- A matriz de provider nao esta incorporada no painel.
- O estado de deploy/GitHub nao esta destacado o suficiente para quem quer saber
  se o site oficial recebeu os fixes.
- Antes desta auditoria, o Doc 09 ainda usava a expressao "fallback robusto de
  `nota_final`" e registrava `N/A` como comportamento concluido. Nesta rodada,
  isso foi reclassificado no Doc 09 como contencao temporaria e debito P0:
  sem nota confiavel, o relatorio deve falhar alto.

Como orientar o proximo loop:

- Manter o Doc 09 curto.
- Acrescentar ao Doc 09 apenas resumo do novo Doc 14, nao colar a auditoria inteira.
- Registrar proximos ciclos como: remover fallbacks, custo persistido, provider
  revalidation, UI de erro.

### Doc 11 -- Decisoes e Correcoes do Otavio

**Arquivo:** `docs/plano_pipeline/11_decisoes_otavio.md`
**Status:** vivo/meta; nasceu do tutorial, mas as regras de loop valem aqui.
**Serve para:** evitar que Paulo repita erros de processo.

Quotes relevantes:

> "RELER o plano mestre no início de cada iteração"

> "QUOTES EXATAS"

> "Velocidade alta é sinal de que pulou etapas"

> "Antes de analisar/propor, RELER plano mestre + último plano curto prazo."

O que prova:

- O usuario ja decidiu que a documentacao precisa citar e comparar contra fonte
  original.
- O loop nao pode ser baseado em memoria.
- Paulo deve falar o que foi feito e o que falta, nao criar conclusoes soltas.
- Deploy, segredo e mudancas de produto exigem gates claros.

O que ficou desatualizado:

- O doc fala bastante do projeto de tutorial. Isso nao invalida as regras de loop,
  mas nao deve confundir o escopo atual.

Como orientar o proximo loop:

- Para pipeline/custos, aplicar o mesmo metodo: quote -> fato atual -> gap ->
  teste -> status.
- Atualizar docs durante o loop, nao depois de perder contexto.

### Doc 12 -- Matriz Provider x Fase

**Arquivo:** `docs/plano_pipeline/12_matriz_provider_fase.md`
**Status:** vivo, mas stale em relacao aos commits locais posteriores.
**Serve para:** registrar evidencias por provider, fase e endpoint.

Quotes relevantes:

> "Gemini 3 Flash via `pipeline-completo`: VALIDADO end-to-end"

> "GPT-5 Nano via `pipeline-completo`: QUEBRADO"

> "Metadata `tokens_usados`, `ia_modelo`, `ia_provider` nao sao populados no DB"

> "50% de falha na primeira tentativa"

O que prova:

- Gemini 3 Flash tem a melhor evidencia de pipeline downstream.
- GPT-5 Nano nao pode ser tratado como pipeline-ready.
- Haiku ficou bloqueado por creditos Anthropic.
- GPT-4o foi referencia parcial, nao confirmacao pos-fixes.
- Metadata de custo/modelo era bug transversal nos testes.

O que ficou desatualizado:

- A matriz e de 2026-04-28 e nao reflete completamente os fixes locais de maio.
- Ela diz que Gemini foi validado "com todos os fixes", mas os commits locais
  posteriores ainda nao foram revalidados em producao.
- O estado de extraction para varios providers ainda esta "nao testado".

Como orientar o proximo loop:

- Atualizar a matriz apenas depois de smoke real por provider.
- Usar categorias mais duras: confirmado, parcial, falhou, bloqueado, nao testado
  pos-fix.
- Nao promover provider com schema invalido ou metadata ausente.

### Doc 13 -- Plano Curto Paulo Rio 3

**Arquivo:** `docs/plano_pipeline/13_plano_curto_paulo_rio3_render.md`
**Status:** pausado.
**Serve para:** guardar a frente Rio sem misturar com saneamento da pipeline.

Quotes relevantes:

> "PAUSADO em 2026-04-28 por decisao do usuario"

> "Paulo nao deve pedir chave, rodar smoke, acionar deploy Rio ou convocar agentes Rio"

> "Nunca registrar segredo, token, URL de deploy hook, header de autorizacao ou preview de chave."

O que prova:

- Rio 3 nao e o objetivo ativo deste ciclo.
- Qualquer chave Rio colada em chat e exposta.
- O fluxo correto, quando retomar, e Render/env server-side, nao popup publico.

O que ficou desatualizado:

- O usuario agora quer custos e pipelines dos providers gerais; Rio deve continuar
  congelado.

Como orientar o proximo loop:

- Ignorar arquivos Rio em stage/commit.
- Nao usar chave Rio.
- Nao deixar Rio distrair da auditoria de custos/providers existentes.

## Historicos Fundamentais

### Doc 01 -- Historico de Problemas da Pipeline

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/01_historico_problemas_pipeline.md`
**Status:** historico fundamental.
**Serve para:** explicar a origem dos bugs: pipeline, endpoints, erros, cascata,
parsing e fallbacks.

Quotes obrigatorias:

> "A pipeline de correcao do NOVO CR processa provas/atividades em 6 etapas sequenciais"

> "Parsing de JSON com fallbacks frageis"

> "O fallback #4 aceita Markdown como resposta valida para relatorios, o que pode mascarar falhas"

> "PDF fallback automatico"

O que prova:

- A pipeline tem 6 etapas: extrair questoes, extrair gabarito, extrair respostas,
  corrigir, analisar habilidades, gerar relatorio.
- Ha endpoints duplicados com contratos diferentes.
- Falhas em uma etapa criavam cascata e documentos "fantasma".
- O sistema ja aceitava estrategias de parse permissivas demais.
- O PDF fallback foi visto como "rede de seguranca", mas hoje deve ser rebaixado
  para risco de mascaramento.

O que ficou desatualizado:

- Alguns bugs de P4/P5/P6 ja foram corrigidos localmente.
- A classificacao positiva de fallback/PDF precisa ser reinterpretada pelo P0:
  fallback silencioso nao e robustez.

Como orientar o proximo loop:

- Remover parsing permissivo que aceita formato errado.
- Criar erro alto quando JSON obrigatorio nao valida.
- Consolidar endpoints ou ao menos alinhar tratamento de erro.

### Doc 02 -- Contexto e Decisoes Arquiteturais

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/02_contexto_decisoes_arquiteturais.md`
**Status:** historico fundamental.
**Serve para:** explicar os dois caminhos tecnicos da pipeline.

Quotes obrigatorias:

> "O pipeline possui **6 etapas por aluno** divididas em dois grupos"

> "A LLM pode seguir qualquer um dos dois schemas"

> "Tokens nao sao rastreados no Path 2"

> "Tools ignorados silenciosamente"

O que prova:

- Path 1 multimodal salva dict parseado por `_salvar_resultado`.
- Path 2 tool-use salva via `create_document`, com conteudo opaco.
- O bug de schema nasceu da dupla instrucao: `PROMPTS_PADRAO` vs
  `STAGE_TOOL_INSTRUCTIONS`.
- O bug de custo nasceu porque Path 2 nao tinha token split.
- Providers sem tool-use podiam cair em chat sem tools, o que e exatamente o tipo
  de fallback proibido.

O que ficou desatualizado:

- Token split no Path 2 foi corrigido localmente.
- O provider fallback silencioso foi parcialmente corrigido em `44c5786`.
- Ainda ha riscos de PDF auto-fallback, metadata e schema invalido.

Como orientar o proximo loop:

- Garantir que Path 2 parseie/valide schema antes de marcar sucesso.
- Garantir que tool calls gerem exatamente o documento esperado.
- Nenhum provider sem tools pode passar por etapa que exige `create_document`.

### Doc 03 -- Plano Operacional de Debug

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/03_plano_operacional_debug.md`
**Status:** historico/fila original.
**Serve para:** organizar os problemas em eixos e prioridades P1-P7.

Quotes relevantes:

> "Risco de falha silenciosa por provider"

> "Endpoint de custos retorna valores nao-zero"

> "P7 (Custos) so apos P4"

> "Nenhum documento fantasma criado"

O que prova:

- O plano original ja via custos como prioridade dependente de token split.
- O teste final desejado sempre foi E2E por provider.
- O criterio de custo nao era "tem estimativa"; era endpoint retornando valor
  nao-zero apos execucao.

O que ficou desatualizado:

- P1-P3, P4-P6 e parte de P7 foram movidos por commits locais.
- A ordem agora precisa incluir P0 anti-fallback antes de persistencia bonita de
  custos, porque custo em cima de output falso e pior que ausencia de custo.

Como orientar o proximo loop:

- Reabrir P7 como "custos reais" e nao "tokens em memoria".
- Criar teste E2E que confirma token/custo por etapa depois de pipeline real.
- Validar erro alto quando provider nao suporta etapa.

### Doc 06 -- Fluxo de Orquestracao e Case Tracking

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/06_fluxo_orquestracao_case_tracking.md`
**Status:** historico/meta.
**Serve para:** mostrar como Paulo deveria coordenar agentes/cases.

Quotes relevantes:

> "Agentes produzem findings, nao conclusoes"

> "Toda ambiguidade vira pergunta para o humano"

> "case_id = `{aluno_id}_{etapa}_{provider}`"

O que prova:

- O projeto precisava de rastreabilidade por caso.
- Provider, aluno e etapa precisam aparecer juntos para diagnostico.
- Conclusao sem evidencia e erro de orquestracao.

O que ficou desatualizado:

- A proposta de varios CSVs pode ser burocratica demais para o desejo atual de
  menos documentos.

Como orientar o proximo loop:

- Usar o conceito de case_id dentro do Doc 09 ou em logs estruturados, nao criar
  muitos docs novos.
- Relatorios de provider devem dizer aluno/atividade/etapa/modelo/commit.

### Doc 07 -- Relatorio de Auditoria Lista0

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/07_relatorio_auditoria_lista0.md`
**Status:** evidencia historica, stale na classificacao inicial.
**Serve para:** mostrar os dados reais da atividade Lista0.

Quotes relevantes:

> "Total documentos: 402"

> "`conteudo=null` em `/api/documentos/{id}/conteudo` foi tratado como fantasma."

> "nao devem ser tratados como candidatos automaticos a delecao"

> "Template nao preenchido"

O que prova:

- Havia documentos duplicados, relatorios ruins e alunos com pipeline incompleta.
- A auditoria inicial errou ao tratar PDF como fantasma por `conteudo=null`.
- Existem 10 alunos com prova sem correcao; 7 prontos para corrigir e 3 precisando
  extrair respostas.

O que ficou desatualizado:

- O numero "183 fantasmas" nao pode ser usado como ordem de delecao.
- `prova_respondida` PDF precisa ser verificado por arquivo/download/view.

Como orientar o proximo loop:

- Sprint de limpeza deve reclassificar antes de deletar.
- Nao repetir o erro de chamar `conteudo=null` de vazio quando o arquivo e PDF.

### Doc 10 -- Triagem Dos Testes Preexistentes

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/10_triagem_testes_preexistentes.md`
**Status:** historico.
**Serve para:** explicar que a suite antiga tinha muitas falhas nao criticas para
aquele marco.

Quotes relevantes:

> "0 criticos para Marco 1"

> "Testes async falham por falta de API key"

O que prova:

- A suite geral nao era um gate confiavel naquele momento.
- Testes focados por problema eram a estrategia correta.

O que ficou desatualizado:

- Depois dos commits locais, a classificacao precisa ser refeita se formos usar a
  suite ampla como gate.

Como orientar o proximo loop:

- Para cada ciclo, rodar teste focado + `py_compile` + `git diff --check`.
- Nao chamar "suite falhando" de bloqueio sem triagem atual.

### Investigacao -- Fantasmas e Templates

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/investigacao_fantasmas_templates.md`
**Status:** evidencia causal.
**Serve para:** explicar dois bugs que pareciam absurdos.

Quotes relevantes:

> "Nenhum dos tres possui documento `prova_respondida`."

> "A IA recebe um prompt pedindo para extrair respostas de... nada."

> "Agravante: `gerar_relatorio()` Descarta Faltantes Silenciosamente"

> "Se encontrar, marcar como erro."

O que prova:

- `EXTRAIR_RESPOSTAS` sem prova valida era bug real.
- O output de tudo em branco nao deveria virar correcao normal.
- `{{nota_final}}` literal veio de variavel nao renderizada + prompt confuso.
- O relatorio descartar `_documentos_faltantes` era mascaramento.

Mudanca de interpretacao:

- A recomendacao antiga de fallback `nota_final = N/A` deve ser vista como
  contencao temporaria.
- O comportamento final deve ser: sem nota confiavel -> erro alto e relatorio nao
  gerado.

Como orientar o proximo loop:

- Criar teste que impede `{{...}}` em qualquer documento salvo.
- Criar teste que sem correcao confiavel `GERAR_RELATORIO` falha.
- Rebaixar "nota N/A" de solucao para alerta de debito.

### Resumo da Sessao 2026-04-17

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/resumo_sessao_2026_04_17.md`
**Status:** historico de rodada.
**Serve para:** registrar sucessos, fracassos e agentes daquele dia.

Quotes relevantes:

> "A IA recebe um prompt pedindo para extrair respostas de... nada."

> "Documentos gerados SEM campos de aviso"

> "Schema da correcao usa formato antigo"

> "Fallback `nota_final = \"N/A\"`"

O que prova:

- O time ja tinha entendido que havia sucesso parcial e fracassos reais.
- Havia 12 agentes em rodadas paralelas.
- O registro final ja misturava fixes com ressalvas importantes.

O que ficou desatualizado:

- Algumas ressalvas foram corrigidas localmente depois.
- Outras, como metadata e provider revalidation, continuam abertas.
- A palavra fallback precisa ser reinterpretada pelo P0.

Como orientar o proximo loop:

- Registrar "feito" e "falta" lado a lado.
- Nao deixar resumo de sucesso apagar ressalvas.

## Evidencias De Teste

### Teste Chat -- Gemini 3 Flash

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/teste_chat_gemini.md`
**Status:** evidencia de teste.
**Serve para:** provar que chat basico com Gemini 3 Flash funcionou.

Quotes relevantes:

> "Ambos os testes retornaram HTTP 200"

> "Tokens reportados > 0"

> "o endpoint `/api/chat` está usando o system prompt do fluxo de correção de provas"

O que prova:

- Gemini 3 Flash funciona para chat em portugues e multi-turn.
- O chat tem tokens.
- O prompt do chat esta errado ou pelo menos contaminado por prompt de correcao,
  pois gerou PDF/base64 em chat livre.

Como orientar o proximo loop:

- Nao confundir "chat funciona" com "pipeline funciona".
- Separar prompt do chat de prompt de correcao.

### Teste `/executar/etapa` -- Apos Fix

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/teste_executar_etapa_corrigido.md`
**Status:** evidencia de teste.
**Serve para:** validar que etapa isolada passou a carregar contexto e falhar
quando falta documento.

Quotes relevantes:

> "Modelo usado: `gpt-5-nano` ... confirma que o `model_id` do request foi respeitado"

> "Campos `_avisos_documento` / `_avisos_questao` / `_avisos_stage` presentes: **NÃO**"

> "HTTP 400 com mensagem clara"

O que prova:

- A etapa isolada pode retornar erro claro quando falta prerequisito.
- GPT-5 Nano gerou resposta coerente para uma correcao isolada, mas sem schema
  oficial completo.
- O endpoint nao persistiu documento naquele teste.

O que precisa mudar:

- Se a etapa isolada e preview, documentar isso.
- Se deveria persistir, corrigir.
- Sem `_avisos_*` e schema oficial, nao promover o modelo para pipeline-ready.

### Teste Pipeline-Completo -- Gemini 3 Flash

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/teste_gemini_pipeline_completo.md`
**Status:** melhor evidencia positiva de provider.
**Serve para:** provar que Gemini 3 Flash completou as etapas downstream em um
aluno real.

Quotes obrigatorias:

> "Status final: SUCESSO"

> "Tentativas: 2"

> "Tentativa 1 falhou sem diagnóstico acessível via API."

> "`tokens_usados = 0` e `ia_modelo = null` nos documentos."

O que prova:

- Gemini 3 Flash conseguiu gerar correcao, analise e relatorio coerentes.
- `_avisos_*` apareceram nos tres JSONs naquele teste.
- A primeira tentativa falhou, entao estabilidade ainda nao era comprovada.
- Metadata de custo/modelo estava quebrada.

Leitura correta:

- Confirmado: conteudo downstream com Gemini 3 Flash pode funcionar.
- Parcial: confiabilidade sem retry e metadata.
- Falta: revalidar depois dos commits locais e medir custo real.

### Teste Pipeline-Completo -- GPT-5 Nano

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/teste_gpt5nano_pipeline_completo.md`
**Status:** evidencia de falha grave.
**Serve para:** impedir que GPT-5 Nano seja tratado como pipeline-ready.

Quotes obrigatorias:

> "Status final: FALHA"

> "corrigir foi marcada como \"completed\" ... mas na prática gerou 3 documentos lixo"

> "JSON válido: NÃO"

> "O behaviour via tool-use foi **pior** que via `/executar/etapa`"

> "Restrições respeitadas: não editei código; não fiz fallback para outro modelo"

O que prova:

- GPT-5 Nano pode entender a prova, mas falha na disciplina de tool-use/schema.
- A orquestracao marcou etapa como `completed` apesar de output inutilizavel.
- O sistema permitiu documento lixo: JSON malformado, txt vazio, frase sobre PDF
  dentro de `.json`.
- A ausencia de `failure_reason` dificulta diagnostico.

Regra para o proximo loop:

- GPT-5 Nano pipeline-completo = falha ate prova contraria.
- Output invalido deve travar a etapa original.
- Nenhum documento lixo deve ser salvo como sucesso.

### Teste Haiku / GPT-4o Referencia

**Arquivo:** `docs/plano_pipeline/arquivo_2026_04_17/teste_haiku_eric.md`
**Status:** evidencia de bloqueio e referencia parcial.
**Serve para:** mostrar Anthropic bloqueado por credito e GPT-4o como fallback
historico, nao como solucao ativa.

Quotes obrigatorias:

> "Creditos Anthropic insuficientes"

> "O modelo `claude-haiku-4-5-20251001` é VÁLIDO"

> "Pipeline com GPT-4o (fallback) | OK"

O que prova:

- Haiku nao foi validado porque faltava credito, nao porque o modelo era invalido.
- A mensagem de erro antiga mascarava a causa real.
- GPT-4o gerou outputs validos, mas em schema antigo e sem `_avisos_*`.

Mudanca de interpretacao:

- GPT-4o "fallback" foi util historicamente para diagnostico, mas hoje troca
  silenciosa de provider e proibida.
- Revalidacao GPT-4o deve ser teste explicito, nao rota de escape.

## Nota Tecnica Sobre PDFs

### Nota -- `/conteudo` nao le PDFs

**Arquivo:** `docs/plano_pipeline/notas/nota_tecnica_conteudo_pdf.md`
**Status:** nota tecnica viva.
**Serve para:** impedir delecao errada de provas respondidas.

Quotes obrigatorias:

> "conteudo: null ... nao prova que o documento esta vazio"

> "Os arquivos PDF estao intactos e acessiveis via outros endpoints."

> "`/api/documentos/{id}/conteudo` so e util para JSONs gerados pela pipeline"

O que prova:

- `prova_respondida` PDF com `conteudo=null` nao e bug por si.
- O arquivo deve ser verificado por `/download`, `/view` e storage.

Como orientar o proximo loop:

- Nunca deletar PDF por `conteudo=null`.
- O nome "conteudo" no endpoint e confuso para PDF; se houver ciclo de UI/API,
  renomear ou documentar melhor.

## Rio 3 Pausado

### Pesquisa Rio 3

**Arquivo:** `docs/plano_pipeline/rio3_pausado/rio3_provider_research.md`
**Status:** pausado.
**Serve para:** guardar pesquisa de modelos Rio e fluxo seguro futuro.

Quotes relevantes:

> "Escopo de teste travado: documentar todos os modelos possiveis"

> "Rio 3.0 so sera um substituto real no pipeline se"

> "um modelo Rio 3 sem tool calling validado nao pode ser marcado como pronto para pipeline"

O que prova:

- Rio 3 era uma frente de provider, nao objetivo central.
- O proprio plano Rio exigia validar tool calling antes de pipeline-ready.
- Ha textos antigos falando em fallback sem tools; pelo P0 atual, isso deve ser
  reinterpretado como design a evitar, salvo decisao explicita com UI muito clara.

Como orientar o proximo loop:

- Nao tocar Rio agora.
- Se Rio voltar, aplicar P0 anti-fallback e seguranca de chaves.

## Docs Meta Do Loop

### Workflow Analysis

**Arquivo:** `docs/workflow_analysis.md`
**Status:** meta vivo.
**Serve para:** explicar por que Paulo nao pode trabalhar de memoria.

Quotes relevantes:

> "Loop sem fonte de verdade granular"

> "Decisões do Otavio não eram persistidas como citações"

> "Nunca pular a verificação."

O que prova:

- O problema recorrente nao e so codigo; e processo.
- O loop precisa de quote, estado atual, gap e criterio verificavel.

Como orientar o proximo loop:

- Usar este Doc 14 como audit doc grande.
- Usar Doc 09 como painel curto.

### Skill Audit Loop

**Arquivo:** `docs/skill_audit_loop.md`
**Status:** meta vivo.
**Serve para:** formalizar o metodo de auditoria.

Quotes relevantes:

> "Extrai citações exatas do plano"

> "Gera uma tabela de gaps"

> "Declarar pronto sem verificar"

O que prova:

- O mega-doc precisa conter quotes, nao apenas resumo.
- Status sem gap table tende a virar autoengano.

Como orientar o proximo loop:

- Proximos ciclos devem atualizar uma tabela pequena de gaps no Doc 09 ou neste
  doc, conforme tamanho.

### Audit Quotes vs Implementation

**Arquivo:** `docs/audit_quotes_vs_implementation.md`
**Status:** meta historico.
**Serve para:** exemplo de auditoria que funcionou no tutorial.

Quotes relevantes:

> "O objetivo principal dessa ferramenta é gerar os relatórios de desempenho."

> "você simplesmente não seguiu o plano em loop corretamente"

> "Todos os gaps críticos corrigidos"

O que prova:

- Quotes exatas ajudam a corrigir rota.
- O produto nao e "um numero"; o output principal sao relatorios.

Como orientar o proximo loop:

- A pipeline precisa ser julgada por documentos corretos e explicaveis, nao so por
  status verde.

### Plano Geral Novo Tutorial

**Arquivo:** `docs/plano_geral_novo_tutorial.md`
**Status:** plano tutorial; util para filosofia e UX.
**Serve para:** lembrar que professor/aluno precisam entender resultado e erro.

Quotes relevantes:

> "MUITO MAIS QUE UM NUMERO"

> "Fallbacks silenciosos do executor"

> "Sem aviso de custo"

O que prova:

- UI precisa explicar custo e falhas.
- Fallbacks silenciosos ja eram ponto de friccao de UX.

Como orientar o proximo loop:

- Sprint 4 de UI de erros e dashboard de custos nao sao luxo; sao parte do produto.

## Fontes Complementares De `docs/`

Estas fontes nao estavam explicadas o bastante na primeira versao deste arquivo.
Elas nao substituem Docs 04/05/09/12, mas explicam por que o loop falha quando
Paulo trabalha rapido demais, ignora producao ou declara pronto sem verificacao.

### Prompt Log -- Sessao `5caa6b6b`

**Arquivo:** `docs/prompts/sessao_5caa6b6b.md`
**Status:** log bruto sensivel.
**Serve para:** preservar falas exatas do usuario que deram origem ao metodo de
auditoria com quotes.

Quotes seguras e relevantes:

> "isso tá rápido demais pra vcc ter feito tudo"

> "Doccumente direito onde você está e o que falta"

> "Your loop lacked in a lot of details"

> "create a new .md with exact quotes"

> "não tenha a capacidade de modificar o plano no meio do caminho"

O que prova:

- O usuario nao quer um resumo bonito: quer comparacao contra fonte original.
- O plano mestre nao pode ser reescrito para facilitar a conclusao.
- O loop precisa dizer o que foi feito e o que falta, especialmente quando ha
  deploy, provider, custo ou verificacao pendente.
- "Rapido demais" nao e elogio neste projeto; e sinal de risco.

Risco de seguranca:

- O prompt log e bruto e pode conter segredo historico. Esta auditoria nao deve
  republicar valores sensiveis.
- O Doc 11 ja registra a decisao correta: segredo/hook em claro deve ser
  rotacionado e nunca colado em docs novos.

Como orientar o proximo loop:

- Quando houver conflito entre resumo e quote, a quote vence.
- Quando Paulo escrever "feito", precisa haver evidencia no arquivo, teste,
  commit, deploy ou smoke correspondente.
- Quando a tarefa exigir uma leitura longa, o loop deve continuar trabalhando e
  reportando progresso, nao encerrar por ansiedade de fechamento.

### Logs -- README

**Arquivo:** `docs/logs/README.md`
**Status:** memoria tecnica antiga, mas formato util.
**Serve para:** padronizar logs de bug com problema, causa, solucao, testes e
verificacao.

Quotes relevantes:

> "Create institutional memory for debugging"

> "Root Cause Analysis"

> "Verification"

O que prova:

- Ja existia cultura de registrar causa raiz e comandos de verificacao.
- O Doc 09 pode usar esse formato em blocos curtos, sem criar muitos docs novos.

O que ficou desatualizado:

- A pasta `docs/logs` registra bugs de janeiro, nao o estado atual da pipeline.
- O formato e bom; os fatos tecnicos precisam ser revalidados antes de guiar
  providers/custos hoje.

Como orientar o proximo loop:

- Para cada provider que falhar, registrar problema, sintoma, causa provavel,
  evidencia, comando/smoke e status.
- Nao registrar valor de token, key, hook ou header.

### Log -- Chat Documents Not Loading

**Arquivo:** `docs/logs/2026-01-30_chat_documents_not_loading.md`
**Status:** resolvido historico; lesson learned ainda viva.
**Serve para:** lembrar que local e producao podem divergir, especialmente por
storage, path e ambiente Render.

Quotes relevantes:

> "frontend showed 161 documents selected"

> "The AI responded saying it had no access"

> "Always test the LIVE endpoint, not just local"

> "Supabase for ephemeral environments"

O que prova:

- UI dizendo que documento esta selecionado nao prova que backend/IA recebeu
  conteudo.
- Debug endpoint funcionar nao prova que o fluxo principal importou a mesma
  dependencia ou usou o mesmo storage.
- Render tem filesystem efemero; arquivos precisam estar no storage certo.

Como orientar o proximo loop:

- Provider smoke deve testar o endpoint real que o usuario usa, nao apenas funcao
  local.
- Quando documento some em producao, investigar DB + storage + resolver de path.
- Qualquer "funcionou local" precisa ser marcado como local ate deploy/smoke
  confirmar.

### Log -- Multiple Default Models

**Arquivo:** `docs/logs/2026-01-30_default_model_bug.md`
**Status:** resolvido historico, com uma tensao importante contra o P0 atual.
**Serve para:** mostrar bug de configuracao que causava escolha imprevisivel de
modelo.

Quotes relevantes:

> "Two models were marked as `is_default: true`"

> "`model_manager.get_default()` returned unpredictable results"

> "Data validation on load is critical"

> "Auto-correction is better than failing"

Leitura antiga:

- O sistema podia corrigir automaticamente `models.json` para manter um unico
  default.

Leitura nova pelo P0:

- Auto-reparo de dado interno pode ser aceitavel somente se for deterministico,
  logado e nao esconder resultado de pipeline.
- Para execucao de pipeline, "auto-correction is better than failing" nao vale
  como regra geral. Se o usuario pediu modelo X, nao trocar para modelo default
  e chamar de sucesso.
- Se a configuracao de modelo estiver ambigua, o correto e erro alto de
  configuracao, ou reparo administrativo visivel antes da execucao.

Como orientar o proximo loop:

- Auditar diferenca entre "sanear config corrompida antes da operacao" e
  "fallback silencioso durante uma etapa".
- Garantir teste: provider/modelo solicitado aparece no resultado e nos metadados.

### Log -- Mobile Modal Scroll Issues

**Arquivo:** `docs/logs/2026-01-30_mobile_modal_scroll_fix.md`
**Status:** deploy historico; util para metodo de UI.
**Serve para:** lembrar que UI exige verificacao visual e producao, nao so diff.

Quotes relevantes:

> "No automated tests added - these are visual/interaction fixes"

> "Manual Testing Checklist"

> "DEPLOYED (pending Render refresh)"

O que prova:

- Quando a mudanca e visual/interativa, o criterio de pronto inclui browser ou
  screenshot, nao apenas teste unitario.
- "Deploy acionado" nao e igual a "Render atualizado".

Como orientar o proximo loop:

- Sprint 4 de UI de erros deve ter evidencias visuais.
- Mensagens de falha por aluno/etapa precisam ser verificadas no site, inclusive
  mobile, porque modais e paineis ja quebraram antes.

### Tutorial Arquivado v1

**Arquivo:** `docs/tutorial_arquivado_v1.html`
**Status:** arquivo de referencia, deprecated.
**Serve para:** preservar prosa antiga e imagens de referencia sem expor ao
usuario final.

Quotes relevantes:

> "NÃO é exposto ao usuário final"

> "O NOVO CR não é só um corretor automático"

> "Relatórios de performance"

> "O aluno entende onde errou"

O que prova:

- A filosofia central e relatorio/entendimento, nao apenas nota.
- O tutorial antigo tambem diz que cada etapa gera documento, alinhado ao produto.
- O arquivo nao deve ser tratado como UI ativa.

O que ficou desatualizado:

- O tutorial antigo fala em algumas estruturas que foram corrigidas ou revisadas
  depois.
- Ele nao serve como prova de pipeline atual.

Como orientar o proximo loop:

- Usar como referencia de linguagem de produto quando UI de erros/custos for
  redesenhada.
- Nao usar como fonte tecnica de provider, tokens ou storage.

### Tutorial Assets v1

**Arquivo:** `docs/tutorial_arquivado_v1_assets/*.png`
**Status:** assets historicos.
**Serve para:** preservar contexto visual do tutorial antigo.

Arquivos existentes:

- `01-dashboard-anotado.png`
- `02-sidebar-anotado.png`
- `03-chat-anotado.png`
- `04-chat-exemplos.png`
- `05-nova-materia-anotado.png`
- `06-fluxo-correcao.png`
- `07-nova-turma.png`
- `08-adicionar-alunos.png`
- `09-nova-atividade.png`
- `10-upload-docs.png`
- `11-upload-lote.png`
- `12-botoes-pipeline.png`
- `13-config-pipeline.png`
- `14-resultados.png`

O que prova:

- Existem imagens antigas para explicar onboarding, pipeline, config e resultados.
- Elas sao evidencia de produto/UX, nao evidencia de provider funcionando.

Como orientar o proximo loop:

- Se a Sprint 4 reabrir UI de erros, usar assets antigos apenas como referencia
  comparativa.
- Se houver novo tutorial/print, verificar imagem real antes de declarar pronto.

## Custos -- Estado Correto

Separar tres camadas:

1. **Estimativa:** existe no Doc 05 e no catalogo.
2. **Medicao local de tokens:** feita localmente em `b12be9a` para input/output em
   chat/tool-use.
3. **Custo real persistido:** ainda nao existe.

Estado honesto em uma frase:

> O projeto esta mais perto de medir custo do que antes, mas ainda nao sabe dizer
> "quanto custou esta atividade" de forma persistida, auditavel e consultavel.

Fatos de codigo observados:

- `ModelCatalogManager.calculate_cost()` existe.
- Endpoints de catalogo/custo estimado existem na area de settings.
- `Documento` tem campos `tokens_usados` e `tempo_processamento_ms`.
- `storage.salvar_documento()` aceita `ia_provider`, `ia_modelo` e `prompt_usado`.
- `storage.salvar_documento()` hoje nao recebe `tokens_usados` nem
  `tempo_processamento_ms` como parametros publicos, apesar de persistir esses
  campos do objeto.
- `_salvar_resultado()` recebe `tokens` e `tempo_ms`, mas precisa garantir que
  esses valores entram no documento persistido.
- `create_document` no tool handler salva documentos com `criado_por="pipeline_tool"`
  sem metadata de provider/modelo/tokens.

Evidencia de codigo observada nesta releitura:

| Evidencia | Arquivo/linhas | Leitura |
|---|---|---|
| `_salvar_resultado()` recebe `tokens` e `tempo_ms` | `backend/executor.py:2042-2054` | O executor tem os dados no ponto certo. |
| `_salvar_resultado()` passa provider/modelo/prompt ao storage | `backend/executor.py:2099-2109` | Provider/modelo chegam ao storage nesse caminho. |
| `storage.salvar_documento()` aceita provider/modelo/prompt, mas nao tokens/tempo como parametros | `backend/storage.py:1270-1278` | Tokens ficam no default do `Documento`, a menos que outro caminho preencha. |
| `Documento` persiste `tokens_usados` e `tempo_processamento_ms` | `backend/storage.py:1370-1407` | O banco aceita os campos; o gap e alimentacao. |
| `ModelCatalogManager.calculate_cost()` calcula por input/output | `backend/model_catalog.py:293-318` | A formula existe; falta chamar no pipeline real. |

Gaps de custo:

| Gap | Impacto | Proximo teste |
|---|---|---|
| Tokens em memoria nao viram registro mensal | Nao ha custo por periodo | Rodar etapa e verificar arquivo `token_usage/YYYY-MM.json` quando implementado. |
| Metadata do documento fica null/0 | Matriz e auditoria nao conseguem explicar custo por artefato | Teste unitario de `salvar_documento` com tokens/modelo. |
| Catalogo stale | Estimativa pode estar errada | Marcar versao/preco como estimado ate atualizar. |
| Cached tokens ausentes | Custo de cache nao mede economia real | Adicionar campos quando provider expuser. |

Regra:

- Nao construir dashboard bonito antes de persistir custo real.
- Nao chamar custo de "medido" se veio de estimativa generica.
- Nao chamar token split de "custo pronto"; token split e pre-requisito.
- Nao aceitar `tokens_usados=0` em documento gerado por IA sem alerta alto.

Fila minima para custo real:

1. Fazer `_salvar_resultado()` e `create_document` carregarem provider/modelo/tokens
   ate o `Documento` persistido.
2. Criar `TokenUsageRecord` com materia/turma/atividade/aluno/etapa/provider/modelo.
3. Chamar `ModelCatalogManager.calculate_cost()` no fim de cada etapa validada.
4. Persistir sucesso e falha; falha tambem custa tokens.
5. So depois expor endpoint/dashboard por materia, turma, atividade e periodo.

## Providers -- Estado Correto

| Provider/modelo | Estado atual | Evidencia | O que falta |
|---|---|---|---|
| Gemini 3 Flash | Chat OK; `corrigir` pos-fix OK com custo | Task `task_8f53987c57c4`; JSON `6396c4feb3d5b92b`; PDF `6c62faa4ce6df137`; custo `US$ 0.007931` | Validar `analisar_habilidades` e `gerar_relatorio` com custo/metadata. |
| GPT-5 Nano | Falhou alto em `corrigir` | Task `task_49b7ada546d4`; nao produziu JSON/PDF obrigatorios; nenhum fallback automatico | Registrar custo de falhas sem documento final e investigar schema/tool-use. |
| Claude Haiku 4.5 | Bloqueado | Creditos Anthropic insuficientes | Recarregar creditos e testar sem trocar provider. |
| GPT-4o | Parcial/referencia historica | Gerou 3 etapas, mas schema antigo e sem avisos | Revalidar como modelo explicito, nao fallback. |
| Gemini 2.5 Flash/Lite | Incerto | Catalogo/flags historicamente inconsistentes | Validar capabilities antes de pipeline. |
| Ollama/local | Fora do pipeline real atual | Sem multimodal/tools suficientes | Nao promover sem testes. |
| OpenRouter/Groq/Mistral/etc | Nao testado ou parcial | Catalogo/sugestoes | So entram apos contrato de tools/vision claro. |

Regra por provider:

- Chat OK nao significa pipeline OK.
- Tool calling OK nao significa schema OK.
- Schema OK nao significa custo persistido.
- Custo persistido nao significa qualidade pedagogica.
- Provider validado antes de `b12be9a` precisa revalidacao se a pergunta envolve
  custo/metadata.

Erros conhecidos por provider/rota:

| Provider/modelo | Rota | Erro observado | Status de produto |
|---|---|---|---|
| Gemini 3 Flash | `pipeline-completo` | Primeira tentativa falhou sem diagnostico acessivel; metadata zerada/null | Usavel parcialmente; precisa mais amostras e custo real. |
| Gemini 3 Flash | `pipeline-completo` pos-fix `corrigir` | Depois de 503 retryability, task `task_8f53987c57c4` completou com JSON/PDF e custo | Confirmado para `corrigir`; nao para pipeline completa. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_49b7ada546d4` falhou alto por saida obrigatoria incompleta | Bloqueado para pipeline, mas nao gera mais sucesso falso nesse caso. |
| Claude Haiku 4.5 | `pipeline-completo` | Creditos Anthropic insuficientes; wrapper mascarou causa como modelo invalido | Bloqueado por credito; erro deve ser exposto com causa real. |
| GPT-4o | referencia historica | Outputs em schema antigo e sem `_avisos_*` | Revalidar explicitamente; nao usar como fallback. |

## Fallbacks A Remover Ou Converter Em Erro

| Area | Comportamento atual/historico | Nova interpretacao |
|---|---|---|
| Modelo solicitado ausente | Antes podia cair em default; `44c5786` corrigiu parte | Manter: modelo escolhido roda ou falha. |
| Provider sem tools | Antes podia cair em chat simples; `44c5786` corrigiu parte | Manter erro alto. |
| JSON parse | Regex/Markdown aceitos em alguns casos | JSON obrigatorio deve validar schema. |
| PDF auto-fallback | Sistema cria PDF se IA nao chamou `execute_python_code` | Nao pode marcar sucesso; virar erro/alerta bloqueante. |
| `nota_final=N/A` | Evita template literal | Contencao temporaria; relatorio sem nota confiavel deve falhar. |
| Gabarito original quando extracao falta | Pode mascarar pipeline incompleta | Deve ser decisao explicita e visivel. |
| Env var de API key | Resolucao server-side alternativa | Permitido se nao vaza e nao troca provider/modelo. |
| UI breadcrumb/display name fallback | Fallback visual local | Menor risco, mas nao pode esconder falha de pipeline. |

Evidencia de codigo observada nesta releitura:

| Evidencia | Arquivo/linhas | Leitura |
|---|---|---|
| Tool-use sem suporte hoje falha explicitamente | `backend/chat_service.py:914-923` | Bom: provider sem tools nao cai mais em chat simples. |
| PDF auto-fallback detecta `create_document` sem `execute_python_code` | `backend/executor.py:2580-2592` | Risco P0: o sistema compensa ausencia de tool esperada. |
| PDF fallback salva documento com display name de fallback | `backend/executor.py:2633-2640` | Risco P0: artefato pode parecer documento final. |
| PDF fallback adiciona alerta e continua | `backend/executor.py:2649-2657` | Alerta nao basta se a UI/estado ainda tratam como sucesso. |
| `executar_com_tools` retorna `sucesso=True` depois do fallback | `backend/executor.py:2666-2674` | Prioridade: transformar em erro alto ou sucesso parcial bloqueante. |
| Teste antigo esperava fallback como sucesso | `backend/tests/unit/test_f7_t1_pdf_auto_fallback.py:226-238` | Teste precisa ser reescrito sob a regra P0. |
| `_preparar_variaveis_texto` garante `nota_final = "N/A"` | `backend/executor.py:1755-1757` | Contencao local; proximo ciclo deve falhar se nota confiavel estiver ausente. |
| Teste P5 aceita JSON sem nota retornando `N/A` | `backend/tests/unit/test_erro_pipeline.py:655-657` | Teste deve mudar quando P0 remover fallback de nota. |

Prioridade P0 de remocao:

1. Schema invalido marcado como `completed`.
2. PDF auto-fallback tratado como sucesso.
3. Relatorio gerado com nota ausente ou falsa.
4. Qualquer troca automatica de modelo/provider.
5. Parsing permissivo que transforma lixo em documento.

Testes P0 que devem nascer do proximo ciclo:

| Teste | Deve provar |
|---|---|
| Modelo solicitado indisponivel | A pipeline falha com erro claro; nao troca para default. |
| Provider sem tools em etapa tool-use | A etapa falha antes de gerar artefato parcial. |
| JSON invalido em `create_document` | A etapa original falha; documento lixo nao vira `completed`. |
| IA nao chama tool de PDF quando PDF e obrigatorio | Resultado vira erro/alerta bloqueante, nao PDF automatico silencioso. |
| Nota confiavel ausente em relatorio | Relatorio nao e marcado como sucesso com `N/A` ou `0` inventado. |
| Erro de credito/provider | UI mostra causa real, sem wrapper generico enganoso. |

## Feito, Falta, Bloqueios

Esta e a leitura curta para retomar o longo prazo sem se perder:

| Frente | Feito localmente | Falta para aceitar | Bloqueio/risco |
|---|---|---|---|
| Docs/painel | Doc 09 consolidado; Doc 14 audita a historia inteira; Doc 12 marcado como historico/stale | Commitar/pushar docs atualizados e manter Doc 09 curto | Nao criar mais documentos pequenos sem decisao explicita. |
| P4 confiabilidade | Falha antes de extrair respostas sem prova valida | Revalidar no site oficial depois de deploy | GitHub tem os commits, mas Render nao atualizou. |
| P5/P6 relatorio | Preserva faltantes e evita template literal | Converter `N/A`/nota ausente em erro alto | Contencao pode parecer sucesso se nao for removida. |
| Sprint 2 schema/avisos | Testes locais de schema e visualizador | Revalidar providers pos-fix | GPT-5 Nano ainda tem historico de schema ruim. |
| Sprint 3/3b custos | `input_tokens`/`output_tokens`; metadata de documentos; endpoints `/api/custos/*` live | Criar registro de custo para falhas sem documento final | Historico antigo bloqueia custo por falta de split/provider. |
| Docs parciais de run falho | Patch marca `created_document_ids` como ERRO quando provider falha depois das tools | Novo caso falho em producao para provar quando ocorrer | Ja existem dois docs antigos com token split faltante do run anterior. |
| Providers | Gemini `corrigir` OK; Nano falha alto; Haiku bloqueado; GPT-4o historico | Smoke matrix pos-fixes por provider/rota/pipeline | Credito Anthropic e custo de falhas sem documento. |
| UI de erro | `task.error` agora aparece no site oficial para falha de etapa | Melhorar apresentacao e retry de erros provider | Mensagem ainda e bruta e longa. |
| Dados fantasmas | Nota PDF impede delecao por `conteudo=null` | Reclassificar lista antes de qualquer limpeza | Delecao errada de prova respondida PDF. |
| Rio 3 | Congelado e separado | Nada neste ciclo | Qualquer chave em chat e exposta. |

Proxima tese tecnica recomendada:

> Antes de melhorar dashboard visual de custo, confirmar deploy oficial e manter
> a regra P0: custo so vale para execucao rastreavel, sem documento inventado.

## Proximos Ciclos Recomendados

### Ciclo A -- Auditoria Anti-Fallback

Objetivo: listar e classificar fallbacks no codigo que afetam pipeline, documento,
provider, custo ou UI de erro.

Aceite:

- Cada fallback vira: permitido, proibido, ou permitido somente com alerta alto.
- Testes focados cobrem os proibidos principais.

### Ciclo B -- Schema Invalido Falha Na Etapa Original

Objetivo: impedir `completed` quando o documento gerado nao parseia ou nao segue
schema minimo.

Aceite:

- GPT-5 Nano-like malformed JSON falha em `CORRIGIR`.
- Nenhuma proxima etapa precisa descobrir o problema.
- Documento lixo nao e salvo como resultado real.

### Ciclo C -- Metadata E Custo Real

Objetivo: conectar tokens/modelo/provider ao documento e ao registro de custo.

Aceite:

- `tokens_usados`, `ia_provider`, `ia_modelo`, `tempo_processamento_ms` populados.
- `/api/custos/status` e `/api/custos/resumo` respondem no site oficial.
- Falhas que consomem tokens ficam registradas com status/erro, sem parecer
  sucesso.

### Ciclo D -- Provider Revalidation

Objetivo: revalidar providers pos-fixes locais.

Aceite:

- Gemini 3 Flash: seguir para `analisar_habilidades` e `gerar_relatorio`, depois
  exigir 2 execucoes completas sem trocar modelo, com custo/metadata.
- GPT-5 Nano: confirmar falha alta ou corrigir schema/tool-use antes de promover.
- Haiku: testar somente quando credito Anthropic existir.
- GPT-4o: testar explicitamente, nunca como fallback automatico.

### Ciclo E -- UI De Erros

Objetivo: usuario entender falha sem terminal.

Aceite:

- Falha por aluno/etapa visivel.
- Mensagem especifica para credito insuficiente, documento faltante, modelo sem
  tools, schema invalido e provider overload.
- Fallback proibido aparece como erro, nao como sucesso.

## Criterios Para Dizer "Pronto"

Nao aceitar como pronto:

- Provider trocado automaticamente.
- Nano testado por acidente.
- Documento `.json` invalido salvo como sucesso.
- PDF gerado automaticamente como se fosse output da IA.
- Relatorio com `N/A` ou template literal tratado como sucesso.
- Custo estimado chamado de custo medido.
- Live site sem commit/deploy confirmado.
- `prova_respondida` PDF deletado por `conteudo=null`.

Aceitar como pronto apenas quando:

- Etapa falha no ponto certo, com mensagem clara.
- Documento salvo valida schema.
- Provider/modelo usado e o solicitado.
- Tokens e custo sao registrados com contexto educacional.
- UI mostra erro alto quando precisa.
- Docs registram fato, evidencia e proximo passo sem esconder ressalva.

## Validacao Desta Auditoria

Validacoes que esta auditoria deve passar antes de ser considerada revisavel:

| Validacao | Comando | Resultado esperado |
|---|---|---|
| Sem whitespace ruim em arquivo novo | `git diff --no-index --check /dev/null docs/plano_pipeline/14_auditoria_mestre_pipeline_custos_providers.md` | Sem saida de erro. |
| Sem segredo reproduzido no novo doc | varredura local por padroes de segredo, com padroes omitidos do documento | No maximo mencoes genericas, nunca valor real. |
| Escopo isolado | `git status --short -- docs/plano_pipeline/05_visao_longo_prazo.md docs/plano_pipeline/09_progresso_longo_prazo.md docs/plano_pipeline/12_matriz_provider_fase.md docs/plano_pipeline/14_auditoria_mestre_pipeline_custos_providers.md` | Apenas Doc 05, Doc 09, Doc 12 e Doc 14 como arquivos deste ciclo. |
| Navegacao compativel com mega-auditoria | checar `Indice`, `Entrada Rapida`, `Fontes De Verdade E Loop Pos-Compactacao`, `Estado Do Projeto Em Uma Pagina`, `Resposta Modelo Do Estado Do Projeto`, `Checklist Executavel Do Doc 02`, `Loop De Resolucao Dos Problemas`, `Guia Para Qualquer IA Retomar` e `Lacunas Do Documento De Longo Prazo` | Leitor consegue ir direto para retomada pos-compactacao, estado, tarefas herdadas do Doc 02, loop de execucao, custos, providers, fallbacks, mapa de docs e proximos ciclos. |

Resultado observado nesta rodada:

- `diff --no-index --check` passou sem erros.
- Varredura de segredo nao encontrou chave ou hook literal no Doc 14; encontrou
  apenas a propria linha do comando de validacao e mencoes genericas a "deploy
  hook" em regras de seguranca.
- O Doc 14 agora tem `Indice`, `Entrada Rapida`, `Fontes De Verdade E Loop
  Pos-Compactacao`, `Estado Do Projeto Em Uma Pagina`, `Resposta Modelo Do
  Estado Do Projeto`, `Checklist Executavel Do Doc 02`, `Loop De Resolucao Dos
  Problemas`, `Guia Para Qualquer IA Retomar` e `Lacunas Do Documento De Longo
  Prazo`; tamanho deixou de ser criterio de qualidade.
- Nenhum codigo, Rio 3, deploy, segredo ou `.pytest_tmp` foi alterado por este
  ciclo. Os unicos ajustes fora do Doc 14 foram o resumo P0 no Doc 09 e a nota
  de status de custos no Doc 05, alem da nota de stale no Doc 12.

## Trabalho Aberto Desta Auditoria

Esta auditoria nao encerra o loop tecnico. Ela deixa o proximo trabalho mais
claro. O que ainda existe para fazer:

| Item | Tipo | Por que ainda falta |
|---|---|---|
| Revisar/aprovar lote de docs | Gate humano | O Doc 14 e grande e deve ser lido antes de commit. |
| Commitar docs explicitamente | Git | Arquivos docs estao modificados/untracked; nao usar `git add .`. |
| Ciclo anti-fallback | Codigo/testes | PDF auto-fallback, `nota_final=N/A`, regex/Markdown e parciais como sucesso ainda precisam tratamento. |
| Metadata/custo real | Codigo/testes/deploy | Metadata e endpoints existem localmente; falta deploy oficial e registro persistente de falhas com tokens. |
| Provider revalidation | Smoke/producao | Matriz Doc 12 esta stale ate push/deploy e testes por provider/rota. |
| UI de erros | Produto/frontend | Usuario precisa ver aluno, etapa, provider e causa sem terminal. |
| Limpeza de dados | Dados | "Fantasmas" precisam reclassificacao; PDF com `/conteudo=null` nao pode ser deletado. |

Regra de continuidade:

- Enquanto houver item aberto acima, uma validacao de docs nao deve ser tratada
  como fim do plano longo.
- O fechamento de um ciclo deve dizer explicitamente qual item fica como proximo.
- Segredo, deploy e comando destrutivo continuam exigindo gate.

## Fechamento

O ponto central desta auditoria e simples: a pipeline nao pode parecer saudavel
quando esta improvisando por baixo. O NOVO CR precisa errar alto, explicar onde
errou, e so chamar de sucesso aquilo que gerou artefato correto, validado,
rastreavel e custeavel.
