# Referência de Modelos e Parâmetros - Prova AI

Este documento lista todos os modelos de IA suportados e seus parâmetros.

---

## Classificação de Modelos

### Modelos REASONING (NÃO suportam temperature)
Usam `reasoning_effort` (low/medium/high) e `max_completion_tokens`:
- **OpenAI**: `o3`, `o3-mini`, `o3-pro`, `o4-mini`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5.1`, `gpt-5.2`
- **DeepSeek**: `deepseek-reasoner`

### Modelos STANDARD (suportam temperature)
Todos os outros modelos que aceitam o parâmetro `temperature`.

---

## OpenAI

### Modelos Standard (suportam temperature)

| Modelo | Vision | Tools | Temperature | Max Tokens | Notas |
|--------|--------|-------|-------------|------------|-------|
| gpt-5.2 | ✅ | ✅ | 0-2 | max_tokens | Best model for coding and agentic tasks across industries |
| gpt-5.2-pro | ✅ | ✅ | 0-2 | max_tokens | Version of GPT-5.2 that produces smarter and more precise responses |
| gpt-5 | ✅ | ✅ | 0-2 | max_tokens | Intelligent reasoning model for coding and agentic tasks |
| gpt-5-mini | ✅ | ✅ | 0-2 | max_tokens | Faster, cost-efficient version of GPT-5 for well-defined tasks |
| gpt-5-nano | ✅ | ✅ | 0-2 | max_tokens | Fastest, most cost-efficient version of GPT-5 |
| gpt-5-pro | ✅ | ✅ | 0-2 | max_tokens | Version of GPT-5 that produces smarter and more precise responses |
| gpt-5-image | ✅ | ✅ | 0-2 | max_tokens | State-of-the-art image generation model |
| gpt-4o | ✅ | ✅ | 0-2 | max_tokens | Fast, intelligent, flexible GPT model |
| gpt-4o-mini | ✅ | ✅ | 0-2 | max_tokens | Fast, affordable small model for focused tasks |
| gpt-4.1 | ✅ | ✅ | 0-2 | max_tokens | Smartest non-reasoning model |
| gpt-4.1-mini | ✅ | ✅ | 0-2 | max_tokens | Smaller, faster version of GPT-4.1 |
| gpt-4.1-nano | ✅ | ✅ | 0-2 | max_tokens | Cost-efficient version of GPT-4.1 |

### Modelos Reasoning (NÃO suportam temperature)

| Modelo | Tools | Reasoning Effort | Max Tokens | Notas |
|--------|-------|------------------|------------|-------|
| o3 | ✅ | low/medium/high | max_completion_tokens | Reasoning model for complex tasks, succeeded by GPT-5 |
| o3-mini | ✅ | low/medium/high | max_completion_tokens | Small model alternative to o3 |
| o3-pro | ✅ | low/medium/high | max_completion_tokens | Version of o3 with more compute for better responses |
| o4-mini | ✅ | low/medium/high | max_completion_tokens | Fast, cost-efficient reasoning model, succeeded by GPT-5 mini |
| gpt-5 | ✅ | low/medium/high | max_completion_tokens | Intelligent reasoning model with configurable reasoning effort |
| gpt-5-mini | ✅ | low/medium/high | max_completion_tokens | Cost-efficient reasoning version |
| gpt-5-nano | ✅ | low/medium/high | max_completion_tokens | Fastest reasoning version |
| gpt-5.1 | ✅ | low/medium/high | max_completion_tokens | Previous intelligent reasoning model |
| gpt-5.2 | ✅ | low/medium/high | max_completion_tokens | Most advanced reasoning model |

**Parâmetros NÃO suportados em modelos reasoning:**
- `temperature`
- `top_p`
- `frequency_penalty`
- `presence_penalty`
- `logit_bias`
- `parallel_tool_calls`

---

## Anthropic (Claude)

| Modelo | Vision | Tools | Temperature | Extended Thinking | Notas |
|--------|--------|-------|-------------|-------------------|-------|
| claude-opus-4-5-20251101 | ✅ | ✅ | 0-1 | ✅ | Premium model combining maximum intelligence with practical performance |
| claude-sonnet-4-5-20250929 | ✅ | ✅ | 0-1 | ✅ | Smart model for complex agents and coding |
| claude-haiku-4-5-20251001 | ✅ | ✅ | 0-1 | ✅ | Fastest model with near-frontier intelligence |
| claude-3-5-sonnet-20241022 | ✅ | ✅ | 0-1 | ❌ | Legacy model |
| claude-3-5-haiku-20241022 | ✅ | ✅ | 0-1 | ❌ | Legacy model |

**Parâmetros específicos:**
- `temperature`: 0-1 (padrão: 0.7)
- `max_tokens`: máximo de tokens na resposta
- `system`: prompt de sistema (separado das mensagens)
- Headers: `x-api-key`, `anthropic-version: 2023-06-01`

**Suporte a arquivos nativos:**
- PDFs: tipo `document` com base64
- Imagens: tipo `image` com base64

---

## Google (Gemini)

| Modelo | Vision | Tools | Temperature | Reasoning | Notas |
|--------|--------|-------|-------------|-----------|-------|
| gemini-3-pro | ✅ | ✅ | 0-2 | ✅ | Most intelligent model, multimodal understanding, agentic and coding |
| gemini-3-flash | ✅ | ✅ | 0-2 | ✅ | Balanced model for speed, scale, and frontier intelligence |
| gemini-3-ultra | ✅ | ✅ | 0-2 | ✅ | Ultra-capable version |
| gemini-2.5-pro | ✅ | ✅ | 0-2 | ✅ | Advanced thinking model for reasoning, math, and STEM |
| gemini-2.5-flash | ✅ | ✅ | 0-2 | ✅ | Best price-performance, thinking, and agentic use cases |
| gemini-2.5-flash-lite | ✅ | ❌ | 0-2 | ❌ | Fastest, cost-efficient version |
| gemini-2.0-flash | ✅ | ✅ | 0-2 | ❌ | Legacy model |

**Parâmetros específicos:**
- `temperature`: vai em `generationConfig`
- `maxOutputTokens`: vai em `generationConfig`
- `systemInstruction`: prompt de sistema separado
- Header: `x-goog-api-key`

**Suporte a arquivos nativos:**
- PDFs: `inline_data` com base64
- Imagens: `inline_data` com base64
- Vídeo e áudio também suportados

---

## DeepSeek

| Modelo | Temperature | Tipo | Notas |
|--------|-------------|------|-------|
| deepseek-chat | ✅ 0-2 | Standard | Chat geral |
| deepseek-reasoner | ❌ | Reasoning | Chain of thought (R1) |

---

## Mistral

| Modelo | Tools | Temperature | Notas |
|--------|-------|-------------|-------|
| mistral-large-latest | ✅ | 0-1 | Mais capaz |
| mistral-small-latest | ✅ | 0-1 | Leve |
| codestral-latest | ✅ | 0-1 | Código |

---

## Groq

| Modelo | Tools | Temperature | Notas |
|--------|-------|-------------|-------|
| llama-3.3-70b-versatile | ✅ | ✅ | Llama 3.3 |
| mixtral-8x7b-32768 | ✅ | ✅ | Mixtral |

---

## xAI (Grok)

| Modelo | Vision | Tools | Temperature | Notas |
|--------|--------|-------|-------------|-------|
| grok-4 | ✅ | ✅ | ✅ | Flagship |
| grok-4-fast | ✅ | ✅ | ✅ | Rápido |

---

## Perplexity

| Modelo | Search | Temperature | Notas |
|--------|--------|-------------|-------|
| sonar | ✅ | ✅ | Busca integrada |
| sonar-pro | ✅ | ✅ | Pro |
| sonar-deep-research | ✅ | ✅ | Pesquisa profunda |

**Nota:** Perplexity não suporta function calling.

---

## Cohere

| Modelo | Tools | RAG | Temperature | Notas |
|--------|-------|-----|-------------|-------|
| command-r-plus | ✅ | ✅ | ✅ | Mais capaz |
| command-r | ✅ | ✅ | ✅ | Leve |

---

## OpenRouter

Proxy para múltiplos modelos:

| Modelo | Notas |
|--------|-------|
| openai/gpt-4o | GPT-4o via OpenRouter |
| anthropic/claude-3.5-sonnet | Claude via OpenRouter |
| meta-llama/llama-3.1-405b-instruct | Llama 405B |

---

## Modelos Locais

### Ollama

| Modelo | Vision | Notas |
|--------|--------|-------|
| llama3.2 | ✅ | Multimodal |
| llama3.1 | ❌ | |
| mistral | ❌ | |
| codellama | ❌ | Código |
| mixtral | ❌ | |

### vLLM / LM Studio

Configuração customizada via `base_url`.

---

## Referência Rápida de Código

### Verificar se é modelo reasoning:
```python
from anexos import is_reasoning_model, REASONING_MODELS

# REASONING_MODELS = ['o3', 'o3-mini', 'o3-pro', 'o4-mini', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'gpt-5.1', 'gpt-5.2', 'deepseek-reasoner']  # Updated to current models

if is_reasoning_model(model_id):
    # Usar max_completion_tokens, reasoning_effort
    # NÃO usar temperature
else:
    # Usar max_tokens, temperature
```

### Construir payload OpenAI:
```python
if is_reasoning:
    payload["max_completion_tokens"] = max_tokens
    if reasoning_effort:
        payload["reasoning_effort"] = reasoning_effort
else:
    payload["temperature"] = temperature
    payload["max_tokens"] = max_tokens
```

### Construir payload Anthropic:
```python
payload = {
    "model": model,
    "max_tokens": max_tokens,
    "temperature": temperature,  # 0-1
    "messages": messages
}
if system_prompt:
    payload["system"] = system_prompt
```

### Construir payload Google:
```python
payload = {
    "contents": contents,
    "generationConfig": {
        "temperature": temperature,
        "maxOutputTokens": max_tokens
    }
}
if system_prompt:
    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
```

---

## Arquivos Relevantes

- `ai_providers.py`: Implementação dos providers
- `chat_service.py`: Gerenciamento de modelos e configurações
- `anexos.py`: Sistema multimodal e constantes REASONING_MODELS
- `data/model_catalog.json`: Catálogo de modelos com metadados
