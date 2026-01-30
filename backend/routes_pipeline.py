"""
PROVA AI - Rotas Pipeline v2.2

Endpoints para:
- Executar pipeline com envio NATIVO de arquivos
- Verificar se anexos foram recebidos pela IA
- Download de arquivos gerados
- Chat com documentos
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import json
import mimetypes

from storage import storage
from models import TipoDocumento


router = APIRouter()


# ============================================================
# HELPER: DETECÇÃO DE MIME TYPE
# ============================================================

MIME_TYPES = {
    # Visualizáveis inline
    '.pdf': 'application/pdf',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.json': 'application/json',
    '.csv': 'text/csv',
    '.xml': 'application/xml',
    # Office (download)
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.doc': 'application/msword',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xls': 'application/vnd.ms-excel',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    # Código comum
    '.py': 'text/x-python',
    '.js': 'text/javascript',
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.cs': 'text/x-csharp',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.rb': 'text/x-ruby',
    '.php': 'text/x-php',
    '.sql': 'text/x-sql',
    '.r': 'text/x-r',
    '.m': 'text/x-matlab',
    '.sh': 'text/x-shellscript',
    # Archives
    '.zip': 'application/zip',
}


def get_mime_type(file_path: Path) -> str:
    """Detecta o MIME type baseado na extensão do arquivo"""
    ext = file_path.suffix.lower()
    if ext in MIME_TYPES:
        return MIME_TYPES[ext]
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'


# ============================================================
# MODELOS
# ============================================================

class ExecutarEtapaRequest(BaseModel):
    atividade_id: str
    aluno_id: Optional[str] = None
    provider_id: Optional[str] = None
    etapa: str


class ChatComDocumentosRequest(BaseModel):
    mensagem: str
    atividade_id: Optional[str] = None
    aluno_id: Optional[str] = None
    model_id: Optional[str] = None  # Novo sistema de modelos
    provider_id: Optional[str] = None  # Legado
    documentos_ids: Optional[List[str]] = None


# ============================================================
# PIPELINE
# ============================================================

@router.post("/api/pipeline/executar", tags=["Pipeline"])
async def executar_etapa(data: ExecutarEtapaRequest):
    """
    [LEGACY - CONSIDER UNIFICATION] Executa uma etapa do pipeline.
    Os arquivos são enviados NATIVAMENTE para a IA.

    ⚠️  UNIFICATION CANDIDATE: Multiple pipeline execution endpoints exist:
    - /api/pipeline/executar (this - single step)
    - /api/executar/etapa (routes_prompts.py - single step with chat service)
    - /api/executar/pipeline-completo (routes_prompts.py - full pipeline for one student)
    - /api/executar/pipeline-turma (routes_prompts.py - full pipeline for all students)

    POTENTIAL ERRORS from unification:
    - Different request/response formats
    - Inconsistent error handling
    - Different authentication/authorization
    - Race conditions when executing multiple students simultaneously
    - Resource exhaustion from parallel processing
    """
    from executor import pipeline_executor
    
    etapa = data.etapa.lower()
    
    try:
        if etapa == "extrair_questoes":
            resultado = await pipeline_executor.extrair_questoes(
                atividade_id=data.atividade_id,
                provider_id=data.provider_id
            )
        
        elif etapa == "extrair_respostas":
            if not data.aluno_id:
                raise HTTPException(400, "aluno_id é obrigatório")
            resultado = await pipeline_executor.extrair_respostas_aluno(
                atividade_id=data.atividade_id,
                aluno_id=data.aluno_id,
                provider_id=data.provider_id
            )
        
        elif etapa == "corrigir":
            if not data.aluno_id:
                raise HTTPException(400, "aluno_id é obrigatório")
            resultado = await pipeline_executor.corrigir(
                atividade_id=data.atividade_id,
                aluno_id=data.aluno_id,
                provider_id=data.provider_id
            )
        
        else:
            raise HTTPException(400, f"Etapa desconhecida: {etapa}")
        
        return {"sucesso": resultado.sucesso, "etapa": resultado.etapa, "resultado": resultado.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/api/pipeline/status/{atividade_id}", tags=["Pipeline"])
async def status_pipeline(atividade_id: str, aluno_id: Optional[str] = None):
    """Retorna status do pipeline"""
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    
    docs_base = storage.listar_documentos(atividade_id)
    
    status_base = {
        "enunciado": any(d.tipo == TipoDocumento.ENUNCIADO for d in docs_base),
        "gabarito": any(d.tipo == TipoDocumento.GABARITO for d in docs_base),
        "questoes_extraidas": any(d.tipo == TipoDocumento.EXTRACAO_QUESTOES for d in docs_base)
    }
    
    status_aluno = None
    if aluno_id:
        docs_aluno = storage.listar_documentos(atividade_id, aluno_id)
        status_aluno = {
            "prova": any(d.tipo == TipoDocumento.PROVA_RESPONDIDA for d in docs_aluno),
            "respostas_extraidas": any(d.tipo == TipoDocumento.EXTRACAO_RESPOSTAS for d in docs_aluno),
            "correcao": any(d.tipo == TipoDocumento.CORRECAO for d in docs_aluno)
        }
    
    return {"atividade_id": atividade_id, "status_base": status_base, "status_aluno": status_aluno}


# ============================================================
# DOWNLOAD E VISUALIZAÇÃO
# ============================================================

@router.get("/api/documentos/{documento_id}/download", tags=["Documentos"])
async def download_documento(documento_id: str):
    """
    [LEGACY - CONSIDER UNIFICATION] Download de documento com MIME type correto

    ⚠️  UNIFICATION CANDIDATE: Multiple document access endpoints exist:
    - /api/documentos/{id}/download (this)
    - /api/documentos/{id}/view (below)
    - /api/documentos/{id}/visualizar (below)
    - /api/documentos/{id}/conteudo (routes_prompts.py)

    POTENTIAL ERRORS from unification:
    - Different response types (FileResponse vs JSON content)
    - MIME type detection inconsistencies
    - File not found handling differences
    - Security implications of exposing different access methods
    """
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")

    arquivo = storage.resolver_caminho_documento(documento)
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado")

    mime_type = get_mime_type(arquivo)
    return FileResponse(arquivo, filename=documento.nome_arquivo, media_type=mime_type)


@router.get("/api/documentos/{documento_id}/view", tags=["Documentos"])
async def view_documento(documento_id: str):
    """
    [LEGACY - CONSIDER UNIFICATION] Visualiza documento inline no navegador (PDFs, imagens, HTML)

    ⚠️  UNIFICATION CANDIDATE: See /api/documentos/{id}/download for details
    """
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")

    arquivo = storage.resolver_caminho_documento(documento)
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado")

    mime_type = get_mime_type(arquivo)

    # Tipos que podem ser visualizados inline
    inline_types = ['application/pdf', 'image/', 'text/html', 'text/plain']
    can_inline = any(mime_type.startswith(t) for t in inline_types)

    if can_inline:
        return FileResponse(
            arquivo,
            media_type=mime_type,
            headers={"Content-Disposition": f"inline; filename=\"{documento.nome_arquivo}\""}
        )
    else:
        return FileResponse(arquivo, filename=documento.nome_arquivo, media_type=mime_type)


@router.get("/api/documentos/{documento_id}/visualizar", tags=["Documentos"])
async def visualizar_documento(documento_id: str):
    """
    [LEGACY - CONSIDER UNIFICATION] Visualiza conteúdo de documento JSON/texto

    ⚠️  UNIFICATION CANDIDATE: See /api/documentos/{id}/download for details
    """
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    arquivo = storage.resolver_caminho_documento(documento)
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo não encontrado")
    
    conteudo = None
    if documento.extensao.lower() == '.json':
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
        except:
            pass
    elif documento.extensao.lower() in ['.txt', '.md', '.csv', '.py']:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
        except:
            pass
    
    return {"documento": documento.to_dict(), "conteudo": conteudo}


# ============================================================
# CHAT COM DOCUMENTOS
# ============================================================

@router.post("/api/chat/com-documentos", tags=["Chat"])
async def chat_com_documentos(data: ChatComDocumentosRequest):
    """Chat com documentos anexados nativamente"""
    from executor import pipeline_executor
    
    arquivos = []
    
    if data.documentos_ids:
        for doc_id in data.documentos_ids:
            doc = storage.get_documento(doc_id)
            if doc and Path(doc.caminho_arquivo).exists():
                arquivos.append(doc.caminho_arquivo)
    elif data.atividade_id:
        docs = storage.listar_documentos(data.atividade_id, data.aluno_id)
        for doc in docs[:5]:
            if Path(doc.caminho_arquivo).exists():
                arquivos.append(doc.caminho_arquivo)
    
    try:
        resultado = await pipeline_executor.chat_com_documentos(
            mensagem=data.mensagem,
            arquivos=arquivos,
            provider_id=data.model_id or data.provider_id  # Prioriza model_id
        )
        
        return {
            "sucesso": resultado.sucesso,
            "resposta": resultado.resposta,
            "provider": resultado.provider,
            "modelo": resultado.modelo,
            "anexos_enviados": resultado.anexos_enviados,
            "anexos_confirmados": resultado.anexos_confirmados,
            "erro": resultado.erro
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================
# ALERTAS E INFO
# ============================================================

@router.get("/api/atividades/{atividade_id}/alertas", tags=["Alertas"])
async def listar_alertas(atividade_id: str, aluno_id: Optional[str] = None):
    """Lista alertas de uma atividade"""
    alertas = []
    docs = storage.listar_documentos(atividade_id, aluno_id)
    
    for doc in docs:
        if doc.extensao.lower() == '.json':
            try:
                with open(doc.caminho_arquivo, 'r') as f:
                    data = json.load(f)
                    for alerta in data.get("alertas", []):
                        alertas.append({"origem": doc.tipo.value, "documento_id": doc.id, **alerta})
            except:
                pass
    
    return {"alertas": alertas, "total": len(alertas)}


@router.get("/api/providers/disponiveis", tags=["Providers"])
async def listar_providers():
    """
    [LEGACY - DUPLICATE ENDPOINT] Lista providers configurados

    ⚠️  DUPLICATE: This endpoint exists in routes_prompts.py with enhanced functionality.
    Consider unifying with /api/providers/disponiveis in routes_prompts.py

    POTENTIAL ERRORS from unification:
    - Different return format (this returns simple list, routes_prompts.py returns with defaults)
    - Missing error handling for no providers configured
    - No fallback to old ai_providers system
    """
    from chat_service import model_manager
    models = model_manager.listar(apenas_ativos=True)
    return {"providers": [{"id": m.id, "nome": m.nome, "tipo": m.tipo.value, "modelo": m.modelo} for m in models]}


@router.get("/api/formatos-suportados", tags=["Info"])
async def formatos_suportados():
    """Lista formatos de arquivo suportados"""
    from anexos import FORMATOS_BINARIOS, FORMATOS_TEXTO, FORMATOS_ESPECIAIS
    return {
        "binarios": list(FORMATOS_BINARIOS.keys()),
        "texto": list(FORMATOS_TEXTO.keys()),
        "especiais": list(FORMATOS_ESPECIAIS.keys())
    }


# ============================================================
# GERAÇÃO DE DOCUMENTOS VIA TOOLS
# ============================================================

class GerarRelatoriosRequest(BaseModel):
    atividade_id: str
    turma_id: Optional[str] = None
    aluno_id: Optional[str] = None
    provider_id: Optional[str] = None
    tipo_relatorio: str = "individual"  # "individual", "turma", "consolidado"


@router.post("/api/pipeline/gerar-relatorios", tags=["Pipeline"])
async def gerar_relatorios(data: GerarRelatoriosRequest):
    """
    Gera relatórios usando a ferramenta create_document.
    
    O modelo pode criar múltiplos documentos:
    - Relatórios individuais por aluno
    - Relatório consolidado da turma
    - Feedback personalizado
    """
    from executor import pipeline_executor
    
    try:
        if data.tipo_relatorio == "turma" and data.turma_id:
            # Gerar relatórios para toda a turma
            resultado = await pipeline_executor.gerar_relatorios_turma(
                atividade_id=data.atividade_id,
                turma_id=data.turma_id,
                provider_id=data.provider_id
            )
            return resultado
        
        elif data.aluno_id:
            # Gerar relatório individual
            aluno = storage.get_aluno(data.aluno_id)
            docs = storage.listar_documentos(data.atividade_id, data.aluno_id)
            
            # Buscar dados de correção
            correcao_doc = next((d for d in docs if d.tipo == TipoDocumento.CORRECAO), None)
            if not correcao_doc:
                raise HTTPException(400, "Correção não encontrada para o aluno")
            
            with open(correcao_doc.caminho_arquivo, 'r', encoding='utf-8') as f:
                correcao_data = json.load(f)
            
            prompt = f"""Gere um relatório detalhado para o aluno.

ALUNO: {aluno.nome if aluno else data.aluno_id}

DADOS DA CORREÇÃO:
{json.dumps(correcao_data, ensure_ascii=False, indent=2)}

Use a ferramenta create_document para criar o relatório em formato Markdown.
Inclua:
- Resumo do desempenho
- Nota e percentual
- Análise por questão
- Pontos fortes e áreas de melhoria
- Feedback construtivo
"""
            
            resultado = await pipeline_executor.executar_com_tools(
                mensagem=prompt,
                atividade_id=data.atividade_id,
                aluno_id=data.aluno_id,
                provider_id=data.provider_id,
                tools_to_use=["create_document"]
            )
            
            return {
                "sucesso": resultado.sucesso,
                "resultado": resultado.to_dict()
            }
        
        else:
            raise HTTPException(400, "Especifique aluno_id ou turma_id")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


class ExecutarComToolsRequest(BaseModel):
    mensagem: str
    atividade_id: str
    aluno_id: Optional[str] = None
    provider_id: Optional[str] = None
    tools: Optional[List[str]] = None  # ["create_document", "execute_python_code"]


@router.post("/api/pipeline/executar-com-tools", tags=["Pipeline"])
async def executar_com_tools(data: ExecutarComToolsRequest):
    """
    Executa um prompt com suporte a tools.
    
    O modelo pode usar ferramentas como:
    - create_document: Criar um ou múltiplos documentos
    - execute_python_code: Executar código Python
    """
    from executor import pipeline_executor
    
    try:
        resultado = await pipeline_executor.executar_com_tools(
            mensagem=data.mensagem,
            atividade_id=data.atividade_id,
            aluno_id=data.aluno_id,
            provider_id=data.provider_id,
            tools_to_use=data.tools
        )
        
        return {
            "sucesso": resultado.sucesso,
            "resultado": resultado.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(500, str(e))


# ============================================================
# DOCUMENT FORMAT REGENERATION
# ============================================================

class RegenerarFormatoRequest(BaseModel):
    titulo: Optional[str] = None


@router.get("/api/documentos/{documento_id}/formatos-disponiveis", tags=["Documentos"])
async def formatos_disponiveis(documento_id: str):
    """
    Lista formatos disponíveis para regeneração de um documento.
    Apenas documentos JSON podem ser regenerados em outros formatos.
    """
    from document_generators import OutputFormat, get_output_formats
    
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    # Só documentos JSON podem ser regenerados
    if documento.extensao.lower() != '.json':
        return {
            "documento_id": documento_id,
            "tipo": documento.tipo.value if hasattr(documento.tipo, 'value') else str(documento.tipo),
            "pode_regenerar": False,
            "motivo": "Apenas documentos JSON podem ser regenerados",
            "formatos_disponiveis": []
        }
    
    # Mapear tipo do documento para formatos sugeridos
    tipo_str = documento.tipo.value if hasattr(documento.tipo, 'value') else str(documento.tipo)
    formatos = get_output_formats(tipo_str)
    
    return {
        "documento_id": documento_id,
        "tipo": tipo_str,
        "pode_regenerar": True,
        "formatos_disponiveis": [
            {"formato": f.value, "extensao": f".{f.value}"} 
            for f in formatos if f != OutputFormat.JSON
        ],
        "todos_formatos": [
            {"formato": "pdf", "extensao": ".pdf"},
            {"formato": "csv", "extensao": ".csv"},
            {"formato": "docx", "extensao": ".docx"},
            {"formato": "md", "extensao": ".md"},
        ]
    }


@router.post("/api/documentos/{documento_id}/regenerar/{formato}", tags=["Documentos"])
async def regenerar_documento(documento_id: str, formato: str, data: Optional[RegenerarFormatoRequest] = None):
    """
    Regenera um documento JSON em outro formato (PDF, CSV, DOCX, MD).
    
    O documento original JSON é preservado. Um novo documento é criado
    no formato solicitado e salvo junto ao original.
    """
    from document_generators import (
        generate_document, OutputFormat, get_file_extension
    )
    import tempfile
    import os
    
    # Validar formato
    try:
        output_format = OutputFormat(formato.lower())
    except ValueError:
        raise HTTPException(400, f"Formato inválido: {formato}. Use: pdf, csv, docx, md")
    
    # Buscar documento original
    documento = storage.get_documento(documento_id)
    if not documento:
        raise HTTPException(404, "Documento não encontrado")
    
    # Verificar se é JSON
    if documento.extensao.lower() != '.json':
        raise HTTPException(400, "Apenas documentos JSON podem ser regenerados")
    
    # Ler dados do JSON
    arquivo = storage.resolver_caminho_documento(documento)
    if not arquivo.exists():
        raise HTTPException(404, "Arquivo JSON não encontrado")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        raise HTTPException(500, f"Erro ao ler JSON: {e}")
    
    # Determinar tipo do documento e título
    tipo_str = documento.tipo.value if hasattr(documento.tipo, 'value') else str(documento.tipo)
    titulo = data.titulo if data and data.titulo else f"{tipo_str.replace('_', ' ').title()}"
    
    # Gerar documento no novo formato
    try:
        content = generate_document(json_data, output_format, titulo, tipo_str)
    except Exception as e:
        raise HTTPException(500, f"Erro ao gerar {formato}: {e}")
    
    # Salvar arquivo
    extensao = get_file_extension(output_format)
    nome_base = documento.nome_arquivo.rsplit('.', 1)[0]
    novo_nome = f"{nome_base}{extensao}"
    
    # Criar arquivo temporário e salvar via storage
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extensao, mode='wb' if isinstance(content, bytes) else 'w', encoding=None if isinstance(content, bytes) else 'utf-8') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Salvar no storage com mesmo contexto do original
        novo_doc = storage.salvar_documento(
            arquivo_origem=tmp_path,
            tipo=documento.tipo,
            atividade_id=documento.atividade_id,
            aluno_id=documento.aluno_id,
            criado_por="sistema"
        )
        
        # Limpar temp
        os.unlink(tmp_path)
        
        return {
            "sucesso": True,
            "documento_original": documento_id,
            "novo_documento": {
                "id": novo_doc.id,
                "nome": novo_doc.nome_arquivo,
                "formato": formato,
                "caminho": novo_doc.caminho_arquivo
            },
            "url_download": f"/api/documentos/{novo_doc.id}/download",
            "url_view": f"/api/documentos/{novo_doc.id}/view"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Erro ao salvar documento: {e}")


# ============================================================
# ENDPOINTS PARA DOWNLOAD DE RESULTADOS
# ============================================================

@router.get("/api/pipeline/{atividade_id}/resultados/json", tags=["Pipeline"])
async def download_resultados_json(atividade_id: str, aluno_id: str = None):
    """
    Baixa todos os resultados JSON de uma atividade.
    Se aluno_id fornecido, retorna apenas daquele aluno.

    Útil para revisar o que a pipeline gerou e depurar problemas.
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")

    documentos = storage.listar_documentos(atividade_id, aluno_id)

    resultados = {}
    for doc in documentos:
        if doc.extensao == ".json":
            arquivo = storage.resolver_caminho_documento(doc)
            if arquivo.exists():
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        resultados[doc.tipo.value] = {
                            "documento_id": doc.id,
                            "aluno_id": doc.aluno_id,
                            "conteudo": json.load(f),
                            "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
                            "ia_provider": doc.ia_provider,
                            "ia_modelo": doc.ia_modelo
                        }
                except Exception as e:
                    resultados[doc.tipo.value] = {
                        "documento_id": doc.id,
                        "erro": str(e)
                    }

    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "resultados": resultados,
        "total_documentos": len(resultados)
    }


@router.get("/api/pipeline/{atividade_id}/texto-extraido", tags=["Pipeline"])
async def get_texto_extraido(atividade_id: str, aluno_id: str = None):
    """
    Retorna o texto extraído de todos os documentos processados.
    Útil para revisar o que a IA entendeu dos PDFs/imagens.

    Retorna dados de:
    - extracao_questoes: questões extraídas do enunciado
    - extracao_gabarito: gabarito extraído
    - extracao_respostas: respostas extraídas da prova do aluno
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")

    docs = storage.listar_documentos(atividade_id, aluno_id)

    tipos_extracao = ["extracao_questoes", "extracao_respostas", "extracao_gabarito"]
    textos = {}

    for doc in docs:
        if doc.tipo.value in tipos_extracao:
            arquivo = storage.resolver_caminho_documento(doc)
            if arquivo.exists():
                try:
                    with open(arquivo, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        textos[doc.tipo.value] = {
                            "documento_id": doc.id,
                            "aluno_id": doc.aluno_id,
                            "questoes": dados.get("questoes", []),
                            "texto_original": dados.get("texto_original", ""),
                            "total_questoes": len(dados.get("questoes", []))
                        }
                except Exception as e:
                    textos[doc.tipo.value] = {
                        "documento_id": doc.id,
                        "erro": str(e)
                    }

    return {
        "atividade_id": atividade_id,
        "aluno_id": aluno_id,
        "textos": textos,
        "tipos_encontrados": list(textos.keys())
    }
