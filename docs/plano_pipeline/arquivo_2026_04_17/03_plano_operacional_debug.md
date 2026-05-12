# Plano Operacional de Debug

**Data:** 2026-04-17
**Autor:** Orquestrador (Claude Code)
**Base:** Docs 01 (Historico) e 02 (Decisoes Arquiteturais)

Este documento define os passos concretos para corrigir os problemas encontrados. Nao define o algoritmo exato de cada correcao -- isso vem durante a implementacao. O foco e priorizar, sequenciar e definir criterios de "pronto".

---

## Diagnostico resumido

Dos Docs 01 e 02, os problemas se organizam em 3 eixos:

| Eixo | Problema raiz | Impacto |
|------|--------------|---------|
| **A. Avisos** | Dupla instrucao conflitante (PROMPTS_PADRAO vs STAGE_TOOL_INSTRUCTIONS) + handler opaco | `_avisos_documento` e `_avisos_questao` nao populados nas etapas 4-6 |
| **B. Pipeline** | Cascade de erros gera documentos fantasma; `executar_com_tools()` nao popula campos essenciais | Alunos aparecem "corrigidos" sem correcao real; perda de tokens/metadata |
| **C. Providers** | Conversao de tools sintatica; flags inconsistentes em models.json | Risco de falha silenciosa por provider; configs erradas |

---

## Prioridade de correcao

A ordem abaixo segue dependencia logica e impacto:

### Prioridade 1: Unificar instrucoes de schema JSON (Eixo A)

**Por que primeiro:** E a causa raiz mais provavel dos avisos nao populados. Modelos menores (Haiku, GPT-5 Nano) seguem o PROMPTS_PADRAO que NAO pede avisos, ignorando STAGE_TOOL_INSTRUCTIONS.

**O que corrigir:**
1. Remover ou alinhar os schemas conflitantes entre `PROMPTS_PADRAO[CORRIGIR/ANALISAR/GERAR]` e `STAGE_TOOL_INSTRUCTIONS`
2. Garantir que existe **uma unica fonte de verdade** para o schema de cada etapa
3. Incluir `_avisos_documento` e `_avisos_questao` em todos os schemas
4. Incluir `_avisos_stage` no JSON salvo (com valor correto, nao hardcode "CORRIGIR")

**Arquivos:**
- `backend/prompts.py` — alinhar PROMPTS_PADRAO com STAGE_TOOL_INSTRUCTIONS
- `backend/executor.py` — rever como system prompt + tool_instructions sao concatenados (~L1232)

**Criterio de pronto:**
- [ ] Para cada etapa (CORRIGIR, ANALISAR, GERAR): existe UM UNICO schema JSON documentado
- [ ] Schema inclui `_avisos_documento`, `_avisos_questao`, `_avisos_stage`
- [ ] Teste: enviar prompt para Haiku, Gemini 3 Flash e GPT-5 Nano — os 3 retornam campos de aviso

---

### Prioridade 2: Injetar defaults de avisos no handler (Eixo A)

**Por que segundo:** Mesmo com prompts unificados, LLMs podem omitir campos opcionais. A defesa em profundidade e injetar defaults.

**O que corrigir:**
1. Em `handle_create_document()`: apos salvar, parsear o JSON e injetar `_avisos_documento: []` e `_avisos_questao: []` se ausentes
2. Injetar `_avisos_stage` com o nome real da etapa (obtido do `ToolExecutionContext`)
3. Re-salvar o JSON corrigido

**Arquivos:**
- `backend/tool_handlers.py` (~L624-756)
- `backend/executor.py` — garantir que `ToolExecutionContext` passa a etapa atual

**Criterio de pronto:**
- [ ] Todo JSON salvo por `create_document` tem `_avisos_documento`, `_avisos_questao`, `_avisos_stage`
- [ ] Teste com JSON que NAO inclui avisos: campos default sao injetados
- [ ] Teste com JSON que inclui avisos: campos originais sao preservados

---

### Prioridade 3: Corrigir leitura de avisos no visualizador (Eixo A)

**O que corrigir:**
1. `_processar_analise()` deve ler `_avisos_documento` e `_avisos_questao` do JSON de analise (atualmente nao le)
2. Adicionar leitura de avisos do GERAR_RELATORIO em `get_resultado_aluno()`
3. Usar `_avisos_stage` real (nao hardcode "CORRIGIR") para calcular severidade

**Arquivos:**
- `backend/visualizador.py` — `_processar_analise()` (~L428-468), `get_resultado_aluno()`

**Criterio de pronto:**
- [ ] Avisos de ANALISAR_HABILIDADES sao exibidos no frontend
- [ ] Avisos de GERAR_RELATORIO sao exibidos no frontend
- [ ] Severidade calculada com stage correto

---

### Prioridade 4: Preencher campos ausentes em `executar_com_tools()` (Eixo B)

**O que corrigir:**
1. Popular `resposta_parsed` com o dict parseado do JSON salvo pelo handler
2. Popular `documento_id` com o ID retornado pelo handler
3. Popular `tokens_saida` separadamente (requer mudanca em chat_service.py)
4. Setar `etapa` com o enum correto (nao string "tools")
5. Popular `prompt_usado` e `prompt_id`

**Arquivos:**
- `backend/executor.py` (~L2449-2460)
- `backend/chat_service.py` — retornar `input_tokens` e `output_tokens` separados nos metodos `_chat_*`

**Criterio de pronto:**
- [ ] `ResultadoExecucao` do Path 2 tem todos os campos preenchidos como o Path 1
- [ ] `tokens_saida` > 0 em execucoes tool-use

---

### Prioridade 5: Eliminar documentos fantasma (Eixo B)

**O que corrigir:**
1. Quando uma etapa falha por `_erro_pipeline`, NAO salvar um documento no banco — ou salvar com um campo/flag que distingue "erro" de "resultado real"
2. Alternativa: adicionar campo `is_error: bool` na tabela `documentos`
3. Ajustar `listar_documentos()` e status checks para ignorar documentos de erro

**Arquivos:**
- `backend/executor.py` — logica de cascade (~L618-659)
- `backend/models.py` — potencialmente adicionar campo
- `backend/storage.py` — `listar_documentos()`, `buscar_documento()`

**Criterio de pronto:**
- [ ] Alunos com falha em EXTRAIR_RESPOSTAS nao aparecem como "corrigidos"
- [ ] Status reflete o estado real (faltando, em_progresso, erro, completo)

---

### Prioridade 6: Corrigir flags inconsistentes em models.json (Eixo C)

**O que corrigir (achados do Doc 04):**
1. Claude Sonnet 4.5: `suporta_function_calling: false` → deve ser `true`
2. Gemini 2.5 Flash Lite: `suporta_function_calling: true` → verificar se e verdade
3. Gemini 2.0 Flash: marcar como `ativo: false` (EOL marco 2026)
4. Verificar outros modelos vs realidade

**Arquivos:**
- `backend/data/models.json`

**Criterio de pronto:**
- [ ] Cada modelo ativo tem flags que correspondem a realidade do provider

---

### Prioridade 7: Implementar tracking de custos de tokens (Eixo novo)

**Depende de:** Prioridade 4 (tokens_saida populado)

**O que implementar (conforme Doc 05):**
1. Dataclass `TokenUsageRecord` em models.py
2. Gravar apos cada etapa em executor.py
3. Endpoints em routes_custos.py
4. Corrigir chat_service.py para retornar input/output tokens separados

**Criterio de pronto:**
- [ ] Apos rodar pipeline, `/api/custos/materia/{id}` retorna custos nao-zero
- [ ] Custos separados por provider e modelo

---

## O que pode rodar em paralelo

```
[Prioridade 1] ──────────────┐
[Prioridade 2] ──────────────┤
[Prioridade 3] ──────────────┤──> Eixo A (Avisos) — 3 tarefas sequenciais
                              │
[Prioridade 4] ──────────────┤──> Eixo B (Pipeline) — paralelo com Eixo A
[Prioridade 5] ──────────────┘

[Prioridade 6] ──────────────────> Eixo C (Providers) — independente, pode rodar a qualquer momento

[Prioridade 7] ──────────────────> Custos — depende de P4, pode rodar apos P4
```

**Paralelo seguro:**
- Eixo A (P1-P3) e Eixo C (P6) podem rodar ao mesmo tempo (arquivos diferentes)
- Eixo B (P4-P5) e Eixo C (P6) podem rodar ao mesmo tempo
- P7 (Custos) so apos P4

**Sequencial obrigatorio:**
- P1 antes de P2 (precisa saber o schema final antes de injetar defaults)
- P2 antes de P3 (precisa que avisos existam no JSON antes de corrigir leitura)
- P4 antes de P7 (precisa que tokens_saida esteja populado)

---

## Testes por prioridade

| P# | Tipo de teste | Descricao |
|----|---------------|-----------|
| P1 | Unit + Integration | Enviar prompt para cada provider, validar schema JSON retornado |
| P2 | Unit | Mock de tool call sem avisos → verificar que defaults sao injetados |
| P3 | Unit | Mock de visualizador com JSON de analise contendo avisos → verificar renderizacao |
| P4 | Integration | Executar etapa CORRIGIR → verificar todos os campos de ResultadoExecucao |
| P5 | Integration | Simular falha em EXTRAIR_RESPOSTAS → verificar que status nao mostra "corrigido" |
| P6 | Unit | Validar models.json contra realidade de cada provider |
| P7 | Integration | Executar pipeline completo → consultar endpoint de custos |

---

## Verificacao end-to-end

Apos todas as prioridades implementadas:

1. Rodar pipeline para 1 aluno em "Algebra Linear Avancada" com cada provider (Haiku, Gemini 3 Flash, GPT-5 Nano)
2. Para cada execucao verificar:
   - [ ] JSON de cada etapa contem `_avisos_documento` e `_avisos_questao`
   - [ ] `_avisos_stage` tem o valor correto
   - [ ] `tokens_entrada` e `tokens_saida` > 0
   - [ ] Nenhum documento fantasma criado
   - [ ] Frontend exibe avisos com severidade correta
   - [ ] Endpoint de custos retorna valores nao-zero
3. Rodar para 1 aluno SEM prova enviada → verificar que status mostra "faltando" (nao "corrigido")

---

## Perguntas para o Otavio (human_questions)

1. **Schemas conflitantes (P1):** Devemos manter o schema do `STAGE_TOOL_INSTRUCTIONS` como fonte de verdade e adaptar `PROMPTS_PADRAO`, ou o contrario?
2. **Documentos fantasma (P5):** Preferencia entre (a) nao salvar documento de erro, (b) salvar com flag `is_error`, ou (c) salvar em path/tipo diferente?
3. **Prioridade real:** O mais urgente agora e corrigir os 7 alunos que nao foram corrigidos, ou e arrumar o sistema de avisos primeiro?
4. **Endpoint a manter:** Dos 4 endpoints duplicados de pipeline, qual o frontend realmente usa? Devemos unificar agora ou depois?
