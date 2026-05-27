# 03 — Custos Reais por Pedido

> **Atualizado:** 2026-05-27 12:36 UTC
> **Fonte:** docs no Supabase (`/api/documentos?atividade_id=126e8b5ad7dd6d59`) com `metadata.tokens_entrada/tokens_saida` × rates do `backend/data/model_catalog.json`
> **Total de docs gerados (excluindo uploads):** 544
> **Runs em andamento:** GPT-5 Nano `task_8c798da9755a` + Gemini `task_10e944fdbd7d` (ambos 2026-05-27)

**NOTA**: custos são calculados como `tokens × rate do catálogo`. O ideal (P4 em 01_objetivos) seria o backend salvar custo real por pedido API. Hoje não faz isso — reconstruímos pós-hoc.

---

## Matriz de custo real por etapa

| Etapa | Claude Haiku 4.5 | GPT-5 Nano | Gemini 3 Flash |
|---|---|---|---|
| EXTRAIR_QUESTOES | $1.3616 (91 docs, 435K in / 185K out) | $0.0283 (6 docs, 16K in / 69K out) | $0.0994 (15 docs, 24K in / 29K out) |
| EXTRAIR_GABARITO | $1.4628 (91 docs, 980K in / 97K out) | $0.0256 (6 docs, 65K in / 56K out) | $0.0761 (15 docs, 87K in / 11K out) |
| EXTRAIR_RESPOSTAS | $4.3625 (76 docs, 3.18M in / 236K out) | $0.3098 (12 docs, 498K in / 90K out) | $0.2602 (6 docs, 361K in / 27K out) |
| CORRIGIR | $30.3843 (149 docs, 13.96M in / 3.28M out) | $0.0829 (11 docs, 637K in / 128K out) | $1.7237 (13 docs, 2.11M in / 223K out) |
| ANALISAR_HABILIDADES | $2.8866 (22 docs, 1.41M in / 295K out) | $0.0107 (2 docs, 90K in / 16K out) | $0.3126 (7 docs, 421K in / 34K out) |
| GERAR_RELATORIO | $2.1960 (20 docs, 1.11M in / 217K out) | $0.0096 (2 docs, 85K in / 13K out) | — (0 docs até agora) |
| **TOTAL** | **$42.6539** (449 docs) | **$0.4669** (39 docs) | **$2.4719** (56 docs) |

---

## Custo por aluno com pipeline completa (relatorio_final existente)

### Anthropic — Claude Haiku 4.5

10 alunos com relatorio_final (JSON + PDF). **Caveat**: gabarito alucinado em Q1-Q4/Q6-Q7 (ver 04_verificacao_docs.md).

| Aluno (primeiros 10 chars) | Custo relatorio_final | Timestamp |
|---|---|---|
| 244423c43d (Ana Beatriz) | $0.2956 (json+pdf) | 2026-05-25 00:27–00:28 |
| 382e5ec2d4 (Gabriel) | $0.1946 | 00:41 |
| 660e9421b2 (Eric v1) | $0.1958 | 00:46 |
| 7eb7b15146 (Gustavo v1) | $0.2366 | 01:00 |
| 40ab839a53 (Alvaro) | $0.1796 | 01:26 |
| f625e78840 (Ana Victoria) | $0.1630 | 01:44 |
| 5e178a4a9b (Edilton) | $0.2610 | 01:58 |
| 660e9421b2 (Eric v2) | $0.2414 | 02:12 |
| 7eb7b15146 (Gustavo v2) | $0.2296 | 02:26 |
| 457b04cfe1 (Jordana) | $0.1986 | 02:49 |

Custo médio do relatorio_final: ~$0.22/aluno (só a etapa final).
Custo total pipeline Anthropic: $42.65 / 10 alunos com pipeline full = **$4.27/aluno** (com retries massivos em CORRIGIR).

### OpenAI — GPT-5 Nano

2 alunos com relatorio_final até agora (run em andamento):

| Aluno | Custo relatorio_final | Timestamp |
|---|---|---|
| 40ab839a53 (Alvaro) | $0.0096 (json+pdf) | 2026-05-27 18:09 |

Custo total pipeline GPT-5 Nano até agora: $0.47 / 39 docs. **Run em andamento.**

### Google — Gemini 3 Flash

0 alunos com relatorio_final até agora (run em andamento, 7 analise_habilidades geradas = está na etapa 5/6 pra ~7 alunos).

Custo total pipeline Gemini até agora: $2.47 / 56 docs. **Run em andamento.**

---

## Relação custo/doc médio por provider

| Provider | Docs | Custo total | Custo médio/doc |
|---|---|---|---|
| Anthropic | 449 | $42.65 | $0.095/doc |
| GPT-5 Nano | 39 | $0.47 | $0.012/doc |
| Gemini 3 Flash | 56 | $2.47 | $0.044/doc |

**Anthropic é 7.9× mais caro que GPT-5 Nano e 2.2× mais caro que Gemini por doc.** Mas grande parte do custo Anthropic vem de retries massivos (149 docs CORRIGIR pra ~22 alunos = média 6.8 docs/aluno numa única etapa, vs ideal de 1-2).
