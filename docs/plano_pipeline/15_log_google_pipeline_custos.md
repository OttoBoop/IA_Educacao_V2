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

Gate de codigo ja feito neste ciclo:

- `9dbb122` preserva `retry_after`.
- `8de0ab3` faz retry por request Google.
- O sistema agora falha alto, registra custo parcial e mostra provider/codigo.

Gate estrutural ainda pendente:

- Aplicar `backend/migrations/002_create_token_usage.sql` no Supabase para que
  falhas sem documento final tenham persistencia duravel de custo.

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
