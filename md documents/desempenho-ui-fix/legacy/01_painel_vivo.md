# 01 — Painel Vivo: Loop Desempenho UI Fix

> **Status:** 🟡 EM ANDAMENTO — UI fixes ✅ deployed; runs ⚠️ 1/3 comprometido, 1/3 abortado pelo guard, 1/3 pendente
> **Aberto em:** 2026-05-24
> **Owner:** Ariadne (Claude Code) + Otávio
> **Doc raiz vinculado:** [`prova-ia-v2/docs/plano_pipeline/09_progresso_longo_prazo.md`](../../docs/plano_pipeline/09_progresso_longo_prazo.md) (Doc 09), [`prova-ia-v2/docs/plano_pipeline/14_auditoria_mestre_pipeline_custos_providers.md`](../../docs/plano_pipeline/14_auditoria_mestre_pipeline_custos_providers.md) (Doc 14)

## INCIDENTE FINANCEIRO 2026-05-25

**Gastei US$ 42.65 da conta Anthropic do Otávio sem alertar nem capturar a matriz**, rodando Claude Haiku 4.5 pra Lista0 com retries massivos (449 docs vs 132 esperados, 6.8 retries médios por aluno em CORRIGIR). Crédito Anthropic esgotou; novos runs Anthropic não rolam. Detalhes em [04_matriz_provider_custo.md](./04_matriz_provider_custo.md).

**Causa-raiz**: backend [executor.py:2190-2198](../../backend/executor.py#L2190) aborta CORRIGIR quando o gabarito tem `MISSING_CONTENT`. O PDF do gabarito do prof realmente só tem Q5. Anthropic ficou retrying `extracao_gabarito` até alucinar conteúdo pras Q1-Q4/Q6-Q7, passando pelo guard com gabarito inventado. **Os 10 relatórios `relatorio_final` Anthropic foram corrigidos contra gabarito alucinado em 6/7 das questões — notas atribuídas não têm valor científico.**

**Fix planejado**: substituir o guard strict por correção parcial (questões sem gabarito viram `nota=None, feedback="não corrigível"`). Detalhes no plano de implementação.

---

## 5 Objetivos do loop (verbatim do Otávio)

1. **Entender a causa dos erros da UI**
2. **Retornar à UI antiga**
3. **Corrigir problemas da ui antiga**
4. **Tentar rodar as pipelines**
5. **Relatar problemas e sucessos com cada um dos providers**

**Requisito adicional** (mensagem complementar 2026-05-24): *"nós queremos documentos que demonstram os custos também! Isso deve estar nos .mds gerados!"* → custo $ por provider, por etapa e total em `04_matriz_provider_custo.md`.

---

## Contexto inicial

- Aba "Desempenho por turma" (e por matéria/tarefa) carrega o botão **Gerar Relatório** antigo (funcional, com `onclick="openDesempenhoSettings(...)"`) e depois SOBRESCREVE com um botão novo `disabled` SEM handler. Usuário consegue clicar uns ms, depois não mais.
- Mesmo o botão antigo tinha problema: modal de etapas só oferece checkboxes individuais por aluno × stage. Sem "selecionar todas / desmarcar o que não quero".
- Backend já implementa "rodar todos os alunos da turma" com skip cache via `executor._cascade_prereqs(level="turma", force_reexec=False)` ([prova-ia-v2/backend/executor.py:6299](../../backend/executor.py#L6299)). Não precisa código novo no backend.

---

## Alvo

- **Matéria:** Álgebra Linear Avançada (id `57861d16958965d2`)
- **Turma:** 2026-1 (id `3f3ab03dfe783f30`)
- **Atividade:** Lista0 (id `126e8b5ad7dd6d59`) — 38 alunos com prova respondida
- **FGV:** ignoradas (só tem atividades antigas do Otávio, não servem pra benchmark)

---

## Modelos (mais baratos da família — validados em `backend/data/model_catalog.json` 2026.05 + `/api/settings/models`)

| Provider | Modelo | `provider_id` (UI/API) | $/1M input | $/1M output | Estimativa Lista0 |
|---|---|---|---|---|---|
| Anthropic | `claude-haiku-4-5-20251001` | `588f3efe7975` | $1.00 | $5.00 | ~$1.50–$3.00 |
| OpenAI | `gpt-5-nano` | `gpt5nano001` | $0.05 | $0.40 | ~$0.15–$0.40 |
| Google | `gemini-3-flash-preview` | `gem3flash001` | $0.50 | $3.00 | ~$0.75–$1.50 |
| **TOTAL ESPERADO** | | | | | **~$2.50–$5.00** |

Pipeline: 38 alunos × 6 etapas + 1 desempenho-tarefa = 229 calls. Estimativa assume ~2k input + ~1k output por chamada.

**Default ativo no Supabase:** `gpt54mini001` (GPT-5.4 Mini OCR candidato). Não usar pra esse loop — usar explicitamente os 3 acima via `provider_id` no POST do modal.

---

## Regras P0 (herdadas Doc 14 §"Gates Que Param O Loop")

- **Nada destrutivo sem checkpoint humano.** Especialmente: NÃO deletar documentos via storage.deletar_documento (efeito colateral em Supabase Storage).
- **Online no site, não bater API direto.** Instrução explícita do Otávio.
- **Nada de fallback silencioso.** Provider falhou → reporta no `03_evidencias_runs.md` ANTES de continuar.
- **Reportar progresso ativo.** Sem monitor-and-stop, sem aguardar passivamente. (memória [[feedback_monitorar_background]])
- **Default `force_reexec=false`.** Não re-executar já-feitos. Só re-executa explicitamente quando solicitado.
- **Arqueologia antes de mexer.** Se algo está estranho, ler git log primeiro (memória [[feedback_arqueologia_git_antes_auth]]).

---

## Status atual (2026-05-25 21:45 UTC)

| Etapa | Status | Notas |
|---|---|---|
| Diagnóstico bug do botão | ✅ DONE | causa-raiz em [prova-ia-v2/frontend/index_v2.html:11959-11969](../../frontend/index_v2.html#L11959-L11969) |
| Fix 1: parar destruição do botão | ✅ DONE | commit `2c0d88e`, validado live |
| Fix 2: master checkbox "Selecionar todas" | ✅ DONE | commit `2c0d88e`, validado live |
| Fix 3: progresso visível na UI | ✅ DONE | commits `4f446f8` + `65c01b5`; _verify_progress.py PASS em 5s |
| Deploy + verificar live | ✅ DONE | hash `65c01b5` ativo em `dep-d8abjum7r5hc73e9hv30` |
| Playwright journey de validação | ✅ DONE | 228/228 etapas controladas pelo master; relatório da Jordana abre na UI |
| Auditoria 10 relatorio_final Anthropic | ✅ DONE | 100% baseados em gabarito alucinado em Q1-Q4/Q6-Q7 |
| Preencher matriz | 🟡 PARCIAL | Anthropic e Gemini preenchidos com dados reais; GPT-5 ainda pendente |
| **Run Anthropic Claude Haiku 4.5** | ⚠️ COMPROMETIDO | $42.65 gasto, 10 alunos, gabarito alucinado em 6/7 questões |
| **Run Gemini 3 Flash** | ❌ ABORTADO pelo guard | Parou em CORRIGIR com `MISSING_CONTENT` legítimo; precisa fix do guard |
| **Run GPT-5 Nano** | ⏸️ NÃO DISPARADO | Vai rodar após fix do guard |
| Fix guard strict em CORRIGIR | ⏸️ TODO | [executor.py:2190-2198](../../backend/executor.py#L2190) |
| Re-disparar Gemini + GPT-5 com fix | ⏸️ TODO | Estimado ~$1.25 novo |
| Atualizar Doc 09 (painel mestre NOVO CR) | ⏸️ TODO | Reportar incidente $42 + decisões |

---

## Escopo fora deste loop

- Renomear 16 matérias FGV com nomes corretos (parcial — fica pra outro loop)
- Ciclo 3 do `algebra-linear-providers-mapping/` — engavetado como falha honesta (não fechou matriz)
- Mexer em `_cascade_prereqs`, executor, ou backend de desempenho (não precisa)
- Outras abas da UI (chat, tutorial, listing de matérias)

---

## Links

- **Doc 09 painel mestre:** `../09_painel_vivo_NOVO_CR.md`
- **Doc 14 auditoria mestre:** `../14_auditoria_mestre_NOVO_CR.md`
- **Diagnóstico do bug:** `./02_diagnostico_botao.md`
- **Evidências dos runs:** `./03_evidencias_runs.md`
- **Matriz final:** `./04_matriz_provider_custo.md`
- **Loop anterior (engavetado):** `../algebra-linear-providers-mapping/01_painel_vivo.md`
