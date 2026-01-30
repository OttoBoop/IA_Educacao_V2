"""
Script de teste rápido para a API v2

Execute com: python test_api.py

Este script cria dados de exemplo para testar o sistema.
"""

import asyncio
import sys
sys.path.insert(0, '.')

from storage import StorageManager
from models import TipoDocumento, NivelEnsino

def test_storage():
    print("=" * 50)
    print("TESTE DO STORAGE V2")
    print("=" * 50)
    
    # Usar pasta temporária para teste
    storage = StorageManager("./data_teste")
    
    # 1. Criar matéria
    print("\n1. Criando matéria...")
    materia = storage.criar_materia("Matemática", "Matemática básica", NivelEnsino.FUNDAMENTAL_2)
    print(f"   ✓ Matéria criada: {materia.nome} (ID: {materia.id})")
    
    # 2. Criar turma
    print("\n2. Criando turma...")
    turma = storage.criar_turma(materia.id, "9º Ano A", ano_letivo=2024, periodo="Manhã")
    print(f"   ✓ Turma criada: {turma.nome} (ID: {turma.id})")
    
    # 3. Criar alunos
    print("\n3. Criando alunos...")
    aluno1 = storage.criar_aluno("João Silva", "joao@email.com", "2024001")
    aluno2 = storage.criar_aluno("Maria Santos", "maria@email.com", "2024002")
    print(f"   ✓ Aluno criado: {aluno1.nome}")
    print(f"   ✓ Aluno criado: {aluno2.nome}")
    
    # 4. Vincular alunos à turma
    print("\n4. Vinculando alunos à turma...")
    storage.vincular_aluno_turma(aluno1.id, turma.id)
    storage.vincular_aluno_turma(aluno2.id, turma.id)
    print(f"   ✓ Alunos vinculados")
    
    # 5. Criar atividade
    print("\n5. Criando atividade...")
    atividade = storage.criar_atividade(turma.id, "Prova 1 - Equações", tipo="prova", nota_maxima=10.0)
    print(f"   ✓ Atividade criada: {atividade.nome} (ID: {atividade.id})")
    
    # 6. Listar hierarquia
    print("\n6. Testando navegação hierárquica...")
    arvore = storage.get_arvore_navegacao()
    print(f"   ✓ Árvore gerada com {len(arvore['materias'])} matéria(s)")
    
    # 7. Verificar status da atividade
    print("\n7. Verificando status da atividade...")
    status = storage.get_status_atividade(atividade.id)
    print(f"   ✓ Documentos base faltando: {status['documentos_base']['faltando']}")
    print(f"   ✓ Total de alunos: {status['alunos']['total']}")
    
    # 8. Listar turmas do aluno
    print("\n8. Listando turmas do aluno...")
    turmas_aluno = storage.get_turmas_do_aluno(aluno1.id)
    print(f"   ✓ {aluno1.nome} está em {len(turmas_aluno)} turma(s)")
    for t in turmas_aluno:
        print(f"     - {t['materia_nome']} / {t['nome']}")
    
    print("\n" + "=" * 50)
    print("TODOS OS TESTES PASSARAM! ✓")
    print("=" * 50)
    
    # Limpar dados de teste
    import shutil
    shutil.rmtree("./data_teste", ignore_errors=True)
    print("\n(Dados de teste removidos)")

if __name__ == "__main__":
    test_storage()
