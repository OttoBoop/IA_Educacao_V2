# Log Google -- Pipeline, Desempenho E Custos

**Criado:** 2026-05-18
**Responsavel:** Paulo
**Escopo:** validar modelos Google no site oficial, com gasto minimo e registro
de custo/erro por tentativa.

## Regra P0

Sem fallback silencioso. O modelo Google escolhido roda ou falha alto. Retry no
mesmo modelo e permitido quando o provider informa erro temporario/quota e o
erro permanece rastreavel. Trocar para OpenAI, aceitar JSON ruim, inventar PDF
ou chamar etapa bloqueada de sucesso continua proibido.

## Estado Oficial Do Ciclo

- URL oficial: `https://ia-educacao-v2.onrender.com`.
- Runtime inicial observado: `0411f9a`.
- Runtime final publicado: `8de0ab3`.
- Health final: `/api/health` retornou `{"status":"healthy","supabase":true}`.
- `origin/main` final: `8de0ab33abfb76d58c2b20960fa1fd21311a371a`.
- Persistencia duravel de `token_usage`: ainda bloqueada por Supabase
  `PGRST205`, tabela `public.token_usage` ausente.

## Dados De Teste Escolhidos

Atividade principal para pipeline individual:

- `8f58cc8b5fb75869` -- `Prova 1 - Equações do 1º Grau`.
- Turma `ec5a0ae78546c78e` -- `9º Ano A`.
- Materia `840eefa3714d7a3e` -- `Matemática`.
- Aluna usada no smoke individual: `08893c99aa53002d` -- Beatriz Soares.

Pre-requisito para desempenho agregado:

- A atividade `8f58cc8b5fb75869` tem `8` documentos `RELATORIO_FINAL` para `4`
  alunos.
- Portanto `desempenho_tarefa` teria insumo suficiente.
- O agregado nao foi executado porque o modelo Google mais barato travou antes
  em `CORRIGIR`; rodar desempenho nessas condicoes gastaria credito para
  confirmar o mesmo bloqueio de quota.

## Baseline De Custos

Baseline antes dos smokes novos, via `/api/custos/resumo?limit=240`:

- `runs_analisados=120`.
- `runs_precificados=118`.
- `custo_usd=2.799771`.
- `por_provider.google.custo_usd=0.052604`.
- `token_usage_durable=false`.

Estado final, via `/api/custos/resumo?limit=300`:

- `runs_analisados=157`.
- `runs_precificados=155`.
- `custo_usd=3.373124`.
- `por_provider.google.custo_usd=0.144800`.
- `token_usage_durable=false`.

Observacao: os limites `limit=240` e `limit=300` mudam a janela de documentos
analisados; portanto o delta global nao deve ser lido como custo exato do ciclo.
As amostras por documento abaixo sao a evidencia de custo mais confiavel deste
ciclo.

## Resposta Operacional: Gasto, Bloqueio E Solucao

### O credito acabou?

Nao ha evidencia de que os `R$40` tenham sido consumidos. Pelo contrario: as
amostras Google diretamente atribuiveis ao ciclo de pipeline custaram frações de
centavo de dolar.

Custos Google medidos nos documentos novos de erro:

- `5df1cac02c5fb746`: `US$0.000493`.
- `91219d221a2b3aa2`: `US$0.000862`.
- Total medido nesses dois documentos: `US$0.001355`.

Tambem houve chamadas de conexao/chat simples que nao entram como documentos no
resumo de custos, mas elas foram muito pequenas: conexoes de `20`, `39` e `84`
tokens, e um JSON simples com `398` tokens. Mesmo somando isso, o gasto e
minimo frente ao credito informado.

O aumento de `/api/custos/resumo` nao deve ser usado como resposta direta sobre
quanto foi gasto neste ciclo, porque o endpoint muda a janela com `limit` e
inclui historico OpenAI/Google anterior. A evidencia confiavel do ciclo sao os
documentos/calls listados nesta pagina.

### O que bloqueou exatamente?

O erro do provider diz:

- quota `generate_content_free_tier_requests`;
- `limit: 20`;
- modelo `gemini-2.5-flash-lite`;
- `RESOURCE_EXHAUSTED`;
- retry sugerido entre ~49s e ~60s nos smokes finais.

Isso prova que:

- a chave Google existe e funciona para chamadas simples;
- o modelo Flash Lite existe e responde;
- o backend agora preserva e respeita `retry_after`;
- o site oficial ainda esta sendo tratado pelo Google como free tier/rate-limit
  no projeto/chave configurado no Render.

Isso nao parece falta de saldo consumido; parece billing/chave/projeto errado ou
quota paga ainda nao aplicada ao projeto da chave usada em producao.

### Solucao concreta

Gate externo, fora do codigo:

1. Abrir Google AI Studio ou Google Cloud no projeto que gerou a chave usada no
   Render.
2. Confirmar que billing pago esta ativo nesse projeto, nao apenas em outra
   conta/projeto.
3. Confirmar que a API key configurada no Render (`GOOGLE_API_KEY` ou chave
   Google no cofre do site) pertence ao projeto pago.
4. Se houver duvida, criar uma nova API key no projeto pago e substituir a chave
   no Render Dashboard, sem colar segredo em chat/docs/logs.
5. Reiniciar/deployar o servico Render.
6. Rodar o gate minimo:
   - `/api/settings/models/gem25lite001/testar`;
   - `/api/chat` JSON simples;
   - `CORRIGIR` em `gem25lite001`.
7. So quando a mensagem parar de citar `generate_content_free_tier_requests`,
   retomar `desempenho-tarefa-sync`.

### Fluxo seguro para rotacionar chaves

Nao colar segredo em chat, doc, terminal ou log.

Ferramenta reutilizavel criada:

```bash
python3 scripts/secure_render_env_form.py --yad
python3 scripts/secure_render_env_form.py --open
```

Ela abre um popup nativo de senha ou um formulario local em `127.0.0.1`, recebe
uma `RENDER_API_KEY` e as chaves de provider, chama a API oficial do Render para
atualizar `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY` e, opcionalmente,
`OPENAI_API_KEY`, e reinicia/deploya se a caixa estiver marcada. Essa etapa de
restart/deploy existe apenas para o processo do site carregar as env vars novas.
A saida permitida e apenas:

- status HTTP por env var;
- preview mascarado;
- status do pedido de deploy.

Lista atual de chaves necessarias para retomar o loop:

- `RENDER_API_KEY`: usada para atualizar env vars e disparar deploy
  no servico `srv-d5t8gbh4tr6s738fr3s0`;
- `GOOGLE_API_KEY`: chave do projeto Google que recebeu credito/billing;
- `ANTHROPIC_API_KEY`: chave Anthropic apos recarga de creditos.

Se a Render API key for permanente, trata-la como segredo de alta criticidade:
nao colar no chat, nao registrar em docs/logs e preferir rotacao posterior pelo
Dashboard quando fizer sentido. Nao pedir Rio 3 neste ciclo. Qualquer chave que
ja apareceu no chat deve ser considerada exposta e nao deve virar segredo
oficial de producao.

Gate de codigo ja feito neste ciclo:

- `9dbb122` preserva `retry_after`.
- `8de0ab3` faz retry por request Google.
- O sistema agora falha alto, registra custo parcial e mostra provider/codigo.

Gate estrutural ainda pendente:

- Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para que
  falhas sem documento final tenham persistencia duravel de custo.

## Atualizacao Pos-Chaves De 2026-05-18

Chaves enviadas pelo fluxo seguro local, sem aparecer em chat/log/doc:

- `GOOGLE_API_KEY` atualizada no Render: HTTP `200`.
- `ANTHROPIC_API_KEY` atualizada no Render: HTTP `200`.
- pedido de deploy/restart: HTTP `201`.
- `/api/deploy-info` continuou em `8de0ab3` porque o redeploy foi do mesmo
  commit; `/api/health` retornou `{"status":"healthy","supabase":true}`.

Baseline pos-env em `/api/custos/resumo?limit=420`:

- `runs_analisados=192`;
- `runs_precificados=190`;
- `custo_usd=5.106744`;
- Google na janela: `US$0.144800`;
- `token_usage_durable=false`, ainda por Supabase `PGRST205`.

Resultados novos:

- Anthropic destravou: Claude Haiku 4.5 (`588f3efe7975`) respondeu conexao
  `success=true`, `tokens=30`.
- Haiku em chat JSON simples respondeu HTTP 200, `tokens_used=490`, mas tambem
  envolveu JSON em bloco Markdown. Para chat simples isso e texto; para pipeline
  continua proibido aceitar como sucesso.
- Haiku `CORRIGIR` isolado passou no site oficial:
  `task_1255fef385bf`, documentos principais `816d1927e116914c` (JSON) e
  `e250407e3823c99d` (PDF), `43096/11976` tokens, `US$0.102976`. Artefatos
  intermediarios do mesmo run (`711ecd38d4feffda`, `fcdbeddc7f746b55`) ficaram
  `status=erro`, sem falso verde.
- Google saiu do bloqueio antigo de free-tier: Flash Lite, Flash e Gemini 3
  passaram conexao no site oficial; Flash Lite ainda oscilou com `503 high
  demand`, que e instabilidade de provider, nao quota `generate_content_free_tier_requests`.
- Google Flash (`gem25flash001`) `CORRIGIR` isolado passou:
  `task_f15775f0c10c`, documentos `2fb79c5a06dd091e` (JSON) e
  `f53b78ceb8fd53ad` (PDF), `27368/6255` tokens, `US$0.023848`.
- Google Flash pipeline completa de Beatriz falhou alto em
  `EXTRAIR_RESPOSTAS`: `task_1cf3a3da23b5`. `EXTRAIR_QUESTOES` e
  `EXTRAIR_GABARITO` passaram; `EXTRAIR_RESPOSTAS` retornou JSON valido dentro
  de Markdown, e o executor bloqueou com: "A resposta contem JSON valido, mas
  veio com Markdown, comentarios ou texto ao redor. A etapa exige APENAS JSON
  cru, sem envelope." As etapas finais foram `skipped` por bloqueio explicito.

Causa provavel do erro novo:

- Os prompts padrao diziam "sem Markdown", mas exibiam exemplos de saida dentro
  de blocos ```json. Isso induz Gemini a copiar o envelope.
- Patch local preparado: remover cercas Markdown dos exemplos de saida JSON nas
  seis etapas oficiais e manter a validacao bloqueante. Teste novo:
  `backend/tests/unit/test_default_prompts_no_json_fences.py`.
- Validacoes locais do patch: `py_compile`, `git diff --check` e pytest focado
  com `2 passed`.

Proximo gate:

1. Commit/push/deploy do patch de prompts.
2. Confirmar Render no novo hash.
3. Repetir pipeline completa `gem25flash001` em Beatriz.
4. So se passar, rodar `desempenho_tarefa` com Google Flash.

### Re-smoke apos `6921c3f`

- Commit `6921c3f` foi publicado e confirmado no Render em `150s`.
- `/api/health` permaneceu saudavel.
- Os prompts live `default_extrair_questoes`, `default_extrair_gabarito` e
  `default_extrair_respostas` nao continham mais cercas Markdown de JSON e continham
  "Estrutura JSON esperada".
- Re-smoke Google Flash pipeline completa:
  `task_f7575b3d5567`.
- Resultado: `EXTRAIR_QUESTOES` passou; `EXTRAIR_GABARITO` falhou alto pelo
  mesmo motivo de JSON valido dentro de Markdown; demais etapas ficaram
  `skipped`.

Nova causa encontrada:

- O prompt de retry de validação ainda mostrava a resposta anterior dentro de
  uma cerca Markdown `text` e ainda escrevia a sequencia literal de tres crases
  ao proibi-la.
- Patch local posterior: sanitizar a resposta anterior removendo cercas Markdown
  e trocar a instrucao literal por "tres crases consecutivas".
- Validacoes locais posteriores: `py_compile`, `git diff --check` e pytest
  focado com `3 passed`.

### Re-smoke apos `2d08eec`

- Commit `2d08eec` foi publicado e confirmado no Render em `150s`.
- `/api/health` permaneceu saudavel.
- Re-smoke Google Flash pipeline completa:
  `task_ca5dd6b8b3b5`.
- Resultado: as seis etapas completaram sem `stage_errors`.
- Artefatos principais:
  - `EXTRAIR_QUESTOES`: `1fceff5c65c98d35`, `3552/1260`,
    `US$0.004216`;
  - `EXTRAIR_GABARITO`: `1402391821f1ce86`, `6028/1773`,
    `US$0.006241`;
  - `EXTRAIR_RESPOSTAS`: `60700bdd1590c8f8`, `6160/719`,
    `US$0.003646`;
  - `CORRIGIR`: JSON `57967fdce60a708a`, PDF `2ac3cfae72865ce3`,
    `19225/3112`, `US$0.013548`;
  - `ANALISAR_HABILIDADES`: JSON `0c9082bdc9f3b5d6`, PDF
    `1bcfebf4fb4153b3`, `36555/7240`, `US$0.029067`;
  - `GERAR_RELATORIO`: JSON `e7a5d3ac2e661360`, PDF
    `92d59649afcf2038`, `46309/17587`, `US$0.057860`.
- Custo total medido da pipeline Beatriz/Google Flash:
  `117829/31691` tokens, `US$0.114578`.

### Desempenho Tarefa Google Flash

- Endpoint: `/api/executar/desempenho-tarefa-sync`.
- Provider: `gem25flash001`.
- Resultado: HTTP 200, `sucesso=true`, `status=PARCIAL`.
- Cobertura: `alunos_incluidos=5`, `alunos_excluidos=5`.
- Motivo dos excluidos: arquivos narrativos ilegiveis/ausentes no storage para
  alguns `RELATORIO_FINAL` antigos.
- Leitura validada em `/api/desempenho/tarefa/8f58cc8b5fb75869`.
- Artefatos lidos:
  - JSON `6a067026f35f1ca4`;
  - PDF `4ce97741964d5cd3`;
  - JSON extra de tool `f2177d727031533c`.
- Custo reportado por run: `46492/11353`, `US$0.042330`.

Bug novo de custos/artefatos:

- O metodo agregado chamava `executar_com_tools`, que ja salva JSON/PDF, e depois
  chamava `_salvar_resultado` de novo com os mesmos tokens.
- Isso gerou JSON duplicado e fez `/api/custos/resumo` aparentar contar o mesmo
  gasto duas vezes.
- Patch local preparado: remover `_salvar_resultado` extra de
  `gerar_relatorio_desempenho_tarefa`, `gerar_relatorio_desempenho_turma` e
  `gerar_relatorio_desempenho_materia`.
- Teste novo: `backend/tests/unit/test_desempenho_no_duplicate_save.py`.
- Validacoes locais: `py_compile`, `git diff --check`, pytest focado
  `4 passed`.

Proximo gate:

1. Commit/push/deploy do patch anti-duplicacao.
2. Repetir `desempenho_tarefa-sync` com Google Flash.
3. Confirmar que o novo run gera apenas um par JSON/PDF oficial e um custo.
4. So depois subir para `desempenho_turma-sync`.

## Tentativas Google

| Ordem | Modelo | Alvo | Resultado | Evidencia | Custo medido |
|---:|---|---|---|---|---:|
| 1 | `gem25lite001` | `/api/settings/models/{id}/testar` | OK | `success=true`, modelo `gemini-2.5-flash-lite`, `tokens=20` | Nao entra no resumo de documentos |
| 2 | `gem25lite001` | `/api/chat` JSON simples, sem backoff | `429` | HTTP `429`, `provider=Google`, `retryable=true` | Nao entra no resumo de documentos |
| 3 | `gem25flash001` | conexao | OK | `success=true`, modelo `gemini-2.5-flash`, `tokens=39` | Nao entra no resumo de documentos |
| 4 | `gem25flash001` | `/api/chat` JSON simples | `429` | HTTP `429`, `provider=Google`, `retryable=true` | Nao entra no resumo de documentos |
| 5 | `gem3flash001` | conexao | OK | `success=true`, modelo `gemini-3-flash-preview`, `tokens=84` | Nao entra no resumo de documentos |
| 6 | `gem3flash001` | `/api/chat` JSON simples | `429` | HTTP `429`, `provider=Google`, `retryable=true` | Nao entra no resumo de documentos |
| 7 | `gem25lite001` | `/api/chat` JSON simples apos `75s` | OK | resposta `{"ok": true, "teste": "backoff"}`, `tokens_used=398` | Nao entra no resumo de documentos |
| 8 | `gem25lite001` | `CORRIGIR` Beatriz antes do patch | Falha alta | `task_cbf8fc1a0d3e`, `corrigir=failed`, Google `429`, retry sugerido `8.610734207s` | Sem documento novo observado |
| 9 | `gem25lite001` | `CORRIGIR` apos `9dbb122` | Falha alta | `task_3669d284c815`, `corrigir=failed`, Google `429`, retry sugerido `57.324042179s` | Documento `5df1cac02c5fb746`, `3467/366`, `US$0.000493` |
| 10 | `gem25lite001` | `CORRIGIR` apos `8de0ab3` | Falha alta | `task_c6e0b3157990`, rodou cerca de `491s`, Google `429`, retry sugerido `59.028617387s` | Documento `91219d221a2b3aa2`, `3467/1287`, `US$0.000862` |
| 11 | `gem25lite001` | conexao apos troca de chave | Parcial | passou 2 vezes (`tokens=20`), depois `503 high demand`; sem free-tier | Nao entra no resumo de documentos |
| 12 | `gem25flash001` | conexao apos troca de chave | OK | 3 tentativas `success=true`, `tokens=39/84/39` | Nao entra no resumo de documentos |
| 13 | `gem3flash001` | conexao apos troca de chave | OK | 3 tentativas `success=true`, `tokens=195/140/178` | Nao entra no resumo de documentos |
| 14 | `gem25lite001` | `CORRIGIR` apos troca de chave | Falha alta | `task_dc80b77ffd58`, Google `503 high demand`, `retryable=true` | Sem documento final observado; custo duravel bloqueado por `token_usage` ausente |
| 15 | `gem25flash001` | `CORRIGIR` apos troca de chave | OK | `task_f15775f0c10c`, JSON `2fb79c5a06dd091e`, PDF `f53b78ceb8fd53ad` | `27368/6255`, `US$0.023848` |
| 16 | `gem25flash001` | pipeline completa Beatriz | Falha alta | `task_1cf3a3da23b5`; passou questoes/gabarito, falhou `EXTRAIR_RESPOSTAS` por JSON dentro de Markdown | A coletar apos patch; erro sem sucesso falso |

## Patches Publicados No Ciclo

### `9dbb122` -- `fix: respect provider retry-after hints`

- `ProviderAPIError` passou a extrair `retry_after` de mensagens como
  `Please retry in 8.610734207s`.
- `/api/chat` passou a devolver `retry_after` no erro estruturado.
- `executar_com_tools` passou a propagar `retry_after` para
  `ResultadoExecucao` e metadata de erro.
- Validacoes locais: `py_compile`, `git diff --check`, testes focados `6 passed`.
- Deploy: Render confirmou `9dbb122`, `/api/health` OK.

### `8de0ab3` -- `fix: retry google quota waits per request`

- `ChatClient` passou a aplicar retry no mesmo request Google quando Gemini
  retorna `429` com `retry_after`.
- Isso evita reiniciar a etapa inteira e repetir tool calls desnecessarias.
- Validacoes locais: `py_compile`, `git diff --check`, testes focados `7 passed`.
- Deploy: Render confirmou `8de0ab3`, `/api/health` OK.

## Interpretação

- Google nao esta sem chave: os testes de conexao funcionaram para Flash Lite,
  Flash e Gemini 3 Flash.
- Google nao esta pipeline-ready neste momento: `CORRIGIR` com Flash Lite ainda
  cai em quota `generate_content_free_tier_requests`, limite `20`.
- A mensagem do provider ainda fala em `free_tier_requests`, mesmo apos o
  credito novo. Isso sugere que o projeto/chave usada pelo Render nao esta
  efetivamente operando com billing pago ou continua limitada por rate-limit do
  tier gratuito.
- O backend agora registra melhor `retry_after`, custo parcial e erro provider;
  isso melhora observabilidade, mas nao remove o bloqueio externo.

## Relatorios De Desempenho

Nao executados neste ciclo.

Motivo: `desempenho_tarefa`, `desempenho_turma` e `desempenho_materia` usam
tool-use e chamariam o mesmo caminho Google que falhou em `CORRIGIR`. Como a
atividade `8f58cc8b5fb75869` ja tem insumo suficiente para `desempenho_tarefa`,
o bloqueio atual nao e dado de teste; e quota/billing/rate-limit do provider.

Proximo passo honesto:

1. Confirmar no Google AI Studio/Cloud que a chave do Render esta vinculada ao
   projeto com billing pago, nao apenas ao tier gratuito.
2. Quando a mensagem deixar de citar `generate_content_free_tier_requests`,
   repetir primeiro `gem25lite001` em `CORRIGIR`.
3. Se `CORRIGIR` passar, rodar `desempenho_tarefa-sync` na atividade
   `8f58cc8b5fb75869`.
4. So depois subir para `desempenho_turma-sync`; `desempenho_materia-sync`
   exige validar se ha duas turmas com finais suficientes.

## Status Final Do Ciclo

- `gem25lite001`: conexao OK, JSON simples OK com backoff, pipeline individual
  bloqueada em `CORRIGIR` por quota free-tier.
- `gem25flash001`: conexao OK; JSON simples imediato bloqueado por `429`; nao
  foi gasto pipeline para poupar credito.
- `gem3flash001`: conexao OK; JSON simples imediato bloqueado por `429`; nao
  foi gasto pipeline para poupar credito.
- `e251747cd7a2`: nao retestado neste ciclo; Pro fica por ultimo por custo.
- Desempenho agregado: preparado por dados, mas nao executado por bloqueio
  Google antes da camada agregada.
