# 🎓 Prova AI - Sistema de Correção Automatizada

Framework para experimentação com diferentes IAs na correção automatizada de provas.

## ✨ Funcionalidades

- **Gerenciamento de Arquivos**: Upload e organização de provas, gabaritos e resoluções por matéria
- **Múltiplos Providers de IA**: OpenAI, Anthropic (Claude), Ollama (LLMs locais)
- **Pipeline de Correção**: Extração automática de questões, identificação de respostas, correção e feedback
- **Vector Database**: Busca semântica em questões para contexto inteligente
- **Experimentos**: Compare resultados de diferentes IAs na mesma tarefa
- **Chat Interativo**: Converse com a IA sobre os documentos carregados
- **Rastreamento**: Saiba qual IA processou cada documento/correção

## 🏗️ Arquitetura

```
prova-ai/
├── backend/
│   ├── main.py           # API FastAPI
│   ├── ai_providers.py   # Abstração de providers (OpenAI, Anthropic, Ollama)
│   ├── storage.py        # Gerenciamento de arquivos e vector DB
│   └── pipeline.py       # Pipeline de correção
├── frontend/
│   └── index.html        # Interface web completa
├── data/
│   ├── provas/           # Gabaritos por matéria
│   ├── resolucoes/       # Resoluções/rubricas
│   ├── alunos/           # Provas dos alunos
│   ├── correcoes/        # Correções geradas
│   └── embeddings/       # Vector embeddings
├── requirements.txt
└── .env.example
```

## 🚀 Instalação

### 1. Clone e instale dependências

```bash
cd prova-ai
pip install -r requirements.txt
```

### 2. Configure as chaves de API

```bash
cp .env.example .env
# Edite .env com suas chaves
```

### 3. Inicie o servidor

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acesse a interface

Abra `http://localhost:8000` no navegador.

## 📖 Como Usar

### Fluxo Básico de Correção

1. **Upload do Gabarito**: Envie a prova original com as respostas corretas
2. **Extração Automática**: A IA identifica e estrutura cada questão
3. **Upload da Prova do Aluno**: Envie a prova respondida
4. **Correção**: O pipeline compara respostas e gera feedback
5. **Relatório**: Documento final com notas, erros e recomendações

### Trocar Provider de IA

Cada etapa do pipeline pode usar uma IA diferente:

```python
from pipeline import CorrectionPipeline, PipelineConfig, PipelineStage

config = PipelineConfig()
config.set_provider(PipelineStage.EXTRACT_GABARITO, "openai-gpt4o")
config.set_provider(PipelineStage.CORRIGIR, "claude-sonnet")
config.set_provider(PipelineStage.GERAR_RELATORIO, "ollama-llama3")

pipeline = CorrectionPipeline(config)
```

### Adicionar Novo Provider

Via API:
```bash
curl -X POST http://localhost:8000/api/providers \
  -H "Content-Type: application/json" \
  -d '{"name": "meu-gpt4", "provider_type": "openai", "model": "gpt-4-turbo"}'
```

Via código:
```python
from ai_providers import OpenAIProvider, ai_registry

provider = OpenAIProvider(api_key="sk-...", model="gpt-4-turbo")
ai_registry.register("meu-gpt4", provider)
```

### Busca Semântica

Encontre questões similares usando embeddings:

```python
from storage import vector_store

# Buscar questões sobre derivadas
results = await vector_store.search_similar(
    "calcule a derivada da função",
    top_k=5,
    materia="Matemática"
)
```

## 🔌 API Endpoints

### Providers
- `GET /api/providers` - Lista providers disponíveis
- `POST /api/providers` - Adiciona novo provider
- `GET /api/providers/{name}/stats` - Estatísticas de uso

### Arquivos
- `GET /api/files` - Lista documentos
- `POST /api/files/upload` - Upload de arquivo
- `GET /api/files/{id}` - Detalhes do documento
- `GET /api/files/tree` - Estrutura de diretórios

### Pipeline
- `POST /api/pipeline/extract-gabarito` - Extrai questões do gabarito
- `POST /api/pipeline/correct` - Executa correção completa
- `GET /api/pipeline/results/{prova_id}` - Resultados da correção

### Chat
- `POST /api/chat` - Chat com IA (com contexto de documentos)

### Experimentos
- `POST /api/experiments/compare` - Compara múltiplos providers

## 🧪 Experimentos

Compare como diferentes IAs performam na mesma tarefa:

```bash
curl -X POST http://localhost:8000/api/experiments/compare \
  -F "file=@prova.pdf" \
  -F "materia=Física" \
  -F "providers=openai-gpt4o,claude-sonnet,ollama-llama3"
```

Resposta:
```json
{
  "comparacao": {
    "openai-gpt4o": {
      "questoes_encontradas": 10,
      "tokens_usados": 2500,
      "tempo_ms": 3200
    },
    "claude-sonnet": {
      "questoes_encontradas": 10,
      "tokens_usados": 2100,
      "tempo_ms": 2800
    }
  }
}
```

## 📊 Estrutura de Dados

### Questão Extraída
```json
{
  "numero": 1,
  "enunciado": "Calcule a integral...",
  "itens": [
    {"item": "a", "texto": "...", "resposta": "..."}
  ],
  "pontuacao_maxima": 2.0,
  "habilidades": ["cálculo integral", "substituição"]
}
```

### Correção
```json
{
  "nota": 1.5,
  "nota_maxima": 2.0,
  "feedback": "Bom raciocínio, mas erro no sinal...",
  "erros_identificados": ["sinal invertido na linha 3"],
  "habilidades_demonstradas": ["integração por partes"],
  "habilidades_faltantes": ["verificação do resultado"],
  "confianca": 0.92
}
```

## 🔧 Configuração Avançada

### Usar Ollama (LLMs Locais)

1. Instale Ollama: https://ollama.ai
2. Baixe um modelo: `ollama pull llama3`
3. O provider `ollama-llama3` estará disponível automaticamente

### Customizar Prompts

Edite os system prompts em `pipeline.py` para cada etapa:

```python
system_prompt = """Você é um professor de matemática...
Critérios específicos de correção:
- Valorize demonstrações formais
- Aceite notação alternativa
..."""
```

## 🗺️ Roadmap

- [ ] OCR para provas manuscritas (Tesseract/GPT-4 Vision)
- [ ] Suporte a fórmulas LaTeX
- [ ] Integração com Google Classroom
- [ ] App mobile (React Native)
- [ ] Dashboard de analytics
- [ ] Export para PDF formatado

## 📝 Licença

MIT - use livremente para fins educacionais e comerciais.

---

Desenvolvido para facilitar a vida de professores e melhorar o feedback aos alunos. 🎓
