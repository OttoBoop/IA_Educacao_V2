"""
PROVA AI - API v2.0

Endpoints organizados por recurso:
- /api/materias
- /api/turmas
- /api/alunos
- /api/atividades
- /api/documentos
- /api/navegacao
- /api/providers
- /api/status
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import os
import json
import tempfile
import shutil

# Importar nossos módulos
from models import (
    Materia, Turma, Aluno, Atividade, Documento, Prompt,
    TipoDocumento, StatusProcessamento, NivelEnsino,
    verificar_dependencias
)
from storage_v2 import StorageManagerV2, storage_v2
from ai_providers import (
    ai_registry,
    setup_providers_from_env,
    OpenAIProvider,
    AnthropicProvider,
    LocalLLMProvider,
)

# Importar rotas opcionais usando importlib para evitar erros de resolução estática
import importlib

def _try_import_router(module_name: str):
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None
    return getattr(module, "router", None)

extras_router = _try_import_router("routes_extras")
HAS_EXTRAS = extras_router is not None

prompts_router = _try_import_router("routes_prompts")
HAS_PROMPTS = prompts_router is not None

resultados_router = _try_import_router("routes_resultados")
HAS_RESULTADOS = resultados_router is not None

chat_router = _try_import_router("routes_chat")
HAS_CHAT = chat_router is not None

visualizacao_router = _try_import_router("routes_visualizacao")
HAS_VISUALIZACAO = visualizacao_router is not None

aluno_router = _try_import_router("routes_aluno")
HAS_ALUNO = aluno_router is not None


# ============================================================
# APP SETUP
# ============================================================

app = FastAPI(
    title="Prova AI - Sistema de Correção v2.0",
    description="Sistema de correção automatizada de provas com IA",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rotas extras se disponíveis
if HAS_EXTRAS:
    app.include_router(extras_router)

# Incluir rotas de prompts se disponíveis
if HAS_PROMPTS:
    app.include_router(prompts_router)

# Incluir rotas de resultados se disponíveis
if HAS_RESULTADOS:
    app.include_router(resultados_router)

# Incluir rotas de chat se disponíveis
if HAS_CHAT:
    app.include_router(chat_router)

# Incluir rotas de visualização se disponíveis
if HAS_VISUALIZACAO:
    app.include_router(visualizacao_router)

# Incluir rotas de aluno se disponíveis
if HAS_ALUNO:
    app.include_router(aluno_router)

# Storage
storage = storage_v2


# ============================================================
# MODELOS PYDANTIC (Request/Response)
# ============================================================

# --- Matérias ---
class MateriaCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    nivel: Optional[str] = "outro"

class MateriaUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    nivel: Optional[str] = None

class MateriaResponse(BaseModel):
    id: str
    nome: str
    descricao: Optional[str]
    nivel: str
    criado_em: str
    atualizado_em: str

# --- Turmas ---
class TurmaCreate(BaseModel):
    materia_id: str
    nome: str
    ano_letivo: Optional[int] = None
    periodo: Optional[str] = None
    descricao: Optional[str] = None

class TurmaUpdate(BaseModel):
    nome: Optional[str] = None
    ano_letivo: Optional[int] = None
    periodo: Optional[str] = None
    descricao: Optional[str] = None

# --- Alunos ---
class AlunoCreate(BaseModel):
    nome: str
    email: Optional[str] = None
    matricula: Optional[str] = None

class AlunoUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    matricula: Optional[str] = None

class VinculoAlunoTurma(BaseModel):
    aluno_id: str
    turma_id: str
    observacoes: Optional[str] = None

# --- Atividades ---
class AtividadeCreate(BaseModel):
    turma_id: str
    nome: str
    tipo: Optional[str] = None  # "prova", "trabalho", "exercicio"
    data_aplicacao: Optional[str] = None  # ISO format
    nota_maxima: Optional[float] = 10.0
    descricao: Optional[str] = None

class AtividadeUpdate(BaseModel):
    nome: Optional[str] = None
    tipo: Optional[str] = None
    data_aplicacao: Optional[str] = None
    nota_maxima: Optional[float] = None
    descricao: Optional[str] = None

# --- Documentos ---
class DocumentoResponse(BaseModel):
    id: str
    tipo: str
    atividade_id: str
    aluno_id: Optional[str]
    nome_arquivo: str
    extensao: str
    tamanho_bytes: int
    ia_provider: Optional[str]
    ia_modelo: Optional[str]
    status: str
    criado_em: str
    versao: int

# --- Providers ---
class ProviderConfig(BaseModel):
    name: str
    provider_type: str  # "openai", "anthropic", "ollama"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None

# --- Verificação ---
class VerificacaoRequest(BaseModel):
    atividade_id: str
    aluno_id: Optional[str] = None
    tipo_alvo: str  # Tipo que quer gerar


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup():
    """Inicializa providers de IA"""
    try:
        setup_providers_from_env()
        print(f"✓ Providers carregados: {ai_registry.list_providers()}")
    except Exception as e:
        print(f"⚠ Erro ao carregar providers: {e}")


# ============================================================
# ENDPOINTS: MATÉRIAS
# ============================================================

@app.post("/api/materias", tags=["Matérias"])
async def criar_materia(data: MateriaCreate):
    """Cria uma nova matéria"""
    nivel = NivelEnsino(data.nivel) if data.nivel else NivelEnsino.OUTRO
    materia = storage.criar_materia(data.nome, data.descricao, nivel)
    return {"success": True, "materia": materia.to_dict()}


@app.get("/api/materias", tags=["Matérias"])
async def listar_materias():
    """Lista todas as matérias"""
    materias = storage.listar_materias()
    return {"materias": [m.to_dict() for m in materias]}


@app.get("/api/materias/{materia_id}", tags=["Matérias"])
async def get_materia(materia_id: str):
    """Busca matéria por ID"""
    materia = storage.get_materia(materia_id)
    if not materia:
        raise HTTPException(404, "Matéria não encontrada")
    
    # Incluir turmas
    turmas = storage.listar_turmas(materia_id)
    
    return {
        "materia": materia.to_dict(),
        "turmas": [t.to_dict() for t in turmas],
        "total_turmas": len(turmas)
    }


@app.put("/api/materias/{materia_id}", tags=["Matérias"])
async def atualizar_materia(materia_id: str, data: MateriaUpdate):
    """Atualiza uma matéria"""
    updates = {k: v for k, v in data.dict().items() if v is not None}
    materia = storage.atualizar_materia(materia_id, **updates)
    if not materia:
        raise HTTPException(404, "Matéria não encontrada")
    return {"success": True, "materia": materia.to_dict()}


@app.delete("/api/materias/{materia_id}", tags=["Matérias"])
async def deletar_materia(materia_id: str):
    """Deleta uma matéria e todos os dados relacionados"""
    success = storage.deletar_materia(materia_id)
    if not success:
        raise HTTPException(404, "Matéria não encontrada")
    return {"success": True, "deleted": materia_id}


# ============================================================
# ENDPOINTS: TURMAS
# ============================================================

@app.post("/api/turmas", tags=["Turmas"])
async def criar_turma(data: TurmaCreate):
    """Cria uma nova turma dentro de uma matéria"""
    turma = storage.criar_turma(
        materia_id=data.materia_id,
        nome=data.nome,
        ano_letivo=data.ano_letivo,
        periodo=data.periodo,
        descricao=data.descricao
    )
    if not turma:
        raise HTTPException(400, "Matéria não encontrada")
    return {"success": True, "turma": turma.to_dict()}


@app.get("/api/turmas", tags=["Turmas"])
async def listar_turmas(materia_id: Optional[str] = None):
    """Lista turmas, opcionalmente filtradas por matéria"""
    turmas = storage.listar_turmas(materia_id)
    return {"turmas": [t.to_dict() for t in turmas]}


@app.get("/api/turmas/{turma_id}", tags=["Turmas"])
async def get_turma(turma_id: str):
    """Busca turma por ID com detalhes"""
    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")
    
    materia = storage.get_materia(turma.materia_id)
    alunos = storage.listar_alunos(turma_id)
    atividades = storage.listar_atividades(turma_id)
    
    return {
        "turma": turma.to_dict(),
        "materia": materia.to_dict() if materia else None,
        "alunos": [a.to_dict() for a in alunos],
        "atividades": [a.to_dict() for a in atividades],
        "total_alunos": len(alunos),
        "total_atividades": len(atividades)
    }


@app.delete("/api/turmas/{turma_id}", tags=["Turmas"])
async def deletar_turma(turma_id: str):
    """Deleta uma turma e todos os dados relacionados"""
    success = storage.deletar_turma(turma_id)
    if not success:
        raise HTTPException(404, "Turma não encontrada")
    return {"success": True, "deleted": turma_id}


# ============================================================
# ENDPOINTS: ALUNOS
# ============================================================

@app.post("/api/alunos", tags=["Alunos"])
async def criar_aluno(data: AlunoCreate):
    """Cria um novo aluno"""
    aluno = storage.criar_aluno(data.nome, data.email, data.matricula)
    return {"success": True, "aluno": aluno.to_dict()}


@app.get("/api/alunos", tags=["Alunos"])
async def listar_alunos(turma_id: Optional[str] = None):
    """Lista alunos, opcionalmente filtrados por turma"""
    alunos = storage.listar_alunos(turma_id)
    return {"alunos": [a.to_dict() for a in alunos]}


@app.get("/api/alunos/{aluno_id}", tags=["Alunos"])
async def get_aluno(aluno_id: str):
    """Busca aluno por ID com suas turmas"""
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    turmas = storage.get_turmas_do_aluno(aluno_id)
    
    return {
        "aluno": aluno.to_dict(),
        "turmas": turmas,
        "total_turmas": len(turmas)
    }


@app.delete("/api/alunos/{aluno_id}", tags=["Alunos"])
async def deletar_aluno(aluno_id: str):
    """Deleta um aluno"""
    # Implementar no storage se necessário
    raise HTTPException(501, "Não implementado ainda")


@app.post("/api/alunos/vincular", tags=["Alunos"])
async def vincular_aluno_turma(data: VinculoAlunoTurma):
    """Vincula um aluno a uma turma"""
    vinculo = storage.vincular_aluno_turma(data.aluno_id, data.turma_id, data.observacoes)
    if not vinculo:
        raise HTTPException(400, "Aluno ou turma não encontrados, ou vínculo já existe")
    return {"success": True, "vinculo": vinculo.to_dict()}


@app.post("/api/alunos/desvincular", tags=["Alunos"])
async def desvincular_aluno_turma(data: VinculoAlunoTurma):
    """Remove vínculo aluno-turma"""
    success = storage.desvincular_aluno_turma(data.aluno_id, data.turma_id)
    if not success:
        raise HTTPException(404, "Vínculo não encontrado")
    return {"success": True}


# ============================================================
# ENDPOINTS: ATIVIDADES
# ============================================================

@app.post("/api/atividades", tags=["Atividades"])
async def criar_atividade(data: AtividadeCreate):
    """Cria uma nova atividade dentro de uma turma"""
    data_aplicacao = None
    if data.data_aplicacao:
        data_aplicacao = datetime.fromisoformat(data.data_aplicacao)
    
    atividade = storage.criar_atividade(
        turma_id=data.turma_id,
        nome=data.nome,
        tipo=data.tipo,
        data_aplicacao=data_aplicacao,
        nota_maxima=data.nota_maxima or 10.0,
        descricao=data.descricao
    )
    if not atividade:
        raise HTTPException(400, "Turma não encontrada")
    return {"success": True, "atividade": atividade.to_dict()}


@app.get("/api/atividades", tags=["Atividades"])
async def listar_atividades(turma_id: str):
    """Lista atividades de uma turma"""
    atividades = storage.listar_atividades(turma_id)
    return {"atividades": [a.to_dict() for a in atividades]}


@app.get("/api/atividades/{atividade_id}", tags=["Atividades"])
async def get_atividade(atividade_id: str):
    """Busca atividade por ID com status completo"""
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    
    status = storage.get_status_atividade(atividade_id)
    
    return status


@app.delete("/api/atividades/{atividade_id}", tags=["Atividades"])
async def deletar_atividade(atividade_id: str):
    """Deleta uma atividade e todos os documentos"""
    success = storage.deletar_atividade(atividade_id)
    if not success:
        raise HTTPException(404, "Atividade não encontrada")
    return {"success": True, "deleted": atividade_id}


# ============================================================
# ENDPOINTS: DOCUMENTOS
# ============================================================

@app.post("/api/documentos/upload", tags=["Documentos"])
async def upload_documento(
    file: UploadFile = File(...),
    tipo: str = Form(...),
    atividade_id: str = Form(...),
    aluno_id: Optional[str] = Form(None),
    ia_provider: Optional[str] = Form(None)
):
    """
    Faz upload de um documento.
    
    - tipo: enunciado, gabarito, criterios_correcao, prova_respondida, correcao_professor
    - atividade_id: ID da atividade
    - aluno_id: ID do aluno (obrigatório para prova_respondida)
    - ia_provider: Provider para indexação (opcional)
    """
    # Validar tipo
    try:
        tipo_doc = TipoDocumento(tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo inválido: {tipo}. Tipos válidos: {[t.value for t in TipoDocumento]}")
    
    # Validar aluno_id para tipos que precisam
    if tipo_doc not in TipoDocumento.documentos_base() and not aluno_id:
        raise HTTPException(400, f"Tipo '{tipo}' requer aluno_id")
    
    # Salvar arquivo temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Salvar documento
        documento = storage.salvar_documento(
            arquivo_origem=tmp_path,
            tipo=tipo_doc,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            ia_provider=ia_provider,
            criado_por="usuario"
        )
        
        if not documento:
            raise HTTPException(400, "Erro ao salvar documento. Verifique atividade_id e aluno_id.")
        
        return {
            "success": True,
            "documento": documento.to_dict(),
            "mensagem": f"Documento '{file.filename}' salvo com sucesso"
        }
    
    finally:
        # Limpar temp
        os.unlink(tmp_path)


@app.get("/api/documentos", tags=["Documentos"])
async def listar_documentos(
    atividade_id: str,
    aluno_id: Optional[str] = None,
    tipo: Optional[str] = None
):
    """Lista documentos com filtros"""
    tipo_doc = TipoDocumento(tipo) if tipo else None
    documentos = storage.listar_documentos(atividade_id, aluno_id, tipo_doc)
    return {"documentos": [d.to_dict() for d in documentos]}


@app.get("/api/documentos/{documento_id}", tags=["Documentos"])
async def get_documento(documento_id: str):
    """Busca documento por ID"""
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    return {"documento": documento.to_dict()}


@app.get("/api/documentos/{documento_id}/download", tags=["Documentos"])
async def download_documento(documento_id: str):
    """Faz download do arquivo"""
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    arquivo = Path(documento.caminho_arquivo)
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado no sistema")
    
    return FileResponse(
        arquivo,
        filename=documento.nome_arquivo,
        media_type="application/octet-stream"
    )


@app.delete("/api/documentos/{documento_id}", tags=["Documentos"])
async def deletar_documento(documento_id: str):
    """Deleta um documento"""
    success = storage.deletar_documento(documento_id)
    if not success:
        raise HTTPException(404, "Documento não encontrado")
    return {"success": True, "deleted": documento_id}


@app.put("/api/documentos/{documento_id}/renomear", tags=["Documentos"])
async def renomear_documento(documento_id: str, novo_nome: str = Form(...)):
    """Renomeia um documento"""
    documento = storage.renomear_documento(documento_id, novo_nome)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    return {"success": True, "documento": documento.to_dict()}


# ============================================================
# ENDPOINTS: VERIFICAÇÃO E STATUS
# ============================================================

@app.post("/api/verificar", tags=["Verificação"])
async def verificar_pode_processar(data: VerificacaoRequest):
    """
    Verifica se um tipo de documento pode ser gerado.
    Retorna documentos faltantes (obrigatórios e opcionais).
    """
    try:
        tipo_alvo = TipoDocumento(data.tipo_alvo)
    except ValueError:
        raise HTTPException(400, f"Tipo inválido: {data.tipo_alvo}")
    
    resultado = storage.verificar_pode_processar(data.atividade_id, data.aluno_id, tipo_alvo)
    
    return {
        "tipo_alvo": data.tipo_alvo,
        "pode_processar": resultado["pode_processar"],
        "faltando_obrigatorios": [t.value for t in resultado["faltando_obrigatorios"]],
        "faltando_opcionais": [t.value for t in resultado["faltando_opcionais"]],
        "aviso": resultado["aviso"]
    }


@app.get("/api/atividades/{atividade_id}/status", tags=["Verificação"])
async def get_status_atividade(atividade_id: str):
    """
    Retorna status completo de uma atividade.
    Inclui documentos existentes, faltantes, e status por aluno.
    """
    status = storage.get_status_atividade(atividade_id)
    if "erro" in status:
        raise HTTPException(404, status["erro"])
    return status


# ============================================================
# ENDPOINTS: NAVEGAÇÃO
# ============================================================

@app.get("/api/navegacao/arvore", tags=["Navegação"])
async def get_arvore_navegacao():
    """
    Retorna árvore completa para navegação.
    Estrutura: Matérias → Turmas → Atividades
    """
    return storage.get_arvore_navegacao()


@app.get("/api/navegacao/breadcrumb/{tipo}/{id}", tags=["Navegação"])
async def get_breadcrumb(tipo: str, id: str):
    """
    Retorna breadcrumb (caminho) até um item.
    tipo: materia, turma, atividade, documento
    """
    breadcrumb = []
    
    if tipo == "materia":
        materia = storage.get_materia(id)
        if materia:
            breadcrumb = [{"tipo": "materia", "id": materia.id, "nome": materia.nome}]
    
    elif tipo == "turma":
        turma = storage.get_turma(id)
        if turma:
            materia = storage.get_materia(turma.materia_id)
            breadcrumb = [
                {"tipo": "materia", "id": materia.id, "nome": materia.nome},
                {"tipo": "turma", "id": turma.id, "nome": turma.nome}
            ]
    
    elif tipo == "atividade":
        atividade = storage.get_atividade(id)
        if atividade:
            turma = storage.get_turma(atividade.turma_id)
            materia = storage.get_materia(turma.materia_id) if turma else None
            breadcrumb = [
                {"tipo": "materia", "id": materia.id, "nome": materia.nome} if materia else None,
                {"tipo": "turma", "id": turma.id, "nome": turma.nome} if turma else None,
                {"tipo": "atividade", "id": atividade.id, "nome": atividade.nome}
            ]
            breadcrumb = [b for b in breadcrumb if b]
    
    elif tipo == "documento":
        documento = storage.get_documento(id)
        if documento:
            atividade = storage.get_atividade(documento.atividade_id)
            turma = storage.get_turma(atividade.turma_id) if atividade else None
            materia = storage.get_materia(turma.materia_id) if turma else None
            breadcrumb = [
                {"tipo": "materia", "id": materia.id, "nome": materia.nome} if materia else None,
                {"tipo": "turma", "id": turma.id, "nome": turma.nome} if turma else None,
                {"tipo": "atividade", "id": atividade.id, "nome": atividade.nome} if atividade else None,
                {"tipo": "documento", "id": documento.id, "nome": documento.nome_arquivo}
            ]
            breadcrumb = [b for b in breadcrumb if b]
    
    return {"breadcrumb": breadcrumb}


# ============================================================
# ENDPOINTS: PROVIDERS DE IA
# ============================================================

@app.get("/api/providers", tags=["Providers"])
async def listar_providers():
    """Lista todos os providers de IA disponíveis"""
    return {
        "providers": ai_registry.get_provider_info(),
        "default": ai_registry.default_provider
    }


@app.post("/api/providers", tags=["Providers"])
async def adicionar_provider(config: ProviderConfig):
    """Adiciona ou atualiza um provider de IA"""
    try:
        provider_type = config.provider_type.lower()
        if provider_type == "openai":
            provider = OpenAIProvider(
                api_key=config.api_key or os.getenv("OPENAI_API_KEY", ""),
                model=config.model
            )
        elif provider_type == "anthropic":
            provider = AnthropicProvider(
                api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY", ""),
                model=config.model
            )
        elif provider_type == "ollama":
            provider = LocalLLMProvider(
                base_url=config.base_url or "http://localhost:11434",
                model=config.model
            )
        else:
            raise HTTPException(400, f"Tipo de provider não suportado: {config.provider_type}")

        ai_registry.register(config.name, provider)
        return {"success": True, "name": config.name}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================
# ENDPOINTS: TIPOS E ENUMS
# ============================================================

@app.get("/api/tipos/documentos", tags=["Tipos"])
async def listar_tipos_documentos():
    """Lista todos os tipos de documentos disponíveis"""
    return {
        "tipos": {
            "base": [t.value for t in TipoDocumento.documentos_base()],
            "aluno": [t.value for t in TipoDocumento.documentos_aluno()],
            "gerados": [t.value for t in TipoDocumento.documentos_gerados()]
        },
        "todos": [t.value for t in TipoDocumento]
    }


@app.get("/api/tipos/niveis", tags=["Tipos"])
async def listar_niveis_ensino():
    """Lista níveis de ensino disponíveis"""
    return {"niveis": [n.value for n in NivelEnsino]}


# ============================================================
# FRONTEND (servir arquivos estáticos)
# ============================================================

FRONTEND_PATH = Path(__file__).parent.parent / "frontend"

@app.get("/", tags=["Frontend"])
async def serve_frontend():
    """Serve a página principal"""
    # Primeiro tenta v2, depois v1
    for filename in ["index_v2.html", "index.html"]:
        frontend_file = FRONTEND_PATH / filename
        if frontend_file.exists():
            return FileResponse(frontend_file)
    
    return JSONResponse({
        "message": "API Prova AI v2.0",
        "docs": "/docs",
        "endpoints": {
            "materias": "/api/materias",
            "turmas": "/api/turmas",
            "alunos": "/api/alunos",
            "atividades": "/api/atividades",
            "documentos": "/api/documentos",
            "navegacao": "/api/navegacao/arvore"
        }
    })


# Servir arquivos estáticos do frontend
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH)), name="static")


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
