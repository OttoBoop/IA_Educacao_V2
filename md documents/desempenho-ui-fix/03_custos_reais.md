# 03 — Custos Reais por Pedido

> **Atualizado:** 2026-05-27 14:00 UTC
> **Fonte:** `token_usage` tabela Supabase (807+ registros) + `/api/documentos` metadata
> **Total de docs gerados (excluindo uploads):** 745
> **Custo total acumulado: US$ 56.19**

---

## Custo real por provider (acumulado, todos os runs)

| Provider | Modelo | Docs | Tokens in | Tokens out | Custo USD |
|---|---|---|---|---|---|
| Anthropic | claude-haiku-4-5-20251001 | 449 | 21,081,059 | 4,314,559 | **$42.65** |
| Google | gemini-3-flash-preview | 247 | 16,248,220 | 1,637,196 | **$13.04** |
| OpenAI | gpt-5-nano | 41 | 1,278,973 | 412,573 | **$0.23** |
| OpenAI | gpt-5.4-mini | 8 | 239,740 | 19,724 | $0.27 (run histórico) |
| **TOTAL** | | **745** | | | **$56.19** |

---

## O que esse dinheiro produziu

| Provider | Relatórios finais | Qualidade | Custo por relatório |
|---|---|---|---|
| Anthropic | 10 (.json + .pdf) | ⚠️ Gabarito alucinado em 6/7 questões | $4.27/aluno |
| Gemini | **0** | ❌ 33/38 falharam no CORRIGIR | $13.04 pra 0 resultados |
| GPT-5 Nano | 1 (VAZIO) | ❌ questoes=[], nota_final=0 | $0.23 pra 1 resultado vazio |

**Custo efetivo por relatório ÚTIL**: Anthropic produziu 10, mas com gabarito alucinado. Se desconsiderarmos como inválidos: **$56.19 gasto, 0 relatórios cientificamente válidos.**

---

## Breakdown por run

### Run 1: Anthropic Claude Haiku (task_eef18debdfe8, 2026-05-25)
- 449 docs, $42.65
- 10 alunos com pipeline full (gabarito alucinado)
- Maior custo: CORRIGIR $30.38 (149 docs, 6.8 retries/aluno)

### Run 2: Gemini Flash (task_873a30ff9736, 2026-05-27 13:45)  
- 247 docs, $13.04 (dos quais ~190 novos neste run, ~$10.56 novo)
- 33/38 falharam no CORRIGIR
- 0 relatórios finais

### Runs GPT-5 Nano (múltiplos, 2026-05-27)
- 41 docs, $0.23
- 1 relatório final VAZIO

### Run histórico GPT-5.4 Mini (2026-05-24)
- 8 docs, $0.27
- Fora do escopo deste loop

---

## Custo médio por doc por provider

| Provider | Docs | Custo total | Custo/doc |
|---|---|---|---|
| Anthropic | 449 | $42.65 | $0.095 |
| Gemini Flash | 247 | $13.04 | $0.053 |
| GPT-5 Nano | 41 | $0.23 | $0.006 |

GPT-5 Nano é o mais barato por doc (18x mais barato que Anthropic, 9x mais barato que Gemini). Mas não produz resultados válidos com gabarito parcial.
