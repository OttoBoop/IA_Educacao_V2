"""
NOVO CR - Rotas de Prompts e Processamento

Endpoints para:
- Gerenciar prompts (CRUD)
- Executar etapas individuais do pipeline
- Visualizar resultados

ATUALIZADO: Integrado com chat_service.py (novo sistema de models/providers)
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Form, UploadFile, File, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path
import asyncio
import inspect
import json
import logging
import tempfile
import threading

from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage import storage
from models import TipoDocumento, Documento
from routes_tasks import register_pipeline_task, complete_pipeline_task
from ai_execution import (
    CAPABILITY_DOCUMENT_READ,
    create_document_provider,
    parse_json_list,
    parse_json_map,
    resolve_ai_model,
)

logger = logging.getLogger(__name__)


def _resolve_names_from_atividade(atividade_id):
    """Look up matéria/turma/atividade names for task_registry.

    Returns dict with materia_nome, turma_nome, atividade_nome (any may be None).
    """
    names = {"materia_nome": None, "turma_nome": None, "atividade_nome": None}
    atividade = storage.get_atividade(atividade_id)
    if atividade:
        names["atividade_nome"] = atividade.nome
        turma = storage.get_turma(atividade.turma_id)
        if turma:
            names["turma_nome"] = turma.nome
            materia = storage.get_materia(turma.materia_id)
            if materia:
                names["materia_nome"] = materia.nome
    return names


def _resolve_student_names(aluno_ids):
    """Look up student names for task_registry.

    Returns dict mapping {aluno_id: nome_string}.
    Missing alunos produce empty-string nome (no KeyError).
    """
    result = {}
    for aluno_id in aluno_ids:
        aluno = storage.get_aluno(aluno_id)
        result[aluno_id] = aluno.nome if aluno else ""
    return result


def _start_detached_task(func, *args, **kwargs):
    """Run long pipeline work outside the request lifecycle.

    FastAPI BackgroundTasks still execute in the server process after the
    response is prepared. The pipeline contains blocking provider/storage work,
    so running it there can keep the Render worker unresponsive. A daemon thread
    gives the HTTP response a clean break: task progress is tracked through
    task_registry, not through the request connection.
    """

    def _runner():
        task_id = kwargs.get("task_id")
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                asyncio.run(result)
        except Exception as exc:
            logger.exception("Detached pipeline task failed")
            if task_id:
                complete_pipeline_task(task_id, "failed", error=str(exc))

    thread = threading.Thread(
        target=_runner,
        name=f"novocr-task-{kwargs.get('task_id', 'detached')}",
        daemon=True,
    )
    thread.start()
    return thread


def _status_value(doc: Documento) -> str:
    status = getattr(doc, "status", "") or ""
    return str(getattr(status, "value", status) or "")


def _is_error_doc(doc: Documento) -> bool:
    return _status_value(doc) == "erro"


def _latest_student_doc(atividade_id: str, aluno_id: str, tipo: TipoDocumento) -> Optional[Documento]:
    docs = storage.listar_documentos(atividade_id, aluno_id=aluno_id, tipo=tipo)
    for doc in docs:
        if getattr(doc, "aluno_id", None) == aluno_id and not _is_error_doc(doc):
            return doc
    return None


def _existing_aluno_turma_report(
    aluno_id: str,
    turma_id: str,
    requested_model_id: Optional[str] = None,
    legacy_provider_id: Optional[str] = None,
) -> Optional[Documento]:
    for atividade in storage.listar_atividades(turma_id):
        docs = storage.listar_documentos(
            atividade.id,
            aluno_id=aluno_id,
            tipo=TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA,
        )
        for doc in docs:
            metadata = doc.metadata if isinstance(doc.metadata, dict) else {}
            if requested_model_id and (
                metadata.get("requested_model_id")
                or metadata.get("model_id")
                or metadata.get("provider_ref")
            ) != requested_model_id:
                continue
            if legacy_provider_id and (
                metadata.get("legacy_provider_id")
                or metadata.get("provider_id")
                or metadata.get("provider_ref")
            ) != legacy_provider_id:
                continue
            if (
                getattr(doc, "aluno_id", None) == aluno_id
                and metadata.get("turma_id") == turma_id
                and metadata.get("geracao") == "provider_document_read_v1"
                and not _is_error_doc(doc)
            ):
                return doc
    return None


def _looks_like_failed_document_read(content: str) -> bool:
    text = (content or "").strip()
    if not text:
        return True

    lowered = text.casefold()
    failure_markers = (
        "falha_leitura_documento",
        "conteudo nao extraido",
        "conteúdo não extraído",
        "não consigo acessar",
        "nao consigo acessar",
        "não posso acessar",
        "nao posso acessar",
        "não foi possível ler",
        "nao foi possivel ler",
        "unable to read",
        "cannot access",
        "can't access",
    )
    return any(marker in lowered for marker in failure_markers)


def _parse_form_map(raw: Optional[str], field_name: str) -> Dict[str, str]:
    try:
        return parse_json_map(raw, field_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _parse_form_list(raw: Optional[str], field_name: str) -> List[str]:
    try:
        return parse_json_list(raw, field_name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


def _parse_models_per_stage(
    models_per_stage: Optional[str] = None,
    providers: Optional[str] = None,
    phase_models: Optional[str] = None,
) -> Dict[str, str]:
    merged: Dict[str, str] = {}
    if providers:
        merged.update(_parse_form_map(providers, "providers"))
    if phase_models:
        merged.update(_parse_form_map(phase_models, "phase_models"))
    if models_per_stage:
        merged.update(_parse_form_map(models_per_stage, "models_per_stage"))
    return merged


def _model_requests(
    model_id: Optional[str],
    model_ids: Optional[str],
    provider_id: Optional[str],
) -> List[Dict[str, Optional[str]]]:
    ids = _parse_form_list(model_ids, "model_ids") if model_ids else []
    if ids:
        return [{"model_id": item, "provider_id": None} for item in ids]
    if model_id:
        return [{"model_id": model_id, "provider_id": None}]
    if provider_id:
        return [{"model_id": None, "provider_id": provider_id}]
    return [{"model_id": None, "provider_id": None}]


def _source_selection_mode(source_document_ids: Dict[str, str]) -> str:
    return "explicit" if source_document_ids else "latest_valid"


def _aluno_turma_document_instruction(aluno, turma, materia, atividade) -> str:
    return f"""
Voce esta gerando um relatorio de desempenho individual aluno-turma.

Leia o documento anexado. Ele e um RELATORIO_FINAL individual ja gerado para uma
atividade do aluno. Use o conteudo real do documento; nao escreva placeholder e
nao diga que o conteudo nao foi extraido.

Escopo obrigatorio:
- Aluno: {aluno.nome}
- Turma: {turma.nome}
- Materia: {materia.nome if materia else 'N/A'}
- Atividade: {atividade.nome}

Responda em Markdown com:
- uma sintese pedagogica concreta da atividade;
- nota ou resultado, se aparecer no documento;
- pontos fortes;
- areas de melhoria;
- recomendacoes acionaveis;
- evidencias do proprio documento.

Se voce nao conseguir ler o documento anexado, responda exatamente:
FALHA_LEITURA_DOCUMENTO: <motivo>
""".strip()


async def _analyze_aluno_turma_report_doc(provider, doc: Documento, aluno, turma, materia, atividade) -> Dict[str, Any]:
    path = storage.resolver_caminho_documento(doc)
    if not path.exists():
        raise HTTPException(
            status_code=500,
            detail={
                "mensagem": "Documento base nao encontrado para relatorio aluno-turma",
                "documento_id": doc.id,
                "nome_arquivo": doc.nome_arquivo,
            },
        )

    try:
        response = await provider.analyze_document(
            str(path),
            _aluno_turma_document_instruction(aluno, turma, materia, atividade),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "mensagem": "Provider falhou ao ler documento base; relatorio aluno-turma nao foi gerado",
                "documento_id": doc.id,
                "provider": getattr(provider, "name", None),
                "modelo": getattr(provider, "model", None),
                "erro": str(exc)[:2000],
            },
        )
    content = (getattr(response, "content", "") or "").strip()
    if _looks_like_failed_document_read(content):
        raise HTTPException(
            status_code=502,
            detail={
                "mensagem": "Provider nao leu o documento base; relatorio aluno-turma nao foi gerado",
                "documento_id": doc.id,
                "provider": getattr(response, "provider", None),
                "modelo": getattr(response, "model", None),
                "resposta": content[:1000],
            },
        )

    return {
        "atividade_id": atividade.id,
        "atividade_nome": atividade.nome,
        "documento_id": doc.id,
        "documento_nome": doc.nome_arquivo,
        "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
        "conteudo": content,
        "provider": getattr(response, "provider", None),
        "modelo": getattr(response, "model", None),
        "tokens_usados": int(getattr(response, "tokens_used", 0) or 0),
        "input_tokens": int(getattr(response, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(response, "output_tokens", 0) or 0),
        "latency_ms": float(getattr(response, "latency_ms", 0) or 0),
    }


def _resolve_document_read_provider(model_id: Optional[str] = None, provider_id: Optional[str] = None):
    try:
        resolution = resolve_ai_model(
            model_id=model_id,
            provider_id=provider_id,
            required_capability=CAPABILITY_DOCUMENT_READ,
        )
        return resolution, create_document_provider(resolution)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "mensagem": "Modelo de IA indisponivel para leitura de documento",
                "model_id": model_id,
                "provider_id": provider_id,
                "erro": str(exc),
            },
        )


def _resolve_source_doc_for_aluno_turma(
    doc_id: str,
    aluno_id: str,
    turma_id: str,
) -> Documento:
    doc = storage.get_documento(doc_id)
    if not doc:
        raise HTTPException(400, f"source_document_ids referencia documento inexistente: {doc_id}")
    if doc.tipo != TipoDocumento.RELATORIO_FINAL:
        raise HTTPException(
            400,
            f"Documento {doc_id} tem tipo {doc.tipo.value}; esperado relatorio_final",
        )
    if getattr(doc, "aluno_id", None) != aluno_id:
        raise HTTPException(400, f"Documento {doc_id} pertence a outro aluno")
    atividade = storage.get_atividade(doc.atividade_id)
    if not atividade or atividade.turma_id != turma_id:
        raise HTTPException(400, f"Documento {doc_id} pertence a outra turma")
    if _is_error_doc(doc):
        raise HTTPException(400, f"Documento {doc_id} esta marcado como erro")
    return doc


def _collect_aluno_turma_report_docs(
    aluno_id: str,
    turma_id: str,
    source_document_ids: Dict[str, str],
) -> List[Documento]:
    if source_document_ids:
        selected: List[Documento] = []
        seen = set()
        for doc_id in source_document_ids.values():
            doc = _resolve_source_doc_for_aluno_turma(doc_id, aluno_id, turma_id)
            if doc.id not in seen:
                selected.append(doc)
                seen.add(doc.id)
        return selected

    docs: List[Documento] = []
    for atividade in storage.listar_atividades(turma_id):
        doc = _latest_student_doc(atividade.id, aluno_id, TipoDocumento.RELATORIO_FINAL)
        if doc:
            docs.append(doc)
    return docs


async def _gerar_aluno_turma_para_modelo(
    aluno,
    turma,
    materia,
    model_id: Optional[str],
    provider_id: Optional[str],
    force_reexec: bool,
    source_document_ids: Dict[str, str],
) -> Dict[str, Any]:
    resolution, provider = _resolve_document_read_provider(model_id=model_id, provider_id=provider_id)

    existente = _existing_aluno_turma_report(
        aluno.id,
        turma.id,
        requested_model_id=resolution.requested_model_id,
        legacy_provider_id=resolution.legacy_provider_id,
    )
    if existente and not force_reexec:
        return {
            "status": "completed",
            "skipped": True,
            "documento": existente.to_dict(),
            "metadata": existente.metadata,
            **resolution.metadata(),
        }

    docs_origem = _collect_aluno_turma_report_docs(aluno.id, turma.id, source_document_ids)
    if not docs_origem:
        raise HTTPException(
            status_code=400,
            detail={
                "mensagem": "Base minima insuficiente para relatorio aluno-turma",
                "scope": "aluno_turma",
                "aluno_id": aluno.id,
                "turma_id": turma.id,
                "faltando": ["relatorio_final_do_aluno"],
                "selection_mode": _source_selection_mode(source_document_ids),
            },
        )

    entradas = []
    for doc in docs_origem:
        atividade = storage.get_atividade(doc.atividade_id)
        if not atividade:
            continue
        entradas.append(
            await _analyze_aluno_turma_report_doc(provider, doc, aluno, turma, materia, atividade)
        )

    if not entradas:
        raise HTTPException(
            status_code=400,
            detail={
                "mensagem": "Nenhum documento de origem valido para relatorio aluno-turma",
                "aluno_id": aluno.id,
                "turma_id": turma.id,
            },
        )

    tokens_usados = sum(entrada.get("tokens_usados", 0) for entrada in entradas)
    tempo_processamento_ms = sum(entrada.get("latency_ms", 0) for entrada in entradas)

    metadata = {
        "scope": "aluno_turma",
        "aluno_id": aluno.id,
        "turma_id": turma.id,
        "materia_id": turma.materia_id,
        "status": "completed",
        "atividade_ids": [entrada["atividade_id"] for entrada in entradas],
        "documento_origem_ids": [entrada["documento_id"] for entrada in entradas],
        "source_document_ids": [entrada["documento_id"] for entrada in entradas],
        "selection_mode": _source_selection_mode(source_document_ids),
        "geracao": "provider_document_read_v1",
        "model_id": model_id,
        "provider_id": provider_id,
        "provider_ref": model_id or provider_id or resolution.resolved_model_id,
        "tokens_usados": tokens_usados,
        "tempo_processamento_ms": tempo_processamento_ms,
        **resolution.metadata(),
        "leituras": [
            {
                "atividade_id": entrada["atividade_id"],
                "documento_id": entrada["documento_id"],
                "provider": entrada.get("provider"),
                "modelo": entrada.get("modelo"),
                "tokens_usados": entrada.get("tokens_usados", 0),
                "input_tokens": entrada.get("input_tokens", 0),
                "output_tokens": entrada.get("output_tokens", 0),
            }
            for entrada in entradas
        ],
    }

    report_text = _build_aluno_turma_report(aluno, turma, materia, entradas)
    provider_nome = next((entrada.get("provider") for entrada in entradas if entrada.get("provider")), None)
    provider_modelo = next((entrada.get("modelo") for entrada in entradas if entrada.get("modelo")), None)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
            tmp.write(report_text)
            tmp_path = Path(tmp.name)

        documento = storage.salvar_documento(
            str(tmp_path),
            TipoDocumento.RELATORIO_DESEMPENHO_ALUNO_TURMA,
            entradas[0]["atividade_id"],
            aluno_id=aluno.id,
            display_name=f"Desempenho aluno-turma - {aluno.nome} - {turma.nome}",
            metadata=metadata,
            ia_provider=provider_nome or resolution.provider_type,
            ia_modelo=provider_modelo or resolution.model_name,
            tokens_usados=tokens_usados,
            tempo_processamento_ms=tempo_processamento_ms,
            criado_por="sistema",
        )
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()

    return {
        "status": "completed",
        "skipped": False,
        "documento": documento.to_dict() if documento else None,
        "metadata": metadata,
        "atividades_usadas": len(entradas),
        **resolution.metadata(),
    }


def _build_aluno_turma_report(aluno, turma, materia, entradas: List[Dict[str, Any]]) -> str:
    linhas = [
        f"# Relatorio de Desempenho Aluno-Turma",
        "",
        f"**Aluno:** {aluno.nome}",
        f"**Turma:** {turma.nome}",
        f"**Materia:** {materia.nome if materia else 'N/A'}",
        f"**Atividades com relatorio final:** {len(entradas)}",
        "",
        "## Sintese",
        "",
        (
            "Este relatorio foi gerado a partir da leitura por IA dos relatorios "
            "finais individuais deste aluno nesta turma. O escopo e aluno + turma; "
            "nao mistura outras turmas da mesma materia nem documentos de outros alunos."
        ),
        "",
        "## Leituras Por Atividade",
    ]
    for entrada in entradas:
        linhas.extend([
            "",
            f"### {entrada['atividade_nome']}",
            "",
            f"- Documento base: `{entrada['documento_id']}`",
            f"- Arquivo base: `{entrada.get('documento_nome') or 'N/A'}`",
            f"- Criado em: {entrada.get('criado_em') or 'N/A'}",
            f"- Provider leitor: {entrada.get('provider') or 'N/A'} / {entrada.get('modelo') or 'N/A'}",
            "",
            entrada["conteudo"].strip(),
        ])
    linhas.extend([
        "",
        "## Proximos usos",
        "",
        "- Usar este documento como insumo para o relatorio longitudinal do aluno.",
        "- Regerar quando novos `relatorio_final` forem adicionados nesta turma.",
    ])
    return "\n".join(linhas).strip() + "\n"

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
    apenas_ativos: bool = True,
    page: int = Query(1, ge=1),
    per_page: int = Query(0, ge=0)
):
    """Lista todos os prompts com filtros opcionais e paginação.

    Quando per_page > 0, retorna resultados paginados com metadados.
    Quando per_page == 0 (default), retorna todos os resultados (backwards compatible).
    """
    etapa_enum = EtapaProcessamento(etapa) if etapa else None
    prompts = prompt_manager.listar_prompts(etapa_enum, materia_id, apenas_ativos)
    total = len(prompts)

    if per_page > 0:
        import math
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        start = (page - 1) * per_page
        end = start + per_page
        prompts_page = prompts[start:end]
        return {
            "prompts": [p.to_dict() for p in prompts_page],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    return {
        "prompts": [p.to_dict() for p in prompts],
        "total": total
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
    """Lê conteúdo de um documento, downloading from Supabase Storage if needed"""
    try:
        # Use resolver to download from Supabase Storage if local file missing
        arquivo = storage.resolver_caminho_documento(doc)
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

    # Carregar variáveis usando o executor (mesma lógica do pipeline-completo)
    from executor import executor

    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, f"Atividade não encontrada: {atividade_id}")

    turma = storage.get_turma(atividade.turma_id)
    materia = storage.get_materia(turma.materia_id) if turma else None

    variaveis = executor._preparar_variaveis_texto(
        etapa, atividade_id, aluno_id, materia, atividade, usar_multimodal=True
    )

    # Carregar contexto JSON de etapas anteriores (questões, gabarito, respostas, correções)
    contexto_json = executor._preparar_contexto_json(atividade_id, aluno_id, etapa)
    docs_faltantes = contexto_json.pop("_documentos_faltantes", [])
    contexto_json.pop("_documentos_carregados", [])

    # Falhar explicitamente se faltam documentos de etapas anteriores
    if docs_faltantes:
        def _formatar_doc(d):
            if isinstance(d, dict):
                tipo = d.get("tipo") or d.get("descricao") or str(d)
                desc = d.get("descricao")
                return f"{tipo} ({desc})" if desc and desc != tipo else str(tipo)
            return str(d)
        lista = ", ".join(_formatar_doc(d) for d in docs_faltantes)
        raise HTTPException(
            400,
            detail=(
                f"Documentos necessários não encontrados: {lista}. "
                "Execute as etapas anteriores do pipeline antes desta."
            )
        )

    variaveis.update(contexto_json)

    # Renderizar prompt (usa customizado se fornecido)
    if prompt_customizado:
        # Substituir variáveis no texto customizado
        texto_renderizado = prompt_customizado
        for key, value in variaveis.items():
            texto_renderizado = texto_renderizado.replace(f"{{{key}}}", str(value))
        texto_sistema = prompt.render_sistema(**variaveis) if prompt and prompt.texto_sistema else None
    else:
        texto_renderizado = prompt.render(**variaveis)
        texto_sistema = prompt.render_sistema(**variaveis) if prompt and prompt.texto_sistema else None
    
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
    models_per_stage: Optional[str] = Form(None),
    source_document_ids: Optional[str] = Form(None),
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

    providers_map = _parse_form_map(providers, "providers")
    models_stage_map = _parse_models_per_stage(
        models_per_stage=models_per_stage,
        providers=None,
    )
    source_map = _parse_form_map(source_document_ids, "source_document_ids")

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
    names = _resolve_names_from_atividade(atividade_id)
    task_id = register_pipeline_task(
        task_type="pipeline",
        atividade_id=atividade_id,
        aluno_ids=[aluno_id],
        student_names=_resolve_student_names([aluno_id]),
        **names,
    )

    # Run pipeline execution detached from the request — endpoint returns task_id immediately.
    _start_detached_task(
        executor.executar_pipeline_completo,
        task_id=task_id,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        model_id=model_id,
        provider_name=provider,
        providers_map=providers_map,
        models_per_stage=models_stage_map,
        source_document_ids=source_map,
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
    
    # Buscar documentos base da atividade e documentos estritamente do aluno.
    # storage.listar_documentos(atividade_id) retorna o historico inteiro da
    # atividade; filtrar aluno_id aqui evita vazar versoes de outros alunos.
    docs_atividade = storage.listar_documentos(atividade_id)
    docs_base = [d for d in docs_atividade if not getattr(d, "aluno_id", None)]
    docs_aluno = [
        d for d in storage.listar_documentos(atividade_id, aluno_id)
        if getattr(d, "aluno_id", None) == aluno_id
    ]

    todos_docs_por_id = {}
    for doc in docs_base + docs_aluno:
        doc_id = getattr(doc, "id", None)
        if doc_id and doc_id in todos_docs_por_id:
            continue
        todos_docs_por_id[doc_id or id(doc)] = doc
    todos_docs = list(todos_docs_por_id.values())
    
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
    providers: Optional[str] = Form(None),
    models_per_stage: Optional[str] = Form(None),
    source_document_ids: Optional[str] = Form(None),
):
    """
    Executa o pipeline completo para múltiplos alunos.
    """
    from executor import executor
    
    ids = [id.strip() for id in aluno_ids.split(',') if id.strip()]
    
    providers_map = _parse_form_map(providers, "providers")
    models_stage_map = _parse_models_per_stage(models_per_stage=models_per_stage)
    source_map = _parse_form_map(source_document_ids, "source_document_ids")
    
    resultados_por_aluno = {}
    for aluno_id in ids:
        aluno = storage.get_aluno(aluno_id)
        nome = aluno.nome if aluno else aluno_id
        
        resultados = await executor.executar_pipeline_completo(
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            model_id=model_id,
            provider_name=provider,
            providers_map=providers_map,
            models_per_stage=models_stage_map,
            source_document_ids=source_map,
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
    models_per_stage,
    source_document_ids,
    prompt_id,
    prompts_map,
    steps_list,
    force_rerun: bool,
):
    """Background helper: runs pipeline for every student in the turma sequentially."""
    from executor import executor
    from routes_tasks import complete_pipeline_task, task_registry, update_stage_progress

    for aluno in alunos_para_processar:
        try:
            await executor.executar_pipeline_completo(
                task_id=task_id,
                atividade_id=atividade_id,
                aluno_id=aluno.id,
                model_id=model_id,
                provider_name=provider,
                providers_map=providers_map,
                models_per_stage=models_per_stage,
                source_document_ids=source_document_ids,
                prompt_id=prompt_id,
                prompts_map=prompts_map,
                selected_steps=steps_list,
                force_rerun=force_rerun,
            )
        except Exception as exc:
            task = task_registry.get(task_id) or {}
            student = (task.get("students") or {}).get(aluno.id, {})
            stages = student.get("stages") or {}
            failed_stage = next(
                (stage for stage, status in stages.items() if status == "running"),
                None,
            ) or next(
                (stage for stage, status in stages.items() if status == "pending"),
                "gerar_relatorio",
            )
            update_stage_progress(
                task_id,
                aluno.id,
                failed_stage,
                "failed",
                error={
                    "mensagem": f"Excecao no processamento em lote: {exc}",
                    "tipo": "batch_student_exception",
                },
            )

    complete_pipeline_task(task_id, "completed")


@router.post("/api/executar/pipeline-todos-os-alunos", tags=["Execução"])
async def executar_pipeline_todos_os_alunos(
    background_tasks: BackgroundTasks,
    atividade_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider: Optional[str] = Form(None),  # [LEGACY - MARK FOR DELETION] Provider de IA a usar (opcional, legacy)
    providers: Optional[str] = Form(None),
    models_per_stage: Optional[str] = Form(None),
    source_document_ids: Optional[str] = Form(None),
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

    providers_map = _parse_form_map(providers, "providers")
    models_stage_map = _parse_models_per_stage(models_per_stage=models_per_stage)
    source_map = _parse_form_map(source_document_ids, "source_document_ids")

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
    names = _resolve_names_from_atividade(atividade_id)
    aluno_ids_para_processar = [aluno.id for aluno in alunos_para_processar]
    task_id = register_pipeline_task(
        task_type="pipeline_todos_os_alunos",
        atividade_id=atividade_id,
        aluno_ids=aluno_ids_para_processar,
        turma_id=atividade.turma_id,
        student_names=_resolve_student_names(aluno_ids_para_processar),
        **names,
    )

    # Run the student loop detached from the request — endpoint returns task_id immediately.
    _start_detached_task(
        _executar_pipeline_todos_os_alunos_background,
        task_id=task_id,
        alunos_para_processar=alunos_para_processar,
        atividade_id=atividade_id,
        model_id=model_id,
        provider=provider,
        providers_map=providers_map,
        models_per_stage=models_stage_map,
        source_document_ids=source_map,
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

@router.post("/api/executar/pipeline-desempenho-aluno-turma", tags=["Execução"])
async def executar_pipeline_desempenho_aluno_turma(
    aluno_id: str = Form(...),
    turma_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    model_ids: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
    source_document_ids: Optional[str] = Form(None),
    force_reexec: bool = Form(False),
):
    """Gera um relatorio de desempenho individual para aluno + turma.

    Le os RELATORIO_FINAL daquele aluno naquela turma com um provider de IA e
    salva um Markdown consolidado. Se o provider nao conseguir ler o documento,
    a execucao falha em vez de criar placeholder.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")

    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")

    turmas_do_aluno = storage.get_turmas_do_aluno(aluno_id, apenas_ativas=False)
    if not any(item.get("id") == turma_id for item in turmas_do_aluno):
        raise HTTPException(404, "Aluno não vinculado a esta turma")

    materia = storage.get_materia(turma.materia_id) if turma.materia_id else None
    source_map = _parse_form_map(source_document_ids, "source_document_ids")
    requests = _model_requests(model_id, model_ids, provider_id)

    atividade_ref = None
    for doc in _collect_aluno_turma_report_docs(aluno_id, turma_id, source_map):
        atividade_ref = doc.atividade_id
        break
    if atividade_ref is None:
        atividades = storage.listar_atividades(turma_id)
        atividade_ref = atividades[0].id if atividades else turma_id

    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_aluno_turma",
        atividade_id=atividade_ref,
        aluno_ids=[],
        turma_id=turma_id,
        materia_id=turma.materia_id,
        materia_nome=materia.nome if materia else None,
        turma_nome=turma.nome,
        student_names={aluno_id: aluno.nome},
    )

    resultados = []
    falhas = []
    for request in requests:
        try:
            resultados.append(
                await _gerar_aluno_turma_para_modelo(
                    aluno=aluno,
                    turma=turma,
                    materia=materia,
                    model_id=request.get("model_id"),
                    provider_id=request.get("provider_id"),
                    force_reexec=force_reexec,
                    source_document_ids=source_map,
                )
            )
        except HTTPException as exc:
            if len(requests) == 1:
                raise
            falhas.append({
                "model_id": request.get("model_id"),
                "provider_id": request.get("provider_id"),
                "status": "failed",
                "erro": exc.detail,
            })

    if not resultados and falhas:
        complete_pipeline_task(task_id, "failed", error=json.dumps(falhas, ensure_ascii=False))
        return {"task_id": task_id, "status": "failed", "resultados": falhas}

    if len(requests) == 1 and resultados:
        result = resultados[0]
        complete_pipeline_task(task_id, "completed", result=result)
        return {"task_id": task_id, **result}

    result = {
        "resultados": resultados + falhas,
        "documentos": [r.get("documento") for r in resultados if r.get("documento")],
        "falhas": falhas,
        "selection_mode": _source_selection_mode(source_map),
    }
    complete_pipeline_task(task_id, "completed", result=result)
    return {"task_id": task_id, "status": "completed", **result}


@router.post("/api/executar/documento-multi-ia", tags=["Execução"])
async def executar_documento_multi_ia(
    documento_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    model_ids: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
    instruction: Optional[str] = Form(None),
):
    """Analisa um documento existente com uma ou varias IAs.

    Contrato: cada modelo solicitado roda ou falha explicitamente. Sucessos
    salvam `analise_documento_ia`; falhas ficam no retorno, sem fallback para
    outro modelo.
    """
    doc = storage.get_documento(documento_id)
    if not doc:
        raise HTTPException(404, "Documento não encontrado")

    path = storage.resolver_caminho_documento(doc)
    if not path.exists():
        raise HTTPException(404, "Arquivo do documento não encontrado")

    requests = _model_requests(model_id, model_ids, provider_id)
    prompt = (instruction or "").strip() or (
        "Leia o documento anexado e produza uma analise objetiva em Markdown. "
        "Use apenas o conteudo real do documento. Se nao conseguir ler, responda "
        "FALHA_LEITURA_DOCUMENTO: <motivo>."
    )

    resultados = []
    for request in requests:
        try:
            resolution, provider = _resolve_document_read_provider(
                model_id=request.get("model_id"),
                provider_id=request.get("provider_id"),
            )
            response = await provider.analyze_document(str(path), prompt)
            content = (getattr(response, "content", "") or "").strip()
            if _looks_like_failed_document_read(content):
                raise HTTPException(
                    502,
                    {
                        "mensagem": "Provider nao leu o documento",
                        "documento_id": documento_id,
                        "resposta": content[:1000],
                    },
                )

            tokens_usados = int(getattr(response, "tokens_used", 0) or 0)
            tempo_processamento_ms = float(getattr(response, "latency_ms", 0) or 0)

            metadata = {
                "scope": "documento_multi_ia",
                "source_document_ids": [documento_id],
                "documento_origem_id": documento_id,
                "selection_mode": "explicit",
                "status": "completed",
                "tokens_usados": tokens_usados,
                "tempo_processamento_ms": tempo_processamento_ms,
                "instruction": prompt,
                **resolution.metadata(),
            }

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
                    tmp.write(content + "\n")
                    tmp_path = Path(tmp.name)

                saved = storage.salvar_documento(
                    str(tmp_path),
                    TipoDocumento.ANALISE_DOCUMENTO_IA,
                    doc.atividade_id,
                    aluno_id=doc.aluno_id,
                    display_name=f"Analise multi-IA - {doc.display_name or doc.nome_arquivo}",
                    metadata=metadata,
                    ia_provider=getattr(response, "provider", None) or resolution.provider_type,
                    ia_modelo=getattr(response, "model", None) or resolution.model_name,
                    tokens_usados=tokens_usados,
                    tempo_processamento_ms=tempo_processamento_ms,
                    criado_por="sistema",
                    documento_origem_id=documento_id,
                )
            finally:
                if tmp_path and tmp_path.exists():
                    tmp_path.unlink()

            resultados.append({
                "status": "completed",
                "documento": saved.to_dict() if saved else None,
                "metadata": metadata,
                "tokens_usados": tokens_usados,
                "tempo_processamento_ms": tempo_processamento_ms,
                **resolution.metadata(),
            })
        except HTTPException as exc:
            resultados.append({
                "status": "failed",
                "model_id": request.get("model_id"),
                "provider_id": request.get("provider_id"),
                "erro": exc.detail,
            })

    ok = [item for item in resultados if item.get("status") == "completed"]
    return {
        "status": "completed" if ok else "failed",
        "documento_id": documento_id,
        "resultados": resultados,
        "documentos": [item.get("documento") for item in ok if item.get("documento")],
    }


@router.post("/api/executar/pipeline-desempenho-tarefa", tags=["Execução"])
async def executar_pipeline_desempenho_tarefa(
    background_tasks: BackgroundTasks,
    atividade_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
    models_per_stage: Optional[str] = Form(None),
    phase_models: Optional[str] = Form(None),
    force_reexec: bool = Form(False),
    etapas_selecionadas: Optional[str] = Form(None),
    isolate_provider: bool = Form(False),
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

    model_ref = model_id or provider_id
    models_stage_map = _parse_models_per_stage(
        models_per_stage=models_per_stage,
        phase_models=phase_models,
    )
    names = _resolve_names_from_atividade(atividade_id)
    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_tarefa",
        atividade_id=atividade_id,
        aluno_ids=[],
        **names,
    )

    _start_detached_task(
        _executar_desempenho_tarefa_background,
        task_id=task_id,
        atividade_id=atividade_id,
        model_id=model_ref,
        provider_id=provider_id,
        models_per_stage=models_stage_map,
        force_reexec=force_reexec,
        isolate_provider=isolate_provider,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_tarefa_background(
    task_id: str,
    atividade_id: str,
    model_id: Optional[str],
    provider_id: Optional[str],
    models_per_stage: Optional[Dict[str, str]],
    force_reexec: bool = False,
    isolate_provider: bool = False,
):
    from executor import executor
    from routes_tasks import task_registry, PIPELINE_STAGES
    try:
        # Pre-populate students for the UI progress panel
        try:
            atividade = storage.get_atividade(atividade_id)
            alunos = storage.listar_alunos(atividade.turma_id) if atividade else []
            task = task_registry.get(task_id)
            if task is not None:
                students = task.setdefault("students", {})
                for aluno in (alunos or []):
                    if aluno.id not in students:
                        students[aluno.id] = {
                            "nome": aluno.nome or "",
                            "stages": {s: "pending" for s in PIPELINE_STAGES},
                            "stage_errors": {},
                        }
        except Exception:
            pass

        await executor._cascade_prereqs(
            level="tarefa",
            entity_id=atividade_id,
            provider_id=model_id or provider_id,
            models_per_stage=models_per_stage,
            force_reexec=force_reexec,
            task_id=task_id,
            isolate_provider=isolate_provider,
        )
        resultado = await executor.gerar_relatorio_desempenho_tarefa(
            atividade_id=atividade_id,
            provider_id=model_id or provider_id,
        )
        if resultado.get("sucesso"):
            complete_pipeline_task(task_id, "completed", result=resultado)
        else:
            complete_pipeline_task(task_id, "failed", error=resultado.get("erro"))
    except Exception as e:
        complete_pipeline_task(task_id, "failed", error=str(e))


@router.post("/api/executar/pipeline-desempenho-turma", tags=["Execução"])
async def executar_pipeline_desempenho_turma(
    background_tasks: BackgroundTasks,
    turma_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
    models_per_stage: Optional[str] = Form(None),
    phase_models: Optional[str] = Form(None),
    force_reexec: bool = Form(False),
    etapas_selecionadas: Optional[str] = Form(None),
    isolate_provider: bool = Form(False),
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

    model_ref = model_id or provider_id
    models_stage_map = _parse_models_per_stage(
        models_per_stage=models_per_stage,
        phase_models=phase_models,
    )
    materia = storage.get_materia(turma.materia_id) if turma else None
    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_turma",
        atividade_id=turma_id,
        aluno_ids=[],
        turma_id=turma_id,
        turma_nome=turma.nome,
        materia_nome=materia.nome if materia else None,
    )

    _start_detached_task(
        _executar_desempenho_turma_background,
        task_id=task_id,
        turma_id=turma_id,
        model_id=model_ref,
        provider_id=provider_id,
        models_per_stage=models_stage_map,
        force_reexec=force_reexec,
        isolate_provider=isolate_provider,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_turma_background(
    task_id: str,
    turma_id: str,
    model_id: Optional[str],
    provider_id: Optional[str],
    models_per_stage: Optional[Dict[str, str]],
    force_reexec: bool = False,
    isolate_provider: bool = False,
):
    from executor import executor
    from routes_tasks import task_registry, PIPELINE_STAGES
    try:
        # Pre-populate students in task_registry so the UI progress panel
        # can show names from the first poll, before the cascade has touched
        # any aluno yet.
        try:
            alunos = storage.listar_alunos(turma_id) or []
            task = task_registry.get(task_id)
            if task is not None:
                students = task.setdefault("students", {})
                for aluno in alunos:
                    if aluno.id not in students:
                        students[aluno.id] = {
                            "nome": aluno.nome or "",
                            "stages": {s: "pending" for s in PIPELINE_STAGES},
                            "stage_errors": {},
                        }
        except Exception:
            pass  # progress pre-population is best-effort; cascade still works

        await executor._cascade_prereqs(
            level="turma",
            entity_id=turma_id,
            provider_id=model_id or provider_id,
            models_per_stage=models_per_stage,
            force_reexec=force_reexec,
            task_id=task_id,
            isolate_provider=isolate_provider,
        )
        resultado = await executor.gerar_relatorio_desempenho_turma(
            turma_id=turma_id,
            provider_id=model_id or provider_id,
        )
        if resultado.get("sucesso"):
            complete_pipeline_task(task_id, "completed", result=resultado)
        else:
            complete_pipeline_task(task_id, "failed", error=resultado.get("erro"))
    except Exception as e:
        complete_pipeline_task(task_id, "failed", error=str(e))


@router.post("/api/executar/pipeline-desempenho-materia", tags=["Execução"])
async def executar_pipeline_desempenho_materia(
    background_tasks: BackgroundTasks,
    materia_id: str = Form(...),
    model_id: Optional[str] = Form(None),
    provider_id: Optional[str] = Form(None),
    models_per_stage: Optional[str] = Form(None),
    phase_models: Optional[str] = Form(None),
    force_reexec: bool = Form(False),
    etapas_selecionadas: Optional[str] = Form(None),
    isolate_provider: bool = Form(False),
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

    model_ref = model_id or provider_id
    models_stage_map = _parse_models_per_stage(
        models_per_stage=models_per_stage,
        phase_models=phase_models,
    )
    task_id = register_pipeline_task(
        task_type="pipeline_desempenho_materia",
        atividade_id=materia_id,
        aluno_ids=[],
        materia_id=materia_id,
        materia_nome=materia.nome,
    )

    _start_detached_task(
        _executar_desempenho_materia_background,
        task_id=task_id,
        materia_id=materia_id,
        model_id=model_ref,
        provider_id=provider_id,
        models_per_stage=models_stage_map,
        force_reexec=force_reexec,
        isolate_provider=isolate_provider,
    )

    return {"task_id": task_id, "status": "started"}


async def _executar_desempenho_materia_background(
    task_id: str,
    materia_id: str,
    model_id: Optional[str],
    provider_id: Optional[str],
    models_per_stage: Optional[Dict[str, str]],
    force_reexec: bool = False,
    isolate_provider: bool = False,
):
    from executor import executor
    try:
        await executor._cascade_prereqs(
            level="materia",
            entity_id=materia_id,
            provider_id=model_id or provider_id,
            models_per_stage=models_per_stage,
            force_reexec=force_reexec,
            task_id=task_id,
            isolate_provider=isolate_provider,
        )
        resultado = await executor.gerar_relatorio_desempenho_materia(
            materia_id=materia_id,
            provider_id=model_id or provider_id,
        )
        if resultado.get("sucesso"):
            complete_pipeline_task(task_id, "completed", result=resultado)
        else:
            complete_pipeline_task(task_id, "failed", error=resultado.get("erro"))
    except Exception as e:
        complete_pipeline_task(task_id, "failed", error=str(e))


# ============================================================
# SYNCHRONOUS DESEMPENHO ENDPOINTS (avoid background task loss on Render)
# ============================================================

@router.post("/api/executar/desempenho-tarefa-sync", tags=["Execução"])
async def executar_desempenho_tarefa_sync(
    atividade_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """Synchronous desempenho tarefa — awaits result instead of background task."""
    from executor import executor
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    resultado = await executor.gerar_relatorio_desempenho_tarefa(
        atividade_id=atividade_id, provider_id=provider_id,
    )
    return resultado


@router.post("/api/executar/desempenho-turma-sync", tags=["Execução"])
async def executar_desempenho_turma_sync(
    turma_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """Synchronous desempenho turma — awaits result instead of background task."""
    from executor import executor
    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")
    resultado = await executor.gerar_relatorio_desempenho_turma(
        turma_id=turma_id, provider_id=provider_id,
    )
    return resultado


@router.post("/api/executar/desempenho-materia-sync", tags=["Execução"])
async def executar_desempenho_materia_sync(
    materia_id: str = Form(...),
    provider_id: Optional[str] = Form(None),
):
    """Synchronous desempenho materia — awaits result instead of background task."""
    from executor import executor
    materia = storage.get_materia(materia_id)
    if not materia:
        raise HTTPException(404, "Matéria não encontrada")
    resultado = await executor.gerar_relatorio_desempenho_materia(
        materia_id=materia_id, provider_id=provider_id,
    )
    return resultado
