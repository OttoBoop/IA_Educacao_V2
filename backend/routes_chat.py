"""
NOVO CR - Rotas de Chat e Configuração de IAs v2.1

Endpoints para:
- Gerenciar API Keys por empresa
- Gerenciar Modelos de IA
- Chat com documentos
- Gerar arquivos via chat
"""

print("=" * 50)
print("[ROUTES_CHAT] MODULE LOADED - v2.0 WITH PYTHON-EXEC")
print("=" * 50)

from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

from chat_service import (
    api_key_manager, model_manager, chat_service,
    ApiKeyConfig, ModelConfig, ProviderType,
    DEFAULT_URLS, MODELOS_SUGERIDOS, get_tipos_providers
)
from model_catalog import model_catalog, ModelMetadata
from storage import storage
import httpx
import mimetypes


router = APIRouter()


# ============================================================
# HELPER: SANITIZAÇÃO DE HISTÓRICO
# ============================================================

import re

def _sanitize_history_content(content: str) -> str:
    """Remove binary document blocks from history to avoid token overflow"""
    return re.sub(
        r'```documento-binario:[^\n]+\n[\s\S]*?```',
        '[Arquivo binário removido do histórico]',
        content
    )


# ============================================================
# HELPER: DETECÇÃO DE MIME TYPE
# ============================================================

MIME_TYPES = {
    # PDFs
    '.pdf': 'application/pdf',
    # Imagens
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    # Documentos texto
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.csv': 'text/csv',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.rtf': 'application/rtf',
    # Office (download only)
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    # Código - linguagens comuns
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.ts': 'text/typescript',
    '.jsx': 'text/javascript',
    '.tsx': 'text/typescript',
    '.css': 'text/css',
    '.scss': 'text/x-scss',
    '.sass': 'text/x-sass',
    '.less': 'text/x-less',
    # Código - linguagens compiladas
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.cc': 'text/x-c++',
    '.cxx': 'text/x-c++',
    '.h': 'text/x-c',
    '.hpp': 'text/x-c++',
    '.cs': 'text/x-csharp',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.swift': 'text/x-swift',
    '.kt': 'text/x-kotlin',
    '.scala': 'text/x-scala',
    # Código - scripting
    '.rb': 'text/x-ruby',
    '.php': 'text/x-php',
    '.pl': 'text/x-perl',
    '.pm': 'text/x-perl',
    '.lua': 'text/x-lua',
    '.r': 'text/x-r',
    '.R': 'text/x-r',
    '.m': 'text/x-matlab',
    '.jl': 'text/x-julia',
    # Shell/Scripts
    '.sh': 'text/x-shellscript',
    '.bash': 'text/x-shellscript',
    '.zsh': 'text/x-shellscript',
    '.ps1': 'text/x-powershell',
    '.bat': 'text/x-batch',
    '.cmd': 'text/x-batch',
    # Web/Markup
    '.vue': 'text/x-vue',
    '.svelte': 'text/x-svelte',
    '.astro': 'text/x-astro',
    # Config/Data
    '.yaml': 'text/yaml',
    '.yml': 'text/yaml',
    '.toml': 'text/x-toml',
    '.ini': 'text/x-ini',
    '.cfg': 'text/plain',
    '.conf': 'text/plain',
    '.env': 'text/plain',
    '.properties': 'text/x-java-properties',
    # Notebooks/Docs
    '.ipynb': 'application/x-ipynb+json',
    '.tex': 'text/x-latex',
    '.latex': 'text/x-latex',
    '.bib': 'text/x-bibtex',
    # Database
    '.sql': 'text/x-sql',
    '.sqlite': 'application/x-sqlite3',
    '.db': 'application/x-sqlite3',
    # Archives (download only)
    '.zip': 'application/zip',
    '.rar': 'application/vnd.rar',
    '.7z': 'application/x-7z-compressed',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    # Audio/Video (download only)
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.mp4': 'video/mp4',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
}


def get_mime_type(file_path: Path) -> str:
    """Detecta o MIME type baseado na extensão do arquivo"""
    ext = file_path.suffix.lower()

    # Primeiro tenta no dicionário customizado
    if ext in MIME_TYPES:
        return MIME_TYPES[ext]

    # Fallback para mimetypes do Python
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        return mime_type

    # Default para binário genérico
    return 'application/octet-stream'


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class ApiKeyCreate(BaseModel):
    empresa: str  # openai, anthropic, google, etc.
    api_key: str
    nome_exibicao: Optional[str] = None

class ApiKeyUpdate(BaseModel):
    api_key: Optional[str] = None
    nome_exibicao: Optional[str] = None
    ativo: Optional[bool] = None

class ModelCreate(BaseModel):
    nome: str
    tipo: str  # openai, anthropic, google, ollama, etc.
    modelo: str
    api_key_id: Optional[str] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    parametros: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    base_url: Optional[str] = None

class ModelUpdate(BaseModel):
    nome: Optional[str] = None
    modelo: Optional[str] = None
    api_key_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    parametros: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    base_url: Optional[str] = None
    ativo: Optional[bool] = None

class ChatSessionCreate(BaseModel):
    titulo: Optional[str] = "Nova conversa"
    model_id: Optional[str] = None
    atividade_id: Optional[str] = None
    aluno_id: Optional[str] = None
    etapa_pipeline: Optional[str] = None

class ChatMessageSend(BaseModel):
    mensagem: str
    model_id: Optional[str] = None
    system_prompt: Optional[str] = None
    incluir_contexto_docs: Optional[bool] = True


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = None  # Legado - usa ai_registry
    model_id: Optional[str] = None  # Novo - usa model_manager
    context_docs: Optional[List[str]] = None


# ============================================================
# CHAT DIRETO (ENDPOINT PRINCIPAL DO FRONTEND)
# ============================================================

@router.post("/api/chat", tags=["Chat"])
async def chat_direto(data: ChatRequest):
    """
    Endpoint principal de chat usado pelo frontend.
    Recebe mensagens, model_id (novo) ou provider (legado), e documentos de contexto opcionais.
    """
    import sys
    sys.stderr.write("=" * 50 + "\n")
    sys.stderr.write("[CHAT_DIRETO] ENDPOINT HIT!\n")
    sys.stderr.write(f"[CHAT_DIRETO] model_id={data.model_id}\n")
    sys.stderr.write(f"[CHAT_DIRETO] provider={data.provider}\n")
    sys.stderr.write(f"[CHAT_DIRETO] messages count={len(data.messages) if data.messages else 0}\n")
    sys.stderr.write("=" * 50 + "\n")
    sys.stderr.flush()
    import time
    from chat_service import ChatClient

    start_time = time.time()

    # Construir o prompt a partir das mensagens
    user_message = data.messages[-1].content if data.messages else ""

    # Histórico anterior para contexto
    historico = []
    if len(data.messages) > 1:
        for msg in data.messages[:-1]:
            if msg.role in ["user", "assistant"]:
                clean_content = _sanitize_history_content(msg.content)
                historico.append({"role": msg.role, "content": clean_content})

    # Carregar contexto de documentos se fornecido
    contexto_docs = ""
    sys.stderr.write(f"[CHAT_DIRETO] context_docs recebido: {data.context_docs}\n")
    sys.stderr.write(f"[CHAT_DIRETO] context_docs len: {len(data.context_docs) if data.context_docs else 0}\n")
    sys.stderr.flush()

    if data.context_docs and len(data.context_docs) > 0:
        docs_content = []
        docs_carregados = 0
        docs_falha = 0
        for doc_id in data.context_docs[:50]:  # Aumentado para 50 documentos
            try:
                doc = storage.get_documento(doc_id)
                if doc:
                    conteudo = _ler_conteudo_documento(doc)
                    if conteudo:
                        docs_content.append(f"### Documento: {doc.nome_arquivo} ({doc.tipo.value})\n{conteudo[:5000]}")
                        docs_carregados += 1
                    else:
                        docs_falha += 1
                        sys.stderr.write(f"[CHAT_DIRETO] Falha ao ler conteudo: {doc_id}\n")
                else:
                    docs_falha += 1
                    sys.stderr.write(f"[CHAT_DIRETO] Documento não encontrado no storage: {doc_id}\n")
            except Exception as e:
                docs_falha += 1
                print(f"Erro ao carregar documento {doc_id}: {e}")

        sys.stderr.write(f"[CHAT_DIRETO] Docs carregados: {docs_carregados}, falhas: {docs_falha}\n")
        sys.stderr.flush()

        if docs_content:
            contexto_docs = "\n\n---\n\n".join(docs_content)

    # System prompt padrão - SIMPLIFICADO para garantir uso de python-exec
    # VERSAO 2.0 - 2026-01-28 - COM PYTHON-EXEC
    print("[DEBUG-V2] SYSTEM PROMPT V2.0 LOADED - WITH PYTHON-EXEC")
    system_prompt = """Voce e um assistente educacional especializado em correcao de provas.

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
- NAO use blocos documento: ou document:
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

    if contexto_docs:
        system_prompt += f"\n\n## DOCUMENTOS DISPONÍVEIS PARA CONSULTA:\n{contexto_docs}"

    # ============================================================
    # NOVO SISTEMA: Usar model_id do model_manager
    # ============================================================
    if data.model_id:
        model_config = model_manager.get(data.model_id)
        if not model_config:
            raise HTTPException(400, f"Modelo não encontrado: {data.model_id}")

        # Usar system prompt do modelo se configurado
        if model_config.system_prompt:
            system_prompt = model_config.system_prompt
            if contexto_docs:
                system_prompt += f"\n\n## DOCUMENTOS DISPONÍVEIS PARA CONSULTA:\n{contexto_docs}"

        # Obter API key
        api_key = None
        if model_config.api_key_id:
            key_config = api_key_manager.get(model_config.api_key_id)
            if key_config:
                api_key = key_config.api_key

        if not api_key:
            key_config = api_key_manager.get_por_empresa(model_config.tipo)
            if key_config:
                api_key = key_config.api_key

        # Ollama não precisa de API key
        if not api_key and model_config.tipo == ProviderType.OLLAMA:
            api_key = "ollama"

        # Fallback: variáveis de ambiente (para produção/Render)
        if not api_key:
            import os
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
                api_key = os.getenv(env_var)

        if not api_key:
            raise HTTPException(400, f"API key não configurada para {model_config.tipo.value}")

        try:
            # DEBUG: Ver qual system prompt está sendo enviado
            print(f"[DEBUG] Model: {model_config.nome}")
            print(f"[DEBUG] Model system_prompt is None: {model_config.system_prompt is None}")
            print(f"[DEBUG] Using system prompt (first 200 chars): {system_prompt[:200]}...")

            # Usar ChatClient do novo sistema
            client = ChatClient(model_config, api_key)
            resposta = await client.chat(user_message, historico, system_prompt)

            # Processar blocos python-exec se houver
            resposta_final = resposta["content"]
            try:
                from chat_service import chat_service
                resposta_final, arquivos_gerados = await chat_service._processar_codigo_executavel(
                    resposta["content"],
                    atividade_id=None,
                    aluno_id=None
                )
                if arquivos_gerados:
                    print(f"[INFO] Arquivos gerados via python-exec: {arquivos_gerados}")
            except ImportError:
                print("[WARN] chat_service nao disponivel para processar python-exec")
            except Exception as e:
                print(f"[ERROR] Erro ao processar python-exec: {e}")

            latency_ms = (time.time() - start_time) * 1000

            # DEBUG: Add marker to response content to verify this exact code is running
            debug_marker = "\n\n<!-- DEBUG_V3_MARKER_2026 -->"

            return {
                "response": resposta_final + debug_marker,
                "provider": model_config.tipo.value,
                "model": resposta["modelo"],
                "model_name": model_config.nome,
                "tokens_used": resposta["tokens"],
                "latency_ms": round(latency_ms, 2),
                "debug_endpoint": "chat_direto_v3",
                "debug_prompt_start": system_prompt[:100] if system_prompt else "NONE"
            }
        except Exception as e:
            raise HTTPException(500, f"Erro ao processar chat: {str(e)}")

    # ============================================================
    # SISTEMA LEGADO: Usar provider do ai_registry
    # ============================================================
    elif data.provider:
        from ai_providers import ai_registry

        try:
            provider = ai_registry.get(data.provider)
        except ValueError as e:
            raise HTTPException(400, f"Provider não encontrado: {data.provider}")

        # Montar prompt final (formato antigo)
        prompt = user_message
        historico_texto = ""
        if len(data.messages) > 1:
            for msg in data.messages[:-1]:
                role_label = "Usuário" if msg.role == "user" else "Assistente"
                historico_texto += f"{role_label}: {msg.content}\n\n"

        if historico_texto:
            prompt = f"Histórico da conversa:\n{historico_texto}\n\nMensagem atual: {user_message}"

        try:
            response = await provider.complete(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=4096
            )

            # Processar blocos python-exec se houver
            resposta_final = response.content
            try:
                from chat_service import chat_service
                resposta_final, arquivos_gerados = await chat_service._processar_codigo_executavel(
                    response.content,
                    atividade_id=None,
                    aluno_id=None
                )
                if arquivos_gerados:
                    print(f"[INFO] Arquivos gerados via python-exec: {arquivos_gerados}")
            except ImportError:
                print("[WARN] chat_service nao disponivel para processar python-exec")
            except Exception as e:
                print(f"[ERROR] Erro ao processar python-exec: {e}")

            latency_ms = (time.time() - start_time) * 1000

            return {
                "response": resposta_final,
                "provider": data.provider,
                "model": response.model,
                "tokens_used": response.tokens_used,
                "latency_ms": round(latency_ms, 2)
            }
        except Exception as e:
            raise HTTPException(500, f"Erro ao processar chat: {str(e)}")

    else:
        raise HTTPException(400, "Informe model_id ou provider para o chat")


def _ler_conteudo_documento(documento) -> Optional[str]:
    """Lê conteúdo de um documento para incluir no contexto do chat.

    Usa storage.resolver_caminho_documento() para baixar do Supabase se não existir localmente.
    """
    import json
    import sys

    try:
        sys.stderr.write(f"[_ler_conteudo] Tentando ler: {documento.id} - {documento.nome_arquivo}\n")
        sys.stderr.write(f"[_ler_conteudo] Caminho original: {documento.caminho_arquivo}\n")
        sys.stderr.flush()

        # Usar resolver_caminho_documento para obter arquivo (baixa do Supabase se necessário)
        arquivo = storage.resolver_caminho_documento(documento)
        sys.stderr.write(f"[_ler_conteudo] Arquivo resolvido: {arquivo}\n")
        sys.stderr.flush()

        if arquivo is None or not arquivo.exists():
            sys.stderr.write(f"[_ler_conteudo] ERRO: Arquivo não encontrado após resolver: {documento.caminho_arquivo}\n")
            sys.stderr.flush()
            return None

        if documento.extensao.lower() == '.json':
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)

        elif documento.extensao.lower() in ['.txt', '.md']:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return f.read()

        else:
            return f"[Arquivo binário: {documento.nome_arquivo} - {documento.extensao}]"

    except Exception as e:
        print(f"Erro ao ler documento: {e}")
        return None


# ============================================================
# API KEYS POR EMPRESA
# ============================================================

@router.get("/api/settings/api-keys", tags=["Settings - API Keys"])
async def listar_api_keys():
    """Lista todas as API keys configuradas"""
    keys = api_key_manager.listar()
    
    return {
        "api_keys": [k.to_dict() for k in keys],
        "total": len(keys)
    }


@router.get("/api/settings/api-keys/empresas", tags=["Settings - API Keys"])
async def listar_empresas():
    """Lista empresas/providers disponíveis"""
    return {"empresas": get_tipos_providers()}


@router.post("/api/settings/api-keys", tags=["Settings - API Keys"])
async def criar_api_key(data: ApiKeyCreate):
    """Adiciona nova API key para uma empresa"""
    try:
        empresa = ProviderType(data.empresa)
    except ValueError:
        raise HTTPException(400, f"Empresa inválida: {data.empresa}")
    
    key = api_key_manager.adicionar(
        empresa=empresa,
        api_key=data.api_key,
        nome_exibicao=data.nome_exibicao or ""
    )
    
    return {"success": True, "api_key": key.to_dict()}


@router.put("/api/settings/api-keys/{key_id}", tags=["Settings - API Keys"])
async def atualizar_api_key(key_id: str, data: ApiKeyUpdate):
    """Atualiza uma API key"""
    updates = {k: v for k, v in data.dict().items() if v is not None}
    
    key = api_key_manager.atualizar(key_id, **updates)
    if not key:
        raise HTTPException(404, "API key não encontrada")
    
    return {"success": True, "api_key": key.to_dict()}


@router.delete("/api/settings/api-keys/{key_id}", tags=["Settings - API Keys"])
async def remover_api_key(key_id: str):
    """Remove uma API key"""
    success = api_key_manager.remover(key_id)
    if not success:
        raise HTTPException(404, "API key não encontrada")
    
    return {"success": True}


# ============================================================
# MODELOS DE IA
# ============================================================

@router.get("/api/settings/models", tags=["Settings - Modelos"])
async def listar_modelos():
    """Lista todos os modelos configurados"""
    models = model_manager.listar(apenas_ativos=False)
    
    return {
        "models": [m.to_dict() for m in models],
        "total": len(models)
    }


@router.get("/api/settings/models/sugeridos", tags=["Settings - Modelos"])
async def listar_modelos_sugeridos(tipo: Optional[str] = None):
    """Lista modelos sugeridos por tipo de provider"""
    if tipo:
        try:
            provider_type = ProviderType(tipo)
            return {"modelos": MODELOS_SUGERIDOS.get(provider_type, [])}
        except ValueError:
            raise HTTPException(400, f"Tipo inválido: {tipo}")
    
    return {"modelos_por_tipo": {t.value: m for t, m in MODELOS_SUGERIDOS.items()}}


@router.post("/api/settings/models", tags=["Settings - Modelos"])
async def criar_modelo(data: ModelCreate):
    """Cria novo modelo de IA"""
    try:
        tipo = ProviderType(data.tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo inválido: {data.tipo}")
    
    model = model_manager.adicionar(
        nome=data.nome,
        tipo=tipo,
        modelo=data.modelo,
        api_key_id=data.api_key_id,
        max_tokens=data.max_tokens or 4096,
        temperature=data.temperature,
        parametros=data.parametros or {},
        system_prompt=data.system_prompt,
        base_url=data.base_url
    )
    
    return {"success": True, "model": model.to_dict()}


@router.get("/api/settings/models/{model_id}", tags=["Settings - Modelos"])
async def get_modelo(model_id: str):
    """Busca modelo por ID"""
    model = model_manager.get(model_id)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    
    return {"model": model.to_dict()}


@router.put("/api/settings/models/{model_id}", tags=["Settings - Modelos"])
async def atualizar_modelo(model_id: str, data: ModelUpdate):
    """Atualiza modelo existente"""
    updates = {k: v for k, v in data.dict().items() if v is not None}
    
    model = model_manager.atualizar(model_id, **updates)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    
    return {"success": True, "model": model.to_dict()}


@router.delete("/api/settings/models/{model_id}", tags=["Settings - Modelos"])
async def remover_modelo(model_id: str):
    """Remove um modelo"""
    success = model_manager.remover(model_id)
    if not success:
        raise HTTPException(404, "Modelo não encontrado")
    
    return {"success": True}


@router.post("/api/settings/models/{model_id}/default", tags=["Settings - Modelos"])
async def definir_modelo_padrao(model_id: str):
    """Define um modelo como padrão"""
    success = model_manager.set_default(model_id)
    if not success:
        raise HTTPException(404, "Modelo não encontrado")
    
    return {"success": True}


@router.post("/api/settings/models/{model_id}/testar", tags=["Settings - Modelos"])
async def testar_modelo(model_id: str):
    """Testa conexão com um modelo"""
    from chat_service import ChatClient
    
    model = model_manager.get(model_id)
    if not model:
        raise HTTPException(404, "Modelo não encontrado")
    
    # Obter API key
    api_key = None
    if model.api_key_id:
        key_config = api_key_manager.get(model.api_key_id)
        if key_config:
            api_key = key_config.api_key
    
    if not api_key:
        key_config = api_key_manager.get_por_empresa(model.tipo)
        if key_config:
            api_key = key_config.api_key
    
    if not api_key and model.tipo != ProviderType.OLLAMA:
        return {"success": False, "erro": f"API key não configurada para {model.tipo.value}"}
    
    try:
        client = ChatClient(model, api_key or "ollama")
        resposta = await client.chat(
            "Responda apenas: OK",
            system_prompt="Responda apenas com a palavra OK, nada mais."
        )
        
        return {
            "success": True,
            "resposta": resposta["content"][:100],
            "modelo": resposta["modelo"],
            "tokens": resposta["tokens"]
        }
    except Exception as e:
        return {"success": False, "erro": str(e)}


# ============================================================
# SESSÕES DE CHAT
# ============================================================

@router.post("/api/chat/sessoes", tags=["Chat"])
async def criar_sessao(data: ChatSessionCreate):
    """Cria nova sessão de chat"""
    sessao = chat_service.criar_sessao(
        titulo=data.titulo or "Nova conversa",
        model_id=data.model_id,
        atividade_id=data.atividade_id,
        aluno_id=data.aluno_id,
        etapa_pipeline=data.etapa_pipeline
    )
    
    return {"success": True, "sessao": sessao.to_dict()}


@router.get("/api/chat/sessoes", tags=["Chat"])
async def listar_sessoes():
    """Lista todas as sessões de chat"""
    sessoes = chat_service.listar_sessoes()
    
    return {
        "sessoes": [s.to_dict() for s in sessoes],
        "total": len(sessoes)
    }


@router.get("/api/chat/sessoes/{session_id}", tags=["Chat"])
async def get_sessao(session_id: str):
    """Busca sessão por ID com mensagens"""
    sessao = chat_service.get_sessao(session_id)
    if not sessao:
        raise HTTPException(404, "Sessão não encontrada")
    
    return {"sessao": sessao.to_dict()}


@router.delete("/api/chat/sessoes/{session_id}", tags=["Chat"])
async def deletar_sessao(session_id: str):
    """Deleta uma sessão"""
    success = chat_service.deletar_sessao(session_id)
    if not success:
        raise HTTPException(404, "Sessão não encontrada")
    
    return {"success": True}


@router.post("/api/chat/sessoes/{session_id}/mensagem", tags=["Chat"])
async def enviar_mensagem(session_id: str, data: ChatMessageSend):
    """Envia mensagem no chat"""
    sessao = chat_service.get_sessao(session_id)
    if not sessao:
        raise HTTPException(404, "Sessão não encontrada")
    
    try:
        resposta = await chat_service.enviar_mensagem(
            session_id=session_id,
            mensagem=data.mensagem,
            model_id=data.model_id,
            system_prompt=data.system_prompt,
            incluir_contexto_docs=data.incluir_contexto_docs
        )
        
        return {"success": True, "resposta": resposta.to_dict()}
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================
# CHAT RÁPIDO (SEM SESSÃO)
# ============================================================

@router.post("/api/chat/rapido", tags=["Chat"])
async def chat_rapido(
    mensagem: str = Form(...),
    model_id: Optional[str] = Form(None),
    atividade_id: Optional[str] = Form(None),
    aluno_id: Optional[str] = Form(None),
    system_prompt: Optional[str] = Form(None),
    etapa_pipeline: Optional[str] = Form(None)
):
    """Chat rápido sem precisar criar sessão"""
    sessao = chat_service.criar_sessao(
        titulo="Chat rápido",
        model_id=model_id,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        etapa_pipeline=etapa_pipeline
    )
    
    try:
        resposta = await chat_service.enviar_mensagem(
            session_id=sessao.id,
            mensagem=mensagem,
            model_id=model_id,
            system_prompt=system_prompt,
            incluir_contexto_docs=bool(atividade_id)
        )
        
        return {
            "success": True,
            "session_id": sessao.id,
            "resposta": resposta.content,
            "modelo": resposta.modelo,
            "provider": resposta.provider,
            "tokens": resposta.tokens,
            "arquivos_gerados": resposta.arquivos_gerados
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================
# DOCUMENTOS - LEITURA PELA IA
# ============================================================

@router.get("/api/chat/documentos/{atividade_id}", tags=["Chat - Documentos"])
async def listar_documentos_para_chat(atividade_id: str, aluno_id: Optional[str] = None):
    """Lista documentos disponíveis para uma atividade"""
    docs = chat_service.listar_documentos_disponiveis(atividade_id, aluno_id)
    
    return {"documentos": docs, "total": len(docs)}


@router.get("/api/chat/documentos/ler/{documento_id}", tags=["Chat - Documentos"])
async def ler_documento_para_chat(documento_id: str):
    """Lê conteúdo completo de um documento"""
    doc = chat_service.ler_documento_completo(documento_id)
    if not doc:
        raise HTTPException(404, "Documento não encontrado")
    
    return {"documento": doc}


# ============================================================
# ARQUIVOS GERADOS
# ============================================================

@router.get("/api/chat/arquivos", tags=["Chat - Arquivos"])
async def listar_arquivos_chat():
    """Lista arquivos gerados pelo chat"""
    pasta = Path(storage.base_path) / "chat_outputs"
    
    if not pasta.exists():
        return {"arquivos": [], "total": 0}
    
    arquivos = []
    for f in pasta.rglob("*"):
        if f.is_file():
            arquivos.append({
                "nome": f.name,
                "caminho": str(f.relative_to(pasta)),
                "tamanho": f.stat().st_size,
                "modificado": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    return {"arquivos": arquivos, "total": len(arquivos)}


@router.get("/api/chat/arquivos/download/{caminho:path}", tags=["Chat - Arquivos"])
async def download_arquivo(caminho: str):
    """Download de arquivo gerado pelo chat"""
    arquivo = Path(storage.base_path) / "chat_outputs" / caminho

    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado")

    mime_type = get_mime_type(arquivo)
    return FileResponse(arquivo, filename=arquivo.name, media_type=mime_type)


@router.get("/api/chat/arquivos/view/{caminho:path}", tags=["Chat - Arquivos"])
async def view_arquivo(caminho: str):
    """Visualiza arquivo inline no navegador (para PDFs, imagens, HTML)"""
    arquivo = Path(storage.base_path) / "chat_outputs" / caminho

    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado")

    mime_type = get_mime_type(arquivo)

    # Tipos que podem ser visualizados inline no navegador
    inline_types = [
        'application/pdf',
        'image/',
        'text/html',
        'text/plain',
        'application/json',
        'text/markdown'
    ]

    can_inline = any(mime_type.startswith(t) for t in inline_types)

    if can_inline:
        # Content-Disposition: inline permite visualização no navegador
        return FileResponse(
            arquivo,
            media_type=mime_type,
            headers={"Content-Disposition": f"inline; filename=\"{arquivo.name}\""}
        )
    else:
        # Para outros tipos, força download
        return FileResponse(arquivo, filename=arquivo.name, media_type=mime_type)


# ============================================================
# CONFIGURAÇÃO GLOBAL
# ============================================================

@router.get("/api/settings/status", tags=["Settings"])
async def get_status_configuracao():
    """Retorna status geral da configuração"""
    default_model = model_manager.get_default()
    api_keys = api_key_manager.listar()
    models = model_manager.listar()

    return {
        "modelo_padrao": default_model.to_dict() if default_model else None,
        "total_api_keys": len(api_keys),
        "total_modelos": len(models),
        "empresas_configuradas": list(set(k.empresa.value for k in api_keys)),
        "tipos_disponiveis": [t.value for t in ProviderType],
        "encryption_enabled": api_key_manager.is_encryption_enabled()
    }


# ============================================================
# CATÁLOGO DE MODELOS
# ============================================================

@router.get("/api/settings/model-catalog", tags=["Model Catalog"])
async def get_model_catalog():
    """Retorna catálogo completo de modelos com custos e capacidades"""
    return model_catalog.get_full_catalog()


@router.get("/api/settings/model-catalog/summary", tags=["Model Catalog"])
async def get_catalog_summary():
    """Retorna resumo do catálogo"""
    return model_catalog.get_catalog_summary()


@router.get("/api/settings/model-catalog/{provider}", tags=["Model Catalog"])
async def get_provider_models(provider: str):
    """Retorna modelos de um provedor específico"""
    provider_info = model_catalog.get_provider(provider)
    if not provider_info:
        raise HTTPException(404, f"Provedor '{provider}' não encontrado")

    return {
        "provider": provider_info.to_dict()
    }


@router.get("/api/settings/model-catalog/{provider}/{model_id}", tags=["Model Catalog"])
async def get_model_info(provider: str, model_id: str):
    """Retorna informações detalhadas de um modelo"""
    model = model_catalog.get_model_info(provider, model_id)
    if not model:
        raise HTTPException(404, f"Modelo '{model_id}' não encontrado no provedor '{provider}'")

    return {
        "model": model.to_dict()
    }


class ModelSearchParams(BaseModel):
    supports_vision: Optional[bool] = None
    supports_tools: Optional[bool] = None
    supports_reasoning: Optional[bool] = None
    supports_search: Optional[bool] = None
    max_input_cost: Optional[float] = None
    min_context_window: Optional[int] = None
    provider: Optional[str] = None
    is_local: Optional[bool] = None


@router.post("/api/settings/model-catalog/search", tags=["Model Catalog"])
async def search_models(params: ModelSearchParams):
    """Busca modelos por capacidades e critérios"""
    results = model_catalog.search_models(
        supports_vision=params.supports_vision,
        supports_tools=params.supports_tools,
        supports_reasoning=params.supports_reasoning,
        supports_search=params.supports_search,
        max_input_cost=params.max_input_cost,
        min_context_window=params.min_context_window,
        provider=params.provider,
        is_local=params.is_local
    )

    return {
        "models": [m.to_dict() for m in results],
        "total": len(results)
    }


class CostCalculationRequest(BaseModel):
    model_ref: str  # "provider/model_id"
    input_tokens: int
    output_tokens: int
    requests_per_day: int = 1
    use_cache: bool = False


@router.post("/api/settings/model-catalog/calculate-cost", tags=["Model Catalog"])
async def calculate_model_cost(params: CostCalculationRequest):
    """Calcula custo estimado para um modelo"""
    result = model_catalog.calculate_cost(
        model_ref=params.model_ref,
        input_tokens=params.input_tokens,
        output_tokens=params.output_tokens,
        requests_per_day=params.requests_per_day,
        use_cache=params.use_cache
    )

    if "error" in result:
        raise HTTPException(400, result["error"])

    return result


class CostComparisonRequest(BaseModel):
    model_refs: List[str]  # ["openai/gpt-4o", "anthropic/claude-sonnet-4.5"]


@router.post("/api/settings/model-catalog/compare-costs", tags=["Model Catalog"])
async def compare_model_costs(params: CostComparisonRequest):
    """Compara custos entre múltiplos modelos"""
    results = model_catalog.get_cost_comparison(params.model_refs)
    return {"models": results}


# ============================================================
# MODELO CUSTOMIZADO
# ============================================================

class CustomModelCreate(BaseModel):
    nome: str
    tipo: str  # "openai", "anthropic", etc.
    custom_model_id: str  # ID exato do modelo
    custom_base_url: str  # URL customizada
    api_version: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    system_prompt: Optional[str] = None


@router.post("/api/settings/models/custom", tags=["Models"])
async def criar_modelo_customizado(data: CustomModelCreate):
    """Cria um modelo com endpoint totalmente customizado"""
    try:
        provider_type = ProviderType(data.tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo de provider inválido: {data.tipo}")

    model = model_manager.adicionar(
        nome=data.nome,
        tipo=provider_type,
        modelo=data.custom_model_id,
        base_url=data.custom_base_url,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        system_prompt=data.system_prompt
    )

    # Adicionar campos customizados
    if data.api_version:
        model.api_version = data.api_version
    if data.extra_headers:
        model.extra_headers = data.extra_headers
    model.custom_model_id = data.custom_model_id

    # Salvar alterações
    model_manager._save()

    return {"success": True, "model": model.to_dict()}


class ModelFromCatalogCreate(BaseModel):
    catalog_ref: str  # "openai/gpt-4o"
    nome: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    system_prompt: Optional[str] = None


@router.post("/api/settings/models/from-catalog", tags=["Models"])
async def criar_modelo_do_catalogo(data: ModelFromCatalogCreate):
    """Cria um modelo a partir do catálogo (pré-configurado)"""
    if "/" not in data.catalog_ref:
        raise HTTPException(400, "Formato inválido. Use 'provider/model_id'")

    provider, model_id = data.catalog_ref.split("/", 1)

    # Buscar info do catálogo
    catalog_model = model_catalog.get_model_info(provider, model_id)
    if not catalog_model:
        raise HTTPException(404, f"Modelo '{data.catalog_ref}' não encontrado no catálogo")

    try:
        provider_type = ProviderType(provider)
    except ValueError:
        raise HTTPException(400, f"Provider '{provider}' não suportado")

    # Criar modelo com dados do catálogo
    model = model_manager.adicionar(
        nome=data.nome or catalog_model.display_name,
        tipo=provider_type,
        modelo=model_id,
        max_tokens=data.max_tokens or catalog_model.max_output or 4096,
        temperature=data.temperature if data.temperature is not None else (0.7 if catalog_model.requires_temperature else None),
        system_prompt=data.system_prompt,
        suporta_vision=catalog_model.supports_vision,
        suporta_function_calling=catalog_model.supports_tools,
        suporta_temperature=catalog_model.requires_temperature
    )

    # Adicionar referência ao catálogo
    model.catalog_ref = data.catalog_ref
    model_manager._save()

    return {"success": True, "model": model.to_dict()}


# ============================================================
# DETECÇÃO DE MODELOS LOCAIS
# ============================================================

@router.get("/api/settings/local-models/{provider}", tags=["Local Models"])
async def detectar_modelos_locais(provider: str):
    """Detecta modelos disponíveis em provedores locais"""
    if provider == "ollama":
        return await detect_ollama_models()
    elif provider == "vllm":
        return await detect_vllm_models()
    elif provider == "lmstudio":
        return await detect_lmstudio_models()

    raise HTTPException(400, f"Provider '{provider}' não suporta detecção automática")


async def detect_ollama_models():
    """Lista modelos instalados no Ollama"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "online": True,
                    "base_url": "http://localhost:11434",
                    "models": [
                        {
                            "id": m["name"],
                            "display_name": m["name"].split(":")[0].title(),
                            "size": m.get("size", 0),
                            "modified": m.get("modified_at"),
                            "details": m.get("details", {})
                        }
                        for m in data.get("models", [])
                    ]
                }
    except Exception as e:
        pass

    return {"online": False, "base_url": "http://localhost:11434", "models": [], "error": "Servidor não encontrado"}


async def detect_vllm_models():
    """Lista modelos no servidor vLLM"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:8000/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "online": True,
                    "base_url": "http://localhost:8000",
                    "models": [
                        {"id": m["id"], "display_name": m["id"]}
                        for m in data.get("data", [])
                    ]
                }
    except Exception as e:
        pass

    return {"online": False, "base_url": "http://localhost:8000", "models": [], "error": "Servidor não encontrado"}


async def detect_lmstudio_models():
    """Lista modelos no LM Studio"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "online": True,
                    "base_url": "http://localhost:1234",
                    "models": [
                        {"id": m["id"], "display_name": m["id"]}
                        for m in data.get("data", [])
                    ]
                }
    except Exception as e:
        pass

    return {"online": False, "base_url": "http://localhost:1234", "models": [], "error": "Servidor não encontrado"}


@router.get("/api/settings/local-models", tags=["Local Models"])
async def detectar_todos_modelos_locais():
    """Detecta modelos em todos os provedores locais"""
    results = {
        "ollama": await detect_ollama_models(),
        "vllm": await detect_vllm_models(),
        "lmstudio": await detect_lmstudio_models()
    }

    online_count = sum(1 for r in results.values() if r.get("online"))
    total_models = sum(len(r.get("models", [])) for r in results.values())

    return {
        "providers": results,
        "summary": {
            "online_providers": online_count,
            "total_models": total_models
        }
    }
