"""
PROVA AI - Rotas de Visualização de Resultados

Endpoints para:
- Ver resultado detalhado de um aluno
- Comparar questões (gabarito vs resposta vs correção)
- Ranking da turma
- Estatísticas agregadas
- Histórico do aluno
- Exportação de resultados
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Optional

from visualizador import VisualizadorResultados, visualizador
from storage import storage


router = APIRouter()


# ============================================================
# RESULTADO DO ALUNO
# ============================================================

@router.get("/api/resultados/{atividade_id}/{aluno_id}", tags=["Resultados"])
async def get_resultado_aluno(atividade_id: str, aluno_id: str):
    """
    Retorna resultado completo de um aluno em uma atividade.
    Inclui nota, questões detalhadas, habilidades e feedback.
    
    Se não houver resultado final, retorna resultados parciais (status do pipeline).
    """
    from models import TipoDocumento
    import json
    from pathlib import Path
    
    resultado = visualizador.get_resultado_aluno(atividade_id, aluno_id)
    
    if resultado:
        return {
            "sucesso": True,
            "completo": True,
            "resultado": resultado.to_dict()
        }
    
    # Sem resultado final - retornar status parcial do pipeline
    # Buscar documentos disponíveis para mostrar progresso
    docs_aluno = storage.listar_documentos(atividade_id, aluno_id)
    docs_base = storage.listar_documentos(atividade_id)  # Docs da atividade (gabarito, etc)
    
    # Definir etapas do pipeline e verificar quais foram concluídas
    etapas = {
        "enunciado": {"nome": "📄 Enunciado", "completa": False, "doc_id": None},
        "gabarito": {"nome": "✅ Gabarito", "completa": False, "doc_id": None},
        "extracao_questoes": {"nome": "🔍 Extração de Questões", "completa": False, "doc_id": None},
        "prova_respondida": {"nome": "📝 Prova do Aluno", "completa": False, "doc_id": None},
        "extracao_respostas": {"nome": "📋 Extração de Respostas", "completa": False, "doc_id": None},
        "correcao": {"nome": "✏️ Correção", "completa": False, "doc_id": None},
        "analise_habilidades": {"nome": "📊 Análise de Habilidades", "completa": False, "doc_id": None},
        "relatorio_final": {"nome": "📑 Relatório Final", "completa": False, "doc_id": None},
    }
    
    # Verificar documentos base da atividade
    for doc in docs_base:
        tipo = doc.tipo.value if hasattr(doc.tipo, 'value') else str(doc.tipo)
        if tipo in etapas:
            etapas[tipo]["completa"] = True
            etapas[tipo]["doc_id"] = doc.id
    
    # Verificar documentos do aluno
    for doc in docs_aluno:
        tipo = doc.tipo.value if hasattr(doc.tipo, 'value') else str(doc.tipo)
        if tipo in etapas:
            etapas[tipo]["completa"] = True
            etapas[tipo]["doc_id"] = doc.id
    
    # Calcular progresso
    total_etapas = len(etapas)
    etapas_completas = sum(1 for e in etapas.values() if e["completa"])
    progresso = round(etapas_completas / total_etapas * 100)
    
    # Tentar ler dados parciais (ex: nota parcial de uma correção incompleta)
    dados_parciais = {}
    for tipo in ["correcao", "analise_habilidades"]:
        if etapas[tipo]["doc_id"]:
            doc = storage.get_documento(etapas[tipo]["doc_id"])
            if doc and doc.extensao == ".json":
                try:
                    arquivo_path = storage.resolver_caminho_documento(doc)
                    if arquivo_path.exists():
                        with open(arquivo_path, 'r', encoding='utf-8') as f:
                            dados_parciais[tipo] = json.load(f)
                    else:
                        # File doesn't exist - mark as unavailable
                        dados_parciais[tipo] = {"_error": "arquivo_nao_encontrado", "_caminho": str(arquivo_path)}
                except Exception as e:
                    # File exists but can't be read
                    dados_parciais[tipo] = {"_error": "erro_leitura", "_mensagem": str(e)}
    
    return {
        "sucesso": True,
        "completo": False,
        "progresso": progresso,
        "etapas": etapas,
        "dados_parciais": dados_parciais,
        "documentos_disponiveis": [
            {
                "id": d.id,
                "tipo": d.tipo.value if hasattr(d.tipo, 'value') else str(d.tipo),
                "nome": d.nome_arquivo,
                "extensao": d.extensao
            }
            for d in docs_aluno + [d for d in docs_base if not d.aluno_id]
        ],
        "mensagem": f"Pipeline em progresso: {etapas_completas}/{total_etapas} etapas concluídas"
    }


@router.get("/api/resultados/{atividade_id}/{aluno_id}/questao/{numero}", tags=["Resultados"])
async def get_comparativo_questao(atividade_id: str, aluno_id: str, numero: int):
    """
    Retorna comparativo detalhado de uma questão específica.
    Mostra lado a lado: enunciado, gabarito, resposta do aluno, correção.
    """
    comparativo = visualizador.get_comparativo_questao(atividade_id, aluno_id, numero)
    
    return {
        "sucesso": True,
        "comparativo": comparativo
    }


# ============================================================
# RANKING E ESTATÍSTICAS
# ============================================================

@router.get("/api/resultados/{atividade_id}/ranking", tags=["Resultados"])
async def get_ranking_turma(atividade_id: str):
    """
    Retorna ranking dos alunos em uma atividade.
    Ordenado por nota (maior para menor).
    """
    ranking = visualizador.get_ranking_turma(atividade_id)
    
    return {
        "sucesso": True,
        "atividade_id": atividade_id,
        "total": len(ranking),
        "ranking": ranking
    }


@router.get("/api/resultados/{atividade_id}/estatisticas", tags=["Resultados"])
async def get_estatisticas_atividade(atividade_id: str):
    """
    Retorna estatísticas agregadas de uma atividade.
    Inclui média, mediana, distribuição de notas, etc.
    """
    atividade = storage.get_atividade(atividade_id)
    if not atividade:
        raise HTTPException(404, "Atividade não encontrada")
    
    stats = visualizador.get_estatisticas_atividade(atividade_id)
    
    return {
        "sucesso": True,
        "atividade": {
            "id": atividade.id,
            "nome": atividade.nome,
            "nota_maxima": atividade.nota_maxima
        },
        **stats
    }


# ============================================================
# HISTÓRICO DO ALUNO
# ============================================================

@router.get("/api/alunos/{aluno_id}/historico", tags=["Resultados"])
async def get_historico_aluno(aluno_id: str):
    """
    Retorna histórico de todas as atividades de um aluno.
    Inclui notas de todas as matérias e turmas.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    historico = visualizador.get_historico_aluno(aluno_id)
    
    # Calcular estatísticas gerais
    notas = [h["nota"] for h in historico if h["nota"] is not None]
    media_geral = sum(notas) / len(notas) if notas else None
    
    return {
        "sucesso": True,
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula
        },
        "estatisticas": {
            "total_atividades": len(historico),
            "corrigidas": len(notas),
            "media_geral": round(media_geral, 2) if media_geral else None
        },
        "historico": historico
    }


# ============================================================
# EXPORTAÇÃO
# ============================================================

@router.get("/api/resultados/{atividade_id}/{aluno_id}/exportar/json", tags=["Exportação"])
async def exportar_json(atividade_id: str, aluno_id: str):
    """Exporta resultado em formato JSON"""
    json_str = visualizador.exportar_resultado_json(atividade_id, aluno_id)
    return JSONResponse(content={"dados": json_str})


@router.get("/api/resultados/{atividade_id}/{aluno_id}/exportar/markdown", tags=["Exportação"])
async def exportar_markdown(atividade_id: str, aluno_id: str):
    """Exporta resultado em formato Markdown"""
    md = visualizador.exportar_resultado_markdown(atividade_id, aluno_id)
    return PlainTextResponse(content=md, media_type="text/markdown")


@router.get("/api/resultados/{atividade_id}/{aluno_id}/exportar/pdf", tags=["Exportação"])
async def exportar_pdf(atividade_id: str, aluno_id: str):
    """Exporta resultado completo em formato PDF"""
    from fastapi.responses import Response
    from document_generators import generate_pdf

    # Buscar dados do resultado
    resultado = visualizador.get_resultado_aluno(atividade_id, aluno_id)
    if not resultado:
        raise HTTPException(404, "Resultado não encontrado")

    # Converter para dict
    resultado_dict = resultado.to_dict() if hasattr(resultado, 'to_dict') else resultado.__dict__

    # Buscar info do aluno e atividade para o título
    aluno = storage.get_aluno(aluno_id)
    atividade = storage.get_atividade(atividade_id)

    titulo = f"Relatório - {aluno.nome if aluno else aluno_id}"
    if atividade:
        titulo = f"{atividade.nome} - {titulo}"

    try:
        pdf_bytes = generate_pdf(resultado_dict, titulo, "relatorio_final")

        # Nome do arquivo para download
        nome_arquivo = f"relatorio_{atividade_id}_{aluno_id}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{nome_arquivo}"'
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Erro ao gerar PDF: {str(e)}")


@router.get("/api/resultados/{atividade_id}/exportar/ranking-csv", tags=["Exportação"])
async def exportar_ranking_csv(atividade_id: str):
    """Exporta ranking da turma em CSV"""
    ranking = visualizador.get_ranking_turma(atividade_id)
    
    # Gerar CSV
    linhas = ["posicao,aluno,nota,nota_maxima,percentual,corrigido"]
    for r in ranking:
        nota = r["nota"] if r["nota"] is not None else ""
        perc = f'{r["percentual"]:.1f}' if r["percentual"] is not None else ""
        linhas.append(f'{r["posicao"]},{r["aluno_nome"]},{nota},{r["nota_maxima"]},{perc},{r["corrigido"]}')
    
    csv_content = "\n".join(linhas)
    
    return PlainTextResponse(content=csv_content, media_type="text/csv")


# ============================================================
# DASHBOARD DE RESULTADOS
# ============================================================

@router.get("/api/dashboard/turma/{turma_id}", tags=["Dashboard"])
async def dashboard_turma(turma_id: str):
    """
    Dashboard completo de uma turma.
    Inclui estatísticas de todas as atividades.
    """
    turma = storage.get_turma(turma_id)
    if not turma:
        raise HTTPException(404, "Turma não encontrada")
    
    materia = storage.get_materia(turma.materia_id)
    alunos = storage.listar_alunos(turma_id)
    atividades = storage.listar_atividades(turma_id)
    
    # Estatísticas por atividade
    atividades_stats = []
    for ativ in atividades:
        stats = visualizador.get_estatisticas_atividade(ativ.id)
        atividades_stats.append({
            "id": ativ.id,
            "nome": ativ.nome,
            "tipo": ativ.tipo,
            "nota_maxima": ativ.nota_maxima,
            "corrigidos": stats["corrigidos"],
            "pendentes": stats["pendentes"],
            "media": stats["estatisticas"]["media"] if stats["estatisticas"] else None
        })
    
    # Calcular médias por aluno
    alunos_medias = []
    for aluno in alunos:
        notas = []
        for ativ in atividades:
            resultado = visualizador.get_resultado_aluno(ativ.id, aluno.id)
            if resultado:
                notas.append(resultado.nota_final)
        
        media = sum(notas) / len(notas) if notas else None
        alunos_medias.append({
            "aluno_id": aluno.id,
            "aluno_nome": aluno.nome,
            "atividades_corrigidas": len(notas),
            "media": round(media, 2) if media else None
        })
    
    # Ordenar por média
    alunos_medias.sort(key=lambda x: -(x["media"] or 0))
    
    return {
        "turma": {
            "id": turma.id,
            "nome": turma.nome,
            "ano_letivo": turma.ano_letivo
        },
        "materia": materia.nome if materia else None,
        "resumo": {
            "total_alunos": len(alunos),
            "total_atividades": len(atividades)
        },
        "atividades": atividades_stats,
        "alunos": alunos_medias
    }


@router.get("/api/dashboard/aluno/{aluno_id}", tags=["Dashboard"])
async def dashboard_aluno(aluno_id: str):
    """
    Dashboard completo de um aluno.
    Inclui desempenho em todas as matérias.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    turmas = storage.get_turmas_do_aluno(aluno_id)
    historico = visualizador.get_historico_aluno(aluno_id)
    
    # Agrupar por matéria
    por_materia = {}
    for h in historico:
        materia = h["materia"]
        if materia not in por_materia:
            por_materia[materia] = {
                "materia": materia,
                "atividades": [],
                "notas": []
            }
        por_materia[materia]["atividades"].append(h)
        if h["nota"] is not None:
            por_materia[materia]["notas"].append(h["nota"])
    
    # Calcular médias por matéria
    materias_stats = []
    for materia, dados in por_materia.items():
        notas = dados["notas"]
        materias_stats.append({
            "materia": materia,
            "total_atividades": len(dados["atividades"]),
            "corrigidas": len(notas),
            "media": round(sum(notas) / len(notas), 2) if notas else None
        })
    
    # Média geral
    todas_notas = [h["nota"] for h in historico if h["nota"] is not None]
    media_geral = sum(todas_notas) / len(todas_notas) if todas_notas else None
    
    return {
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula
        },
        "resumo": {
            "total_turmas": len(turmas),
            "total_atividades": len(historico),
            "atividades_corrigidas": len(todas_notas),
            "media_geral": round(media_geral, 2) if media_geral else None
        },
        "por_materia": materias_stats,
        "historico_recente": historico[:10]  # Últimas 10
    }


# ============================================================
# FASE 8: FILTROS AVANÇADOS POR ALUNO
# ============================================================

@router.get("/api/alunos/{aluno_id}/turmas-detalhado", tags=["Filtros Aluno"])
async def get_turmas_aluno_detalhado(aluno_id: str):
    """
    Retorna todas as turmas de um aluno com detalhes completos.
    Inclui caso de aluno repetente em múltiplas turmas da mesma matéria.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    turmas_info = storage.get_turmas_do_aluno(aluno_id, apenas_ativas=False)
    
    # Agrupar por matéria para detectar repetência
    por_materia = {}
    for t in turmas_info:
        materia = t["materia_nome"]
        if materia not in por_materia:
            por_materia[materia] = []
        por_materia[materia].append(t)
    
    # Identificar repetências
    resultado = []
    for materia, turmas_mat in por_materia.items():
        is_repetente = len(turmas_mat) > 1
        
        for t in turmas_mat:
            turma = storage.get_turma(t["id"])
            atividades = storage.listar_atividades(t["id"]) if turma else []
            
            # Contar atividades corrigidas
            atividades_corrigidas = 0
            notas = []
            for ativ in atividades:
                resultado_ativ = visualizador.get_resultado_aluno(ativ.id, aluno_id)
                if resultado_ativ:
                    atividades_corrigidas += 1
                    notas.append(resultado_ativ.nota_final)
            
            media = sum(notas) / len(notas) if notas else None
            
            resultado.append({
                "materia": materia,
                "turma_id": t["id"],
                "turma_nome": t["nome"],
                "ano_letivo": t.get("ano_letivo"),
                "is_repetente": is_repetente,
                "observacoes": t.get("observacoes"),
                "data_entrada": t.get("data_entrada"),
                "total_atividades": len(atividades),
                "atividades_corrigidas": atividades_corrigidas,
                "media": round(media, 2) if media else None
            })
    
    # Ordenar por matéria, depois por ano letivo
    resultado.sort(key=lambda x: (x["materia"], -(x["ano_letivo"] or 0)))
    
    return {
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome,
            "matricula": aluno.matricula
        },
        "total_turmas": len(resultado),
        "materias_repetidas": [m for m, ts in por_materia.items() if len(ts) > 1],
        "turmas": resultado
    }


@router.get("/api/alunos/{aluno_id}/atividades-pendentes", tags=["Filtros Aluno"])
async def get_atividades_pendentes_aluno(aluno_id: str):
    """
    Retorna todas as atividades pendentes de correção para um aluno.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    turmas = storage.get_turmas_do_aluno(aluno_id)
    pendentes = []
    
    for turma_info in turmas:
        turma = storage.get_turma(turma_info["id"])
        if not turma:
            continue
        
        materia = storage.get_materia(turma.materia_id)
        atividades = storage.listar_atividades(turma.id)
        
        for ativ in atividades:
            # Verificar se tem prova mas não tem correção
            docs = storage.listar_documentos(ativ.id, aluno_id)
            tem_prova = any(d.tipo == TipoDocumento.PROVA_RESPONDIDA for d in docs)
            tem_correcao = any(d.tipo == TipoDocumento.CORRECAO for d in docs)
            
            if tem_prova and not tem_correcao:
                pendentes.append({
                    "atividade_id": ativ.id,
                    "atividade_nome": ativ.nome,
                    "materia": materia.nome if materia else "?",
                    "turma": turma.nome,
                    "tipo": ativ.tipo,
                    "status": "aguardando_correcao"
                })
            elif not tem_prova:
                pendentes.append({
                    "atividade_id": ativ.id,
                    "atividade_nome": ativ.nome,
                    "materia": materia.nome if materia else "?",
                    "turma": turma.nome,
                    "tipo": ativ.tipo,
                    "status": "sem_prova"
                })
    
    return {
        "aluno": aluno.nome,
        "total_pendentes": len(pendentes),
        "aguardando_correcao": len([p for p in pendentes if p["status"] == "aguardando_correcao"]),
        "sem_prova": len([p for p in pendentes if p["status"] == "sem_prova"]),
        "pendentes": pendentes
    }


@router.get("/api/alunos/{aluno_id}/comparativo-turmas", tags=["Filtros Aluno"])
async def get_comparativo_turmas_aluno(aluno_id: str, materia_id: Optional[str] = None):
    """
    Compara desempenho do aluno entre diferentes turmas.
    Útil para ver evolução de aluno repetente.
    """
    aluno = storage.get_aluno(aluno_id)
    if not aluno:
        raise HTTPException(404, "Aluno não encontrado")
    
    turmas = storage.get_turmas_do_aluno(aluno_id)
    
    comparativo = []
    for turma_info in turmas:
        turma = storage.get_turma(turma_info["id"])
        if not turma:
            continue
        
        # Filtrar por matéria se especificado
        if materia_id and turma.materia_id != materia_id:
            continue
        
        materia = storage.get_materia(turma.materia_id)
        atividades = storage.listar_atividades(turma.id)
        
        notas = []
        for ativ in atividades:
            resultado = visualizador.get_resultado_aluno(ativ.id, aluno_id)
            if resultado:
                notas.append({
                    "atividade": ativ.nome,
                    "nota": resultado.nota_final,
                    "percentual": resultado.percentual
                })
        
        media = sum(n["nota"] for n in notas) / len(notas) if notas else None
        media_percentual = sum(n["percentual"] for n in notas) / len(notas) if notas else None
        
        comparativo.append({
            "materia": materia.nome if materia else "?",
            "turma_id": turma.id,
            "turma": turma.nome,
            "ano_letivo": turma.ano_letivo,
            "total_atividades": len(atividades),
            "atividades_corrigidas": len(notas),
            "media": round(media, 2) if media else None,
            "media_percentual": round(media_percentual, 1) if media_percentual else None,
            "notas": notas
        })
    
    # Ordenar por matéria e ano
    comparativo.sort(key=lambda x: (x["materia"], x["ano_letivo"] or 0))
    
    return {
        "aluno": {
            "id": aluno.id,
            "nome": aluno.nome
        },
        "comparativo": comparativo
    }


# Importar TipoDocumento para os filtros
from models import TipoDocumento
