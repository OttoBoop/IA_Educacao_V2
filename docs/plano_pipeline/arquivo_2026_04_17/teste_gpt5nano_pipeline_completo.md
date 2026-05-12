# Teste pipeline-completo — GPT-5 Nano — Henrique

**Data:** 2026-04-17
**Commit:** 50935ea
**Task ID:** `task_ca3769cfdc97`
**Endpoint:** `POST https://ia-educacao-v2.onrender.com/api/executar/pipeline-completo`
**Atividade:** `126e8b5ad7dd6d59` (Lista0, Álgebra Linear Avançada, 2026-1)
**Aluno:** Henrique Coelho Beltrão (`fb881a3961022dd9`)
**Model ID:** `gpt5nano001` (GPT-5 Nano)
**Selected steps:** `["corrigir","analisar_habilidades","gerar_relatorio"]`
**Force rerun:** true

## Status final: FALHA

A pipeline-completo terminou em `status=failed` no polling, com o seguinte padrão de stages (`/api/task-progress/task_ca3769cfdc97`):

```
extrair_questoes      = pending
extrair_gabarito      = pending
extrair_respostas     = pending
corrigir              = completed   <-- mas outputs corrompidos, ver abaixo
analisar_habilidades  = failed      <-- bloqueou a pipeline
gerar_relatorio       = pending
```

`corrigir` foi marcada como "completed" pela orquestração, mas na prática gerou 3 documentos lixo (ver seção CORRECAO), e `analisar_habilidades` falhou em seguida — provavelmente porque não conseguiu ler uma correção válida como input. `gerar_relatorio` nunca executou. A task parou aí.

Timing: task criada 12:10:36, última stage com timestamp em CORRIGIR 12:10:59 — falhou em ~23s do início.

Nenhum documento `analise_habilidades` foi persistido (`/api/documentos?...&tipo=analise_habilidades` → `[]`) e nenhum `relatorio_final` novo foi criado após essa task.

### Resultado por documento

O endpoint de CORRIGIR criou **3 documentos** (o tool-use fez múltiplas chamadas `create_document`):

#### correcao `455cceac050b6290` (1388 bytes) — o único com conteúdo semelhante a JSON
- **JSON válido:** NÃO. `/api/documentos/{id}/conteudo` retorna `conteudo=null`, `erro="Erro ao ler JSON: Extra data: line 12 column 2 (char 1349)"`. O arquivo termina com `]},` literal, fora do objeto — parser rejeita.
- **Schema:** flat antigo — `nota`, `nota_maxima`, `percentual`, `status`, `feedback`, `pontos_positivos`, `pontos_melhorar`, `erros_conceituais`, `habilidades_demonstradas`, `habilidades_faltantes`. **NÃO** é o STAGE_TOOL_INSTRUCTIONS (não tem `nota_final` nem `questoes[]`).
- **nota_final / nota:** `nota: 5.72` (de 10). Mesmo valor do teste anterior via `/executar/etapa`, inclusive percentual 57.2 e status `parcial`. Feedback textual também bate com o anterior (resumo por questão, Q3/Q5/Q6/Q7 respondidas, Q1/Q2/Q4 em branco). Output do modelo é consistente entre rotas — o problema é só persistência/schema.
- **`_avisos_documento`:** AUSENTE. A injeção default de `create_document` (commit 5737611) **não aplicou** — provavelmente porque o tool-use escreveu o arquivo direto fora do caminho que injeta defaults, ou porque o parse falhou antes da injeção.
- **`_avisos_questao`:** AUSENTE.
- **`_avisos_stage`:** AUSENTE.
- **Tokens in/out:** N/A — `ia_provider=null`, `ia_modelo=null`, `tokens_usados=0`, `prompt_usado=null`. A task completou sem registrar metadata nenhuma no DB.
- **Conteúdo faz sentido?** SIM (o que dá para ler). Feedback cita forward substitution, operadores elementares, Q/Z3, interpolação — tudo coerente com a matéria. O modelo entendeu a prova. Mas como o JSON está malformado, a camada de consumo (analise_habilidades) não conseguiu ler.

#### correcao `021a58b20d2fee05` (0 bytes, extensão `.txt`) — alucinação do tool-use
- **Nome:** `document_2.txt_b551.txt`. O GPT-5 Nano chamou `create_document` pedindo para criar um arquivo `.txt` chamado "document_2" com conteúdo vazio.
- **JSON válido:** N/A (não é JSON, é txt vazio).
- **Conteúdo:** string vazia.
- **`_avisos_*`:** AUSENTES.
- **ia_provider / modelo:** null / null.
- **Faz sentido?** NÃO. É entrada lixo que nunca deveria ter sido criada.

#### correcao `a766783a9b352032` (75 bytes) — outra alucinação
- **Nome:** `correcao_henrique.pdf.json_1d33.json`.
- **JSON válido:** NÃO. `conteudo=null`, erro "Expecting value: line 1 column 1 (char 0)".
- **Conteúdo raw:** `PDF gerado com resumo da correção (link/arquivo: correção_henrique.pdf)` — ou seja, o modelo devolveu um TEXTO em linguagem natural afirmando ter gerado um PDF, dentro de um arquivo `.json`. Alucinação completa.
- **`_avisos_*`:** AUSENTES.

#### analise_habilidades — **NÃO FOI CRIADO**
- Stage falhou (`status=failed`). Nenhum documento persistido.
- Sem endpoint público de logs — não é possível recuperar a mensagem de erro exata nesta sessão. O `/api/tasks/{id}` não expõe detalhe e `/api/task-progress/{id}` só dá o state machine.
- Hipótese forte: o leitor tentou carregar uma correção como input; o mais recente é o `a766783a9b352032` (texto "PDF gerado..."), que falha no JSON parse, e a stage aborta.

#### relatorio_final — **NÃO FOI CRIADO**
- Stage `gerar_relatorio` ficou em `pending`, nunca executada (bloqueada pela falha anterior).

### Checklist de critérios de sucesso

Para os 3 documentos exigidos (correcao, analise_habilidades, relatorio_final):

- [ ] JSON válido (parseia) — **0/3**. A correção "principal" tem lixo no fim; os outros 2 são texto/vazio; os outros 2 docs não existem.
- [ ] Campo esperado presente — **parcial/0**. A `nota` existe na correção malformada; `habilidades` e `resumo/conteudo` não existem.
- [ ] `_avisos_documento` array presente — **0/3**.
- [ ] `_avisos_questao` array presente — **0/3**.
- [ ] `_avisos_stage` com valor correto — **0/3**.
- [ ] `conteudo` do endpoint NÃO é null — **0/3** (2 doc.correcao com conteudo=null, 1 doc.correcao com txt vazio, 2 docs ausentes).
- [ ] Feedback faz sentido para Álgebra Linear — **1/3 parcial** (o feedback textual da correção 455c é correto e específico).

## Comparação com `/executar/etapa` (mesmo modelo, mesmo aluno)

Baseline: `teste_executar_etapa_corrigido.md` — commit `a632883`, Henrique, `gpt5nano001`, stage `corrigir`.

| Aspecto | `/executar/etapa` (a632883) | `/pipeline-completo` (50935ea) |
|---------|------------------------------|-------------------------------|
| HTTP status | 200 | 200 (task aceita) |
| Task final | `sucesso=true` no payload | `status=failed` |
| Schema produzido | flat antigo (`nota`, listas) | flat antigo (`nota`, listas) — **mesmo** |
| `nota` | 5.72 | 5.72 — **idêntico** |
| Feedback textual | específico Álgebra Linear, Q3/5/6/7 respondidas, Q1/2/4 branco | mesmo conteúdo, mesmo diagnóstico |
| `_avisos_documento/_questao/_stage` presente | NÃO | NÃO |
| Documento persistido | NÃO (payload volta, nada grava em DB) | SIM, porém **3 arquivos lixo**: 1 JSON malformado + 1 txt vazio + 1 txt alucinando ser PDF |
| `ia_provider` / `ia_modelo` em DB | N/A (sem persistência) | `null` / `null` — metadata não foi gravada mesmo persistindo |
| `tokens_usados` em DB | N/A | `0` |
| analise_habilidades | não testado | **falhou**, bloqueou pipeline |
| relatorio_final | não testado | não executou |

**Conclusão:** A injeção automática de `_avisos_*` (commit 5737611) **não resolveu** o problema para GPT-5 Nano em nenhum dos dois caminhos. O modelo simplesmente não emite o schema STAGE_TOOL_INSTRUCTIONS — ele continua produzindo o schema flat antigo. E no caminho tool-use (`pipeline-completo`), o tool-use introduziu problemas NOVOS:

1. Múltiplas chamadas `create_document` (3 em uma stage que deveria produzir 1 doc)
2. Nomes de arquivo alucinados (`document_2.txt`, `correcao_henrique.pdf.json`)
3. Conteúdo em texto livre dentro de arquivos `.json` (ex.: "PDF gerado com resumo...")
4. JSON com lixo no final (`]},` sem abertura correspondente)
5. Metadata (provider/modelo/tokens) não persistida em DB mesmo com documento criado

A **hipótese da missão** ("os `_avisos_*` só pegam no caminho tool-use") **não se confirma**: em nenhum caminho o GPT-5 Nano emite esses campos, e os defaults do `create_document` também não estão sendo aplicados aos arquivos que ele gera (nem o JSON malformado tem `_avisos_documento: []` injetado).

O **pre-flight check PROVA_RESPONDIDA** (commit 50935ea) aparentemente passou, pois extracao_respostas está ok em DB (doc `c0be6afcb18470ef`) e a pipeline não abortou antes de CORRIGIR. Esse fix funciona.

## Atingi o objetivo? NÃO

Porque:

1. A pipeline não completou — terminou em `failed` antes de chegar em `analisar_habilidades` e `gerar_relatorio`. Faltam 2 dos 3 documentos exigidos.
2. O único documento gerado (correção) tem JSON malformado (`conteudo=null` via API), sem `_avisos_*`, sem metadata de provider/modelo/tokens, em schema flat legado.
3. O behaviour via tool-use foi **pior** que via `/executar/etapa`: criou 2 documentos extras que são lixo puro (`.txt` vazio e JSON com frase sobre PDF).
4. A matriz atualmente lista GPT-5 Nano como ⚠️ PARCIAL no `/executar/etapa`. Este teste mostra que em `pipeline-completo` ele está **pior**: não só continua sem `_avisos_*` e com schema antigo, como agora emite tool-calls múltiplos e mal formatados. Deveria ser rebaixado para ❌ FALHA (para esta combinação de rota + stage + modelo) na matriz.

### Sinais concretos para os próximos fixes

- **Tool-use instruções de `create_document` para GPT-5 Nano precisam de reforço:** o modelo precisa ser restringido a 1 chamada por stage, com nome fixo, conteúdo estritamente JSON válido no schema STAGE_TOOL_INSTRUCTIONS. Em reasoning models (Nano), instruções fortes no "developer" role e few-shot no prompt costumam resolver.
- **Persistência sem metadata:** mesmo com o doc criado, `ia_provider`, `ia_modelo`, `tokens_usados` ficaram null/0. Há um bug separado — a rotina que grava o documento a partir do tool-call não está populando essas colunas. Vale verificar `pipeline_tool` (criado_por) no `create_document`.
- **Injeção de `_avisos_*` default:** não está sendo aplicada quando o conteúdo escrito pelo tool-call falha no JSON parse. O fix do commit 5737611 precisa rodar **antes** de qualquer parse, e também quando o parse falhar precisa ou rejeitar o arquivo ou injetar defaults em um JSON de erro conhecido.
- **Validação de output de CORRIGIR antes de dar "completed":** a stage foi marcada como completa apesar dos 3 outputs serem inutilizáveis. Deveria haver um schema check (`nota_final` OU `nota` + `feedback` obrigatórios) que falhe explicitamente em vez de deixar analise_habilidades falhar depois, mascarando o root cause.

### Observações sobre a missão

- Restrições respeitadas: não editei código; não fiz fallback para outro modelo; usei apenas o model_id pedido; terminei bem dentro do timeout de 12 min (task de ~23s + polling).
- Não consegui recuperar a mensagem de erro literal do `analisar_habilidades` — o backend não expõe logs por task (só state machine via `/api/task-progress/{task_id}`). Para próximos testes, seria útil expor `failure_reason` ou `last_error` no payload da task.
