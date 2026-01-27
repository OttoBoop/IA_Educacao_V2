"""
PROVA AI - Visualização de Resultados v2.0

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

from models import TipoDocumento, Documento
from storage_v2 import storage_v2 as storage


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
            "corrigido_por_ia": self.corrigido_por_ia
        }


class VisualizadorResultados:
    """Serviço para visualização de resultados"""
    
    def __init__(self):
        self.storage = storage
    
    def get_resultado_aluno(self, atividade_id: str, aluno_id: str) -> Optional[VisaoAluno]:
        """
        Monta visão consolidada do resultado de um aluno.
        Combina dados de correção, análise de habilidades e relatório.
        """
        atividade = self.storage.get_atividade(atividade_id)
        aluno = self.storage.get_aluno(aluno_id)
        
        if not atividade or not aluno:
            return None
        
        # Buscar documentos do aluno
        documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        
        # Encontrar correção
        correcao_doc = next((d for d in documentos if d.tipo == TipoDocumento.CORRECAO), None)
        analise_doc = next((d for d in documentos if d.tipo == TipoDocumento.ANALISE_HABILIDADES), None)
        
        if not correcao_doc:
            return None
        
        # Ler dados da correção
        correcao_data = self._ler_json(correcao_doc)
        analise_data = self._ler_json(analise_doc) if analise_doc else {}
        
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
        
        # Processar correção
        self._processar_correcao(visao, correcao_data)
        
        # Processar análise de habilidades
        self._processar_analise(visao, analise_data)
        
        return visao
    
    def _ler_json(self, documento: Documento) -> Dict[str, Any]:
        """Lê conteúdo JSON de um documento"""
        try:
            arquivo = Path(documento.caminho_arquivo)
            if arquivo.exists():
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _processar_correcao(self, visao: VisaoAluno, data: Dict[str, Any]):
        """Processa dados de correção para a visão"""
        # Tentar diferentes formatos de resposta da IA
        
        # Formato 1: Resposta direta com nota
        if "nota" in data:
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
    
    def _processar_analise(self, visao: VisaoAluno, data: Dict[str, Any]):
        """Processa análise de habilidades"""
        if not data:
            return
        
        # Habilidades
        habilidades = data.get("habilidades", {})
        
        if isinstance(habilidades, dict):
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
    
    def get_historico_aluno(self, aluno_id: str) -> List[Dict[str, Any]]:
        """
        Retorna histórico de todas as atividades de um aluno.
        """
        turmas = self.storage.get_turmas_do_aluno(aluno_id)
        historico = []
        
        for turma_info in turmas:
            turma = self.storage.get_turma(turma_info["id"])
            if not turma:
                continue
            
            materia = self.storage.get_materia(turma.materia_id)
            atividades = self.storage.listar_atividades(turma.id)
            
            for atividade in atividades:
                resultado = self.get_resultado_aluno(atividade.id, aluno_id)
                
                historico.append({
                    "materia": materia.nome if materia else "?",
                    "turma": turma.nome,
                    "atividade_id": atividade.id,
                    "atividade": atividade.nome,
                    "tipo": atividade.tipo,
                    "data": atividade.data_aplicacao.isoformat() if atividade.data_aplicacao else None,
                    "nota": resultado.nota_final if resultado else None,
                    "nota_maxima": atividade.nota_maxima,
                    "percentual": resultado.percentual if resultado else None,
                    "corrigido": resultado is not None
                })
        
        # Ordenar por data (mais recente primeiro)
        historico.sort(key=lambda x: x["data"] or "", reverse=True)
        
        return historico
    
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
