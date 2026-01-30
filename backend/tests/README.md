# Prova AI - Test Suite

> **Last Updated**: January 2026
> **Total Test Files**: 35+ organized test files

## Quick Start

```bash
# Run all tests with cheap models (recommended for development)
python test_runner.py --local

# Run with powerful models (higher cost)
python test_runner.py --local --full

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests only
pytest tests/models/ -v                  # Model provider tests
pytest tests/integration/ -v             # Integration tests
pytest tests/scenarios/ -v               # E2E scenarios

# Skip slow tests
pytest tests/ -v -m "not slow"

# Run with coverage
python test_runner.py --local --coverage
```

## Directory Structure

```
tests/
├── README.md              # This file
├── conftest.py            # Shared pytest fixtures and configuration
│
├── fixtures/              # Test data factories and generators
│   ├── document_factory.py
│   └── test_document_generation.py
│
├── unit/                  # Pure unit tests (no API calls, fast)
│   ├── test_api_keys.py           # API key encryption & env fallback
│   ├── test_chat_import.py        # Chat service imports
│   ├── test_executor_models.py    # ResultadoExecucao dataclass
│   ├── test_file_types.py         # File format handling
│   ├── test_fixes.py              # Bug fix validations
│   ├── test_frontend_logic.py     # Frontend-related logic
│   ├── test_model_selection.py    # Model selection logic
│   ├── test_pdf_report.py         # PDF report generation
│   └── test_pipeline_validation.py # JSON schema validation
│
├── models/                # AI model provider tests (require API keys)
│   ├── base_model_test.py         # Abstract base class for model tests
│   ├── test_anthropic.py          # Claude models (haiku, sonnet, opus)
│   ├── test_google.py             # Gemini models (2.5, 3-preview)
│   ├── test_haiku_tools.py        # Claude Haiku tool use
│   ├── test_models_stress.py      # Model stress testing
│   ├── test_openai_standard.py    # GPT models (4o, 5)
│   ├── test_reasoning.py          # Reasoning models (o3, o4-mini)
│   └── test_tool_use.py           # Tool/function calling
│
├── integration/           # External service integration tests
│   ├── test_api_quick.py          # Quick API health check
│   ├── test_binary_handling.py    # Binary data handling
│   ├── test_code_executor.py      # E2B code execution
│   ├── test_e2b_sandbox.py        # E2B sandbox sync
│   ├── test_endpoints.py          # API endpoint testing
│   ├── test_providers.py          # Provider configuration
│   ├── test_render_platform.py    # Render platform checks
│   └── test_storage_sync.py       # Supabase storage sync
│
├── ui/                    # UI/Browser tests (Playwright)
│   ├── __init__.py                # Module docstring
│   └── test_click_navigation.py   # Click navigation & JS loading tests
│
└── scenarios/             # End-to-end workflow tests
    ├── test_corrupted_docs.py     # Error handling for bad documents
    ├── test_downloads.py          # File download workflows
    ├── test_e2e_workflow.py       # Full multi-model workflow
    ├── test_happy_path.py         # Complete success pipeline
    ├── test_model_comparison.py   # Multi-model comparison
    ├── test_skip_steps.py         # Partial pipeline execution
    └── test_system_prompts.py     # System prompt variations
```

## UI Tests (Playwright)

Testes de interface que verificam navegação, cliques e carregamento de JS/CSS.

### O que os testes UI verificam

- **Carregamento de JavaScript**: Detecta erros 404 em arquivos JS (ex: `chat_system.js`)
- **Funções definidas**: Verifica que funções como `showChat()` existem
- **Navegação por cliques**: Testa que botões abrem os modais corretos
- **Responsividade**: Testa menu mobile e diferentes viewports
- **Regressões**: Testes específicos para bugs históricos

### Executar UI Tests

```bash
# Instalar Playwright (uma vez)
pip install playwright pytest-playwright pytest-asyncio
playwright install chromium

# Rodar testes UI (requer servidor local rodando)
# Terminal 1:
python -m uvicorn main_v2:app --port 8000

# Terminal 2:
pytest tests/ui/ -v

# Rodar com screenshots em caso de falha
pytest tests/ui/ -v --screenshot=only-on-failure --output=test-results/

# Rodar teste específico
pytest tests/ui/test_click_navigation.py::TestRegressions::test_static_files_are_served -v
```

### Bugs que os UI Tests detectam

| Teste | Bug detectado |
|-------|---------------|
| `test_static_files_are_served` | `app.mount("/static", ...)` comentado |
| `test_showChat_is_callable` | `ReferenceError: showChat is not defined` |
| `test_chat_button_opens_modal` | Modal não abre ao clicar |
| `test_no_reference_errors_on_load` | JS com erros de sintaxe |

## Model Configurations

The test runner supports different model tiers for cost/capability tradeoffs:

| Mode | Flag | OpenAI | Anthropic | Google | Use Case |
|------|------|--------|-----------|--------|----------|
| **Cheap** | `--cheap` (default) | gpt-5-mini | claude-haiku-4-5-20251001 | gemini-3-flash-preview | Development, CI |
| **Full** | `--full` | gpt-5 | claude-sonnet-4-5-20250929 | gemini-3-pro-preview | Production validation |
| **Legacy** | `--legacy` | gpt-4o-mini | claude-3-5-haiku-20241022 | gemini-2.5-flash | Cost-sensitive tests |
| **Reasoning** | `--reasoning` | o3-mini | claude-sonnet-4-5 | gemini-3-pro-preview | Complex logic tests |

## Pytest Markers

Use markers to filter tests:

```bash
pytest tests/ -m "e2e"           # End-to-end tests only
pytest tests/ -m "not slow"      # Skip slow tests (>30s)
pytest tests/ -m "not expensive" # Skip tests using expensive models
pytest tests/ -m "openai"        # OpenAI provider tests only
pytest tests/ -m "anthropic"     # Anthropic provider tests only
pytest tests/ -m "google"        # Google provider tests only
```

Available markers:
- `@pytest.mark.e2e` - End-to-end pipeline tests
- `@pytest.mark.slow` - Tests taking >30 seconds
- `@pytest.mark.expensive` - Tests using expensive models
- `@pytest.mark.openai` - OpenAI-specific tests
- `@pytest.mark.anthropic` - Anthropic-specific tests
- `@pytest.mark.google` - Google-specific tests
- `@pytest.mark.reasoning` - Reasoning model tests
- `@pytest.mark.local_only` - Tests that only run locally
- `@pytest.mark.render_compatible` - Tests safe for Render environment

## Model IDs Reference

> **Verified Working**: January 2026

### Google Gemini
- **Gemini 3** requires `-preview` suffix: `gemini-3-flash-preview`, `gemini-3-pro-preview`
- **Gemini 2.5** uses direct IDs: `gemini-2.5-flash`, `gemini-2.5-pro`
- **Gemini 2.0** DEPRECATED (EOL March 2026)

### Anthropic Claude
- `claude-opus-4-5-20251101` - Most capable
- `claude-sonnet-4-5-20250929` - Balanced
- `claude-haiku-4-5-20251001` - Fast & cheap

### OpenAI
- `gpt-5`, `gpt-5-mini` - Latest generation
- `o3`, `o3-mini`, `o4-mini` - Reasoning models (no temperature)
- `gpt-4o`, `gpt-4o-mini` - Previous generation

## Environment Variables

Required for full test coverage:

```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...
E2B_API_KEY=e2b_...           # For code execution tests
SUPABASE_URL=https://...      # For storage tests
SUPABASE_SERVICE_KEY=eyJ...   # For storage tests
```

Tests automatically skip if required API keys are missing.

## Adding New Tests

1. **Choose the right directory**:
   - `unit/` - No external dependencies, fast
   - `models/` - Tests AI model providers
   - `integration/` - Tests external services
   - `scenarios/` - Tests complete workflows

2. **Add docstrings** with requirements:
   ```python
   class TestMyFeature:
       """
       Tests for my feature.

       Requires: OPENAI_API_KEY
       Markers: @pytest.mark.slow, @pytest.mark.openai
       """
   ```

3. **Use appropriate markers**:
   ```python
   @pytest.mark.slow
   @pytest.mark.openai
   async def test_expensive_operation():
       ...
   ```

4. **Add to conftest.py** if you need shared fixtures.

## Troubleshooting

### Tests Skip Unexpectedly
- Check API keys are set in environment
- Run with `-v` to see skip reasons

### Timeout Errors
- Default timeout is 120s
- Use `--timeout 300` for slower tests

### Import Errors
- Ensure you're in the `backend/` directory
- Check `conftest.py` for path setup

## Related Documentation

- [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) - Detailed testing guide
- [MODELS_REFERENCE.md](docs/MODELS_REFERENCE.md) - Model capabilities reference
- [API_UNIFICATION_README.md](../API_UNIFICATION_README.md) - API consolidation guide
