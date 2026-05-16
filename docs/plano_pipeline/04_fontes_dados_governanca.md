# Fontes de Dados e Governanca

Catalogo exaustivo de todas as fontes de dados, schemas, configuracoes de modelos e regras de governanca do NOVO CR.
Documento gerado em 2026-04-17, verificado contra os arquivos-fonte do repositorio.

**Arquivos-fonte verificados:**

| Arquivo | Descricao |
|---------|-----------|
| `backend/data/models.json` | Modelos de IA configurados para uso no sistema |
| `backend/data/providers.json` | Providers registrados (legado, so Ollama) |
| `backend/data/model_catalog.json` | Catalogo completo de metadados, precos e capabilities |
| `backend/models.py` | Dataclasses Python, enums, framework de erros |
| `backend/migrations/001_create_tables.sql` | DDL PostgreSQL (Supabase) |
| `backend/model_catalog.py` | Gerenciador do catalogo de modelos |
| `backend/visualizador.py` | Sistema de avisos e visualizacao de resultados |
| `backend/chat_service.py` | ProviderType enum, DEFAULT_URLS, MODELOS_SUGERIDOS, ApiKeyManager |

---

## 1. Banco de Dados (Supabase / PostgreSQL)

### 1.1 Hierarquia de Entidades

```
Materia
  └── Turma (N por materia)
        ├── Aluno (N:M via alunos_turmas)
        └── Atividade (N por turma)
              └── Documento (N por atividade, opcionalmente vinculado a aluno)
```

Relacao aluno-turma e many-to-many via tabela de juncao `alunos_turmas`.

### 1.2 Tabelas e Campos

#### `materias`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | Identificador unico |
| nome | TEXT NOT NULL | -- | Nome da materia |
| descricao | TEXT | NULL | Descricao opcional |
| nivel | TEXT | 'outro' | Enum: fundamental_1, fundamental_2, medio, superior, outro |
| criado_em | TIMESTAMPTZ | NOW() | Data de criacao |
| atualizado_em | TIMESTAMPTZ | NOW() | Ultima atualizacao |
| metadata | JSONB | '{}' | Dados extras livres |

#### `turmas`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | Identificador unico |
| materia_id | TEXT NOT NULL FK(materias) | -- | Referencia a materia (CASCADE) |
| nome | TEXT NOT NULL | -- | Ex: "9o Ano A" |
| ano_letivo | INTEGER | NULL | Ex: 2024 |
| periodo | TEXT | NULL | Ex: "1o Semestre" |
| descricao | TEXT | NULL | Descricao opcional |
| criado_em | TIMESTAMPTZ | NOW() | -- |
| atualizado_em | TIMESTAMPTZ | NOW() | -- |
| metadata | JSONB | '{}' | -- |

Indice: `idx_turmas_materia(materia_id)`

#### `alunos`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| nome | TEXT NOT NULL | -- | Nome completo |
| email | TEXT | NULL | Email do aluno |
| matricula | TEXT | NULL | Numero de matricula |
| criado_em | TIMESTAMPTZ | NOW() | -- |
| atualizado_em | TIMESTAMPTZ | NOW() | -- |
| metadata | JSONB | '{}' | -- |

#### `alunos_turmas` (tabela de juncao M:N)

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| aluno_id | TEXT NOT NULL FK(alunos) | -- | CASCADE |
| turma_id | TEXT NOT NULL FK(turmas) | -- | CASCADE |
| ativo | BOOLEAN | TRUE | Se o aluno ainda esta na turma |
| data_entrada | TIMESTAMPTZ | NOW() | -- |
| data_saida | TIMESTAMPTZ | NULL | Preenchido ao sair |
| observacoes | TEXT | NULL | Ex: "Repetente" |

Constraint: UNIQUE(aluno_id, turma_id)
Indices: `idx_alunos_turmas_aluno(aluno_id)`, `idx_alunos_turmas_turma(turma_id)`

#### `atividades`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| turma_id | TEXT NOT NULL FK(turmas) | -- | CASCADE |
| nome | TEXT NOT NULL | -- | Ex: "Prova 1" |
| tipo | TEXT | NULL | Ex: "prova", "trabalho", "exercicio" |
| data_aplicacao | TIMESTAMPTZ | NULL | Quando foi aplicada |
| data_entrega | TIMESTAMPTZ | NULL | Prazo de entrega |
| peso | REAL | 1.0 | Peso na media |
| nota_maxima | REAL | 10.0 | Nota maxima possivel |
| descricao | TEXT | NULL | -- |
| criado_em | TIMESTAMPTZ | NOW() | -- |
| atualizado_em | TIMESTAMPTZ | NOW() | -- |
| metadata | JSONB | '{}' | -- |

Indice: `idx_atividades_turma(turma_id)`

#### `documentos`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| tipo | TEXT NOT NULL | -- | Valor de TipoDocumento (ver abaixo) |
| atividade_id | TEXT NOT NULL FK(atividades) | -- | CASCADE |
| aluno_id | TEXT FK(alunos) | NULL | SET NULL ao deletar aluno |
| display_name | TEXT | '' | Nome legivel |
| nome_arquivo | TEXT | NULL | Nome original do arquivo |
| caminho_arquivo | TEXT | NULL | Caminho no sistema de arquivos |
| extensao | TEXT | NULL | Ex: ".pdf", ".docx" |
| tamanho_bytes | INTEGER | 0 | -- |
| ia_provider | TEXT | NULL | Ex: "openai-gpt4o" |
| ia_modelo | TEXT | NULL | Ex: "gpt-4o" |
| prompt_usado | TEXT | NULL | ID ou texto do prompt |
| prompt_versao | TEXT | NULL | -- |
| tokens_usados | INTEGER | 0 | -- |
| tempo_processamento_ms | REAL | 0 | -- |
| status | TEXT | 'concluido' | Enum: pendente, processando, concluido, erro |
| criado_em | TIMESTAMPTZ | NOW() | -- |
| atualizado_em | TIMESTAMPTZ | NOW() | -- |
| criado_por | TEXT | NULL | Usuario ou "sistema" |
| versao | INTEGER | 1 | Para historico de versoes |
| documento_origem_id | TEXT | NULL | Se re-processado |
| metadata | JSONB | '{}' | -- |

Indices: `idx_documentos_atividade(atividade_id)`, `idx_documentos_aluno(aluno_id)`

#### `resultados`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| aluno_id | TEXT NOT NULL FK(alunos) | -- | CASCADE |
| atividade_id | TEXT NOT NULL FK(atividades) | -- | CASCADE |
| nota_obtida | REAL | NULL | -- |
| nota_maxima | REAL | 10.0 | -- |
| percentual | REAL | NULL | -- |
| total_questoes | INTEGER | 0 | -- |
| questoes_corretas | INTEGER | 0 | -- |
| questoes_parciais | INTEGER | 0 | -- |
| questoes_incorretas | INTEGER | 0 | -- |
| habilidades_demonstradas | TEXT | NULL | Serializado como texto |
| habilidades_faltantes | TEXT | NULL | Serializado como texto |
| feedback_geral | TEXT | NULL | -- |
| corrigido_em | TIMESTAMPTZ | NULL | -- |
| corrigido_por_ia | TEXT | NULL | -- |
| metadata | JSONB | '{}' | -- |

Constraint: UNIQUE(aluno_id, atividade_id)

#### `prompts`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | TEXT PK | -- | -- |
| nome | TEXT NOT NULL | -- | Ex: "Extracao de Questoes - Padrao" |
| etapa | TEXT NOT NULL | -- | Ex: "extracao_questoes", "correcao" |
| texto | TEXT NOT NULL | -- | O prompt em si |
| texto_sistema | TEXT | NULL | System prompt (coluna SQL, nao presente no dataclass) |
| descricao | TEXT | NULL | -- |
| is_padrao | BOOLEAN | FALSE | Se e prompt padrao do sistema |
| is_ativo | BOOLEAN | TRUE | -- |
| materia_id | TEXT | NULL | Se especifico para uma materia |
| variaveis | JSONB | '[]' | Variaveis do template |
| versao | INTEGER | 1 | -- |
| criado_em | TIMESTAMPTZ | NOW() | -- |
| atualizado_em | TIMESTAMPTZ | NOW() | -- |
| criado_por | TEXT | NULL | -- |

#### `prompts_historico`

| Coluna | Tipo SQL | Default | Descricao |
|--------|----------|---------|-----------|
| id | SERIAL PK | auto | -- |
| prompt_id | TEXT NOT NULL FK(prompts) | -- | CASCADE |
| versao | INTEGER NOT NULL | -- | -- |
| texto | TEXT NOT NULL | -- | Texto da versao |
| modificado_em | TIMESTAMPTZ | NOW() | -- |
| modificado_por | TEXT | NULL | -- |

### 1.3 TipoDocumento (Enum Completo)

Definido em `backend/models.py`. Dividido em 3 categorias ativas + 1 deprecated + 1 de relatorios agregados:

**Documentos BASE (nivel Atividade - professor faz upload):**

| Valor | Descricao |
|-------|-----------|
| `enunciado` | Prova/atividade em branco |
| `gabarito` | Respostas corretas |
| `criterios_correcao` | Rubrica/criterios de avaliacao |
| `material_apoio` | Material extra (opcional) |

**Documentos do ALUNO (nivel Aluno - professor faz upload):**

| Valor | Descricao |
|-------|-----------|
| `prova_respondida` | Prova feita pelo aluno |
| `correcao_professor` | Correcao feita pelo professor |

**Documentos GERADOS pela IA (nivel Aluno):**

| Valor | Descricao |
|-------|-----------|
| `extracao_questoes` | Questoes extraidas do enunciado |
| `extracao_gabarito` | Respostas extraidas do gabarito |
| `extracao_respostas` | Respostas extraidas do aluno |
| `correcao` | Correcao questao por questao |
| `analise_habilidades` | Analise de competencias |
| `relatorio_final` | Relatorio para o professor |

**DEPRECATED (Two-Pass Pipeline, 2026-02-27) - mantidos para compatibilidade:**

| Valor | Status |
|-------|--------|
| `correcao_narrativa` | DEPRECATED - usar CORRECAO PDF |
| `analise_habilidades_narrativa` | DEPRECATED - usar ANALISE_HABILIDADES PDF |
| `relatorio_narrativo` | DEPRECATED - usar RELATORIO_FINAL PDF |
| `relatorio_final_old` | DEPRECATED - nome legado |

**Relatorios de Desempenho Agregados:**

| Valor | Descricao |
|-------|-----------|
| `relatorio_desempenho_tarefa` | Analise agregada de uma atividade |
| `relatorio_desempenho_turma` | Analise holistica de uma turma |
| `relatorio_desempenho_materia` | Analise cross-turma de uma materia |

### 1.4 StatusProcessamento (Enum)

| Valor | Descricao |
|-------|-----------|
| `pendente` | Ainda nao processado |
| `processando` | Em andamento |
| `concluido` | Finalizado com sucesso |
| `erro` | Falhou |

### 1.5 NivelEnsino (Enum)

| Valor | Descricao |
|-------|-----------|
| `fundamental_1` | Ensino fundamental 1 |
| `fundamental_2` | Ensino fundamental 2 |
| `medio` | Ensino medio |
| `superior` | Ensino superior |
| `outro` | Outro (default) |

### 1.6 Dependencias de Documentos no Pipeline

Mapa definido em `DEPENDENCIAS_DOCUMENTOS` (models.py). Define quais documentos sao pre-requisito para gerar cada tipo:

| Tipo Alvo | Obrigatorios | Opcionais |
|-----------|-------------|-----------|
| EXTRACAO_QUESTOES | ENUNCIADO | -- |
| EXTRACAO_GABARITO | GABARITO | ENUNCIADO |
| EXTRACAO_RESPOSTAS | PROVA_RESPONDIDA | ENUNCIADO, EXTRACAO_QUESTOES |
| CORRECAO | EXTRACAO_RESPOSTAS, GABARITO | CRITERIOS_CORRECAO, EXTRACAO_GABARITO |
| ANALISE_HABILIDADES | CORRECAO | CRITERIOS_CORRECAO |
| RELATORIO_FINAL | CORRECAO | ANALISE_HABILIDADES, CRITERIOS_CORRECAO |
| RELATORIO_DESEMPENHO_TAREFA | RELATORIO_FINAL | -- |
| RELATORIO_DESEMPENHO_TURMA | RELATORIO_FINAL | -- |
| RELATORIO_DESEMPENHO_MATERIA | RELATORIO_FINAL | -- |

---

## 2. Configuracao de Modelos (models.json)

Arquivo: `backend/data/models.json`

### 2.1 Schema de um modelo configurado

```json
{
  "id": "string (hex ou slug)",
  "nome": "string (display name)",
  "tipo": "string (openai|anthropic|google|ollama)",
  "modelo": "string (ID real da API)",
  "api_key_id": "string|null",
  "max_tokens": "int",
  "temperature": "float|null",
  "parametros": "object (ex: {reasoning_effort: 'low'})",
  "system_prompt": "string|null",
  "suporta_temperature": "bool",
  "suporta_vision": "bool",
  "suporta_streaming": "bool",
  "suporta_function_calling": "bool",
  "base_url": "string|null",
  "custom_model_id": "string|null",
  "api_version": "string|null",
  "extra_headers": "object",
  "catalog_ref": "string|null",
  "ativo": "bool",
  "is_default": "bool",
  "criado_em": "ISO datetime string"
}
```

### 2.2 Modelos Ativos (14 modelos, todos com ativo: true)

| ID | Nome | Tipo | Modelo API | is_default | temp | vision | fn_call | Notas |
|----|------|------|-----------|------------|------|--------|---------|-------|
| 180b8298a279 | gpt-4o | openai | gpt-4o | false | 0.7 | sim | sim | -- |
| 58ff5dcdff67 | o3 Mini | openai | o3-mini | false | null | nao | nao | reasoning_effort=low |
| ffae9accf68e | GPT-4.1 | openai | gpt-4.1 | false | 0.7 | sim | sim | -- |
| 9f6b2b61b6c3 | o4 Mini | openai | o4-mini | false | null | nao | nao | reasoning_effort=high |
| gpt5nano001 | GPT-5 Nano | openai | gpt-5-nano | false | null | nao | sim | reasoning_effort=low |
| gpt54mini001 | GPT-5.4 Mini OCR candidato | openai | gpt-5.4-mini | **true** | null | sim | sim | MODELO DEFAULT desde `22f6f31`; reasoning_effort=low |
| 588f3efe7975 | Claude Haiku 4.5 | anthropic | claude-haiku-4-5-20251001 | false | 0.7 | sim | sim | Bloqueado por credito Anthropic nos smokes recentes |
| 4eaeb5105f5d | Claude Sonnet 4.5 | anthropic | claude-sonnet-4-5-20250929 | false | 0.7 | sim | **nao** | -- |
| c489f094083c | o3 Mini | openai | o3-mini | false | null | nao | nao | reasoning_effort=medium |
| e251747cd7a2 | Gemini 2.5 Pro | google | gemini-2.5-pro | false | 0.7 | sim | sim | Tem system_prompt customizado |
| gem25flash001 | Gemini 2.5 Flash | google | gemini-2.5-flash | false | 0.7 | sim | sim | -- |
| gem25lite001 | Gemini 2.5 Flash Lite | google | gemini-2.5-flash-lite | false | 0.7 | sim | sim | -- |
| gem3flash001 | Gemini 3 Flash | google | gemini-3-flash-preview | false | 0.7 | sim | sim | -- |
| ollama-llama3 | Llama 3.2 (Local) | ollama | llama3.2:latest | false | 0.7 | sim | nao | base_url local |

### 2.3 Verificacoes de Consistencia em models.json

**PROBLEMAS ENCONTRADOS:**

1. **Entradas duplicadas de o3-mini:** Existem dois modelos com `modelo: "o3-mini"` (IDs `58ff5dcdff67` com reasoning_effort=low e `c489f094083c` com reasoning_effort=medium). Ambos ativos. Isso e intencional (variantes de esforco), mas compartilham o mesmo `nome` ("o3 Mini") -- pode causar confusao na UI.

2. **Claude Sonnet 4.5 com suporta_function_calling=false:** Em models.json, o Claude Sonnet 4.5 (`4eaeb5105f5d`) tem `suporta_function_calling: false`. Porem, no `model_catalog.json` e no `MODELOS_SUGERIDOS` de `chat_service.py`, Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`) e listado com `supports_tools: true` e `suporta_tools: True`. **INCONSISTENCIA:** O Sonnet 4.5 suporta tools na realidade. O campo em models.json esta incorreto.

3. **o3 Mini e o4 Mini com suporta_vision=false:** Em models.json, ambos modelos reasoning (o3-mini e o4-mini) estao com `suporta_vision: false`. No `model_catalog.json`, o3-mini e o4-mini possuem `supports_vision: true`. **INCONSISTENCIA:** Os modelos o3/o4 da OpenAI suportam vision. O campo em models.json esta possivelmente desatualizado.

4. **o3 Mini e o4 Mini com suporta_function_calling=false:** Analogamente, models.json lista `suporta_function_calling: false`, mas `model_catalog.json` e `MODELOS_SUGERIDOS` listam `supports_tools: true` para esses modelos. **INCONSISTENCIA.**

5. **GPT-5 Nano com suporta_vision=false e suporta_temperature=false:** No `model_catalog.json`, `gpt-5-nano` tem `supports_vision: true` e `supports_reasoning: true`. Em models.json tem `suporta_vision: false` e `suporta_temperature: false`. O modelo e da familia GPT-5 com reasoning, entao `suporta_temperature: false` e coerente (modelos reasoning nao usam temperature). Porem `suporta_vision: false` contradiz o catalogo.

6. **Gemini 2.5 Flash Lite com suporta_function_calling=true:** Em models.json, `gem25lite001` tem `suporta_function_calling: true`. No `model_catalog.json`, `gemini-2.5-flash-lite` tem `supports_tools: false` e a descricao diz "sem tools". **INCONSISTENCIA:** O Flash Lite nao suporta tools.

7. **Gemini 2.5 Pro com system_prompt embutido:** O modelo `e251747cd7a2` tem um `system_prompt` longo embutido com instrucoes de geracao de arquivos python-exec. Todos os outros modelos tem `system_prompt: null`. Isso e intencional mas nao esta documentado em nenhum lugar.

8. **Nenhum modelo tem `catalog_ref` preenchido:** Todos os 13 modelos tem `catalog_ref: null`. Este campo deveria vincular ao `model_catalog.json` mas nunca e usado. Funcionalidade morta.

9. **Nenhum modelo usa `api_key_id`:** Todos tem `api_key_id: null`. As chaves sao resolvidas via env vars ou ApiKeyManager, nao por vinculacao direta.

---

## 3. Configuracao de Providers

### 3.1 providers.json (Legado)

Arquivo: `backend/data/providers.json`

```json
{
  "default_provider": "ollama-llama3",
  "providers": [
    {
      "name": "ollama-llama3",
      "provider_type": "LocalLLMProvider",
      "model": "llama3",
      "base_url": "http://localhost:11434"
    }
  ]
}
```

Este arquivo e **legado** e contem apenas um provider local. O sistema real usa o `ProviderType` enum e `DEFAULT_URLS` definidos em `chat_service.py`, alem do `model_catalog.json`.

### 3.2 ProviderType Enum (chat_service.py)

| Valor | Descricao |
|-------|-----------|
| `openai` | OpenAI |
| `anthropic` | Anthropic |
| `google` | Google Gemini |
| `ollama` | Ollama (local) |
| `openrouter` | OpenRouter (multi-provider) |
| `groq` | Groq (inferencia rapida) |
| `mistral` | Mistral AI |
| `deepseek` | DeepSeek |
| `xai` | xAI (Grok) |
| `perplexity` | Perplexity (search) |
| `cohere` | Cohere (RAG) |
| `vllm` | vLLM (local) |
| `lmstudio` | LM Studio (local) |
| `custom` | Custom (generico) |

### 3.3 DEFAULT_URLS

| Provider | URL |
|----------|-----|
| openai | https://api.openai.com/v1 |
| anthropic | https://api.anthropic.com/v1 |
| google | https://generativelanguage.googleapis.com/v1beta |
| ollama | http://localhost:11434/api |
| openrouter | https://openrouter.ai/api/v1 |
| groq | https://api.groq.com/openai/v1 |
| mistral | https://api.mistral.ai/v1 |
| deepseek | https://api.deepseek.com/v1 |
| xai | https://api.x.ai/v1 |
| perplexity | https://api.perplexity.ai |
| cohere | https://api.cohere.ai/v1 |
| vllm | http://localhost:8000/v1 |
| lmstudio | http://localhost:1234/v1 |

### 3.4 Configuracao de Autenticacao por Provider (model_catalog.json)

| Provider | auth_header | auth_prefix | extra_headers | is_local |
|----------|-------------|-------------|---------------|----------|
| openai | Authorization | Bearer | -- | false |
| anthropic | x-api-key | (vazio) | anthropic-version: 2023-06-01 | false |
| google | x-goog-api-key | (vazio) | -- | false |
| deepseek | Authorization | Bearer | -- | false |
| mistral | Authorization | Bearer | -- | false |
| xai | Authorization | Bearer | -- | false |
| perplexity | Authorization | Bearer | -- | false |
| cohere | Authorization | Bearer | -- | false |
| groq | Authorization | Bearer | -- | false |
| openrouter | Authorization | Bearer | -- | false |
| ollama | (vazio) | (vazio) | -- | true |
| vllm | (vazio) | (vazio) | -- | true |
| lmstudio | (vazio) | (vazio) | -- | true |

### 3.5 MODELOS_SUGERIDOS (chat_service.py)

Lista de modelos sugeridos por provider exibida na UI de configuracao. Contem os seguintes providers populados:

- **OpenAI:** 15 modelos (GPT-5.2, GPT-5.2 Pro, GPT-5, GPT-5 Mini, GPT-5 Nano, GPT-5 Pro, GPT-5 Image, GPT-4o, GPT-4o Mini, GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano, o3, o3 Mini, o4 Mini)
- **Anthropic:** 5 modelos (Opus 4.5, Sonnet 4.5, Haiku 4.5, 3.5 Sonnet, 3.5 Haiku)
- **Google:** 6 modelos (3 Pro Preview, 3 Flash Preview, 2.5 Pro, 2.5 Flash, 2.5 Flash Lite, 2.0 Flash [deprecated])
- **Ollama:** 5 modelos (Llama 3.2, 3.1, Mistral, Code Llama, Mixtral)
- **Groq:** 2 modelos (Llama 3.3 70B, Mixtral 8x7B)
- **Mistral:** 3 modelos (Large 2, Small, Codestral)
- **OpenRouter:** 3 modelos (GPT-4o, Claude 3.5 Sonnet, Llama 3.1 405B)
- **DeepSeek:** 2 modelos (Chat, Reasoner R1)
- **xAI:** 2 modelos (Grok 4, Grok 4 Fast)
- **Perplexity:** 3 modelos (Sonar, Sonar Pro, Sonar Deep Research)
- **Cohere:** 2 modelos (Command R+, Command R)
- **vLLM / LM Studio:** vazios

### 3.6 REASONING_MODELS (chat_service.py)

Modelos que usam `reasoning_effort` ao inves de `temperature`:

```
o3, o3-mini, o3-pro, o4-mini, gpt-5*, gpt-5.1, gpt-5.2*, gpt-5.4*, gpt-5.5*, deepseek-reasoner
```

Nota 2026-05-17: as familias GPT-5.4/5.5 e variantes `-pro` entram como
reasoning/no-temperature. `o1` e `o1-pro` permanecem no catalogo historico, mas
nao sao sugeridos para novos cadastros.

---

## 4. Gerenciamento de API Keys

### 4.1 Estrutura do api_keys.json

O arquivo `backend/data/api_keys.json` **nao existe no repositorio** (esta no .gitignore). E criado automaticamente em runtime pelo `ApiKeyManager`.

Estrutura esperada:

```json
{
  "keys": [
    {
      "id": "string",
      "empresa": "openai|anthropic|google|...",
      "api_key": "gAAAAA... (criptografado com Fernet)",
      "nome_exibicao": "string",
      "ativo": true,
      "criado_em": "ISO datetime"
    }
  ]
}
```

### 4.2 Cadeia de Resolucao de Chaves

1. **api_keys.json** -- se existir, carrega todas as chaves (descriptografa automaticamente)
2. **Variaveis de ambiente** -- se api_keys.json nao existir, `_init_from_env()` cria configs a partir de:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `GOOGLE_API_KEY`
3. **Criptografia obrigatoria** -- Fernet cipher. Chave armazenada em `backend/data/.encryption_key`
4. **Migracao automatica** -- chaves em texto plano sao migradas para formato criptografado na primeira leitura

### 4.3 ApiKeyConfig (Dataclass)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| id | str | Identificador unico |
| empresa | ProviderType | Enum do provider |
| api_key | str | Valor descriptografado em memoria |
| nome_exibicao | str | Nome amigavel |
| ativo | bool | Se esta ativa |
| criado_em | datetime | Data de criacao |

O metodo `to_dict()` expoe apenas preview da chave (primeiros 8 + ultimos 4 caracteres), nunca o valor completo.

---

## 5. Catalogo de Modelos (model_catalog.json + model_catalog.py)

### 5.1 Metadados Globais

- **Versao:** 2026.05
- **Ultima atualizacao:** 2026-05-17

### 5.2 Precos por Modelo (USD por 1M tokens)

#### OpenAI

| Modelo | Input | Output | Cache | Context | Max Output |
|--------|-------|--------|-------|---------|------------|
| gpt-5.5 | $5.00 | $30.00 | $0.50 | 1.05M | 128K |
| gpt-5.5-pro | $30.00 | $180.00 | -- | 1.05M | 128K |
| gpt-5.4 | $2.50 | $15.00 | $0.25 | 1.05M | 128K |
| gpt-5.4-mini | $0.75 | $4.50 | $0.075 | 400K | 128K |
| gpt-5.4-nano | $0.20 | $1.25 | $0.02 | 400K | 128K |
| gpt-5.4-pro | $30.00 | $180.00 | -- | 1.05M | 128K |
| gpt-5.2 | $1.75 | $14.00 | $0.175 | 400K | 128K |
| gpt-5.2-pro | $21.00 | $168.00 | -- | 400K | 128K |
| gpt-5 | $1.25 | $10.00 | $0.125 | 400K | 128K |
| gpt-5-mini | $0.25 | $2.00 | $0.025 | 400K | 128K |
| gpt-5-nano | $0.05 | $0.40 | $0.005 | 400K | 128K |
| gpt-5-pro | $15.00 | $120.00 | -- | 400K | 272K |
| gpt-4o | $2.50 | $10.00 | -- | 128K | 16K |
| gpt-4o-mini | $0.15 | $0.60 | -- | 128K | 16K |
| gpt-4.1 | $2.00 | $8.00 | -- | 1M | 32K |
| gpt-4.1-mini | $0.40 | $1.60 | -- | 1M | 32K |
| gpt-4.1-nano | $0.10 | $0.40 | -- | 1M | 32K |
| o1 | $15.00 | $60.00 | -- | 200K | 100K |
| o1-mini | $3.00 | $12.00 | -- | 128K | 65K |
| o1-pro | $150.00 | $600.00 | -- | 200K | 100K |
| o3 | $2.00 | $8.00 | -- | 200K | 100K |
| o3-mini | $1.10 | $4.40 | -- | 200K | 100K |
| o3-pro | $20.00 | $80.00 | -- | 200K | 100K |
| o4-mini | $1.10 | $4.40 | -- | 200K | 100K |
| gpt-4-turbo | $10.00 | $30.00 | -- | 128K | 4K |
| gpt-4 | $30.00 | $60.00 | -- | 8K | 4K |

#### Anthropic

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| claude-opus-4-5-20251101 | $15.00 | $75.00 | 200K | 32K |
| claude-sonnet-4-5-20250929 | $3.00 | $15.00 | 200K | 64K |
| claude-haiku-4-5-20251001 | $1.00 | $5.00 | 200K | 64K |
| claude-3-5-sonnet-20241022 | $3.00 | $15.00 | 200K | 8K |
| claude-3-5-haiku-20241022 | $0.80 | $4.00 | 200K | 8K |

#### Google Gemini

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| gemini-2.5-pro | $1.25 | $10.00 | 1M | 65K |
| gemini-2.5-flash | $0.15 | $0.60 | 1M | 65K |
| gemini-2.5-flash-lite | $0.075 | $0.30 | 1M | 65K |
| gemini-2.0-flash | $0.10 | $0.40 | 1M | 8K |
| gemini-3-pro-preview | $2.00 | $15.00 | 2M | 131K |
| gemini-3-flash-preview | $0.30 | $1.20 | 2M | 131K |

#### DeepSeek

| Modelo | Input | Output | Cache | Context | Max Output |
|--------|-------|--------|-------|---------|------------|
| deepseek-chat | $0.28 | $0.42 | $0.028 | 64K | 8K |
| deepseek-reasoner | $0.55 | $2.19 | -- | 64K | 8K |

#### Mistral

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| mistral-large-latest | $2.00 | $6.00 | 128K | 8K |
| mistral-small-latest | $0.20 | $0.60 | 128K | 8K |
| codestral-latest | $0.30 | $0.90 | 32K | 8K |

#### xAI (Grok)

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| grok-4 | $5.00 | $15.00 | 131K | 8K |
| grok-4-fast | $2.00 | $6.00 | 131K | 8K |

#### Perplexity

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| sonar | $1.00 | $1.00 | 32K | 4K |
| sonar-pro | $3.00 | $15.00 | 32K | 4K |
| sonar-deep-research | $5.00 | $20.00 | 128K | 8K |

#### Cohere

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| command-r-plus | $2.50 | $10.00 | 128K | 4K |
| command-r | $0.15 | $0.60 | 128K | 4K |

#### Groq

| Modelo | Input | Output | Context | Max Output |
|--------|-------|--------|---------|------------|
| llama-3.3-70b-versatile | $0.59 | $0.79 | 128K | 32K |
| mixtral-8x7b-32768 | $0.24 | $0.24 | 32K | 8K |

#### Locais (custo zero)

| Modelo | Provider | Context | Max Output |
|--------|----------|---------|------------|
| llama3.2 | ollama | 128K | 8K |
| mistral | ollama | 32K | 4K |
| codellama | ollama | 16K | 4K |

### 5.3 Capabilities por Modelo (Resumo)

| Capability | Descricao | Modelos que NAO suportam |
|-----------|-----------|--------------------------|
| vision | Processamento de imagens | deepseek-*, mistral-*, codestral, perplexity-*, cohere-*, groq-*, ollama/mistral, ollama/codellama |
| tools (function calling) | Chamada de funcoes | perplexity-*, ollama-*, gemini-2.5-flash-lite |
| json_mode | Output JSON estruturado | Varios modelos legados |
| reasoning | Raciocinio avancado (CoT) | Modelos GPT-4 non-o, Claude (usa extended_thinking), mistral, cohere, groq |
| extended_thinking | Pensamento estendido Anthropic | Todos exceto Claude Opus/Sonnet 4.5 |
| search | Busca em tempo real | Todos exceto Perplexity |
| code_exec | Execucao de codigo | Todos exceto Gemini 2.5+/3 |
| rag | RAG integrado | Todos exceto Cohere |

### 5.4 Verificacoes de Atualidade do Catalogo

**PROBLEMAS ENCONTRADOS:**

1. **Historico resolvido em 2026-05-17:** a auditoria original registrava
   "Catalogo datado de 2026-01-28"; o campo `last_updated` agora acompanha a
   versao 2026.05. A regra continua: checar periodicamente contra docs oficiais
   antes de promover modelo para pipeline.

2. **o1 e o1-pro ainda no catalogo:** Em `MODELOS_SUGERIDOS` de `chat_service.py`, o1 e o1-pro estao marcados como deprecated com comentario "removed as deprecated". Porem, o `model_catalog.json` ainda os lista com precos. **INCONSISTENCIA: modelos deprecated existem no catalogo mas nao nos sugeridos.**

3. **Gemini 2.0 Flash marcado como deprecated:** Consta no catalogo e em `MODELOS_SUGERIDOS` com nota "Deprecated - EOL March 2026". Como estamos em abril 2026, este modelo provavelmente ja foi desligado. **Recomendacao: remover ou marcar como inativo.**

4. **Precos do GPT-5.2-pro sao altos, mas confirmados:** $21/1M input e
   $168/1M output foram mantidos por bater com a documentacao oficial atual.

5. **gpt-5.1 na lista REASONING_MODELS mas nao no catalogo:** `chat_service.py`
   lista `gpt-5.1` em `REASONING_MODELS`, mas nao existe entrada correspondente
   em `model_catalog.json` nem em `models.json`.

6. **`gpt-5-image` removido:** o slug textual antigo nao aparece no catalogo
   oficial atual de modelos de texto. Imagem fica em familia dedicada
   `GPT Image`/`gpt-image-*`, fora da matriz de pipeline textual.

---

## 6. Framework de Erros do Pipeline

### 6.1 Constantes de Tipo de Erro (models.py)

| Constante | Valor | Descricao |
|-----------|-------|-----------|
| ERRO_DOCUMENTO_FALTANTE | "DOCUMENTO_FALTANTE" | Documento obrigatorio ausente |
| ERRO_QUESTOES_FALTANTES | "QUESTOES_FALTANTES" | Questoes nao encontradas |

### 6.2 SeveridadeErro (Enum)

| Valor | Descricao |
|-------|-----------|
| `critico` | Erro critico, bloqueia processamento |
| `alto` | Erro alto, resultado pode ser comprometido |
| `medio` | Erro medio, resultado parcial |

### 6.3 Funcao criar_erro_pipeline()

Cria dicts estruturados de erro com campos: `tipo`, `mensagem`, `severidade`, `etapa`, `timestamp`.

---

## 7. Sistema de Avisos (visualizador.py)

### 7.1 Codigos de Aviso Validos

Definidos em `_VALID_CODES` (visualizador.py):

| Codigo | Descricao |
|--------|-----------|
| `ILLEGIBLE_DOCUMENT` | Documento inteiro ilegivel |
| `ILLEGIBLE_QUESTION` | Questao especifica ilegivel |
| `MISSING_CONTENT` | Conteudo ausente (pode ser intencional em etapas de resposta do aluno) |
| `LOW_CONFIDENCE` | Baixa confianca na leitura/interpretacao da IA |

### 7.2 Etapas Validas

Definidas em `_VALID_STAGES`:

| Etapa | Descricao |
|-------|-----------|
| `EXTRAIR_QUESTOES` | Extracao de questoes do enunciado |
| `EXTRAIR_GABARITO` | Extracao de respostas do gabarito |
| `EXTRAIR_RESPOSTAS` | Extracao de respostas do aluno |
| `CORRIGIR` | Correcao questao por questao |
| `ANALISAR_HABILIDADES` | Analise de competencias |
| `GERAR_RELATORIO` | Geracao de relatorio final |

### 7.3 Mapeamento de Severidade (stage x code)

A funcao `get_warning_severity(stage, code)` retorna:

| Codigo | Etapa | Severidade | Cor |
|--------|-------|-----------|-----|
| MISSING_CONTENT | EXTRAIR_RESPOSTAS | yellow | Amarelo (aluno pode ter deixado em branco) |
| MISSING_CONTENT | CORRIGIR | yellow | Amarelo |
| MISSING_CONTENT | ANALISAR_HABILIDADES | yellow | Amarelo |
| MISSING_CONTENT | GERAR_RELATORIO | yellow | Amarelo |
| MISSING_CONTENT | EXTRAIR_QUESTOES | orange | Laranja (ausencia inesperada) |
| MISSING_CONTENT | EXTRAIR_GABARITO | orange | Laranja |
| ILLEGIBLE_DOCUMENT | (qualquer valida) | orange | Laranja |
| ILLEGIBLE_QUESTION | (qualquer valida) | orange | Laranja |
| LOW_CONFIDENCE | (qualquer valida) | orange | Laranja |
| (qualquer) | (invalida) | None | Vermelho na UI (violacao de schema) |
| (invalido) | (qualquer) | None | Vermelho na UI |

### 7.4 Como Avisos Sao Lidos pelo Visualizador

Os JSONs gerados pelo pipeline contem dois arrays de avisos:

```json
{
  "_avisos_documento": [
    {"codigo": "ILLEGIBLE_DOCUMENT", "explicacao": "Documento muito borrado"}
  ],
  "_avisos_questao": [
    {"codigo": "MISSING_CONTENT", "questao": 3, "explicacao": "Questao 3 em branco"}
  ],
  "_avisos_stage": "CORRIGIR"
}
```

O `VisaoAluno.to_dict()` injeta a severidade calculada em cada aviso ao serializar:

```python
{**w, "severidade": get_warning_severity(self._avisos_stage, w.get("codigo", ""))}
```

### 7.5 VisaoAluno (Dataclass Principal do Visualizador)

| Campo | Tipo | Descricao |
|-------|------|-----------|
| aluno_id | str | -- |
| aluno_nome | str | -- |
| atividade_id | str | -- |
| atividade_nome | str | -- |
| nota_final | float | -- |
| nota_maxima | float | -- |
| percentual | float | -- |
| total_questoes | int | -- |
| questoes_corretas | int | -- |
| questoes_parciais | int | -- |
| questoes_incorretas | int | -- |
| questoes_branco | int | -- |
| questoes | List[VisaoQuestao] | Detalhamento por questao |
| habilidades_demonstradas | List[str] | -- |
| habilidades_faltantes | List[str] | -- |
| recomendacoes | List[str] | -- |
| feedback_geral | str | -- |
| corrigido_em | datetime? | -- |
| corrigido_por_ia | str | -- |
| erro_pipeline | Dict? | Presente se houve erro |
| dados_incompletos | bool | True quando JSON nao tem campos estruturados |
| avisos_documento | List[Dict] | Avisos de nivel documento |
| avisos_questao | List[Dict] | Avisos de nivel questao |
| _avisos_stage | str | Etapa para calculo de severidade |
| fontes_utilizadas | List[str]? | Etapas upstream consumidas |

---

## 8. Verificacoes Gerais de Consistencia

Consolidacao de todos os problemas encontrados no cruzamento dos arquivos:

### 8.1 Inconsistencias Criticas

| # | Descricao | Arquivos Afetados | Impacto |
|---|-----------|-------------------|---------|
| 1 | Claude Sonnet 4.5 com fn_calling=false em models.json, mas supports_tools=true no catalogo e sugeridos | models.json, model_catalog.json, chat_service.py | Modelo pode nao ter function calling habilitado no pipeline quando deveria |
| 2 | Gemini 2.5 Flash Lite com fn_calling=true em models.json, mas supports_tools=false no catalogo | models.json, model_catalog.json | Chamadas de tools vao falhar com este modelo |

### 8.2 Inconsistencias Medias

| # | Descricao | Arquivos Afetados |
|---|-----------|-------------------|
| 3 | o3-mini e o4-mini com vision=false em models.json, mas vision=true no catalogo | models.json, model_catalog.json |
| 4 | GPT-5 Nano com vision=false em models.json, mas vision=true no catalogo | models.json, model_catalog.json |
| 5 | gpt-5.1 listado em REASONING_MODELS mas nao existe em nenhum catalogo | chat_service.py |
| 6 | o1, o1-pro deprecated nos sugeridos mas ativos no catalogo | chat_service.py, model_catalog.json |
| 7 | Gemini 2.0 Flash provavelmente desligado (EOL marco 2026) | model_catalog.json, chat_service.py |

### 8.3 Avisos de Governanca

| # | Descricao |
|---|-----------|
| 8 | Dois modelos o3-mini com mesmo nome ("o3 Mini") causam confusao na UI |
| 9 | Campo catalog_ref nunca e utilizado (dead code) |
| 10 | Campo api_key_id nunca e utilizado nos modelos configurados |
| 11 | Catalogo desatualizado (janeiro 2026 vs abril 2026) |
| 12 | providers.json e arquivo legado -- so contem Ollama, irrelevante para operacao real |

### 8.4 Divergencias entre Dataclass Python e Schema SQL

| Campo/Tabela | Python | SQL | Nota |
|--------------|--------|-----|------|
| prompts.texto_sistema | Nao existe no dataclass Prompt | Existe na tabela | SQL tem coluna extra |
| prompts.is_ativo | Nao existe no dataclass Prompt | Existe na tabela | SQL tem coluna extra |
| prompts.variaveis | Nao existe no dataclass Prompt | Existe na tabela (JSONB) | SQL tem coluna extra |
| prompts.versao | Nao existe no dataclass Prompt | Existe na tabela | SQL tem coluna extra |
| prompts.criado_por | Nao existe no dataclass Prompt | Existe na tabela | SQL tem coluna extra |
| resultados.habilidades_* | List[str] no dataclass | TEXT no SQL | Divergencia de tipo: lista vs texto serializado |

---

## 9. Cuidados de Uso

### 9.1 Dados Sensiveis

| Dado | Localizacao | Protecao |
|------|------------|----------|
| API Keys | `backend/data/api_keys.json` | Criptografia Fernet obrigatoria. Arquivo NAO deve estar no repositorio (.gitignore) |
| Chave de criptografia | `backend/data/.encryption_key` | Arquivo binario, NAO deve estar no repositorio |
| Variaveis de ambiente | Runtime (Render) | OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, SUPABASE_SERVICE_KEY |
| Credenciais Supabase | Runtime | SUPABASE_URL, SUPABASE_SERVICE_KEY |
| Credenciais E2B | Runtime | E2B_API_KEY |

### 9.2 O que NUNCA Expor

- Valores reais de API keys (o sistema so mostra preview: 8 primeiros + 4 ultimos caracteres)
- O conteudo de `.encryption_key`
- O `SUPABASE_SERVICE_KEY` (bypass de RLS)
- Dados pessoais de alunos (nome, email, matricula) em logs ou relatorios publicos

### 9.3 RLS (Row Level Security)

O SQL de migracao tem RLS **desabilitado** (comentado). O sistema usa `service_key` do Supabase, que bypassa RLS. Se futuramente houver acesso multi-tenant, RLS deve ser habilitado.

### 9.4 Recomendacoes

1. **Atualizar model_catalog.json** para versao 2026.04 com precos verificados
2. **Corrigir inconsistencias** entre models.json e model_catalog.json (especialmente fn_calling do Sonnet 4.5 e Flash Lite)
3. **Remover Gemini 2.0 Flash** do catalogo (EOL passado)
4. **Remover o1/o1-pro** do catalogo ou marcar como deprecated explicitamente
5. **Unificar nomes** dos dois modelos o3-mini para distingui-los (ex: "o3 Mini (Low)" e "o3 Mini (Medium)")
6. **Sincronizar dataclass Prompt** com as colunas extras do SQL (texto_sistema, is_ativo, variaveis, versao, criado_por)
7. **Popular catalog_ref** nos modelos de models.json ou remover o campo se nao sera usado
