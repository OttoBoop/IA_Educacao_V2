"""Quick test of GERAR_RELATORIO stage."""
import asyncio
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ["PROVA_AI_DISABLE_LOCAL_LLM"] = "1"
os.environ["PROVA_AI_TESTING"] = "1"


async def test():
    from chat_service import ApiKeyManager, ProviderType
    from ai_providers import AnthropicProvider
    from prompts import PROMPTS_PADRAO, EtapaProcessamento

    api_keys_path = Path("data/api_keys.json")
    km = ApiKeyManager(config_path=str(api_keys_path))
    key = km.get_por_empresa(ProviderType.ANTHROPIC)
    provider = AnthropicProvider(api_key=key.api_key, model="claude-haiku-4-5-20251001")

    prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
    texto = prompt.render(
        nome_aluno="Diana Freitas Ramos",
        materia="Matematica",
        atividade="Prova 1 - Equacoes do 1 grau",
        correcoes=json.dumps([
            {"questao_numero": 1, "nota": 1.0, "nota_maxima": 2.0, "status": "parcial",
             "feedback": "Correta mas sem passo a passo", "narrativa_correcao": "Aluno resolveu corretamente mas omitiu o desenvolvimento."},
            {"questao_numero": 2, "nota": 2.0, "nota_maxima": 2.0, "status": "correta", "feedback": "Perfeita"},
            {"questao_numero": 3, "nota": 3.0, "nota_maxima": 3.0, "status": "correta", "feedback": "Perfeita"},
            {"questao_numero": 4, "nota": 3.0, "nota_maxima": 3.0, "status": "correta", "feedback": "Perfeita"},
        ], ensure_ascii=False),
        analise_habilidades=json.dumps({
            "resumo_desempenho": "Excelente dominio de algebra e geometria",
            "nota_final": 9.0,
            "narrativa_habilidades": "Diana demonstra dominio solido. Padrao de omissao de passos intermediarios.",
        }, ensure_ascii=False),
        nota_final="9.0",
    )

    print("Calling GERAR_RELATORIO...")
    response = await provider.complete(
        texto,
        system_prompt=prompt.texto_sistema,
        max_tokens=4096,
    )

    content = response.content.strip()
    # Try JSON extraction
    for marker in ["```json", "```"]:
        if marker in content:
            try:
                content = content.split(marker)[1].split("```")[0].strip()
                break
            except IndexError:
                pass

    try:
        parsed = json.loads(content)
        narrativa = parsed.get("relatorio_narrativo", "AUSENTE")
        print(f"relatorio_narrativo: {len(narrativa)} chars")
        print("---")
        print(narrativa.encode("ascii", errors="replace").decode("ascii"))
    except json.JSONDecodeError as e:
        print(f"JSON error: {e}")
        print(f"Raw (first 800 chars):")
        print(content[:800].encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    asyncio.run(test())
