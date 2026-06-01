# 01 — Objetivos, Decisões e Tarefas do Loop

## Objetivos originais (Otávio, 2026-05-24)

> 1. Entender a causa dos erros da UI
> 2. Retornar à UI antiga
> 3. Corrigir problemas da ui antiga
> 4. Tentar rodar as pipelines
> 5. Relatar problemas e sucessos com cada um dos providers

> "nós queremos documentos que demonstram os custos também!" — Otávio, 2026-05-24

> Custos devem ser REAIS por pedido API, não estimados — Otávio, 2026-05-27

> "é perfeitamente esperado que a gente possa usar uma provider ou ia para um doc e outra para outro. O que não está claro é o comportamento que estamos adotando." — Otávio, 2026-05-27

> "Precisamos de alguma forma, nas opções avançadas da ui e do backend, para escolher quais dos documentos anteriores vamos utilizar na pipeline." — Otávio, 2026-05-27

> "pipeline de todos os alunos não precisa esperar que um aluno termine para começar o outro, apenas esperar que um documento na pipeline individual de alunos termine" — Otávio, 2026-05-20

---

## O que já foi feito (deployed)

| # | O quê | Commit | Funciona? | Verificado como? |
|---|---|---|---|---|
| D1 | Fix botão Gerar Relatório | `2c0d88e` | ✅ | Playwright 228/228 checkboxes |
| D2 | Master select-all no modal | `2c0d88e` | ✅ | Playwright |
| D3 | Painel de progresso live per-student per-stage | `4f446f8` + `65c01b5` | ✅ | Playwright: painel renderiza em 5s |
| D4 | Guard gabarito: correção parcial permitida | `4c68e15` | ⚠️ | Guard passa, mas modelos baratos geram relatório vazio (T3 tenta consertar) |
| D5 | Schema validator aceita MISSING_CONTENT | `181d2df` | ✅ | Questões MISSING_CONTENT pulam checks de nota/acerto |
| D6 | Batch tolerance (1 aluno falha não mata 38) | `181d2df` | ✅ | Task continua running com 33 falhas e 5 pendentes |
| D7 | Pre-popular students com nomes no task_registry | `65c01b5` | ✅ | Nomes aparecem no painel desde o poll 0 |
| D8 | **T1: Paralelismo** asyncio.gather + Semaphore(12) | `7fc6833` | ✅ | **Confirmado**: poll mostrou `active=12` (12 alunos simultâneos) |
| D9 | **T2: Isolamento provider** checkbox + tabela Docs Disponíveis | `7fc6833` | ⚠️ Parcial | Checkbox + tabela visual OK. Seleção individual de doc ❌. **Bug**: `etapas_selecionadas` não filtra alunos no cascade (selecionei 2, rodou 38) |
| D10 | **T3: Diretiva CORRIGIR** reescrita com 6 instruções | `7fc6833` | ❌ Não resolveu | Gemini Flash: 33/38 falharam em CORRIGIR ("limite iterações tools" + "resposta_aluno divergente"). GPT-5 Nano antes: relatório vazio. |

---

## Tarefas pendentes (atualizado 2026-05-27 13:55 UTC)

### T1. Paralelismo ✅ FEITO
Commit `7fc6833`. 12 workers (env var `PARALLEL_WORKERS`). Confirmado: 12 alunos simultâneos.

### T2. Seleção de docs por provider ⚠️ PARCIAL
- ✅ Checkbox "Isolar provider" + seção "Docs Disponíveis" (commit `7fc6833`)
- ❌ Seleção individual de doc por etapa (`doc_id` override)
- **Bug achado**: `etapas_selecionadas` do modal é ignorado pelo `_cascade_prereqs` — selecionei 2 alunos mas rodou 38. O cascade não olha `etapas_selecionadas` pra filtrar quais alunos rodar.

### T3. Diretiva CORRIGIR — DIAGNÓSTICO ATUALIZADO APÓS 3 TENTATIVAS

**Histórico dos fixes:**
1. Commit `7fc6833`: diretiva com 6 instruções → Gemini 33/38 fail (pôs MISSING_CONTENT no resposta_aluno)
2. Commit `d6acf51`: regra 3 "NUNCA coloque MISSING_CONTENT no resposta_aluno" → Re-teste: Gemini AINDA falha, agora com `resposta_aluno=''` (vazio) em TODAS as questões

**Diagnóstico PRECISO (investigado abrindo docs gerados + código):**
- EXTRAIR_RESPOSTAS funciona PERFEITAMENTE (Gemini, 7 respostas reais, Q3/Q5/Q6/Q7 com álgebra linear)
- O contexto `respostas_aluno` É CARREGADO no prompt (se não fosse, `documentos_faltantes` bloquearia a etapa — verificado no código [executor.py:2114-2121](../../backend/executor.py#L2114))
- O template injeta via `{{resposta_aluno}}` no prompt ([prompts.py:411](../../backend/prompts.py#L411))
- O CORRIGIR gera JSON com 7 questões (estrutura OK) MAS com `resposta_aluno=''` em TODAS
- **O modelo LÊ o contexto mas NÃO COPIA os dados pra dentro do JSON de output**

**Causa-raiz**: o prompt pede pro modelo "Copie exatamente a resposta_aluno da extração de respostas" ([prompts.py:431](../../backend/prompts.py#L431)). Isso exige que o modelo LOCALIZE cada resposta no bloco `{{resposta_aluno}}` (que é um JSON grande), EXTRAIA a string correta pra cada questão, e COLE no JSON de output. Com a diretiva de gabarito parcial adicionando ~40 linhas extras, o modelo não consegue fazer essa cópia complexa.

**NÃO É** "modelo barato demais". **É** a pipeline pedindo ao modelo pra fazer trabalho que deveria ser feito por CÓDIGO:
- A cópia de `resposta_aluno` e `resposta_correta` pode ser feita programaticamente ANTES de chamar o modelo
- O modelo recebe a correção pré-montada e só precisa adicionar `nota`, `acerto` e `feedback`

**Fix proposto (T3-v3)**: pré-montar o array `questoes[]` no código ([executor.py, dentro de `corrigir()`](../../backend/executor.py)) com `resposta_aluno` e `resposta_correta` já preenchidos do contexto JSON. Passar esse array pré-montado pro modelo como parte do prompt. O modelo preenche APENAS nota, acerto, feedback.

**Status**: NÃO implementado. Precisa code change no `corrigir()` function.

### T4. Custos reais ✅ JÁ EXISTE
Tabela `token_usage` no Supabase com 807+ registros. Endpoint `/api/custos/resumo` agrega por provider/etapa. Custo = tokens × rate do catálogo. Sem caching API, custo é exato. Confirmado com Otávio: OK pra este teste.

### T5. Verificação automática de conteúdo pós-run — PENDENTE
Script não escrito. Verificação manual feita em:
- 10 relatorio_final Anthropic: conteúdo presente mas gabarito alucinado em 6/7 questões
- 1 relatorio_final GPT-5 Nano: VAZIO (questoes=[])
- 0 relatorio_final Gemini: 33/38 falharam em CORRIGIR, pipeline não chegou lá

### T6. task_registry persistente — PENDENTE
Registry in-memory. 404 intermitentes observados durante polling do teste (Render instável sob 12 workers paralelos?).

### T7. Rodar pipelines de verdade com verificação — BLOQUEADO
**Bloqueado por T3**: enquanto modelos baratos falharem no CORRIGIR, não produzem relatórios verificáveis.
**Bloqueado por T5**: sem verificação automática, relatórios vazios ou alucinados passam despercebidos.
**Decisão pendente do Otávio**: testar com modelo mais capaz (GPT-5, Gemini 2.5 Pro) pra ver se o problema é do modelo ou da pipeline?

---

## Problemas descobertos durante os testes

| # | Problema | Onde | Impacto |
|---|---|---|---|
| P1 | `etapas_selecionadas` ignorado pelo cascade | `_cascade_prereqs` não usa o param | Selecionei 2 alunos, rodou 38 |
| P2 | ~~Modelos baratos falham no CORRIGIR~~ **DIAGNÓSTICO ERRADO** — bug era na diretiva T3 | Gemini pôs MISSING_CONTENT no `resposta_aluno` (campo errado). Fix: regra 3 na diretiva. | Re-teste pendente |
| P3 | Validator rejeita "resposta_aluno divergente" — CORRETO neste caso | executor.py:4707-4735 | Rejeitou porque CORRIGIR escreveu MISSING_CONTENT onde deveria ter texto real |
| P4 | "Limite máximo de iterações de tools" em alguns alunos | Gemini Flash pode precisar de mais iterações OU a diretiva confusa causava loops | Re-testar após fix da diretiva |
| P5 | 404 intermitentes no task-progress durante runs pesados | task_registry in-memory + Render instável | Painel some/pisca durante run |
| P6 | Anthropic sem créditos | Bloqueio externo | Não testa Claude Haiku |
| **P7** | **ENUNCIADO + GABARITO PERDIDOS → RESTAURADOS 2026-05-27** | DB tinha 0 enunciado, 0 gabarito (perdidos no incidente 2026-05-20). PDFs físicos sobreviveram no Storage com paths sanitizados (sem acentos). Restaurados via `_restore_enunciado_gabarito.py` | **TODA pipeline antes da restauração rodava sem input real** — providers inventavam questões e gabarito. **Após restauração**: Gemini extraiu 7 questões REAIS (polinômio interpolador, sistema linear da Asdrúbal, matriz B 4x4) e gabarito HONESTO (Q5 com resposta real + Q1-Q4/Q6-Q7 marcadas MISSING_CONTENT com "documento contém apenas gabarito do Exercício 5"). |

| **D11** | **Restauração enunciado/gabarito + apagamento de 408 extrações falsas** (commit pendente) | 2026-05-27 | ✅ Verificado: extrações novas com conteúdo real do PDF, gabarito honesto detecta MISSING_CONTENT |

---

## Regras do loop

> Reler este documento no início de CADA ciclo do loop. Se eu estiver em dúvida, leio o 02_arquitetura_pipeline.md.

1. ANTES de rodar pipeline: UI funciona? Botão clicável? Modal abre? Etapas selecionáveis?
2. ANTES de rodar pipeline: paralelismo implementado? (T1 ✅)
3. ANTES de rodar pipeline: custos rastreados? (T4 ✅)
4. DURANTE pipeline: painel de progresso mostra progresso real? (D3 ✅)
5. DEPOIS de pipeline: abrir cada relatorio_final e verificar conteúdo. Registrar em 04_verificacao_docs.md.
6. DEPOIS de pipeline: custos reais em 03_custos_reais.md.
7. NUNCA declarar pronto sem verificação end-to-end no nível do usuário.
8. NUNCA estimar custos — usar tokens reais × rates.

---

## Modelos do teste

| Provider | ID no Supabase | Modelo | $/1M in | $/1M out | Status pipeline |
|---|---|---|---|---|---|
| Anthropic | `588f3efe7975` | `claude-haiku-4-5-20251001` | $1.00 | $5.00 | ⛔ Sem créditos |
| OpenAI | `gpt5nano001` | `gpt-5-nano` | $0.05 | $0.40 | ⚠️ Re-teste pendente (bug diretiva corrigido) |
| Google | `gem3flash001` | `gemini-3-flash-preview` | $0.50 | $3.00 | ⚠️ Re-teste pendente (bug diretiva corrigido) |

**Matéria**: Álgebra Linear Avançada (id `57861d16958965d2`)
**Turma**: 2026-1 (id `3f3ab03dfe783f30`)
**Atividade**: Lista0 (id `126e8b5ad7dd6d59`) — 38 alunos
**Gabarito**: PDF só tem Q5. Q1-Q4/Q6-Q7 = MISSING_CONTENT.
