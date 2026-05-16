"""
NOVO CR - Executor de Pipeline v2.5 (Unificado)

Executa etapas individuais do pipeline de correção.
Suporta envio MULTIMODAL (PDFs e imagens nativos) para APIs de IA.

Mantém compatibilidade com:
- ai_registry (sistema antigo)
- chat_service.provider_manager (sistema novo)
- Sistema de prompts existente
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import json
import asyncio
import time
import re
import tempfile
import os
import math
import uuid
import unicodedata
import fitz  # PyMuPDF — extract text from binary PDFs (RELATORIO_FINAL)

from models import (
    TipoDocumento, Documento, StatusProcessamento, criar_erro_pipeline,
    ERRO_DOCUMENTO_FALTANTE, ERRO_QUESTOES_FALTANTES,
    ERRO_NOTA_FINAL_INDETERMINADA, SeveridadeErro,
)
from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage import StorageManager, storage
from ai_providers import ai_registry, AIResponse
from token_usage import record_token_usage

# Import do sistema multimodal
try:
    from anexos import ClienteAPIMultimodal, PreparadorArquivos, ResultadoEnvio
    HAS_MULTIMODAL = True
except ImportError:
    HAS_MULTIMODAL = False
    print("[WARN] Sistema multimodal não disponível (anexos.py não encontrado)")

# Import do sistema de logging estruturado
try:
    from logging_config import get_logger, truncate_for_log
    _logger = get_logger("pipeline.executor")
except ImportError:
    # Fallback para logging básico
    import logging
    _logger = logging.getLogger("pipeline.executor")
    def truncate_for_log(text, max_length=500):
        return text[:max_length] + "..." if len(text) > max_length else text

# Import dos modelos de validação (feito lazy para evitar erros de sintaxe)
HAS_VALIDATION = False
_validar_json_pipeline = None


# ============================================================
# DATACLASSES DE RESULTADO
# ============================================================

@dataclass
class ResultadoExecucao:
    """Resultado de uma execução de etapa (compatível com sistema antigo)"""
    sucesso: bool
    etapa: Union[EtapaProcessamento, str]
    
    # Dados da execução
    prompt_usado: str = ""
    prompt_id: str = ""
    provider: str = ""
    modelo: str = ""
    
    # Resultado
    resposta_raw: str = ""
    resposta_parsed: Optional[Dict[str, Any]] = None
    
    # Metadados
    tokens_entrada: int = 0
    tokens_saida: int = 0
    tempo_ms: float = 0
    
    # Documento gerado (se salvou)
    documento_id: Optional[str] = None
    
    # Multimodal - novos campos
    anexos_enviados: List[Dict[str, Any]] = field(default_factory=list)
    anexos_confirmados: bool = False
    alertas: List[Dict[str, Any]] = field(default_factory=list)

    # Erro (se falhou)
    erro: Optional[str] = None
    erro_codigo: Optional[int] = None  # Código HTTP do erro

    # Retry
    retryable: bool = False  # Se o erro pode ser retentado
    retry_after: Optional[int] = None  # Segundos para aguardar
    tentativas: int = 1  # Número de tentativas realizadas

    # PDF fallback (F7-T1): True when LLM skipped execute_python_code
    # and backend auto-generated PDF from create_document JSON content
    pdf_fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        etapa_valor = self.etapa.value if isinstance(self.etapa, EtapaProcessamento) else self.etapa
        return {
            "sucesso": self.sucesso,
            "etapa": etapa_valor,
            "prompt_id": self.prompt_id,
            "provider": self.provider,
            "modelo": self.modelo,
            "resposta_raw": self.resposta_raw[:2000] + "..." if len(self.resposta_raw) > 2000 else self.resposta_raw,
            "resposta_parsed": self.resposta_parsed,
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "tempo_ms": self.tempo_ms,
            "documento_id": self.documento_id,
            "anexos_enviados": self.anexos_enviados,
            "anexos_confirmados": self.anexos_confirmados,
            "alertas": self.alertas,
            "erro": self.erro,
            "erro_codigo": self.erro_codigo,
            "retryable": self.retryable,
            "retry_after": self.retry_after,
            "tentativas": self.tentativas,
            "pdf_fallback_used": self.pdf_fallback_used
        }


# Alias para compatibilidade com routes_pipeline.py
ResultadoEtapa = ResultadoExecucao


# ============================================================
# STAGE TOOL CONFIGURATION (F-T1, F-T2, F-T3)
# ============================================================

STAGE_TOOLS: Dict[EtapaProcessamento, List[str]] = {
    EtapaProcessamento.CORRIGIR: ["create_document", "execute_python_code"],
    EtapaProcessamento.ANALISAR_HABILIDADES: ["create_document", "execute_python_code"],
    EtapaProcessamento.GERAR_RELATORIO: ["create_document", "execute_python_code"],
    # F-T4 / F-T5 / F-T6 — aggregate desempenho reports
    EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA: ["create_document", "execute_python_code"],
    EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA: ["create_document", "execute_python_code"],
    EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA: ["create_document", "execute_python_code"],
}

PDF_SANDBOX_RULES = (
    "Use somente nome de arquivo relativo simples para o PDF, sem diretorios, "
    "sem barras e sem paths absolutos como /mnt/data, /tmp ou /home. "
    "NUNCA use open(..., 'w') nem open(..., 'wb') para criar o PDF; esse padrao "
    "e bloqueado pelo sandbox. Use APIs do reportlab diretamente, por exemplo "
    "canvas.Canvas('relatorio.pdf') ou SimpleDocTemplate('relatorio.pdf'), e "
    "chame save()/build() no objeto do reportlab."
)

STAGE_TOOL_INSTRUCTIONS: Dict[EtapaProcessamento, str] = {
    EtapaProcessamento.CORRIGIR: """
INSTRUÇÕES DE TOOL-USE PARA CORREÇÃO:
=====================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve o resultado da correção como JSON com o schema:
   {
     "nota_final": <float>,
     "questoes": [
       {
         "numero": <int>,
         "resposta_aluno": "<copie exatamente a resposta_aluno da EXTRAIR_RESPOSTAS>",
         "resposta_correta": "<copie exatamente a resposta_correta da EXTRAIR_GABARITO>",
         "nota": <float>,
         "nota_maxima": <float>,
         "acerto": <bool>,
         "feedback": "<str>"
       }
     ],
     "total_acertos": <int>,
     "total_erros": <int>,
     "feedback_geral": "<str>",
     "_avisos_documento": [
       {"codigo": "<um_codigo_unico>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<um_codigo_unico>", "questao": <int>, "explicacao": "<str>"}
     ]
   }

   **Códigos de aviso disponíveis:**
   - ILLEGIBLE_DOCUMENT — Documento inteiro ilegível ou muito borrado para processar
   - ILLEGIBLE_QUESTION — Questão específica ilegível (resposta do aluno não pode ser lida)
   - MISSING_CONTENT — Conteúdo ausente (aluno pode ter pulado a questão intencionalmente)
   - LOW_CONFIDENCE — Baixa confiança na leitura/interpretação do conteúdo

   Use _avisos_documento para problemas no documento inteiro.
   Use _avisos_questao para problemas em questões específicas (inclua o número da questão).
   Cada aviso deve ter exatamente um codigo. Nunca combine codigos com "|";
   se houver mais de um problema, crie um item de aviso separado para cada codigo.
   Codigos validos em _avisos_documento: ILLEGIBLE_DOCUMENT, MISSING_CONTENT, LOW_CONFIDENCE.
   Codigos validos em _avisos_questao: ILLEGIBLE_QUESTION, MISSING_CONTENT, LOW_CONFIDENCE.
   Se não houver avisos, envie listas vazias [].
   Nunca substitua a resposta do aluno pela resposta correta. Cada item de
   questoes deve copiar `resposta_aluno` da extração de respostas e
   `resposta_correta` do gabarito antes de atribuir nota.
   Use extensão .json e nome descritivo (ex: "correcao_aluno.json").

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com nome do aluno, matéria e data
   - Nota final em destaque
   - Questões com status (acerto/erro), nota e feedback completo
   - Resumo geral
   Nao use placeholders como "—", "N/A" ou "Nao informado" no cabecalho quando
   os metadados aparecem no prompt.
   O PDF nao pode cortar, truncar ou esconder feedback. Evite tabelas largas
   para textos longos; prefira blocos por questao ou use Paragraph/word-wrap do
   ReportLab com largura suficiente. Nao use slicing tipo texto[:80] para
   caber no layout. Se usar tabela, cada celula textual deve quebrar linha e
   preservar o conteudo essencial.
   Use extensão .pdf e nome descritivo.
""" + PDF_SANDBOX_RULES + """
""",
    EtapaProcessamento.ANALISAR_HABILIDADES: """
INSTRUÇÕES DE TOOL-USE PARA ANÁLISE DE HABILIDADES:
====================================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve a análise como JSON com o schema:
   {
     "habilidades": [
       {"nome": "<str>", "nivel": "<str>", "evidencias": ["<str>"], "nota": <float>}
     ],
     "indicadores": {
       "proficiencia_geral": <float>,
       "areas_destaque": ["<str>"],
       "areas_atencao": ["<str>"]
     },
     "recomendacoes": [
       {"tipo": "<str>", "descricao": "<str>", "prioridade": "<str>"}
     ],
     "_avisos_documento": [
       {"codigo": "<um_codigo_unico>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<um_codigo_unico>", "questao": <int>, "explicacao": "<str>"}
     ]
   }

   **Códigos de aviso disponíveis:**
   - ILLEGIBLE_DOCUMENT — Documento inteiro ilegível ou muito borrado para processar
   - ILLEGIBLE_QUESTION — Questão específica com resposta ilegível (confirme se houve problema de leitura)
   - MISSING_CONTENT — Conteúdo ausente na análise (dados upstream incompletos)
   - LOW_CONFIDENCE — Baixa confiança na análise de habilidades

   Use _avisos_documento para problemas no documento inteiro.
   Use _avisos_questao para problemas em questões específicas (inclua o número da questão).
   Cada aviso deve ter exatamente um codigo. Nunca combine codigos com "|";
   se houver mais de um problema, crie um item de aviso separado para cada codigo.
   Codigos validos em _avisos_documento: ILLEGIBLE_DOCUMENT, MISSING_CONTENT, LOW_CONFIDENCE.
   Codigos validos em _avisos_questao: ILLEGIBLE_QUESTION, MISSING_CONTENT, LOW_CONFIDENCE.
   Se não houver avisos, envie listas vazias [].
   Use exatamente um arquivo .json em create_document. Exemplo de chamada:
   {
     "documents": [
       {
         "filename": "analise_habilidades_aluno.json",
         "document_type": "analysis",
         "content": "{\"habilidades\": [], \"indicadores\": {}, \"recomendacoes\": [], \"_avisos_documento\": [], \"_avisos_questao\": []}"
       }
     ]
   }
   O campo content deve ser JSON valido serializado como string, com aspas
   duplas. Nao crie PDF, Markdown ou texto livre via create_document.
   NUNCA use placeholders como "student123", "aluno_teste", "nome_do_aluno",
   "Aluno", "Student" ou valores fictícios. Se o nome real do aluno estiver
   ausente, use o aluno_id real do contexto e registre aviso explícito.

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com identificação do aluno
   - Lista de habilidades com níveis e indicadores visuais
   - Indicadores de proficiência
   - Recomendações pedagógicas priorizadas
   O PDF nao pode cortar, truncar ou esconder evidencias/recomendacoes. Use
   Paragraph/word-wrap ou blocos verticais em vez de colunas estreitas para
   textos longos.
   Use o arquivo "analise_habilidades.pdf". O código DEVE gravar esse .pdf real
   no disco e preencher output_files com ["analise_habilidades.pdf"]. Não basta
   imprimir, retornar base64 ou descrever o PDF.
""" + PDF_SANDBOX_RULES + """
""",
    EtapaProcessamento.GERAR_RELATORIO: """
INSTRUÇÕES DE TOOL-USE PARA RELATÓRIO FINAL:
=============================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve o relatório como JSON com o schema:
   {
     "resumo_geral": "<str>",
     "pontos_fortes": ["<str>"],
     "areas_melhoria": ["<str>"],
     "recomendacoes": [
       {"tipo": "<str>", "descricao": "<str>", "prioridade": "<str>"}
     ],
     "nota_final": <float>,
     "detalhamento": "<str>",
     "_avisos_documento": [
       {"codigo": "<um_codigo_unico>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<um_codigo_unico>", "questao": <int>, "explicacao": "<str>"}
     ],
     "_fontes_utilizadas": ["<lista de etapas upstream cujos dados foram consumidos, ex: EXTRAIR_QUESTOES, CORRIGIR, ANALISAR_HABILIDADES>"]
   }

   **Códigos de aviso disponíveis:**
   - ILLEGIBLE_DOCUMENT — Documento inteiro ilegível ou muito borrado para processar
   - ILLEGIBLE_QUESTION — Questão específica com resposta ilegível (confirme se houve problema de leitura)
   - MISSING_CONTENT — Conteúdo ausente no relatório (dados upstream incompletos)
   - LOW_CONFIDENCE — Baixa confiança na geração do relatório

   Use _avisos_documento para problemas no documento inteiro.
   Use _avisos_questao para problemas em questões específicas (inclua o número da questão).
   Cada aviso deve ter exatamente um codigo. Nunca combine codigos com "|";
   se houver mais de um problema, crie um item de aviso separado para cada codigo.
   Codigos validos em _avisos_documento: ILLEGIBLE_DOCUMENT, MISSING_CONTENT, LOW_CONFIDENCE.
   Codigos validos em _avisos_questao: ILLEGIBLE_QUESTION, MISSING_CONTENT, LOW_CONFIDENCE.
   Se não houver avisos, envie listas vazias [].
   _fontes_utilizadas: liste quais etapas do pipeline você usou como fonte de dados para gerar este relatório.
   Use extensão .json e nome descritivo.

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com dados do aluno e atividade
   - Resumo geral narrativo
   - Pontos fortes destacados
   - Áreas de melhoria
   - Recomendações pedagógicas
   Se exibir `nota_final` e `proficiencia_geral`, trate como metricas separadas
   e rotule claramente (ex: "Nota final: 8/10" e "Proficiência geral: 75%").
   Nao escreva "8/10 (75%)" nem qualquer texto que faca parecer que a nota
   8/10 equivale a 75%. Se nao houver percentual confiavel, omita o percentual.
   O PDF nao pode cortar ou truncar textos longos; use Paragraph/word-wrap ou
   blocos verticais.
   Use extensão .pdf.
""" + PDF_SANDBOX_RULES + """
""",
    # F-T4: DESEMPENHO_TAREFA
    EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA: """
INSTRUÇÕES DE TOOL-USE PARA RELATÓRIO DE DESEMPENHO DA TAREFA:
==============================================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve a análise como JSON com o schema:
   {
     "resumo_turma": "<str>",
     "media_geral": <float>,
     "distribuicao_notas": {"excelente": <int>, "bom": <int>, "regular": <int>, "insuficiente": <int>},
     "questoes_dificeis": ["<str>"],
     "padroes_erros": ["<str>"],
     "recomendacoes": [{"tipo": "<str>", "descricao": "<str>", "prioridade": "<str>"}]
   }
   Use extensão .json e nome descritivo (ex: "desempenho_tarefa.json").

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com nome da atividade, turma e data
   - Média geral e distribuição de notas (tabela ou gráfico de barras)
   - Questões com maior dificuldade
   - Padrões de erros identificados
   - Recomendações pedagógicas
   Use extensão .pdf e nome descritivo.
""",
    # F-T5: DESEMPENHO_TURMA
    EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA: """
INSTRUÇÕES DE TOOL-USE PARA RELATÓRIO DE DESEMPENHO DA TURMA:
=============================================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve a análise como JSON com o schema:
   {
     "resumo_evolucao": "<str>",
     "tendencia_geral": "<str>",
     "atividades_analisadas": ["<str>"],
     "alunos_destaque": [{"aluno_id": "<str>", "motivo": "<str>"}],
     "alunos_atencao": [{"aluno_id": "<str>", "motivo": "<str>"}],
     "padroes_turma": ["<str>"],
     "recomendacoes": [{"tipo": "<str>", "descricao": "<str>", "prioridade": "<str>"}]
   }
   Use extensão .json e nome descritivo (ex: "desempenho_turma.json").

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com nome da turma, matéria e período analisado
   - Resumo da evolução ao longo das atividades
   - Distribuição de alunos por perfil (destaque / atenção)
   - Padrões identificados na turma
   - Recomendações para o professor
   Use extensão .pdf e nome descritivo.
""",
    # F-T6: DESEMPENHO_MATERIA
    EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA: """
INSTRUÇÕES DE TOOL-USE PARA RELATÓRIO DE DESEMPENHO DA MATÉRIA:
===============================================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve a análise como JSON com o schema:
   {
     "resumo_materia": "<str>",
     "comparativo_turmas": [{"turma": "<str>", "media": <float>, "observacao": "<str>"}],
     "padroes_transversais": ["<str>"],
     "turmas_destaque": ["<str>"],
     "turmas_atencao": ["<str>"],
     "efetividade_curriculo": "<str>",
     "recomendacoes": [{"tipo": "<str>", "descricao": "<str>", "prioridade": "<str>"}]
   }
   Use extensão .json e nome descritivo (ex: "desempenho_materia.json").

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com nome da matéria e período
   - Tabela comparativa de desempenho entre turmas
   - Padrões transversais identificados
   - Avaliação da efetividade curricular
   - Recomendações para revisão do currículo
   Use extensão .pdf e nome descritivo.
""",
}


# ============================================================
# PIPELINE EXECUTOR UNIFICADO
# ============================================================

class PipelineExecutor:
    """
    Executa etapas do pipeline de correção.
    
    Suporta dois modos:
    1. Modo texto (legado): extrai texto de documentos e envia como string
    2. Modo multimodal (novo): envia PDFs e imagens nativamente para a API
    """
    
    def __init__(self):
        self.prompt_manager = prompt_manager
        self.storage = storage
        self.preparador = PreparadorArquivos() if HAS_MULTIMODAL else None

    def _validar_consistencia_pdf_json_tool_outputs(
        self,
        docs_by_tool: Dict[str, List[Any]],
        expected_document_type: Optional[TipoDocumento],
    ) -> List[str]:
        """Validate minimum consistency between persisted JSON and PDF artifacts."""
        if expected_document_type not in {TipoDocumento.CORRECAO, TipoDocumento.RELATORIO_FINAL}:
            return []

        json_docs = [
            doc for doc in docs_by_tool.get("create_document", [])
            if (getattr(doc, "extensao", "") or "").lower() == ".json"
        ]
        pdf_docs = [
            doc for doc in docs_by_tool.get("execute_python_code", [])
            if (getattr(doc, "extensao", "") or "").lower() == ".pdf"
        ]
        if not json_docs or not pdf_docs:
            return []

        errors: List[str] = []
        json_doc = json_docs[-1]
        pdf_doc = pdf_docs[-1]
        json_label = getattr(json_doc, "id", None) or getattr(json_doc, "nome_arquivo", "json")
        pdf_label = getattr(pdf_doc, "id", None) or getattr(pdf_doc, "nome_arquivo", "pdf")

        try:
            json_path = self.storage.resolver_caminho_documento(json_doc)
            with open(json_path, "r", encoding="utf-8") as fh:
                json_data = json.load(fh)
        except Exception as exc:
            return [f"JSON {json_label} não pôde ser lido para comparar com PDF: {exc}"]

        try:
            pdf_path = self.storage.resolver_caminho_documento(pdf_doc)
            with fitz.open(str(pdf_path)) as pdf:
                pdf_text = "\n".join(page.get_text("text") for page in pdf)
        except Exception as exc:
            return [f"PDF {pdf_label} não pôde ser lido para comparar com JSON: {exc}"]

        text = (pdf_text or "").replace(",", ".")

        def _as_float(value: Any) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                if math.isfinite(float(value)):
                    return float(value)
                return None
            if isinstance(value, str):
                cleaned = value.strip().replace(",", ".")
                if cleaned.upper() in {"N/A", "NA", ""}:
                    return None
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            return None

        def _format_num(value: float) -> str:
            if float(value).is_integer():
                return str(int(value))
            return f"{value:.2f}".rstrip("0").rstrip(".")

        def _placeholder_header(label_pattern: str) -> bool:
            placeholder = (
                r"(?:[-–—?]+|n/?a|nao\s+informad[oa]|não\s+informad[oa]|"
                r"nao\s+definid[oa]|não\s+definid[oa])"
            )
            return bool(
                re.search(
                    rf"\b(?:{label_pattern})\s*:\s*{placeholder}(?=\s|$|\|)",
                    pdf_text or "",
                    flags=re.IGNORECASE,
                )
            )

        expected_grade = _as_float(json_data.get("nota_final") if isinstance(json_data, dict) else None)
        if expected_grade is not None:
            grade_match = re.search(
                r"nota\s*final\s*[:\-]?\s*(n/?a|[0-9]+(?:\.[0-9]+)?)",
                text,
                flags=re.IGNORECASE,
            )
            if not grade_match:
                errors.append(f"PDF {pdf_label} sem nota_final verificável para JSON {json_label}")
            else:
                grade_raw = grade_match.group(1)
                if grade_raw.lower().replace("/", "") in {"na", "n/a"}:
                    errors.append(
                        f"PDF {pdf_label} mostra nota_final N/A, mas JSON {json_label} tem "
                        f"nota_final {_format_num(expected_grade)}"
                    )
                else:
                    pdf_grade = _as_float(grade_raw)
                    if pdf_grade is None or abs(pdf_grade - expected_grade) > 0.01:
                        errors.append(
                            f"PDF {pdf_label} mostra nota_final {grade_raw}, mas JSON "
                            f"{json_label} tem nota_final {_format_num(expected_grade)}"
                        )

            if re.search(r"nota\s*final[^\n]{0,100}\([^\)]*%", text, flags=re.IGNORECASE):
                errors.append(
                    f"PDF {pdf_label} mistura nota_final com percentual/proficiência no mesmo rótulo"
                )

        if expected_document_type == TipoDocumento.CORRECAO and isinstance(json_data, dict):
            for label_pattern, label in (
                (r"aluno", "aluno"),
                (r"mat[eé]ria", "materia"),
                (r"atividade", "atividade"),
                (r"data", "data"),
            ):
                if _placeholder_header(label_pattern):
                    errors.append(
                        f"PDF {pdf_label} usa placeholder no cabeçalho para {label}"
                    )

            checked_questions = 0
            for question in json_data.get("questoes") or []:
                if not isinstance(question, dict):
                    continue
                numero = question.get("numero")
                expected_note = _as_float(question.get("nota"))
                if numero is None or expected_note is None:
                    continue
                question_match = re.search(
                    rf"quest(?:a|ã)o\s*{re.escape(str(numero))}\b.*?nota\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)",
                    text,
                    flags=re.IGNORECASE | re.DOTALL,
                )
                if not question_match:
                    continue
                checked_questions += 1
                pdf_note_raw = question_match.group(1)
                pdf_note = _as_float(pdf_note_raw)
                if pdf_note is None or abs(pdf_note - expected_note) > 0.01:
                    errors.append(
                        f"PDF {pdf_label} mostra nota {pdf_note_raw} na questão {numero}, "
                        f"mas JSON {json_label} tem nota {_format_num(expected_note)}"
                    )
            if json_data.get("questoes") and checked_questions == 0:
                errors.append(f"PDF {pdf_label} sem notas por questão verificáveis para CORRIGIR")

            feedback_geral = json_data.get("feedback_geral")
            if isinstance(feedback_geral, str) and len(feedback_geral.strip()) >= 120:
                def _norm(value: str) -> str:
                    return re.sub(r"\s+", " ", value or "").strip().lower()

                def _word_text(value: str) -> str:
                    return " ".join(re.findall(r"\w+", _norm(value), flags=re.UNICODE))

                def _keywords(value: str) -> set[str]:
                    stopwords = {
                        "aluno", "aluna", "diana", "omega", "questao", "questoes",
                        "resposta", "respostas", "correta", "incorreta", "desempenho",
                        "geral", "muito", "mais", "para", "como", "onde", "sobre",
                        "esta", "este", "essa", "esse", "pela", "pelo", "pelos",
                        "pelas", "uma", "com", "das", "dos", "que", "deve",
                        "pode", "ponto", "pontos",
                    }
                    return {
                        word
                        for word in re.findall(r"\w+", _norm(value), flags=re.UNICODE)
                        if len(word) >= 5 and word not in stopwords
                    }

                expected_feedback = _norm(feedback_geral)
                pdf_full_text = _norm(pdf_text or "")
                expected_words = _word_text(feedback_geral)
                pdf_words = _word_text(pdf_text or "")
                expected_word_list = expected_words.split()

                feedback_match = re.search(
                    (
                        r"(?:feedback\s+geral(?:\s+da\s+avalia[cç][aã]o)?|"
                        r"parecer(?:\s+pedag[oó]gico)?\s+geral|"
                        r"coment[aá]rio\s+pedag[oó]gico\s+geral)"
                        r"\s*[:\-]?\s*(.+)$"
                    ),
                    pdf_text or "",
                    flags=re.IGNORECASE | re.DOTALL,
                )
                pdf_feedback = _norm(feedback_match.group(1)) if feedback_match else ""
                full_feedback_present = expected_feedback in pdf_full_text

                prefix_size = min(12, len(expected_word_list))
                suffix_size = min(8, len(expected_word_list))
                prefix = " ".join(expected_word_list[:prefix_size])
                suffix = " ".join(expected_word_list[-suffix_size:])
                prefix_found = bool(prefix) and prefix in pdf_words
                suffix_found = bool(suffix) and suffix in pdf_words
                feedback_keywords = _keywords(feedback_geral)
                pdf_feedback_keywords = _keywords(pdf_feedback)
                keyword_overlap = feedback_keywords & pdf_feedback_keywords
                overlap_ratio = (
                    len(keyword_overlap) / len(feedback_keywords)
                    if feedback_keywords
                    else 0.0
                )
                min_len = min(160, int(len(feedback_geral.strip()) * 0.45))
                paraphrase_present = (
                    bool(pdf_feedback)
                    and len(pdf_feedback) >= min_len
                    and (
                        len(keyword_overlap) >= 6
                        or overlap_ratio >= 0.35
                    )
                )

                if not full_feedback_present and not prefix_found and not paraphrase_present:
                    errors.append(
                        f"PDF {pdf_label} sem feedback_geral do JSON verificável para CORRIGIR"
                    )
                else:
                    measured_feedback = pdf_feedback or expected_feedback if full_feedback_present else pdf_feedback
                    if (
                        not full_feedback_present
                        and not paraphrase_present
                        and (len(measured_feedback) < min_len or not suffix_found)
                    ):
                        errors.append(
                            f"PDF {pdf_label} parece truncar Feedback Geral: "
                            f"{len(measured_feedback)} chars no PDF contra {len(feedback_geral.strip())} no JSON"
                        )
                    if pdf_feedback and not re.search(r"[.!?)]\s*$", pdf_feedback):
                        errors.append(
                            f"PDF {pdf_label} termina Feedback Geral sem pontuação final; "
                            "possível corte de layout"
                        )

        return errors
    
    # ============================================================
    # MÉTODOS AUXILIARES PARA OBTER PROVIDER
    # ============================================================

    def _get_provider_config(self, provider_id: str = None) -> Dict[str, Any]:
        """
        Obtém configuração do provider para uso com ClienteAPIMultimodal.
        Usa a função unificada resolve_provider_config do chat_service.
        """
        from chat_service import resolve_provider_config
        config = resolve_provider_config(provider_id)
        print(f"[DEBUG] Provider config: tipo={config['tipo']}, modelo={config['modelo']}")
        return config
    
    def _get_provider_legacy(self, provider_name: str = None):
        """
        Obtém provider para uso legado (modo texto).
        Usa a função unificada resolve_provider_config e converte para objeto Provider.
        """
        from ai_providers import OpenAIProvider, AnthropicProvider, GeminiProvider
        from chat_service import resolve_provider_config

        # Usar função unificada para obter config
        config = resolve_provider_config(provider_name)

        # Converter config para objeto Provider
        tipo = config["tipo"]
        api_key = config["api_key"]
        modelo = config["modelo"]
        base_url = config.get("base_url")

        if tipo == "openai":
            return OpenAIProvider(api_key=api_key, model=modelo, base_url=base_url)
        elif tipo == "anthropic":
            return AnthropicProvider(api_key=api_key, model=modelo)
        elif tipo == "google":
            return GeminiProvider(api_key=api_key, model=modelo)
        else:
            raise ValueError(f"Tipo de provider não suportado para modo legado: {tipo}")
    
    # ============================================================
    # MÉTODO PRINCIPAL - EXECUTAR ETAPA (LEGADO + MULTIMODAL)
    # ============================================================
    
    async def executar_etapa(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        prompt_customizado: Optional[str] = None,  # NOVO: texto do prompt customizado
        provider_name: Optional[str] = None,
        variaveis_extra: Optional[Dict[str, str]] = None,
        salvar_resultado: bool = True,
        usar_multimodal: bool = True,  # NOVO: flag para usar visão
        criar_nova_versao: bool = False  # NOVO: cria versão ao invés de sobrescrever
    ) -> ResultadoExecucao:
        """
        Executa uma etapa do pipeline.

        Args:
            etapa: Qual etapa executar
            atividade_id: ID da atividade
            aluno_id: ID do aluno (necessário para etapas de aluno)
            prompt_id: ID do prompt a usar (ou usa o padrão)
            prompt_customizado: Texto do prompt customizado (override)
            provider_name: Nome do provider de IA (ou usa o padrão)
            variaveis_extra: Variáveis adicionais para o prompt
            salvar_resultado: Se deve salvar o resultado como documento
            usar_multimodal: Se deve enviar arquivos como anexos multimodais
            criar_nova_versao: Se True, cria nova versão do documento ao invés de sobrescrever
        """
        inicio = time.time()
        prompt_usado_id = ""
        provider_nome = ""
        provider_modelo = ""

        try:
            # 1. Buscar contexto
            atividade = self.storage.get_atividade(atividade_id)
            if not atividade:
                return self._erro(etapa, "Atividade não encontrada")

            turma = self.storage.get_turma(atividade.turma_id)
            materia = self.storage.get_materia(turma.materia_id) if turma else None

            # 2. Buscar prompt
            if prompt_id:
                prompt = self.prompt_manager.get_prompt(prompt_id)
            else:
                prompt = self.prompt_manager.get_prompt_padrao(etapa, materia.id if materia else None)

            if not prompt and not prompt_customizado:
                return self._erro(etapa, f"Nenhum prompt disponível para etapa {etapa.value}")
            prompt_usado_id = prompt.id if prompt else "customizado"

            # Se tiver prompt customizado, criar um prompt temporário
            if prompt_customizado:
                from prompts import PromptTemplate
                prompt = PromptTemplate(
                    id="customizado",
                    nome="Prompt Customizado",
                    etapa=etapa,
                    texto=prompt_customizado,
                    texto_sistema=prompt.texto_sistema if prompt else None,
                    is_padrao=False
                )
            
            # 3. Decidir modo de execução
            if usar_multimodal and HAS_MULTIMODAL:
                return await self._executar_multimodal(
                    etapa, atividade_id, aluno_id, prompt, materia, atividade,
                    provider_name, variaveis_extra, salvar_resultado, inicio,
                    criar_nova_versao
                )
            else:
                return await self._executar_texto(
                    etapa, atividade_id, aluno_id, prompt, materia, atividade,
                    provider_name, variaveis_extra, salvar_resultado, inicio,
                    criar_nova_versao
                )
            
        except Exception as e:
            return self._erro(etapa, str(e), prompt_usado_id, provider_nome, provider_modelo)
    
    async def _executar_texto(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        prompt: PromptTemplate,
        materia: Any,
        atividade: Any,
        provider_name: Optional[str],
        variaveis_extra: Optional[Dict[str, str]],
        salvar_resultado: bool,
        inicio: float,
        criar_nova_versao: bool = False
    ) -> ResultadoExecucao:
        """Executa etapa no modo texto (legado)"""
        
        # Buscar provider
        provider = self._get_provider_legacy(provider_name)
        if not provider:
            return self._erro(etapa, "Nenhum provider de IA disponível")
        
        # Preparar variáveis (extrai texto dos documentos)
        variaveis = self._preparar_variaveis_texto(etapa, atividade_id, aluno_id, materia, atividade, usar_multimodal=False)
        if variaveis_extra:
            variaveis.update(variaveis_extra)

        # Log de debug: variáveis disponíveis
        _logger.debug(
            "Variáveis preparadas para renderização",
            stage=etapa.value if hasattr(etapa, 'value') else str(etapa),
            variaveis_disponiveis=list(variaveis.keys())
        )

        # Renderizar prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema_renderizado = prompt.render_sistema(**variaveis) or None

        # Verificar variáveis não substituídas
        import re as re_module
        nao_substituidas = re_module.findall(r'\{\{(\w+)\}\}', prompt_renderizado)
        if nao_substituidas:
            _logger.warning(
                "Variáveis não substituídas no prompt",
                stage=etapa.value if hasattr(etapa, 'value') else str(etapa),
                variaveis_faltantes=nao_substituidas
            )
        
        # Executar IA
        response = await provider.complete(prompt_renderizado, prompt_sistema_renderizado)

        # Parsear resposta com contexto para logging
        resposta_parsed = self._parsear_resposta(
            response.content,
            context={
                "stage": etapa.value if hasattr(etapa, 'value') else str(etapa),
                "provider": provider.name,
                "model": provider.model,
                "atividade_id": atividade_id,
                "aluno_id": aluno_id
            }
        )
        
        tempo_ms = (time.time() - inicio) * 1000

        erro_parseado = self._erro_resposta_parseada(etapa, resposta_parsed)
        if erro_parseado:
            self._registrar_custo_resposta_invalida(
                etapa=etapa,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                provider=provider.name,
                modelo=provider.model,
                tokens_entrada=response.input_tokens,
                tokens_saida=response.output_tokens or response.tokens_used,
                erro=erro_parseado,
                tempo_ms=tempo_ms,
                prompt_id=prompt.id,
                source="executar_texto",
            )
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=provider.name,
                modelo=provider.model,
                resposta_raw=response.content,
                resposta_parsed=resposta_parsed,
                erro=erro_parseado,
                tokens_entrada=response.input_tokens,
                tokens_saida=response.output_tokens or response.tokens_used,
                tempo_ms=tempo_ms,
            )
        
        # Salvar resultado se solicitado
        documento_id = None
        if salvar_resultado:
            documento_id = await self._salvar_resultado(
                etapa, atividade_id, aluno_id,
                response.content, resposta_parsed,
                provider.name, provider.model, prompt.id,
                response.tokens_used, tempo_ms,
                tokens_entrada=response.input_tokens,
                tokens_saida=response.output_tokens,
                criar_nova_versao=criar_nova_versao
            )
        
        return ResultadoExecucao(
            sucesso=True,
            etapa=etapa,
            prompt_usado=prompt_renderizado,
            prompt_id=prompt.id,
            provider=provider.name,
            modelo=provider.model,
            resposta_raw=response.content,
            resposta_parsed=resposta_parsed,
            tokens_entrada=response.input_tokens,
            tokens_saida=response.output_tokens or response.tokens_used,
            tempo_ms=tempo_ms,
            documento_id=documento_id
        )
    
    async def _executar_multimodal(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        prompt: PromptTemplate,
        materia: Any,
        atividade: Any,
        provider_id: Optional[str],
        variaveis_extra: Optional[Dict[str, str]],
        salvar_resultado: bool,
        inicio: float,
        criar_nova_versao: bool = False
    ) -> ResultadoExecucao:
        """Executa etapa no modo multimodal (envia arquivos nativamente)"""
        
        # Obter configuração do provider
        config = self._get_provider_config(provider_id)
        cliente = ClienteAPIMultimodal(config)
        
        # Preparar variáveis com conteúdo de documentos (reutiliza lógica do modo texto)
        variaveis = self._preparar_variaveis_texto(etapa, atividade_id, aluno_id, materia, atividade, usar_multimodal=True)

        if variaveis_extra:
            variaveis.update(variaveis_extra)

        # Coletar arquivos para anexar (multimodal envia arquivos como anexos)
        arquivos = self._coletar_arquivos_para_etapa(etapa, atividade_id, aluno_id)

        # Adicionar contexto de arquivos JSON já processados
        contexto_json = self._preparar_contexto_json(atividade_id, aluno_id, etapa)

        # Verificar documentos faltantes e falhar se etapa depende deles
        docs_faltantes = contexto_json.pop("_documentos_faltantes", [])
        docs_carregados = contexto_json.pop("_documentos_carregados", [])

        if docs_faltantes:
            _logger.error(
                f"Documentos obrigatórios faltando para {etapa.value}",
                faltantes=docs_faltantes,
                carregados=docs_carregados
            )
            # Criar erro estruturado para o JSON
            erro_pipeline = criar_erro_pipeline(
                tipo=ERRO_DOCUMENTO_FALTANTE,
                mensagem=f"Documentos obrigatórios faltando para {etapa.value}: {', '.join(docs_faltantes)}. Execute as etapas anteriores primeiro.",
                severidade=SeveridadeErro.CRITICO,
                etapa=etapa.value if hasattr(etapa, 'value') else str(etapa)
            )
            # Salvar JSON com erro para debug e UI
            erro_content = {
                "_erro_pipeline": erro_pipeline,
                "_documentos_faltantes": docs_faltantes,
                "_documentos_carregados": docs_carregados
            }
            if salvar_resultado:
                await self._salvar_resultado(
                    etapa, atividade_id, aluno_id,
                    "", erro_content,
                    config.get("tipo", "unknown"), config.get("modelo", "unknown"),
                    prompt.id, 0, (time.time() - inicio) * 1000,
                    gerar_formatos_extras=False
                )
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado="",
                prompt_id=prompt.id,
                provider=config.get("tipo", "unknown"),
                modelo=config.get("modelo", "unknown"),
                erro=erro_pipeline["mensagem"],
                anexos_enviados=[],
                tempo_ms=(time.time() - inicio) * 1000
            )

        variaveis.update(contexto_json)

        # Log de debug: variáveis disponíveis
        _logger.debug(
            "Variáveis preparadas para renderização (multimodal)",
            stage=etapa.value if hasattr(etapa, 'value') else str(etapa),
            variaveis_disponiveis=list(variaveis.keys())
        )

        # Renderizar prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema_renderizado = prompt.render_sistema(**variaveis) or None

        # Verificar variáveis não substituídas
        import re as re_module
        nao_substituidas = re_module.findall(r'\{\{(\w+)\}\}', prompt_renderizado)
        if nao_substituidas:
            _logger.warning(
                "Variáveis não substituídas no prompt (multimodal)",
                stage=etapa.value if hasattr(etapa, 'value') else str(etapa),
                variaveis_faltantes=nao_substituidas
            )

        # IMPORTANTE: Verificar se há arquivos para etapas que REQUEREM arquivos
        etapas_requerem_arquivo = [
            EtapaProcessamento.EXTRAIR_QUESTOES,
            EtapaProcessamento.EXTRAIR_GABARITO,
            EtapaProcessamento.EXTRAIR_RESPOSTAS
        ]
        if etapa in etapas_requerem_arquivo and not arquivos:
            import logging
            logger = logging.getLogger("pipeline")
            logger.error(f"FALHA: Etapa {etapa.value} requer arquivos mas nenhum foi encontrado!")

            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=config.get("tipo", "unknown"),
                modelo=config.get("modelo", "unknown"),
                erro=f"Arquivo não encontrado para {etapa.value}. Verifique se o documento foi enviado corretamente.",
                anexos_enviados=[],
                tempo_ms=(time.time() - inicio) * 1000
            )

        # Verificar tamanho total dos arquivos (limite: 50MB para evitar erro 413)
        LIMITE_TAMANHO_MB = 50
        tamanho_total_bytes = sum(os.path.getsize(f) for f in arquivos if os.path.exists(f))
        tamanho_total_mb = tamanho_total_bytes / (1024 * 1024)
        
        if tamanho_total_mb > LIMITE_TAMANHO_MB:
            import logging
            logger = logging.getLogger("pipeline")
            logger.error(f"FALHA: Tamanho total dos arquivos ({tamanho_total_mb:.1f}MB) excede o limite de {LIMITE_TAMANHO_MB}MB!")
            
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=config.get("tipo", "unknown"),
                modelo=config.get("modelo", "unknown"),
                erro=f"Tamanho total dos arquivos ({tamanho_total_mb:.1f}MB) excede o limite de {LIMITE_TAMANHO_MB}MB. Remova arquivos desnecessários ou use arquivos menores.",
                anexos_enviados=[],
                tempo_ms=(time.time() - inicio) * 1000
            )

        arquivos_envio = list(arquivos)
        paginas_pdf_renderizadas: List[str] = []
        temp_dir_paginas_pdf = None
        if etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            paginas_pdf_renderizadas, temp_dir_paginas_pdf = (
                self._renderizar_paginas_pdf_sem_texto_para_anexos(
                    arquivos,
                    provider_tipo=config.get("tipo", ""),
                )
            )
            if paginas_pdf_renderizadas:
                arquivos_envio.extend(paginas_pdf_renderizadas)
                _logger.info(
                    "Paginas PDF sem texto renderizadas para EXTRAIR_RESPOSTAS",
                    quantidade=len(paginas_pdf_renderizadas),
                    provider=config.get("tipo", "unknown"),
                )

        # Enviar para IA com anexos. Para extrações, uma resposta inválida pode
        # receber uma segunda tentativa explícita no mesmo provider/modelo.
        max_tentativas_validacao = 2 if etapa in etapas_requerem_arquivo else 1
        mensagem_tentativa = prompt_renderizado
        tentativas_validacao = 0
        tokens_entrada_total = 0
        tokens_saida_total = 0
        resultado = None
        resposta_parsed = None
        erro_parseado = None
        erro_scan_suspeito = None
        erro_validacao = None

        try:
            for indice_tentativa in range(max_tentativas_validacao):
                tentativas_validacao = indice_tentativa + 1
                resultado = await cliente.enviar_com_anexos(
                    mensagem=mensagem_tentativa,
                    arquivos=arquivos_envio,
                    system_prompt=prompt_sistema_renderizado,
                    verificar_anexos=True
                )
                tokens_entrada_total += int(getattr(resultado, "tokens_entrada", 0) or 0)
                tokens_saida_total += int(getattr(resultado, "tokens_saida", 0) or 0)

                if not resultado.sucesso:
                    break

                # Parsear resposta com contexto para logging
                resposta_parsed = self._parsear_resposta(
                    resultado.resposta,
                    context={
                        "stage": etapa.value if hasattr(etapa, 'value') else str(etapa),
                        "provider": resultado.provider,
                        "model": resultado.modelo,
                        "atividade_id": atividade_id,
                        "aluno_id": aluno_id
                    }
                )
                erro_parseado = self._erro_resposta_parseada(etapa, resposta_parsed)
                erro_scan_suspeito = None
                erro_questoes_faltantes = None

                if not erro_parseado:
                    erro_scan_suspeito = self._erro_respostas_scan_suspeitas(
                        resposta_parsed,
                        tem_paginas_pdf_renderizadas=bool(paginas_pdf_renderizadas),
                    )

                if not erro_parseado and not erro_scan_suspeito:
                    if etapa == EtapaProcessamento.EXTRAIR_QUESTOES and resposta_parsed:
                        questoes = resposta_parsed.get("questoes", [])
                        if len(questoes) == 0:
                            erro_questoes_faltantes = (
                                "Nenhuma questão foi extraída do documento. "
                                "Verifique se o arquivo de enunciado está correto e legível."
                            )

                erro_validacao = erro_parseado or erro_scan_suspeito or erro_questoes_faltantes
                if not erro_validacao:
                    break

                if tentativas_validacao >= max_tentativas_validacao:
                    break

                _logger.warning(
                    "Retry explicito de validacao multimodal no mesmo modelo",
                    stage=etapa.value if hasattr(etapa, 'value') else str(etapa),
                    provider=resultado.provider,
                    model=resultado.modelo,
                    erro=erro_validacao,
                    tentativa=tentativas_validacao,
                )
                mensagem_tentativa = self._montar_prompt_retry_validacao_multimodal(
                    etapa=etapa,
                    prompt_original=prompt_renderizado,
                    erro=erro_validacao,
                    resposta_raw=resultado.resposta,
                )
        finally:
            if temp_dir_paginas_pdf is not None:
                temp_dir_paginas_pdf.cleanup()

        tempo_ms = (time.time() - inicio) * 1000
        if resultado is None:
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=config.get("tipo", "unknown"),
                modelo=config.get("modelo", "unknown"),
                erro=f"Nenhuma tentativa de envio foi executada para {etapa.value}.",
                tempo_ms=tempo_ms,
            )
        
        if not resultado.sucesso:
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                erro=resultado.erro,
                erro_codigo=getattr(resultado, 'erro_codigo', None),
                retryable=getattr(resultado, 'retryable', False),
                retry_after=getattr(resultado, 'retry_after', None),
                tentativas=tentativas_validacao,
                anexos_enviados=resultado.anexos_enviados,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                tempo_ms=tempo_ms
            )

        if erro_parseado:
            self._registrar_custo_resposta_invalida(
                etapa=etapa,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                erro=erro_parseado,
                tempo_ms=tempo_ms,
                prompt_id=prompt.id,
                source="executar_multimodal",
                tentativas_validacao=tentativas_validacao,
            )
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                resposta_raw=resultado.resposta,
                resposta_parsed=resposta_parsed,
                erro=erro_parseado,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                anexos_enviados=resultado.anexos_enviados,
                anexos_confirmados=resultado.anexos_confirmados,
                tempo_ms=tempo_ms,
                tentativas=tentativas_validacao,
            )
        if erro_scan_suspeito:
            self._registrar_custo_resposta_invalida(
                etapa=etapa,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                erro=erro_scan_suspeito,
                tempo_ms=tempo_ms,
                prompt_id=prompt.id,
                source="executar_multimodal",
                tentativas_validacao=tentativas_validacao,
            )
            return ResultadoExecucao(
                sucesso=False,
                etapa=etapa,
                prompt_usado=prompt_renderizado,
                prompt_id=prompt.id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                resposta_raw=resultado.resposta,
                resposta_parsed=resposta_parsed,
                erro=erro_scan_suspeito,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                anexos_enviados=resultado.anexos_enviados,
                anexos_confirmados=resultado.anexos_confirmados,
                tempo_ms=tempo_ms,
                tentativas=tentativas_validacao,
            )
        alertas = resposta_parsed.get("alertas", []) if resposta_parsed else []
        
        # Verificar se anexo foi processado
        if not resultado.anexos_confirmados and arquivos:
            alertas.append({
                "tipo": "aviso",
                "mensagem": "Não foi possível confirmar se a IA processou os documentos corretamente"
            })

        # Validar extração de questões - detectar questões faltantes
        if etapa == EtapaProcessamento.EXTRAIR_QUESTOES and resposta_parsed:
            questoes = resposta_parsed.get("questoes", [])
            if len(questoes) == 0:
                erro_pipeline = criar_erro_pipeline(
                    tipo=ERRO_QUESTOES_FALTANTES,
                    mensagem="Nenhuma questão foi extraída do documento. Verifique se o arquivo de enunciado está correto e legível.",
                    severidade=SeveridadeErro.CRITICO,
                    etapa=etapa.value if hasattr(etapa, 'value') else str(etapa)
                )
                # Salvar JSON com erro
                erro_content = {
                    "_erro_pipeline": erro_pipeline,
                    "questoes": []
                }
                if salvar_resultado:
                    await self._salvar_resultado(
                        etapa, atividade_id, aluno_id,
                        resultado.resposta, erro_content,
                        resultado.provider, resultado.modelo, prompt.id,
                        tokens_entrada_total + tokens_saida_total,
                        tempo_ms,
                        gerar_formatos_extras=False,
                        tokens_entrada=tokens_entrada_total,
                        tokens_saida=tokens_saida_total,
                    )
                return ResultadoExecucao(
                    sucesso=False,
                    etapa=etapa,
                    prompt_usado=prompt_renderizado,
                    prompt_id=prompt.id,
                    provider=resultado.provider,
                    modelo=resultado.modelo,
                    resposta_raw=resultado.resposta,
                    resposta_parsed=erro_content,
                    erro=erro_pipeline["mensagem"],
                    tokens_entrada=tokens_entrada_total,
                    tokens_saida=tokens_saida_total,
                    anexos_enviados=resultado.anexos_enviados,
                    anexos_confirmados=resultado.anexos_confirmados,
                    tempo_ms=tempo_ms,
                    tentativas=tentativas_validacao,
                )

        # Validar extração de respostas - detectar falha silenciosa
        if etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS and resposta_parsed:
            respostas = resposta_parsed.get("respostas", [])
            total = len(respostas)
            em_branco = sum(1 for r in respostas if r.get("em_branco", False))

            if total > 0 and em_branco == total:
                alertas.append({
                    "tipo": "erro_extracao",
                    "severidade": "critico",
                    "codigo": "ALL_RESPONSES_BLANK",
                    "mensagem": f"ERRO: Todas as {total} questões foram marcadas como em branco. "
                               f"Verifique se o arquivo de respostas do aluno está correto e legível."
                })
            elif total > 0 and em_branco >= total * 0.8:  # 80%+ em branco
                alertas.append({
                    "tipo": "aviso_extracao",
                    "severidade": "alto",
                    "codigo": "MOSTLY_BLANK_RESPONSES",
                    "mensagem": f"AVISO: {em_branco} de {total} questões ({int(em_branco/total*100)}%) "
                               f"foram marcadas como em branco. Verifique o arquivo de respostas."
                })

        # Salvar resultado
        documento_id = None
        if salvar_resultado:
            documento_id = await self._salvar_resultado(
                etapa, atividade_id, aluno_id,
                resultado.resposta, resposta_parsed,
                resultado.provider, resultado.modelo, prompt.id,
                tokens_entrada_total + tokens_saida_total, tempo_ms,
                tokens_entrada=tokens_entrada_total,
                tokens_saida=tokens_saida_total,
                criar_nova_versao=criar_nova_versao
            )
        
        return ResultadoExecucao(
            sucesso=True,
            etapa=etapa,
            prompt_usado=prompt_renderizado,
            prompt_id=prompt.id,
            provider=resultado.provider,
            modelo=resultado.modelo,
            resposta_raw=resultado.resposta,
            resposta_parsed=resposta_parsed,
            tokens_entrada=tokens_entrada_total,
            tokens_saida=tokens_saida_total,
            tempo_ms=tempo_ms,
            documento_id=documento_id,
            anexos_enviados=resultado.anexos_enviados,
            anexos_confirmados=resultado.anexos_confirmados,
            alertas=alertas,
            tentativas=tentativas_validacao,
        )

    def _montar_prompt_retry_validacao_multimodal(
        self,
        *,
        etapa: EtapaProcessamento,
        prompt_original: str,
        erro: str,
        resposta_raw: str,
    ) -> str:
        """Build an explicit same-model retry prompt after invalid extraction output."""
        etapa_nome = etapa.value if hasattr(etapa, "value") else str(etapa)
        resposta_anterior = truncate_for_log(resposta_raw or "", 1800)
        instrucoes_especificas = ""

        if etapa == EtapaProcessamento.EXTRAIR_GABARITO:
            instrucoes_especificas = """
Para EXTRAIR_GABARITO:
- Reanalise o PDF/arquivo de gabarito anexado e as questões já extraídas.
- Use MISSING_CONTENT apenas para questões individualmente ausentes ou ilegíveis.
- Se houver respostas legíveis no gabarito, extraia essas respostas; não marque todas como MISSING_CONTENT sem evidência.
"""
        elif etapa == EtapaProcessamento.EXTRAIR_QUESTOES:
            instrucoes_especificas = """
Para EXTRAIR_QUESTOES:
- Reanalise o enunciado anexado e extraia todas as questões visíveis.
- Se uma questão estiver parcialmente ilegível, mantenha a questão e registre aviso específico em _avisos_questao.
"""
        elif etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            instrucoes_especificas = """
Para EXTRAIR_RESPOSTAS:
- Reanalise a prova respondida anexada.
- Não deixe resposta_aluno vazio sem marcar explicitamente em_branco=true ou ilegivel=true.
- Não marque todas as questões como vazias/ilegíveis sem evidência visual clara.
"""

        return f"""{prompt_original}

---

RETRY EXPLICITO DE VALIDACAO, NO MESMO PROVIDER E MODELO.

A resposta anterior desta mesma etapa ({etapa_nome}) falhou na validação bloqueante:
{erro}

Trecho da resposta anterior que falhou:
```text
{resposta_anterior}
```

Isto não é fallback e não troca de modelo. Refaça a extração usando os mesmos anexos originais.

Regras obrigatórias:
- Retorne APENAS JSON válido.
- Não use Markdown, comentários, texto antes ou depois do JSON.
- Use exatamente o schema solicitado no prompt original.
- Não invente dados; quando algo estiver ausente ou ilegível, use os avisos estruturados do schema.
{instrucoes_especificas}
"""
    
    def _valor_data_documento(self, documento: Any) -> str:
        """Return a sortable timestamp string for a document, when available."""
        valor = getattr(documento, "criado_em", None) or getattr(documento, "atualizado_em", None)
        if isinstance(valor, datetime):
            return valor.isoformat()
        if isinstance(valor, str):
            return valor
        return ""

    def _documentos_novos_primeiro(self, documentos: List[Any]) -> List[Any]:
        """Sort documents by creation date, keeping existing order when dates are absent."""
        return sorted(
            list(documentos or []),
            key=self._valor_data_documento,
            reverse=True,
        )

    def _documento_mais_recente(
        self,
        documentos: List[Any],
        tipo: TipoDocumento,
        extensao: Optional[str] = None,
    ) -> Optional[Any]:
        """Select the newest document for a type, without falling back to older artifacts."""
        extensao_normalizada = extensao.lower() if extensao else None
        for doc in self._documentos_novos_primeiro(documentos):
            if doc.tipo != tipo:
                continue
            if extensao_normalizada and str(doc.extensao or "").lower() != extensao_normalizada:
                continue
            return doc
        return None

    def _status_documento(self, documento: Any) -> str:
        status = getattr(documento, "status", "")
        return getattr(status, "value", status) if isinstance(getattr(status, "value", status), str) else ""

    def _cost_run_id_documento(self, documento: Any) -> Optional[str]:
        metadata = getattr(documento, "metadata", None)
        if isinstance(metadata, dict):
            cost_run_id = metadata.get("cost_run_id")
            if cost_run_id:
                return str(cost_run_id)
        return None

    def _documento_em_erro(self, documento: Any) -> bool:
        return self._status_documento(documento).lower() == StatusProcessamento.ERRO.value

    def _documentos_da_ultima_execucao(
        self,
        documentos: List[Any],
        tipo: TipoDocumento,
    ) -> List[Any]:
        docs_tipo = [
            doc
            for doc in self._documentos_novos_primeiro(documentos)
            if doc.tipo == tipo
        ]
        if not docs_tipo:
            return []

        doc_mais_recente = docs_tipo[0]
        cost_run_id = self._cost_run_id_documento(doc_mais_recente)
        if not cost_run_id:
            return [doc_mais_recente]

        return [
            doc
            for doc in docs_tipo
            if self._cost_run_id_documento(doc) == cost_run_id
        ]

    def _documento_json_da_ultima_execucao(
        self,
        documentos: List[Any],
        tipo: TipoDocumento,
    ) -> Optional[Any]:
        """Return the JSON artifact from the latest run, never an older run's JSON."""
        for doc in self._documentos_da_ultima_execucao(documentos, tipo):
            if str(getattr(doc, "extensao", "") or "").lower() == ".json":
                return doc
        return None

    def _coletar_arquivos_para_etapa(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str]
    ) -> List[str]:
        """Coleta arquivos relevantes para uma etapa específica"""
        import logging
        logger = logging.getLogger("pipeline")

        arquivos = []

        # Documentos base da atividade
        docs_base = self._documentos_novos_primeiro(self.storage.listar_documentos(atividade_id))

        # Documentos do aluno (se aplicável)
        docs_aluno = (
            self._documentos_novos_primeiro(self.storage.listar_documentos(atividade_id, aluno_id))
            if aluno_id
            else []
        )

        logger.info(f"Coletando arquivos para {etapa.value}: docs_base={len(docs_base)}, docs_aluno={len(docs_aluno)}")

        def _normalizar_e_verificar(doc) -> Optional[str]:
            """
            Resolve o caminho do documento usando storage.resolver_caminho_documento().
            Isso automaticamente baixa do Supabase se não existir localmente.
            """
            if not doc.caminho_arquivo:
                logger.warning(f"  Doc {doc.id} ({doc.tipo.value}): caminho vazio")
                return None

            try:
                # Usar resolver_caminho_documento que já implementa:
                # 1. Verificação local
                # 2. Download do Supabase se não existir localmente
                caminho_resolvido = self.storage.resolver_caminho_documento(doc)

                if caminho_resolvido and caminho_resolvido.exists():
                    logger.info(f"  Doc {doc.id} ({doc.tipo.value}): OK - {caminho_resolvido}")
                    return str(caminho_resolvido)
                else:
                    logger.error(f"  Doc {doc.id} ({doc.tipo.value}): ARQUIVO NÃO ENCONTRADO")
                    logger.error(f"    Caminho retornado: {caminho_resolvido}")
                    logger.error(f"    Caminho original (BD): {doc.caminho_arquivo}")
                    return None
            except Exception as e:
                logger.error(f"  Doc {doc.id} ({doc.tipo.value}): ERRO ao resolver caminho: {e}")
                return None

        def _adicionar_documento(doc) -> None:
            if not doc:
                return
            caminho = _normalizar_e_verificar(doc)
            if caminho:
                arquivos.append(caminho)

        def _adicionar_json_mais_recente(docs, tipo: TipoDocumento) -> None:
            _adicionar_documento(self._documento_json_da_ultima_execucao(docs, tipo))

        # Mapa de quais documentos cada etapa precisa
        if etapa == EtapaProcessamento.EXTRAIR_QUESTOES:
            # Precisa do enunciado original
            for doc in docs_base:
                if doc.tipo == TipoDocumento.ENUNCIADO:
                    _adicionar_documento(doc)

        elif etapa == EtapaProcessamento.EXTRAIR_GABARITO:
            # Precisa do gabarito original + questões extraídas (JSON)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.GABARITO:
                    _adicionar_documento(doc)
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_QUESTOES)

        elif etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            # Precisa da prova respondida + questões extraídas (JSON)
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    _adicionar_documento(doc)
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_QUESTOES)

        elif etapa == EtapaProcessamento.CORRIGIR:
            # Arquivos originais para referência visual
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    _adicionar_documento(doc)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.GABARITO:
                    _adicionar_documento(doc)
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_QUESTOES)
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_GABARITO)
            _adicionar_json_mais_recente(docs_aluno, TipoDocumento.EXTRACAO_RESPOSTAS)

        elif etapa == EtapaProcessamento.ANALISAR_HABILIDADES:
            # Prova do aluno para referência visual
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    _adicionar_documento(doc)
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_QUESTOES)
            _adicionar_json_mais_recente(docs_aluno, TipoDocumento.EXTRACAO_RESPOSTAS)
            _adicionar_json_mais_recente(docs_aluno, TipoDocumento.CORRECAO)

        elif etapa == EtapaProcessamento.GERAR_RELATORIO:
            _adicionar_json_mais_recente(docs_base, TipoDocumento.EXTRACAO_QUESTOES)
            _adicionar_json_mais_recente(docs_aluno, TipoDocumento.CORRECAO)
            _adicionar_json_mais_recente(docs_aluno, TipoDocumento.ANALISE_HABILIDADES)

        logger.info(f"Arquivos coletados para {etapa.value}: {len(arquivos)} - tipos: {[Path(a).suffix for a in arquivos]}")
        if not arquivos:
            logger.warning(f"ATENÇÃO: Nenhum arquivo encontrado para {etapa.value}!")

        return arquivos
    
    def _preparar_contexto_json(
        self,
        atividade_id: str,
        aluno_id: Optional[str],
        etapa: EtapaProcessamento
    ) -> Dict[str, str]:
        """
        Prepara contexto de documentos JSON já processados.

        Retorna dict com:
        - Dados dos documentos encontrados
        - "_documentos_faltantes": lista de documentos obrigatórios que não foram encontrados
        - "_documentos_carregados": lista de documentos que foram carregados com sucesso
        """
        contexto = {}
        documentos_faltantes = []
        documentos_carregados = []

        docs_base = self._documentos_novos_primeiro(self.storage.listar_documentos(atividade_id))
        docs_aluno = (
            self._documentos_novos_primeiro(self.storage.listar_documentos(atividade_id, aluno_id))
            if aluno_id
            else []
        )

        # Helper para carregar documento JSON
        def _carregar_json(doc, chave: str) -> bool:
            try:
                if self._documento_em_erro(doc):
                    _logger.warning(
                        f"Documento {chave} pertence a uma execução com erro",
                        doc_id=doc.id,
                    )
                    documentos_faltantes.append(f"{chave} (execução anterior falhou)")
                    return False
                # Use resolver_caminho_documento to handle Supabase downloads on Render
                caminho = self.storage.resolver_caminho_documento(doc)
                if caminho and caminho.exists():
                    with open(caminho, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Verificar se o JSON tem erro de parsing
                        if isinstance(data, dict) and data.get("_error"):
                            _logger.warning(
                                f"Documento {chave} contém erro de parsing anterior",
                                doc_id=doc.id,
                                error=data.get("_error")
                            )
                            documentos_faltantes.append(f"{chave} (erro: {data.get('_error')})")
                            return False
                        contexto[chave] = json.dumps(data, ensure_ascii=False)
                        documentos_carregados.append(chave)
                        return True
                else:
                    _logger.warning(f"Arquivo não encontrado após resolver: {doc.caminho_arquivo}")
            except Exception as e:
                _logger.warning(f"Erro ao carregar {chave}: {e}")
            return False

        def _carregar_json_mais_recente(docs, tipo: TipoDocumento, chave: str) -> bool:
            doc = self._documento_json_da_ultima_execucao(docs, tipo)
            if not doc:
                return False
            return _carregar_json(doc, chave)

        # EXTRAIR_RESPOSTAS precisa das questoes extraidas no corpo do prompt.
        # Anexar o JSON sozinho nao basta: modelos pequenos podem ignorar ou
        # subutilizar anexos quando a variavel {{questoes_extraidas}} fica vazia.
        if etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            encontrou_questoes = _carregar_json_mais_recente(
                docs_base,
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes_extraidas",
            )
            if not encontrou_questoes:
                documentos_faltantes.append("questoes_extraidas (execute 'extrair_questoes' primeiro)")

        # Para correção, incluir questões extraídas, gabarito e respostas
        if etapa in [EtapaProcessamento.CORRIGIR, EtapaProcessamento.ANALISAR_HABILIDADES, EtapaProcessamento.GERAR_RELATORIO]:
            encontrou_questoes = _carregar_json_mais_recente(
                docs_base,
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes_extraidas",
            )
            if not encontrou_questoes and etapa in [EtapaProcessamento.CORRIGIR, EtapaProcessamento.ANALISAR_HABILIDADES]:
                documentos_faltantes.append("questoes_extraidas (execute 'extrair_questoes' primeiro)")

            # Verificar gabarito extraído para correção
            if etapa == EtapaProcessamento.CORRIGIR:
                encontrou_gabarito = _carregar_json_mais_recente(
                    docs_base,
                    TipoDocumento.EXTRACAO_GABARITO,
                    "gabarito_extraido",
                )
                if not encontrou_gabarito:
                    documentos_faltantes.append("gabarito (faça upload do gabarito ou execute 'extrair_gabarito')")

            encontrou_respostas = _carregar_json_mais_recente(
                docs_aluno,
                TipoDocumento.EXTRACAO_RESPOSTAS,
                "respostas_aluno",
            )
            if not encontrou_respostas and etapa == EtapaProcessamento.CORRIGIR:
                documentos_faltantes.append("respostas_aluno (execute 'extrair_respostas' primeiro)")

        # Para análise de habilidades e relatório, incluir correção
        if etapa in [EtapaProcessamento.ANALISAR_HABILIDADES, EtapaProcessamento.GERAR_RELATORIO]:
            encontrou_correcoes = _carregar_json_mais_recente(
                docs_aluno,
                TipoDocumento.CORRECAO,
                "correcoes",
            )
            if not encontrou_correcoes:
                documentos_faltantes.append("correcoes")

        # Para relatório, incluir análise de habilidades
        if etapa == EtapaProcessamento.GERAR_RELATORIO:
            encontrou_analise = _carregar_json_mais_recente(
                docs_aluno,
                TipoDocumento.ANALISE_HABILIDADES,
                "analise_habilidades",
            )
            if not encontrou_analise:
                documentos_faltantes.append("analise_habilidades")

        # Logar status dos documentos
        if documentos_carregados:
            _logger.info(
                f"Documentos carregados para {etapa.value}",
                documentos=documentos_carregados
            )

        if documentos_faltantes:
            _logger.warning(
                f"DOCUMENTOS FALTANTES para {etapa.value}",
                faltantes=documentos_faltantes,
                atividade_id=atividade_id,
                aluno_id=aluno_id
            )
            contexto["_documentos_faltantes"] = documentos_faltantes

        contexto["_documentos_carregados"] = documentos_carregados

        return contexto
    
    # ============================================================
    # NOVOS MÉTODOS PARA PIPELINE MULTIMODAL (compatível com routes_pipeline.py)
    # ============================================================
    
    async def extrair_questoes(
        self,
        atividade_id: str,
        provider_id: str = None
    ) -> ResultadoExecucao:
        """Extrai questões do enunciado usando visão multimodal"""
        return await self.executar_etapa(
            etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
            atividade_id=atividade_id,
            provider_name=provider_id,
            usar_multimodal=True
        )
    
    async def extrair_gabarito(
        self,
        atividade_id: str,
        provider_id: str = None
    ) -> ResultadoExecucao:
        """Extrai gabarito usando visão multimodal"""
        return await self.executar_etapa(
            etapa=EtapaProcessamento.EXTRAIR_GABARITO,
            atividade_id=atividade_id,
            provider_name=provider_id,
            usar_multimodal=True
        )

    async def extrair_respostas_aluno(
        self,
        atividade_id: str,
        aluno_id: str,
        provider_id: str = None
    ) -> ResultadoExecucao:
        """Extrai respostas da prova do aluno usando visão multimodal"""
        prova_valida, mensagem_erro, _ = self._validar_prova_respondida_para_extracao(
            atividade_id, aluno_id
        )
        if not prova_valida:
            return self._erro(
                EtapaProcessamento.EXTRAIR_RESPOSTAS,
                mensagem_erro,
                provider=provider_id,
            )

        return await self.executar_etapa(
            etapa=EtapaProcessamento.EXTRAIR_RESPOSTAS,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_name=provider_id,
            usar_multimodal=True
        )
    
    async def corrigir(
        self,
        atividade_id: str,
        aluno_id: str,
        provider_id: str = None
    ) -> ResultadoExecucao:
        """Corrige a prova do aluno using tool-use for dual output (JSON + PDF).

        Migrated from two-pass narrative (F-T1): single executar_com_tools() call
        with create_document (JSON) + execute_python_code (PDF via E2B).
        """
        # Get context
        atividade = self.storage.get_atividade(atividade_id)
        if not atividade:
            return self._erro(EtapaProcessamento.CORRIGIR, "Atividade não encontrada")

        turma = self.storage.get_turma(atividade.turma_id)
        materia = self.storage.get_materia(turma.materia_id) if turma else None

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.CORRIGIR,
            materia.id if materia else None,
        )
        if not prompt:
            return self._erro(EtapaProcessamento.CORRIGIR, "Prompt CORRIGIR não encontrado")

        # Prepare variables
        variaveis = self._preparar_variaveis_texto(
            EtapaProcessamento.CORRIGIR, atividade_id, aluno_id,
            materia, atividade, usar_multimodal=True
        )

        # Prepare JSON context (extracted questions, answers, rubric)
        contexto_json = self._preparar_contexto_json(
            atividade_id, aluno_id, EtapaProcessamento.CORRIGIR
        )
        documentos_faltantes = contexto_json.pop("_documentos_faltantes", [])
        contexto_json.pop("_documentos_carregados", [])

        if documentos_faltantes:
            lista = ", ".join(documentos_faltantes)
            return self._erro(
                EtapaProcessamento.CORRIGIR,
                f"Documentos obrigatórios ausentes para corrigir: {lista}. "
                f"Execute as etapas anteriores do pipeline antes da correção.",
                provider=provider_id,
            )

        variaveis.update(contexto_json)
        self._aplicar_aliases_contexto_corrigir(variaveis, contexto_json)
        erro_gabarito = self._erro_gabarito_incompleto_para_correcao(
            contexto_json.get("gabarito_extraido")
        )
        if erro_gabarito:
            return self._erro(
                EtapaProcessamento.CORRIGIR,
                erro_gabarito,
                provider=provider_id,
            )

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema_raw = prompt.render_sistema(**variaveis)
        prompt_sistema = prompt_sistema_raw if isinstance(prompt_sistema_raw, str) else ""

        # Add tool-use instructions for dual output (from module-level STAGE_TOOL_INSTRUCTIONS)
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.CORRIGIR, "")
        full_system = prompt_sistema + tool_instructions

        # Call with tools — single pass replaces two-pass narrative
        return await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_id=provider_id,
            system_prompt=full_system,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.CORRECAO,
            prompt_id=prompt.id,
        )

    def _aplicar_aliases_contexto_corrigir(
        self,
        variaveis: Dict[str, str],
        contexto_json: Dict[str, str],
    ) -> None:
        """Ensure CORRIGIR uses structured extraction JSON, not raw uploaded text."""
        if "questoes_extraidas" in contexto_json:
            variaveis["questoes_extraidas"] = contexto_json["questoes_extraidas"]
            variaveis["questao"] = contexto_json["questoes_extraidas"]

        if "gabarito_extraido" in contexto_json:
            variaveis["gabarito_extraido"] = contexto_json["gabarito_extraido"]
            variaveis["resposta_esperada"] = contexto_json["gabarito_extraido"]

        if "respostas_aluno" in contexto_json:
            variaveis["respostas_aluno"] = contexto_json["respostas_aluno"]
            variaveis["resposta_aluno"] = contexto_json["respostas_aluno"]

    def _erro_gabarito_incompleto_para_correcao(
        self,
        gabarito_extraido: Optional[str],
    ) -> Optional[str]:
        """Block grading when the extracted answer key cannot support a grade."""
        if not gabarito_extraido:
            return "Gabarito extraido ausente; nao e seguro corrigir sem resposta esperada estruturada."

        try:
            dados = json.loads(gabarito_extraido)
        except json.JSONDecodeError:
            return "Gabarito extraido nao e JSON valido; nao e seguro corrigir."

        if not isinstance(dados, dict):
            return "Gabarito extraido nao tem estrutura de objeto JSON; nao e seguro corrigir."

        avisos_documento = dados.get("_avisos_documento") or []
        avisos_questao = dados.get("_avisos_questao") or []
        respostas = dados.get("respostas") or []

        codigos_bloqueantes_doc = {"MISSING_CONTENT", "ILLEGIBLE_DOCUMENT"}
        codigos_bloqueantes_questao = {"MISSING_CONTENT", "ILLEGIBLE_QUESTION"}

        doc_bloqueado = [
            aviso
            for aviso in avisos_documento
            if isinstance(aviso, dict)
            and str(aviso.get("codigo", "")).upper() in codigos_bloqueantes_doc
        ]
        questoes_bloqueadas = [
            aviso.get("questao", "?")
            for aviso in avisos_questao
            if isinstance(aviso, dict)
            and str(aviso.get("codigo", "")).upper() in codigos_bloqueantes_questao
        ]
        respostas_missing = [
            resposta.get("questao_numero", "?")
            for resposta in respostas
            if isinstance(resposta, dict)
            and str(resposta.get("resposta_correta", "")).strip().upper() == "MISSING_CONTENT"
        ]

        if doc_bloqueado or questoes_bloqueadas or respostas_missing:
            questoes = sorted({str(q) for q in [*questoes_bloqueadas, *respostas_missing]})
            questoes_txt = ", ".join(questoes[:10]) if questoes else "documento inteiro"
            return (
                "Gabarito extraido incompleto para correcao: questoes "
                f"{questoes_txt}. A etapa CORRIGIR nao pode atribuir nota ou "
                "gerar feedback como se houvesse resposta esperada completa. "
                "Reenvie um gabarito completo ou corrija a etapa EXTRAIR_GABARITO."
            )

        return None

    async def analisar_habilidades(
        self,
        atividade_id: str,
        aluno_id: str = None,
        provider_id: str = None
    ) -> ResultadoExecucao:
        """Analisa habilidades do aluno using tool-use for dual output (JSON + PDF).

        Migrated from two-pass narrative (F-T2): single executar_com_tools() call
        with create_document (JSON) + execute_python_code (PDF via E2B).
        """
        # Get context
        atividade = self.storage.get_atividade(atividade_id)
        if not atividade:
            return self._erro(EtapaProcessamento.ANALISAR_HABILIDADES, "Atividade não encontrada")

        turma = self.storage.get_turma(atividade.turma_id)
        materia = self.storage.get_materia(turma.materia_id) if turma else None

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.ANALISAR_HABILIDADES,
            materia.id if materia else None,
        )
        if not prompt:
            return self._erro(EtapaProcessamento.ANALISAR_HABILIDADES, "Prompt ANALISAR_HABILIDADES não encontrado")

        # Prepare variables
        variaveis = self._preparar_variaveis_texto(
            EtapaProcessamento.ANALISAR_HABILIDADES, atividade_id, aluno_id,
            materia, atividade, usar_multimodal=True
        )

        # Prepare JSON context
        contexto_json = self._preparar_contexto_json(
            atividade_id, aluno_id, EtapaProcessamento.ANALISAR_HABILIDADES
        )
        documentos_faltantes = contexto_json.pop("_documentos_faltantes", [])
        contexto_json.pop("_documentos_carregados", [])

        if documentos_faltantes:
            lista = ", ".join(documentos_faltantes)
            return self._erro(
                EtapaProcessamento.ANALISAR_HABILIDADES,
                f"Documentos obrigatórios ausentes para análise: {lista}. "
                f"Execute as etapas anteriores do pipeline antes da análise.",
                provider=provider_id,
            )

        variaveis.update(contexto_json)

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema_raw = prompt.render_sistema(**variaveis)
        prompt_sistema = prompt_sistema_raw if isinstance(prompt_sistema_raw, str) else ""

        # Add tool-use instructions for dual output
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.ANALISAR_HABILIDADES, "")
        full_system = prompt_sistema + tool_instructions

        # Call with tools — single pass replaces two-pass narrative
        return await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_id=provider_id,
            system_prompt=full_system,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.ANALISE_HABILIDADES,
            prompt_id=prompt.id,
        )

    async def gerar_relatorio(
        self,
        atividade_id: str,
        aluno_id: str = None,
        provider_id: str = None,
        salvar_erro_documento: bool = False
    ) -> ResultadoExecucao:
        """Gera o relatório final do aluno using tool-use for dual output (JSON + PDF).

        Migrated from two-pass narrative (F-T3): single executar_com_tools() call
        with create_document (JSON) + execute_python_code (PDF via E2B).
        """
        # Get context
        atividade = self.storage.get_atividade(atividade_id)
        if not atividade:
            return self._erro(EtapaProcessamento.GERAR_RELATORIO, "Atividade não encontrada")

        turma = self.storage.get_turma(atividade.turma_id)
        materia = self.storage.get_materia(turma.materia_id) if turma else None

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.GERAR_RELATORIO,
            materia.id if materia else None,
        )
        if not prompt:
            return self._erro(EtapaProcessamento.GERAR_RELATORIO, "Prompt GERAR_RELATORIO não encontrado")

        # Prepare variables
        variaveis = self._preparar_variaveis_texto(
            EtapaProcessamento.GERAR_RELATORIO, atividade_id, aluno_id,
            materia, atividade, usar_multimodal=True
        )

        # Prepare JSON context
        contexto_json = self._preparar_contexto_json(
            atividade_id, aluno_id, EtapaProcessamento.GERAR_RELATORIO
        )
        documentos_faltantes = contexto_json.pop("_documentos_faltantes", [])
        documentos_carregados = contexto_json.pop("_documentos_carregados", [])

        if documentos_faltantes:
            lista = ", ".join(documentos_faltantes)
            mensagem = (
                f"Documentos obrigatórios ausentes para gerar relatório: {lista}. "
                f"Execute as etapas anteriores do pipeline antes de gerar o relatório."
            )
            erro_pipeline = criar_erro_pipeline(
                tipo=ERRO_DOCUMENTO_FALTANTE,
                mensagem=mensagem,
                severidade=SeveridadeErro.CRITICO,
                etapa=EtapaProcessamento.GERAR_RELATORIO.value,
            )
            erro_content = {
                "_erro_pipeline": erro_pipeline,
                "_documentos_faltantes": documentos_faltantes,
                "_documentos_carregados": documentos_carregados,
            }
            documento_id = None
            if salvar_erro_documento:
                documento_id = await self._salvar_resultado(
                    EtapaProcessamento.GERAR_RELATORIO,
                    atividade_id,
                    aluno_id,
                    "",
                    erro_content,
                    provider_id or "",
                    "",
                    prompt.id,
                    0,
                    0,
                    gerar_formatos_extras=False,
                )
            return ResultadoExecucao(
                sucesso=False,
                etapa=EtapaProcessamento.GERAR_RELATORIO,
                prompt_usado="",
                prompt_id=prompt.id,
                provider=provider_id or "",
                modelo="",
                erro=mensagem,
                resposta_parsed=erro_content,
                documento_id=documento_id,
            )

        variaveis.update(contexto_json)

        nota_final = self._nota_final_top_level(variaveis.get("nota_final"))
        if nota_final is None:
            nota_final = self._calcular_nota_final_de_correcoes(
                variaveis.get("correcoes")
            )
        if nota_final is None:
            mensagem = (
                "Não foi possível determinar uma nota_final numérica e confiável "
                "para gerar relatório. A etapa foi bloqueada para evitar relatório "
                "com nota inventada ou N/A."
            )
            erro_pipeline = criar_erro_pipeline(
                tipo=ERRO_NOTA_FINAL_INDETERMINADA,
                mensagem=mensagem,
                severidade=SeveridadeErro.CRITICO,
                etapa=EtapaProcessamento.GERAR_RELATORIO.value,
            )
            erro_content = {
                "_erro_pipeline": erro_pipeline,
                "_documentos_carregados": documentos_carregados,
            }
            documento_id = None
            if salvar_erro_documento:
                documento_id = await self._salvar_resultado(
                    EtapaProcessamento.GERAR_RELATORIO,
                    atividade_id,
                    aluno_id,
                    "",
                    erro_content,
                    provider_id or "",
                    "",
                    prompt.id,
                    0,
                    0,
                    gerar_formatos_extras=False,
                )
            return ResultadoExecucao(
                sucesso=False,
                etapa=EtapaProcessamento.GERAR_RELATORIO,
                prompt_usado="",
                prompt_id=prompt.id,
                provider=provider_id or "",
                modelo="",
                erro=mensagem,
                resposta_parsed=erro_content,
                documento_id=documento_id,
            )

        variaveis["nota_final"] = nota_final

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema_raw = prompt.render_sistema(**variaveis)
        prompt_sistema = prompt_sistema_raw if isinstance(prompt_sistema_raw, str) else ""

        # Add tool-use instructions for dual output
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.GERAR_RELATORIO, "")
        full_system = prompt_sistema + tool_instructions

        # Call with tools
        return await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_id=provider_id,
            system_prompt=full_system,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.RELATORIO_FINAL,
            prompt_id=prompt.id,
        )

    async def chat_com_documentos(
        self,
        mensagem: str,
        arquivos: List[str],
        provider_id: str = None,
        system_prompt: str = None
    ) -> ResultadoExecucao:
        """Chat livre com documentos anexados"""
        inicio = time.time()
        
        if not HAS_MULTIMODAL:
            return ResultadoExecucao(
                sucesso=False,
                etapa="chat",
                erro="Sistema multimodal não disponível"
            )
        
        try:
            config = self._get_provider_config(provider_id)
            cliente = ClienteAPIMultimodal(config)
            
            resultado = await cliente.enviar_com_anexos(
                mensagem=mensagem,
                arquivos=arquivos,
                system_prompt=system_prompt or "Você é um assistente educacional especializado em análise de provas e documentos acadêmicos.",
                verificar_anexos=True
            )
            
            tempo_ms = (time.time() - inicio) * 1000
            
            return ResultadoExecucao(
                sucesso=resultado.sucesso,
                etapa="chat",
                resposta_raw=resultado.resposta,
                provider=resultado.provider,
                modelo=resultado.modelo,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                tempo_ms=tempo_ms,
                anexos_enviados=resultado.anexos_enviados,
                anexos_confirmados=resultado.anexos_confirmados,
                erro=resultado.erro
            )
            
        except Exception as e:
            return ResultadoExecucao(
                sucesso=False,
                etapa="chat",
                erro=str(e),
                tempo_ms=(time.time() - inicio) * 1000
            )
    
    # ============================================================
    # MÉTODOS AUXILIARES (mantidos do original)
    # ============================================================
    
    def _erro(
        self,
        etapa: Union[EtapaProcessamento, str],
        mensagem: str,
        prompt_id: str = None,
        provider: str = None,
        modelo: str = None
    ) -> ResultadoExecucao:
        """Cria resultado de erro"""
        return ResultadoExecucao(
            sucesso=False,
            etapa=etapa,
            prompt_usado="",
            prompt_id=prompt_id or "",
            provider=provider or "",
            modelo=modelo or "",
            erro=mensagem
        )

    def _validar_prova_respondida_para_extracao(
        self,
        atividade_id: str,
        aluno_id: Optional[str],
        docs_aluno: Optional[List[Any]] = None,
    ) -> tuple[bool, str, Optional[Documento]]:
        """Valida se EXTRAIR_RESPOSTAS tem um arquivo de prova do aluno acessivel."""
        if not aluno_id:
            return False, "Aluno nao informado para extrair respostas.", None

        if docs_aluno is None:
            try:
                docs_aluno = self.storage.listar_documentos(atividade_id, aluno_id)
            except Exception as e:
                return False, f"Erro ao listar documentos do aluno: {e}", None

        def _tipo_documento(doc) -> Optional[str]:
            tipo = getattr(doc, "tipo", None)
            return getattr(tipo, "value", tipo)

        provas = [
            doc for doc in docs_aluno
            if _tipo_documento(doc) == TipoDocumento.PROVA_RESPONDIDA.value
        ]

        nome_aluno = aluno_id
        try:
            aluno = self.storage.get_aluno(aluno_id)
            nome_aluno = getattr(aluno, "nome", None) or aluno_id
        except Exception:
            pass

        if not provas:
            return (
                False,
                f"Aluno {nome_aluno} nao tem prova_respondida enviada.",
                None,
            )

        erros_resolucao = []
        for doc in provas:
            doc_id = getattr(doc, "id", "sem-id")
            try:
                caminho = self.storage.resolver_caminho_documento(doc)
            except Exception as e:
                erros_resolucao.append(f"{doc_id}: erro ao resolver caminho ({e})")
                continue

            if caminho and Path(caminho).exists():
                return True, "", doc

            caminho_original = getattr(doc, "caminho_arquivo", None) or caminho or "sem caminho"
            erros_resolucao.append(f"{doc_id}: arquivo nao encontrado ({caminho_original})")

        detalhes = ""
        if erros_resolucao:
            detalhes = " Detalhes: " + "; ".join(erros_resolucao[:3])

        return (
            False,
            f"Aluno {nome_aluno} tem prova_respondida cadastrada, "
            f"mas nenhum arquivo foi encontrado no storage.{detalhes}",
            None,
        )

    def _nota_como_float(self, valor: Any) -> Optional[float]:
        if valor is None or isinstance(valor, bool):
            return None
        if isinstance(valor, (int, float)):
            nota = float(valor)
        elif isinstance(valor, str):
            texto = valor.strip().replace(",", ".")
            if not re.fullmatch(r"[-+]?\d+(?:\.\d+)?", texto):
                return None
            nota = float(texto)
        else:
            return None

        return nota if math.isfinite(nota) else None

    def _nota_final_top_level(self, valor: Any) -> Optional[str]:
        nota = self._nota_como_float(valor)
        if nota is None:
            return None
        if isinstance(valor, str):
            return valor.strip().replace(",", ".")
        return str(valor)

    def _somar_notas(self, itens: Any) -> Optional[str]:
        if not isinstance(itens, list):
            return None

        total = 0.0
        notas_encontradas = 0
        for item in itens:
            if not isinstance(item, dict):
                continue
            nota = self._nota_como_float(item.get("nota"))
            if nota is None:
                continue
            total += nota
            notas_encontradas += 1

        if notas_encontradas == 0:
            return None
        return str(total)

    def _calcular_nota_final_de_correcoes(self, correcoes: Any) -> Optional[str]:
        """Calcula nota_final para GERAR_RELATORIO sem inventar nota silenciosa."""
        dados = correcoes
        if isinstance(correcoes, str):
            try:
                dados = json.loads(correcoes)
            except json.JSONDecodeError:
                return None

        if isinstance(dados, dict):
            for chave in ("nota_final", "nota"):
                nota = self._nota_final_top_level(dados.get(chave))
                if nota is not None:
                    return nota

            for chave in ("questoes", "correcoes"):
                nota = self._somar_notas(dados.get(chave))
                if nota is not None:
                    return nota

        elif isinstance(dados, list):
            nota = self._somar_notas(dados)
            if nota is not None:
                return nota

        return None

    def _nota_final_correcao_oficial(
        self,
        atividade_id: str,
        aluno_id: Optional[str],
    ) -> tuple[Optional[float], Optional[str]]:
        """Return the latest official CORRECAO nota_final, without older-run fallback."""
        if not aluno_id:
            return None, None

        try:
            documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        except Exception as exc:
            return None, f"nao foi possivel listar documentos de correcao: {exc}"

        docs_correcao = [
            doc
            for doc in documentos or []
            if getattr(doc, "tipo", None) == TipoDocumento.CORRECAO
        ]
        if not docs_correcao:
            return None, None

        doc = self._documento_json_da_ultima_execucao(docs_correcao, TipoDocumento.CORRECAO)
        if not doc:
            return None, "a ultima execucao de CORRECAO nao tem JSON oficial"
        if self._documento_em_erro(doc):
            return None, f"o JSON oficial da CORRECAO {getattr(doc, 'id', '')} esta em erro"

        doc_label = getattr(doc, "id", None) or getattr(doc, "nome_arquivo", "correcao")
        try:
            caminho = self.storage.resolver_caminho_documento(doc)
        except Exception as exc:
            return None, f"nao foi possivel resolver CORRECAO {doc_label}: {exc}"

        if not caminho or not Path(caminho).exists():
            return None, f"arquivo da CORRECAO {doc_label} nao encontrado"

        try:
            with open(caminho, "r", encoding="utf-8") as fh:
                dados = json.load(fh)
        except Exception as exc:
            return None, f"JSON da CORRECAO {doc_label} invalido: {exc}"

        if not isinstance(dados, dict):
            return None, f"JSON da CORRECAO {doc_label} deve ser objeto na raiz"

        nota = self._nota_como_float(dados.get("nota_final"))
        if nota is None:
            return None, f"JSON da CORRECAO {doc_label} sem nota_final numerica"
        return nota, None

    def _validar_relatorio_nota_final_contra_correcao(
        self,
        dados_relatorio: Dict[str, Any],
        atividade_id: str,
        aluno_id: Optional[str],
        doc_label: str,
    ) -> List[str]:
        """Block RELATORIO_FINAL if it silently changes the official correction grade."""
        erros: List[str] = []
        nota_correcao, erro_correcao = self._nota_final_correcao_oficial(
            atividade_id,
            aluno_id,
        )
        if erro_correcao:
            erros.append(
                f"JSON {doc_label} nao pode validar nota_final contra CORRECAO oficial: "
                f"{erro_correcao}"
            )
            return erros
        if nota_correcao is None:
            return erros

        nota_relatorio = self._nota_como_float(dados_relatorio.get("nota_final"))
        if nota_relatorio is None:
            return erros
        if abs(nota_relatorio - nota_correcao) > 0.01:
            erros.append(
                f"JSON {doc_label} tem nota_final {nota_relatorio:g}, mas CORRECAO "
                f"oficial tem nota_final {nota_correcao:g}"
            )
        return erros
    
    def _preparar_variaveis_texto(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        materia: Any,
        atividade: Any,
        usar_multimodal: bool = False
    ) -> Dict[str, str]:
        """Prepara variáveis para o prompt extraindo TEXTO dos documentos"""
        variaveis = {
            "materia": materia.nome if materia else "Não definida",
            "atividade": atividade.nome if atividade else "Não definida",
            "nota_maxima": str(atividade.nota_maxima) if atividade else "10"
        }
        
        # Buscar documentos relevantes
        documentos = self._documentos_novos_primeiro(
            self.storage.listar_documentos(atividade_id, aluno_id)
        )

        def _definir_variavel(chave: str, valor: str) -> None:
            if chave not in variaveis or not str(variaveis[chave]).strip():
                variaveis[chave] = valor
        
        for doc in documentos:
            if usar_multimodal and doc.tipo in [TipoDocumento.ENUNCIADO, TipoDocumento.GABARITO, TipoDocumento.PROVA_RESPONDIDA]:
                if etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS and doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    conteudo = self._extrair_texto_pdf_para_prompt(doc)
                    if not conteudo:
                        conteudo = self._ler_documento_texto(doc, usar_multimodal=True)
                else:
                    conteudo = self._ler_documento_texto(doc, usar_multimodal=True)
            else:
                conteudo = self._ler_documento_texto(doc, usar_multimodal)
            
            if doc.tipo == TipoDocumento.ENUNCIADO:
                _definir_variavel("conteudo_documento", conteudo)
                _definir_variavel("enunciado", conteudo)
            
            elif doc.tipo == TipoDocumento.GABARITO:
                _definir_variavel("gabarito", conteudo)
                _definir_variavel("resposta_esperada", conteudo)
            
            elif doc.tipo == TipoDocumento.CRITERIOS_CORRECAO:
                _definir_variavel("criterios", conteudo)
            
            elif doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                _definir_variavel("prova_aluno", conteudo)
                _definir_variavel("resposta_aluno", conteudo)
            
            elif doc.tipo == TipoDocumento.EXTRACAO_QUESTOES:
                _definir_variavel("questoes_extraidas", conteudo)

            elif doc.tipo == TipoDocumento.EXTRACAO_GABARITO:
                _definir_variavel("gabarito_extraido", conteudo)
                # Usar como resposta_esperada se não houver outra (ou se estiver vazia no multimodal)
                if not variaveis.get("resposta_esperada"):
                    variaveis["resposta_esperada"] = conteudo

            elif doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS:
                _definir_variavel("respostas_aluno", conteudo)

            elif doc.tipo == TipoDocumento.CORRECAO:
                _definir_variavel("correcoes", conteudo)

            elif doc.tipo == TipoDocumento.ANALISE_HABILIDADES:
                _definir_variavel("analise_habilidades", conteudo)
        
        # Info do aluno
        if aluno_id:
            aluno = self.storage.get_aluno(aluno_id)
            if aluno:
                variaveis["nome_aluno"] = aluno.nome
                variaveis["aluno"] = aluno.nome

        # Aliases para compatibilidade com diferentes prompts
        # O prompt CORRIGIR usa {{questao}} mas o código fornece questoes_extraidas
        if "questoes_extraidas" in variaveis:
            variaveis["questao"] = variaveis["questoes_extraidas"]

        # O prompt pode usar {{conteudo_documento}} para diferentes tipos de docs
        if "prova_aluno" in variaveis and "conteudo_documento" not in variaveis:
            variaveis["conteudo_documento"] = variaveis["prova_aluno"]
        if "gabarito" in variaveis and "conteudo_documento" not in variaveis:
            variaveis["conteudo_documento"] = variaveis["gabarito"]

        # Gabarito extraído como resposta_esperada
        # Use gabarito_extraido when resposta_esperada is missing OR empty
        # (empty happens in multimodal mode where raw GABARITO content is skipped)
        if "gabarito_extraido" in variaveis and not variaveis.get("resposta_esperada"):
            variaveis["resposta_esperada"] = variaveis["gabarito_extraido"]
        # Compatibilidade de template: se a etapa usa resposta_esperada e só ha
        # gabarito original no contexto textual, exponha explicitamente esse valor.
        if "gabarito" in variaveis and not variaveis.get("resposta_esperada"):
            variaveis["resposta_esperada"] = variaveis["gabarito"]

        # Respostas extraídas como resposta_aluno
        # (in multimodal mode, raw PROVA_RESPONDIDA is skipped, use extraction)
        if "respostas_aluno" in variaveis and not variaveis.get("resposta_aluno"):
            variaveis["resposta_aluno"] = variaveis["respostas_aluno"]

        # Critérios podem não existir - usar string vazia
        if "criterios" not in variaveis:
            variaveis["criterios"] = "(Nenhum critério específico fornecido)"

        # Calcular nota_final se houver correções (para gerar_relatorio)
        if etapa == EtapaProcessamento.GERAR_RELATORIO and "correcoes" in variaveis and "nota_final" not in variaveis:
            variaveis["nota_final"] = self._calcular_nota_final_de_correcoes(
                variaveis["correcoes"]
            )

        # Compatibilidade para etapas antigas; GERAR_RELATORIO valida nota antes
        # de renderizar e nao pode receber N/A como fallback.
        if "nota_final" not in variaveis and etapa != EtapaProcessamento.GERAR_RELATORIO:
            variaveis["nota_final"] = "N/A"

        return variaveis

    def _extrair_texto_pdf_para_prompt(self, documento: Documento, limite_chars: int = 60000) -> str:
        """Extrai texto de PDF para compor o prompt sem substituir o anexo original."""
        try:
            arquivo = self.storage.resolver_caminho_documento(documento)
            if not arquivo or not Path(arquivo).exists():
                return ""

            if getattr(documento, "extensao", "").lower() != ".pdf":
                return ""

            partes = []
            total_chars = 0
            with fitz.open(str(arquivo)) as pdf_doc:
                for pagina_idx, pagina in enumerate(pdf_doc, start=1):
                    texto = (pagina.get_text("text") or "").strip()
                    if not texto:
                        continue
                    trecho = f"--- pagina {pagina_idx} ---\n{texto}"
                    partes.append(trecho)
                    total_chars += len(trecho)
                    if total_chars >= limite_chars:
                        break

            texto_extraido = "\n\n".join(partes).strip()
            if not texto_extraido:
                return ""

            truncado = len(texto_extraido) > limite_chars
            texto_extraido = texto_extraido[:limite_chars]
            sufixo = "\n\n[Texto truncado para caber no prompt. Consulte tambem o PDF anexado.]" if truncado else ""
            nome = getattr(documento, "nome_arquivo", None) or getattr(documento, "id", "documento.pdf")
            return (
                f"[TEXTO EXTRAIDO DO PDF: {nome}]\n"
                f"{texto_extraido}"
                f"{sufixo}\n"
                "[O PDF original tambem esta anexado; use o anexo para conferir layout, rasuras e imagens.]"
            )
        except Exception as e:
            nome = getattr(documento, "nome_arquivo", None) or getattr(documento, "id", "documento.pdf")
            _logger.warning(
                "Falha ao extrair texto de PDF para prompt",
                documento=nome,
                erro=str(e),
            )
            return ""

    def _pagina_pdf_sem_texto_tem_marcas_visuais(self, pagina: Any) -> bool:
        """Detecta se uma pagina sem texto contem marcas visuais suficientes."""
        try:
            pix = pagina.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
        except Exception:
            return False

        canais = max(1, pix.n)
        amostras = pix.samples
        total_pixels = max(1, pix.width * pix.height)
        pixels_escuros = 0
        for i in range(0, len(amostras), canais):
            rgb = amostras[i:i + min(3, canais)]
            if not rgb:
                continue
            media = sum(rgb) / len(rgb)
            if media < 210 and min(rgb) < 170:
                pixels_escuros += 1

        minimo = max(20, int(total_pixels * 0.002))
        return pixels_escuros >= minimo

    def _renderizar_paginas_pdf_sem_texto_para_anexos(
        self,
        arquivos: List[str],
        provider_tipo: str,
        max_paginas: int = 8,
        min_text_chars: int = 40,
    ) -> tuple[List[str], Optional[tempfile.TemporaryDirectory]]:
        """
        Para OpenAI/OpenRouter, anexa imagens de paginas escaneadas sem texto.

        A documentacao oficial diz que PDFs podem entrar como arquivo e que imagens
        tambem podem ser passadas no mesmo content array. Esta etapa torna paginas
        sem texto extraivel visiveis explicitamente para modelos que nao aproveitaram
        essas paginas apenas pelo anexo PDF.
        """
        if provider_tipo not in {"openai", "openrouter"}:
            return [], None

        temp_dir = tempfile.TemporaryDirectory(prefix="novocr_pdf_pages_")
        renderizados: List[str] = []
        destino = Path(temp_dir.name)

        try:
            for arquivo_str in arquivos:
                if len(renderizados) >= max_paginas:
                    break

                arquivo = Path(arquivo_str)
                if arquivo.suffix.lower() != ".pdf" or not arquivo.exists():
                    continue

                with fitz.open(str(arquivo)) as pdf_doc:
                    for pagina_idx, pagina in enumerate(pdf_doc, start=1):
                        if len(renderizados) >= max_paginas:
                            break

                        texto = (pagina.get_text("text") or "").strip()
                        if len(texto) >= min_text_chars:
                            continue
                        if not self._pagina_pdf_sem_texto_tem_marcas_visuais(pagina):
                            continue

                        nome_base = re.sub(r"[^A-Za-z0-9_.-]+", "_", arquivo.stem)[:80]
                        out_path = destino / f"{nome_base}_pagina_{pagina_idx:03d}_scan.png"
                        pix = pagina.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
                        pix.save(str(out_path))
                        renderizados.append(str(out_path))
        except Exception as e:
            _logger.warning(
                "Falha ao renderizar paginas PDF sem texto",
                erro=str(e),
            )

        if not renderizados:
            temp_dir.cleanup()
            return [], None

        return renderizados, temp_dir

    def _erro_respostas_scan_suspeitas(
        self,
        resposta_parsed: Optional[Dict[str, Any]],
        *,
        tem_paginas_pdf_renderizadas: bool,
    ) -> Optional[str]:
        """Bloqueia sucesso quando scans foram enviados mas quase tudo voltou em branco."""
        if not tem_paginas_pdf_renderizadas or not isinstance(resposta_parsed, dict):
            return None

        respostas = resposta_parsed.get("respostas")
        if not isinstance(respostas, list) or not respostas:
            return None

        def _sem_conteudo(item: Any) -> bool:
            if not isinstance(item, dict):
                return False
            resposta_aluno = str(item.get("resposta_aluno") or "").strip()
            return bool(item.get("ilegivel")) or bool(item.get("em_branco")) or not resposta_aluno

        total = len(respostas)
        sem_conteudo = sum(1 for item in respostas if _sem_conteudo(item))
        if total >= 3 and sem_conteudo / total >= 0.7:
            return (
                f"EXTRAIR_RESPOSTAS marcou {sem_conteudo} de {total} respostas como "
                "sem conteudo mesmo com paginas escaneadas anexadas como imagem. "
                "Isso e suspeito demais para concluir a etapa; revise OCR/vision do "
                "modelo ou use outro provider explicitamente."
            )

        return None
    
    def _ler_documento_texto(self, documento: Documento, usar_multimodal: bool = False) -> str:
        """
        Lê conteúdo de um documento como TEXTO.
        
        NOTA: Para PDFs e imagens, retorna placeholder indicando que
        o documento deve ser processado via multimodal.
        """
        try:
            arquivo = self.storage.resolver_caminho_documento(documento)
            if not arquivo.exists():
                return f"[Arquivo não encontrado: {documento.nome_arquivo}]"
            
            ext = documento.extensao.lower()
            
            # Arquivos JSON
            if ext == '.json':
                with open(arquivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            
            # Arquivos de texto
            elif ext in ['.txt', '.md', '.csv']:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return f.read()
            
            # PDFs - NÃO extrair texto, indicar que precisa de multimodal
            elif ext == '.pdf':
                if usar_multimodal:
                    return f"[DOCUMENTO ANEXADO: {documento.nome_arquivo} - Analise o documento anexado para extrair o conteúdo]"
                else:
                    return f"[DOCUMENTO PDF: {documento.nome_arquivo} - Use modo multimodal para processar]"
            
            # Imagens - NÃO processar, indicar que precisa de multimodal
            elif ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif']:
                if usar_multimodal:
                    return f"[IMAGEM ANEXADA: {documento.nome_arquivo} - Analise a imagem anexada para extrair o conteúdo]"
                else:
                    return f"[IMAGEM: {documento.nome_arquivo} - Use modo multimodal para processar]"
            
            # DOCX - tentar extrair texto (pode ser útil para alguns casos)
            elif ext == '.docx':
                try:
                    import importlib
                    docx_module = importlib.import_module("docx")
                    doc = docx_module.Document(arquivo)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    return text if text.strip() else f"[DOCX vazio: {documento.nome_arquivo}]"
                except:
                    return f"[DOCX: {documento.nome_arquivo} - Não foi possível extrair texto]"
            
            else:
                return f"[Arquivo: {documento.nome_arquivo} - Tipo não suportado]"
                
        except Exception as e:
            return f"[Erro ao ler {documento.nome_arquivo}: {str(e)}]"
    
    def _parsear_resposta(self, resposta: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Tenta extrair JSON da resposta com logging detalhado.

        Args:
            resposta: String de resposta da IA
            context: Contexto para logging (stage, provider, model, etc.)

        Returns:
            Dict parseado ou None se falhar
            Se retornar dict com "_error", indica falha com detalhes
        """
        ctx = context or {}
        global _validar_json_pipeline, HAS_VALIDATION

        etapa_nome = ctx.get("stage")
        if isinstance(etapa_nome, EtapaProcessamento):
            etapa_nome = etapa_nome.value

        def _json_raiz_invalida(data: Any) -> Dict[str, Any]:
            tipo = type(data).__name__
            _logger.warning(
                "JSON da IA tem raiz invalida para etapa de pipeline",
                stage=ctx.get("stage"),
                provider=ctx.get("provider"),
                tipo_raiz=tipo,
                raw_response=truncate_for_log(resposta, 300),
            )
            return {
                "_error": "invalid_json_root",
                "_message": (
                    "JSON da IA deve ser um objeto na raiz para esta etapa; "
                    f"recebido {tipo}."
                ),
                "_raw": resposta[:1000],
            }

        def _json_envelopado(origem: str) -> Dict[str, Any]:
            _logger.warning(
                "JSON valido encontrado dentro de envelope proibido",
                stage=ctx.get("stage"),
                provider=ctx.get("provider"),
                origem=origem,
                raw_response=truncate_for_log(resposta, 300),
            )
            return {
                "_error": "invalid_json_envelope",
                "_message": (
                    "A resposta contem JSON valido, mas veio com Markdown, "
                    "comentarios ou texto ao redor. A etapa exige APENAS JSON "
                    "cru, sem envelope."
                ),
                "_raw": resposta[:1000],
                "_attempts": ["direct", origem],
            }

        def _finalizar_json(data: Any, origem: str, raw_fragment: str) -> Any:
            global _validar_json_pipeline, HAS_VALIDATION

            if data == {} or data == []:
                _logger.warning(
                    "JSON vazio retornado pela IA",
                    stage=ctx.get("stage"),
                    provider=ctx.get("provider"),
                    origem=origem,
                    raw_response=truncate_for_log(raw_fragment, 200),
                )
                return {"_error": "empty_json", "_message": "JSON vazio {}", "_raw": raw_fragment[:500]}

            if etapa_nome and not isinstance(data, dict):
                return _json_raiz_invalida(data)

            if isinstance(data, dict) and HAS_VALIDATION and etapa_nome:
                try:
                    if _validar_json_pipeline is None:
                        from pipeline_validation import validar_json_pipeline as vjp
                        _validar_json_pipeline = vjp
                        HAS_VALIDATION = True

                    resultado_validacao = _validar_json_pipeline(etapa_nome, data)
                    if isinstance(resultado_validacao, dict) and resultado_validacao.get("_error"):
                        _logger.warning(
                            "JSON parseado mas falhou na validação estrutural",
                            stage=ctx.get("stage"),
                            provider=ctx.get("provider"),
                            origem=origem,
                            validation_error=resultado_validacao.get("_message"),
                            raw_response=truncate_for_log(raw_fragment, 300),
                        )
                        data["_validation_warning"] = resultado_validacao.get("_message")
                    else:
                        _logger.debug(
                            "JSON validado com sucesso",
                            stage=ctx.get("stage"),
                            provider=ctx.get("provider"),
                            origem=origem,
                        )
                except Exception as ve:
                    _logger.warning(
                        "Erro durante validação JSON",
                        stage=ctx.get("stage"),
                        origem=origem,
                        validation_error=str(ve),
                    )
                    data["_validation_error"] = str(ve)

            return data

        # Validar resposta vazia
        if not resposta:
            _logger.warning(
                "Resposta vazia recebida da IA",
                stage=ctx.get("stage"),
                provider=ctx.get("provider"),
                model=ctx.get("model")
            )
            return {"_error": "empty_response", "_message": "Resposta vazia da IA"}

        # Validar resposta só com espaços
        if not resposta.strip():
            _logger.warning(
                "Resposta contém apenas espaços em branco",
                stage=ctx.get("stage"),
                provider=ctx.get("provider")
            )
            return {"_error": "whitespace_only", "_message": "Resposta apenas com espaços"}

        # Tentativa 1: Parsear diretamente
        try:
            data = json.loads(resposta)
            return _finalizar_json(data, "direct", resposta)
        except json.JSONDecodeError as e:
            _logger.debug(
                f"Parsing direto falhou: {e.msg} na posição {e.pos}",
                stage=ctx.get("stage")
            )

        # Tentativa 2: Extrair de bloco de código ```json
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', resposta)
        if json_match:
            json_str = json_match.group(1).strip()
            if json_str:
                try:
                    data = json.loads(json_str)
                    if etapa_nome:
                        return _json_envelopado("code_block")
                    return _finalizar_json(data, "code_block", json_str)
                except json.JSONDecodeError as e:
                    _logger.debug(
                        f"Parsing de bloco ``` falhou: {e.msg}",
                        stage=ctx.get("stage")
                    )

        # Tentativa 3: Encontrar {} ou [] no texto
        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            match = re.search(pattern, resposta)
            if match:
                try:
                    data = json.loads(match.group())
                    if data == {} or data == []:
                        continue  # Tentar próximo pattern
                    if etapa_nome:
                        return _json_envelopado("regex")
                    return _finalizar_json(data, "regex", match.group())
                except json.JSONDecodeError:
                    continue

        # Todas as tentativas falharam
        _logger.error(
            "Não foi possível extrair JSON da resposta",
            stage=ctx.get("stage"),
            provider=ctx.get("provider"),
            model=ctx.get("model"),
            raw_response=truncate_for_log(resposta, 500)
        )
        return {
            "_error": "parse_failed",
            "_message": "Não foi possível extrair JSON válido",
            "_raw": resposta[:1000],  # Limitar tamanho
            "_attempts": ["direct", "code_block", "regex"]
        }

    def _erro_resposta_parseada(
        self,
        etapa: EtapaProcessamento,
        resposta_parsed: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Return a blocking error when parsed AI output must not be accepted."""
        if not resposta_parsed:
            return "Resposta da IA nao gerou JSON parseavel."

        if not isinstance(resposta_parsed, dict):
            return None

        if resposta_parsed.get("_error"):
            return resposta_parsed.get("_message") or resposta_parsed.get("_error")

        if resposta_parsed.get("_validation_warning"):
            return (
                "JSON nao corresponde ao schema esperado: "
                f"{resposta_parsed.get('_validation_warning')}"
            )

        if resposta_parsed.get("_validation_error"):
            return (
                "Erro ao validar JSON retornado pela IA: "
                f"{resposta_parsed.get('_validation_error')}"
            )

        etapa_nome = etapa.value if hasattr(etapa, "value") else str(etapa)
        if etapa_nome == EtapaProcessamento.EXTRAIR_GABARITO.value:
            respostas = resposta_parsed.get("respostas")
            if isinstance(respostas, list) and respostas:
                todas_missing = all(
                    isinstance(item, dict)
                    and str(item.get("resposta_correta") or "").strip().upper() == "MISSING_CONTENT"
                    for item in respostas
                )
                if todas_missing:
                    return (
                        "EXTRAIR_GABARITO retornou todas as respostas como "
                        "MISSING_CONTENT. Isso nao pode ser tratado como sucesso."
                    )

        if etapa_nome == EtapaProcessamento.EXTRAIR_RESPOSTAS.value:
            respostas = resposta_parsed.get("respostas")
            if isinstance(respostas, list) and respostas:
                inconsistentes = []
                julgamentos = []
                julgamento_pattern = re.compile(
                    (
                        r"\b(corret[oa]s?|incorret[oa]s?|errad[oa]s?|"
                        r"acertou|errou|deveria(?:\s+ser)?|esperad[oa]s?)\b"
                    ),
                    flags=re.IGNORECASE,
                )
                especulacao_pattern = re.compile(
                    r"\b(provavelmente|possivelmente|talvez|aparentemente|deve\s+ter|parece\s+que)\b",
                    flags=re.IGNORECASE,
                )

                def _sem_conteudo(item: Any) -> bool:
                    if not isinstance(item, dict):
                        return False
                    resposta_aluno = str(item.get("resposta_aluno") or "").strip()
                    raciocinio_parcial = str(item.get("raciocinio_parcial") or "").strip()
                    if not resposta_aluno and not item.get("em_branco") and not item.get("ilegivel"):
                        inconsistentes.append(item.get("questao_numero", "?"))
                    if raciocinio_parcial and julgamento_pattern.search(raciocinio_parcial):
                        julgamentos.append(item.get("questao_numero", "?"))
                    if raciocinio_parcial and especulacao_pattern.search(raciocinio_parcial):
                        julgamentos.append(item.get("questao_numero", "?"))
                    return (
                        bool(item.get("ilegivel"))
                        or bool(item.get("em_branco"))
                        or not resposta_aluno
                    )

                marcadores_sem_conteudo = [_sem_conteudo(item) for item in respostas]
                if inconsistentes:
                    questoes = ", ".join(str(q) for q in inconsistentes[:5])
                    return (
                        "EXTRAIR_RESPOSTAS retornou resposta_aluno vazio sem marcar "
                        f"em_branco=true ou ilegivel=true nas questoes: {questoes}. "
                        "Isso e JSON inconsistente e nao pode ser tratado como sucesso."
                    )

                if julgamentos:
                    questoes = ", ".join(str(q) for q in julgamentos[:5])
                    return (
                        "EXTRAIR_RESPOSTAS colocou julgamento/correcao em "
                        f"raciocinio_parcial nas questoes: {questoes}. Esta etapa deve "
                        "transcrever sinais observaveis, nao especular metodo, comparar "
                        "com gabarito nem dizer se a resposta esta correta."
                    )

                todas_sem_conteudo = all(marcadores_sem_conteudo)
                if todas_sem_conteudo:
                    return (
                        "EXTRAIR_RESPOSTAS retornou todas as respostas sem conteudo "
                        "extraido (em branco, ilegiveis ou vazias). Isso nao pode "
                        "ser tratado como sucesso."
                    )

        return None

    def _registrar_custo_resposta_invalida(
        self,
        *,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        provider: str,
        modelo: str,
        tokens_entrada: int,
        tokens_saida: int,
        erro: str,
        tempo_ms: float,
        prompt_id: Optional[str],
        source: str,
        tentativas_validacao: int = 1,
    ) -> None:
        tokens_total = int(tokens_entrada or 0) + int(tokens_saida or 0)
        if tokens_total <= 0:
            return
        try:
            record_token_usage(
                cost_run_id=f"validation_{uuid.uuid4().hex[:12]}",
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                etapa=etapa.value if hasattr(etapa, "value") else str(etapa),
                provider=provider,
                modelo=modelo,
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
                status="erro",
                erro=erro,
                tempo_ms=tempo_ms,
                prompt_id=prompt_id,
                source=source,
                metadata={
                    "erro_tipo": "parsed_response_invalid",
                    "tentativas_validacao": tentativas_validacao,
                },
            )
        except Exception as exc:
            _logger.warning(
                "Falha ao registrar custo de resposta invalida",
                stage=etapa.value if hasattr(etapa, "value") else str(etapa),
                erro=str(exc),
            )
    
    async def _salvar_resultado(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        resposta_raw: str,
        resposta_parsed: Optional[Dict],
        provider: str,
        modelo: str,
        prompt_id: str,
        tokens: int,
        tempo_ms: float,
        gerar_formatos_extras: bool = True,  # Gerar PDF/CSV automaticamente
        criar_nova_versao: bool = False,  # Cria nova versão ao invés de sobrescrever
        tokens_entrada: int = 0,
        tokens_saida: int = 0,
    ) -> Optional[str]:
        """Salva o resultado como documento JSON e opcionalmente gera outros formatos"""
        
        # Determinar tipo de documento
        tipo_map = {
            EtapaProcessamento.EXTRAIR_QUESTOES: TipoDocumento.EXTRACAO_QUESTOES,
            EtapaProcessamento.EXTRAIR_GABARITO: TipoDocumento.EXTRACAO_GABARITO,
            EtapaProcessamento.EXTRAIR_RESPOSTAS: TipoDocumento.EXTRACAO_RESPOSTAS,
            EtapaProcessamento.CORRIGIR: TipoDocumento.CORRECAO,
            EtapaProcessamento.ANALISAR_HABILIDADES: TipoDocumento.ANALISE_HABILIDADES,
            EtapaProcessamento.GERAR_RELATORIO: TipoDocumento.RELATORIO_FINAL,
            EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA: TipoDocumento.RELATORIO_DESEMPENHO_TAREFA,
            EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA: TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
            EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA: TipoDocumento.RELATORIO_DESEMPENHO_MATERIA,
        }
        
        tipo = tipo_map.get(etapa)
        if not tipo:
            return None
        
        # Se criar_nova_versao, buscar documento existente para determinar próxima versão
        versao = 1
        documento_origem_id = None
        if criar_nova_versao:
            docs_existentes = self.storage.listar_documentos(atividade_id, aluno_id)
            docs_tipo = [d for d in docs_existentes if d.tipo == tipo]
            if docs_tipo:
                # Encontrar maior versão
                max_versao = max(d.versao for d in docs_tipo)
                versao = max_versao + 1
                # O documento original é o de versão 1
                doc_original = next((d for d in docs_tipo if d.versao == 1), docs_tipo[0])
                documento_origem_id = doc_original.id
        
        # Criar arquivo temporário com resultado
        conteudo = resposta_parsed if resposta_parsed else {"resposta_raw": resposta_raw}
        metadata_processamento = {
            "tokens_entrada": int(tokens_entrada or 0),
            "tokens_saida": int(tokens_saida or 0),
            "tokens_total": int(tokens or 0),
            "custo_origem": "pipeline_executor",
            "etapa": etapa.value if hasattr(etapa, "value") else str(etapa),
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(conteudo, f, ensure_ascii=False, indent=2)
            temp_path = f.name

        try:
            # Salvar documento JSON (sempre)
            documento = self.storage.salvar_documento(
                arquivo_origem=temp_path,
                tipo=tipo,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                ia_provider=provider,
                ia_modelo=modelo,
                prompt_usado=prompt_id,
                tokens_usados=tokens,
                tempo_processamento_ms=tempo_ms,
                metadata=metadata_processamento,
                criado_por="sistema",
                versao=versao,
                documento_origem_id=documento_origem_id
            )

            documento_id = documento.id if documento else None

            # Gerar formatos extras (PDF, CSV) se configurado
            if gerar_formatos_extras and documento_id:
                # For narrative stages, skip old PDF (will be replaced by narrative PDF)
                # but still generate CSV and other formats
                await self._gerar_formatos_extras(
                    documento_id=documento_id,
                    tipo=tipo,
                    conteudo=conteudo,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    skip_pdf_for_narrative=(etapa in self.NARRATIVA_PROMPT_MAP)
                )

                # Pass 2: Generate narrative PDF for analytical stages
                if etapa in self.NARRATIVA_PROMPT_MAP:
                    await self._gerar_narrativa_pdf(
                        etapa=etapa,
                        conteudo=conteudo,
                        tipo=tipo,
                        atividade_id=atividade_id,
                        aluno_id=aluno_id,
                    )

        finally:
            # Limpar temp JSON
            os.unlink(temp_path)

        return documento_id

    # ============================================================
    # PASS 2: NARRATIVE PDF GENERATION (Two-Pass Pipeline)
    # ============================================================

    # Maps analytical etapas to their internal narrative prompt IDs
    # CORRIGIR removed (F-T1), ANALISAR_HABILIDADES removed (F-T2)
    # F-T3: GERAR_RELATORIO removed — now uses tool-use single-pass (see STAGE_TOOLS)
    NARRATIVA_PROMPT_MAP = {}

    async def _gerar_narrativa_pdf(
        self,
        etapa: EtapaProcessamento,
        conteudo: Dict[str, Any],
        tipo: TipoDocumento,
        atividade_id: str,
        aluno_id: Optional[str],
    ) -> Optional[str]:
        """
        Pass 2: Generate narrative PDF for analytical stages.

        Calls an internal narrative prompt with the JSON from Pass 1,
        converts the Markdown response to PDF, and saves it.

        Returns the document ID of the saved PDF, or None on failure.
        Falls back to old superficial PDF on error.
        """
        prompt_id = self.NARRATIVA_PROMPT_MAP.get(etapa)
        if not prompt_id:
            return None

        try:
            from prompts import render_narrativa_prompt
            from document_generators import narrative_markdown_to_pdf
            import json as json_mod

            # Extract context from the JSON data for template rendering
            nome_aluno = conteudo.get("aluno", conteudo.get("nome_aluno", "Aluno"))
            materia = conteudo.get("materia", "")
            atividade = conteudo.get("atividade", "")
            nota_final = conteudo.get("nota_final", conteudo.get("nota", ""))

            # Render the internal narrative prompt
            rendered = render_narrativa_prompt(
                prompt_id,
                resultado_json=json_mod.dumps(conteudo, ensure_ascii=False, indent=2),
                nome_aluno=nome_aluno,
                materia=materia,
                atividade=atividade,
                nota_final=str(nota_final),
            )
            if not rendered:
                print(f"[WARN] Narrative prompt '{prompt_id}' not found, skipping narrative PDF")
                return None

            # Call AI provider for Pass 2
            provider = self._get_provider_legacy()
            response = await provider.complete(rendered["texto"], rendered["sistema"])

            narrative_md = response.content
            if not narrative_md or len(narrative_md.strip()) < 20:
                print(f"[WARN] Narrative response too short for {etapa.value}, skipping")
                return None

            # Convert Markdown → PDF
            tipo_str = tipo.value if hasattr(tipo, 'value') else str(tipo)
            titulo = tipo_str.replace('_', ' ').title()
            pdf_bytes = narrative_markdown_to_pdf(narrative_md, title=titulo)

            # Save PDF to storage
            temp_pdf_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix='.pdf', mode='wb'
                ) as tmp:
                    tmp.write(pdf_bytes)
                    temp_pdf_path = tmp.name

                doc = self.storage.salvar_documento(
                    arquivo_origem=temp_pdf_path,
                    tipo=tipo,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    criado_por="sistema",
                )

                if doc:
                    print(f"[DOC] Narrative PDF generated for {etapa.value}: {doc.id}")
                    return doc.id
            finally:
                if temp_pdf_path and os.path.exists(temp_pdf_path):
                    os.unlink(temp_pdf_path)

        except Exception as e:
            print(f"[WARN] Narrative PDF generation failed for {etapa.value}: {e}")
            print(f"[WARN] Falling back to structured PDF from JSON data")
            return None

        return None

    async def _gerar_formatos_extras(
        self,
        documento_id: str,
        tipo: TipoDocumento,
        conteudo: Dict[str, Any],
        atividade_id: str,
        aluno_id: Optional[str],
        skip_pdf_for_narrative: bool = False
    ) -> List[str]:
        """
        Gera documentos em formatos adicionais (PDF, CSV) com base no tipo.

        Args:
            skip_pdf_for_narrative: If True, skip PDF generation (narrative PDF
                will be generated separately by _gerar_narrativa_pdf).

        Returns:
            Lista de IDs dos documentos gerados
        """
        from document_generators import (
            OutputFormat, get_output_formats, generate_document, get_file_extension
        )

        tipo_str = tipo.value if hasattr(tipo, 'value') else str(tipo)
        formatos = get_output_formats(tipo_str)

        documentos_gerados = []

        for fmt in formatos:
            # Pular JSON (já foi salvo)
            if fmt == OutputFormat.JSON:
                continue

            # Skip PDF for narrative stages (narrative PDF generated separately)
            if skip_pdf_for_narrative and fmt == OutputFormat.PDF:
                continue
            
            try:
                # Determinar título
                titulo = tipo_str.replace('_', ' ').title()
                
                # Gerar conteúdo no formato
                content = generate_document(conteudo, fmt, titulo, tipo_str)
                
                # Salvar
                extensao = get_file_extension(fmt)
                nome_arquivo = f"{tipo_str}{extensao}"
                
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=extensao, 
                    mode='wb' if isinstance(content, bytes) else 'w',
                    encoding=None if isinstance(content, bytes) else 'utf-8'
                ) as tmp:
                    tmp.write(content)
                    tmp_path = tmp.name
                
                novo_doc = self.storage.salvar_documento(
                    arquivo_origem=tmp_path,
                    tipo=tipo,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    criado_por="sistema"
                    # Nota: metadata não suportado no storage_v2
                )
                
                os.unlink(tmp_path)
                
                if novo_doc:
                    documentos_gerados.append(novo_doc.id)
                    print(f"[DOC] Gerado {fmt.value}: {novo_doc.id}")
                    
            except Exception as e:
                print(f"[WARN] Falha ao gerar {fmt.value}: {e}")
        
        return documentos_gerados
    
    # ============================================================
    # EXECUÇÃO COM TOOLS (Para geração de documentos)
    # ============================================================
    
    async def executar_com_tools(
        self,
        mensagem: str,
        atividade_id: str,
        aluno_id: Optional[str] = None,
        turma_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        tools_to_use: Optional[List[str]] = None,
        expected_document_type: Optional['TipoDocumento'] = None,
        prompt_id: Optional[str] = None,
    ) -> ResultadoExecucao:
        """
        Executa uma chamada de IA com suporte a tools.
        
        Usado quando a IA precisa criar documentos ou executar código.
        O modelo pode chamar create_document múltiplas vezes para
        gerar vários arquivos (ex: relatórios individuais por aluno).
        
        Args:
            mensagem: Prompt para a IA
            atividade_id: ID da atividade
            aluno_id: ID do aluno (opcional)
            turma_id: ID da turma (para geração em lote)
            provider_id: ID do modelo a usar
            system_prompt: System prompt customizado
            tools_to_use: Lista de tools para habilitar (default: create_document, execute_python_code)
        
        Returns:
            ResultadoExecucao com documentos gerados
        """
        inicio = time.time()
        
        try:
            from chat_service import (
                model_manager,
                api_key_manager,
                ChatClient,
                ProviderType,
                ProviderAPIError,
            )
            from tools import ToolRegistry, CREATE_DOCUMENT, EXECUTE_PYTHON_CODE, PIPELINE_TOOLS
            from tool_handlers import TOOL_HANDLERS
            
            # Obter modelo (check models.json first, then ai_registry fallback)
            model = None
            if provider_id:
                model = model_manager.get(provider_id)
                if not model:
                    # Fallback: try resolve_provider_config (supports ai_registry IDs)
                    try:
                        from chat_service import resolve_provider_config
                        config = resolve_provider_config(provider_id)
                        if config:
                            # Find the model by its modelo string
                            model = model_manager.get_by_modelo(config.get("modelo")) if hasattr(model_manager, 'get_by_modelo') else None
                            if not model:
                                # Create a temporary model-like object from config
                                from chat_service import ModelConfig
                                provider_type = config.get("tipo", "openai")
                                model = ModelConfig(
                                    id=provider_id,
                                    nome=config.get("modelo", provider_id),
                                    tipo=ProviderType(provider_type),
                                    modelo=config.get("modelo", ""),
                                    max_tokens=config.get("max_tokens", 4096),
                                    temperature=config.get("temperature", 0.7),
                                    suporta_temperature=config.get("suporta_temperature", True),
                                    suporta_function_calling=provider_type in ("openai", "anthropic", "google"),
                                )
                    except Exception as e:
                        print(f"[executar_com_tools] Fallback provider resolution failed: {e}")
            if not model:
                if provider_id:
                    # User explicitly requested a model that doesn't exist — fail loudly
                    return self._erro(
                        "tools",
                        f"Modelo '{provider_id}' não encontrado. Verifique o ID do modelo "
                        f"em Configurações > Modelos. Nenhum fallback será usado — o pipeline "
                        f"deve rodar com o modelo solicitado ou falhar explicitamente."
                    )
                # No model specified at all — use default
                model = model_manager.get_default()

            if not model:
                return self._erro("tools", "Nenhum modelo configurado. Configure pelo menos um modelo padrão em Configurações > Modelos.")
            
            # Obter API key (DB → api_key_manager → env var fallback)
            api_key = None
            if model.api_key_id:
                key_config = api_key_manager.get(model.api_key_id)
                if key_config:
                    api_key = key_config.api_key
            if not api_key:
                key_config = api_key_manager.get_por_empresa(model.tipo)
                if key_config:
                    api_key = key_config.api_key
            if not api_key:
                # Fallback to environment variables (Render deploys wipe local key store)
                import os
                env_map = {
                    ProviderType.OPENAI: "OPENAI_API_KEY",
                    ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
                    ProviderType.GOOGLE: "GOOGLE_API_KEY",
                }
                env_var = env_map.get(model.tipo)
                if env_var:
                    api_key = os.getenv(env_var, "")

            if not api_key and model.tipo != ProviderType.OLLAMA:
                return self._erro("tools", f"API key não encontrada para {model.tipo.value}")
            
            # Criar registry de tools
            registry = ToolRegistry()
            
            # Determinar quais tools usar
            if tools_to_use is None:
                tools_to_use = ["create_document", "execute_python_code"]
            
            # Registrar tools com handlers
            tools_definitions = []
            for tool in PIPELINE_TOOLS:
                if tool.name in tools_to_use:
                    handler = TOOL_HANDLERS.get(tool.name)
                    if handler:
                        tool.handler = handler
                    registry.register(tool)
                    tool_definition = tool.to_anthropic_format()
                    if tool.name == "create_document" and expected_document_type:
                        tool_definition["description"] = (
                            "Create and save the required structured JSON artifact for this "
                            "pipeline stage. In pipeline stages this tool accepts ONLY .json "
                            "filenames with valid JSON content. Do not use create_document "
                            "for PDF, DOCX, Markdown, text, or narrative files; use "
                            "execute_python_code for PDF generation."
                        )
                        documents_schema = (
                            tool_definition
                            .get("input_schema", {})
                            .get("properties", {})
                            .get("documents", {})
                        )
                        documents_schema["description"] = (
                            "Array with JSON document objects only. Each filename must end "
                            "with .json and content must be valid JSON serialized as a string "
                            "or passed as an object."
                        )
                        content_schema = (
                            documents_schema
                            .get("items", {})
                            .get("properties", {})
                            .get("content")
                        )
                        if isinstance(content_schema, dict):
                            content_schema.clear()
                            content_schema.update({
                                "description": (
                                    "Valid JSON content for the artifact. Prefer passing an "
                                    "object or array directly; a JSON-serialized string is also "
                                    "accepted."
                                ),
                                "anyOf": [
                                    {"type": "object"},
                                    {"type": "array", "items": {}},
                                    {"type": "string"},
                                ],
                            })
                    tools_definitions.append(tool_definition)
            
            # Criar contexto de execução
            from tools import ToolExecutionContext
            context = ToolExecutionContext(
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                session_id=f"pipeline_{atividade_id}_{aluno_id or 'base'}",
                expected_document_type=expected_document_type,
                etapa=expected_document_type.value if expected_document_type else "tools",
                provider=model.tipo.value,
                modelo=model.modelo,
                prompt_id=prompt_id,
                cost_run_id=f"tool_{uuid.uuid4().hex[:12]}",
            )
            if not isinstance(getattr(context, "created_document_ids", None), list):
                context.created_document_ids = []
            
            # Default system prompt para pipeline
            if not system_prompt:
                system_prompt = """Você é um assistente educacional especializado em análise e correção de provas.

CAPACIDADES DE GERAÇÃO DE DOCUMENTOS:
=====================================
Você pode criar documentos usando a ferramenta create_document. Use-a para:
- Gerar relatórios individuais de alunos (PDF, DOCX, MD)
- Criar feedback detalhado para cada estudante
- Produzir análises consolidadas da turma
- Salvar qualquer documento estruturado

IMPORTANTE:
- Você pode criar MÚLTIPLOS documentos em uma única chamada
- Cada documento será salvo e associado ao aluno/atividade correta
- Use nomes de arquivo descritivos (ex: "relatorio_joao_matematica.pdf")

Seja preciso, educativo e construtivo em suas análises."""
            
            # E-T1: Tool capability gate — block non-tool models
            if tools_to_use and not model.suporta_function_calling:
                return ResultadoExecucao(
                    sucesso=False,
                    etapa="tools",
                    erro="Este modelo não suporta geração de documentos. Selecione um modelo compatível com function calling.",
                    provider=model.tipo.value,
                    modelo=model.modelo,
                    tempo_ms=(time.time() - inicio) * 1000,
                )

            # E-T2/P0: dual-output stages must use both tools, never an
            # invented backend fallback. OpenAI gets explicit tool_choice so
            # small reasoning models do not answer in plain text.
            dual_output_expected = (
                "create_document" in tools_to_use
                and "execute_python_code" in tools_to_use
            )
            provider_value = getattr(model.tipo, "value", model.tipo)
            is_openai_provider = provider_value == ProviderType.OPENAI.value
            is_google_provider = provider_value == ProviderType.GOOGLE.value
            uses_phased_tool_calls = is_openai_provider or is_google_provider

            def _forced_openai_tool(tool_name: str) -> Dict[str, Any]:
                return {"type": "function", "function": {"name": tool_name}}

            def _combined_tool_calls(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                calls = []
                for response in responses:
                    calls.extend(response.get("tool_calls", []) or [])
                return calls

            def _sum_usage(responses: List[Dict[str, Any]], key: str) -> int:
                total = 0
                for response in responses:
                    try:
                        total += int(response.get(key, 0) or 0)
                    except (TypeError, ValueError):
                        pass
                return total

            def _safe_response_debug(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                debug: List[Dict[str, Any]] = []
                for idx, response in enumerate(responses, start=1):
                    if not isinstance(response, dict):
                        continue
                    item: Dict[str, Any] = {"tentativa": idx}
                    if response.get("response_status"):
                        item["response_status"] = response.get("response_status")
                    if response.get("stop_reason"):
                        item["stop_reason"] = response.get("stop_reason")
                    if response.get("output_item_types"):
                        item["output_item_types"] = response.get("output_item_types")
                    tool_names = [
                        tc.get("name")
                        for tc in response.get("tool_calls", []) or []
                        if isinstance(tc, dict) and tc.get("name")
                    ]
                    if tool_names:
                        item["tool_calls"] = tool_names
                    preview = response.get("content_preview") or response.get("content") or ""
                    if isinstance(preview, str) and preview.strip():
                        item["content_preview"] = preview.strip()[:300]
                    if len(item) > 1:
                        debug.append(item)
                return debug

            def _created_docs_by_tool() -> Dict[str, List[Any]]:
                docs_by_tool = {"create_document": [], "execute_python_code": []}
                for doc_id in dict.fromkeys(context.created_document_ids):
                    try:
                        doc = self.storage.get_documento(doc_id)
                    except Exception:
                        doc = None
                    if not doc:
                        continue

                    metadata = getattr(doc, "metadata", {}) if isinstance(getattr(doc, "metadata", {}), dict) else {}
                    tool_name = metadata.get("tool")
                    if not tool_name:
                        criado_por = getattr(doc, "criado_por", "") or ""
                        if "execute_python_code" in criado_por:
                            tool_name = "execute_python_code"
                        elif "create_document" in criado_por:
                            tool_name = "create_document"

                    if tool_name in docs_by_tool:
                        docs_by_tool[tool_name].append(doc)
                return docs_by_tool

            def _dual_output_state(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
                calls = _combined_tool_calls(responses)
                has_runtime_metadata = any(
                    "is_error" in tc or "files_generated" in tc
                    for tc in calls
                )
                docs_by_tool = _created_docs_by_tool()
                has_persisted_docs = bool(context.created_document_ids)

                if has_persisted_docs or has_runtime_metadata:
                    has_json = any(
                        (getattr(doc, "extensao", "") or "").lower() == ".json"
                        and not _doc_is_error(doc)
                        for doc in docs_by_tool["create_document"]
                    )
                    has_pdf = any(
                        (getattr(doc, "extensao", "") or "").lower() == ".pdf"
                        and not _doc_is_error(doc)
                        for doc in docs_by_tool["execute_python_code"]
                    )
                else:
                    has_json = any(
                        tc.get("name") == "create_document" and not tc.get("is_error", False)
                        for tc in calls
                    )
                    has_pdf = any(
                        tc.get("name") == "execute_python_code"
                        and not tc.get("is_error", False)
                        and ("files_generated" not in tc or bool(tc.get("files_generated")))
                        for tc in calls
                    )

                missing = []
                if not has_json:
                    missing.append(
                        "JSON persistido via create_document"
                        if has_persisted_docs or has_runtime_metadata
                        else "JSON via create_document"
                    )
                if not has_pdf:
                    missing.append(
                        "PDF persistido via execute_python_code"
                        if has_persisted_docs or has_runtime_metadata
                        else "PDF via execute_python_code"
                    )

                errored_tools = [
                    tc.get("name")
                    for tc in calls
                    if tc.get("name") and tc.get("is_error", False)
                ]
                errored_tool_details = []
                for tc in calls:
                    if not tc.get("is_error", False) or not tc.get("name"):
                        continue
                    detail = tc.get("error_content")
                    if detail:
                        errored_tool_details.append(f"{tc.get('name')}: {detail}")
                pdf_calls_without_file = [
                    tc.get("id") or tc.get("name")
                    for tc in calls
                    if tc.get("name") == "execute_python_code"
                    and not tc.get("is_error", False)
                    and "files_generated" in tc
                    and not tc.get("files_generated")
                ]

                return {
                    "complete": not missing,
                    "missing": missing,
                    "has_json": has_json,
                    "has_pdf": has_pdf,
                    "has_runtime_metadata": has_runtime_metadata,
                    "docs_by_tool": docs_by_tool,
                    "errored_tools": errored_tools,
                    "errored_tool_details": errored_tool_details,
                    "pdf_calls_without_file": pdf_calls_without_file,
                }

            def _retry_message_for_state(state: Dict[str, Any]) -> str:
                missing_json = not state["has_json"]
                missing_pdf = not state["has_pdf"]
                pdf_filename = f"{expected_document_type.value if expected_document_type else 'relatorio'}.pdf"

                contexto_original = str(mensagem or "").strip()
                if len(contexto_original) > 12000:
                    contexto_original = contexto_original[:12000] + "\n...[contexto truncado para retry]..."

                contexto_retry = (
                    "\n\nCONTEXTO ORIGINAL DA ETAPA, OBRIGATÓRIO PARA O RETRY:\n"
                    "Use estes dados reais para nomes, atividade, aluno, matéria, nota e conteúdo. "
                    "NUNCA use placeholders como student123, aluno_teste, nome_do_aluno, "
                    "Aluno ou Student. Se algum dado real estiver ausente, registre aviso "
                    "explícito no artefato em vez de inventar.\n"
                    "```\n"
                    f"{contexto_original}\n"
                    "```"
                )

                if missing_pdf and not missing_json:
                    return (
                        "O JSON foi salvo, mas o PDF obrigatório não foi persistido. "
                        "Chame execute_python_code agora, preencha output_files com "
                        f"['{pdf_filename}'], e use reportlab para salvar exatamente esse arquivo. "
                        + PDF_SANDBOX_RULES
                        + " "
                        "O código precisa gravar esse .pdf real no diretório atual. "
                        "Não responda em texto simples."
                        + contexto_retry
                    )
                if missing_json and not missing_pdf:
                    return (
                        "O PDF foi gerado, mas o JSON obrigatório não foi persistido. "
                        "Chame create_document agora para salvar o JSON estruturado. "
                        "Não responda em texto simples."
                        + contexto_retry
                    )
                return (
                    "Esta etapa exige dois artefatos persistidos: JSON via create_document "
                    "e PDF via execute_python_code. Chame as ferramentas agora; para o PDF, "
                    f"preencha output_files com ['{pdf_filename}'] e salve esse arquivo com reportlab. "
                    + PDF_SANDBOX_RULES
                    + " "
                    "Não responda em texto simples."
                    + contexto_retry
                )

            def _retry_pdf_execution_error_message(state: Dict[str, Any]) -> str:
                pdf_filename = f"{expected_document_type.value if expected_document_type else 'relatorio'}.pdf"
                json_doc = _latest_tool_doc(state, "create_document", ".json")
                json_content = ""
                if json_doc is not None:
                    try:
                        json_content = _read_doc_text_for_retry(json_doc)
                    except Exception as exc:
                        json_content = f"[JSON indisponivel para leitura no retry: {exc}]"

                contexto_original = str(mensagem or "").strip()
                if len(contexto_original) > 6000:
                    contexto_original = contexto_original[:6000] + "\n...[contexto truncado para retry de codigo PDF]..."

                errored_details = [
                    detail
                    for detail in state.get("errored_tool_details", [])
                    if detail.startswith("execute_python_code:")
                ]
                erro_anterior = "\n".join(f"- {detail}" for detail in errored_details) or "- execute_python_code falhou sem detalhe estruturado."

                return (
                    "A tentativa anterior de gerar o PDF com execute_python_code falhou. "
                    "Isto e uma tentativa explicita de reparo no MESMO modelo; nao ha "
                    "fallback automatico.\n"
                    "Nesta chamada, a unica ferramenta disponivel e execute_python_code. "
                    "Nao chame create_document, nao altere o JSON, nao recalcule notas e "
                    "nao invente valores. Corrija somente o codigo Python do PDF.\n"
                    f"Preencha output_files com ['{pdf_filename}'] e salve exatamente esse "
                    "arquivo com reportlab. "
                    + PDF_SANDBOX_RULES
                    + "\n\nERRO DA TENTATIVA ANTERIOR:\n"
                    + erro_anterior
                    + "\n\nCONTEXTO ORIGINAL DA ETAPA:\n```\n"
                    + contexto_original
                    + "\n```\n"
                    + "\n\nJSON OFICIAL JA PERSISTIDO:\n```json\n"
                    + json_content
                    + "\n```\n"
                )

            def _has_execute_python_code_error(state: Dict[str, Any]) -> bool:
                return any(
                    detail.startswith("execute_python_code:")
                    for detail in state.get("errored_tool_details", [])
                )

            def _retry_tools_for_state(state: Dict[str, Any]) -> List[Dict[str, Any]]:
                missing_names = []
                if not state["has_json"]:
                    missing_names.append("create_document")
                if not state["has_pdf"]:
                    missing_names.append("execute_python_code")
                if not missing_names:
                    return tools_definitions
                allowed = set(missing_names)
                return [
                    tool
                    for tool in tools_definitions
                    if tool.get("name") in allowed
                ]

            def _retry_tool_choice_for_state(state: Dict[str, Any]) -> Optional[Any]:
                if not uses_phased_tool_calls:
                    return None
                if not state["has_json"]:
                    return _forced_openai_tool("create_document")
                if not state["has_pdf"]:
                    return _forced_openai_tool("execute_python_code")
                return "required"

            def _initial_tools_for_provider() -> List[Dict[str, Any]]:
                if dual_output_expected and uses_phased_tool_calls:
                    return [
                        tool
                        for tool in tools_definitions
                        if tool.get("name") == "create_document"
                    ]
                return tools_definitions

            def _tools_by_names(names: List[str]) -> List[Dict[str, Any]]:
                allowed = set(names)
                return [
                    tool
                    for tool in tools_definitions
                    if tool.get("name") in allowed
                ]

            def _retry_create_document_message() -> str:
                contexto_original = str(mensagem or "").strip()
                if len(contexto_original) > 12000:
                    contexto_original = contexto_original[:12000] + "\n...[contexto truncado para retry]..."
                return (
                    "A etapa ainda NAO salvou o JSON obrigatorio. Nesta chamada, "
                    "a unica ferramenta disponivel e create_document. Chame "
                    "create_document agora com exatamente um arquivo .json e content "
                    "como JSON valido. Nao gere PDF, Markdown ou texto livre nesta "
                    "chamada; PDF sera uma chamada separada via execute_python_code. "
                    "Nao responda em texto simples.\n\n"
                    "CONTEXTO ORIGINAL DA ETAPA:\n```\n"
                    f"{contexto_original}\n"
                    "```"
                )

            def _initial_message_for_provider() -> str:
                if not (dual_output_expected and is_openai_provider):
                    return mensagem

                contexto_original = str(mensagem or "").strip()
                if len(contexto_original) > 12000:
                    contexto_original = contexto_original[:12000] + "\n...[contexto truncado para primeira chamada]..."

                return (
                    "PRIMEIRA CHAMADA DE ETAPA DUAL-OUTPUT.\n"
                    "Nesta chamada inicial, a unica ferramenta disponivel e create_document. "
                    "Chame create_document agora com exatamente um arquivo .json e content "
                    "como JSON valido. Nao gere PDF, Markdown, narrativa ou texto livre nesta "
                    "chamada; o PDF sera produzido depois em chamada separada via "
                    "execute_python_code. Nao responda em texto simples.\n\n"
                    "PROMPT ORIGINAL DA ETAPA:\n```\n"
                    f"{contexto_original}\n"
                    "```"
                )

            docs_marked_error: set[str] = set()
            correcao_trace_cache: Optional[Dict[str, Dict[Any, str]]] = None

            def _doc_status_value(doc: Any) -> str:
                status = getattr(doc, "status", "") or ""
                return getattr(status, "value", str(status))

            def _doc_is_error(doc: Any) -> bool:
                doc_id = getattr(doc, "id", None)
                return (
                    (doc_id is not None and doc_id in docs_marked_error)
                    or _doc_status_value(doc) == StatusProcessamento.ERRO.value
                )

            def _read_json_doc_for_trace(doc: Any) -> Optional[Dict[str, Any]]:
                try:
                    path = self.storage.resolver_caminho_documento(doc)
                except Exception:
                    return None
                if not path or not Path(path).exists():
                    return None
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except Exception:
                    return None
                return data if isinstance(data, dict) else None

            def _question_key(value: Any) -> Optional[Any]:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    text = str(value or "").strip()
                    return text or None

            def _correcao_trace_maps() -> Dict[str, Dict[Any, str]]:
                """Load upstream answers used to detect correction hallucinations."""
                nonlocal correcao_trace_cache
                if correcao_trace_cache is not None:
                    return correcao_trace_cache

                maps: Dict[str, Dict[Any, str]] = {"respostas_aluno": {}, "gabarito": {}}
                correcao_trace_cache = maps
                if expected_document_type != TipoDocumento.CORRECAO:
                    return maps

                try:
                    docs_base_raw = self.storage.listar_documentos(atividade_id)
                    docs_base = self._documentos_novos_primeiro(list(docs_base_raw or []))
                except Exception:
                    docs_base = []

                try:
                    docs_aluno_raw = (
                        self.storage.listar_documentos(atividade_id, aluno_id)
                        if aluno_id
                        else []
                    )
                    docs_aluno = self._documentos_novos_primeiro(list(docs_aluno_raw or []))
                except Exception:
                    docs_aluno = []

                respostas_doc = self._documento_json_da_ultima_execucao(
                    docs_aluno,
                    TipoDocumento.EXTRACAO_RESPOSTAS,
                )
                respostas_data = _read_json_doc_for_trace(respostas_doc) if respostas_doc else None
                if isinstance(respostas_data, dict):
                    for item in respostas_data.get("respostas") or []:
                        if not isinstance(item, dict):
                            continue
                        key = _question_key(item.get("questao_numero"))
                        if key is not None and item.get("resposta_aluno") is not None:
                            maps["respostas_aluno"][key] = str(item.get("resposta_aluno"))

                gabarito_doc = self._documento_json_da_ultima_execucao(
                    docs_base,
                    TipoDocumento.EXTRACAO_GABARITO,
                )
                gabarito_data = _read_json_doc_for_trace(gabarito_doc) if gabarito_doc else None
                if isinstance(gabarito_data, dict):
                    for item in gabarito_data.get("respostas") or []:
                        if not isinstance(item, dict):
                            continue
                        key = _question_key(item.get("questao_numero"))
                        if key is not None and item.get("resposta_correta") is not None:
                            maps["gabarito"][key] = str(item.get("resposta_correta"))

                return maps

            def _json_schema_errors_for_data(
                data: Any,
                doc_label: str,
                filename: str = "",
            ) -> List[str]:
                """Fail high on known placeholder/schema leaks in JSON payloads."""
                errors: List[str] = []
                placeholders = (
                    "student123",
                    "aluno_teste",
                    "nome_do_aluno",
                    "nome do aluno",
                    "student_name",
                    "<nome",
                    "<str>",
                )

                serialized = json.dumps(data, ensure_ascii=False).lower()
                for placeholder in placeholders:
                    if placeholder in serialized or placeholder in filename:
                        errors.append(f"JSON {doc_label} contém placeholder proibido: {placeholder}")
                        break

                if not isinstance(data, dict):
                    errors.append(
                        f"JSON {doc_label} deve ser objeto JSON na raiz, não {type(data).__name__}"
                    )
                    return errors

                def _numeric(value: Any) -> bool:
                    if isinstance(value, (int, float)):
                        return math.isfinite(float(value))
                    if isinstance(value, str):
                        try:
                            return math.isfinite(float(value.replace(",", ".")))
                        except ValueError:
                            return False
                    return False

                def _format_schema_num(value: float) -> str:
                    if float(value).is_integer():
                        return str(int(value))
                    return f"{value:.2f}".rstrip("0").rstrip(".")

                def _required_list(field: str) -> None:
                    if not isinstance(data.get(field), list):
                        errors.append(f"JSON {doc_label} sem {field} como lista")

                def _validate_aviso_codes(
                    field: str,
                    allowed_codes: set[str],
                    label: str,
                ) -> None:
                    items = data.get(field)
                    if not isinstance(items, list):
                        return
                    for index, aviso in enumerate(items):
                        if not isinstance(aviso, dict):
                            errors.append(
                                f"JSON {doc_label} tem {field}[{index}] que não é objeto"
                            )
                            continue
                        codigo = aviso.get("codigo")
                        if not isinstance(codigo, str) or not codigo.strip():
                            errors.append(
                                f"JSON {doc_label} tem {field}[{index}].codigo ausente"
                            )
                            continue
                        normalized = codigo.strip().upper()
                        if "|" in normalized:
                            errors.append(
                                f"JSON {doc_label} tem {field}[{index}].codigo composto "
                                f"'{codigo}'; use um aviso por codigo"
                            )
                            continue
                        if normalized not in allowed_codes:
                            allowed = ", ".join(sorted(allowed_codes))
                            errors.append(
                                f"JSON {doc_label} tem {field}[{index}].codigo invalido "
                                f"'{codigo}' para {label}; codigos validos: {allowed}"
                            )

                def _validate_avisos() -> None:
                    _validate_aviso_codes(
                        "_avisos_documento",
                        {"ILLEGIBLE_DOCUMENT", "MISSING_CONTENT", "LOW_CONFIDENCE"},
                        "_avisos_documento",
                    )
                    _validate_aviso_codes(
                        "_avisos_questao",
                        {"ILLEGIBLE_QUESTION", "MISSING_CONTENT", "LOW_CONFIDENCE"},
                        "_avisos_questao",
                    )

                def _required_text(field: str) -> None:
                    if not isinstance(data.get(field), str) or not data.get(field, "").strip():
                        errors.append(f"JSON {doc_label} sem {field} textual")

                def _normalize_answer(value: Any) -> str:
                    text = str(value or "").strip().lower()
                    text = unicodedata.normalize("NFKD", text)
                    text = "".join(ch for ch in text if not unicodedata.combining(ch))
                    text = text.replace("²", "2")
                    text = re.sub(r"\s+", "", text)
                    text = re.sub(r"[\.;]+$", "", text)
                    return text

                def _single_numeric(value: Any) -> Optional[float]:
                    numbers = re.findall(r"-?\d+(?:[\.,]\d+)?", str(value or ""))
                    if len(numbers) != 1:
                        return None
                    try:
                        return float(numbers[0].replace(",", "."))
                    except ValueError:
                        return None

                def _simple_literal_for_blocking(value: Any) -> Optional[str]:
                    normalized = _normalize_answer(value)
                    if not normalized or _single_numeric(value) is not None:
                        return None
                    if re.fullmatch(r"[a-z]", normalized):
                        return normalized
                    if normalized in {"verdadeiro", "falso", "true", "false", "sim", "nao"}:
                        return normalized
                    if (
                        len(normalized) <= 12
                        and re.fullmatch(r"[a-z]+", normalized)
                        and len(str(value or "").split()) <= 2
                    ):
                        return normalized
                    return None

                if expected_document_type == TipoDocumento.CORRECAO:
                    if not _numeric(data.get("nota_final")):
                        errors.append(f"JSON {doc_label} sem nota_final numérica")
                    questoes = data.get("questoes")
                    if not isinstance(questoes, list) or not questoes:
                        errors.append(f"JSON {doc_label} sem lista de questoes")
                    if not isinstance(data.get("feedback_geral"), str) or not data.get("feedback_geral", "").strip():
                        errors.append(f"JSON {doc_label} sem feedback_geral textual")
                    if not _numeric(data.get("total_acertos")):
                        errors.append(f"JSON {doc_label} sem total_acertos numérico")
                    if not _numeric(data.get("total_erros")):
                        errors.append(f"JSON {doc_label} sem total_erros numérico")
                    _required_list("_avisos_documento")
                    _required_list("_avisos_questao")
                    _validate_avisos()
                    if isinstance(questoes, list):
                        trace_maps = _correcao_trace_maps()
                        has_respostas = bool(trace_maps["respostas_aluno"])
                        has_gabarito = bool(trace_maps["gabarito"])
                        soma_notas = 0.0
                        notas_validas = 0
                        acertos_calculados = 0
                        erros_calculados = 0
                        acertos_ou_erros = 0
                        for item in questoes:
                            if not isinstance(item, dict):
                                errors.append(f"JSON {doc_label} tem item de questoes que não é objeto")
                                continue
                            numero = _question_key(item.get("numero"))
                            questao_label = numero if numero is not None else "?"
                            nota_item = self._nota_como_float(item.get("nota"))
                            if nota_item is None:
                                errors.append(
                                    f"JSON {doc_label} questão {questao_label} sem nota numérica"
                                )
                            else:
                                soma_notas += nota_item
                                notas_validas += 1

                            if item.get("acerto") is True:
                                acertos_calculados += 1
                                acertos_ou_erros += 1
                            elif item.get("acerto") is False:
                                erros_calculados += 1
                                acertos_ou_erros += 1
                            else:
                                errors.append(
                                    f"JSON {doc_label} questão {questao_label} sem acerto booleano"
                                )

                            if has_respostas:
                                resposta_aluno = item.get("resposta_aluno")
                                if resposta_aluno is None or not str(resposta_aluno).strip():
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} sem resposta_aluno rastreável"
                                    )
                                upstream = trace_maps["respostas_aluno"].get(numero)
                                if (
                                    upstream is not None
                                    and resposta_aluno is not None
                                    and _normalize_answer(resposta_aluno) != _normalize_answer(upstream)
                                ):
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} tem resposta_aluno "
                                        "divergente da EXTRAIR_RESPOSTAS"
                                    )

                            if has_gabarito:
                                resposta_correta = item.get("resposta_correta")
                                if resposta_correta is None or not str(resposta_correta).strip():
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} sem resposta_correta rastreável"
                                    )
                                upstream = trace_maps["gabarito"].get(numero)
                                if (
                                    upstream is not None
                                    and resposta_correta is not None
                                    and _normalize_answer(resposta_correta) != _normalize_answer(upstream)
                                ):
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} tem resposta_correta "
                                        "divergente da EXTRACAO_GABARITO"
                                    )

                            resposta_aluno_num = _single_numeric(item.get("resposta_aluno"))
                            resposta_correta_num = _single_numeric(item.get("resposta_correta"))
                            if (
                                resposta_aluno_num is not None
                                and resposta_correta_num is not None
                                and abs(resposta_aluno_num - resposta_correta_num) > 0.001
                            ):
                                nota = self._nota_como_float(item.get("nota"))
                                nota_maxima = self._nota_como_float(item.get("nota_maxima"))
                                if item.get("acerto") is True:
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} marcada acerto=true "
                                        "apesar de resposta_aluno numérica divergir do gabarito"
                                    )
                                if (
                                    nota is not None
                                    and nota_maxima is not None
                                    and nota_maxima > 0
                                    and nota >= nota_maxima - 0.001
                                ):
                                    errors.append(
                                        f"JSON {doc_label} questão {questao_label} recebeu nota máxima "
                                        "apesar de resposta_aluno numérica divergir do gabarito"
                                    )
                            elif resposta_aluno_num is None and resposta_correta_num is None:
                                resposta_aluno_literal = _simple_literal_for_blocking(
                                    item.get("resposta_aluno")
                                )
                                resposta_correta_literal = _simple_literal_for_blocking(
                                    item.get("resposta_correta")
                                )
                                if (
                                    resposta_aluno_literal is not None
                                    and resposta_correta_literal is not None
                                    and resposta_aluno_literal != resposta_correta_literal
                                ):
                                    nota = self._nota_como_float(item.get("nota"))
                                    nota_maxima = self._nota_como_float(item.get("nota_maxima"))
                                    if item.get("acerto") is True:
                                        errors.append(
                                            f"JSON {doc_label} questão {questao_label} marcada acerto=true "
                                            "apesar de resposta_aluno literal divergir do gabarito"
                                        )
                                    if (
                                        nota is not None
                                        and nota_maxima is not None
                                        and nota_maxima > 0
                                        and nota >= nota_maxima - 0.001
                                    ):
                                        errors.append(
                                            f"JSON {doc_label} questão {questao_label} recebeu nota máxima "
                                            "apesar de resposta_aluno literal divergir do gabarito"
                                        )

                        nota_final = self._nota_como_float(data.get("nota_final"))
                        if (
                            nota_final is not None
                            and notas_validas == len(questoes)
                            and abs(soma_notas - nota_final) > 0.01
                        ):
                            errors.append(
                                f"JSON {doc_label} tem nota_final {_format_schema_num(nota_final)} "
                                f"mas a soma de questoes[].nota e {_format_schema_num(soma_notas)}"
                            )

                        total_acertos = self._nota_como_float(data.get("total_acertos"))
                        if (
                            total_acertos is not None
                            and acertos_ou_erros == len(questoes)
                            and abs(total_acertos - acertos_calculados) > 0.01
                        ):
                            errors.append(
                                f"JSON {doc_label} tem total_acertos {_format_schema_num(total_acertos)} "
                                f"mas questoes[].acerto indica {acertos_calculados}"
                            )

                        total_erros = self._nota_como_float(data.get("total_erros"))
                        if (
                            total_erros is not None
                            and acertos_ou_erros == len(questoes)
                            and abs(total_erros - erros_calculados) > 0.01
                        ):
                            errors.append(
                                f"JSON {doc_label} tem total_erros {_format_schema_num(total_erros)} "
                                f"mas questoes[].acerto indica {erros_calculados}"
                            )

                if expected_document_type == TipoDocumento.ANALISE_HABILIDADES:
                    habilidades = data.get("habilidades")
                    if not isinstance(habilidades, (list, dict)) or not habilidades:
                        errors.append(f"JSON {doc_label} sem lista/dicionário de habilidades")
                    if not isinstance(data.get("indicadores"), dict):
                        errors.append(f"JSON {doc_label} sem indicadores como objeto")
                    _required_list("recomendacoes")
                    _required_list("_avisos_documento")
                    _required_list("_avisos_questao")
                    _validate_avisos()

                if expected_document_type == TipoDocumento.RELATORIO_FINAL:
                    if not _numeric(data.get("nota_final")):
                        errors.append(f"JSON {doc_label} sem nota_final numérica")
                    _required_text("resumo_geral")
                    _required_list("pontos_fortes")
                    _required_list("areas_melhoria")
                    _required_list("recomendacoes")
                    _required_text("detalhamento")
                    _required_list("_avisos_documento")
                    _required_list("_avisos_questao")
                    _validate_avisos()
                    _required_list("_fontes_utilizadas")
                    errors.extend(
                        self._validar_relatorio_nota_final_contra_correcao(
                            data,
                            atividade_id,
                            aluno_id,
                            doc_label,
                        )
                    )

                return errors

            def _json_schema_errors_for_doc(doc: Any) -> List[str]:
                """Fail high on known placeholder/schema leaks in persisted JSON."""
                doc_label = getattr(doc, "id", None) or getattr(doc, "nome_arquivo", "json")
                filename = (getattr(doc, "nome_arquivo", "") or "").lower()
                try:
                    path = self.storage.resolver_caminho_documento(doc)
                except Exception as exc:
                    return [f"JSON {doc_label} não pôde ser resolvido para validação: {exc}"]

                if not path or not Path(path).exists():
                    return [f"JSON {doc_label} não pôde ser lido para validação"]

                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except Exception as exc:
                    return [f"JSON {doc_label} inválido: {exc}"]

                return _json_schema_errors_for_data(data, doc_label, filename)

            def _invalid_json_artifacts(state: Dict[str, Any]) -> List[tuple[Any, List[str]]]:
                if expected_document_type not in {
                    TipoDocumento.CORRECAO,
                    TipoDocumento.ANALISE_HABILIDADES,
                    TipoDocumento.RELATORIO_FINAL,
                }:
                    return []

                invalid: List[tuple[Any, List[str]]] = []
                for doc in state.get("docs_by_tool", {}).get("create_document", []):
                    if (getattr(doc, "extensao", "") or "").lower() != ".json":
                        continue
                    if _doc_is_error(doc):
                        continue
                    errors = _json_schema_errors_for_doc(doc)
                    if errors:
                        invalid.append((doc, errors))
                return invalid

            def _validate_json_artifacts(state: Dict[str, Any]) -> List[str]:
                errors: List[str] = []
                for _, doc_errors in _invalid_json_artifacts(state):
                    errors.extend(doc_errors)
                if (
                    expected_document_type in {
                        TipoDocumento.CORRECAO,
                        TipoDocumento.ANALISE_HABILIDADES,
                        TipoDocumento.RELATORIO_FINAL,
                    }
                    and not state.get("docs_by_tool", {}).get("create_document")
                ):
                    for idx, tc in enumerate(_combined_tool_calls(respostas_tool), start=1):
                        if tc.get("name") != "create_document":
                            continue
                        docs_input = tc.get("input", {}).get("documents", [])
                        if isinstance(docs_input, dict):
                            docs = [docs_input]
                        elif isinstance(docs_input, list):
                            docs = docs_input
                        else:
                            docs = []
                        if not docs and tc.get("input", {}).get("content") is not None:
                            docs = [{"content": tc.get("input", {}).get("content")}]
                        for doc_idx, doc in enumerate(docs, start=1):
                            if not isinstance(doc, dict):
                                continue
                            label = doc.get("filename") or f"runtime create_document {idx}.{doc_idx}"
                            content = doc.get("content")
                            if isinstance(content, dict):
                                data = content
                            elif isinstance(content, str):
                                try:
                                    data = json.loads(content)
                                except Exception as exc:
                                    errors.append(f"JSON {label} inválido: {exc}")
                                    continue
                            else:
                                errors.append(f"JSON {label} sem content JSON")
                                continue
                            errors.extend(_json_schema_errors_for_data(data, str(label), str(label).lower()))
                return errors

            def _latest_tool_doc(
                state: Dict[str, Any],
                tool_name: str,
                extension: str,
            ) -> Optional[Any]:
                docs = state.get("docs_by_tool", {}).get(tool_name, [])
                for doc in reversed(docs):
                    if (getattr(doc, "extensao", "") or "").lower() == extension:
                        return doc
                return None

            def _read_doc_text_for_retry(doc: Any, max_chars: int = 16000) -> str:
                path = self.storage.resolver_caminho_documento(doc)
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                if len(content) > max_chars:
                    return content[:max_chars] + "\n...[json truncado para retry]..."
                return content

            def _etapa_resultado_tool_use() -> Union[EtapaProcessamento, str]:
                tipo_para_etapa = {
                    TipoDocumento.CORRECAO: EtapaProcessamento.CORRIGIR,
                    TipoDocumento.ANALISE_HABILIDADES: EtapaProcessamento.ANALISAR_HABILIDADES,
                    TipoDocumento.RELATORIO_FINAL: EtapaProcessamento.GERAR_RELATORIO,
                    TipoDocumento.RELATORIO_DESEMPENHO_TAREFA: EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA,
                    TipoDocumento.RELATORIO_DESEMPENHO_TURMA: EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA,
                    TipoDocumento.RELATORIO_DESEMPENHO_MATERIA: EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA,
                }
                if expected_document_type:
                    return tipo_para_etapa.get(expected_document_type, expected_document_type.value)
                return "tools"

            def _json_doc_oficial(state: Dict[str, Any]) -> Optional[Any]:
                docs = state.get("docs_by_tool", {}).get("create_document", [])
                for doc in reversed(docs):
                    if (getattr(doc, "extensao", "") or "").lower() == ".json" and not _doc_is_error(doc):
                        return doc
                return None

            def _json_from_content(raw: Any) -> Optional[Dict[str, Any]]:
                if isinstance(raw, dict):
                    return raw
                if not isinstance(raw, str) or not raw.strip():
                    return None
                try:
                    parsed = json.loads(raw)
                except Exception:
                    return None
                return parsed if isinstance(parsed, dict) else None

            def _json_from_tool_calls() -> Optional[Dict[str, Any]]:
                for tc in reversed(_combined_tool_calls(respostas_tool)):
                    if tc.get("name") != "create_document":
                        continue
                    docs_input = tc.get("input", {}).get("documents", [])
                    if isinstance(docs_input, dict):
                        docs = [docs_input]
                    elif isinstance(docs_input, list):
                        docs = docs_input
                    else:
                        docs = []
                    for doc in reversed(docs):
                        if not isinstance(doc, dict):
                            continue
                        parsed = _json_from_content(doc.get("content"))
                        if parsed is not None:
                            return parsed
                    parsed = _json_from_content(tc.get("input", {}).get("content"))
                    if parsed is not None:
                        return parsed
                return None

            def _resposta_parsed_e_documento_principal(state: Dict[str, Any]) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
                json_doc = _json_doc_oficial(state)
                if json_doc is not None:
                    doc_id = getattr(json_doc, "id", None)
                    try:
                        path = self.storage.resolver_caminho_documento(json_doc)
                        with open(path, "r", encoding="utf-8") as fh:
                            parsed = json.load(fh)
                        if isinstance(parsed, dict):
                            return parsed, doc_id
                    except Exception as exc:
                        _logger.warning(
                            "Nao foi possivel carregar JSON principal de tool-use",
                            documento_id=doc_id,
                            erro=str(exc),
                        )
                    return None, doc_id

                return _json_from_tool_calls(), None

            def _retry_pdf_consistency_message(
                state: Dict[str, Any],
                pdf_errors: List[str],
            ) -> str:
                json_doc = _latest_tool_doc(state, "create_document", ".json")
                json_content = ""
                if json_doc is not None:
                    try:
                        json_content = _read_doc_text_for_retry(json_doc)
                    except Exception as exc:
                        json_content = f"[JSON indisponivel para leitura no retry: {exc}]"
                contexto_original = str(mensagem or "").strip()
                if len(contexto_original) > 6000:
                    contexto_original = contexto_original[:6000] + "\n...[contexto truncado para retry de PDF]..."

                pdf_filename = f"{expected_document_type.value if expected_document_type else 'relatorio'}.pdf"
                return (
                    "O PDF gerado divergiu do JSON oficial validado. Isto e erro "
                    "bloqueante, mas voce tem uma tentativa explicita de reparo no "
                    "MESMO modelo.\n"
                    "Nesta chamada, a unica ferramenta disponivel e execute_python_code. "
                    "Nao chame create_document, nao altere o JSON, nao recalcule notas "
                    "e nao invente valores. Gere novamente apenas o PDF usando exatamente "
                    "os valores do JSON abaixo.\n"
                    f"Preencha output_files com ['{pdf_filename}'] e salve um PDF real "
                    "com reportlab. "
                    + PDF_SANDBOX_RULES
                    + " Se for CORRIGIR, cada questao exibida no PDF deve "
                    "usar exatamente questoes[].nota do JSON; a nota final do PDF deve "
                    "usar exatamente nota_final do JSON. O cabecalho do PDF nao pode usar "
                    "placeholders como '—', 'N/A' ou 'Nao informado' para aluno, materia, "
                    "atividade ou data; use os metadados do prompt original quando estiverem "
                    "disponiveis. Se for GERAR_RELATORIO, "
                    "nota_final e proficiencia_geral devem aparecer como metricas "
                    "separadas.\n\n"
                    "ERROS DETECTADOS NO PDF ANTERIOR:\n"
                    + "\n".join(f"- {error}" for error in pdf_errors)
                    + "\n\nCONTEXTO ORIGINAL DA ETAPA, INCLUINDO METADADOS DO CABECALHO:\n```\n"
                    + contexto_original
                    + "\n```\n"
                    + "\n\nJSON OFICIAL VALIDADO:\n```json\n"
                    + json_content
                    + "\n```\n"
                )

            def _retry_json_validation_message(
                state: Dict[str, Any],
                json_errors: List[str],
            ) -> str:
                json_doc = _latest_tool_doc(state, "create_document", ".json")
                json_content = ""
                if json_doc is not None:
                    try:
                        json_content = _read_doc_text_for_retry(json_doc)
                    except Exception as exc:
                        json_content = f"[JSON anterior indisponivel para leitura no retry: {exc}]"

                schema_hint = ""
                if expected_document_type == TipoDocumento.CORRECAO:
                    schema_hint = (
                        "Para CORRIGIR, o content salvo por create_document deve ser "
                        "um OBJETO JSON na raiz, nunca uma lista/array. Campos "
                        "obrigatorios na raiz: nota_final, questoes, total_acertos, "
                        "total_erros, feedback_geral, _avisos_documento, "
                        "_avisos_questao. Cada item em questoes deve copiar "
                        "resposta_aluno da EXTRACAO_RESPOSTAS e resposta_correta "
                        "da EXTRACAO_GABARITO. "
                    )
                if expected_document_type == TipoDocumento.ANALISE_HABILIDADES:
                    schema_hint = (
                        "Para ANALISAR_HABILIDADES, o content salvo por create_document "
                        "deve ser um OBJETO JSON na raiz, nunca uma lista/array. "
                        "Campos obrigatorios na raiz: habilidades, indicadores, "
                        "recomendacoes, _avisos_documento, _avisos_questao. "
                    )
                if expected_document_type == TipoDocumento.RELATORIO_FINAL:
                    schema_hint = (
                        "Para GERAR_RELATORIO, o content salvo por create_document "
                        "deve ser um OBJETO JSON na raiz, nunca uma lista/array. "
                        "Campos obrigatorios na raiz: resumo_geral, pontos_fortes, "
                        "areas_melhoria, recomendacoes, nota_final, detalhamento, "
                        "_avisos_documento, _avisos_questao, _fontes_utilizadas. "
                        "A nota_final deve ser exatamente a nota_final da CORRECAO "
                        "oficial mais recente. "
                    )

                return (
                    "O JSON salvo nao respeitou o schema obrigatorio da etapa. Isto e "
                    "erro bloqueante, mas voce tem uma tentativa explicita de reparo no "
                    "MESMO modelo.\n"
                    "Nesta chamada, a unica ferramenta disponivel e create_document. "
                    "Nao gere PDF, nao responda em texto livre e nao mude o conteudo "
                    "pedagogico; apenas salve novamente um arquivo .json com schema "
                    "valido.\n"
                    + schema_hint
                    + "\nERROS DETECTADOS NO JSON ANTERIOR:\n"
                    + "\n".join(f"- {error}" for error in json_errors)
                    + "\n\nJSON ANTERIOR INVALIDO:\n```json\n"
                    + json_content
                    + "\n```\n"
                )

            def _mark_invalid_json_errors(
                state: Dict[str, Any],
                erro_msg: str,
            ) -> None:
                for json_doc, _ in _invalid_json_artifacts(state):
                    docs_marked_error.add(getattr(json_doc, "id"))
                    self.storage.atualizar_documento_processamento(
                        getattr(json_doc, "id"),
                        status=StatusProcessamento.ERRO,
                        metadata_patch={
                            "erro_pipeline": erro_msg,
                            "erro_tipo": "json_schema_validation",
                            "cost_run_id": context.cost_run_id,
                        },
                    )

            def _mark_latest_pdf_error(
                state: Dict[str, Any],
                erro_msg: str,
            ) -> None:
                pdf_doc = _latest_tool_doc(state, "execute_python_code", ".pdf")
                if not pdf_doc:
                    return
                docs_marked_error.add(getattr(pdf_doc, "id"))
                self.storage.atualizar_documento_processamento(
                    getattr(pdf_doc, "id"),
                    status=StatusProcessamento.ERRO,
                    metadata_patch={
                        "erro_pipeline": erro_msg,
                        "erro_tipo": "pdf_json_consistency",
                        "cost_run_id": context.cost_run_id,
                    },
                )

            def _mark_stale_dual_output_artifacts(
                state: Dict[str, Any],
                tokens_entrada: int,
                tokens_saida: int,
                tokens_total: int,
                tempo_ms: float,
            ) -> List[str]:
                if not dual_output_expected:
                    return []

                marked: List[str] = []
                specs = [
                    ("create_document", ".json", "JSON"),
                    ("execute_python_code", ".pdf", "PDF"),
                ]
                for tool_name, extension, label in specs:
                    docs = [
                        doc
                        for doc in state.get("docs_by_tool", {}).get(tool_name, [])
                        if (getattr(doc, "extensao", "") or "").lower() == extension
                        and not _doc_is_error(doc)
                    ]
                    if len(docs) <= 1:
                        continue

                    official_doc = docs[-1]
                    official_id = getattr(official_doc, "id", "artefato oficial")
                    for stale_doc in docs[:-1]:
                        stale_id = getattr(stale_doc, "id", None)
                        if not stale_id:
                            continue
                        docs_marked_error.add(stale_id)
                        erro_msg = (
                            f"Artefato {label} extra gerado pela etapa. "
                            f"Somente o mais recente validado ({official_id}) "
                            "permanece como artefato oficial."
                        )
                        self.storage.atualizar_documento_processamento(
                            stale_id,
                            ia_provider=model.tipo.value,
                            ia_modelo=model.modelo,
                            prompt_usado=prompt_id,
                            tokens_usados=tokens_total,
                            tempo_processamento_ms=tempo_ms,
                            status=StatusProcessamento.ERRO,
                            metadata_patch={
                                "erro_pipeline": erro_msg,
                                "erro_tipo": "stale_tool_artifact",
                                "tokens_entrada": tokens_entrada,
                                "tokens_saida": tokens_saida,
                                "tokens_total": tokens_total,
                                "cost_run_id": context.cost_run_id,
                                "custo_origem": "tool_use",
                            },
                        )
                        marked.append(f"{label} extra {stale_id} marcado como erro")
                return marked

            initial_tool_choice = (
                _forced_openai_tool("create_document")
                if dual_output_expected and uses_phased_tool_calls
                else None
            )

            # Executar com tools
            client = ChatClient(model, api_key or "")
            resposta = await client.chat_with_tools(
                mensagem=_initial_message_for_provider(),
                tools=_initial_tools_for_provider(),
                tool_registry=registry,
                system_prompt=system_prompt,
                context=context,
                tool_choice=initial_tool_choice,
            )

            tentativas = 1
            alertas = []
            respostas_tool = [resposta]

            if dual_output_expected:
                state = _dual_output_state(respostas_tool)
                if uses_phased_tool_calls:
                    if not state["has_json"]:
                        resposta = await client.chat_with_tools(
                            mensagem=_retry_create_document_message(),
                            tools=_tools_by_names(["create_document"]),
                            tool_registry=registry,
                            system_prompt=system_prompt,
                            context=context,
                            tool_choice=_forced_openai_tool("create_document"),
                        )
                        respostas_tool.append(resposta)
                        tentativas += 1
                        state = _dual_output_state(respostas_tool)

                    if state["has_json"] and not state["has_pdf"]:
                        resposta = await client.chat_with_tools(
                            mensagem=_retry_message_for_state(state),
                            tools=_tools_by_names(["execute_python_code"]),
                            tool_registry=registry,
                            system_prompt=system_prompt,
                            context=context,
                            tool_choice=_forced_openai_tool("execute_python_code"),
                        )
                        respostas_tool.append(resposta)
                        tentativas += 1
                        state = _dual_output_state(respostas_tool)

                    if state["has_json"] and not state["has_pdf"] and _has_execute_python_code_error(state):
                        resposta = await client.chat_with_tools(
                            mensagem=_retry_pdf_execution_error_message(state),
                            tools=_tools_by_names(["execute_python_code"]),
                            tool_registry=registry,
                            system_prompt=system_prompt,
                            context=context,
                            tool_choice=_forced_openai_tool("execute_python_code"),
                        )
                        respostas_tool.append(resposta)
                        tentativas += 1
                        state = _dual_output_state(respostas_tool)

                    if not state["complete"]:
                        alertas.append({
                            "tipo": "aviso",
                            "mensagem": (
                                "Saída incompleta após retry: "
                                + ", ".join(state["missing"])
                                + ". A etapa falhará sem fallback automático."
                            )
                        })
                elif not state["complete"]:
                    # Partial/missing output — one explicit retry on the same model.
                    retry_msg = _retry_message_for_state(state)
                    retry_tools_definitions = _retry_tools_for_state(state)
                    retry_tool_choice = _retry_tool_choice_for_state(state)

                    resposta = await client.chat_with_tools(
                        mensagem=retry_msg,
                        tools=retry_tools_definitions,
                        tool_registry=registry,
                        system_prompt=system_prompt,
                        context=context,
                        tool_choice=retry_tool_choice,
                    )
                    respostas_tool.append(resposta)
                    tentativas += 1

                    # Check again after retry
                    state = _dual_output_state(respostas_tool)
                    if not state["complete"]:
                        alertas.append({
                            "tipo": "aviso",
                            "mensagem": (
                                "Saída incompleta após retry: "
                                + ", ".join(state["missing"])
                                + ". A etapa falhará sem fallback automático."
                            )
                        })

            tempo_ms = (time.time() - inicio) * 1000

            # Coletar documentos gerados pelas tools
            documentos_gerados = []
            tool_calls = _combined_tool_calls(respostas_tool)
            for tc in tool_calls:
                if tc.get("name") == "create_document":
                    docs_input = tc.get("input", {}).get("documents", [])
                    if isinstance(docs_input, dict):
                        docs = [docs_input]
                    elif isinstance(docs_input, list):
                        docs = docs_input
                    else:
                        docs = []
                    for doc in docs:
                        if isinstance(doc, dict):
                            documentos_gerados.append(doc.get("filename", "documento"))

            if documentos_gerados:
                alertas.append({"tipo": "info", "mensagem": f"Documentos gerados: {documentos_gerados}"})

            # F2-T2: Check for max_iterations error and add alert
            if resposta.get("error") == "max_iterations_exceeded":
                alertas.append({
                    "tipo": "aviso",
                    "mensagem": "Limite máximo de iterações de tools atingido. Resultado pode estar incompleto."
                })

            # F2-T1: Extract resposta_raw from create_document tool content
            # when the API content field is empty (LLM was busy calling tools)
            raw_content = resposta.get("content") or ""
            is_sentinel = raw_content == "[Maximum tool iterations reached]"

            if not raw_content.strip() or is_sentinel:
                # Look for create_document tool calls — their input contains the actual content
                for tc in tool_calls:
                    if tc.get("name") == "create_document":
                        # Check top-level content first
                        doc_content = tc.get("input", {}).get("content", "")
                        # If not there, check inside documents array
                        if not doc_content:
                            docs_input = tc.get("input", {}).get("documents", [])
                            if isinstance(docs_input, dict):
                                docs = [docs_input]
                            elif isinstance(docs_input, list):
                                docs = docs_input
                            else:
                                docs = []
                            for doc in docs:
                                if isinstance(doc, dict) and doc.get("content"):
                                    doc_content = doc["content"]
                                    break
                        if doc_content:
                            raw_content = doc_content
                            break

            # If still sentinel after extraction attempt, clear it
            if raw_content == "[Maximum tool iterations reached]":
                raw_content = ""

            pdf_fallback_used = False
            final_state = _dual_output_state(respostas_tool) if dual_output_expected else {"complete": True}

            if dual_output_expected and not final_state["complete"]:
                tokens_entrada = _sum_usage(respostas_tool, "input_tokens") or _sum_usage(respostas_tool, "tokens")
                tokens_saida = _sum_usage(respostas_tool, "output_tokens")
                tokens_total = tokens_entrada + tokens_saida
                detalhes = []
                if final_state.get("errored_tool_details"):
                    detalhes.append("tools com erro: " + " | ".join(final_state["errored_tool_details"]))
                elif final_state.get("errored_tools"):
                    detalhes.append("tools com erro: " + ", ".join(final_state["errored_tools"]))
                if final_state.get("pdf_calls_without_file"):
                    detalhes.append("execute_python_code rodou sem arquivo gerado")
                response_debug = _safe_response_debug(respostas_tool)
                if response_debug:
                    debug_preview = json.dumps(response_debug, ensure_ascii=False)[:700]
                    detalhes.append("diagnostico_modelo=" + debug_preview)

                erro_msg = (
                    "Saída obrigatória incompleta: "
                    + ", ".join(final_state["missing"])
                    + ". Nenhum PDF/JSON será inventado por fallback automático; "
                    + "o modelo solicitado deve produzir os artefatos exigidos ou a etapa falha."
                )
                if detalhes:
                    erro_msg += " Detalhes: " + "; ".join(detalhes) + "."
                for doc_id in context.created_document_ids:
                    self.storage.atualizar_documento_processamento(
                        doc_id,
                        ia_provider=model.tipo.value,
                        ia_modelo=model.modelo,
                        prompt_usado=prompt_id,
                        tokens_usados=tokens_total,
                        tempo_processamento_ms=tempo_ms,
                        status=StatusProcessamento.ERRO,
                        metadata_patch={
                            "erro_pipeline": erro_msg,
                            "tokens_entrada": tokens_entrada,
                            "tokens_saida": tokens_saida,
                            "tokens_total": tokens_total,
                            "cost_run_id": context.cost_run_id,
                            "custo_origem": "tool_use_error",
                        },
                    )
                if not context.created_document_ids and tokens_total > 0:
                    record_token_usage(
                        cost_run_id=context.cost_run_id,
                        atividade_id=atividade_id,
                        aluno_id=aluno_id,
                        etapa=expected_document_type.value if expected_document_type else "tools",
                        provider=model.tipo.value,
                        modelo=model.modelo,
                        tokens_entrada=tokens_entrada,
                        tokens_saida=tokens_saida,
                        status="erro",
                        erro=erro_msg,
                        tentativas=tentativas,
                        tempo_ms=tempo_ms,
                        prompt_id=prompt_id,
                        source="executar_com_tools",
                        metadata={
                            "erro_tipo": "dual_output_incomplete",
                            "response_debug": response_debug,
                        },
                    )
                return ResultadoExecucao(
                    sucesso=False,
                    etapa="tools",
                    resposta_raw=raw_content,
                    provider=model.tipo.value,
                    modelo=model.modelo,
                    tokens_entrada=tokens_entrada,
                    tokens_saida=tokens_saida,
                    tempo_ms=tempo_ms,
                    alertas=alertas,
                    tentativas=tentativas,
                    erro=erro_msg,
                )

            tokens_entrada = _sum_usage(respostas_tool, "input_tokens") or _sum_usage(respostas_tool, "tokens")
            tokens_saida = _sum_usage(respostas_tool, "output_tokens")
            tokens_total = tokens_entrada + tokens_saida

            json_repair_error_msg: Optional[str] = None
            json_validation_errors = _validate_json_artifacts(final_state)
            if (
                json_validation_errors
                and dual_output_expected
                and "create_document" in tools_to_use
            ):
                repair_error_msg = (
                    "Saida JSON invalida antes do retry: "
                    + "; ".join(json_validation_errors)
                )
                json_repair_error_msg = repair_error_msg
                _mark_invalid_json_errors(final_state, repair_error_msg)
                resposta = await client.chat_with_tools(
                    mensagem=_retry_json_validation_message(final_state, json_validation_errors),
                    tools=_tools_by_names(["create_document"]),
                    tool_registry=registry,
                    system_prompt=system_prompt,
                    context=context,
                    tool_choice=(
                        _forced_openai_tool("create_document")
                        if is_openai_provider
                        else None
                    ),
                )
                respostas_tool.append(resposta)
                tentativas += 1
                final_state = _dual_output_state(respostas_tool)
                tokens_entrada = _sum_usage(respostas_tool, "input_tokens") or _sum_usage(respostas_tool, "tokens")
                tokens_saida = _sum_usage(respostas_tool, "output_tokens")
                tokens_total = tokens_entrada + tokens_saida
                alertas.append({
                    "tipo": "aviso",
                    "mensagem": repair_error_msg + ". JSON regenerado por retry explicito.",
                })
                json_validation_errors = _validate_json_artifacts(final_state)

            pdf_json_errors = self._validar_consistencia_pdf_json_tool_outputs(
                final_state.get("docs_by_tool", {}),
                expected_document_type,
            )
            pdf_consistency_repair_attempts = 0
            max_pdf_consistency_repairs = 2
            while (
                pdf_json_errors
                and not json_validation_errors
                and dual_output_expected
                and "execute_python_code" in tools_to_use
                and pdf_consistency_repair_attempts < max_pdf_consistency_repairs
            ):
                repair_error_msg = (
                    "Saida PDF/JSON inconsistente antes do retry "
                    f"{pdf_consistency_repair_attempts + 1}/{max_pdf_consistency_repairs}: "
                    + "; ".join(pdf_json_errors)
                )
                _mark_latest_pdf_error(final_state, repair_error_msg)
                resposta = await client.chat_with_tools(
                    mensagem=_retry_pdf_consistency_message(final_state, pdf_json_errors),
                    tools=_tools_by_names(["execute_python_code"]),
                    tool_registry=registry,
                    system_prompt=system_prompt,
                    context=context,
                    tool_choice=(
                        _forced_openai_tool("execute_python_code")
                        if is_openai_provider
                        else None
                    ),
                )
                respostas_tool.append(resposta)
                tentativas += 1
                pdf_consistency_repair_attempts += 1
                final_state = _dual_output_state(respostas_tool)
                tokens_entrada = _sum_usage(respostas_tool, "input_tokens") or _sum_usage(respostas_tool, "tokens")
                tokens_saida = _sum_usage(respostas_tool, "output_tokens")
                tokens_total = tokens_entrada + tokens_saida
                alertas.append({
                    "tipo": "aviso",
                    "mensagem": (
                        repair_error_msg
                        + ". PDF regenerado por retry explicito no mesmo modelo."
                    ),
                })

                json_validation_errors = _validate_json_artifacts(final_state)
                pdf_json_errors = self._validar_consistencia_pdf_json_tool_outputs(
                    final_state.get("docs_by_tool", {}),
                    expected_document_type,
                )

            post_repair_missing_errors: List[str] = []
            if dual_output_expected and not final_state["complete"]:
                msg = (
                    "Saída obrigatória incompleta após retry de validação: "
                    + ", ".join(final_state["missing"])
                )
                if json_repair_error_msg:
                    msg += f". Erro original: {json_repair_error_msg}"
                post_repair_missing_errors.append(msg)

            validation_errors = post_repair_missing_errors + json_validation_errors + pdf_json_errors
            if validation_errors:
                erro_msg = (
                    "Saída obrigatória inválida: "
                    + "; ".join(validation_errors)
                    + ". Nenhum artefato será aceito como sucesso com placeholder "
                    + "ou schema mínimo ausente."
                )
                for doc_id in context.created_document_ids:
                    self.storage.atualizar_documento_processamento(
                        doc_id,
                        ia_provider=model.tipo.value,
                        ia_modelo=model.modelo,
                        prompt_usado=prompt_id,
                        tokens_usados=tokens_total,
                        tempo_processamento_ms=tempo_ms,
                        status=StatusProcessamento.ERRO,
                        metadata_patch={
                            "erro_pipeline": erro_msg,
                            "tokens_entrada": tokens_entrada,
                            "tokens_saida": tokens_saida,
                            "tokens_total": tokens_total,
                            "cost_run_id": context.cost_run_id,
                            "custo_origem": "tool_use_error",
                        },
                    )
                alertas.append({
                    "tipo": "aviso",
                    "mensagem": erro_msg,
                })
                return ResultadoExecucao(
                    sucesso=False,
                    etapa="tools",
                    resposta_raw=raw_content,
                    provider=model.tipo.value,
                    modelo=model.modelo,
                    tokens_entrada=tokens_entrada,
                    tokens_saida=tokens_saida,
                    tempo_ms=tempo_ms,
                    alertas=alertas,
                    tentativas=tentativas,
                    erro=erro_msg,
                )

            stale_artifact_warnings = _mark_stale_dual_output_artifacts(
                final_state,
                tokens_entrada,
                tokens_saida,
                tokens_total,
                tempo_ms,
            )
            if stale_artifact_warnings:
                alertas.append({
                    "tipo": "aviso",
                    "mensagem": "; ".join(stale_artifact_warnings),
                })

            for doc_id in context.created_document_ids:
                self.storage.atualizar_documento_processamento(
                    doc_id,
                    ia_provider=model.tipo.value,
                    ia_modelo=model.modelo,
                    prompt_usado=prompt_id,
                    tokens_usados=tokens_total,
                    tempo_processamento_ms=tempo_ms,
                    metadata_patch={
                        "tokens_entrada": tokens_entrada,
                        "tokens_saida": tokens_saida,
                        "tokens_total": tokens_total,
                        "cost_run_id": context.cost_run_id,
                        "custo_origem": "tool_use",
                    },
                )

            resposta_parsed_final, documento_id_principal = _resposta_parsed_e_documento_principal(final_state)

            return ResultadoExecucao(
                sucesso=True,
                etapa=_etapa_resultado_tool_use(),
                resposta_raw=raw_content,
                resposta_parsed=resposta_parsed_final,
                provider=model.tipo.value,
                modelo=model.modelo,
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
                tempo_ms=tempo_ms,
                documento_id=documento_id_principal,
                alertas=alertas,
                tentativas=tentativas,
                pdf_fallback_used=pdf_fallback_used,
            )
            
        except ProviderAPIError as e:
            created_context = locals().get("context")
            responses_so_far = locals().get("respostas_tool", []) or []
            sum_usage = locals().get("_sum_usage")
            if callable(sum_usage):
                tokens_entrada = sum_usage(responses_so_far, "input_tokens") or sum_usage(responses_so_far, "tokens")
                tokens_saida = sum_usage(responses_so_far, "output_tokens")
            else:
                tokens_entrada = 0
                tokens_saida = 0
            tokens_total = int(tokens_entrada or 0) + int(tokens_saida or 0)
            if tokens_total <= 0:
                tokens_entrada = int(getattr(e, "input_tokens", 0) or 0)
                tokens_saida = int(getattr(e, "output_tokens", 0) or 0)
                tokens_total = int(getattr(e, "total_tokens", 0) or 0) or tokens_entrada + tokens_saida
            tempo_ms = (time.time() - inicio) * 1000
            model_info = locals().get("model")
            model_provider = getattr(getattr(model_info, "tipo", None), "value", getattr(model_info, "tipo", ""))
            model_name = getattr(model_info, "modelo", "")
            cost_run_id = getattr(created_context, "cost_run_id", None)
            metadata_patch = {
                "erro_pipeline": str(e),
                "cost_run_id": cost_run_id,
            }
            if tokens_total > 0:
                metadata_patch.update(
                    {
                        "tokens_entrada": tokens_entrada,
                        "tokens_saida": tokens_saida,
                        "tokens_total": tokens_total,
                        "custo_origem": "provider_error_after_partial_tool_use",
                    }
                )
            for doc_id in getattr(created_context, "created_document_ids", []) or []:
                self.storage.atualizar_documento_processamento(
                    doc_id,
                    ia_provider=model_provider or getattr(e, "provider", ""),
                    ia_modelo=model_name,
                    prompt_usado=locals().get("prompt_id"),
                    tokens_usados=tokens_total,
                    tempo_processamento_ms=tempo_ms,
                    status=StatusProcessamento.ERRO,
                    metadata_patch=metadata_patch,
                )
            if not getattr(created_context, "created_document_ids", []) and tokens_total > 0:
                record_token_usage(
                    cost_run_id=cost_run_id or f"provider_error_{uuid.uuid4().hex[:12]}",
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    etapa=expected_document_type.value if expected_document_type else "tools",
                    provider=model_provider or getattr(e, "provider", ""),
                    modelo=model_name,
                    tokens_entrada=tokens_entrada,
                    tokens_saida=tokens_saida,
                    status="erro",
                    erro=str(e),
                    erro_codigo=e.status_code,
                    retryable=e.retryable,
                    tempo_ms=tempo_ms,
                    prompt_id=locals().get("prompt_id"),
                    source="executar_com_tools_provider_error",
                    metadata={"erro_tipo": "provider_api_error"},
                )
            return ResultadoExecucao(
                sucesso=False,
                etapa="tools",
                erro=str(e),
                erro_codigo=e.status_code,
                retryable=e.retryable,
                provider=getattr(e, "provider", ""),
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
                tempo_ms=tempo_ms,
            )
        except Exception as e:
            return self._erro("tools", str(e))
    
    async def gerar_relatorios_turma(
        self,
        atividade_id: str,
        turma_id: str,
        provider_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera relatórios para todos os alunos de uma turma.
        
        O modelo pode usar create_document para criar múltiplos
        relatórios individuais em uma única chamada.
        """
        # Buscar alunos da turma
        alunos = self.storage.listar_alunos(turma_id)
        
        if not alunos:
            return {"sucesso": False, "erro": "Nenhum aluno encontrado na turma"}
        
        # Buscar dados de correção de cada aluno
        dados_alunos = []
        for aluno in alunos:
            docs = self.storage.listar_documentos(atividade_id, aluno.id)
            correcao = next((d for d in docs if d.tipo == TipoDocumento.CORRECAO), None)
            
            if correcao:
                try:
                    with open(correcao.caminho_arquivo, 'r', encoding='utf-8') as f:
                        dados = json.load(f)
                        dados_alunos.append({
                            "aluno_id": aluno.id,
                            "nome": aluno.nome,
                            "correcao": dados
                        })
                except:
                    pass
        
        if not dados_alunos:
            return {"sucesso": False, "erro": "Nenhuma correção encontrada para os alunos"}
        
        # Montar prompt para geração em lote
        prompt = f"""Gere relatórios individuais para cada aluno da turma.

DADOS DAS CORREÇÕES:
{json.dumps(dados_alunos, ensure_ascii=False, indent=2)}

Para cada aluno, use a ferramenta create_document para criar um relatório individual.
O relatório deve incluir:
- Nome do aluno
- Nota obtida e percentual
- Pontos fortes identificados
- Áreas de melhoria
- Feedback construtivo personalizado

Crie UM documento separado para cada aluno, nomeando como "relatorio_[nome_aluno].md"
"""
        
        resultado = await self.executar_com_tools(
            mensagem=prompt,
            atividade_id=atividade_id,
            turma_id=turma_id,
            provider_id=provider_id,
            tools_to_use=["create_document"]
        )
        
        return {
            "sucesso": resultado.sucesso,
            "etapa": "gerar_relatorios_turma",
            "alunos_processados": len(dados_alunos),
            "resultado": resultado.to_dict()
        }
    
    # ============================================================
    # RELATÓRIO DE DESEMPENHO — métodos de síntese agregada
    # ============================================================

    async def gerar_relatorio_desempenho_tarefa(
        self,
        atividade_id: str,
        provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Síntese narrativa agregada para uma atividade.

        Busca todos os RELATORIO_FINAL da atividade e gera um relatório
        coletivo usando o prompt RELATORIO_DESEMPENHO_TAREFA.
        Requer pelo menos 2 alunos com relatórios — falha caso contrário.
        """
        narrativos = self.storage.listar_documentos(
            atividade_id, tipo=TipoDocumento.RELATORIO_FINAL
        )
        if len(narrativos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"São necessários pelo menos 2 alunos com RELATORIO_FINAL para gerar o "
                    f"relatório de desempenho da tarefa. Encontrados: {len(narrativos)}."
                ),
            }

        # Read narrative file contents (resolve via Supabase on Render)
        conteudos = []
        avisos = []
        for doc in narrativos:
            try:
                resolved = self.storage.resolver_caminho_documento(doc)
                pdf_doc = fitz.open(str(resolved))
                texto = "".join(page.get_text() for page in pdf_doc)
                pdf_doc.close()
                if texto.strip():
                    conteudos.append({
                        "aluno_id": doc.aluno_id,
                        "conteudo": texto.strip(),
                    })
                else:
                    avisos.append({
                        "aluno_id": doc.aluno_id,
                        "motivo": "PDF sem texto extraível (página em branco ou imagem)",
                    })
            except Exception as e:
                avisos.append({
                    "aluno_id": doc.aluno_id,
                    "motivo": f"Arquivo narrativo ilegível: {e}",
                })

        if len(conteudos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"Apenas {len(conteudos)} narrativa(s) legível(is) de {len(narrativos)} "
                    f"encontrada(s). São necessárias pelo menos 2."
                ),
            }

        # Fetch context
        atividade = self.storage.get_atividade(atividade_id)
        turma = self.storage.get_turma(atividade.turma_id) if atividade else None
        materia = self.storage.get_materia(turma.materia_id) if turma else None

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA,
            materia.id if materia else None,
        )
        if not prompt:
            return {"sucesso": False, "erro": "Prompt RELATORIO_DESEMPENHO_TAREFA não encontrado"}

        # Build variables
        relatorios_texto = "\n\n---\n\n".join([
            f"### Aluno: {c['aluno_id']}\n\n{c['conteudo']}" for c in conteudos
        ])
        variaveis = {
            "relatorios_narrativos": relatorios_texto,
            "atividade": atividade.nome if atividade else atividade_id,
            "materia": materia.nome if materia else "N/A",
            "total_alunos": str(len(narrativos)),
            "alunos_incluidos": str(len(conteudos)),
            "alunos_excluidos": str(len(avisos)),
        }

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema = prompt.render_sistema(**variaveis) or None

        # Call LLM — F-T4: tool-use dual output (JSON + PDF)
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA, "")
        full_system = (prompt_sistema or "") + tool_instructions
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_id,
            provider_id=provider_id,
            system_prompt=full_system or None,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TAREFA,
            prompt_id=prompt.id,
        )

        # Save result
        if resultado.sucesso:
            await self._salvar_resultado(
                etapa=EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA,
                atividade_id=atividade_id,
                aluno_id=None,
                resposta_raw=resultado.resposta_raw,
                resposta_parsed=None,
                provider=resultado.provider,
                modelo=resultado.modelo,
                prompt_id=prompt.id,
                tokens=resultado.tokens_entrada + (resultado.tokens_saida or 0),
                tempo_ms=resultado.tempo_ms,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_tarefa",
            "alunos_incluidos": len(conteudos),
            "alunos_excluidos": len(avisos),
            "avisos": avisos,
            "alertas": resultado.alertas,
            "status": "PARCIAL" if avisos else "COMPLETO",
            "erro": resultado.erro if not resultado.sucesso else None,
        }

    async def gerar_relatorio_desempenho_turma(
        self,
        turma_id: str,
        provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Narrativa holística de uma turma ao longo de todas as atividades.

        Busca todos os alunos da turma e seus RELATORIO_FINAL em todas as
        atividades. Requer pelo menos 2 alunos com resultados.
        """
        alunos = self.storage.listar_alunos(turma_id)
        if len(alunos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"São necessários pelo menos 2 alunos com resultados para gerar o "
                    f"relatório de desempenho da turma. Encontrados: {len(alunos)}."
                ),
            }

        # Fetch context
        turma = self.storage.get_turma(turma_id)
        materia = self.storage.get_materia(turma.materia_id) if turma else None

        # Fetch atividades for this turma
        atividades = self.storage.listar_atividades(turma_id)

        # Gather narratives across all atividades for each student
        conteudos = []
        avisos = []
        atividades_cobertas = set()
        alunos_por_atividade = {}  # atividade_nome → set of aluno_ids with narratives
        for atividade in atividades:
            docs = self.storage.listar_documentos(
                atividade.id, tipo=TipoDocumento.RELATORIO_FINAL,
            )
            alunos_com_narrativa = set()
            for doc in docs:
                try:
                    resolved = self.storage.resolver_caminho_documento(doc)
                    pdf_doc = fitz.open(str(resolved))
                    texto = "".join(page.get_text() for page in pdf_doc)
                    pdf_doc.close()
                    if texto.strip():
                        conteudos.append({
                            "aluno_id": doc.aluno_id,
                            "atividade": atividade.nome,
                            "conteudo": texto.strip(),
                        })
                        atividades_cobertas.add(atividade.nome)
                        alunos_com_narrativa.add(doc.aluno_id)
                    else:
                        avisos.append({
                            "aluno_id": doc.aluno_id,
                            "motivo": "PDF sem texto extraível (página em branco ou imagem)",
                        })
                except Exception as e:
                    avisos.append({
                        "aluno_id": doc.aluno_id,
                        "motivo": f"Arquivo narrativo ilegível: {e}",
                    })
            alunos_por_atividade[atividade.nome] = alunos_com_narrativa

        # Detect atividades with coverage gaps (not all enrolled students have narratives)
        all_aluno_ids = {a.id for a in alunos}
        atividades_com_lacunas = []
        for ativ_nome, alunos_ativ in alunos_por_atividade.items():
            faltantes = all_aluno_ids - alunos_ativ
            if faltantes:
                atividades_com_lacunas.append(ativ_nome)

        if len(conteudos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"Apenas {len(conteudos)} narrativa(s) encontrada(s) para a turma. "
                    f"São necessárias pelo menos 2."
                ),
            }

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA,
            materia.id if materia else None,
        )
        if not prompt:
            return {"sucesso": False, "erro": "Prompt RELATORIO_DESEMPENHO_TURMA não encontrado"}

        # Build variables
        relatorios_texto = "\n\n---\n\n".join([
            f"### Aluno: {c['aluno_id']} | Atividade: {c['atividade']}\n\n{c['conteudo']}"
            for c in conteudos
        ])
        variaveis = {
            "relatorios_narrativos": relatorios_texto,
            "turma": turma.nome if turma else turma_id,
            "materia": materia.nome if materia else "N/A",
            "total_alunos": str(len(alunos)),
            "atividades_cobertas": ", ".join(sorted(atividades_cobertas)) or "Nenhuma",
        }

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema = prompt.render_sistema(**variaveis) or None

        # Call LLM — use first atividade_id as reference (aggregate report)
        # F-T5: tool-use dual output (JSON + PDF)
        atividade_ref = atividades[0].id if atividades else turma_id
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA, "")
        full_system = (prompt_sistema or "") + tool_instructions
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_ref,
            turma_id=turma_id,
            provider_id=provider_id,
            system_prompt=full_system or None,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_TURMA,
            prompt_id=prompt.id,
        )

        # Save result
        if resultado.sucesso:
            await self._salvar_resultado(
                etapa=EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA,
                atividade_id=atividade_ref,
                aluno_id=None,
                resposta_raw=resultado.resposta_raw,
                resposta_parsed=None,
                provider=resultado.provider,
                modelo=resultado.modelo,
                prompt_id=prompt.id,
                tokens=resultado.tokens_entrada + (resultado.tokens_saida or 0),
                tempo_ms=resultado.tempo_ms,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_turma",
            "total_alunos": len(alunos),
            "narrativas_encontradas": len(conteudos),
            "atividades_cobertas": len(atividades_cobertas),
            "avisos": avisos,
            "alertas": resultado.alertas,
            "atividades_com_lacunas": atividades_com_lacunas,
            "status": "PARCIAL" if avisos or atividades_com_lacunas else "COMPLETO",
            "erro": resultado.erro if not resultado.sucesso else None,
        }

    async def gerar_relatorio_desempenho_materia(
        self,
        materia_id: str,
        provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Narrativa cross-turma para uma matéria.

        Busca todas as turmas da matéria. Requer pelo menos 2 turmas com
        resultados para uma comparação significativa.
        """
        turmas = self.storage.listar_turmas(materia_id)
        if len(turmas) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"São necessárias pelo menos 2 turmas com resultados para gerar o "
                    f"relatório de desempenho da matéria. Encontradas: {len(turmas)}."
                ),
            }

        # Fetch context
        materia = self.storage.get_materia(materia_id)

        # Gather narratives across all turmas
        conteudos = []
        avisos = []
        cobertura = {}  # turma_nome → {"narrativas": count}
        atividade_ref = None
        for turma in turmas:
            alunos = self.storage.listar_alunos(turma.id)
            atividades = self.storage.listar_atividades(turma.id)
            narrativas_turma = 0
            for atividade in atividades:
                if atividade_ref is None:
                    atividade_ref = atividade.id
                docs = self.storage.listar_documentos(
                    atividade.id, tipo=TipoDocumento.RELATORIO_FINAL,
                )
                for doc in docs:
                    try:
                        resolved = self.storage.resolver_caminho_documento(doc)
                        pdf_doc = fitz.open(str(resolved))
                        texto = "".join(page.get_text() for page in pdf_doc)
                        pdf_doc.close()
                        if texto.strip():
                            conteudos.append({
                                "turma": turma.nome,
                                "aluno_id": doc.aluno_id,
                                "atividade": atividade.nome,
                                "conteudo": texto.strip(),
                            })
                            narrativas_turma += 1
                        else:
                            avisos.append({
                                "aluno_id": doc.aluno_id,
                                "motivo": "PDF sem texto extraível (página em branco ou imagem)",
                            })
                    except Exception as e:
                        avisos.append({
                            "aluno_id": doc.aluno_id,
                            "motivo": f"Arquivo narrativo ilegível: {e}",
                        })
            cobertura[turma.nome] = {"narrativas": narrativas_turma}

        if len(conteudos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"Apenas {len(conteudos)} narrativa(s) encontrada(s) para a matéria. "
                    f"São necessárias pelo menos 2."
                ),
            }

        # Get prompt
        prompt = self.prompt_manager.get_prompt_padrao(
            EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA,
            materia.id if materia else None,
        )
        if not prompt:
            return {"sucesso": False, "erro": "Prompt RELATORIO_DESEMPENHO_MATERIA não encontrado"}

        # Build variables
        relatorios_texto = "\n\n---\n\n".join([
            f"### Turma: {c['turma']} | Aluno: {c['aluno_id']} | Atividade: {c['atividade']}\n\n{c['conteudo']}"
            for c in conteudos
        ])
        turma_nomes = sorted(set(c["turma"] for c in conteudos))
        variaveis = {
            "relatorios_narrativos": relatorios_texto,
            "materia": materia.nome if materia else materia_id,
            "turmas": ", ".join(turma_nomes),
            "total_turmas": str(len(turmas)),
        }

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema = prompt.render_sistema(**variaveis) or None

        # Call LLM — F-T6: tool-use dual output (JSON + PDF)
        tool_instructions = STAGE_TOOL_INSTRUCTIONS.get(EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA, "")
        full_system = (prompt_sistema or "") + tool_instructions
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_ref or materia_id,
            provider_id=provider_id,
            system_prompt=full_system or None,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.RELATORIO_DESEMPENHO_MATERIA,
            prompt_id=prompt.id,
        )

        # Save result
        if resultado.sucesso:
            await self._salvar_resultado(
                etapa=EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA,
                atividade_id=atividade_ref or materia_id,
                aluno_id=None,
                resposta_raw=resultado.resposta_raw,
                resposta_parsed=None,
                provider=resultado.provider,
                modelo=resultado.modelo,
                prompt_id=prompt.id,
                tokens=resultado.tokens_entrada + (resultado.tokens_saida or 0),
                tempo_ms=resultado.tempo_ms,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_materia",
            "total_turmas": len(turmas),
            "narrativas_encontradas": len(conteudos),
            "cobertura": cobertura,
            "avisos": avisos,
            "alertas": resultado.alertas,
            "status": "PARCIAL" if avisos else "COMPLETO",
            "erro": resultado.erro if not resultado.sucesso else None,
        }

    # ============================================================
    # CASCADE PRE-PIPELINE (FC-T1 — F2-T4)
    # ============================================================

    async def _cascade_prereqs(
        self,
        level: str,
        entity_id: str,
        provider_id: Optional[str] = None,
        force_reexec: bool = False,
    ) -> Dict[str, Any]:
        """
        Ensure all upstream prerequisite docs exist before running desempenho.

        For 'tarefa' level:
          - For each aluno in the atividade's turma, if RELATORIO_FINAL is missing
            (or force_reexec=True), run executar_pipeline_completo().

        For 'turma' level:
          - For each atividade in the turma, if RELATORIO_DESEMPENHO_TAREFA is
            missing (or force_reexec), run _cascade_prereqs('tarefa', ...) then
            gerar_relatorio_desempenho_tarefa().

        For 'materia' level:
          - For each turma in the materia, if RELATORIO_DESEMPENHO_TURMA is
            missing (or force_reexec), run _cascade_prereqs('turma', ...) then
            gerar_relatorio_desempenho_turma().

        Returns a summary dict with lists of created/skipped/failed entries.
        """
        created = []
        skipped = []
        failed = []

        if level == "tarefa":
            atividade = self.storage.get_atividade(entity_id)
            if not atividade:
                return {"created": created, "skipped": skipped, "failed": [f"atividade {entity_id} not found"]}

            alunos = self.storage.listar_alunos(atividade.turma_id)
            docs = self.storage.listar_documentos(entity_id)
            alunos_com_relatorio = {
                d.aluno_id for d in docs
                if d.tipo == TipoDocumento.RELATORIO_FINAL
            }

            for aluno in alunos:
                if not force_reexec and aluno.id in alunos_com_relatorio:
                    skipped.append(aluno.id)
                    continue
                resultado = await self.executar_pipeline_completo(
                    entity_id,
                    aluno.id,
                    provider_name=provider_id,
                    force_rerun=force_reexec,
                )
                last = list(resultado.values())[-1] if resultado else None
                last_ok = getattr(last, "sucesso", None) if last else None
                if last_ok is None and isinstance(last, dict):
                    last_ok = last.get("sucesso")
                if last_ok:
                    created.append(aluno.id)
                else:
                    failed.append(aluno.id)

        elif level == "turma":
            atividades = self.storage.listar_atividades(entity_id)

            for atividade in atividades:
                # Query docs per-atividade (not turma_id) and check RELATORIO_FINAL
                docs = self.storage.listar_documentos(atividade.id)
                has_relatorio_final = any(
                    d.tipo == TipoDocumento.RELATORIO_FINAL for d in docs
                )
                if not force_reexec and has_relatorio_final:
                    skipped.append(atividade.id)
                    continue
                await self._cascade_prereqs("tarefa", atividade.id, provider_id, force_reexec)
                resultado = await self.gerar_relatorio_desempenho_tarefa(atividade.id, provider_id)
                if resultado.get("sucesso"):
                    created.append(atividade.id)
                else:
                    failed.append(atividade.id)

        elif level == "materia":
            turmas = self.storage.listar_turmas(entity_id)

            for turma in turmas:
                # Query docs per-atividade within each turma (not materia_id)
                atividades = self.storage.listar_atividades(turma.id)
                has_relatorio_final = False
                for atividade in atividades:
                    docs = self.storage.listar_documentos(atividade.id)
                    if any(d.tipo == TipoDocumento.RELATORIO_FINAL for d in docs):
                        has_relatorio_final = True
                        break
                if not force_reexec and has_relatorio_final:
                    skipped.append(turma.id)
                    continue
                await self._cascade_prereqs("turma", turma.id, provider_id, force_reexec)
                resultado = await self.gerar_relatorio_desempenho_turma(turma.id, provider_id)
                if resultado.get("sucesso"):
                    created.append(turma.id)
                else:
                    failed.append(turma.id)

        return {"created": created, "skipped": skipped, "failed": failed}

    # ============================================================
    # PIPELINE COMPLETO (mantido do original)
    # ============================================================

    async def executar_pipeline_completo(
        self,
        atividade_id: str,
        aluno_id: str,
        model_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        providers_map: Optional[Dict[str, str]] = None,
        prompt_id: Optional[str] = None,
        prompts_map: Optional[Dict[str, str]] = None,
        usar_multimodal: bool = True,
        selected_steps: Optional[List[str]] = None,
        force_rerun: bool = False,
        task_id: Optional[str] = None
    ) -> Dict[str, ResultadoExecucao]:
        """
        Executa o pipeline completo para um aluno.
        Retorna resultados de cada etapa.

        Args:
            selected_steps: Lista de etapas a executar. Se None, executa todas.
            force_rerun: Se True, re-executa mesmo que já existam resultados.
            prompt_id: ID do prompt padrão para todas as etapas.
            prompts_map: Dict com prompt_id por etapa (ex: {"extrair_questoes": "abc123"})
            task_id: Optional task registry ID for progress tracking.
        """
        import logging
        from routes_tasks import update_stage_progress, complete_pipeline_task, task_registry
        logger = logging.getLogger("pipeline")

        resultados = {}
        etapas_puladas = {}  # Registra motivo de cada etapa pulada
        providers_map = providers_map or {}
        prompts_map = prompts_map or {}

        logger.info(f"Pipeline iniciado: atividade={atividade_id}, aluno={aluno_id}, model={model_id or provider_name}")

        # Todas as etapas disponíveis
        ALL_STEPS = [
            "extrair_questoes", "extrair_gabarito", "extrair_respostas",
            "corrigir", "analisar_habilidades", "gerar_relatorio"
        ]

        # Se não especificou etapas, executa todas
        steps_to_run = selected_steps if selected_steps else ALL_STEPS
        logger.info(f"Etapas selecionadas: {steps_to_run}")

        def _resolve_provider(stage: EtapaProcessamento) -> Optional[str]:
            # Prioridade: providers_map > model_id > provider_name
            resolved = providers_map.get(stage.value) or model_id or provider_name
            if not resolved:
                logger.warning(f"Nenhum provider definido para etapa {stage.value}")
            return resolved

        def _resolve_prompt(stage: EtapaProcessamento) -> Optional[str]:
            # Prioridade: prompts_map > prompt_id
            return prompts_map.get(stage.value) or prompt_id

        def _should_run(step_name: str, doc_type: TipoDocumento, docs_list: List) -> tuple:
            """
            Verifica se deve executar uma etapa.
            Retorna (should_run: bool, reason: str)
            """
            if step_name not in steps_to_run:
                return False, f"não selecionada (selecionadas: {steps_to_run})"
            if force_rerun:
                return True, "force_rerun ativado"

            existing_doc = next((d for d in docs_list if d.tipo == doc_type), None)
            if existing_doc:
                return False, f"documento já existe (id={existing_doc.id}, tipo={doc_type.value})"
            return True, "documento não existe, executando"

        async def _executar_com_retry(
            stage: EtapaProcessamento,
            aluno_id_param: Optional[str] = None,
            max_retries: int = 2
        ) -> ResultadoExecucao:
            """
            Executa etapa com retry automático para erros temporários (429, 5xx).
            """
            tentativas = 0
            resultado = None

            while tentativas <= max_retries:
                if stage == EtapaProcessamento.CORRIGIR:
                    resultado = await self.corrigir(
                        atividade_id, aluno_id_param, _resolve_provider(stage)
                    )
                elif stage == EtapaProcessamento.ANALISAR_HABILIDADES:
                    resultado = await self.analisar_habilidades(
                        atividade_id, aluno_id_param, _resolve_provider(stage)
                    )
                elif stage == EtapaProcessamento.GERAR_RELATORIO:
                    resultado = await self.gerar_relatorio(
                        atividade_id, aluno_id_param, _resolve_provider(stage)
                    )
                else:
                    resultado = await self.executar_etapa(
                        stage,
                        atividade_id,
                        aluno_id_param,
                        provider_name=_resolve_provider(stage),
                        prompt_id=_resolve_prompt(stage),
                        usar_multimodal=usar_multimodal,
                        criar_nova_versao=force_rerun
                    )

                if resultado.sucesso:
                    if tentativas > 0:
                        logger.info(f"  -> Sucesso após {tentativas + 1} tentativas")
                    return resultado

                # Verificar se é erro retryable
                if not resultado.retryable or tentativas >= max_retries:
                    return resultado

                # Calcular tempo de espera
                espera = resultado.retry_after or (2 * (2 ** tentativas))  # 2, 4, 8...
                espera = min(espera, 60)  # máximo 60 segundos

                tentativas += 1
                logger.warning(
                    f"  -> Erro retryable (código {resultado.erro_codigo}), "
                    f"tentativa {tentativas}/{max_retries + 1}, "
                    f"aguardando {espera}s..."
                )
                await asyncio.sleep(espera)

            # Atualizar número de tentativas no resultado final
            if resultado:
                resultado.tentativas = tentativas + 1

            return resultado

        # Carregar documentos existentes
        try:
            docs = self.storage.listar_documentos(atividade_id)
            docs_aluno = self.storage.listar_documentos(atividade_id, aluno_id)
            logger.info(f"Documentos encontrados: base={len(docs)}, aluno={len(docs_aluno)}")
            logger.debug(f"Tipos base: {[d.tipo.value for d in docs]}")
            logger.debug(f"Tipos aluno: {[d.tipo.value for d in docs_aluno]}")
        except Exception as e:
            logger.error(f"Erro ao carregar documentos: {e}")
            if task_id:
                complete_pipeline_task(task_id, "failed", error=f"carregar_documentos: {str(e)}")
            # Retorna resultado de erro
            return {
                "_erro_carregamento": ResultadoExecucao(
                    sucesso=False,
                    etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
                    mensagem=f"Erro ao carregar documentos existentes: {str(e)}",
                    erro=str(e)
                )
            }
        
        def _marcar_erro_pipeline(resultado):
            """Add _pipeline_erro to results dict when pipeline halts due to failure."""
            etapa_val = resultado.etapa.value if hasattr(resultado.etapa, 'value') else str(resultado.etapa)
            erro_pipeline = {
                "etapa_falha": etapa_val,
                "erro": resultado.erro,
                "sucesso": False
            }
            if isinstance(resultado.resposta_parsed, dict):
                documentos_faltantes = resultado.resposta_parsed.get("_documentos_faltantes")
                if documentos_faltantes:
                    erro_pipeline["documentos_faltantes"] = documentos_faltantes
            resultados["_pipeline_erro"] = erro_pipeline

        def _mensagem_erro_task(resultado):
            etapa_val = resultado.etapa.value if hasattr(resultado.etapa, 'value') else str(resultado.etapa)
            detalhe = resultado.erro or "Pipeline falhou sem detalhe do provider."
            if resultado.erro_codigo:
                detalhe = f"{detalhe} (codigo {resultado.erro_codigo})"
            return f"{etapa_val}: {detalhe}"

        def _erro_stage_task(resultado):
            etapa_val = resultado.etapa.value if hasattr(resultado.etapa, 'value') else str(resultado.etapa)
            payload = {
                "etapa": etapa_val,
                "mensagem": resultado.erro or "Pipeline falhou sem detalhe do provider.",
            }
            if resultado.erro_codigo:
                payload["codigo"] = resultado.erro_codigo
            if resultado.retryable is not None:
                payload["retryable"] = bool(resultado.retryable)
            if resultado.provider:
                payload["provider"] = resultado.provider
            if resultado.modelo:
                payload["modelo"] = resultado.modelo
            if isinstance(resultado.resposta_parsed, dict):
                documentos_faltantes = resultado.resposta_parsed.get("_documentos_faltantes")
                if documentos_faltantes:
                    payload["documentos_faltantes"] = documentos_faltantes
                erro_pipeline = resultado.resposta_parsed.get("_erro_pipeline")
                if isinstance(erro_pipeline, dict):
                    payload["tipo"] = erro_pipeline.get("tipo")
                    payload["severidade"] = erro_pipeline.get("severidade")
            return payload

        def _finalizar_task_com_erro(resultado):
            if task_id:
                complete_pipeline_task(task_id, "failed", error=_mensagem_erro_task(resultado))

        # 1. Extrair questões
        should_run, reason = _should_run("extrair_questoes", TipoDocumento.EXTRACAO_QUESTOES, docs)
        logger.info(f"[1/6] extrair_questoes: run={should_run}, reason={reason}")
        if should_run:
            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "extrair_questoes", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.EXTRAIR_QUESTOES)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "extrair_questoes",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["extrair_questoes"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}, erro={resultado.erro[:100] if resultado.erro else 'N/A'}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["extrair_questoes"] = reason

        # 2. Extrair gabarito
        should_run, reason = _should_run("extrair_gabarito", TipoDocumento.EXTRACAO_GABARITO, docs)
        logger.info(f"[2/6] extrair_gabarito: run={should_run}, reason={reason}")
        if should_run:
            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "extrair_gabarito", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.EXTRAIR_GABARITO)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "extrair_gabarito",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["extrair_gabarito"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["extrair_gabarito"] = reason

        # 3. Extrair respostas do aluno
        should_run, reason = _should_run("extrair_respostas", TipoDocumento.EXTRACAO_RESPOSTAS, docs_aluno)
        logger.info(f"[3/6] extrair_respostas: run={should_run}, reason={reason}")
        if should_run:
            prova_valida, mensagem_erro, _ = self._validar_prova_respondida_para_extracao(
                atividade_id, aluno_id, docs_aluno
            )
            if not prova_valida:
                logger.warning(f"[3/6] extrair_respostas: BLOQUEADO - {mensagem_erro}")
                resultados["extrair_respostas"] = ResultadoExecucao(
                    sucesso=False,
                    etapa=EtapaProcessamento.EXTRAIR_RESPOSTAS,
                    erro=mensagem_erro,
                )
                _marcar_erro_pipeline(resultados["extrair_respostas"])
                if task_id:
                    update_stage_progress(
                        task_id,
                        aluno_id,
                        "extrair_respostas",
                        "failed",
                        error=_erro_stage_task(resultados["extrair_respostas"]),
                    )
                _finalizar_task_com_erro(resultados["extrair_respostas"])
                return resultados

            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "extrair_respostas", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.EXTRAIR_RESPOSTAS, aluno_id)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "extrair_respostas",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["extrair_respostas"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["extrair_respostas"] = reason

        # 4. Corrigir
        should_run, reason = _should_run("corrigir", TipoDocumento.CORRECAO, docs_aluno)
        logger.info(f"[4/6] corrigir: run={should_run}, reason={reason}")
        if should_run:
            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "corrigir", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.CORRIGIR, aluno_id)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "corrigir",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["corrigir"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["corrigir"] = reason

        # 5. Analisar habilidades
        should_run, reason = _should_run("analisar_habilidades", TipoDocumento.ANALISE_HABILIDADES, docs_aluno)
        logger.info(f"[5/6] analisar_habilidades: run={should_run}, reason={reason}")
        if should_run:
            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "analisar_habilidades", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.ANALISAR_HABILIDADES, aluno_id)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "analisar_habilidades",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["analisar_habilidades"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["analisar_habilidades"] = reason

        # 6. Gerar relatório
        should_run, reason = _should_run("gerar_relatorio", TipoDocumento.RELATORIO_FINAL, docs_aluno)
        logger.info(f"[6/6] gerar_relatorio: run={should_run}, reason={reason}")
        if should_run:
            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "gerar_relatorio", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.GERAR_RELATORIO, aluno_id)
            if task_id:
                update_stage_progress(
                    task_id,
                    aluno_id,
                    "gerar_relatorio",
                    "completed" if resultado.sucesso else "failed",
                    error=None if resultado.sucesso else _erro_stage_task(resultado),
                )
            resultados["gerar_relatorio"] = resultado
            logger.info(f"  -> sucesso={resultado.sucesso}, tentativas={resultado.tentativas}")
            if not resultado.sucesso:
                logger.error(f"  -> FALHA DEFINITIVA: {resultado.erro} (código: {resultado.erro_codigo})")
                _marcar_erro_pipeline(resultado)
                _finalizar_task_com_erro(resultado)
                return resultados
        else:
            etapas_puladas["gerar_relatorio"] = reason

        # Log final summary
        logger.info(f"Pipeline concluído: {len(resultados)} etapas executadas, {len(etapas_puladas)} puladas")
        if etapas_puladas:
            logger.info(f"Etapas puladas: {etapas_puladas}")

        # Se NENHUMA etapa foi executada, adicionar info especial para debugging
        if not resultados and etapas_puladas:
            logger.warning("ATENÇÃO: Nenhuma etapa foi executada! Todas foram puladas.")
            # Adicionar um resultado especial para indicar isso
            resultados["_info_pipeline"] = ResultadoExecucao(
                sucesso=True,
                etapa=EtapaProcessamento.EXTRAIR_QUESTOES,  # placeholder
                erro=f"Nenhuma etapa executada. Motivos: {etapas_puladas}",
                documento_id=None
            )

        if task_id:
            complete_pipeline_task(task_id, "completed")

        return resultados


# ============================================================
# INSTÂNCIAS GLOBAIS
# ============================================================

# Instância principal (compatível com código existente)
executor = PipelineExecutor()

# Alias para compatibilidade com routes_pipeline.py
pipeline_executor = executor
