"""
Script: inject_erro_pipeline.py
Injeta um resultado com _erro_pipeline em um aluno existente para testar
os indicadores de erro na UI (badge ERRO, banner, PDF error section).

Uso: python scripts/inject_erro_pipeline.py
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import storage
from models import TipoDocumento

TARGET_MATERIA = "Ciências"
TARGET_TURMA = "9º Ano A"
TARGET_ATIVIDADE = "Prova 1 - Sistema Solar"


def find_atividade():
    materias = storage.listar_materias()
    for m in materias:
        if m.nome == TARGET_MATERIA:
            turmas = storage.listar_turmas(m.id)
            for t in turmas:
                if t.nome == TARGET_TURMA:
                    atividades = storage.listar_atividades(t.id)
                    for a in atividades:
                        if a.nome == TARGET_ATIVIDADE:
                            return t, a
    return None, None


def main():
    print(f"\n{'='*60}")
    print("INJECT ERRO PIPELINE")
    print(f"{'='*60}")

    turma, atividade = find_atividade()
    if not atividade:
        print(f"ERRO: Não encontrei '{TARGET_MATERIA} > {TARGET_TURMA} > {TARGET_ATIVIDADE}'")
        sys.exit(1)

    print(f"[OK] Atividade: {atividade.nome} (id={atividade.id})")
    print(f"[OK] Turma:     {turma.nome} (id={turma.id})")

    alunos = storage.listar_alunos(turma.id)
    if not alunos:
        print("ERRO: Nenhum aluno encontrado na turma")
        sys.exit(1)

    # Pegar o primeiro aluno
    aluno = alunos[0]
    print(f"[OK] Aluno:     {aluno.nome} (id={aluno.id})")

    # Montar resultado com _erro_pipeline
    erro_pipeline = {
        "tipo": "documento_faltante",
        "mensagem": "Gabarito não encontrado para a atividade. O pipeline foi interrompido antes da correção.",
        "severidade": "critica",
        "etapa": "verificacao_pre_pipeline",
        "timestamp": datetime.now().isoformat()
    }

    resultado = {
        "atividade_id": atividade.id,
        "aluno_id": aluno.id,
        "aluno_nome": aluno.nome,
        "data_correcao": datetime.now().isoformat(),
        "_erro_pipeline": erro_pipeline,
        "questoes": [],
        "nota_total": None,
        "nota_maxima": atividade.nota_maxima,
        "ia_provider": "inject_script",
        "ia_modelo": "n/a",
    }

    # Salvar como arquivo temporário e depois no storage
    temp_path = Path(tempfile.gettempdir()) / f"erro_{atividade.id}_{aluno.id}.json"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    doc = storage.salvar_documento(
        arquivo_origem=str(temp_path),
        tipo=TipoDocumento.CORRECAO,
        atividade_id=atividade.id,
        aluno_id=aluno.id,
        ia_provider="inject_script",
        ia_modelo="n/a",
        criado_por="inject_erro_pipeline",
    )

    temp_path.unlink(missing_ok=True)

    if doc:
        print(f"\n[OK] Resultado com _erro_pipeline salvo!")
        print(f"     Documento ID: {doc.id}")
        print(f"\nAgora acesse na UI:")
        print(f"  {TARGET_MATERIA} > {TARGET_TURMA} > {TARGET_ATIVIDADE}")
        print(f"  Aluno: {aluno.nome}")
        print(f"  Esperado: badge ERRO vermelho na listagem + banner no detalhe")
    else:
        print("ERRO: salvar_documento retornou None")
        sys.exit(1)


if __name__ == "__main__":
    main()
