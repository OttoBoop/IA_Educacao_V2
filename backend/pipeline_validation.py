"""
NOVO CR - Validation Models for Pipeline JSON Outputs v2.0

Pydantic models for validating JSON outputs from each pipeline stage.
These models ensure AI models produce correctly structured responses.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import List, Dict, Any, Optional, Union
from enum import Enum


# ============================================================
# ENUMS FOR VALIDATION
# ============================================================

AVISO_DOCUMENTO_CODES = frozenset({
    "ILLEGIBLE_DOCUMENT",
    "MISSING_CONTENT",
    "LOW_CONFIDENCE",
})
AVISO_QUESTAO_CODES = frozenset({
    "ILLEGIBLE_QUESTION",
    "MISSING_CONTENT",
    "LOW_CONFIDENCE",
})

class TipoQuestao(str, Enum):
    """Tipos de questões suportadas"""
    MULTIPLA_ESCOLHA = "multipla_escolha"
    DISSERTATIVA = "dissertativa"
    VERDADEIRO_FALSO = "verdadeiro_falso"
    ASSOCIACAO = "associacao"


class StatusCorrecao(str, Enum):
    """Status possíveis para correção de questões"""
    CORRETA = "correta"
    PARCIAL = "parcial"
    INCORRETA = "incorreta"
    EM_BRANCO = "em_branco"


class NivelHabilidade(str, Enum):
    """Níveis de domínio de habilidades"""
    DOMINADA = "dominadas"
    EM_DESENVOLVIMENTO = "em_desenvolvimento"
    NAO_DEMONSTRADA = "nao_demonstradas"


# ============================================================
# MODELS FOR EACH PIPELINE STAGE
# ============================================================

class PipelineModel(BaseModel):
    """Base permissiva para outputs de IA com metadados de aviso.

    Os prompts e o handler create_document usam chaves com underscore
    (`_avisos_*`). Pydantic trata atributos iniciados com underscore como
    privados, então usamos aliases para manter o contrato JSON público.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    avisos_documento: List[Dict[str, Any]] = Field(
        default_factory=list,
        alias="_avisos_documento",
        description="Avisos sobre o documento inteiro",
    )
    avisos_questao: List[Dict[str, Any]] = Field(
        default_factory=list,
        alias="_avisos_questao",
        description="Avisos por questao",
    )
    avisos_stage: Optional[str] = Field(
        default=None,
        alias="_avisos_stage",
        description="Etapa usada para calcular severidade dos avisos",
    )

    @model_validator(mode="after")
    def _validar_codigos_de_aviso_unicos(self):
        def _validar_lista(
            campo: str,
            avisos: List[Dict[str, Any]],
            codigos_validos: frozenset[str],
        ) -> None:
            for index, aviso in enumerate(avisos):
                codigo = aviso.get("codigo") if isinstance(aviso, dict) else None
                if not isinstance(codigo, str) or not codigo.strip():
                    raise ValueError(f"{campo}[{index}].codigo ausente")

                codigo_limpo = codigo.strip()
                if "|" in codigo_limpo:
                    raise ValueError(
                        f"{campo}[{index}].codigo deve ter um unico codigo; "
                        f"recebido '{codigo}'"
                    )
                if codigo_limpo not in codigos_validos:
                    validos = ", ".join(sorted(codigos_validos))
                    raise ValueError(
                        f"{campo}[{index}].codigo invalido '{codigo}'; "
                        f"codigos validos: {validos}"
                    )

        _validar_lista("_avisos_documento", self.avisos_documento, AVISO_DOCUMENTO_CODES)
        _validar_lista("_avisos_questao", self.avisos_questao, AVISO_QUESTAO_CODES)
        return self


class ItemQuestao(BaseModel):
    """Item de uma questão de múltipla escolha"""
    letra: str = Field(..., description="Letra do item (a, b, c, d, etc.)", min_length=1, max_length=2)
    texto: str = Field(..., description="Texto do item", min_length=1)


class Questao(BaseModel):
    """Questão extraída do enunciado"""
    numero: int = Field(..., description="Número da questão", gt=0)
    enunciado: str = Field(..., description="Enunciado completo da questão", min_length=1)
    itens: List[ItemQuestao] = Field(default_factory=list, description="Itens para questões de múltipla escolha")
    tipo: TipoQuestao = Field(..., description="Tipo da questão")
    pontuacao: float = Field(..., description="Pontuação da questão", ge=0)
    habilidades: List[str] = Field(default_factory=list, description="Habilidades relacionadas")
    tipo_raciocinio: Optional[str] = Field(None, description="Tipo de raciocínio exigido: memória, aplicação, análise, síntese, avaliação")


class ExtracaoQuestoes(PipelineModel):
    """Saída da etapa EXTRAIR_QUESTOES"""
    questoes: List[Questao] = Field(..., description="Lista de questões extraídas")
    total_questoes: int = Field(..., description="Total de questões encontradas", ge=0)
    pontuacao_total: float = Field(..., description="Pontuação total da prova", ge=0)


class CriterioParcial(BaseModel):
    """Critério para correção parcial"""
    descricao: str = Field(..., description="Descrição do critério", min_length=1)
    percentual: int = Field(..., description="Percentual de pontuação (0-100)", ge=0, le=100)


class RespostaGabarito(BaseModel):
    """Resposta correta do gabarito"""
    questao_numero: int = Field(..., description="Número da questão", gt=0)
    resposta_correta: str = Field(..., description="Resposta correta", min_length=1)
    justificativa: str = Field(default="", description="Justificativa da resposta correta")
    criterios_parciais: List[CriterioParcial] = Field(default_factory=list, description="Critérios para correção parcial")
    conceito_central: Optional[str] = Field(None, description="Conceito pedagógico principal testado pela questão")


class ExtracaoGabarito(PipelineModel):
    """Saída da etapa EXTRAIR_GABARITO"""
    respostas: List[RespostaGabarito] = Field(..., description="Lista de respostas corretas")

    @model_validator(mode="after")
    def nao_aceita_gabarito_todo_missing_content(self):
        if self.respostas and all(
            (resposta.resposta_correta or "").strip().upper() == "MISSING_CONTENT"
            for resposta in self.respostas
        ):
            raise ValueError(
                "extrair_gabarito retornou todas as respostas como MISSING_CONTENT; "
                "isso nao pode ser tratado como sucesso"
            )
        return self


class RespostaAluno(BaseModel):
    """Resposta extraída da prova do aluno"""
    questao_numero: int = Field(..., description="Número da questão", gt=0)
    resposta_aluno: Optional[str] = Field(None, description="Resposta dada pelo aluno")
    em_branco: bool = Field(default=False, description="Se a questão foi deixada em branco")
    ilegivel: bool = Field(default=False, description="Se a resposta é ilegível")
    observacoes: str = Field(default="", description="Observações adicionais")
    raciocinio_parcial: Optional[str] = Field(None, description="Raciocínio parcial do aluno identificado — sinais de entendimento mesmo em respostas erradas")


class ExtracaoRespostas(PipelineModel):
    """Saída da etapa EXTRAIR_RESPOSTAS"""
    aluno: str = Field(..., description="Nome do aluno", min_length=1)
    respostas: List[RespostaAluno] = Field(..., description="Lista de respostas do aluno")
    questoes_respondidas: int = Field(..., description="Número de questões respondidas", ge=0)
    questoes_em_branco: int = Field(..., description="Número de questões em branco", ge=0)

    @model_validator(mode="after")
    def nao_aceita_respostas_sem_conteudo_extraido(self):
        def _sem_conteudo(resposta: RespostaAluno) -> bool:
            return (
                resposta.ilegivel
                or resposta.em_branco
                or not (resposta.resposta_aluno or "").strip()
            )

        if self.respostas and all(_sem_conteudo(resposta) for resposta in self.respostas):
            raise ValueError(
                "extrair_respostas retornou todas as respostas sem conteudo extraido "
                "(em branco, ilegiveis ou vazias); "
                "isso nao pode ser tratado como sucesso"
            )
        return self


class CorrecaoQuestao(PipelineModel):
    """Resultado da correção de uma questão individual"""
    nota: float = Field(..., description="Nota atribuída", ge=0)
    nota_maxima: float = Field(..., description="Nota máxima da questão", gt=0)
    percentual: int = Field(..., description="Percentual de acerto (0-100)", ge=0, le=100)
    status: StatusCorrecao = Field(..., description="Status da correção")
    feedback: str = Field(..., description="Feedback detalhado para o aluno", min_length=1)
    pontos_positivos: List[str] = Field(default_factory=list, description="Pontos positivos da resposta")
    pontos_melhorar: List[str] = Field(default_factory=list, description="Pontos a melhorar")
    erros_conceituais: List[str] = Field(default_factory=list, description="Erros conceituais identificados")
    habilidades_demonstradas: List[str] = Field(default_factory=list, description="Habilidades demonstradas")
    habilidades_faltantes: List[str] = Field(default_factory=list, description="Habilidades que precisam ser desenvolvidas")
    narrativa_correcao: Optional[str] = Field(None, description="Análise pedagógica narrativa: raciocínio do aluno, tipo de erro, potencial")


class CorrecaoPipeline(PipelineModel):
    """Saida aceita para CORRIGIR.

    A pipeline ainda suporta o formato legado de questao unica
    (`nota`, `status`, `feedback`) e o formato de tool-use atual
    (`nota_final`, `questoes`, `feedback_geral`).
    """

    nota_final: Optional[float] = Field(None, description="Nota final agregada")
    questoes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Correcoes por questao no formato agregado",
    )
    total_acertos: Optional[int] = Field(None, description="Total de questoes corretas")
    total_erros: Optional[int] = Field(None, description="Total de questoes incorretas")
    feedback_geral: str = Field(default="", description="Feedback geral da correcao")

    nota: Optional[float] = Field(None, description="Nota atribuida a uma questao unica", ge=0)
    nota_maxima: Optional[float] = Field(None, description="Nota maxima da questao", gt=0)
    percentual: Optional[int] = Field(None, description="Percentual de acerto", ge=0, le=100)
    status: Optional[StatusCorrecao] = Field(None, description="Status da correcao")
    feedback: str = Field(default="", description="Feedback detalhado")
    pontos_positivos: List[str] = Field(default_factory=list, description="Pontos positivos")
    pontos_melhorar: List[str] = Field(default_factory=list, description="Pontos a melhorar")
    erros_conceituais: List[str] = Field(default_factory=list, description="Erros conceituais")
    habilidades_demonstradas: List[str] = Field(default_factory=list, description="Habilidades demonstradas")
    habilidades_faltantes: List[str] = Field(default_factory=list, description="Habilidades faltantes")
    narrativa_correcao: Optional[str] = Field(None, description="Narrativa pedagogica da correcao")

    @model_validator(mode="after")
    def _validar_formato_minimo(self):
        if self.questoes or self.nota_final is not None or self.nota is not None:
            return self
        raise ValueError(
            "CORRIGIR precisa ter formato agregado (nota_final/questoes) "
            "ou formato de questao unica (nota)"
        )


class AnaliseHabilidades(PipelineModel):
    """Saída da etapa ANALISAR_HABILIDADES"""
    aluno: str = Field(default="", description="Nome do aluno")
    resumo_desempenho: str = Field(default="", description="Resumo geral do desempenho")
    nota_final: Optional[float] = Field(None, description="Nota final do aluno", ge=0)
    nota_maxima: Optional[float] = Field(None, description="Nota máxima possível", gt=0)
    percentual_acerto: Optional[int] = Field(None, description="Percentual geral de acerto (0-100)", ge=0, le=100)
    habilidades: Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="Análise de habilidades por categoria ou lista plana do tool-use",
    )
    indicadores: Dict[str, Any] = Field(default_factory=dict, description="Indicadores agregados do tool-use")
    recomendacoes: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="Recomendações de estudo")
    pontos_fortes: List[str] = Field(default_factory=list, description="Pontos fortes do aluno")
    areas_atencao: List[str] = Field(default_factory=list, description="Áreas que precisam de atenção")
    narrativa_habilidades: Optional[str] = Field(None, description="Síntese narrativa de padrões de aprendizado: consistência, esforço vs. conhecimento, transferência de conceitos")


class RelatorioFinal(PipelineModel):
    """Saída da etapa GERAR_RELATORIO"""
    conteudo: str = Field(default="", description="Conteúdo do relatório em Markdown")
    resumo_executivo: str = Field(default="", description="Resumo executivo breve")
    nota_final: Union[str, float] = Field(..., description="Nota final formatada")
    aluno: str = Field(default="", description="Nome do aluno")
    materia: str = Field(default="", description="Matéria da prova")
    atividade: str = Field(default="", description="Nome/título da atividade")
    resumo_geral: str = Field(default="", description="Resumo geral no formato tool-use")
    pontos_fortes: List[str] = Field(default_factory=list, description="Pontos fortes")
    areas_melhoria: List[str] = Field(default_factory=list, description="Áreas de melhoria")
    recomendacoes: List[Union[str, Dict[str, Any]]] = Field(default_factory=list, description="Recomendações")
    detalhamento: str = Field(default="", description="Detalhamento do relatório")
    relatorio_narrativo: Optional[str] = Field(None, description="Narrativa holística: visão geral do aluno, combinando nota, habilidades e análise numa leitura fluida")
    fontes_utilizadas: List[str] = Field(
        default_factory=list,
        alias="_fontes_utilizadas",
        description="Etapas upstream usadas para gerar o relatorio",
    )


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def validar_json_pipeline(etapa: str, dados: Dict[str, Any]) -> Union[BaseModel, Dict[str, Any]]:
    """
    Valida JSON de saída de uma etapa do pipeline usando Pydantic models.

    Args:
        etapa: Nome da etapa do pipeline
        dados: Dados JSON a validar

    Returns:
        Instância do modelo Pydantic se válido, ou dict com erro se inválido
    """
    modelos = {
        'extrair_questoes': ExtracaoQuestoes,
        'extrair_gabarito': ExtracaoGabarito,
        'extrair_respostas': ExtracaoRespostas,
        'corrigir': CorrecaoPipeline,
        'analisar_habilidades': AnaliseHabilidades,
        'gerar_relatorio': RelatorioFinal
    }

    modelo = modelos.get(etapa.lower().replace(' ', '_'))
    if not modelo:
        return {
            "_error": "etapa_desconhecida",
            "_message": f"Etapa '{etapa}' não possui modelo de validação",
            "_etapa": etapa
        }

    try:
        instancia = modelo(**dados)
        return instancia
    except Exception as e:
        return {
            "_error": "validacao_falhou",
            "_message": f"JSON não corresponde ao esquema esperado: {str(e)}",
            "_etapa": etapa,
            "_erros": str(e),
            "_dados_recebidos": dados
        }


def obter_schema_json(etapa: str):
    """
    Retorna o schema JSON Schema para uma etapa do pipeline.

    Args:
        etapa: Nome da etapa

    Returns:
        Schema JSON Schema ou None se etapa não existir
    """
    modelos = {
        'extrair_questoes': ExtracaoQuestoes,
        'extrair_gabarito': ExtracaoGabarito,
        'extrair_respostas': ExtracaoRespostas,
        'corrigir': CorrecaoPipeline,
        'analisar_habilidades': AnaliseHabilidades,
        'gerar_relatorio': RelatorioFinal
    }

    modelo = modelos.get(etapa.lower().replace(' ', '_'))
    if modelo:
        return modelo.model_json_schema(by_alias=True)
    return None
