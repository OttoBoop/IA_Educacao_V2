"""
API Principal - FastAPI

Endpoints para:
1. Upload e gerenciamento de arquivos
2. Configuração de providers de IA
3. Execução de pipelines
4. Consulta de resultados
5. Chat interativo com acesso aos documentos
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import asyncio

from ai_providers import (
    AIProvider, AIResponse, ai_registry, 
    OpenAIProvider, AnthropicProvider, LocalLLMProvider,
    setup_providers_from_env
)
from storage import (
    StorageManager, VectorStore, DocumentType,
    Questao, Correcao, storage, vector_store
)
from pipeline import CorrectionPipeline, PipelineConfig, PipelineStage


app = FastAPI(
    title="Prova AI - Sistema de Correção Automatizada",
    description="Framework para experimentação com diferentes IAs na correção de provas",
    version="0.1.0"
)

# CORS para permitir frontend local
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (frontend)
FRONTEND_PATH = Path(__file__).parent.parent / "frontend"
if FRONTEND_PATH.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_PATH)), name="static")


# ============== MODELOS PYDANTIC ==============

class ProviderConfig(BaseModel):
    name: str
    provider_type: str  # "openai", "anthropic", "ollama"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class PipelineConfigRequest(BaseModel):
    providers: Dict[str, str]  # {stage_name: provider_name}


class ChatMessage(BaseModel):
    role: str  # "user" ou "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    provider: Optional[str] = None
    context_docs: Optional[List[str]] = None  # IDs de documentos para contexto


class SearchRequest(BaseModel):
    query: str
    materia: Optional[str] = None
    top_k: int = 5


class CorrectionRequest(BaseModel):
    gabarito_id: str
    prova_aluno_path: str
    aluno_id: str
    aluno_nome: str
    materia: str
    pipeline_config: Optional[Dict[str, str]] = None


# ============== STARTUP ==============

@app.on_event("startup")
async def startup():
    """Inicializa providers e storage"""
    setup_providers_from_env()
    print(f"Providers registrados: {ai_registry.list_providers()}")


# ============== ENDPOINTS: PROVIDERS ==============

@app.get("/api/providers")
async def list_providers():
    """Lista todos os providers de IA disponíveis"""
    return {
        "providers": ai_registry.get_provider_info(),
        "default": ai_registry.default_provider
    }


@app.post("/api/providers")
async def add_provider(config: ProviderConfig):
    """Adiciona um novo provider de IA"""
    try:
        if config.provider_type == "openai":
            provider = OpenAIProvider(
                api_key=config.api_key or os.getenv("OPENAI_API_KEY"),
                model=config.model
            )
        elif config.provider_type == "anthropic":
            provider = AnthropicProvider(
                api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"),
                model=config.model
            )
        elif config.provider_type == "ollama":
            provider = LocalLLMProvider(
                base_url=config.base_url or "http://localhost:11434",
                model=config.model
            )
        else:
            raise HTTPException(400, f"Tipo de provider não suportado: {config.provider_type}")
        
        ai_registry.register(config.name, provider)
        return {"success": True, "name": config.name}
    
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/providers/{name}/stats")
async def get_provider_stats(name: str):
    """Retorna estatísticas de uso de um provider"""
    if name not in ai_registry.list_providers():
        raise HTTPException(404, f"Provider '{name}' não encontrado")
    
    provider = ai_registry.get(name)
    return storage.get_estatisticas_ia(provider.get_identifier())


# ============== ENDPOINTS: ARQUIVOS ==============

@app.get("/api/files")
async def list_files(
    tipo: Optional[str] = None,
    materia: Optional[str] = None
):
    """Lista arquivos no sistema"""
    doc_type = DocumentType(tipo) if tipo else None
    return {
        "documentos": storage.list_documentos(doc_type, materia),
        "materias": storage.list_materias()
    }


@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    tipo: str = Form(...),
    materia: str = Form(...)
):
    """Upload de arquivo (prova, gabarito, etc.)"""
    try:
        # Salvar arquivo temporário
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Registrar no storage
        doc_type = DocumentType(tipo)
        doc_id = storage.save_document(
            str(temp_path),
            doc_type,
            materia,
            processado_por="upload_manual"
        )
        
        # Limpar temp
        temp_path.unlink()
        
        return {
            "success": True,
            "documento_id": doc_id,
            "filename": file.filename,
            "tipo": tipo,
            "materia": materia
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/files/{doc_id}")
async def get_file(doc_id: str):
    """Retorna detalhes de um documento"""
    doc = storage.get_documento(doc_id)
    if not doc:
        raise HTTPException(404, "Documento não encontrado")
    
    questoes = storage.get_questoes_documento(doc_id)
    
    return {
        "documento": doc,
        "questoes": [
            {
                "id": q.id,
                "numero": q.numero,
                "enunciado": q.enunciado[:200] + "..." if len(q.enunciado) > 200 else q.enunciado,
                "itens_count": len(q.itens),
                "pontuacao": q.pontuacao_maxima,
                "habilidades": q.habilidades
            }
            for q in questoes
        ]
    }


@app.delete("/api/files/{doc_id}")
async def delete_file(doc_id: str):
    """Remove um documento"""
    doc = storage.get_documento(doc_id)
    if not doc:
        raise HTTPException(404, "Documento não encontrado")
    
    # Remover arquivo físico
    try:
        Path(doc["arquivo_original"]).unlink()
    except:
        pass
    
    # TODO: Remover do banco (implementar no storage)
    return {"success": True, "deleted": doc_id}


@app.get("/api/files/tree")
async def get_file_tree():
    """Retorna estrutura de diretórios para visualização"""
    tree = {}
    
    for materia in storage.list_materias():
        tree[materia] = {
            "provas": [],
            "resolucoes": [],
            "alunos": [],
            "correcoes": []
        }
        
        for doc in storage.list_documentos(materia=materia):
            tipo_map = {
                "prova_original": "provas",
                "resolucao": "resolucoes", 
                "prova_aluno": "alunos",
                "correcao": "correcoes"
            }
            categoria = tipo_map.get(doc["tipo"], "outros")
            if categoria in tree[materia]:
                tree[materia][categoria].append({
                    "id": doc["id"],
                    "arquivo": Path(doc["arquivo_original"]).name,
                    "processado_por": doc["processado_por"],
                    "timestamp": doc["timestamp"]
                })
    
    return tree


# ============== ENDPOINTS: BUSCA ==============

@app.post("/api/search")
async def search_questions(request: SearchRequest):
    """Busca semântica em questões indexadas"""
    try:
        results = await vector_store.search_similar(
            request.query,
            top_k=request.top_k,
            materia=request.materia
        )
        
        return {
            "query": request.query,
            "results": [
                {
                    "questao_id": r[0],
                    "similarity": round(r[1], 4),
                    "texto": r[2]["texto"][:300],
                    "materia": r[2]["materia"]
                }
                for r in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


# ============== ENDPOINTS: PIPELINE ==============

@app.post("/api/pipeline/extract-gabarito")
async def extract_gabarito(
    file: UploadFile = File(...),
    materia: str = Form(...),
    provider: Optional[str] = Form(None)
):
    """Extrai questões de um gabarito/prova original"""
    try:
        # Salvar arquivo
        temp_path = Path(f"/tmp/{file.filename}")
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Configurar pipeline
        config = PipelineConfig()
        if provider:
            config.set_provider(PipelineStage.EXTRACT_GABARITO, provider)
        
        pipeline = CorrectionPipeline(config)
        result = await pipeline.extract_questoes_gabarito(str(temp_path), materia)
        
        temp_path.unlink()
        
        if not result.success:
            raise HTTPException(400, result.error)
        
        return {
            "success": True,
            "documento_id": result.data["documento_id"],
            "total_questoes": result.data["total"],
            "provider_usado": result.ai_response.provider + "/" + result.ai_response.model,
            "tokens_usados": result.ai_response.tokens_used,
            "tempo_ms": result.duration_ms
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@app.post("/api/pipeline/correct")
async def run_correction(
    background_tasks: BackgroundTasks,
    gabarito_file: UploadFile = File(...),
    aluno_file: UploadFile = File(...),
    materia: str = Form(...),
    aluno_id: str = Form(...),
    aluno_nome: str = Form(...)
):
    """Executa pipeline completo de correção"""
    try:
        # Salvar arquivos
        gabarito_path = Path(f"/tmp/gabarito_{gabarito_file.filename}")
        aluno_path = Path(f"/tmp/aluno_{aluno_file.filename}")
        
        with open(gabarito_path, "wb") as f:
            f.write(await gabarito_file.read())
        with open(aluno_path, "wb") as f:
            f.write(await aluno_file.read())
        
        # Executar pipeline
        pipeline = CorrectionPipeline()
        results = await pipeline.run_full_pipeline(
            str(gabarito_path),
            str(aluno_path),
            materia,
            aluno_id,
            aluno_nome
        )
        
        # Limpar
        gabarito_path.unlink()
        aluno_path.unlink()
        
        return results
    
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/pipeline/results/{prova_id}")
async def get_correction_results(prova_id: str):
    """Retorna resultados de correção de uma prova"""
    correcoes = storage.get_correcoes_aluno(prova_id)
    
    if not correcoes:
        raise HTTPException(404, "Correções não encontradas")
    
    return {
        "prova_id": prova_id,
        "total_questoes": len(correcoes),
        "nota_total": sum(c.nota for c in correcoes),
        "nota_maxima": sum(c.nota_maxima for c in correcoes),
        "correcoes": [
            {
                "questao_id": c.questao_id,
                "item_id": c.item_id,
                "nota": c.nota,
                "nota_maxima": c.nota_maxima,
                "feedback": c.feedback,
                "erros": c.erros_identificados,
                "habilidades_ok": c.habilidades_demonstradas,
                "habilidades_faltantes": c.habilidades_faltantes,
                "confianca": c.confianca,
                "corrigido_por": c.corrigido_por
            }
            for c in correcoes
        ]
    }


# ============== ENDPOINTS: CHAT ==============

@app.post("/api/chat")
async def chat_with_ai(request: ChatRequest):
    """Chat interativo com a IA, com acesso aos documentos"""
    try:
        provider = ai_registry.get(request.provider)
        
        # Montar contexto se documentos especificados
        context = ""
        if request.context_docs:
            for doc_id in request.context_docs:
                doc = storage.get_documento(doc_id)
                if doc:
                    questoes = storage.get_questoes_documento(doc_id)
                    context += f"\n--- Documento: {doc['arquivo_original']} ---\n"
                    for q in questoes:
                        context += f"Questão {q.numero}: {q.enunciado[:500]}\n"
        
        # Montar mensagens
        system_prompt = """Você é um assistente especializado em análise e correção de provas.
        
Você tem acesso a documentos de provas, gabaritos e correções que foram processados.
Ajude o professor a entender os resultados, fazer ajustes, ou realizar análises adicionais.

Se precisar de informações específicas de algum documento, peça ao usuário para 
especificar qual documento deseja consultar."""

        if context:
            system_prompt += f"\n\nContexto dos documentos selecionados:\n{context}"
        
        # Última mensagem do usuário
        last_message = request.messages[-1].content if request.messages else ""
        
        response = await provider.complete(last_message, system_prompt)
        
        return {
            "response": response.content,
            "provider": response.provider,
            "model": response.model,
            "tokens_used": response.tokens_used,
            "latency_ms": response.latency_ms
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


# ============== ENDPOINTS: EXPERIMENTOS ==============

@app.post("/api/experiments/compare")
async def compare_providers(
    file: UploadFile = File(...),
    materia: str = Form(...),
    providers: str = Form(...)  # Lista separada por vírgula
):
    """Compara resultados de diferentes providers na mesma tarefa"""
    provider_list = [p.strip() for p in providers.split(",")]
    
    # Salvar arquivo
    temp_path = Path(f"/tmp/{file.filename}")
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    results = {}
    
    for provider_name in provider_list:
        try:
            config = PipelineConfig()
            config.set_provider(PipelineStage.EXTRACT_GABARITO, provider_name)
            
            pipeline = CorrectionPipeline(config)
            result = await pipeline.extract_questoes_gabarito(str(temp_path), materia)
            
            results[provider_name] = {
                "success": result.success,
                "questoes_encontradas": result.data.get("total", 0) if result.success else 0,
                "tokens_usados": result.ai_response.tokens_used if result.ai_response else 0,
                "tempo_ms": result.duration_ms,
                "erro": result.error
            }
        except Exception as e:
            results[provider_name] = {
                "success": False,
                "erro": str(e)
            }
    
    temp_path.unlink()
    
    return {
        "arquivo": file.filename,
        "materia": materia,
        "comparacao": results
    }


# ============== FRONTEND ==============

@app.get("/")
async def serve_frontend():
    """Serve a página principal"""
    frontend_file = FRONTEND_PATH / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "Frontend não encontrado. Use /api para acessar a API."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
