"""
PROVA AI - Executor de Pipeline v2.0

Executa etapas individuais do pipeline de correção.
Permite escolher IA e prompt para cada execução.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import asyncio
import time

from models import TipoDocumento, Documento
from prompts import PromptManager, PromptTemplate, EtapaProcessamento, prompt_manager
from storage_v2 import StorageManagerV2, storage_v2 as storage
from ai_providers import ai_registry, AIResponse


@dataclass
class ResultadoExecucao:
    """Resultado de uma execução de etapa"""
    sucesso: bool
    etapa: EtapaProcessamento
    
    # Dados da execução
    prompt_usado: str
    prompt_id: str
    provider: str
    modelo: str
    
    # Resultado
    resposta_raw: str = ""
    resposta_parsed: Optional[Dict[str, Any]] = None
    
    # Metadados
    tokens_entrada: int = 0
    tokens_saida: int = 0
    tempo_ms: float = 0
    
    # Documento gerado (se salvou)
    documento_id: Optional[str] = None
    
    # Erro (se falhou)
    erro: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sucesso": self.sucesso,
            "etapa": self.etapa.value,
            "prompt_id": self.prompt_id,
            "provider": self.provider,
            "modelo": self.modelo,
            "resposta_raw": self.resposta_raw,
            "resposta_parsed": self.resposta_parsed,
            "tokens_entrada": self.tokens_entrada,
            "tokens_saida": self.tokens_saida,
            "tempo_ms": self.tempo_ms,
            "documento_id": self.documento_id,
            "erro": self.erro
        }


class PipelineExecutor:
    """Executa etapas do pipeline de correção"""
    
    def __init__(self):
        self.prompt_manager = prompt_manager
        self.storage = storage
    
    async def executar_etapa(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str] = None,
        prompt_id: Optional[str] = None,
        provider_name: Optional[str] = None,
        variaveis_extra: Optional[Dict[str, str]] = None,
        salvar_resultado: bool = True
    ) -> ResultadoExecucao:
        """
        Executa uma etapa do pipeline.
        
        Args:
            etapa: Qual etapa executar
            atividade_id: ID da atividade
            aluno_id: ID do aluno (necessário para etapas de aluno)
            prompt_id: ID do prompt a usar (ou usa o padrão)
            provider_name: Nome do provider de IA (ou usa o padrão)
            variaveis_extra: Variáveis adicionais para o prompt
            salvar_resultado: Se deve salvar o resultado como documento
        """
        inicio = time.time()
        
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
            
            if not prompt:
                return self._erro(etapa, f"Nenhum prompt disponível para etapa {etapa.value}")
            
            # 3. Buscar provider
            provider = ai_registry.get(provider_name) if provider_name else ai_registry.get_default()
            if not provider:
                return self._erro(etapa, "Nenhum provider de IA disponível")
            
            # 4. Preparar variáveis
            variaveis = self._preparar_variaveis(etapa, atividade_id, aluno_id, materia, atividade)
            if variaveis_extra:
                variaveis.update(variaveis_extra)
            
            # 5. Renderizar prompt
            prompt_renderizado = prompt.render(**variaveis)
            prompt_sistema_renderizado = prompt.render_sistema(**variaveis) or None
            
            # 6. Executar IA
            response = await provider.complete(prompt_renderizado, prompt_sistema_renderizado)
            
            # 7. Parsear resposta
            resposta_parsed = self._parsear_resposta(response.content)
            
            tempo_ms = (time.time() - inicio) * 1000
            
            # 8. Salvar resultado se solicitado
            documento_id = None
            if salvar_resultado:
                documento_id = await self._salvar_resultado(
                    etapa, atividade_id, aluno_id,
                    response.content, resposta_parsed,
                    provider.name, provider.model, prompt.id,
                    response.tokens_used, tempo_ms
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
                tokens_entrada=0,  # TODO: calcular
                tokens_saida=response.tokens_used,
                tempo_ms=tempo_ms,
                documento_id=documento_id
            )
            
        except Exception as e:
            return self._erro(etapa, str(e), prompt_id, provider_name)
    
    def _erro(self, etapa: EtapaProcessamento, mensagem: str, 
              prompt_id: str = None, provider: str = None) -> ResultadoExecucao:
        """Cria resultado de erro"""
        return ResultadoExecucao(
            sucesso=False,
            etapa=etapa,
            prompt_usado="",
            prompt_id=prompt_id or "",
            provider=provider or "",
            modelo="",
            erro=mensagem
        )
    
    def _preparar_variaveis(
        self,
        etapa: EtapaProcessamento,
        atividade_id: str,
        aluno_id: Optional[str],
        materia: Any,
        atividade: Any
    ) -> Dict[str, str]:
        """Prepara variáveis para o prompt baseado no contexto"""
        variaveis = {
            "materia": materia.nome if materia else "Não definida",
            "atividade": atividade.nome if atividade else "Não definida",
            "nota_maxima": str(atividade.nota_maxima) if atividade else "10"
        }
        
        # Buscar documentos relevantes
        documentos = self.storage.listar_documentos(atividade_id, aluno_id)
        
        for doc in documentos:
            conteudo = self._ler_documento(doc)
            
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
        
        return variaveis
    
    def _ler_documento(self, documento: Documento) -> str:
        """Lê conteúdo de um documento"""
        try:
            arquivo = Path(documento.caminho_arquivo)
            if not arquivo.exists():
                return f"[Arquivo não encontrado: {documento.nome_arquivo}]"
            
            if documento.extensao.lower() == '.json':
                with open(arquivo, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return json.dumps(data, ensure_ascii=False, indent=2)
            
            elif documento.extensao.lower() in ['.txt', '.md']:
                with open(arquivo, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif documento.extensao.lower() == '.pdf':
                # Tentar extrair texto do PDF
                try:
                    import importlib
                    with open(arquivo, 'rb') as f:
                        pypdf2 = importlib.import_module("PyPDF2")
                        reader = pypdf2.PdfReader(f)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except:
                    return f"[PDF: {documento.nome_arquivo} - Não foi possível extrair texto]"
            
            elif documento.extensao.lower() == '.docx':
                try:
                    import importlib
                    docx = importlib.import_module("docx")
                    doc = docx.Document(arquivo)
                    text = "\n".join([p.text for p in doc.paragraphs])
                    return text
                except:
                    return f"[DOCX: {documento.nome_arquivo} - Não foi possível extrair texto]"
            
            else:
                return f"[Arquivo: {documento.nome_arquivo} - Tipo não suportado para leitura automática]"
                
        except Exception as e:
            return f"[Erro ao ler {documento.nome_arquivo}: {str(e)}]"
    
    def _parsear_resposta(self, resposta: str) -> Optional[Dict[str, Any]]:
        """Tenta extrair JSON da resposta"""
        try:
            # Tentar parsear diretamente
            return json.loads(resposta)
        except:
            pass
        
        # Tentar extrair JSON de bloco de código
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', resposta)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Tentar encontrar {} ou []
        for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
            match = re.search(pattern, resposta)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        
        return None
    
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
        tempo_ms: float
    ) -> Optional[str]:
        """Salva o resultado como documento"""
        
        # Determinar tipo de documento
        tipo_map = {
            EtapaProcessamento.EXTRAIR_QUESTOES: TipoDocumento.EXTRACAO_QUESTOES,
            EtapaProcessamento.EXTRAIR_GABARITO: TipoDocumento.EXTRACAO_GABARITO,
            EtapaProcessamento.EXTRAIR_RESPOSTAS: TipoDocumento.EXTRACAO_RESPOSTAS,
            EtapaProcessamento.CORRIGIR: TipoDocumento.CORRECAO,
            EtapaProcessamento.ANALISAR_HABILIDADES: TipoDocumento.ANALISE_HABILIDADES,
            EtapaProcessamento.GERAR_RELATORIO: TipoDocumento.RELATORIO_FINAL
        }
        
        tipo = tipo_map.get(etapa)
        if not tipo:
            return None
        
        # Criar arquivo temporário com resultado
        import tempfile
        
        conteudo = resposta_parsed if resposta_parsed else {"resposta_raw": resposta_raw}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(conteudo, f, ensure_ascii=False, indent=2)
            temp_path = f.name
        
        try:
            # Salvar documento
            documento = self.storage.salvar_documento(
                arquivo_origem=temp_path,
                tipo=tipo,
                atividade_id=atividade_id,
                aluno_id=aluno_id,
                ia_provider=provider,
                ia_modelo=modelo,
                prompt_usado=prompt_id,
                criado_por="sistema"
            )
            
            # Atualizar metadados
            if documento:
                # TODO: Atualizar tokens e tempo no documento
                pass
            
            return documento.id if documento else None
            
        finally:
            # Limpar temp
            import os
            os.unlink(temp_path)
    
    async def executar_pipeline_completo(
        self,
        atividade_id: str,
        aluno_id: str,
        provider_name: Optional[str] = None
    ) -> Dict[str, ResultadoExecucao]:
        """
        Executa o pipeline completo para um aluno.
        Retorna resultados de cada etapa.
        """
        resultados = {}
        
        # 1. Extrair questões (se não existir)
        docs = self.storage.listar_documentos(atividade_id)
        if not any(d.tipo == TipoDocumento.EXTRACAO_QUESTOES for d in docs):
            resultado = await self.executar_etapa(
                EtapaProcessamento.EXTRAIR_QUESTOES,
                atividade_id,
                provider_name=provider_name
            )
            resultados["extrair_questoes"] = resultado
            if not resultado.sucesso:
                return resultados
        
        # 2. Extrair gabarito (se não existir)
        if not any(d.tipo == TipoDocumento.EXTRACAO_GABARITO for d in docs):
            resultado = await self.executar_etapa(
                EtapaProcessamento.EXTRAIR_GABARITO,
                atividade_id,
                provider_name=provider_name
            )
            resultados["extrair_gabarito"] = resultado
        
        # 3. Extrair respostas do aluno
        docs_aluno = self.storage.listar_documentos(atividade_id, aluno_id)
        if not any(d.tipo == TipoDocumento.EXTRACAO_RESPOSTAS for d in docs_aluno):
            resultado = await self.executar_etapa(
                EtapaProcessamento.EXTRAIR_RESPOSTAS,
                atividade_id,
                aluno_id,
                provider_name=provider_name
            )
            resultados["extrair_respostas"] = resultado
            if not resultado.sucesso:
                return resultados
        
        # 4. Corrigir
        if not any(d.tipo == TipoDocumento.CORRECAO for d in docs_aluno):
            resultado = await self.executar_etapa(
                EtapaProcessamento.CORRIGIR,
                atividade_id,
                aluno_id,
                provider_name=provider_name
            )
            resultados["corrigir"] = resultado
            if not resultado.sucesso:
                return resultados
        
        # 5. Analisar habilidades
        if not any(d.tipo == TipoDocumento.ANALISE_HABILIDADES for d in docs_aluno):
            resultado = await self.executar_etapa(
                EtapaProcessamento.ANALISAR_HABILIDADES,
                atividade_id,
                aluno_id,
                provider_name=provider_name
            )
            resultados["analisar_habilidades"] = resultado
        
        # 6. Gerar relatório
        if not any(d.tipo == TipoDocumento.RELATORIO_FINAL for d in docs_aluno):
            resultado = await self.executar_etapa(
                EtapaProcessamento.GERAR_RELATORIO,
                atividade_id,
                aluno_id,
                provider_name=provider_name
            )
            resultados["gerar_relatorio"] = resultado
        
        return resultados


# Instância global
executor = PipelineExecutor()
