# Matriz Provider × Fase — Status Atual

**Atualizado:** 2026-05-17
**Atividades de teste principais:** Lista0 — Algebra Linear Avancada
(`126e8b5ad7dd6d59`) e smoke simples oficial `Smoke Paulo Pipeline 2026-05-16`
(`f68d57a9a339081f`)
**Runtime oficial atual:** backend Render em `fdf0cbd`; `origin/main` recebeu o
ciclo funcional `fdf0cbd` e pode receber registro documental posterior. Use
`/api/deploy-info` como gate de codigo live.
**Commits aplicados/observados:** `a632883`, `5737611`, `50935ea`, `479b77d`,
`b12be9a`, `301eba6`, `f67055c`, `462ea1d`, `b4d7ee6`, `99483d1`,
`f505be6`, `d75b05a`, `97a7c79`, `ec95193`, `ff7b92a`, `68ebe51`,
`c75af88`, `45d543a`, `39aa50a`, `3ddf6c5`, `b24f03e`, `6ed31a4`,
`eab7d90`, `dcecdfa`, `7ed8b8b`, `9e1aee5`, `839968e`, `45c6f97`,
`55e168a`, `9823afb`, `4f27dae`, `f0dae61`, `87bdee2`, `b2dc88b`,
`28cfd6a`, `cacedcd`, `a311ade`, `924fd79`, `0dfdbbe`, `d653c13`,
`2947178`, `53d0252`, `f55e299`, `5f10651`, `e6060e1`, `a7dead3`,
`5527e26`, `2792d89`, `23282d7`, `7d0c874`, `8dd6c54`, `c1598b9`,
`01fb04c`, `6b57ef1`, `3b9eedc`, `b8b8693`, `283e8c6`, `1ce3d23`,
`2d72c6b`, `f2211bb`, `5a3daca`, `92bd095`, `f6b040c`, `2cad38a`,
`2885da7`, `99b8c3c`, `392ec7c`, `460643f`, `54d083e`,
`854cec7`, `b07472f`, `dc5884f`, `0d5ab9d`, `c870ed4`, `45f5cf8`,
`4094bda`, `4d8f73d`, `f40acf3`, `700b088`, `1307909`, `bed0c08`, `feaf5d0`,
`d47d748`, `c53fae6`, `9ab53df`, `1454e68`, `3fce335`, `33fb7d5`, `0f84552`,
`974f040`, `11a396b`, `c094fba`, `d799165`, `6b43016`, `8c77cc4`, `29a4b7e`,
`fdf0cbd`

## Status Oficial De Deploy

- O servico oficial em 2026-05-17 e
  `srv-d5t8gbh4tr6s738fr3s0` (`IA_Educacao_V2`), branch `main`,
  `rootDir=backend`, URL `https://ia-educacao-v2.onrender.com`.
- `/api/deploy-info` confirmou o runtime backend `11a396b` com
  `source=RENDER_GIT_COMMIT`; esse e o gate primario atual para codigo live.
- `origin/main` avancou para `29a4b7e` apenas com documentacao; isso nao mudou o
  codigo Render live nem a matriz de comportamento do backend.
- O commit `fdf0cbd` mudou backend/frontend para catalogo OpenAI GPT-5.x e foi
  publicado no GitHub; Render confirmou `fdf0cbd` por `/api/deploy-info`,
  `wait_deploy.sh` e `check_deploy.sh`.
- O HTML marker pode ficar stale e nao prova runtime antigo: commits de
  frontend/docs/marker podem nao disparar deploy quando o servico Render usa
  `rootDir=backend`.
- Os smokes abaixo devem dizer qual evidencia oficial usam: `/api/deploy-info`,
  lista de deploys quando disponivel e sempre comportamento live por endpoint.
- O commit `f2211bb` esta live em Render (`dep-d84bsou8bjmc73dgr12g`) e
  `/api/deploy-info` confirmou `source=RENDER_GIT_COMMIT`; ele corrige selecao
  de artefatos processados antigos em prompts/anexos.
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
  bloquearam JSON vazio inconsistente. O runtime live daquele ciclo foi `1ce3d23`; o smoke
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
- Render live agora chegou a `feaf5d0` por `/api/deploy-info`; marker HTML segue
  apenas auxiliar. O smoke `task_ec7acffbb6d4` validou `corrigir` com GPT-5.4
  Mini depois das guardas de literal, cabecalho PDF e soma/totais de nota.
- Render live chegou depois a `d47d748` e `c53fae6`: `d47d748` removeu o
  marcador HTML `DEBUG_V3_MARKER_2026` do corpo de `/api/chat`; `c53fae6`
  preserva HTTP status real de provider no chat. Smokes live: GPT-5.4 Mini
  retornou HTTP 200 com JSON parseavel; Gemini 3 Flash retornou HTTP 429
  estruturado por quota Google; Claude Haiku retornou HTTP 400 estruturado por
  credito Anthropic insuficiente.
- Render live chegou a `9ab53df`: o handler global de erro agora deixa
  `error.message` textual e preserva `provider`, `provider_status_code` e
  `retryable` como campos proprios; o frontend servido mostra esses metadados
  em toasts/API errors e em erros por etapa da sidebar.
- Render live chegou a `1454e68` e depois `3fce335`: erros de provider depois
  de tool-use agora preservam usage parcial. `1454e68` cobre tokens ja vistos
  pelo executor em respostas parciais; `3fce335` cobre o caso em que o erro
  nasce dentro do loop de tools do `ChatClient`, antes de retornar resposta ao
  executor. Smoke live `task_81f274a6f510` com `gem25flash001` falhou alto por
  Google `429` antes de criar novo documento parcial; por isso a correcao ficou
  validada por testes e deploy, mas a reproduçao live exata segue bloqueada por
  quota Google.
- Render live chegou a `33fb7d5`: `create_document` em etapas de pipeline agora
  usa `ToolExecutionContext.atividade_id`/`aluno_id` em vez de valores
  inventados pelo modelo. Re-smoke Gemini 2.5 Flash Lite
  `task_52e5fa9020a0` nao repetiu `Atividade não encontrada`; falhou alto por
  tentativa indevida de PDF via `create_document` e `IndentationError` no
  `execute_python_code`, com custo rastreavel no documento `ea407d2ce87fb99a`.
- Render live chegou a `0f84552`: se `execute_python_code` falhar antes de
  persistir PDF, o executor faz uma tentativa adicional no mesmo modelo com o
  erro anterior e o JSON oficial. O smoke Gemini 2.5 Flash Lite
  `task_124bf0e8d7bf` nao chegou a usar esse reparo como sucesso porque o JSON
  oficial estava invalido; falhou alto por `JSON ... sem lista de questoes` e
  divergencia de `nota_final`, com custo rastreavel no run `tool_44dd029b1954`.
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
| **Gemini 2.5 Flash** (`gem25flash001`) | ✅ | ✅ | ✅ | 🚫 | ⏸️ | ⏸️ |
| **Gemini 2.5 Flash Lite** (`gem25lite001`) | ⏸️ | ⏸️ | ⏸️ | ❌ | ⏸️ | ⏸️ |
| **Gemini 3 Flash** (`gem3flash001`) | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| **GPT-5 Nano** (`gpt5nano001`) | ✅ | ✅ | ⚠️ | ❌ | ⚠️ | ✅ |
| **GPT-5.4 Mini** (`gpt54mini001`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GPT-4o** (`180b8298a279`) — referencia | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **GPT-4.1** (`ffae9accf68e`) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Nota de leitura: os checks da tabela acima sao por etapa individual validada.
Eles nao significam que a pipeline completa de 6 etapas passou em uma unica
task. Em 2026-05-16, Gemini completou as tres extracoes em uma task sequencial,
mas parou em `corrigir` por quota `429`.
Nota OpenAI/catalogo 2026-05-17: a matriz de comportamento nao muda so por
catalogo, mas o lote `fdf0cbd` corrigiu cadastro e chamada de modelos GPT-5.x:
`gpt-5.4/5.5`, `gpt-5.2`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano` e variantes
`-pro` passam a ser reasoning/no-temperature em todos os caminhos relevantes;
`gpt-5-image` sai do catalogo textual; limites de output/contexto e capabilities
das variantes `-pro` foram alinhados aos docs oficiais. Confirmacao operacional:
catalogo live retornou metadata esperada, `gpt-5-image` retornou `404`,
estimativa de custo de `gpt-5.4-mini` retornou `US$ 0.003` por request
`1000/500`, e `/api/chat` com `gpt54mini001` respondeu JSON valido com
`tokens_used=409`.
Nota GPT-5.4 Mini pos-`fdf0cbd`: o smoke `task_0559fc57a3cc` rodou
`selected_steps=["corrigir"]` na fixture Diana com `gpt54mini001` e completou
sem `stage_errors`. JSON `92737f5ba69ca2d4` e PDF `bb6522992d2fe7d4` ficaram
`status=concluido`, provider/modelo `openai/gpt-5.4-mini`, `24593/4061` tokens,
`US$ 0.036719`; o PDF intermediario `067f4db99040043b` foi marcado
`status=erro` por `pdf_json_consistency`, confirmando retry explicito sem
fallback silencioso.
Nota provider sweep pos-`fdf0cbd`: `/api/settings/models/{id}/testar` confirmou
OpenAI disponivel (`gpt54mini001` OK/42 tokens, `gpt5nano001` OK/38 tokens).
Google esta bloqueado por quota em `gem25flash001`, `gem25lite001` e
`gem3flash001` (`Erro API Google: 429 - Limite de requisições atingido`).
Anthropic esta bloqueado por credito em Haiku/Sonnet 4.5 (`400`, saldo
insuficiente). Ollama local falha conexao no Render.
Nota de dataset Lista0: a atividade `126e8b5ad7dd6d59` possui base docs
presentes, porem a auditoria de PDF de 2026-05-17 confirmou que o enunciado
`5dc75513e958c25b` contem os exercicios 1 a 7 enquanto o gabarito
`dbfe3a77a631489f` cobre somente `Lista 0, Exercicio 5`. Portanto qualquer smoke
integral da Lista0 precisa falhar alto ou ser explicitamente escopado ao
exercicio 5; sucesso de correcao da atividade inteira com esse gabarito nao conta
como validacao de provider.
Nota GPT-4o: as tres etapas finais foram revalidadas em 2026-05-17 no smoke
`task_386f96bbf158`. As tres extracoes foram revalidadas depois em
`task_013ad41fd3ed`, runtime `99b8c3c`: `extrair_questoes`
`69dd5c07acb2ff52`, `extrair_gabarito` `98dbaf8613ec9fc3` e
`extrair_respostas` `8019a2a2c5fc3cea`. O primeiro rerun
`task_d6506d2f2ccc` tinha exposto julgamento/especulacao em
`raciocinio_parcial`; os commits `2885da7` e `99b8c3c` transformaram isso em
erro bloqueante. O rerun final veio com `raciocinio_parcial=null` quando so
havia resposta final visivel.
Nota GPT-4o full: em `54d083e`, a task `task_68b19146a95b` completou as 6
etapas na fixture Diana: `extrair_questoes` `5adf51fcd1adc4c0` (`1151/409`,
`US$ 0.006967`), `extrair_gabarito` `7c097774fce46472` (`1774/284`,
`US$ 0.007275`), `extrair_respostas` `9e6d562d51a6f6e4` (`2167/292`,
`US$ 0.008337`), `corrigir` JSON/PDF
`b2abc9a73c8dc3a8`/`8911e1a3acae4ad2` (`23696/2916`, `US$ 0.088400`),
`analisar_habilidades` JSON/PDF `21f2d7d065aeafe5`/`72203996b8960b50`
(`37758/3279`, `US$ 0.127185`) e `gerar_relatorio` JSON/PDF
`bbc5963d712a7f1e`/`f12312b96e3725a3` (`21482/2250`, `US$ 0.076205`).
Total aproximado: `US$ 0.314369`. Houve retries explicitos com JSONs inválidos
marcados `status=erro` antes dos artefatos finais de `corrigir`,
`analisar_habilidades` e `gerar_relatorio`; isso nao e fallback de provider,
mas precisa continuar visivel nos custos e na UI.
Nota Gemini 2.5 Flash: o teste de conexao respondeu `success=true`, mas a
pipeline full `task_f1f1511f21d5`, runtime `54d083e`, falhou alto em
`corrigir`. As tres extracoes passaram com conteudo coerente:
`extrair_questoes` `4d5c5abdc1203f2b` (`1188/567`, `US$ 0.000518`),
`extrair_gabarito` `d27793f610a3696c` (`2114/318`, `US$ 0.000508`) e
`extrair_respostas` `ffed15b8003145e9` (`2456/336`, `US$ 0.000570`). A falha
foi: `tools: Saída obrigatória incompleta: JSON via create_document, PDF via
execute_python_code`; portanto tools Gemini 2.5 Flash ainda nao estao
pipeline-ready nesse executor. O commit `854cec7` passou a forcar tool-use
Google com `toolConfig.functionCallingConfig.mode=ANY` e `allowedFunctionNames`,
alem de fasear JSON/PDF como OpenAI. O commit `b07472f` passou a aceitar
parafrase coerente de `feedback_geral` no PDF sem aceitar corte/truncamento. No
runtime `b07472f`, o rerun full `task_6bba32964706` chegou novamente a
`corrigir`, mas falhou por Google `429` antes de validar a etapa; a tentativa
isolada `task_f9b76153875a` tambem falhou por `429`. Um JSON parcial
`338b25f9c0f74415` foi marcado `status=erro`, como esperado. Status atual:
extracoes ✅, tools bloqueadas por quota para revalidacao. Novo sweep em
runtime `4d8f73d`: o endpoint de conexao de Gemini 2.5 Flash retornou
`success=true`, mas o smoke isolado `task_e99a2c20be17` em `corrigir` falhou
alto por Google `429 RESOURCE_EXHAUSTED`, com `stage_errors.corrigir.codigo=429`
e `retryable=true`, sem novo documento verde. Conexao viva nao promove a etapa
para pipeline-ready. Novo smoke em runtime `3fce335`,
`task_81f274a6f510`, repetiu `corrigir` com `gem25flash001` e tambem falhou
alto por Google `429`; desta vez o objetivo era validar custo de erro depois de
documento parcial, mas a quota travou antes de criar novo artefato, entao nao
houve novo `token_split_missing`. Os bloqueios de custo restantes sao
historicos (`338b25f9c0f74415` e `c4d75e5b0456b27a`).
Nota sweep de conexao 2026-05-17: OpenAI (`gpt-4o`, GPT-4.1, GPT-5 Nano,
GPT-5.4 Mini, o3 Mini, o4 Mini), Gemini 2.5 Flash/Lite e Gemini 3 Flash
retornaram `success=true`; Gemini 2.5 Pro retornou `429`; Haiku/Sonnet seguem
bloqueados por creditos Anthropic.
Nota Gemini 2.5 Flash Lite: conexao `success=true`, mas `corrigir` nao esta
pipeline-ready. O smoke `task_6ee6a6386cea` revelou um bug do sistema, corrigido
em `33fb7d5`: model input com nome da atividade nao deve sobrescrever o id
server-side do contexto. O re-smoke `task_52e5fa9020a0` no runtime `33fb7d5`
removeu esse erro de storage e falhou alto por contrato/modelo: tentativa de PDF
via `create_document` e `IndentationError` no `execute_python_code`. O custo do
erro ficou ok: documento `ea407d2ce87fb99a`, `14772/1805` tokens,
`US$ 0.001649`. No runtime `0f84552`, o executor ganhou reparo explicito para
erro de codigo PDF, mas o smoke `task_124bf0e8d7bf` falhou antes por JSON
invalido e PDF divergente: `7fde0dfd076a36e3` sem `questoes`, `nota_final=0`,
PDF `e8861f03a2980412` com `8.0`, custo `18748/1934`, `US$ 0.001986`.
Nota Nano/relatorio: a full Nano `task_f0c0f15a2f27`, no runtime `99b8c3c`,
completou as 6 etapas, mas revelou falso verde em `GERAR_RELATORIO`: correcao
JSON `cff76af34d9248a6` tinha `nota_final=8.0` e o relatorio JSON/PDF
`8184fe013490b53e`/`15cbe3b104f37891` registrou `nota_final=0.0`. O commit
`392ec7c` passou a validar `RELATORIO_FINAL.nota_final` contra a `CORRECAO`
oficial da ultima execucao. O smoke live `task_57da745b8de5` reexecutou apenas
`gerar_relatorio` com Nano e gerou JSON `66fcc132db1be96a` com `nota_final=8.0`;
o PDF ruim `34e404fcd809270d` foi marcado `status=erro` por
`pdf_json_consistency`; o PDF final `735896580f441e89` ficou concluido e
`pdftotext` confirmou `Nota final: 8.0`. Tokens do run: `29067/6701`.
Nota Nano/corrigir: no runtime `0f84552`, o smoke `task_90eb0936b7ce` com
`selected_steps=["corrigir"]` falhou alto por PDF/JSON divergentes. JSON
`c96bafb0c134d0bd` trouxe `nota_final=8`, mas PDF `43450aa937013578` trouxe
`nota_final=0.0`, nota errada na Q1 e sem `feedback_geral` verificavel. Custo:
`tool_37b678de7e7d`, `55975/9221`, `US$ 0.006487`. Portanto `CORRIGIR` volta a
❌ para Nano nesse runtime, embora a falha esteja corretamente bloqueada e
custeada.
Nota GPT-4.1/corrigir: no runtime `0f84552`, o smoke `task_714dab24c41a` com
`selected_steps=["corrigir"]` completou no site oficial. JSON
`d921c575837e38d7` e PDF final `a7669eb5352e3d9d` ficaram coerentes:
`nota_final=8.0`, Q3 errada por `25` vs `30`, e feedback geral presente. O PDF
intermediario `b18662384cdac7c6` ficou `status=erro` antes do retry explicito.
Custo: `tool_9d63d57a7b83`, `24217/4005`, `US$ 0.080474`.
Nota GPT-4.1 etapas finais: no mesmo runtime, `task_5c3ba86e86c1` completou
`ANALISAR_HABILIDADES` e `GERAR_RELATORIO`. Analise: JSON
`7b39243c100e30de`, PDF `e6c692989734476b`, `12478/2235`, `US$ 0.042836`.
Relatorio: JSON `10d478289be3cf03`, PDF `e4e6f65038d399db`, `14021/2107`,
`US$ 0.044898`. A nota final permaneceu `8.0`. A validacao de qualidade achou
typo `Proeficiência` no PDF de analise; isso e melhoria visual, nao falso verde
de pipeline.
Nota GPT-4.1 extracoes: `task_fd62c9db2359` completou as tres extracoes no
runtime `0f84552`. `EXTRAIR_QUESTOES` `b5393676dc1c1dd4` trouxe 4 questoes e
10 pontos (`US$ 0.005830`), `EXTRAIR_GABARITO` `f6e322b5829d4d34` trouxe
respostas completas (`US$ 0.007312`) e `EXTRAIR_RESPOSTAS`
`c429ee5f3276fa90` trouxe 4 respostas da Diana, Q3 `25` e
`raciocinio_parcial=null` (`US$ 0.006788`). A cobertura GPT-4.1 fica ✅ nas 6
etapas para a fixture simples, embora ainda falte dataset maior.
Nota GPT-4.1 full pipeline: `task_f6851ed535b8` executou as 6 etapas em uma
unica task no runtime `0f84552` e completou sem `stage_errors`. Documentos:
`79b5876544c6c2ae`, `bfb2a7590d943fa3`, `afacce7606ab43b3`,
`c186d3f6f852fb9b`/`df34a13a49ad03e5`, `b8126c7d15ecee56`/`5f86f4d2dd3abe23`,
`71cf0b53fe147668`/`3490b806647c8e2a`. Q3 permaneceu erro por `25` vs `30`,
nota final e proficiencia ficaram `8.0`, e custo total aproximado foi
`US$ 0.222856`. O PDF intermediario `6edcd9f8ecd80b52` ficou `status=erro`
antes do retry.
Nota GPT-4.1 pos-guard PDF: apos `974f040` e `11a396b`, o re-smoke
`task_92c4b74494f7` em `corrigir` gerou apenas JSON `a05a2a4faeab71d1` e PDF
`dc9fe13dc6b8b994`, ambos `concluido`, sem PDF intermediario marcado como erro.
Custo do run: `14617/2400`, `US$ 0.048434`. A melhoria foi no validador de
rotulos de feedback do PDF, nao relaxamento de nota ou questoes.
Nota Gemini Lite/corrigir: no runtime `11a396b`, `task_5850e9adf001` falhou
alto por quota Google `429 RESOURCE_EXHAUSTED`, com `provider=Google` e
`retryable=true`. Documentos de erro custeaveis: `494856278a41ff57`
(`6408/208`, `US$ 0.000543`) e `badbaadbe86ce541` (`3029/515`,
`US$ 0.000382`). Continua ❌ em `CORRIGIR`; repetir somente quando quota Google
permitir.
Nota P0 atualizada: `extrair_gabarito` Gemini era ❌ porque o output historico
retornou todas as respostas como `MISSING_CONTENT`, embora o PDF base tivesse
texto extraivel de "Exercicio 5". Em 2026-05-17, o smoke
`task_c08f3d478aad` revalidou Gemini 3 Flash na fixture Diana e criou JSON
`92e5e77b24874ad1` com 4 respostas reais (`x=5`, `34`, `30`, `20 cm2`),
tokens `2040/507` e custo `US$ 0.001220`; por isso a etapa volta a ✅ nessa
fixture simples. Nano tinha a mesma falha historica em `task_2da0fb90c3fb`, mas
foi revalidado apos `5527e26` na task `task_dc719eeea626`, com JSON
`5f433f9a1bc30842` e 7 respostas reais. Schema parseavel e custo medido nao
bastam; conteudo precisa fazer sentido.
Nota Gemini pos-`aff2180`: `task_c9302f341734` chegou a completar as 6 etapas
em `629c4ee`, mas a auditoria achou falso verde de schema em `corrigir`: JSON
`54c7fafd5569cca2` tinha `feedback_geral_texto`/`feedback_geralSmall`, nao
`feedback_geral`. O commit `aff2180` passou a bloquear esse caso. Reruns
posteriores (`task_0cbc99255c7e`, `task_6347f5e0d311`,
`task_26412081ac9f`) falharam alto por Google quota `429`; por isso as etapas
finais Gemini ficam ⚠️ ate nova revalidacao com quota disponivel.
Nota P0 adicional: `extrair_respostas` Nano rodou em
`task_a9ff0d69d5e9`, mas o JSON `b968c9539f277deb` marcou todas as 7 respostas
como `ilegivel=true`, embora o PDF `f60d37284d616ca4` tenha texto extraivel da
questao 7. Isso e falha de conteudo, nao validacao. Depois disso, `8dd6c54`
ainda deixou passar tudo `em_branco=true` (`2a518dfb6b2a03ef`) e `c1598b9`
ainda deixou passar porque a validacao central nao estava no caminho real do
executor (`10d1c1d9741a6273`). Desde `01fb04c`, o smoke
`task_b511641dfa52` falha alto. A rodada posterior melhorou entrada e guards:
`3b9eedc` criou `6b28875e8a9fdc73` com apenas Q7 real; `b8b8693` criou
um caminho mais estrito para nao aceitar scan vazio. Em `aff2180`, Nano passou
na fixture simples Diana: `task_ff7eeda28964` gerou JSON
`4175e0e7476931d7` com 4 respostas reais (`x = 5`, `34`, `25`, `20 cm2`),
`2129/2261` tokens e `US$ 0.001011`. Por isso a coluna vira ⚠️, nao ✅:
melhorou na fixture simples, mas ainda precisa dataset maior para apagar o
historico de falha.
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
custo `US$ 0.081492`. Depois do deploy do modelo versionado, o smoke
`task_706931a94555` com `gpt54mini001` criou `fec100a2e41eabcf`, 5/7 respostas
com conteudo real, Q1/Q2 `MISSING_CONTENT`, Q3 `LOW_CONFIDENCE`, tokens
`97004/1737` e custo `US$ 0.080570`. A segunda amostra com `gpt54mini001`,
Alvaro (`task_19062336eb8b`), criou `4a82ddf1d2118ff0`, 7/7 respostas com
conteudo real, Q2/Q3 `LOW_CONFIDENCE`, tokens `90588/2813` e custo `US$ 0.0806`.
Isso valida a etapa nessas amostras, nao pipeline completa.

Nota pos-`2cad38a`: GPT-5.4 Mini passou tambem em um smoke full oficial simples
no Render, `task_a5f0d734f0b3`, atividade `Smoke Paulo Pipeline 2026-05-16`,
aluna Diana Omega, hash live `2cad38a`. As 6 etapas ficaram `completed` usando
`gpt54mini001`: `extrair_questoes` doc `f65318c550a76842`, `extrair_gabarito`
doc `70df18512be9c617`, `extrair_respostas` doc `14ca81d800de2648`,
`corrigir` docs `2c7cd4cf9eb85e57`/`769744b6fff6f3b9`,
`analisar_habilidades` docs `12b24cd992477eab`/`15579ed3ad2614be` e
`gerar_relatorio` docs `38686372cb8ea981`/`37b0c86cee879ced`. Custo aproximado
das 6 etapas: `US$ 0.079110`. Isso move GPT-5.4 Mini para ✅ nessa fixture, mas
nao valida automaticamente datasets reais maiores, Gemini/Nano/Haiku. A
inspeção semantica inicial dos JSONs tambem passou: 4 questoes, gabarito
completo, 4 respostas da aluna, correcao `8/10` por erro na porcentagem da Q3,
analise e relatorio alinhados. PDFs baixaram com HTTP 200 e texto extraivel;
houve achados de qualidade no layout/metricas: feedback cortado no PDF de
correcao e `8/10` apresentado junto de `75% de proficiencia geral`. O patch
`0ac92f0` endureceu as instrucoes de PDF para wrap de texto e metricas
separadas e ficou live no Render. O re-smoke `task_605512496b0d` completou as
6 etapas, mas revelou divergencia P0 entre artefatos: JSON de correcao
`a899697b81e7e10d` trouxe `nota_final=8` e Q3 `0`, enquanto PDF
`2114140f8d5aaf61` trouxe `Nota final: 9.0` e Q3 `2.0`; JSON de relatorio
`680aa0c4bf6183ec` trouxe `nota_final=8`, enquanto PDF `dde1d63db71f2a5b`
trouxe `Nota final: N/A`. Patch local seguinte adiciona guarda PDF/JSON no
executor: a matriz so deve voltar a ✅ plena nessa fixture se o smoke produzir
artefatos coerentes ou falhar alto antes de marcar sucesso. A guarda foi
publicada em `2052a01`; o smoke `task_857c0c3657ef` falhou alto em `corrigir`
porque o PDF `7559f610981995cd` mostrou Q3 `3.0` contra JSON
`0fdcfe4d7d9b9072` com Q3 `0`. Patch local seguinte adiciona retry explicito
para regenerar apenas o PDF a partir do JSON validado e expor `erro_pipeline`
no resumo de custos. O retry foi publicado em `3a77a17`; o smoke reduzido
`task_e389f360b812` completou `corrigir`, `analisar_habilidades` e
`gerar_relatorio`. Inspeção manual confirmou `corrigir` PDF/JSON coerente
(`b9fbaf4dc24b4a75`/`dd79a9c3f369fc09`, nota final `8.0`, Q3 `0.0/2.0`) e
relatorio com nota final separada de proficiencia.

Nota de pipeline per-phase: antes de `f2211bb`, o smoke
`task_ea1ac75c9459` falhou alto em `extrair_gabarito` porque Nano retornou tudo
`MISSING_CONTENT` depois de receber contexto contaminado por muitos JSONs
historicos. O patch `f2211bb` passou a usar apenas o artefato mais recente por
tipo. No smoke pos-patch `task_19ee59ac1881`, `extrair_questoes` gerou
`d50f3b909e6773e7` (`2178/8678`, `US$ 0.003580`), `extrair_gabarito` gerou
`8dd414ee1617c3a5` (`6918/5497`, `US$ 0.002545`), `extrair_respostas` com
`gpt54mini001` gerou `1e5db36f3ab9aa0e` (`18176/2081`, `US$ 0.022996`) e
`corrigir` gerou JSON/PDF `f0302debf41ae58f`/`31794fc784905c00`
(`19614/4566`, `US$ 0.002807`). A task falhou alto em `analisar_habilidades`,
com doc parcial `b5f17f2d1a980a3d` marcado `status=erro` (`21193/7884`,
`US$ 0.004213`), porque Nano nao produziu os artefatos obrigatorios via tools.
Por isso `analisar_habilidades` de Nano fica ⚠️ em pipeline integrada, embora
tenha smokes individuais historicos.

Nota pos-`3a7dfea`: o smoke full `task_bc6cc84d10ef` completou as 6 etapas com
Nano+`gpt54mini001`, mas nao valida pipeline completa. A inspeção do conteúdo
mostrou que `extrair_gabarito` com `gpt54mini001` gerou JSON
`17573f1218bd6c39` com resposta real apenas para Q5 e avisos
`MISSING_CONTENT` para Q1, Q2, Q3, Q4, Q6 e Q7. O `CORRIGIR` posterior chegou a
gerar nota, mas isso foi reclassificado como falso sucesso porque não havia
gabarito completo. O patch `3a7dfea` mudou o comportamento esperado: no smoke
`task_5894e6d5858e`, `corrigir` falhou alto antes de chamar IA e não criou novo
documento verde. Portanto:

- `gpt54mini001` em `EXTRAIR_GABARITO` fica ⚠️: a etapa gera estrutura, mas este
  gabarito da Lista0 está incompleto e não serve para correção integral.
- `gpt5nano001` em `CORRIGIR` fica ⚠️: com gabarito completo pode corrigir, mas
  agora deve bloquear quando o gabarito estruturado está incompleto.
- `ANALISAR_HABILIDADES` e `GERAR_RELATORIO` de Nano ficam ⚠️ para pipeline
  integrada, porque qualquer sucesso baseado numa correção invalidada não conta
  como validação de produto.

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
| **Gemini 3 Flash** | 🚫 |
| **GPT-5.4 Mini** | ✅ |
| **GPT-5 Nano** | ✅ |
| **GPT-4o** | ⏸️ |

**Smokes live de chat em 2026-05-15:**
- Gemini 3 Flash (`gem3flash001`): respondeu JSON simples, 585 tokens, HTTP 200.
- GPT-5 Nano (`gpt5nano001`): respondeu JSON simples, 526 tokens, HTTP 200.
- Claude Haiku 4.5 (`588f3efe7975`): HTTP 500 com erro Anthropic de credito
  baixo. Bloqueado por billing, nao por codigo do chat.

**Smokes live de chat em 2026-05-17 (`c53fae6`):**
- GPT-5.4 Mini (`gpt54mini001`): HTTP 200, JSON parseavel, 413 tokens, sem
  marcador `DEBUG_V3_MARKER_2026`.
- Gemini 3 Flash (`gem3flash001`): HTTP 429 com erro estruturado
  `provider_api_error`, `provider=Google`, `provider_status_code=429`,
  `retryable=true`. Status atual de chat: bloqueado por quota, embora tenha
  historico de chat OK.
- Claude Haiku 4.5 (`588f3efe7975`): HTTP 400 com erro estruturado
  `provider_api_error`, `provider=Anthropic`, `provider_status_code=400`,
  `retryable=false`, credito insuficiente.

**Re-smoke live de chat em 2026-05-17 (`9ab53df`):**
- GPT-5.4 Mini segue HTTP 200 com JSON parseavel e 413 tokens.
- Gemini 3 Flash segue bloqueado por quota, agora com shape normalizado:
  `error.message` string, `error.provider=Google`,
  `error.provider_status_code=429`, `error.retryable=true`.
- Haiku segue bloqueado por credito, agora com shape normalizado:
  `error.provider=Anthropic`, `error.provider_status_code=400`,
  `error.retryable=false`.

**Teste live de conexao em 2026-05-17 (`0f84552`):**
- OpenAI OK: `180b8298a279` (`gpt-4o`), `ffae9accf68e` (GPT-4.1),
  `gpt5nano001` e `gpt54mini001`.
- Anthropic bloqueado por credito: Haiku 4.5 e Sonnet 4.5 retornam saldo
  insuficiente.
- Google saturado: Gemini 2.5 Pro, Gemini 2.5 Flash e Gemini 3 Flash retornam
  `429`. Gemini 2.5 Flash Lite conecta, mas o ultimo smoke de `corrigir`
  falhou alto por JSON/PDF divergentes.
- Ollama local falha conexao no Render.

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
Rechecagem em 2026-05-17 via `POST /api/settings/models/588f3efe7975/testar`
tambem retornou `success=false`, erro Anthropic `invalid_request_error` e
mensagem de saldo insuficiente.

**Acao necessaria (Otavio):** Recarregar creditos na conta Anthropic. Nenhum teste possivel ate la.

---

### Gemini 3 Flash Preview — ⚠️ ETAPAS FINAIS AGUARDAM REVALIDACAO POS-SCHEMA

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

**Atualizacao 2026-05-17 em `aff2180`:** `629c4ee` corrigiu a validação de PDF
para aceitar o texto completo de `feedback_geral` mesmo quando o PDF usa o
título "Parecer Pedagógico Geral". Em seguida, a auditoria do Gemini full
`task_c9302f341734` descobriu falso verde de JSON: `corrigir` gerou
`feedback_geral_texto`/`feedback_geralSmall` no lugar de `feedback_geral`.
`aff2180` endureceu o schema de `CORRIGIR`. A revalidacao ficou bloqueada por
quota Google `429` nos reruns `task_0cbc99255c7e`, `task_6347f5e0d311` e
`task_26412081ac9f`.

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

### GPT-5 Nano — ✅ CHAT SIMPLES, ✅ RELATORIO COM NOTA CROSS-STAGE VALIDADA

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

**Smoke full e re-smoke de relatorio em 2026-05-17:** `task_f0c0f15a2f27`
completou a pipeline simples inteira com Nano, mas a auditoria classificou o
resultado como falso verde em `GERAR_RELATORIO`: o relatorio mudou a nota de
`8.0` para `0.0`. Depois do commit `392ec7c`, `task_57da745b8de5` confirmou o
comportamento correto no site oficial: relatorio JSON `66fcc132db1be96a` com
`nota_final=8.0`, primeiro PDF `34e404fcd809270d` marcado erro por falta de
nota verificavel, PDF final `735896580f441e89` concluido com `Nota final: 8.0`.
Isso promove `GERAR_RELATORIO` Nano para ✅ na fixture simples, mas nao promove a
pipeline Nano inteira: `extrair_respostas` segue ⚠️ por historico de qualidade em
dataset maior/manuscrito.

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

### GPT-4o — ✅ etapas finais confirmadas na fixture simples

**Testado via `pipeline-completo`** na atividade `Smoke Paulo Pipeline
2026-05-16`, aluna Diana Omega, modelo `180b8298a279`, Render `3e6be20`,
task `task_386f96bbf158`, `selected_steps=["corrigir",
"analisar_habilidades","gerar_relatorio"]`.

| Etapa | Status | Artefatos oficiais | Tokens In/Out | Custo |
|-------|--------|--------------------|---------------|-------|
| CORRIGIR | ✅ | PDF `e5ca0900654ed0e9`, JSON `e8269ff428d50802` | `66527/6861` | `US$ 0.234928` |
| ANALISAR_HABILIDADES | ✅ | PDF `9b8ef8b03388a741`, JSON `58ddf040c628863c` | `47566/4498` | `US$ 0.163895` |
| GERAR_RELATORIO | ✅ | PDF `4d4a42b77010d27a`, JSON `30c5a9c3225f1ed5` | `39023/4062` | `US$ 0.138178` |

**O que foi corrigido antes de virar ✅:**

1. `f7bca4c` passou OpenAI forced tools para Responses API; antes GPT-4o nao
   persistia os artefatos obrigatorios em `corrigir`.
2. `33829bc` e `fdf1829` fizeram retry/validação de JSON para impedir raiz
   array em `analise_habilidades`, `correcao` e `relatorio_final`.
3. `3af2918` marcou todos os JSONs invalidos e artefatos extras/stale como
   `status=erro`; antes alguns arrays ficavam concluídos no mesmo run.
4. `00eb26b` corrigiu instruções de sandbox de PDF; antes `gerar_relatorio`
   falhava alto por `E2B_SECURITY File write outside sandbox`.
5. `3e6be20` bloqueou PDF de correcao com Feedback Geral truncado; o smoke
   final confirmou PDF com Feedback Geral completo.

**Limite da validação:** GPT-4o esta confirmado apenas para essas tres etapas
na fixture simples. Ainda falta pipeline completa de 6 etapas e datasets maiores.

---

## Testes Pendentes (para fechar Marco 1)

### Prioridade ALTA
- [x] Rodar Gemini 3 Flash em `analisar_habilidades` e `gerar_relatorio` com
      custo/metadata
- [x] Rodar Gemini 3 Flash em `extrair_questoes` com custo/metadata
- [x] Rodar Gemini 3 Flash em `extrair_gabarito` com custo/metadata e health
      responsivo durante a execucao
- [x] Rerodar Gemini 3 Flash em `extrair_gabarito` apos guard anti-tudo-
      `MISSING_CONTENT`; `task_c08f3d478aad` criou JSON `92e5e77b24874ad1`
      com 4 respostas reais e custo `US$ 0.001220`
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
- [x] Corrigir contaminacao por artefatos antigos em prompts/anexos; `f2211bb`
      reduziu tokens e destravou o gabarito no smoke per-phase
- [ ] Corrigir `analisar_habilidades` em pipeline integrada: `task_19ee59ac1881`
      falhou alto por tool-use incompleto em GPT-5 Nano; GPT-5.4 Mini passou em
      pipeline completa propria no smoke `task_a5f0d734f0b3`
- [x] Validar GPT-5.4 Mini (`gpt54mini001`) nas 6 etapas em uma fixture simples
      oficial: `task_a5f0d734f0b3`, Render `2cad38a`, documentos e custos
      registrados
- [x] Revalidar GPT-5.4 Mini apos guarda PDF/JSON: re-smoke `task_605512496b0d`
      no Render `0ac92f0` completou as 6 etapas, mas PDFs divergiram dos JSONs;
      `2052a01` falhou alto no smoke `task_857c0c3657ef`; proximo runtime deve
      testar retry explicito de PDF ou continuar falhando alto com erro visivel;
      `3a77a17` passou no smoke reduzido `task_e389f360b812` e manteve o PDF
      ruim anterior marcado como `erro`
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
- [x] Revalidar `gerar_relatorio` Nano apos guard cross-stage de `nota_final`:
      `task_57da745b8de5`, Render `392ec7c`, JSON `66fcc132db1be96a`, PDF final
      `735896580f441e89`
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
  `extrair_gabarito`, `corrigir` e `gerar_relatorio` passaram em smokes
  oficiais com JSON/PDF quando aplicavel, custo e metadata, mas o smoke full
  `task_bc6cc84d10ef` mostrou que uma task completa ainda pode ser semanticamente
  invalida se o gabarito estiver incompleto. Desde `3a7dfea`, `corrigir` falha
  alto antes de chamar IA quando `gabarito_extraido` tem `MISSING_CONTENT`
  bloqueante. `analisar_habilidades` tem sucesso individual historico, mas
  qualquer análise baseada em correção invalidada nao conta como validação.
  `extrair_respostas` rodou varias vezes, mas foi reclassificada como falha de
  conteudo por tudo `ilegivel=true`/vazio, por inferencia suspeita do enunciado
  ou por scan majoritariamente sem conteudo. O deploy `1ce3d23` corrigiu o
  falso sucesso final naquele caso: agora ele falha alto, nao cria documento
  verde e registra custo de falha (`usage_52590d55d210459e`). Em `aff2180`,
  Nano passou `extrair_respostas` na fixture simples Diana (`task_ff7eeda28964`,
  doc `4175e0e7476931d7`, custo `US$ 0.001011`), entao a etapa esta parcial,
  nao resolvida de forma geral. Ainda faltam dataset maior, `analisar_habilidades`
  no run integrado, pipeline completa de 6 etapas, schema minimo por etapa e
  custo duravel de falhas sem documento final.
- ⚠️ **GPT-5.4 Mini candidato OCR/pipeline simples:** `extrair_respostas` passou em uma amostra
  oficial primeiro como cadastro efemero (`task_9c10e3752bcb`, doc
  `a39d26fcc621c7a8`, custo `US$ 0.081492`) e depois como modelo versionado
  `gpt54mini001` (`task_706931a94555`, doc `fec100a2e41eabcf`, custo
  `US$ 0.080570`; `task_19062336eb8b`, doc `4a82ddf1d2118ff0`, custo
  `US$ 0.0806`). No smoke full `task_bc6cc84d10ef`, `gpt54mini001` tambem
  completou `extrair_respostas` (`f10a6ef8a8ca0897`) e gerou gabarito
  estruturado (`17573f1218bd6c39`), mas o gabarito da Lista0 estava incompleto;
  portanto ele fica confirmado em `extrair_respostas` e parcial em
  `extrair_gabarito` para aquela Lista0. Depois de `2cad38a`, a fixture simples
  `task_a5f0d734f0b3` completou as 6 etapas com `gpt54mini001`, documentos
  persistidos e custo aproximado `US$ 0.079110`. Depois de `0ac92f0`, o
  re-smoke `task_605512496b0d` tambem completou as 6 etapas, mas mostrou P0 de
  artefato: JSONs coerentes e PDFs divergentes em `corrigir` e
  `gerar_relatorio`. Depois, `2052a01` bloqueou essa classe de falso verde:
  `task_857c0c3657ef` falhou alto em `corrigir` por PDF/JSON divergente.
  Finalmente, `3a77a17` passou no smoke reduzido `task_e389f360b812`:
  `corrigir`, `analisar_habilidades` e `gerar_relatorio` completaram, e a
  inspeção manual confirmou PDF/JSON coerentes para correcao e relatorio.
  Em `aff2180`, o full smoke `task_299dd8a00517` completou novamente as 6
  etapas com schema de `CORRIGIR` endurecido; `corrigir` trouxe
  `feedback_geral` real no JSON `f4f5a5d1f71a262f`, PDF `54bbdd06a48f9376` e
  custo total aproximado de `US$ 0.094958`. Em `45f5cf8`, o smoke reduzido
  `task_42e3b303c39a` revalidou `corrigir` apos as guardas anti-fallback:
  JSON `776b70be01c24641`, PDF final `12dbdc65d469e982`, PDF intermediario
  `204a8a5c3f81af97` marcado `status=erro` por `pdf_json_consistency`, split
  `26251/4582` e custo `US$ 0.040307`. O PDF final bateu com o JSON
  (`nota_final=8.0`, Q3 `0.0/2.0`, feedback geral completo). O commit
  `4094bda` nao muda a matriz por provider, mas adiciona cobertura unitária
  para impedir regressao do mesmo guard em `ANALISAR_HABILIDADES` e
  `GERAR_RELATORIO`. O commit `4d8f73d` tambem nao muda a matriz, mas cobre
  D02-10: PDF duplicado/stale em retry dual-output deve virar
  `status=erro`/`stale_tool_artifact`, tal como JSON stale. Depois disso,
  `f40acf3` alinhou `PROMPTS_PADRAO` e `STAGE_TOOL_INSTRUCTIONS` para
  `CORRIGIR`, `ANALISAR_HABILIDADES` e `GERAR_RELATORIO`, mas o smoke
  `task_9671e072f42c` revelou falso verde semantico: Q3 tinha resposta do aluno
  `25`, gabarito `30`, e a correcao ainda marcou acerto/nota 10. O commit
  `700b088` tornou `resposta_aluno` e `resposta_correta` obrigatorios em
  `CORRIGIR` quando ha upstream, compara esses campos contra
  `EXTRACAO_RESPOSTAS`/`EXTRACAO_GABARITO` e falha alto se houver troca da
  resposta ou acerto maximo para divergencia numerica. O re-smoke
  `task_cc22b6c239d0` passou no runtime `700b088`: JSON de correcao
  `c3c680d099f781f7`, PDF `9814e0d8107b4d44`, Q3 `25` vs `30`,
  `nota_final=8.0`; relatorio JSON/PDF `9bf0e1dac90a58c1`/
  `a6f80bac65611376`; custo `56891/9827` tokens, `US$ 0.086890`. Depois,
  `1307909` bloqueou acerto literal divergente, `bed0c08` bloqueou cabecalho
  PDF com placeholder e `feaf5d0` bloqueou `nota_final`/totais incoerentes. O
  smoke `task_ec7acffbb6d4` no runtime `feaf5d0` marcou o JSON inconsistente
  `a6e92125cee2b4d4` como erro (`nota_final=10`, soma 8) e aceitou o retry:
  JSON `51f5a6a4536b60e7`, PDF `db4903bda7b4d2c0`, cabecalho real,
  Q3 `25` vs `30`, `nota_final=8`, custo `41137/5962`, `US$ 0.057682`.
- ⏸️ **Claude Haiku 4.5:** Aguardando creditos.
- 📊 **Confiabilidade Gemini 3 Flash:** extracoes OK; etapas finais ficaram
  ⚠️ depois que `aff2180` endureceu `feedback_geral` em `CORRIGIR`. A
  revalidacao foi bloqueada por quota Google `429`. Precisa duas execucoes
  completas quando quota/credito permitir.

**Marco 1 atingido para uma fixture simples, nao para a matriz inteira:** o site
oficial completou 6 etapas com GPT-5.4 Mini, custo/metadata e inspeção
semantica inicial coerente dos JSONs; depois `3a77a17` validou as etapas finais
com contrato PDF/JSON coerente. Isso ainda nao valida Gemini/Nano/Haiku/GPT-4o
nem datasets maiores.

**Bugs criticos descobertos nesta sessao:**
1. GPT-5 Nano tool-use historico: multiplas chamadas `create_document`, nomes alucinados, sem validacao de schema
2. Metadata `tokens_usados`, `ia_modelo`, `ia_provider` faltava no DB historico; smokes pos-fix de Gemini e Nano ja registram metadata/custo
3. Endpoint `/conteudo` nao retorna conteudo para alguns tipos (usar `/view`)
4. Sem endpoint de eventos de task (dificulta diagnostico de falhas transientes)

**Proximos passos:**
1. Manter deploy oficial confirmado por `/api/deploy-info` antes de cada smoke
   novo; o codigo funcional mais recente confirmado e `48407f2`. Commits
   documentais posteriores podem mudar o hash de `/api/deploy-info` sem alterar
   comportamento de pipeline.
2. Aplicar/validar a migration Supabase `token_usage` antes de chamar custo de
   falha sem documento de duravel.
3. Revalidar matriz por provider/modelo; GPT-5.4 Mini passou 6 etapas em
   fixture simples e GPT-4o passou as seis etapas individualmente, mas ainda
   faltam datasets maiores e GPT-4o full 6 etapas em uma unica task.
4. Revalidar Gemini/Nano/Haiku por provider/modelo; GPT-5 Nano permanece ❌ em
   `extrair_respostas` e Haiku segue bloqueado por credito.
5. Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para
   tornar duravel o custo de falhas sem documento.
6. Quando creditos Anthropic forem recarregados, validar Haiku 4.5 via
   `pipeline-completo`.
7. Confirmar no site oficial que telas de resultado obedecem `status=erro`:
   documento parcial em erro nao conta como etapa concluida; retry concluido
   pode fechar a etapa, mas o documento de erro continua visivel na lista para
   auditoria e custo. Status: confirmado em `b8e14db` para HTML live e fixture
   Diana com retry concluido; `325c200` confirmou Eric/Lista0 como parcial/erro
   quando a correcao nao tem questao/correcao avaliavel; `148d8b3` confirmou
   ranking/estatisticas/dashboard com rota correta e media zero preservada;
   `147296d` confirmou agregados em lote com dashboard da Lista0 em `1.433s`.
   `22f6f31` confirmou default vivo em `gpt54mini001`/GPT-5.4 Mini, removendo
   Haiku bloqueado do caminho default; `48407f2` confirmou resumo estruturado
   de erro de provider em custos (`429`, `RESOURCE_EXHAUSTED`,
   `quota_exhausted`). Falta migration `token_usage` e proxima revalidacao de
   provider.
