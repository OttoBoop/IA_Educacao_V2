# Matriz Provider × Fase — Status Atual

**Atualizado:** 2026-05-16
**Atividade de teste:** Lista0 — Algebra Linear Avancada (`126e8b5ad7dd6d59`)
**Commits aplicados/observados:** `a632883`, `5737611`, `50935ea`, `479b77d`,
`b12be9a`, `301eba6`, `f67055c`, `462ea1d`, `b4d7ee6`, `99483d1`,
`f505be6`, `d75b05a`, `97a7c79`, `ec95193`, `ff7b92a`, `68ebe51`,
`c75af88`, `45d543a`, `39aa50a`, `3ddf6c5`, `b24f03e`, `6ed31a4`,
`eab7d90`, `dcecdfa`, `7ed8b8b`, `9e1aee5`, `839968e`, `45c6f97`,
`55e168a`, `9823afb`, `4f27dae`, `f0dae61`, `87bdee2`, `b2dc88b`,
`28cfd6a`, `cacedcd`, `a311ade`, `924fd79`, `0dfdbbe`, `d653c13`,
`2947178`, `53d0252`, `f55e299`, `5f10651`, `e6060e1`, `a7dead3`,
`5527e26`, `2792d89`, `23282d7`, `7d0c874`, `8dd6c54`, `c1598b9`,
`01fb04c`, `6b57ef1`, `3b9eedc`, `b8b8693`, `283e8c6`, `1ce3d23`

## Status Oficial De Deploy

- Render MCP confirmou em 2026-05-16 o servico oficial
  `srv-d5t8gbh4tr6s738fr3s0` (`IA_Educacao_V2`), branch `main`,
  `rootDir=backend`, URL `https://ia-educacao-v2.onrender.com`.
- `list_deploys` marcou o deploy `dep-d841f437uimc73fs60lg` como `live`,
  apontando para o commit funcional
  `1ce3d2314c278d853bb7e6c74105e628d1a19b9c`. Os deploys `283e8c6`,
  `b8b8693`, `3b9eedc`, `01fb04c`, `c1598b9`, `8dd6c54` e `5527e26`
  aparecem como historicos/deactivated.
- O HTML live ainda aponta `novocr-deploy=e6060e1`. Isso e marker stale, nao
  prova de runtime antigo: commits de frontend/docs/marker podem nao disparar
  deploy quando o servico Render usa `rootDir=backend`.
- Os smokes abaixo devem dizer qual evidencia oficial usam: marker HTML quando
  aplicavel, Render MCP/lista de deploys quando o runtime for confirmado por
  commit backend, e sempre comportamento live por endpoint.
- Depois do smoke de `extrair_questoes`, o commit `f55e299` foi publicado para
  destacar tarefas longas do ciclo da requisicao; marker `5f10651` foi publicado
  no GitHub, mas ainda precisa confirmacao Render.
- O commit `e6060e1` bloqueia as rotas legadas sincrônicas
  `/api/pipeline/executar` e `/api/pipeline/executar-com-tools` com `410 Gone`;
  marker `a7dead3` foi publicado no GitHub, mas ainda precisa confirmacao Render.
- Em producao, as duas rotas legadas ja retornaram `410`, provando
  comportamento backend de `e6060e1`; porem o HTML marker ainda foi observado em
  `f55e299`, entao a confirmacao por marker segue pendente. `wait_deploy.sh
  e6060e1` deu timeout apos 600s.
- O commit `5527e26` adiciona o guard anti-gabarito-tudo-`MISSING_CONTENT` e
  remove o fallback Markdown de relatorio; marker `2792d89` aponta o HTML para
  `5527e26`, mas o HTML nao atualizou. Render MCP confirmou o runtime
  `5527e26` como live antes dos deploys posteriores.
- O commit `8dd6c54` adicionou guard anti-respostas-tudo-`ilegivel`, mas o smoke
  seguinte mostrou que a task ainda salvava tudo `em_branco=true`.
- O commit `c1598b9` ampliou a validacao para todas as respostas sem conteudo,
  mas o smoke seguinte provou que a validacao central nao estava no caminho real
  do executor multimodal.
- O commit `01fb04c` bloqueou o mesmo caso diretamente no executor; Render MCP
  confirmou `01fb04c` live e o smoke `task_b511641dfa52` falhou alto sem salvar
  novo documento verde.
- Depois disso, os commits `6b57ef1`, `3b9eedc`, `b8b8693`, `283e8c6` e
  `1ce3d23` tentaram corrigir a qualidade real de `extrair_respostas` Nano:
  adicionaram questoes/texto do PDF/imagens, proibiram inferencia do enunciado e
  bloquearam JSON vazio inconsistente. O runtime live atual e `1ce3d23`; o smoke
  final `task_3d5feaf0da71` falhou alto sem documento verde e registrou custo em
  `usage_52590d55d210459e`.
- Tambem em producao, uma pipeline sequencial completa Gemini (`task_5e97bbee896e`)
  confirmou que o runner destacado nao prende a resposta inicial e mantem
  `/api/health` saudavel, mas falhou alto em `corrigir` por quota Google/Gemini
  `429`. As tres extracoes dessa mesma task passaram com custo/metadata; as
  etapas finais ficaram pendentes.
- `origin/main` tambem contem a migration dedicada `b2dc88b`
  (`backend/migrations/002_create_token_usage.sql`), ainda nao aplicada ao
  Supabase de producao.
- Render live chegou a `1ce3d23` pela lista de deploys do Render MCP; o marker
  HTML segue atrasado em `e6060e1`.
- Docs antigos registram que auto-deploy Git nao funciona de forma confiavel; o
  ciclo usou deploy via API Render com token local seguro, sem imprimir segredo.
- Smokes live anteriores continuam citados com seus markers; smokes de
  2026-05-16 usam Render MCP/lista de deploys como fonte oficial quando o marker
  HTML fica atrasado.

## Legenda

- ✅ **OK** — Etapa rodou, JSON valido, conteudo faz sentido
- ⚠️ **PARCIAL** — Rodou mas com problemas (sem avisos, schema antigo, nao persistiu, etc.)
- ❌ **FALHA** — Nao rodou ou retornou erro
- ⏸️ **NAO TESTADO** — Ainda nao foi testado
- 🚫 **BLOQUEADO** — Nao pode testar (creditos, overload, etc.)

---

## Matriz Consolidada — 3 Categorias por Provider

### Categoria 1: Pipeline do Aluno (6 etapas)

| Provider/Modelo | EXTRAIR_QUESTOES | EXTRAIR_GABARITO | EXTRAIR_RESPOSTAS | CORRIGIR | ANALISAR_HABILIDADES | GERAR_RELATORIO |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Claude Haiku 4.5** (`588f3efe7975`) | ⏸️ | ⏸️ | ⏸️ | 🚫 | 🚫 | 🚫 |
| **Gemini 3 Flash** (`gem3flash001`) | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| **GPT-5 Nano** (`gpt5nano001`) | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| **GPT-5.4 Mini** (`gpt54mini001`) | ⏸️ | ⏸️ | ✅ | ⏸️ | ⏸️ | ⏸️ |
| **GPT-4o** (`180b8298a279`) — referencia | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |

Nota de leitura: os checks da tabela acima sao por etapa individual validada.
Eles nao significam que a pipeline completa de 6 etapas passou em uma unica
task. Em 2026-05-16, Gemini completou as tres extracoes em uma task sequencial,
mas parou em `corrigir` por quota `429`.
Nota P0: `extrair_gabarito` Gemini continua ❌ porque o output retornou todas
as respostas como `MISSING_CONTENT`, embora o PDF base tenha texto extraivel de
"Exercicio 5". Nano tinha a mesma falha historica em `task_2da0fb90c3fb`, mas
foi revalidado apos `5527e26` na task `task_dc719eeea626`, com JSON
`5f433f9a1bc30842` e 7 respostas reais. Schema parseavel e custo medido nao
bastam; conteudo precisa fazer sentido.
Nota P0 adicional: `extrair_respostas` Nano rodou em
`task_a9ff0d69d5e9`, mas o JSON `b968c9539f277deb` marcou todas as 7 respostas
como `ilegivel=true`, embora o PDF `f60d37284d616ca4` tenha texto extraivel da
questao 7. Isso e falha de conteudo, nao validacao. Depois disso, `8dd6c54`
ainda deixou passar tudo `em_branco=true` (`2a518dfb6b2a03ef`) e `c1598b9`
ainda deixou passar porque a validacao central nao estava no caminho real do
executor (`10d1c1d9741a6273`). Desde `01fb04c`, o smoke
`task_b511641dfa52` falha alto. A rodada posterior melhorou entrada e guards:
`3b9eedc` criou `6b28875e8a9fdc73` com apenas Q7 real; `b8b8693` criou
`893987838fd275bd` com conteudo demais e suspeita de inferencia; `283e8c6`
criou `ff0882e8db71e79d`, mais honesto, mas ainda verde inconsistente; por fim
`1ce3d23` fez `task_3d5feaf0da71` falhar alto e registrar custo sem documento
(`usage_52590d55d210459e`). Portanto a matriz mantem Nano
`EXTRAIR_RESPOSTAS` como ❌ por qualidade de extracao, e o comportamento de
produto contra falso sucesso esta corrigido para vazio total, inferencia obvia,
JSON vazio inconsistente e scan majoritariamente sem conteudo.
Nota de candidato: `gpt-5.4-mini` passou no smoke como cadastro efemero
`04b31001cf81` antes do deploy seguinte; depois ficou claro que modelos criados
via settings em disco Render nao sobrevivem deploy. O candidato duravel passa a
ser `gpt54mini001` em `backend/data/models.json`. No smoke `task_9c10e3752bcb`,
`EXTRAIR_RESPOSTAS` completou com documento `a39d26fcc621c7a8`, 4/7 respostas
com conteudo real, 3/7 marcadas como `MISSING_CONTENT`, tokens `97004/1942` e
custo `US$ 0.081492`. Isso valida a etapa nessa amostra, nao pipeline completa.

### Categoria 2: Relatorios de Desempenho (3 niveis)

| Provider/Modelo | DESEMPENHO_TAREFA | DESEMPENHO_TURMA | DESEMPENHO_MATERIA |
|-----------------|:---:|:---:|:---:|
| **Claude Haiku 4.5** | ⏸️ | ⏸️ | ⏸️ |
| **Gemini 3 Flash** | ⏸️ (sendo testado) | ⏸️ | ⏸️ |
| **GPT-5 Nano** | ⏸️ | ⏸️ | ⏸️ |
| **GPT-4o** | ⏸️ | ⏸️ | ⏸️ |

### Categoria 3: Chat Interativo (`POST /api/chat`)

| Provider/Modelo | Chat |
|-----------------|:---:|
| **Claude Haiku 4.5** | ⏸️ |
| **Gemini 3 Flash** | ✅ |
| **GPT-5 Nano** | ✅ |
| **GPT-4o** | ⏸️ |

**Smokes live de chat em 2026-05-15:**
- Gemini 3 Flash (`gem3flash001`): respondeu JSON simples, 585 tokens, HTTP 200.
- GPT-5 Nano (`gpt5nano001`): respondeu JSON simples, 526 tokens, HTTP 200.
- Claude Haiku 4.5 (`588f3efe7975`): HTTP 500 com erro Anthropic de credito
  baixo. Bloqueado por billing, nao por codigo do chat.

**Smoke live de pipeline em 2026-05-15:**
- Gemini 3 Flash (`gem3flash001`) em `pipeline-completo`, aluno Eric,
  `selected_steps=["corrigir"]`, task `task_e22dbdbffe4d`: terminou `failed`,
  com `corrigir=failed`. A resposta de `/api/task-progress/{task_id}` nao
  trazia `error`, entao a causa ficou invisivel no site. Resultado: Gemini
  continua OK em chat, mas nao esta confirmado para pipeline pos-fix.
- Depois do deploy `b4d7ee6`, o mesmo smoke gerou task `task_08d4648d7053` e
  falhou de novo em `corrigir`, agora com causa visivel: Google API 503
  `UNAVAILABLE`, alta demanda temporaria do modelo. Resultado: o erro nao esta
  mais silencioso; Gemini segue nao confirmado para pipeline.
- Patch Sprint 4b local: 429/5xx em tool-use agora preserva `retryable=True` e
  `erro_codigo`, para o retry acontecer no mesmo modelo de forma visivel.
- Depois do deploy `f505be6`/`97a7c79`, Gemini 3 Flash em `corrigir` completou
  na task `task_8f53987c57c4`, gerando JSON `6396c4feb3d5b92b` e PDF
  `6c62faa4ce6df137` com tokens/custo medidos.
- GPT-5 Nano em `corrigir` falhou alto na task `task_49b7ada546d4`: nao produziu
  JSON/PDF obrigatorios e nao houve fallback automatico.
- Patch `ff7b92a` publicado no GitHub tenta corrigir esse ponto usando
  `tool_choice="required"` no primeiro request OpenAI e tool-choice especifico
  no retry de reparo.
- Depois do deploy `c75af88`, GPT-5 Nano completou `corrigir`
  (`task_edb822810ddc`), mas o JSON principal nao parseava
  (`Invalid control character`). Isso rebaixou o resultado: artefato persistido
  sem JSON valido nao basta.
- Depois do deploy `39aa50a`, GPT-5 Nano completou `corrigir`
  (`task_1a7857360267`) com JSON parseavel `d3a4be288960e301`, PDF via
  `execute_python_code` `3e0d534238dc0067`, tokens 20.127/6.817 e custo
  `US$ 0.003733`. Observacao: criou tambem PDF extra via `create_document`
  (`29d20245529f26a7`), a restringir em ciclo futuro.
- Em 2026-05-16, GPT-5 Nano passou em `extrair_questoes` na task
  `task_ae679b5c3fee`, gerando JSON `946e66708fd72643` com 7 questoes,
  `_avisos_*`, tokens `2148/12147` e custo `US$ 0.004966`.
- Em seguida, GPT-5 Nano em `extrair_gabarito` (`task_2da0fb90c3fb`) gerou JSON
  `61fb077d746c2a55`, tokens `78104/3635`, custo `US$ 0.005359`, mas marcou
  todas as 7 respostas como `MISSING_CONTENT`; reclassificado como falha de
  conteudo.
- Depois do deploy Render MCP `5527e26`, GPT-5 Nano em `extrair_gabarito`
  (`task_dc719eeea626`) completou com JSON `5f433f9a1bc30842`, 7 respostas
  reais, tokens `78104/8353` e custo `US$ 0.007246`. A etapa volta a ✅ para
  Nano neste exemplo; ainda falta `extrair_respostas` e pipeline completa.
- Depois do deploy `b24f03e`, GPT-5 Nano em `corrigir` falhou sem falso sucesso
  na task `task_c460627779fc`, mas o erro ficou cru demais:
  `tools: 'str' object has no attribute 'get'`. Causa: payload malformado em
  `documents` dentro de `create_document`.
- Depois do deploy `eab7d90`, GPT-5 Nano completou `corrigir`
  (`task_a591421ab84b`) com JSON parseavel `42dc1fcd758e913b`, PDF via
  `execute_python_code` `cd72e7233ee061ad`, tokens 16.081/3.470 e custo
  `US$ 0.002192`. Nao houve PDF extra via `create_document`.
- Depois do deploy `7ed8b8b`, `/api/custos/resumo` passou a agrupar amostras por
  `cost_run_id`. O ultimo run Nano `tool_056e2e1f7179` aparece uma vez, com
  `documentos_contagem=2`, documentos JSON+PDF e custo unico `US$ 0.002192`.
- Depois do deploy `839968e`, `/api/custos/status` passou a expor
  `token_usage_analisados`; o live retornou `0`, como esperado enquanto nenhuma
  nova falha sem documento ocorrer. O caminho e local mensal
  `data/token_usage/YYYY-MM.json`, ainda nao Supabase.
- Depois do deploy `55e168a`, o codigo ficou preparado para Supabase
  `token_usage` e a migration declara a tabela. O live segue retornando
  `token_usage_analisados=0`; a aplicacao da migration no banco ainda nao foi
  confirmada.
- Depois do deploy `4f27dae`, `/api/custos/status` passou a diagnosticar o
  backend de token usage. Resultado live: Supabase ligado, mas
  `token_usage_backend.supabase.table_available=false`, `durable=false`, erro
  `PGRST205` porque `public.token_usage` nao existe no schema cache.
- Depois disso, `b2dc88b` criou a migration dedicada
  `backend/migrations/002_create_token_usage.sql`. Isso e preparo de banco,
  nao prova de persistencia: a matriz so pode marcar custo de falha como duravel
  quando o endpoint live retornar `table_available=true`.
- Depois disso, Gemini 3 Flash passou em `analisar_habilidades`
  (`task_a78369e23e5c`) e `gerar_relatorio` (`task_58fb48fc8324`) no Render
  live `4f27dae`. A primeira gerou JSON `7904a6a1aa34131f` e PDF
  `245970da4cc42c02`, 15.993/3.874 tokens, `US$ 0.009447`; a segunda gerou
  JSON `fe6ad549481a0ed9` e PDF `b815d1faa5aeab77`, 9.215/2.796 tokens,
  `US$ 0.006120`.
- No marker live `924fd79`, Gemini 3 Flash passou em `extrair_questoes`
  (`task_737c8d45befc`), com JSONs `3f1ca7eed14f5d37` e
  `9d61dcb36e6ca4b5`, ambos parseados e com `questoes`,
  `total_questoes`, `pontuacao_total` e `_avisos_*`. Tokens/custos:
  `1602/1938`, `US$ 0.002806`, e `1602/1934`, `US$ 0.002801`. A duplicacao
  veio de retry operacional apos timeout de cliente; nao deve ser repetida como
  comportamento normal.
- Depois do deploy do runner destacado, Gemini 3 Flash passou em
  `extrair_gabarito` (`task_094c921eb038`): a resposta inicial voltou em
  `1.155s` com `task_id`, `/api/health` ficou saudavel em 20 polls, e o JSON
  `36d1fdd0a453e2f5` registrou tokens `65018/727`, custo `US$ 0.020378`,
  `respostas` e avisos `MISSING_CONTENT` para questoes ausentes no gabarito de
  origem. Reclassificacao posterior: o PDF base continha texto de Q5, mas esse
  output marcou todas as questoes como `MISSING_CONTENT`; portanto nao e
  validacao de conteudo, apenas prova de execucao/schema/custo.
- Gemini 3 Flash tambem passou em `extrair_respostas`
  (`task_7d357943288d`): resposta inicial em `1.002s`, health saudavel, JSON
  `59cb3e341515d745`, tokens `70414/1791`, custo `US$ 0.023273`, aluno real e
  questoes ausentes marcadas como `em_branco=true` sem inventar resposta.
- GPT-5 Nano falhou alto em `analisar_habilidades` (`task_43d48d9deea2`):
  nao gerou PDF obrigatorio via `execute_python_code`; o erro ficou visivel na
  task e nao houve fallback. Dois JSONs parciais foram marcados `status=erro`
  (`3648e6629e7d6b04`, `a67c0f394f0133e7`) com tokens 25.237/8.024,
  custo `US$ 0.004471`, `cost_run_id=tool_58b8188d8fad`. Problema novo:
  nome/conteudo generico `student123`.
- Patch `924fd79` reforca o retry de PDF/JSON mantendo o contexto original da
  etapa e proibindo placeholders; esta live e o smoke Nano de 2026-05-16 passou.
- Patch `d653c13` faz JSON de `ANALISAR_HABILIDADES` com placeholder proibido
  falhar alto mesmo quando JSON+PDF existem; ainda aguarda deploy e smoke
  especifico desse guard.
- No marker live `924fd79`, GPT-5 Nano passou em `analisar_habilidades`
  (`task_020ba25bdb2b`): JSON `ba5dec781e46e665`, PDF
  `385f6b78018b8c07`, tokens `22817/5969`, custo `US$ 0.003528`,
  `cost_run_id=tool_8948b7aa5731`. O JSON usa aluno real e nao contem
  placeholders proibidos (`student123`, `aluno_teste`, `nome_do_aluno`, `<str>`,
  `student_name`).
- No mesmo marker, GPT-5 Nano passou em `gerar_relatorio`
  (`task_aec830b85c03`): JSON `200c1b5272ba10f1`, PDF
  `a629dee567b10274`, tokens `24520/5305`, custo `US$ 0.003348`,
  `cost_run_id=tool_9ce5bf31c005`. O JSON traz `nota_final=1.43`,
  `resumo_geral`, `recomendacoes`, `_avisos_*` e fontes usadas; o PDF resolve
  em disco pelo debug endpoint.
- No deploy live `5527e26` confirmado por Render MCP, GPT-5 Nano passou em
  `extrair_gabarito` (`task_dc719eeea626`): JSON `5f433f9a1bc30842`,
  `status=concluido`, provider/modelo `openai/gpt-5-nano`, tokens
  `78104/8353`, custo `US$ 0.007246`, e 7 respostas reais sem
  `MISSING_CONTENT`.
- No mesmo runtime, GPT-5 Nano em `extrair_respostas`
  (`task_a9ff0d69d5e9`) completou com JSON `b968c9539f277deb`, tokens
  `85774/3002` e custo `US$ 0.005489`, mas marcou todas as 7 respostas como
  `ilegivel=true`. Como o PDF da prova tem texto extraivel de Q7, a etapa foi
  reclassificada como ❌.
- Depois do deploy `8dd6c54`, GPT-5 Nano em `extrair_respostas`
  (`task_03ae99db3006`) ainda completou verde com JSON `2a518dfb6b2a03ef`,
  agora marcando todas as respostas como `em_branco=true`.
- Depois do deploy `c1598b9`, GPT-5 Nano em `extrair_respostas`
  (`task_6772978a20c4`) ainda completou verde com JSON `10d1c1d9741a6273`;
  isso provou que a validacao Pydantic nao estava sendo aplicada no caminho real
  do executor multimodal.
- Depois do deploy `01fb04c`, GPT-5 Nano em `extrair_respostas`
  (`task_b511641dfa52`) falhou alto com erro explicito de respostas sem conteudo
  extraido. A listagem de documentos confirmou que nenhum novo
  `extracao_respostas` verde foi criado apos `10d1c1d9741a6273`.
- Depois dos deploys `6b57ef1`, `3b9eedc`, `b8b8693`, `283e8c6` e `1ce3d23`,
  o sistema passou a carregar questoes no prompt, inserir texto extraido do PDF,
  anexar paginas escaneadas como imagem, proibir inferencia do enunciado e
  bloquear JSON inconsistente/scan majoritariamente vazio. O smoke final
  `task_3d5feaf0da71` falhou alto, sem novo documento verde, e registrou
  `TokenUsageRecord` `usage_52590d55d210459e` com custo `US$ 0.008555`.
- GPT-5.4 Mini foi testado como candidato explicito para a mesma etapa:
  `task_9c10e3752bcb` completou, JSON `a39d26fcc621c7a8`, provider/modelo
  `openai/gpt-5.4-mini`, tokens `97004/1942`, custo `US$ 0.081492`,
  4 respostas extraidas e 3 questoes marcadas como sem resposta visivel. Antes
  do smoke, `from-catalog` retornou 500 e o create basico ignorou capabilities;
  o patch `b16e051` corrigiu settings e o reteste pos-deploy criou
  `d1e2d1851836` com capabilities corretas. Como o cadastro por API sumiu apos
  deploy, o candidato precisa ficar versionado como `gpt54mini001`.

**Gemini 3 Flash:** tambem validado em 2 testes historicos de chat (mensagem unica + multi-turn). Ver [teste_chat_gemini.md](arquivo_2026_04_17/teste_chat_gemini.md).
- Teste 1: 662 tokens, 1930ms, resposta em PT correta
- Teste 2: 2502 tokens, 14993ms, usou contexto do histórico
- Sem templates `{{...}}`
- Zero retries necessários

**Achado colateral** (não bloqueia, mas reportar): `/api/chat` está usando o **system prompt do fluxo de correção de provas** ("Você é um assistente educacional especializado em correção de provas..."). Consequência: Gemini anexou espontaneamente um PDF base64 no teste 2. Sugere que `/api/chat` deveria ter system prompt próprio mais neutro.

---

## Detalhamento por Provider

### Claude Haiku 4.5 — 🚫 BLOQUEADO

**Motivo:** Creditos Anthropic insuficientes. O smoke live de chat em
2026-05-15 retornou erro Anthropic "Your credit balance is too low".

**Acao necessaria (Otavio):** Recarregar creditos na conta Anthropic. Nenhum teste possivel ate la.

---

### Gemini 3 Flash Preview — ✅ ETAPAS FINAIS DO ALUNO POS-FIX VALIDADAS

**Smoke live pos-fix:** `pipeline-completo` com apenas `corrigir` falhou em
2026-05-15. Antes do patch, a task nao expôs `error`; depois do deploy
`b4d7ee6`, a causa apareceu: Google API 503 `UNAVAILABLE` por alta demanda.
Depois do deploy `f505be6`, a repeticao `task_8f53987c57c4` completou em
`corrigir`, com custo medido. Depois do deploy `4f27dae`, Gemini tambem passou
em `analisar_habilidades` e `gerar_relatorio`, com custo medido. Depois do
marker `924fd79`, `extrair_questoes` tambem passou com custo medido. Depois do
runner destacado, `extrair_gabarito` e `extrair_respostas` passaram com custo
medido e health saudavel. As 6 etapas individuais do aluno estao validadas para
Gemini. A primeira pipeline sequencial completa pos-runner (`task_5e97bbee896e`)
passou por `extrair_questoes`, `extrair_gabarito` e `extrair_respostas`, mas
falhou alto em `corrigir` por quota Google/Gemini `429`, sem troca silenciosa de
modelo e sem marcar as etapas finais como sucesso.

**Historico positivo via `pipeline-completo`** para Eric Manoel antes dos commits
`b12be9a`/Sprint 3b (ver [teste_gemini_pipeline_completo.md](arquivo_2026_04_17/teste_gemini_pipeline_completo.md)).

**Tentativa 1:** Falhou em ~30s (provavelmente 503 transiente)
**Tentativa 2:** SUCESSO em ~105s, 3 documentos gerados

| Etapa | Status | Doc JSON | Doc PDF |
|-------|--------|----------|---------|
| CORRIGIR | ✅ | `bb0f0c63f75589dd` | `b3a786693fc384df` |
| ANALISAR_HABILIDADES | ✅ | `f6e7fa7ef961bf15` | `085a078eebb5ef93` |
| GERAR_RELATORIO | ✅ | `26697c8894eca2ad` | `4a00dcef2eed4ea3` |

**Verificacoes que passaram na epoca:**
- Nota final consistente cross-stage: **7.01**
- Avisos `MISSING_CONTENT` propagaram corretamente para Q2 e Q4 (questoes em branco)
- Todos os 3 JSONs tem `_avisos_documento`, `_avisos_questao` (com 2 itens reais!), `_avisos_stage`
- Conteudo qualitativamente correto (Vandermonde+Julia, decomposicoes matriciais, forward substitution, minimos quadrados)

**Ressalvas:**
1. `tokens_usados=0` e `ia_modelo=null` no metadata do DB foram bugs observados
   no teste historico; Sprint 3b corrige o preenchimento localmente, mas ainda
   precisa smoke oficial.
2. 50% de falha na primeira tentativa (precisa mais amostras para confiar sem retry)
3. Endpoint `/conteudo` retorna metadata, nao conteudo — usar `/view` (gap de contrato)

---

### GPT-5 Nano — ✅ CHAT SIMPLES, ✅ ETAPAS FINAIS POS-FIX VALIDADAS

**Smoke live de chat em 2026-05-15:** respondeu JSON simples corretamente via
`POST /api/chat` com `model_id=gpt5nano001` e 526 tokens. Portanto o bloqueio
inicial do Nano nao era conexao/API key; era pipeline/tool-use/schema.

**Smoke live de `corrigir` em 2026-05-15:** depois dos patches `ff7b92a`,
`c75af88`, `39aa50a`, `b24f03e` e `eab7d90`, a task `task_a591421ab84b`
completou com JSON parseavel, PDF obrigatorio via `execute_python_code`,
provider/modelo/tokens/custo no storage e sem PDF extra via `create_document`.
Ainda nao estava pipeline-ready porque faltavam as etapas seguintes e schema
minimo por etapa.

**Smoke live de `analisar_habilidades` em 2026-05-15:** task
`task_43d48d9deea2` falhou alto: PDF obrigatorio nao foi produzido por
`execute_python_code`. O sistema nao inventou PDF nem marcou sucesso. Dois JSONs
parciais ficaram `status=erro`, com custo medido, mas usam placeholder
`student123`; isso e bug de prompt/schema/qualidade.

**Smokes live em 2026-05-16 no marker `924fd79`:** `analisar_habilidades`
passou na task `task_020ba25bdb2b` e `gerar_relatorio` passou na task
`task_aec830b85c03`, ambos com JSON+PDF, provider/modelo, tokens splitados,
custo por `cost_run_id` e sem placeholders proibidos nos JSONs novos. O patch
anti-placeholder `d653c13` e ancestral dos deploys atuais, mas ainda falta
smoke especifico se esse risco voltar a aparecer.

**Testado em 2 caminhos com resultados muito diferentes:**

#### Via `/executar/etapa` — ⚠️ PARCIAL
Ver [teste_executar_etapa_corrigido.md](arquivo_2026_04_17/teste_executar_etapa_corrigido.md). Gerou nota 5.72/10 com feedback coerente, mas sem `_avisos_*`, schema flat, sem persistencia.

#### Via `pipeline-completo` historico — ❌ FALHA GRAVE
Ver [teste_gpt5nano_pipeline_completo.md](arquivo_2026_04_17/teste_gpt5nano_pipeline_completo.md). Task `task_ca3769cfdc97` terminou em `failed` em ~23s.

**Bugs descobertos no tool-use path:**
1. **Multiplas chamadas `create_document` por stage** (deveria ser 1) — criou 3 docs lixo: JSON malformado, txt vazio, texto natural salvo em arquivo `.json`
2. **Nomes/extensoes alucinadas:** `document_2.txt`, `correcao_henrique.pdf.json`
3. **Sem validacao de schema** — stage marcada como "completed" apesar de outputs inutilizaveis
4. **Metadata nula no DB:** `ia_provider`, `ia_modelo`, `tokens_usados`, `prompt_usado` ficaram null/0
5. **Cascade de falha:** `analisar_habilidades` falhou (nao achou correcao valida), `gerar_relatorio` nem executou
6. **`_avisos_*` NAO aparecem** — hipotese de que tool-use path injetaria foi **refutada**
7. **Schema ainda flat** — GPT-5 Nano nao segue STAGE_TOOL_INSTRUCTIONS mesmo em pipeline-completo

**Bugs corrigidos depois desse historico:**
1. OpenAI dual-output inicia com `tool_choice="required"` e retry forca a tool
   faltante quando conhecida (`ff7b92a`).
2. Sucesso exige artefato persistido por tool, nao apenas nome de tool
   (`c75af88`).
3. `.json` salvo por `create_document` precisa parsear antes de entrar no
   storage; dual-output exige `.json` por `create_document` e `.pdf` por
   `execute_python_code` (`39aa50a`).
4. Em etapa de pipeline, `create_document` nao pode salvar PDF/artefato nao-JSON;
   esses arquivos pertencem a `execute_python_code` (`b24f03e`).
5. Payload `documents` malformado vira erro estruturado da tool, nao excecao
   Python crua (`eab7d90`).

---

### GPT-4o — ⚠️ PARCIAL (modelo de referencia/fallback anterior)

**Testado via `pipeline-completo`** para Eric Manoel (ver [teste_haiku_eric.md](arquivo_2026_04_17/teste_haiku_eric.md))

| Etapa | Status | Doc ID | Tokens In | Tokens Out | Tempo |
|-------|--------|--------|-----------|------------|-------|
| CORRIGIR | ✅ | `53642cb495a0be3b` | 92.639 | 291 | 15.7s |
| ANALISAR_HABILIDADES | ✅ | `38998862379fd325` | 66.068 | 412 | 14.8s |
| GERAR_RELATORIO | ✅ | `186a822b5ce1db5c` | 60.634 | 492 | 11.5s |

**Problemas identificados:**
1. ⚠️ **Sem campos `_avisos_*`** — nenhum dos 3 documentos contem avisos (teste anterior aos commits de injecao).
2. ⚠️ **Schema antigo** — `correcao` usa flat format, nao STAGE_TOOL_INSTRUCTIONS.
3. ⚠️ **Variaveis duplicadas** — ~50 arquivos enviados por chamada (docs base duplicados na atividade).

**Nao testado:** as 3 etapas de extracao (foram feitas antes, sem registro de qual modelo gerou).

---

## Testes Pendentes (para fechar Marco 1)

### Prioridade ALTA
- [x] Rodar Gemini 3 Flash em `analisar_habilidades` e `gerar_relatorio` com
      custo/metadata
- [x] Rodar Gemini 3 Flash em `extrair_questoes` com custo/metadata
- [x] Rodar Gemini 3 Flash em `extrair_gabarito` com custo/metadata e health
      responsivo durante a execucao
- [ ] Rerodar Gemini 3 Flash em `extrair_gabarito` apos guard anti-tudo-
      `MISSING_CONTENT`; execucao anterior foi reclassificada como conteudo
      invalido
- [x] Confirmar deploy `5527e26`: Render MCP mostrou deploy live
      `dep-d83spamq1p3s73f0ks20` em `5527e265...`; o marker HTML segue
      atrasado em `e6060e1`
- [x] Confirmar deploy `01fb04c`: Render MCP mostrou deploy live
      `dep-d83tp2m7r5hc73d7o7d0` em `01fb04c060...`; o smoke
      `task_b511641dfa52` provou falha alta de `extrair_respostas` sem novo
      documento verde
- [x] Confirmar deploy `1ce3d23`: Render MCP mostrou deploy live
      `dep-d841f437uimc73fs60lg` em `1ce3d23...`; o smoke
      `task_3d5feaf0da71` provou falha alta final de `extrair_respostas` sem
      documento verde e com custo de falha em `usage_52590d55d210459e`
- [x] Rodar Gemini 3 Flash em `extrair_respostas` com custo/metadata e health
      responsivo durante a execucao
- [x] Validar que `f55e299` elimina timeout/indisponibilidade na resposta
      imediata do `pipeline-completo`
- [x] Confirmar que `e6060e1` faz rotas legadas sincrônicas retornarem `410`
      rapidamente em producao
- [x] Rodar primeira pipeline sequencial completa Gemini pos-runner e registrar
      o bloqueio real: quota Google/Gemini `429` em `corrigir`, nao falha de
      health nem timeout de requisicao
- [ ] Repetir pipeline sequencial completa Gemini quando quota/credito permitir,
      sem retry cego e sem trocar modelo
- [ ] Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase e revalidar
      `token_usage_backend.supabase.table_available=true`
- [x] Preparar codigo para persistir `TokenUsageRecord` em Supabase quando a
      tabela existir
- [x] Criar registro local mensal de custo de falhas sem documento final
- [x] Auditar se `/api/custos/resumo` soma por documento em vez de por
      `cost_run_id`
- [x] Restringir ou marcar como erro artefato extra `create_document` nao-JSON em
      etapas dual-output
- [ ] Investigar por que `/executar/etapa` nao persiste documento (gap ou by-design?)

### Prioridade MEDIA
- [x] Validar `corrigir` com GPT-5 Nano para 1 aluno no site oficial
- [x] Corrigir/validar GPT-5 Nano em `analisar_habilidades` no marker
      `924fd79`, com JSON+PDF e custo
- [x] Confirmar runtime com `d653c13` incluido: deploy live `5527e26` e
      descendente de `d653c13`
- [ ] Rerodar smoke especifico do guard anti-placeholder se esse risco voltar a
      aparecer
- [x] Validar `gerar_relatorio` com GPT-5 Nano apos `analisar_habilidades`
- [ ] Testar Haiku 4.5 (bloqueado ate creditos recarregarem)

### Prioridade BAIXA
- [ ] Testar GPT-5 Nano nas 6 etapas (as etapas `extrair_questoes`,
      `extrair_gabarito`, `corrigir`, `analisar_habilidades` e
      `gerar_relatorio` ja passaram; `extrair_respostas` rodou mas foi
      reclassificada como conteudo invalido por tudo `ilegivel`/vazio,
      inferencia suspeita ou scan majoritariamente sem conteudo; desde
      `1ce3d23`, o falso sucesso final foi bloqueado, mas ainda falta fazer a
      etapa extrair conteudo real e depois rodar pipeline completa)
- [ ] Comparar qualidade dos outputs entre os 3 modelos-alvo

---

## Resumo Executivo (atualizado)

**Estado atual:**
- ⚠️ **Gemini 3 Flash:** chat simples live OK; `corrigir`,
  `analisar_habilidades`, `gerar_relatorio`, `extrair_questoes`,
  e `extrair_respostas` pos-fix OK com custo/metadata. `extrair_gabarito`
  rodou, mas foi reclassificado como invalido porque retornou tudo
  `MISSING_CONTENT`.
  Pipeline sequencial completa pos-runner chegou a `corrigir` e falhou alto por
  quota `429`; falta repetir quando quota permitir.
- ⚠️ **GPT-5 Nano via `pipeline-completo`:** `extrair_questoes`,
  `extrair_gabarito`, `corrigir`, `analisar_habilidades` e `gerar_relatorio`
  passaram em smokes oficiais com JSON/PDF quando aplicavel, custo e metadata.
  `extrair_respostas` rodou varias vezes, mas foi reclassificada como falha de
  conteudo por tudo `ilegivel=true`/vazio, por inferencia suspeita do enunciado
  ou por scan majoritariamente sem conteudo. O deploy `1ce3d23` corrigiu o
  falso sucesso final: agora esse caso falha alto, nao cria documento verde e
  registra custo de falha (`usage_52590d55d210459e`). Ainda faltam corrigir a
  extracao real de respostas, rodar pipeline completa de 6 etapas, schema minimo
  por etapa e custo duravel de falhas sem documento final.
- ✅ **GPT-5.4 Mini candidato OCR:** `extrair_respostas` passou em uma amostra
  oficial (`task_9c10e3752bcb`, doc `a39d26fcc621c7a8`) com custo `US$ 0.081492`.
  Ainda nao foi testado em pipeline completa nem nas outras etapas.
- ⏸️ **Claude Haiku 4.5:** Aguardando creditos.
- 📊 **Confiabilidade Gemini 3 Flash:** etapas individuais OK, mas a primeira
  pipeline sequencial pos-runner bateu quota `429` em `corrigir`. Precisa duas
  execucoes completas quando quota/credito permitir.

**Marco 1 ainda nao atingido oficialmente:** chat, etapas individuais e a
pipeline sequencial parcial ajudam, mas o site oficial precisa completar uma
pipeline de 6 etapas com erro/custo/metadata visiveis.

**Bugs criticos descobertos nesta sessao:**
1. GPT-5 Nano tool-use historico: multiplas chamadas `create_document`, nomes alucinados, sem validacao de schema
2. Metadata `tokens_usados`, `ia_modelo`, `ia_provider` faltava no DB historico; smokes pos-fix de Gemini e Nano ja registram metadata/custo
3. Endpoint `/conteudo` nao retorna conteudo para alguns tipos (usar `/view`)
4. Sem endpoint de eventos de task (dificulta diagnostico de falhas transientes)

**Proximos passos:**
1. Manter deploy oficial confirmado por Render MCP/lista de deploys ou marker
   confiavel antes de cada smoke novo.
2. Corrigir `check_deploy.sh` para nao depender apenas do marker HTML quando o
   Render usa `rootDir=backend`.
3. Revalidar `extrair_respostas` com provider/modelo mais forte em OCR/handwriting
   ou melhorar o caminho OpenAI por pagina; GPT-5 Nano permanece ❌ nessa fase.
4. Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para
   tornar duravel o custo de falhas sem documento.
5. Quando creditos Anthropic forem recarregados, validar Haiku 4.5 via
   `pipeline-completo`.
