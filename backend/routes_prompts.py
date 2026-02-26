"""
PROVA AI - Rotas de Prompts e Processamento

Endpoints para:
- Gerenciar prompts (CRUD)
- Executar etapas individuais do pipeline
- Visualizar resultados

ATUALIZADO: Integrado com chat_service.py (novo sistema de models/providers)
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import json

from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage import storage
from models import TipoDocumento, Documento
from routes_tasks import register_pipeline_task, complete_pipeline_task

# Importar novo sistema de chat/models
try:
    from chat_service import (
        chat_service, model_manager, api_key_manager,
        ModelConfig, ProviderType
    )
    HAS_NEW_CHAT = True
except ImportError:
    HAS_NEW_CHAT = False


router = APIRouter()


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class PromptCreate(BaseModel):
    nome: str
    etapa: str  # Valor do enum
    texto: str
    texto_sistema: Optional[str] = None
    descricao: Optional[str] = None
    materia_id: Optional[str] = None
    variaveis: Optional[List[str]] = None

class PromptUpdate(BaseModel):
    nome: Optional[str] = None
    texto: Optional[str] = None
    texto_sistema: Optional[str] = None
    descricao: Optional[str] = None

class PromptRender(BaseModel):
    prompt_id: str
    variaveis: Dict[str, str]

class ProcessarEtapaRequest(BaseModel):
    etapa: str
    atividade_id: str
    aluno_id: Optional[str] = None
    prompt_id: Optional[str] = None  # Se não fornecido, usa o padrão
    prompt_customizado: Optional[str] = None  # Texto do prompt customizado (override)
    model_id: Optional[str] = None   # NOVO: ID do modelo a usar
    provider: Optional[str] = None   # Legado: nome do provider
    
class ProcessarEtapaSimples(BaseModel):
    """Para processar com entrada manual (sem documentos)"""
    etapa: str
    prompt_id: Optional[str] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    entrada: Dict[str, str]  # Variáveis do prompt


# ============================================================
# ENDPOINTS: PROMPTS CRUD
# ============================================================

@router.get("/api/prompts", tags=["Prompts"])
@router.get("/prompts", tags=["Prompts"], include_in_schema=False)
async def listar_prompts(
    etapa: Optional[str] = None,
    materia_id: Optional[str] = None,
    apenas_ativos: bool = True
):
    """Lista todos os prompts com filtros opcionais"""
    etapa_enum = EtapaProcessamento(etapa) if etapa else None
    prompts = prompt_manager.listar_prompts(etapa_enum, materia_id, apenas_ativos)
    
    return {
        "prompts": [p.to_dict() for p in prompts],
        "total": len(prompts)
    }


@router.get("/api/prompts/etapas", tags=["Prompts"])
@router.get("/api/etapas", tags=["Prompts"], include_in_schema=False)
@router.get("/prompts/etapas", tags=["Prompts"], include_in_schema=False)
@router.get("/etapas", tags=["Prompts"], include_in_schema=False)
async def listar_etapas():
    """Lista todas as etapas disponíveis"""
    return {
        "etapas": [
            {
                "id": e.value,
                "nome": e.value.replace("_", " ").title(),
                "descricao": _get_descricao_etapa(e)
            }
            for e in EtapaProcessamento
        ]
    }


def _get_descricao_etapa(etapa: EtapaProcessamento) -> str:
    descricoes = {
        EtapaProcessamento.EXTRAIR_QUESTOES: "Extrai questões do enunciado da prova",
        EtapaProcessamento.EXTRAIR_GABARITO: "Extrai respostas corretas do gabarito",
        EtapaProcessamento.EXTRAIR_RESPOSTAS: "Extrai respostas da prova do aluno",
        EtapaProcessamento.CORRIGIR: "Corrige as respostas comparando com o gabarito",
        EtapaProcessamento.ANALISAR_HABILIDADES: "Analisa habilidades demonstradas pelo aluno",
        EtapaProcessamento.GERAR_RELATORIO: "Gera relatório final de desempenho",
        EtapaProcessamento.CHAT_GERAL: "Chat geral sobre os documentos"
    }
    return descricoes.get(etapa, "")


@router.get("/api/prompts/{prompt_id}", tags=["Prompts"])
async def get_prompt(prompt_id: str):
    """Busca um prompt específico"""
    prompt = prompt_manager.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt não encontrado")
    
    historico = prompt_manager.get_historico(prompt_id)
    
    return {
        "prompt": prompt.to_dict(),
        "historico": historico
    }


@router.post("/api/prompts", tags=["Prompts"])
async def criar_prompt(data: PromptCreate):
    """Cria um novo prompt"""
    try:
        etapa = EtapaProcessamento(data.etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {data.etapa}")
    
    prompt = prompt_manager.criar_prompt(
        nome=data.nome,
        etapa=etapa,
        texto=data.texto,
        texto_sistema=data.texto_sistema,
        descricao=data.descricao,
        materia_id=data.materia_id,
        variaveis=data.variaveis
    )
    
    return {"success": True, "prompt": prompt.to_dict()}


@router.put("/api/prompts/{prompt_id}", tags=["Prompts"])
async def atualizar_prompt(prompt_id: str, data: PromptUpdate):
    """Atualiza um prompt existente"""
    prompt = prompt_manager.atualizar_prompt(
        prompt_id=prompt_id,
        texto=data.texto,
        nome=data.nome,
        texto_sistema=data.texto_sistema,
        descricao=data.descricao
    )
    
    if not prompt:
        raise HTTPException(404, "Prompt não encontrado")
    
    return {"success": True, "prompt": prompt.to_dict()}


@router.delete("/api/prompts/{prompt_id}", tags=["Prompts"])
async def deletar_prompt(prompt_id: str):
    """Deleta um prompt (soft delete)"""
    success = prompt_manager.deletar_prompt(prompt_id)
    if not success:
        raise HTTPException(400, "Não foi possível deletar. Prompts padrão não podem ser deletados.")
    
    return {"success": True}


@router.post("/api/prompts/{prompt_id}/duplicar", tags=["Prompts"])
async def duplicar_prompt(prompt_id: str, novo_nome: str = Form(...), materia_id: Optional[str] = Form(None)):
    """Duplica um prompt"""
    prompt = prompt_manager.duplicar_prompt(prompt_id, novo_nome, materia_id)
    if not prompt:
        raise HTTPException(404, "Prompt original não encontrado")
    
    return {"success": True, "prompt": prompt.to_dict()}


@router.post("/api/prompts/{prompt_id}/definir-padrao", tags=["Prompts"])
async def definir_padrao(prompt_id: str, materia_id: Optional[str] = Form(None)):
    """Define um prompt como padrão para sua etapa"""
    prompt = prompt_manager.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt não encontrado")
    
    prompt_manager.definir_padrao(prompt_id, prompt.etapa, materia_id)
    
    return {"success": True, "mensagem": f"Prompt definido como padrão para {prompt.etapa.value}"}


@router.post("/api/prompts/render", tags=["Prompts"])
async def renderizar_prompt(data: PromptRender):
    """Renderiza um prompt com as variáveis fornecidas (preview)"""
    prompt = prompt_manager.get_prompt(data.prompt_id)
    if not prompt:
        raise HTTPException(404, "Prompt não encontrado")
    
    texto_renderizado = prompt.render(**data.variaveis)
    texto_sistema_renderizado = prompt.render_sistema(**data.variaveis)
    
    return {
        "prompt_id": data.prompt_id,
        "texto_original": prompt.texto,
        "texto_renderizado": texto_renderizado,
        "texto_sistema_original": prompt.texto_sistema,
        "texto_sistema_renderizado": texto_sistema_renderizado,
        "variaveis_usadas": data.variaveis
    }


# ============================================================
# ENDPOINTS: PROCESSAMENTO
# ============================================================

@router.get("/api/processamento/status/{atividade_id}", tags=["Processamento"])
async def status_processamento(atividade_id: str, aluno_id: Optional[str] = None):
    """
    Retorna status de processamento de uma atividade.
    Mostra o que já foi gerado e o que falta.
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    
    documentos = storage.listar_documentos(atividade_id, aluno_id)
    
    # Mapear tipos de documentos presentes
    tipos_presentes = {d.tipo for d in documentos}
    
    # Definir etapas e documentos requeridos
    etapas_status = []
    
    etapas_config = [
        {
            "etapa": EtapaProcessamento.EXTRAIR_QUESTOES,
            "requer": [TipoDocumento.ENUNCIADO],
            "gera": TipoDocumento.EXTRACAO_QUESTOES
        },
        {
            "etapa": EtapaProcessamento.EXTRAIR_GABARITO,
            "requer": [TipoDocumento.GABARITO, TipoDocumento.EXTRACAO_QUESTOES],
            "gera": TipoDocumento.EXTRACAO_GABARITO
        },
        {
            "etapa": EtapaProcessamento.EXTRAIR_RESPOSTAS,
            "requer": [TipoDocumento.PROVA_RESPONDIDA, TipoDocumento.EXTRACAO_QUESTOES],
            "gera": TipoDocumento.EXTRACAO_RESPOSTAS
        },
        {
            "etapa": EtapaProcessamento.CORRIGIR,
            "requer": [TipoDocumento.EXTRACAO_RESPOSTAS, TipoDocumento.EXTRACAO_GABARITO],
            "gera": TipoDocumento.CORRECAO
        },
        {
            "etapa": EtapaProcessamento.ANALISAR_HABILIDADES,
            "requer": [TipoDocumento.CORRECAO],
            "gera": TipoDocumento.ANALISE_HABILIDADES
        },
        {
            "etapa": EtapaProcessamento.GERAR_RELATORIO,
            "requer": [TipoDocumento.CORRECAO, TipoDocumento.ANALISE_HABILIDADES],
            "gera": TipoDocumento.RELATORIO_FINAL
        }
    ]
    
    for cfg in etapas_config:
        faltando = [r for r in cfg["requer"] if r not in tipos_presentes]
        concluida = cfg["gera"] in tipos_presentes
        pode_executar = len(faltando) == 0 and not concluida
        
        etapas_status.append({
            "etapa": cfg["etapa"].value,
            "nome": cfg["etapa"].value.replace("_", " ").title(),
            "concluida": concluida,
            "pode_executar": pode_executar,
            "documentos_faltando": [f.value for f in faltando],
            "documento_gerado": cfg["gera"].value
        })
    
    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "documentos": [{"id": d.id, "tipo": d.tipo.value, "nome": d.nome_arquivo} for d in documentos],
        "etapas": etapas_status
    }


@router.get("/api/processamento/preparar/{etapa}", tags=["Processamento"])
async def preparar_etapa(etapa: str, atividade_id: str, aluno_id: Optional[str] = None):
    """
    Prepara execução de uma etapa: retorna prompt, variáveis disponíveis, etc.
    """
    try:
        etapa_enum = EtapaProcessamento(etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {etapa}")
    
    # Buscar prompt padrão
    prompt = prompt_manager.get_prompt_padrao(etapa_enum)
    if not prompt:
        raise HTTPException(404, f"Nenhum prompt padrão para etapa {etapa}")
    
    # Carregar documentos disponíveis
    documentos = storage.listar_documentos(atividade_id, aluno_id)
    
    # Preparar variáveis disponíveis
    variaveis_disponiveis = {}
    
    for doc in documentos:
        # Ler conteúdo do documento
        conteudo = _ler_conteudo_documento(doc)
        
        # Mapear para variáveis
        if doc.tipo == TipoDocumento.ENUNCIADO:
            variaveis_disponiveis["conteudo_documento"] = conteudo
        elif doc.tipo == TipoDocumento.GABARITO:
            variaveis_disponiveis["conteudo_documento"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_QUESTOES:
            variaveis_disponiveis["questoes_extraidas"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_GABARITO:
            variaveis_disponiveis["gabarito_extraido"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS:
            variaveis_disponiveis["respostas_extraidas"] = conteudo
        elif doc.tipo == TipoDocumento.CORRECAO:
            variaveis_disponiveis["correcao"] = conteudo
        elif doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
            variaveis_disponiveis["prova_aluno"] = conteudo
    
    # Info da atividade
    atividade = storage.get_atividade(atividade_id)
    if atividade:
        turma = storage.get_turma(atividade.turma_id)
        materia = storage.get_materia(turma.materia_id) if turma else None
        variaveis_disponiveis["materia"] = materia.nome if materia else "Não definida"
        variaveis_disponiveis["atividade"] = atividade.nome
    
    # Info do aluno
    if aluno_id:
        aluno = storage.get_aluno(aluno_id)
        if aluno:
            variaveis_disponiveis["nome_aluno"] = aluno.nome
    
    # Modelos disponíveis (novo sistema)
    modelos_disponiveis = []
    if HAS_NEW_CHAT:
        modelos = model_manager.listar()
        modelos_disponiveis = [{"id": m.id, "nome": m.nome, "is_default": m.is_default} for m in modelos]
    
    return {
        "etapa": etapa,
        "prompt": prompt.to_dict(),
        "variaveis_requeridas": prompt.variaveis,
        "variaveis_disponiveis": variaveis_disponiveis,
        "documentos_encontrados": [{"id": d.id, "tipo": d.tipo.value, "nome": d.nome_arquivo} for d in documentos],
        "modelos_disponiveis": modelos_disponiveis
    }


def _ler_conteudo_documento(doc) -> str:
    """Lê conteúdo de um documento"""
    try:
        arquivo = Path(doc.caminho_arquivo)
        if not arquivo.exists():
            return f"[Arquivo não encontrado: {doc.nome_arquivo}]"
        
        if doc.extensao.lower() == '.json':
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, ensure_ascii=False, indent=2)
        elif doc.extensao.lower() in ['.txt', '.md']:
            with open(arquivo, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            return f"[Arquivo: {doc.nome_arquivo}]"
    except Exception as e:
        return f"[Erro ao ler: {e}]"


@router.get("/api/documentos/{documento_id}/conteudo", tags=["Documentos"])
async def get_conteudo_documento(documento_id: str):
    """
    [LEGACY - CONSIDER UNIFICATION] Retorna o conteúdo de um documento.
    Para JSONs, retorna parseado. Para outros, retorna texto ou info do arquivo.

    ⚠️  UNIFICATION CANDIDATE: Multiple document access endpoints exist.
    See routes_pipeline.py /api/documentos/{id}/download for full details.

    POTENTIAL ERRORS from unification:
    - This returns JSON content, others return FileResponse
    - Different error handling for unsupported file types
    - JSON parsing errors not handled in other endpoints
    """
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    arquivo = storage.resolver_caminho_documento(documento)

    if not arquivo.exists():
        # File doesn't exist - return info about the missing file
        return {
            "documento": documento.to_dict(),
            "tipo_conteudo": "arquivo_inexistente",
            "conteudo": None,
            "erro": "Arquivo não encontrado no sistema de arquivos",
            "pode_visualizar": False,
            "caminho_esperado": str(arquivo)
        }
    
    conteudo = None
    tipo_conteudo = "arquivo"
    
    # Tentar ler baseado na extensão
    if documento.extensao.lower() == '.json':
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
            tipo_conteudo = "json"
        except Exception as e:
            return {
                "documento": documento.to_dict(),
                "tipo_conteudo": "erro_json",
                "conteudo": None,
                "erro": f"Erro ao ler JSON: {str(e)}",
                "pode_visualizar": False
            }
    elif documento.extensao.lower() in ['.txt', '.md']:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            tipo_conteudo = "texto"
        except Exception as e:
            return {
                "documento": documento.to_dict(),
                "tipo_conteudo": "erro_texto",
                "conteudo": None,
                "erro": f"Erro ao ler texto: {str(e)}",
                "pode_visualizar": False
            }
    
    return {
        "documento": documento.to_dict(),
        "tipo_conteudo": tipo_conteudo,
        "conteudo": conteudo,
        "pode_visualizar": tipo_conteudo in ["json", "texto"]
    }


# ============================================================
# ENDPOINTS: PROVIDERS/MODELS
# ============================================================

@router.get("/api/providers/disponiveis", tags=["Providers"])
async def listar_providers_disponiveis():
    """Lista providers de IA disponíveis para processamento"""
    
    # Novo sistema (chat_service)
    if HAS_NEW_CHAT:
        modelos = model_manager.listar()
        default_model = model_manager.get_default()
        
        return {
            "providers": [
                {
                    "id": m.id,
                    "nome": m.nome,
                    "tipo": m.tipo.value,
                    "modelo": m.modelo,
                    "is_default": m.is_default
                }
                for m in modelos
            ],
            "default": default_model.id if default_model else None,
            "sistema": "chat_service"
        }
    
    # Fallback para sistema antigo
    try:
        from ai_providers import ai_registry
        providers = ai_registry.get_provider_info()
        return {
            "providers": providers,
            "default": ai_registry.default_provider,
            "sistema": "ai_providers"
        }
    except ImportError:
        return {
            "providers": [],
            "default": None,
            "sistema": "none",
            "erro": "Nenhum sistema de IA configurado"
        }


# ============================================================
# ENDPOINTS: EXECUÇÃO DE ETAPAS
# ============================================================

@router.post("/api/executar/etapa", tags=["Execução"])
async def executar_etapa(data: ProcessarEtapaRequest):
    """
    [LEGACY - CONSIDER UNIFICATION] Executa uma etapa específica do pipeline.

    Usa o novo sistema de chat se disponível, senão fallback para executor antigo.
    Suporta prompt_customizado para override do texto do prompt.

    ⚠️  UNIFICATION CANDIDATE: See /api/pipeline/executar in routes_pipeline.py for details
    """
    try:
        etapa = EtapaProcessamento(data.etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {data.etapa}")

    # Usar novo sistema de chat
    if HAS_NEW_CHAT and data.model_id:
        return await _executar_com_chat_service(
            etapa=etapa,
            atividade_id=data.atividade_id,
            aluno_id=data.aluno_id,
            prompt_id=data.prompt_id,
            prompt_customizado=data.prompt_customizado,
            model_id=data.model_id,
            salvar=True
        )

    # Fallback para executor antigo
    from executor import executor

    resultado = await executor.executar_etapa(
        etapa=etapa,
        atividade_id=data.atividade_id,
        aluno_id=data.aluno_id,
        prompt_id=data.prompt_id,
        prompt_customizado=data.prompt_customizado,
        provider_name=data.provider,
        salvar_resultado=True
    )

    return {
        "sucesso": resultado.sucesso,
        "resultado": resultado.to_dict()
    }


@router.post("/api/executar/etapa-preview", tags=["Execução"])
async def executar_etapa_preview(data: ProcessarEtapaRequest):
    """
    Executa uma etapa SEM salvar o resultado.
    Útil para testar prompts e ver a resposta antes de confirmar.
    """
    try:
        etapa = EtapaProcessamento(data.etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {data.etapa}")

    # Usar novo sistema de chat
    if HAS_NEW_CHAT and data.model_id:
        return await _executar_com_chat_service(
            etapa=etapa,
            atividade_id=data.atividade_id,
            aluno_id=data.aluno_id,
            prompt_id=data.prompt_id,
            prompt_customizado=data.prompt_customizado,
            model_id=data.model_id,
            salvar=False
        )

    # Fallback
    from executor import executor

    resultado = await executor.executar_etapa(
        etapa=etapa,
        atividade_id=data.atividade_id,
        aluno_id=data.aluno_id,
        prompt_id=data.prompt_id,
        prompt_customizado=data.prompt_customizado,
        provider_name=data.provider,
        salvar_resultado=False
    )

    return {
        "sucesso": resultado.sucesso,
        "preview": True,
        "resultado": resultado.to_dict()
    }


async def _executar_com_chat_service(
    etapa: EtapaProcessamento,
    atividade_id: str,
    aluno_id: Optional[str],
    prompt_id: Optional[str],
    model_id: str,
    salvar: bool,
    prompt_customizado: Optional[str] = None
) -> Dict[str, Any]:
    """Executa etapa usando o novo chat_service"""

    # Buscar prompt
    if prompt_id:
        prompt = prompt_manager.get_prompt(prompt_id)
    else:
        prompt = prompt_manager.get_prompt_padrao(etapa)

    if not prompt and not prompt_customizado:
        raise HTTPException(404, f"Nenhum prompt encontrado para etapa {etapa.value}")

    # Carregar variáveis
    documentos = storage.listar_documentos(atividade_id, aluno_id)
    variaveis = {}

    for doc in documentos:
        conteudo = _ler_conteudo_documento(doc)

        if doc.tipo == TipoDocumento.ENUNCIADO:
            variaveis["conteudo_documento"] = conteudo
        elif doc.tipo == TipoDocumento.GABARITO:
            variaveis["conteudo_documento"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_QUESTOES:
            variaveis["questoes_extraidas"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_GABARITO:
            variaveis["gabarito_extraido"] = conteudo
        elif doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS:
            variaveis["respostas_extraidas"] = conteudo
        elif doc.tipo == TipoDocumento.CORRECAO:
            variaveis["correcao"] = conteudo
        elif doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
            variaveis["prova_aluno"] = conteudo

    # Info contextual
    atividade = storage.get_atividade(atividade_id)
    if atividade:
        turma = storage.get_turma(atividade.turma_id)
        materia = storage.get_materia(turma.materia_id) if turma else None
        variaveis["materia"] = materia.nome if materia else "Não definida"
        variaveis["atividade"] = atividade.nome

    if aluno_id:
        aluno = storage.get_aluno(aluno_id)
        if aluno:
            variaveis["nome_aluno"] = aluno.nome

    # Renderizar prompt (usa customizado se fornecido)
    if prompt_customizado:
        # Substituir variáveis no texto customizado
        texto_renderizado = prompt_customizado
        for key, value in variaveis.items():
            texto_renderizado = texto_renderizado.replace(f"{{{key}}}", str(value))
        texto_sistema = prompt.render_sistema(**variaveis) if prompt and prompt.texto_sistema else None
    else:
        texto_renderizado = prompt.render(**variaveis)
    texto_sistema = prompt.render_sistema(**variaveis) if prompt.texto_sistema else None
    
    # Criar sessão de chat
    sessao = chat_service.criar_sessao(
        titulo=f"Pipeline: {etapa.value}",
        model_id=model_id,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        etapa_pipeline=etapa.value
    )
    
    try:
        # Enviar para IA
        resposta = await chat_service.enviar_mensagem(
            session_id=sessao.id,
            mensagem=texto_renderizado,
            model_id=model_id,
            system_prompt=texto_sistema,
            incluir_contexto_docs=False  # Já incluímos no prompt
        )
        
        return {
            "sucesso": True,
            "preview": not salvar,
            "resultado": {
                "session_id": sessao.id,
                "etapa": etapa.value,
                "resposta": resposta.content,
                "modelo": resposta.modelo,
                "provider": resposta.provider,
                "tokens": resposta.tokens,
                "arquivos_gerados": resposta.arquivos_gerados
            }
        }
        
    except Exception as e:
        return {
            "sucesso": False,
            "erro": str(e),
            "resultado": None
        }


@router.post("/api/executar/pipeline-completo", tags=["Execução"])
async def executar_pipeline_completo(
    background_tasks: BackgroundTasks,
    atividade_id: str = Form(...),
    aluno_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    providers: Optional[str] = Form(None),
    prompt_id: Optional[str] = Form(None),
    prompts_per_stage: Optional[str] = Form(None),
    selected_steps: Optional[str] = Form(None),
    force_rerun: bool = Form(False)
):
    """
    [LEGACY - CONSIDER UNIFICATION] Executa o pipeline completo para um aluno.
    Registra a tarefa em task_registry e inicia execução como BackgroundTask.
    Retorna task_id imediatamente para polling via /api/task-progress/{task_id}.

    ⚠️  UNIFICATION CANDIDATE: See /api/pipeline/executar in routes_pipeline.py for details
    """
    from executor import executor

    providers_map = None
    if providers:
        try:
            providers_map = json.loads(providers)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para providers. Use JSON.")

    prompts_map = None
    if prompts_per_stage:
        try:
            prompts_map = json.loads(prompts_per_stage)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para prompts_per_stage. Use JSON.")

    steps_list = None
    if selected_steps:
        try:
            steps_list = json.loads(selected_steps)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para selected_steps. Use JSON array.")

    # Register the task in task_registry synchronously so the task_id
    # exists before the response is returned and polling can start immediately.
    task_id = register_pipeline_task(
        task_type="pipeline",
        atividade_id=atividade_id,
        aluno_ids=[aluno_id],
    )

    # Run pipeline execution in the background — endpoint returns task_id immediately.
    background_tasks.add_task(
        executor.executar_pipeline_completo,
        task_id=task_id,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        model_id=model_id,
        provider_name=provider,
        providers_map=providers_map,
        prompt_id=prompt_id,
        prompts_map=prompts_map,
        selected_steps=steps_list,
        force_rerun=force_rerun,
    )

    return {"task_id": task_id, "status": "started"}


@router.get("/api/executar/status-etapas/{atividade_id}/{aluno_id}", tags=["Execução"])
async def status_etapas_pipeline(atividade_id: str, aluno_id: str):
    """
    Retorna o status de cada etapa do pipeline para um aluno.
    Mostra quais etapas já foram executadas, por qual modelo, e quantas versões existem.
    """
    from models import TipoDocumento
    
    # Mapear etapas para tipos de documento
    etapa_tipo_map = {
        "extrair_questoes": TipoDocumento.EXTRACAO_QUESTOES,
        "extrair_gabarito": TipoDocumento.EXTRACAO_GABARITO,
        "extrair_respostas": TipoDocumento.EXTRACAO_RESPOSTAS,
        "corrigir": TipoDocumento.CORRECAO,
        "analisar_habilidades": TipoDocumento.ANALISE_HABILIDADES,
        "gerar_relatorio": TipoDocumento.RELATORIO_FINAL
    }
    
    # Etapas de atividade (sem aluno)
    etapas_atividade = ["extrair_questoes", "extrair_gabarito"]
    
    # Buscar documentos
    docs_base = storage.listar_documentos(atividade_id)
    docs_aluno = storage.listar_documentos(atividade_id, aluno_id)
    
    status = {}
    for etapa_nome, tipo_doc in etapa_tipo_map.items():
        # Escolher lista de docs correta
        docs_list = docs_base if etapa_nome in etapas_atividade else docs_aluno
        
        # Filtrar por tipo
        docs_etapa = [d for d in docs_list if d.tipo == tipo_doc]
        
        if not docs_etapa:
            status[etapa_nome] = {
                "executada": False,
                "versoes": 0,
                "documentos": []
            }
        else:
            status[etapa_nome] = {
                "executada": True,
                "versoes": len(docs_etapa),
                "documentos": [
                    {
                        "id": d.id,
                        "versao": d.versao,
                        "modelo": d.ia_modelo,
                        "provider": d.ia_provider,
                        "criado_em": d.criado_em.isoformat() if d.criado_em else None
                    }
                    for d in sorted(docs_etapa, key=lambda x: x.versao)
                ]
            }
    
    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "etapas": status
    }


@router.get("/api/documentos/{atividade_id}/{aluno_id}/versoes", tags=["Documentos"])
async def listar_versoes_documentos(
    atividade_id: str, 
    aluno_id: str,
    tipo: Optional[str] = None
):
    """
    Lista todas as versões de documentos para um aluno, agrupadas por tipo.
    Útil para comparar resultados de diferentes modelos.
    """
    from models import TipoDocumento
    
    # Buscar documentos do aluno e da atividade
    docs_base = storage.listar_documentos(atividade_id)
    docs_aluno = storage.listar_documentos(atividade_id, aluno_id)
    
    todos_docs = docs_base + docs_aluno
    
    # Filtrar por tipo se especificado
    if tipo:
        try:
            tipo_enum = TipoDocumento(tipo)
            todos_docs = [d for d in todos_docs if d.tipo == tipo_enum]
        except ValueError:
            pass
    
    # Agrupar por tipo
    por_tipo = {}
    for doc in todos_docs:
        tipo_str = doc.tipo.value
        if tipo_str not in por_tipo:
            por_tipo[tipo_str] = []
        por_tipo[tipo_str].append({
            "id": doc.id,
            "versao": doc.versao,
            "modelo": doc.ia_modelo,
            "provider": doc.ia_provider,
            "nome_arquivo": doc.nome_arquivo,
            "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
            "documento_origem_id": doc.documento_origem_id
        })
    
    # Ordenar por versão dentro de cada tipo
    for tipo_str in por_tipo:
        por_tipo[tipo_str] = sorted(por_tipo[tipo_str], key=lambda x: x["versao"])
    
    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "documentos_por_tipo": por_tipo
    }


@router.post("/api/executar/lote", tags=["Execução"])
async def executar_lote(
    atividade_id: str = Form(...),
    aluno_ids: str = Form(...),  # IDs separados por vírgula
    model_id: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),
    providers: Optional[str] = Form(None)
):
    """
    Executa o pipeline completo para múltiplos alunos.
    """
    from executor import executor
    
    ids = [id.strip() for id in aluno_ids.split(',') if id.strip()]
    
    providers_map = None
    if providers:
        try:
            providers_map = json.loads(providers)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para providers. Use JSON.")
    
    resultados_por_aluno = {}
    for aluno_id in ids:
        aluno = storage.get_aluno(aluno_id)
        nome = aluno.nome if aluno else aluno_id
        
        resultados = await executor.executar_pipeline_completo(
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_name=provider,
            providers_map=providers_map
        )
        
        sucesso = all(r.sucesso for r in resultados.values())
        resultados_por_aluno[aluno_id] = {
            "nome": nome,
            "sucesso": sucesso,
            "etapas": list(resultados.keys())
        }
    
    return {
        "total_alunos": len(ids),
        "sucesso": sum(1 for r in resultados_por_aluno.values() if r["sucesso"]),
        "falhas": sum(1 for r in resultados_por_aluno.values() if not r["sucesso"]),
        "resultados": resultados_por_aluno
    }


async def _executar_pipeline_todos_os_alunos_background(
    task_id: str,
    alunos_para_processar: list,
    atividade_id: str,
    model_id,
    provider: str,
    providers_map,
    prompt_id,
    prompts_map,
    steps_list,
    force_rerun: bool,
):
    """Background helper: runs pipeline for every student in the turma sequentially."""
    from executor import executor

    for aluno in alunos_para_processar:
        try:
            await executor.executar_pipeline_completo(
                task_id=task_id,
                atividade_id=atividade_id,
                aluno_id=aluno.id,
                model_id=model_id,
                provider_name=provider,
                providers_map=providers_map,
                prompt_id=prompt_id,
                prompts_map=prompts_map,
                selected_steps=steps_list,
                force_rerun=force_rerun,
            )
        except Exception:
            pass  # Individual student failures don't block remaining students


@router.post("/api/executar/pipeline-todos-os-alunos", tags=["Execução"])
async def executar_pipeline_todos_os_alunos(
    background_tasks: BackgroundTasks,
    atividade_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),  # [LEGACY - MARK FOR DELETION] Provider de IA a usar (opcional, legacy)
    providers: Optional[str] = Form(None),
    prompt_id: Optional[str] = Form(None),
    prompts_per_stage: Optional[str] = Form(None),
    selected_steps: Optional[str] = Form(None),
    force_rerun: bool = Form(False),
    apenas_com_prova: bool = Form(True)  # Apenas alunos que têm prova enviada
):
    """
    [LEGACY - CONSIDER UNIFICATION] Executa o pipeline completo para TODOS os alunos de uma turma.
    Registra a tarefa em task_registry e inicia execução como BackgroundTask.
    Retorna task_id imediatamente para polling via /api/task-progress/{task_id}.

    ⚠️  UNIFICATION CANDIDATE: See /api/pipeline/executar in routes_pipeline.py for details
    """
    # Buscar atividade e turma
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")

    # Buscar todos os alunos da turma
    alunos = storage.listar_alunos(atividade.turma_id)
    if not alunos:
        raise HTTPException(400, "Nenhum aluno encontrado na turma")

    # Filtrar apenas alunos com prova enviada, se solicitado
    alunos_para_processar = []
    for aluno in alunos:
        if apenas_com_prova:
            docs_aluno = storage.listar_documentos(atividade_id, aluno.id)
            tem_prova = any(d.tipo == TipoDocumento.PROVA_RESPONDIDA for d in docs_aluno)
            if tem_prova:
                alunos_para_processar.append(aluno)
        else:
            alunos_para_processar.append(aluno)

    if not alunos_para_processar:
        return {
            "sucesso": False,
            "mensagem": "Nenhum aluno com prova enviada para processar",
            "total_alunos": 0,
            "resultados": {}
        }

    providers_map = None
    if providers:
        try:
            providers_map = json.loads(providers)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para providers. Use JSON.")

    prompts_map = None
    if prompts_per_stage:
        try:
            prompts_map = json.loads(prompts_per_stage)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para prompts_per_stage. Use JSON.")

    steps_list = None
    if selected_steps:
        try:
            steps_list = json.loads(selected_steps)
        except json.JSONDecodeError:
            raise HTTPException(400, "Formato inválido para selected_steps. Use JSON array.")

    # Register all students synchronously so task_id exists before response is returned.
    task_id = register_pipeline_task(
        task_type="pipeline_todos_os_alunos",
        atividade_id=atividade_id,
        aluno_ids=[aluno.id for aluno in alunos_para_processar],
    )

    # Run the student loop in the background — endpoint returns task_id immediately.
    background_tasks.add_task(
        _executar_pipeline_todos_os_alunos_background,
        task_id=task_id,
        alunos_para_processar=alunos_para_processar,
        atividade_id=atividade_id,
        model_id=model_id,
        provider=provider,
        providers_map=providers_map,
        prompt_id=prompt_id,
        prompts_map=prompts_map,
        steps_list=steps_list,
        force_rerun=force_rerun,
    )

    return {"task_id": task_id, "status": "started"}


# ============================================================
# BACKWARD-COMPAT REDIRECT: old pipeline-turma URL → new URL
# ============================================================

@router.post("/api/executar/pipeline-turma", tags=["Execução"], include_in_schema=False)
async def redirect_legacy_pipeline_todos_os_alunos():
    """HTTP 301 redirect: /api/executar/pipeline-turma → /api/executar/pipeline-todos-os-alunos.

    Provides backward compatibility for any existing bookmarks or external integrations
    still calling the old endpoint URL.
    """
    return RedirectResponse(
        url="/api/executar/pipeline-todos-os-alunos",
        status_code=301,
    )


# ============================================================
# RELATÓRIO DE DESEMPENHO — aggregate synthesis endpoints
# ============================================================

@router.post("/api/executar/pipeline-desempenho-tarefa", tags=["Execução"])
async def executar_pipeline_desempenho_tarefa(
    background_tasks: BackgroundTasks,
    atividade_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """
    Gera relatório de desempenho agregado para uma atividade.

    Busca todos os RELATORIO_NARRATIVO dos alunos e sintetiza um relatório
    coletivo questão-a-questão com exemplos concretos de alunos.
    Requer pelo menos 2 alunos com narrativas completas.
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")

    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_tarefa",
        atividade_id=atividade_id,
        aluno_ids=[],
    )

    background_tasks.add_task(
        _executar_desempenho_tarefa_background,
        task_id=task_id,
        atividade_id=atividade_id,
        provider_id=provider_id,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_tarefa_background(
    task_id: str,
    atividade_id: str,
    provider_id: Optional[str],
):
    from executor import executor
    try:
        await executor.gerar_relatorio_desempenho_tarefa(
            atividade_id=atividade_id,
            provider_id=provider_id,
        )
        complete_pipeline_task(task_id, "completed")
    except Exception:
        complete_pipeline_task(task_id, "failed")


@router.post("/api/executar/pipeline-desempenho-turma", tags=["Execução"])
async def executar_pipeline_desempenho_turma(
    background_tasks: BackgroundTasks,
    turma_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """
    Gera relatório de desempenho holístico para uma turma.

    Busca relatórios narrativos de todos os alunos ao longo de todas as
    atividades e sintetiza progressão, problemas persistentes, perfil
    coletivo e evolução individual.
    Requer pelo menos 2 alunos na turma.
    """
    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")

    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_turma",
        atividade_id=turma_id,
        aluno_ids=[],
    )

    background_tasks.add_task(
        _executar_desempenho_turma_background,
        task_id=task_id,
        turma_id=turma_id,
        provider_id=provider_id,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_turma_background(
    task_id: str,
    turma_id: str,
    provider_id: Optional[str],
):
    from executor import executor
    try:
        await executor.gerar_relatorio_desempenho_turma(
            turma_id=turma_id,
            provider_id=provider_id,
        )
        complete_pipeline_task(task_id, "completed")
    except Exception:
        complete_pipeline_task(task_id, "failed")


@router.post("/api/executar/pipeline-desempenho-materia", tags=["Execução"])
async def executar_pipeline_desempenho_materia(
    background_tasks: BackgroundTasks,
    materia_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """
    Gera relatório de desempenho cross-turma para uma matéria.

    Compara o desempenho de todas as turmas da matéria, identificando
    padrões cross-turma e efetividade curricular.
    Requer pelo menos 2 turmas com resultados.
    """
    materia = storage.get_materia(materia_id)
    if not materia:
        raise HTTPException(404, "Matéria não encontrada")

    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_materia",
        atividade_id=materia_id,
        aluno_ids=[],
    )

    background_tasks.add_task(
        _executar_desempenho_materia_background,
        task_id=task_id,
        materia_id=materia_id,
        provider_id=provider_id,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_materia_background(
    task_id: str,
    materia_id: str,
    provider_id: Optional[str],
):
    from executor import executor
    try:
        await executor.gerar_relatorio_desempenho_materia(
            materia_id=materia_id,
            provider_id=provider_id,
        )
        complete_pipeline_task(task_id, "completed")
    except Exception:
        complete_pipeline_task(task_id, "failed")

