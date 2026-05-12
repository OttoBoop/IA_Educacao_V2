# Teste pipeline-completo — Gemini 3 Flash — Eric Manoel

**Data:** 2026-04-17
**Commit:** 50935ea
**Task ID (final, sucesso):** task_00d2240157ab
**Task ID (tentativa 1, falhou):** task_40d1fe249dfc
**Tentativas:** 2 (primeira falhou em `corrigir` sem produzir documento; segunda completou os 3 estágios)

## Status final: SUCESSO

### Resumo da execução

- Atividade: `126e8b5ad7dd6d59` (Lista0 — Álgebra Linear Avançada 2026-1)
- Aluno: Eric Manoel Ribeiro de Sousa (`660e9421b246ad3f`)
- Modelo: `gem3flash001` (Gemini 3 Flash)
- Etapas executadas: `corrigir`, `analisar_habilidades`, `gerar_relatorio`
- Extrações anteriores: usadas as já prontas (nao re-extraídas)

### Histórico das tentativas

**Tentativa 1 — task_40d1fe249dfc (12:10:22 UTC)**

- Disparada com `force_rerun=true`.
- Status evoluiu para `failed` antes de 30s (primeira iteração já veio `corrigir:failed`).
- Não foi possível recuperar a causa exata pelo endpoint público (não há endpoint `/task-events` ou log acessível via API). Nenhum documento novo de correcao foi persistido com timestamp próximo ao disparo (apenas docs pré-existentes das 12:01 e 05:24).
- Aguardado 90s conforme política de retry e disparada nova tentativa.

**Tentativa 2 — task_00d2240157ab (12:13:39 UTC)**

- Polling a cada 30s:
  - iter 1: `corrigir:completed, analisar_habilidades:running`
  - iter 2: `corrigir:completed, analisar_habilidades:running`
  - iter 3: `corrigir:completed, analisar_habilidades:completed, gerar_relatorio:running`
  - iter 4: `status=completed` (todos os 3 estágios ok)
- Tempo total aproximado: ~105 segundos (≈ 4 iterações × 30s).

## Resultado por documento

Cada estágio produziu 2 artefatos: o JSON de dados (`criado_por=pipeline_tool`) e o PDF renderizado (`criado_por=ia_execute_python_code`). A validação abaixo é sobre o JSON de dados (o que importa para a pipeline).

### correcao (doc_id: bb0f0c63f75589dd)

- Arquivo: `correcao_eric_manoel.json_3742.json`
- Criado em: 2026-04-17T12:13:59Z
- JSON válido: SIM
- Keys: `nota_final`, `questoes`, `total_acertos`, `total_erros`, `feedback_geral`, `_avisos_documento`, `_avisos_questao`, `_avisos_stage`
- `nota_final`: **7.01**
- `_avisos_documento`: `[]` (0 itens)
- `_avisos_questao`: 2 itens — MISSING_CONTENT em Q2 e Q4 ("Questão deixada em branco na prova manuscrita.")
- `_avisos_stage`: `"CORRIGIR"` ✓
- `questoes[]`: 7 itens com `numero`, `nota`, `nota_maxima`, `acerto`, `feedback`
- Tokens in/out: não disponíveis no metadata (`tokens_usados=0` — campo não populado pelo endpoint, mas output válido)
- PDF gerado: `b3a786693fc384df`
- Conteúdo faz sentido? **SIM** — feedbacks coerentes com conteúdo de Álgebra Linear (Vandermonde+Julia, dualidade linha/coluna, escalonamento em Q vs Z3, pseudocódigo de substituição direta, análise O(n²) empírica).

### analise_habilidades (doc_id: f6e7fa7ef961bf15)

- Arquivo: `analise_eric_sousa.json_1c38.json`
- Criado em: 2026-04-17T12:14:39Z
- JSON válido: SIM
- Keys: `habilidades`, `indicadores`, `recomendacoes`, `_avisos_documento`, `_avisos_questao`, `_avisos_stage`
- `habilidades[]`: 5 habilidades com `nome`, `nivel`, `evidencias`, `nota`
- `_avisos_documento`: `[]`
- `_avisos_questao`: 2 MISSING_CONTENT (Q2, Q4)
- `_avisos_stage`: `"ANALISAR_HABILIDADES"` ✓
- `indicadores.proficiencia_geral`: 7.01 (consistente com a correção)
- PDF gerado: `085a078eebb5ef93`
- Conteúdo faz sentido? **SIM** — habilidades bem caracterizadas: Álgebra Linear Computacional e Algorítmica, Análise Assintótica Empírica, Operações Matriciais Estruturais, Espaços Vetoriais e Escalonamento, Modelagem e Singularidade (marcada como "Não Demonstrado" devido às questões em branco). Níveis calibrados com evidências que citam questões específicas.

### relatorio_final (doc_id: 26697c8894eca2ad)

- Arquivo: `relatorio_eric_sousa.json_5bf8.json`
- Criado em: 2026-04-17T12:15:07Z
- JSON válido: SIM
- Keys: `resumo_geral`, `pontos_fortes`, `areas_melhoria`, `recomendacoes`, `nota_final`, `detalhamento`, `_avisos_documento`, `_avisos_questao`, `_fontes_utilizadas`, `_avisos_stage`
- `nota_final`: 7.01 (consistente)
- `_avisos_documento`: `[]`
- `_avisos_questao`: 2 MISSING_CONTENT (Q2, Q4)
- `_avisos_stage`: `"GERAR_RELATORIO"` ✓
- `resumo_geral`: parágrafo coerente focando no perfil computacional do aluno.
- PDF gerado: `4a00dcef2eed4ea3`
- Conteúdo faz sentido? **SIM** — pontos fortes (Julia, complexidade algorítmica, decomposições, mínimos quadrados) e áreas de melhoria (modelagem de problemas reais, matrizes singulares, aritmética modular em Zp) batem com a análise e a correção. Recomendações com prioridade alta/média/baixa.

## Checklist

Para cada um dos 3 documentos:

- [x] JSON válido (parseia) — 3/3
- [x] Campo esperado presente (correcao: nota_final + questoes[]; analise: habilidades[]; relatorio: resumo_geral + nota_final) — 3/3
- [x] `_avisos_documento` array presente (vazio nos 3) — 3/3
- [x] `_avisos_questao` array presente (2 itens MISSING_CONTENT em Q2/Q4 nos 3) — 3/3
- [x] `_avisos_stage` com valor correto (CORRIGIR / ANALISAR_HABILIDADES / GERAR_RELATORIO) — 3/3
- [x] `conteudo` do endpoint NÃO é null (endpoint `/view` retorna JSON pleno; `/conteudo` retorna metadata) — 3/3
- [x] Feedback/texto faz sentido para Álgebra Linear (não é lixo) — 3/3

## Problemas encontrados

1. **Tentativa 1 falhou sem diagnóstico acessível via API.** A primeira task (`task_40d1fe249dfc`) falhou em `corrigir` em menos de 30s. Não existe endpoint público que exponha o evento de erro da task (tentei `/api/task-events/{id}`, `/api/tasks/{id}`, `/api/task-progress/{id}/eventos` — todos 404). Sem acesso aos logs do Render, não dá para confirmar se foi 503, parse_err, ou outro. A segunda tentativa 90s depois passou sem incidente, o que é compatível com um 503 overload transiente.
2. **`tokens_usados = 0` e `ia_modelo = null` nos documentos.** Todos os docs gerados (tanto JSON quanto PDF) vêm com `tokens_usados=0`, `ia_provider=null`, `ia_modelo=null` no metadata. Isso não invalida o conteúdo, mas impede telemetria/custo por documento. Provavelmente um bug de populamento de metadata no `create_document` — **vale abrir issue separada** (fora do escopo desta validação).
3. **Diferença entre `/conteudo` e `/view`.** O endpoint `/api/documentos/{id}/conteudo` retorna metadata JSON (não o conteúdo do arquivo). O conteúdo real do JSON persistido acessa-se via `/api/documentos/{id}/view`. O roteiro da missão dizia "baixar via `/api/documentos/{id}/conteudo`" — ajustei para `/view` (e validei). Vale alinhar o contrato/documentação.

## Atingi o objetivo? SIM

Pipeline-completo com `gem3flash001` executou com sucesso end-to-end na 2ª tentativa, produzindo os 3 JSONs (correcao, analise_habilidades, relatorio_final) com:

- JSON parseável
- Todos os campos esperados por stage
- Os 3 campos injetados (`_avisos_documento`, `_avisos_questao`, `_avisos_stage`) presentes e com valores corretos
- Conteúdo qualitativamente correto para Álgebra Linear (feedback por questão coerente, habilidades bem caracterizadas, relatório consistente com nota 7.01)
- Consistência cross-stage (nota 7.01 aparece nos 3; os avisos Q2/Q4 propagam corretamente)

**Recomendação para a matriz de provider×fase:** `gem3flash001` pode sair de 🚫 e ir para ✅ em `corrigir`, `analisar_habilidades` e `gerar_relatorio` — com o asterisco de que **1 em 2 disparos falhou silenciosamente** (provavelmente 503 overload), então não é livre de retry. Estabilidade ainda precisa de mais amostras antes de elevar a ✅ "confiável".
