# Teste /executar/etapa — Após Fix

**Data:** 2026-04-17
**Commit testado:** a632883
**Endpoint:** `POST https://ia-educacao-v2.onrender.com/api/executar/etapa`

## Cenário 1: Aluno com docs OK (Henrique Coelho Beltrão)

- `atividade_id`: `126e8b5ad7dd6d59`
- `aluno_id`: `fb881a3961022dd9`
- Etapa: `corrigir`

**Tentativa 1 com `gem3flash001`:** HTTP 200 mas `sucesso=false` — Gemini 3 Flash retornou 503 UNAVAILABLE ("This model is currently experiencing high demand"). Seguindo a instrução da missão, migrei para `gpt5nano001`.

**Tentativa 2 com `gpt5nano001` (fallback):**

- HTTP status: **200**
- sucesso: **true**
- Modelo usado: `gpt-5-nano` (provider `openai`) — confirma que o `model_id` do request foi respeitado e não caiu para default
- Session ID: `3ea1e0f8af3c0605`
- Tokens: 7093
- `arquivos_gerados`: `[]` (ver observação abaixo)
- Resposta contém templates literais `{{...}}`? **NÃO** (verificado: nem `{{questao}}`, nem `{{resposta_aluno}}`, nem qualquer `{{` aparece no payload retornado)

**JSON gerado (parse do campo `resposta`):**

- `nota`: **5.72** (de 10, `percentual: 57.2`, `status: parcial`)
- `feedback` (trecho): "Resumo direto: o aluno respondeu com conteúdo relevante para as questões 3, 5, 6 e 7, demonstrando compreensão sólida de operações com matrizes, espaços nulos em Q5 e implementação/complexidade de forward substitution em Q6..."
- Campos presentes: `nota`, `nota_maxima`, `percentual`, `status`, `feedback`, `pontos_positivos`, `pontos_melhorar`, `erros_conceituais`, `habilidades_demonstradas`, `habilidades_faltantes`
- `_avisos_documento` / `_avisos_questao` / `_avisos_stage` presentes: **NÃO** — o modelo não incluiu esses campos de meta-avisos no JSON de saída. O schema que ele produziu é o esperado para "corrigir" (nota + feedback + listas de pontos), mas sem os campos `_avisos_*` que a missão mencionava.
- Conteúdo faz sentido? **SIM** — feedback é específico ao conteúdo de Álgebra Linear (matrizes elementares, forward substitution, análise empírica log-log, Q3/Q5/Q6/Q7), o que só é possível se as variáveis de template foram de fato substituídas pelos documentos de `extracao_questoes`, `extracao_gabarito` e `extracao_respostas` do Henrique. Fix do commit `a632883` confirmado em operação.

**Observação sobre persistência:**
`arquivos_gerados: []` e não aparece nenhum documento do tipo `correcao` ao listar os docs da atividade/aluno (`/api/documentos/todos?atividade_ids=...&aluno_ids=...` retornou 63 docs, tipos: `extracao_gabarito` x27, `extracao_questoes` x29, `extracao_respostas` x3, `relatorio_final` x1, `prova_respondida` x1, `gabarito` x1, `enunciado` x1 — zero `correcao`). O endpoint `/executar/etapa` retornou a resposta no payload mas **não persistiu** o documento. Isto pode ser comportamento intencional (o endpoint de execução isolada não grava, só preview) ou gap separado — fora do escopo do fix em teste.

## Cenário 2: Aluno sem docs (Luisa Villanueva Guerrero)

- `atividade_id`: `126e8b5ad7dd6d59`
- `aluno_id`: `dfaa27d39b2dd166`
- Etapa: `corrigir`
- Modelo: `gem3flash001`

**Resultado:**

- HTTP status: **400**
- Mensagem de erro: `"Documentos necessários não encontrados: respostas_aluno (execute 'extrair_respostas' primeiro). Execute as etapas anteriores do pipeline antes desta."`
- Estrutura: `{"error": {"message": "...", "status_code": 400, "trace_id": null}}`
- É mensagem clara e actionable? **SIM** — diz exatamente qual documento falta (`respostas_aluno`) e qual etapa rodar para gerá-lo (`extrair_respostas`)
- Lista docs faltantes? **SIM** — identifica `respostas_aluno` como o faltante

## Atingi o objetivo? SIM

**Cenário 1 funcionou:** endpoint processou corretamente, chamou `gpt-5-nano` conforme pedido, substituiu as variáveis `{{questao}}`/`{{gabarito}}`/`{{resposta_aluno}}` pelo contexto real dos documentos pré-requisito, e devolveu um JSON de correção com conteúdo específico à matéria (Álgebra Linear Avançada — Lista0). Nenhum template literal `{{...}}` sobreviveu na saída. Gemini 3 Flash está em 503 overload no momento do teste, mas isso é problema do provider, não do endpoint.

**Cenário 2 falhou corretamente:** retornou HTTP 400 com mensagem clara identificando `respostas_aluno` como documento faltante e instruindo rodar `extrair_respostas` antes. Comportamento de fast-fail com erro explícito conforme esperado do fix.

## Ressalvas para acompanhamento (fora do escopo deste teste)

1. `gem3flash001` não testado end-to-end por 503 do provider. Re-testar quando Gemini estabilizar para confirmar que o path Google também funciona (o fix é no server, não no provider, então deve funcionar — mas empiricamente só validei OpenAI hoje).
2. Campos `_avisos_documento`, `_avisos_questao`, `_avisos_stage` não apareceram no JSON de saída do `gpt-5-nano`. Investigar se isto é exigência do schema de "corrigir" que o modelo deveria preencher mas não preencheu, ou se esses campos só são injetados em outra etapa (ex: `gerar_relatorio`).
3. `arquivos_gerados: []` — endpoint não está persistindo o documento de correção. Pode ser by-design (execução isolada = preview não persistido) ou gap. Confirmar com Otavio se é esperado.
