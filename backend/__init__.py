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
    VectorStore,
    DocumentType,
    Questao,
    Correcao,
    storage,
    vector_store
)

from .pipeline import (
    CorrectionPipeline,
    PipelineConfig,
    PipelineStage,
    PipelineResult
)

__version__ = "0.1.0"
__all__ = [
    "AIProvider", "AIResponse", "OpenAIProvider", "AnthropicProvider", 
    "LocalLLMProvider", "ai_registry", "setup_providers_from_env",
    "StorageManager", "VectorStore", "DocumentType", "Questao", "Correcao",
    "storage", "vector_store",
    "CorrectionPipeline", "PipelineConfig", "PipelineStage", "PipelineResult"
]
