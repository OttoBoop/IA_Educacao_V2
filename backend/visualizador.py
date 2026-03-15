"""
NOVO CR - Visualização de Resultados v2.0

Sistema para:
- Visualizar resultados de correções
- Comparar respostas (aluno vs gabarito vs correção)
- Gerar relatórios agregados
- Exportar dados
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import logging
import time

from models import TipoDocumento, Documento
from storage import storage


# ============================================================
# WARNING SEVERITY MAPPING (stage + code → color)
# ============================================================
# MISSING_CONTENT is yellow in student-answer stages (student may skip intentionally)
# All other codes are orange in all stages

_YELLOW_MISSING_CONTENT_STAGES = frozenset({
    "EXTRAIR_RESPOSTAS", "CORRIGIR",
    "ANALISAR_HABILIDADES", "GERAR_RELATORIO",
})

_VALID_CODES = frozenset({
    "ILLEGIBLE_DOCUMENT", "ILLEGIBLE_QUESTION",
    "MISSING_CONTENT", "LOW_CONFIDENCE",
})

_VALID_STAGES = frozenset({
    "EXTRAIR_QUESTOES", "EXTRAIR_GABARITO", "EXTRAIR_RESPOSTAS",
    "CORRIGIR", "ANALISAR_HABILIDADES", "GERAR_RELATORIO",
})


def get_warning_severity(stage: str, code: str) -> str | None:
    """Return severity color for a (stage, code) pair.

    Returns "orange", "yellow", or None (unknown stage/code).
    """
    if stage not in _VALID_STAGES or code not in _VALID_CODES:
        return None
    if code == "MISSING_CONTENT" and stage in _YELLOW_MISSING_CONTENT_STAGES:
        return "yellow"
    return "orange"


@dataclass
class VisaoQuestao:
    """Visão consolidada de uma questão corrigida"""
    numero: int
    enunciado: str
    resposta_esperada: str
    resposta_aluno: str
    nota: float
    nota_maxima: float
    percentual: float
    status: str  # correta, parcial, incorreta, em_branco
    feedback: str
    pontos_positivos: List[str] = field(default_factory=list)
    pontos_melhorar: List[str] = field(default_factory=list)


@dataclass
class VisaoAluno:
    """Visão consolidada do desempenho de um aluno"""
    aluno_id: str
    aluno_nome: str
    atividade_id: str
    atividade_nome: str
    
    nota_final: float
    nota_maxima: float
    percentual: float
    
    total_questoes: int
    questoes_corretas: int
    questoes_parciais: int
    questoes_incorretas: int
    questoes_branco: int
    
    questoes: List[VisaoQuestao] = field(default_factory=list)
    
    habilidades_demonstradas: List[str] = field(default_factory=list)
    habilidades_faltantes: List[str] = field(default_factory=list)
    
    recomendacoes: List[str] = field(default_factory=list)
    feedback_geral: str = ""
    
    # Metadados do processamento
    corrigido_em: Optional[datetime] = None
    corrigido_por_ia: str = ""

    # Pipeline error info (when processing failed)
    erro_pipeline: Optional[Dict[str, Any]] = None

    # True when correction JSON had no structured fields (only resposta_raw or empty)
    dados_incompletos: bool = False

    # Warning/aviso fields (populated from _avisos_documento/_avisos_questao in JSON)
    avisos_documento: List[Dict[str, Any]] = field(default_factory=list)
    avisos_questao: List[Dict[str, Any]] = field(default_factory=list)
    _avisos_stage: str = ""  # stage context for severity computation

    # GERAR_RELATORIO lineage (which upstream stages were consumed)
    fontes_utilizadas: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "aluno_id": self.aluno_id,
            "aluno_nome": self.aluno_nome,
            "atividade_id": self.atividade_id,
            "atividade_nome": self.atividade_nome,
            "nota_final": self.nota_final,
            "nota_maxima": self.nota_maxima,
            "percentual": self.percentual,
            "total_questoes": self.total_questoes,
            "questoes_corretas": self.questoes_corretas,
            "questoes_parciais": self.questoes_parciais,
            "questoes_incorretas": self.questoes_incorretas,
            "questoes_branco": self.questoes_branco,
            "questoes": [vars(q) for q in self.questoes],
            "habilidades_demonstradas": self.habilidades_demonstradas,
            "habilidades_faltantes": self.habilidades_faltantes,
            "recomendacoes": self.recomendacoes,
            "feedback_geral": self.feedback_geral,
            "corrigido_em": self.corrigido_em.isoformat() if self.corrigido_em else None,
            "corrigido_por_ia": self.corrigido_por_ia,
            "dados_incompletos": self.dados_incompletos,
            "avisos_documento": [
                {**w, "severidade": get_warning_severity(self._avisos_stage, w.get("codigo", ""))}
                for w in self.avisos_documento
            ],
            "avisos_questao": [
                {**w, "severidade": get_warning_severity(self._avisos_stage, w.get("codigo", ""))}
                for w in self.avisos_questao
            ],
            "fontes_utilizadas": self.fontes_utilizadas,
            **({"erro_pipeline": self.erro_pipeline} if self.erro_pipeline else {})
        }


class VisualizadorResultados:
    """Serviço para visualização de resultados"""
    
    def __init__(self):
        self.storage = storage

    def _safe_float(self, value: Any, default: Optional[float] = None) -> Optional[float]:
        try:
            if value is None or value == "":
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _resumir_correcao(
        self,
        atividade_nota_maxima: float,
        data: Dict[str, Any],
    ) -> Dict[str, Optional[float]]:
        """Extrai um resumo leve da correção sem montar a visão completa."""
        nota_maxima = self._safe_float(atividade_nota_maxima, 0.0) or 0.0

        if not data:
            return {"nota": None, "nota_maxima": nota_maxima, "percentual": None}

        nota = self._safe_float(data.get("nota_final"))
        if nota is None:
            nota = self._safe_float(data.get("nota"))

        correcoes = data.get("correcoes")
        if nota is None and isinstance(correcoes, list):
            nota = 0.0
            nota_max_total = 0.0
            for correcao in correcoes:
                nota += self._safe_float(correcao.get("nota"), 0.0) or 0.0
                nota_max_total += self._safe_float(correcao.get("nota_maxima"), 0.0) or 0.0
            if nota_max_total > 0:
                nota_maxima = nota_max_total

        percentual = None
        if nota is not None and nota_maxima > 0:
            percentual = nota / nota_maxima * 100

        return {"nota": nota, "nota_maxima": nota_maxima, "percentual": percentual}
    
    def get_resultado_aluno(self, atividade_id: str, aluno_id: str) -> Optional[VisaoAluno]:
        """
        Monta visão consolidada do resultado de um aluno.
        Combina dados de correção, análise de habilidades e relatório.
        """
        started_at = time.perf_counter()
        atividade = self.storage.get_atividade(atividade_id)
        aluno = self.storage.get_aluno(aluno_id)
        
        if not atividade or not aluno:
            self.storage._log_hot_endpoint_profile(
                "/api/resultados/{atividade_id}/{aluno_id}",
                started_at,
                {"atividade": 1 if atividade else 0, "aluno": 1 if aluno else 0, "documentos": 0},
            )
            return None
        
        # Buscar documentos do aluno
        documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        
        # Encontrar correção — prefer JSON files over PDFs (pipeline creates both)
        correcao_docs = [d for d in documentos if d.tipo == TipoDocumento.CORRECAO]
        correcao_doc = next(
            (d for d in correcao_docs if d.nome_arquivo and d.nome_arquivo.endswith('.json')),
            next(iter(correcao_docs), None)
        )
        analise_docs = [d for d in documentos if d.tipo == TipoDocumento.ANALISE_HABILIDADES]
        analise_doc = next(
            (d for d in analise_docs if d.nome_arquivo and d.nome_arquivo.endswith('.json')),
            next(iter(analise_docs), None)
        )
        
        if not correcao_doc:
            self.storage._log_hot_endpoint_profile(
                "/api/resultados/{atividade_id}/{aluno_id}",
                started_at,
                {"atividade": 1, "aluno": 1, "documentos": len(documentos)},
                {"json_reads": 0},
            )
            return None
        
        # Ler dados da correção
        correcao_data = self._ler_json(correcao_doc)
        analise_data = self._ler_json(analise_doc) if analise_doc else {}
        json_reads = 1 + (1 if analise_doc else 0)
        
        # Montar visão
        visao = VisaoAluno(
            aluno_id=aluno_id,
            aluno_nome=aluno.nome,
            atividade_id=atividade_id,
            atividade_nome=atividade.nome,
            nota_final=0,
            nota_maxima=atividade.nota_maxima,
            percentual=0,
            total_questoes=0,
            questoes_corretas=0,
            questoes_parciais=0,
            questoes_incorretas=0,
            questoes_branco=0,
            corrigido_em=correcao_doc.criado_em,
            corrigido_por_ia=correcao_doc.ia_provider or ""
        )
        
        # Check for pipeline error in correction data
        if "_erro_pipeline" in correcao_data:
            visao.erro_pipeline = correcao_data["_erro_pipeline"]

        # Processar correção
        self._processar_correcao(visao, correcao_data)

        # Processar análise de habilidades
        self._processar_analise(visao, analise_data)

        self.storage._log_hot_endpoint_profile(
            "/api/resultados/{atividade_id}/{aluno_id}",
            started_at,
            {"atividade": 1, "aluno": 1, "documentos": len(documentos)},
            {"json_reads": json_reads},
        )

        return visao
    
    def _ler_json(self, documento: Documento) -> Dict[str, Any]:
        """Lê conteúdo JSON de um documento"""
        try:
            arquivo = storage.resolver_caminho_documento(documento)
            if arquivo.exists():
                with open(arquivo, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Handle files with extra data after the JSON object
                    # (e.g., two concatenated JSON objects from pipeline)
                    decoder = json.JSONDecoder()
                    obj, _ = decoder.raw_decode(content.lstrip())
                    if isinstance(obj, dict):
                        return obj
        except:
            pass
        return {}
    
    def _processar_correcao(self, visao: VisaoAluno, data: Dict[str, Any]):
        """Processa dados de correção para a visão"""
        # Tentar diferentes formatos de resposta da IA

        # Formato 0: STAGE_TOOL_INSTRUCTIONS format (questoes[] + nota_final)
        if "questoes" in data and "nota_final" in data:
            visao.nota_final = float(data.get("nota_final", 0))
            visao.percentual = (visao.nota_final / visao.nota_maxima * 100) if visao.nota_maxima > 0 else 0
            visao.feedback_geral = data.get("feedback_geral", "")

            questoes = data.get("questoes", [])
            for q in questoes:
                acerto = q.get("acerto", False)
                nota = float(q.get("nota", 0))
                nota_max = float(q.get("nota_maxima", 1))

                # Map acerto bool to status string
                if acerto:
                    status = "correta"
                    visao.questoes_corretas += 1
                else:
                    status = "incorreta"
                    visao.questoes_incorretas += 1

                questao = VisaoQuestao(
                    numero=q.get("numero", len(visao.questoes) + 1),
                    enunciado=q.get("enunciado", ""),
                    resposta_esperada=q.get("resposta_esperada", ""),
                    resposta_aluno=q.get("resposta_aluno", ""),
                    nota=nota,
                    nota_maxima=nota_max,
                    percentual=(nota / nota_max * 100) if nota_max > 0 else 0,
                    status=status,
                    feedback=q.get("feedback", ""),
                    pontos_positivos=q.get("pontos_positivos", []),
                    pontos_melhorar=q.get("pontos_melhorar", []),
                )
                visao.questoes.append(questao)

            visao.total_questoes = len(questoes)

        # Formato 1: Resposta direta com nota
        elif "nota" in data:
            visao.nota_final = float(data.get("nota", 0))
            visao.percentual = (visao.nota_final / visao.nota_maxima * 100) if visao.nota_maxima > 0 else 0
            visao.feedback_geral = data.get("feedback", "")
            
            status = data.get("status", "")
            if status == "correta":
                visao.questoes_corretas = 1
            elif status == "parcial":
                visao.questoes_parciais = 1
            elif status == "incorreta":
                visao.questoes_incorretas = 1
            
            visao.total_questoes = 1
            
            questao = VisaoQuestao(
                numero=1,
                enunciado=data.get("questao", ""),
                resposta_esperada=data.get("resposta_esperada", ""),
                resposta_aluno=data.get("resposta_aluno", ""),
                nota=visao.nota_final,
                nota_maxima=visao.nota_maxima,
                percentual=visao.percentual,
                status=status,
                feedback=visao.feedback_geral,
                pontos_positivos=data.get("pontos_positivos", []),
                pontos_melhorar=data.get("pontos_melhorar", [])
            )
            visao.questoes.append(questao)
        
        # Formato 2: Lista de correções por questão
        elif "correcoes" in data:
            correcoes = data["correcoes"]
            nota_total = 0
            nota_max_total = 0
            
            for c in correcoes:
                nota = float(c.get("nota", 0))
                nota_max = float(c.get("nota_maxima", 1))
                nota_total += nota
                nota_max_total += nota_max
                
                status = c.get("status", "")
                if status == "correta":
                    visao.questoes_corretas += 1
                elif status == "parcial":
                    visao.questoes_parciais += 1
                elif status == "incorreta":
                    visao.questoes_incorretas += 1
                elif status == "em_branco":
                    visao.questoes_branco += 1
                
                questao = VisaoQuestao(
                    numero=c.get("questao_numero", len(visao.questoes) + 1),
                    enunciado=c.get("enunciado", ""),
                    resposta_esperada=c.get("resposta_esperada", ""),
                    resposta_aluno=c.get("resposta_aluno", ""),
                    nota=nota,
                    nota_maxima=nota_max,
                    percentual=(nota / nota_max * 100) if nota_max > 0 else 0,
                    status=status,
                    feedback=c.get("feedback", ""),
                    pontos_positivos=c.get("pontos_positivos", []),
                    pontos_melhorar=c.get("pontos_melhorar", [])
                )
                visao.questoes.append(questao)
            
            visao.total_questoes = len(correcoes)
            visao.nota_final = nota_total
            visao.nota_maxima = nota_max_total if nota_max_total > 0 else visao.nota_maxima
            visao.percentual = (nota_total / nota_max_total * 100) if nota_max_total > 0 else 0
        
        # Formato 3: resposta_raw (texto livre)
        elif "resposta_raw" in data:
            visao.feedback_geral = data["resposta_raw"]
            visao.dados_incompletos = True

        # No recognized format
        else:
            visao.dados_incompletos = True

        # Read warning/aviso fields (present in all formats, added by _avisos schema)
        visao.avisos_documento = data.get("_avisos_documento", [])
        visao.avisos_questao = data.get("_avisos_questao", [])
        visao._avisos_stage = data.get("_avisos_stage", "CORRIGIR")

    def _processar_analise(self, visao: VisaoAluno, data: Dict[str, Any]):
        """Processa análise de habilidades"""
        if not data:
            return

        # Habilidades
        habilidades = data.get("habilidades", {})

        if isinstance(habilidades, dict):
            # Existing format: dict with dominadas/em_desenvolvimento/nao_demonstradas
            dominadas = habilidades.get("dominadas", [])
            em_dev = habilidades.get("em_desenvolvimento", [])
            nao_dem = habilidades.get("nao_demonstradas", [])

            visao.habilidades_demonstradas = [
                h.get("nome", h) if isinstance(h, dict) else h
                for h in dominadas
            ]
            visao.habilidades_faltantes = [
                h.get("nome", h) if isinstance(h, dict) else h
                for h in nao_dem
            ]
        elif isinstance(habilidades, list):
            # STAGE_TOOL_INSTRUCTIONS format: flat list of dicts with nome/nivel/nota
            for h in habilidades:
                nome = h.get("nome", h) if isinstance(h, dict) else h
                nivel = h.get("nivel", "").lower() if isinstance(h, dict) else ""
                if nivel in ("avançado", "avancado", "dominado", "excelente"):
                    visao.habilidades_demonstradas.append(nome)
                elif nivel in ("nao_demonstrado", "ausente", "insuficiente"):
                    visao.habilidades_faltantes.append(nome)
                else:
                    # intermediário or unknown → demonstrated (benefit of doubt)
                    visao.habilidades_demonstradas.append(nome)

        # Recomendações
        visao.recomendacoes = data.get("recomendacoes", [])

        # Feedback geral
        if not visao.feedback_geral:
            visao.feedback_geral = data.get("resumo_desempenho", "")
    
    def get_comparativo_questao(
        self, 
        atividade_id: str, 
        aluno_id: str, 
        numero_questao: int
    ) -> Dict[str, Any]:
        """
        Retorna comparativo detalhado de uma questão específica.
        Mostra lado a lado: enunciado, gabarito, resposta aluno, correção.
        """
        documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        docs_base = self.storage.listar_documentos(atividade_id)
        
        resultado = {
            "numero": numero_questao,
            "enunciado": None,
            "gabarito": None,
            "resposta_aluno": None,
            "correcao": None
        }
        
        # Buscar questões extraídas
        questoes_doc = next((d for d in docs_base if d.tipo == TipoDocumento.EXTRACAO_QUESTOES), None)
        if questoes_doc:
            data = self._ler_json(questoes_doc)
            questoes = data.get("questoes", [])
            questao = next((q for q in questoes if q.get("numero") == numero_questao), None)
            if questao:
                resultado["enunciado"] = questao
        
        # Buscar gabarito
        gabarito_doc = next((d for d in docs_base if d.tipo == TipoDocumento.EXTRACAO_GABARITO), None)
        if gabarito_doc:
            data = self._ler_json(gabarito_doc)
            respostas = data.get("respostas", [])
            resposta = next((r for r in respostas if r.get("questao_numero") == numero_questao), None)
            if resposta:
                resultado["gabarito"] = resposta
        
        # Buscar resposta do aluno
        respostas_doc = next((d for d in documentos if d.tipo == TipoDocumento.EXTRACAO_RESPOSTAS), None)
        if respostas_doc:
            data = self._ler_json(respostas_doc)
            respostas = data.get("respostas", [])
            resposta = next((r for r in respostas if r.get("questao_numero") == numero_questao), None)
            if resposta:
                resultado["resposta_aluno"] = resposta
        
        # Buscar correção
        correcao_doc = next((d for d in documentos if d.tipo == TipoDocumento.CORRECAO), None)
        if correcao_doc:
            data = self._ler_json(correcao_doc)
            
            # Tentar encontrar correção da questão específica
            correcoes = data.get("correcoes", [])
            correcao = next((c for c in correcoes if c.get("questao_numero") == numero_questao), None)
            
            if correcao:
                resultado["correcao"] = correcao
            elif "nota" in data:
                # Correção única
                resultado["correcao"] = data
        
        return resultado
    
    def get_ranking_turma(self, atividade_id: str) -> List[Dict[str, Any]]:
        """
        Retorna ranking dos alunos em uma atividade.
        Ordenado por nota (maior para menor).
        """
        atividade = self.storage.get_atividade(atividade_id)
        if not atividade:
            return []
        
        turma = self.storage.get_turma(atividade.turma_id)
        alunos = self.storage.listar_alunos(turma.id) if turma else []
        
        ranking = []
        
        for aluno in alunos:
            resultado = self.get_resultado_aluno(atividade_id, aluno.id)
            
            if resultado:
                ranking.append({
                    "posicao": 0,  # Será preenchido depois
                    "aluno_id": aluno.id,
                    "aluno_nome": aluno.nome,
                    "nota": resultado.nota_final,
                    "nota_maxima": resultado.nota_maxima,
                    "percentual": resultado.percentual,
                    "questoes_corretas": resultado.questoes_corretas,
                    "total_questoes": resultado.total_questoes,
                    "corrigido": True
                })
            else:
                ranking.append({
                    "posicao": 0,
                    "aluno_id": aluno.id,
                    "aluno_nome": aluno.nome,
                    "nota": None,
                    "nota_maxima": atividade.nota_maxima,
                    "percentual": None,
                    "questoes_corretas": None,
                    "total_questoes": None,
                    "corrigido": False
                })
        
        # Ordenar por nota (corrigidos primeiro, depois por nota decrescente)
        ranking.sort(key=lambda x: (not x["corrigido"], -(x["nota"] or 0)))
        
        # Preencher posições
        for i, item in enumerate(ranking):
            if item["corrigido"]:
                item["posicao"] = i + 1
        
        return ranking
    
    def get_estatisticas_atividade(self, atividade_id: str) -> Dict[str, Any]:
        """
        Retorna estatísticas agregadas de uma atividade.
        """
        ranking = self.get_ranking_turma(atividade_id)
        
        corrigidos = [r for r in ranking if r["corrigido"]]
        
        if not corrigidos:
            return {
                "total_alunos": len(ranking),
                "corrigidos": 0,
                "pendentes": len(ranking),
                "estatisticas": None
            }
        
        notas = [r["nota"] for r in corrigidos]
        
        return {
            "total_alunos": len(ranking),
            "corrigidos": len(corrigidos),
            "pendentes": len(ranking) - len(corrigidos),
            "estatisticas": {
                "media": sum(notas) / len(notas),
                "maior_nota": max(notas),
                "menor_nota": min(notas),
                "mediana": sorted(notas)[len(notas) // 2],
                "aprovados": sum(1 for n in notas if n >= 6),  # Nota >= 6
                "reprovados": sum(1 for n in notas if n < 6),
                "distribuicao": {
                    "0-2": sum(1 for n in notas if 0 <= n < 2),
                    "2-4": sum(1 for n in notas if 2 <= n < 4),
                    "4-6": sum(1 for n in notas if 4 <= n < 6),
                    "6-8": sum(1 for n in notas if 6 <= n < 8),
                    "8-10": sum(1 for n in notas if 8 <= n <= 10)
                }
            }
        }
    
    def get_historico_aluno_fast(
        self,
        aluno_id: str,
        turmas_info: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Retorna histórico agregado do aluno sem N+1 por atividade."""
        started_at = time.perf_counter()
        turmas = turmas_info if turmas_info is not None else self.storage.get_turmas_do_aluno(aluno_id)
        if not turmas:
            self.storage._log_hot_endpoint_profile(
                "/api/dashboard/aluno/{aluno_id}/historico",
                started_at,
                {"turmas": 0, "atividades": 0, "documentos": 0},
                {"json_reads": 0},
            )
            return []

        turma_by_id = {
            turma["id"]: turma
            for turma in turmas
            if turma.get("id")
        }
        turma_ids = list(turma_by_id.keys())
        atividades_rows = self.storage._select_rows(
            "atividades",
            filters={"turma_id": turma_ids},
            columns=["id", "turma_id", "nome", "tipo", "data_aplicacao", "nota_maxima"],
        )

        if not atividades_rows:
            self.storage._log_hot_endpoint_profile(
                "/api/dashboard/aluno/{aluno_id}/historico",
                started_at,
                {"turmas": len(turmas), "atividades": 0, "documentos": 0},
                {"json_reads": 0},
            )
            return []

        activity_ids = [row["id"] for row in atividades_rows if row.get("id")]
        atividades_by_id = {
            row["id"]: row
            for row in atividades_rows
            if row.get("id")
        }
        correction_rows = self.storage._select_rows(
            "documentos",
            filters={
                "atividade_id": activity_ids,
                "aluno_id": aluno_id,
                "tipo": TipoDocumento.CORRECAO.value,
            },
            order_by="criado_em",
            order_desc=True,
        )

        latest_docs: Dict[str, Documento] = {}
        for row in correction_rows:
            atividade_id = row.get("atividade_id")
            if atividade_id and atividade_id not in latest_docs:
                latest_docs[atividade_id] = Documento.from_dict(row)

        summaries: Dict[str, Dict[str, Optional[float]]] = {}
        json_reads = 0
        for atividade_id, documento in latest_docs.items():
            try:
                correction_data = self._ler_json(documento)
                json_reads += 1
                atividade_row = atividades_by_id.get(atividade_id, {})
                summaries[atividade_id] = self._resumir_correcao(
                    atividade_row.get("nota_maxima", 0),
                    correction_data,
                )
            except Exception as exc:
                logging.warning(
                    "[visualizador] Falha ao resumir correção do aluno atividade=%s aluno=%s: %s",
                    atividade_id,
                    aluno_id,
                    exc,
                )

        historico: List[Dict[str, Any]] = []
        for atividade in atividades_rows:
            turma_info = turma_by_id.get(atividade.get("turma_id"))
            if not turma_info:
                continue

            summary = summaries.get(atividade["id"])
            historico.append({
                "materia": turma_info.get("materia_nome") or "?",
                "turma": turma_info.get("nome") or "?",
                "atividade_id": atividade["id"],
                "atividade": atividade.get("nome"),
                "tipo": atividade.get("tipo"),
                "data": atividade.get("data_aplicacao"),
                "nota": summary["nota"] if summary else None,
                "nota_maxima": (
                    summary["nota_maxima"]
                    if summary and summary.get("nota_maxima") is not None
                    else atividade.get("nota_maxima")
                ),
                "percentual": summary["percentual"] if summary else None,
                "corrigido": summary is not None,
            })

        historico.sort(key=lambda item: item["data"] or "", reverse=True)
        self.storage._log_hot_endpoint_profile(
            "/api/dashboard/aluno/{aluno_id}/historico",
            started_at,
            {
                "turmas": len(turmas),
                "atividades": len(atividades_rows),
                "documentos": len(correction_rows),
            },
            {"json_reads": json_reads},
        )
        return historico

    def get_historico_aluno(self, aluno_id: str) -> List[Dict[str, Any]]:
        """
        Retorna histórico de todas as atividades de um aluno.
        """
        return self.get_historico_aluno_fast(aluno_id)

    def get_dashboard_aluno_fast(self, aluno_id: str) -> Optional[Dict[str, Any]]:
        """Monta o dashboard do aluno usando os helpers batch do storage."""
        started_at = time.perf_counter()
        aluno_data = self.storage.get_aluno_detalhes_fast(aluno_id)
        if not aluno_data:
            self.storage._log_hot_endpoint_profile(
                "/api/dashboard/aluno/{aluno_id}",
                started_at,
                {"turmas": 0, "atividades": 0},
            )
            return None

        historico = self.get_historico_aluno_fast(aluno_id, turmas_info=aluno_data["turmas"])

        por_materia: Dict[str, Dict[str, Any]] = {}
        for item in historico:
            materia = item["materia"]
            if materia not in por_materia:
                por_materia[materia] = {
                    "materia": materia,
                    "total_atividades": 0,
                    "corrigidas": 0,
                    "notas": [],
                }
            por_materia[materia]["total_atividades"] += 1
            if item["nota"] is not None:
                por_materia[materia]["corrigidas"] += 1
                por_materia[materia]["notas"].append(item["nota"])

        materias_stats = []
        for materia, dados in por_materia.items():
            notas = dados.pop("notas")
            materias_stats.append({
                **dados,
                "media": round(sum(notas) / len(notas), 2) if notas else None,
            })

        todas_notas = [item["nota"] for item in historico if item["nota"] is not None]
        media_geral = round(sum(todas_notas) / len(todas_notas), 2) if todas_notas else None

        payload = {
            "aluno": aluno_data["aluno"],
            "resumo": {
                "total_turmas": aluno_data["total_turmas"],
                "total_atividades": len(historico),
                "atividades_corrigidas": len(todas_notas),
                "media_geral": media_geral,
            },
            "por_materia": materias_stats,
            "historico_recente": historico[:10],
        }
        self.storage._log_hot_endpoint_profile(
            "/api/dashboard/aluno/{aluno_id}",
            started_at,
            {"turmas": aluno_data["total_turmas"], "atividades": len(historico)},
            {"atividades_corrigidas": len(todas_notas)},
        )
        return payload
    
    def exportar_resultado_json(self, atividade_id: str, aluno_id: str) -> str:
        """Exporta resultado em JSON"""
        resultado = self.get_resultado_aluno(atividade_id, aluno_id)
        if not resultado:
            return "{}"
        return json.dumps(resultado.to_dict(), ensure_ascii=False, indent=2)
    
    def exportar_resultado_markdown(self, atividade_id: str, aluno_id: str) -> str:
        """Exporta resultado em Markdown"""
        resultado = self.get_resultado_aluno(atividade_id, aluno_id)
        if not resultado:
            return "# Resultado não encontrado"
        
        md = f"""# Resultado da Avaliação

## Informações Gerais
- **Aluno:** {resultado.aluno_nome}
- **Atividade:** {resultado.atividade_nome}
- **Nota Final:** {resultado.nota_final:.1f} / {resultado.nota_maxima:.1f} ({resultado.percentual:.0f}%)

## Resumo
| Métrica | Valor |
|---------|-------|
| Total de Questões | {resultado.total_questoes} |
| Corretas | {resultado.questoes_corretas} |
| Parciais | {resultado.questoes_parciais} |
| Incorretas | {resultado.questoes_incorretas} |
| Em Branco | {resultado.questoes_branco} |

## Detalhamento por Questão
"""
        
        for q in resultado.questoes:
            status_emoji = {"correta": "✅", "parcial": "⚠️", "incorreta": "❌", "em_branco": "⬜"}.get(q.status, "❓")
            md += f"""
### Questão {q.numero} {status_emoji}
- **Nota:** {q.nota:.1f} / {q.nota_maxima:.1f}
- **Status:** {q.status}
- **Feedback:** {q.feedback}
"""
        
        if resultado.habilidades_demonstradas:
            md += "\n## Habilidades Demonstradas\n"
            for h in resultado.habilidades_demonstradas:
                md += f"- ✅ {h}\n"
        
        if resultado.habilidades_faltantes:
            md += "\n## Habilidades a Desenvolver\n"
            for h in resultado.habilidades_faltantes:
                md += f"- 📚 {h}\n"
        
        if resultado.recomendacoes:
            md += "\n## Recomendações de Estudo\n"
            for r in resultado.recomendacoes:
                md += f"- {r}\n"
        
        if resultado.feedback_geral:
            md += f"\n## Feedback Geral\n{resultado.feedback_geral}\n"
        
        md += f"\n---\n*Corrigido por: {resultado.corrigido_por_ia}*\n"
        
        return md


# Instância global
visualizador = VisualizadorResultados()
