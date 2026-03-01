"""
NOVO CR - Sistema de Chat v2.1

Melhorias:
- API Keys por empresa (não por provider)
- Parâmetros flexíveis por modelo
- Capacidades específicas por modelo
- Leitura e criação de documentos
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Tuple
from pathlib import Path
from enum import Enum
import json
import os
import re
import hashlib
import httpx

from models import TipoDocumento
from storage import storage
from tools import ToolRegistry, ToolCall, ToolResult, ToolExecutionContext


# ============================================================
# DIRETÓRIO BASE (para paths absolutos, compatível com Render)
# ============================================================
BASE_DIR = Path(__file__).parent


# ============================================================
# TIPOS DE PROVIDERS E EMPRESAS
# ============================================================

class ProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GROQ = "groq"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    XAI = "xai"
    PERPLEXITY = "perplexity"
    COHERE = "cohere"
    VLLM = "vllm"
    LMSTUDIO = "lmstudio"
    CUSTOM = "custom"


# URLs padrão por tipo
DEFAULT_URLS = {
    ProviderType.OPENAI: "https://api.openai.com/v1",
    ProviderType.ANTHROPIC: "https://api.anthropic.com/v1",
    ProviderType.GOOGLE: "https://generativelanguage.googleapis.com/v1beta",
    ProviderType.OLLAMA: "http://localhost:11434/api",
    ProviderType.OPENROUTER: "https://openrouter.ai/api/v1",
    ProviderType.GROQ: "https://api.groq.com/openai/v1",
    ProviderType.MISTRAL: "https://api.mistral.ai/v1",
    ProviderType.DEEPSEEK: "https://api.deepseek.com/v1",
    ProviderType.XAI: "https://api.x.ai/v1",
    ProviderType.PERPLEXITY: "https://api.perplexity.ai",
    ProviderType.COHERE: "https://api.cohere.ai/v1",
    ProviderType.VLLM: "http://localhost:8000/v1",
    ProviderType.LMSTUDIO: "http://localhost:1234/v1",
}

# Modelos populares por provider (atualizado com documento Jan 2026)
MODELOS_SUGERIDOS = {
    ProviderType.OPENAI: [
        # GPT-5 Series (Newest)
        {"id": "gpt-5.2", "nome": "GPT-5.2", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5.2-pro", "nome": "GPT-5.2 Pro", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5", "nome": "GPT-5", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5-mini", "nome": "GPT-5 Mini", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5-nano", "nome": "GPT-5 Nano", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5-pro", "nome": "GPT-5 Pro", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-5-image", "nome": "GPT-5 Image", "suporta_vision": True, "suporta_tools": True},
        # GPT-4 Series
        {"id": "gpt-4o", "nome": "GPT-4o", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-4o-mini", "nome": "GPT-4o Mini", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-4.1", "nome": "GPT-4.1", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-4.1-mini", "nome": "GPT-4.1 Mini", "suporta_vision": True, "suporta_tools": True},
        {"id": "gpt-4.1-nano", "nome": "GPT-4.1 Nano", "suporta_vision": True, "suporta_tools": True},
        # Reasoning Models
        # Deprecated: 'o1', 'o1-pro' (removed as deprecated)
        {"id": "o3", "nome": "o3 (Reasoning)", "suporta_temperature": False, "suporta_tools": True, "suporta_reasoning": True},
        {"id": "o3-mini", "nome": "o3 Mini", "suporta_temperature": False, "suporta_tools": True, "suporta_reasoning": True},
        {"id": "o4-mini", "nome": "o4 Mini", "suporta_temperature": False, "suporta_tools": True, "suporta_reasoning": True},
    ],
    ProviderType.ANTHROPIC: [
        {"id": "claude-opus-4-5-20251101", "nome": "Claude Opus 4.5", "suporta_vision": True, "suporta_tools": True, "suporta_extended_thinking": True},
        {"id": "claude-sonnet-4-5-20250929", "nome": "Claude Sonnet 4.5", "suporta_vision": True, "suporta_tools": True, "suporta_extended_thinking": True},
        {"id": "claude-haiku-4-5-20251001", "nome": "Claude Haiku 4.5", "suporta_vision": True, "suporta_tools": True, "suporta_extended_thinking": True},
        {"id": "claude-3-5-sonnet-20241022", "nome": "Claude 3.5 Sonnet", "suporta_vision": True, "suporta_tools": True},
        {"id": "claude-3-5-haiku-20241022", "nome": "Claude 3.5 Haiku", "suporta_vision": True, "suporta_tools": True},
    ],
    # Google Gemini models - verified working endpoints as of January 2026
    # NOTE: Gemini 3 models require "-preview" suffix (unlike Gemini 2.x which uses direct IDs)
    # API: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
    # Gemini 2.0 deprecated, shutting down March 31, 2026
    ProviderType.GOOGLE: [
        # Gemini 3 series (preview) - require "-preview" suffix
        {"id": "gemini-3-pro-preview", "nome": "Gemini 3 Pro", "suporta_vision": True, "suporta_tools": True, "suporta_reasoning": True},
        {"id": "gemini-3-flash-preview", "nome": "Gemini 3 Flash", "suporta_vision": True, "suporta_tools": True, "suporta_reasoning": True},
        # Gemini 2.5 series (stable) - direct model IDs work
        {"id": "gemini-2.5-pro", "nome": "Gemini 2.5 Pro", "suporta_vision": True, "suporta_tools": True, "suporta_reasoning": True},
        {"id": "gemini-2.5-flash", "nome": "Gemini 2.5 Flash", "suporta_vision": True, "suporta_tools": True, "suporta_reasoning": True},
        {"id": "gemini-2.5-flash-lite", "nome": "Gemini 2.5 Flash Lite", "suporta_vision": True, "suporta_tools": False},
        # Gemini 2.0 series (deprecated - EOL March 2026)
        {"id": "gemini-2.0-flash", "nome": "Gemini 2.0 Flash (Deprecated)", "suporta_vision": True, "suporta_tools": True},
    ],
    ProviderType.OLLAMA: [
        {"id": "llama3.2", "nome": "Llama 3.2", "suporta_vision": True},
        {"id": "llama3.1", "nome": "Llama 3.1"},
        {"id": "mistral", "nome": "Mistral"},
        {"id": "codellama", "nome": "Code Llama"},
        {"id": "mixtral", "nome": "Mixtral"},
    ],
    ProviderType.GROQ: [
        {"id": "llama-3.3-70b-versatile", "nome": "Llama 3.3 70B", "suporta_tools": True},
        {"id": "mixtral-8x7b-32768", "nome": "Mixtral 8x7B", "suporta_tools": True},
    ],
    ProviderType.MISTRAL: [
        {"id": "mistral-large-latest", "nome": "Mistral Large 2", "suporta_tools": True},
        {"id": "mistral-small-latest", "nome": "Mistral Small", "suporta_tools": True},
        {"id": "codestral-latest", "nome": "Codestral", "suporta_tools": True},
    ],
    ProviderType.OPENROUTER: [
        {"id": "openai/gpt-4o", "nome": "GPT-4o (via OpenRouter)", "suporta_vision": True, "suporta_tools": True},
        {"id": "anthropic/claude-3.5-sonnet", "nome": "Claude 3.5 Sonnet (via OpenRouter)", "suporta_vision": True, "suporta_tools": True},
        {"id": "meta-llama/llama-3.1-405b-instruct", "nome": "Llama 3.1 405B", "suporta_tools": True},
    ],
    ProviderType.DEEPSEEK: [
        {"id": "deepseek-chat", "nome": "DeepSeek Chat", "suporta_tools": True},
        {"id": "deepseek-reasoner", "nome": "DeepSeek Reasoner (R1)", "suporta_temperature": False, "suporta_reasoning": True},
    ],
    ProviderType.XAI: [
        {"id": "grok-4", "nome": "Grok 4", "suporta_vision": True, "suporta_tools": True},
        {"id": "grok-4-fast", "nome": "Grok 4 Fast", "suporta_vision": True, "suporta_tools": True},
    ],
    ProviderType.PERPLEXITY: [
        {"id": "sonar", "nome": "Sonar", "suporta_search": True},
        {"id": "sonar-pro", "nome": "Sonar Pro", "suporta_search": True},
        {"id": "sonar-deep-research", "nome": "Sonar Deep Research", "suporta_search": True, "suporta_reasoning": True},
    ],
    ProviderType.COHERE: [
        {"id": "command-r-plus", "nome": "Command R+", "suporta_tools": True, "suporta_rag": True},
        {"id": "command-r", "nome": "Command R", "suporta_tools": True, "suporta_rag": True},
    ],
    ProviderType.VLLM: [],
    ProviderType.LMSTUDIO: [],
}

# Modelos que usam reasoning_effort ao invés de temperature
# Deprecated: 'o1', 'o1-pro' (removidos pois estão deprecated)
REASONING_MODELS = ['o3', 'o3-mini', 'o3-pro', 'o4-mini', 'gpt-5', 'gpt-5-mini', 'gpt-5-nano', 'gpt-5.1', 'gpt-5.2', 'deepseek-reasoner']


# ============================================================
# API KEYS POR EMPRESA (COM CRIPTOGRAFIA)
# ============================================================

# Criptografia é OBRIGATÓRIA para API keys
from cryptography.fernet import Fernet


@dataclass
class ApiKeyConfig:
    """Configuração de API Key por empresa"""
    id: str
    empresa: ProviderType
    api_key: str  # Armazenado descriptografado em memória
    nome_exibicao: str = ""
    ativo: bool = True
    criado_em: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "empresa": self.empresa.value,
            "nome_exibicao": self.nome_exibicao or self.empresa.value.title(),
            "api_key_preview": self.api_key[:8] + "..." + self.api_key[-4:] if len(self.api_key) > 12 else "***",
            "ativo": self.ativo,
            "criado_em": self.criado_em.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiKeyConfig':
        return cls(
            id=data["id"],
            empresa=ProviderType(data["empresa"]),
            api_key=data.get("api_key", ""),
            nome_exibicao=data.get("nome_exibicao", ""),
            ativo=data.get("ativo", True),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now()
        )


class ApiKeyManager:
    """Gerencia API Keys por empresa com criptografia Fernet (obrigatória)"""

    def __init__(self, config_path: str = None):
        # Usar path absoluto baseado em __file__ para compatibilidade com Render
        if config_path is None:
            config_path = str(BASE_DIR / "data" / "api_keys.json")
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        # Usar mesmo diretório do config_path para a chave de criptografia
        self.key_file = self.config_path.parent / ".encryption_key"
        self._cipher = self._get_cipher()
        self.keys: Dict[str, ApiKeyConfig] = {}
        self._load()

    def _get_cipher(self) -> Fernet:
        """Obtém ou cria chave de criptografia (OBRIGATÓRIO)"""
        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            self.key_file.write_bytes(key)
            # Tentar definir como oculto no Windows
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(str(self.key_file), 0x02)
            except:
                pass
        return Fernet(key)

    def _encrypt(self, value: str) -> str:
        """Criptografa um valor (OBRIGATÓRIO)"""
        if not value:
            return value
        return self._cipher.encrypt(value.encode()).decode()

    def _decrypt(self, value: str) -> str:
        """Descriptografa um valor"""
        if not value:
            return value
        try:
            return self._cipher.decrypt(value.encode()).decode()
        except Exception:
            # Pode ser valor não criptografado (migração de dados antigos)
            # Retorna o valor original para permitir migração
            return value

    def _is_encrypted(self, value: str) -> bool:
        """Verifica se um valor parece estar criptografado (base64 do Fernet)"""
        if not value or len(value) < 50:
            return False
        try:
            # Fernet tokens começam com 'gAAAAA'
            return value.startswith('gAAAAA')
        except:
            return False

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                needs_migration = False
                for k in data.get("keys", []):
                    api_key = k.get("api_key", "")

                    # Descriptografar se necessário
                    if self._is_encrypted(api_key):
                        api_key = self._decrypt(api_key)
                    elif self._cipher and api_key:
                        # Key não criptografada - marcar para migração
                        needs_migration = True

                    k["api_key"] = api_key
                    config = ApiKeyConfig.from_dict(k)
                    self.keys[config.id] = config

                # Migrar keys não criptografadas
                if needs_migration:
                    self._save()
                    print("API keys migradas para formato criptografado.")

            except Exception as e:
                print(f"Erro ao carregar API keys: {e}")
        else:
            self._init_from_env()

    def _init_from_env(self):
        """Auto-create API key configs from env vars (for fresh Render deploys)."""
        env_map = {
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            ProviderType.GOOGLE: "GOOGLE_API_KEY",
        }
        created = []
        for provider_type, env_var in env_map.items():
            key_value = os.environ.get(env_var)
            if key_value:
                self.adicionar(provider_type, key_value, f"{provider_type.value.title()} (env)")
                created.append(provider_type.value)
        if created:
            print(f"[ApiKeyManager] Auto-initialized from env: {', '.join(created)}")

    def _save(self):
        keys_data = []
        for k in self.keys.values():
            key_dict = k.to_dict()
            # Criptografar a API key antes de salvar
            key_dict["api_key"] = self._encrypt(k.api_key)
            keys_data.append(key_dict)

        data = {"keys": keys_data, "encrypted": self._cipher is not None}
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def adicionar(self, empresa: ProviderType, api_key: str, nome_exibicao: str = "") -> ApiKeyConfig:
        key_id = hashlib.sha256(f"{empresa.value}_{datetime.now().timestamp()}".encode()).hexdigest()[:12]

        config = ApiKeyConfig(
            id=key_id,
            empresa=empresa,
            api_key=api_key,  # Armazenado em texto claro na memória
            nome_exibicao=nome_exibicao or empresa.value.title()
        )

        self.keys[key_id] = config
        self._save()  # Salva criptografado
        return config

    def atualizar(self, key_id: str, **kwargs) -> Optional[ApiKeyConfig]:
        if key_id not in self.keys:
            return None

        config = self.keys[key_id]
        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        self._save()
        return config

    def remover(self, key_id: str) -> bool:
        if key_id in self.keys:
            del self.keys[key_id]
            self._save()
            return True
        return False

    def listar(self, empresa: ProviderType = None) -> List[ApiKeyConfig]:
        keys = list(self.keys.values())
        if empresa:
            keys = [k for k in keys if k.empresa == empresa]
        return [k for k in keys if k.ativo]

    def get(self, key_id: str) -> Optional[ApiKeyConfig]:
        return self.keys.get(key_id)

    def get_por_empresa(self, empresa: ProviderType) -> Optional[ApiKeyConfig]:
        """Retorna a primeira API key ativa para uma empresa"""
        for key in self.keys.values():
            if key.empresa == empresa and key.ativo:
                return key
        return None

    def get_decrypted_key(self, key_id: str) -> Optional[str]:
        """Retorna a API key descriptografada para uso"""
        config = self.keys.get(key_id)
        return config.api_key if config else None

    def is_encryption_enabled(self) -> bool:
        """Verifica se a criptografia está habilitada"""
        return self._cipher is not None


# Instância global
api_key_manager = ApiKeyManager()


# ============================================================
# CONFIGURAÇÃO DE MODELO (PROVIDER)
# ============================================================

@dataclass
class ModelConfig:
    """Configuração de um modelo específico"""
    id: str
    nome: str
    tipo: ProviderType
    modelo: str

    # Referência à API key (usa a da empresa se não especificada)
    api_key_id: Optional[str] = None

    # Configurações de geração
    max_tokens: int = 4096
    temperature: Optional[float] = 0.7  # None = não suporta

    # Parâmetros extras (variam por modelo)
    parametros: Dict[str, Any] = field(default_factory=dict)
    # Ex: {"reasoning_effort": "high"} para modelos reasoning
    # Nota: temperature, top_p, parallel_tool_calls são filtrados automaticamente para modelos reasoning

    # System prompt padrão para este modelo
    system_prompt: Optional[str] = None

    # Capacidades
    suporta_temperature: bool = True
    suporta_vision: bool = False
    suporta_streaming: bool = True
    suporta_function_calling: bool = False

    # URL customizada (se diferente do padrão)
    base_url: Optional[str] = None

    # NOVOS: Campos para endpoint customizado
    custom_model_id: Optional[str] = None   # ID exato do modelo (override)
    api_version: Optional[str] = None       # Versão da API (ex: "2024-02-15")
    extra_headers: Dict[str, str] = field(default_factory=dict)  # Headers extras

    # Referência ao catálogo
    catalog_ref: Optional[str] = None       # "openai/gpt-4o"

    # Status
    ativo: bool = True
    is_default: bool = False
    criado_em: datetime = field(default_factory=datetime.now)

    def get_model_id(self) -> str:
        """Retorna o ID do modelo a ser usado na requisição"""
        return self.custom_model_id or self.modelo

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "tipo": self.tipo.value,
            "modelo": self.modelo,
            "api_key_id": self.api_key_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "parametros": self.parametros,
            "system_prompt": self.system_prompt,
            "suporta_temperature": self.suporta_temperature,
            "suporta_vision": self.suporta_vision,
            "suporta_streaming": self.suporta_streaming,
            "suporta_function_calling": self.suporta_function_calling,
            "base_url": self.base_url,
            "custom_model_id": self.custom_model_id,
            "api_version": self.api_version,
            "extra_headers": self.extra_headers,
            "catalog_ref": self.catalog_ref,
            "ativo": self.ativo,
            "is_default": self.is_default,
            "criado_em": self.criado_em.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfig':
        return cls(
            id=data["id"],
            nome=data["nome"],
            tipo=ProviderType(data["tipo"]),
            modelo=data["modelo"],
            api_key_id=data.get("api_key_id"),
            max_tokens=data.get("max_tokens", 4096),
            temperature=data.get("temperature", 0.7),
            parametros=data.get("parametros", {}),
            system_prompt=data.get("system_prompt"),
            suporta_temperature=data.get("suporta_temperature", True),
            suporta_vision=data.get("suporta_vision", False),
            suporta_streaming=data.get("suporta_streaming", True),
            suporta_function_calling=data.get("suporta_function_calling", False),
            base_url=data.get("base_url"),
            custom_model_id=data.get("custom_model_id"),
            api_version=data.get("api_version"),
            extra_headers=data.get("extra_headers", {}),
            catalog_ref=data.get("catalog_ref"),
            ativo=data.get("ativo", True),
            is_default=data.get("is_default", False),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now()
        )


class ModelManager:
    """Gerencia modelos configurados"""

    def __init__(self, config_path: str = None):
        # Usar path absoluto baseado em __file__ para compatibilidade com Render
        if config_path is None:
            config_path = str(BASE_DIR / "data" / "models.json")
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.models: Dict[str, ModelConfig] = {}
        self._load()
    
    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for m in data.get("models", []):
                        config = ModelConfig.from_dict(m)
                        self.models[config.id] = config

                # Validar unicidade de is_default
                self._ensure_single_default()
            except Exception as e:
                print(f"Erro ao carregar modelos: {e}")
        else:
            self._init_from_env()

    def _init_from_env(self):
        """Auto-create default model configs from env vars (for fresh Render deploys)."""
        first = True
        if os.environ.get("OPENAI_API_KEY"):
            openai_key = api_key_manager.get_por_empresa(ProviderType.OPENAI)
            key_id = openai_key.id if openai_key else None
            self.models["openai-gpt4o-mini"] = ModelConfig(
                id="openai-gpt4o-mini",
                nome="GPT-4o Mini",
                tipo=ProviderType.OPENAI,
                modelo="gpt-4o-mini",
                api_key_id=key_id,
                is_default=first,
                ativo=True,
            )
            first = False
        if os.environ.get("ANTHROPIC_API_KEY"):
            anthropic_key = api_key_manager.get_por_empresa(ProviderType.ANTHROPIC)
            key_id = anthropic_key.id if anthropic_key else None
            self.models["claude-haiku"] = ModelConfig(
                id="claude-haiku",
                nome="Claude Haiku",
                tipo=ProviderType.ANTHROPIC,
                modelo="claude-haiku-4-5-20251001",
                api_key_id=key_id,
                is_default=first,
                ativo=True,
            )
            first = False
        if os.environ.get("GOOGLE_API_KEY"):
            google_key = api_key_manager.get_por_empresa(ProviderType.GOOGLE)
            key_id = google_key.id if google_key else None
            self.models["gemini-flash"] = ModelConfig(
                id="gemini-flash",
                nome="Gemini Flash",
                tipo=ProviderType.GOOGLE,
                modelo="gemini-2.0-flash",
                api_key_id=key_id,
                is_default=first,
                ativo=True,
            )
        if self.models:
            self._save()
            names = [m.nome for m in self.models.values()]
            print(f"[ModelManager] Auto-initialized from env: {', '.join(names)}")

    def _ensure_single_default(self):
        """Garante que apenas um modelo seja marcado como padrao.

        Corrige automaticamente se multiplos defaults ou nenhum existir.
        Prefere manter Haiku como default quando possivel.
        """
        defaults = [m for m in self.models.values() if m.is_default]

        if len(defaults) > 1:
            # ERRO: Multiplos defaults detectados
            nomes = [m.nome for m in defaults]
            print(f"[WARN] {len(defaults)} modelos marcados como padrao: {nomes}")
            print("       Corrigindo automaticamente...")

            # Manter Haiku (se existir) ou o primeiro
            haiku = next((m for m in defaults if "haiku" in m.nome.lower()), None)
            keep = haiku if haiku else defaults[0]

            for m in self.models.values():
                m.is_default = (m.id == keep.id)

            print(f"       Modelo padrao definido: {keep.nome}")
            self._save()  # Persistir correcao

        elif len(defaults) == 0 and self.models:
            # Nenhum default: definir Haiku ou primeiro
            print("[WARN] Nenhum modelo padrao encontrado. Definindo automaticamente...")
            haiku = next((m for m in self.models.values() if "haiku" in m.nome.lower()), None)
            default = haiku if haiku else next(iter(self.models.values()))
            default.is_default = True
            print(f"       Modelo padrao definido: {default.nome}")
            self._save()
    
    def _save(self):
        data = {"models": [m.to_dict() for m in self.models.values()]}
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def adicionar(
        self,
        nome: str,
        tipo: ProviderType,
        modelo: str,
        api_key_id: str = None,
        **kwargs
    ) -> ModelConfig:
        model_id = hashlib.sha256(f"{nome}_{tipo.value}_{datetime.now().timestamp()}".encode()).hexdigest()[:12]
        
        # Pegar capacidades do modelo sugerido, se existir
        capacidades = {}
        for m in MODELOS_SUGERIDOS.get(tipo, []):
            if m["id"] == modelo:
                capacidades = {
                    "suporta_temperature": m.get("suporta_temperature", True),
                    "suporta_vision": m.get("suporta_vision", False),
                }
                break
        
        config = ModelConfig(
            id=model_id,
            nome=nome,
            tipo=tipo,
            modelo=modelo,
            api_key_id=api_key_id,
            **capacidades,
            **kwargs
        )
        
        # Se é o primeiro modelo, torna default
        if not self.models:
            config.is_default = True
        
        self.models[model_id] = config
        self._save()
        return config
    
    def atualizar(self, model_id: str, **kwargs) -> Optional[ModelConfig]:
        if model_id not in self.models:
            return None
        
        config = self.models[model_id]
        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                if key == "tipo" and isinstance(value, str):
                    value = ProviderType(value)
                setattr(config, key, value)
        
        self._save()
        return config
    
    def remover(self, model_id: str) -> bool:
        if model_id in self.models:
            was_default = self.models[model_id].is_default
            del self.models[model_id]
            
            # Se removeu o default, define outro
            if was_default and self.models:
                next(iter(self.models.values())).is_default = True
            
            self._save()
            return True
        return False
    
    def listar(self, apenas_ativos: bool = True, tipo: ProviderType = None) -> List[ModelConfig]:
        models = list(self.models.values())
        if apenas_ativos:
            models = [m for m in models if m.ativo]
        if tipo:
            models = [m for m in models if m.tipo == tipo]
        return models
    
    def get(self, model_id: str) -> Optional[ModelConfig]:
        return self.models.get(model_id)
    
    def get_default(self) -> Optional[ModelConfig]:
        for model in self.models.values():
            if model.is_default and model.ativo:
                return model
        # Fallback: primeiro ativo
        ativos = [m for m in self.models.values() if m.ativo]
        return ativos[0] if ativos else None
    
    def set_default(self, model_id: str) -> bool:
        if model_id not in self.models:
            return False
        
        for m in self.models.values():
            m.is_default = (m.id == model_id)
        
        self._save()
        return True


# Instância global
model_manager = ModelManager()
# ============================================================
# CLIENTE DE CHAT UNIVERSAL
# ============================================================

class ChatClient:
    """Cliente universal para diferentes APIs de IA"""
    
    def __init__(self, model_config: ModelConfig, api_key: str):
        self.config = model_config
        self.api_key = api_key
        self.base_url = model_config.base_url or DEFAULT_URLS.get(model_config.tipo, "")
    
    async def chat(
        self,
        mensagem: str,
        historico: List[Dict[str, str]] = None,
        system_prompt: Optional[str] = None,
        documentos_contexto: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envia mensagem e retorna resposta.
        
        Args:
            mensagem: Mensagem do usuário
            historico: Lista de mensagens anteriores
            system_prompt: System prompt customizado
            documentos_contexto: Lista de documentos para incluir no contexto
        
        Returns:
            {"content": "resposta", "tokens": 123, "modelo": "gpt-4o"}
        """
        system = system_prompt or self.config.system_prompt or "Você é um assistente útil."
        
        # Adicionar contexto de documentos ao system prompt se fornecido
        if documentos_contexto:
            docs_text = self._formatar_documentos(documentos_contexto)
            system = f"{system}\n\n## DOCUMENTOS DISPONÍVEIS:\n{docs_text}"
        
        if self.config.tipo == ProviderType.OPENAI:
            return await self._chat_openai(mensagem, historico, system)
        elif self.config.tipo == ProviderType.ANTHROPIC:
            return await self._chat_anthropic(mensagem, historico, system)
        elif self.config.tipo == ProviderType.GOOGLE:
            return await self._chat_google(mensagem, historico, system)
        elif self.config.tipo == ProviderType.OLLAMA:
            return await self._chat_ollama(mensagem, historico, system)
        elif self.config.tipo in [ProviderType.OPENROUTER, ProviderType.GROQ, ProviderType.MISTRAL]:
            return await self._chat_openai_compatible(mensagem, historico, system)
        else:
            # Custom - tenta formato OpenAI
            return await self._chat_openai(mensagem, historico, system)

    async def chat_with_tools(
        self,
        mensagem: str,
        tools: List[Dict[str, Any]],
        tool_registry: ToolRegistry,
        historico: List[Dict[str, str]] = None,
        system_prompt: Optional[str] = None,
        documentos_contexto: List[Dict[str, Any]] = None,
        context: Optional[ToolExecutionContext] = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Envia mensagem com suporte a tool use (function calling).

        Args:
            mensagem: Mensagem do usuário
            tools: Lista de definições de tools no formato Anthropic
            tool_registry: Registry com handlers para executar tools
            historico: Lista de mensagens anteriores
            system_prompt: System prompt customizado
            documentos_contexto: Lista de documentos para incluir no contexto
            context: Contexto de execução para tools (atividade_id, aluno_id, etc.)
            max_iterations: Máximo de iterações do loop de tools

        Returns:
            {"content": "resposta", "tokens": 123, "modelo": "...", "tool_calls": [...]}
        """
        system = system_prompt or self.config.system_prompt or "Você é um assistente útil."

        if documentos_contexto:
            docs_text = self._formatar_documentos(documentos_contexto)
            system = f"{system}\n\n## DOCUMENTOS DISPONÍVEIS:\n{docs_text}"

        # Currently only Anthropic supports tool use in this implementation
        if self.config.tipo == ProviderType.ANTHROPIC:
            return await self._chat_anthropic_with_tools(
                mensagem=mensagem,
                historico=historico or [],
                system=system,
                tools=tools,
                tool_registry=tool_registry,
                context=context,
                max_iterations=max_iterations
            )
        else:
            # Fallback: regular chat without tools for unsupported providers
            return await self.chat(
                mensagem=mensagem,
                historico=historico,
                system_prompt=system_prompt,
                documentos_contexto=documentos_contexto
            )

    def _formatar_documentos(self, documentos: List[Dict[str, Any]]) -> str:
        """Formata documentos para incluir no contexto"""
        partes = []
        for doc in documentos:
            nome = doc.get("nome", "documento")
            tipo = doc.get("tipo", "")
            conteudo = doc.get("conteudo", "")[:10000]  # Limitar tamanho
            partes.append(f"### {tipo.upper()}: {nome}\n```\n{conteudo}\n```\n")
        return "\n".join(partes)
    
    def _is_reasoning_model(self) -> bool:
        """Verifica se o modelo é de reasoning (não suporta temperature)"""
        model_id = self.config.get_model_id().lower()
        return any(r in model_id for r in REASONING_MODELS) or not self.config.suporta_temperature

    # Parâmetros NÃO suportados por modelos de reasoning (o1, o3, o4-mini, etc)
    # Estes causam erro 400 se enviados
    REASONING_UNSUPPORTED_PARAMS = {
        'temperature',
        'top_p',
        'presence_penalty',
        'frequency_penalty',
        'logprobs',
        'top_logprobs',
        'logit_bias',
        'n',
        'parallel_tool_calls'
    }

    def _build_params(self) -> Dict[str, Any]:
        """Constrói parâmetros para a API baseado nas capacidades do modelo"""
        model_id = self.config.get_model_id()
        is_reasoning = self._is_reasoning_model()

        params = {
            "model": model_id,
        }

        # Modelos de reasoning usam max_completion_tokens, outros usam max_tokens
        if is_reasoning and self.config.tipo == ProviderType.OPENAI:
            params["max_completion_tokens"] = self.config.max_tokens
        else:
            params["max_tokens"] = self.config.max_tokens

        # Adiciona temperature apenas se o modelo suporta (não é reasoning)
        if not is_reasoning and self.config.temperature is not None:
            params["temperature"] = self.config.temperature

        # Adiciona parâmetros extras (reasoning_effort, etc)
        for key, value in self.config.parametros.items():
            if value is not None:
                # Filtrar parâmetros não suportados por modelos reasoning
                if is_reasoning and key in self.REASONING_UNSUPPORTED_PARAMS:
                    continue
                params[key] = value

        return params
    
    async def _chat_openai(self, mensagem: str, historico: List, system: str) -> Dict:
        """Chat com API OpenAI"""
        is_reasoning = self._is_reasoning_model()

        # Modelos reasoning usam "developer" ao invés de "system"
        system_role = "developer" if is_reasoning else "system"
        messages = [{"role": system_role, "content": system}]

        # Converter mensagens do histórico também
        if historico:
            for msg in historico:
                role = msg.get("role", "user")
                # Converter system para developer em modelos reasoning
                if role == "system" and is_reasoning:
                    role = "developer"
                messages.append({"role": role, "content": msg.get("content", "")})

        messages.append({"role": "user", "content": mensagem})

        params = self._build_params()
        params["messages"] = messages
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=params
            )
            
            if response.status_code != 200:
                error_msg = f"Erro API OpenAI: {response.status_code}"
                if response.status_code == 400:
                    error_msg += f" - Erro na requisição para '{self.config.modelo}'. Verifique os parâmetros ou tente outro modelo como GPT-4o."
                elif response.status_code == 401:
                    error_msg += " - Chave de API inválida ou expirada."
                elif response.status_code == 429:
                    error_msg += " - Limite de requisições atingido. Aguarde alguns minutos ou tente outro modelo."
                elif response.status_code == 404:
                    error_msg += f" - Modelo '{self.config.modelo}' não encontrado. Tente outro modelo."
                else:
                    error_msg += f" - {response.text[:300]}"
                raise Exception(error_msg)

            data = response.json()

            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "modelo": self.config.modelo,
                "provider": self.config.tipo.value
            }
    
    async def _chat_anthropic(self, mensagem: str, historico: List, system: str) -> Dict:
        """Chat com API Anthropic/Claude"""
        messages = []
        if historico:
            messages.extend(historico)
        messages.append({"role": "user", "content": mensagem})
        
        params = {
            "model": self.config.modelo,
            "max_tokens": self.config.max_tokens,
            "system": system,
            "messages": messages
        }
        
        # Anthropic usa temperature diferente
        if self.config.suporta_temperature and self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        
        # Parâmetros extras
        for key, value in self.config.parametros.items():
            if value is not None and key not in params:
                params[key] = value
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=params
            )
            
            if response.status_code != 200:
                error_msg = f"Erro API Anthropic: {response.status_code}"
                if response.status_code == 400:
                    error_msg += f" - Modelo '{self.config.modelo}' pode estar indisponível ou com ID incorreto. Tente outro modelo como Claude Sonnet."
                elif response.status_code == 401:
                    error_msg += " - Chave de API inválida ou expirada."
                elif response.status_code == 429:
                    error_msg += " - Limite de requisições atingido. Aguarde alguns minutos ou tente outro modelo."
                elif response.status_code == 404:
                    error_msg += f" - Modelo '{self.config.modelo}' não encontrado. Tente outro modelo."
                else:
                    error_msg += f" - {response.text[:300]}"
                raise Exception(error_msg)

            data = response.json()

            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")
            
            return {
                "content": content,
                "tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0),
                "modelo": self.config.modelo,
                "provider": self.config.tipo.value
            }

    async def _chat_anthropic_with_tools(
        self,
        mensagem: str,
        historico: List,
        system: str,
        tools: List[Dict[str, Any]],
        tool_registry: ToolRegistry,
        context: Optional[ToolExecutionContext] = None,
        max_iterations: int = 10
    ) -> Dict:
        """Chat com API Anthropic/Claude with tool use support"""
        messages = []
        if historico:
            messages.extend(historico)
        messages.append({"role": "user", "content": mensagem})

        total_tokens = 0
        all_tool_calls = []

        for iteration in range(max_iterations):
            params = {
                "model": self.config.modelo,
                "max_tokens": self.config.max_tokens,
                "system": system,
                "messages": messages,
                "tools": tools
            }

            if self.config.suporta_temperature and self.config.temperature is not None:
                params["temperature"] = self.config.temperature

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json=params
                )

                if response.status_code != 200:
                    raise Exception(f"Erro API Anthropic: {response.status_code} - {response.text}")

                data = response.json()

            # Track tokens
            total_tokens += data.get("usage", {}).get("input_tokens", 0)
            total_tokens += data.get("usage", {}).get("output_tokens", 0)

            stop_reason = data.get("stop_reason")
            content_blocks = data.get("content", [])

            if stop_reason == "end_turn":
                # Claude finished - extract final text
                final_text = self._extract_text_from_blocks(content_blocks)
                return {
                    "content": final_text,
                    "tokens": total_tokens,
                    "modelo": self.config.modelo,
                    "provider": self.config.tipo.value,
                    "tool_calls": all_tool_calls
                }

            elif stop_reason == "tool_use":
                # Extract tool calls
                tool_calls = self._extract_tool_calls(content_blocks)
                all_tool_calls.extend([{
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.input
                } for tc in tool_calls])

                # Execute each tool
                tool_results = []
                for tool_call in tool_calls:
                    result = await tool_registry.execute(
                        tool_name=tool_call.name,
                        tool_input=tool_call.input,
                        tool_use_id=tool_call.id,
                        context=context
                    )
                    tool_results.append(result.to_anthropic_format())

                # Add assistant message with tool use blocks
                messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })

                # Add tool results as user message
                messages.append({
                    "role": "user",
                    "content": tool_results
                })

            else:
                # Unexpected stop reason (max_tokens, etc.)
                final_text = self._extract_text_from_blocks(content_blocks)
                return {
                    "content": final_text,
                    "tokens": total_tokens,
                    "modelo": self.config.modelo,
                    "provider": self.config.tipo.value,
                    "tool_calls": all_tool_calls,
                    "stop_reason": stop_reason
                }

        # Max iterations reached
        return {
            "content": "[Maximum tool iterations reached]",
            "tokens": total_tokens,
            "modelo": self.config.modelo,
            "provider": self.config.tipo.value,
            "tool_calls": all_tool_calls,
            "error": "max_iterations_exceeded"
        }

    def _extract_tool_calls(self, content_blocks: List[Dict]) -> List[ToolCall]:
        """Extract tool_use blocks from response content"""
        tool_calls = []
        for block in content_blocks:
            if block.get("type") == "tool_use":
                tool_calls.append(ToolCall(
                    id=block["id"],
                    name=block["name"],
                    input=block["input"]
                ))
        return tool_calls

    def _extract_text_from_blocks(self, content_blocks: List[Dict]) -> str:
        """Extract text content from response blocks"""
        texts = []
        for block in content_blocks:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
        return "\n".join(texts)

    async def _chat_google(self, mensagem: str, historico: List, system: str) -> Dict:
        """Chat com API Google/Gemini"""
        contents = []

        # Add history messages
        if historico:
            for msg in historico:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})

        # Add current user message
        contents.append({"role": "user", "parts": [{"text": mensagem}]})

        generation_config = {"maxOutputTokens": self.config.max_tokens}
        if self.config.suporta_temperature and self.config.temperature is not None:
            generation_config["temperature"] = self.config.temperature

        # Extra parameters
        for key, value in self.config.parametros.items():
            if value is not None:
                generation_config[key] = value

        # Build request with proper system_instruction parameter
        request_body = {
            "contents": contents,
            "generationConfig": generation_config
        }

        # Add system instruction if provided
        if system:
            request_body["system_instruction"] = {
                "parts": [{"text": system}]
            }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/models/{self.config.modelo}:generateContent",
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                json=request_body
            )
            
            if response.status_code != 200:
                error_msg = f"Erro API Google: {response.status_code}"
                if response.status_code == 400:
                    error_msg += f" - Erro na requisição para '{self.config.modelo}'. Verifique os parâmetros ou tente outro modelo como GPT-4o."
                elif response.status_code == 403:
                    error_msg += " - Chave de API sem permissão para este modelo ou região."
                elif response.status_code == 429:
                    error_msg += " - Limite de requisições atingido. Aguarde alguns minutos ou tente outro modelo."
                elif response.status_code == 404:
                    error_msg += f" - Modelo '{self.config.modelo}' não encontrado. Tente outro modelo."
                else:
                    error_msg += f" - {response.text[:300]}"
                raise Exception(error_msg)

            data = response.json()

            content = ""
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    content += part.get("text", "")
            
            return {
                "content": content,
                "tokens": data.get("usageMetadata", {}).get("totalTokenCount", 0),
                "modelo": self.config.modelo,
                "provider": self.config.tipo.value
            }
    
    async def _chat_ollama(self, mensagem: str, historico: List, system: str) -> Dict:
        """Chat com Ollama local"""
        messages = [{"role": "system", "content": system}]
        if historico:
            messages.extend(historico)
        messages.append({"role": "user", "content": mensagem})
        
        options = {}
        if self.config.suporta_temperature and self.config.temperature is not None:
            options["temperature"] = self.config.temperature
        
        # Parâmetros extras
        for key, value in self.config.parametros.items():
            if value is not None:
                options[key] = value
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.config.modelo,
                    "messages": messages,
                    "stream": False,
                    "options": options
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro Ollama: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return {
                "content": data.get("message", {}).get("content", ""),
                "tokens": data.get("eval_count", 0),
                "modelo": self.config.modelo,
                "provider": self.config.tipo.value
            }
    
    async def _chat_openai_compatible(self, mensagem: str, historico: List, system: str) -> Dict:
        """Chat com APIs compatíveis com OpenAI (Groq, OpenRouter, Mistral)"""
        messages = [{"role": "system", "content": system}]
        if historico:
            messages.extend(historico)
        messages.append({"role": "user", "content": mensagem})
        
        params = self._build_params()
        params["messages"] = messages
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Headers específicos para OpenRouter
        if self.config.tipo == ProviderType.OPENROUTER:
            headers["HTTP-Referer"] = "https://novocr.local"
            headers["X-Title"] = "NOVO CR"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=params
            )
            
            if response.status_code != 200:
                raise Exception(f"Erro API: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens": data.get("usage", {}).get("total_tokens", 0),
                "modelo": self.config.modelo,
                "provider": self.config.tipo.value
            }


# ============================================================
# MENSAGENS E SESSÕES DE CHAT
# ============================================================

@dataclass
class ChatMessage:
    """Uma mensagem no chat"""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    model_id: Optional[str] = None
    modelo: Optional[str] = None
    provider: Optional[str] = None
    tokens: int = 0
    arquivos_gerados: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "model_id": self.model_id,
            "modelo": self.modelo,
            "provider": self.provider,
            "tokens": self.tokens,
            "arquivos_gerados": self.arquivos_gerados
        }


@dataclass
class ChatSession:
    """Uma sessão de chat"""
    id: str
    titulo: str
    model_id: Optional[str] = None
    atividade_id: Optional[str] = None
    aluno_id: Optional[str] = None
    etapa_pipeline: Optional[str] = None  # Se é parte do pipeline
    mensagens: List[ChatMessage] = field(default_factory=list)
    criado_em: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "model_id": self.model_id,
            "atividade_id": self.atividade_id,
            "aluno_id": self.aluno_id,
            "etapa_pipeline": self.etapa_pipeline,
            "mensagens": [m.to_dict() for m in self.mensagens],
            "criado_em": self.criado_em.isoformat(),
            "total_mensagens": len(self.mensagens)
        }
# ============================================================
# SERVIÇO DE CHAT COM DOCUMENTOS
# ============================================================

class ChatService:
    """Serviço de chat com documentos"""
    
    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
    
    def criar_sessao(
        self,
        titulo: str = "Nova conversa",
        model_id: Optional[str] = None,
        atividade_id: Optional[str] = None,
        aluno_id: Optional[str] = None,
        etapa_pipeline: Optional[str] = None
    ) -> ChatSession:
        """Cria nova sessão de chat"""
        session_id = hashlib.sha256(f"chat_{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        session = ChatSession(
            id=session_id,
            titulo=titulo,
            model_id=model_id,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            etapa_pipeline=etapa_pipeline
        )
        
        self.sessions[session_id] = session
        return session
    
    def get_sessao(self, session_id: str) -> Optional[ChatSession]:
        return self.sessions.get(session_id)
    
    def listar_sessoes(self) -> List[ChatSession]:
        return list(self.sessions.values())
    
    def deletar_sessao(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    async def enviar_mensagem(
        self,
        session_id: str,
        mensagem: str,
        model_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        incluir_contexto_docs: bool = True
    ) -> ChatMessage:
        """
        Envia mensagem e retorna resposta.
        """
        session = self.get_sessao(session_id)
        if not session:
            raise ValueError("Sessão não encontrada")
        
        # Determinar modelo
        mid = model_id or session.model_id
        model_config = model_manager.get(mid) if mid else model_manager.get_default()
        
        if not model_config:
            raise ValueError("Nenhum modelo de IA configurado")
        
        # Obter API key
        api_key = self._get_api_key(model_config)
        if not api_key:
            raise ValueError(f"API key não configurada para {model_config.tipo.value}")
        
        # Adicionar mensagem do usuário
        user_msg = ChatMessage(role="user", content=mensagem)
        session.mensagens.append(user_msg)
        
        # Carregar documentos do contexto
        documentos_contexto = []
        if incluir_contexto_docs and session.atividade_id:
            documentos_contexto = self._carregar_documentos(session.atividade_id, session.aluno_id)
        
        # System prompt
        system = system_prompt or model_config.system_prompt or self._get_system_prompt_padrao()
        
        # Montar histórico
        historico = []
        for msg in session.mensagens[:-1]:
            if msg.role in ["user", "assistant"]:
                historico.append({"role": msg.role, "content": msg.content})
        
        # Enviar para IA
        client = ChatClient(model_config, api_key)
        resposta = await client.chat(
            mensagem, 
            historico, 
            system,
            documentos_contexto if not system_prompt else None  # Só inclui docs se não tiver system customizado
        )
        
        # Processar arquivos gerados (texto/markdown)
        arquivos_gerados = await self._processar_arquivos_gerados(
            resposta["content"],
            session.atividade_id,
            session.aluno_id,
            session.etapa_pipeline
        )

        # Processar código executável (python-exec: blocks)
        resposta_final = resposta["content"]
        try:
            resposta_final, arquivos_exec = await self._processar_codigo_executavel(
                resposta["content"],
                session.atividade_id,
                session.aluno_id
            )
            arquivos_gerados.extend(arquivos_exec)
        except Exception as e:
            print(f"Erro ao processar código executável: {e}")

        # Adicionar resposta
        assistant_msg = ChatMessage(
            role="assistant",
            content=resposta_final,
            model_id=model_config.id,
            modelo=resposta["modelo"],
            provider=resposta["provider"],
            tokens=resposta["tokens"],
            arquivos_gerados=arquivos_gerados
        )
        session.mensagens.append(assistant_msg)
        
        return assistant_msg
    
    def _get_api_key(self, model_config: ModelConfig) -> Optional[str]:
        """Obtém API key para o modelo"""
        # Primeiro tenta API key específica do modelo
        if model_config.api_key_id:
            key_config = api_key_manager.get(model_config.api_key_id)
            if key_config:
                return key_config.api_key

        # Depois tenta API key da empresa
        key_config = api_key_manager.get_por_empresa(model_config.tipo)
        if key_config:
            return key_config.api_key

        # Ollama não precisa de API key
        if model_config.tipo == ProviderType.OLLAMA:
            return "ollama"

        # Fallback: variáveis de ambiente (para produção)
        env_var_map = {
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            ProviderType.GOOGLE: "GOOGLE_API_KEY",
            ProviderType.GROQ: "GROQ_API_KEY",
            ProviderType.MISTRAL: "MISTRAL_API_KEY",
            ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
        }
        env_var = env_var_map.get(model_config.tipo)
        if env_var:
            return os.getenv(env_var)

        return None
    
    def _carregar_documentos(self, atividade_id: str, aluno_id: Optional[str]) -> List[Dict[str, Any]]:
        """Carrega documentos de uma atividade para o contexto"""
        documentos = []
        
        try:
            docs = storage.listar_documentos(atividade_id, aluno_id)
            
            for doc in docs:
                conteudo = self._ler_documento(doc)
                if conteudo:
                    documentos.append({
                        "id": doc.id,
                        "nome": doc.nome_arquivo,
                        "tipo": doc.tipo.value,
                        "conteudo": conteudo
                    })
        except Exception as e:
            print(f"Erro ao carregar documentos: {e}")
        
        return documentos
    
    def _ler_documento(self, documento) -> Optional[str]:
        """Lê conteúdo de um documento"""
        try:
            arquivo = Path(documento.caminho_arquivo)
            if not arquivo.exists():
                return None
            
            if documento.extensao.lower() == '.json':
                with open(arquivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)[:8000]
            
            elif documento.extensao.lower() in ['.txt', '.md']:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return f.read()[:8000]
            
            else:
                return f"[Arquivo binário: {documento.nome_arquivo} - {documento.extensao}]"
                
        except Exception as e:
            print(f"Erro ao ler documento: {e}")
            return None
    
    def _get_system_prompt_padrao(self) -> str:
        """Retorna system prompt padrao - SIMPLIFICADO para garantir uso de python-exec"""
        return """Voce e um assistente educacional especializado em correcao de provas.

REGRA CRITICA PARA GERACAO DE ARQUIVOS:
=========================================
Quando o usuario pedir para criar/gerar qualquer arquivo (Excel, PDF, Word, PowerPoint, imagem, CSV, etc.), voce DEVE usar o formato python-exec.

FORMATO OBRIGATORIO:
```python-exec:nome_arquivo.extensao
# codigo Python aqui
```

NUNCA FACA ISSO:
- NAO diga "copie e cole"
- NAO diga "salve como"
- NAO diga "converta manualmente"
- NAO use blocos documento: ou document: ou arquivo:
- NAO descreva como criar o arquivo - CRIE O ARQUIVO

Bibliotecas disponiveis: pandas, openpyxl, python-docx, reportlab, python-pptx, matplotlib, pillow, numpy

EXEMPLO CORRETO (Excel):
```python-exec:notas.xlsx
import pandas as pd
df = pd.DataFrame({'Aluno': ['Ana', 'Bruno'], 'Nota': [9.0, 7.5]})
df.to_excel('notas.xlsx', index=False)
print('Criado!')
```

EXEMPLO CORRETO (PDF):
```python-exec:relatorio.pdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
c = canvas.Canvas('relatorio.pdf', pagesize=letter)
c.drawString(100, 700, 'Relatorio')
c.save()
print('Criado!')
```

Seja preciso e educativo nas correcoes."""
    
    async def _processar_arquivos_gerados(
        self,
        resposta: str,
        atividade_id: Optional[str],
        aluno_id: Optional[str],
        etapa_pipeline: Optional[str]
    ) -> List[str]:
        """Detecta e salva arquivos gerados na resposta"""
        arquivos_salvos = []
        
        # Padrão: ```arquivo:nome.ext ou ```file:nome.ext
        pattern = r'```(?:arquivo|file):([^\n]+)\n([\s\S]*?)```'
        matches = re.findall(pattern, resposta)
        
        for nome_arquivo, conteudo in matches:
            nome_arquivo = nome_arquivo.strip()
            conteudo = conteudo.strip()
            
            caminho = await self._salvar_arquivo_gerado(
                nome_arquivo,
                conteudo,
                atividade_id,
                aluno_id,
                etapa_pipeline
            )
            
            if caminho:
                arquivos_salvos.append(caminho)
        
        return arquivos_salvos
    
    async def _salvar_arquivo_gerado(
        self,
        nome_arquivo: str,
        conteudo: str,
        atividade_id: Optional[str],
        aluno_id: Optional[str],
        etapa_pipeline: Optional[str]
    ) -> Optional[str]:
        """Salva arquivo gerado pelo chat"""
        try:
            # Determinar pasta destino
            if atividade_id:
                atividade = storage.get_atividade(atividade_id)
                if atividade:
                    turma = storage.get_turma(atividade.turma_id)
                    if turma:
                        base_path = Path(storage.arquivos_path) / turma.materia_id / turma.id / atividade_id
                        
                        if aluno_id:
                            base_path = base_path / aluno_id
                        else:
                            base_path = base_path / "_base"
                        
                        base_path.mkdir(parents=True, exist_ok=True)
                        
                        # Adicionar prefixo da etapa se for do pipeline
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nome_base = Path(nome_arquivo).stem
                        extensao = Path(nome_arquivo).suffix
                        
                        if etapa_pipeline:
                            nome_final = f"{etapa_pipeline}_{nome_base}_{timestamp}{extensao}"
                        else:
                            nome_final = f"{nome_base}_{timestamp}{extensao}"
                        
                        caminho_final = base_path / nome_final
                        
                        with open(caminho_final, 'w', encoding='utf-8') as f:
                            f.write(conteudo)
                        
                        return str(caminho_final)
            
            # Fallback: pasta genérica
            fallback_path = Path(storage.base_path) / "chat_outputs"
            fallback_path.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_base = Path(nome_arquivo).stem
            extensao = Path(nome_arquivo).suffix
            nome_final = f"{nome_base}_{timestamp}{extensao}"
            
            caminho_final = fallback_path / nome_final
            
            with open(caminho_final, 'w', encoding='utf-8') as f:
                f.write(conteudo)
            
            return str(caminho_final)
            
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return None

    async def _processar_codigo_executavel(
        self,
        resposta: str,
        atividade_id: Optional[str],
        aluno_id: Optional[str]
    ) -> Tuple[str, List[str]]:
        """
        Detecta e executa blocos python-exec: na resposta.

        Retorna:
            Tuple de (resposta_modificada, lista_de_arquivos_gerados)
        """
        arquivos_salvos = []
        resposta_modificada = resposta

        # Padrão: ```python-exec:arquivo.xlsx
        pattern = r'```python-exec:([^\n]+)\n([\s\S]*?)```'
        matches = re.findall(pattern, resposta)

        if not matches:
            return resposta, []

        try:
            from code_executor import (
                code_executor,
                ExecutionStatus,
                detect_libraries_from_code,
                detect_output_files_from_code
            )
        except ImportError:
            print("code_executor não disponível - blocos python-exec serão ignorados")
            return resposta, []

        for output_spec, code in matches:
            output_files = [f.strip() for f in output_spec.split(',')]

            # Detectar bibliotecas e arquivos
            detected_libs = detect_libraries_from_code(code)
            detected_files = detect_output_files_from_code(code)
            all_output_files = list(set(output_files + detected_files))

            print(f"Executando código Python com outputs esperados: {all_output_files}")
            print(f"Bibliotecas detectadas: {detected_libs}")

            try:
                # Executar o código
                result = await code_executor.execute(
                    code=code,
                    libraries=detected_libs,
                    output_files=all_output_files
                )

                if result.is_success and result.files_generated:
                    # Criar blocos documento-binario para cada arquivo gerado
                    replacement_blocks = []

                    for gen_file in result.files_generated:
                        # Formato: documento-binario com metadados
                        block = f"""```documento-binario:{gen_file.filename}
type={gen_file.mime_type}
size={gen_file.size_bytes}
data={gen_file.content_base64}
```"""
                        replacement_blocks.append(block)
                        arquivos_salvos.append(gen_file.filename)
                        print(f"Arquivo gerado: {gen_file.filename} ({gen_file.size_bytes} bytes)")

                    # Substituir bloco python-exec pelo documento-binario
                    original_block = f'```python-exec:{output_spec}\n{code}```'
                    replacement = '\n\n'.join(replacement_blocks)

                    # Adicionar mensagem de sucesso
                    success_msg = f"\n\n**Arquivos gerados com sucesso:**\n"
                    for f in result.files_generated:
                        size_kb = round(f.size_bytes / 1024, 1)
                        success_msg += f"- {f.filename} ({size_kb} KB)\n"
                    success_msg += "\nClique no botao 'Baixar' acima para fazer o download."

                    resposta_modificada = resposta_modificada.replace(
                        original_block,
                        replacement + success_msg
                    )

                elif result.status == ExecutionStatus.SECURITY_VIOLATION:
                    # Adicionar erro de segurança
                    error_block = f"""
**[BLOQUEADO] Erro de Seguranca:** Codigo bloqueado por violar politicas de seguranca.
Detalhes: {result.error_message}
"""
                    original_block = f'```python-exec:{output_spec}\n{code}```'
                    resposta_modificada = resposta_modificada.replace(
                        original_block,
                        f'```python\n{code}\n```\n{error_block}'
                    )

                else:
                    # Adicionar mensagem de erro clara
                    error_details = result.stderr or result.error_message or "Erro desconhecido"
                    error_block = f"""
**[ERRO] Falha ao gerar arquivo:**
```
{error_details}
```
O codigo Python encontrou um erro durante a execucao. Verifique a sintaxe e tente novamente.
"""
                    if result.stdout:
                        error_block += f"\n**Saida parcial:**\n```\n{result.stdout}\n```"

                    original_block = f'```python-exec:{output_spec}\n{code}```'
                    resposta_modificada = resposta_modificada.replace(
                        original_block,
                        f'```python\n{code}\n```\n{error_block}'
                    )

            except Exception as e:
                print(f"Erro ao executar codigo: {e}")
                error_block = f"\n**[ERRO] Falha ao executar codigo:** {str(e)}\n"
                original_block = f'```python-exec:{output_spec}\n{code}```'
                resposta_modificada = resposta_modificada.replace(
                    original_block,
                    f'```python\n{code}\n```\n{error_block}'
                )

        return resposta_modificada, arquivos_salvos

    # ============================================================
    # MÉTODOS PARA LEITURA DE DOCUMENTOS (ACESSO PELA IA)
    # ============================================================
    
    def listar_documentos_disponiveis(
        self, 
        atividade_id: str, 
        aluno_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista documentos disponíveis para uma atividade"""
        docs = storage.listar_documentos(atividade_id, aluno_id)
        
        return [{
            "id": d.id,
            "tipo": d.tipo.value,
            "nome": d.nome_arquivo,
            "extensao": d.extensao,
            "tamanho": d.tamanho_bytes,
            "criado_em": d.criado_em.isoformat()
        } for d in docs]
    
    def ler_documento_completo(self, documento_id: str) -> Optional[Dict[str, Any]]:
        """Lê conteúdo completo de um documento"""
        doc = storage.get_documento(documento_id)
        if not doc:
            return None
        
        conteudo = self._ler_documento(doc)
        
        return {
            "id": doc.id,
            "tipo": doc.tipo.value,
            "nome": doc.nome_arquivo,
            "extensao": doc.extensao,
            "conteudo": conteudo,
            "caminho": doc.caminho_arquivo
        }


# ============================================================
# INSTÂNCIAS GLOBAIS
# ============================================================

chat_service = ChatService()


# ============================================================
# FUNÇÕES AUXILIARES PARA EXPORTAÇÃO
# ============================================================

def get_tipos_providers():
    """Retorna tipos de providers disponíveis"""
    tipos = []
    for tipo in ProviderType:
        tipos.append({
            "id": tipo.value,
            "nome": tipo.name,
            "url_padrao": DEFAULT_URLS.get(tipo, ""),
            "modelos_sugeridos": MODELOS_SUGERIDOS.get(tipo, []),
            "requer_api_key": tipo != ProviderType.OLLAMA
        })
    return tipos


# ============================================================
# FUNÇÃO UNIFICADA DE RESOLUÇÃO DE PROVIDER
# ============================================================

def resolve_provider_config(model_id: str = None) -> Dict[str, Any]:
    """
    Resolve configuração de provider de forma UNIFICADA.
    Usado por chat E pipeline para garantir comportamento consistente.

    Ordem de busca:
    1. model_manager (models.json) - via model_id ou default
    2. ai_registry (providers configurados em código)
    3. Variáveis de ambiente (OPENAI_API_KEY, etc.)

    Retorna dict com:
        - tipo: str (openai, anthropic, google, etc.)
        - api_key: str
        - modelo: str (nome do modelo para a API)
        - base_url: str ou None
        - max_tokens: int
        - temperature: float
        - suporta_temperature: bool

    Levanta ValueError com mensagem clara se nenhum provider disponível.
    """
    from ai_providers import ai_registry

    # ====================================================
    # PASSO 1: Tentar model_manager (sistema principal)
    # ====================================================
    model = None
    if model_id:
        model = model_manager.get(model_id)
        if not model:
            # Tentar ai_registry antes de falhar
            try:
                provider = ai_registry.get(model_id)
                # Converter provider do ai_registry para dict
                provider_type = "openai"
                if "Anthropic" in provider.name or "claude" in provider.model.lower():
                    provider_type = "anthropic"
                elif "Gemini" in provider.name or "gemini" in provider.model.lower():
                    provider_type = "google"

                return {
                    "tipo": provider_type,
                    "api_key": getattr(provider, 'api_key', ''),
                    "modelo": provider.model,
                    "base_url": getattr(provider, 'base_url', None),
                    "max_tokens": 4096,
                    "temperature": 0.7,
                    "suporta_temperature": True
                }
            except ValueError:
                pass

            # Listar disponíveis para mensagem de erro clara
            modelos_disponiveis = [f"{m.id} ({m.nome})" for m in model_manager.listar()]
            providers_registry = ai_registry.list_providers()

            raise ValueError(
                f"Modelo '{model_id}' não encontrado. "
                f"Este ID pode ser de outro ambiente (local vs Render). "
                f"Modelos em models.json: {modelos_disponiveis if modelos_disponiveis else 'Nenhum'}. "
                f"Providers em ai_registry: {providers_registry if providers_registry else 'Nenhum'}."
            )
    else:
        # Sem model_id, usar padrão
        model = model_manager.get_default()
        if not model:
            # Tentar ai_registry default
            try:
                provider = ai_registry.get_default()
                if provider:
                    provider_type = "openai"
                    if "Anthropic" in provider.name or "claude" in provider.model.lower():
                        provider_type = "anthropic"
                    elif "Gemini" in provider.name or "gemini" in provider.model.lower():
                        provider_type = "google"

                    return {
                        "tipo": provider_type,
                        "api_key": getattr(provider, 'api_key', ''),
                        "modelo": provider.model,
                        "base_url": getattr(provider, 'base_url', None),
                        "max_tokens": 4096,
                        "temperature": 0.7,
                        "suporta_temperature": True
                    }
            except:
                pass

            raise ValueError(
                "Nenhum modelo padrão configurado. "
                "Configure um modelo em Configurações > Modelos ou defina variáveis de ambiente."
            )

    # ====================================================
    # PASSO 2: Buscar API Key (ordem de prioridade)
    # ====================================================
    api_key = None

    # 2a. API key específica do modelo
    if model.api_key_id:
        key_config = api_key_manager.get(model.api_key_id)
        if key_config:
            api_key = key_config.api_key

    # 2b. API key por empresa/provider type
    if not api_key:
        key_config = api_key_manager.get_por_empresa(model.tipo)
        if key_config:
            api_key = key_config.api_key

    # 2c. Ollama não precisa de API key
    if not api_key and model.tipo == ProviderType.OLLAMA:
        api_key = "ollama"

    # 2d. Variáveis de ambiente (para Render/produção)
    if not api_key:
        env_var_map = {
            ProviderType.OPENAI: "OPENAI_API_KEY",
            ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
            ProviderType.GOOGLE: "GOOGLE_API_KEY",
            ProviderType.GROQ: "GROQ_API_KEY",
            ProviderType.MISTRAL: "MISTRAL_API_KEY",
            ProviderType.OPENROUTER: "OPENROUTER_API_KEY",
            ProviderType.DEEPSEEK: "DEEPSEEK_API_KEY",
            ProviderType.XAI: "XAI_API_KEY",
        }
        env_var = env_var_map.get(model.tipo)
        if env_var:
            api_key = os.getenv(env_var)

    if not api_key:
        raise ValueError(
            f"Nenhuma API key encontrada para modelo '{model.nome}' (tipo: {model.tipo.value}). "
            f"Configure uma API key em Configurações > API Keys ou defina a variável de ambiente."
        )

    # ====================================================
    # PASSO 3: Retornar configuração completa
    # ====================================================
    return {
        "tipo": model.tipo.value,
        "api_key": api_key,
        "modelo": model.get_model_id(),
        "base_url": model.base_url,
        "max_tokens": model.max_tokens,
        "temperature": model.temperature,
        "suporta_temperature": model.suporta_temperature
    }
