# Matriz Provider × Fase — Status Atual

**Atualizado:** 2026-04-17
**Atividade de teste:** Lista0 — Algebra Linear Avancada (`126e8b5ad7dd6d59`)
**Commits aplicados:** `a632883`, `5737611`

## Legenda

- ✅ **OK** — Etapa rodou, JSON valido, conteudo faz sentido
- ⚠️ **PARCIAL** — Rodou mas com problemas (sem avisos, schema antigo, nao persistiu, etc.)
- ❌ **FALHA** — Nao rodou ou retornou erro
- ⏸️ **NAO TESTADO** — Ainda nao foi testado
- 🚫 **BLOQUEADO** — Nao pode testar (creditos, overload, etc.)

---

## Matriz por Provider e Etapa (atualizada apos Rodada 4c/4d)

| Provider/Modelo | 1. EXTRAIR_QUESTOES | 2. EXTRAIR_GABARITO | 3. EXTRAIR_RESPOSTAS | 4. CORRIGIR | 5. ANALISAR_HABILIDADES | 6. GERAR_RELATORIO |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Claude Haiku 4.5** (`588f3efe7975`) | ⏸️ | ⏸️ | ⏸️ | 🚫 | 🚫 | 🚫 |
| **Gemini 3 Flash** (`gem3flash001`) | ⏸️ | ⏸️ | ⏸️ | ✅ | ✅ | ✅ |
| **GPT-5 Nano** (`gpt5nano001`) | ⏸️ | ⏸️ | ⏸️ | ❌ | ❌ | ❌ |
| **GPT-4o** (`180b8298a279`) — referencia | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |

---

## Detalhamento por Provider

### Claude Haiku 4.5 — 🚫 BLOQUEADO

**Motivo:** Creditos Anthropic insuficientes. Todas as tentativas retornam 400 com "This organization's credit balance is too low."

**Acao necessaria (Otavio):** Recarregar creditos na conta Anthropic. Nenhum teste possivel ate la.

---

### Gemini 3 Flash Preview — ✅ SUCESSO (com 1 retry)

**Testado via `pipeline-completo`** para Eric Manoel (ver [teste_gemini_pipeline_completo.md](teste_gemini_pipeline_completo.md))

**Tentativa 1:** Falhou em ~30s (provavelmente 503 transiente)
**Tentativa 2:** SUCESSO em ~105s, 3 documentos gerados

| Etapa | Status | Doc JSON | Doc PDF |
|-------|--------|----------|---------|
| CORRIGIR | ✅ | `bb0f0c63f75589dd` | `b3a786693fc384df` |
| ANALISAR_HABILIDADES | ✅ | `f6e7fa7ef961bf15` | `085a078eebb5ef93` |
| GERAR_RELATORIO | ✅ | `26697c8894eca2ad` | `4a00dcef2eed4ea3` |

**Verificacoes que passaram:**
- Nota final consistente cross-stage: **7.01**
- Avisos `MISSING_CONTENT` propagaram corretamente para Q2 e Q4 (questoes em branco)
- Todos os 3 JSONs tem `_avisos_documento`, `_avisos_questao` (com 2 itens reais!), `_avisos_stage`
- Conteudo qualitativamente correto (Vandermonde+Julia, decomposicoes matriciais, forward substitution, minimos quadrados)

**Ressalvas:**
1. `tokens_usados=0` e `ia_modelo=null` no metadata do DB — bug de populamento (nao invalida conteudo)
2. 50% de falha na primeira tentativa (precisa mais amostras para confiar sem retry)
3. Endpoint `/conteudo` retorna metadata, nao conteudo — usar `/view` (gap de contrato)

---

### GPT-5 Nano — ❌ FALHA no pipeline-completo

**Testado em 2 caminhos com resultados muito diferentes:**

#### Via `/executar/etapa` — ⚠️ PARCIAL
Ver [teste_executar_etapa_corrigido.md](teste_executar_etapa_corrigido.md). Gerou nota 5.72/10 com feedback coerente, mas sem `_avisos_*`, schema flat, sem persistencia.

#### Via `pipeline-completo` — ❌ FALHA GRAVE
Ver [teste_gpt5nano_pipeline_completo.md](teste_gpt5nano_pipeline_completo.md). Task `task_ca3769cfdc97` terminou em `failed` em ~23s.

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

**Testado via `pipeline-completo`** para Eric Manoel (ver [teste_haiku_eric.md](teste_haiku_eric.md))

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
- [ ] Validar `pipeline-completo` com Gemini 3 Flash (quando overload passar) para 1 aluno
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
- ✅ **Gemini 3 Flash via `pipeline-completo`:** VALIDADO end-to-end com todos os fixes. Marco 1 atingido com este provider (nota 7.01 consistente, avisos propagando, conteudo correto).
- ❌ **GPT-5 Nano via `pipeline-completo`:** QUEBRADO — tool-use path produz documentos lixo. Fix necessario no loop de tool-use.
- ⏸️ **Claude Haiku 4.5:** Aguardando creditos.
- 📊 **Confiabilidade Gemini 3 Flash:** 50% de sucesso na primeira tentativa (1 em 2 testes). Precisa mais amostras.

**Marco 1 parcialmente atingido:** Gemini 3 Flash funciona com `pipeline-completo`. Quando Haiku tiver creditos, validamos o segundo provider.

**Bugs criticos descobertos nesta sessao:**
1. GPT-5 Nano tool-use: multiplas chamadas `create_document`, nomes alucinados, sem validacao de schema
2. Metadata `tokens_usados`, `ia_modelo`, `ia_provider` nao sao populados no DB (afeta todos os providers testados)
3. Endpoint `/conteudo` nao retorna conteudo para alguns tipos (usar `/view`)
4. Sem endpoint de eventos de task (dificulta diagnostico de falhas transientes)

**Proximos passos:**
1. Investigar por que GPT-5 Nano gera documentos lixo no tool-use (provavelmente loop de iteracoes sem limite + sem validacao de schema do `create_document`)
2. Quando creditos Anthropic forem recarregados, validar Haiku 4.5 via `pipeline-completo`
3. Corrigir populamento de metadata de tokens/modelo no DB
