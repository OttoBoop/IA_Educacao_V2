"""
Testes para os novos valores de TipoDocumento para documentos narrativos.

Verifica que o enum TipoDocumento inclui os 3 novos tipos para armazenar
os Markdowns narrativos gerados pelos stages analíticos:
- CORRECAO_NARRATIVA: análise pedagógica por questão (narrativa_correcao)
- ANALISE_HABILIDADES_NARRATIVA: síntese de padrões (narrativa_habilidades)
- RELATORIO_NARRATIVO: relatório holístico (relatorio_narrativo)

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F7-T1, F7-T2, F7-T3
"""

import pytest


class TestTipoDocumentoNarrativosExistem:
    """
    F7-T1: Os 3 novos valores do enum TipoDocumento devem existir.

    Esses tipos são necessários para que o executor (F8) possa salvar
    os Markdowns narrativos como documentos separados no storage,
    catalogados e recuperáveis para exibição no frontend.
    """

    def test_correcao_narrativa_enum_existe(self):
        """TipoDocumento deve ter CORRECAO_NARRATIVA para o Markdown por questão."""
        from models import TipoDocumento

        assert hasattr(TipoDocumento, "CORRECAO_NARRATIVA"), (
            "TipoDocumento não tem CORRECAO_NARRATIVA. "
            "Este tipo é necessário para salvar o Markdown de análise pedagógica "
            "por questão (extraído do campo narrativa_correcao do CORRIGIR)."
        )
        # Verificar que o valor é uma string válida
        assert isinstance(TipoDocumento.CORRECAO_NARRATIVA.value, str)
        assert len(TipoDocumento.CORRECAO_NARRATIVA.value) > 0

    def test_analise_habilidades_narrativa_enum_existe(self):
        """TipoDocumento deve ter ANALISE_HABILIDADES_NARRATIVA para síntese de padrões."""
        from models import TipoDocumento

        assert hasattr(TipoDocumento, "ANALISE_HABILIDADES_NARRATIVA"), (
            "TipoDocumento não tem ANALISE_HABILIDADES_NARRATIVA. "
            "Este tipo é necessário para salvar o Markdown de síntese de padrões "
            "(extraído do campo narrativa_habilidades do ANALISAR_HABILIDADES)."
        )
        assert isinstance(TipoDocumento.ANALISE_HABILIDADES_NARRATIVA.value, str)
        assert len(TipoDocumento.ANALISE_HABILIDADES_NARRATIVA.value) > 0

    def test_relatorio_narrativo_enum_existe(self):
        """TipoDocumento deve ter RELATORIO_NARRATIVO para o relatório holístico."""
        from models import TipoDocumento

        assert hasattr(TipoDocumento, "RELATORIO_NARRATIVO"), (
            "TipoDocumento não tem RELATORIO_NARRATIVO. "
            "Este tipo é necessário para salvar o Markdown do relatório holístico "
            "(extraído do campo relatorio_narrativo do GERAR_RELATORIO)."
        )
        assert isinstance(TipoDocumento.RELATORIO_NARRATIVO.value, str)
        assert len(TipoDocumento.RELATORIO_NARRATIVO.value) > 0

    def test_novos_tipos_tem_valores_distintos(self):
        """Os 3 novos tipos devem ter valores de string distintos entre si."""
        from models import TipoDocumento

        valores = [
            TipoDocumento.CORRECAO_NARRATIVA.value,
            TipoDocumento.ANALISE_HABILIDADES_NARRATIVA.value,
            TipoDocumento.RELATORIO_NARRATIVO.value,
        ]
        assert len(valores) == len(set(valores)), (
            "Os 3 novos TipoDocumento narrativos têm valores duplicados. "
            "Cada tipo deve ter um valor único para não colidir no storage."
        )

    def test_novos_valores_nao_colidem_com_existentes(self):
        """Os 3 novos valores não devem colidir com tipos existentes."""
        from models import TipoDocumento

        tipos_existentes_antes = {
            "enunciado", "gabarito", "criterios_correcao", "material_apoio",
            "prova_respondida", "correcao_professor",
            "extracao_questoes", "extracao_gabarito", "extracao_respostas",
            "correcao", "analise_habilidades", "relatorio_final",
        }

        novos_valores = {
            TipoDocumento.CORRECAO_NARRATIVA.value,
            TipoDocumento.ANALISE_HABILIDADES_NARRATIVA.value,
            TipoDocumento.RELATORIO_NARRATIVO.value,
        }

        colisoes = novos_valores & tipos_existentes_antes
        assert not colisoes, (
            f"Novos TipoDocumento colidem com tipos existentes: {colisoes}. "
            "Cada tipo deve ter um valor de string único no storage."
        )


class TestDocumentosGeradosInclueNarrativos:
    """
    F7-T3: documentos_gerados() deve incluir os 3 novos tipos narrativos.

    O método documentos_gerados() é usado pelo executor para determinar quais
    documentos são gerados pela IA. Se os novos tipos não estiverem nessa lista,
    o sistema não saberá que eles são documentos de IA e não os listará corretamente.
    """

    def test_documentos_gerados_inclui_correcao_narrativa(self):
        """documentos_gerados() deve incluir CORRECAO_NARRATIVA."""
        from models import TipoDocumento

        gerados = TipoDocumento.documentos_gerados()
        assert TipoDocumento.CORRECAO_NARRATIVA in gerados, (
            "CORRECAO_NARRATIVA não está em documentos_gerados(). "
            "O executor precisa saber que este é um documento gerado pela IA "
            "para listá-lo corretamente quando o professor consultar os documentos."
        )

    def test_documentos_gerados_inclui_analise_habilidades_narrativa(self):
        """documentos_gerados() deve incluir ANALISE_HABILIDADES_NARRATIVA."""
        from models import TipoDocumento

        gerados = TipoDocumento.documentos_gerados()
        assert TipoDocumento.ANALISE_HABILIDADES_NARRATIVA in gerados, (
            "ANALISE_HABILIDADES_NARRATIVA não está em documentos_gerados(). "
            "Este tipo precisa ser reconhecido como documento gerado pela IA."
        )

    def test_documentos_gerados_inclui_relatorio_narrativo(self):
        """documentos_gerados() deve incluir RELATORIO_NARRATIVO."""
        from models import TipoDocumento

        gerados = TipoDocumento.documentos_gerados()
        assert TipoDocumento.RELATORIO_NARRATIVO in gerados, (
            "RELATORIO_NARRATIVO não está em documentos_gerados(). "
            "O relatório holístico em Markdown deve ser listado como documento gerado."
        )

    def test_tipos_anteriores_preservados_em_documentos_gerados(self):
        """documentos_gerados() deve ainda incluir todos os tipos existentes antes de F7."""
        from models import TipoDocumento

        gerados = TipoDocumento.documentos_gerados()

        tipos_que_devem_continuar = [
            TipoDocumento.EXTRACAO_QUESTOES,
            TipoDocumento.EXTRACAO_GABARITO,
            TipoDocumento.EXTRACAO_RESPOSTAS,
            TipoDocumento.CORRECAO,
            TipoDocumento.ANALISE_HABILIDADES,
            TipoDocumento.RELATORIO_FINAL,
        ]

        for tipo in tipos_que_devem_continuar:
            assert tipo in gerados, (
                f"documentos_gerados() não inclui mais {tipo.value} — tipo existente removido. "
                "A adição de novos tipos não deve remover os existentes."
            )
