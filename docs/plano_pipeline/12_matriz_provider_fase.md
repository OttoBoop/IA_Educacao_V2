# Matriz Provider × Fase — Status Atual

**Atualizado:** 2026-05-15
**Atividade de teste:** Lista0 — Algebra Linear Avancada (`126e8b5ad7dd6d59`)
**Commits aplicados/observados:** `a632883`, `5737611`, `50935ea`, `479b77d`,
`b12be9a`, `301eba6`, `f67055c`, `462ea1d`, `b4d7ee6`, `99483d1`

## Status Oficial De Deploy

- GitHub `origin/main` contem `99483d1` e registros documentais posteriores; o
  marcador HTML aponta para `b4d7ee6`.
- Render live confirma marcador `b4d7ee6`; `/api/health` e `/api/custos/status`
  responderam HTTP 200.
- Portanto, os smokes live de 2026-05-15 abaixo sao oficiais para o estado
  `b4d7ee6`.

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
| **Gemini 3 Flash** (`gem3flash001`) | ⏸️ | ⏸️ | ⏸️ | ❌ | ⚠️ | ⚠️ |
| **GPT-5 Nano** (`gpt5nano001`) | ⏸️ | ⏸️ | ⏸️ | ❌ | ❌ | ❌ |
| **GPT-4o** (`180b8298a279`) — referencia | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |

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

### Gemini 3 Flash Preview — ❌ PIPELINE POS-FIX FALHOU NO CORRIGIR

**Smoke live pos-fix:** `pipeline-completo` com apenas `corrigir` falhou em
2026-05-15. Antes do patch, a task nao expôs `error`; depois do deploy
`b4d7ee6`, a causa apareceu: Google API 503 `UNAVAILABLE` por alta demanda.
Antes de promover Gemini como confirmado, e necessario repetir a etapa quando o
provider sair de overload ou implementar retry visivel no caminho tool-use.

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

### GPT-5 Nano — ✅ CHAT SIMPLES, ❌ FALHA no pipeline-completo

**Smoke live de chat em 2026-05-15:** respondeu JSON simples corretamente via
`POST /api/chat` com `model_id=gpt5nano001` e 526 tokens. Portanto o bloqueio
atual do Nano nao e conexao/API key; e pipeline/tool-use/schema.

**Testado em 2 caminhos com resultados muito diferentes:**

#### Via `/executar/etapa` — ⚠️ PARCIAL
Ver [teste_executar_etapa_corrigido.md](arquivo_2026_04_17/teste_executar_etapa_corrigido.md). Gerou nota 5.72/10 com feedback coerente, mas sem `_avisos_*`, schema flat, sem persistencia.

#### Via `pipeline-completo` — ❌ FALHA GRAVE
Ver [teste_gpt5nano_pipeline_completo.md](arquivo_2026_04_17/teste_gpt5nano_pipeline_completo.md). Task `task_ca3769cfdc97` terminou em `failed` em ~23s.

**Bugs descobertos no tool-use path:**
1. **Multiplas chamadas `create_document` por stage** (deveria ser 1) — criou 3 docs lixo: JSON malformado, txt vazio, texto natural salvo em arquivo `.json`
2. **Nomes/extensoes alucinadas:** `document_2.txt`, `correcao_henrique.pdf.json`
3. **Sem validacao de schema** — stage marcada como "completed" apesar de outputs inutilizaveis
4. **Metadata nula no DB:** `ia_provider`, `ia_modelo`, `tokens_usados`, `prompt_usado` ficaram null/0
5. **Cascade de falha:** `analisar_habilidades` falhou (nao achou correcao valida), `gerar_relatorio` nem executou
6. **`_avisos_*` NAO aparecem** — hipotese de que tool-use path injetaria foi **refutada**
7. **Schema ainda flat** — GPT-5 Nano nao segue STAGE_TOOL_INSTRUCTIONS mesmo em pipeline-completo

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
- [ ] Repetir `pipeline-completo` com Gemini 3 Flash quando 503 passar, ou
      corrigir retry visivel para 429/5xx no tool-use antes da repeticao
- [ ] Investigar por que `_avisos_*` nao aparece com GPT-5 Nano mesmo com injecao ativa
- [ ] Investigar por que `/executar/etapa` nao persiste documento (gap ou by-design?)

### Prioridade MEDIA
- [ ] Validar `pipeline-completo` com GPT-5 Nano para 1 aluno
- [ ] Testar Haiku 4.5 (bloqueado ate creditos recarregarem)

### Prioridade BAIXA
- [ ] Testar GPT-5 Nano nas 6 etapas (atualmente so testado em CORRIGIR)
- [ ] Comparar qualidade dos outputs entre os 3 modelos-alvo

---

## Resumo Executivo (atualizado)

**Estado atual:**
- ⚠️ **Gemini 3 Flash:** chat simples live OK; pipeline historica teve sucesso,
  mas o smoke pos-fix de `corrigir` falhou por Google 503 `UNAVAILABLE`. Nao
  esta confirmado para pipeline oficial.
- ❌ **GPT-5 Nano via `pipeline-completo`:** QUEBRADO — tool-use path produz documentos lixo. Fix necessario no loop de tool-use.
- ⏸️ **Claude Haiku 4.5:** Aguardando creditos.
- 📊 **Confiabilidade Gemini 3 Flash:** 50% de sucesso na primeira tentativa (1 em 2 testes). Precisa mais amostras.

**Marco 1 ainda nao atingido oficialmente:** chat e historico positivo ajudam,
mas o site oficial precisa passar pipeline pos-fix com erro/custo/metadata
visiveis.

**Bugs criticos descobertos nesta sessao:**
1. GPT-5 Nano tool-use: multiplas chamadas `create_document`, nomes alucinados, sem validacao de schema
2. Metadata `tokens_usados`, `ia_modelo`, `ia_provider` nao sao populados no DB (afeta todos os providers testados)
3. Endpoint `/conteudo` nao retorna conteudo para alguns tipos (usar `/view`)
4. Sem endpoint de eventos de task (dificulta diagnostico de falhas transientes)

**Proximos passos:**
1. Desbloquear deploy oficial; sem Render no hash esperado, a matriz continua
   historica.
2. Corrigir/classificar retry visivel para Google 503/429 em tool-use, ou
   repetir Gemini 3 Flash quando a sobrecarga passar.
3. Revalidar GPT-5 Nano esperando falha alta quando dual-output estiver
   incompleto; nao aceitar JSON/PDF lixo como sucesso.
4. Quando creditos Anthropic forem recarregados, validar Haiku 4.5 via
   `pipeline-completo`.
