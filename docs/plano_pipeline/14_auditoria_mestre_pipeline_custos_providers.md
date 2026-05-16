# Auditoria Mestre -- Pipeline, Custos, Providers e Fallbacks

**Data:** 2026-05-17
**Responsavel operacional:** Paulo
**Status:** mapa grande de auditoria; o Doc 09 continua sendo o painel vivo curto

Este documento existe porque a pasta de planejamento ficou grande demais para ser
lida de memoria. Ele nao substitui os documentos originais: ele explica como cada
um deve ser lido, o que ainda vale, o que ficou historico, e quais fatos precisam
guiar os proximos ciclos.

Atualizacao de controle de 2026-05-17: o site oficial esta em runtime backend
`4094bda` por `/api/deploy-info` e `check_deploy.sh`. O commit funcional
`45f5cf8` fechou schema runtime fora do contrato; `4094bda` publica a cobertura
unitária anti-regressao para `ANALISAR_HABILIDADES` e `GERAR_RELATORIO`. O
smoke reduzido
`task_42e3b303c39a` revalidou `corrigir` com GPT-5.4 Mini (`gpt54mini001`) na
fixture Diana Omega: JSON `776b70be01c24641`, PDF final `12dbdc65d469e982`,
PDF intermediario `204a8a5c3f81af97` marcado `status=erro` por
`pdf_json_consistency`, split `26251/4582` e custo `US$ 0.040307`. O bloqueio
de custo duravel segue: `/api/custos/status?limit=80` retorna `ok=false` por
Supabase `PGRST205` em `public.token_usage`.

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
4. Os fixes principais ja chegaram ao site oficial ate `98fafc9`: `/api/deploy-info`
   confirma o servico `srv-d5t8gbh4tr6s738fr3s0` com
   `source=RENDER_GIT_COMMIT`. O marker HTML continua sendo apenas auxiliar em
   servico `rootDir=backend`.
5. P4 ja esta no codigo publicado: `EXTRAIR_RESPOSTAS` nao deve rodar sem
   `prova_respondida` valida; falta apenas smoke dedicado se esse bug voltar a
   ser alvo.
6. P5/P6 melhoraram relatorio e documentos faltantes; a contencao historica
   `nota_final=N/A` foi convertida em erro alto no commit `ad7e00e` para
   `GERAR_RELATORIO`.
7. Sprint 2 melhorou schema/defaults/visualizador, mas nao fechou o contrato do
   Doc 02 porque Path 2 ainda precisa validar schema antes de sucesso.
8. Sprint 3 separou `input_tokens`/`output_tokens`; Sprint 3b/4h confirmaram
   metadata/custo em documentos reais; Sprint 3c agrupou custo por `cost_run_id`;
   Sprint 3d criou `TokenUsageRecord` local para falhas sem documento; Sprint 3e
   preparou Supabase `token_usage`; Sprint 3f confirmou no endpoint live que a
   tabela ainda nao existe; Sprint 3g criou a migration dedicada `b2dc88b`,
   ainda nao aplicada ao banco.
9. Gemini 3 Flash esta confirmado em 5 etapas individuais do aluno, mas
   `extrair_gabarito` foi reclassificado como invalido porque retornou tudo
   `MISSING_CONTENT`; a pipeline sequencial pos-runner chegou ate `corrigir` e
   falhou alto por quota Google/Gemini `429`, deixando as etapas finais
   pendentes. GPT-5 Nano esta confirmado em `extrair_questoes`,
   `extrair_gabarito` pos-`5527e26` e nas tres etapas finais; `extrair_respostas`
   rodou mas foi reclassificada como falha de conteudo por tudo `ilegivel=true`
   ou vazio; a rodada `6b57ef1` -> `1ce3d23` mostrou que Nano consegue receber
   texto extraido e paginas escaneadas, mas ainda produz conteudo insuficiente
   ou suspeito; desde `1ce3d23`, esse falso sucesso falha alto no executor, nao
   cria novo documento verde e registra custo de falha. GPT-5.4 Mini entrou como
   candidato explicito para OCR/handwriting, passou em amostras de
   `extrair_respostas` e, depois de `2cad38a`, completou as 6 etapas em uma
   fixture simples oficial (`task_a5f0d734f0b3`) com documentos, custo medido
   aproximado `US$ 0.079110` e inspeção semantica inicial coerente dos JSONs.
   PDFs baixaram e têm texto, mas revelaram problemas de qualidade: feedback
   cortado em correção e nota/proficiência misturadas no relatório. Isso valida
   essa fixture com ressalva de PDF, nao a matriz inteira. O patch `0ac92f0`
   ficou live e o re-smoke `task_605512496b0d` completou as 6 etapas, mas
   revelou outro P0: JSONs coerentes e PDFs semanticamente divergentes
   (`corrigir` PDF `9.0`/Q3 `2.0` contra JSON `8`/Q3 `0`; `gerar_relatorio`
   PDF `Nota final: N/A` contra JSON `8`). O proximo patch deve bloquear essa
   divergencia no executor. O bloqueio foi publicado em `2052a01` e o smoke
   `task_857c0c3657ef` falhou alto em `corrigir`, como deveria; patch local
   seguinte adiciona retry explicito no mesmo modelo para regenerar somente o
   PDF a partir do JSON validado. O retry foi publicado em `3a77a17` e o smoke
   reduzido `task_e389f360b812` completou as etapas finais com PDF/JSON
   coerentes; o PDF invalido anterior ficou marcado como `erro` e o resumo de
   custos passou a expor `erro_pipeline`. Depois disso, a full Nano
   `task_f0c0f15a2f27` expôs um falso verde diferente: `GERAR_RELATORIO`
   mudou a nota da `CORRECAO` oficial de `8.0` para `0.0`. O commit `392ec7c`
   fechou essa brecha com validacao cross-stage de `nota_final`; o smoke
   `task_57da745b8de5` confirmou relatorio Nano com JSON `66fcc132db1be96a`,
   PDF final `735896580f441e89` e `Nota final: 8.0`, enquanto o PDF anterior
   `34e404fcd809270d` ficou `status=erro`. GPT-4o completou full smoke em
   `task_68b19146a95b`, com as 6 etapas, custo aproximado `US$ 0.314369` e
   JSON/PDF de correcao e relatorio coerentes na fixture Diana. Gemini 2.5
   Flash completou as tres extracoes em `task_f1f1511f21d5`; `854cec7`
   corrigiu a falta de tool-use Google com `toolConfig.functionCallingConfig`
   e fases JSON/PDF; `b07472f` removeu falso bloqueio de feedback por
   parafrase coerente; porem os reruns `task_6bba32964706` e
   `task_f9b76153875a` bateram quota Google `429`, entao tools Gemini 2.5
   Flash seguem bloqueadas para revalidacao final, nao confirmadas. Haiku segue
   bloqueado por creditos; Rio 3 esta pausado. Depois dos fixes anti-fallback
   `dc5884f`, `0d5ab9d`, `c870ed4` e `45f5cf8`, o smoke reduzido
   `task_42e3b303c39a` confirmou que `corrigir` com GPT-5.4 Mini ainda passa
   quando o JSON/PDF sao validos, e que o PDF inconsistente anterior fica como
   erro persistido, nao sucesso silencioso. O commit `4094bda` adicionou teste
   unitário para provar que o mesmo guard falha alto em `ANALISAR_HABILIDADES`
   sem `habilidades` e em `GERAR_RELATORIO` sem `nota_final`.
10. O proximo eixo correto e aplicar `backend/migrations/002_create_token_usage.sql`
    no Supabase, ampliar a revalidacao por etapa/provider e endurecer o contrato
    contra schema ruim. Enquanto a migration nao for aplicada, `460643f` faz
    `/api/custos/status` gritar `ok=false` e alerta `token_usage_not_durable`, e
    `54d083e` mostra esse bloqueio no dashboard oficial; em `45f5cf8`, o live
    ainda retorna `custos_persistencia_status=parcial_sem_token_usage_duravel`.

### O Que Temos

| Frente | Temos hoje | Limite da afirmacao |
|---|---|---|
| Documentacao | Doc 09 como painel curto; Doc 14 como auditoria mestre; Doc 05/12 com notas de status | Manter Doc 09 curto e Doc 14 detalhado; registrar novos ciclos sem criar doc extra. |
| Git/GitHub | `/api/deploy-info` confirmou runtime `4094bda`; `origin/main` esta alinhado com os fixes de dashboard de custo, tool-use Google faseado, consistencia PDF/JSON por feedback coerente, erro por aluno/etapa na sidebar, bloqueio anti-`nota_final=N/A`, guarda contra PDF auto-fallback, rejeicao de JSON embrulhado em Markdown/prosa, retorno Path 2 com etapa real/JSON parseado, schema minimo runtime e cobertura anti-regressao para etapas tardias | Nao usar somente marker HTML como gate quando Render `rootDir=backend` ignora commits sem backend; combinar `/api/deploy-info`, deploy list quando disponivel e comportamento live. |
| Pipeline P4 | Bloqueio de extracao de respostas sem prova valida esta no codigo publicado | Precisa smoke dedicado apenas se P4 voltar a ser alvo. |
| Pipeline P5/P6 | Preservacao de `_documentos_faltantes`; `ad7e00e` bloqueia `GERAR_RELATORIO` sem `nota_final` numerica confiavel | Ainda falta caçar outros fallbacks antigos, mas `nota_final=N/A` nao e mais aceite final no executor de relatório. |
| Schema/avisos | Defaults `_avisos_*`, visualizador melhorado e schemas mais permissivos | Permissividade nao e contrato forte; pode aceitar legado demais. |
| Tokens/custos | Split input/output; metadata de documento; endpoints `/api/custos/status` e `/api/custos/resumo` respondendo live; resumo agrega por `cost_run_id`; `TokenUsageRecord` local cobre falha sem documento enquanto o filesystem vive; codigo Supabase e migration dedicada `b2dc88b` existem; diagnostico live mostra `PGRST205`; smoke full GPT-5.4 Mini `task_a5f0d734f0b3` mediu custo por etapa e total aproximado `US$ 0.079110`; smoke Nano `task_57da745b8de5` registrou `29067/6701` tokens em documentos de relatorio; smoke reduzido GPT-5.4 Mini `task_42e3b303c39a` registrou `26251/4582`, `US$ 0.040307`, incluindo PDF intermediario em erro no mesmo `cost_run_id`; `/api/custos/status?limit=80` em `45f5cf8` mostrou `runs_precificados=46`, `runs_bloqueados=1`, `ok=false`, `custos_persistencia_status=parcial_sem_token_usage_duravel` e alerta bloqueante `token_usage_not_durable`; dashboard live em `54d083e` mostra "Custos não duráveis" | Falta aplicar `backend/migrations/002_create_token_usage.sql` no Supabase. |
| Providers | Gemini 2.5 Flash passou nas tres extracoes da fixture Diana; `854cec7` corrigiu o bug de tools incompletas com tool-use Google forcado/faseado; `b07472f` corrigiu falso bloqueio de feedback parafraseado; a revalidacao final agora esta bloqueada por quota Google `429`; Gemini 3 Flash passou em chat simples live, `extrair_questoes`, `extrair_respostas` e nas tres etapas finais, mas segue bloqueado por quota `429` para revalidacao full; `extrair_gabarito` Gemini foi reclassificado como invalido por tudo `MISSING_CONTENT` e depois revalidado na fixture simples; GPT-5 Nano passou em chat simples live, `extrair_questoes`, `extrair_gabarito` pos-`5527e26` e `gerar_relatorio` pos-`392ec7c`, mas `extrair_respostas` Nano continua parcial por historico de qualidade em dataset maior; GPT-5.4 Mini passou `extrair_respostas` em amostras e completou um smoke full oficial simples em `task_a5f0d734f0b3` com inspeção semantica inicial coerente; re-smoke `task_605512496b0d` no patch `0ac92f0` completou, mas PDFs divergiram dos JSONs; `2052a01` bloqueou isso com falha alta em `task_857c0c3657ef`; `3a77a17` passou no smoke reduzido `task_e389f360b812` com retry PDF/JSON; `45f5cf8` passou no smoke reduzido `task_42e3b303c39a` de `corrigir`, com JSON/PDF final coerentes e PDF intermediario em erro; `392ec7c` passou no smoke Nano de relatorio `task_57da745b8de5`; GPT-4o completou full smoke `task_68b19146a95b` em `54d083e`, com custo aproximado `US$ 0.314369`; `98fafc9` nao muda provider, mas torna falhas por etapa visiveis na sidebar | Revalidar matriz por provider, mas nao rerodar Gemini enquanto quota Google estiver saturada. |
| Seguranca Rio | Regra de nao usar chave em chat e Rio pausado | Arquivos Rio/untracked continuam fora do ciclo ativo. |

### O Que Falta

| Frente | Falta | Por que importa |
|---|---|---|
| Path 2/tool-use | Restringir artefatos extras e validar schema minimo, alem do JSON parseavel | Sem isso, documento ruidoso pode parecer resultado pedagogico final. |
| Anti-fallback | PDF auto-fallback, `nota_final=N/A`, JSON embrulhado em Markdown/prosa e schema minimo runtime de `CORRIGIR` estao protegidos contra sucesso verde; restam parciais como sucesso, duplicatas/stale e provider/model swap | Fallback silencioso engana o usuario. |
| Prompts/schema | Resolver conflito entre `PROMPTS_PADRAO` legado e `STAGE_TOOL_INSTRUCTIONS` | Modelos pequenos podem seguir o schema errado. |
| Custos | Registrar falhas que consomem tokens sem documento final | Sucesso com documento ja tem custo medido; falha ainda pode sumir. |
| Metadata | Revalidar provider/modelo/tokens/tempo nas rotas e providers restantes | GPT-5.4 Mini ja mostrou metadata e conteudo JSON coerente nas 6 etapas da fixture simples; Gemini/Nano/Haiku/GPT-4o ainda precisam matriz atualizada. |
| Providers | Revalidar Gemini, Nano, Haiku e GPT-4o nas etapas restantes, especialmente extracoes e pipeline completa | Resultado historico ou schema parseavel nao prova qualidade de conteudo. |
| UI de erro | `98fafc9` publica `stage_errors` por aluno/etapa no task-progress e renderiza a causa na sidebar; falta expandir o mesmo padrao para resultado/historico | Backend falhar alto nao basta se a UI traduz mal. |
| Dados | Reclassificar "fantasmas" sem deletar PDF valido por `/conteudo=null` | Evita apagar prova respondida real. |
| Git/deploy | Commit `2d72c6b` adicionou `/api/deploy-info`; o runtime atual confirmado e `45f5cf8` | Usar `/api/deploy-info` antes de novos smokes; marker HTML e apenas auxiliar. |

### Bloqueios E Alertas

| Item | Estado | Acao correta |
|---|---|---|
| Render/site oficial | `/api/deploy-info` confirmou `ad7e00e` como deploy live no patch anti-`nota_final=N/A` | Tratar HTML marker como auxiliar; usar smoke real para aceite. |
| Guard `5527e26` | Runtime confirmado por Render MCP; smoke Nano `extrair_gabarito` pos-guard passou com 7 respostas reais | Guard publicado; falta rerodar Gemini. |
| Respostas tudo ilegivel/vazio/inferidas | Nano ja produziu `extrair_respostas` com todas as respostas sem conteudo, depois conteudo so de Q7, depois conteudo suspeito inferido do enunciado, depois JSON verde inconsistente; o PDF de Eric tem paginas manuscritas e texto extraivel de Q7 | Desde `1ce3d23`, o caso final falha alto no executor e registra custo sem documento. Agora falta corrigir prompt/entrada/modelo para extrair conteudo real ou marcar Nano como inadequado para prova manuscrita. |
| Gemini quota | Pipeline sequencial `task_5e97bbee896e` falhou em `corrigir` por `429 RESOURCE_EXHAUSTED`, limite free tier `20` para `gemini-3-flash` | Nao rerodar de imediato; tratar como bloqueio de provider/quota, nao como sucesso nem como falha silenciosa. |
| Gabarito tudo missing | Gemini e Nano produziram historicamente `extrair_gabarito` com todas as respostas `MISSING_CONTENT`, apesar do PDF base ter texto de "Exercicio 5" extraivel por `pdftotext`; Nano passou pos-`5527e26` | Manter Gemini como falha ate rerun; Nano volta a confirmado nesta amostra. |
| Anthropic Haiku | Bloqueado por creditos | Testar apenas quando houver credito; erro deve aparecer claro. |
| Rio 3 | Pausado | Nao pedir chave, nao rodar smoke, nao misturar no ciclo atual. |
| `.pytest_tmp` e assets soltos | Muito ruido no worktree | Nao stagear por acidente; nunca usar `git add .`. |
| Segredos | Chave em chat e sempre exposta | Nunca registrar valor; usar Render/env/admin gate quando retomar. |

### Ordem Correta Agora

1. Aplicar a migration `backend/migrations/002_create_token_usage.sql` no
   Supabase e revalidar `/api/custos/status` ate `durable=true`.
2. Rerodar matriz de providers: Gemini quando quota permitir, Nano mantendo
   `extrair_respostas` como parcial ate dataset maior, Haiku quando houver credito
   e GPT-4o/mini em tarefas maiores.
3. Continuar ciclo anti-fallback e UI de erro: falhas por aluno/etapa/provider
   precisam aparecer sem terminal.
4. Rodar ciclo anti-fallback/Doc 02 no Path 2, com schema minimo por etapa.
5. Reclassificar dados "fantasma".
6. Retomar Rio 3 apenas por decisao explicita.

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
correto. A Sprint 3 separou `input_tokens` e `output_tokens`; o site oficial ja
expõe endpoints de custo, mas o historico duravel de `TokenUsageRecord` ainda
nao existe no Supabase.

O estado oficial agora e melhor que estava no inicio desta auditoria:
`/api/deploy-info` confirmou `2cad38a` live e o smoke GPT-5.4 Mini
`task_a5f0d734f0b3` completou 6 etapas com inspeção semantica inicial coerente
dos JSONs. A palavra "feito" continua exigindo quatro provas:
commit em `origin/main`, deploy Render confirmado, smoke oficial e registro nos
Docs 09/12/14. O marker HTML sozinho nao basta porque segue atrasado em
`e6060e1`.

Provider por provider: Gemini 3 Flash e o melhor positivo parcial, mas
`extrair_gabarito` foi reclassificado como invalido e a pipeline sequencial
bateu quota `429`; GPT-5 Nano passou em cinco etapas, mas `extrair_respostas`
continua falhando conteudo e agora falha alto desde `1ce3d23`, com custo de
falha registrado em `usage_52590d55d210459e`; GPT-5.4 Mini completou uma
fixture simples de 6 etapas com custo aproximado `US$ 0.079110` e JSONs
coerentes; PDFs baixam e têm texto, mas precisaram de patch de qualidade para
evitar feedback cortado e metricas confusas; Haiku esta bloqueado por creditos
Anthropic; GPT-4o e referencia historica, nao fallback automatico; Rio 3 esta
pausado e nao deve entrar em ciclo ativo nem receber chave em chat.

Custos estao em tres camadas: estimativas no Doc 05/catalogo, medicao de tokens
e custo por run em documentos/endpoints recentes, e persistencia duravel ainda
bloqueada porque `public.token_usage` nao existe no Supabase (`PGRST205`). Sem
essa tabela aplicada, nao da para responder com confianca historica "quanto
custou esta atividade/turma/aluno/periodo".

O proximo ciclo tecnico correto e cumprir o Doc 02 no Path 2 e remover fallback
silencioso: JSON invalido deve falhar na etapa original; a guarda contra PDF
auto-fallback deve continuar passando; nota ausente nao pode virar `N/A`;
provider/modelo solicitado deve rodar ou falhar; metadata e documento principal
precisam ser retornados e persistidos. So depois faz sentido persistir custo
real, revalidar providers, melhorar UI de erro e limpar dados.

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
| D02-1 | Path 2 deve parsear e validar JSON de `create_document` antes de sucesso | Parcial forte | JSON invalido agora falha antes do storage (`39aa50a`); `0d5ab9d` rejeita JSON de etapa quando ele vem embrulhado em Markdown/prosa ou array na raiz; `45f5cf8` aplica schema minimo tambem ao payload runtime de `create_document` | Proximo teste: cobrir ANALISAR/GERAR runtime fora do schema e duplicatas/stale. |
| D02-2 | `executar_com_tools()` deve retornar etapa real, `resposta_parsed` e `documento_id` | Parcial forte | `c870ed4` faz sucesso de tool-use retornar etapa real por `expected_document_type`, JSON parseado e `documento_id` quando ha JSON persistido; `45f5cf8` impede sucesso com JSON runtime fora de schema minimo | Proximo teste: retorno valido com storage persistido real e smoke provider/site. |
| D02-3 | Resolver conflito `PROMPTS_PADRAO` vs `STAGE_TOOL_INSTRUCTIONS` | Aberto | Validacao aceita formatos, mas prompt legado ainda pode orientar modelo ao schema errado | Teste: prompt ativo de Path 2 contem apenas contrato esperado ou marca legado como fora do caminho ativo. |
| D02-4 | `_avisos_documento`, `_avisos_questao`, `_avisos_stage` devem ser confiaveis | Parcial | Defaults foram injetados; visualizador melhorou; ainda falta distinguir default de output real do modelo | Teste: ausencia de `_avisos_*` em JSON de IA gera alerta de schema/default, nao sucesso silencioso. |
| D02-5 | Tokens do Path 2 precisam de input/output separados | Feito live para smokes recentes | Gemini e Nano em `corrigir` registraram `tokens_entrada`/`tokens_saida`; manter cobertura | Revalidar nas etapas `analisar_habilidades` e `gerar_relatorio`. |
| D02-6 | Tokens precisam virar custo persistido por contexto educacional | Parcial | Endpoints `/api/custos/*` respondem, precificam runs com split, agrupam JSON+PDF por `cost_run_id`; `TokenUsageRecord` local e codigo/migration Supabase existem; live confirma `PGRST205` | Teste: aplicar tabela Supabase `token_usage` e falha depois de consumir tokens cria registro duravel. |
| D02-7 | Metadata dos documentos deve ter provider/modelo/tokens/tempo | Parcial live | Documentos recentes de Gemini/Nano carregam provider/modelo/tokens/custo; falta cobrir todas as etapas e falhas | Teste: documento gerado por IA tem `ia_provider`, `ia_modelo`, `tokens_usados`, `tempo_processamento_ms` em cada etapa. |
| D02-8 | Provider sem tools nao pode cair em chat simples | Parcialmente fechado | `chat_service.py` agora falha explicitamente; manter contrato | Teste: provider sem function calling em etapa tool-use falha antes de criar artefato. |
| D02-9 | PDF obrigatorio ausente nao pode virar sucesso enganoso | Feito/guardado | O executor atual falha alto quando a saida dual esta incompleta; `dc5884f` estabilizou `test_f7_t1_pdf_auto_fallback.py` para provar JSON-only sem PDF como erro, sem falso vermelho de mock | Manter teste P0 em toda mudanca de `executar_com_tools`; se provider voltar a gerar parcial verde, corrigir no ciclo. |
| D02-10 | Retry dual-output nao pode duplicar/mascarar documentos | Parcial | Artefato extra nao-JSON foi bloqueado; duplicata JSON/retry ainda precisa auditoria | Teste: retry cria no maximo um JSON principal por etapa ou marca duplicata como erro. |
| D02-11 | GPT-5 Nano-like output lixo deve falhar cedo | Parcial | Historico gerou lixo; fixes agora rejeitam tool ausente, JSON invalido e payload malformado | Teste fixture Nano-like fora do schema minimo falha em CORRIGIR antes de ANALISAR/GERAR. |
| D02-12 | `GERAR_RELATORIO` precisa de schema unico e nota confiavel | Parcial | `ad7e00e` faz relatorio sem nota confiavel falhar alto; formatos legado/tool-use ainda coexistem | Proximo teste: schema ativo e unico, sem permissividade legado excessiva. |

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
- Manter a guarda de PDF ausente como erro alto e cobrir qualquer regressao em
  `executar_com_tools()`.
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
- quais commits ja estao no site oficial e qual gate provou isso;
- quais providers funcionaram, falharam, bloquearam ou estao stale;
- por que custo por run existe, mas custo historico duravel ainda nao existe;
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
| Medicao de tokens | Confirmada no site para runs recentes | Permite calcular custo por run com split input/output. |
| Persistencia de custo | Parcial | Documentos carregam custo; falhas sem documento usam `TokenUsageRecord` local; falta Supabase para historico duravel por materia/turma/aluno. |

Leitura geral:

- O projeto ja tem custo real por run recente, mas ainda nao tem historico
  duravel completo.
- `input_tokens`/`output_tokens` separados sao pre-requisito, nao meta final.
- Sem `TokenUsageRecord` em Supabase, custo por periodo ainda e projeto futuro.
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
| `a695db4` | P5/P6: nota e documentos faltantes | Contencao historica; superseded por `ad7e00e`, onde `N/A` virou erro alto para `GERAR_RELATORIO`. |
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
| `68ebe51` | Marcador `novocr-deploy` para `ff7b92a` | Publicado; `check_deploy.sh ff7b92a` falhou porque o live ainda mostra `97a7c79`. Docs antigos explicam que auto-deploy Git nao funciona e que precisa hook rotacionado/manual seguro. |

Estado do worktree no momento desta auditoria:

- Ha alteracoes de outros agentes/rodadas em `backend/chat_service.py`,
  `backend/routes_chat.py`, `frontend/index_v2.html`, `render.yaml` e muitos
  artefatos `.pytest_tmp`.
- Ha arquivos Rio/scripts/assets untracked que nao pertencem a este ciclo.
- O ciclo atual esta sendo executado em worktree limpo para nao misturar ruido
  do workspace principal.

O que ainda falta:

- Deployar/revalidar o patch PDF do smoke GPT-5.4 Mini `task_a5f0d734f0b3`; os
  JSONs ja passaram na inspeção semantica inicial.
- Manter o gate de deploy por `/api/deploy-info` e smoke real; HTML marker segue
  auxiliar.
- Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para que
  `token_usage_backend.durable=true`.
- Confirmar custo duravel por etapa/aluno/atividade no site oficial.
- Popular metadata de documento (`tokens_usados`, `ia_modelo`, `ia_provider`) de
  forma confiavel em todas as rotas restantes.
- Revalidar providers depois dos fixes atuais: Gemini `extrair_gabarito`, Nano
  sem promover `extrair_respostas`, Haiku quando houver credito e GPT-4o
  explicito.
- Remover ou converter fallbacks silenciosos restantes em erro alto.
- Corrigir UI para explicar falhas por aluno/etapa.
- Reclassificar dados "fantasma" sem deletar PDF valido por `conteudo=null`.

## Mapa Geral Das Travas

Esta secao fica antes do mapa de documentos porque ela responde a pergunta
"onde o projeto esta travando?" sem obrigar leitura arquivo por arquivo.

| Trava | O que significa | Evidencia | Proximo movimento |
|---|---|---|---|
| Gate oficial confuso | O HTML marker pode ficar stale por `rootDir=backend`; `/api/deploy-info` reporta o runtime backend. | `/api/deploy-info` retornou `2cad38a` via `RENDER_GIT_COMMIT`; smoke `task_a5f0d734f0b3` rodou no site oficial. | Usar `/api/deploy-info` como gate primario e smoke como aceite. |
| Fallbacks ainda misturados com robustez | Alguns docs/testes antigos tratam fallback como comportamento bom. | PDF auto-fallback e `nota_final=N/A` ja foram reclassificados; parsing permissivo segue risco ativo. | Ciclo anti-fallback antes de custo/dashboard. |
| Custo parcialmente persistido | Documentos recentes e `TokenUsageRecord` local cobrem parte do problema; historico por periodo ainda nao e duravel. | Deploy `4f27dae` e endpoints `/api/custos/*`; `PGRST205` confirma tabela ausente. | Aplicar `token_usage` no Supabase e validar falha real sem documento. |
| Provider matrix ainda incompleta | Doc 12 agora registra GPT-5.4 Mini full smoke com JSONs coerentes, mas nem todos os providers/rotas estao confirmados. | Gemini `extrair_gabarito` invalido; Nano `extrair_respostas` falha alto mas nao extrai; Haiku bloqueado por credito; GPT-4o historico. | Smoke por provider/rota depois de cada fix real, com custo e erro registrados. |
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
| `executar_com_tools()` deve retornar metadados uteis | `c870ed4` corrige o basico: etapa real, `resposta_parsed` e `documento_id` quando ha JSON persistido; `45f5cf8` adiciona schema minimo runtime. | Validar com storage real/site e cobrir ANALISAR/GERAR fora do schema. |
| Tokens do Path 2 precisam virar custo auditavel | `input_tokens`/`output_tokens` existem e custos recentes aparecem nos endpoints. | Persistir `TokenUsageRecord` em Supabase, custo por etapa/aluno/atividade e custo de falhas duravel. |
| Provider sem tools nao pode cair em chat simples | `chat_service.py` agora falha explicitamente para provider sem tool-use. | Manter teste cobrindo esse contrato e revalidar providers no site oficial. |
| PDF/artefato faltante nao pode virar sucesso enganoso | Estado atual guardado: `executar_com_tools()` falha alto para saida dual incompleta; `dc5884f` estabilizou o teste P0. | Manter a guarda e investigar somente regressao ou provider que volte a marcar parcial como verde. |
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
| PDF ausente continua falhando alto? | Garante que a regra P0 nao regrediu. | `test_f7_t1_pdf_auto_fallback.py` e smoke de etapa tool-use quando houver provider/credito. |
| `nota_final=N/A` continua bloqueado? | Evita regressao para relatorio enganoso. | Teste de `GERAR_RELATORIO` sem nota confiavel. |
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
| Markdown/prosa com JSON embutido | `0d5ab9d` | Corrigido para chamadas com `stage`: vira `invalid_json_envelope`, nao sucesso verde. |
| Regex para extrair JSON | `_parsear_resposta()` sem `stage` ainda preserva compatibilidade utilitaria | Risco baixo fora de pipeline; no caminho de etapa com `stage`, `0d5ab9d` bloqueia envelope. |
| Path 2 retorna `"tools"` sem JSON parseado | `c870ed4` + `45f5cf8` | Corrigido parcialmente: sucesso retorna etapa real e `resposta_parsed`; runtime fora do schema minimo de `CORRIGIR` falha alto. |
| PDF auto-fallback | Historico Doc 01; guarda atual em `backend/tests/unit/test_f7_t1_pdf_auto_fallback.py` | Reclassificado em 2026-05-17: nao apareceu como bug de runtime atual; `executar_com_tools()` falha alto para JSON-only sem PDF, e `dc5884f` estabilizou o teste P0. |
| Gabarito original se extracao falta | `backend/executor.py:1736` | Pode mascarar pipeline incompleta se nao for explicito. |
| Teste de PDF fallback esperando sucesso | `dc5884f` | Corrigido: nomes e asserts agora medem erro alto, `pdf_fallback_used=False` e ausencia de alerta `pdf_fallback`. |
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

- Migrar o registro local de `TokenUsageRecord` para persistencia duravel.
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
- PDF auto-fallback saiu da lista de risco ativo em `dc5884f`; ainda ha riscos
  de metadata e schema invalido.

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
| Tokens em memoria nao viram registro duravel | Custo por periodo ainda depende de Supabase `token_usage` | Rodar falha sem documento e verificar tabela `token_usage` apos migration aplicada. |
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
   ate o `Documento` persistido. **Parcialmente fechado para runs recentes.**
2. Criar `TokenUsageRecord` com materia/turma/atividade/aluno/etapa/provider/modelo.
   **Primeira versao local em `839968e`; preparo Supabase em `55e168a`;
   migration dedicada em `b2dc88b`; falta aplicar/verificar a tabela.**
3. Chamar `ModelCatalogManager.calculate_cost()` no fim de cada etapa validada.
4. Persistir sucesso e falha; falha tambem custa tokens.
5. So depois expor endpoint/dashboard por materia, turma, atividade e periodo.

## Providers -- Estado Correto

| Provider/modelo | Estado atual | Evidencia | O que falta |
|---|---|---|---|
| Gemini 3 Flash | Chat OK; `extrair_questoes`, `extrair_gabarito`, `extrair_respostas` e etapas finais OK em smokes individuais com custo; pipeline sequencial pos-runner bloqueada por quota em `corrigir` | `extrair_questoes`: task `task_737c8d45befc`, JSONs `3f1ca7eed14f5d37`/`9d61dcb36e6ca4b5`, custos `US$ 0.002806`/`US$ 0.002801`; `extrair_gabarito` historico `task_094c921eb038` foi invalido por tudo `MISSING_CONTENT`, mas o rerun `task_c08f3d478aad` criou JSON `92e5e77b24874ad1` com 4 respostas reais, tokens `2040/507`, custo `US$ 0.001220`; `extrair_respostas`: task `task_7d357943288d`, JSON `59cb3e341515d745`, custo `US$ 0.023273`; `corrigir`: task `task_8f53987c57c4`, custo `US$ 0.007931`; `analisar_habilidades`: task `task_a78369e23e5c`, JSON `7904a6a1aa34131f`, PDF `245970da4cc42c02`, custo `US$ 0.009447`; `gerar_relatorio`: task `task_58fb48fc8324`, JSON `fe6ad549481a0ed9`, PDF `b815d1faa5aeab77`, custo `US$ 0.006120`; sequencial `task_5e97bbee896e`: extracoes `025e065ceca92237`, `9188bd504796f767`, `ea25e7d9d9a0f9a0`, falha `429` em `corrigir` | Repetir pipeline sequencial completa quando quota/credito permitir, sem trocar modelo e sem retry cego. |
| GPT-5 Nano | Chat OK; `extrair_questoes`, `extrair_gabarito` e `corrigir` OK no smoke integrado pos-`f2211bb`; etapas finais tem sucesso individual historico; `extrair_respostas` falhou conteudo e agora falha alto desde `1ce3d23`; falta pipeline completa propria do Nano | Smoke integrado `task_19ee59ac1881`: `extrair_questoes` `d50f3b909e6773e7` (`US$ 0.003580`), `extrair_gabarito` `8dd414ee1617c3a5` (`US$ 0.002545`), `corrigir` JSON/PDF `f0302debf41ae58f`/`31794fc784905c00` (`US$ 0.002807`), falha em `analisar_habilidades` com doc erro `b5f17f2d1a980a3d` (`US$ 0.004213`). Historico: `extrair_respostas` falhou em `task_3d5feaf0da71`; analise individual ja passou em `task_020ba25bdb2b`; relatorio individual ja passou em `task_aec830b85c03`. | Manter Nano fora de `extrair_respostas`; revalidar etapas finais em run integrado apenas se Nano voltar a ser alvo. |
| GPT-5.4 Mini | `extrair_respostas` OK em amostras avulsas e smoke integrado; full smoke oficial simples completou as 6 etapas; etapas finais revalidadas com retry PDF/JSON | Smoke usou cadastro efemero `04b31001cf81`; teste de conexao retornou `OK`; `task_9c10e3752bcb` criou JSON `a39d26fcc621c7a8`, 4/7 respostas com conteudo real, 3/7 `MISSING_CONTENT`, tokens `97004/1942`, custo `US$ 0.081492`; depois `gpt54mini001` entrou em `backend/data/models.json`; `task_706931a94555` criou `fec100a2e41eabcf`, tokens `97004/1737`, custo `US$ 0.080570`; `task_19062336eb8b` criou `4a82ddf1d2118ff0`, 7/7 respostas reais, tokens `90588/2813`, custo `US$ 0.0806`; no smoke integrado `task_19ee59ac1881`, `gpt54mini001` criou `1e5db36f3ab9aa0e`, tokens `18176/2081`, custo `US$ 0.022996`; no smoke full `task_a5f0d734f0b3` completou as 6 etapas no Render `2cad38a`, com custo total aproximado `US$ 0.079110` e JSONs coerentes; re-smoke `task_605512496b0d` no Render `0ac92f0` completou as 6 etapas, mas PDF de correcao divergiu (`9.0`/Q3 `2.0` contra JSON `8`/Q3 `0`) e PDF de relatorio mostrou `Nota final: N/A` contra JSON `8`; `task_857c0c3657ef` no Render `2052a01` falhou alto em `corrigir` e registrou custo `US$ 0.024458` (`16116/2749`); `task_e389f360b812` no Render `3a77a17` completou etapas finais, com `corrigir` PDF/JSON `b9fbaf4dc24b4a75`/`dd79a9c3f369fc09`, Q3 `0.0/2.0`, `gerar_relatorio` PDF/JSON `3bc1b11467f885ce`/`ce538fb798f1230e`, custo das etapas finais `US$ 0.032536`, `US$ 0.021490`, `US$ 0.019338`. | Confirmado nessa fixture simples; repetir em datasets maiores e nos demais providers. |
| Claude Haiku 4.5 | Bloqueado | Creditos Anthropic insuficientes | Recarregar creditos e testar sem trocar provider. |
| GPT-4o | Confirmado na fixture simples Diana para pipeline completa | Full smoke `task_68b19146a95b` em `54d083e`: `extrair_questoes` `5adf51fcd1adc4c0`, `extrair_gabarito` `7c097774fce46472`, `extrair_respostas` `9e6d562d51a6f6e4`, `corrigir` JSON/PDF `b2abc9a73c8dc3a8`/`8911e1a3acae4ad2`, `analisar_habilidades` JSON/PDF `21f2d7d065aeafe5`/`72203996b8960b50`, `gerar_relatorio` JSON/PDF `bbc5963d712a7f1e`/`f12312b96e3725a3`; custo aproximado `US$ 0.314369`; inspeção semantica: 4 questoes, nota `8.0`, PDFs de correcao/relatorio com `Nota Final: 8.0`. | Repetir em dataset maior e confirmar UI/metadata/custo persistido, mas nao tratar mais como fallback historico. |
| Gemini 2.5 Flash/Lite | Flash confirmado para extracoes; tools corrigidas no codigo, mas revalidacao bloqueada por quota; Lite apenas conexao OK | `task_f1f1511f21d5` em `54d083e` completou `extrair_questoes` `4d5c5abdc1203f2b`, `extrair_gabarito` `d27793f610a3696c` e `extrair_respostas` `ffed15b8003145e9`; falhou alto em `corrigir` por tools incompletas. `854cec7` passou a enviar `toolConfig.functionCallingConfig.mode=ANY` e `allowedFunctionNames` para Google e a fasear JSON/PDF; `task_cdef8694893e` provou que Google passou a chamar tools, mas revelou bloqueio de consistencia de feedback. `b07472f` aceitou parafrase coerente sem aceitar feedback truncado. Reruns `task_6bba32964706` e `task_f9b76153875a` falharam por quota Google `429`. | Nao rerodar enquanto quota estiver saturada; quando liberar, repetir `corrigir`/pipeline e atualizar status para confirmado ou falhou alto. |
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
| Gemini 3 Flash | `pipeline-completo` pos-fix `corrigir` | Depois de 503 retryability, task `task_8f53987c57c4` completou com JSON/PDF e custo | Confirmado para `corrigir`; extracoes ainda pendentes. |
| Gemini 3 Flash | `pipeline-completo` pos-fix etapas finais | Tasks `task_a78369e23e5c` e `task_58fb48fc8324` completaram com JSON/PDF e custo | Confirmado para `analisar_habilidades` e `gerar_relatorio`; nao valida extracoes. |
| Gemini 3 Flash | `pipeline-completo` pos-fix `extrair_questoes` | Task `task_737c8d45befc` completou, mas timeout de cliente e retry operacional geraram dois documentos de extracao | Confirmado para conteudo/custo de `extrair_questoes`; bug operacional corrigido por `f55e299` e endurecido por `e6060e1`; marker HTML ainda atrasado. |
| Gemini 3 Flash | `pipeline-completo` pos-fix `extrair_gabarito` | Task `task_094c921eb038` completou; resposta inicial retornou `task_id` em 1.155s e `/api/health` ficou saudavel nos 20 polls, mas o JSON marcou todas as questoes como `MISSING_CONTENT` apesar de existir texto de Q5 no PDF base | Reclassificado como falha de conteudo historica; rerun posterior `task_c08f3d478aad` corrigiu a fixture Diana. |
| Gemini 3 Flash | `pipeline-completo` pos-fix `extrair_respostas` | Task `task_7d357943288d` completou; resposta inicial retornou `task_id` em 1.002s e `/api/health` ficou saudavel | Confirmado para conteudo/custo de `extrair_respostas`; as 6 etapas individuais estao OK. |
| Gemini 3 Flash | `pipeline-completo` sequencial pos-runner | Task `task_5e97bbee896e` completou as tres extracoes, manteve health saudavel, mas falhou alto em `corrigir` por quota `429`; correcoes parciais ficaram `status=erro` e custo bloqueado por `token_split_missing` | Bloqueado por quota provider; nao promover como pipeline completa validada. |
| Gemini 2.5 Flash | `pipeline-completo` em `54d083e` | Task `task_f1f1511f21d5` completou as tres extracoes, mas falhou alto em `corrigir` por saida obrigatoria incompleta: sem JSON via `create_document` e PDF via `execute_python_code` | Falha correta antes de `854cec7`; nao criou PDF/JSON inventado. |
| Gemini 2.5 Flash | `pipeline-completo` em `854cec7` | Task `task_cdef8694893e` provou que Google passou a chamar tools depois de `toolConfig.functionCallingConfig`, mas o PDF foi marcado `status=erro` por consistencia de feedback geral | Bug de tool-use corrigido; validador de feedback estava estrito demais para parafrase coerente. |
| Gemini 2.5 Flash | `pipeline-completo` e `corrigir` isolado em `b07472f` | Tasks `task_6bba32964706` e `task_f9b76153875a` falharam por quota Google `429`; documento parcial `338b25f9c0f74415` ficou `status=erro` e nao conta como sucesso | Bloqueado por quota; repetir quando quota liberar, sem trocar provider/modelo e sem aceitar parcial verde. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_49b7ada546d4` falhou alto por saida obrigatoria incompleta | Falha correta, sem fallback. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_edb822810ddc` completou com PDF, mas JSON invalido | Corrigido por `39aa50a`; JSON invalido nao deve entrar no storage. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_1a7857360267` completou com JSON parseavel, PDF via execute e custo | Confirmado para `corrigir`; nao para pipeline completa. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_c460627779fc` falhou com `tools: 'str' object has no attribute 'get'` | Corrigido por `eab7d90`; payload malformado vira erro estruturado. |
| GPT-5 Nano | `pipeline-completo` pos-fix `analisar_habilidades` | Task `task_43d48d9deea2` falhou alto: `execute_python_code` nao gerou PDF obrigatorio; JSONs parciais ficaram `status=erro` com custo medido, mas nome `student123` | Historico de falha que motivou `924fd79`/`d653c13`; nao e mais o ultimo smoke. |
| GPT-5 Nano | patches `924fd79`/`d653c13` | Retry de PDF/JSON agora inclui contexto original e instrucao anti-placeholder; JSON de analise com placeholder proibido falha alto; testes locais passaram | `924fd79` esta live; `d653c13` ainda aguarda marker live. |
| GPT-5 Nano | `pipeline-completo` pos-fix `corrigir` | Task `task_a591421ab84b` completou com JSON parseavel, PDF via execute, custo e sem artefato extra | Confirmado para `corrigir`; proximo alvo e custo de falhas e etapas seguintes. |
| GPT-5 Nano | `pipeline-completo` pos-fix etapas finais no marker `924fd79` | Task `task_020ba25bdb2b` completou `analisar_habilidades` e task `task_aec830b85c03` completou `gerar_relatorio`, ambas com JSON+PDF, tokens splitados, custo e sem placeholders proibidos nos JSONs novos | Confirmado para as tres etapas finais; ainda nao confirma extracoes, pipeline completa de 6 etapas nem deploy do guard `d653c13`. |
| GPT-5 Nano | `pipeline-completo` pos-fix `extrair_questoes` | Task `task_ae679b5c3fee` completou, JSON `946e66708fd72643` com `questoes`, `total_questoes=7`, `_avisos_*`, tokens `2148/12147` e custo `US$ 0.004966` | Confirmado para `extrair_questoes`; faltam `extrair_gabarito` e `extrair_respostas`. |
| GPT-5 Nano | `pipeline-completo` pos-fix `extrair_gabarito` | Task `task_2da0fb90c3fb` completou, JSON `61fb077d746c2a55`, tokens `78104/3635`, custo `US$ 0.005359`, mas todas as 7 respostas vieram `MISSING_CONTENT` | Falha historica de conteudo; motivou `5527e26`. |
| GPT-5 Nano | `pipeline-completo` pos-`5527e26` `extrair_gabarito` | Task `task_dc719eeea626` completou, JSON `5f433f9a1bc30842`, tokens `78104/8353`, custo `US$ 0.007246`, 7 respostas reais e nenhuma `MISSING_CONTENT` | Confirmado para Nano nesta amostra; proximo alvo e `extrair_respostas`. |
| GPT-5 Nano | `pipeline-completo` pos-`5527e26` `extrair_respostas` | Task `task_a9ff0d69d5e9` completou, JSON `b968c9539f277deb`, tokens `85774/3002`, custo `US$ 0.005489`, mas todas as 7 respostas vieram `ilegivel=true`; PDF `f60d37284d616ca4` tem texto extraivel da questao 7 | Falha de conteudo; motivou `8dd6c54`. |
| GPT-5 Nano | `pipeline-completo` pos-`8dd6c54` `extrair_respostas` | Task `task_03ae99db3006` completou, JSON `2a518dfb6b2a03ef`, mas todas as 7 respostas vieram `em_branco=true` e sem `resposta_aluno` | Guard anti-tudo-`ilegivel` foi insuficiente. |
| GPT-5 Nano | `pipeline-completo` pos-`c1598b9` `extrair_respostas` | Task `task_6772978a20c4` completou, JSON `10d1c1d9741a6273`, ainda sem conteudo real | Validacao central correta no schema nao estava no caminho real do executor multimodal. |
| GPT-5 Nano | `pipeline-completo` pos-`01fb04c` `extrair_respostas` | Task `task_b511641dfa52` falhou alto com erro explicito de respostas sem conteudo; nenhum novo documento verde apareceu depois de `10d1c1d9741a6273`; `/api/custos/status` mostrou `token_usage_analisados=1`, mas `durable=false` por `PGRST205` | Falso sucesso corrigido. A etapa ainda precisa extrair conteudo real antes da pipeline completa. |
| GPT-5 Nano | `pipeline-completo` pos-`1ce3d23` `extrair_respostas` | Depois de adicionar questoes, texto extraido, imagens de paginas escaneadas e proibicao de inferencia, a task `task_3d5feaf0da71` falhou alto: 6 de 7 respostas sem conteudo com scans anexados; nao criou novo documento verde; custo de falha `usage_52590d55d210459e`, tokens `100188/8863`, `US$ 0.008555` | Produto protegido contra falso sucesso final. Qualidade real de OCR/handwriting com Nano segue ❌. |
| GPT-5.4 Mini | `pipeline-completo` apenas `extrair_respostas` | Task `task_9c10e3752bcb` completou com JSON `a39d26fcc621c7a8`; 4/7 respostas extraidas, 3/7 `MISSING_CONTENT`, tokens `97004/1942`, custo `US$ 0.081492`. Task versionada `task_706931a94555` com `gpt54mini001` completou com JSON `fec100a2e41eabcf`; 5/7 respostas extraidas, Q1/Q2 `MISSING_CONTENT`, Q3 `LOW_CONFIDENCE`, tokens `97004/1737`, custo `US$ 0.080570`. Segunda amostra versionada `task_19062336eb8b` completou com JSON `4a82ddf1d2118ff0`; 7/7 respostas extraidas, Q2/Q3 `LOW_CONFIDENCE`, tokens `90588/2813`, custo `US$ 0.0806` | Primeiro candidato OpenAI que destrava conteudo real em mais de uma amostra manuscrita; ainda precisa pipeline per-phase. |
| GPT-5.4 Mini | `pipeline-completo` full smoke pos-`2cad38a` e etapas finais pos-`3a77a17` | Task `task_a5f0d734f0b3` completou as 6 etapas com `gpt54mini001` na fixture Diana Omega: `extrair_questoes` `f65318c550a76842`, `extrair_gabarito` `70df18512be9c617`, `extrair_respostas` `14ca81d800de2648`, `corrigir` `2c7cd4cf9eb85e57`/`769744b6fff6f3b9`, `analisar_habilidades` `12b24cd992477eab`/`15579ed3ad2614be`, `gerar_relatorio` `38686372cb8ea981`/`37b0c86cee879ced`; custo aproximado `US$ 0.079110`; inspeção JSON: 4 questoes, gabarito completo, 4 respostas da aluna, nota `8/10`, erro apenas na Q3 de porcentagem, analise/relatorio coerentes; inspeção PDF inicial achou feedback cortado e metrica misturada. Depois, `task_e389f360b812` no Render `3a77a17` revalidou etapas finais com PDF/JSON coerentes. | Confirmado para essa fixture simples no site oficial; repetir por dataset/provider. |
| GPT-5 Nano + GPT-5.4 Mini per-phase | `pipeline-completo` pos-`f2211bb` | Task `task_19ee59ac1881` passou por `extrair_questoes`, `extrair_gabarito`, `extrair_respostas` e `corrigir`; depois falhou alto em `analisar_habilidades` por tool-use incompleto. O patch `f2211bb` reduziu contaminacao de artefatos antigos: `extrair_gabarito` caiu para `6918/5497` tokens e `extrair_respostas` Mini para `18176/2081`. | Pipeline completa ainda nao validada; proximo bloqueador e `analisar_habilidades` em tool-use integrado. |
| Claude Haiku 4.5 | `pipeline-completo` | Creditos Anthropic insuficientes; wrapper mascarou causa como modelo invalido | Bloqueado por credito; erro deve ser exposto com causa real. |
| GPT-4o | referencia historica | Outputs em schema antigo e sem `_avisos_*` | Revalidar explicitamente; nao usar como fallback. |

## Fallbacks A Remover Ou Converter Em Erro

| Area | Comportamento atual/historico | Nova interpretacao |
|---|---|---|
| Modelo solicitado ausente | Antes podia cair em default; `44c5786` corrigiu parte | Manter: modelo escolhido roda ou falha. |
| Provider sem tools | Antes podia cair em chat simples; `44c5786` corrigiu parte | Manter erro alto. |
| JSON parse | Sem `stage`, regex/Markdown ainda servem como utilitario; com `stage`, `0d5ab9d` exige JSON cru | Manter etapa de pipeline estrita e validar schema minimo antes de sucesso. |
| PDF auto-fallback | Historico: sistema podia compensar ausencia de `execute_python_code`; estado atual guardado em `dc5884f` | Manter erro alto e teste P0; nao reabrir como feature. |
| `nota_final=N/A` | Evitava template literal | Fechado em `ad7e00e`: relatorio sem nota confiavel falha antes da IA. |
| Gabarito original quando extracao falta | Pode mascarar pipeline incompleta | Deve ser decisao explicita e visivel. |
| Env var de API key | Resolucao server-side alternativa | Permitido se nao vaza e nao troca provider/modelo. |
| UI breadcrumb/display name fallback | Fallback visual local | Menor risco, mas nao pode esconder falha de pipeline. |

Evidencia de codigo observada nesta releitura:

| Evidencia | Arquivo/linhas | Leitura |
|---|---|---|
| Tool-use sem suporte hoje falha explicitamente | `backend/chat_service.py:914-923` | Bom: provider sem tools nao cai mais em chat simples. |
| Saida dual incompleta gera erro alto | `backend/executor.py` + `backend/tests/unit/test_f7_t1_pdf_auto_fallback.py` em `dc5884f` | Bom: JSON-only sem PDF retorna `sucesso=False`, `pdf_fallback_used=False` e alerta bloqueante. |
| Teste antigo de PDF fallback | `dc5884f` | Corrigido: a suite nao espera mais sucesso enganoso e nao quebra por mock de excecao/cost_run_id. |
| `_preparar_variaveis_texto` nao injeta `N/A` em `GERAR_RELATORIO` | `ad7e00e` | Bom: relatorio sem nota confiavel falha antes da IA. |
| Teste P5 de nota ausente | `ad7e00e` | Corrigido: JSON invalido ou sem nota retorna `None` e gera `NOTA_FINAL_INDETERMINADA`. |

Prioridade P0 de remocao:

1. Schema invalido marcado como `completed`.
2. Schema minimo permissivo que transforma lixo em documento.
3. Relatorio gerado com nota ausente ou falsa.
4. Qualquer troca automatica de modelo/provider.
5. Avisos/defaults que fazem parecer que o modelo declarou algo que o sistema
   apenas preencheu.

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
| Docs/painel | Doc 09 consolidado; Doc 14 audita a historia inteira; Doc 12 registra matriz provider/fase | Manter Doc 09 curto e Doc 14 como auditoria grande | Nao criar mais documentos pequenos sem decisao explicita. |
| P4 confiabilidade | Falha antes de extrair respostas sem prova valida | Smoke especifico de P4 se esse bug voltar a ser alvo | Codigo ja esta no deploy oficial, mas nao foi o smoke principal de 2026-05-15. |
| P5/P6 relatorio | Preserva faltantes e evita template literal | Converter `N/A`/nota ausente em erro alto | Contencao pode parecer sucesso se nao for removida. |
| Sprint 2 schema/avisos | Testes locais de schema e visualizador | Revalidar providers pos-fix | GPT-5 Nano ainda tem historico de schema ruim. |
| Sprint 3/3b/3c/3d/3e/3f/3g custos | `input_tokens`/`output_tokens`; metadata de documentos; endpoints `/api/custos/*` live; runs Gemini/Nano custeaveis; amostras agrupadas por `cost_run_id`; registro local para falha sem documento; codigo Supabase preparado; migration dedicada `b2dc88b`; endpoint diagnostica backend | Aplicar tabela Supabase `token_usage` | Historico antigo bloqueia custo por falta de split/provider; live confirmou `PGRST205`, entao persistencia local nao e duravel entre deploys. |
| Higiene de artefatos processados | `f2211bb` usa somente o artefato processado mais recente por tipo em prompts/anexos e impede recuo para gabarito original em `corrigir` | Repetir pipeline ate completar 6 etapas | A correcao reduziu custo/contexto e revelou o proximo bloqueador real em `analisar_habilidades`. |
| Docs parciais de run falho | Patch marca `created_document_ids` como ERRO quando provider falha depois das tools | Novo caso falho em producao para provar quando ocorrer | Ja existem dois docs antigos com token split faltante do run anterior. |
| Providers | Gemini 5 etapas individuais OK e `extrair_gabarito` reclassificado como falha de conteudo; Nano `extrair_questoes`/`extrair_gabarito`/`corrigir` OK no run integrado, `analisar_habilidades` parcial e `extrair_respostas` ❌; rotas legadas retornam 410; Haiku bloqueado; GPT-4o historico | Corrigir maior bloqueador reproduzido: `analisar_habilidades` integrado; depois repetir ate `gerar_relatorio` | Credito Anthropic, quota Gemini, custo duravel de falhas sem documento e UI ainda pouco clara. |
| UI de erro | `task.error` agora aparece no site oficial para falha de etapa | Melhorar apresentacao e retry de erros provider | Mensagem ainda e bruta e longa. |
| Dados fantasmas | Nota PDF impede delecao por `conteudo=null` | Reclassificar lista antes de qualquer limpeza | Delecao errada de prova respondida PDF. |
| Rio 3 | Congelado e separado | Nada neste ciclo | Qualquer chave em chat e exposta. |

Proxima tese tecnica recomendada:

> Antes de melhorar dashboard visual de custo, manter gate oficial confiavel
> (Render MCP/deploy list ou marker comprovadamente atualizado) e a regra P0:
> custo so vale para execucao rastreavel, sem documento inventado.

## Proximos Ciclos Recomendados

### Ciclo A -- Auditoria Anti-Fallback

Objetivo: listar e classificar fallbacks no codigo que afetam pipeline, documento,
provider, custo ou UI de erro.

Aceite:

- Cada fallback vira: permitido, proibido, ou permitido somente com alerta alto.
- Testes focados cobrem os proibidos principais.

### Ciclo B -- Schema Invalido Falha Na Etapa Original

Objetivo: impedir `completed` quando o documento gerado nao parseia ou nao segue
schema minimo. A parte de JSON parseavel foi fechada em `39aa50a`; a restricao
de artefato extra nao-JSON em `create_document` foi fechada em `b24f03e`; o
payload malformado em `documents` foi fechado em `eab7d90`; schema minimo por
etapa ainda fica aberto.

Aceite:

- GPT-5 Nano-like malformed JSON falha em `CORRIGIR`.
- Nenhuma proxima etapa precisa descobrir o problema.
- Documento lixo nao e salvo como resultado real.
- `create_document` nao gera artefato extra nao-JSON em etapa dual-output.

### Ciclo C -- Metadata E Custo Real

Objetivo: conectar tokens/modelo/provider ao documento e ao registro de custo.

Aceite:

- `tokens_usados`, `ia_provider`, `ia_modelo`, `tempo_processamento_ms` populados.
- `/api/custos/status` e `/api/custos/resumo` respondem no site oficial.
- O resumo agrega custo por `cost_run_id`, nao por documento salvo, quando JSON e
  PDF pertencem ao mesmo run. **Fechado em `7ed8b8b`.**
- Falhas que consomem tokens sem documento ficam registradas em
  `TokenUsageRecord` local, sem parecer sucesso. **Primeira versao em
  `839968e`; preparo Supabase em `55e168a`; diagnostico live em `4f27dae`
  confirmou `PGRST205`; falta aplicar a tabela.**

### Ciclo D -- Provider Revalidation

Objetivo: revalidar providers pos-fixes locais.

Aceite:

- Gemini 3 Flash: as 6 etapas individuais ja passaram; exigir 2 execucoes
  completas sem trocar modelo, com custo/metadata. A primeira tentativa
  sequencial pos-runner falhou por quota `429`, entao aguardar quota/credito
  antes de repetir.
- GPT-5 Nano: `extrair_questoes`, `extrair_gabarito` pos-`f2211bb` e
  `corrigir` passaram no smoke integrado; etapas finais passaram em smokes
  individuais, mas `analisar_habilidades` falhou alto no run integrado por
  tool-use incompleto. `extrair_respostas` continua fora do Nano e deve usar
  modelo explicito melhor, como `gpt54mini001`.
- GPT-5.4 Mini: `extrair_respostas` passou em amostras oficiais; settings
  `from-catalog` foi corrigido e retestado, mas cadastro por API nao sobreviveu
  deploy. `gpt54mini001` versionado passou tambem no smoke per-phase
  `task_19ee59ac1881` e, depois de `2cad38a`, completou o full smoke oficial
  simples `task_a5f0d734f0b3`, com inspeção semantica inicial coerente dos
  JSONs. PDFs baixaram com texto extraivel, mas revelaram feedback cortado e
  metrica confusa; o patch local endurece essas instrucoes. O aceite seguinte
  nao e "rodou uma vez"; e deploy/re-smoke do PDF + repeticao em dataset
  real/maior.
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

## Atualizacao 2026-05-16 -- Loop Real Pos-`f2211bb`

Esta auditoria ganhou uma evidencia importante depois do ciclo de docs:
`completed` nao e sinonimo de pipeline valida.

Sequencia factual:

1. `f2211bb` removeu contaminacao por artefatos antigos e reduziu contexto/custo
   do smoke per-phase. O gabarito deixou de falhar por tudo `MISSING_CONTENT`,
   mas a task ainda parou em `analisar_habilidades`.
2. `6b20d43` adicionou retry explicito de validacao multimodal no mesmo
   provider/modelo para extrações inválidas. Isso corrigiu o caso em que
   `gpt54mini001` falhava em `extrair_gabarito` com JSON invalido; nao houve
   troca de modelo.
3. `task_bc6cc84d10ef` completou as 6 etapas no site oficial com Nano nas
   etapas de texto/tool-use e `gpt54mini001` em `extrair_gabarito` e
   `extrair_respostas`.
4. A inspeção dos documentos mostrou falso sucesso semântico: `extracao_respostas`
   (`f10a6ef8a8ca0897`) tinha 7/7 respostas reais, mas a primeira correção
   (`2b7dce2e84108fdc`) dizia que não havia respostas. Isso expôs que
   `CORRIGIR` usava texto cru/alias antigo em vez do JSON `respostas_aluno`.
5. `d4bb2bd` corrigiu o alias: `CORRIGIR` passa a renderizar
   `questoes_extraidas`, `gabarito_extraido` e `respostas_aluno` estruturados.
   O smoke isolado seguinte melhorou a correção (`964f132d5d6eaad8`), mas ainda
   gerou nota com gabarito incompleto.
6. A segunda inspeção mostrou outro P0: `gabarito_extraido`
   (`17573f1218bd6c39`) só tinha resposta real para Q5 e avisos
   `MISSING_CONTENT` para Q1, Q2, Q3, Q4, Q6 e Q7. Corrigir com esse gabarito
   inventa confiança.
7. `3a7dfea` bloqueou `CORRIGIR` quando o gabarito estruturado tem
   `MISSING_CONTENT`/`ILLEGIBLE_*` bloqueante. O smoke `task_5894e6d5858e`
   falhou alto em `corrigir`, sem chamar IA e sem criar documento verde.

Custos observados:

- Smoke full `task_bc6cc84d10ef`: custo medido aproximado `US$ 0.045389`.
- Por etapa principal: `extrair_questoes` `US$ 0.004570`,
  `extrair_gabarito` `US$ 0.009687`, `extrair_respostas` `US$ 0.021602`,
  `corrigir` `US$ 0.001731`, `analisar_habilidades` `US$ 0.003039`,
  `gerar_relatorio` `US$ 0.004760`.
- O smoke bloqueado `task_5894e6d5858e` nao gerou custo novo porque falhou antes
  da chamada de IA.
- `token_usage_backend.supabase.table_available=false` (`PGRST205`) continua:
  falhas sem documento ainda nao sao duraveis ate aplicar
  `backend/migrations/002_create_token_usage.sql`.

Novo criterio de aceite:

- Uma pipeline so pode ser chamada validada se a task terminal, os documentos
  obrigatorios, a matriz provider/modelo, os custos e a inspeção minima de
  conteudo concordarem.
- Correção nao pode rodar com gabarito incompleto. Deve falhar alto e pedir
  gabarito completo/reextração.
- Relatorio e análise gerados sobre correção invalidada nao contam como sucesso
  de produto.

Proximo movimento daquele ciclo:

1. Usar uma atividade com gabarito completo ou corrigir o gabarito da Lista0.
2. Rerodar `extrair_gabarito` e confirmar ausencia de `MISSING_CONTENT`
   bloqueante.
3. Rerodar `corrigir`, `analisar_habilidades` e `gerar_relatorio`.
4. So depois chamar a pipeline Nano+`gpt54mini001` de validada para esse caso.

## Atualizacao 2026-05-16 -- Full Smoke GPT-5.4 Mini Pos-`2cad38a`

O ciclo seguinte escolheu uma fixture simples oficial diferente e destravou o
fluxo OpenAI completo:

1. `5a3daca` alinhou o prompt OpenAI para dual-output via tools.
2. `92bd095` permitiu conteudo JSON estruturado em `create_document`, com
   diagnostico seguro de Responses API.
3. `f6b040c` corrigiu o schema OpenAI invalido de `array` sem `items`.
4. `2cad38a` transformou tool-call sem artefato persistido em erro alto no
   handler, em vez de deixar a etapa acreditar em sucesso.
5. O Render oficial confirmou `2cad38a` por `/api/deploy-info`.
6. `task_a5f0d734f0b3` completou as 6 etapas com `gpt54mini001` na atividade
   `Smoke Paulo Pipeline 2026-05-16`, aluna Diana Omega.
7. A inspeção dos JSONs confirmou conteudo coerente: 4 questoes, gabarito
   completo, 4 respostas da aluna, correcao `8/10`, erro apenas na Q3 de
   porcentagem, analise e relatorio alinhados.
8. A inspeção PDF confirmou arquivos reais, HTTP 200 e texto extraivel, mas
   revelou dois problemas: feedback cortado no PDF de correcao e relatorio com
   `8/10 (75% de proficiencia geral)`. O patch local em `backend/executor.py`
   reforca word-wrap/blocos e separa `nota_final` de `proficiencia_geral`.

Falhas intermediarias que viraram aprendizado:

- `task_04bfc1bbe616`: ainda falhava em `analisar_habilidades`.
- `task_a1977746ef2f`: OpenAI retornou 400 por schema de tool invalido.
- `task_200440ba527e`: o modelo chamou `create_document`, mas o artefato nao
  ficou persistido; `2cad38a` fechou esse falso sucesso.

Custos e documentos do full smoke:

| Etapa | Documento(s) | Tokens | Custo |
|---|---|---:|---:|
| `extrair_questoes` | `f65318c550a76842` | `1150/322` | `US$ 0.002312` |
| `extrair_gabarito` | `70df18512be9c617` | `1813/311` | `US$ 0.002759` |
| `extrair_respostas` | `14ca81d800de2648` | `2042/250` | `US$ 0.002657` |
| `corrigir` | `2c7cd4cf9eb85e57`, `769744b6fff6f3b9` | `18480/2731` | `US$ 0.026149` |
| `analisar_habilidades` | `12b24cd992477eab`, `15579ed3ad2614be` | `10627/2111` | `US$ 0.017470` |
| `gerar_relatorio` | `38686372cb8ea981`, `37b0c86cee879ced` | `16246/3462` | `US$ 0.027763` |

Total aproximado das 6 etapas: `US$ 0.079110`.

Novo movimento correto:

1. Revalidar providers/datasets restantes; o retry PDF/JSON descoberto em
   `task_857c0c3657ef` foi publicado e validado em `task_e389f360b812`.
2. Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para
   tornar duravel o registro de falhas sem documento.
3. Revalidar matriz de providers: Gemini quando quota permitir, Nano sem
   promover `extrair_respostas`, Haiku quando houver credito e GPT-4o explicito.
4. Continuar removendo fallbacks silenciosos e melhorando UI de erros.

## Atualizacao 2026-05-17 -- GPT-4o Sem Falso Verde Nas Etapas Finais

O loop seguinte atacou GPT-4o como modelo explicito, nao como fallback. O
objetivo era descobrir se o provider OpenAI classico ainda conseguia cumprir o
contrato moderno de tools, JSON, PDF, custo e erro alto.

Sequencia de correcoes:

1. `f7bca4c` passou chamadas OpenAI com tool forçada para Responses API.
2. `33829bc` adicionou retry de JSON invalido em `analisar_habilidades`.
3. `fdf1829` estendeu schema minimo para `correcao`,
   `analise_habilidades` e `relatorio_final`.
4. `3af2918` fez artefato em `status=erro` deixar de contar como JSON/PDF
   presente, marcou todos os JSONs invalidos do run e marcou extras/stale como
   erro.
5. `00eb26b` proibiu caminhos absolutos e `open(..., "wb")` nos prompts da
   tool de PDF, destravando erro `E2B_SECURITY File write outside sandbox`.
6. `3e6be20` adicionou validação de PDF de correcao contra Feedback Geral
   truncado.

Smokes que guiaram o patch:

- `task_738c5247b97f`: `corrigir` passou, mas `analisar_habilidades` falhou por
  JSON array na raiz (`9c9653a86f447f9a`), custo `US$ 0.035130`.
- `task_82763c17bac3`: completou, mas inspeção achou arrays ainda concluídos em
  `correcao` e `relatorio_final`. Isso virou `3af2918`.
- `task_8661e1034c6a`: falhou alto em `gerar_relatorio` por
  `E2B_SECURITY File write outside sandbox`. Isso virou `00eb26b`.
- `task_4880fd35b86c`: completou em `00eb26b`, mas o PDF de correcao cortou
  Feedback Geral. Isso virou `3e6be20`.
- `task_386f96bbf158`: completou em `3e6be20` com os artefatos oficiais
  legiveis e coerentes.

Resultado final do smoke GPT-4o `task_386f96bbf158`:

| Etapa | Artefatos oficiais | Erros esperados preservados | Tokens | Custo |
|---|---|---|---:|---:|
| `corrigir` | PDF `e5ca0900654ed0e9`, JSON `e8269ff428d50802` | JSON arrays e PDF anterior inconsistente em `status=erro` | `66527/6861` | `US$ 0.234928` |
| `analisar_habilidades` | PDF `9b8ef8b03388a741`, JSON `58ddf040c628863c` | JSONs extras marcados `stale_tool_artifact` | `47566/4498` | `US$ 0.163895` |
| `gerar_relatorio` | PDF `4d4a42b77010d27a`, JSON `30c5a9c3225f1ed5` | JSON arrays, JSON stale e PDF `nota_final=N/A` em erro | `39023/4062` | `US$ 0.138178` |

Total aproximado das tres etapas GPT-4o: `US$ 0.536...`. O endpoint
`/api/custos/status` continua apontando `token_usage_backend.durable=false` por
`PGRST205`; portanto o custo medido aparece nos documentos/cost summary, mas o
registro duravel Supabase ainda depende da migration.

Interpretação:

- GPT-4o volta a ✅ somente para `corrigir`, `analisar_habilidades` e
  `gerar_relatorio` nesta fixture simples.
- A pipeline completa de 6 etapas com GPT-4o ainda nao esta validada.
- O comportamento arquitetural melhorou: arrays, PDFs divergentes, PDFs
  truncados, PDF com `N/A` e artefatos extras nao ficam mais verdes.

## Atualizacao 2026-05-17 -- Gemini 3 Flash `extrair_gabarito`

Depois do ciclo GPT-4o, o loop voltou para a matriz de providers. O alvo foi um
P0 antigo: Gemini 3 Flash tinha `extrair_gabarito` reclassificado como falha de
conteudo porque retornou todas as respostas como `MISSING_CONTENT`.

Smoke oficial:

- Task: `task_c08f3d478aad`
- Runtime Render: `3e6be20`
- Modelo: `gem3flash001` (`google/gemini-3-flash-preview`)
- Etapa: `selected_steps=["extrair_gabarito"]`
- Documento: `92e5e77b24874ad1`
- Tokens/custo: `2040/507`, `US$ 0.001220`

Inspeção:

- JSON raiz e objeto.
- Campo `respostas` tem 4 itens reais.
- Respostas conferidas: Q1 `x = 5`, Q2 `34`, Q3 `30`, Q4 `20 cm2`.
- Nao houve `MISSING_CONTENT` no resultado inspecionado.

Interpretação:

- Gemini 3 Flash volta a ✅ em `extrair_gabarito` para a fixture simples Diana.
- Isso nao fecha Gemini como pipeline completa: a sequencial anterior parou em
  `corrigir` por quota `429`, entao ainda precisa rerun completo quando quota
  permitir.
- O custo medido apareceu em `/api/custos/resumo`; a persistencia duravel
  Supabase continua bloqueada por `PGRST205`.

## Atualizacao 2026-05-17 -- `aff2180`, Schema De Correção E GPT-5.4 Mini Full

Este ciclo mostrou por que o loop nao pode parar no primeiro `completed`.

Sequencia factual:

1. `629c4ee` foi publicado e confirmado no Render. Ele corrigiu uma validação
   estreita demais: o PDF Gemini trazia o texto completo do parecer, mas com o
   titulo "Parecer Pedagógico Geral", nao "Feedback Geral". A regra correta
   passou a validar o conteudo do `feedback_geral`, sem aceitar truncamento.
2. Em `629c4ee`, Gemini 3 Flash completou a pipeline full
   `task_c9302f341734`, mas a auditoria achou falso verde de schema:
   `corrigir` gerou JSON `54c7fafd5569cca2` com
   `feedback_geral_texto`/`feedback_geralSmall`, sem `feedback_geral`.
3. `aff2180` foi publicado e confirmado no Render. Ele tornou obrigatorios no
   JSON de `CORRIGIR`: `feedback_geral`, `total_acertos`, `total_erros`,
   `_avisos_documento` e `_avisos_questao`.
4. Reruns Gemini em `aff2180` nao conseguiram validar o schema novo por quota
   Google `429`: full `task_0cbc99255c7e` falhou em `extrair_questoes`;
   correção-only `task_6347f5e0d311` e `task_26412081ac9f` falharam em
   `corrigir`. O erro expôs limite free-tier
   `generate_content_free_tier_requests`, `limit: 20`, modelo
   `gemini-3-flash`.
5. No mesmo runtime, GPT-5.4 Mini completou full pipeline
   `task_299dd8a00517` com schema endurecido e custo medido.

Artefatos GPT-5.4 Mini `task_299dd8a00517`:

| Etapa | Artefatos | Tokens | Custo |
|---|---|---:|---:|
| `extrair_questoes` | JSON `6510078afa7dcc4b` | `1150/489` | `US$ 0.003063` |
| `extrair_gabarito` | JSON `1f2e9af35f895de1` | `1903/295` | `US$ 0.002755` |
| `extrair_respostas` | JSON `98dc9d287f28893e` | `2129/455` | `US$ 0.003644` |
| `corrigir` | PDF `54bbdd06a48f9376`, JSON `f4f5a5d1f71a262f` | `23462/3876` | `US$ 0.035039` |
| `analisar_habilidades` | PDF `71c5cd58b3a11403`, JSON `6972964717580587` | `12285/2154` | `US$ 0.018907` |
| `gerar_relatorio` | PDF `092a5ac44779a0e7`, JSON `c9552a74276b38ac` | `19398/3778` | `US$ 0.031550` |

Total aproximado: `US$ 0.094958`.

Interpretação:

- GPT-5.4 Mini segue como melhor provider validado para a fixture simples
  Diana: 6 etapas, JSONs coerentes, PDF/JSON de correção coerentes, custo
  medido por etapa.
- Gemini 3 Flash nao deve ser marcado como full confirmado pos-`aff2180`; ele
  esta bloqueado por quota para revalidar as etapas finais com o schema novo.
- O custo ainda nao e duravel no Supabase: `/api/custos/status` segue com
  `token_usage_backend.durable=false` e `PGRST205`.
- Lacunas de qualidade ainda abertas: PDF de correção GPT-5.4 Mini mostrou
  "Aluno: Não informado"; `extrair_respostas` incluiu uma observacao
  contraditoria na Q1 apesar de extrair `x = 5` corretamente.

## Atualizacao 2026-05-17 -- Nano `extrair_respostas` Na Fixture Simples

Depois do full smoke GPT-5.4 Mini, o loop reavaliou o ponto mais fraco do
GPT-5 Nano: `extrair_respostas`.

Smoke oficial:

- Task: `task_ff7eeda28964`
- Runtime Render: `aff2180`
- Modelo: `gpt5nano001` (`openai/gpt-5-nano`)
- Etapa: `selected_steps=["extrair_respostas"]`
- Documento: `4175e0e7476931d7`
- Tokens/custo: `2129/2261`, `US$ 0.001011`

Inspeção:

- JSON raiz e objeto.
- `respostas` tem 4 itens reais.
- Respostas conferidas: Q1 `x = 5`, Q2 `34`, Q3 `25`, Q4 `20 cm2`.
- `questoes_respondidas=4`, `questoes_em_branco=0`, sem `ilegivel=true`.

Interpretação:

- Nano melhorou na fixture simples Diana e nao deve continuar classificado como
  falha absoluta em `extrair_respostas`.
- A classificacao correta ainda e parcial: o historico em PDF/lista maior teve
  tudo `ilegivel=true`, tudo `em_branco=true`, inferencia suspeita e scan
  majoritariamente vazio. Precisa repetir em dataset maior antes de promover a
  etapa para ✅ geral.

## Atualizacao 2026-05-17 -- GPT-4o Extracoes Sem Julgamento Em `raciocinio_parcial`

O loop fechou a lacuna das tres primeiras etapas do GPT-4o.

Primeiro smoke:

- Task: `task_d6506d2f2ccc`
- Runtime: `aff2180`
- Resultado: `completed`
- Problema encontrado: `extrair_respostas` extraiu os valores corretos, mas
  escreveu julgamentos/especulacoes em `raciocinio_parcial`, incluindo uma
  avaliacao errada da Q2.

Correcoes:

- `2885da7`: bloqueia linguagem de correcao/julgamento em
  `raciocinio_parcial` da etapa `EXTRAIR_RESPOSTAS`.
- `99b8c3c`: bloqueia linguagem especulativa como "provavelmente",
  "possivelmente", "deve ter" e "parece que"; se so ha resposta final visivel,
  `raciocinio_parcial` deve ser `null`.

Rerun oficial:

- Task: `task_013ad41fd3ed`
- Runtime Render: `99b8c3c`
- `extrair_questoes`: JSON `69dd5c07acb2ff52`, `1151/381`, `US$ 0.006687`
- `extrair_gabarito`: JSON `98dbaf8613ec9fc3`, `1718/282`, `US$ 0.007115`
- `extrair_respostas`: JSON `8019a2a2c5fc3cea`, `2115/292`, `US$ 0.008207`

Inspeção:

- Questões: 4 itens, pontuação total `10.0`.
- Gabarito: Q1 `x = 5`, Q2 `34`, Q3 `30`, Q4 `20 cm2`.
- Respostas da aluna: Q1 `x = 5`, Q2 `34`, Q3 `25`, Q4 `20 cm2`.
- `raciocinio_parcial=null` nas quatro questões, correto para uma prova com
  apenas resposta final visivel.

Interpretação:

- GPT-4o fica ✅ nas seis etapas individualmente para a fixture simples Diana:
  tres etapas finais em `task_386f96bbf158` e tres extracoes em
  `task_013ad41fd3ed`.
- Ainda falta uma task full de 6 etapas GPT-4o e datasets maiores. Nao promover
  para confiabilidade geral sem esses smokes.

## Atualizacao 2026-05-17 -- Haiku Continua Bloqueado Por Créditos

Foi feita uma verificação mínima pelo endpoint oficial de settings:

- Endpoint: `POST /api/settings/models/588f3efe7975/testar`
- Resultado HTTP do site: `200`
- Payload: `success=false`
- Erro Anthropic: `invalid_request_error`
- Mensagem: saldo de créditos baixo demais para acessar a API Anthropic.

Interpretação:

- Claude Haiku 4.5 continua 🚫 bloqueado por crédito externo.
- Nao faz sentido rodar pipeline Haiku ate a conta Anthropic ser recarregada.

## Atualizacao 2026-05-17 -- Dashboard Grita Custos Nao Duraveis

O backend ja tinha sido corrigido em `460643f` para responder
`/api/custos/status` com `ok=false` enquanto `public.token_usage` nao existir no
Supabase. O problema seguinte era de produto: o usuario ainda precisava abrir
endpoint/terminal para perceber o bloqueio.

Correção publicada:

- Commit: `54d083e`
- Deploy: `/api/deploy-info` confirmou `54d083e` com
  `source=RENDER_GIT_COMMIT`.
- Frontend: `frontend/index_v2.html` criou `dashboard-cost-alerts`, consulta
  `/api/custos/status?limit=80` no dashboard e mostra "Custos não duráveis"
  quando `token_usage_backend.durable=false`,
  `custos_persistencia_status=parcial_sem_token_usage_duravel` ou alerta
  `token_usage_not_durable` aparecerem.
- Teste: `backend/tests/unit/test_frontend_cost_status_ui.py` trava a presença
  do endpoint, do container, dos checks de durabilidade e da mensagem visivel.

Smokes oficiais:

- `./scripts/check_deploy.sh 54d083e`: passou.
- `/api/health`: `healthy`, `supabase=true`.
- `/api/custos/status?limit=80`: `ok=false`,
  `custos_persistencia_status=parcial_sem_token_usage_duravel`,
  `runs_precificados=37`, `runs_bloqueados=0`, `durable=false`, alerta
  `token_usage_not_durable`.
- HTML live: contem `dashboard-cost-alerts`, `/custos/status?limit=80`,
  `Custos não duráveis` e `parcial_sem_token_usage_duravel`.

Interpretação:

- O bloqueio de custo ainda nao foi resolvido: a migration Supabase continua
  faltando.
- O erro deixou de ser invisivel na interface principal. Isso fecha uma parte
  da UI de erros, mas nao substitui os alertas por aluno/etapa/provider que
  ainda faltam.

## Atualizacao 2026-05-17 -- GPT-4o Full Smoke Oficial

Motivo:

- GPT-4o tinha sido revalidado por etapas, mas faltava uma pipeline completa de
  6 etapas depois dos guards de schema, PDF/JSON e custos.

Smoke:

- Task: `task_68b19146a95b`
- Runtime: `54d083e`
- Modelo: `180b8298a279` (`openai/gpt-4o`)
- Fixture: Diana Omega, atividade `f68d57a9a339081f`
- Resultado da task: `completed` nas 6 etapas.

Artefatos finais:

| Etapa | Documento(s) | Tokens | Custo |
|---|---|---:|---:|
| `extrair_questoes` | `5adf51fcd1adc4c0` | `1151/409` | `US$ 0.006967` |
| `extrair_gabarito` | `7c097774fce46472` | `1774/284` | `US$ 0.007275` |
| `extrair_respostas` | `9e6d562d51a6f6e4` | `2167/292` | `US$ 0.008337` |
| `corrigir` | `b2abc9a73c8dc3a8` / `8911e1a3acae4ad2` | `23696/2916` | `US$ 0.088400` |
| `analisar_habilidades` | `21f2d7d065aeafe5` / `72203996b8960b50` | `37758/3279` | `US$ 0.127185` |
| `gerar_relatorio` | `bbc5963d712a7f1e` / `f12312b96e3725a3` | `21482/2250` | `US$ 0.076205` |

Total aproximado: `US$ 0.314369`.

Inspecao:

- Questões e gabarito: 4 itens, valores esperados.
- Respostas da aluna: `x = 5`, `34`, `25`, `20 cm2`,
  `questoes_respondidas=4`, sem `ilegivel`.
- Correção final: `nota_final=8.0`, notas por questão `3.0`, `3.0`, `0.0`,
  `2.0`.
- Habilidades: proficiencia geral `8.0`, porcentagem como area de atenção.
- Relatorio final: `nota_final=8.0`; PDF de correção e PDF de relatório
  confirmados via `pdftotext` com `Nota Final: 8.0`.

Observacao importante:

- As etapas de tools geraram documentos intermediarios `status=erro` por
  `json_schema_validation` antes dos documentos finais. Isso e retry explicito
  no mesmo modelo, com erro visivel e custo registrado. Nao e fallback
  silencioso. A UI ainda precisa deixar essas tentativas visiveis por
  aluno/etapa.

## Atualizacao 2026-05-17 -- Gemini 2.5 Flash: Extracoes OK, Tools Falham Alto

Contexto:

- Gemini 3 Flash e Gemini 2.5 Pro retornaram Google `429` no teste de conexão.
- Gemini 2.5 Flash e Gemini 2.5 Flash Lite retornaram `success=true`.
- Anthropic Haiku/Sonnet continuam bloqueados por crédito baixo.

Smoke:

- Task: `task_f1f1511f21d5`
- Runtime: `54d083e`
- Modelo: `gem25flash001` (`google/gemini-2.5-flash`)
- Resultado: task `failed`; extracoes `completed`, `corrigir=failed`, etapas
  seguintes `pending`.

Evidencia das extracoes:

| Etapa | Documento | Tokens | Custo | Inspecao |
|---|---|---:|---:|---|
| `extrair_questoes` | `4d5c5abdc1203f2b` | `1188/567` | `US$ 0.000518` | 4 questoes, pontuação `3/3/2/2` |
| `extrair_gabarito` | `d27793f610a3696c` | `2114/318` | `US$ 0.000508` | `x = 5`, `34`, `30`, `20 cm2` |
| `extrair_respostas` | `ffed15b8003145e9` | `2456/336` | `US$ 0.000570` | `x = 5`, `34`, `25`, `20 cm2`, sem `ilegivel` |

Erro de tools:

- `tools: Saída obrigatória incompleta: JSON via create_document, PDF via
  execute_python_code. Nenhum PDF/JSON será inventado por fallback automático; o
  modelo solicitado deve produzir os artefatos exigidos ou a etapa falha.`

Interpretação:

- Gemini 2.5 Flash e barato e funcionou nas extracoes da fixture simples.
- O provider/modelo nao esta pronto para pipeline completa porque o contrato de
  tool-use de `CORRIGIR` nao foi cumprido.
- O comportamento atual do executor esta correto: falha alta, sem PDF/JSON
  inventado, sem trocar provider.

## Atualizacao 2026-05-17 -- Gemini 2.5 Flash: Tool-use Corrigido, Quota Bloqueia Revalidacao

O ciclo seguinte atacou o erro real, nao o contornou:

- Fonte tecnica usada: documentacao oficial Google Gemini Function Calling,
  especialmente `toolConfig.functionCallingConfig.mode=ANY` e
  `allowedFunctionNames`:
  `https://ai.google.dev/gemini-api/docs/function-calling`.
- Commit `854cec7`: o `ChatService` passou a enviar `toolConfig` para Google na
  primeira iteracao de tools; o executor passou a usar o mesmo fluxo faseado de
  OpenAI para Google: primeiro `create_document`, depois `execute_python_code`.
- Testes do ciclo `854cec7`: `test_d_t2_google_tool_use.py`,
  `test_e_t2_retry_partial_output.py`, `test_cost_tracking.py` e
  `test_stage_tool_pdf_quality.py` passaram.
- Deploy: `/api/deploy-info` confirmou `854cec7`.
- Smoke `task_cdef8694893e`: Gemini 2.5 Flash passou a chamar tools e criou
  JSON/PDF de correcao; o bloqueio restante virou consistencia PDF/JSON de
  feedback, nao mais ausencia de tools.
- Commit `b07472f`: o validador de consistencia aceitou `Feedback Geral`
  substantivo e parafraseado quando ele cobre semanticamente o JSON e nao esta
  truncado; feedback curto/truncado continua bloqueado.
- Testes do ciclo `b07472f`: `test_stage_tool_pdf_quality.py`,
  `test_d_t2_google_tool_use.py`, `test_e_t2_retry_partial_output.py` e
  `test_cost_tracking.py` passaram.
- Deploy: `/api/deploy-info` confirmou `b07472f`.
- Rerun full `task_6bba32964706`: chegou novamente a `corrigir`, mas falhou por
  Google `429 RESOURCE_EXHAUSTED`.
- Rerun isolado `task_f9b76153875a`: tambem falhou por Google `429`; o JSON
  parcial `338b25f9c0f74415` ficou `status=erro` e nao pode ser contado como
  etapa concluida.

Interpretação atualizada:

- O bug de "Gemini nao chama tools" foi corrigido no codigo e publicado.
- A matriz ainda nao pode marcar Gemini 2.5 Flash como pipeline-ready, porque a
  revalidacao final de `CORRIGIR`/tools foi bloqueada por quota.
- O comportamento correto enquanto isso e registrar bloqueio de provider/quota,
  nao rerodar em loop cego e nao trocar para outro modelo em silencio.

## Atualizacao 2026-05-17 -- Erro Por Aluno/Etapa Na Sidebar

Problema:

- O backend ja falhava alto e o run tinha `task.error`, mas cada etapa na
  sidebar era apenas `pending/running/completed/failed`.
- Isso obrigava o usuario a abrir terminal ou endpoint para saber qual etapa,
  aluno, provider/codigo ou documento faltante causou o bloqueio.

Mudanca publicada:

- Commit funcional `98fafc9`.
- `backend/routes_tasks.py`: `register_pipeline_task()` cria
  `stage_errors={}` por aluno; `update_stage_progress()` aceita `error`,
  armazena payload por etapa quando o status e `failed` e limpa erro antigo
  quando a etapa volta a `running`, `completed` ou `pending`.
- `backend/executor.py`: cada falha de etapa envia mensagem, codigo,
  retryability, provider/modelo e documentos faltantes quando existirem.
- `frontend/index_v2.html`: `renderTarefasTree()` le `aluno.stage_errors` e
  renderiza `tarefa-stage-error` abaixo da etapa falha.

Validacao:

- Local: `py_compile`, `git diff --check` e suite focada com `154 passed`.
- Deploy: `/api/deploy-info` confirmou `98fafc9`; `/api/health` respondeu
  `healthy`; HTML live contem `stage_errors`, `renderStageError` e
  `tarefa-stage-error`.
- Smoke sem IA: `task_7362d0fb1939` rodou somente `extrair_respostas` para
  aluno inexistente e falhou antes de provider, expondo:
  `students.smoke_sem_prova_stage_error.stage_errors.extrair_respostas.mensagem`
  = "Aluno smoke_sem_prova_stage_error nao tem prova_respondida enviada."

Estado:

- Primeira camada de UI de erro por aluno/etapa esta oficial.
- Ainda falta repetir o padrao em telas de resultado/historico e custos
  persistidos, para que o usuario nunca precise inferir falha por ausencia de
  documento.

## Atualizacao 2026-05-17 -- Relatorio Sem Nota Confiavel Falha Alto

Problema:

- O P5 antigo era uma contencao: calculava `nota_final` por caminhos ordenados e
  usava `N/A` quando nada numerico era confiavel.
- Pela regra P0, isso nao pode ser aceite final. Um relatorio com `nota_final`
  ausente deve bloquear antes da IA, nao pedir para o modelo completar uma nota
  inventada.

Mudanca publicada:

- Commit funcional `ad7e00e`.
- `backend/models.py`: novo tipo `ERRO_NOTA_FINAL_INDETERMINADA`.
- `backend/executor.py`: `_calcular_nota_final_de_correcoes()` retorna `None`
  quando nao ha nota numerica confiavel; `GERAR_RELATORIO` bloqueia antes de
  `executar_com_tools()` se nao encontra `nota_final`, `nota`,
  `questoes[].nota` ou `correcoes[].nota`; `_preparar_variaveis_texto()` nao
  injeta mais `N/A` para `GERAR_RELATORIO`.
- `backend/tests/unit/test_erro_pipeline.py`: testes agora provam que JSON
  invalido/sem nota retorna `None` e que relatorio sem nota falha com
  `_erro_pipeline.tipo=NOTA_FINAL_INDETERMINADA`, sem chamada de IA.

Validacao:

- Local: `py_compile`, `git diff --check` e suite focada com `101 passed`.
- Suite ampliada: relatório/tool-use, prompts, schema, visualizador e avisos com
  `164 passed, 3 skipped`.
- Deploy: `/api/deploy-info` confirmou `ad7e00e`; `/api/health` respondeu
  `healthy`.
- Smoke sem IA: `task_d4947f5a3594` rodou apenas `gerar_relatorio` para aluno
  inexistente e falhou antes de provider com
  `stage_errors.gerar_relatorio.tipo=DOCUMENTO_FALTANTE`, preservando
  `documentos_faltantes=["correcoes","analise_habilidades"]`.

Estado:

- `nota_final=N/A` nao e mais saida aceitavel do executor de relatorio.
- PDF auto-fallback nao esta aberto como bug de runtime atual; existe guarda de
  teste dedicada em `dc5884f`.
- JSON embrulhado em Markdown/prosa nas etapas nao e mais aceito como sucesso
  verde depois de `0d5ab9d`.
- Ainda restam outras frentes anti-fallback: ampliar schema minimo runtime para
  ANALISAR/GERAR, artefatos parciais verdes e status historico que precisa
  obedecer `status=erro`.

## Trabalho Aberto Desta Auditoria

Esta auditoria nao encerra o loop tecnico. Ela deixa o proximo trabalho mais
claro. O que ainda existe para fazer:

| Item | Tipo | Por que ainda falta |
|---|---|---|
| Ciclo anti-fallback | Codigo/testes | `nota_final=N/A` em relatório foi fechado em `ad7e00e`; PDF auto-fallback foi reclassificado como guardado em `dc5884f`; JSON embrulhado em Markdown/prosa foi bloqueado em `0d5ab9d`; retorno Path 2 basico foi melhorado em `c870ed4`; schema minimo runtime de `CORRIGIR` foi bloqueado em `45f5cf8`; smoke oficial `task_42e3b303c39a` confirmou sucesso real de `corrigir` com PDF intermediario inconsistente marcado como erro; `4094bda` adicionou cobertura para `ANALISAR_HABILIDADES`/`GERAR_RELATORIO` runtime fora do schema; ainda restam parciais/duplicatas/stale e smokes de matriz. |
| Settings de modelos | Codigo/testes/deploy | `from-catalog` deu 500 e create ignorou capabilities no site live; patch `b16e051` ja foi deployado e retestado; cadastro por API sumiu no deploy, mas o modelo versionado `gpt54mini001` apareceu no site em `be19b7e` e passou teste de conexao. |
| Metadata/custo real | Codigo/testes/deploy | Metadata e endpoints existem no site; full smoke GPT-5.4 Mini mediu custo por etapa; smoke `task_42e3b303c39a` mediu `26251/4582` tokens e `US$ 0.040307`; Supabase `token_usage` segue ausente (`PGRST205`), `local_record_count=0` depois de deploy e custo de falha sem documento ainda nao e duravel. |
| Provider revalidation | Smoke/producao | Matriz Doc 12 registra GPT-5.4 Mini full smoke em fixture simples, GPT-4o full smoke (`task_68b19146a95b`) e Gemini 2.5 Flash com extracoes OK/tool-use corrigido mas bloqueado por quota; continua incompleta ate novos smokes por provider/rota/dataset. |
| PDFs/UI GPT-5.4 Mini/GPT-4o | Codigo/testes/deploy/smoke | `task_a5f0d734f0b3` completou 6 etapas, JSONs passaram inspeção semantica inicial e PDFs existem; `0ac92f0` corrigiu parte do layout, mas `task_605512496b0d` provou divergencia PDF/JSON; `2052a01` transformou essa divergencia em erro alto; `3a77a17` validou retry explicito do PDF; `3e6be20` bloqueia Feedback Geral truncado; GPT-4o passou as etapas finais com artefatos ruins marcados como erro; `task_42e3b303c39a` confirmou PDF final coerente em `corrigir`. Ainda falta repetir em datasets maiores e melhorar UI de erro para o usuario final. |
| Gabarito incompleto bloqueia correção | Codigo/testes/deploy/smoke | `3a7dfea` bloqueia `CORRIGIR` com `MISSING_CONTENT` no gabarito; continua importante para datasets como Lista0, embora a fixture Diana tenha completado. |
| UI de erros | Produto/frontend | Sidebar ja mostra a causa por aluno/etapa desde `98fafc9`; ainda falta resultado/historico e mensagens completas para provider/custo. |
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
