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
