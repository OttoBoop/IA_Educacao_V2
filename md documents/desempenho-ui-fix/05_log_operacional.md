# 05 — Log Operacional

Timeline de ações reais deste loop. Sem interpretação. Cada entry = ação → resultado.

---

| Timestamp (UTC) | Ação | Resultado |
|---|---|---|
| 2026-05-24 17:59 | Commit `2c0d88e`: fix botão Gerar Relatório + master select-all | Push OK. Deploy `dep-d89p1ougvqtc73c78lbg`. |
| 2026-05-24 18:03 | Playwright verify: botão clicável, 228/228 etapas controladas | PASS. Screenshots em `_verify_screenshots_20260524_180305/`. |
| 2026-05-24 18:14 | Dispatch Claude Haiku `task_eef18debdfe8` via UI (Playwright) | task_id capturado. Pipeline iniciou. |
| 2026-05-25 00:12–03:11 | task_eef18debdfe8 rodou ~3h | 449 docs gerados (Anthropic). 10 alunos com pipeline full. Custo ~$42.65. |
| 2026-05-25 ~03:11 | Crédito Anthropic esgotou | Novos runs Anthropic falham com HTTP 400 "credit balance too low". |
| 2026-05-25 ~10:55 | Cancel task_eef18debdfe8 (eu, achando que era pré-fix) | Task cancelada. 20 relatorio_final já existiam no DB. |
| 2026-05-25 18:03 | Commit `4f446f8`: progresso visível na UI (painel live per-student) | Push OK. |
| 2026-05-25 18:09 | Commit `65c01b5`: fix students dict vazio + pre-populate nomes | Push OK. Deploy live ~18:09. |
| 2026-05-25 21:03 | Dispatch Gemini `task_0f8772372008` via UI | Abortou em CORRIGIR: "Gabarito extraido incompleto". Guard strict. |
| 2026-05-25 21:12 | task_0f8772372008 sumiu do registry | Render restart? Registry in-memory. 27 docs Gemini no DB. |
| 2026-05-25 21:14 | Dispatch Claude Haiku `task_e210dac64d69` | Falhou em 6s: crédito esgotado. |
| 2026-05-25 21:15 | Dispatch Gemini `task_286e8b9beb7e` | Falhou em 2min: guard strict (mesmo bug). |
| 2026-05-25 21:45 | Auditoria dos 10 relatorio_final Anthropic | 10/10 baseados em gabarito alucinado em Q1-Q4/Q6-Q7. |
| 2026-05-25 21:50 | Commit `4c68e15`: fix guard gabarito parcial + diretiva CORRIGIR | Push OK. Deploy. |
| 2026-05-27 01:14 | Dispatch GPT-5 Nano `task_6f9800ea487d` via UI | Falhou em ~7min: schema strict rejeitou nota=null em questões MISSING_CONTENT. |
| 2026-05-27 01:30 | Commit `181d2df`: fix schema uncorrectable + batch tolerance | Push OK. Deploy. |
| 2026-05-27 12:00 | Dispatch GPT-5 Nano `task_8c798da9755a` + Gemini `task_10e944fdbd7d` | Ambos rodando. 1/38 alunos cada (sequencial). |
| 2026-05-27 ~12:30 | Snapshot: GPT-5 39 docs (2 relatorio_final!), Gemini 56 docs (7 analise_habilidades) | Pipelines avançando. Fixes D4+D5+D6 funcionaram. |
| 2026-05-27 12:35 | Movidos 01-04.md pra `legacy/`. Início da escrita dos docs frescos. | — |
| 2026-05-27 12:36 | Cancelados runs GPT-5 `task_8c798da9755a` + Gemini `task_10e944fdbd7d` (contaminados) | Ambos cancelados OK |
| 2026-05-27 ~13:00 | Commit `7fc6833`: T1 (paralelismo 12 workers) + T2 (isolate provider) + T3 (diretiva CORRIGIR reescrita) + docs frescos 01-05 | Push + deploy `dep-d8bkfeernols7394tjn0` |
| 2026-05-27 13:40 | Deploy `7fc6833` live. UI verificada: checkbox isolar ✅, seção Docs Disponíveis ✅ | Playwright screenshot |
| 2026-05-27 13:45 | Confirmado: custos reais já existem em `token_usage` (807 records Supabase) + `/api/custos/resumo` funciona | Sem caching API → custo = tokens × rate = custo real |
| 2026-05-27 13:45 | Teste 2 alunos via UI Playwright: Gemini Flash, force_reexec, isolate_provider | task_873a30ff9736. Bug: selecionei 2, rodou 38 (`etapas_selecionadas` ignorado) |
| 2026-05-27 13:46 | **T1 confirmado**: `active=12` (12 alunos simultâneos no poll) | Paralelismo funciona |
| 2026-05-27 13:49 | Falhas: 33/38 alunos falharam no CORRIGIR com Gemini Flash | "limite iterações tools" + "resposta_aluno divergente" |
| 2026-05-27 13:55 | Atualizado 01_objetivos com status real de T1-T7, bugs P1-P6, decisões D8-D10 | — |
| 2026-05-27 16:30 | D11: restauração enunciado/gabarito perdidos no incidente 2026-05-20 via `_restore_enunciado_gabarito.py` | DB volta a ter 1 enunciado + 1 gabarito; PDFs físicos sobreviveram no Storage (paths sanitizados). Toda pipeline antes disso rodou sem input real. |
| 2026-06-01 17:12 | Commit `66ae800`: D12 — rejeita stubs vazios em `handle_create_document` | Deploy live 20:12 UTC. 0 stubs de 85 bytes hoje (histórico: 58 em 27/05). Pipeline agora trava antes da CORRIGIR completar. |
| 2026-06-01 18:00 | Diagnóstico das 38 FALHAS DEFINITIVAS pós-D12: reportlab quebrado (18), sandbox (17), schema/string_too_short (24), PDF/JSON nota_final divergente (5) | T8 desenhado em 01_objetivos com 3 opções. |
| 2026-06-02 16:25 | Implementado server-side PDF render (T8 opção 1): `generate_pipeline_pdf` + auto-hook em `handle_create_document` + STAGE_TOOLS sem execute_python_code para CORRIGIR/ANALISAR/RELATORIO | Commit `82c2cbf`. Deploy live 19:31 UTC. |
| 2026-06-02 16:30 | Regras 9-13 do loop adicionadas em 01_objetivos: não pedir permissão mid-loop, "Agora vou X" + execução, condições de término, formato de output, AskUserQuestion em plan mode | Otávio reagiu ao "Posso prosseguir com o commit/push?" que quebrou o ciclo anterior. |
| 2026-06-02 17:26 | Pré-cleanup: 44 docs aluno-level antigos do Alvaro apagados (correcao/analise/relatorio/extracao_respostas) | DELETE direto no Supabase (estava na regra do loop como ação operacional autorizada). |
| 2026-06-02 17:26 | Dispatch via `_dispatch_alvaro.py` (mode aluno único) → task_971fe37f07c9 | gem3flash001, force_rerun=true. 3 versões do script (v1 falhou em `wait_for_function`, v2 falhou porque `hasStudentsInTurma()` rodava antes de `ensureAtividadeData`, v3 pre-carrega `_atividadeData` e passou). |
| 2026-06-02 17:31 | task_971fe37f07c9 = **completed** | 6/6 etapas OK em 5min43s. 7 docs criados. Custo $0.0736. CORRECAO.json nota_final=2.86 com Q4+Q5 corrigidas e Q1-3/Q6-7 honestamente MISSING_CONTENT. 3 PDFs server-side passaram validator checks. |
| 2026-06-02 17:34 | 01/03/04/05 atualizados: T8 ✅ FEITO + D13 + custo real + verificação Alvaro + timeline | — |
| 2026-06-02 17:38 | Dispatcher turma 38 alunos Gemini Flash `task_da1c78d83aa2` com force_reexec=true | P8 descoberto: race no Supabase Storage para enunciado.pdf (38 workers paralelos). 12 alunos com correcao+PDF, 4 com pipeline completa, depois 38 FALHA DEFINITIVA "Arquivo não encontrado para extrair_questoes". |
| 2026-06-02 17:56 | Re-dispatch turma sem force_reexec `task_310176c9452b` | Falhou em <1min com 38 students_failed + 0 stages_completed. P9 descoberto: cascade desempenho-turma com bug no partial state. |
| 2026-06-02 18:58 | Batch dispatch 33 alunos via `_dispatch_batch.py` (pipeline-completo direto) | 9 completed + 24 failed. 1 aluno novo com pipeline completa (45b01c, f494). |
| 2026-06-02 19:06 | Diagnóstico: 16 alunos com tem_relatorio=True na API, mas só 8 são pós-D13 (Gemini). 8 são pré-D11 (Anthropic alucinado). | 04 atualizado com auditoria forense. |
| 2026-06-02 19:06 | Single dispatch GPT-5 Nano + Anthropic Haiku para Alvaro pós-D13 | Ambos falharam em CORRIGIR com schema/math issues (sem `_avisos_*` lista, nota_final≠soma, MISSING_CONTENT sem feedback). |
| 2026-06-02 19:15 | Fix pre-save schema enforcement (commit `be5496d`) + deploy | Anthropic falhou EXTRAIR_RESPOSTAS (julgamento em raciocinio_parcial). GPT-5 Nano falhou CORRIGIR ainda (bug for-else). |
| 2026-06-02 19:32 | Fix bug for-else (commit `fb9c74d`) + deploy | GPT-5 Nano progrediu para CORRIGIR completed; Anthropic EXTRAIR_RESPOSTAS ainda falhou. |
| 2026-06-02 19:45 | Investigação raciocinio_parcial Anthropic — descoberto que PRÓPRIO PROMPT contém palavras-gatilho ("errada") em exemplos | D15 |
| 2026-06-02 19:48 | Fix prompt + validator EXTRAIR_RESPOSTAS (commit `3001e2f`) + deploy | Anthropic Haiku passa EXTRAIR_RESPOSTAS, falha em CORRIGIR (resposta_correta divergente). |
| 2026-06-02 20:03 | Fix trace-check CORRIGIR vs gabarito (commit `e7deb21`) + deploy | GPT-5 Nano: extracao_questoes/gabarito/respostas + CORRIGIR ✅ todos completed. Falha em ANALISE (JSON sintaxe). Anthropic falha EXTRACAO_GABARITO "Falha após 3 tentativas" (API). |
| 2026-06-02 20:15 | Obj 5 comparativo finalizado em 04: Gemini end-to-end OK, GPT-5 Nano até CORRIGIR, Anthropic instável. | — |
| 2026-06-05 ~08:45 | **Loop 2 (Otávio aprovou plan combo obj 4 + UI accuracy + cleanup pré-D11)** | — |
| 2026-06-05 08:46 | `_cleanup_pre_d11.py`: 262 docs gerados pré-D11 apagados (253 Anthropic + 7 OpenAI + 2 Google), Storage preservado | DB limpo de docs alucinados, todos os atividade-level extracao_questoes/gabarito remanescentes são post-D11 |
| 2026-06-05 ~08:50 | Backend: `storage.get_status_atividade` expõe `correcao_provider`/`correcao_criado_em`/`relatorio_provider`/`relatorio_criado_em` por aluno | — |
| 2026-06-05 ~08:51 | Backend: `routes_extras._check_has_atividades` conta CORRECAO per-aluno (não só RELATORIO_FINAL atividade-level) | Mensagem "Nenhuma atividade corrigida" deixa de mentir para alunos com correcao mas sem relatorio |
| 2026-06-05 ~08:52 | Frontend: helper `renderPipelineStatusBadge` retorna 3 estados (✓ verde post-D11, ⚠️ Antigo pre-D11, Pendente missing). Aplicado às colunas Correção+Relatório. | — |
| 2026-06-05 08:53 | Commit `545a4a4` + push + deploy live (build 1.5min + update 1.5min) | — |
| 2026-06-05 08:55 | Batch direto 30 alunos → 1 OK, rate limits crescentes | Apaga 143 erro docs para tentar limpar slate |
| 2026-06-05 09:00 | Staggered 30 alunos delay=30s `--force-rerun` → 0/30 (Google 429 burst em extrair_questoes — force_rerun forçou re-extração 30×) | Aprendizado: NÃO usar `--force-rerun` em batch — só usa em isolado |
| 2026-06-05 09:13 | Staggered v2 SEM force-rerun → 1 completed, 18 failed (429), 11 lost (task_registry) | Quota estava sendo consumida ainda |
| 2026-06-05 09:25 | `_dispatch_sequential.py`: 1 aluno por vez, 12min timeout, 15s cooldown → 0 completed, 11 failed CORRIGIR, 19 lost (cascade falha em <15s) | Quota esgotada — cascade rejeitada na primeira chamada |
| 2026-06-05 09:30 | Teste Alvaro com `gem25flash001` (Gemini 2.5 Flash GA) → 429 também | Confirmado: quota é Google-wide, não por modelo |
| 2026-06-05 09:32 | P11 documentado em 01: BLOQUEIO EXTERNO Google rate limit. Aguardar reset (próximo 00:00 UTC). | Loop 2 fecha com 8/38 alunos válidos + cleanup + UI accuracy entregues, dispatch turma adiado por bloqueio externo |
