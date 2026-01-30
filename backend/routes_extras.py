"""
PROVA AI - Endpoints Adicionais v2.0

Este arquivo contém endpoints extras que são importados pelo main_v2.py:
- Operações em lote (importar alunos, upload múltiplo)
- Busca e filtros avançados
- Estatísticas e relatórios
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import tempfile
import os
import csv
import io
from pathlib import Path

from models import TipoDocumento
from storage import storage


# Router para endpoints adicionais
router = APIRouter()


# ============================================================
# MODELOS
# ============================================================

class AlunoImport(BaseModel):
    nome: str
    email: Optional[str] = None
    matricula: Optional[str] = None

class ImportarAlunosRequest(BaseModel):
    alunos: List[AlunoImport]
    turma_id: Optional[str] = None  # Se fornecido, já vincula

class BuscaRequest(BaseModel):
    termo: str
    tipo: Optional[str] = None  # "aluno", "materia", "turma", "atividade"


# ============================================================
# IMPORTAÇÃO EM LOTE: ALUNOS
# ============================================================

@router.post("/api/alunos/importar", tags=["Lote"])
async def importar_alunos(data: ImportarAlunosRequest):
    """
    Importa múltiplos alunos de uma vez.
    Opcionalmente já vincula todos a uma turma.
    """
    criados = []
    erros = []
    
    for aluno_data in data.alunos:
        try:
            aluno = storage.criar_aluno(
                nome=aluno_data.nome,
                email=aluno_data.email,
                matricula=aluno_data.matricula
            )
            criados.append(aluno.to_dict())
            
            # Vincular à turma se especificado
            if data.turma_id:
                storage.vincular_aluno_turma(aluno.id, data.turma_id)
                
        except Exception as e:
            erros.append({"aluno": aluno_data.nome, "erro": str(e)})
    
    return {
        "success": True,
        "criados": len(criados),
        "erros": len(erros),
        "alunos": criados,
        "detalhes_erros": erros
    }


@router.post("/api/alunos/importar-csv", tags=["Lote"])
async def importar_alunos_csv(
    file: UploadFile = File(...),
    turma_id: Optional[str] = Form(None)
):
    """
    Importa alunos de um arquivo CSV.
    
    Formato esperado do CSV:
    nome,email,matricula
    João Silva,joao@email.com,2024001
    Maria Santos,maria@email.com,2024002
    
    A primeira linha (cabeçalho) é ignorada.
    """
    content = await file.read()
    
    try:
        # Decodificar CSV
        text = content.decode('utf-8-sig')  # utf-8-sig remove BOM se existir
        reader = csv.DictReader(io.StringIO(text))
        
        criados = []
        erros = []
        
        for row in reader:
            nome = row.get('nome', '').strip()
            if not nome:
                continue
                
            email = row.get('email', '').strip() or None
            matricula = row.get('matricula', '').strip() or None
            
            try:
                aluno = storage.criar_aluno(nome, email, matricula)
                criados.append(aluno.to_dict())
                
                if turma_id:
                    storage.vincular_aluno_turma(aluno.id, turma_id)
                    
            except Exception as e:
                erros.append({"nome": nome, "erro": str(e)})
        
        return {
            "success": True,
            "arquivo": file.filename,
            "criados": len(criados),
            "erros": len(erros),
            "alunos": criados,
            "detalhes_erros": erros
        }
        
    except Exception as e:
        raise HTTPException(400, f"Erro ao processar CSV: {str(e)}")


@router.post("/api/alunos/vincular-lote", tags=["Lote"])
async def vincular_alunos_lote(
    turma_id: str = Form(...),
    aluno_ids: str = Form(...)  # IDs separados por vírgula
):
    """Vincula múltiplos alunos a uma turma de uma vez"""
    ids = [id.strip() for id in aluno_ids.split(',') if id.strip()]
    
    sucesso = []
    erros = []
    
    for aluno_id in ids:
        try:
            vinculo = storage.vincular_aluno_turma(aluno_id, turma_id)
            if vinculo:
                sucesso.append(aluno_id)
            else:
                erros.append({"aluno_id": aluno_id, "erro": "Já vinculado ou não encontrado"})
        except Exception as e:
            erros.append({"aluno_id": aluno_id, "erro": str(e)})
    
    return {
        "success": True,
        "vinculados": len(sucesso),
        "erros": len(erros),
        "detalhes_erros": erros
    }


# ============================================================
# UPLOAD EM LOTE: DOCUMENTOS
# ============================================================

@router.post("/api/documentos/upload-lote", tags=["Lote"])
async def upload_documentos_lote(
    files: List[UploadFile] = File(...),
    tipo: str = Form(...),
    atividade_id: str = Form(...),
    aluno_id: Optional[str] = Form(None)
):
    """
    Upload de múltiplos documentos de uma vez.
    Útil para subir várias provas de alunos.
    """
    try:
        tipo_doc = TipoDocumento(tipo)
    except ValueError:
        raise HTTPException(400, f"Tipo inválido: {tipo}")
    
    salvos = []
    erros = []
    
    for file in files:
        try:
            # Salvar temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            # Salvar documento
            documento = storage.salvar_documento(
                arquivo_origem=tmp_path,
                tipo=tipo_doc,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                criado_por="usuario"
            )
            
            os.unlink(tmp_path)
            
            if documento:
                salvos.append(documento.to_dict())
            else:
                erros.append({"arquivo": file.filename, "erro": "Falha ao salvar"})
                
        except Exception as e:
            erros.append({"arquivo": file.filename, "erro": str(e)})
    
    return {
        "success": True,
        "salvos": len(salvos),
        "erros": len(erros),
        "documentos": salvos,
        "detalhes_erros": erros
    }


@router.post("/api/documentos/upload-provas-alunos", tags=["Lote"])
async def upload_provas_alunos(
    files: List[UploadFile] = File(...),
    atividade_id: str = Form(...),
    modo_nome: str = Form("matricula")  # "matricula" ou "nome"
):
    """
    Upload inteligente de provas de alunos.
    
    O nome do arquivo deve conter a matrícula ou nome do aluno.
    Exemplos:
    - 2024001_prova.pdf → busca aluno com matrícula 2024001
    - joao_silva_prova.pdf → busca aluno com nome "joao silva"
    
    modo_nome: "matricula" ou "nome"
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    
    turma = storage.get_turma(atividade.turma_id)
    alunos_turma = storage.listar_alunos(turma.id)
    
    salvos = []
    erros = []
    
    for file in files:
        try:
            # Extrair identificador do nome do arquivo
            nome_arquivo = Path(file.filename).stem.lower()
            
            # Buscar aluno
            aluno_encontrado = None
            
            if modo_nome == "matricula":
                # Procura matrícula no nome do arquivo
                for aluno in alunos_turma:
                    if aluno.matricula and aluno.matricula.lower() in nome_arquivo:
                        aluno_encontrado = aluno
                        break
            else:
                # Procura nome no arquivo
                for aluno in alunos_turma:
                    nome_normalizado = aluno.nome.lower().replace(" ", "_")
                    if nome_normalizado in nome_arquivo or nome_arquivo in nome_normalizado:
                        aluno_encontrado = aluno
                        break
            
            if not aluno_encontrado:
                erros.append({
                    "arquivo": file.filename,
                    "erro": f"Aluno não encontrado. Nome do arquivo: {nome_arquivo}"
                })
                continue
            
            # Salvar temporário
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            # Salvar documento
            documento = storage.salvar_documento(
                arquivo_origem=tmp_path,
                tipo=TipoDocumento.PROVA_RESPONDIDA,
                atividade_id=atividade_id,
                aluno_id=aluno_encontrado.id,
                criado_por="usuario"
            )
            
            os.unlink(tmp_path)
            
            if documento:
                salvos.append({
                    "documento": documento.to_dict(),
                    "aluno": aluno_encontrado.nome
                })
            else:
                erros.append({"arquivo": file.filename, "erro": "Falha ao salvar"})
                
        except Exception as e:
            erros.append({"arquivo": file.filename, "erro": str(e)})
    
    return {
        "success": True,
        "salvos": len(salvos),
        "erros": len(erros),
        "documentos": salvos,
        "detalhes_erros": erros,
        "dica": "Certifique-se que o nome do arquivo contém a matrícula ou nome do aluno"
    }


# ============================================================
# BUSCA GLOBAL
# ============================================================

@router.get("/api/busca", tags=["Busca"])
async def busca_global(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo: aluno, materia, turma, atividade")
):
    """
    Busca global em todo o sistema.
    Retorna resultados organizados por tipo.
    """
    termo = q.lower()
    resultados = {
        "alunos": [],
        "materias": [],
        "turmas": [],
        "atividades": []
    }
    
    # Buscar alunos
    if not tipo or tipo == "aluno":
        for aluno in storage.listar_alunos():
            if termo in aluno.nome.lower() or (aluno.matricula and termo in aluno.matricula.lower()):
                resultados["alunos"].append({
                    "id": aluno.id,
                    "nome": aluno.nome,
                    "matricula": aluno.matricula,
                    "tipo": "aluno"
                })
    
    # Buscar matérias
    if not tipo or tipo == "materia":
        for materia in storage.listar_materias():
            if termo in materia.nome.lower():
                resultados["materias"].append({
                    "id": materia.id,
                    "nome": materia.nome,
                    "tipo": "materia"
                })
    
    # Buscar turmas
    if not tipo or tipo == "turma":
        for turma in storage.listar_turmas():
            if termo in turma.nome.lower():
                materia = storage.get_materia(turma.materia_id)
                resultados["turmas"].append({
                    "id": turma.id,
                    "nome": turma.nome,
                    "materia": materia.nome if materia else None,
                    "tipo": "turma"
                })
    
    # Buscar atividades
    if not tipo or tipo == "atividade":
        for turma in storage.listar_turmas():
            for atividade in storage.listar_atividades(turma.id):
                if termo in atividade.nome.lower():
                    resultados["atividades"].append({
                        "id": atividade.id,
                        "nome": atividade.nome,
                        "turma": turma.nome,
                        "tipo": "atividade"
                    })
    
    total = sum(len(v) for v in resultados.values())
    
    return {
        "termo": q,
        "total": total,
        "resultados": resultados
    }


# ============================================================
# ESTATÍSTICAS
# ============================================================

@router.get("/api/estatisticas", tags=["Estatísticas"])
async def get_estatisticas_gerais():
    """Retorna estatísticas gerais do sistema"""
    
    materias = storage.listar_materias()
    turmas = storage.listar_turmas()
    alunos = storage.listar_alunos()
    
    total_atividades = 0
    total_documentos = 0
    atividades_sem_gabarito = 0
    
    for turma in turmas:
        atividades = storage.listar_atividades(turma.id)
        total_atividades += len(atividades)
        
        for ativ in atividades:
            docs = storage.listar_documentos(ativ.id)
            total_documentos += len(docs)
            
            tipos = [d.tipo for d in docs]
            if TipoDocumento.GABARITO not in tipos:
                atividades_sem_gabarito += 1
    
    return {
        "total_materias": len(materias),
        "total_turmas": len(turmas),
        "total_alunos": len(alunos),
        "total_atividades": total_atividades,
        "total_documentos": total_documentos,
        "alertas": {
            "atividades_sem_gabarito": atividades_sem_gabarito
        }
    }


@router.get("/api/estatisticas/turma/{turma_id}", tags=["Estatísticas"])
async def get_estatisticas_turma(turma_id: str):
    """Retorna estatísticas de uma turma específica"""
    
    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")
    
    alunos = storage.listar_alunos(turma_id)
    atividades = storage.listar_atividades(turma_id)
    
    stats_atividades = []
    for ativ in atividades:
        status = storage.get_status_atividade(ativ.id)
        stats_atividades.append({
            "id": ativ.id,
            "nome": ativ.nome,
            "alunos_com_prova": status["alunos"]["com_prova"],
            "alunos_corrigidos": status["alunos"]["corrigidos"],
            "docs_faltando": status["documentos_base"]["faltando"]
        })
    
    return {
        "turma": turma.to_dict(),
        "total_alunos": len(alunos),
        "total_atividades": len(atividades),
        "atividades": stats_atividades
    }


# ============================================================
# EXPORTAÇÃO
# ============================================================

@router.get("/api/exportar/alunos-csv", tags=["Exportação"])
async def exportar_alunos_csv(turma_id: Optional[str] = None):
    """Exporta lista de alunos em CSV"""
    
    alunos = storage.listar_alunos(turma_id)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["nome", "email", "matricula", "id"])
    
    for aluno in alunos:
        writer.writerow([aluno.nome, aluno.email or "", aluno.matricula or "", aluno.id])
    
    content = output.getvalue()
    
    return {
        "csv": content,
        "total": len(alunos),
        "dica": "Cole este conteúdo em um arquivo .csv"
    }


# ============================================================
# DUPLICAÇÃO / CÓPIA
# ============================================================

@router.post("/api/atividades/{atividade_id}/duplicar", tags=["Utilitários"])
async def duplicar_atividade(
    atividade_id: str,
    nova_turma_id: str = Form(...),
    novo_nome: Optional[str] = Form(None)
):
    """
    Duplica uma atividade para outra turma.
    Copia os documentos base (enunciado, gabarito, critérios).
    """
    atividade_original = storage.get_atividade(atividade_id)
    if not atividade_original:
        raise HTTPException(404, "Atividade não encontrada")
    
    # Criar nova atividade
    nova_atividade = storage.criar_atividade(
        turma_id=nova_turma_id,
        nome=novo_nome or f"{atividade_original.nome} (cópia)",
        tipo=atividade_original.tipo,
        nota_maxima=atividade_original.nota_maxima,
        descricao=atividade_original.descricao
    )
    
    if not nova_atividade:
        raise HTTPException(400, "Turma destino não encontrada")
    
    # Copiar documentos base
    docs_copiados = 0
    docs_originais = storage.listar_documentos(atividade_id)
    
    for doc in docs_originais:
        if doc.is_documento_base and Path(doc.caminho_arquivo).exists():
            try:
                novo_doc = storage.salvar_documento(
                    arquivo_origem=doc.caminho_arquivo,
                    tipo=doc.tipo,
                    atividade_id=nova_atividade.id,
                    criado_por="sistema_copia"
                )
                if novo_doc:
                    docs_copiados += 1
            except:
                pass
    
    return {
        "success": True,
        "atividade_original": atividade_id,
        "nova_atividade": nova_atividade.to_dict(),
        "documentos_copiados": docs_copiados
    }
# ============================================================
# ENDPOINT: DOCUMENTOS PARA CHAT
# ============================================================

@router.get("/api/documentos/todos", tags=["Chat"])
async def listar_todos_documentos(
    materia_ids: Optional[str] = None,
    turma_ids: Optional[str] = None,
    atividade_ids: Optional[str] = None,
    aluno_ids: Optional[str] = None,
    tipos: Optional[str] = None
):
    """Lista todos os documentos do sistema com metadados completos."""
    filters = {
        'materia_ids': materia_ids.split(',') if materia_ids else None,
        'turma_ids': turma_ids.split(',') if turma_ids else None,
        'atividade_ids': atividade_ids.split(',') if atividade_ids else None,
        'aluno_ids': aluno_ids.split(',') if aluno_ids else None,
        'tipos': tipos.split(',') if tipos else None,
    }
    
    documentos = []
    materias = storage.listar_materias()
    
    for materia in materias:
        if filters['materia_ids'] and materia.id not in filters['materia_ids']:
            continue
        
        turmas = storage.listar_turmas(materia.id)
        for turma in turmas:
            if filters['turma_ids'] and turma.id not in filters['turma_ids']:
                continue
            
            atividades = storage.listar_atividades(turma.id)
            for atividade in atividades:
                if filters['atividade_ids'] and atividade.id not in filters['atividade_ids']:
                    continue
                
                docs = storage.listar_documentos(atividade.id)
                for doc in docs:
                    if filters['tipos'] and doc.tipo.value not in filters['tipos']:
                        continue
                    if filters['aluno_ids'] and doc.aluno_id and doc.aluno_id not in filters['aluno_ids']:
                        continue
                    
                    aluno_nome = None
                    if doc.aluno_id:
                        aluno = storage.get_aluno(doc.aluno_id)
                        aluno_nome = aluno.nome if aluno else None
                    
                    documentos.append({
                        "id": doc.id,
                        "nome_arquivo": doc.nome_arquivo,
                        "tipo": doc.tipo.value,
                        "materia_id": materia.id,
                        "materia_nome": materia.nome,
                        "turma_id": turma.id,
                        "turma_nome": turma.nome,
                        "atividade_id": atividade.id,
                        "atividade_nome": atividade.nome,
                        "aluno_id": doc.aluno_id,
                        "aluno_nome": aluno_nome,
                        "criado_em": doc.criado_em.isoformat() if doc.criado_em else None,
                    })
    
    return {"documentos": documentos, "total": len(documentos)}


@router.get("/api/chat/providers", tags=["Chat"])
async def listar_chat_providers():
    """Lista providers disponíveis para o chat."""
    from ai_providers import ai_registry
    return {
        "providers": ai_registry.get_provider_info(),
        "default": ai_registry.default_provider
    }


@router.get("/api/debug/documento/{documento_id}", tags=["Debug"])
async def debug_documento(documento_id: str):
    """Diagnóstico completo de um documento - verifica DB, arquivo local e Supabase"""
    from supabase_storage import supabase_storage

    result = {
        "documento_id": documento_id,
        "etapas": {}
    }

    # 1. Verificar se existe no banco
    doc = storage.get_documento(documento_id)
    result["etapas"]["1_banco_dados"] = {
        "encontrado": doc is not None,
        "nome_arquivo": doc.nome_arquivo if doc else None,
        "caminho": doc.caminho_arquivo if doc else None,
        "extensao": doc.extensao if doc else None
    }

    if not doc:
        result["erro"] = "Documento não encontrado no banco de dados"
        return result

    # 2. Verificar arquivo local
    from pathlib import Path
    caminho_direto = Path(doc.caminho_arquivo)
    caminho_base = storage.base_path / doc.caminho_arquivo
    caminho_sem_data = storage.base_path / doc.caminho_arquivo.replace("data/", "").replace("data\\", "")

    result["etapas"]["2_arquivo_local"] = {
        "caminho_direto_existe": caminho_direto.exists(),
        "caminho_base_existe": caminho_base.exists(),
        "caminho_sem_data_existe": caminho_sem_data.exists(),
        "base_path": str(storage.base_path)
    }

    # 3. Verificar Supabase
    result["etapas"]["3_supabase"] = {
        "habilitado": supabase_storage.enabled if supabase_storage else False,
        "url": supabase_storage.url[:50] + "..." if supabase_storage and supabase_storage.url else None
    }

    # 4. Tentar resolver caminho
    try:
        arquivo_resolvido = storage.resolver_caminho_documento(doc)
        result["etapas"]["4_resolver_caminho"] = {
            "sucesso": arquivo_resolvido is not None and arquivo_resolvido.exists(),
            "caminho_resolvido": str(arquivo_resolvido) if arquivo_resolvido else None,
            "existe": arquivo_resolvido.exists() if arquivo_resolvido else False
        }
    except Exception as e:
        result["etapas"]["4_resolver_caminho"] = {
            "sucesso": False,
            "erro": str(e)
        }

    return result


# ============================================================
# SINCRONIZAÇÃO COM SERVIDOR REMOTO
# ============================================================

@router.post("/api/sync/test-connection", tags=["Sync"])
async def test_remote_connection():
    """Testa conexão com o servidor remoto"""
    from sync_service import sync_service

    try:
        # Tentar fazer uma requisição simples
        import requests
        response = requests.get(f"{sync_service.remote_base_url}/docs", timeout=10)
        return {
            "success": True,
            "remote_url": sync_service.remote_base_url,
            "status_code": response.status_code,
            "message": "Conexão estabelecida com sucesso"
        }
    except Exception as e:
        raise HTTPException(500, f"Falha na conexão: {str(e)}")


@router.post("/api/sync/atividade/{atividade_id}", tags=["Sync"])
async def sync_atividade_to_remote(atividade_id: str):
    """Sincroniza uma atividade completa para o servidor remoto"""
    from sync_service import sync_service

    try:
        result = sync_service.sync_atividade_completa(atividade_id, storage)
        return {
            "success": True,
            "message": "Atividade sincronizada com sucesso",
            "data": result
        }
    except Exception as e:
        raise HTTPException(500, f"Erro na sincronização: {str(e)}")


@router.post("/api/sync/materia/{materia_id}", tags=["Sync"])
async def sync_materia_to_remote(materia_id: str):
    """Sincroniza uma matéria para o servidor remoto"""
    from sync_service import sync_service

    try:
        materia = storage.get_materia(materia_id)
        if not materia:
            raise HTTPException(404, "Matéria não encontrada")

        materia_data = {
            "nome": materia.nome,
            "descricao": materia.descricao,
            "nivel": materia.nivel.value if hasattr(materia.nivel, 'value') else str(materia.nivel)
        }

        result = sync_service.sync_materia(materia_data)
        return {
            "success": True,
            "message": "Matéria sincronizada com sucesso",
            "remote_materia": result
        }
    except Exception as e:
        raise HTTPException(500, f"Erro na sincronização: {str(e)}")


@router.post("/api/sync/turma/{turma_id}", tags=["Sync"])
async def sync_turma_to_remote(turma_id: str):
    """Sincroniza uma turma para o servidor remoto"""
    from sync_service import sync_service

    try:
        turma = storage.get_turma(turma_id)
        if not turma:
            raise HTTPException(404, "Turma não encontrada")

        # Buscar matéria relacionada
        materia = storage.get_materia(turma.materia_id)
        if not materia:
            raise HTTPException(404, "Matéria da turma não encontrada")

        # Verificar se a matéria já existe remotamente
        try:
            remote_materias = sync_service._make_request("GET", "/api/materias")
            remote_materia_id = None
            for m in remote_materias.get("materias", []):
                if m["nome"] == materia.nome:
                    remote_materia_id = m["id"]
                    break

            if not remote_materia_id:
                raise HTTPException(400, "Matéria não encontrada no servidor remoto. Sincronize a matéria primeiro.")

        except Exception as e:
            raise HTTPException(500, f"Erro ao buscar matéria remota: {str(e)}")

        turma_data = {
            "materia_id": remote_materia_id,
            "nome": turma.nome,
            "ano_letivo": turma.ano_letivo,
            "periodo": turma.periodo,
            "descricao": turma.descricao
        }

        result = sync_service.sync_turma(turma_data)
        return {
            "success": True,
            "message": "Turma sincronizada com sucesso",
            "remote_turma": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Erro na sincronização: {str(e)}")


@router.post("/api/sync/documentos", tags=["Sync"])
async def sync_documentos_to_remote(documento_ids: List[str]):
    """Sincroniza múltiplos documentos para o servidor remoto"""
    from sync_service import sync_service

    results = []
    errors = []

    for doc_id in documento_ids:
        try:
            documento = storage.get_documento(doc_id)
            if not documento:
                errors.append(f"Documento {doc_id} não encontrado")
                continue

            # Preparar metadados
            metadata = {
                "nome_arquivo": documento.nome_arquivo,
                "atividade_id": documento.atividade_id,
                "aluno_id": documento.aluno_id,
                "tipo": documento.tipo.value if hasattr(documento.tipo, 'value') else str(documento.tipo)
            }

            # Sincronizar
            result = sync_service.sync_documento(documento.caminho_arquivo, metadata)
            results.append({
                "documento_id": doc_id,
                "remote_documento": result
            })

        except Exception as e:
            errors.append(f"Erro sincronizando {doc_id}: {str(e)}")

    return {
        "success": len(results) > 0,
        "synchronized": results,
        "errors": errors,
        "total_synchronized": len(results),
        "total_errors": len(errors)
    }


@router.get("/api/sync/status", tags=["Sync"])
async def get_sync_status():
    """Verifica status da sincronização e conexão com servidor remoto"""
    from sync_service import sync_service

    status = {
        "local_server": "online",
        "remote_server": {
            "url": sync_service.remote_base_url,
            "status": "unknown"
        },
        "sync_service": "available"
    }

    # Testar conexão remota
    try:
        import requests
        response = requests.get(f"{sync_service.remote_base_url}/docs", timeout=5)
        status["remote_server"]["status"] = "online" if response.status_code == 200 else f"http_{response.status_code}"
    except Exception as e:
        status["remote_server"]["status"] = f"offline: {str(e)[:50]}"

    return status