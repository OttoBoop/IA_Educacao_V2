"""Guards against prompts that induce fenced JSON in pipeline stages."""


def test_default_pipeline_json_prompts_do_not_show_markdown_fences():
    from prompts import EtapaProcessamento, PROMPTS_PADRAO

    stages = [
        EtapaProcessamento.EXTRAIR_QUESTOES,
        EtapaProcessamento.EXTRAIR_GABARITO,
        EtapaProcessamento.EXTRAIR_RESPOSTAS,
        EtapaProcessamento.CORRIGIR,
        EtapaProcessamento.ANALISAR_HABILIDADES,
        EtapaProcessamento.GERAR_RELATORIO,
    ]

    for stage in stages:
        prompt = PROMPTS_PADRAO[stage]
        assert "```json" not in prompt.texto
        assert "formatação Markdown" in prompt.texto or "cercas Markdown" in prompt.texto
