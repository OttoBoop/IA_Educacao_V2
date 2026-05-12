# Contexto e Decisoes Arquiteturais

Este documento descreve as decisoes arquiteturais implicitas do pipeline de correcao do NOVO CR, com foco nos dois caminhos de execucao, no sistema de avisos (`_avisos_documento` / `_avisos_questao`), e na compatibilidade entre providers. Todos os numeros de linha referem-se ao estado do codigo em 2026-04-17.

---

## Os dois caminhos de execucao

O pipeline possui **6 etapas por aluno** divididas em dois grupos que seguem caminhos de execucao completamente distintos:

| Grupo | Etapas | Caminho | Metodo de entrada |
|-------|--------|---------|-------------------|
| Extracao | EXTRAIR_QUESTOES, EXTRAIR_GABARITO, EXTRAIR_RESPOSTAS | **Path 1 -- Multimodal** | `executar_etapa()` -> `_executar_multimodal()` |
| Analise | CORRIGIR, ANALISAR_HABILIDADES, GERAR_RELATORIO | **Path 2 -- Tool-use** | `corrigir()` / `analisar_habilidades()` / `gerar_relatorio()` -> `executar_com_tools()` |

Alem disso, existem 3 etapas agregadas (RELATORIO_DESEMPENHO_TAREFA/TURMA/MATERIA) que tambem usam o Path 2.

### Path 1: Multimodal (EXTRAIR_*)

**Fluxo completo:**
```
executar_etapa() [executor.py:415]
  -> _executar_multimodal() [executor.py:586]
       1. _get_provider_config(provider_id)        -- resolve config do provider
       2. _preparar_variaveis_texto()               -- carrega texto dos documentos
       3. _coletar_arquivos_para_etapa()            -- coleta PDFs/imagens para envio nativo
       4. _preparar_contexto_json()                 -- carrega JSONs de etapas anteriores
       5. prompt.render(**variaveis)                 -- renderiza prompt com variaveis
       6. cliente.enviar_com_anexos()               -- envia para API com arquivos multimodais
       7. _parsear_resposta()                        -- extrai JSON da resposta textual
       8. _salvar_resultado()                        -- salva JSON como documento no storage
  -> Retorna ResultadoExecucao com todos os campos preenchidos
```

**Caracteristicas:**
- A LLM recebe o prompt completo (de `PROMPTS_PADRAO` em `prompts.py`) com arquivos anexados nativamente
- A resposta eh texto livre contendo JSON
- `_parsear_resposta()` tenta 4 estrategias de parsing: (1) `json.loads()` direto, (2) bloco ````json`, (3) regex `{...}`, (4) aceitar Markdown para `gerar_relatorio`
- O JSON parseado eh salvo diretamente via `_salvar_resultado()`, que faz `json.dump(conteudo)` no storage
- **Os campos `_avisos_documento` e `_avisos_questao` fazem parte do JSON retornado pela LLM** e sao preservados intactos ao salvar

**Onde o JSON eh salvo:**
- `_salvar_resultado()` [executor.py:1834] pega `resposta_parsed` (o dict) e salva como `.json`
- Linha 1883: `conteudo = resposta_parsed if resposta_parsed else {"resposta_raw": resposta_raw}`
- Linha 1886: `json.dump(conteudo, f, ensure_ascii=False, indent=2)`
- Resultado: **todos os campos do dict, incluindo `_avisos_*`, sao preservados no arquivo JSON**

### Path 2: Tool-use (CORRIGIR, ANALISAR, GERAR)

**Fluxo completo:**
```
corrigir() [executor.py:1184]
  -> Prepara variaveis, contexto JSON, renderiza prompt
  -> Concatena prompt_sistema + STAGE_TOOL_INSTRUCTIONS[CORRIGIR]
  -> executar_com_tools() [executor.py:2115]
       1. Resolve modelo via model_manager / ai_registry / env vars
       2. Cria ToolRegistry com create_document + execute_python_code
       3. Cria ToolExecutionContext com atividade_id, aluno_id
       4. ChatClient.chat_with_tools() [chat_service.py:762]
            -> Dispatcha para _chat_anthropic_with_tools / _chat_openai_with_tools / _chat_google_with_tools
            -> Loop de iteracoes:
                a. Envia mensagem + tools para API
                b. Se stop_reason == "tool_use": executa tools via ToolRegistry
                c. Adiciona resultado como mensagem "user" e continua loop
                d. Se stop_reason == "end_turn": retorna
       5. E-T2: Verifica dual-output (JSON + PDF). Se parcial, retry uma vez.
       6. F2-T1: Extrai resposta_raw do conteudo do create_document
       7. F7-T1: PDF auto-fallback se LLM nao chamou execute_python_code
  -> Retorna ResultadoExecucao
```

**Caracteristicas:**
- A LLM recebe 2 tools: `create_document` e `execute_python_code`
- A LLM deve chamar `create_document` com o JSON da correcao/analise
- O handler `handle_create_document()` [tool_handlers.py:581] salva o documento no storage
- **O handler NAO salva o JSON estruturado diretamente** -- ele salva o campo `content` de cada documento como arquivo de texto

**ACHADO CRITICO -- O handler `handle_create_document` descarta campos:**

O handler (tool_handlers.py:624-756) recebe um array `documents[]` onde cada item tem:
- `filename` -- nome do arquivo
- `content` -- conteudo textual
- `document_type` -- tipo do documento
- `description` -- descricao

Na linha 627-628:
```python
content = doc_data.get("content", "")
doc_type_str = doc_data.get("document_type", "other").lower()
```

O `content` eh tratado como **texto livre** e salvo diretamente no arquivo (linhas 650-653):
```python
if ext in ['.txt', '.md', '.csv', '.json']:
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(content)
```

Isso significa que:
1. Se a LLM envia `content` como uma **string JSON** (o texto do JSON), ele sera salvo corretamente como `.json`
2. Se a LLM envia `content` como texto narrativo, o JSON estruturado se perde
3. **Os campos `_avisos_documento` e `_avisos_questao` so serao preservados se a LLM incluir esses campos DENTRO da string `content`**

### Comparacao dos paths

| Aspecto | Path 1 (Multimodal) | Path 2 (Tool-use) |
|---------|---------------------|---------------------|
| **Como JSON eh produzido** | LLM retorna texto, `_parsear_resposta()` extrai dict | LLM chama `create_document` com `content` string |
| **Quem salva o JSON** | `_salvar_resultado()` faz `json.dump(dict)` | `handle_create_document()` faz `f.write(content)` |
| **Preservacao de avisos** | Sim -- dict inteiro eh salvo | Depende -- so se a LLM incluiu no `content` |
| **tokens_entrada populado** | Sim (`resultado.tokens_entrada`) | **NAO** -- `resposta.get("tokens", 0)` eh total, nao split |
| **tokens_saida populado** | Sim (`resultado.tokens_saida`) | **NAO** -- `ResultadoExecucao.tokens_saida` = 0 (default) |
| **resposta_parsed populado** | Sim (dict do JSON) | **NAO** -- `executar_com_tools()` nunca seta `resposta_parsed` |
| **documento_id retornado** | Sim (de `_salvar_resultado()`) | **NAO** -- `executar_com_tools()` nunca seta `documento_id` |
| **Etapa no ResultadoExecucao** | `EtapaProcessamento.CORRIGIR` etc | String literal `"tools"` |
| **Validacao Pydantic** | Sim (se `HAS_VALIDATION`) | NAO -- nao passa por `_parsear_resposta()` |
| **PDF gerado por** | `_gerar_formatos_extras()` (backend) | LLM via `execute_python_code` (E2B sandbox) |

---

## Diagnostico: onde os avisos se perdem

### Contexto

Os campos `_avisos_documento` e `_avisos_questao` sao arrays JSON que cada etapa deve incluir no seu output. Eles sao lidos pelo `visualizador.py` (linha 424-426):

```python
visao.avisos_documento = data.get("_avisos_documento", [])
visao.avisos_questao = data.get("_avisos_questao", [])
visao._avisos_stage = data.get("_avisos_stage", "CORRIGIR")
```

### Onde os avisos funcionam (Path 1 -- EXTRAIR_*)

Para etapas de extracao, o fluxo eh:
1. **Prompt**: `PROMPTS_PADRAO[EXTRAIR_QUESTOES]` inclui `_avisos_documento` e `_avisos_questao` no schema JSON do prompt (prompts.py:192-198)
2. **LLM retorna**: JSON com esses campos
3. **Parse**: `_parsear_resposta()` extrai dict completo
4. **Salvar**: `_salvar_resultado()` faz `json.dump(dict)` -- todos os campos preservados
5. **Ler**: `visualizador._ler_json()` le o arquivo JSON, `data.get("_avisos_documento", [])` funciona

**Resultado: avisos funcionam corretamente para EXTRAIR_*.**

### Onde os avisos se perdem (Path 2 -- CORRIGIR, ANALISAR, GERAR)

Existem **3 pontos de falha** no Path 2:

#### Ponto de falha 1: Dupla fonte de instrucoes (confusao para a LLM)

Para CORRIGIR, a LLM recebe dois conjuntos de instrucoes:

1. **Prompt em `PROMPTS_PADRAO[CORRIGIR]`** (prompts.py:362-412): pede um JSON com campos `nota`, `nota_maxima`, `percentual`, `status`, `feedback`, etc. **NAO inclui `_avisos_documento` nem `_avisos_questao`.**

2. **`STAGE_TOOL_INSTRUCTIONS[CORRIGIR]`** (executor.py:144-184): pede que a LLM use `create_document` com um JSON que **SIM inclui `_avisos_documento` e `_avisos_questao`.**

Esses dois schemas sao **incompativeis**: o prompt pede um JSON flat com `nota` na raiz, e o STAGE_TOOL_INSTRUCTIONS pede um JSON com `nota_final` e `questoes[]`. A LLM recebe ambos concatenados no system prompt (executor.py:1232):
```python
full_system = prompt_sistema + tool_instructions
```

**A LLM pode seguir qualquer um dos dois schemas**, dependendo do provider e modelo. Isso cria inconsistencia.

#### Ponto de falha 2: O handler `handle_create_document` nao parseia JSON

Mesmo que a LLM inclua `_avisos_documento` no JSON que envia como `content` do `create_document`, o handler:
- Trata `content` como string opaca
- Salva no arquivo como texto
- **NAO valida** se o JSON eh valido
- **NAO extrai** campos especificos

Se o visualizador depois le esse arquivo `.json` e faz `json.loads()`, os avisos estarao la **apenas se a LLM os incluiu na string `content`**.

#### Ponto de falha 3: `executar_com_tools()` nao popula `resposta_parsed`

O metodo `executar_com_tools()` (executor.py:2449-2460) retorna:
```python
return ResultadoExecucao(
    sucesso=True,
    etapa="tools",             # <- String, nao EtapaProcessamento
    resposta_raw=raw_content,  # <- Texto extraido do create_document
    provider=model.tipo.value,
    modelo=model.modelo,
    tokens_entrada=resposta.get("tokens", 0),
    tempo_ms=tempo_ms,
    alertas=alertas,
    tentativas=tentativas,
    pdf_fallback_used=pdf_fallback_used,
)
```

**Campos ausentes:**
- `resposta_parsed`: nunca setado (fica `None`)
- `documento_id`: nunca setado (fica `None`)
- `tokens_saida`: nunca setado (fica `0`)
- `prompt_usado`: nunca setado (fica `""`)
- `prompt_id`: nunca setado (fica `""`)

Isso significa que qualquer codigo que dependa de `resultado.resposta_parsed` para acessar avisos **nao vai encontra-los**.

#### Ponto de falha 4: O visualizador le do arquivo JSON salvo pelo handler

O `visualizador.py` nao depende de `resposta_parsed` -- ele le diretamente do arquivo JSON salvo no storage (linhas 280-298, `_ler_json()`). Entao **se o handler salvou o JSON corretamente, o visualizador consegue ler**.

**Mas**: o handler salva via `f.write(content)` onde `content` eh a string que a LLM enviou. Se a LLM seguiu as instrucoes de `STAGE_TOOL_INSTRUCTIONS` e enviou o JSON completo como string `content`, os avisos estarao no arquivo.

#### Resumo do diagnostico

```
Path 1 (EXTRAIR_*):
  LLM -> texto JSON -> _parsear_resposta() -> dict -> _salvar_resultado() -> json.dump() -> arquivo .json
  [avisos preservados em todas as etapas]

Path 2 (CORRIGIR/ANALISAR/GERAR):
  LLM -> tool_call create_document(content="...JSON string...") -> handle_create_document() -> f.write(content) -> arquivo .json
  [avisos dependem de:
    1. LLM ter seguido STAGE_TOOL_INSTRUCTIONS (nao o prompt PROMPTS_PADRAO que nao pede avisos)
    2. LLM ter incluido avisos DENTRO da string content (nao como campos do input_data)
    3. LLM ter gerado JSON valido como content (nao Markdown ou texto)]
```

**Probabilidade de perda**: ALTA para modelos menores (Haiku, GPT-4o-mini) que podem:
- Seguir o schema do PROMPTS_PADRAO (que nao pede avisos) ao inves do STAGE_TOOL_INSTRUCTIONS
- Enviar o JSON como campos do `input_data` do tool call ao inves de como string `content`
- Gerar texto narrativo ao inves de JSON como `content`

---

## Decisoes implicitas sobre providers

### Como o provider eh selecionado

Para Path 2, a resolucao de provider segue esta cadeia (executor.py:2152-2209):

1. `model_manager.get(provider_id)` -- busca em `models.json`
2. Se nao encontrou: `resolve_provider_config(provider_id)` -- tenta `ai_registry`
3. Se nao encontrou: `model_manager.get_default()` -- modelo padrao
4. API key: `api_key_manager.get(model.api_key_id)` -> `get_por_empresa(model.tipo)` -> variavel de ambiente

### Dispatching por provider no tool-use

`ChatClient.chat_with_tools()` (chat_service.py:795-832) dispatcha por `ProviderType`:

| Provider | Metodo | Formato de tools |
|----------|--------|-----------------|
| Anthropic | `_chat_anthropic_with_tools()` | Nativo Anthropic (tools[] no payload) |
| OpenAI | `_chat_openai_with_tools()` | Convertido para OpenAI format via `_convert_tools_to_openai_format()` |
| Google | `_chat_google_with_tools()` | Convertido para Google format |
| Outros | Fallback para `chat()` sem tools | **Tools ignorados silenciosamente** |

**Gate de capability**: antes de chamar `chat_with_tools()`, `executar_com_tools()` verifica `model.suporta_function_calling` (executor.py:2257). Se o modelo nao suporta, retorna erro explicito.

### Conversao de formato de tools

As tools sao definidas em formato Anthropic (`tool.to_anthropic_format()`, executor.py:2226). Para OpenAI, sao convertidas por `_convert_tools_to_openai_format()` (chat_service.py:1148-1160):

```python
{
    "type": "function",
    "function": {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parameters": tool.get("input_schema", {})
    }
}
```

**Risco**: a conversao eh sintatica, nao semantica. Se o input_schema do Anthropic tem tipos ou restricoes que o OpenAI/Google interpreta diferente, pode haver incompatibilidade.

### Diferenca no loop de tool execution

- **Anthropic** (chat_service.py:1028-1126): stop_reason `"tool_use"` ou `"end_turn"`, max 10 iteracoes
- **OpenAI** (chat_service.py:1162+): `finish_reason` `"tool_calls"` ou `"stop"`, mesma logica
- **Google** (chat_service.py): similar, mas com particularidades de formato

Todos usam o mesmo `ToolRegistry.execute()` para rodar os handlers.

### Modelos de reasoning (o3, o4-mini)

Modelos de reasoning tem restricoes especiais (chat_service.py:849-860):
- Nao suportam `temperature`, `top_p`, `presence_penalty`, etc.
- Usam `max_completion_tokens` ao inves de `max_tokens`
- System prompt vai como `"developer"` ao inves de `"system"`
- `parallel_tool_calls` eh filtrado dos params

---

## Verificacoes por arquivo

### executor.py

**O que faz sentido:**
- A separacao entre Path 1 (multimodal com parsing) e Path 2 (tool-use) eh funcional
- O retry de dual-output (E-T2, linhas 2280-2315) eh uma boa defesa contra output parcial
- O PDF fallback (F7-T1, linhas 2363-2447) eh uma boa rede de seguranca
- A validacao de documentos faltantes (linhas 618-659) com erro estruturado eh bem feita

**O que esta errado/incompleto:**
- `executar_com_tools()` retorna `etapa="tools"` (string literal) ao inves do enum `EtapaProcessamento` correto. Isso quebra qualquer logica downstream que dependa de `resultado.etapa` para identificar a etapa real.
- `executar_com_tools()` nunca popula `resposta_parsed`, `documento_id`, `prompt_usado`, `prompt_id`, `tokens_saida`
- `STAGE_TOOL_INSTRUCTIONS` e `PROMPTS_PADRAO` tem schemas conflitantes para CORRIGIR (um pede `nota_final` + `questoes[]`, outro pede `nota`)
- A validacao Pydantic (`HAS_VALIDATION`) so roda no Path 1, nunca no Path 2

### tool_handlers.py

**O que faz sentido:**
- O handler `handle_create_document` eh generico e flexivel -- suporta multiplos formatos de arquivo
- A persistencia no storage com `salvar_documento()` funciona corretamente
- O `expected_document_type` do context eh respeitado

**O que esta errado/incompleto:**
- O handler trata `content` como texto opaco -- nao faz nenhuma validacao de schema JSON
- Para o pipeline, o handler deveria parsear o JSON, validar a presenca de campos obrigatorios (incluindo `_avisos_*`), e rejeitar conteudo invalido
- NAO ha nenhum mecanismo para garantir que `_avisos_documento` e `_avisos_questao` existam no JSON salvo
- O handler nao injeta `_avisos_stage` no JSON (que o visualizador espera, linha 426)

### prompts.py

**O que faz sentido:**
- Os prompts de EXTRAIR_* sao completos: incluem schema JSON com `_avisos_documento`, `_avisos_questao`, codigos de aviso, e instrucao de enviar `[]` quando vazio
- Os prompts de sistema tem contexto pedagogico rico
- Cada prompt tem `texto_sistema` + `texto` separados

**O que esta errado/incompleto:**
- **O prompt PROMPTS_PADRAO[CORRIGIR]** (linhas 362-412) NAO inclui `_avisos_documento` nem `_avisos_questao` no schema JSON. O schema pede `nota`, `feedback`, `pontos_positivos`, etc -- mas nenhum campo de aviso.
- **O prompt PROMPTS_PADRAO[ANALISAR_HABILIDADES]** (linhas 415-472) NAO inclui `_avisos_*`. O schema pede `habilidades`, `recomendacoes`, etc.
- **O prompt PROMPTS_PADRAO[GERAR_RELATORIO]** (linhas 475-519) NAO inclui `_avisos_*`. O schema pede `conteudo`, `resumo_executivo`, etc.
- Esses prompts sao do sistema antigo (Path 1 legado), mas ainda sao usados como base para o Path 2. Os avisos so estao no `STAGE_TOOL_INSTRUCTIONS` que eh concatenado depois.

### chat_service.py

**O que faz sentido:**
- A arquitetura de dispatching por provider eh limpa
- A conversao de formato de tools eh funcional
- O loop de tool execution com max_iterations eh uma boa protecao
- `resolve_provider_config()` tem boa cadeia de fallbacks

**O que esta errado/incompleto:**
- O `_chat_anthropic_with_tools()` nao propaga info de tokens de forma granular (so soma tudo em `total_tokens`)
- Providers que nao suportam tools fazem fallback silencioso para `chat()` sem tools -- isso deveria ser um erro explicito no contexto de pipeline (ja ha o gate E-T1 no executor, entao o fallback em chat_service eh redundante mas nao prejudicial)

### visualizador.py

**O que faz sentido:**
- O sistema de severidade (`get_warning_severity`) eh bem definido com mapeamento stage x code
- A leitura de avisos (linhas 423-426) eh robusta -- usa `.get()` com default `[]`
- Suporta 4 formatos de correcao (STAGE_TOOL_INSTRUCTIONS, nota flat, correcoes[], resposta_raw)
- O campo `dados_incompletos` marca corretamente quando nao ha dados estruturados

**O que esta errado/incompleto:**
- `_processar_analise()` (linhas 428-468) NAO le `_avisos_documento` nem `_avisos_questao` da analise de habilidades. Os avisos so sao lidos de `correcao_data` em `_processar_correcao()`.
- Nao ha leitura de avisos do GERAR_RELATORIO -- o `get_resultado_aluno()` nem carrega esse documento
- O campo `_avisos_stage` nao eh setado pela LLM -- eh hardcoded como `"CORRIGIR"` no default (linha 426). Para ANALISAR_HABILIDADES e GERAR_RELATORIO, a severidade sera calculada com o stage errado.

---

## Achados criticos

1. **Dupla instrucao conflitante**: Para CORRIGIR/ANALISAR/GERAR, a LLM recebe `PROMPTS_PADRAO` (que NAO pede avisos) e `STAGE_TOOL_INSTRUCTIONS` (que pede avisos) concatenados. A LLM pode seguir qualquer um.

2. **`executar_com_tools()` nao popula campos essenciais**: `resposta_parsed`, `documento_id`, `tokens_saida`, `prompt_usado`, `prompt_id` ficam vazios. O campo `etapa` eh a string `"tools"` ao inves do enum correto.

3. **O handler `handle_create_document` eh agnostico ao conteudo**: Ele salva `content` como string sem parsear nem validar. Nao ha garantia de que o JSON salvo contenha `_avisos_documento` ou `_avisos_questao`.

4. **Avisos nao sao lidos de ANALISAR_HABILIDADES**: `_processar_analise()` no visualizador nao le `_avisos_*` -- so `_processar_correcao()` faz isso. Se o JSON de analise contiver avisos, eles serao ignorados.

5. **`_avisos_stage` nunca eh setado corretamente**: O visualizador espera `_avisos_stage` no JSON para calcular severidade, mas nenhuma etapa do pipeline injeta esse campo. O default eh `"CORRIGIR"`, o que gera severidades incorretas para avisos de EXTRAIR_* ou ANALISAR_*.

6. **Path 2 nao passa por `_salvar_resultado()`**: No Path 2, o JSON eh salvo pelo handler da tool (`handle_create_document`), e o executor **nao salva novamente**. Isso significa que o JSON salvo pelo Path 2 nao tem os metadados que `_salvar_resultado()` adicionaria (e.g., versionamento).

7. **Tokens nao sao rastreados no Path 2**: `tokens_entrada` recebe o total de tokens (input+output somados), e `tokens_saida` fica como 0. Nao ha contabilidade precisa de custo para etapas tool-use.

8. **Modelos que nao suportam function calling sao barrados**: O gate E-T1 (executor.py:2257) retorna erro explicito. Mas o campo `suporta_function_calling` eh setado com heuristica (`provider_type in ("openai", "anthropic", "google")`), o que pode bloquear providers validos via OpenRouter/etc.

9. **Retry de dual-output pode gerar duplicatas**: Se o E-T2 retry produz o JSON novamente (alem do PDF), o handler cria dois documentos JSON no storage. Nao ha deduplicacao.

10. **O PROMPTS_PADRAO[GERAR_RELATORIO] nao segue STAGE_TOOL_INSTRUCTIONS format**: O prompt pede um JSON com `conteudo` (Markdown) + `resumo_executivo` + `nota_final`, enquanto o STAGE_TOOL_INSTRUCTIONS pede `resumo_geral` + `pontos_fortes[]` + `areas_melhoria[]` + `recomendacoes[]`. O visualizador espera o formato do STAGE_TOOL_INSTRUCTIONS.
