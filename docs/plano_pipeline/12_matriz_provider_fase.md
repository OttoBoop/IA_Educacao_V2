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

## Matriz por Provider e Etapa

| Provider/Modelo | 1. EXTRAIR_QUESTOES | 2. EXTRAIR_GABARITO | 3. EXTRAIR_RESPOSTAS | 4. CORRIGIR | 5. ANALISAR_HABILIDADES | 6. GERAR_RELATORIO |
|-----------------|:---:|:---:|:---:|:---:|:---:|:---:|
| **Claude Haiku 4.5** (`588f3efe7975`) | ⏸️ | ⏸️ | ⏸️ | 🚫 | 🚫 | 🚫 |
| **Gemini 3 Flash** (`gem3flash001`) | ⏸️ | ⏸️ | ⏸️ | 🚫 503 | ⏸️ | ⏸️ |
| **GPT-5 Nano** (`gpt5nano001`) | ⏸️ | ⏸️ | ⏸️ | ⚠️ | ⏸️ | ⏸️ |
| **GPT-4o** (`180b8298a279`) — referencia | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |

---

## Detalhamento por Provider

### Claude Haiku 4.5 — 🚫 BLOQUEADO

**Motivo:** Creditos Anthropic insuficientes. Todas as tentativas retornam 400 com "This organization's credit balance is too low."

**Acao necessaria (Otavio):** Recarregar creditos na conta Anthropic. Nenhum teste possivel ate la.

---

### Gemini 3 Flash Preview — 🚫 OVERLOAD + PARSE_ERR

**Motivo:** Modelo em preview retorna 503 "high demand" ou parse_err ao tentar CORRIGIR/pipeline-completo.

**Status:**
- Tentativa via `/executar/etapa`: 503 (provider overload)
- Tentativa via `pipeline-completo`: task disparou mas monitor reportou `status=parse_err` (Gemini retornou JSON malformado que nao passou no `_parsear_resposta`)
- Fix do `/executar/etapa` foi aplicado, mas nao validado empiricamente com Gemini

**Acao recomendada:** Tentar novamente em horario menos pico. Ou testar com Gemini 2.5 Pro (nao-preview). O parse_err sugere que o schema JSON que Gemini retorna pode divergir do esperado — vale investigar.

---

### GPT-5 Nano — ⚠️ PARCIAL

**Testado via `/executar/etapa`** (ver [teste_executar_etapa_corrigido.md](teste_executar_etapa_corrigido.md))

**Etapa CORRIGIR para Henrique Coelho Beltrao:**
- HTTP 200, sucesso=true
- Tokens: 7093
- JSON gerado: nota 5.72/10, feedback especifico (Q3/Q5/Q6/Q7, matrizes elementares)
- Template `{{...}}` literais: **NENHUM** na saida (fix confirmado)

**Problemas identificados:**
1. ⚠️ **Sem campos `_avisos_*`** — JSON nao contem `_avisos_documento`, `_avisos_questao`, `_avisos_stage`. A injecao do `tool_handlers.py` nao pegou este caminho.
2. ⚠️ **Schema antigo (flat)** — retornou `nota`, `feedback`, `pontos_positivos` em vez do STAGE_TOOL_INSTRUCTIONS (`nota_final`, `questoes[]`).
3. ⚠️ **Nao persistiu** — `arquivos_gerados: []`, zero documentos `correcao` no banco apos o teste. Endpoint gera resposta mas nao salva.

**Nao testado ainda:** outras 5 etapas.

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

## Resumo Executivo

**Estado atual:** Apenas **GPT-4o via `pipeline-completo`** e **GPT-5 Nano via `/executar/etapa`** tem validacao empirica parcial (ambos com ressalvas sobre `_avisos_*`).

**Nenhum provider** foi validado end-to-end com os novos fixes aplicados (commits de hoje).

**Bloqueios:**
- Anthropic: sem creditos (acao do Otavio)
- Google (Gemini 3 Flash): 503 overload (aguardar)

**Proximo passo logico:** Quando Gemini estabilizar ou Anthropic recarregar, rodar `pipeline-completo` end-to-end com esse provider para o Eric e atualizar esta matriz.
