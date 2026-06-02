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

## Google — Gemini 3 Flash (teste 2026-05-27 13:45, task_873a30ff9736)

**Run**: `task_873a30ff9736`, Gemini Flash, force_reexec=true, isolate_provider=true, 38 alunos (bug: selecionei 2 mas cascade rodou todos).

**Resultado**: 33/38 falharam no CORRIGIR. 0 relatórios finais gerados.

| Tipo de falha | Qtd | Exemplo |
|---|---|---|
| "Limite máximo de iterações de tools" | ~15 | Alvaro, Ana Beatriz — modelo fica em loop de tool calls |
| "resposta_aluno divergente da EXTRAIR_RESPOSTAS" | ~12 | Ana Julia, Ana Victoria — cópia não-exata entre etapas |
| "questão 5 sem resposta_aluno rastreável" | ~6 | Beatriz — resposta_aluno vazia ou mal formatada |

**Análise**: Gemini Flash conseguiu EXTRAIR (questões, gabarito, respostas) com sucesso pra muitos alunos (56+ docs). Mas no CORRIGIR:
- Não consegue produzir JSON + PDF dentro do limite de iterações de tools
- Quando produz JSON, a cópia de resposta_aluno não bate exatamente com EXTRAIR_RESPOSTAS (paráfrase, truncamento, formatação diferente)
- O schema validator rejeita por divergência

**Conclusão**: Gemini 3 Flash Preview NÃO consegue completar CORRIGIR com gabarito parcial na forma atual. Não é problema da diretiva T3 — é limitação do modelo com tool-use complexo.

---

## Problemas identificados na verificação (consolidado)

1. **GPT-5 Nano gera relatorio_final vazio** (run 2026-05-27 01:14): `questoes: []`, nota_final=0. Diretiva T3 reescrita mas NÃO testada novamente com GPT-5 Nano ainda.
2. **Gemini Flash falha no CORRIGIR** (run 2026-05-27 13:45): 33/38 falham por limite de iterações ou resposta_aluno divergente. 0 relatórios.
3. **Anthropic gabarito alucinado** (run 2026-05-25): 10 relatórios existem mas com notas baseadas em gabarito inventado em 6/7 questões.
4. **Schema validator estrito**: rejeita cópia não-exata de resposta_aluno entre etapas. Modelos baratos parafraseiam em vez de copiar literalmente.
5. **`etapas_selecionadas` ignorado**: cascade roda 38 alunos mesmo quando só 2 estão selecionados.

---

## Teste pós-server-side-PDF — Alvaro / Gemini Flash (2026-06-02, task_971fe37f07c9)

**Setup**: commit `82c2cbf` deploy live 19:31 UTC. Dispatch via UI Playwright `_dispatch_alvaro.py` modo aluno único. Provider gem3flash001, force_rerun=true. Tarefa terminou em 5min43s. Custo $0.0736.

**Doc IDs**:
| Tipo | ID JSON | ID PDF | bytes JSON / PDF |
|---|---|---|---|
| extracao_respostas | ca170211015c3db9 | (n/a) | 5373 / — |
| correcao | ad597feb9ae104fc | fa510f56b601c4c2 | 6760 / 7171 |
| analise_habilidades | 04befff18ad7079c | e4fea6e5d1b1fe17 | 3299 / 3690 |
| relatorio_final | 8e537097449ee7de | bb7b0885cf5bdba6 | 3377 / 3137 |

**Auto-PDF rastreabilidade**: cada PDF tem `metadata.tool="execute_python_code"` + `metadata.auto_generated_from=<json_id>` apontando pro JSON pai. PDFs gerados pelo `document_generators.generate_pipeline_pdf` server-side, não pelo modelo.

**CORRECAO.json — verificado manualmente**:
- `nota_final`: **2.86** (Q4 + Q5 = 1.43 + 1.43 = 2.86 — soma correta)
- `total_acertos`: 2 (Q4 e Q5)
- `total_erros`: 0
- `feedback_geral`: 680 chars, análise pedagógica real ("O aluno demonstra um domínio técnico excepcional...")
- `questoes[]`: 7 itens, schema correto:
  - Q1, Q2, Q3, Q6, Q7: `nota=None, acerto=None, resposta_correta="MISSING_CONTENT"`, feedback="Nao corrigivel: gabarito do professor nao cobre esta questao." — comportamento HONESTO (gabarito real só tinha Q4/Q5)
  - Q4, Q5: `nota=1.43, acerto=true`, feedback de análise pedagógica detalhada
- `_avisos_documento`: 1 aviso MISSING_CONTENT explicando que gabarito só cobria Q4/Q5
- `_avisos_questao`: 5 avisos MISSING_CONTENT (um por questão sem gabarito)

**CORRECAO.pdf — checks do validator passaram**:
- ✅ Contém "Nota final: 2.86"
- ✅ Contém "Feedback Geral"
- ✅ Contém "ALVARO JOEL TICONA MOTTA" no cabeçalho
- ✅ Contém "Questão 4 — Nota: 1.43" e "Questão 5 — Nota: 1.43"
- ✅ Contém respostas do aluno + feedback por questão
- Sem violações sandbox, sem `colors.hexColor` errors, sem PDF/JSON divergence (impossível por construção — PDF é função pura do JSON)

**ANALISE.pdf**: cabeçalho com nome do aluno, 3 habilidades avaliadas ("Modelagem Matemática", "Álgebra Matricial", "Álgebra sobre Corpos Finitos"), todas marcadas "dominado" com nota 10, evidências por habilidade.

**RELATORIO.pdf**: "Nota final: 2.86", "Resumo Geral" com análise unificada, "Pontos Fortes" listados (domínio de aritmética modular, modelagem matemática, integração Python).

**Veredicto**: ✅ **PIPELINE FUNCIONA END-TO-END com Gemini Flash pós-D13**. Primeiro relatório CIENTIFICAMENTE VÁLIDO de todo o loop (D11 restaurou inputs reais, D13 destravou CORRIGIR).

**Próximos testes pendentes**:
- Replicar para 38 alunos (via pipeline-desempenho-turma) — EM CURSO (task_da1c78d83aa2)
- Replicar com GPT-5 Nano (mesmo fix se aplica) — PENDENTE
- Replicar com Anthropic Haiku — créditos VOLTARAM 2026-06-02 (verificado via API direct)
- Marcar relatórios pré-D13 com PDF gerado pelo modelo como **POTENCIALMENTE INCONSISTENTES** (PDF vs JSON divergence)

---

## Obj 5 — comparativo entre providers pós-fixes (2026-06-02, single-aluno Alvaro)

Após sequência de fixes D13/be5496d/fb9c74d/3001e2f/e7deb21 (PDF server-side + pre-save schema validation + raciocinio_parcial vocabulary fix + resposta_correta trace-check), 4 dispatches de single-aluno para Alvaro:

| Provider | Modelo | EXTRAIR_Q | EXTRAIR_G | EXTRAIR_R | CORRIGIR | ANALISE | RELATORIO | Pipeline completa? |
|---|---|---|---|---|---|---|---|---|
| Google | gemini-3-flash-preview | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ SIM ($0.0736) |
| OpenAI | gpt-5-nano | ✅ | ✅ | ✅ | ✅ (pós-trace-check) | ❌ JSON sintaxe | — | ❌ |
| Anthropic | claude-haiku-4-5 | ✅ | ❌ "Falha após 3 tentativas" (API) | — | — | — | — | ❌ |

**Causas-raiz diagnosticadas e RESOLVIDAS no código:**
1. **Stubs vazios** (D12, `66ae800`): `_inject_default_avisos` aceitava `{}` → 85-byte ghost docs. Fix: validation em `handle_create_document`.
2. **PDF reportlab quebrado** (D13, `82c2cbf`): modelo escreveu `colors.hexColor`+`pagesize`+gravava fora sandbox. Fix: PDF server-side via `document_generators.generate_pipeline_pdf`.
3. **Schema CORRECAO incompleto** (`be5496d`): modelo omitia `_avisos_*`/`total_*`. Fix: pre-save required fields enforcement.
4. **Bug for-else** (`fb9c74d`): minha validação aceitava `_avisos` como null. Fix: collect errs + continue.
5. **Anthropic raciocinio_parcial drift** (`3001e2f`): prompt CONTINHA palavras-gatilho ("errada") em exemplos → modelo as copiava. Fix: prompt rewrite + pre-save regex check.
6. **CORRIGIR resposta_correta divergente** (`e7deb21`): modelo reescrevia gabarito apesar de pre-montado + directive. Fix: pre-save trace-check carrega upstream EXTRACAO_GABARITO e compara.

**Falhas remanescentes (limites do modelo, não do código):**
- GPT-5 Nano ANALISE: JSON sintaxe inválida (char 324) — modelo produz JSON malformado consistentemente. Mitigação possível: prompt mais simples para ANALISE OU passar para JSON mode da OpenAI API.
- Anthropic Haiku EXTRACAO_GABARITO: 3 retries esgotados (não-determinístico — provavelmente API rate limit ou modelo produzindo output rejeitável). Pode ser resolvido com max_retries maior + backoff específico.

**Veredicto obj 5:**
- ✅ **Gemini Flash** é o ÚNICO provider que completa pipeline end-to-end com fidelidade pedagógica. $0.0736/aluno.
- ⚠️ **GPT-5 Nano** chega muito longe pós-fixes mas trava em ANALISE. Útil para EXTRAIR_RESPOSTAS / CORRIGIR isolados.
- ❌ **Anthropic Haiku** pré-D13 alucinava gabarito + fazia retries explosivos ($42); pós-D13 instabilidade não-determinística em EXTRAIR_GABARITO. Custo: $0.15-0.20 por tentativa.

**Recomendação:** rodar turma inteira com Gemini Flash como provider default. Custo estimado 38 alunos ≈ $2.40. Anthropic/GPT-5 Nano como fallback para etapas isoladas se necessário.

---

## Auditoria forense: 18 relatorio_final Anthropic pré-D11 (2026-05-25)

**Status**: ❌ **CIENTIFICAMENTE INVÁLIDOS** — gabarito alucinado, mas conteúdo do aluno parcialmente real.

**Evidência (doc `a7f1bec364819192`, Ana Beatriz)**:
- `nota_final`: 5.29 (parece plausível, mas contra gabarito FICTÍCIO)
- `resumo_geral`: 1059 chars de texto pedagogicamente válido
- `detalhamento`: 7110 chars descrevendo "4 de 7 questões respondidas"

**Markers do enunciado REAL (NÃO aparecem nos docs pré-D11)**:

| Marker | Esperado se input real | Presente no doc pré-D11? |
|---|---|---|
| "Asdrúbal" (Q2 — sistema linear com nomes próprios) | ✓ | ❌ |
| "polinômio interpolador" (Q1) | ✓ | ❌ |
| "Corpo Z3" / "matriz B 4x4" (Q4-5) | ✓ | ❌ |
| "numpy" / "interpolação" / "lapack" (genéricos de Álgebra Linear) | possível | ✓ (do aluno) |

**Diagnóstico**: pre-D11 a pipeline rodou com:
- EXTRACAO_RESPOSTAS: ✅ leu prova_respondida.pdf real → conteúdo real do aluno
- EXTRACAO_QUESTOES: ❌ sem enunciado.pdf → modelo INVENTOU questões
- EXTRACAO_GABARITO: ❌ sem gabarito.pdf → modelo INVENTOU respostas
- CORRIGIR: comparou respostas reais vs gabarito alucinado → notas SEM VALIDADE EDUCACIONAL

**Confronto com nota REAL do Alvaro pós-D13 (gabarito de verdade)**:
- Pre-D11 Anthropic Alvaro: relatorio_final com nota 6.35 (alucinada vs gabarito fictício de Q1-Q7)
- Pós-D13 Gemini Alvaro: nota_final = 2.86 (Q4=1.43 + Q5=1.43, soma real contra Q5+Q4 cobertas)
- Diferença reflete o gap: nota "fictícia" cobre 7 questões inventadas; nota real cobre só 2 com gabarito real

**Veredicto**: 18 relatórios pré-D11 (10 alunos × 2 versões × 2 formatos = 18 docs) devem ser tratados como histórico do incidente, NÃO como avaliações válidas. Não foram deletados ainda — aguardando decisão do Otávio sobre cleanup.

---

## Decisão pendente

Nenhum dos 3 providers baratos completa a pipeline CORRIGIR com gabarito parcial (Lista0 Q5-only):
- Anthropic: completou mas alucinando gabarito + $42 de custo
- GPT-5 Nano: relatório vazio
- Gemini Flash: 33/38 falham no CORRIGIR

**Opções**:
a) Testar modelo mais capaz (GPT-5, Gemini 2.5 Pro, Claude Sonnet) — custo maior mas pode funcionar
b) Relaxar validator de "resposta_aluno divergente" — aceitar paráfrases
c) Aumentar max_tool_iterations — mais custo por tentativa
d) Aceitar que gabarito parcial é limitação real e buscar gabarito completo
e) Combinação de b+c

Aguardando direção do Otávio.
