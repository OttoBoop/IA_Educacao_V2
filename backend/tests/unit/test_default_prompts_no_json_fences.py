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


def test_validation_retry_prompt_does_not_reintroduce_markdown_fences():
    from executor import PipelineExecutor
    from prompts import EtapaProcessamento

    executor = PipelineExecutor.__new__(PipelineExecutor)
    retry_prompt = executor._montar_prompt_retry_validacao_multimodal(
        etapa=EtapaProcessamento.EXTRAIR_GABARITO,
        prompt_original="Retorne apenas JSON cru.",
        erro="JSON veio envelopado em Markdown.",
        resposta_raw='```json\n{"respostas": []}\n```',
    )

    assert "```" not in retry_prompt
    assert "[cerca Markdown removida]" in retry_prompt
    assert "primeira caractere da resposta deve ser {" in retry_prompt
