"""
Pipeline de Correção de Provas

Este módulo orquestra todo o fluxo:
1. Extração de questões do gabarito
2. Identificação de respostas do aluno
3. Correção questão por questão
4. Agregação em relatório final

Cada etapa pode usar uma IA diferente, permitindo experimentação.
"""

import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from ai_providers import AIProvider, AIResponse, ai_registry
from storage import (
    StorageManager, VectorStore, DocumentType, 
    Questao, Correcao, storage, vector_store
)


class PipelineStage(Enum):
    """Estágios do pipeline de correção"""
    EXTRACT_GABARITO = "extract_gabarito"
    EXTRACT_ALUNO = "extract_aluno"
    MATCH_QUESTOES = "match_questoes"
    CORRIGIR = "corrigir"
    ANALISAR_HABILIDADES = "analisar_habilidades"
    GERAR_RELATORIO = "gerar_relatorio"


@dataclass
class PipelineConfig:
    """Configuração do pipeline - qual IA usar em cada etapa"""
    providers: Dict[PipelineStage, str] = field(default_factory=dict)
    
    def get_provider(self, stage: PipelineStage) -> str:
        """Retorna o provider para um estágio (ou default)"""
        return self.providers.get(stage, ai_registry.default_provider)
    
    def set_provider(self, stage: PipelineStage, provider_name: str):
        """Define qual provider usar em um estágio"""
        if provider_name not in ai_registry.list_providers():
            raise ValueError(f"Provider '{provider_name}' não registrado")
        self.providers[stage] = provider_name


@dataclass
class PipelineResult:
    """Resultado de uma execução do pipeline"""
    success: bool
    stage: PipelineStage
    data: Any
    ai_response: Optional[AIResponse] = None
    error: Optional[str] = None
    duration_ms: float = 0


class CorrectionPipeline:
    """Pipeline principal de correção"""
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self.storage = storage
        self.vector_store = vector_store
        self.results: List[PipelineResult] = []
    
    def _get_provider(self, stage: PipelineStage) -> AIProvider:
        """Obtém o provider configurado para um estágio"""
        provider_name = self.config.get_provider(stage)
        return ai_registry.get(provider_name)
    
    async def extract_questoes_gabarito(self, 
                                         file_path: str,
                                         materia: str) -> PipelineResult:
        """
        Etapa 1: Extrai questões do gabarito/prova original
        
        A IA deve identificar:
        - Número de cada questão
        - Enunciado
        - Itens (a, b, c, etc.)
        - Resposta esperada
        - Pontuação (se disponível)
        """
        import time
        start = time.time()
        
        provider = self._get_provider(PipelineStage.EXTRACT_GABARITO)
        
        system_prompt = """Você é um especialista em análise de provas e avaliações educacionais.
        
Sua tarefa é extrair TODAS as questões de uma prova/gabarito de forma estruturada.

Para cada questão, identifique:
1. Número da questão
2. Enunciado completo
3. Itens/alternativas (se houver)
4. Resposta esperada/gabarito
5. Pontuação (se indicada)
6. Habilidades avaliadas (interprete com base no conteúdo)

IMPORTANTE: 
- Seja extremamente preciso na extração
- Preserve formatação matemática quando relevante
- Identifique se há subquestões (a, b, c, etc.)
- Se não houver gabarito explícito, deixe vazio

Retorne em formato JSON com a estrutura:
{
    "questoes": [
        {
            "numero": 1,
            "enunciado": "...",
            "itens": [
                {"item": "a", "texto": "...", "resposta": "..."},
                {"item": "b", "texto": "...", "resposta": "..."}
            ],
            "resposta_geral": "...",
            "pontuacao": 2.0,
            "habilidades": ["interpretação de texto", "cálculo diferencial"]
        }
    ],
    "total_questoes": 5,
    "pontuacao_total": 10.0,
    "observacoes": "..."
}"""

        instruction = f"""Analise este documento de prova/gabarito da matéria "{materia}".
Extraia todas as questões no formato JSON especificado.
Seja meticuloso - cada detalhe importa para a correção automática."""

        try:
            response = await provider.analyze_document(file_path, instruction)
            
            # Parse do JSON da resposta
            content = response.content
            # Tentar extrair JSON da resposta
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            data = json.loads(json_str.strip())
            
            # Salvar documento
            doc_id = self.storage.save_document(
                file_path,
                DocumentType.PROVA_ORIGINAL,
                materia,
                processado_por=provider.get_identifier(),
                metadata={"total_questoes": data.get("total_questoes", 0)}
            )
            
            # Salvar cada questão
            questoes = []
            for q in data.get("questoes", []):
                questao = Questao(
                    id=self.storage._generate_id(doc_id, q["numero"]),
                    numero=q["numero"],
                    enunciado=q["enunciado"],
                    itens=q.get("itens", []),
                    pontuacao_maxima=q.get("pontuacao", 0),
                    habilidades=q.get("habilidades", []),
                    metadata={"resposta_geral": q.get("resposta_geral", "")}
                )
                self.storage.save_questao(questao, doc_id)
                questoes.append(questao)
                
                # Indexar para busca semântica
                await self.vector_store.index_questao(questao, doc_id)
            
            duration = (time.time() - start) * 1000
            
            result = PipelineResult(
                success=True,
                stage=PipelineStage.EXTRACT_GABARITO,
                data={
                    "documento_id": doc_id,
                    "questoes": [q.id for q in questoes],
                    "total": len(questoes)
                },
                ai_response=response,
                duration_ms=duration
            )
            
        except Exception as e:
            result = PipelineResult(
                success=False,
                stage=PipelineStage.EXTRACT_GABARITO,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )
        
        self.results.append(result)
        return result
    
    async def extract_respostas_aluno(self,
                                       file_path: str,
                                       materia: str,
                                       aluno_id: str) -> PipelineResult:
        """
        Etapa 2: Extrai respostas do aluno de sua prova
        
        A IA deve identificar o que o aluno respondeu em cada questão,
        mesmo que a organização seja diferente do gabarito.
        """
        import time
        start = time.time()
        
        provider = self._get_provider(PipelineStage.EXTRACT_ALUNO)
        
        system_prompt = """Você é um especialista em análise de provas respondidas por alunos.

Sua tarefa é extrair TODAS as respostas que o aluno forneceu, identificando:
1. A qual questão/item cada resposta se refere
2. O conteúdo exato da resposta
3. Se há rascunhos ou partes rasuradas
4. Se alguma questão ficou em branco

IMPORTANTE:
- Preserve exatamente o que o aluno escreveu
- Identifique numeração mesmo que inconsistente
- Note se há páginas faltando ou ilegíveis
- Marque incertezas explicitamente

Retorne em formato JSON:
{
    "respostas": [
        {
            "questao_ref": "1",
            "item_ref": "a",
            "resposta": "conteúdo da resposta do aluno",
            "observacoes": "rasurado", "em branco", etc.
        }
    ],
    "questoes_em_branco": [2, 3],
    "problemas_identificados": ["página 2 parece cortada"],
    "legibilidade": 0.9
}"""

        instruction = f"""Analise esta prova respondida pelo aluno "{aluno_id}" na matéria "{materia}".
Extraia todas as respostas no formato JSON especificado.
Seja preciso ao identificar a qual questão cada resposta pertence."""

        try:
            response = await provider.analyze_document(file_path, instruction)
            
            # Parse JSON
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            data = json.loads(json_str.strip())
            
            # Salvar documento
            doc_id = self.storage.save_document(
                file_path,
                DocumentType.PROVA_ALUNO,
                materia,
                processado_por=provider.get_identifier(),
                metadata={
                    "aluno_id": aluno_id,
                    "legibilidade": data.get("legibilidade", 1.0),
                    "problemas": data.get("problemas_identificados", [])
                }
            )
            
            duration = (time.time() - start) * 1000
            
            result = PipelineResult(
                success=True,
                stage=PipelineStage.EXTRACT_ALUNO,
                data={
                    "documento_id": doc_id,
                    "aluno_id": aluno_id,
                    "respostas": data.get("respostas", []),
                    "questoes_em_branco": data.get("questoes_em_branco", []),
                    "problemas": data.get("problemas_identificados", [])
                },
                ai_response=response,
                duration_ms=duration
            )
            
        except Exception as e:
            result = PipelineResult(
                success=False,
                stage=PipelineStage.EXTRACT_ALUNO,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )
        
        self.results.append(result)
        return result
    
    async def corrigir_questao(self,
                               questao: Questao,
                               resposta_aluno: Dict[str, Any],
                               prova_aluno_id: str) -> PipelineResult:
        """
        Etapa 3: Corrige uma questão específica
        
        A IA deve:
        1. Comparar resposta do aluno com gabarito
        2. Identificar acertos e erros
        3. Avaliar parcialmente se aplicável
        4. Identificar habilidades demonstradas
        5. Gerar feedback construtivo
        """
        import time
        start = time.time()
        
        provider = self._get_provider(PipelineStage.CORRIGIR)
        
        system_prompt = """Você é um professor experiente realizando correção detalhada de provas.

Para cada questão, você deve:
1. Analisar cuidadosamente a resposta do aluno
2. Comparar com a resposta esperada
3. Atribuir nota proporcional aos acertos
4. Identificar erros específicos e suas causas prováveis
5. Avaliar quais habilidades o aluno demonstrou
6. Gerar feedback educativo e construtivo

CRITÉRIOS DE CORREÇÃO:
- Seja justo e consistente
- Valorize raciocínio correto mesmo com pequenos erros
- Identifique padrões de erro que indicam lacunas de aprendizado
- O feedback deve ajudar o aluno a melhorar

Retorne em formato JSON:
{
    "nota": 1.5,
    "nota_maxima": 2.0,
    "acertos": ["identificou corretamente X", "aplicou Y"],
    "erros": [
        {
            "descricao": "confundiu A com B",
            "gravidade": "leve|moderado|grave",
            "causa_provavel": "confusão conceitual entre..."
        }
    ],
    "habilidades_demonstradas": ["interpretação", "cálculo básico"],
    "habilidades_faltantes": ["álgebra avançada"],
    "feedback": "Bom trabalho em... Para melhorar, revise...",
    "confianca": 0.95
}"""

        # Montar contexto
        resposta_esperada = questao.metadata.get("resposta_geral", "")
        if questao.itens:
            for item in questao.itens:
                if item.get("item") == resposta_aluno.get("item_ref"):
                    resposta_esperada = item.get("resposta", resposta_esperada)
                    break
        
        prompt = f"""QUESTÃO {questao.numero}:
{questao.enunciado}

RESPOSTA ESPERADA:
{resposta_esperada}

RESPOSTA DO ALUNO:
{resposta_aluno.get('resposta', '[EM BRANCO]')}

Observações sobre a resposta: {resposta_aluno.get('observacoes', 'Nenhuma')}

Pontuação máxima desta questão: {questao.pontuacao_maxima}

Corrija esta questão seguindo os critérios estabelecidos."""

        try:
            response = await provider.complete(prompt, system_prompt)
            
            # Parse JSON
            content = response.content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]
            else:
                json_str = content
            
            data = json.loads(json_str.strip())
            
            # Criar objeto Correcao
            correcao = Correcao(
                id=self.storage._generate_id(prova_aluno_id, questao.id),
                prova_aluno_id=prova_aluno_id,
                questao_id=questao.id,
                item_id=resposta_aluno.get("item_ref"),
                resposta_aluno=resposta_aluno.get("resposta", ""),
                resposta_esperada=resposta_esperada,
                nota=data.get("nota", 0),
                nota_maxima=data.get("nota_maxima", questao.pontuacao_maxima),
                feedback=data.get("feedback", ""),
                erros_identificados=[e["descricao"] for e in data.get("erros", [])],
                habilidades_demonstradas=data.get("habilidades_demonstradas", []),
                habilidades_faltantes=data.get("habilidades_faltantes", []),
                corrigido_por=provider.get_identifier(),
                timestamp=datetime.now(),
                confianca=data.get("confianca", 0.5),
                metadata={
                    "acertos": data.get("acertos", []),
                    "erros_detalhados": data.get("erros", [])
                }
            )
            
            # Salvar correção
            self.storage.save_correcao(correcao)
            
            duration = (time.time() - start) * 1000
            
            result = PipelineResult(
                success=True,
                stage=PipelineStage.CORRIGIR,
                data={
                    "correcao_id": correcao.id,
                    "nota": correcao.nota,
                    "nota_maxima": correcao.nota_maxima,
                    "feedback": correcao.feedback
                },
                ai_response=response,
                duration_ms=duration
            )
            
        except Exception as e:
            result = PipelineResult(
                success=False,
                stage=PipelineStage.CORRIGIR,
                data={"questao_id": questao.id},
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )
        
        self.results.append(result)
        return result
    
    async def gerar_relatorio_final(self,
                                     prova_aluno_id: str,
                                     aluno_nome: str,
                                     usar_tools: bool = False,
                                     atividade_id: str = None,
                                     aluno_id: str = None) -> PipelineResult:
        """
        Etapa final: Gera relatório consolidado para o professor
        
        Agrega todas as correções em um documento final com:
        - Nota total
        - Resumo por questão
        - Análise de habilidades
        - Recomendações de estudo
        
        Se usar_tools=True, permite que o modelo use create_document
        para criar múltiplos documentos (relatório, resumo, etc.)
        """
        import time
        start = time.time()
        
        provider = self._get_provider(PipelineStage.GERAR_RELATORIO)
        
        # Buscar todas as correções
        correcoes = self.storage.get_correcoes_aluno(prova_aluno_id)
        
        if not correcoes:
            return PipelineResult(
                success=False,
                stage=PipelineStage.GERAR_RELATORIO,
                data=None,
                error="Nenhuma correção encontrada para esta prova"
            )
        
        # Calcular estatísticas
        nota_total = sum(c.nota for c in correcoes)
        nota_maxima = sum(c.nota_maxima for c in correcoes)
        
        todas_habilidades_dem = []
        todas_habilidades_falt = []
        for c in correcoes:
            todas_habilidades_dem.extend(c.habilidades_demonstradas)
            todas_habilidades_falt.extend(c.habilidades_faltantes)
        
        system_prompt = """Você é um especialista em avaliação educacional.

Gere um relatório de desempenho profissional e construtivo que:
1. Apresente resultados de forma clara
2. Destaque pontos fortes do aluno
3. Identifique áreas de melhoria
4. Sugira próximos passos de estudo
5. Seja encorajador mas honesto

O relatório deve ser adequado para ser enviado ao professor,
que poderá compartilhar com o aluno ou responsáveis."""

        # Montar resumo das correções
        resumo_correcoes = []
        for c in correcoes:
            resumo_correcoes.append({
                "questao": c.questao_id,
                "nota": f"{c.nota}/{c.nota_maxima}",
                "feedback_resumido": c.feedback[:200] if c.feedback else "",
                "erros": c.erros_identificados[:3]
            })
        
        base_info = f"""Aluno: {aluno_nome}
Prova ID: {prova_aluno_id}

RESULTADO GERAL:
- Nota Final: {nota_total}/{nota_maxima} ({(nota_total/nota_maxima*100):.1f}%)
- Questões corrigidas: {len(correcoes)}

HABILIDADES DEMONSTRADAS:
{', '.join(set(todas_habilidades_dem)) or 'Nenhuma identificada'}

HABILIDADES A DESENVOLVER:
{', '.join(set(todas_habilidades_falt)) or 'Nenhuma identificada'}

DETALHAMENTO POR QUESTÃO:
{json.dumps(resumo_correcoes, indent=2, ensure_ascii=False)}"""

        try:
            # Se usar tools, permite que o modelo crie múltiplos documentos
            if usar_tools and atividade_id:
                from executor import pipeline_executor
                
                prompt_com_tools = f"""Gere relatório(s) para este aluno usando a ferramenta create_document.

{base_info}

Você DEVE usar a ferramenta create_document para criar os documentos.
Pode criar múltiplos documentos se desejar:
1. Relatório completo para o professor (markdown)
2. Resumo simples para o aluno (markdown)
3. Versão PDF profissional (docx)

Escolha os formatos mais apropriados. Use a ferramenta create_document."""

                executor_result = await pipeline_executor.executar_com_tools(
                    mensagem=prompt_com_tools,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    provider_id=self.config.get_provider(PipelineStage.GERAR_RELATORIO),
                    tools_to_use=["create_document"]
                )
                
                duration = (time.time() - start) * 1000
                
                result = PipelineResult(
                    success=executor_result.sucesso,
                    stage=PipelineStage.GERAR_RELATORIO,
                    data={
                        "documentos_criados": executor_result.documentos_criados,
                        "nota_final": nota_total,
                        "nota_maxima": nota_maxima,
                        "percentual": round(nota_total/nota_maxima*100, 1),
                        "usar_tools": True
                    },
                    ai_response=executor_result.ai_response,
                    duration_ms=duration
                )
                
                self.results.append(result)
                return result
            
            # Modo tradicional sem tools
            prompt = f"""Gere um relatório de avaliação para:
{base_info}

Gere um relatório completo em Markdown."""

            response = await provider.complete(prompt, system_prompt)
            
            # Salvar relatório
            relatorio_path = self.storage.base_path / "exports" / f"relatorio_{prova_aluno_id}.md"
            relatorio_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                f.write(response.content)
            
            duration = (time.time() - start) * 1000
            
            result = PipelineResult(
                success=True,
                stage=PipelineStage.GERAR_RELATORIO,
                data={
                    "relatorio_path": str(relatorio_path),
                    "nota_final": nota_total,
                    "nota_maxima": nota_maxima,
                    "percentual": round(nota_total/nota_maxima*100, 1)
                },
                ai_response=response,
                duration_ms=duration
            )
            
        except Exception as e:
            result = PipelineResult(
                success=False,
                stage=PipelineStage.GERAR_RELATORIO,
                data=None,
                error=str(e),
                duration_ms=(time.time() - start) * 1000
            )
        
        self.results.append(result)
        return result
    
    async def run_full_pipeline(self,
                                gabarito_path: str,
                                prova_aluno_path: str,
                                materia: str,
                                aluno_id: str,
                                aluno_nome: str) -> Dict[str, Any]:
        """
        Executa o pipeline completo de correção
        
        1. Extrai questões do gabarito
        2. Extrai respostas do aluno
        3. Para cada questão, realiza correção
        4. Gera relatório final
        """
        results = {
            "success": True,
            "stages": {},
            "errors": []
        }
        
        # Etapa 1: Extrair gabarito
        gabarito_result = await self.extract_questoes_gabarito(gabarito_path, materia)
        results["stages"]["extract_gabarito"] = gabarito_result.data
        
        if not gabarito_result.success:
            results["success"] = False
            results["errors"].append(f"Falha ao extrair gabarito: {gabarito_result.error}")
            return results
        
        # Etapa 2: Extrair respostas do aluno
        aluno_result = await self.extract_respostas_aluno(prova_aluno_path, materia, aluno_id)
        results["stages"]["extract_aluno"] = aluno_result.data
        
        if not aluno_result.success:
            results["success"] = False
            results["errors"].append(f"Falha ao extrair respostas: {aluno_result.error}")
            return results
        
        # Verificar problemas identificados
        if aluno_result.data.get("problemas"):
            results["warnings"] = aluno_result.data["problemas"]
        
        # Etapa 3: Corrigir cada questão
        questoes = self.storage.get_questoes_documento(gabarito_result.data["documento_id"])
        respostas = aluno_result.data.get("respostas", [])
        
        correcoes_results = []
        for questao in questoes:
            # Encontrar resposta correspondente
            resposta = next(
                (r for r in respostas if str(r.get("questao_ref")) == str(questao.numero)),
                {"resposta": "[EM BRANCO]", "questao_ref": questao.numero}
            )
            
            correcao_result = await self.corrigir_questao(
                questao, 
                resposta, 
                aluno_result.data["documento_id"]
            )
            correcoes_results.append(correcao_result.data)
            
            if not correcao_result.success:
                results["errors"].append(f"Erro na questão {questao.numero}: {correcao_result.error}")
        
        results["stages"]["correcoes"] = correcoes_results
        
        # Etapa 4: Gerar relatório final
        relatorio_result = await self.gerar_relatorio_final(
            aluno_result.data["documento_id"],
            aluno_nome
        )
        results["stages"]["relatorio"] = relatorio_result.data
        
        if not relatorio_result.success:
            results["errors"].append(f"Falha ao gerar relatório: {relatorio_result.error}")
        
        # Resumo final
        results["summary"] = {
            "nota_final": relatorio_result.data.get("nota_final") if relatorio_result.success else None,
            "nota_maxima": relatorio_result.data.get("nota_maxima") if relatorio_result.success else None,
            "relatorio_path": relatorio_result.data.get("relatorio_path") if relatorio_result.success else None,
            "providers_usados": list(set(
                r.ai_response.provider + "/" + r.ai_response.model 
                for r in self.results 
                if r.ai_response
            )),
            "tempo_total_ms": sum(r.duration_ms for r in self.results)
        }
        
        return results
