"""
PROVA AI - Executor de Pipeline v2.5 (Unificado)

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

from models import TipoDocumento, Documento, criar_erro_pipeline, ERRO_DOCUMENTO_FALTANTE, ERRO_QUESTOES_FALTANTES, SeveridadeErro
from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage import StorageManager, storage
from ai_providers import ai_registry, AIResponse

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
            "tentativas": self.tentativas
        }


# Alias para compatibilidade com routes_pipeline.py
ResultadoEtapa = ResultadoExecucao


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
        
        # Salvar resultado se solicitado
        documento_id = None
        if salvar_resultado:
            documento_id = await self._salvar_resultado(
                etapa, atividade_id, aluno_id,
                response.content, resposta_parsed,
                provider.name, provider.model, prompt.id,
                response.tokens_used, tempo_ms,
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

        # Enviar para IA com anexos
        resultado = await cliente.enviar_com_anexos(
            mensagem=prompt_renderizado,
            arquivos=arquivos,
            system_prompt=prompt_sistema_renderizado,
            verificar_anexos=True
        )
        
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
                        tempo_ms, gerar_formatos_extras=False
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
                caminho = Path(doc.caminho_arquivo)
                if not caminho.is_absolute():
                    caminho = self.storage.base_path / caminho
                if caminho.exists():
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
                    _logger.warning(f"Arquivo não encontrado: {caminho}")
            except Exception as e:
                _logger.warning(f"Erro ao carregar {chave}: {e}")
            return False

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
        """Corrige a prova do aluno"""
        return await self.executar_etapa(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id=atividade_id,
            aluno_id=aluno_id,
            provider_name=provider_id,
            usar_multimodal=True
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
                # Em modo multimodal, não incluir conteúdo de PDFs/imagens no prompt
                # Eles serão enviados como anexos
                conteudo = ""
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
                # Usar como resposta_esperada se não houver outra
                if "resposta_esperada" not in variaveis:
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
        if "gabarito_extraido" in variaveis and "resposta_esperada" not in variaveis:
            variaveis["resposta_esperada"] = variaveis["gabarito_extraido"]
        # Fallback: usar gabarito original se não houver extraído
        if "gabarito" in variaveis and "resposta_esperada" not in variaveis:
            variaveis["resposta_esperada"] = variaveis["gabarito"]

        # Critérios podem não existir - usar string vazia
        if "criterios" not in variaveis:
            variaveis["criterios"] = "(Nenhum critério específico fornecido)"

        # Calcular nota_final se houver correções (para gerar_relatorio)
        if "correcoes" in variaveis and "nota_final" not in variaveis:
            try:
                import json as json_module
                correcoes_data = json_module.loads(variaveis["correcoes"]) if isinstance(variaveis["correcoes"], str) else variaveis["correcoes"]
                if isinstance(correcoes_data, dict) and "nota_final" in correcoes_data:
                    variaveis["nota_final"] = str(correcoes_data["nota_final"])
                elif isinstance(correcoes_data, list):
                    total = sum(c.get("nota", 0) for c in correcoes_data if isinstance(c, dict))
                    variaveis["nota_final"] = str(total)
            except:
                variaveis["nota_final"] = "N/A"

        return variaveis
    
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

        # Tentativa 4: Para relatórios, aceitar Markdown como válido
        if ctx.get("stage") == "gerar_relatorio":
            # Se parece ser Markdown (tem # ou - ou *), aceitar como válido
            if any(char in resposta for char in ['#', '-', '*']) and len(resposta.strip()) > 50:
                _logger.info(
                    "Aceitando resposta Markdown para relatório",
                    stage=ctx.get("stage")
                )
                return {
                    "conteudo": resposta.strip(),
                    "formato": "markdown",
                    "aluno_nome": ctx.get("aluno_nome", "Desconhecido"),
                    "atividade_id": ctx.get("atividade_id", "Desconhecido")
                }
        
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
        criar_nova_versao: bool = False  # Cria nova versão ao invés de sobrescrever
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
        
        # Mapeamento de narrativa: etapa → (campo_no_json, TipoDocumento_narrativo)
        narrativa_map = {
            EtapaProcessamento.CORRIGIR: ("narrativa_correcao", TipoDocumento.CORRECAO_NARRATIVA),
            EtapaProcessamento.ANALISAR_HABILIDADES: ("narrativa_habilidades", TipoDocumento.ANALISE_HABILIDADES_NARRATIVA),
            EtapaProcessamento.GERAR_RELATORIO: ("relatorio_narrativo", TipoDocumento.RELATORIO_NARRATIVO),
        }

        # Criar arquivo temporário com resultado
        conteudo = resposta_parsed if resposta_parsed else {"resposta_raw": resposta_raw}

        # Extrair campo narrativo antes de salvar o JSON técnico
        narrativa_info = narrativa_map.get(etapa)
        narrativa_conteudo = None
        if narrativa_info and isinstance(conteudo, dict):
            campo_narrativa, tipo_narrativa = narrativa_info
            # Extrai e remove do dict (não modifica o original — trabalha em cópia)
            conteudo = dict(conteudo)
            narrativa_conteudo = conteudo.pop(campo_narrativa, None)

        # Validar que campo narrativo está presente para stages analíticos
        if narrativa_info and not narrativa_conteudo:
            campo_narrativa = narrativa_info[0]
            raise ValueError(
                f"Campo narrativo '{campo_narrativa}' obrigatório está ausente ou vazio "
                f"para etapa '{etapa.value}'. O stage não pode continuar sem narrativa."
            )

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
                criado_por="sistema",
                versao=versao,
                documento_origem_id=documento_origem_id
            )

            documento_id = documento.id if documento else None

            # Gerar formatos extras (PDF, CSV) se configurado
            if gerar_formatos_extras and documento_id:
                await self._gerar_formatos_extras(
                    documento_id=documento_id,
                    tipo=tipo,
                    conteudo=conteudo,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id
                )

        finally:
            # Limpar temp JSON
            os.unlink(temp_path)

        # Salvar documento Markdown narrativo (se extraído)
        if narrativa_conteudo and narrativa_info:
            _, tipo_narrativa = narrativa_info
            temp_md_path = None
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
                    f.write(narrativa_conteudo)
                    temp_md_path = f.name
                self.storage.salvar_documento(
                    arquivo_origem=temp_md_path,
                    tipo=tipo_narrativa,
                    atividade_id=atividade_id,
                    aluno_id=aluno_id,
                    ia_provider=provider,
                    ia_modelo=modelo,
                    prompt_usado=prompt_id,
                    criado_por="sistema",
                )
            finally:
                if temp_md_path:
                    os.unlink(temp_md_path)

        return documento_id
    
    async def _gerar_formatos_extras(
        self,
        documento_id: str,
        tipo: TipoDocumento,
        conteudo: Dict[str, Any],
        atividade_id: str,
        aluno_id: Optional[str]
    ) -> List[str]:
        """
        Gera documentos em formatos adicionais (PDF, CSV) com base no tipo.
        
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
        tools_to_use: Optional[List[str]] = None
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
            from chat_service import model_manager, api_key_manager, ChatClient, ProviderType
            from tools import ToolRegistry, CREATE_DOCUMENT, EXECUTE_PYTHON_CODE, PIPELINE_TOOLS
            from tool_handlers import TOOL_HANDLERS
            
            # Obter modelo
            if provider_id:
                model = model_manager.get(provider_id)
            else:
                model = model_manager.get_default()
            
            if not model:
                return self._erro("tools", "Nenhum modelo configurado")
            
            # Obter API key
            api_key = None
            if model.api_key_id:
                key_config = api_key_manager.get(model.api_key_id)
                if key_config:
                    api_key = key_config.api_key
            if not api_key:
                key_config = api_key_manager.get_por_empresa(model.tipo)
                if key_config:
                    api_key = key_config.api_key
            
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
                session_id=f"pipeline_{atividade_id}_{aluno_id or 'base'}"
            )
            
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
            
            # Verificar se o modelo suporta tools
            if not model.suporta_function_calling:
                # Fallback: executar sem tools
                client = ChatClient(model, api_key or "")
                resposta = await client.chat(mensagem, system_prompt=system_prompt)
                
                return ResultadoExecucao(
                    sucesso=True,
                    etapa="tools",
                    resposta_raw=resposta.get("content", ""),
                    provider=model.tipo.value,
                    modelo=model.modelo,
                    tokens_entrada=resposta.get("tokens", 0),
                    tempo_ms=(time.time() - inicio) * 1000,
                    alertas=[{"tipo": "aviso", "mensagem": "Modelo não suporta tools - executado sem geração de documentos"}]
                )
            
            # Executar com tools (apenas para Anthropic por enquanto)
            client = ChatClient(model, api_key or "")
            resposta = await client.chat_with_tools(
                mensagem=mensagem,
                tools=tools_definitions,
                tool_registry=registry,
                system_prompt=system_prompt,
                context=context
            )
            
            tempo_ms = (time.time() - inicio) * 1000
            
            # Coletar documentos gerados pelas tools
            documentos_gerados = []
            tool_calls = resposta.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "create_document":
                    docs = tc.get("input", {}).get("documents", [])
                    for doc in docs:
                        documentos_gerados.append(doc.get("filename", "documento"))
            
            return ResultadoExecucao(
                sucesso=True,
                etapa="tools",
                resposta_raw=resposta.get("content", ""),
                provider=model.tipo.value,
                modelo=model.modelo,
                tokens_entrada=resposta.get("tokens", 0),
                tempo_ms=tempo_ms,
                alertas=[{"tipo": "info", "mensagem": f"Documentos gerados: {documentos_gerados}"}] if documentos_gerados else []
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

        Busca todos os RELATORIO_NARRATIVO da atividade e gera um relatório
        coletivo usando o prompt RELATORIO_DESEMPENHO_TAREFA.
        Requer pelo menos 2 alunos com narrativas — falha caso contrário.
        """
        narrativos = self.storage.listar_documentos(
            atividade_id, tipo=TipoDocumento.RELATORIO_NARRATIVO
        )
        if len(narrativos) < 2:
            return {
                "sucesso": False,
                "erro": (
                    f"São necessários pelo menos 2 alunos com RELATORIO_NARRATIVO para gerar o "
                    f"relatório de desempenho da tarefa. Encontrados: {len(narrativos)}."
                ),
            }

        # Read narrative file contents
        conteudos = []
        excluidos = []
        for doc in narrativos:
            try:
                with open(doc.caminho_arquivo, 'r', encoding='utf-8') as f:
                    conteudos.append({
                        "aluno_id": doc.aluno_id,
                        "conteudo": f.read(),
                    })
            except Exception:
                excluidos.append(doc.aluno_id)

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
            "alunos_excluidos": str(len(excluidos)),
        }

        # Render prompt
        prompt_renderizado = prompt.render(**variaveis)
        prompt_sistema = prompt.render_sistema(**variaveis) or None

        # Call LLM
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_id,
            provider_id=provider_id,
            system_prompt=prompt_sistema,
            tools_to_use=[],
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
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_tarefa",
            "alunos_incluidos": len(conteudos),
            "alunos_excluidos": len(excluidos),
            "erro": resultado.erro if not resultado.sucesso else None,
        }

    async def gerar_relatorio_desempenho_turma(
        self,
        turma_id: str,
        provider_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Narrativa holística de uma turma ao longo de todas as atividades.

        Busca todos os alunos da turma e seus RELATORIO_NARRATIVO em todas as
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
        atividades_cobertas = set()
        for atividade in atividades:
            docs = self.storage.listar_documentos(
                atividade.id, tipo=TipoDocumento.RELATORIO_NARRATIVO,
            )
            for doc in docs:
                try:
                    with open(doc.caminho_arquivo, 'r', encoding='utf-8') as f:
                        conteudos.append({
                            "aluno_id": doc.aluno_id,
                            "atividade": atividade.nome,
                            "conteudo": f.read(),
                        })
                        atividades_cobertas.add(atividade.nome)
                except Exception:
                    pass

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
        atividade_ref = atividades[0].id if atividades else turma_id
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_ref,
            turma_id=turma_id,
            provider_id=provider_id,
            system_prompt=prompt_sistema,
            tools_to_use=[],
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
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_turma",
            "total_alunos": len(alunos),
            "narrativas_encontradas": len(conteudos),
            "atividades_cobertas": len(atividades_cobertas),
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
        atividade_ref = None
        for turma in turmas:
            alunos = self.storage.listar_alunos(turma.id)
            atividades = self.storage.listar_atividades(turma.id)
            for atividade in atividades:
                if atividade_ref is None:
                    atividade_ref = atividade.id
                docs = self.storage.listar_documentos(
                    atividade.id, tipo=TipoDocumento.RELATORIO_NARRATIVO,
                )
                for doc in docs:
                    try:
                        with open(doc.caminho_arquivo, 'r', encoding='utf-8') as f:
                            conteudos.append({
                                "turma": turma.nome,
                                "aluno_id": doc.aluno_id,
                                "atividade": atividade.nome,
                                "conteudo": f.read(),
                            })
                    except Exception:
                        pass

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

        # Call LLM
        resultado = await self.executar_com_tools(
            mensagem=prompt_renderizado,
            atividade_id=atividade_ref or materia_id,
            provider_id=provider_id,
            system_prompt=prompt_sistema,
            tools_to_use=[],
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
            )

        return {
            "sucesso": resultado.sucesso,
            "etapa": "relatorio_desempenho_materia",
            "total_turmas": len(turmas),
            "narrativas_encontradas": len(conteudos),
            "erro": resultado.erro if not resultado.sucesso else None,
        }

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
            resultados["_pipeline_erro"] = {
                "etapa_falha": etapa_val,
                "erro": resultado.erro,
                "sucesso": False
            }

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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
                return resultados
        else:
            etapas_puladas["extrair_gabarito"] = reason

        # 3. Extrair respostas do aluno
        should_run, reason = _should_run("extrair_respostas", TipoDocumento.EXTRACAO_RESPOSTAS, docs_aluno)
        logger.info(f"[3/6] extrair_respostas: run={should_run}, reason={reason}")
        if should_run:
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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
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
                if task_id:
                    complete_pipeline_task(task_id, "failed")
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
