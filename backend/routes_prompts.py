"""
PROVA AI - Rotas de Prompts e Processamento

Endpoints para:
- Gerenciar prompts (CRUD)
- Executar etapas individuais do pipeline
- Visualizar resultados
"""

from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage_v2 import storage_v2 as storage
from models import TipoDocumento, Documento


router = APIRouter()


# ============================================================
# MODELOS PYDANTIC
# ============================================================

class PromptCreate(BaseModel):
    nome: str
    etapa: str  # Valor do enum
    texto: str
    descricao: Optional[str] = None
    materia_id: Optional[str] = None
    variaveis: Optional[List[str]] = None

class PromptUpdate(BaseModel):
    nome: Optional[str] = None
    texto: Optional[str] = None
    descricao: Optional[str] = None

class PromptRender(BaseModel):
    prompt_id: str
    variaveis: Dict[str, str]

class ProcessarEtapaRequest(BaseModel):
    etapa: str
    atividade_id: str
    aluno_id: Optional[str] = None
    prompt_id: Optional[str] = None  # Se não fornecido, usa o padrão
    provider: Optional[str] = None   # Se não fornecido, usa o padrão
    
class ProcessarEtapaSimples(BaseModel):
    """Para processar com entrada manual (sem documentos)"""
    etapa: str
    prompt_id: Optional[str] = None
    provider: Optional[str] = None
    entrada: Dict[str, str]  # Variáveis do prompt


# ============================================================
# ENDPOINTS: PROMPTS CRUD
# ============================================================

@router.get("/api/prompts", tags=["Prompts"])
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
    
    return {
        "prompt_id": data.prompt_id,
        "texto_original": prompt.texto,
        "texto_renderizado": texto_renderizado,
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
    tipos_existentes = [d.tipo for d in documentos]
    
    # Documentos base
    docs_base = {
        "enunciado": TipoDocumento.ENUNCIADO in tipos_existentes,
        "gabarito": TipoDocumento.GABARITO in tipos_existentes,
        "criterios": TipoDocumento.CRITERIOS_CORRECAO in tipos_existentes
    }
    
    # Se pediu aluno específico
    docs_aluno = {}
    if aluno_id:
        docs_aluno = {
            "prova_respondida": TipoDocumento.PROVA_RESPONDIDA in tipos_existentes,
            "extracao_respostas": TipoDocumento.EXTRACAO_RESPOSTAS in tipos_existentes,
            "correcao": TipoDocumento.CORRECAO in tipos_existentes,
            "analise_habilidades": TipoDocumento.ANALISE_HABILIDADES in tipos_existentes,
            "relatorio": TipoDocumento.RELATORIO_FINAL in tipos_existentes
        }
    
    # Determinar próximas etapas possíveis
    proximas_etapas = []
    
    if docs_base["enunciado"] and not any(d.tipo == TipoDocumento.EXTRACAO_QUESTOES for d in documentos):
        proximas_etapas.append({
            "etapa": "extrair_questoes",
            "descricao": "Extrair questões do enunciado",
            "pode_executar": True
        })
    
    if docs_base["gabarito"] and not any(d.tipo == TipoDocumento.EXTRACAO_GABARITO for d in documentos):
        proximas_etapas.append({
            "etapa": "extrair_gabarito",
            "descricao": "Extrair respostas do gabarito",
            "pode_executar": True
        })
    
    if aluno_id and docs_aluno.get("prova_respondida") and not docs_aluno.get("extracao_respostas"):
        proximas_etapas.append({
            "etapa": "extrair_respostas",
            "descricao": "Extrair respostas do aluno",
            "pode_executar": True
        })
    
    if aluno_id and docs_aluno.get("extracao_respostas") and docs_base["gabarito"] and not docs_aluno.get("correcao"):
        proximas_etapas.append({
            "etapa": "corrigir",
            "descricao": "Corrigir respostas",
            "pode_executar": True
        })
    
    if aluno_id and docs_aluno.get("correcao") and not docs_aluno.get("analise_habilidades"):
        proximas_etapas.append({
            "etapa": "analisar_habilidades",
            "descricao": "Analisar habilidades",
            "pode_executar": True
        })
    
    if aluno_id and docs_aluno.get("correcao") and not docs_aluno.get("relatorio"):
        proximas_etapas.append({
            "etapa": "gerar_relatorio",
            "descricao": "Gerar relatório final",
            "pode_executar": True
        })
    
    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "documentos_base": docs_base,
        "documentos_aluno": docs_aluno,
        "documentos": [d.to_dict() for d in documentos],
        "proximas_etapas": proximas_etapas
    }


@router.get("/api/processamento/preparar/{etapa}", tags=["Processamento"])
async def preparar_etapa(
    etapa: str,
    atividade_id: str,
    aluno_id: Optional[str] = None,
    prompt_id: Optional[str] = None
):
    """
    Prepara dados para executar uma etapa.
    Retorna o prompt que será usado e as variáveis disponíveis.
    """
    try:
        etapa_enum = EtapaProcessamento(etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {etapa}")
    
    # Buscar prompt
    if prompt_id:
        prompt = prompt_manager.get_prompt(prompt_id)
    else:
        atividade = storage.get_atividade(atividade_id)
        turma = storage.get_turma(atividade.turma_id) if atividade else None
        materia_id = turma.materia_id if turma else None
        prompt = prompt_manager.get_prompt_padrao(etapa_enum, materia_id)
    
    if not prompt:
        raise HTTPException(404, f"Nenhum prompt encontrado para etapa {etapa}")
    
    # Buscar documentos relevantes
    documentos = storage.listar_documentos(atividade_id, aluno_id)
    
    # Preparar variáveis disponíveis
    variaveis_disponiveis = {}
    
    for doc in documentos:
        if doc.tipo == TipoDocumento.ENUNCIADO:
            variaveis_disponiveis["conteudo_documento"] = f"[Conteúdo do arquivo: {doc.nome_arquivo}]"
        if doc.tipo == TipoDocumento.GABARITO:
            variaveis_disponiveis["gabarito"] = f"[Conteúdo do gabarito: {doc.nome_arquivo}]"
        if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
            variaveis_disponiveis["prova_aluno"] = f"[Conteúdo da prova: {doc.nome_arquivo}]"
    
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
    
    return {
        "etapa": etapa,
        "prompt": prompt.to_dict(),
        "variaveis_requeridas": prompt.variaveis,
        "variaveis_disponiveis": variaveis_disponiveis,
        "documentos_encontrados": [{"id": d.id, "tipo": d.tipo.value, "nome": d.nome_arquivo} for d in documentos]
    }


@router.get("/api/documentos/{documento_id}/conteudo", tags=["Documentos"])
async def get_conteudo_documento(documento_id: str):
    """
    Retorna o conteúdo de um documento.
    Para JSONs, retorna parseado. Para outros, retorna texto ou info do arquivo.
    """
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    from pathlib import Path
    arquivo = Path(documento.caminho_arquivo)
    
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado no sistema")
    
    conteudo = None
    tipo_conteudo = "arquivo"
    
    # Tentar ler baseado na extensão
    if documento.extensao.lower() == '.json':
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
            tipo_conteudo = "json"
        except:
            pass
    elif documento.extensao.lower() in ['.txt', '.md']:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            tipo_conteudo = "texto"
        except:
            pass
    
    return {
        "documento": documento.to_dict(),
        "tipo_conteudo": tipo_conteudo,
        "conteudo": conteudo,
        "pode_visualizar": tipo_conteudo in ["json", "texto"]
    }


# ============================================================
# ENDPOINTS: PROVIDERS
# ============================================================

@router.get("/api/providers/disponiveis", tags=["Providers"])
async def listar_providers_disponiveis():
    """Lista providers de IA disponíveis para processamento"""
    from ai_providers import ai_registry
    
    providers = ai_registry.get_provider_info()
    
    return {
        "providers": providers,
        "default": ai_registry.default_provider
    }


# ============================================================
# ENDPOINTS: EXECUÇÃO DE ETAPAS
# ============================================================

@router.post("/api/executar/etapa", tags=["Execução"])
async def executar_etapa(data: ProcessarEtapaRequest):
    """
    Executa uma etapa específica do pipeline.
    
    Retorna o resultado da execução, incluindo a resposta da IA.
    """
    from executor import executor, EtapaProcessamento
    
    try:
        etapa = EtapaProcessamento(data.etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {data.etapa}")
    
    resultado = await executor.executar_etapa(
        etapa=etapa,
        atividade_id=data.atividade_id,
        aluno_id=data.aluno_id,
        prompt_id=data.prompt_id,
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
    from executor import executor, EtapaProcessamento
    
    try:
        etapa = EtapaProcessamento(data.etapa)
    except ValueError:
        raise HTTPException(400, f"Etapa inválida: {data.etapa}")
    
    resultado = await executor.executar_etapa(
        etapa=etapa,
        atividade_id=data.atividade_id,
        aluno_id=data.aluno_id,
        prompt_id=data.prompt_id,
        provider_name=data.provider,
        salvar_resultado=False  # Não salva!
    )
    
    return {
        "sucesso": resultado.sucesso,
        "preview": True,
        "resultado": resultado.to_dict()
    }


@router.post("/api/executar/pipeline-completo", tags=["Execução"])
async def executar_pipeline_completo(
    atividade_id: str = Form(...),
    aluno_id: str = Form(...),
    provider: Optional[str] = Form(None)
):
    """
    Executa o pipeline completo para um aluno.
    Executa todas as etapas necessárias em sequência.
    """
    from executor import executor
    
    resultados = await executor.executar_pipeline_completo(
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        provider_name=provider
    )
    
    # Resumo
    sucesso_total = all(r.sucesso for r in resultados.values())
    etapas_executadas = [k for k, v in resultados.items() if v.sucesso]
    etapas_falharam = [k for k, v in resultados.items() if not v.sucesso]
    
    return {
        "sucesso": sucesso_total,
        "etapas_executadas": etapas_executadas,
        "etapas_falharam": etapas_falharam,
        "resultados": {k: v.to_dict() for k, v in resultados.items()}
    }


@router.post("/api/executar/lote", tags=["Execução"])
async def executar_lote(
    atividade_id: str = Form(...),
    aluno_ids: str = Form(...),  # IDs separados por vírgula
    provider: Optional[str] = Form(None)
):
    """
    Executa o pipeline completo para múltiplos alunos.
    """
    from executor import executor
    
    ids = [id.strip() for id in aluno_ids.split(',') if id.strip()]
    
    resultados_por_aluno = {}
    for aluno_id in ids:
        aluno = storage.get_aluno(aluno_id)
        nome = aluno.nome if aluno else aluno_id
        
        resultados = await executor.executar_pipeline_completo(
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_name=provider
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
