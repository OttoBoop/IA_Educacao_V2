# Guia de Testes - Prova AI

Este documento explica todos os testes disponíveis, como executá-los e como interpretar os resultados.

---

## Visão Geral

O sistema de testes do Prova AI é dividido em:

1. **Testes Legado** - Arquivos `test_*.py` na raiz do backend
2. **Testes Novos** - Estruturados em `tests/` usando pytest
3. **test_runner.py** - CLI unificado para execução

---

## Estrutura de Testes

### 1. Testes Existentes (Legado)

| Arquivo | Descrição | Como Executar |
|---------|-----------|---------------|
| `test_data_generator.py` | Gera dados fictícios (matérias, turmas, alunos) | `python test_data_generator.py --mini` |
| `test_api.py` | Testa storage e API | `python test_api.py` |
| `test_models.py` | Testa modelos de LLM | `python test_models.py` |
| `test_document_generation.py` | Testa geração de documentos | `python test_document_generation.py` |
| `test_download_e2e.py` | Testa download end-to-end | `python test_download_e2e.py` |
| `test_file_types.py` | Testa tipos de arquivo | `python test_file_types.py` |
| `test_pdf_report.py` | Testa geração de relatórios PDF | `python test_pdf_report.py` |
| `test_tool_use.py` | Testa function calling | `python test_tool_use.py` |
| `test_haiku_tools.py` | Testa Claude Haiku com tools | `python test_haiku_tools.py` |
| `test_system_prompt.py` | Testa system prompts | `python test_system_prompt.py` |
| `test_endpoint.py` | Testa endpoints HTTP | `python test_endpoint.py` |
| `test_download_simples.py` | Testa downloads simples | `python test_download_simples.py` |

### 2. Novos Testes (Pipeline)

| Arquivo | Descrição | Marcador pytest |
|---------|-----------|-----------------|
| `tests/models/test_reasoning.py` | Modelos o1, o3, deepseek-reasoner | `@pytest.mark.reasoning` |
| `tests/models/test_openai_standard.py` | GPT-4o, GPT-5 | `@pytest.mark.openai` |
| `tests/models/test_anthropic.py` | Claude | `@pytest.mark.anthropic` |
| `tests/models/test_google.py` | Gemini | `@pytest.mark.google` |
| `tests/scenarios/test_happy_path.py` | Fluxo de sucesso completo | `@pytest.mark.e2e` |
| `tests/scenarios/test_corrupted_docs.py` | Documentos corrompidos | `@pytest.mark.error_handling` |
| `tests/scenarios/test_skip_steps.py` | Pular etapas do pipeline | `@pytest.mark.partial` |

---

## Como Executar

### Usando test_runner.py (Recomendado)

```bash
# Primeiro: Gerar dados de teste (executar uma vez)
python test_runner.py --generate-data --mini

# Executar todos os testes locais
python test_runner.py --local

# Por provider específico
python test_runner.py --local --provider openai
python test_runner.py --local --provider anthropic
python test_runner.py --local --provider google

# Por modelo específico
python test_runner.py --local --model gpt-4o-mini
python test_runner.py --local --model claude-haiku-4-5-20251001
python test_runner.py --local --model gemini-2.5-flash

# Apenas modelos reasoning
python test_runner.py --local --reasoning

# Cenários específicos
python test_runner.py --scenario happy-path
python test_runner.py --scenario corrupted-docs
python test_runner.py --scenario skip-steps

# Para ambiente Render (pula modelos caros)
python test_runner.py --render --skip-expensive

# Gerar relatório
python test_runner.py --local --report html
python test_runner.py --local --report json
```

### Usando pytest Diretamente

```bash
# Todos os testes
pytest tests/ -v

# Por marcador
pytest tests/ -m "openai" -v
pytest tests/ -m "anthropic" -v
pytest tests/ -m "google" -v
pytest tests/ -m "reasoning" -v
pytest tests/ -m "e2e" -v
pytest tests/ -m "not slow" -v

# Com cobertura de código
pytest tests/ --cov=backend --cov-report=html

# Arquivo específico
pytest tests/models/test_anthropic.py -v
pytest tests/scenarios/test_happy_path.py -v

# Função específica
pytest tests/models/test_openai_standard.py::test_basic_completion -v
```

### Usando Testes Legado

```bash
# Gerar dados de teste
python test_data_generator.py --mini      # Mínimo (3 alunos)
python test_data_generator.py             # Padrão (20 alunos)
python test_data_generator.py --completo  # Completo (50 alunos)
python test_data_generator.py --limpar    # Limpa antes de gerar

# Testar API
python test_api.py

# Testar modelos
python test_models.py

# Testar endpoints (requer servidor rodando)
python main_v2.py &  # Iniciar servidor
python test_endpoint.py
```

---

## Interpretando Resultados

### Console Output

```
PASSED  tests/models/test_openai_standard.py::test_basic_completion
        ✓ Teste passou

FAILED  tests/scenarios/test_corrupted_docs.py::test_json_vazio
        ✗ Teste falhou - verificar logs para detalhes
        → Indica problema no tratamento de JSON vazio

SKIPPED tests/models/test_reasoning.py::test_o3
        ⊘ Teste pulado
        → API key não disponível ou modelo caro

ERROR   tests/models/test_google.py::test_vision
        ! Erro na execução do teste
        → Problema de configuração ou dependência
```

### Relatórios

**HTML (`--report html`):**
- Salva em `test_reports/report.html`
- Abre no navegador para visualização
- Mostra testes agrupados por módulo
- Indica tempo de execução de cada teste
- Destaca falhas com stack trace

**JSON (`--report json`):**
- Salva em `test_reports/results.json`
- Inclui metadata de cada teste
- Útil para CI/CD e automação
- Formato:
```json
{
  "timestamp": "2026-01-29T10:30:00",
  "total": 50,
  "passed": 45,
  "failed": 3,
  "skipped": 2,
  "duration_ms": 12345,
  "tests": [...]
}
```

### Logs Estruturados

Os logs são salvos em `logs/pipeline_tests.jsonl` (JSON Lines):

```json
{"timestamp": "2026-01-29T10:30:00", "level": "INFO", "stage": "extract_gabarito", "provider": "openai", "model": "gpt-4o-mini", "message": "Iniciando extração"}
{"timestamp": "2026-01-29T10:30:05", "level": "ERROR", "stage": "extract_gabarito", "provider": "openai", "model": "gpt-4o-mini", "message": "JSON parsing failed", "error_type": "JSONDecodeError", "raw_response": "..."}
```

**Campos do log:**
- `timestamp`: Data/hora ISO
- `level`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `stage`: Etapa do pipeline (extract_gabarito, extract_aluno, corrigir, etc.)
- `provider`: Provider de IA usado
- `model`: Modelo específico
- `atividade_id`: ID da atividade (se aplicável)
- `aluno_id`: ID do aluno (se aplicável)
- `duration_ms`: Tempo de execução
- `message`: Mensagem descritiva
- `error_type`: Tipo de exceção (se erro)
- `raw_response`: Resposta bruta (se erro de parsing)

---

## Troubleshooting

### "API key não encontrada"

**Causa:** Variável de ambiente não configurada.

**Solução:**
```bash
# Windows
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-ant-...
set GOOGLE_API_KEY=AIza...

# Linux/Mac
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
```

Ou configurar em `data/api_keys.json`:
```json
{
  "openai": {"api_key": "sk-..."},
  "anthropic": {"api_key": "sk-ant-..."},
  "google": {"api_key": "AIza..."}
}
```

### "Timeout na requisição"

**Causa:** Modelo lento ou rede instável.

**Solução:**
```bash
# Aumentar timeout
python test_runner.py --timeout 180

# Usar modelo mais rápido
python test_runner.py --local --model gpt-4o-mini
python test_runner.py --local --model claude-haiku-4-5-20251001
```

### "JSON vazio retornado"

**Causa:** Modelo retornou resposta vazia ou mal formatada.

**Solução:**
1. Verificar logs para ver resposta raw
2. Pode indicar problema no prompt
3. Pode indicar modelo sobrecarregado
4. Tentar novamente ou usar outro modelo

### "ModuleNotFoundError"

**Causa:** Dependência não instalada.

**Solução:**
```bash
pip install pytest pytest-asyncio pytest-cov
pip install -r requirements.txt
```

### "Arquivo não encontrado"

**Causa:** Dados de teste não gerados.

**Solução:**
```bash
python test_runner.py --generate-data --mini
```

---

## Adicionando Novos Testes

### 1. Criar arquivo de teste

```python
# tests/scenarios/test_meu_cenario.py

import pytest
from tests.fixtures.document_factory import DocumentFactory

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_meu_cenario(document_factory, selected_provider):
    """Descrição do teste"""
    # Criar cenário
    cenario = document_factory.criar_cenario_completo(
        materia="Matemática",
        num_alunos=2
    )

    # Executar pipeline
    resultado = await executar_pipeline(cenario, selected_provider)

    # Verificações
    assert resultado.sucesso
    assert resultado.nota >= 0
```

### 2. Usar fixtures disponíveis

```python
# Fixtures disponíveis em conftest.py:
# - temp_data_dir: Diretório temporário
# - document_factory: Fábrica de documentos
# - selected_provider: Provider selecionado via CLI
# - api_keys_available: Verifica quais keys existem
# - is_render_environment: Detecta ambiente Render
# - mock_openai_chat_response: Mock de resposta OpenAI
# - mock_anthropic_chat_response: Mock de resposta Anthropic
# - mock_google_chat_response: Mock de resposta Google
```

### 3. Adicionar marcadores

```python
@pytest.mark.openai       # Específico para OpenAI
@pytest.mark.anthropic    # Específico para Anthropic
@pytest.mark.google       # Específico para Google
@pytest.mark.reasoning    # Modelos reasoning
@pytest.mark.e2e          # End-to-end
@pytest.mark.slow         # Testes lentos
@pytest.mark.expensive    # Modelos caros
@pytest.mark.error_handling  # Tratamento de erros
```

### 4. Documentar neste guia

Adicionar entrada na tabela "Novos Testes (Pipeline)" acima.

---

## Configuração pytest.ini

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
markers =
    openai: Testes específicos para OpenAI
    anthropic: Testes específicos para Anthropic
    google: Testes específicos para Google
    reasoning: Testes para modelos de raciocínio (o1, o3)
    e2e: Testes end-to-end
    slow: Testes lentos (>30s)
    expensive: Testes que usam modelos caros
    error_handling: Testes de tratamento de erros
    local_only: Testes que só rodam localmente
    render_compatible: Testes compatíveis com Render
```

---

## CI/CD

### GitHub Actions

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio pytest-cov
      - run: python test_runner.py --render --skip-expensive --report json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      - uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_reports/
```

### Render

```yaml
# render.yaml
services:
  - type: web
    name: prova-ai
    buildCommand: pip install -r requirements.txt && python test_runner.py --render --skip-expensive
```

---

## Arquivos Relevantes

- `test_runner.py`: CLI unificado de testes
- `logging_config.py`: Configuração de logging
- `pytest.ini`: Configuração pytest
- `tests/conftest.py`: Fixtures compartilhadas
- `tests/fixtures/document_factory.py`: Geração de documentos de teste
- `tests/models/`: Testes por tipo de modelo
- `tests/scenarios/`: Cenários de teste
