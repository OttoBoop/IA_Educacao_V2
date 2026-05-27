# 04 — Verificação de Documentos Gerados

> **Atualizado:** 2026-05-27 12:40 UTC
> **Método**: abri cada `relatorio_final.json` via `/api/documentos/{id}/conteudo` e inspecionei campos. Screenshots via Playwright quando aplicável.
> **Runs em andamento**: GPT-5 Nano + Gemini 3 Flash (parciais)

---

## Resumo

| Provider | Relatórios finais | Abri e verifiquei? | Veredicto |
|---|---|---|---|
| Anthropic (Claude Haiku 4.5) | 10 JSON + 10 PDF = 20 docs | ✅ Sim, todos os 10 JSON | ⚠️ Conteúdo presente mas gabarito alucinado em 6/7 questões |
| OpenAI (GPT-5 Nano) | 1 JSON + 1 PDF = 2 docs | ✅ Sim, o JSON | ❌ VAZIO: 0 questões, nota_final=0, feedback_geral="" |
| Google (Gemini 3 Flash) | 0 docs | — | ⏸️ Run em andamento, ainda na etapa 5/6 pra ~7 alunos |

---

## Anthropic — Claude Haiku 4.5 (10 relatórios)

**Verificação feita em**: 2026-05-25 21:45 UTC (script `_audit_relatorios.py`)

Cada um dos 10 `relatorio_final.json` foi aberto e inspecionado:

| Aluno | nota_final | Q com gabarito REAL (Q5 apenas) | Q1-Q4/Q6-Q7 | feedback_geral presente? | Conteúdo legível? |
|---|---|---|---|---|---|
| Ana Beatriz Botacim Rodrigues | 5.29 | Q5 OK | Alucinado | ✅ sim (12KB) | ✅ sim |
| Gabriel Schuenker Rosa de Oliveira | 2.90 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| Eric Manoel Ribeiro de Sousa | 3.65 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| GUSTAVO DE OLIVEIRA DA SILVA | 4.45 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| ALVARO JOEL TICONA MOTTA | 6.35 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| ANA VICTORIA MACHADO VILELA ROCHA | 0.00 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| EDILTON BRANDÃO DE SOUSA | 6.58 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| Eric Manoel (v2) | 3.23 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| GUSTAVO (v2) | 4.00 | Q5 OK | Alucinado | ✅ sim | ✅ sim |
| Jordana Martinelli | 5.40 | Q5 OK | Alucinado | ✅ sim | ✅ sim |

**Veredicto Anthropic**: relatórios TÊM conteúdo (feedback extenso, notas por questão, PDF de 4 páginas). Mas **6/7 questões foram corrigidas contra gabarito inventado pelo próprio Anthropic** em retries de `extracao_gabarito`. Apenas Q5 tem gabarito real do professor. As notas (0.00 a 6.58) incluem correções de questões alucinadas.

**Visualização na UI**: Playwright abriu relatório da Jordana em `visualizarDocumento()` → modal com 12KB de texto renderizado. Screenshots em `_click_relatorio_20260525_212924/`.

---

## OpenAI — GPT-5 Nano (1 relatório até agora)

**Verificação feita em**: 2026-05-27 12:38 UTC (curl direto)

Doc ID `c72e715da4e4add3`, aluno ALVARO JOEL TICONA MOTTA:

```json
{
  "nota_final": 0,
  "feedback_geral": "",
  "questoes": [],
  "_avisos_documento": [
    {"codigo": "MISSING_CONTENT", "explicacao": "As questões 1, 2, 3, 4, 6 e 7 ficaram sem correção por falta de gabarito do professor."}
  ]
}
```

**Veredicto GPT-5 Nano**: ❌ **RELATÓRIO VAZIO**. Zero questões, nota 0, feedback vazio. O modelo obedeceu a diretiva `MISSING_CONTENT` pras Q1-Q4/Q6-Q7 mas aparentemente NÃO corrigiu a Q5 (que TEM gabarito). O aviso de documento lista corretamente as questões sem gabarito, mas a lista de `questoes` é vazia em vez de ter 7 itens (1 corrigível + 6 MISSING_CONTENT).

**Causa provável**: o GPT-5 Nano interpretou a diretiva "GABARITO PARCIAL" como "não corrija nada" em vez de "corrija o que tem gabarito e marque o resto como MISSING_CONTENT". A diretiva no prompt pode precisar ser mais explícita.

**PDF companion**: existe (`abce6ea034ea84ee`, extensao `.pdf`, 10KB) mas provavelmente reflete o mesmo JSON vazio.

---

## Google — Gemini 3 Flash (0 relatórios até agora)

**Run em andamento** (`task_10e944fdbd7d`, 2026-05-27 12:00 UTC). Snapshot às 12:36 UTC:
- 56 docs totais: 15 extracao_questoes, 15 extracao_gabarito, 6 extracao_respostas, 13 correcao, 7 analise_habilidades
- Passou pelo CORRIGIR (13 docs!) = fix D4 funcionou
- Passou pelo ANALISAR (7 docs)
- Ainda não gerou relatorio_final

Verificação de conteúdo pendente até ter relatorio_final.

---

## Problemas identificados na verificação

1. **GPT-5 Nano gera relatorio_final vazio**: diretiva "GABARITO PARCIAL" fez o modelo entender "não corrija nada" pra Q5 também. Precisa ajustar prompt pra ser explícito: "corrija NORMALMENTE as questões COM gabarito (neste caso, questão 5)".
2. **Schema validator aceitou JSON vazio**: `questoes: []` deveria ter sido rejeitado pelo check `not questoes → "sem lista de questoes"`, mas o doc foi gravado. Possível falha na propagação de erros.
3. **Anthropic gabarito alucinado**: notas existem mas são cientificamente inválidas. As correções de Q1-Q4/Q6-Q7 são baseadas em texto inventado.
4. **Nenhum relatório Gemini** ainda pra verificar.

---

## Próxima atualização

Quando runs GPT-5 Nano + Gemini completarem, ABRIR cada novo relatorio_final e adicionar à tabela acima.
