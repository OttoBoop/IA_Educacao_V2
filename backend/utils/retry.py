"""
Utilitário de retry com backoff exponencial para chamadas de API.

Trata erros temporários (429, 5xx) com retry automático.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Callable, TypeVar, Set, Optional, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErroRetryable(Exception):
    """Exceção para erros que podem ser retentados"""
    def __init__(self, mensagem: str, codigo: int = None, retry_after: int = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.retry_after = retry_after


@dataclass
class RetryConfig:
    """Configuração de retry"""
    max_tentativas: int = 3
    backoff_base: float = 2.0  # segundos
    backoff_max: float = 60.0  # máximo de espera
    backoff_multiplicador: float = 2.0  # fator exponencial
    erros_retryable: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})

    def calcular_espera(self, tentativa: int, retry_after: int = None) -> float:
        """Calcula tempo de espera para a tentativa"""
        if retry_after and retry_after > 0:
            # Usar Retry-After header se disponível
            return min(retry_after, self.backoff_max)

        # Backoff exponencial: base * (multiplicador ^ tentativa)
        espera = self.backoff_base * (self.backoff_multiplicador ** tentativa)
        return min(espera, self.backoff_max)


def _extrair_codigo_erro(erro_str: str) -> Optional[int]:
    """Extrai código HTTP de mensagem de erro"""
    if not erro_str:
        return None

    # Padrões comuns: "Erro API Anthropic: 429", "HTTP 500", etc.
    import re
    match = re.search(r'\b(4\d{2}|5\d{2})\b', erro_str)
    if match:
        return int(match.group(1))
    return None


def _erro_retryable(erro: str, codigos_retryable: Set[int]) -> bool:
    """Verifica se erro é retryable baseado no código HTTP"""
    codigo = _extrair_codigo_erro(erro)
    return codigo in codigos_retryable if codigo else False


async def retry_com_backoff(
    func: Callable,
    config: RetryConfig = None,
    *args,
    **kwargs
) -> Any:
    """
    Executa função assíncrona com retry e backoff exponencial.

    Args:
        func: Função assíncrona a executar
        config: Configuração de retry (usa padrão se None)
        *args, **kwargs: Argumentos para a função

    Returns:
        Resultado da função se sucesso

    Raises:
        ErroRetryable: Se todas tentativas falharam com erro retryable
        Exception: Se erro não retryable ocorrer
    """
    config = config or RetryConfig()
    ultima_excecao = None
    ultimo_resultado = None

    for tentativa in range(config.max_tentativas):
        try:
            resultado = await func(*args, **kwargs)

            # Verificar se resultado indica erro retryable
            # (para objetos que retornam sucesso=False ao invés de exceção)
            if hasattr(resultado, 'sucesso') and not resultado.sucesso:
                erro_str = getattr(resultado, 'erro', '') or ''
                codigo = getattr(resultado, 'erro_codigo', None) or _extrair_codigo_erro(erro_str)
                retry_after = getattr(resultado, 'retry_after', None)

                if codigo and codigo in config.erros_retryable:
                    ultimo_resultado = resultado

                    if tentativa < config.max_tentativas - 1:
                        espera = config.calcular_espera(tentativa, retry_after)
                        logger.warning(
                            f"Erro retryable (código {codigo}), "
                            f"tentativa {tentativa + 1}/{config.max_tentativas}, "
                            f"aguardando {espera:.1f}s..."
                        )
                        await asyncio.sleep(espera)
                        continue
                    else:
                        logger.error(
                            f"Erro retryable (código {codigo}) após "
                            f"{config.max_tentativas} tentativas"
                        )

                # Erro não retryable ou tentativas esgotadas
                return resultado

            # Sucesso!
            if tentativa > 0:
                logger.info(f"Sucesso na tentativa {tentativa + 1}")
            return resultado

        except ErroRetryable as e:
            ultima_excecao = e

            if tentativa < config.max_tentativas - 1:
                espera = config.calcular_espera(tentativa, e.retry_after)
                logger.warning(
                    f"ErroRetryable: {e}, "
                    f"tentativa {tentativa + 1}/{config.max_tentativas}, "
                    f"aguardando {espera:.1f}s..."
                )
                await asyncio.sleep(espera)
            else:
                logger.error(f"ErroRetryable após {config.max_tentativas} tentativas: {e}")
                raise

        except Exception as e:
            # Erro não esperado - não faz retry
            logger.error(f"Erro não retryable: {type(e).__name__}: {e}")
            raise

    # Se chegou aqui, todas tentativas falharam
    if ultimo_resultado is not None:
        return ultimo_resultado

    if ultima_excecao:
        raise ultima_excecao

    raise Exception("Retry esgotado sem resultado")


class RetryableHTTPClient:
    """
    Wrapper para httpx.AsyncClient com retry automático.

    Uso:
        client = RetryableHTTPClient(config=RetryConfig(max_tentativas=3))
        response = await client.post(url, json=data, headers=headers)
    """

    def __init__(self, config: RetryConfig = None, timeout: float = 180.0):
        self.config = config or RetryConfig()
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> 'httpx.Response':
        """Executa request com retry"""
        import httpx

        ultima_excecao = None

        for tentativa in range(self.config.max_tentativas):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, **kwargs)

                    # Verificar se é erro retryable
                    if response.status_code in self.config.erros_retryable:
                        retry_after = response.headers.get('Retry-After')
                        retry_after_int = int(retry_after) if retry_after and retry_after.isdigit() else None

                        if tentativa < self.config.max_tentativas - 1:
                            espera = self.config.calcular_espera(tentativa, retry_after_int)
                            logger.warning(
                                f"HTTP {response.status_code} em {url}, "
                                f"tentativa {tentativa + 1}/{self.config.max_tentativas}, "
                                f"aguardando {espera:.1f}s..."
                            )
                            await asyncio.sleep(espera)
                            continue

                    return response

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                ultima_excecao = e

                if tentativa < self.config.max_tentativas - 1:
                    espera = self.config.calcular_espera(tentativa)
                    logger.warning(
                        f"Erro de conexão ({type(e).__name__}), "
                        f"tentativa {tentativa + 1}/{self.config.max_tentativas}, "
                        f"aguardando {espera:.1f}s..."
                    )
                    await asyncio.sleep(espera)
                else:
                    raise

        if ultima_excecao:
            raise ultima_excecao

        raise Exception("Retry esgotado")

    async def get(self, url: str, **kwargs) -> 'httpx.Response':
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> 'httpx.Response':
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> 'httpx.Response':
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> 'httpx.Response':
        return await self._request("DELETE", url, **kwargs)
