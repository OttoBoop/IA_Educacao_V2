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

| # | O quê | Commit | Funciona? |
|---|---|---|---|
| D1 | Fix botão Gerar Relatório | `2c0d88e` | ✅ Verificado: Playwright 228/228 |
| D2 | Master select-all no modal | `2c0d88e` | ✅ Verificado |
| D3 | Painel de progresso live per-student per-stage | `4f446f8` + `65c01b5` | ✅ Verificado: painel renderiza em 5s |
| D4 | Guard gabarito: correção parcial permitida | `4c68e15` | ⚠️ Funciona mas GPT-5 Nano gera relatório VAZIO (interpretou como "não corrija nada") |
| D5 | Schema validator aceita MISSING_CONTENT | `181d2df` | ⚠️ Funciona parcialmente (aceita mas modelo não segue diretiva) |
| D6 | Batch tolerance (1 aluno falha não mata 38) | `181d2df` | ✅ Funciona |
| D7 | Pre-popular students com nomes no task_registry | `65c01b5` | ✅ Funciona |

---

## Tarefas pendentes (em ordem de prioridade pra um loop)

### T1. Paralelismo de alunos no cascade
**O quê**: Trocar `for aluno in alunos: await executar_pipeline_completo(...)` por `asyncio.gather` com semáforo (N=4).
**Onde**: [executor.py:6462-6480](../../backend/executor.py#L6462) (branch `level == "tarefa"`)
**Por quê**: 38 alunos sequenciais = 2-3h. Com 4 workers → ~30-50min.
**Cuidados**: `update_stage_progress` é thread-safe (dict in-memory). `gerar_relatorio_desempenho_tarefa()` roda DEPOIS do gather.
**Verificação**: UI mostra 4 alunos "em andamento" simultaneamente.

### T2. Seleção de docs por provider na UI e backend
**O quê**: Nas opções avançadas do modal de desempenho, mostrar quais docs existem por etapa (provider, data, versão) e permitir ao professor escolher qual usar como input.
**Onde**: Frontend: modal `modal-desempenho-settings` + `prefetchDesempenhoEtapasState()`. Backend: `_documento_json_da_ultima_execucao()` ([executor.py:1734](../../backend/executor.py#L1734)) precisa aceitar `doc_id` override além do default "mais recente".
**Por quê**: Hoje o professor não tem controle. Com force_reexec=true, o provider alimenta a si mesmo (OK). Mas quando há docs de múltiplos providers, o mais recente é pego sem perguntar.
**Comportamento desejado**: 
  - Default: mais recente (como hoje)
  - Opção avançada: lista de docs por etapa, selecionar qual
  - Neste teste: mesma IA em toda pipeline (→ force_reexec=true em todas)

### T3. Diretiva CORRIGIR com gabarito parcial mais explícita
**O quê**: A diretiva "GABARITO PARCIAL" no system prompt ([executor.py:2118-2133](../../backend/executor.py#L2118)) precisa dizer EXPLICITAMENTE: "corrija NORMALMENTE as questões que TÊM gabarito (neste caso, Q5). Para as questões SEM gabarito (Q1-Q4/Q6-Q7), inclua-as na lista com resposta_correta='MISSING_CONTENT', nota=null, acerto=null."
**Por quê**: GPT-5 Nano interpretou como "não corrija nada" e retornou `questoes: []`.
**Verificação**: após fix, GPT-5 Nano gera relatorio_final com 7 questões (1 com nota, 6 MISSING_CONTENT).

### T4. Custos reais por pedido API
**O quê**: Backend salvar custo no momento da chamada (não recalcular pós-hoc). Tabela Supabase `token_usage` (pode já existir parcial — checar `/api/custos/status`). Endpoint `/api/custos/resumo` deve agregar por provider, etapa, aluno.
**Onde**: `executor.py` onde chama providers (após cada API call), tabela Supabase.
**Por quê**: hoje custos são reconstruídos lendo `metadata.tokens_*` de 544 docs — frágil e pós-hoc.

### T5. Verificação automática de conteúdo pós-run
**O quê**: Script que após cada pipeline run, abre cada `relatorio_final.json` e checa:
  - `nota_final` numérica e razoável
  - `questoes[]` não vazia, cada questão tem feedback
  - Questões com gabarito real têm `nota` numérica
  - Questões MISSING_CONTENT têm `nota=null`
  - `feedback_geral` tem >200 chars
**Por quê**: sem isso, relatórios vazios ou com gabarito alucinado passam despercebidos.

### T6. task_registry persistente
**O quê**: Salvar `task_registry` em Supabase pra sobreviver a restarts.
**Onde**: `routes_tasks.py`, tabela nova `pipeline_tasks`.
**Por quê**: restart do Render apaga o registry in-memory. Painel de progresso some mid-run.

### T7. Rodar pipelines de verdade (3 providers) com verificação
**O quê**: Após T1-T5, disparar GPT-5 Nano + Gemini + (Anthropic se crédito restaurado) com:
  - force_reexec=true pra todas as etapas (cada provider usa seus próprios docs)
  - Paralelismo entre alunos (T1)
  - Verificação de conteúdo pós-run (T5)
  - Custos reais capturados (T4)
  - Atualizar 03_custos_reais.md e 04_verificacao_docs.md após cada run
**Por quê**: runs anteriores foram comprometidas (gabarito alucinado, contexto contaminado, relatório vazio).

---

## Regras do loop

> Reler este documento no início de CADA ciclo do loop. Se eu estiver em dúvida, leio o 02_arquitetura_pipeline.md.

1. ANTES de rodar pipeline: UI funciona? Botão clicável? Modal abre? Etapas selecionáveis?
2. ANTES de rodar pipeline: paralelismo implementado? (T1)
3. DURANTE pipeline: painel de progresso mostra progresso real? (D3)
4. DEPOIS de pipeline: abrir cada relatorio_final e verificar conteúdo (T5). Registrar em 04_verificacao_docs.md.
5. DEPOIS de pipeline: custos reais registrados em 03_custos_reais.md.
6. NUNCA declarar pronto sem verificação end-to-end no nível do usuário.
7. NUNCA estimar custos — usar tokens reais × rates.

---

## Modelos do teste

| Provider | ID no Supabase | Modelo | $/1M in | $/1M out |
|---|---|---|---|---|
| Anthropic | `588f3efe7975` | `claude-haiku-4-5-20251001` | $1.00 | $5.00 |
| OpenAI | `gpt5nano001` | `gpt-5-nano` | $0.05 | $0.40 |
| Google | `gem3flash001` | `gemini-3-flash-preview` | $0.50 | $3.00 |

**Matéria**: Álgebra Linear Avançada (id `57861d16958965d2`)
**Turma**: 2026-1 (id `3f3ab03dfe783f30`)
**Atividade**: Lista0 (id `126e8b5ad7dd6d59`) — 38 alunos
**Gabarito**: PDF só tem Q5. Q1-Q4/Q6-Q7 = MISSING_CONTENT.
