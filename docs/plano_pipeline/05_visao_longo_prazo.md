# Visao de Longo Prazo -- NOVO CR

> Direcao estrategica do projeto alem das correcoes imediatas: rastreamento de custos,
> roadmap de providers e otimizacoes de escala.
>
> Ultima atualizacao: 2026-04-17

---

## 1. Rastreamento de custos de tokens

### 1.1 Dados ja existentes no codigo

O pipeline atual **ja captura** contagem de tokens em varias camadas, mas de forma
inconsistente. A tabela abaixo resume o estado real do codigo (verificado em 2026-04-17):

| Caminho | Campo | Populado? | Fonte dos dados |
|---------|-------|-----------|-----------------|
| `executor.py` L75-76 -- `ResultadoExecucao` dataclass | `tokens_entrada`, `tokens_saida` | Declarados como `int = 0` | Preenchidos nos caminhos abaixo |
| `executor.py` L580-581 -- caminho `_executar_etapa` (provider legado via `ai_providers.py`) | `tokens_entrada = response.input_tokens` | Sim | `AIResponse.input_tokens` |
| | `tokens_saida = response.output_tokens or response.tokens_used` | Sim (com fallback) | `AIResponse.output_tokens` |
| `executor.py` L857-858 -- caminho `_executar_multimodal` (via `anexos.py`) | `tokens_entrada = resultado.tokens_entrada` | Sim | `ResultadoEnvio.tokens_entrada` (de `anexos.py`) |
| | `tokens_saida = resultado.tokens_saida` | Sim | `ResultadoEnvio.tokens_saida` |
| `executor.py` L2455 -- caminho `executar_com_tools` (via `chat_service.py`) | `tokens_entrada = resposta.get("tokens", 0)` | **PARCIAL** -- soma total, nao input separado | `ChatClient` retorna `"tokens"` como total |
| | `tokens_saida` | **NAO POPULADO** (fica 0) | Campo nao preenchido neste caminho |
| `anexos.py` L680-682 -- OpenAI | `tokens_entrada`, `tokens_saida` | Sim | `usage.prompt_tokens`, `usage.completion_tokens` |
| `anexos.py` L792-793 -- Anthropic | `tokens_entrada`, `tokens_saida` | Sim | `usage.input_tokens`, `usage.output_tokens` |
| `anexos.py` L888-889 -- Google | `tokens_entrada`, `tokens_saida` | Sim | `usageMetadata.promptTokenCount`, `usageMetadata.candidatesTokenCount` |
| `ai_providers.py` -- OpenAIProvider | `input_tokens`, `output_tokens` | Sim | `usage.prompt_tokens`, `usage.completion_tokens` |
| `ai_providers.py` -- AnthropicProvider | `input_tokens`, `output_tokens` | Sim | `usage.input_tokens`, `usage.output_tokens` |
| `ai_providers.py` -- GeminiProvider | `input_tokens`, `output_tokens` | Sim | `usageMetadata.promptTokenCount`, `usageMetadata.candidatesTokenCount` |
| `ai_providers.py` -- LocalLLMProvider (Ollama) | `input_tokens`, `output_tokens` | Sim | `prompt_eval_count`, `eval_count` |
| `chat_service.py` -- `_chat_openai` | `"tokens"` (total) | **Apenas total** | `usage.total_tokens` |
| `chat_service.py` -- `_chat_anthropic` | `"tokens"` (total) | **Apenas total** | `input_tokens + output_tokens` somados |
| `chat_service.py` -- tool loops (Anthropic/OpenAI/Google) | `total_tokens` acumulado | **Apenas total acumulado** | Soma iterativa no loop |

### 1.2 Gaps identificados

1. **`executar_com_tools` nao popula `tokens_saida`** (L2449-2460 de `executor.py`).
   Apenas `tokens_entrada` recebe o total via `resposta.get("tokens", 0)`, e `tokens_saida`
   fica zero. Isso significa que toda execucao via tool-use (a maioria das etapas CORRIGIR,
   ANALISAR_HABILIDADES, GERAR_RELATORIO) **perde a granularidade input/output**.

2. **`ChatClient` retorna apenas `"tokens"` como total.** Os metodos `_chat_openai`,
   `_chat_anthropic`, etc. em `chat_service.py` descartam a separacao input/output e
   retornam so a soma. Precisam retornar `"input_tokens"` e `"output_tokens"` separados.

3. **Nenhum registro persistente de custos.** Os tokens sao retornados no `ResultadoExecucao`
   e aparecem nos logs/resposta da API, mas nao sao gravados em nenhum banco ou arquivo.
   Nao ha como consultar "quanto gastei no mes passado".

4. **Precificacao nao e aplicada automaticamente.** O `model_catalog.json` tem precos por
   1M tokens, e `ModelCatalogManager.calculate_cost()` existe, mas nunca e chamado
   pelo pipeline de execucao.

5. **Cached input tokens nao sao rastreados.** Anthropic e OpenAI retornam tokens de cache
   separados, mas nenhum caminho do codigo os captura.

### 1.3 Arquitetura proposta

#### 1.3.1 Modelo de dados (TokenUsageRecord)

```python
@dataclass
class TokenUsageRecord:
    id: str                    # UUID
    timestamp: datetime

    # Contexto educacional
    materia_id: str
    turma_id: str
    atividade_id: str
    aluno_id: Optional[str]    # None para etapas de turma (EXTRAIR_QUESTOES, EXTRAIR_GABARITO)

    # Execucao
    etapa: str                 # "EXTRAIR_QUESTOES", "CORRIGIR", etc.
    provider: str              # "openai", "anthropic", "google"
    modelo: str                # "claude-haiku-4-5-20251001"

    # Tokens
    tokens_entrada: int
    tokens_saida: int
    tokens_cache_leitura: int  # cached_input (se disponivel)
    tokens_cache_escrita: int  # cache_creation (se disponivel)

    # Custo
    custo_entrada_usd: float   # tokens_entrada * preco_input / 1M
    custo_saida_usd: float     # tokens_saida * preco_output / 1M
    custo_total_usd: float     # soma

    # Performance
    tempo_ms: float
    tentativas: int
    sucesso: bool
```

#### 1.3.2 Armazenamento

**Fase 1 (imediata):** Arquivo JSON local em `data/token_usage/YYYY-MM.json`, um por mes.
Simples, sem dependencias, funciona no Render free tier. Estimativa: ~200 bytes por registro,
~1000 execucoes/mes = ~200 KB/mes.

**Fase 2 (quando justificar):** Tabela Supabase `token_usage` com o mesmo schema.
Habilita queries SQL, dashboards, e acesso multi-instancia. Migrar o acumulado dos JSONs.

**Estrutura do JSON (Fase 1):**
```json
{
  "version": "1.0",
  "records": [
    {
      "id": "uuid",
      "timestamp": "2026-04-17T14:30:00Z",
      "materia_id": "...",
      "turma_id": "...",
      "atividade_id": "...",
      "aluno_id": "...",
      "etapa": "CORRIGIR",
      "provider": "anthropic",
      "modelo": "claude-haiku-4-5-20251001",
      "tokens_entrada": 2500,
      "tokens_saida": 1200,
      "tokens_cache_leitura": 0,
      "tokens_cache_escrita": 0,
      "custo_entrada_usd": 0.0025,
      "custo_saida_usd": 0.006,
      "custo_total_usd": 0.0085,
      "tempo_ms": 3400,
      "tentativas": 1,
      "sucesso": true
    }
  ]
}
```

#### 1.3.3 Calculo de custos

**Fonte de precos:** `data/model_catalog.json` (ja existente, campos `input_cost` e
`output_cost` por 1M tokens).

**Formula:**
```
custo_entrada = tokens_entrada * (input_cost / 1_000_000)
custo_saida   = tokens_saida   * (output_cost / 1_000_000)
custo_cache   = tokens_cache_leitura * (cached_input_cost / 1_000_000)  # se disponivel
custo_total   = custo_entrada + custo_saida + custo_cache
```

O `ModelCatalogManager.calculate_cost()` ja implementa essa logica -- basta chamar
apos cada execucao e gravar o resultado.

#### 1.3.4 API endpoints propostos

| Endpoint | Metodo | Descricao |
|----------|--------|-----------|
| `/api/custos/materia/{materia_id}` | GET | Custo total e por etapa de uma materia |
| `/api/custos/turma/{turma_id}` | GET | Custo total de uma turma |
| `/api/custos/atividade/{atividade_id}` | GET | Custo detalhado de uma atividade (por aluno, por etapa) |
| `/api/custos/resumo` | GET | Resumo geral: custo por mes, por provider, por modelo |
| `/api/custos/provider/{tipo}` | GET | Custo acumulado por provider |
| `/api/custos/periodo` | GET | Custo entre `?inicio=` e `?fim=` |

Todos retornam JSON com campos: `total_usd`, `tokens_entrada`, `tokens_saida`,
`num_execucoes`, `detalhamento[]`.

### 1.4 Precificacao por modelo (referencia)

Dados do `model_catalog.json` (versao 2026.01, atualizado 2026-01-28).
**Precos em USD por 1M tokens.**

#### Modelos recomendados para o pipeline educacional

| Modelo | Provider | Input | Output | Cache Input | Uso recomendado |
|--------|----------|-------|--------|-------------|-----------------|
| claude-haiku-4-5 | Anthropic | $1.00 | $5.00 | -- | **EXTRAIR**, CORRIGIR (questoes simples) |
| gemini-2.5-flash | Google | $0.15 | $0.60 | -- | **EXTRAIR** (mais barato com vision) |
| gemini-3-flash-preview | Google | $0.30 | $1.20 | -- | CORRIGIR, ANALISAR (custo/beneficio) |
| gpt-5-nano | OpenAI | $0.05 | $0.40 | $0.005 | **EXTRAIR** (ultra-economico) |
| gpt-5-mini | OpenAI | $0.25 | $2.00 | $0.025 | CORRIGIR, ANALISAR |
| claude-sonnet-4-5 | Anthropic | $3.00 | $15.00 | -- | GERAR_RELATORIO (qualidade alta) |
| gpt-5 | OpenAI | $1.25 | $10.00 | $0.125 | GERAR_RELATORIO (alternativa) |

#### Estimativa de custo por prova (30 alunos, 10 questoes)

Supondo ~3000 tokens de entrada e ~1500 de saida por etapa por aluno:

| Cenario | Modelo pipeline | Custo estimado |
|---------|----------------|----------------|
| Ultra-economico | gpt-5-nano em todas etapas | ~$0.04 |
| Economico | gemini-2.5-flash (extrair) + gemini-3-flash (corrigir/analisar) | ~$0.12 |
| Equilibrado | haiku-4.5 (extrair) + sonnet-4.5 (corrigir) + haiku-4.5 (relatorio) | ~$0.55 |
| Premium | gpt-5 (todas etapas) | ~$1.05 |

---

## 2. Roadmap de providers

### 2.1 Estado atual

| Provider | ProviderType | Implementado em | Chat | Tool-use | Multimodal (anexos) | Testado em producao? |
|----------|-------------|-----------------|------|----------|---------------------|---------------------|
| OpenAI | `OPENAI` | `ai_providers.py`, `chat_service.py`, `anexos.py` | Sim | Sim | Sim (PDF, imagens) | Sim |
| Anthropic | `ANTHROPIC` | `ai_providers.py`, `chat_service.py`, `anexos.py` | Sim | Sim | Sim (PDF, imagens) | Sim |
| Google Gemini | `GOOGLE` | `ai_providers.py`, `chat_service.py`, `anexos.py` | Sim | Sim | Sim (PDF, imagens, video, audio) | Sim |
| Ollama (local) | `OLLAMA` | `ai_providers.py`, `chat_service.py` | Sim | Nao | Nao | Parcial |
| OpenRouter | `OPENROUTER` | `chat_service.py` (compat. OpenAI) | Sim | Sim | Nao | Parcial |
| Groq | `GROQ` | `chat_service.py` (compat. OpenAI) | Sim | Sim | Nao | Nao |
| Mistral | `MISTRAL` | `chat_service.py` (compat. OpenAI) | Sim | Sim | Nao | Nao |
| DeepSeek | `DEEPSEEK` | Catalogo apenas | Nao* | Nao | Nao | Nao |
| xAI (Grok) | `XAI` | Catalogo apenas | Nao* | Nao | Nao | Nao |
| Perplexity | `PERPLEXITY` | Catalogo apenas | Nao* | Nao | Nao | Nao |
| Cohere | `COHERE` | Catalogo apenas | Nao* | Nao | Nao | Nao |
| vLLM | `VLLM` | Catalogo apenas | Nao | Nao | Nao | Nao |
| LM Studio | `LMSTUDIO` | Catalogo apenas | Nao | Nao | Nao | Nao |

*Providers com compat. OpenAI (`DEEPSEEK`, `XAI`) provavelmente funcionam via
`_chat_openai_compatible` mas nao foram validados.

### 2.2 Rio 3.0 (PAUSADO)

**Status atualizado em 2026-04-17:** ja ha fontes publicas e model cards no
Hugging Face para a familia Rio. A nota dedicada cataloga `Rio-3.0-Open`,
`Rio-3.0-Open-Search`, `Rio-3.0-Open-Mini`, `Rio-3.0-Open-Nano`,
`Rio-2.5-Open` e `Rio-2.5-Open-VL`:
`docs/plano_pipeline/rio3_pausado/rio3_provider_research.md`.

O provider Rio 3.0 segue como requisito futuro do projeto, mas agora a pergunta
nao e mais "existe especificacao?", e sim: qual endpoint sera usado, se ele e
OpenAI-compatible, e se suporta tool calling suficiente para o Path 2 do
pipeline.

Escopo combinado: documentar todos os modelos Rio possiveis, mas a primeira
bateria de testes deve rodar apenas com Rio Open Mini. O nome de modelo usado no
payload deve vir da listagem real do endpoint (`/v1/models` ou equivalente), nao
de inferencia a partir do Hugging Face.

**Reorientacao 2026-04-17 -- site oficial primeiro:** a frente Rio 3 nao deve
ser considerada destravada por um cadastro local/dev. O alvo operacional e o
site oficial no Render. O caminho aceito para chave real, enquanto nao houver
admin gate no site publico, e provisionamento por secrets do Render
(`RIO3_API_KEY`, `RIO3_BASE_URL`, `RIO3_MODEL_ID`) e sincronizacao server-side.
Qualquer popup publico para colar chave fica bloqueado ate existir autenticacao,
autorizacao e restricao de CORS/origem para rotas de settings.

Consolidacao operacional: Rio 3 continua como frente futura relevante, mas so
vira progresso real quando estiver no Render/site oficial. O popup local e
apenas ferramenta de desenvolvimento; segredo real nao deve aparecer em chat,
docs, logs, URL ou resposta de terminal. Este documento registra somente estado,
gates e decisoes operacionais, nunca valores de chave.

**Estado aprovado em 2026-04-17:** a frente Rio 3 esta aprovada somente no
caminho oficial Render/site oficial. A chave real deve ser cadastrada pelo
Render Dashboard ou por secrets/env server-side equivalentes; popup publico
continua bloqueado enquanto nao houver admin gate, autorizacao e CORS/origem
restritos para settings. O primeiro smoke deve provar apenas chat simples com
JSON valido usando Rio Open Mini. Rio Open Mini e o unico alvo da bateria
inicial; Nano fica apenas documentado. Tool calling ainda nao foi validado e nao
deve ser assumido como disponivel.

**O que precisamos saber para integrar:**
1. URL base da API
2. Formato da API (OpenAI-compatible? Formato proprio?)
3. Model ID(s) disponiveis
4. Capacidades: vision? tool-use? JSON mode? streaming?
5. Limites: context window, max output, rate limits
6. Autenticacao: API key? OAuth? Certificado?
7. Precificacao (ou se e gratuito para orgaos publicos)

**Proximos passos prioritarios:**

Pausa 2026-04-28: por decisao do usuario, estes passos ficam congelados ate a
documentacao principal da pipeline estar saneada.

1. Confirmar o caminho oficial do site Render para provisionar `RIO3_*`.
2. Descobrir o alias real do Rio Open Mini via `/v1/models` ou equivalente, sem
   expor a chave.
3. Validar chat simples/JSON com Rio Open Mini no site oficial.
4. So depois decidir se a integracao fica como `ProviderType.CUSTOM`
   OpenAI-compatible ou evolui para provider proprio `RIO3`.

**Como adicionar quando as informacoes estiverem disponiveis:**

O sistema ja suporta `ProviderType.CUSTOM` (definido em `chat_service.py` L51).
O caminho `CUSTOM` no `ChatClient.chat()` faz fallback para formato OpenAI (L759-760):

```python
else:
    # Custom - tenta formato OpenAI
    return await self._chat_openai(mensagem, historico, system)
```

**Checklist de implementacao:**

- [ ] Obter/confirmar documentacao tecnica do endpoint Rio usado no NOVO CR
- [ ] Definir o fluxo de producao no Render antes de qualquer teste com chave real
- [ ] Configurar Rio Open Mini por secrets do Render, nao por popup publico
- [ ] Testar manualmente contra o endpoint oficial para confirmar formato da API
- [ ] Descobrir o alias real com `/v1/models` ou equivalente e registrar na nota
  Rio pausada
- [ ] Se formato OpenAI: adicionar Rio Open Mini como `ProviderType.CUSTOM` com `base_url` e `api_key_id`
- [ ] Se formato proprio: criar `_chat_rio3()` em `chat_service.py` e `RioProvider` em `ai_providers.py`
- [ ] Adicionar a familia Rio ao `model_catalog.json` com precos (ou $0.00 se gratuito), mantendo Rio Open Mini como unico alvo inicial de teste
- [ ] Adicionar suporte multimodal em `anexos.py` (se necessario)
- [ ] Testar no site oficial apenas com Rio Open Mini antes de qualquer outro Rio
- [ ] Documentar capacidades e limitacoes

### 2.3 Providers futuros

**Prioridade alta (ja tem infraestrutura):**
- DeepSeek: excelente custo-beneficio ($0.28/$0.42 por 1M), API OpenAI-compatible.
  Basta validar que `_chat_openai_compatible` funciona. Sem vision = limitado a CORRIGIR com texto.

**Prioridade media (util mas nao urgente):**
- Groq: latencia ultra-baixa, bom para etapas simples (EXTRAIR).
  Ja configurado como OpenAI-compatible.
- Mistral: alternativa europeia, pode ser relevante para LGPD.

**Prioridade baixa (nice-to-have):**
- xAI (Grok): sem vantagem clara sobre OpenAI/Anthropic para uso educacional.
- Perplexity: focado em search, nao alinhado com pipeline de correcao.
- Cohere: RAG nativo interessante mas pipeline nao usa RAG.
- vLLM/LM Studio: relevante se houver deploy on-premise.

---

## 3. Otimizacoes futuras

### 3.1 Selecao de modelo por etapa

O pipeline tem 6 etapas com complexidades diferentes. Usar o mesmo modelo para todas
e desperdicio. Proposta:

| Etapa | Complexidade | Modelo recomendado | Justificativa |
|-------|-------------|-------------------|---------------|
| EXTRAIR_QUESTOES | Baixa (OCR + lista) | gemini-2.5-flash ou gpt-5-nano | Vision barato, output estruturado simples |
| EXTRAIR_GABARITO | Baixa (OCR + lista) | gemini-2.5-flash ou gpt-5-nano | Idem |
| EXTRAIR_RESPOSTAS | Media (OCR + interpretacao) | gemini-3-flash-preview ou haiku-4.5 | Precisa interpretar caligrafia |
| CORRIGIR | Alta (julgamento + justificativa) | claude-sonnet-4-5 ou gpt-5 | Qualidade do feedback importa |
| ANALISAR_HABILIDADES | Media (mapeamento BNCC) | haiku-4.5 ou gpt-5-mini | Mapeamento sistematico, nao criativo |
| GERAR_RELATORIO | Alta (redacao coesa) | claude-sonnet-4-5 ou gpt-5 | Qualidade textual importa para o professor |

**Economia estimada vs modelo unico (gpt-5 em tudo):**
- Modelo unico: ~$1.05 por prova (30 alunos)
- Mix otimizado: ~$0.40 por prova (30 alunos)
- **Economia: ~60%**

**Implementacao:** Adicionar campo `modelo_preferido` por etapa na configuracao da
atividade ou materia. Se nao definido, usar o provider padrao.

### 3.2 Cache de resultados

Etapas de turma (EXTRAIR_QUESTOES, EXTRAIR_GABARITO) produzem o mesmo resultado
para todos os alunos. Hoje sao executadas uma vez, mas se falhar e reexecutar, paga-se
novamente.

**Proposta:**
- Cachear resultado de etapas de turma em `data/cache/{atividade_id}/{etapa}.json`
- TTL: 24h (questoes nao mudam)
- Invalidar se o arquivo da prova for atualizado

### 3.3 Prompt caching (Anthropic/OpenAI)

Anthropic oferece `cached_input_cost` a ~10% do preco normal. OpenAI tem sistema similar.
Para turmas com 30+ alunos usando o mesmo gabarito:

- O system prompt + questoes/gabarito sao identicos para todos os alunos
- Apenas a resposta do aluno muda
- Com cache ativo: o prompt base (possivelmente 80% dos tokens de entrada) custa 10x menos

**Economia potencial:** Para CORRIGIR com 30 alunos e ~2000 tokens de prompt base:
- Sem cache: 30 * 2000 * $3.00/1M = $0.18 (so entrada)
- Com cache: 1 * 2000 * $3.00/1M + 29 * 2000 * $0.30/1M = $0.02
- **Economia: ~89% nos tokens de entrada**

**Implementacao:** Requer mudancas em `chat_service.py` para enviar blocos com `cache_control`
(Anthropic) ou usar o endpoint de caching (OpenAI).

### 3.4 Batching

Para turmas grandes, executar todas as correcoes em paralelo sobrecarrega rate limits.
Implementar fila com concorrencia limitada (3-5 chamadas simultaneas) e backoff
exponencial automatico (ja parcialmente implementado em `anexos.py` com `RetryConfig`).

---

## 4. Verificacoes realizadas

Resumo do que foi verificado em cada arquivo para produzir este documento:

| Arquivo | O que foi verificado | Resultado |
|---------|---------------------|-----------|
| `executor.py` L58-98 | Dataclass `ResultadoExecucao` | `tokens_entrada` e `tokens_saida` declarados como `int = 0` |
| `executor.py` L580-581 | Caminho legado (`_executar_etapa`) | Tokens preenchidos corretamente de `AIResponse` |
| `executor.py` L857-858 | Caminho multimodal (`_executar_multimodal`) | Tokens preenchidos de `ResultadoEnvio` |
| `executor.py` L2449-2460 | Caminho tool-use (`executar_com_tools`) | **GAP:** `tokens_entrada` recebe total, `tokens_saida` fica 0 |
| `model_catalog.py` | Schema `ModelMetadata` | Campos `input_cost`, `output_cost`, `cached_input_cost` presentes |
| `data/model_catalog.json` | Precos dos modelos | Versao 2026.01 -- precisa atualizar para modelos lancados apos Jan 2026 |
| `chat_service.py` | `ChatClient.chat()` e dispatch por provider | `CUSTOM` faz fallback para formato OpenAI |
| `chat_service.py` | Retorno de tokens nos metodos `_chat_*` | **GAP:** Retorna apenas `"tokens"` (total), nao separa input/output |
| `anexos.py` | `ClienteAPIMultimodal` -- 3 providers | OpenAI, Anthropic, Google: todos capturam input/output separados corretamente |
| `ai_providers.py` | `AIResponse` dataclass e providers | `input_tokens`/`output_tokens` preenchidos corretamente em todos os providers |
| `ai_providers.py` | `AIProviderRegistry` | Sistema legado de registro, funcional mas menos flexivel que `chat_service.py` |

---

## 5. Ordem de implementacao recomendada

### Fase 1 -- Corrigir gaps (1-2 dias, custo zero)

1. **Separar input/output tokens no `ChatClient`.**
   Alterar `_chat_openai`, `_chat_anthropic`, `_chat_google` em `chat_service.py`
   para retornar `"input_tokens"` e `"output_tokens"` alem de `"tokens"`.

2. **Corrigir `executar_com_tools` em `executor.py`.**
   Usar os novos campos para popular `tokens_entrada` e `tokens_saida` separadamente
   no `ResultadoExecucao`.

### Fase 2 -- Registro de custos (2-3 dias)

3. **Criar `TokenUsageRecord` e servico de gravacao.**
   Gravar em JSON local (`data/token_usage/YYYY-MM.json`) apos cada execucao de etapa.

4. **Calcular custo automaticamente.**
   Chamar `ModelCatalogManager.calculate_cost()` ou formula direta usando precos do
   catalogo e gravar `custo_total_usd` no registro.

5. **Criar endpoints `/api/custos/*`.**
   Implementar leitura dos JSONs e agregacao para os endpoints propostos.

### Fase 3 -- Otimizacoes (1-2 semanas, sob demanda)

6. **Modelo por etapa.**
   Adicionar configuracao de modelo preferido por etapa e implementar selecao automatica.

7. **Prompt caching (Anthropic).**
   Implementar `cache_control` para o bloco system+gabarito em etapas por aluno.

8. **Atualizar `model_catalog.json`.**
   Revisar precos para modelos lancados apos Jan 2026, adicionar novos modelos.

### Fase 4 -- Integracao Rio 3.0 (quando disponivel)

9. **Integrar Rio 3.0 no site oficial** seguindo o checklist da secao 2.2.
   O criterio de pronto nao e "funciona localmente"; e "esta provisionado no
   Render, sem chave em chat/log/popup publico, e testado no caminho real do
   site oficial".

### Fase 5 -- Escala (quando volume justificar)

10. **Migrar token_usage para Supabase.**
11. **Dashboard de custos no frontend.**
12. **Batching com fila e concorrencia controlada.**
