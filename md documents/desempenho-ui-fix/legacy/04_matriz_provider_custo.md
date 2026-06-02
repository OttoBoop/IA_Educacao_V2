# 04 — Matriz Provider × Etapa × Custo

> **Status:** 🟡 PARCIAL — Anthropic já rodou (mas com gabarito alucinado); Gemini parado pelo bug do strict guard; GPT-5 ainda não foi disparado
> **Atualizado:** 2026-05-25 21:45 UTC
> **Fonte de dados:** `/api/documentos?atividade_id=126e8b5ad7dd6d59` (Supabase live) — auditado por [_audit_relatorios.py](./_audit_relatorios.py)

---

<!-- AUTO:matrix-start -->
> **Atualizado em:** 2026-05-27 13:18 UTC (auto-updated by `_matrix_updater.py`)
> **Total de docs no Supabase atividade Lista0:** 564

### Matriz de sucesso por etapa

| Etapa | Claude Haiku 4.5 | GPT-5 Nano | Gemini 3 Flash |
|---|---|---|---|
| EXTRAIR_QUESTOES | ✅ 91 docs | ✅ 3 docs | ✅ 12 docs |
| EXTRAIR_GABARITO | ✅ 91 docs | ✅ 3 docs | ✅ 12 docs |
| EXTRAIR_RESPOSTAS | ✅ 76 docs | ✅ 2 docs | ✅ 3 docs |
| CORRIGIR | ✅ 149 docs | ✅ 6 docs | ⏸️ 0 |
| ANALISAR_HABILIDADES | ✅ 22 docs | ⏸️ 0 | ⏸️ 0 |
| GERAR_RELATORIO | ✅ 20 docs | ⏸️ 0 | ⏸️ 0 |
| **Alunos com pipeline 6/6** | **0/38** | **0/38** | **0/38** |

Legenda: ✅ docs gerados · ⏸️ 0 docs

### Matriz de custo $ por etapa (real, baseado em tokens_entrada/tokens_saida × rates do catálogo)

| Etapa | Claude Haiku 4.5 | GPT-5 Nano | Gemini 3 Flash |
|---|---|---|---|
| EXTRAIR_QUESTOES | $1.3616 (435K in / 185K out) | $0.0136 (7K in / 33K out) | $0.0793 (19K in / 23K out) |
| EXTRAIR_GABARITO | $1.4628 (980K in / 97K out) | $0.0155 (36K in / 34K out) | $0.0609 (70K in / 9K out) |
| EXTRAIR_RESPOSTAS | $4.3625 (3180K in / 236K out) | $0.0210 (106K in / 39K out) | $0.1321 (180K in / 14K out) |
| CORRIGIR | $30.3843 (13964K in / 3284K out) | $0.0432 (319K in / 68K out) | $0.00 |
| ANALISAR_HABILIDADES | $2.8866 (1410K in / 295K out) | $0.00 | $0.00 |
| GERAR_RELATORIO | $2.1960 (1111K in / 217K out) | $0.00 | $0.00 |
| **TOTAL** | **$42.6539** (449 docs, 21.08M in / 4.31M out) | **$0.0933** (14 docs, 0.47M in / 0.17M out) | **$0.2723** (27 docs, 0.27M in / 0.05M out) |

<!-- AUTO:matrix-end -->

---

## Matriz de sucesso por etapa (real, 2026-05-25 21:45 UTC)

| Etapa | Claude Haiku 4.5 | GPT-5 Nano | Gemini 3 Flash |
|---|---|---|---|
| EXTRAIR_QUESTOES | ⚠️ 91 docs (retries × ~22 alunos), JSON OK, parseado | ⏸️ não rodado | ⚠️ 12 docs OK |
| EXTRAIR_GABARITO | ⚠️ 91 docs — **alucinou Q1-Q4/Q6-Q7 em retries** | ⏸️ não rodado | ✅ 12 docs (honesto: marca MISSING_CONTENT) |
| EXTRAIR_RESPOSTAS | ⚠️ 76 docs, 2-6 retries/aluno | ⏸️ não rodado | ⚠️ 3 docs (parou no CORRIGIR) |
| CORRIGIR | ⚠️ 149 docs em ~22 alunos (média 6.8 retries/aluno) — baseadas em gabarito alucinado | ⏸️ não rodado | ❌ aborta no guard `MISSING_CONTENT` |
| ANALISAR_HABILIDADES | ⚠️ 22 docs, 1 por aluno | ⏸️ não rodado | ⏸️ não chegou |
| GERAR_RELATORIO | ⚠️ 10 relatorio_final.json + 10 .pdf — todos com gabarito alucinado | ⏸️ não rodado | ⏸️ não chegou |
| desempenho-tarefa | ⏸️ não disparado pela pipeline-desempenho-turma (cascade só faz relatorio_final por aluno) | ⏸️ | ⏸️ |

Legenda: ✅ funcionando · ⚠️ funcionando mas com problema · ❌ falha · ⏸️ não rodado

---

## Matriz de custo $ por etapa (estimado por tokens reais nos docs × rates do catálogo)

| Etapa | Claude Haiku 4.5<br>($1.00/$5.00 por 1M) | GPT-5 Nano<br>($0.05/$0.40 por 1M) | Gemini 3 Flash<br>($0.50/$3.00 por 1M) |
|---|---|---|---|
| EXTRAIR_QUESTOES | $1.36 (435K in / 185K out / 91 docs) | $0 | $0.08 (19K in / 23K out / 12 docs) |
| EXTRAIR_GABARITO | $1.46 (980K in / 96K out / 91 docs) | $0 | $0.06 (70K in / 9K out / 12 docs) |
| EXTRAIR_RESPOSTAS | $4.36 (3.18M in / 236K out / 76 docs) | $0 | $0.13 (180K in / 14K out / 3 docs) |
| CORRIGIR | $30.38 (13.96M in / 3.28M out / 149 docs) | $0 | $0 |
| ANALISAR_HABILIDADES | $2.89 (1.41M in / 295K out / 22 docs) | $0 | $0 |
| GERAR_RELATORIO | $2.20 (1.11M in / 217K out / 20 docs) | $0 | $0 |
| desempenho-tarefa | $0 | $0 | $0 |
| **TOTAL** | **$42.65** | **$0** | **$0.27** |
| **Custo/aluno (10 com pipeline full Anthropic)** | **$4.27/aluno** | n/a | n/a |
| **Custo/etapa-call médio** | **$0.095/call** (449 calls) | n/a | **$0.01/call** (27 calls) |

> OpenAI tinha 8 docs `extracao_respostas` de run histórico 2026-05-24 (modelo `gpt-5.4-mini`), custo $0.27 — fora do escopo deste loop.

---

## Por aluno — sample de 10 relatórios Anthropic (audit completa)

| Aluno | Nota final atribuída | Q com gabarito alucinado | Retries CORRIGIR | Retries EXTRACAO_RESPOSTAS |
|---|---|---|---|---|
| Ana Beatriz Botacim Rodrigues | 5.29 | 1,2,3,4,6,7 (6/7) | 4 | 6 |
| Gabriel Schuenker Rosa de Oliveira | 2.90 | 1,2,3,4,6,7 (6/7) | 2 | 2 |
| Eric Manoel Ribeiro de Sousa | 3.65 | 1,2,3,4,6,7 (6/7) | 6 | 4 |
| GUSTAVO DE OLIVEIRA DA SILVA | 4.45 | 1,2,3,4,6,7 (6/7) | 8 | 4 |
| ALVARO JOEL TICONA MOTTA | 6.35 | 1,2,3,4,6,7 (6/7) | 4 | 5 |
| ANA VICTORIA MACHADO VILELA ROCHA | 0.00 | 1,2,3,4,6,7 (6/7) | 6 | 5 |
| EDILTON BRANDÃO DE SOUSA | 6.58 | 1,2,3,4,6,7 (6/7) | 4 | 5 |
| Eric Manoel Ribeiro de Sousa (v2) | 3.23 | 1,2,3,4,6,7 (6/7) | 6 | 4 |
| GUSTAVO DE OLIVEIRA DA SILVA (v2) | 4.00 | 1,2,3,4,6,7 (6/7) | 8 | 4 |
| Jordana Martinelli | 5.40 | 1,2,3,4,6,7 (6/7) | 4 | 4 |

Conclusão: **das 7 questões da Lista0, apenas a Q5 foi corrigida contra gabarito real**. As outras 6 receberam nota contra texto inventado pelo Anthropic em retries. Notas atribuídas são essencialmente notas geradas com 6/7 = 86% do conteúdo de avaliação alucinado.

---

## Wall-time real

| Run | Início | Fim | Duração | Estado |
|---|---|---|---|---|
| Anthropic Claude Haiku (`task_eef18debdfe8`, cancelado) | 2026-05-25T00:12:31 UTC | 2026-05-25T03:11:47 UTC | ~3h | 10/22 alunos completaram antes do cancel; crédito esgotado |
| Gemini 3 Flash run 1 (histórico) | 2026-05-23T18:29:18 | 2026-05-23T18:29:33 | 15s | abortou em extracao (run de smoke?) |
| Gemini 3 Flash `task_0f8772372008` | 2026-05-25T21:03:35 UTC | 2026-05-25T21:12:06 UTC | ~9 min | parou em CORRIGIR no guard; registry sumiu em restart |
| GPT-5 Nano | ⏸️ | ⏸️ | ⏸️ | ainda não disparado |

---

## Próximos passos (deste plano)

1. Fix do guard strict em [executor.py:2190-2198](../../backend/executor.py#L2190) — permitir CORRIGIR com gabarito parcial, marcando questões sem gabarito como "não corrigíveis"
2. Disparar GPT-5 Nano via UI (estimado ~$0.50 com fix)
3. Re-disparar Gemini 3 Flash via UI (estimado ~$0.75 com fix)
4. Esta matriz vai ser atualizada incrementalmente a cada doc gerado (script polling no Supabase a cada 60s)

---

## Conclusão (provisória, após Fase 1)

- **Provider mais barato (custo real)**: Gemini 3 Flash ($0.01/call vs Anthropic $0.095/call), mas custo só é justo quando comparado em pipeline completa — ainda não temos isso pro Gemini
- **Provider mais confiável (zero alucinação)**: Gemini 3 Flash bateu honestamente no guard; Anthropic alucinou pra passar. Em termos de **integridade científica**, Gemini > Anthropic
- **Provider mais rápido**: indeterminado (Anthropic levou 3h com retries; Gemini não rolou pipeline completa)
- **Recomendação preliminar pra produção**: PRIMEIRO consertar o guard strict em CORRIGIR. SEM esse fix, qualquer provider honesto vai bater no guard e o sistema vai parecer "quebrado" enquanto na verdade só está sendo verdadeiro sobre o input. O guard atual incentiva alucinação como side-effect de retries.
- **Recomendação SECUNDÁRIA**: re-uploadar o gabarito do professor com Q1-Q7 completas (se existe versão completa), ou aceitar oficialmente que Lista0 só tem Q5 com gabarito.

A conclusão final será reescrita após Fases 2 e 3.
