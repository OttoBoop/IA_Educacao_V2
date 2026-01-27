"""
Abstração de Providers de IA - Permite trocar facilmente entre diferentes modelos/APIs

Cada provider implementa a mesma interface, permitindo:
1. Trocar a IA usada em cada etapa do pipeline
2. Comparar resultados entre diferentes IAs
3. Rastrear qual IA gerou cada output
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path


@dataclass
class AIResponse:
    """Resposta padronizada de qualquer provider de IA"""
    content: str
    provider: str
    model: str
    tokens_used: int
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "provider": self.provider,
            "model": self.model,
            "tokens_used": self.tokens_used,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


def _format_httpx_error(exc: "httpx.HTTPStatusError") -> str:
    response = exc.response
    request = exc.request
    body = response.text.strip()
    if len(body) > 2000:
        body = f"{body[:2000]}... (truncado)"
    request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
    request_id_info = f" request_id={request_id}" if request_id else ""
    return (
        f"Erro HTTP {response.status_code} em {request.method} {request.url}.{request_id_info} "
        f"Resposta: {body}"
    )


class AIProvider(ABC):
    """Interface base para todos os providers de IA"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def complete(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 4096) -> AIResponse:
        """Gera uma completion dado um prompt"""
        pass
    
    @abstractmethod
    async def analyze_document(self, 
                               file_path: str,
                               instruction: str) -> AIResponse:
        """Analisa um documento (PDF, DOCX, imagem)"""
        pass
    
    def get_identifier(self) -> str:
        """Retorna identificador único para rastreamento"""
        return f"{self.name}_{self.model}"


class OpenAIProvider(AIProvider):
    """Provider para OpenAI (GPT-4, GPT-4o, etc.)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        super().__init__(api_key, model)
        self.base_url = "https://api.openai.com/v1"
    
    async def complete(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 4096) -> AIResponse:
        import httpx
        import time
        
        start = time.time()
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(_format_httpx_error(exc)) from exc
        
        latency = (time.time() - start) * 1000
        
        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            provider="openai",
            model=self.model,
            tokens_used=data["usage"]["total_tokens"],
            input_tokens=data["usage"].get("prompt_tokens", 0),
            output_tokens=data["usage"].get("completion_tokens", 0),
            latency_ms=latency,
            metadata={"finish_reason": data["choices"][0]["finish_reason"]}
        )
    
    async def analyze_document(self, 
                               file_path: str,
                               instruction: str) -> AIResponse:
        import httpx
        import base64
        import time
        
        start = time.time()
        
        # Determinar tipo de arquivo
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            # Imagem - usar vision
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }[ext]
            
            messages = [{
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"
                        }
                    }
                ]
            }]
        else:
            # Texto - extrair conteúdo primeiro
            content = await self._extract_text(file_path)
            messages = [{
                "role": "user",
                "content": f"{instruction}\n\n---\nConteúdo do documento:\n{content}"
            }]
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": 4096
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(_format_httpx_error(exc)) from exc
        
        latency = (time.time() - start) * 1000
        
        return AIResponse(
            content=data["choices"][0]["message"]["content"],
            provider="openai",
            model=self.model,
            tokens_used=data["usage"]["total_tokens"],
            input_tokens=data["usage"].get("prompt_tokens", 0),
            output_tokens=data["usage"].get("completion_tokens", 0),
            latency_ms=latency,
            metadata={
                "file_analyzed": file_path,
                "finish_reason": data["choices"][0]["finish_reason"]
            }
        )
    
    async def _extract_text(self, file_path: str) -> str:
        """Extrai texto de diferentes formatos"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            return text
        elif ext == '.docx':
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            raise ValueError(f"Formato não suportado: {ext}")


class AnthropicProvider(AIProvider):
    """Provider para Anthropic (Claude)"""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        super().__init__(api_key, model)
        self.base_url = "https://api.anthropic.com/v1"
    
    async def complete(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 4096) -> AIResponse:
        import httpx
        import time
        
        start = time.time()
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(_format_httpx_error(exc)) from exc
        
        latency = (time.time() - start) * 1000
        
        return AIResponse(
            content=data["content"][0]["text"],
            provider="anthropic",
            model=self.model,
            tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            input_tokens=data["usage"].get("input_tokens", 0),
            output_tokens=data["usage"].get("output_tokens", 0),
            latency_ms=latency,
            metadata={"stop_reason": data["stop_reason"]}
        )
    
    async def analyze_document(self, 
                               file_path: str,
                               instruction: str) -> AIResponse:
        import httpx
        import base64
        import time
        
        start = time.time()
        ext = Path(file_path).suffix.lower()
        
        if ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            with open(file_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }[ext]
            
            content = [
                {"type": "text", "text": instruction},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": mime_type,
                        "data": image_data
                    }
                }
            ]
        elif ext == '.pdf':
            with open(file_path, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode()
            
            content = [
                {"type": "text", "text": instruction},
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data
                    }
                }
            ]
        else:
            # Extrair texto para outros formatos
            text_content = await self._extract_text(file_path)
            content = [{"type": "text", "text": f"{instruction}\n\n---\n{text_content}"}]
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "messages": [{"role": "user", "content": content}]
                    },
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as exc:
                raise RuntimeError(_format_httpx_error(exc)) from exc
        
        latency = (time.time() - start) * 1000
        
        return AIResponse(
            content=data["content"][0]["text"],
            provider="anthropic",
            model=self.model,
            tokens_used=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            input_tokens=data["usage"].get("input_tokens", 0),
            output_tokens=data["usage"].get("output_tokens", 0),
            latency_ms=latency,
            metadata={
                "file_analyzed": file_path,
                "stop_reason": data["stop_reason"]
            }
        )
    
    async def _extract_text(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.docx':
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            raise ValueError(f"Formato não suportado para extração de texto: {ext}")


class LocalLLMProvider(AIProvider):
    """Provider para LLMs locais via Ollama ou similar"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        super().__init__("", model)
        self.base_url = base_url
    
    async def complete(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       temperature: float = 0.7,
                       max_tokens: int = 4096) -> AIResponse:
        import httpx
        import time
        
        start = time.time()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=300.0
            )
            response.raise_for_status()
            data = response.json()
        
        latency = (time.time() - start) * 1000
        
        return AIResponse(
            content=data["response"],
            provider="ollama",
            model=self.model,
            tokens_used=data.get("eval_count", 0) + data.get("prompt_eval_count", 0),
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            latency_ms=latency,
            metadata={"done": data.get("done", True)}
        )
    
    async def analyze_document(self, 
                               file_path: str,
                               instruction: str) -> AIResponse:
        # Para modelos locais, extrair texto primeiro
        text = await self._extract_text(file_path)
        return await self.complete(f"{instruction}\n\n---\n{text}")
    
    async def _extract_text(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == '.pdf':
            import fitz
            doc = fitz.open(file_path)
            return "\n".join([page.get_text() for page in doc])
        elif ext == '.docx':
            from docx import Document
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        else:
            raise ValueError(f"Formato não suportado: {ext}")


class AIProviderRegistry:
    """Registro central de providers - permite trocar IAs facilmente"""
    
    def __init__(self):
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider: Optional[str] = None
    
    def register(self, name: str, provider: AIProvider, set_default: bool = False):
        """Registra um provider com um nome"""
        self.providers[name] = provider
        if set_default or self.default_provider is None:
            self.default_provider = name
    
    def get(self, name: Optional[str] = None) -> AIProvider:
        """Obtém um provider pelo nome ou retorna o default"""
        if name is None:
            name = self.default_provider
        if name not in self.providers:
            raise ValueError(f"Provider '{name}' não registrado")
        return self.providers[name]
    
    def list_providers(self) -> List[str]:
        """Lista todos os providers registrados"""
        return list(self.providers.keys())
    
    def get_provider_info(self) -> List[Dict[str, str]]:
        """Retorna informações de todos os providers"""
        return [
            {
                "name": name,
                "provider_type": p.name,
                "model": p.model,
                "identifier": p.get_identifier()
            }
            for name, p in self.providers.items()
        ]


# Instância global do registry
ai_registry = AIProviderRegistry()


def setup_providers_from_env():
    """Configura providers a partir de variáveis de ambiente"""
    
    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        ai_registry.register(
            "openai-gpt4o",
            OpenAIProvider(os.getenv("OPENAI_API_KEY"), "gpt-4o"),
            set_default=True
        )
        ai_registry.register(
            "openai-gpt4o-mini",
            OpenAIProvider(os.getenv("OPENAI_API_KEY"), "gpt-4o-mini")
        )
    
    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        ai_registry.register(
            "claude-sonnet",
            AnthropicProvider(os.getenv("ANTHROPIC_API_KEY"), "claude-sonnet-4-20250514")
        )
        ai_registry.register(
            "claude-haiku",
            AnthropicProvider(os.getenv("ANTHROPIC_API_KEY"), "claude-haiku-4-5-20251001")
        )
    
    # Ollama (local)
    ai_registry.register(
        "ollama-llama3",
        LocalLLMProvider(model="llama3")
    )
