# Teste Chat — Gemini 3 Flash

**Data:** 2026-04-17
**Endpoint:** POST /api/chat
**Modelo:** gem3flash001
**Base URL:** https://ia-educacao-v2.onrender.com

## Status final: SUCESSO

Ambos os testes retornaram HTTP 200, respostas em português coerentes, sem templates literais `{{...}}`, com tokens > 0 e o segundo teste demonstrou uso do contexto do histórico.

---

## Teste 1 — Mensagem única

- **HTTP:** 200
- **Provider:** google
- **Model:** gemini-3-flash-preview
- **Model name:** Gemini 3 Flash
- **Latência:** 1930,22 ms
- **Tokens:** 662
- **Resposta:**
  > "Álgebra linear é o ramo da matemática que estuda espaços vetoriais, transformações lineares e sistemas de equações, utilizando vetores e matrizes como ferramentas fundamentais para modelar e resolver problemas multidimensionais."
- **Templates literais `{{...}}`?** NÃO
- **Observação:** a resposta inclui um comentário HTML `<!-- DEBUG_V3_MARKER_2026 -->` no final (marcador do endpoint `chat_direto_v3`). Não é template literal; é um marcador de debug controlado pelo servidor.

---

## Teste 2 — Conversação multi-turn

Payload com 3 turnos (user → assistant → user), onde a última mensagem pedia "Dê um exemplo prático." após o assistant já ter definido álgebra linear.

- **HTTP:** 200
- **Provider:** google
- **Model:** gemini-3-flash-preview
- **Model name:** Gemini 3 Flash
- **Latência:** 14993,25 ms
- **Tokens:** 2502
- **Resposta (resumo):** apresentou como exemplo prático a **resolução de sistemas de equações** aplicada a preços de produtos A e B, com matriz de coeficientes 2x2, vetor de incógnitas (Preço A, Preço B) e vetor de resultados (190, 180), sugerindo Matriz Inversa ou Eliminação de Gauss. Trecho inicial:
  > "Um dos exemplos mais práticos e fundamentais da álgebra linear é a **resolução de sistemas de equações**, que é utilizada em diversas áreas, desde a economia até a engenharia e computação."
- **Usa contexto do histórico?** SIM. A resposta é claramente continuação do diálogo: não redefine álgebra linear, parte direto para um exemplo prático como solicitado no último turno.
- **Templates literais `{{...}}`?** NÃO
- **Observação importante (comportamento lateral do endpoint):** além do texto, a resposta incluiu um bloco `documento-binario:exemplo_pratico_algebra.pdf` com PDF em base64 (2,6 KB) gerado pelo servidor e a frase "Clique no botao 'Baixar' acima para fazer o download." Isso vem do system prompt ativo no endpoint (`debug_prompt_start` começa com "Voce e um assistente educacional especializado em correcao de provas. REGRA CRITICA PARA GERACAO DE..."), que instrui o modelo a gerar arquivos binários. Não afeta o critério de sucesso (resposta em PT, sem `{{...}}`, tokens > 0, contexto usado), mas é um comportamento inesperado para um endpoint "chat genérico" — o system prompt do `/api/chat` não é um prompt neutro de assistente de chat, e sim o mesmo prompt do fluxo de correção de provas.

---

## Critérios de sucesso

- [x] HTTP 200 em ambos os testes
- [x] Resposta em português
- [x] Sem templates literais `{{...}}`
- [x] Segundo teste usa contexto do histórico (não responde do zero)
- [x] Tokens reportados > 0 (662 e 2502)

---

## Atingi o objetivo?

**SIM**, porque o endpoint `POST /api/chat` respondeu com HTTP 200 em ambos os testes usando o modelo `gem3flash001` (Gemini 3 Flash), produziu respostas reais em português sem templates literais `{{...}}`, reportou tokens > 0 e respeitou o histórico de conversação no teste multi-turn.

### Nota para a matriz consolidada (`12_matriz_provider_fase.md`)

Gemini 3 Flash (`gem3flash001`) está **VALIDADO na categoria Chat**, somando-se à validação prévia em Pipeline do aluno (`teste_gemini_pipeline_completo.md`).

### Ressalva (não bloqueante)

O endpoint `/api/chat` está usando o system prompt do fluxo de correção de provas (confirmado pelo `debug_prompt_start` retornado: "Voce e um assistente educacional especializado em correcao de provas. REGRA CRITICA PARA GERACAO DE..."). Isso faz o modelo ocasionalmente gerar arquivos binários (PDF em base64) dentro da resposta de chat livre. Vale avaliar se o `/api/chat` deveria ter system prompt próprio, mais neutro, em vez de reaproveitar o de correção. Fica como observação para a fase de polimento — não invalida este teste.
