# 02 — Arquitetura da Pipeline: Como Funciona, Como Deveria Funcionar

> **Referência para qualquer ação futura na pipeline.** Este doc descreve o comportamento REAL do código hoje (com file:line quando relevante), distingue do comportamento DESEJADO, e lista o que precisa mudar.

---

## 1. Fluxo de uma pipeline individual (1 aluno, 1 atividade)

Função: `executar_pipeline_completo()` ([executor.py:6484](../../backend/executor.py#L6484))

```
EXTRAIR_QUESTOES → EXTRAIR_GABARITO → EXTRAIR_RESPOSTAS → CORRIGIR → ANALISAR_HABILIDADES → GERAR_RELATORIO
```

**Cada etapa é sequencial por design** — a próxima PRECISA do output da anterior:
- EXTRAIR_QUESTOES lê o PDF do enunciado, produz JSON com lista de questões
- EXTRAIR_GABARITO lê o PDF do gabarito do prof, produz JSON com respostas_corretas por questão
- EXTRAIR_RESPOSTAS lê o PDF da prova do aluno + questões extraídas, produz JSON com respostas do aluno
- CORRIGIR lê respostas do aluno + gabarito, produz JSON com nota por questão + feedback
- ANALISAR_HABILIDADES lê correção, produz JSON com perfil de habilidades
- GERAR_RELATORIO lê tudo anterior, produz JSON narrativo + PDF final

Cada etapa gera **2 artefatos**: 1 JSON (dados estruturados) + 1 PDF (visualização). Ambos são salvos como `Documento` no Supabase via `storage.salvar_documento()`.

### Escopo dos documentos

| Etapa | Escopo | aluno_id |
|---|---|---|
| EXTRAIR_QUESTOES | Atividade-level (compartilhado entre todos os alunos) | `None` |
| EXTRAIR_GABARITO | Atividade-level | `None` |
| EXTRAIR_RESPOSTAS | Aluno-level (1 por aluno) | ID do aluno |
| CORRIGIR | Aluno-level | ID do aluno |
| ANALISAR_HABILIDADES | Aluno-level | ID do aluno |
| GERAR_RELATORIO | Aluno-level | ID do aluno |

**Implicação**: EXTRAIR_QUESTOES e EXTRAIR_GABARITO são executados UMA VEZ pra toda a atividade (não 1 vez por aluno). Se já existem, `_should_run()` retorna False e a etapa é skipada.

---

## 2. Como o contexto passa entre etapas

Função: `_preparar_contexto_json()` ([executor.py:~1800](../../backend/executor.py))

Para cada etapa, essa função busca os documentos JSON das etapas anteriores e os converte em strings pra incluir no prompt:

```python
# Exemplo: pra CORRIGIR, busca:
# - questoes_extraidas ← EXTRAIR_QUESTOES mais recente
# - gabarito_extraido  ← EXTRAIR_GABARITO mais recente
# - respostas_aluno    ← EXTRAIR_RESPOSTAS mais recente pro aluno
```

### Qual documento é selecionado quando há múltiplos?

Função: `_documento_json_da_ultima_execucao()` ([executor.py:1734](../../backend/executor.py#L1734))

1. Filtra docs pelo `tipo` (ex: `TipoDocumento.EXTRACAO_QUESTOES`)
2. Ordena por `criado_em` **descendente** (mais recente primeiro)
3. Pega o `cost_run_id` do mais recente
4. Retorna todos os docs com esse `cost_run_id` (normalmente 1 JSON + 1 PDF)
5. De entre esses, seleciona o `.json`

**COMPORTAMENTO ATUAL**: NÃO filtra por `ia_provider`. Se existem docs de providers diferentes, pega O MAIS RECENTE independente de quem gerou.

**COMPORTAMENTO DESEJADO** (decisão Otávio 2026-05-27):
- Poder ESCOLHER quais docs anteriores usar, por etapa
- Na UI (opções avançadas), mostrar docs existentes e permitir selecionar
- Neste teste específico: queremos mesma IA em toda pipeline
- É perfeitamente válido usar provider A numa etapa e provider B noutra — é uma FEATURE, não bug

**COMPORTAMENTO COM `force_reexec=true`**:
- Função `_should_run()` sempre retorna True → etapa roda mesmo se doc já existe
- Novo doc é criado com novo `cost_run_id`
- Na PRÓXIMA etapa, `_documento_json_da_ultima_execucao` vai pegar O MAIS RECENTE — que é o doc recém-criado pelo provider atual
- **Ou seja: com force_reexec=true pra TODAS as etapas, o provider atual alimenta a si mesmo ao longo da pipeline**
- **MAS: se force_reexec=false pra alguma etapa (ex: EXTRAIR_QUESTOES skipada porque já existe), o contexto vem do provider que gerou o doc existente**

---

## 3. Fluxo por turma (cascade)

Função: `_cascade_prereqs()` ([executor.py:6375](../../backend/executor.py#L6375))

```
_cascade_prereqs(level="turma", entity_id=turma_id)
  → listar atividades da turma
  → para cada atividade:
      _cascade_prereqs(level="tarefa", entity_id=atividade_id)
        → listar alunos da turma
        → para cada aluno:  ← HOJE: sequencial (for/await)
            executar_pipeline_completo(atividade_id, aluno_id)
      gerar_relatorio_desempenho_tarefa(atividade_id)
  gerar_relatorio_desempenho_turma(turma_id)
```

### Paralelismo (P1)

**HOJE**: `for aluno in alunos: await executar_pipeline_completo(...)` — sequencial. 38 alunos × ~3-5 min/aluno = 2-3h.

**DESEJADO** (pedido Otávio 2026-05-20): alunos em paralelo com semáforo. Pipeline de cada aluno continua sequencial (etapa depende da anterior). Mas N alunos rodam simultaneamente.

> "Obviamente a pipeline de todos os alunos não precisa esperar que um aluno termine para começar o outro, apenas esperar que um documento na pipeline individual de alunos termine." — Otávio, 2026-05-20

**Relatório de desempenho**: espera TODOS os alunos terminarem antes de gerar. Isso é correto — o relatório agrega todos os alunos.

---

## 4. Validação dos artefatos gerados

### 4a. Schema JSON (dentro de `executar_com_tools`, executor.py:4655+)

Para `TipoDocumento.CORRECAO`, o validator exige:
- `nota_final` numérico
- `questoes[]` não vazia
- Cada questão: `nota` numérica, `acerto` booleano, `resposta_aluno` e `resposta_correta` rastreáveis contra docs anteriores
- `feedback_geral` string não vazia
- `total_acertos` e `total_erros` numéricos
- `_avisos_documento[]` e `_avisos_questao[]` presentes

**Exceção MISSING_CONTENT** (commit `181d2df`): questões com `resposta_correta = "MISSING_CONTENT"` ou vazio pulam checks de nota/acerto/trace. Só exigem `feedback` explicativo.

### 4b. PDF cross-check (executor.py:490-697)

- `nota_final` no PDF bate com JSON
- `feedback_geral` presente e não truncado
- Notas por questão no PDF batem com JSON (regex "questão N nota M")

### 4c. O que NÃO é validado (P5)

- Nota faz sentido? (0 pra aluno que acertou? 10 pra quem não respondeu?)
- Feedback referencia questões corretas?
- Gabarito é real ou inventado pela IA?
- `nota_final` = soma das notas por questão?
- Conteúdo é pedagogicamente útil?

---

## 5. Retries e custo

### Retries de API
- `_executar_com_retry()` (executor.py:6580-6617)
- `max_retries = 2` → até 3 tentativas por chamada
- Trigger: `resultado.retryable == True` (erros 429 rate-limit, 5xx server)
- Cada retry gera NOVO doc com NOVO `cost_run_id`

### Retries de pipeline (NÃO são retries de API)
- Quando `_cascade_prereqs` falha pra um aluno e o sistema retenta via `force_reexec=true`, toda a pipeline de 6 etapas roda de novo
- Isso causou o incidente Anthropic: 91 chamadas `extracao_gabarito` (retries do pipeline inteiro, não da API)

### Custo
- Cada doc gerado tem `metadata.tokens_entrada` e `metadata.tokens_saida`
- Custo real = `tokens × rate do modelo` (rates no `backend/data/model_catalog.json`)
- **HOJE**: custo é calculado pós-hoc lendo docs do Supabase. Não existe endpoint/tabela dedicada.
- **DESEJADO** (P4): backend salvar custo real por pedido API no momento da chamada

### Incidente Anthropic ($42.65)
- Run `task_eef18debdfe8` (Claude Haiku 4.5, 2026-05-25)
- 449 docs gerados (esperado ~132 sem retries)
- CORRIGIR: 149 docs pra ~22 alunos = média 6.8 docs/aluno (retries do guard strict que abortava CORRIGIR quando gabarito tinha MISSING_CONTENT; Anthropic alucinou gabarito completo em retries pra passar)
- 10 alunos com pipeline full, todos com gabarito alucinado em 6/7 questões
- Crédito Anthropic esgotou após o run

---

## 6. Caso especial: gabarito parcial

PDF do gabarito do prof para Lista0 contém APENAS a resolução da Q5 (as questões 1, 2, 3, 4, 6, 7 não estão no PDF).

Todos os providers extraem corretamente: `_avisos_questao: [{codigo: "MISSING_CONTENT", questao: 1}, ...]`

**Antes do fix** (guard strict): CORRIGIR abortava se gabarito tinha MISSING_CONTENT → providers honestos travavam, providers que alucinavam gabarito passavam.

**Depois do fix** (commit `4c68e15`): CORRIGIR recebe diretiva "GABARITO PARCIAL" no system prompt pedindo pra marcar Q1-Q4/Q6-Q7 como `nota=null, acerto=null, resposta_correta="MISSING_CONTENT"`.

**Problema residual**: GPT-5 Nano interpretou a diretiva como "não corrija nada" e retornou `questoes: []` (relatório vazio). Diretiva precisa ser mais explícita.

---

## 7. Arquivos-chave no código

| Arquivo | Conteúdo relevante |
|---|---|
| [backend/executor.py](../../backend/executor.py) | Pipeline completa, cascade, validação, retries, STAGE_TOOL_INSTRUCTIONS |
| [backend/routes_prompts.py](../../backend/routes_prompts.py) | Endpoints `/api/executar/pipeline-desempenho-*`, background launchers |
| [backend/routes_tasks.py](../../backend/routes_tasks.py) | `task_registry`, `update_stage_progress`, `complete_pipeline_task` |
| [backend/prompts.py](../../backend/prompts.py) | Templates de prompt por etapa (EXTRAIR_QUESTOES, etc.) |
| [backend/storage.py](../../backend/storage.py) | Supabase storage, `salvar_documento`, `listar_documentos` |
| [backend/data/model_catalog.json](../../backend/data/model_catalog.json) | IDs e rates de modelos |
| [frontend/index_v2.html](../../frontend/index_v2.html) | Painel de progresso, modal desempenho, botão Gerar Relatório |

---

## 8. Contrato Multi-IA Canonico (2026-06-06)

Decisao: `model_id` e a referencia publica canonica. `provider_id` permanece
apenas como compatibilidade legada e deve ser registrado como legado quando
usado.

Regras:

- Nenhum endpoint pode trocar modelo em silencio. Modelo inexistente falha alto.
- `model_ids[]` permite comparar o mesmo documento em varias IAs; sucesso de
  uma IA nao apaga falha de outra.
- `models_per_stage` e o mapa canonico por etapa. `providers` e `phase_models`
  sao aliases aceitos temporariamente.
- `source_document_ids` permite escolher documentos anteriores explicitamente.
  Quando ausente, o sistema usa `selection_mode=latest_valid`.
- Todo documento gerado deve registrar `requested_model_id`, `resolved_provider`,
  `resolved_model`, `source_document_ids`, tokens e tempo quando disponiveis.

Novo tipo generico:

```text
analise_documento_ia
```

Novo endpoint generico:

```text
POST /api/executar/documento-multi-ia
```

Uso esperado: analisar qualquer documento existente com um ou mais `model_id`,
salvando uma saida por IA sem fingir que a analise e `relatorio_final` ou
desempenho agregado.
