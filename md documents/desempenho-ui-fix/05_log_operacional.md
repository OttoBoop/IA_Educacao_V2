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
