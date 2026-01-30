"""
Prova AI Backend
Sistema de correção automatizada de provas com múltiplos providers de IA
"""

from .ai_providers import (
    AIProvider,
    AIResponse,
    OpenAIProvider,
    AnthropicProvider,
    LocalLLMProvider,
    ai_registry,
    setup_providers_from_env
)

from .storage import (
    StorageManager,
    storage
)

from .models import (
    TipoDocumento,
    Materia,
    Turma,
    Aluno,
    Atividade,
    Documento
)

from .executor import (
    PipelineExecutor,
    pipeline_executor,
    EtapaProcessamento,
    ResultadoExecucao
)

__version__ = "0.1.0"
__all__ = [
    # AI Providers
    "AIProvider", "AIResponse", "OpenAIProvider", "AnthropicProvider",
    "LocalLLMProvider", "ai_registry", "setup_providers_from_env",
    # Storage
    "StorageManager", "storage",
    # Models
    "TipoDocumento", "Materia", "Turma", "Aluno", "Atividade", "Documento",
    # Pipeline Executor
    "PipelineExecutor", "pipeline_executor", "EtapaProcessamento", "ResultadoExecucao"
]
