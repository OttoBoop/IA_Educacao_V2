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
import fitz  # PyMuPDF — extract text from binary PDFs (RELATORIO_FINAL)

from models import (
    TipoDocumento, Documento, StatusProcessamento, criar_erro_pipeline,
    ERRO_DOCUMENTO_FALTANTE, ERRO_QUESTOES_FALTANTES, SeveridadeErro,
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

STAGE_TOOL_INSTRUCTIONS: Dict[EtapaProcessamento, str] = {
    EtapaProcessamento.CORRIGIR: """
INSTRUÇÕES DE TOOL-USE PARA CORREÇÃO:
=====================================
Você DEVE usar as ferramentas disponíveis para produzir dois outputs:

1. **create_document** — Salve o resultado da correção como JSON com o schema:
   {
     "nota_final": <float>,
     "questoes": [
       {"numero": <int>, "nota": <float>, "nota_maxima": <float>, "acerto": <bool>, "feedback": "<str>"}
     ],
     "total_acertos": <int>,
     "total_erros": <int>,
     "feedback_geral": "<str>",
     "_avisos_documento": [
       {"codigo": "<ILLEGIBLE_DOCUMENT|MISSING_CONTENT|LOW_CONFIDENCE>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE>", "questao": <int>, "explicacao": "<str>"}
     ]
   }

   **Códigos de aviso disponíveis:**
   - ILLEGIBLE_DOCUMENT — Documento inteiro ilegível ou muito borrado para processar
   - ILLEGIBLE_QUESTION — Questão específica ilegível (resposta do aluno não pode ser lida)
   - MISSING_CONTENT — Conteúdo ausente (aluno pode ter pulado a questão intencionalmente)
   - LOW_CONFIDENCE — Baixa confiança na leitura/interpretação do conteúdo

   Use _avisos_documento para problemas no documento inteiro.
   Use _avisos_questao para problemas em questões específicas (inclua o número da questão).
   Se não houver avisos, envie listas vazias [].
   Use extensão .json e nome descritivo (ex: "correcao_aluno.json").

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com nome do aluno, matéria e data
   - Nota final em destaque
   - Tabela de questões com status (acerto/erro) e feedback
   - Resumo geral
   Use extensão .pdf e nome descritivo.
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
       {"codigo": "<ILLEGIBLE_DOCUMENT|MISSING_CONTENT|LOW_CONFIDENCE>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE>", "questao": <int>, "explicacao": "<str>"}
     ]
   }

   **Códigos de aviso disponíveis:**
   - ILLEGIBLE_DOCUMENT — Documento inteiro ilegível ou muito borrado para processar
   - ILLEGIBLE_QUESTION — Questão específica com resposta ilegível (confirme se houve problema de leitura)
   - MISSING_CONTENT — Conteúdo ausente na análise (dados upstream incompletos)
   - LOW_CONFIDENCE — Baixa confiança na análise de habilidades

   Use _avisos_documento para problemas no documento inteiro.
   Use _avisos_questao para problemas em questões específicas (inclua o número da questão).
   Se não houver avisos, envie listas vazias [].
   Use extensão .json e nome descritivo com dados reais do contexto.
   NUNCA use placeholders como "student123", "aluno_teste", "nome_do_aluno",
   "Aluno", "Student" ou valores fictícios. Se o nome real do aluno estiver
   ausente, use o aluno_id real do contexto e registre aviso explícito.

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com identificação do aluno
   - Lista de habilidades com níveis e indicadores visuais
   - Indicadores de proficiência
   - Recomendações pedagógicas priorizadas
   Use extensão .pdf. O código DEVE gravar um arquivo .pdf real no disco e
   preencher output_files com o nome exato desse arquivo. Não basta imprimir,
   retornar base64 ou descrever o PDF.
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
       {"codigo": "<ILLEGIBLE_DOCUMENT|MISSING_CONTENT|LOW_CONFIDENCE>", "explicacao": "<str>"}
     ],
     "_avisos_questao": [
       {"codigo": "<ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE>", "questao": <int>, "explicacao": "<str>"}
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
   Se não houver avisos, envie listas vazias [].
   _fontes_utilizadas: liste quais etapas do pipeline você usou como fonte de dados para gerar este relatório.
   Use extensão .json e nome descritivo.

2. **execute_python_code** — Gere um PDF estilizado com reportlab contendo:
   - Cabeçalho com dados do aluno e atividade
   - Resumo geral narrativo
   - Pontos fortes destacados
   - Áreas de melhoria
   - Recomendações pedagógicas
   Use extensão .pdf.
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

        # Enviar para IA com anexos
        try:
            resultado = await cliente.enviar_com_anexos(
                mensagem=prompt_renderizado,
                arquivos=arquivos_envio,
                system_prompt=prompt_sistema_renderizado,
                verificar_anexos=True
            )
        finally:
            if temp_dir_paginas_pdf is not None:
                temp_dir_paginas_pdf.cleanup()
        
        tempo_ms = (time.time() - inicio) * 1000
        
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
                tentativas=getattr(resultado, 'tentativas', 1),
                anexos_enviados=resultado.anexos_enviados,
                tempo_ms=tempo_ms
            )

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
        if erro_parseado:
            self._registrar_custo_resposta_invalida(
                etapa=etapa,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                erro=erro_parseado,
                tempo_ms=tempo_ms,
                prompt_id=prompt.id,
                source="executar_multimodal",
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
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                anexos_enviados=resultado.anexos_enviados,
                anexos_confirmados=resultado.anexos_confirmados,
                tempo_ms=tempo_ms,
            )
        erro_scan_suspeito = self._erro_respostas_scan_suspeitas(
            resposta_parsed,
            tem_paginas_pdf_renderizadas=bool(paginas_pdf_renderizadas),
        )
        if erro_scan_suspeito:
            self._registrar_custo_resposta_invalida(
                etapa=etapa,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                provider=resultado.provider,
                modelo=resultado.modelo,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                erro=erro_scan_suspeito,
                tempo_ms=tempo_ms,
                prompt_id=prompt.id,
                source="executar_multimodal",
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
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
                anexos_enviados=resultado.anexos_enviados,
                anexos_confirmados=resultado.anexos_confirmados,
                tempo_ms=tempo_ms,
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
                        resultado.tokens_entrada + resultado.tokens_saida,
                        tempo_ms,
                        gerar_formatos_extras=False,
                        tokens_entrada=resultado.tokens_entrada,
                        tokens_saida=resultado.tokens_saida,
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
                    anexos_enviados=resultado.anexos_enviados,
                    anexos_confirmados=resultado.anexos_confirmados,
                    tempo_ms=tempo_ms
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
                resultado.tokens_entrada + resultado.tokens_saida, tempo_ms,
                tokens_entrada=resultado.tokens_entrada,
                tokens_saida=resultado.tokens_saida,
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
            tokens_entrada=resultado.tokens_entrada,
            tokens_saida=resultado.tokens_saida,
            tempo_ms=tempo_ms,
            documento_id=documento_id,
            anexos_enviados=resultado.anexos_enviados,
            anexos_confirmados=resultado.anexos_confirmados,
            alertas=alertas
        )
    
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
        docs_base = self.storage.listar_documentos(atividade_id)

        # Documentos do aluno (se aplicável)
        docs_aluno = self.storage.listar_documentos(atividade_id, aluno_id) if aluno_id else []

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

        # Mapa de quais documentos cada etapa precisa
        if etapa == EtapaProcessamento.EXTRAIR_QUESTOES:
            # Precisa do enunciado original
            for doc in docs_base:
                if doc.tipo == TipoDocumento.ENUNCIADO:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

        elif etapa == EtapaProcessamento.EXTRAIR_GABARITO:
            # Precisa do gabarito original + questões extraídas (JSON)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.GABARITO:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            # Incluir questões extraídas para referência
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

        elif etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            # Precisa da prova respondida + questões extraídas (JSON)
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            # Incluir questões extraídas para referência
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

        elif etapa == EtapaProcessamento.CORRIGIR:
            # Arquivos originais para referência visual
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.GABARITO:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            # JSONs processados (questões, gabarito extraído, respostas)
            for doc in docs_base:
                if doc.tipo in [TipoDocumento.EXTRACAO_QUESTOES, TipoDocumento.EXTRACAO_GABARITO] and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

        elif etapa == EtapaProcessamento.ANALISAR_HABILIDADES:
            # Prova do aluno para referência visual
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            # JSONs processados (questões, respostas, correção)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            for doc in docs_aluno:
                if doc.tipo in [TipoDocumento.EXTRACAO_RESPOSTAS, TipoDocumento.CORRECAO] and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

        elif etapa == EtapaProcessamento.GERAR_RELATORIO:
            # JSONs processados (correção, análise de habilidades)
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)
            for doc in docs_aluno:
                if doc.tipo in [TipoDocumento.CORRECAO, TipoDocumento.ANALISE_HABILIDADES] and doc.extensao.lower() == '.json':
                    caminho = _normalizar_e_verificar(doc)
                    if caminho:
                        arquivos.append(caminho)

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

        docs_base = self.storage.listar_documentos(atividade_id)
        docs_aluno = self.storage.listar_documentos(atividade_id, aluno_id) if aluno_id else []

        # Helper para carregar documento JSON
        def _carregar_json(doc, chave: str) -> bool:
            try:
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

        # EXTRAIR_RESPOSTAS precisa das questoes extraidas no corpo do prompt.
        # Anexar o JSON sozinho nao basta: modelos pequenos podem ignorar ou
        # subutilizar anexos quando a variavel {{questoes_extraidas}} fica vazia.
        if etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS:
            encontrou_questoes = False
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    if _carregar_json(doc, "questoes_extraidas"):
                        encontrou_questoes = True
                        break
            if not encontrou_questoes:
                documentos_faltantes.append("questoes_extraidas (execute 'extrair_questoes' primeiro)")

        # Para correção, incluir questões extraídas, gabarito e respostas
        if etapa in [EtapaProcessamento.CORRIGIR, EtapaProcessamento.ANALISAR_HABILIDADES, EtapaProcessamento.GERAR_RELATORIO]:
            encontrou_questoes = False
            for doc in docs_base:
                if doc.tipo == TipoDocumento.EXTRACAO_QUESTOES and doc.extensao.lower() == '.json':
                    if _carregar_json(doc, "questoes_extraidas"):
                        encontrou_questoes = True
                        break
            if not encontrou_questoes and etapa in [EtapaProcessamento.CORRIGIR, EtapaProcessamento.ANALISAR_HABILIDADES]:
                documentos_faltantes.append("questoes_extraidas (execute 'extrair_questoes' primeiro)")

            # Verificar gabarito extraído para correção
            if etapa == EtapaProcessamento.CORRIGIR:
                encontrou_gabarito = False
                for doc in docs_base:
                    if doc.tipo == TipoDocumento.EXTRACAO_GABARITO and doc.extensao.lower() == '.json':
                        if _carregar_json(doc, "gabarito_extraido"):
                            encontrou_gabarito = True
                            break
                if not encontrou_gabarito:
                    # Tentar carregar gabarito original como fallback
                    for doc in docs_base:
                        if doc.tipo == TipoDocumento.GABARITO:
                            _logger.warning("Gabarito extraído não encontrado, usando gabarito original")
                            encontrou_gabarito = True
                            break
                if not encontrou_gabarito:
                    documentos_faltantes.append("gabarito (faça upload do gabarito ou execute 'extrair_gabarito')")

            encontrou_respostas = False
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS and doc.extensao.lower() == '.json':
                    if _carregar_json(doc, "respostas_aluno"):
                        encontrou_respostas = True
                        break
            if not encontrou_respostas and etapa == EtapaProcessamento.CORRIGIR:
                documentos_faltantes.append("respostas_aluno (execute 'extrair_respostas' primeiro)")

        # Para análise de habilidades e relatório, incluir correção
        if etapa in [EtapaProcessamento.ANALISAR_HABILIDADES, EtapaProcessamento.GERAR_RELATORIO]:
            encontrou_correcoes = False
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.CORRECAO and doc.extensao.lower() == '.json':
                    if _carregar_json(doc, "correcoes"):
                        encontrou_correcoes = True
                        break
            if not encontrou_correcoes:
                documentos_faltantes.append("correcoes")

        # Para relatório, incluir análise de habilidades
        if etapa == EtapaProcessamento.GERAR_RELATORIO:
            encontrou_analise = False
            for doc in docs_aluno:
                if doc.tipo == TipoDocumento.ANALISE_HABILIDADES and doc.extensao.lower() == '.json':
                    if _carregar_json(doc, "analise_habilidades"):
                        encontrou_analise = True
                        break
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

    def _calcular_nota_final_de_correcoes(self, correcoes: Any) -> str:
        """Calcula nota_final para GERAR_RELATORIO sem inventar nota silenciosa."""
        dados = correcoes
        if isinstance(correcoes, str):
            try:
                dados = json.loads(correcoes)
            except json.JSONDecodeError:
                return "N/A"

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

        return "N/A"
    
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
        documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        
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
                variaveis["conteudo_documento"] = conteudo
                variaveis["enunciado"] = conteudo
            
            elif doc.tipo == TipoDocumento.GABARITO:
                variaveis["gabarito"] = conteudo
                variaveis["resposta_esperada"] = conteudo
            
            elif doc.tipo == TipoDocumento.CRITERIOS_CORRECAO:
                variaveis["criterios"] = conteudo
            
            elif doc.tipo == TipoDocumento.PROVA_RESPONDIDA:
                variaveis["prova_aluno"] = conteudo
                variaveis["resposta_aluno"] = conteudo
            
            elif doc.tipo == TipoDocumento.EXTRACAO_QUESTOES:
                variaveis["questoes_extraidas"] = conteudo

            elif doc.tipo == TipoDocumento.EXTRACAO_GABARITO:
                variaveis["gabarito_extraido"] = conteudo
                # Usar como resposta_esperada se não houver outra (or if empty from multimodal)
                if not variaveis.get("resposta_esperada"):
                    variaveis["resposta_esperada"] = conteudo

            elif doc.tipo == TipoDocumento.EXTRACAO_RESPOSTAS:
                variaveis["respostas_aluno"] = conteudo

            elif doc.tipo == TipoDocumento.CORRECAO:
                variaveis["correcoes"] = conteudo

            elif doc.tipo == TipoDocumento.ANALISE_HABILIDADES:
                variaveis["analise_habilidades"] = conteudo
        
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
        # Fallback: usar gabarito original se não houver extraído
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

        # Fallback: garantir que nota_final sempre existe para evitar {{nota_final}} literal no output
        if "nota_final" not in variaveis:
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
            # Validar JSON vazio
            if data == {} or data == []:
                _logger.warning(
                    "JSON vazio retornado pela IA",
                    stage=ctx.get("stage"),
                    provider=ctx.get("provider"),
                    raw_response=truncate_for_log(resposta, 200)
                )
                return {"_error": "empty_json", "_message": "JSON vazio {}", "_raw": resposta[:500]}

            # Validar estrutura com Pydantic se disponível
            if HAS_VALIDATION and ctx.get("stage"):
                try:
                    if _validar_json_pipeline is None:
                        from pipeline_validation import validar_json_pipeline as vjp
                        _validar_json_pipeline = vjp
                        HAS_VALIDATION = True

                    etapa_nome = ctx.get("stage")
                    if isinstance(etapa_nome, EtapaProcessamento):
                        etapa_nome = etapa_nome.value

                    resultado_validacao = _validar_json_pipeline(etapa_nome, data)
                    if isinstance(resultado_validacao, dict) and resultado_validacao.get("_error"):
                        _logger.warning(
                            "JSON parseado mas falhou na validação estrutural",
                            stage=ctx.get("stage"),
                            provider=ctx.get("provider"),
                            validation_error=resultado_validacao.get("_message"),
                            raw_response=truncate_for_log(resposta, 300)
                        )
                        # Retornar dados parseados mesmo com erro de validação, mas incluir aviso
                        data["_validation_warning"] = resultado_validacao.get("_message")
                    else:
                        _logger.debug(
                            "JSON validado com sucesso",
                            stage=ctx.get("stage"),
                            provider=ctx.get("provider")
                        )
                except Exception as ve:
                    _logger.warning(
                        "Erro durante validação JSON",
                        stage=ctx.get("stage"),
                        validation_error=str(ve)
                    )
                    data["_validation_error"] = str(ve)

            return data
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
                    if data == {} or data == []:
                        _logger.warning(
                            "JSON vazio extraído de bloco de código",
                            stage=ctx.get("stage")
                        )
                        return {"_error": "empty_json", "_message": "JSON vazio em bloco ```"}

                    # Validar estrutura com Pydantic se disponível
                    if HAS_VALIDATION and ctx.get("stage"):
                        try:
                            if _validar_json_pipeline is None:
                                from pipeline_validation import validar_json_pipeline as vjp
                                _validar_json_pipeline = vjp
                                HAS_VALIDATION = True

                            etapa_nome = ctx.get("stage")
                            if isinstance(etapa_nome, EtapaProcessamento):
                                etapa_nome = etapa_nome.value

                            resultado_validacao = _validar_json_pipeline(etapa_nome, data)
                            if isinstance(resultado_validacao, dict) and resultado_validacao.get("_error"):
                                _logger.warning(
                                    "JSON extraído de bloco mas falhou na validação estrutural",
                                    stage=ctx.get("stage"),
                                    provider=ctx.get("provider"),
                                    validation_error=resultado_validacao.get("_message")
                                )
                                data["_validation_warning"] = resultado_validacao.get("_message")
                            else:
                                _logger.debug(
                                    "JSON de bloco de código validado com sucesso",
                                    stage=ctx.get("stage"),
                                    provider=ctx.get("provider")
                                )
                        except Exception as ve:
                            _logger.warning(
                                "Erro durante validação JSON de bloco",
                                stage=ctx.get("stage"),
                                validation_error=str(ve)
                            )
                            data["_validation_error"] = str(ve)

                    return data
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

                    # Validar estrutura com Pydantic se disponível
                    if HAS_VALIDATION and ctx.get("stage"):
                        try:
                            if _validar_json_pipeline is None:
                                from pipeline_validation import validar_json_pipeline as vjp
                                _validar_json_pipeline = vjp
                                HAS_VALIDATION = True

                            etapa_nome = ctx.get("stage")
                            if isinstance(etapa_nome, EtapaProcessamento):
                                etapa_nome = etapa_nome.value

                            resultado_validacao = _validar_json_pipeline(etapa_nome, data)
                            if isinstance(resultado_validacao, dict) and resultado_validacao.get("_error"):
                                _logger.warning(
                                    "JSON extraído por regex mas falhou na validação estrutural",
                                    stage=ctx.get("stage"),
                                    provider=ctx.get("provider"),
                                    validation_error=resultado_validacao.get("_message")
                                )
                                data["_validation_warning"] = resultado_validacao.get("_message")
                            else:
                                _logger.debug(
                                    "JSON por regex validado com sucesso",
                                    stage=ctx.get("stage"),
                                    provider=ctx.get("provider")
                                )
                        except Exception as ve:
                            _logger.warning(
                                "Erro durante validação JSON por regex",
                                stage=ctx.get("stage"),
                                validation_error=str(ve)
                            )
                            data["_validation_error"] = str(ve)

                    return data
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

                def _sem_conteudo(item: Any) -> bool:
                    if not isinstance(item, dict):
                        return False
                    resposta_aluno = str(item.get("resposta_aluno") or "").strip()
                    if not resposta_aluno and not item.get("em_branco") and not item.get("ilegivel"):
                        inconsistentes.append(item.get("questao_numero", "?"))
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
                metadata={"erro_tipo": "parsed_response_invalid"},
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
                    tools_definitions.append(tool.to_anthropic_format())
            
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
                        for doc in docs_by_tool["create_document"]
                    )
                    has_pdf = any(
                        (getattr(doc, "extensao", "") or "").lower() == ".pdf"
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
                    "Não responda em texto simples."
                    + contexto_retry
                )

            def _retry_tool_choice_for_state(state: Dict[str, Any]) -> Optional[Any]:
                if not is_openai_provider:
                    return None
                if not state["has_pdf"] and state["has_json"]:
                    return _forced_openai_tool("execute_python_code")
                if not state["has_json"] and state["has_pdf"]:
                    return _forced_openai_tool("create_document")
                return "required"

            def _validate_json_artifacts(state: Dict[str, Any]) -> List[str]:
                """Fail high on known placeholder/schema leaks in persisted JSON."""
                if expected_document_type != TipoDocumento.ANALISE_HABILIDADES:
                    return []

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

                for doc in state.get("docs_by_tool", {}).get("create_document", []):
                    if (getattr(doc, "extensao", "") or "").lower() != ".json":
                        continue

                    doc_label = getattr(doc, "id", None) or getattr(doc, "nome_arquivo", "json")
                    filename = (getattr(doc, "nome_arquivo", "") or "").lower()
                    try:
                        path = self.storage.resolver_caminho_documento(doc)
                    except Exception as exc:
                        errors.append(f"JSON {doc_label} não pôde ser resolvido para validação: {exc}")
                        continue

                    if not path or not Path(path).exists():
                        errors.append(f"JSON {doc_label} não pôde ser lido para validação")
                        continue

                    try:
                        with open(path, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                    except Exception as exc:
                        errors.append(f"JSON {doc_label} inválido: {exc}")
                        continue

                    serialized = json.dumps(data, ensure_ascii=False).lower()
                    for placeholder in placeholders:
                        if placeholder in serialized or placeholder in filename:
                            errors.append(f"JSON {doc_label} contém placeholder proibido: {placeholder}")
                            break

                    habilidades = data.get("habilidades") if isinstance(data, dict) else None
                    if not habilidades:
                        errors.append(f"JSON {doc_label} sem lista/dicionário de habilidades")

                return errors

            initial_tool_choice = (
                "required"
                if dual_output_expected and is_openai_provider
                else None
            )

            # Executar com tools
            client = ChatClient(model, api_key or "")
            resposta = await client.chat_with_tools(
                mensagem=mensagem,
                tools=tools_definitions,
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
                if not state["complete"]:
                    # Partial/missing output — one explicit retry on the same model.
                    retry_msg = _retry_message_for_state(state)
                    retry_tool_choice = _retry_tool_choice_for_state(state)

                    resposta = await client.chat_with_tools(
                        mensagem=retry_msg,
                        tools=tools_definitions,
                        tool_registry=registry,
                        system_prompt=system_prompt,
                        context=context,
                        tool_choice=retry_tool_choice,
                    )
                    respostas_tool.append(resposta)
                    tentativas = 2

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
                if final_state.get("errored_tools"):
                    detalhes.append("tools com erro: " + ", ".join(final_state["errored_tools"]))
                if final_state.get("pdf_calls_without_file"):
                    detalhes.append("execute_python_code rodou sem arquivo gerado")

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
                        metadata={"erro_tipo": "dual_output_incomplete"},
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

            validation_errors = _validate_json_artifacts(final_state)
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

            return ResultadoExecucao(
                sucesso=True,
                etapa="tools",
                resposta_raw=raw_content,
                provider=model.tipo.value,
                modelo=model.modelo,
                tokens_entrada=tokens_entrada,
                tokens_saida=tokens_saida,
                tempo_ms=tempo_ms,
                alertas=alertas,
                tentativas=tentativas,
                pdf_fallback_used=pdf_fallback_used,
            )
            
        except ProviderAPIError as e:
            created_context = locals().get("context")
            for doc_id in getattr(created_context, "created_document_ids", []) or []:
                self.storage.atualizar_documento_processamento(
                    doc_id,
                    status=StatusProcessamento.ERRO,
                    metadata_patch={
                        "erro_pipeline": str(e),
                        "cost_run_id": getattr(created_context, "cost_run_id", None),
                    },
                )
            return ResultadoExecucao(
                sucesso=False,
                etapa="tools",
                erro=str(e),
                erro_codigo=e.status_code,
                retryable=e.retryable,
                provider=getattr(e, "provider", ""),
                tempo_ms=(time.time() - inicio) * 1000,
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
                update_stage_progress(task_id, aluno_id, "extrair_questoes", "completed" if resultado.sucesso else "failed")
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
                update_stage_progress(task_id, aluno_id, "extrair_gabarito", "completed" if resultado.sucesso else "failed")
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
                    update_stage_progress(task_id, aluno_id, "extrair_respostas", "failed")
                _finalizar_task_com_erro(resultados["extrair_respostas"])
                return resultados

            if task_id and task_registry.get(task_id, {}).get("cancel_requested"):
                complete_pipeline_task(task_id, "cancelled")
                return resultados
            if task_id:
                update_stage_progress(task_id, aluno_id, "extrair_respostas", "running")
            resultado = await _executar_com_retry(EtapaProcessamento.EXTRAIR_RESPOSTAS, aluno_id)
            if task_id:
                update_stage_progress(task_id, aluno_id, "extrair_respostas", "completed" if resultado.sucesso else "failed")
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
                update_stage_progress(task_id, aluno_id, "corrigir", "completed" if resultado.sucesso else "failed")
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
                update_stage_progress(task_id, aluno_id, "analisar_habilidades", "completed" if resultado.sucesso else "failed")
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
                update_stage_progress(task_id, aluno_id, "gerar_relatorio", "completed" if resultado.sucesso else "failed")
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
