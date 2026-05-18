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
- Runtime final do subloop Google original: `a7f02a3`.
- Runtime funcional oficial atual: `e85be11`.
- Health final: `/api/health` retornou `{"status":"healthy","supabase":true}`.
- `origin/main` no fechamento Google: `a7f02a31fc04606de82e22bec3345150fff9ead6`;
  depois avançou ate `e85be1151400b8cf0985581d39d4a944d75cd10f`.
- Persistencia duravel de `token_usage`: migration aplicada; `/api/custos/status`
  retorna `ok=true`, `table_available=true`, `error_code=null` e
  `token_usage_backend.durable=true`. Smokes oficiais em `518f8a2` e `58781a1`
  provaram escrita row-level; apos o smoke Haiku agregado em `f534576`, o status
  atual e `record_count=6`, `token_usage_analisados=6`, `alertas=[]`. Ainda
  falta ampliar a prova para falhas sem documento final.

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

### Re-smoke agregado apos `d7313a6`

- Commit `d7313a6` foi publicado e confirmado no Render.
- Repeticao de `/api/executar/desempenho-tarefa-sync` com `gem25flash001`:
  HTTP 200, `sucesso=true`, `status=PARCIAL`.
- Readback em `/api/desempenho/tarefa/8f58cc8b5fb75869` mostrou run novo
  `run-20260518-153754` com exatamente dois documentos oficiais:
  PDF `0cfd4f362eacc903` e JSON `30dbb7e96531bf62`.
- Custo do run novo: `25237/4965` tokens, `US$0.019984`.
- Resultado do patch anti-duplicacao: nao apareceu novo JSON artificial de
  sistema para o run novo; os artefatos duplicados antigos seguem no historico
  apenas como evidencia do bug corrigido.

### Desempenho Turma Google Flash

- Endpoint: `/api/executar/desempenho-turma-sync`.
- Provider: `gem25flash001`.
- Resultado: HTTP 200 em `157.5s`, `sucesso=true`, `status=PARCIAL`.
- Cobertura: `total_alunos=5`, `narrativas_encontradas=5`,
  `atividades_cobertas=1`.
- Avisos: arquivos narrativos antigos ilegiveis para alguns documentos e
  lacunas em `Prova 1 - Equações do 1º Grau` e `Trabalho - Estatística`.
- Readback em `/api/desempenho/turma/ec5a0ae78546c78e` mostrou run novo
  `run-20260518-154054` com PDF `c4919dd7ac988fa2` e JSON
  `8fe7dc2276f4f670`.
- Custo do run: `65800/13969` tokens, `US$0.054663`.

### Desempenho Materia Google Flash

- Dados oficiais checados antes de gastar IA:
  - Materia `840eefa3714d7a3e` tem duas turmas:
    `7a4edd9e4d2af0be` e `ec5a0ae78546c78e`.
  - A turma `7a4edd9e4d2af0be` tem uma atividade e zero documentos.
  - A turma `ec5a0ae78546c78e` tem relatórios finais legiveis.
- Bug encontrado: o codigo aceitava duas narrativas da mesma turma como se isso
  bastasse para um relatorio cross-turma de materia.
- Patch publicado: `16afe40` (`fix: block materia desempenho without two
  turmas`) exige `RELATORIO_FINAL` legivel em pelo menos duas turmas distintas
  antes de chamar IA.
- Validacoes locais: `py_compile`, `git diff --check`,
  `test_desempenho_materia_prereqs.py` e `test_desempenho_no_duplicate_save.py`
  com `3 passed`.
- Deploy oficial: Render confirmou `16afe40`; `/api/health` saudavel.
- Smoke oficial:
  `/api/executar/desempenho-materia-sync` com `gem25flash001` retornou HTTP
  200, `sucesso=false`, `status=BLOQUEADO_PREREQUISITO`,
  `total_turmas=2`, `narrativas_encontradas=5`, cobertura
  `7a4edd9e4d2af0be=0` e `ec5a0ae78546c78e=5`.
- Interpretação: isso e sucesso de produto no sentido P0. O sistema nao gerou
  relatorio de materia falso, nao chamou IA e explicou o dado faltante.

### Re-smoke Flash Lite apos `a7f02a3`

- Alvo: `gem25lite001` em `CORRIGIR` isolado para Beatriz, mesmo dado usado nos
  smokes anteriores.
- Antes do patch, `task_e8ae68627a05` falhou alto porque o modelo tentou salvar
  PDF via `create_document`; documento de erro `401d50c195b34968`,
  `56512/17776` tokens, `US$0.012762`.
- Causa tecnica: Google ja recebia `toolConfig` forçando `create_document`, mas
  a mensagem inicial faseada so era usada para OpenAI. O prompt completo ainda
  pedia JSON e PDF ao mesmo tempo, incentivando o Lite a tentar PDF na unica
  ferramenta exposta.
- Patch publicado: `a7f02a3` (`fix: phase google dual output tool prompts`)
  faz Google usar a mesma mensagem inicial faseada: primeira chamada salva
  somente JSON via `create_document`; PDF fica para a chamada seguinte via
  `execute_python_code`.
- Validacoes locais: `py_compile`, `git diff --check` e
  `test_e_t2_retry_partial_output.py` com `34 passed`.
- Deploy oficial: Render confirmou `a7f02a3`; `/api/health` saudavel.
- Re-smoke apos patch: `task_44ec067a3d82` ainda falhou alto, mas por motivo
  melhor diagnosticado: JSON persistido via `create_document` sem schema minimo
  (`nota_final`, `questoes`, `feedback_geral`, `total_acertos`,
  `total_erros`). Documento de erro `8c875cf984e55e91`, JSON invalido
  `bc878df188ec3d18`, `31602/5201` tokens, `US$0.005241`.
- Interpretação: Flash Lite nao esta validado para `CORRIGIR`; apos o patch,
  o bloqueio deixou de ser "tool errada" e virou "modelo nao entregou schema".
  Isso deve ficar como falha alta do modelo nesta etapa, sem fallback para
  Flash.

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
| 17 | `gem25flash001` | pipeline completa Beatriz apos `2d08eec` | OK | `task_ca5dd6b8b3b5`; seis etapas sem `stage_errors` | `117829/31691`, `US$0.114578` |
| 18 | `gem25flash001` | `desempenho_tarefa` apos `d7313a6` | OK parcial | `run-20260518-153754`; 5 alunos incluidos, 5 excluidos por arquivos antigos ilegiveis/ausentes | `25237/4965`, `US$0.019984` |
| 19 | `gem25flash001` | `desempenho_turma` apos `d7313a6` | OK parcial | `run-20260518-154054`; 5 narrativas, 1 atividade coberta, lacunas em atividades | `65800/13969`, `US$0.054663` |
| 20 | `gem25flash001` | `desempenho_materia` apos `16afe40` | Bloqueio correto | HTTP 200 com `sucesso=false`, `BLOQUEADO_PREREQUISITO`; so 1 turma tinha resultado legivel | Sem chamada IA; sem custo novo |
| 21 | `gem25lite001` | `CORRIGIR` antes de `a7f02a3` | Falha alta | `task_e8ae68627a05`; tentou PDF via `create_document`, bloqueado sem falso verde | `56512/17776`, `US$0.012762` |
| 22 | `gem25lite001` | `CORRIGIR` apos `a7f02a3` | Falha alta | `task_44ec067a3d82`; JSON via `create_document`, mas sem schema minimo; bloqueado | `31602/5201`, `US$0.005241` |
| 23 | `gem3flash001` | `/api/chat` JSON simples | OK | HTTP 200, JSON cru `{"ok": true, "modelo": "gemini3"}`, `tokens_used=801` | Nao entra no resumo de documentos |
| 24 | `gem3flash001` | `CORRIGIR` isolado | OK | `task_ead090df8740`; JSON/PDF concluidos, sem erro | `57750/8221`, `US$0.053538` |
| 25 | `gem3flash001` | pipeline completa Beatriz | OK lento | `task_24fe4d7b7ecc`; seis etapas concluidas, sem `stage_errors`; `CORRIGIR` demorou mais de 13min | `181550/33182`, `US$0.190321` |
| 26 | `gem3flash001` | `desempenho_tarefa` | OK parcial | HTTP 200 em `110.6s`, run `run-20260518-162141`; 6 alunos incluidos, 8 excluidos; JSON extra marcado erro | `108350/11191`, `US$0.087748` |

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

### `a7f02a3` -- `fix: phase google dual output tool prompts`

- Google passou a receber a primeira chamada dual-output faseada igual OpenAI:
  `create_document` primeiro para JSON, `execute_python_code` depois para PDF.
- O patch reduziu erro de ferramenta no Lite, mas o modelo continuou falhando
  alto por schema JSON insuficiente.
- Validacoes locais: `py_compile`, `git diff --check`,
  `test_e_t2_retry_partial_output.py` com `34 passed`.
- Deploy: Render confirmou `a7f02a3`, `/api/health` OK.

## Atualizacao 2026-05-19 -- Matemática-V Agregada Pos-`bc96faf`

Motivo do ciclo:

- O primeiro smoke em Matemática-V no runtime `737a709` provou um bug de
  produto: `desempenho_tarefa` para `810ef4c1a71c701b` retornou
  `alunos_incluidos=12` e `alunos_excluidos=4`, embora Alpha-V tenha 2 alunos.
- Causa: os agregados liam todos os `RELATORIO_FINAL` historicos da atividade e
  contavam versões antigas/arquivos quebrados como se fossem alunos.
- Correção `bc96faf`: coletar no maximo uma narrativa legivel por aluno e
  atividade, usando alunos matriculados como denominador; arquivos ilegiveis
  viram avisos explícitos.

Validações:

- Local: `py_compile`, `git diff --check` e suite focada de desempenho com
  `56 passed`.
- Deploy: `./scripts/wait_deploy.sh bc96faf` confirmou Render em `bc96faf`.
- Custos: `/api/custos/status?limit=100` retornou `ok=true`,
  `custos_persistencia_status=duravel` e `token_usage_backend.durable=true`.

Smokes oficiais com `gem25flash001`:

| Nivel | Endpoint | Evidencia | Status | Tokens | Custo |
|---|---|---|---|---:|---:|
| tarefa | `/api/executar/desempenho-tarefa-sync` | `run-20260519-112430`, docs `15f81063a315ef79`/`3c278a0623e8a9d4` | `COMPLETO`, 2 incluidos, 0 excluidos | `15858/3404` | `US$0.013267` |
| turma | `/api/executar/desempenho-turma-sync` | `run-20260519-112612`, docs `3c69d6ab6949a343`/`03dd9c3b5f943281` | `COMPLETO`, 4 narrativas, 2 atividades | `30310/9049` | `US$0.031716` |
| materia | `/api/executar/desempenho-materia-sync` | `run-20260519-112841`, docs `3791ca018fb615d6`/`e252c6af3c9b88e4` | `PARCIAL`, 3 turmas, 11 narrativas | `34922/4815` | `US$0.022514` |

Avisos do agregado de matéria:

- Beta-V/Daniel: dois documentos antigos ilegiveis foram registrados com
  `documento_id` (`46f652f9442e3e53` e `dfde26721d0dcf6e`), sem esconder o
  problema.
- Omega-V/Erik: falta `RELATORIO_FINAL` na atividade `Smoke Paulo Pipeline
  2026-05-16`.

Interpretação nova:

- Google Flash (`gem25flash001`) está validado no site oficial para pipeline
  individual, desempenho de tarefa, desempenho de turma e desempenho de matéria
  com avisos explícitos.
- O status parcial de matéria é dado real a limpar, não erro de provider.
- O custo total dos três agregados Matemática-V pos-`bc96faf` foi
  `US$0.067497` (`0.013267 + 0.031716 + 0.022514`).
- A queda de custo em tarefa (`US$0.020012` antes contra `US$0.013267` depois)
  confirma que remover versões historicas reduziu prompt e custo.
- Patch de observabilidade de custos `c8f538a`: quando
  `token_usage_backend.durable=true` mas `record_count=0`, o resumo passa a
  retornar alerta informativo `token_usage_sem_registros`. Assim o painel não
  confunde "tabela existe" com "falhas sem documento ja foram persistidas".
  Smoke live: `/api/custos/status?limit=100` retornou `ok=true` e
  `alertas[0].tipo=token_usage_sem_registros`.
- Patch `518f8a2`: cada execução tool-use com tokens passa a registrar
  `TokenUsageRecord` row-level mesmo quando documentos JSON/PDF são gerados.
  Como documentos e usage compartilham `cost_run_id`, o custo continua contado
  uma vez só. Validacao local: `test_cost_tracking.py` com `33 passed`.
  Smoke live: `run-20260519-115020` criou docs `6b174d9b7b9d8873` /
  `36ddf06eabb9da00` e usage `usage_38b5132cecab4e38`; `/api/custos/status`
  passou para `record_count=1`, `token_usage_analisados=1`, `alertas=[]`.
- Patch `58781a1`: agregados passam a preferir `RELATORIO_FINAL` em PDF quando
  existe PDF para o aluno, ignorando versões historicas `.json`/`.md` que antes
  geravam falso aviso de arquivo ilegivel. Validacoes locais:
  `py_compile`, `git diff --check`, `test_f1_desempenho_narrative_reading.py`,
  `test_desempenho_materia_prereqs.py`,
  `test_b3_c3_d3_desempenho_implementation.py` e
  `test_desempenho_no_duplicate_save.py` com `20 passed`.
  Deploy: `./scripts/check_deploy.sh 58781a1` confirmou Render.
  Smoke live: `run-20260519-120054` em Matemática-V com `gem25flash001`,
  `status=PARCIAL`, 3 turmas, 11 narrativas, cobertura Alpha-V `4`, Beta-V `4`,
  Omega-V `3`, apenas um aviso real (`Erik` sem `RELATORIO_FINAL` na atividade
  `Smoke Paulo Pipeline 2026-05-16`). Docs: PDF `1500c163ad6efab8`, JSON
  oficial `4722445c303f9393`, JSON extra `814489ad08fab682` marcado como
  `erro`/`stale_tool_artifact`. Custo: `28889/3299`, `US$0.016914`,
  `usage_c53952166c3d40ce`; `/api/custos/status?limit=160` passou para
  `record_count=2`, `token_usage_analisados=2`, `alertas=[]`.

## Interpretação

- Google nao esta sem chave: os testes de conexao funcionaram para Flash Lite,
  Flash e Gemini 3 Flash.
- Google Flash (`gem25flash001`) esta validado no site oficial para pipeline
  individual completa da Beatriz, `desempenho_tarefa` completo,
  `desempenho_turma` completo e `desempenho_materia` parcial honesto em
  Matemática-V, com custos medidos.
- Google Lite (`gem25lite001`) ainda nao esta validado para pipeline:
  `a7f02a3` corrigiu o prompt faseado de tools, mas o re-smoke ainda falhou
  alto por JSON sem schema minimo.
- Gemini 3 Flash (`gem3flash001`) esta validado para pipeline individual
  completa e `desempenho_tarefa`, mas e mais caro/lento que Flash neste caso.
- `desempenho_materia` nao e falha do modelo neste momento: ele gera artefato
  real, mas retorna parcial por arquivos historicos ilegiveis e um aluno sem
  `RELATORIO_FINAL` na atividade smoke.
- O backend agora registra melhor `retry_after`, custo parcial e erro provider;
  isso melhora observabilidade, mas nao remove o bloqueio externo.

## Relatorios De Desempenho

Executados para `gem25flash001`:

- `desempenho_tarefa`: passou completo pos-`bc96faf`, 2 alunos incluidos e 0
  excluidos.
- `desempenho_turma`: passou completo pos-`bc96faf`, 4 narrativas e 2
  atividades.
- `desempenho_materia`: passou parcial pos-`bc96faf`, 3 turmas e 11 narrativas,
  com avisos explícitos de dados.
- `desempenho_tarefa` pos-`e85be11`: passou completo de novo em
  `810ef4c1a71c701b`, agora com contrato de artefatos reforçado. O alerta de
  documentos gerados listou somente JSON/PDF persistidos:
  `desempenho_tarefa.json_b310.json` e
  `Relatório de Desempenho (Tarefa) - Matemática-V - Alpha-V_dc96.pdf`. Custo
  principal: `usage_459e3a56a73748fc`, `16939/3300`, `US$0.013332`, documentos
  `afa143d8e6390caf`/`692d50f8be3d885d`.

Nota operacional: uma tentativa anterior de smoke local fechou o pipe de leitura
antes de gravar resposta em arquivo, mas o servidor continuou processando e gerou
outro par JSON/PDF oficial. Esse gasto tambem fica registrado:
`usage_ac21f90610244c4b`, `16842/4329`, `US$0.015875`, documentos
`6041b3de9c64f769`/`18f24ee5c213ab55`. Nao repetir esse padrao: para smokes
longos, usar `curl -o arquivo` e parsear depois.

Proximo passo honesto:

1. Limpar/renomear historicos ilegiveis da Matemática-V e completar o
   `RELATORIO_FINAL` ausente do smoke Omega antes de repetir matéria.
2. Tratar `gem25lite001` como falha alta em `CORRIGIR` por schema invalido,
   salvo se houver novo patch especifico de prompt/JSON para modelos baratos.
3. Nao rodar `desempenho_turma`/`materia` com Gemini 3 sem necessidade: Flash ja
   cobriu turma, e Gemini 3 mostrou custo/latencia maiores.
4. Repetir `desempenho_materia` com `gem25flash001` somente depois do dado do
   Erik/Omega existir, para verificar se `e85be11` tambem elimina artefatos extras
   no agregado de matéria.

## Status Final Do Ciclo

- `gem25lite001`: conexao OK, JSON simples OK com backoff; `CORRIGIR` falhou
  alto apos `a7f02a3` por JSON sem schema minimo (`8c875cf984e55e91`,
  `US$0.005241`).
- `gem25flash001`: conexao OK, `CORRIGIR` OK, pipeline individual completa OK,
  `desempenho_tarefa` OK completo, `desempenho_turma` OK completo,
  `desempenho_materia` OK parcial com avisos de dados.
- `gem3flash001`: conexao OK, chat JSON OK, `CORRIGIR` OK, pipeline completa OK
  e `desempenho_tarefa` OK parcial; manter como validado com ressalva de
  custo/latencia.
- `e251747cd7a2`: nao retestado neste ciclo; Pro fica por ultimo por custo.
- Desempenho agregado: validado ate materia com Google Flash. O proximo passo
  nao e desbloquear endpoint, e limpar dados historicos/ausentes para transformar
  materia de parcial em completo.

## Atualizacao 2026-05-18 -- Anthropic Haiku 4.5 Completa Pipeline Individual

Patches publicados e validados:

- `334825d` (`fix: prioritize strict json retry prompts`): colocou o contrato de JSON cru antes do prompt original no retry, sem aceitar envelope Markdown.
- `62fa27d` (`fix: request structured json from anthropic`): passou a usar `output_config` JSON estruturado da API Anthropic quando o prompt pede JSON cru.
- `e548816` (`fix: use strict anthropic extraction schemas`): substituiu schema generico por schemas estritos de extração.
- `d357960` (`fix: validate pipeline schemas during parsing`): corrigiu a ordem de inferencia de schema quando `questoes` aparece apenas como contexto e religou a validação runtime lazy.

Evidencia oficial no Render `d357960`:

| Etapa | Documento | Tokens | Custo |
|---|---|---:|---:|
| `EXTRAIR_QUESTOES` | `d11486043fd2856e` | `2400/437` | `US$0.004585` |
| `EXTRAIR_GABARITO` | `55bbe9f20a79d3f7` | `3296/848` | `US$0.007536` |
| `EXTRAIR_RESPOSTAS` | `fa21df6427683bca` | `3677/520` | `US$0.006277` |
| `CORRIGIR` | `cf52ae50099a7623` | `55539/13206` | `US$0.121569` |
| `ANALISAR_HABILIDADES` | `cff266a64d1d4256` | `27858/8636` | `US$0.071038` |
| `GERAR_RELATORIO` | `611f9ae8226692cf` / `60fe1cc4dfd2a1af` | `25255/9245` | `US$0.071480` |

Total medido da pipeline Haiku Beatriz: `118025/32892` tokens, `US$0.282485`.

Interpretação:

- Haiku 4.5 saiu de ❌ por envelope Markdown para ✅ em pipeline individual no site oficial.
- A validação do parser continua bloqueante; o sistema não passou a aceitar Markdown como JSON.
- O task id da full pipeline não foi preservado pelo cliente local de polling, mas os artefatos, o runtime `d357960` e `/api/custos/resumo` confirmam o ciclo completo.
- Haiku custa mais que Gemini 2.5 Flash neste caso (`US$0.282485` vs `US$0.114578`) e menos que alguns OpenAI/GPT-4o históricos; vale como provider funcional, não como default automático.
- Atualizacao 2026-05-19: a migration `backend/migrations/002_create_token_usage.sql` foi aplicada; `token_usage_durable=true`. Naquele momento ainda faltava provar escrita row-level; isso foi fechado depois por `518f8a2` e `58781a1`, que levaram `record_count` para `2` e `token_usage_analisados=2`.
