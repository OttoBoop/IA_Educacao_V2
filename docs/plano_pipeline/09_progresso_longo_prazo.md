# Painel Vivo Paulo -- NOVO CR

**Atualizado:** 2026-05-17
**Responsavel operacional:** Paulo
**Status geral:** o servico oficial Render
`srv-d5t8gbh4tr6s738fr3s0` (`IA_Educacao_V2`, branch `main`, URL
`https://ia-educacao-v2.onrender.com`) tem como codigo funcional mais recente
confirmado o commit `ae04982` (`fix: expose cost totals by pipeline stage`),
validado por `/api/deploy-info`, `/api/health` e
`./scripts/check_deploy.sh ae04982250877dc12da5a01be16edc2eaa43b5bd`. Se
`/api/deploy-info` apontar commit documental posterior, comparar com este hash
funcional antes de concluir que houve nova mudanca de runtime. O lote funcional
publicado ate esse hash faz resultado, historico, pendencias e status de
pipeline obedecerem `status=erro` e conteudo avaliavel: documento em erro nao
conta como progresso, correcao sem questao/correcao com nota nao vira
`completo=true`, retry concluido pode fechar a etapa sem esconder erro anterior,
e documentos de erro continuam visiveis com provider/modelo/tokens/causa.
O mesmo lote corrigiu as rotas agregadas de ranking/estatisticas, que antes
eram capturadas pela rota dinamica de aluno, e preservou medias legitimas `0.0`
no dashboard/historico/comparativos. O ciclo `147296d` reduziu o dashboard da
turma Lista0 de cerca de 85s para 1.4s ao reaproveitar ranking em lote, sem
reabilitar resultados sem itens avaliaveis.
O ciclo `22f6f31` trocou o modelo padrao versionado de Claude Haiku 4.5
(bloqueado por credito Anthropic) para GPT-5.4 Mini (`gpt54mini001`) e confirmou
o default vivo em `/api/settings/status` e `/api/settings/models`.
O ciclo `48407f2` adicionou resumo estruturado para erros de provider em
`/api/custos/resumo`, expondo `erro_codigo`, `erro_provider_status`,
`erro_provider_modelo`, `erro_categoria` e `erro_resumo` curto sem depender do
JSON bruto gigante.
O ciclo `50fb1d7` deixou `/api/custos/status` expor `error_code=PGRST205`,
`missing_migration=true` e `migration_path=backend/migrations/002_create_token_usage.sql`
para o bloqueio Supabase `token_usage`.
O ciclo `e2260d2` fez o dashboard ler esses campos no objeto
`token_usage_backend.supabase` e mostrar o codigo/caminho da migration no site,
sem exigir terminal para entender o bloqueio.
O ciclo `ae04982` adicionou `por_etapa` em `/api/custos/resumo` e confirmou o
agregado live: `correcao` segue como a maior fatia de custo, seguida por
`analise_habilidades` e `relatorio_final`.
GPT-4.1, GPT-5.4 Mini, GPT-4o e GPT-5 Nano seguem referencias OpenAI na fixture
Diana; Nano passou `extrair_respostas`, `corrigir`, `analisar_habilidades` e
`gerar_relatorio` nessa fixture simples, mas continua parcial por historico de
qualidade em dataset maior e por ressalva nova de schema de aviso composto. O
sweep mais recente confirmou OpenAI OK, Gemini Flash/Flash Lite/3 Flash OK em
conexao simples, mas `corrigir` com Gemini 2.5 Flash ainda falha alto por quota
`429`; Gemini 2.5 Pro tambem esta bloqueado por quota, Anthropic bloqueado por
credito e Ollama indisponivel no Render. Supabase `token_usage` continua
ausente (`PGRST205`), deixando custo duravel como gate real.

Atualizacao Lista0 de 2026-05-17: a atividade real `Lista0`
(`126e8b5ad7dd6d59`) tem documentos base cadastrados e 63 alunos
(`38` com prova, `34` com correcao), mas a inspeção dos PDFs mostrou um bloqueio
de dado para smoke integral honesto. O enunciado `5dc75513e958c25b` lista os
exercicios 1 a 7; o gabarito `dbfe3a77a631489f` e explicitamente
`Gabarito -- Lista 0, Exercicio 5` e contem apenas a solucao do exercicio 5.
Conclusao operacional: a Lista0 so pode ser usada como caso de correcao se o
escopo for declarado como exercicio 5; para validar a pipeline integral da
atividade inteira, falta gabarito completo ou reextracao/cadastro correto. Nenhuma
chamada de IA foi feita neste ciclo; o objetivo foi evitar gasto em smoke que
nasceria invalidado pelo dado.

Atualizacao OpenAI/catalogo de 2026-05-17: consulta aos docs oficiais da OpenAI
confirmou `gpt-5.5` como linha mais recente, com `reasoning.effort` e preferencia
por Responses API em workflows de raciocinio/tool-use. O ciclo corrigiu um risco
de modelo fantasma/parametro errado: `gpt-5.2`, `gpt-5.2-pro`, `gpt-5-pro` e a
familia GPT-5.4/5.5 entram como reasoning sem `temperature`; variantes `-pro`
tambem sao reconhecidas pelo provider legado e pelo frontend; o slug inexistente
`gpt-5-image` saiu do catalogo textual. Validacoes locais: `py_compile`,
`git diff --check`, `test_model_manager.py` (55), `test_d_t1_openai_tool_use.py`
com `test_cost_tracking.py` (38) e `test_providers.py` (11). No mesmo ciclo, o
catalogo foi ajustado para limites oficiais de contexto/output e capabilities
das variantes `-pro`. Publicacao: commit `fdf0cbd`, push para `origin/main`,
Render confirmado em 150s por `wait_deploy.sh`/`check_deploy.sh`. Smokes live:
`/api/settings/model-catalog/openai/gpt-5.5`, `gpt-5.5-pro`, `gpt-5.4-pro`,
`gpt-5.2-pro` e `gpt-5-pro` retornaram metadata esperada; `gpt-5-image`
retornou `404`; `/api/settings/model-catalog/calculate-cost` para
`openai/gpt-5.4-mini` retornou `cost_per_request=0.003`, `daily_cost=0.09`;
`/api/chat` com `gpt54mini001` retornou JSON valido e `tokens_used=409`. Nenhum
smoke de pipeline integral foi feito neste ciclo porque a Lista0 segue bloqueada
por gabarito parcial.

Atualizacao pipeline OpenAI de 2026-05-17 no runtime `fdf0cbd`: o smoke oficial
`task_0559fc57a3cc` rodou a etapa `corrigir` na fixture Diana
(`f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`) com `model_id=gpt54mini001`,
`force_rerun=true` e `selected_steps=["corrigir"]`. A task completou sem
`stage_errors`. Artefatos: JSON `92737f5ba69ca2d4` e PDF
`bb6522992d2fe7d4`, ambos `status=concluido`, provider/modelo
`openai/gpt-5.4-mini`, `tokens_entrada=24593`, `tokens_saida=4061`,
`cost_run_id=tool_9c04a9d6a4af`, custo `US$ 0.036719`. O retry explicito
marcou o PDF intermediario `067f4db99040043b` como `status=erro` por
`pdf_json_consistency`; isso e comportamento correto, nao fallback silencioso.
`/api/custos/status?limit=80` passou a `runs_analisados=44`,
`runs_precificados=42`, mas segue `ok=false` por `token_usage_not_durable` /
Supabase `PGRST205`.

Atualizacao provider sweep de 2026-05-17 no runtime `fdf0cbd`: o endpoint
`/api/settings/models/{id}/testar` confirmou disponibilidade atual sem trocar
modelo em silencio. OpenAI OK: `gpt54mini001` respondeu `OK`, modelo
`gpt-5.4-mini`, `42` tokens; `gpt5nano001` respondeu `OK`, modelo
`gpt-5-nano`, `38` tokens. Google bloqueado por quota: `gem25flash001`,
`gem25lite001` e `gem3flash001` retornaram `success=false`, erro
`Erro API Google: 429 - Limite de requisições atingido`. Anthropic bloqueado por
credito: `588f3efe7975` (Haiku 4.5) e `4eaeb5105f5d` (Sonnet 4.5) retornaram
HTTP 200 do endpoint, mas `success=false` com API Anthropic `400` e mensagem de
saldo insuficiente. Ollama no Render segue indisponivel: `ollama-llama3`
retornou `All connection attempts failed`.

Atualizacao chat/providers de 2026-05-17 no runtime `c53fae6`: o smoke oficial
`POST /api/chat` com GPT-5.4 Mini (`gpt54mini001`) retornou HTTP 200, JSON
parseavel e sem marcador de debug (`tokens_used=413`). O mesmo smoke com
Gemini 3 Flash (`gem3flash001`) retornou HTTP 429 estruturado, com
`provider=Google`, `provider_status_code=429` e `retryable=true`; isso e quota
de provider, nao falha silenciosa nem motivo para trocar modelo. Claude Haiku
4.5 (`588f3efe7975`) retornou HTTP 400 estruturado, com
`provider=Anthropic`, `provider_status_code=400`, `retryable=false` e mensagem
de credito Anthropic insuficiente. A pendencia de custo duravel segue igual:
`/api/custos/status?limit=80` continua `ok=false` por `public.token_usage`
ausente no Supabase (`PGRST205`).

Atualizacao UI/API de erro em 2026-05-17 no runtime `9ab53df`: o handler global
de `HTTPException` nao embrulha mais `detail` estruturado como
`error.message=<objeto>`. O smoke live de chat confirmou o novo formato:
Gemini 3 Flash retorna HTTP 429 com `error.message` textual,
`error.provider=Google`, `error.provider_status_code=429`, `retryable=true`;
Haiku retorna HTTP 400 com `error.provider=Anthropic`, `retryable=false`; GPT-5.4
Mini continua HTTP 200 com JSON parseavel. O HTML live contem
`provider_status_code`, `retry possível`, `stageError.erro_codigo` e
`formatApiErrorMessage`, evitando toast/erro visual com objeto cru.

Atualizacao custos/provider em 2026-05-17 no runtime `3fce335`: commits
`1454e68` e `3fce335` fecharam a lacuna de tokens parciais em erro de provider
depois de tool-use. Validacoes locais: `py_compile` de `backend/chat_service.py`
e `backend/executor.py`; `git diff --check`; `test_cost_tracking.py` e
`test_d_t2_google_tool_use.py` com 39 testes; regressao curta com
`test_cost_tracking.py`, `test_erro_pipeline.py`, `test_stage_tool_pdf_quality.py`,
`test_e_t2_retry_partial_output.py` e `test_d_t2_google_tool_use.py` com 158
testes. Deploy oficial: `3fce335` em `origin/main` e Render `live`. Smoke:
`task_81f274a6f510` rodou `selected_steps=["corrigir"]` com `gem25flash001` e
falhou alto por Google `429 RESOURCE_EXHAUSTED`; como a quota bloqueou antes de
novo documento parcial, o teste live nao reproduziu o caso de documento criado
antes do erro. `/api/custos/resumo?limit=60` ficou com `runs_precificados=25`,
`runs_bloqueados=2`, ambos historicos por `token_split_missing`; sem novo falso
verde e sem novo bloqueio criado por esse smoke.

Atualizacao de tool-use Google em 2026-05-17 no runtime `33fb7d5`: o smoke
Gemini 2.5 Flash Lite `task_6ee6a6386cea` revelou bug real em `create_document`:
o modelo passou `atividade_id="Smoke Paulo Pipeline 2026-05-16"` e a tool
tentou salvar com esse nome em vez do id oficial, gerando
`Atividade não encontrada`. O commit `33fb7d5` passou a preferir o
`ToolExecutionContext` server-side para `atividade_id`/`aluno_id` em etapas de
pipeline. Validacoes: `py_compile`, `git diff --check`, `test_warning_system.py`
com 76 testes e regressao curta com 161 testes. Deploy confirmado por
`check_deploy.sh 33fb7d5`, `/api/deploy-info`, `/api/health` e Render MCP
`dep-d84ua8flk1mc73em0f60`. Re-smoke `task_52e5fa9020a0` removeu o erro de
storage: a etapa agora falha alto por erro real do modelo (`create_document`
tentou PDF e `execute_python_code` gerou `IndentationError`). O custo do erro
ficou rastreavel: documento `ea407d2ce87fb99a`, `tool_f0e5ce2a3a55`,
`14772/1805` tokens, `US$ 0.001649`, `status=erro`, `custo_status=ok`.

Atualizacao de retry PDF em 2026-05-17 no runtime `0f84552`: quando uma etapa
dual-output ja tem JSON persistido, mas `execute_python_code` falha antes de
gerar o PDF, o executor agora faz uma tentativa explicita adicional no mesmo
modelo, com o erro anterior e o JSON oficial na mensagem. Validacoes:
`py_compile`, `git diff --check`, `test_e_t2_retry_partial_output.py` com 31
testes e regressao curta com 162 testes. Deploy confirmado por
`check_deploy.sh 0f84552`, `/api/deploy-info`, `/api/health` e Render MCP
`dep-d84uf0e7r5hc73dmk4fg`. Re-smoke Gemini 2.5 Flash Lite
`task_124bf0e8d7bf` falhou alto antes desse reparo ser necessario porque o JSON
oficial veio invalido (`7fde0dfd076a36e3` sem `questoes`, `nota_final=0`)
enquanto o PDF `e8861f03a2980412` mostrava `8.0`. Resultado correto: todos os
artefatos do run `tool_44dd029b1954` foram marcados `status=erro`, custo
`18748/1934` tokens e `US$ 0.001986`, sem fallback e sem `completed` falso.

Atualizacao GPT-5 Nano em 2026-05-17 no runtime `0f84552`: smoke
`task_90eb0936b7ce`, `selected_steps=["corrigir"]`, falhou alto por divergencia
PDF/JSON. JSON `c96bafb0c134d0bd` registrou `nota_final=8`, mas PDF
`43450aa937013578` mostrou `nota_final=0.0`, nota `0.0` na questao 1 onde o
JSON tinha `3`, e nao continha `feedback_geral` verificavel. Todos os artefatos
do run `tool_37b678de7e7d` ficaram `status=erro`; custo rastreavel
`55975/9221` tokens, `US$ 0.006487`. Status correto: Nano nao esta confirmado
para `corrigir` nesse runtime, mas a pipeline bloqueia o falso verde.

Atualizacao GPT-4.1 em 2026-05-17 no runtime `0f84552`: smoke
`task_714dab24c41a`, modelo `ffae9accf68e`, `selected_steps=["corrigir"]`,
completou no site oficial. A inspeção manual baixou JSON `d921c575837e38d7` e
PDF final `a7669eb5352e3d9d`; ambos registram `nota_final=8.0`, Q1/Q2/Q4
corretas, Q3 errada por `25` vs `30`, e feedback geral coerente. O PDF
intermediario `b18662384cdac7c6` foi marcado `status=erro` por consistencia
antes do retry; o artefato final ficou `concluido`. Custo calculado pelo
endpoint `/api/custos/resumo`: run `tool_9d63d57a7b83`, `24217/4005` tokens,
`US$ 0.080474`, `custo_status=ok`. Status: `CORRIGIR` confirmado para GPT-4.1
nessa fixture simples, com retry explicito e sem fallback.

Atualizacao GPT-4.1 etapas finais em 2026-05-17 no runtime `0f84552`: smoke
`task_5c3ba86e86c1`, `selected_steps=["analisar_habilidades","gerar_relatorio"]`,
completou no site oficial usando a correcao GPT-4.1 previa. Analise:
JSON `7b39243c100e30de`, PDF `e6c692989734476b`, run `tool_ec6f3dfbc045`,
`12478/2235` tokens, `US$ 0.042836`. Relatorio: JSON
`10d478289be3cf03`, PDF `e4e6f65038d399db`, run `tool_3d4161aa8b2d`,
`14021/2107` tokens, `US$ 0.044898`. A inspeção manual confirmou
`nota_final=8.0`, proficiencia `8.0`, areas de melhoria em porcentagem e
ausencia de erro de etapa. Observacao de polish: o PDF de analise contem typo
visual `Proeficiência`; nao e falso verde de schema/custo, mas deve entrar em
melhoria de qualidade de PDF.

Atualizacao GPT-4.1 extracoes em 2026-05-17 no runtime `0f84552`: smoke
`task_fd62c9db2359`, `selected_steps=["extrair_questoes","extrair_gabarito","extrair_respostas"]`,
completou no site oficial. `EXTRAIR_QUESTOES` gerou JSON `b5393676dc1c1dd4`
com 4 questoes e pontuacao total `10.0` (`1151/441`, `US$ 0.005830`);
`EXTRAIR_GABARITO` gerou `f6e322b5829d4d34` com respostas `x=5`, `34`, `30`,
`20 cm2` (`1852/451`, `US$ 0.007312`); `EXTRAIR_RESPOSTAS` gerou
`c429ee5f3276fa90` com 4 respostas da Diana, Q3 `25`, sem resposta em branco e
`raciocinio_parcial=null` (`2242/288`, `US$ 0.006788`). Status: GPT-4.1 esta
confirmado nas 6 etapas da fixture simples, somando os smokes por grupo de
etapas, com custo medido por etapa.

Atualizacao GPT-4.1 full pipeline em 2026-05-17 no runtime `0f84552`: smoke
`task_f6851ed535b8` executou as 6 etapas em uma unica corrida e completou sem
`stage_errors`. Artefatos principais: questoes `79b5876544c6c2ae`, gabarito
`bfb2a7590d943fa3`, respostas `afacce7606ab43b3`, correcao JSON/PDF
`c186d3f6f852fb9b`/`df34a13a49ad03e5`, analise JSON/PDF
`b8126c7d15ecee56`/`5f86f4d2dd3abe23`, relatorio JSON/PDF
`71cf0b53fe147668`/`3490b806647c8e2a`. A inspeção confirmou Q3 `25` vs `30`,
`nota_final=8.0`, proficiencia `8.0`, recomendacao focada em porcentagem e
PDFs legiveis. O PDF intermediario `6edcd9f8ecd80b52` foi marcado `status=erro`
por consistencia antes do retry. Custos por etapa: `US$ 0.006134`,
`0.007068`, `0.006862`, `0.080190`, `0.075614`, `0.046988`; total aproximado
`US$ 0.222856`. Status: GPT-4.1 confirmado como full smoke na fixture simples.

Atualizacao de disponibilidade de providers em 2026-05-17 no runtime
`0f84552`: teste live de conexao em `/api/settings/models/{id}/testar`.
OpenAI OK: `gpt-4o`, GPT-4.1, GPT-5 Nano e GPT-5.4 Mini. Anthropic bloqueado:
Haiku 4.5 e Sonnet 4.5 retornam credito insuficiente. Google: Gemini 2.5 Pro,
Gemini 2.5 Flash e Gemini 3 Flash retornam `429`; Gemini 2.5 Flash Lite
conecta (`success=true`), mas segue falhando em `corrigir` por qualidade/artefato
no smoke anterior. Ollama local falha conexao no Render. Regra operacional:
nao rerodar Anthropic sem credito nem Google pesado enquanto a quota estiver
saturada; priorizar OpenAI/GPT-4.1 ou fixes internos sem trocar provider por
baixo.

Atualizacao de guard PDF/JSON em 2026-05-17: o full smoke GPT-4.1 revelou custo
extra causado por validador rigido demais. PDFs de correcao com texto
consistente eram marcados `status=erro` quando usavam rotulos como
`Comentário pedagógico geral` ou `Feedback geral da avaliação`. Commits
`974f040` e `11a396b` adicionaram esses aliases ao guard e testes focados.
Validacoes: `py_compile`, `git diff --check`, `test_stage_tool_pdf_quality.py`
e regressao curta `test_stage_tool_pdf_quality.py`, `test_e_t2_retry_partial_output.py`,
`test_cost_tracking.py` com 74 testes. Deploy confirmado em `11a396b` por
`check_deploy.sh`, `/api/deploy-info` e `/api/health`. Re-smoke
`task_92c4b74494f7`, GPT-4.1 `corrigir`, gerou apenas JSON
`a05a2a4faeab71d1` e PDF `dc9fe13dc6b8b994`, ambos `concluido`, sem PDF
intermediario `status=erro`; custo `14617/2400`, `US$ 0.048434`. Status: retry
artificial removido para esse formato de PDF live, mantendo erro alto para PDF
realmente inconsistente.

Atualizacao Gemini 2.5 Flash Lite em 2026-05-17 no runtime `11a396b`: smoke
`task_5850e9adf001`, `selected_steps=["corrigir"]`, falhou alto por quota
Google `429 RESOURCE_EXHAUSTED`, `provider=Google`, `retryable=true`, sem
promover sucesso nem trocar provider. Houve documentos de erro custeaveis:
`494856278a41ff57` (`6408/208`, `US$ 0.000543`) e `badbaadbe86ce541`
(`3029/515`, `US$ 0.000382`), ambos `status=erro`. Status: Gemini Lite continua
❌/bloqueado em `CORRIGIR`; neste run o bloqueio observado foi quota, nao mais o
erro antigo de ids server-side nem falso verde.

Atualizacao de 2026-05-17 no runtime `700b088`: o ciclo `f40acf3` alinhou
`PROMPTS_PADRAO` e `STAGE_TOOL_INSTRUCTIONS` para `CORRIGIR`,
`ANALISAR_HABILIDADES` e `GERAR_RELATORIO`, e tornou obrigatorios campos de
schema/avisos/linhagem em `ANALISAR_HABILIDADES` e `GERAR_RELATORIO`. O smoke
`task_9671e072f42c` passou tecnicamente, mas revelou falso verde semantico:
Q3 tinha `resposta_aluno=25` em `EXTRACAO_RESPOSTAS` e `resposta_correta=30`
no gabarito, mas a correcao marcou Q3 como correta e `nota_final=10.0`. O
commit `700b088` adicionou rastreabilidade obrigatoria em `CORRIGIR`: quando
existem documentos upstream, cada `questoes[]` precisa carregar
`resposta_aluno` da extracao de respostas e `resposta_correta` do gabarito; se
trocar a resposta do aluno ou der acerto/nota maxima para divergencia numerica,
a etapa falha alto. Deploy confirmado por `./scripts/check_deploy.sh 700b088`,
`/api/deploy-info` e `/api/health`. O re-smoke `task_cc22b6c239d0` completou
`corrigir`, `analisar_habilidades` e `gerar_relatorio` com GPT-5.4 Mini:
correcao JSON `c3c680d099f781f7` marcou Q3 `25` vs `30`, nota `0.0/2.0` e
`nota_final=8.0`; PDFs finais extraidos por `pdftotext` confirmaram nota 8.0,
Q3 erro e recomendacao focada em porcentagem. Custo do re-smoke:
`56891/9827` tokens, `US$ 0.086890`; o alerta `token_usage_not_durable`
continua bloqueante ate aplicar `backend/migrations/002_create_token_usage.sql`.

Atualizacao operacional de 2026-05-17: depois de `3e6be20`, o loop publicou
`629c4ee` e `aff2180`. `629c4ee` corrigiu uma validação estreita demais que
exigia o rótulo literal "Feedback Geral" no PDF, embora Gemini tivesse gerado o
conteudo completo sob "Parecer Pedagógico Geral". O smoke Gemini full
`task_c9302f341734` completou as 6 etapas em `629c4ee`, mas a auditoria achou
novo falso verde: o JSON de `corrigir` usou `feedback_geral_texto` e
`feedback_geralSmall`, sem `feedback_geral`. `aff2180` tornou
`feedback_geral`, `total_acertos`, `total_erros`, `_avisos_documento` e
`_avisos_questao` obrigatorios para `CORRIGIR`. Os reruns Gemini posteriores
(`task_0cbc99255c7e`, `task_6347f5e0d311`, `task_26412081ac9f`) falharam alto
por quota Google `429`, com limite free-tier `generate_content_free_tier_requests`
do modelo `gemini-3-flash`; portanto Gemini fica bloqueado por quota para
revalidar o schema novo, nao confirmado como full final.

No mesmo runtime `aff2180`, GPT-5.4 Mini completou novamente a pipeline de 6
etapas em `task_299dd8a00517`. Artefatos/custos: `extrair_questoes`
`6510078afa7dcc4b` (`1150/489`, `US$ 0.003063`), `extrair_gabarito`
`1f2e9af35f895de1` (`1903/295`, `US$ 0.002755`), `extrair_respostas`
`98dc9d287f28893e` (`2129/455`, `US$ 0.003644`), `corrigir`
PDF/JSON `54bbdd06a48f9376`/`f4f5a5d1f71a262f` (`23462/3876`,
`US$ 0.035039`), `analisar_habilidades`
`71c5cd58b3a11403`/`6972964717580587` (`12285/2154`, `US$ 0.018907`) e
`gerar_relatorio` `092a5ac44779a0e7`/`c9552a74276b38ac`
(`19398/3778`, `US$ 0.031550`). Total aproximado: `US$ 0.094958`. O JSON de
correcao veio com `feedback_geral` correto e o PDF/JSON ficaram coerentes; o
PDF de correcao ainda mostra "Aluno: Não informado", que fica como lacuna de
qualidade/metadata de PDF.

Ainda em `aff2180`, Nano foi reavaliado no ponto historicamente fraco
`extrair_respostas`. O smoke `task_ff7eeda28964`, com
`selected_steps=["extrair_respostas"]`, completou e criou o JSON
`4175e0e7476931d7` com as 4 respostas reais da fixture Diana (`x = 5`, `34`,
`25`, `20 cm2`), `2129/2261` tokens e custo `US$ 0.001011`. Isso melhora Nano
para a fixture simples, mas nao apaga as falhas historicas em PDFs/listas
maiores; o status correto e parcial ate repetir em dataset mais dificil.

Atualizacao GPT-4o de 2026-05-17: `task_d6506d2f2ccc` completou as tres
extracoes em `aff2180`, mas a auditoria achou `raciocinio_parcial` avaliando
ou especulando metodo na extração de respostas. Os commits `2885da7` e
`99b8c3c` proibiram, respectivamente, linguagem de correção e linguagem
especulativa em `EXTRAIR_RESPOSTAS`. O rerun `task_013ad41fd3ed` em
`99b8c3c` completou as tres extracoes com conteúdo limpo: questoes
`69dd5c07acb2ff52` (`1151/381`, `US$ 0.006687`), gabarito
`98dbaf8613ec9fc3` (`1718/282`, `US$ 0.007115`) e respostas
`8019a2a2c5fc3cea` (`2115/292`, `US$ 0.008207`). O JSON de respostas traz
`x = 5`, `34`, `25`, `20 cm2` e `raciocinio_parcial=null` nas quatro questoes,
como esperado quando so ha resposta final visivel.

Haiku 4.5 foi rechecado pelo endpoint oficial
`POST /api/settings/models/588f3efe7975/testar` no mesmo ciclo e continua
bloqueado por créditos Anthropic: HTTP 200 da API do site, `success=false`, erro
Anthropic `invalid_request_error` com mensagem de saldo insuficiente. Nao ha
pipeline Haiku util enquanto esse bloqueio externo persistir.

Atualizacao Nano/relatorio de 2026-05-17: a pipeline full Nano
`task_f0c0f15a2f27`, no runtime `99b8c3c`, completou as 6 etapas, mas a
auditoria achou falso verde em `GERAR_RELATORIO`: a correcao oficial Nano
`cff76af34d9248a6` tinha `nota_final=8.0`, enquanto o relatorio JSON
`8184fe013490b53e`/PDF `15cbe3b104f37891` registrou `nota_final=0.0`. O commit
`392ec7c` passou a validar `RELATORIO_FINAL.nota_final` contra a `CORRECAO`
oficial mais recente, sem buscar correcao antiga como fallback. O smoke live
`task_57da745b8de5`, em Render `392ec7c`, reexecutou apenas `gerar_relatorio`
com `gpt5nano001`: JSON `66fcc132db1be96a` ficou com `nota_final=8.0`, o PDF
ruim `34e404fcd809270d` foi marcado `status=erro` por
`pdf_json_consistency`, e o PDF final `735896580f441e89` trouxe texto extraivel
com `Nota final: 8.0`. Tokens do run: `29067/6701`, total `35768`.

Atualizacao custos de 2026-05-17: nao ha `SUPABASE_*`, `DATABASE_URL` ou credencial
admin disponivel no ambiente local para aplicar a migration
`backend/migrations/002_create_token_usage.sql`. O commit `460643f` corrigiu o
comportamento possivel sem segredo: `/api/custos/status?limit=80` no Render
agora retorna `ok=false`, `custos_persistencia_status=parcial_sem_token_usage_duravel`
e alerta bloqueante `token_usage_not_durable`, mantendo `PGRST205` visivel. Isso
deixa claro que custos em documentos com metadata estao medidos, mas falhas sem
documento final ainda nao tem persistencia duravel ate a tabela Supabase existir.

Atualizacao UI custos de 2026-05-17: o commit `54d083e` levou esse bloqueio
para o dashboard oficial. O HTML live agora busca `/api/custos/status?limit=80`
e mostra alerta "Custos não duráveis" quando `token_usage_backend.durable=false`,
`custos_persistencia_status=parcial_sem_token_usage_duravel` ou alerta
`token_usage_not_durable` aparecerem. Smokes oficiais: `check_deploy.sh 54d083e`
passou, `/api/health` retornou `healthy`, `/api/custos/status?limit=80`
retornou `ok=false`, `runs_precificados=37`, `runs_bloqueados=0`,
`durable=false`, e o HTML servido continha `dashboard-cost-alerts` e a chamada
`/custos/status?limit=80`.

Atualizacao GPT-4o full de 2026-05-17: no mesmo runtime `54d083e`, a task
`task_68b19146a95b` completou as 6 etapas com `180b8298a279` na fixture Diana.
Artefatos finais: questoes `5adf51fcd1adc4c0`, gabarito
`7c097774fce46472`, respostas `9e6d562d51a6f6e4`, correcao JSON/PDF
`b2abc9a73c8dc3a8`/`8911e1a3acae4ad2`, habilidades JSON/PDF
`21f2d7d065aeafe5`/`72203996b8960b50` e relatorio JSON/PDF
`bbc5963d712a7f1e`/`f12312b96e3725a3`. PDFs baixados por `pdftotext`
confirmaram `Nota Final: 8.0`; custo aproximado das 6 etapas: `US$ 0.314369`.
Houve retries explicitos: JSONs inválidos anteriores ficaram `status=erro`
antes dos artefatos finais, sem troca silenciosa de modelo.

Atualizacao Gemini 2.5 Flash de 2026-05-17: testes de conexao mostraram
OpenAI (`gpt-4o`, GPT-4.1, GPT-5 Nano e GPT-5.4 Mini) com `success=true`;
Gemini 2.5 Flash e Flash Lite tambem com `success=true`; Haiku/Sonnet continuam
bloqueados por creditos Anthropic; Gemini 2.5 Pro e Gemini 3 Flash retornaram
Google `429`. Em seguida, a task `task_f1f1511f21d5` rodou full smoke com
`gem25flash001`: as tres extracoes passaram com conteudo correto, mas
`corrigir` falhou alto por saida obrigatoria incompleta de tools
(`create_document` JSON + `execute_python_code` PDF). Status correto: Google
Gemini 2.5 Flash funciona para extracoes na fixture simples, mas nao esta
pipeline-ready para tools. Os commits `854cec7` e `b07472f` atacaram esse
ponto: primeiro forcaram tool-use Google faseado (`create_document` depois
`execute_python_code`), depois aceitaram paráfrase coerente de `feedback_geral`
sem aceitar feedback truncado. A revalidacao em `b07472f` chegou a criar JSON
de correcao, mas parou em Google `429`; `task_6bba32964706` e a tentativa
isolada `task_f9b76153875a` ficam como bloqueio de quota, nao como falso verde.

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
`75% de proficiencia geral` de modo potencialmente confuso. O patch
`0ac92f0` foi deployado e o re-smoke `task_605512496b0d` completou as 6 etapas,
mas revelou um P0 novo: os JSONs ficaram coerentes (`nota_final=8`, Q3 `0`),
enquanto o PDF de correcao mostrou `Nota final: 9.0` e Q3 `2.0`; o PDF de
relatorio mostrou `Nota final: N/A` apesar do JSON ter `nota_final=8`. Patch
local atual adiciona validação PDF/JSON no executor para transformar essa
divergencia em erro alto, sem aceitar PDF semanticamente diferente do JSON. Essa
guarda foi deployada em `2052a01`; o smoke reduzido `task_857c0c3657ef` falhou
alto em `corrigir`, como esperado, porque o PDF `7559f610981995cd` mostrou Q3
`3.0` enquanto o JSON `0fdcfe4d7d9b9072` tinha Q3 `0`. O retry PDF/JSON foi
deployado em `3a77a17`; o smoke reduzido `task_e389f360b812` completou
`corrigir`, `analisar_habilidades` e `gerar_relatorio`. Inspeção manual
confirmou PDF de correção coerente com JSON (`nota_final=8.0`, Q3 `0.0/2.0`) e
relatório com `Nota final: 8,0/10` separado de `Proficiência geral: 80%`. O
resumo de custos agora também expõe `erro_pipeline` em documentos com status
`erro`.

Atualizacao GPT-4o em 2026-05-17: commits `f7bca4c`, `33829bc`, `fdf1829`,
`3af2918`, `00eb26b` e `3e6be20` corrigiram, em ordem, o uso de Responses API
para OpenAI forced tools, retry de JSON invalido, schema minimo de JSON para
`correcao`/`analise_habilidades`/`relatorio_final`, marcacao de artefatos
invalidos ou stale como `status=erro`, regras de sandbox para PDF e bloqueio de
PDF de correcao truncado. O smoke reduzido GPT-4o final
`task_386f96bbf158` em Render `3e6be20` completou `corrigir`,
`analisar_habilidades` e `gerar_relatorio`. Artefatos oficiais: correcao PDF
`e5ca0900654ed0e9` + JSON `e8269ff428d50802`; analise PDF
`9b8ef8b03388a741` + JSON `58ddf040c628863c`; relatorio PDF
`4d4a42b77010d27a` + JSON `30c5a9c3225f1ed5`. Inspecao `pdftotext` confirmou
nota `8.0`, Q3 `0.0/2.0`, Feedback Geral completo, relatorio com Nota Final
`8.0` e documentos legiveis. O run tambem registrou erros explicitos esperados:
JSON arrays como `json_schema_validation`, JSONs extras como
`stale_tool_artifact` e um PDF anterior de relatorio com `nota_final=N/A` como
`pdf_json_consistency`. Custos GPT-4o do smoke final: `corrigir`
`66527/6861`, `US$ 0.234928`; `analisar_habilidades` `47566/4498`,
`US$ 0.163895`; `gerar_relatorio` `39023/4062`, `US$ 0.138178`; total
aproximado das tres etapas `US$ 0.536...`.

Proximos alvos reais: aplicar e validar `token_usage` duravel; revalidar
Gemini/Nano/Haiku e datasets maiores; e melhorar UI de erros para que o usuario
veja aluno, etapa, provider, custo e causa sem abrir terminal.

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
| Pipeline | GPT-4.1 (`ffae9accf68e`) tem full smoke unico confirmado em `task_f6851ed535b8` e re-smoke `corrigir` pos-guard `task_92c4b74494f7` sem retry artificial; GPT-5.4 Mini (`gpt54mini001`) completou 6 etapas em `task_a5f0d734f0b3` e segue referencia confirmada apos guards; GPT-4o completou full smoke `task_68b19146a95b` em `54d083e`; Gemini 2.5 Flash/Gemini 3/Gemini Lite estao bloqueados por quota Google `429` nos smokes recentes, embora tenham historicos parciais; GPT-5 Nano segue parcial/falhando alto em pontos de qualidade, especialmente `corrigir`/`extrair_respostas` | Revalidar matriz por provider/modelo quando quota/credito permitir e manter P0: nao aceitar `completed` sem documento, schema, custo, conteudo minimo, nota cross-stage e artefatos coerentes entre si |
| Schema e avisos | Sprint 2 concluida localmente | Manter schema oficial, defaults e visualizador cobertos por testes |
| Custos/tokens | Metadata de documento, endpoints live, resumo por `cost_run_id`, `TokenUsageRecord` local, migration Supabase dedicada `b2dc88b`; GPT-4.1 full smoke `task_f6851ed535b8` mediu total aproximado `US$ 0.222856`; re-smoke `task_92c4b74494f7` apos guard reduziu `corrigir` para `US$ 0.048434`; Gemini Lite quota `task_5850e9adf001` registrou documentos de erro custeaveis `US$ 0.000543` e `US$ 0.000382`; `460643f` faz `/api/custos/status` retornar `ok=false` e alerta bloqueante enquanto `PGRST205`, `durable=false` e `local_record_count=0` persistirem; `54d083e` mostra esse bloqueio no dashboard oficial | Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase; revalidar ate `token_usage_backend.durable=true`; depois persistir custos de falhas sem documento |
| UI de erros | Dashboard oficial mostra bloqueio de custos nao duraveis no commit `54d083e`; `98fafc9` adicionou `stage_errors` por aluno/etapa em `/api/task-progress` e a sidebar renderiza a causa abaixo da etapa falha; smoke live `task_7362d0fb1939` confirmou erro de `extrair_respostas` sem prova antes de chamar IA | Ampliar para telas de resultado/historico e garantir que erros de provider/custo apareçam com a mesma clareza |
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
- Commit funcional de usage parcial em erro de provider apos tools:
  `1454e68`/`3fce335` (Render live; testes locais 158; smoke Gemini 2.5 Flash
  `task_81f274a6f510` falhou alto por quota antes de criar novo artefato).
- Commit funcional para IDs server-side em `create_document` de pipeline:
  `33fb7d5` (Render live; `task_52e5fa9020a0` removeu erro de storage por
  nome de atividade e expôs erro real de PDF/codigo do Gemini Lite).
- Commit funcional de retry explicito para erro de codigo PDF:
  `0f84552` (Render live; `task_124bf0e8d7bf` falhou alto por JSON invalido do
  Gemini Lite, com artefatos e custo marcados como erro).
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
- Commit funcional de guards de `EXTRAIR_RESPOSTAS`: `2885da7` bloqueou linguagem
  de correcao e `99b8c3c` bloqueou raciocinio especulativo; GPT-4o
  `task_013ad41fd3ed` confirmou extracoes limpas.
- Commit funcional de validacao de `nota_final` do relatorio contra correcao:
  `392ec7c` (Render live e smoke Nano `task_57da745b8de5` com JSON/PDF de
  relatorio `nota_final=8.0`).
- Commit funcional de alerta bloqueante para custos nao duraveis:
  `460643f` (`/api/custos/status.ok=false` enquanto `public.token_usage` nao
  existir no Supabase).
- Commit funcional de alerta de custo nao duravel no dashboard:
  `54d083e` (`dashboard-cost-alerts` consulta `/api/custos/status?limit=80`).
- Commit docs de registro Google/quota: `f836ab2`.
- Commit funcional de erro por aluno/etapa na sidebar:
  `98fafc9` (`stage_errors` em `/api/task-progress`, renderizado em
  `tarefa-stage-error`).
- Commit funcional anti-`nota_final=N/A` em relatório:
  `ad7e00e` (`GERAR_RELATORIO` falha alto com
  `NOTA_FINAL_INDETERMINADA` quando não há nota numérica confiável).
- Commit funcional de usage parcial em erro dentro do `ChatClient`:
  `3fce335`.
- Commit funcional de ids server-side no `create_document` de pipeline:
  `33fb7d5`.
- Commit funcional de retry explicito para erro de codigo PDF:
  `0f84552`.
- Commit funcional de guard PDF/JSON para headings reais de feedback:
  `974f040` e `11a396b` (Render live; re-smoke GPT-4.1
  `task_92c4b74494f7` sem PDF intermediario `status=erro`).
- Commits documentais mais recentes apos o deploy de codigo:
  `c094fba` e `d799165` em `origin/main`.
- Marker mais novo publicado no GitHub para runtime: `a7dead3`
  (`chore: mark deploy e6060e1`).
- Marker mais novo publicado no GitHub para o guard: `2792d89`
  (`chore: mark deploy 5527e26`).
- Render em 2026-05-17: servico oficial `srv-d5t8gbh4tr6s738fr3s0`, branch
  `main`, repo `https://github.com/OttoBoop/IA_Educacao_V2`, `rootDir=backend`,
  autoDeploy `yes`; `/api/deploy-info` confirmou `11a396b` com
  `source=RENDER_GIT_COMMIT` depois de `check_deploy.sh 11a396b`.
- Marker HTML pode ficar atrasado em commits de docs/frontend; o gate oficial
  para backend agora e `/api/deploy-info` + smoke live, nao apenas marcador HTML.
- GitHub `origin/main`: `d799165` no ultimo registro documental observado; como
  foi docs-only, o backend live segue em `11a396b`.
- Render live observado: saiu de `2e1098f` para `b12be9a` e depois confirmou
  marcadores/fixes sucessivos ate `11a396b`.
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
- P5: contencao temporaria de `nota_final` foi concluida em 2026-05-13; em
  2026-05-17, `ad7e00e` removeu o aceite final de `nota_final=N/A` em
  `GERAR_RELATORIO`, que agora falha alto quando a nota confiavel esta ausente.
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
- Proximo alvo historico daquele momento: Sprint 1/P5, contencao temporaria de
  `nota_final`; estado atual: `ad7e00e` converteu ausencia de nota confiavel em
  erro alto no relatorio.

### 2026-05-13 -- Sprint 1/P5-P6: nota_final e documentos faltantes

- Alvo: robustecer `nota_final` em `GERAR_RELATORIO` e preservar
  `_documentos_faltantes` quando o relatório não puder rodar.
- Status: concluido localmente.
- Arquivos tocados: `backend/executor.py`, `backend/tests/unit/test_erro_pipeline.py`.
- Comportamento: nota usa contencao ordenada (`nota_final`, `nota`, soma de
  `questoes[].nota`, soma de `correcoes[].nota`, `N/A`); erro de relatório
  retorna `_erro_pipeline`, `_documentos_faltantes` e `_documentos_carregados`.
- Ressalva P0 resolvida em 2026-05-17 para `GERAR_RELATORIO`: `ad7e00e`
  transforma nota nao confiavel em erro alto antes de chamar IA.
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
- Deploy/re-smoke do patch PDF: commit `0ac92f0` ficou live no Render; re-smoke
  full `task_605512496b0d` completou as 6 etapas, mas revelou P0 de
  consistencia: JSON de correcao `a899697b81e7e10d` manteve `nota_final=8` e
  Q3 `0`, enquanto PDF `2114140f8d5aaf61` mostrou `Nota final: 9.0` e Q3
  `2.0`; JSON de relatorio `680aa0c4bf6183ec` manteve `nota_final=8`, enquanto
  PDF `dde1d63db71f2a5b` mostrou `Nota final: N/A`.
- Patch local seguinte: `backend/executor.py` valida consistencia minima entre
  JSON e PDF de `CORRIGIR`/`GERAR_RELATORIO`; se o PDF divergir em `nota_final`,
  misturar nota com percentual, ou mostrar nota por questao diferente do JSON,
  a etapa vira "Saida obrigatoria invalida" e os documentos do run sao marcados
  como erro.
- Validações locais da guarda PDF/JSON: `python -m py_compile
  backend/executor.py backend/tests/unit/test_stage_tool_pdf_quality.py
  backend/tests/unit/test_cost_tracking.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_stage_tool_pdf_quality.py
  backend/tests/unit/test_e_t2_retry_partial_output.py
  backend/tests/unit/test_cost_tracking.py -q` com `42 passed` e o aviso
  conhecido de pytest `timeout`.
- Deploy da guarda PDF/JSON: commit `2052a01` ficou live no Render; smoke
  reduzido `task_857c0c3657ef` com `selected_steps=["corrigir",
  "analisar_habilidades","gerar_relatorio"]` falhou alto ja em `corrigir`.
  Erro oficial: PDF `7559f610981995cd` mostrou nota `3.0` na questao 3, mas JSON
  `0fdcfe4d7d9b9072` tinha nota `0`. Isso confirma que o falso verde foi
  bloqueado no site oficial.
- Custo do erro oficial: `/api/custos/resumo?limit=20` mostrou o run
  `tool_55b78f5b0f02` com status `erro`, `16116/2749` tokens e custo
  `US$ 0.024458`. Limite achado: o documento no resumo ainda mostrava
  `erro=null`, porque o resumo nao promovia `metadata.erro_pipeline`.
- Patch local seguinte: `executar_com_tools` faz um retry explicito no mesmo
  modelo, apenas com `execute_python_code`, quando PDF diverge do JSON validado;
  o PDF invalido anterior fica marcado como `erro` e a etapa so fica verde se o
  novo PDF concordar com o JSON. `cost_tracking` passa a expor
  `erro_pipeline`/`erro_tipo` nos documentos do resumo.
- Validações locais do retry PDF/JSON e custo: `python -m py_compile
  backend/executor.py backend/cost_tracking.py
  backend/tests/unit/test_cost_tracking.py
  backend/tests/unit/test_stage_tool_pdf_quality.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_stage_tool_pdf_quality.py
  backend/tests/unit/test_e_t2_retry_partial_output.py
  backend/tests/unit/test_cost_tracking.py -q` com `44 passed` e o aviso
  conhecido de pytest `timeout`.
- Deploy do retry PDF/JSON: commit `3a77a17` ficou live no Render. Smoke
  reduzido `task_e389f360b812` completou `corrigir`, `analisar_habilidades` e
  `gerar_relatorio`.
- Artefatos do smoke `3a77a17`: `corrigir` gerou PDF valido
  `b9fbaf4dc24b4a75`, PDF invalido anterior marcado como erro
  `c1c66de78fa3c388`, e JSON `dd79a9c3f369fc09`; `analisar_habilidades` gerou
  PDF/JSON `255960a24f219f15`/`cb441f5a0c6651d6`; `gerar_relatorio` gerou
  PDF/JSON `3bc1b11467f885ce`/`ce538fb798f1230e`.
- Inspeção manual: PDF de correcao extraido por `pdftotext` mostra
  `Nota final 8.0`, Q3 `Nota: 0.0 / 2.0`, e feedback completo; JSON confirma
  `nota_final=8.0` e Q3 `nota=0.0`. Relatorio mostra `Nota final: 8,0/10` e
  `Proficiência geral: 80%` em linhas separadas; JSON confirma
  `nota_final=8.0`.
- Custo do smoke `3a77a17`: `corrigir` `18319/4177`, `US$ 0.032536`;
  `analisar_habilidades` `11968/2781`, `US$ 0.021490`;
  `gerar_relatorio` `12788/2166`, `US$ 0.019338`. O resumo agora expõe
  `erro_pipeline` no PDF invalido marcado como `status=erro`.
- Proximo alvo: aplicar `token_usage` duravel, revalidar providers restantes e
  atacar UI de erros. O contrato PDF/JSON fica: sucesso apenas se artefatos
  concordam; divergencia vira retry explicito e depois erro alto.

### 2026-05-17 -- GPT-4o explicito, schema/stale/PDF truncado

- Alvo: revalidar GPT-4o como modelo explicito nas etapas finais sem fallback
  de provider e sem aceitar artefato invalido como sucesso.
- Commits publicados e confirmados no Render: `f7bca4c` usa Responses API para
  OpenAI forced tools; `33829bc` adiciona retry de JSON invalido; `fdf1829`
  amplia schema minimo para `correcao`, `analise_habilidades` e
  `relatorio_final`; `3af2918` ignora artefatos em erro, marca todos os JSONs
  invalidos e artefatos stale; `00eb26b` reforca regras de sandbox para PDFs;
  `3e6be20` bloqueia PDF de correcao com Feedback Geral truncado.
- Falhas intermediarias uteis: `task_738c5247b97f` destravou `corrigir`, mas
  falhou em `analisar_habilidades` por JSON array na raiz; `task_82763c17bac3`
  completou, mas inspecao achou arrays concluídos em `correcao`/`relatorio`;
  `task_8661e1034c6a` falhou alto em `gerar_relatorio` por
  `E2B_SECURITY File write outside sandbox`; `task_4880fd35b86c` completou em
  `00eb26b`, mas a inspeção pegou PDF de correcao com Feedback Geral cortado.
- Smoke final: `task_386f96bbf158` completou `corrigir`,
  `analisar_habilidades` e `gerar_relatorio` em `3e6be20`. Artefatos oficiais:
  correcao PDF/JSON `e5ca0900654ed0e9`/`e8269ff428d50802`; analise
  `9b8ef8b03388a741`/`58ddf040c628863c`; relatorio
  `4d4a42b77010d27a`/`30c5a9c3225f1ed5`.
- Inspecao: JSONs oficiais sao objetos; PDFs tem texto extraivel; correcao
  mostra `Nota Final: 8.0`, Q3 `0.0/2.0` e Feedback Geral completo; relatorio
  mostra `Nota Final: 8.0`. Artefatos ruins do mesmo run ficaram em
  `status=erro` com `json_schema_validation`, `stale_tool_artifact` ou
  `pdf_json_consistency`.
- Custos do smoke final GPT-4o: `corrigir` `66527/6861`, `US$ 0.234928`;
  `analisar_habilidades` `47566/4498`, `US$ 0.163895`; `gerar_relatorio`
  `39023/4062`, `US$ 0.138178`. Total aproximado das tres etapas:
  `US$ 0.536...`.
- Validacoes locais dos patches: `python -m py_compile` nos arquivos tocados;
  `git diff --check`; suites focadas com `59`, depois `60`, depois `61`
  testes passando conforme os guards foram adicionados.
- Proximo alvo: revalidar outros providers/datasets e aplicar a migration
  Supabase `token_usage`; GPT-4o esta confirmado para estas tres etapas na
  fixture simples, nao para a pipeline completa de 6 etapas.

### 2026-05-17 -- Gemini 3 Flash `extrair_gabarito` revalidado

- Alvo: revalidar o P0 historico de Gemini em `extrair_gabarito`, que antes
  retornava tudo como `MISSING_CONTENT`.
- Smoke oficial: `task_c08f3d478aad`, Render runtime `3e6be20`, modelo
  `gem3flash001`, `selected_steps=["extrair_gabarito"]`, `force_rerun=true`.
- Resultado: etapa `completed`; documento JSON `92e5e77b24874ad1`,
  provider/modelo `google/gemini-3-flash-preview`, `2040/507` tokens,
  `US$ 0.001220`.
- Inspecao do JSON: raiz objeto com `respostas`, 4 itens reais e coerentes:
  Q1 `x = 5`, Q2 `34`, Q3 `30`, Q4 `20 cm2`. Nenhum `MISSING_CONTENT` no
  resultado inspecionado.
- Atualizacao de matriz: Gemini 3 Flash volta a ✅ em `extrair_gabarito` para
  esta fixture simples. Ainda falta pipeline sequencial completa quando quota
  permitir.
- Observacao de deploy/docs: commit docs `d829291` esta no GitHub, mas Render
  nao mudou de `3e6be20` apos 600s, provavelmente por mudança fora do
  `rootDir=backend`; o runtime tecnico validado segue `3e6be20`.

### 2026-05-17 -- Schema `CORRIGIR` endurecido e smokes em `aff2180`

- Alvo: impedir falso verde quando o modelo gera campo parecido com
  `feedback_geral`, mas nao o campo contratual.
- Commits/deploy: `629c4ee` validou feedback de correcao por conteudo do PDF,
  aceitando "Parecer Pedagógico Geral" quando o texto completo esta presente;
  `aff2180` passou a exigir `feedback_geral`, `total_acertos`, `total_erros`,
  `_avisos_documento` e `_avisos_questao` no JSON de `CORRIGIR`.
- Evidencia que motivou `aff2180`: Gemini full `task_c9302f341734` completou em
  `629c4ee`, mas o JSON `54c7fafd5569cca2` usou `feedback_geral_texto` e
  `feedback_geralSmall`, entao o completed era falso verde de schema.
- Reruns Gemini em `aff2180`: `task_0cbc99255c7e` falhou em
  `extrair_questoes` por Google `429`; `task_6347f5e0d311` e
  `task_26412081ac9f` falharam em `corrigir` pelo mesmo limite free-tier
  `generate_content_free_tier_requests`, modelo `gemini-3-flash`. Status:
  bloqueado por quota para revalidar `CORRIGIR` com o schema novo.
- Smoke GPT-5.4 Mini em `aff2180`: `task_299dd8a00517` completou 6 etapas.
  JSONs principais estao coerentes; `corrigir` agora contem `feedback_geral`
  real. Custos por etapa: `US$ 0.003063`, `US$ 0.002755`, `US$ 0.003644`,
  `US$ 0.035039`, `US$ 0.018907`, `US$ 0.031550`; total aproximado
  `US$ 0.094958`.
- Observacoes de qualidade: `extrair_respostas` incluiu uma observacao
  contraditoria na Q1 ("x = 5" mas "nao corresponde ao valor correto esperado"),
  embora a correcao final tenha pontuado corretamente; o PDF de correcao mostra
  "Aluno: Não informado". Esses pontos nao quebraram o smoke, mas entram na fila
  de qualidade/UX e validacao semantica mais fina.
- Smoke Nano em `aff2180`: `task_ff7eeda28964` completou `extrair_respostas`
  na fixture Diana, documento `4175e0e7476931d7`, respostas reais
  `x = 5`/`34`/`25`/`20 cm2`, `2129/2261` tokens, `US$ 0.001011`. Status:
  melhora parcial de Nano; ainda exige dataset maior antes de sair do risco.
- Smokes GPT-4o de extracoes: `task_d6506d2f2ccc` em `aff2180` revelou
  julgamento/especulacao em `raciocinio_parcial`; `2885da7` e `99b8c3c`
  transformaram isso em contrato bloqueante. Rerun `task_013ad41fd3ed` passou:
  `extrair_questoes` `69dd5c07acb2ff52`, `extrair_gabarito`
  `98dbaf8613ec9fc3`, `extrair_respostas` `8019a2a2c5fc3cea`; custo total das
  tres extracoes `US$ 0.022009`.

### 2026-05-17 -- Dashboard mostra bloqueio de custos nao duraveis

- Alvo: impedir que o usuario precise abrir terminal ou endpoint cru para saber
  que custos ainda nao tem persistencia duravel de `token_usage`.
- Commit/deploy: `54d083e` publicado em `origin/main` e confirmado no Render por
  `/api/deploy-info` com `source=RENDER_GIT_COMMIT`.
- Mudanca: `frontend/index_v2.html` agora cria `dashboard-cost-alerts`, consulta
  `/api/custos/status?limit=80` no dashboard e mostra alerta "Custos não
  duráveis" quando `token_usage_backend.durable=false`,
  `custos_persistencia_status=parcial_sem_token_usage_duravel` ou
  `token_usage_not_durable` aparecerem. Falha ao consultar custos tambem gera
  alerta visivel, nao silencio.
- Testes locais: `python -m py_compile
  backend/tests/unit/test_frontend_cost_status_ui.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_frontend_health_banner.py
  backend/tests/unit/test_frontend_cost_status_ui.py -q` com `11 passed` e o
  aviso conhecido de `timeout`.
- Smoke oficial: `./scripts/check_deploy.sh 54d083e` passou; `/api/health`
  retornou `{"status":"healthy","supabase":true}`; `/api/custos/status?limit=80`
  retornou `ok=false`, `custos_persistencia_status=parcial_sem_token_usage_duravel`,
  `runs_precificados=37`, `runs_bloqueados=0`, `durable=false` e alerta
  `token_usage_not_durable`; o HTML live contem `dashboard-cost-alerts` e
  `/custos/status?limit=80`.
- Proximo alvo: aplicar a migration Supabase `002_create_token_usage.sql` quando
  houver credencial/admin, ou continuar a matriz provider sem depender desse
  segredo.

### 2026-05-17 -- GPT-4o full smoke pós-fixes

- Alvo: fechar a lacuna em que GPT-4o tinha etapas individuais revalidadas, mas
  nao uma pipeline completa de 6 etapas no site oficial pos-fixes.
- Smoke oficial: `task_68b19146a95b`, runtime `54d083e`, modelo
  `180b8298a279` (`openai/gpt-4o`), fixture Diana, `force_rerun=true`.
- Resultado task: `completed`; etapas `extrair_questoes`, `extrair_gabarito`,
  `extrair_respostas`, `corrigir`, `analisar_habilidades` e `gerar_relatorio`
  marcadas `completed`.
- Artefatos finais:
  `5adf51fcd1adc4c0`, `7c097774fce46472`, `9e6d562d51a6f6e4`,
  `b2abc9a73c8dc3a8`/`8911e1a3acae4ad2`,
  `21f2d7d065aeafe5`/`72203996b8960b50` e
  `bbc5963d712a7f1e`/`f12312b96e3725a3`.
- Inspecao semantica: 4 questoes, gabarito correto, respostas da aluna
  `x = 5`, `34`, `25`, `20 cm2`, correcao `8.0` com Q3 errada, habilidades
  coerentes e relatorio `nota_final=8.0`. `pdftotext` confirmou PDF de correcao
  e relatorio com `Nota Final: 8.0`.
- Custos medidos: extracoes `US$ 0.006967`, `US$ 0.007275`,
  `US$ 0.008337`; tools `US$ 0.088400`, `US$ 0.127185`, `US$ 0.076205`;
  total aproximado `US$ 0.314369`.
- Observacao: retries explicitos geraram documentos `status=erro` por
  `json_schema_validation` antes dos JSONs finais de tools. Isso e aceitavel
  como retry no mesmo modelo, mas deve permanecer visivel na UI/custos e nunca
  virar sucesso silencioso.

### 2026-05-17 -- Gemini 2.5 Flash falha alto em tools

- Alvo: testar provider Google sem depender do Gemini 3 Flash, que retornou
  quota `429` no teste de conexao.
- Conexao de modelos: `gpt-4o`, GPT-4.1, GPT-5 Nano e GPT-5.4 Mini retornaram
  `success=true`; Gemini 2.5 Flash e Flash Lite retornaram `success=true`;
  Haiku/Sonnet retornaram erro Anthropic de creditos baixos; Gemini 2.5 Pro e
  Gemini 3 Flash retornaram Google `429`.
- Smoke oficial: `task_f1f1511f21d5`, runtime `54d083e`, modelo
  `gem25flash001`, fixture Diana, `force_rerun=true`.
- Resultado task: `failed`; extracoes `completed`, `corrigir=failed`,
  `analisar_habilidades` e `gerar_relatorio` ficaram `pending`.
- Artefatos de extracao: questoes `4d5c5abdc1203f2b` (`1188/567`,
  `US$ 0.000518`), gabarito `d27793f610a3696c` (`2114/318`,
  `US$ 0.000508`) e respostas `ffed15b8003145e9` (`2456/336`,
  `US$ 0.000570`). Inspecao: 4 questoes, gabarito correto, respostas da aluna
  coerentes e sem `ilegivel`.
- Erro alto: `tools: Saída obrigatória incompleta: JSON via create_document,
  PDF via execute_python_code`. Nenhum PDF/JSON foi inventado por fallback.
- Proximo alvo possivel: corrigir contrato/prompt/tool-use Gemini para
  `CORRIGIR`, ou manter Gemini 2.5 Flash como ✅ extracoes/❌ tools enquanto o
  foco passa para UI de erros por etapa.

### 2026-05-17 -- Gemini 2.5 Flash tool-use corrigido, revalidacao bloqueada por quota

- Alvo: corrigir a falha real do smoke anterior, em que Gemini 2.5 Flash nao
  produziu os dois artefatos obrigatorios de `CORRIGIR`.
- Base tecnica: a doc oficial Gemini descreve
  `toolConfig.functionCallingConfig.mode=ANY` com `allowedFunctionNames` para
  forcar chamada de função. O commit `854cec7` passou a enviar esse controle e
  fasear Google como OpenAI: primeira chamada força `create_document`; chamada
  seguinte força `execute_python_code`.
- Validador: `b07472f` ajustou a consistencia PDF/JSON para aceitar
  paráfrase substantiva de `feedback_geral` quando o PDF tem seção longa,
  pontuação final e overlap de conceitos, sem aceitar feedback curto/truncado.
- Testes locais: `py_compile` dos arquivos alterados; `git diff --check`;
  `test_d_t2_google_tool_use.py`, `test_e_t2_retry_partial_output.py`,
  `test_stage_tool_pdf_quality.py` e `test_cost_tracking.py` passaram.
- Deploy: `/api/deploy-info` confirmou `854cec7` e depois `b07472f`;
  `/api/health` permaneceu `healthy`.
- Smokes: `task_cdef8694893e` em `854cec7` provou que Google passou a chamar
  tools, mas o PDF foi barrado por consistencia de feedback. Em `b07472f`,
  `task_6bba32964706` chegou a `corrigir`, mas falhou por Google `429`
  (`generate_content_free_tier_requests`, limite `20`, modelo
  `gemini-2.5-flash`). A tentativa isolada `task_f9b76153875a` tambem falhou
  por `429`.
- Evidencia de erro seguro: o JSON parcial `338b25f9c0f74415` foi marcado
  `status=erro`; a task nao virou `completed`. `/api/custos/status?limit=160`
  retornou `runs_bloqueados=1`, `custo_usd=None` e ainda
  `custos_persistencia_status=parcial_sem_token_usage_duravel`.
- Status: bloqueado por quota para concluir `CORRIGIR`/tools Gemini 2.5 Flash.
  Nao e aceito como full smoke, mas a falha silenciosa anterior foi corrigida.

### 2026-05-17 -- Sidebar mostra erro por aluno e etapa

- Alvo: tirar o diagnostico de falha do terminal e colocar no contrato vivo de
  progresso que a UI consome.
- Commit funcional: `98fafc9`.
- Mudancas: `routes_tasks.update_stage_progress()` agora aceita `error` e grava
  `students[aluno].stage_errors[etapa]`; `PipelineExecutor` envia mensagem,
  codigo, provider/modelo e documentos faltantes quando uma etapa falha; a
  sidebar de tarefas renderiza um bloco `tarefa-stage-error` abaixo da etapa
  vermelha.
- Testes locais: `py_compile`; `git diff --check`; suite focada com
  `test_pipeline_progress.py`, `test_erro_pipeline.py`,
  `test_a4_render_tarefas_tree.py`, `test_routes_tasks.py`,
  `test_hierarchy_rendering.py`, `test_taskqueue_refactor.py`,
  `test_backend_async_pipeline.py`, `test_backend_async_turma.py` e
  `test_cancel_buttons.py` passou com `154 passed`.
- Deploy: `/api/deploy-info` confirmou `98fafc9`; `/api/health` respondeu
  `healthy`; HTML live contem `stage_errors`, `renderStageError` e
  `tarefa-stage-error`.
- Smoke sem custo de IA: `task_7362d0fb1939`, apenas `extrair_respostas` para
  aluno inexistente na fixture Diana, falhou antes de provider com
  `students.smoke_sem_prova_stage_error.stage_errors.extrair_respostas.mensagem`
  igual a "Aluno smoke_sem_prova_stage_error nao tem prova_respondida enviada."
- Status: primeira camada de UI de erro por aluno/etapa publicada. Ainda falta
  levar a mesma clareza para telas de resultado/historico e para custos
  persistidos.

### 2026-05-17 -- `GERAR_RELATORIO` sem nota confiavel falha alto

- Alvo: remover a contencao antiga que podia colocar `nota_final=N/A` no prompt
  de relatório e permitir resultado final enganoso.
- Commit funcional: `ad7e00e`.
- Mudancas: `ERRO_NOTA_FINAL_INDETERMINADA` entrou no framework de erros;
  `_calcular_nota_final_de_correcoes()` retorna `None` quando não há número
  confiável; `GERAR_RELATORIO` bloqueia antes da IA quando não consegue
  determinar `nota_final` numérica por `nota_final`, `nota`, `questoes[].nota`
  ou `correcoes[].nota`; `_preparar_variaveis_texto()` não injeta mais `N/A`
  para `GERAR_RELATORIO`.
- Testes locais: `py_compile`; `git diff --check`; suite focada
  `test_erro_pipeline.py`, `test_stage_tool_pdf_quality.py` e
  `test_cost_tracking.py` passou com `101 passed`; suite ampliada de relatório,
  prompts, schema, visualizador e avisos passou com `164 passed, 3 skipped`.
- Deploy: `/api/deploy-info` confirmou `ad7e00e`; `/api/health` respondeu
  `healthy`.
- Smoke sem custo de IA: `task_d4947f5a3594`, apenas `gerar_relatorio` para
  aluno inexistente, falhou antes de provider com
  `stage_errors.gerar_relatorio.tipo=DOCUMENTO_FALTANTE` e
  `_documentos_faltantes=["correcoes","analise_habilidades"]`.
- Status: o fallback final `nota_final=N/A` deixou de ser aceitável no executor
  de relatório. Naquele momento ainda faltavam fallbacks/permissividades
  antigas; depois, `0d5ab9d` fechou o caso de JSON embrulhado em
  Markdown/prosa. Restam schema minimo Path 2 e parciais verdes.

### 2026-05-17 -- Guarda contra PDF auto-fallback estabilizada

- Alvo: confirmar que a regra P0 "sem PDF inventado" esta protegida por teste
  confiavel, em vez de depender de uma suite quebrada por mocks.
- Commit funcional/teste: `dc5884f`.
- Mudancas: `test_f7_t1_pdf_auto_fallback.py` agora injeta a classe real
  `ProviderAPIError` no mock de `chat_service` e usa um
  `ToolExecutionContext` minimo com `cost_run_id` serializavel. Os nomes dos
  testes tambem deixam claro que JSON-only deve falhar sem fallback.
- Validacoes locais: `python -m py_compile
  backend/tests/unit/test_f7_t1_pdf_auto_fallback.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_f7_t1_pdf_auto_fallback.py
  backend/tests/unit/test_e_t2_retry_partial_output.py
  backend/tests/unit/test_cost_tracking.py -q` com `49 passed`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh dc5884f`
  encontrou o hash apos 120s; `./scripts/check_deploy.sh dc5884f` passou;
  `/api/health` respondeu `healthy`.
- Status: nao havia patch de runtime neste ciclo. A descoberta importante e que
  o produto ja falha alto para saida dual incompleta, e agora o teste P0 mede
  isso sem falso vermelho. O item PDF auto-fallback sai da lista de "aberto no
  codigo atual" e fica como guarda a manter.

### 2026-05-17 -- JSON embrulhado em Markdown/prosa falha alto

- Alvo: remover a permissividade em que `_parsear_resposta()` podia extrair
  JSON por bloco Markdown ou regex e aceitar uma resposta que descumpriu a regra
  "APENAS JSON cru".
- Commit funcional: `0d5ab9d`.
- Mudancas: `_parsear_resposta()` agora calcula `stage` uma vez, valida que a
  raiz do JSON de etapa e objeto, retorna `invalid_json_root` para arrays na
  raiz e retorna `invalid_json_envelope` quando o JSON so aparece dentro de
  Markdown, comentarios ou texto ao redor. Sem `stage`, a compatibilidade dos
  testes utilitarios de parse permanece.
- Testes locais: `python -m py_compile backend/executor.py
  backend/tests/unit/test_erro_pipeline.py`; `git diff --check`;
  `PYTHONPATH=backend /home/otavio/Documents/vscode/.venv/bin/python -m pytest
  backend/tests/unit/test_erro_pipeline.py backend/tests/unit/test_executor_models.py
  backend/tests/unit/test_pipeline_validation.py backend/tests/unit/test_e_t2_retry_partial_output.py
  backend/tests/unit/test_f7_t1_pdf_auto_fallback.py backend/tests/unit/test_cost_tracking.py -q`
  com `161 passed, 3 skipped`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh 0d5ab9d`
  encontrou o hash apos 150s; `./scripts/check_deploy.sh 0d5ab9d` passou;
  `/api/health` respondeu `healthy`.
- Status: mais uma permissividade P0 saiu do caminho ativo da pipeline. Ainda
  falta fechar o contrato Path 2: `executar_com_tools()` retornar etapa real,
  `resposta_parsed` e `documento_id` principal, alem de validar schema minimo
  de cada etapa antes do sucesso.

### 2026-05-17 -- Path 2 retorna etapa real e JSON parseado

- Alvo: fechar parte do contrato D02-2, em que `executar_com_tools()` ainda
  retornava sucesso como etapa `"tools"` e sem `resposta_parsed`/documento
  principal no `ResultadoExecucao`.
- Commit funcional: `c870ed4`.
- Mudancas: sucesso de tool-use agora mapeia `TipoDocumento.CORRECAO` para
  `EtapaProcessamento.CORRIGIR`, `ANALISE_HABILIDADES` para
  `ANALISAR_HABILIDADES`, `RELATORIO_FINAL` para `GERAR_RELATORIO` e relatorios
  agregados para suas etapas reais. O executor carrega o JSON oficial
  persistido como `resposta_parsed` e `documento_id`; em testes sem storage,
  extrai o JSON do `create_document` da chamada de tool.
- Testes locais: `python -m py_compile backend/executor.py
  backend/tests/unit/test_e_t2_retry_partial_output.py`; `git diff --check`;
  suite dual-output/custo/PDF com `60 passed`; suite de migracao
  `corrigir`/`analisar_habilidades`/`gerar_relatorio` + erro/schema com
  `158 passed, 3 skipped`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh c870ed4`
  encontrou o hash apos 150s; `./scripts/check_deploy.sh c870ed4` passou;
  `/api/health` respondeu `healthy`.
- Status: D02-2 saiu de aberto puro para parcial melhorado. Ainda falta
  garantir schema minimo por etapa no objeto retornado e tratar todo parcial
  parseavel como erro alto antes de sucesso.

### 2026-05-17 -- Path 2 bloqueia JSON runtime fora do schema minimo

- Alvo: impedir que um `create_document` com JSON parseavel, mas fora do schema
  minimo da etapa, seja aceito como sucesso quando o teste nao simula storage
  persistido.
- Commit funcional: `45f5cf8`.
- Mudancas: a validacao de schema de tool-use foi extraida para
  `_json_schema_errors_for_data()` e agora cobre tanto JSON persistido em
  arquivo quanto payload runtime vindo do `create_document`. Para `CORRIGIR`,
  um JSON como `{"feedback_geral":"sem dados"}` falha por ausencia de
  `nota_final`, `questoes`, totais e `_avisos_*`, mesmo tendo PDF presente.
- Testes locais: `python -m py_compile backend/executor.py
  backend/tests/unit/test_e_t2_retry_partial_output.py`; `git diff --check`;
  suite dual-output/custo/PDF com `61 passed`; suite de migracao
  `corrigir`/`analisar_habilidades`/`gerar_relatorio` + erro/schema com
  `158 passed, 3 skipped`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh 45f5cf8`
  encontrou o hash apos 150s; `./scripts/check_deploy.sh 45f5cf8` passou;
  `/api/health` respondeu `healthy`.
- Status: D02-1 esta muito mais perto de fechado: JSON parseavel mas fora do
  schema de `CORRIGIR` nao passa no caminho runtime. Proximo ciclo deve decidir
  entre smoke barato sem IA, smoke de provider existente, ou seguir para parciais
  verdes/status historico.

### 2026-05-17 -- Smoke oficial reduzido confirma `corrigir` no runtime `45f5cf8`

- Alvo: validar no site oficial, com provider real, que o endurecimento do Path
  2 nao quebrou a etapa `corrigir` quando o modelo gera JSON/PDF validos, e que
  retry inconsistente fica marcado como erro em vez de falso sucesso.
- Fixture: atividade `f68d57a9a339081f` (`Smoke Paulo Pipeline 2026-05-16`),
  aluna `10d9fa4f4303ea1f` (Diana Omega), modelo `gpt54mini001`, apenas
  `selected_steps=["corrigir"]`, `force_rerun=true`.
- Deploy: `/api/deploy-info` confirmou `45f5cf8`;
  `./scripts/check_deploy.sh 45f5cf8` passou; `/api/health` respondeu
  `{"status":"healthy","supabase":true}`.
- Task: `task_42e3b303c39a` terminou `completed`, com `corrigir=completed` e
  `stage_errors={}`.
- Artefatos: JSON `776b70be01c24641`, PDF final `12dbdc65d469e982` e PDF
  intermediario `204a8a5c3f81af97` marcado `status=erro` por
  `pdf_json_consistency`. Isso e retry explicito, nao fallback: o modelo nao foi
  trocado e o erro ficou persistido no custo/resumo.
- Conteudo validado: JSON com `nota_final=8.0`, quatro questoes, Q3 `0.0/2.0`,
  `total_acertos=3`, `total_erros=1`, `_avisos_documento=[]`,
  `_avisos_questao=[]`, `_avisos_stage=CORRIGIR`. O PDF final extraido por
  `pdftotext` repete `Nota final 8.0`, notas por questao e feedback geral.
- Custos: `/api/custos/resumo?limit=80` agrupou o run
  `tool_9cf805ce976a` com provider `openai`, modelo `gpt-5.4-mini`,
  `tokens_entrada=26251`, `tokens_saida=4582`, `tokens_total=30833`,
  `custo_usd=0.040307`.
- Bloqueio ainda aberto: `/api/custos/status?limit=80` continua `ok=false`,
  `custos_persistencia_status=parcial_sem_token_usage_duravel` e Supabase
  `PGRST205` para `public.token_usage`. Custo de documento final esta medido;
  custo de falha sem documento final ainda nao e duravel.
- Status: GPT-5.4 Mini segue confirmado para `corrigir` nessa fixture simples
  pos-`45f5cf8`. Proximo ciclo tecnico deve atacar um bloqueador ainda aberto,
  nao repetir Rio 3: ou ampliar os testes de schema runtime para
  `ANALISAR_HABILIDADES`/`GERAR_RELATORIO`, ou resolver a durabilidade
  Supabase de `token_usage` quando houver credencial/admin.

### 2026-05-17 -- Cobertura anti-regressao para schema runtime tardio

- Alvo: fechar a lacuna de teste do ciclo `45f5cf8`. A implementacao ja
  validava payload runtime de `create_document` para `CORRIGIR`,
  `ANALISAR_HABILIDADES` e `GERAR_RELATORIO`, mas o teste automatizado cobria
  apenas `CORRIGIR`.
- Commit: `4094bda`.
- Mudanca: `backend/tests/unit/test_e_t2_retry_partial_output.py` ganhou teste
  parametrizado provando que `ANALISAR_HABILIDADES` falha alto sem
  `habilidades` e que `GERAR_RELATORIO` falha alto sem `nota_final`, mesmo que
  `create_document` tenha JSON parseavel e `execute_python_code` exista.
- Validacoes locais: `python -m py_compile
  backend/tests/unit/test_e_t2_retry_partial_output.py`; `git diff --check`;
  teste focado com `28 passed`; cesta dual-output/PDF/custos com `63 passed`;
  cesta de migracao/schema com `158 passed, 3 skipped`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh 4094bda`
  encontrou o hash apos 150s; `./scripts/check_deploy.sh 4094bda` passou;
  `/api/deploy-info` retornou `commit=4094bda`; `/api/health` respondeu
  `healthy`.
- Status: D02-1 fica mais protegido por teste, mas ainda nao fechado inteiro:
  restam artefatos parciais/duplicados/stale e qualidade semantica por provider.

### 2026-05-17 -- Cobertura D02-10 para PDF stale em retry dual-output

- Alvo: reforcar a prova de que retries dual-output nao deixam artefatos extras
  parecendo oficiais. Antes, a cobertura ja checava JSON stale; faltava PDF
  stale no mesmo contrato.
- Commit: `4d8f73d`.
- Mudanca: `backend/tests/unit/test_cost_tracking.py` agora simula uma correção
  com JSONs invalidos, JSON stale, PDF stale e JSON/PDF finais. O teste exige
  que o JSON stale e o PDF stale sejam marcados `StatusProcessamento.ERRO` com
  `metadata.erro_tipo=stale_tool_artifact`.
- Validacoes locais: `python -m py_compile backend/tests/unit/test_cost_tracking.py`;
  `git diff --check`; teste focado com `1 passed`; cesta dual-output/PDF/custos
  com `63 passed`; cesta de migracao/schema com `158 passed, 3 skipped`.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh 4d8f73d`
  encontrou o hash apos 150s; `./scripts/check_deploy.sh 4d8f73d` passou;
  `/api/deploy-info` retornou `commit=4d8f73d`; `/api/health` respondeu
  `healthy`.
- Status: D02-10 fica melhor coberto por teste, mas ainda pede smoke oficial de
  provider/site e verificacao de UI/historico obedecendo `status=erro`.

### 2026-05-17 -- Sweep de conexao dos providers e smoke Gemini bloqueado

- Alvo: atualizar o estado real dos providers existentes no site oficial, sem
  Rio 3 e sem usar segredo novo.
- Conexoes OpenAI: `gpt-4o`, GPT-4.1, GPT-5 Nano, GPT-5.4 Mini, o3 Mini e o4
  Mini retornaram `success=true` no endpoint
  `POST /api/settings/models/{id}/testar`.
- Conexoes Google: Gemini 2.5 Flash, Gemini 2.5 Flash Lite e Gemini 3 Flash
  retornaram `success=true`; Gemini 2.5 Pro retornou Google `429`.
- Conexoes Anthropic: Haiku 4.5 e Sonnet 4.5 continuam bloqueados por creditos
  Anthropic insuficientes.
- Smoke oficial Gemini 2.5 Flash: `task_e99a2c20be17`, fixture Diana Omega,
  `selected_steps=["corrigir"]`, `force_rerun=true`, modelo `gem25flash001`,
  runtime `4d8f73d`. Resultado: `status=failed`, `corrigir=failed`,
  `stage_errors.corrigir.provider=Google`, `codigo=429`, `retryable=true`,
  mensagem `RESOURCE_EXHAUSTED` por limite free-tier
  `generate_content_free_tier_requests` do modelo `gemini-2.5-flash`.
- Custos/documentos: nenhum novo documento de correcao apareceu para essa task;
  `/api/custos/resumo?limit=30` continuou mostrando o run Google antigo
  `338b25f9c0f74415` como bloqueado por `token_split_missing`, alem dos runs
  medidos anteriores. Como a chamada bateu quota antes de gerar artefato/tokens,
  o registro oficial novo fica no task-progress, nao em documento.
- Status: Gemini 2.5 Flash tem conexao viva e extracoes historicas medidas, mas
  `corrigir` segue bloqueado por quota, nao pipeline-ready. Nao trocar provider
  por baixo; repetir apenas quando quota liberar.

### 2026-05-17 -- Contrato tecnico e semantico de CORRIGIR

- Alvo: fechar D02-3/D02-4 e capturar o falso verde semantico exposto pelo
  smoke oficial das etapas finais.
- Commit tecnico: `f40acf3`.
  - `backend/prompts.py`: `PROMPTS_PADRAO` de `CORRIGIR`,
    `ANALISAR_HABILIDADES` e `GERAR_RELATORIO` agora aponta para o contrato de
    tool-use, sem schema legado contraditorio.
  - `backend/executor.py`: `ANALISE_HABILIDADES` exige `indicadores`,
    `recomendacoes` e `_avisos_*`; `RELATORIO_FINAL` exige `pontos_fortes`,
    `areas_melhoria`, `recomendacoes`, `detalhamento`, `_avisos_*` e
    `_fontes_utilizadas`.
  - Testes: `70 passed` na cesta tool-use/PDF/custos e `112 passed, 3 skipped`
    na cesta validacao/erros/modelos.
- Smoke em `f40acf3`: `task_9671e072f42c` passou, mas a auditoria rejeitou o
  resultado como falso verde semantico. A correcao JSON `acede2d27bc6c38a`
  transformou Q3 de `resposta_aluno=25` em acerto com `nota_final=10.0`.
- Commit semantico: `700b088`.
  - `CORRIGIR` agora deve copiar `resposta_aluno` e `resposta_correta` em cada
    questao; o runtime compara esses campos com `EXTRACAO_RESPOSTAS` e
    `EXTRACAO_GABARITO` quando eles existem.
  - Teste novo: `test_executar_com_tools_rejeita_correcao_que_troca_resposta_do_aluno`.
  - Validacoes: `py_compile`, `git diff --check`, `70 passed` na cesta
    tool-use/PDF/custos e `112 passed, 3 skipped` na cesta validacao/erros/modelos.
- Deploy: `git push origin HEAD:main`; `./scripts/wait_deploy.sh 700b088`
  encontrou o runtime apos 120s; `./scripts/check_deploy.sh 700b088` passou;
  `/api/deploy-info` retornou `commit=700b088`; `/api/health` respondeu
  `healthy`.
- Smoke oficial: `task_cc22b6c239d0`, fixture Diana Omega, modelo
  `gpt54mini001`, `selected_steps=["corrigir","analisar_habilidades","gerar_relatorio"]`.
  Resultado: `completed` sem `stage_errors`.
- Artefatos finais:
  - Correcao JSON `c3c680d099f781f7`, PDF `9814e0d8107b4d44`:
    `nota_final=8.0`, Q3 `resposta_aluno=25.`, `resposta_correta=30`,
    `nota=0.0/2.0`, `total_acertos=3`, `total_erros=1`.
  - Analise JSON `aabad9f809a388a3`, PDF `17575cac06b3e8f7`:
    `proficiencia_geral=0.8`, porcentagem em desenvolvimento.
  - Relatorio JSON `9bf0e1dac90a58c1`, PDF `a6f80bac65611376`:
    `nota_final=8.0`, `_fontes_utilizadas=["CORRIGIR","ANALISAR_HABILIDADES"]`.
- Custos: `/api/custos/resumo?limit=5` mostrou `56891/9827` tokens e
  `US$ 0.086890` nos tres runs OpenAI do smoke. `/api/custos/status?limit=80`
  continua `ok=false` por `token_usage_not_durable`/Supabase `PGRST205`.
- Status: GPT-5.4 Mini esta confirmado para as etapas finais nessa fixture
  simples pos-`700b088`. O proximo alvo real e ampliar a checagem semantica para
  mais tipos de resposta/datasets e resolver persistencia duravel de custos.

### 2026-05-17 -- CORRIGIR sem falso verde de literal, cabecalho e totais

- Alvo: continuar o loop depois do smoke `700b088`, sem tratar verde superficial
  como pronto.
- Commits:
  - `1307909`: bloqueia correcao que marca acerto/nota maxima quando
    `resposta_aluno` literal simples diverge de `resposta_correta` (ex.: `B`
    contra `C`).
  - `bed0c08`: adiciona metadados de aluno/materia/atividade ao prompt de
    `CORRIGIR` e bloqueia PDF de correcao que usa placeholder no cabecalho
    (`—`, `?`, `N/A`, `Nao informado`).
  - `feaf5d0`: bloqueia JSON de correcao cuja `nota_final` nao bate com a soma
    de `questoes[].nota`, ou cujos `total_acertos`/`total_erros` nao batem com
    `questoes[].acerto`.
- Validacoes locais:
  - `py_compile` dos arquivos Python tocados.
  - `git diff --check`.
  - `backend/tests/unit/test_cost_tracking.py`,
    `backend/tests/unit/test_stage_tool_pdf_quality.py`,
    `backend/tests/unit/test_e_t2_retry_partial_output.py`: `69 passed`.
  - `backend/tests/unit/test_erro_pipeline.py`: `73 passed`.
- Deploy:
  - `1307909`, `bed0c08` e `feaf5d0` foram publicados em `origin/main`.
  - `./scripts/wait_deploy.sh feaf5d0` encontrou o runtime apos 150s;
    `./scripts/check_deploy.sh feaf5d0`, `/api/deploy-info` e `/api/health`
    confirmaram o site oficial.
- Smokes oficiais:
  - `task_8f66a773d51a` em `1307909`: `corrigir` completou com Q3 errada e
    nota 8; custo `20598/3837`, `US$ 0.032715`.
  - `task_8905598b5ee7` em `bed0c08`: cabecalho real foi corrigido, mas o
    smoke revelou novo falso verde interno: JSON `6fb8bb49a07a8c9b` tinha
    `nota_final=9` apesar de as questoes somarem 8.
  - `task_ec7acffbb6d4` em `feaf5d0`: o primeiro JSON inconsistente
    `a6e92125cee2b4d4` foi marcado `status=erro` com
    `json_schema_validation`; o retry produziu JSON oficial
    `51f5a6a4536b60e7` e PDF `db4903bda7b4d2c0`, ambos coerentes:
    cabecalho `Diana Omega`/`Matemática-V`/atividade/data, `nota_final=8`,
    Q3 `25` vs `30`, `nota=0/2`.
- Custos: o run final `tool_a4afb35132b0` registrou `41137/5962` tokens,
  `US$ 0.057682`. `/api/custos/status?limit=80` segue `ok=false` por
  `token_usage_not_durable`/Supabase `PGRST205`.
- Status: `CORRIGIR` esta mais protegido para a fixture Diana em GPT-5.4 Mini.
  Proximos alvos continuam: persistencia duravel de custos, UI/historico de
  erro e revalidacao por provider/dataset maior.

### 2026-05-17 -- Resultado parcial nao conta `status=erro` como progresso

- Alvo: fechar a lacuna de UI/resultados em que existir arquivo parcial podia
  parecer etapa concluida mesmo quando o documento estava marcado
  `status=erro`.
- Mudanca: `/api/resultados/{atividade_id}/{aluno_id}` agora calcula progresso
  apenas com documentos `concluido`; documentos `erro`, `processando` ou
  `pendente` ficam visiveis com `status`, `erro_tipo`, `erro_execucao`,
  provider/modelo/tokens e entram em `documentos_com_erro`.
- Mudanca: o visualizador consolidado ignora documentos de correcao em
  `status=erro` para nao devolver `completo=true` quando so existe falha.
- Mudanca: a tela de resultado do aluno mostra banner de erro tambem para
  resultado parcial, destaca etapa com erro e marca cards de documento em erro.
- Validacoes locais: `py_compile` de `routes_resultados.py`,
  `visualizador.py` e `test_erro_pipeline.py`; `test_erro_pipeline.py`
  passou com `76 passed`; recorte de integracao `Visualizador or RoutesEndpoint`
  passou com `7 passed`; `git diff --check` passou.
- Limitacao registrada: a suite completa
  `test_erro_pipeline_integration.py` ainda tem 3 falhas antigas em testes que
  procuram texto dentro do PDF binario bruto do ReportLab; o recorte afetado
  por este ciclo passou.
- Commit/deploy: `b8e14db` (`fix: surface partial result error documents`)
  foi publicado em `origin/main`; `wait_deploy.sh` encontrou o runtime apos
  `180s`; `check_deploy.sh b8e14db9336789f2dfa74410738a2c903bc2fc8d` passou;
  `/api/deploy-info` retornou `full_commit=b8e14db9336789f2dfa74410738a2c903bc2fc8d`;
  `/api/health` respondeu `healthy`.
- Smoke oficial sem nova IA: HTML live em `/` contem `statusDoc`,
  `erroPipeline` e `Pipeline com Erro`; `/api/documentos` na fixture Diana
  (`f68d57a9a339081f`/`10d9fa4f4303ea1f`) expõe documentos `status=erro` e
  `erro_tipo=pdf_json_consistency`; `/api/resultados` para a mesma fixture
  segue `completo=true`, `aluno_nome=Diana Omega`, `nota_final=8.0`, porque ha
  retry concluido valido. Esse caso confirma a regra: retry concluido fecha a
  etapa, mas documentos de erro permanecem visiveis na lista/auditoria.
- Limite do smoke live: nao havia no resumo de custos uma fixture recente com
  apenas documento de erro e sem correcao concluida; essa parte do contrato foi
  coberta localmente por teste unitario da rota parcial.
- Status: publicado no site oficial. Proximo alvo de Sprint 4 e revisar
  historico/ranking/agregados para impedir que documentos `status=erro` virem
  nota/correcao valida em listas resumidas.

### 2026-05-17 -- Historico/status nao contam correcao em erro

- Alvo: continuar Sprint 4 nos agregados depois da rota/tela de resultado
  parcial. O problema era o mesmo falso verde em outra superficie: historico,
  pendencias e status de pipeline podiam responder "corrigido" quando havia
  apenas documento `CORRECAO` em `status=erro`.
- Mudanca: `VisualizadorResultados.get_historico_aluno_fast()` ignora correcoes
  em `status=erro` e tambem nao marca atividade como corrigida quando o JSON
  concluido nao produz nota numerica.
- Mudanca: `VisualizadorResultados.get_resultado_aluno()` tambem deixa de
  devolver `completo=true` quando a correcao concluida nao tem nota numerica nem
  questoes/correcoes avaliaveis; isso fecha o falso verde observado no aluno
  Eric/Lista0, que aparecia com `nota_final=0` e `total_questoes=0`.
- Mudanca: `get_comparativo_questao()` passa a escolher somente documentos
  concluidos para questoes/gabarito/respostas/correcao, evitando comparativo
  baseado em artefato parcial ou falho.
- Mudanca: `/api/alunos/{aluno_id}/atividades-pendentes` e
  `/api/pipeline/status/{atividade_id}` consideram correção/respostas/prova
  como presentes apenas quando o documento esta `concluido`; para correcao, o
  status agora usa o resultado consolidado confiavel, nao a mera existencia de
  arquivo.
- Validacoes locais: `py_compile` de `visualizador.py`, `routes_resultados.py`,
  `routes_pipeline.py` e testes; `test_student_fast_paths.py` passou com
  `10 passed`; `test_erro_pipeline.py` passou com `79 passed`;
  `git diff --check` passou.
- Commits/deploys:
  - `a1f6375` publicou a primeira parte: historico rapido, comparativo,
    atividades pendentes e status pipeline ignorando documentos `status=erro`;
    Render confirmou em 150s.
  - O smoke live em Eric/Lista0 revelou que ainda havia falso verde quando a
    correcao era `concluido`, mas sem questoes/correcoes avaliaveis
    (`nota_final=0`, `total_questoes=0`).
  - `27c6b16` tentou bloquear nota numerica sem nota confiavel, mas o smoke
    mostrou que o dado antigo ainda passava.
  - `325c200` endureceu a regra: correcao so vira resultado completo/status
    pronto se houver ao menos uma questao/correcao com nota. Render confirmou
    `325c20023fa940766b9dcf116b9a2bcbc8765e7d` em 180s; `check_deploy.sh`,
    `/api/deploy-info` e `/api/health` passaram.
- Smokes oficiais sem nova IA:
  - Eric/Lista0 (`126e8b5ad7dd6d59`/`660e9421b246ad3f`):
    `/api/resultados` agora retorna `completo=false`, etapa `correcao` com
    `status=erro` e `erro_tipo=CORRECAO_SEM_NOTA_CONFIAVEL`;
    `/api/pipeline/status` retorna `correcao=false`;
    `/api/alunos/.../historico` retorna `corrigido=false`, `nota=null`;
    `/api/alunos/.../atividades-pendentes` retorna `aguardando_correcao`.
  - Diana/fixture simples (`f68d57a9a339081f`/`10d9fa4f4303ea1f`) continua
    `completo=true`, `aluno_nome=Diana Omega`, `nota_final=8.0`.
- Status: publicado no site oficial. Proximo alvo de Sprint 4 e revisar ranking
  de turma/dashboard e mensagens de erro para provider/custo com a mesma
  clareza.

### 2026-05-17 -- Ranking/dashboard: rota estatica e nota zero

- Alvo: continuar a validacao de agregados apos `325c200`.
- Achado live: `/api/resultados/126e8b5ad7dd6d59/ranking` estava sendo
  capturado pela rota dinamica `/api/resultados/{atividade_id}/{aluno_id}` e
  retornava resultado parcial para um aluno ficticio `ranking`, nao o ranking.
- Achado live: o dashboard de turma usava `if media`, entao uma media legitima
  `0` aparecia como `null`, enquanto `atividades_corrigidas` ficava `1`.
- Mudanca: as rotas estaticas de ranking/estatisticas foram registradas antes
  da rota dinamica; os wrappers antigos agora usam helpers compartilhados.
- Mudanca: medias zero em dashboard/historico/comparativos sao preservadas com
  `is not None`, sem transformar `0` em `null`.
- Validacoes locais: `py_compile` de `routes_resultados.py`; `git diff --check`;
  `test_erro_pipeline.py` passou com `81 passed`, incluindo teste de ordem das
  rotas e media zero no dashboard.
- Commit/deploy: `148d8b3` (`fix: protect ranking routes and zero averages`)
  publicado em `origin/main`; Render confirmou
  `148d8b30e2a2a126792d8c94831cd1ae69f5e3f6` em 210s por
  `./scripts/check_deploy.sh`, `/api/deploy-info` e `/api/health`.
- Smoke live de agregados:
  - `/api/resultados/126e8b5ad7dd6d59/estatisticas` voltou a responder
    estatisticas reais, com `corrigidos=19`, `pendentes=44`,
    `media=1.2415789473684211` e `menor_nota=0.0`.
  - `/api/resultados/126e8b5ad7dd6d59/ranking` voltou a responder ranking real:
    `total=63`; Eric (`660e9421b246ad3f`) aparece como `corrigido=false`,
    `nota=null`, `posicao=0`; Alice (`9b0f104fa9e7c5d9`) preserva
    `nota=0.0`, `corrigido=true`, `posicao=7`.
  - `/api/dashboard/turma/3f3ab03dfe783f30` preserva Eric com `media=null` e
    Alice com `media=0.0`.
- Achado que abriu o ciclo seguinte: dashboard/ranking de turma grande ainda
  era lento no site oficial (dashboard levou cerca de 85s para parsear a
  resposta da Lista0). O alvo virou reduzir leituras repetidas/N+1 nos
  agregados sem relaxar as regras de erro alto.

### 2026-05-17 -- Ranking/dashboard: agregados em lote

- Alvo: corrigir o gargalo de agregados descoberto apos `148d8b3`.
- Causa provavel: `get_ranking_turma` chamava `get_resultado_aluno` para cada
  aluno; `dashboard_turma` ainda percorria aluno por aluno por atividade para
  calcular medias. Na Lista0, isso multiplicava leituras de documentos e JSONs.
- Mudanca: `get_ranking_turma` agora busca as correcoes concluidas da atividade
  em lote via `_select_rows`, agrupa por aluno, le somente o JSON de correcao
  escolhido e usa a mesma regra de nota confiavel: nota numerica so conta se
  houver item avaliavel em `questoes[]` ou `correcoes[]`.
- Mudanca: `dashboard_turma` reutiliza o ranking de cada atividade para montar
  estatisticas e medias por aluno, em vez de chamar resultado detalhado para
  cada par aluno/atividade.
- Validacoes locais: `py_compile` de `visualizador.py`, `routes_resultados.py`
  e testes; `git diff --check`; `test_student_fast_paths.py` +
  `test_erro_pipeline.py` passaram juntos com `92 passed`.
- Commit/deploy: `147296d` (`fix: batch ranking dashboard aggregates`)
  publicado em `origin/main`; Render confirmou
  `147296d5f3c93a7687c76ce11e09c2c6d1a60f40` em 150s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live sem nova IA:
  - `/api/resultados/126e8b5ad7dd6d59/estatisticas`: primeiro acesso apos
    deploy levou `12.315s`; repeticoes aquecidas ficaram entre `0.907s` e
    `1.309s`, com `corrigidos=19`, `pendentes=44`, `media=1.2415789473684211`
    e `menor_nota=0.0`.
  - `/api/resultados/126e8b5ad7dd6d59/ranking`: repeticoes ficaram entre
    `0.818s` e `1.126s`, `total=63`; Eric segue `corrigido=false`,
    `nota=null`; Alice segue `corrigido=true`, `nota=0.0`, `posicao=7`.
  - `/api/dashboard/turma/3f3ab03dfe783f30`: `1.433s`, `63` alunos e `1`
    atividade; Eric segue com `atividades_corrigidas=0`, `media=null`; Alice
    segue com `atividades_corrigidas=1`, `media=0.0`.
- Status: publicado e smokeado no site oficial. Proximo alvo do loop: voltar
  para provider/custo/pipeline, priorizando falhas ainda abertas de mensagens
  provider/custo e persistencia duravel de `token_usage`.

### 2026-05-17 -- Modelo padrao: sair de provider bloqueado

- Alvo: evitar que execucoes sem escolha explicita de modelo usem Claude Haiku
  4.5 enquanto Anthropic segue bloqueado por credito.
- Achado live sem gastar IA: `/api/settings/status` mostrava
  `modelo_padrao.id=588f3efe7975`, `tipo=anthropic`,
  `modelo=claude-haiku-4-5-20251001`, apesar dos smokes/documentos marcarem
  Haiku como bloqueado por credito. Isso criava falha previsivel para fluxo
  default.
- Mudanca: `backend/data/models.json` passou a marcar `gpt54mini001`
  (`gpt-5.4-mini`) como unico default e Haiku como nao default.
- Mudanca: `ModelManager._ensure_single_default()` deixou de preferir Haiku ao
  corrigir defaults corrompidos e passou a preferir modelo OpenAI operacional
  conhecido (`gpt54mini001`, depois GPT-4.1/GPT-4o, depois outro OpenAI ativo).
- Validacoes locais: `py_compile` de `chat_service.py` e testes de modelo;
  `git diff --check`; `test_model_manager.py` +
  `test_gpt5_nano_registration.py` passaram com `63 passed`.
- Commit/deploy: `22f6f31` (`fix: default to confirmed openai model`)
  publicado em `origin/main`; Render confirmou
  `22f6f315a12e34d0a15597eca82743f09314046f` em 180s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live sem nova IA: `/api/settings/status` e `/api/settings/models`
  retornaram `total_modelos=14` e um unico default:
  `id=gpt54mini001`, `tipo=openai`, `modelo=gpt-5.4-mini`,
  `suporta_function_calling=true`.
- Status: publicado e smokeado no site oficial. Proximo alvo do loop: custo
  duravel (`token_usage` no Supabase) ou smoke minimo de provider escolhido por
  evidencia, sem usar Rio 3 e sem aceitar fallback silencioso.

### 2026-05-17 -- Custos: resumo estruturado de erro de provider

- Alvo: deixar o resumo de custos legivel quando provider falha, sem depender
  de JSON bruto enorme de erro.
- Achado live: `/api/custos/resumo?limit=80` ja media custos, mas amostras de
  erro Google `429` carregavam blocos longos de `erro_execucao`; isso dificultava
  UI, docs e agentes entenderem rapidamente se era quota, schema, provider ou
  custo ausente.
- Mudanca: `cost_tracking.py` agora adiciona campos derivados:
  `erro_resumo` truncado, `erro_codigo`, `erro_provider_status`,
  `erro_provider_modelo` e `erro_categoria` (`quota_exhausted` quando detecta
  quota/`RESOURCE_EXHAUSTED`). O erro bruto continua por compatibilidade, mas o
  caminho recomendado para UI/docs passa a ser o resumo estruturado.
- Validacoes locais: `py_compile` de `cost_tracking.py`; `git diff --check`;
  `test_cost_tracking.py` passou com `26 passed`.
- Commit/deploy: `48407f2` (`fix: summarize provider cost errors`) publicado
  em `origin/main`; Render confirmou
  `48407f2be70b538ad38550366fcef0be33c1dc90` em 150s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live sem nova IA: `/api/custos/resumo?limit=80` retornou
  `runs_analisados=44`, `runs_precificados=42`, `runs_bloqueados=2`,
  `custo_usd=1.033313`, `token_usage_durable=false`; encontrou `4` amostras de
  quota com `erro_codigo=429`, `erro_provider_status=RESOURCE_EXHAUSTED`,
  `erro_provider_modelo=gemini-2.5-flash-lite` e
  `erro_categoria=quota_exhausted`.
- Status: publicado e smokeado no site oficial. Bloqueio remanescente:
  `public.token_usage` segue ausente no Supabase (`PGRST205`), entao falhas sem
  documento final ainda nao tem persistencia duravel.

### 2026-05-17 -- Custos: diagnostico explicito da migration `token_usage`

- Alvo: fazer o bloqueio de custo duravel aparecer como acao objetiva no
  endpoint, nao apenas como string bruta de Supabase.
- Achado: a UI ja tentava mostrar `token_usage_backend.error_code`, mas
  `TokenUsageStore.status()` nao preenchia esse campo; o status carregava apenas
  a mensagem raw truncada.
- Mudanca: `token_usage.py` passou a extrair codigos como `PGRST205` do erro do
  Supabase e adicionou `missing_migration` e `migration_path` no objeto
  `token_usage_backend.supabase`.
- Validacoes locais: `py_compile` de `token_usage.py`; `git diff --check`;
  `test_cost_tracking.py` passou com `27 passed`.
- Commit/deploy: `50fb1d7` (`fix: expose token usage migration status`)
  publicado em `origin/main`; Render confirmou
  `50fb1d704bb9c72e775376a0cb627c0a71e44b27` em 150s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live: `/api/custos/status?limit=80` retornou `ok=false`,
  `custos_persistencia_status=parcial_sem_token_usage_duravel`,
  `token_usage_durable=false`, `supabase_enabled=true`,
  `table_available=false`, `error_code=PGRST205`,
  `missing_migration=true` e
  `migration_path=backend/migrations/002_create_token_usage.sql`.
- Status: diagnostico publicado e smokeado. Bloqueio real permanece externo:
  aplicar a migration no Supabase ou disponibilizar credencial/caminho admin
  para que Paulo rode a SQL sem expor segredo.

### 2026-05-17 -- Dashboard: alerta visivel da migration `token_usage`

- Alvo: fazer o bloqueio de custo duravel aparecer no site oficial, nao apenas
  no JSON de `/api/custos/status`.
- Achado: o frontend lia `tokenUsageBackend.error_code`, mas o backend publicado
  em `50fb1d7` entrega `error_code`, `missing_migration` e `migration_path`
  dentro de `token_usage_backend.supabase`.
- Mudanca: `frontend/index_v2.html` agora le tambem o objeto Supabase aninhado e
  monta o alerta com `Codigo: PGRST205` e
  `backend/migrations/002_create_token_usage.sql` quando a migration estiver
  ausente.
- Validacoes locais: `py_compile` de `test_frontend_cost_status_ui.py`;
  `git diff --check`; `test_frontend_cost_status_ui.py` passou com `4 passed`.
- Commit/deploy: `e2260d2` (`fix: show token usage migration details in dashboard`)
  publicado em `origin/main`; Render confirmou
  `e2260d26ca06d0a9598689bcef2c4b7d800385d8` em 180s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live: HTML oficial contem `tokenUsageSupabase.error_code`,
  `tokenUsageSupabase.missing_migration === true`,
  `backend/migrations/002_create_token_usage.sql` e `Custos não duráveis`.
  `/api/custos/status?limit=80` segue retornando `ok=false`,
  `error_code=PGRST205`, `missing_migration=true` e o mesmo `migration_path`.
- Status: UI publicada e smokeada. Bloqueio real permanece externo: a tabela
  `public.token_usage` ainda precisa existir no Supabase.

### 2026-05-17 -- Custos: agregado oficial por etapa e sweep de providers

- Alvo: deixar custos consultaveis por etapa de pipeline, alem de provider e
  run, e atualizar o estado real dos providers configurados.
- Sweep de conexao via `/api/settings/models/{id}/testar`: OpenAI OK para
  `gpt-4o`, `o3-mini`, `gpt-4.1`, `o4-mini`, `gpt-5-nano` e
  `gpt-5.4-mini`; Google OK para `gemini-2.5-flash`,
  `gemini-2.5-flash-lite` e `gemini-3-flash-preview`; Google Pro bloqueado por
  quota `429`; Claude Haiku/Sonnet 4.5 bloqueados por credito Anthropic; Ollama
  local indisponivel no Render.
- Smoke de pipeline: `task_a1f7521077a5`, runtime `e2260d2`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gpt54mini001`,
  `force_rerun=true`, seis etapas `completed` e sem `stage_errors`.
- Observacao operacional: a primeira chamada Python nao recebeu o `task_id`, mas
  `/api/tasks` mostrou a task registrada e concluida; a repeticao curta via
  `curl` (`task_a0ac9628c0fa`, apenas `corrigir`) retornou `task_id` em
  `1.27s` e completou. Monitorar se a perda de resposta inicial voltar a
  ocorrer.
- Mudanca: `cost_tracking.py` passou a expor `etapa`, `etapa_origem` e agregado
  `por_etapa`; quando a etapa vem da metadata, `etapa_origem=metadata`; quando
  so vem do tipo do documento, `etapa_origem=tipo_documento`.
- Validacoes locais: `py_compile` de `cost_tracking.py` e
  `test_cost_tracking.py`; `git diff --check`; `test_cost_tracking.py` passou
  com `28 passed`.
- Commit/deploy: `ae04982` (`fix: expose cost totals by pipeline stage`)
  publicado em `origin/main`; Render confirmou
  `ae04982250877dc12da5a01be16edc2eaa43b5bd` em 180s por
  `./scripts/wait_deploy.sh`, `./scripts/check_deploy.sh`, `/api/deploy-info`
  e `/api/health`.
- Smoke live de custo: `/api/custos/resumo?limit=120` retornou
  `runs_analisados=59`, `runs_precificados=57`, `runs_bloqueados=2`,
  `custo_usd=1.404252`, `token_usage_durable=false` e `por_etapa` com
  `correcao=US$ 0.755318`, `analise_habilidades=US$ 0.311354`,
  `relatorio_final=US$ 0.261663`, `extrair_gabarito=US$ 0.026077`,
  `extrair_respostas=US$ 0.026308` e `extrair_questoes=US$ 0.023532`.
- Status: custo por etapa publicado e smokeado. Bloqueio real remanescente:
  aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para
  tornar falhas sem documento duraveis.

### 2026-05-17 -- Provider: Gemini 2.5 Flash ainda bloqueado em pipeline

- Alvo: distinguir conexao simples OK de pipeline-stage realmente operavel.
- Smoke: `task_41c45d7939b5`, runtime `ae04982`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gem25flash001`,
  `selected_steps=["corrigir"]`, `force_rerun=true`.
- Resultado: task `failed`; `corrigir=failed`; `stage_errors.corrigir` trouxe
  `provider=Google`, `codigo=429`, `retryable=true`, mensagem
  `RESOURCE_EXHAUSTED`, modelo `gemini-2.5-flash`, limite free tier `20` e
  sugestao de retry do provider.
- Custos/erros: `/api/custos/resumo?limit=120` manteve
  `runs_analisados=59`, `runs_precificados=57`, `runs_bloqueados=2` e mostrou
  amostras de quota Google categorizadas; a tentativa Gemini 2.5 Flash apareceu
  como erro `quota_exhausted` em `correcao`, mas com `tokens_entrada=0` e
  `tokens_saida=0`, portanto nao foi precificada.
- Status: Gemini 2.5 Flash nao esta pipeline-ready agora. O sistema falhou alto
  e nao fez fallback para OpenAI.

### 2026-05-17 -- Provider: GPT-5 Nano passa `extrair_respostas` na fixture simples

- Alvo: revalidar o ponto mais sensivel do Nano na fixture Diana, sem extrapolar
  para dataset maior.
- Smoke: `task_0818b99194aa`, runtime `ae04982`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gpt5nano001`,
  `selected_steps=["extrair_respostas"]`, `force_rerun=true`.
- Resultado: task `completed`; `extrair_respostas=completed`; sem
  `stage_errors`.
- Documento: `f021525b6fdf0db0`, `status=concluido`, provider/modelo
  `openai/gpt-5-nano`, `tokens_entrada=2286`, `tokens_saida=1998`,
  `tokens_total=4284`, `tempo_processamento_ms=14522.7`.
- Conteudo verificado: 4 respostas reais (`x = 5`, `34`, `25`, `20 cm2`),
  `questoes_respondidas=4`, `questoes_em_branco=0`, sem avisos no JSON.
- Custo live: `/api/custos/resumo?limit=120` precificou o run
  `f021525b6fdf0db0` em `US$ 0.000914`; `extrair_respostas` subiu para
  `8` runs, `tokens_entrada=18620`, `tokens_saida=4070`,
  `custo_usd=0.027222`.
- Status: Nano fica confirmado para `extrair_respostas` nessa fixture simples,
  mas nao vira pipeline-ready em dataset maior sem novos smokes de qualidade.

### 2026-05-17 -- Provider: GPT-5 Nano passa `corrigir` com retries visiveis

- Alvo: testar o ponto historicamente perigoso do Nano: JSON/PDF divergente em
  `CORRIGIR`.
- Smoke: `task_960c0a287a13`, runtime `ae04982`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gpt5nano001`,
  `selected_steps=["corrigir"]`, `force_rerun=true`.
- Resultado: task `completed`; `corrigir=completed`; sem `stage_errors` finais.
- Artefatos oficiais: JSON `d6ae91c76625c82b` e PDF `1ba9013486b61342`,
  ambos `status=concluido`, provider/modelo `openai/gpt-5-nano`,
  `tokens_entrada=33949`, `tokens_saida=8630`, `tokens_total=42579`,
  `cost_run_id=tool_fe3dec8d7c1c`.
- Conteudo verificado: `nota_final=8.0`; Q1 `3/3`, Q2 `3/3`, Q3 `0/2` por
  porcentagem `25` vs `30`, Q4 `2/2`; `total_acertos=3`, `total_erros=1`.
- Erros intermediarios preservados: JSON `9bf3a79a50ec0ff7` falhou por
  `json_schema_validation`; PDF `a643037bf008e890` falhou por
  `pdf_json_consistency`; JSON `2804464ef6056e8b` foi marcado
  `stale_tool_artifact`. Isso e retry explicito no mesmo modelo, nao fallback.
- Custo live: `/api/custos/resumo?limit=140` precificou
  `tool_fe3dec8d7c1c` em `US$ 0.005149`; o resumo retornou
  `runs_analisados=73`, `runs_precificados=71`, `runs_bloqueados=2` e
  `custo_usd=1.478610`.
- Status: Nano fica confirmado para `corrigir` nessa fixture simples com
  retries visiveis, mas ainda nao vira pipeline-ready em datasets maiores.

### 2026-05-17 -- Provider: GPT-5 Nano passa etapas finais com ressalva de aviso

- Alvo: fechar `ANALISAR_HABILIDADES` e `GERAR_RELATORIO` do Nano na fixture
  Diana, usando a correcao oficial recente.
- Smoke: `task_fa50cb3ffc16`, runtime `ae04982`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gpt5nano001`,
  `selected_steps=["analisar_habilidades","gerar_relatorio"]`,
  `force_rerun=true`.
- Resultado: task `completed`; `analisar_habilidades=completed` e
  `gerar_relatorio=completed`; sem `stage_errors`.
- Analise: JSON `2d8d88a985a24701` e PDF `9267575cffe1d443`, ambos
  `status=concluido`, `cost_run_id=tool_318aee5ffa98`,
  `tokens_entrada=16729`, `tokens_saida=3614`, custo `US$ 0.002282`.
- Relatorio: JSON `f94add68a8a7f8e3` e PDF `139a6e500184e13d`, ambos
  `status=concluido`, `cost_run_id=tool_ba65fbf2385a`,
  `tokens_entrada=14352`, `tokens_saida=2986`, custo `US$ 0.001912`.
- Conteudo verificado: relatorio manteve `nota_final=8.0`, fontes
  `CORRIGIR` e `ANALISAR_HABILIDADES`, foco em porcentagem como area de
  melhoria; analise marcou proficiencia geral `0.83`.
- Ressalva: `_avisos_questao.codigo` no relatorio veio como string composta
  `ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE`; isso deve virar alvo de
  schema/avisos, porque codigo de aviso composto pode confundir UI/analise.
- Custo live: `/api/custos/resumo?limit=160` retornou `runs_analisados=85`,
  `runs_precificados=83`, `runs_bloqueados=2`, `custo_usd=1.599386`.
- Status: Nano fica confirmado nas etapas finais da fixture simples, com
  ressalva aberta para normalizar codigos de aviso.

### 2026-05-17 -- Schema/avisos: codigo composto virou erro alto e smoke passou

- Alvo: corrigir a ressalva do smoke Nano em que `_avisos_questao.codigo`
  apareceu como `ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE`.
- Mudanca: commit `ed592de` removeu exemplos `A|B|C` de `executor.py` e
  `prompts.py`, adicionou instrucao explicita de um codigo por aviso, e passou
  a validar codigos em `pipeline_validation.py` e no caminho runtime de
  `executar_com_tools`.
- Regra agora: `_avisos_documento` aceita somente `ILLEGIBLE_DOCUMENT`,
  `MISSING_CONTENT` ou `LOW_CONFIDENCE`; `_avisos_questao` aceita somente
  `ILLEGIBLE_QUESTION`, `MISSING_CONTENT` ou `LOW_CONFIDENCE`. Codigo composto
  com `|` deve falhar alto ou acionar retry explicito no mesmo modelo.
- Validacao local: `py_compile` dos arquivos tocados, `git diff --check` e
  `pytest` focado em `test_pipeline_validation.py`, `test_warning_system.py` e
  `test_e_t2_retry_partial_output.py`: `141 passed`, `3 skipped`, `1 warning`
  de config `timeout`.
- Deploy oficial: `origin/main` e Render chegaram a
  `ed592de1f2a04523a54b8d0662fe8ed29069d08b`; `wait_deploy.sh` achou o hash
  em 150s; `check_deploy.sh` e `/api/health` passaram.
- Smoke oficial pos-fix: `task_0c7339f48aec`, runtime `ed592de`, atividade
  `f68d57a9a339081f`, aluna `10d9fa4f4303ea1f`, modelo `gpt5nano001`,
  `selected_steps=["gerar_relatorio"]`, `force_rerun=true`.
- Resultado: task `completed`; `gerar_relatorio=completed`; sem
  `stage_errors`.
- Artefatos oficiais: JSON `e0bd0926113e66bd` e PDF `170ce2985e0356e7`,
  ambos `status=concluido`, provider/modelo `openai/gpt-5-nano`,
  `cost_run_id=tool_c491ce8289ee`, `tokens_entrada=66621`,
  `tokens_saida=6703`, `tokens_total=73324`.
- Conteudo verificado: relatorio manteve `nota_final=8.0`, fontes
  `CORRIGIR` e `ANALISAR_HABILIDADES`, e `_avisos_questao[0].codigo` veio como
  `ILLEGIBLE_QUESTION`, sem `|`.
- Custo live: `/api/custos/resumo?limit=240` precificou o run
  `tool_c491ce8289ee` em `US$ 0.006012`; o agregado `relatorio_final` ficou
  com `15` runs, `tokens_entrada=375223`, `tokens_saida=54884`,
  `custo_usd=0.687618`. O total geral observado ficou em
  `runs_analisados=102`, `runs_precificados=100`, `runs_bloqueados=2`,
  `custo_usd=2.694486`.
- Bloqueio que permanece: `/api/custos/status?limit=80` ainda retorna
  `ok=false`, `token_usage_backend.durable=false` e Supabase `PGRST205` para
  `public.token_usage`; aplicar `backend/migrations/002_create_token_usage.sql`
  continua sendo gate externo para custo duravel de falhas sem documento.
- Proximo alvo: continuar a matriz por provider/custo. Gemini segue bloqueado
  por quota `429`, Anthropic por credito, e Nano/GPT-5.4 Mini precisam de
  smokes em datasets menos simples antes de virarem pipeline-ready geral.

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
