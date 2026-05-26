# 03 — Evidências dos runs por provider

> **Status:** 🟡 Anthropic terminou parcialmente (comprometido por alucinação); Gemini parado pelo bug do guard; GPT-5 ainda não disparado
> **Atualizado:** 2026-05-25 21:45 UTC

---

## Setup comum

- **Matéria/turma/atividade:** Álgebra Linear Avançada → 2026-1 → Lista0 (38 alunos, ids preservados via `_recover_supabase.py`)
- **Nível:** "Desempenho da turma" (cascade: 38 alunos × 6 etapas + 1 desempenho-tarefa = 229 calls ideal)
- **force_reexec:** true (para gerar versão de cada provider)
- **Captura de custo:** tokens já estão em `metadata.tokens_entrada/tokens_saida` de cada doc; agregado por [_audit_relatorios.py](./_audit_relatorios.py); custo estimado por rates do `backend/data/model_catalog.json`

---

## Incidente operacional 2026-05-24 ~21:11 UTC (não conta como Run)

Primeiro dispatch via Playwright falhou em capturar `task_id` (sleep de 4s pós-submit < latência real ~5-8s do endpoint). Pra debugar, executei `curl -X POST /api/executar/pipeline-desempenho-turma` direto e o endpoint retornou `task_5087f07f6438` — criando um run real sem ter passado pela UI.

Otávio escolheu **Cancelar e re-disparar via UI** (vs deixar rodar). Cancelamento via `POST /api/task-cancel/task_5087f07f6438` registrado. Custo gasto antes do cancel: trivial (<$0.05, task ainda em init quando flag setou).

Script corrigido: `page.on('response', ...)` intercepta o body do POST, polling de até 20s, fallback pra `window._desempenhoActiveTasks`. Re-dispatch via UI logo após.

---

## Incidente operacional 2026-05-25 — gabarito alucinado em retries Anthropic

Auditoria descobriu que TODOS os 10 relatórios `relatorio_final.json` Anthropic foram baseados em correção contra gabarito **alucinado** pelo próprio Anthropic em retries de `extracao_gabarito`. Detalhes em [04_matriz_provider_custo.md](./04_matriz_provider_custo.md#caveat).

- PDF real do gabarito: só tem resolução da Q5
- Anthropic chamou `extracao_gabarito` 91 vezes; em algum retry alucinou conteúdo pra Q1-Q4/Q6-Q7 (texto longo de "interpolação polinomial", "matriz de Vandermonde" inventado)
- Backend guard ([executor.py:2190-2198](../../backend/executor.py#L2190)) abortava CORRIGIR se o gabarito tinha `MISSING_CONTENT`; com o gabarito alucinado, MISSING_CONTENT some, guard libera, CORRIGIR passa, mas a "nota" é contra texto inventado

Notas atribuídas (variação 0.00–6.58 entre os 10 alunos) **não têm valor científico** — 6 das 7 questões foram comparadas contra resposta_correta alucinada.

---

## Run 1: Anthropic — claude-haiku-4-5-20251001

- **Iniciado em:** 2026-05-25T00:12:31 UTC
- **task_id:** `task_eef18debdfe8` (cancelado em ~10:55 UTC; cumulative work até 03:11 UTC já fixado no DB)
- **Status:** ⚠️ **PARCIALMENTE COMPROMETIDO** — 10/22 alunos com pipeline full, todas as 10 correções comprometidas por alucinação no gabarito
- **Duração:** ~3h reais de processamento (00:12 → 03:11 UTC) antes de eu cancelar
- **Docs gerados:** 449 (esperado ~132 — 2x mais por retries)
- **Custo total:** **US$ 42.6539** (estimado por tokens, rates do catálogo)
- **Custo por etapa:**
  - EXTRAIR_QUESTOES: $1.36 (91 docs, 435K in / 185K out)
  - EXTRAIR_GABARITO: $1.46 (91 docs, 980K in / 96K out) — com alucinação
  - EXTRAIR_RESPOSTAS: $4.36 (76 docs, 3.18M in / 236K out)
  - CORRIGIR: $30.38 (149 docs, 13.96M in / 3.28M out) — 6.8 retries médios por aluno
  - ANALISAR_HABILIDADES: $2.89 (22 docs, 1.41M in / 295K out)
  - GERAR_RELATORIO: $2.20 (20 docs, 1.11M in / 217K out)
- **Erros observados:**
  - Crédito Anthropic esgotado após o run (sem novos runs possíveis)
  - 100% dos 10 relatórios `.json` baseados em gabarito alucinado em Q1-Q4/Q6-Q7
- **Notas dos 10 alunos com pipeline full:** ver tabela em [04_matriz_provider_custo.md#por-aluno](./04_matriz_provider_custo.md#por-aluno-—-sample-de-10-relatórios-anthropic-audit-completa)
- **Evidência de visualização na UI:** Playwright clicou no relatório da Jordana e modal abriu com 12KB de texto — screenshot em [`_click_relatorio_20260525_212924/`](./_click_relatorio_20260525_212924/). UI renderiza, conteúdo legível — só não é cientificamente correto.

---

## Run 2: Google — gemini-3-flash-preview

- **Iniciado em:** 2026-05-25T21:03:35 UTC (`task_0f8772372008`)
- **task_id:** `task_0f8772372008` — SUMIU do registry após restart Render às ~21:12 UTC
- **Status:** ❌ **ABORTADO pelo guard strict no CORRIGIR**
- **Duração:** ~9 min reais antes de parar
- **Docs gerados:** 27 (12 extracao_questoes, 12 extracao_gabarito, 3 extracao_respostas — todos OK, JSON estruturado)
- **Custo total:** **US$ 0.2723** (todos os 27 docs Gemini, somando run histórico 2026-05-23 + run de hoje)
- **Erros observados:**
  - Backend retornou `error: "corrigir: Gabarito extraido incompleto para correcao: questoes 1, 2, 3, 4, 6, 7"`
  - Causa: Gemini reportou honestamente `MISSING_CONTENT` no gabarito; guard [executor.py:2190](../../backend/executor.py#L2190) aborta a etapa
  - Registry in-memory perdeu task_id em restart Render; painel de progresso na UI sumiu antes da task completar
- **Notas:** Gemini é o provider mais barato POR CALL ($0.01 contra $0.095 do Anthropic, 9.5x mais barato). Mas só dá pra comparar pipeline completa após o fix do guard.

---

## Run 3: OpenAI — gpt-5-nano

- **Iniciado em:** _pendente_ (ainda não disparei)
- **task_id:** _pendente_
- **Status:** ⏸️ **NÃO DISPARADO AINDA**
- **Custo total:** $0
- **Notas:**
  - GPT-5 Nano é teoricamente o mais barato dos 3 ($0.05 in / $0.40 out por 1M)
  - Vou disparar via UI (Playwright) APÓS o fix do guard, com `force_reexec=true`
  - 8 docs OpenAI existentes na atividade são de run histórico `gpt-5.4-mini` 2026-05-24, fora do escopo deste loop

---

## Próximas ações operacionais

1. Aplicar fix do guard ([executor.py:2190-2198](../../backend/executor.py#L2190))
2. Commit + push + deploy
3. Re-disparar Gemini com fix (deve passar pelo CORRIGIR agora, com Q1-Q4/Q6-Q7 marcadas "não corrigíveis")
4. Disparar GPT-5 Nano
5. Atualizar esta tabela + matriz incrementalmente conforme docs forem gerados (script de polling a cada 60s)
