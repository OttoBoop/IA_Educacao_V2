"""
Tests for pipeline error framework (F2-T1, F3-T1, F4-T1, F3-T2, F5-T1, F5-T2, F6-T1, F6-T2, F7-T1).

F2-T1: Error constants, SeveridadeErro enum, criar_erro_pipeline() helper.
F3-T1: Missing document detection saves JSON with _erro_pipeline.
F4-T1: Missing questions detection saves JSON with _erro_pipeline.
F3-T2: Pipeline orchestration marks overall result as ERRO when stage fails.
F5-T1: API propagates _erro_pipeline in response JSON.
F5-T2: Visualizador includes erro_pipeline in VisaoAluno.
F6-T1: UI red error banner in result detail view.
F6-T2: UI red ERRO badge in result rendering.
F7-T1: PDF includes "ERRO DE PROCESSAMENTO" section when data has _erro_pipeline.
"""
import pytest
import json
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, ANY


class TestBlockingParsedResponses:
    """Outputs parseáveis mas sem conteúdo obrigatório devem falhar alto."""

    def test_extrair_respostas_tudo_em_branco_bloqueia_sucesso(self):
        from executor import EtapaProcessamento, PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        erro = executor._erro_resposta_parseada(
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            {
                "aluno": "João Silva",
                "respostas": [
                    {
                        "questao_numero": 1,
                        "resposta_aluno": "",
                        "em_branco": True,
                        "ilegivel": False,
                    },
                    {
                        "questao_numero": 2,
                        "resposta_aluno": "",
                        "em_branco": True,
                        "ilegivel": False,
                    },
                ],
                "questoes_respondidas": 0,
                "questoes_em_branco": 2,
            },
        )

        assert erro is not None
        assert "sem conteudo extraido" in erro

    def test_extrair_respostas_com_algum_conteudo_nao_bloqueia(self):
        from executor import EtapaProcessamento, PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        erro = executor._erro_resposta_parseada(
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            {
                "aluno": "João Silva",
                "respostas": [
                    {
                        "questao_numero": 1,
                        "resposta_aluno": "",
                        "em_branco": True,
                        "ilegivel": False,
                    },
                    {
                        "questao_numero": 2,
                        "resposta_aluno": "x = 2",
                        "em_branco": False,
                        "ilegivel": False,
                    },
                ],
                "questoes_respondidas": 1,
                "questoes_em_branco": 1,
            },
        )

        assert erro is None

    def test_extrair_respostas_vazio_sem_flag_bloqueia_sucesso(self):
        from executor import EtapaProcessamento, PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        erro = executor._erro_resposta_parseada(
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            {
                "aluno": "João Silva",
                "respostas": [
                    {
                        "questao_numero": 1,
                        "resposta_aluno": "",
                        "em_branco": False,
                        "ilegivel": False,
                    },
                    {
                        "questao_numero": 2,
                        "resposta_aluno": "x = 2",
                        "em_branco": False,
                        "ilegivel": False,
                    },
                ],
                "questoes_respondidas": 2,
                "questoes_em_branco": 0,
            },
        )

        assert erro is not None
        assert "JSON inconsistente" in erro


class TestExtrairRespostasContextoQuestoes:
    """EXTRAIR_RESPOSTAS deve receber questoes extraidas no prompt, nao so anexo."""

    @staticmethod
    def _doc(tipo, doc_id, path, extensao=".json", criado_em=None, status="concluido", metadata=None):
        doc = MagicMock()
        doc.tipo = tipo
        doc.id = doc_id
        doc.caminho_arquivo = str(path)
        doc.extensao = extensao
        doc.nome_arquivo = Path(path).name
        doc.criado_em = criado_em or ""
        doc.status = status
        doc.metadata = metadata or {}
        return doc

    def test_extrair_respostas_carrega_questoes_extraidas_no_contexto(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        questoes_path = tmp_path / "extracao_questoes.json"
        questoes_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "enunciado": "Calcule A+B"}]}),
            encoding="utf-8",
        )
        doc_questoes = self._doc(
            TipoDocumento.EXTRACAO_QUESTOES,
            "questoes-1",
            questoes_path,
        )

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _atividade_id, aluno_id=None: [] if aluno_id else [doc_questoes]
        )
        executor.storage.resolver_caminho_documento = MagicMock(return_value=questoes_path)

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
        )

        assert "questoes_extraidas" in contexto
        assert "Calcule A+B" in contexto["questoes_extraidas"]
        assert contexto["_documentos_carregados"] == ["questoes_extraidas"]
        assert "_documentos_faltantes" not in contexto

    def test_extrair_respostas_falha_sem_questoes_extraidas(self):
        from executor import EtapaProcessamento, PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=[])

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
        )

        assert "questoes_extraidas" not in contexto
        assert "questoes_extraidas" in contexto["_documentos_faltantes"][0]

    def test_extrair_respostas_inclui_texto_extraido_da_prova_pdf(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento
        import fitz

        prova_path = tmp_path / "prova_respondida.pdf"
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "Questao 1\nResposta do aluno: x = 2")
        pdf.save(str(prova_path))
        pdf.close()

        prova_doc = self._doc(
            TipoDocumento.PROVA_RESPONDIDA,
            "prova-1",
            prova_path,
            ".pdf",
        )

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=[prova_doc])
        executor.storage.resolver_caminho_documento = MagicMock(return_value=prova_path)
        executor.storage.get_aluno = MagicMock(return_value=MagicMock(nome="Aluno PDF"))

        variaveis = executor._preparar_variaveis_texto(
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            "ativ_test",
            "aluno_test",
            materia=MagicMock(nome="Matematica"),
            atividade=MagicMock(nome="Lista", nota_maxima=10),
            usar_multimodal=True,
        )

        assert "TEXTO EXTRAIDO DO PDF" in variaveis["conteudo_documento"]
        assert "Resposta do aluno: x = 2" in variaveis["conteudo_documento"]
        assert variaveis["prova_aluno"] == variaveis["conteudo_documento"]

    def test_preparar_variaveis_texto_usa_documento_processado_mais_recente(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        antigo_path = tmp_path / "questoes_antigas.json"
        antigo_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "enunciado": "VERSAO ANTIGA"}]}),
            encoding="utf-8",
        )
        novo_path = tmp_path / "questoes_novas.json"
        novo_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "enunciado": "VERSAO NOVA"}]}),
            encoding="utf-8",
        )
        docs = [
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-novas",
                novo_path,
                criado_em="2026-05-16T18:52:16",
            ),
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-antigas",
                antigo_path,
                criado_em="2026-05-16T01:11:01",
            ),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=docs)
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        variaveis = executor._preparar_variaveis_texto(
            EtapaProcessamento.EXTRAIR_GABARITO,
            "ativ_test",
            None,
            materia=MagicMock(nome="Matematica"),
            atividade=MagicMock(nome="Lista", nota_maxima=10),
            usar_multimodal=True,
        )

        assert "VERSAO NOVA" in variaveis["questoes_extraidas"]
        assert "VERSAO ANTIGA" not in variaveis["questoes_extraidas"]

    def test_coletar_arquivos_para_gabarito_anexa_apenas_questoes_mais_recentes(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        gabarito_path = tmp_path / "gabarito.pdf"
        gabarito_path.write_bytes(b"%PDF-1.4\n")
        antigo_path = tmp_path / "questoes_antigas.json"
        antigo_path.write_text("{}", encoding="utf-8")
        novo_path = tmp_path / "questoes_novas.json"
        novo_path.write_text("{}", encoding="utf-8")

        docs = [
            self._doc(TipoDocumento.GABARITO, "gabarito", gabarito_path, ".pdf"),
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-novas",
                novo_path,
                criado_em="2026-05-16T18:52:16",
            ),
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-antigas",
                antigo_path,
                criado_em="2026-05-16T01:11:01",
            ),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=docs)
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        arquivos = executor._coletar_arquivos_para_etapa(
            EtapaProcessamento.EXTRAIR_GABARITO,
            "ativ_test",
            None,
        )

        assert str(gabarito_path) in arquivos
        assert str(novo_path) in arquivos
        assert str(antigo_path) not in arquivos

    def test_contexto_json_nao_recua_para_json_antigo_quando_mais_recente_tem_erro(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        erro_path = tmp_path / "questoes_erro.json"
        erro_path.write_text(json.dumps({"_error": "parse_failed"}), encoding="utf-8")
        antigo_path = tmp_path / "questoes_antigas.json"
        antigo_path.write_text(
            json.dumps({"questoes": [{"numero": 1, "enunciado": "ANTIGA"}]}),
            encoding="utf-8",
        )
        docs = [
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-erro",
                erro_path,
                criado_em="2026-05-16T18:52:16",
            ),
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes-antigas",
                antigo_path,
                criado_em="2026-05-16T01:11:01",
            ),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _atividade_id, aluno_id=None: [] if aluno_id else docs
        )
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
        )

        assert "questoes_extraidas" not in contexto
        assert any("questoes_extraidas" in item for item in contexto["_documentos_faltantes"])

    def test_corrigir_exige_gabarito_extraido_sem_usar_gabarito_original(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        questoes_path = tmp_path / "questoes.json"
        questoes_path.write_text(json.dumps({"questoes": []}), encoding="utf-8")
        gabarito_original_path = tmp_path / "gabarito.pdf"
        gabarito_original_path.write_bytes(b"%PDF-1.4\n")
        respostas_path = tmp_path / "respostas.json"
        respostas_path.write_text(json.dumps({"respostas": []}), encoding="utf-8")

        docs_base = [
            self._doc(TipoDocumento.EXTRACAO_QUESTOES, "questoes", questoes_path),
            self._doc(TipoDocumento.GABARITO, "gabarito-original", gabarito_original_path, ".pdf"),
        ]
        docs_aluno = docs_base + [
            self._doc(TipoDocumento.EXTRACAO_RESPOSTAS, "respostas", respostas_path),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
        )
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.CORRIGIR,
        )

        assert "gabarito_extraido" not in contexto
        assert any("gabarito" in item for item in contexto["_documentos_faltantes"])

    def test_contexto_json_usa_json_da_ultima_execucao_dual_output(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        questoes_path = tmp_path / "questoes.json"
        questoes_path.write_text(json.dumps({"questoes": []}), encoding="utf-8")
        correcao_antiga_path = tmp_path / "correcao_antiga.json"
        correcao_antiga_path.write_text(json.dumps({"nota_final": 4}), encoding="utf-8")
        correcao_nova_path = tmp_path / "correcao_nova.json"
        correcao_nova_path.write_text(json.dumps({"nota_final": 8}), encoding="utf-8")
        correcao_pdf_path = tmp_path / "correcao_nova.pdf"
        correcao_pdf_path.write_bytes(b"%PDF-1.4\n")

        docs_base = [
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes",
                questoes_path,
                criado_em="2026-05-16T19:00:00",
                metadata={"cost_run_id": "questoes-run"},
            ),
        ]
        docs_aluno = docs_base + [
            self._doc(
                TipoDocumento.CORRECAO,
                "correcao-pdf-nova",
                correcao_pdf_path,
                ".pdf",
                criado_em="2026-05-16T19:02:00",
                metadata={"cost_run_id": "correcao-run-nova"},
            ),
            self._doc(
                TipoDocumento.CORRECAO,
                "correcao-json-nova",
                correcao_nova_path,
                ".json",
                criado_em="2026-05-16T19:01:00",
                metadata={"cost_run_id": "correcao-run-nova"},
            ),
            self._doc(
                TipoDocumento.CORRECAO,
                "correcao-json-antiga",
                correcao_antiga_path,
                ".json",
                criado_em="2026-05-16T18:00:00",
                metadata={"cost_run_id": "correcao-run-antiga"},
            ),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
        )
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.ANALISAR_HABILIDADES,
        )

        assert '"nota_final": 8' in contexto["correcoes"]
        assert '"nota_final": 4' not in contexto["correcoes"]

    def test_contexto_json_nao_usa_analise_antiga_se_ultima_execucao_falhou_sem_json(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento

        questoes_path = tmp_path / "questoes.json"
        questoes_path.write_text(json.dumps({"questoes": []}), encoding="utf-8")
        correcao_path = tmp_path / "correcao.json"
        correcao_path.write_text(json.dumps({"nota_final": 8}), encoding="utf-8")
        analise_antiga_path = tmp_path / "analise_antiga.json"
        analise_antiga_path.write_text(json.dumps({"habilidades": {"dominadas": []}}), encoding="utf-8")
        analise_erro_pdf = tmp_path / "analise_erro.pdf"
        analise_erro_pdf.write_bytes(b"%PDF-1.4\n")

        docs_base = [
            self._doc(
                TipoDocumento.EXTRACAO_QUESTOES,
                "questoes",
                questoes_path,
                criado_em="2026-05-16T19:00:00",
                metadata={"cost_run_id": "questoes-run"},
            ),
        ]
        docs_aluno = docs_base + [
            self._doc(
                TipoDocumento.CORRECAO,
                "correcao",
                correcao_path,
                criado_em="2026-05-16T19:01:00",
                metadata={"cost_run_id": "correcao-run"},
            ),
            self._doc(
                TipoDocumento.ANALISE_HABILIDADES,
                "analise-erro-pdf",
                analise_erro_pdf,
                ".pdf",
                criado_em="2026-05-16T19:03:00",
                status="erro",
                metadata={"cost_run_id": "analise-run-falha"},
            ),
            self._doc(
                TipoDocumento.ANALISE_HABILIDADES,
                "analise-json-antiga",
                analise_antiga_path,
                ".json",
                criado_em="2026-05-16T18:00:00",
                metadata={"cost_run_id": "analise-run-antiga"},
            ),
        ]

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _atividade_id, aluno_id=None: docs_aluno if aluno_id else docs_base
        )
        executor.storage.resolver_caminho_documento = MagicMock(
            side_effect=lambda doc: Path(doc.caminho_arquivo)
        )

        contexto = executor._preparar_contexto_json(
            "ativ_test",
            "aluno_test",
            EtapaProcessamento.GERAR_RELATORIO,
        )

        assert "analise_habilidades" not in contexto
        assert "analise_habilidades" in contexto["_documentos_faltantes"]

    def test_extrair_respostas_pdf_sem_texto_mantem_placeholder_de_anexo(self, tmp_path):
        from executor import EtapaProcessamento, PipelineExecutor
        from models import TipoDocumento
        import fitz

        prova_path = tmp_path / "prova_sem_texto.pdf"
        pdf = fitz.open()
        pdf.new_page()
        pdf.save(str(prova_path))
        pdf.close()

        prova_doc = self._doc(
            TipoDocumento.PROVA_RESPONDIDA,
            "prova-sem-texto",
            prova_path,
            ".pdf",
        )

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=[prova_doc])
        executor.storage.resolver_caminho_documento = MagicMock(return_value=prova_path)
        executor.storage.get_aluno = MagicMock(return_value=MagicMock(nome="Aluno PDF"))

        variaveis = executor._preparar_variaveis_texto(
            EtapaProcessamento.EXTRAIR_RESPOSTAS,
            "ativ_test",
            "aluno_test",
            materia=MagicMock(nome="Matematica"),
            atividade=MagicMock(nome="Lista", nota_maxima=10),
            usar_multimodal=True,
        )

        assert "DOCUMENTO ANEXADO" in variaveis["conteudo_documento"]

    def test_paginas_pdf_sem_texto_sao_renderizadas_como_imagem(self, tmp_path):
        from executor import PipelineExecutor
        import fitz

        imagem_doc = fitz.open()
        imagem_page = imagem_doc.new_page(width=300, height=180)
        imagem_page.insert_text((24, 60), "Questao 3 resposta manuscrita simulada")
        png_bytes = imagem_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
        imagem_doc.close()

        prova_path = tmp_path / "prova_scan.pdf"
        pdf = fitz.open()
        page_scan = pdf.new_page(width=300, height=180)
        page_scan.insert_image(page_scan.rect, stream=png_bytes)
        page_texto = pdf.new_page(width=300, height=180)
        page_texto.insert_text((24, 60), "Questao 7 resposta digitada com texto extraivel")
        pdf.save(str(prova_path))
        pdf.close()

        executor = PipelineExecutor.__new__(PipelineExecutor)
        imagens, temp_dir = executor._renderizar_paginas_pdf_sem_texto_para_anexos(
            [str(prova_path)],
            provider_tipo="openai",
        )

        try:
            assert len(imagens) == 1
            assert "pagina_001" in Path(imagens[0]).name
            assert Path(imagens[0]).suffix == ".png"
            assert Path(imagens[0]).exists()
        finally:
            if temp_dir is not None:
                temp_dir.cleanup()

    def test_extrair_respostas_scan_quase_tudo_branco_falha_alto(self):
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        resposta = {
            "respostas": [
                {"questao_numero": 1, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 2, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 3, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 4, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 5, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 6, "resposta_aluno": "", "em_branco": True},
                {"questao_numero": 7, "resposta_aluno": "codigo Julia", "em_branco": False},
            ]
        }

        erro = executor._erro_respostas_scan_suspeitas(
            resposta,
            tem_paginas_pdf_renderizadas=True,
        )

        assert erro is not None
        assert "paginas escaneadas anexadas como imagem" in erro
        assert executor._erro_respostas_scan_suspeitas(
            resposta,
            tem_paginas_pdf_renderizadas=False,
        ) is None

    @pytest.mark.asyncio
    async def test_openai_reasoning_model_envia_imagem_sem_bloqueio_local(self, monkeypatch):
        from anexos import ArquivoAnexo, ClienteAPIMultimodal

        captured = {}

        class FakeResponse:
            status_code = 200
            headers = {}

            def json(self):
                return {
                    "choices": [{"message": {"content": "{\"ok\": true}"}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                }

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def post(self, url, headers, json):
                captured["payload"] = json
                return FakeResponse()

        monkeypatch.setattr("anexos.httpx.AsyncClient", FakeClient)

        cliente = ClienteAPIMultimodal({
            "tipo": "openai",
            "api_key": "test-key",
            "modelo": "gpt-5-nano",
            "max_tokens": 128,
        })
        anexo = ArquivoAnexo(
            nome="pagina_001_scan.png",
            caminho="/tmp/pagina_001_scan.png",
            extensao=".png",
            mime_type="image/png",
            tamanho_bytes=10,
            conteudo_base64="aW1hZ2U=",
            tipo_envio="binario",
        )

        resultado = await cliente._enviar_openai("Leia a imagem", [anexo], None, None)

        assert resultado.sucesso is True
        content = captured["payload"]["messages"][-1]["content"]
        assert any(part.get("type") == "image_url" for part in content)
        assert any("IMAGEM ANEXADA" in part.get("text", "") for part in content)


class TestF2T1_ErrorFramework:
    """F2-T1: Framework de erros estruturados."""

    def test_erro_documento_faltante_constant_exists(self):
        """ERRO_DOCUMENTO_FALTANTE constant exists and is correct string."""
        from models import ERRO_DOCUMENTO_FALTANTE
        assert ERRO_DOCUMENTO_FALTANTE == "DOCUMENTO_FALTANTE"

    def test_erro_questoes_faltantes_constant_exists(self):
        """ERRO_QUESTOES_FALTANTES constant exists and is correct string."""
        from models import ERRO_QUESTOES_FALTANTES
        assert ERRO_QUESTOES_FALTANTES == "QUESTOES_FALTANTES"

    def test_severidade_erro_enum_has_critico(self):
        """SeveridadeErro enum has CRITICO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "CRITICO")
        assert SeveridadeErro.CRITICO.value == "critico"

    def test_severidade_erro_enum_has_alto(self):
        """SeveridadeErro enum has ALTO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "ALTO")
        assert SeveridadeErro.ALTO.value == "alto"

    def test_severidade_erro_enum_has_medio(self):
        """SeveridadeErro enum has MEDIO member."""
        from models import SeveridadeErro
        assert hasattr(SeveridadeErro, "MEDIO")
        assert SeveridadeErro.MEDIO.value == "medio"

    def test_criar_erro_pipeline_returns_dict_with_all_fields(self):
        """criar_erro_pipeline() returns dict with tipo, mensagem, severidade, etapa, timestamp."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="Arquivo não encontrado",
            severidade=SeveridadeErro.CRITICO,
            etapa="extrair_questoes"
        )
        assert isinstance(result, dict)
        assert result["tipo"] == "DOCUMENTO_FALTANTE"
        assert result["mensagem"] == "Arquivo não encontrado"
        assert result["severidade"] == "critico"
        assert result["etapa"] == "extrair_questoes"
        assert "timestamp" in result

    def test_criar_erro_pipeline_timestamp_is_iso_format(self):
        """Timestamp field is a valid ISO format string."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="corrigir"
        )
        # Should not raise
        datetime.fromisoformat(result["timestamp"])

    def test_parsear_resposta_rejeita_markdown_relatorio_sem_json(self):
        """Relatorio em Markdown nao deve ser aceito como fallback silencioso."""
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        parsed = executor._parsear_resposta(
            "# Relatorio\n\n- Texto longo sem JSON estruturado para a etapa final.",
            context={"stage": "gerar_relatorio", "provider": "teste"},
        )

        assert parsed["_error"] == "parse_failed"

    def test_criar_erro_pipeline_severidade_accepts_string(self):
        """criar_erro_pipeline() works when severidade is passed as string too."""
        from models import criar_erro_pipeline
        result = criar_erro_pipeline(
            tipo="QUESTOES_FALTANTES",
            mensagem="Nenhuma questão extraída",
            severidade="alto",
            etapa="extrair_questoes"
        )
        assert result["severidade"] == "alto"

    def test_criar_erro_pipeline_no_extra_fields(self):
        """Result dict has exactly the expected fields."""
        from models import criar_erro_pipeline, SeveridadeErro
        result = criar_erro_pipeline(
            tipo="DOCUMENTO_FALTANTE",
            mensagem="test",
            severidade=SeveridadeErro.CRITICO,
            etapa="test_etapa"
        )
        expected_keys = {"tipo", "mensagem", "severidade", "etapa", "timestamp"}
        assert set(result.keys()) == expected_keys


# ============================================================
# F3-T1: Missing document detection saves JSON with _erro_pipeline
# ============================================================

class TestF3T1_DocumentoFaltante:
    """F3-T1: When documents are missing, executor saves JSON with _erro_pipeline."""

    @pytest.fixture
    def executor_with_mocks(self):
        """Create a PipelineExecutor with mocked storage."""
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = None
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "test-provider",
            "modelo": "test-model",
        })

        # Track what content gets saved via _salvar_resultado
        executor._saved_contents = []
        original_salvar = None

        return executor

    @pytest.mark.asyncio
    async def test_missing_doc_saves_json_with_erro_pipeline(self, executor_with_mocks):
        """When docs are missing, _executar_multimodal should save JSON with _erro_pipeline field."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        # Mock _preparar_contexto_json to return missing docs
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_questoes.json"],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        # Mock _salvar_resultado to capture what gets saved
        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        # Create mock prompt
        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        # Call the method
        resultado = await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        # Verify: result is failure
        assert resultado.sucesso is False

        # Verify: JSON was saved with _erro_pipeline
        assert "_erro_pipeline" in saved_content, \
            "Missing doc should trigger saving JSON with _erro_pipeline field"

    @pytest.mark.asyncio
    async def test_missing_doc_erro_pipeline_has_correct_type(self, executor_with_mocks):
        """The _erro_pipeline saved should have tipo=DOCUMENTO_FALTANTE."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_gabarito.json"],
            "_documentos_carregados": ["extracao_questoes.json"]
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        assert saved_content.get("_erro_pipeline", {}).get("tipo") == "DOCUMENTO_FALTANTE", \
            "_erro_pipeline.tipo should be DOCUMENTO_FALTANTE"

    @pytest.mark.asyncio
    async def test_missing_doc_erro_pipeline_has_all_fields(self, executor_with_mocks):
        """The _erro_pipeline should have tipo, mensagem, severidade, etapa, timestamp."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["extracao_questoes.json"],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=[])

        saved_content = {}
        async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
            saved_content.update(resposta_parsed or {})
            return "mock_doc_id"

        executor._salvar_resultado = mock_salvar

        mock_prompt = MagicMock()
        mock_prompt.id = "test_prompt"

        await executor._executar_multimodal(
            etapa=EtapaProcessamento.CORRIGIR,
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            prompt=mock_prompt,
            materia=MagicMock(),
            atividade=MagicMock(),
            provider_id=None,
            variaveis_extra=None,
            salvar_resultado=True,
            inicio=time.time(),
        )

        erro = saved_content.get("_erro_pipeline", {})
        required_fields = {"tipo", "mensagem", "severidade", "etapa", "timestamp"}
        assert required_fields.issubset(set(erro.keys())), \
            f"_erro_pipeline missing fields: {required_fields - set(erro.keys())}"


# ============================================================
# F4-T1: Missing questions detection saves JSON with _erro_pipeline
# ============================================================

class TestF4T1_QuestoesFaltantes:
    """F4-T1: When question extraction returns 0 questions, save JSON with _erro_pipeline."""

    @pytest.fixture
    def executor_with_mocks(self):
        """Create a PipelineExecutor with mocked dependencies for post-extraction testing."""
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        return executor

    @pytest.mark.asyncio
    async def test_empty_questoes_saves_erro_pipeline(self, executor_with_mocks):
        """When EXTRAIR_QUESTOES returns empty questoes list, save JSON with _erro_pipeline."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        # Mock dependencies to get past the missing docs check
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": [],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=["fake_file.pdf"])
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "openai", "api_key": "fake", "modelo": "gpt-4"
        })

        # Mock the API client to return a response with empty questoes
        mock_response = MagicMock()
        mock_response.content = '{"questoes": []}'
        mock_response.input_tokens = 100
        mock_response.output_tokens = 50
        mock_response.tokens_used = 50
        mock_response.provider = "openai"
        mock_response.modelo = "gpt-4"
        mock_response.resposta = '{"questoes": []}'
        mock_response.anexos_enviados = []
        mock_response.anexos_confirmados = False
        mock_response.retryable = False
        mock_response.retry_after = None
        mock_response.tentativas = 1
        mock_response.sucesso = True

        # Mock ClienteAPIMultimodal
        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            # Mock _parsear_resposta to return parsed response with empty questoes
            executor._parsear_resposta = MagicMock(return_value={"questoes": []})

            # Track what gets saved
            saved_content = {}
            async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
                saved_content.update(resposta_parsed or {})
                return "mock_doc_id"

            executor._salvar_resultado = mock_salvar

            mock_prompt = MagicMock()
            mock_prompt.id = "test_prompt"
            mock_prompt.render = MagicMock(return_value="rendered prompt")
            mock_prompt.render_sistema = MagicMock(return_value=None)

            resultado = await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
                atividade_id="ativ_test",
                aluno_id=None,
                prompt=mock_prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        # Verify: result should indicate failure
        assert resultado.sucesso is False, \
            "Empty questoes should make the result fail"

        # Verify: JSON was saved with _erro_pipeline
        assert "_erro_pipeline" in saved_content, \
            "Empty questoes should trigger saving JSON with _erro_pipeline field"

    @pytest.mark.asyncio
    async def test_empty_questoes_erro_pipeline_type(self, executor_with_mocks):
        """The _erro_pipeline for empty questoes should have tipo=QUESTOES_FALTANTES."""
        executor = executor_with_mocks
        from executor import EtapaProcessamento

        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": [],
            "_documentos_carregados": []
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=["fake.pdf"])
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "openai", "api_key": "fake", "modelo": "gpt-4"
        })

        mock_response = MagicMock()
        mock_response.content = '{"questoes": []}'
        mock_response.input_tokens = 100
        mock_response.output_tokens = 50
        mock_response.tokens_used = 50
        mock_response.provider = "openai"
        mock_response.modelo = "gpt-4"
        mock_response.resposta = '{"questoes": []}'
        mock_response.anexos_enviados = []
        mock_response.anexos_confirmados = False
        mock_response.retryable = False
        mock_response.retry_after = None
        mock_response.tentativas = 1
        mock_response.sucesso = True

        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            executor._parsear_resposta = MagicMock(return_value={"questoes": []})

            saved_content = {}
            async def mock_salvar(etapa, ativ_id, aluno_id, resposta_raw, resposta_parsed, *args, **kwargs):
                saved_content.update(resposta_parsed or {})
                return "mock_doc_id"

            executor._salvar_resultado = mock_salvar

            mock_prompt = MagicMock()
            mock_prompt.id = "test_prompt"
            mock_prompt.render = MagicMock(return_value="rendered prompt")
            mock_prompt.render_sistema = MagicMock(return_value=None)

            await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
                atividade_id="ativ_test",
                aluno_id=None,
                prompt=mock_prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        assert saved_content.get("_erro_pipeline", {}).get("tipo") == "QUESTOES_FALTANTES", \
            "_erro_pipeline.tipo should be QUESTOES_FALTANTES"


class TestMultimodalExtractionValidationRetry:
    """Retry de validação deve usar o mesmo modelo e continuar falhando alto."""

    @staticmethod
    def _executor():
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": [],
            "_documentos_carregados": [],
        })
        executor._coletar_arquivos_para_etapa = MagicMock(return_value=["fake.pdf"])
        executor._get_provider_config = MagicMock(return_value={
            "tipo": "openai",
            "api_key": "fake",
            "modelo": "gpt-5.4-mini",
        })
        executor._salvar_resultado = AsyncMock(return_value="doc-ok")
        return executor

    @staticmethod
    def _prompt():
        mock_prompt = MagicMock()
        mock_prompt.id = "prompt-gabarito"
        mock_prompt.render = MagicMock(return_value="prompt original")
        mock_prompt.render_sistema = MagicMock(return_value=None)
        return mock_prompt

    @staticmethod
    def _response(resposta, tokens_entrada=10, tokens_saida=5):
        mock_response = MagicMock()
        mock_response.sucesso = True
        mock_response.resposta = resposta
        mock_response.provider = "openai"
        mock_response.modelo = "gpt-5.4-mini"
        mock_response.tokens_entrada = tokens_entrada
        mock_response.tokens_saida = tokens_saida
        mock_response.anexos_enviados = [{"nome": "fake.pdf"}]
        mock_response.anexos_confirmados = True
        mock_response.retryable = False
        mock_response.retry_after = None
        mock_response.tentativas = 1
        return mock_response

    @staticmethod
    def _gabarito_valido():
        return json.dumps({
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_correta": "A",
                    "justificativa": "Resposta indicada no gabarito.",
                    "conceito_central": "Aplicar definição de subespaço vetorial",
                    "criterios_parciais": [],
                }
            ],
            "_avisos_documento": [],
            "_avisos_questao": [],
        })

    @pytest.mark.asyncio
    async def test_retry_corrige_json_invalido_e_soma_tokens(self):
        from executor import EtapaProcessamento

        executor = self._executor()
        prompt = self._prompt()
        respostas = [
            self._response("Aqui está o JSON:\n```json\n{ quebrado", 100, 20),
            self._response(self._gabarito_valido(), 120, 30),
        ]

        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(side_effect=respostas)
            mock_client_class.return_value = mock_client

            resultado = await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_GABARITO,
                atividade_id="ativ",
                aluno_id=None,
                prompt=prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        assert resultado.sucesso is True
        assert resultado.tentativas == 2
        assert resultado.tokens_entrada == 220
        assert resultado.tokens_saida == 50
        assert mock_client.enviar_com_anexos.await_count == 2
        segunda_mensagem = mock_client.enviar_com_anexos.await_args_list[1].kwargs["mensagem"]
        assert "RETRY EXPLICITO DE VALIDACAO" in segunda_mensagem
        assert "mesmo provider e modelo" in segunda_mensagem.lower()
        executor._salvar_resultado.assert_awaited_once()
        salvar_kwargs = executor._salvar_resultado.await_args.kwargs
        assert salvar_kwargs["tokens_entrada"] == 220
        assert salvar_kwargs["tokens_saida"] == 50

    @pytest.mark.asyncio
    async def test_retry_corrige_gabarito_todo_missing_content(self):
        from executor import EtapaProcessamento

        executor = self._executor()
        prompt = self._prompt()
        todos_missing = json.dumps({
            "respostas": [
                {
                    "questao_numero": 1,
                    "resposta_correta": "MISSING_CONTENT",
                    "justificativa": "",
                    "conceito_central": "MISSING_CONTENT",
                    "criterios_parciais": [],
                }
            ],
            "_avisos_documento": [],
            "_avisos_questao": [],
        })
        respostas = [
            self._response(todos_missing, 60, 15),
            self._response(self._gabarito_valido(), 70, 20),
        ]

        with patch("executor.ClienteAPIMultimodal") as mock_client_class:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(side_effect=respostas)
            mock_client_class.return_value = mock_client

            resultado = await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_GABARITO,
                atividade_id="ativ",
                aluno_id=None,
                prompt=prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        assert resultado.sucesso is True
        assert resultado.tentativas == 2
        segunda_mensagem = mock_client.enviar_com_anexos.await_args_list[1].kwargs["mensagem"]
        assert "não marque todas como MISSING_CONTENT" in segunda_mensagem

    @pytest.mark.asyncio
    async def test_retry_invalido_duas_vezes_registra_custo_e_nao_salva_documento(self):
        from executor import EtapaProcessamento

        executor = self._executor()
        prompt = self._prompt()
        respostas = [
            self._response("nao e json", 11, 2),
            self._response("continua sem json", 13, 3),
        ]

        with patch("executor.ClienteAPIMultimodal") as mock_client_class, \
                patch("executor.record_token_usage") as record_usage:
            mock_client = MagicMock()
            mock_client.enviar_com_anexos = AsyncMock(side_effect=respostas)
            mock_client_class.return_value = mock_client

            resultado = await executor._executar_multimodal(
                etapa=EtapaProcessamento.EXTRAIR_GABARITO,
                atividade_id="ativ",
                aluno_id=None,
                prompt=prompt,
                materia=MagicMock(),
                atividade=MagicMock(),
                provider_id=None,
                variaveis_extra=None,
                salvar_resultado=True,
                inicio=time.time(),
            )

        assert resultado.sucesso is False
        assert resultado.tentativas == 2
        assert resultado.tokens_entrada == 24
        assert resultado.tokens_saida == 5
        executor._salvar_resultado.assert_not_awaited()
        record_usage.assert_called_once()
        assert record_usage.call_args.kwargs["tokens_entrada"] == 24
        assert record_usage.call_args.kwargs["tokens_saida"] == 5
        assert record_usage.call_args.kwargs["metadata"]["tentativas_validacao"] == 2


# ============================================================
# F3-T2: Pipeline orchestration marks overall result as ERRO
# ============================================================

class TestF3T2_PipelineOrquestracao:
    """F3-T2: When pipeline stage fails, orchestration adds _pipeline_erro to results."""

    @pytest.fixture
    def executor_pipeline(self):
        """Create executor for pipeline orchestration testing."""
        from executor import PipelineExecutor
        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        return executor

    @pytest.mark.asyncio
    async def test_failed_stage_adds_pipeline_erro(self, executor_pipeline):
        """When a stage returns sucesso=False, results dict should have _pipeline_erro."""
        from executor import ResultadoExecucao, EtapaProcessamento
        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])

        async def mock_executar_etapa(etapa, ativ_id, aluno_id=None, **kwargs):
            return ResultadoExecucao(
                sucesso=False, etapa=etapa, erro="Doc faltante", retryable=False
            )

        executor.executar_etapa = mock_executar_etapa

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test", aluno_id="aluno_test"
        )

        assert "_pipeline_erro" in resultados, \
            "Failed pipeline should include _pipeline_erro in returned dict"

    @pytest.mark.asyncio
    async def test_pipeline_erro_has_stage_and_status(self, executor_pipeline):
        """_pipeline_erro should have etapa_falha and sucesso=False."""
        from executor import ResultadoExecucao, EtapaProcessamento
        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])

        async def mock_executar_etapa(etapa, ativ_id, aluno_id=None, **kwargs):
            return ResultadoExecucao(
                sucesso=False, etapa=etapa, erro="Fail", retryable=False
            )

        executor.executar_etapa = mock_executar_etapa

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test", aluno_id="aluno_test"
        )

        erro = resultados.get("_pipeline_erro")
        assert erro is not None, "_pipeline_erro should exist"
        assert "etapa_falha" in erro, "Should have etapa_falha field"
        assert erro.get("sucesso") is False, "sucesso should be False"

    @pytest.mark.asyncio
    async def test_failed_stage_records_task_error(self, executor_pipeline):
        """Task progress must expose the failure reason, not just status=failed."""
        from executor import ResultadoExecucao, EtapaProcessamento
        from routes_tasks import register_pipeline_task, task_registry

        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])
        executor.corrigir = AsyncMock(return_value=ResultadoExecucao(
            sucesso=False,
            etapa=EtapaProcessamento.CORRIGIR,
            erro="Provider recusou tool-use",
            erro_codigo=400,
            retryable=False,
        ))
        task_id = register_pipeline_task("pipeline", "ativ_test", ["aluno_test"])

        try:
            await executor.executar_pipeline_completo(
                atividade_id="ativ_test",
                aluno_id="aluno_test",
                selected_steps=["corrigir"],
                task_id=task_id,
            )

            task = task_registry[task_id]
            assert task["status"] == "failed"
            assert "corrigir" in task["error"]
            assert "Provider recusou tool-use" in task["error"]
            assert "400" in task["error"]
        finally:
            task_registry.pop(task_id, None)


# ============================================================
# P4: EXTRAIR_RESPOSTAS requires a valid prova_respondida file
# ============================================================

class TestP4ProvaRespondidaGate:
    """P4: EXTRAIR_RESPOSTAS must fail early without a valid student proof file."""

    @pytest.fixture
    def executor_pipeline(self):
        """Create executor for P4 orchestration tests."""
        from executor import PipelineExecutor
        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        return executor

    @staticmethod
    def _doc(tipo, doc_id="doc-test", path="doc-test.pdf", extensao=".pdf"):
        doc = MagicMock()
        doc.tipo = tipo
        doc.id = doc_id
        doc.caminho_arquivo = path
        doc.extensao = extensao
        return doc

    @pytest.mark.asyncio
    async def test_pipeline_does_not_call_ai_when_respostas_needs_missing_prova(self, executor_pipeline):
        """Pipeline should block before AI when extrair_respostas is selected and proof is absent."""
        from executor import EtapaProcessamento

        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])
        aluno = MagicMock()
        aluno.nome = "Aluno Sem Prova"
        executor.storage.get_aluno = MagicMock(return_value=aluno)
        executor.executar_etapa = AsyncMock()

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            selected_steps=["extrair_respostas"],
        )

        executor.executar_etapa.assert_not_called()
        assert resultados["extrair_respostas"].sucesso is False
        assert resultados["extrair_respostas"].etapa == EtapaProcessamento.EXTRAIR_RESPOSTAS
        assert "_pipeline_erro" in resultados

    @pytest.mark.asyncio
    async def test_pipeline_fails_when_prova_doc_exists_but_file_missing(self, executor_pipeline, tmp_path):
        """A registered prova_respondida is not valid if storage cannot resolve an existing file."""
        from models import TipoDocumento

        executor = executor_pipeline
        missing_path = tmp_path / "missing.pdf"
        prova_doc = self._doc(TipoDocumento.PROVA_RESPONDIDA, "prova-1", str(missing_path))
        executor.storage.listar_documentos = MagicMock(
            side_effect=lambda _ativ, aluno_id=None: [prova_doc] if aluno_id else []
        )
        executor.storage.get_aluno = MagicMock(return_value=MagicMock(nome="Aluno Com Caminho Quebrado"))
        executor.storage.resolver_caminho_documento = MagicMock(return_value=missing_path)
        executor.executar_etapa = AsyncMock()

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            selected_steps=["extrair_respostas"],
        )

        executor.executar_etapa.assert_not_called()
        assert resultados["extrair_respostas"].sucesso is False
        assert "arquivo" in resultados["extrair_respostas"].erro.lower()
        assert "_pipeline_erro" in resultados

    @pytest.mark.asyncio
    async def test_pipeline_does_not_block_when_extrair_respostas_not_selected(self, executor_pipeline):
        """Missing proof must not block unrelated selected steps."""
        from executor import ResultadoExecucao, EtapaProcessamento

        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])
        executor.corrigir = AsyncMock(return_value=ResultadoExecucao(
            sucesso=True,
            etapa=EtapaProcessamento.CORRIGIR,
        ))

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            selected_steps=["corrigir"],
        )

        executor.corrigir.assert_awaited_once()
        assert "extrair_respostas" not in resultados
        assert "_pipeline_erro" not in resultados

    @pytest.mark.asyncio
    async def test_extrair_respostas_aluno_fails_early_without_prova(self, executor_pipeline):
        """Direct extraction must also block before executar_etapa when proof is absent."""
        executor = executor_pipeline
        executor.storage.listar_documentos = MagicMock(return_value=[])
        executor.storage.get_aluno = MagicMock(return_value=MagicMock(nome="Aluno Sem Prova"))
        executor.executar_etapa = AsyncMock()

        resultado = await executor.extrair_respostas_aluno(
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            provider_id="provider-test",
        )

        executor.executar_etapa.assert_not_called()
        assert resultado.sucesso is False
        assert "prova_respondida" in resultado.erro

    @pytest.mark.asyncio
    async def test_existing_pdf_prova_is_valid_even_without_text_content(self, executor_pipeline, tmp_path):
        """A PDF proof is valid when its file exists; the gate must not require /conteudo."""
        from executor import ResultadoExecucao, EtapaProcessamento
        from models import TipoDocumento

        executor = executor_pipeline
        prova_path = tmp_path / "prova_respondida.pdf"
        prova_path.write_bytes(b"%PDF-1.4\n% test\n")
        prova_doc = self._doc(TipoDocumento.PROVA_RESPONDIDA, "prova-pdf", str(prova_path))
        executor.storage.listar_documentos = MagicMock(return_value=[prova_doc])
        executor.storage.get_aluno = MagicMock(return_value=MagicMock(nome="Aluno Com PDF"))
        executor.storage.resolver_caminho_documento = MagicMock(return_value=prova_path)
        executor.executar_etapa = AsyncMock(return_value=ResultadoExecucao(
            sucesso=True,
            etapa=EtapaProcessamento.EXTRAIR_RESPOSTAS,
        ))

        resultado = await executor.extrair_respostas_aluno(
            atividade_id="ativ_test",
            aluno_id="aluno_test",
            provider_id="provider-test",
        )

        executor.executar_etapa.assert_awaited_once()
        assert resultado.sucesso is True


# ============================================================
# P5/P6: Robust nota_final and missing-doc preservation
# ============================================================

class TestP5NotaFinalFallback:
    """P5: GERAR_RELATORIO must get a robust nota_final from correction JSON."""

    @pytest.fixture
    def executor(self):
        from executor import PipelineExecutor
        return PipelineExecutor.__new__(PipelineExecutor)

    def test_nota_final_top_level_wins(self, executor):
        data = {"nota_final": 8.5, "nota": 1, "questoes": [{"nota": 2}]}

        assert executor._calcular_nota_final_de_correcoes(data) == "8.5"

    def test_nota_top_level_is_fallback(self, executor):
        data = {"nota": 7.25, "questoes": [{"nota": 2}]}

        assert executor._calcular_nota_final_de_correcoes(data) == "7.25"

    def test_questoes_notas_are_summed(self, executor):
        data = {"questoes": [{"nota": 2}, {"nota": "3.5"}, {"feedback": "sem nota"}]}

        assert executor._calcular_nota_final_de_correcoes(data) == "5.5"

    def test_correcoes_notas_are_summed(self, executor):
        data = {"correcoes": [{"nota": 4}, {"nota": 1.75}]}

        assert executor._calcular_nota_final_de_correcoes(data) == "5.75"

    def test_invalid_json_or_no_numeric_grade_returns_na(self, executor):
        assert executor._calcular_nota_final_de_correcoes("{json inválido") == "N/A"
        assert executor._calcular_nota_final_de_correcoes({"feedback": "sem nota"}) == "N/A"


class TestP6GerarRelatorioDocumentosFaltantes:
    """P6: GERAR_RELATORIO must preserve missing document metadata."""

    @pytest.fixture
    def executor_relatorio(self):
        from executor import PipelineExecutor

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()

        atividade = MagicMock()
        atividade.turma_id = "turma-test"
        turma = MagicMock()
        turma.materia_id = "materia-test"
        materia = MagicMock()
        materia.id = "materia-test"
        prompt = MagicMock()
        prompt.id = "prompt-gerar-relatorio"

        executor.storage.get_atividade = MagicMock(return_value=atividade)
        executor.storage.get_turma = MagicMock(return_value=turma)
        executor.storage.get_materia = MagicMock(return_value=materia)
        executor.prompt_manager.get_prompt_padrao = MagicMock(return_value=prompt)
        executor._preparar_variaveis_texto = MagicMock(return_value={})
        executor._preparar_contexto_json = MagicMock(return_value={
            "_documentos_faltantes": ["correcoes", "analise_habilidades"],
            "_documentos_carregados": ["questoes_extraidas"],
        })
        executor._salvar_resultado = AsyncMock(return_value="doc-erro")
        return executor

    @pytest.mark.asyncio
    async def test_gerar_relatorio_missing_docs_returns_structured_error(self, executor_relatorio):
        resultado = await executor_relatorio.gerar_relatorio("ativ-test", "aluno-test")

        assert resultado.sucesso is False
        assert resultado.resposta_parsed["_erro_pipeline"]["tipo"] == "DOCUMENTO_FALTANTE"
        assert resultado.resposta_parsed["_documentos_faltantes"] == [
            "correcoes",
            "analise_habilidades",
        ]
        assert resultado.resposta_parsed["_documentos_carregados"] == ["questoes_extraidas"]

    @pytest.mark.asyncio
    async def test_gerar_relatorio_missing_docs_does_not_save_by_default(self, executor_relatorio):
        await executor_relatorio.gerar_relatorio("ativ-test", "aluno-test")

        executor_relatorio._salvar_resultado.assert_not_called()

    @pytest.mark.asyncio
    async def test_gerar_relatorio_can_save_error_json_without_extra_formats(self, executor_relatorio):
        resultado = await executor_relatorio.gerar_relatorio(
            "ativ-test",
            "aluno-test",
            salvar_erro_documento=True,
        )

        executor_relatorio._salvar_resultado.assert_awaited_once()
        args, kwargs = executor_relatorio._salvar_resultado.call_args
        assert args[4]["_documentos_faltantes"] == ["correcoes", "analise_habilidades"]
        assert kwargs["gerar_formatos_extras"] is False
        assert resultado.documento_id == "doc-erro"

    @pytest.mark.asyncio
    async def test_pipeline_erro_preserves_documentos_faltantes(self):
        from executor import PipelineExecutor, ResultadoExecucao, EtapaProcessamento

        executor = PipelineExecutor.__new__(PipelineExecutor)
        executor.storage = MagicMock()
        executor.prompt_manager = MagicMock()
        executor.preparador = MagicMock()
        executor.storage.listar_documentos = MagicMock(return_value=[])
        executor.gerar_relatorio = AsyncMock(return_value=ResultadoExecucao(
            sucesso=False,
            etapa=EtapaProcessamento.GERAR_RELATORIO,
            erro="Documentos obrigatórios ausentes",
            resposta_parsed={"_documentos_faltantes": ["correcoes"]},
        ))

        resultados = await executor.executar_pipeline_completo(
            atividade_id="ativ-test",
            aluno_id="aluno-test",
            selected_steps=["gerar_relatorio"],
        )

        assert resultados["_pipeline_erro"]["documentos_faltantes"] == ["correcoes"]


# ============================================================
# F5-T1: API propagates _erro_pipeline in response JSON
# ============================================================

class TestF5T1_APIPropagaErro:
    """F5-T1: API endpoint propagates _erro_pipeline when found in stored documents."""

    @pytest.mark.asyncio
    async def test_partial_result_with_erro_returns_status_erro(self):
        """When partial result has doc with _erro_pipeline, response has status=erro."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump({
                "_erro_pipeline": {
                    "tipo": "DOCUMENTO_FALTANTE",
                    "mensagem": "Docs faltando",
                    "severidade": "critico",
                    "etapa": "corrigir",
                    "timestamp": "2026-02-24T12:00:00"
                }
            }, f)
            temp_path = f.name

        try:
            mock_doc = MagicMock()
            mock_doc.tipo = MagicMock()
            mock_doc.tipo.value = "correcao"
            mock_doc.id = "doc_erro"
            mock_doc.extensao = ".json"
            mock_doc.aluno_id = "aluno_test"
            mock_doc.nome_arquivo = "correcao.json"

            mock_storage = MagicMock()
            mock_storage.listar_documentos = MagicMock(
                side_effect=lambda ativ_id, aluno_id=None: [mock_doc] if aluno_id else []
            )
            mock_storage.get_documento = MagicMock(return_value=mock_doc)
            mock_storage.resolver_caminho_documento = MagicMock(return_value=Path(temp_path))

            mock_visualizador = MagicMock()
            mock_visualizador.get_resultado_aluno = MagicMock(return_value=None)

            with patch("routes_resultados.visualizador", mock_visualizador), \
                 patch("routes_resultados.storage", mock_storage):
                from routes_resultados import get_resultado_aluno
                response = await get_resultado_aluno("ativ_test", "aluno_test")

            assert response.get("status") == "erro", \
                "Response should have status='erro' when doc has _erro_pipeline"
            assert "erro_pipeline" in response, \
                "Response should include erro_pipeline dict"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_partial_result_without_erro_no_status_erro(self):
        """Normal partial result should NOT have status=erro."""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False, encoding='utf-8'
        ) as f:
            json.dump({"nota": 8.5, "correcoes": []}, f)
            temp_path = f.name

        try:
            mock_doc = MagicMock()
            mock_doc.tipo = MagicMock()
            mock_doc.tipo.value = "correcao"
            mock_doc.id = "doc_ok"
            mock_doc.extensao = ".json"
            mock_doc.aluno_id = "aluno_test"
            mock_doc.nome_arquivo = "correcao.json"

            mock_storage = MagicMock()
            mock_storage.listar_documentos = MagicMock(
                side_effect=lambda ativ_id, aluno_id=None: [mock_doc] if aluno_id else []
            )
            mock_storage.get_documento = MagicMock(return_value=mock_doc)
            mock_storage.resolver_caminho_documento = MagicMock(return_value=Path(temp_path))

            mock_visualizador = MagicMock()
            mock_visualizador.get_resultado_aluno = MagicMock(return_value=None)

            with patch("routes_resultados.visualizador", mock_visualizador), \
                 patch("routes_resultados.storage", mock_storage):
                from routes_resultados import get_resultado_aluno
                response = await get_resultado_aluno("ativ_test", "aluno_test")

            assert response.get("status") != "erro", \
                "Normal partial result should NOT have status=erro"
        finally:
            os.unlink(temp_path)


# ============================================================
# F5-T2: Visualizador includes erro_pipeline in VisaoAluno
# ============================================================

class TestF5T2_VisualizadorPropagaErro:
    """F5-T2: Visualizador includes _erro_pipeline in VisaoAluno.to_dict()."""

    def test_correction_with_erro_pipeline_included_in_to_dict(self):
        """When correction JSON has _erro_pipeline, to_dict() should include erro_pipeline."""
        from visualizador import VisualizadorResultados
        from models import TipoDocumento

        vis = VisualizadorResultados()

        mock_atividade = MagicMock()
        mock_atividade.nome = "Prova 1"
        mock_atividade.nota_maxima = 10.0

        mock_aluno = MagicMock()
        mock_aluno.nome = "Joao"
        mock_aluno.id = "aluno_test"

        mock_correcao_doc = MagicMock()
        mock_correcao_doc.tipo = TipoDocumento.CORRECAO
        mock_correcao_doc.criado_em = None
        mock_correcao_doc.ia_provider = "test"

        vis.storage = MagicMock()
        vis.storage.get_atividade = MagicMock(return_value=mock_atividade)
        vis.storage.get_aluno = MagicMock(return_value=mock_aluno)
        vis.storage.listar_documentos = MagicMock(return_value=[mock_correcao_doc])

        erro_data = {
            "_erro_pipeline": {
                "tipo": "DOCUMENTO_FALTANTE",
                "mensagem": "Docs faltando",
                "severidade": "critico",
                "etapa": "corrigir",
                "timestamp": "2026-02-24T12:00:00"
            },
            "_documentos_faltantes": ["extracao_questoes.json"]
        }
        vis._ler_json = MagicMock(return_value=erro_data)

        resultado = vis.get_resultado_aluno("ativ_test", "aluno_test")

        assert resultado is not None, "Should return VisaoAluno even with error"
        resultado_dict = resultado.to_dict()
        assert "erro_pipeline" in resultado_dict, \
            "to_dict() should include erro_pipeline when correction has error"

    def test_normal_correction_no_erro_pipeline_in_to_dict(self):
        """Normal correction should NOT have erro_pipeline in to_dict()."""
        from visualizador import VisualizadorResultados
        from models import TipoDocumento

        vis = VisualizadorResultados()

        mock_atividade = MagicMock()
        mock_atividade.nome = "Prova 1"
        mock_atividade.nota_maxima = 10.0

        mock_aluno = MagicMock()
        mock_aluno.nome = "Maria"
        mock_aluno.id = "aluno_test"

        mock_correcao_doc = MagicMock()
        mock_correcao_doc.tipo = TipoDocumento.CORRECAO
        mock_correcao_doc.criado_em = None
        mock_correcao_doc.ia_provider = "test"

        vis.storage = MagicMock()
        vis.storage.get_atividade = MagicMock(return_value=mock_atividade)
        vis.storage.get_aluno = MagicMock(return_value=mock_aluno)
        vis.storage.listar_documentos = MagicMock(return_value=[mock_correcao_doc])

        vis._ler_json = MagicMock(return_value={"nota": 8.5, "feedback": "Bom"})

        resultado = vis.get_resultado_aluno("ativ_test", "aluno_test")

        assert resultado is not None
        resultado_dict = resultado.to_dict()
        assert "erro_pipeline" not in resultado_dict, \
            "Normal result should NOT have erro_pipeline"


# ============================================================
# F6-T1: UI red error banner in result detail view
# ============================================================

FRONTEND_HTML = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"


class TestF6T1_UIBannerErro:
    """F6-T1: showResultadoAluno should render a red error banner when result has error."""

    @pytest.fixture
    def html_content(self):
        """Read the frontend HTML file."""
        assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
        return FRONTEND_HTML.read_text(encoding="utf-8")

    def test_show_resultado_aluno_checks_erro_pipeline(self, html_content):
        """showResultadoAluno function should check for erro_pipeline in response data."""
        # Find the showResultadoAluno function body
        start = html_content.find("function showResultadoAluno")
        assert start != -1, "showResultadoAluno function must exist"
        # Check that it references erro_pipeline
        func_body = html_content[start:start + 5000]
        assert "erro_pipeline" in func_body, \
            "showResultadoAluno should check for erro_pipeline in response data"

    def test_show_resultado_aluno_renders_alert_danger(self, html_content):
        """showResultadoAluno should render alert-danger when error is present."""
        start = html_content.find("function showResultadoAluno")
        func_body = html_content[start:start + 5000]
        assert "alert-danger" in func_body, \
            "showResultadoAluno should render alert-danger banner for errors"

    def test_show_resultado_aluno_shows_error_type(self, html_content):
        """Error banner should display the error type (tipo)."""
        start = html_content.find("function showResultadoAluno")
        func_body = html_content[start:start + 5000]
        assert ".tipo" in func_body or '["tipo"]' in func_body or "tipo" in func_body, \
            "Error banner should display error tipo"


# ============================================================
# F6-T2: UI red ERRO badge in result visual rendering
# ============================================================

class TestF6T2_UIBadgeErro:
    """F6-T2: renderResultadoVisual should show ERRO badge instead of nota when error present."""

    @pytest.fixture
    def html_content(self):
        """Read the frontend HTML file."""
        assert FRONTEND_HTML.exists(), f"Frontend file not found: {FRONTEND_HTML}"
        return FRONTEND_HTML.read_text(encoding="utf-8")

    def test_render_resultado_visual_checks_erro_pipeline(self, html_content):
        """renderResultadoVisual should check for erro_pipeline in result data."""
        start = html_content.find("function renderResultadoVisual")
        assert start != -1, "renderResultadoVisual function must exist"
        func_body = html_content[start:start + 3000]
        assert "erro_pipeline" in func_body, \
            "renderResultadoVisual should check for erro_pipeline"

    def test_render_resultado_visual_shows_erro_badge(self, html_content):
        """renderResultadoVisual should show a red ERRO badge when error is present."""
        start = html_content.find("function renderResultadoVisual")
        func_body = html_content[start:start + 3000]
        assert "ERRO" in func_body, \
            "renderResultadoVisual should display ERRO text when error present"
        assert "badge-danger" in func_body or "danger" in func_body, \
            "renderResultadoVisual should use danger styling for error badge"


# ============================================================
# F7-T1: PDF includes "ERRO DE PROCESSAMENTO" section
# ============================================================

class TestF7T1_PDFErroSection:
    """F7-T1: generate_pdf() adds error section when data has _erro_pipeline."""

    def test_pdf_with_erro_pipeline_contains_error_text(self):
        """PDF generated from data with _erro_pipeline should contain ERRO DE PROCESSAMENTO."""
        from document_generators import generate_pdf
        import fitz

        data_with_error = {
            "_erro_pipeline": {
                "tipo": "DOCUMENTO_FALTANTE",
                "mensagem": "Documentos necessarios nao encontrados",
                "severidade": "critico",
                "etapa": "corrigir",
                "timestamp": "2026-02-24T12:00:00"
            },
            "nota": 0,
            "questoes": []
        }

        pdf_bytes = generate_pdf(data_with_error, title="Resultado", doc_type="correcao")
        assert isinstance(pdf_bytes, bytes), "generate_pdf should return bytes"

        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_doc:
            pdf_text = "\n".join(page.get_text() for page in pdf_doc)
        assert "ERRO DE PROCESSAMENTO" in pdf_text, \
            "PDF with _erro_pipeline should contain 'ERRO DE PROCESSAMENTO' text"

    def test_pdf_without_erro_pipeline_no_error_section(self):
        """Normal PDF should NOT contain ERRO DE PROCESSAMENTO."""
        from document_generators import generate_pdf
        import fitz

        normal_data = {
            "nota": 8.5,
            "nota_maxima": 10,
            "questoes": [{"numero": 1, "pontos_obtidos": 8.5, "pontos_maximos": 10}]
        }

        pdf_bytes = generate_pdf(normal_data, title="Resultado", doc_type="correcao")
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_doc:
            pdf_text = "\n".join(page.get_text() for page in pdf_doc)
        assert "ERRO DE PROCESSAMENTO" not in pdf_text, \
            "Normal PDF should NOT contain error section"
