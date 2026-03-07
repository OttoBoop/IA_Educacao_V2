"""
F9-T1 -- Demo E2E: Verificacao de Narrativa com Dados Reais

Runs CORRIGIR (per-question) + ANALISAR_HABILIDADES + GERAR_RELATORIO stages
with the new narrative prompts against real local prova data.

Usage (from backend/):
    python demo_e2e_narrativa.py
"""
import asyncio
import json
import sys
import os
from pathlib import Path

# Setup path and encoding
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("PROVA_AI_DISABLE_LOCAL_LLM", "1")
os.environ.setdefault("PROVA_AI_TESTING", "1")

# Real exam data
QUESTOES = [
    {
        "numero": 1,
        "questao": "Resolva a equacao: 3x + 7 = 22",
        "resposta_esperada": "x = 5",
        "criterios": "Demonstrar o passo a passo. Resposta correta sem desenvolvimento: 1,0 ponto.",
        "nota_maxima": 2.0,
        "tipo_raciocinio": "aplicacao",
        "resposta_aluno": "x = 5",
    },
    {
        "numero": 2,
        "questao": "Calcule a area de um triangulo com base 8cm e altura 5cm.",
        "resposta_esperada": "Area = 20 cm2",
        "criterios": "Uso correto da formula. Unidades corretas.",
        "nota_maxima": 2.0,
        "tipo_raciocinio": "aplicacao",
        "resposta_aluno": "Area = 20 cm2",
    },
    {
        "numero": 3,
        "questao": "Um produto custa R$ 150,00 e esta com 20% de desconto. Qual o valor final?",
        "resposta_esperada": "R$ 120,00",
        "criterios": "Raciocinio logico (1,5), calculo correto (1,5).",
        "nota_maxima": 3.0,
        "tipo_raciocinio": "aplicacao",
        "resposta_aluno": "R$ 120,00",
    },
    {
        "numero": 4,
        "questao": "Simplifique a fracao 48/64 ate sua forma irredutivel.",
        "resposta_esperada": "3/4",
        "criterios": "Explicacao clara e completa.",
        "nota_maxima": 3.0,
        "tipo_raciocinio": "analise",
        "resposta_aluno": "3/4",
    },
]

NOME_ALUNO = "Diana Freitas Ramos"
MATERIA = "Matematica"
ATIVIDADE = "Prova 1 - Equacoes do 1 grau"


def print_section(title, content):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")
    print(content.encode('ascii', errors='replace').decode('ascii'))


async def run_corrigir_questao(provider, q):
    """Run CORRIGIR for a single question."""
    from prompts import PROMPTS_PADRAO, EtapaProcessamento

    prompt = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR]
    texto = prompt.render(
        questao=q["questao"],
        resposta_esperada=q["resposta_esperada"],
        resposta_aluno=q["resposta_aluno"],
        criterios=q["criterios"],
        nota_maxima=str(q["nota_maxima"]),
    )

    response = await provider.complete(
        texto,
        max_tokens=1500,
        system_prompt=prompt.texto_sistema,
    )

    content = response.content.strip()
    for marker in ["```json", "```"]:
        if marker in content:
            try:
                content = content.split(marker)[1].split("```")[0].strip()
                break
            except IndexError:
                pass

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"nota": 0.0, "nota_maxima": q["nota_maxima"], "raw": content[:200]}


async def run_analisar_habilidades(provider, correcoes_json):
    """Run ANALISAR_HABILIDADES with per-question corrections."""
    from prompts import PROMPTS_PADRAO, EtapaProcessamento

    prompt = PROMPTS_PADRAO[EtapaProcessamento.ANALISAR_HABILIDADES]
    texto = prompt.render(
        correcoes=json.dumps(correcoes_json, ensure_ascii=False, indent=2),
        nome_aluno=NOME_ALUNO,
        materia=MATERIA,
    )

    response = await provider.complete(
        texto,
        max_tokens=2000,
        system_prompt=prompt.texto_sistema,
    )

    content = response.content.strip()
    for marker in ["```json", "```"]:
        if marker in content:
            try:
                content = content.split(marker)[1].split("```")[0].strip()
                break
            except IndexError:
                pass

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw": content[:200]}


async def run_gerar_relatorio(provider, correcoes_json, analise_json):
    """Run GERAR_RELATORIO with full pipeline data."""
    from prompts import PROMPTS_PADRAO, EtapaProcessamento

    prompt = PROMPTS_PADRAO[EtapaProcessamento.GERAR_RELATORIO]
    nota_final = sum(c.get("nota", 0.0) for c in correcoes_json)

    texto = prompt.render(
        nome_aluno=NOME_ALUNO,
        materia=MATERIA,
        atividade=ATIVIDADE,
        correcoes=json.dumps(correcoes_json, ensure_ascii=False, indent=2),
        analise_habilidades=json.dumps(analise_json, ensure_ascii=False, indent=2),
        nota_final=str(nota_final),
    )

    response = await provider.complete(
        texto,
        max_tokens=3000,
        system_prompt=prompt.texto_sistema,
    )

    content = response.content.strip()
    for marker in ["```json", "```"]:
        if marker in content:
            try:
                content = content.split(marker)[1].split("```")[0].strip()
                break
            except IndexError:
                pass

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [GERAR_RELATORIO JSON parse error: {e}]")
        print(f"  [Raw preview: {content[:300]}]")
        return {"raw": content[:500], "relatorio_narrativo": content[:2000] if "relatorio_narrativo" in content else ""}


async def main():
    print("\nF9-T1 -- Demo E2E: Verificacao de Narrativa com Dados Reais")
    print(f"Aluno: {NOME_ALUNO} | Materia: {MATERIA} | {len(QUESTOES)} questoes")

    # Load AI provider
    try:
        from chat_service import ApiKeyManager, ProviderType
        from ai_providers import AnthropicProvider, OpenAIProvider

        api_keys_path = Path(__file__).parent / "data" / "api_keys.json"
        key_manager = ApiKeyManager(config_path=str(api_keys_path))

        anthropic_key = key_manager.get_por_empresa(ProviderType.ANTHROPIC)
        openai_key = key_manager.get_por_empresa(ProviderType.OPENAI)

        if anthropic_key:
            provider = AnthropicProvider(api_key=anthropic_key.api_key, model="claude-haiku-4-5-20251001")
            print("Provider: Anthropic claude-haiku-4-5-20251001")
        elif openai_key:
            provider = OpenAIProvider(api_key=openai_key.api_key, model="gpt-5-mini")
            print("Provider: OpenAI gpt-5-mini")
        else:
            print("ERRO: Nenhum provider disponivel. Configure api_keys.json.")
            return

    except Exception as e:
        print(f"ERRO ao carregar provider: {e}")
        return

    # ----------------------------------------------------------------
    # Stage 1: CORRIGIR (once per question)
    # ----------------------------------------------------------------
    print(f"\n--- STAGE 1: CORRIGIR ({len(QUESTOES)} questoes) ---")
    correcoes = []
    for q in QUESTOES:
        print(f"  Corrigindo Q{q['numero']}...", end=" ", flush=True)
        resultado = await run_corrigir_questao(provider, q)
        resultado["questao_numero"] = q["numero"]
        correcoes.append(resultado)
        narrativa = resultado.get("narrativa_correcao", "")
        nota = resultado.get("nota", "?")
        print(f"nota={nota}/{q['nota_maxima']} | narrativa: {'OK (' + str(len(narrativa)) + ' chars)' if narrativa else 'AUSENTE'}")

    print_section(
        "NARRATIVA_CORRECAO Q1 (campo extraido do CORRIGIR)",
        correcoes[0].get("narrativa_correcao", "AUSENTE")
    )

    # ----------------------------------------------------------------
    # Stage 2: ANALISAR_HABILIDADES
    # ----------------------------------------------------------------
    print("\n--- STAGE 2: ANALISAR_HABILIDADES ---")
    analise = await run_analisar_habilidades(provider, correcoes)
    narrativa_hab = analise.get("narrativa_habilidades", "AUSENTE")
    print(f"  narrativa_habilidades: {'OK (' + str(len(narrativa_hab)) + ' chars)' if narrativa_hab != 'AUSENTE' else 'AUSENTE'}")
    print_section("NARRATIVA_HABILIDADES (campo extraido)", narrativa_hab)

    # ----------------------------------------------------------------
    # Stage 3: GERAR_RELATORIO
    # ----------------------------------------------------------------
    print("\n--- STAGE 3: GERAR_RELATORIO ---")
    relatorio = await run_gerar_relatorio(provider, correcoes, analise)
    narrativa_rel = relatorio.get("relatorio_narrativo", "AUSENTE")
    print(f"  relatorio_narrativo: {'OK (' + str(len(narrativa_rel)) + ' chars)' if narrativa_rel != 'AUSENTE' else 'AUSENTE'}")
    print_section("RELATORIO_NARRATIVO (campo extraido)", narrativa_rel)

    # ----------------------------------------------------------------
    # Summary
    # ----------------------------------------------------------------
    nota_total = sum(c.get("nota", 0.0) for c in correcoes)
    nota_max = sum(q["nota_maxima"] for q in QUESTOES)

    print(f"""
{'='*70}
  RESUMO F9-T1 E2E
{'='*70}
  Aluno: {NOME_ALUNO}
  Nota: {nota_total}/{nota_max}
  narrativa_correcao (Q1): {'PRESENTE' if correcoes[0].get('narrativa_correcao') else 'AUSENTE'}
  narrativa_habilidades:   {'PRESENTE' if analise.get('narrativa_habilidades') else 'AUSENTE'}
  relatorio_narrativo:     {'PRESENTE' if relatorio.get('relatorio_narrativo') else 'AUSENTE'}

  Verifique acima se as narrativas sao ricas (nao checklists).
  Se PRESENTE e rico -> F9-T1 aprovado para deploy.
{'='*70}""")


if __name__ == "__main__":
    asyncio.run(main())
