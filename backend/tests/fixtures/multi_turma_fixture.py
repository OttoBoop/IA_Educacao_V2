"""
D0: Multi-turma test fixtures for Relatório de Desempenho scenario tests.

Provides synthetic RELATORIO_NARRATIVO .md content for ≥2 turmas,
simulating the output of the GERAR_RELATORIO pipeline stage.

These fixtures are used by S1 (Shared Scenario E2E for Feature C + D) to
test gerar_relatorio_desempenho_turma() and gerar_relatorio_desempenho_materia().

Usage:
    from tests.fixtures.multi_turma_fixture import criar_cenario_multi_turma

    cenario = criar_cenario_multi_turma()
    # cenario['materia_id'], cenario['turmas'][0]['turma_id'], ...
"""

import uuid
from typing import Dict, Any, List


# ============================================================
# SYNTHETIC RELATORIO_NARRATIVO CONTENT
# (Mimics real pipeline output from GERAR_RELATORIO stage)
# ============================================================

def _relatorio_narrativo_aluno(nome: str, turma: str, materia: str, desempenho: str) -> str:
    """Generate a realistic RELATORIO_NARRATIVO markdown for one student."""
    if desempenho == "excelente":
        resumo = f"demonstrou excelente domínio dos conceitos de {materia}"
        questoes = (
            "**Q1:** Respondeu corretamente, com raciocínio completo e bem estruturado.\n"
            "**Q2:** Solução correta. Demonstrou uso eficiente da fórmula aprendida.\n"
            "**Q3:** Resposta perfeita. Interpretou o enunciado com precisão.\n"
            "**Q4:** Correto, incluindo a unidade de medida e verificação do resultado."
        )
        habilidades = (
            f"{nome} demonstra consistência na aplicação de algoritmos e boa capacidade de "
            "abstração. Raras omissões, geralmente de natureza formal (sinais, unidades). "
            "Aluno com perfil autônomo — beneficia-se de desafios além do currículo padrão."
        )
        recomendacao = "Manter o nível. Desafiar com questões discursivas mais abertas."
    elif desempenho == "bom":
        resumo = f"apresentou bom desempenho geral em {materia}, com algumas lacunas pontuais"
        questoes = (
            "**Q1:** Correto. Algoritmo aplicado sem erros.\n"
            "**Q2:** Parcialmente correto — erro na etapa final do cálculo.\n"
            "**Q3:** Correto, mas sem justificativa detalhada.\n"
            "**Q4:** Resposta correta, mas unidade de medida omitida."
        )
        habilidades = (
            f"{nome} demonstra compreensão dos conceitos centrais, mas apresenta erros "
            "procedimentais em etapas intermediárias. Padrão de erro: precipitação na "
            "etapa final antes de verificar o resultado."
        )
        recomendacao = "Reforçar o hábito de revisão. Exercícios com etapas intermediárias explícitas."
    else:  # médio/ruim
        resumo = f"apresentou dificuldades significativas com os conceitos de {materia}"
        questoes = (
            "**Q1:** Tentativa sem sucesso — processo correto mas resultado errado.\n"
            "**Q2:** Resposta em branco.\n"
            "**Q3:** Método incorreto aplicado.\n"
            "**Q4:** Parcialmente correto — acertou a primeira etapa."
        )
        habilidades = (
            f"{nome} demonstra dificuldade com a representação formal dos conceitos. "
            "Há compreensão intuitiva em alguns casos, mas falta consolidação do algoritmo. "
            "Padrão de erro: confusão entre operações relacionadas (e.g., adição e multiplicação)."
        )
        recomendacao = "Atividades de reforço focadas nos algoritmos básicos. Revisão dos pré-requisitos."

    return f"""# Relatório de Desempenho Individual — {nome}

**Turma:** {turma}
**Matéria:** {materia}
**Data:** 2026-02-20

---

## Resumo Executivo

{nome} {resumo} nesta avaliação.

---

## Análise por Questão

{questoes}

---

## Perfil de Habilidades

{habilidades}

---

## Recomendação Pedagógica

{recomendacao}
"""


# ============================================================
# MULTI-TURMA SCENARIO DATA
# ============================================================

MATERIA = "Matemática"
MATERIA_ID = "fixture-materia-matematica-001"

TURMAS = [
    {
        "nome": "8º Ano A",
        "turma_id": "fixture-turma-8a-001",
        "alunos": [
            {"nome": "Ana Silva",        "aluno_id": "fixture-aluno-ana-001",     "desempenho": "excelente"},
            {"nome": "Bruno Santos",     "aluno_id": "fixture-aluno-bruno-001",   "desempenho": "bom"},
            {"nome": "Carla Oliveira",   "aluno_id": "fixture-aluno-carla-001",   "desempenho": "médio"},
        ],
    },
    {
        "nome": "8º Ano B",
        "turma_id": "fixture-turma-8b-001",
        "alunos": [
            {"nome": "Daniel Costa",     "aluno_id": "fixture-aluno-daniel-001",  "desempenho": "bom"},
            {"nome": "Elena Ferreira",   "aluno_id": "fixture-aluno-elena-001",   "desempenho": "excelente"},
            {"nome": "Felipe Rodrigues", "aluno_id": "fixture-aluno-felipe-001",  "desempenho": "médio"},
        ],
    },
]

# One shared atividade for both turmas
ATIVIDADE_ID = "fixture-atividade-prova1-001"


def criar_cenario_multi_turma() -> Dict[str, Any]:
    """
    Returns a complete multi-turma scenario with synthetic RELATORIO_NARRATIVO docs.

    Structure:
        {
            "materia": "Matemática",
            "materia_id": "fixture-...",
            "atividade_id": "fixture-...",
            "turmas": [
                {
                    "nome": "8º Ano A",
                    "turma_id": "fixture-...",
                    "alunos": [
                        {
                            "nome": "Ana Silva",
                            "aluno_id": "fixture-...",
                            "desempenho": "excelente",
                            "relatorio_narrativo": "# Relatório...",
                        },
                        ...
                    ]
                },
                ...
            ]
        }
    """
    turmas_com_docs = []

    for turma_info in TURMAS:
        alunos_com_docs = []
        for aluno in turma_info["alunos"]:
            relatorio = _relatorio_narrativo_aluno(
                nome=aluno["nome"],
                turma=turma_info["nome"],
                materia=MATERIA,
                desempenho=aluno["desempenho"],
            )
            alunos_com_docs.append({
                **aluno,
                "relatorio_narrativo": relatorio,
            })

        turmas_com_docs.append({
            "nome": turma_info["nome"],
            "turma_id": turma_info["turma_id"],
            "alunos": alunos_com_docs,
        })

    return {
        "materia": MATERIA,
        "materia_id": MATERIA_ID,
        "atividade_id": ATIVIDADE_ID,
        "turmas": turmas_com_docs,
    }


def get_all_relatorio_narrativos(cenario: Dict[str, Any]) -> List[str]:
    """Extract all RELATORIO_NARRATIVO texts from the cenario."""
    narrativos = []
    for turma in cenario["turmas"]:
        for aluno in turma["alunos"]:
            narrativos.append(aluno["relatorio_narrativo"])
    return narrativos


def get_turma_narrativos(cenario: Dict[str, Any], turma_id: str) -> List[str]:
    """Extract RELATORIO_NARRATIVO texts for a specific turma."""
    for turma in cenario["turmas"]:
        if turma["turma_id"] == turma_id:
            return [a["relatorio_narrativo"] for a in turma["alunos"]]
    return []


# ============================================================
# QUICK VALIDATION — run as script to inspect fixtures
# ============================================================

if __name__ == "__main__":
    cenario = criar_cenario_multi_turma()
    print(f"Matéria: {cenario['materia']} ({cenario['materia_id']})")
    print(f"Atividade ID: {cenario['atividade_id']}")
    print(f"Turmas: {len(cenario['turmas'])}")
    for turma in cenario["turmas"]:
        print(f"\n  Turma: {turma['nome']} ({turma['turma_id']})")
        print(f"  Alunos: {len(turma['alunos'])}")
        for aluno in turma["alunos"]:
            print(f"    - {aluno['nome']} ({aluno['desempenho']}): {len(aluno['relatorio_narrativo'])} chars")

    all_narrativos = get_all_relatorio_narrativos(cenario)
    print(f"\nTotal RELATORIO_NARRATIVO docs: {len(all_narrativos)}")
    print("Sample (first 300 chars of first doc):")
    print(all_narrativos[0][:300])
