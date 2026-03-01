"""
NOVO CR - Sistema de Logging Estruturado

Fornece logging JSON estruturado para rastreamento de pipeline.
Cada log inclui contexto completo: stage, provider, model, IDs, etc.

Uso:
    from logging_config import get_logger, setup_logging

    # Setup inicial
    setup_logging(level="INFO", log_dir=Path("logs"))

    # Obter logger
    logger = get_logger("pipeline.executor")

    # Logging com contexto
    logger.info("Iniciando extração", stage="extract_gabarito", provider="openai")
    logger.error("Falha no parsing", error=e, stage="corrigir", raw_response=resp[:500])
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict


# ============================================================
# DATACLASSES
# ============================================================

@dataclass
class LogContext:
    """Contexto para uma entrada de log"""
    stage: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    atividade_id: Optional[str] = None
    aluno_id: Optional[str] = None
    documento_id: Optional[str] = None
    duration_ms: Optional[float] = None
    tokens_used: Optional[int] = None
    error_type: Optional[str] = None
    raw_response: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict, removendo valores None"""
        result = {}
        for key, value in asdict(self).items():
            if value is not None and key != "extra":
                result[key] = value
            elif key == "extra" and value:
                result.update(value)
        return result


# ============================================================
# JSON FORMATTER
# ============================================================

class JSONFormatter(logging.Formatter):
    """
    Formatter que produz logs em JSON estruturado.

    Formato de saída:
    {
        "timestamp": "2026-01-29T10:30:00.123456",
        "level": "ERROR",
        "logger": "pipeline.executor",
        "message": "JSON parsing failed",
        "stage": "extract_gabarito",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "error_type": "JSONDecodeError",
        ...
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Adicionar contexto do pipeline se disponível
        context_fields = [
            "stage", "provider", "model", "atividade_id", "aluno_id",
            "documento_id", "duration_ms", "tokens_used", "error_type",
            "raw_response"
        ]

        for field in context_fields:
            value = getattr(record, field, None)
            if value is not None:
                log_data[field] = value

        # Adicionar campos extras
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)

        # Informações de exceção
        if record.exc_info:
            log_data["error_type"] = record.exc_info[0].__name__
            log_data["error_message"] = str(record.exc_info[1])
            log_data["traceback"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """
    Formatter para console com cores e formatação legível.
    """

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET

        # Timestamp curto
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Contexto
        parts = [f"{color}[{timestamp}] {record.levelname:8}{reset}"]

        # Stage se disponível
        stage = getattr(record, "stage", None)
        if stage:
            parts.append(f"[{stage}]")

        # Provider/model se disponível
        provider = getattr(record, "provider", None)
        model = getattr(record, "model", None)
        if provider or model:
            provider_info = f"{provider or ''}/{model or ''}"
            parts.append(f"({provider_info})")

        # Mensagem
        parts.append(record.getMessage())

        # Duration se disponível
        duration = getattr(record, "duration_ms", None)
        if duration:
            parts.append(f"({duration:.0f}ms)")

        return " ".join(parts)


# ============================================================
# PIPELINE LOGGER
# ============================================================

class PipelineLogger:
    """
    Logger customizado para o pipeline com suporte a contexto.

    Uso:
        logger = PipelineLogger("pipeline.executor")
        logger.info("Iniciando", stage="extract_gabarito")
        logger.error("Falha", error=e, raw_response=resp[:500])
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: int, msg: str, error: Optional[Exception] = None, **context):
        """Log interno com contexto"""
        extra = {}

        # Adicionar contexto como atributos do record
        for key, value in context.items():
            extra[key] = value

        # Preparar record
        self.logger.log(
            level,
            msg,
            exc_info=error,
            extra=extra
        )

    def debug(self, msg: str, **context):
        self._log(logging.DEBUG, msg, **context)

    def info(self, msg: str, **context):
        self._log(logging.INFO, msg, **context)

    def warning(self, msg: str, **context):
        self._log(logging.WARNING, msg, **context)

    def error(self, msg: str, error: Optional[Exception] = None, **context):
        self._log(logging.ERROR, msg, error=error, **context)

    def critical(self, msg: str, error: Optional[Exception] = None, **context):
        self._log(logging.CRITICAL, msg, error=error, **context)


# ============================================================
# CONTEXT MANAGER
# ============================================================

class LogContextManager:
    """
    Context manager para adicionar contexto a todos os logs em um bloco.

    Uso:
        with LogContextManager(stage="corrigir", atividade_id="123"):
            logger.info("Processando...")  # Automaticamente inclui stage e atividade_id
    """

    _context: Dict[str, Any] = {}

    def __init__(self, **context):
        self.new_context = context
        self.old_context = {}

    def __enter__(self):
        self.old_context = LogContextManager._context.copy()
        LogContextManager._context.update(self.new_context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        LogContextManager._context = self.old_context

    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        return cls._context.copy()


# ============================================================
# SETUP FUNCTIONS
# ============================================================

def setup_logging(
    level: str = "INFO",
    log_dir: Optional[Path] = None,
    console_output: bool = True,
    file_output: bool = True,
    json_format: bool = True,
    log_filename: str = "pipeline.jsonl"
):
    """
    Configura logging global.

    Args:
        level: Nível mínimo (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Diretório para arquivos de log
        console_output: Mostrar no console
        file_output: Salvar em arquivo
        json_format: Usar formato JSON (vs texto)
        log_filename: Nome do arquivo de log
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Limpar handlers existentes
    root_logger.handlers.clear()

    # Handler para console
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        if json_format:
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(ConsoleFormatter())

        root_logger.addHandler(console_handler)

    # Handler para arquivo
    if file_output and log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / log_filename
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(JSONFormatter())

        root_logger.addHandler(file_handler)


def get_logger(name: str) -> PipelineLogger:
    """
    Obtém um logger para o módulo especificado.

    Args:
        name: Nome do logger (ex: "pipeline.executor")

    Returns:
        PipelineLogger configurado
    """
    return PipelineLogger(name)


# ============================================================
# DECORATORS
# ============================================================

def log_execution(
    logger: PipelineLogger,
    stage: Optional[str] = None,
    log_args: bool = False
):
    """
    Decorator para logar execução de funções.

    Uso:
        @log_execution(logger, stage="corrigir")
        async def corrigir_questao(questao_id: str):
            ...
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            func_name = func.__name__

            context = {"stage": stage} if stage else {}
            if log_args:
                context["args"] = str(args)[:200]
                context["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Iniciando {func_name}", **context)

            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.info(f"Concluído {func_name}", duration_ms=duration, **context)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(
                    f"Erro em {func_name}: {str(e)}",
                    error=e,
                    duration_ms=duration,
                    **context
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            func_name = func.__name__

            context = {"stage": stage} if stage else {}
            if log_args:
                context["args"] = str(args)[:200]
                context["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Iniciando {func_name}", **context)

            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start) * 1000
                logger.info(f"Concluído {func_name}", duration_ms=duration, **context)
                return result
            except Exception as e:
                duration = (time.time() - start) * 1000
                logger.error(
                    f"Erro em {func_name}: {str(e)}",
                    error=e,
                    duration_ms=duration,
                    **context
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================
# UTILITIES
# ============================================================

def truncate_for_log(text: str, max_length: int = 500) -> str:
    """Trunca texto para logging, preservando início e fim."""
    if len(text) <= max_length:
        return text

    half = max_length // 2
    return f"{text[:half]}... [truncado {len(text) - max_length} chars] ...{text[-half:]}"


def format_duration(ms: float) -> str:
    """Formata duração em formato legível."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        minutes = int(ms // 60000)
        seconds = (ms % 60000) / 1000
        return f"{minutes}m{seconds:.0f}s"


# ============================================================
# SINGLETON LOGGERS
# ============================================================

# Loggers pré-configurados para uso comum
_loggers: Dict[str, PipelineLogger] = {}


def pipeline_logger() -> PipelineLogger:
    """Logger para o pipeline principal."""
    if "pipeline" not in _loggers:
        _loggers["pipeline"] = get_logger("pipeline")
    return _loggers["pipeline"]


def executor_logger() -> PipelineLogger:
    """Logger para o executor."""
    if "executor" not in _loggers:
        _loggers["executor"] = get_logger("pipeline.executor")
    return _loggers["executor"]


def provider_logger() -> PipelineLogger:
    """Logger para providers de IA."""
    if "provider" not in _loggers:
        _loggers["provider"] = get_logger("pipeline.provider")
    return _loggers["provider"]


# ============================================================
# INICIALIZAÇÃO DEFAULT
# ============================================================

# Setup básico se importado diretamente
if __name__ != "__main__":
    # Configuração mínima para não quebrar imports
    logging.basicConfig(level=logging.WARNING)
