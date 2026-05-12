# Fluxo de Orquestracao e Case Tracking

**Data:** 2026-04-17
**Autor:** Orquestrador (Claude Code)
**Base:** Docs 01 (Historico) e 04 (Fontes e Governanca)

Este documento define como agentes de teste, orquestrador e humano devem trabalhar juntos para diagnosticar e corrigir os problemas da pipeline. Segue o principio do projeto de ciclovias: **ambiguidade vira pergunta, nao decisao silenciosa**.

---

## Licao aprendida do projeto ciclovias

A primeira tentativa do projeto de ciclovias produziu arquivos uteis, mas nao executou bem a parte mais importante: envolver o humano em tempo real. Agentes trabalharam invisiveis, perguntas ficaram em CSV sem serem feitas, e decisoes foram registradas antes do input humano.

Para o NOVO CR, o protocolo e:
- Agentes produzem **achados** (evidencia), nao conclusoes
- Duvidas viram perguntas **apresentadas ao humano antes de continuar**
- O orquestrador decide **apenas apos** evidencia + input humano

---

## Papeis

### Orquestrador (Claude Code - sessao principal)

Coordena o trabalho. Responsabilidades:
- Dividir cases entre agentes
- Revisar achados antes de registrar decisoes
- Transformar ambiguidades em perguntas para o humano
- Consolidar respostas humanas em decisoes
- Manter documentos, CSVs e relatorios coerentes
- **Nunca fingir certeza quando ha ambiguidade**

### Agentes trabalhadores (subagentes Claude Code)

Fazem investigacao focada. No fluxo padrao:
- Recebem um case ou conjunto pequeno de cases
- Leem codigo, JSONs, logs e API
- Produzem achados objetivos com evidencia
- Listam duvidas e hipoteses
- **Nao tomam decisoes finais** — o achado de um agente e evidencia, nao conclusao
- **Nao editam codigo** na fase de investigacao

### Humano (Otavio)

Fonte contextual e decisoria. Nesta fase:
- Responde perguntas escaladas pelo orquestrador
- Valida achados que dependem de contexto local
- Define prioridades quando ha trade-offs
- Respostas sao registradas em `human_answers.csv`

---

## Unidade de analise

A unidade principal e `case_id`, definida como:

```
case_id = {aluno_id}_{etapa}_{provider}
```

Exemplo: `alice_barros_CORRIGIR_anthropic`

Cada case pode apontar para:
- 1 aluno (ID no Supabase)
- 1 etapa do pipeline (EXTRAIR_QUESTOES, ..., GERAR_RELATORIO)
- 1 provider/modelo usado
- 1 ou mais documentos gerados (JSON, PDF)
- 0 ou mais erros registrados

### Cases especiais

| Tipo | Descricao |
|------|-----------|
| `global_{etapa}` | Problema na etapa que afeta todos os alunos (ex: schema conflitante) |
| `{aluno}_cascade` | Falha em cascata (etapa N falhou, N+1..6 tambem) |
| `{aluno}_phantom` | Documento fantasma (JSON com `_erro_pipeline` conta como "corrigido") |

---

## Registros

Todos ficam em `data/pipeline_debug/`:

### cases.csv

| Campo | Tipo | Descricao |
|-------|------|-----------|
| case_id | str | Identificador unico do case |
| aluno_id | str | ID do aluno no Supabase (ou "global") |
| aluno_nome | str | Nome do aluno |
| etapa | str | Etapa do pipeline |
| provider | str | Provider usado (anthropic, google, openai) |
| modelo | str | Modelo especifico |
| status | str | OK, ERRO_PARSE, ERRO_API, ERRO_DOCUMENTO, ERRO_CASCADE, PHANTOM, PENDENTE_HUMANO, WIP |
| erro_tipo | str | Tipo de erro especifico (se aplicavel) |
| erro_mensagem | str | Mensagem de erro |
| documento_id | str | ID do documento gerado (se existir) |
| tem_avisos | bool | JSON contem `_avisos_documento` ou `_avisos_questao` nao-vazios |
| timestamp | str | ISO 8601 |

### agent_findings.csv

| Campo | Tipo | Descricao |
|-------|------|-----------|
| finding_id | str | ID unico |
| case_id | str | FK para cases.csv |
| agent_name | str | Nome do agente que produziu o achado |
| finding_type | str | EVIDENCIA, HIPOTESE, DUVIDA |
| descricao | str | Texto do achado |
| arquivo_fonte | str | Arquivo de onde veio a evidencia |
| linha | int | Numero da linha (se aplicavel) |
| timestamp | str | ISO 8601 |

### human_questions.csv

| Campo | Tipo | Descricao |
|-------|------|-----------|
| question_id | str | ID unico |
| case_id | str | FK para cases.csv |
| pergunta | str | Texto da pergunta |
| contexto | str | Evidencia/achado que motivou a pergunta |
| urgencia | str | ALTA (bloqueia progresso), MEDIA (influencia decisao), BAIXA (informacional) |
| status | str | PENDENTE, RESPONDIDA |
| timestamp | str | ISO 8601 |

### human_answers.csv

| Campo | Tipo | Descricao |
|-------|------|-----------|
| answer_id | str | ID unico |
| question_id | str | FK para human_questions.csv |
| resposta | str | Texto da resposta do humano |
| timestamp | str | ISO 8601 |

### decisions.csv

| Campo | Tipo | Descricao |
|-------|------|-----------|
| decision_id | str | ID unico |
| case_id | str | FK para cases.csv |
| decisao | str | FIX_APLICADO, WORKAROUND, ADIADO, NAO_E_BUG, PRECISA_MAIS_INFO |
| descricao | str | O que foi decidido |
| base | str | Achados e respostas que fundamentaram a decisao |
| timestamp | str | ISO 8601 |

---

## Fluxo de trabalho

### Fase de Investigacao

```
1. Orquestrador cria cases em cases.csv (baseado nos dados do Doc 01)
   - 7 alunos com prova nao corrigidos → 7 cases
   - 3 alunos "corrigidos sem prova" → 3 cases (phantom)
   - Issues globais (schemas, avisos) → cases globais

2. Orquestrador lanca agentes trabalhadores (2-3 em paralelo):

   Agente Debug-Aluno:
   - Recebe 3-4 case_ids de alunos especificos
   - Le documentos JSON de cada aluno via API/storage
   - Classifica o erro (PARSE, API, DOCUMENTO, CASCADE)
   - Registra achados em agent_findings.csv

   Agente Verify-Provider:
   - Recebe 1 provider + lista de etapas
   - Executa 1 chamada de teste por etapa
   - Verifica se JSON de retorno contem avisos
   - Verifica se tool use funciona
   - Registra achados em agent_findings.csv

3. Orquestrador revisa achados:
   - Se achado e claro → registra decisao
   - Se achado e ambiguo → cria pergunta em human_questions.csv
   - Apresenta perguntas ao humano via AskUserQuestion

4. Humano responde → respostas registradas em human_answers.csv

5. Orquestrador registra decisao em decisions.csv
```

### Fase de Correcao

```
1. Orquestrador prioriza fixes baseado em decisions.csv + Doc 03

2. Para cada fix:
   a. Lanca agente implementador (1 por fix, paralelo quando possivel)
   b. Agente implementa + cria teste
   c. Orquestrador verifica resultado
   d. Atualiza case status em cases.csv

3. Apos todos os fixes:
   - Roda testes completos
   - Reexecuta pipeline para cases que falharam
   - Atualiza status final em cases.csv
```

### Fase de Verificacao

```
1. Para cada case com status != OK:
   - Reexecutar com fix aplicado
   - Verificar se status mudou para OK
   - Se nao: investigar novamente (volta para Fase de Investigacao)

2. Verificacao cross-provider:
   - Mesmo aluno, 3 providers diferentes
   - Comparar JSONs: mesma estrutura? Avisos presentes?
   - Registrar diferenças em agent_findings.csv
```

---

## Regras do protocolo

1. **Perguntar cedo, nao esconder ambiguidade.** Se um agente encontra algo que nao sabe interpretar, a acao correta e registrar como DUVIDA e o orquestrador transforma em pergunta.

2. **Resultados no chat antes de ir para CSV.** O orquestrador sempre mostra achados ao humano antes de registrar decisoes. O CSV e registro, nao substituto de comunicacao.

3. **Um case, um status.** Cada case tem exatamente um status em cada momento. Se o status muda, atualiza a linha (nao cria nova).

4. **Evidencia separada de decisao.** `agent_findings.csv` (o que foi encontrado) nunca mistura com `decisions.csv` (o que foi decidido). Achado e fato observavel; decisao e julgamento.

5. **Checkpoint humano entre rodadas.** Antes de iniciar a Fase de Correcao, o orquestrador apresenta o resumo dos achados e perguntas pendentes. Nao segue em frente com questoes abertas.

---

## Cases iniciais (baseados no Doc 01)

Esses cases devem ser criados na primeira rodada:

| case_id | aluno | etapa | status inicial | descricao |
|---------|-------|-------|----------------|-----------|
| `global_schema_conflito` | global | CORRIGIR/ANALISAR/GERAR | WIP | PROMPTS_PADRAO vs STAGE_TOOL_INSTRUCTIONS |
| `global_avisos_perdidos` | global | CORRIGIR/ANALISAR/GERAR | WIP | `_avisos_*` nao populados no Path 2 |
| `global_tokens_path2` | global | CORRIGIR/ANALISAR/GERAR | WIP | `tokens_saida` = 0 no Path 2 |
| `alice_barros_phantom` | alice_barros | CORRIGIR | PHANTOM | Corrigida sem prova enviada |
| `fabricio_dalvi_phantom` | fabricio_dalvi | CORRIGIR | PHANTOM | Corrigido sem prova enviada |
| `raphael_felberg_phantom` | raphael_felberg | CORRIGIR | PHANTOM | Corrigido sem prova enviada |
| (7 cases) | 7 alunos | variavel | ERRO_* | Prova enviada mas nao corrigidos |
| `sonnet_fc_flag` | global | config | WIP | Sonnet 4.5 com suporta_function_calling=false |
| `gemini_lite_fc_flag` | global | config | WIP | Gemini 2.5 Flash Lite com suporta_function_calling=true |

Os 7 alunos com prova nao corrigidos precisam ser identificados individualmente consultando a API.

---

## Painel operacional

O orquestrador deve manter e reportar este painel ao humano regularmente:

```
=== Painel de Progresso ===
Cases totais:    NN
  OK:            NN
  ERRO_*:        NN
  PHANTOM:       NN
  WIP:           NN
  PENDENTE_HUMANO: NN

Perguntas:
  Pendentes:     NN
  Respondidas:   NN

Fixes:
  Planejados:    NN (Doc 03)
  Implementados: NN
  Verificados:   NN
```
