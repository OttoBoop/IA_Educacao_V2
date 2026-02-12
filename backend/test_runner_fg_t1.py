"""
Simple test runner for FG-T1 to avoid pytest capture issues
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from test_data_generator import TestDataGenerator

def test_vincular_alunos_turmas_propagates_db_error():
    """
    Test that DB errors propagate instead of being silently swallowed
    """
    # Setup mock storage
    mock_storage = MagicMock()
    mock_storage.vincular_aluno_turma = MagicMock(side_effect=RuntimeError("DB connection lost"))

    # Create generator with data
    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    # Create test alunos
    aluno1 = Mock()
    aluno1.id = "aluno-001"
    aluno1.nome = "Ana Silva"

    aluno2 = Mock()
    aluno2.id = "aluno-002"
    aluno2.nome = "Bruno Santos"

    generator.alunos_criados = [aluno1, aluno2]

    # Create test turmas
    turma1 = Mock()
    turma1.id = "turma-001"
    turma1.nome = "9º Ano A"

    turma2 = Mock()
    turma2.id = "turma-002"
    turma2.nome = "9º Ano B"

    generator.turmas_criadas = {
        "mat_9a": turma1,
        "mat_9b": turma2
    }

    # Try to run vincular_alunos_turmas
    print("\n[TEST] Running vincular_alunos_turmas() with DB error mock...")
    print("[TEST] Expected: RuntimeError should propagate")
    print("[TEST] Current bug: Exception is silently swallowed by bare except: pass\n")

    try:
        generator.vincular_alunos_turmas(alunos_por_turma=2)
        # If we get here, the exception was swallowed (BUG!)
        print("❌ FAILED: Exception was NOT raised (silently swallowed)")
        print("   This confirms the bug: bare except: pass is swallowing RuntimeError")
        return False
    except RuntimeError as e:
        # If we get here, the exception propagated (CORRECT!)
        print(f"✅ PASSED: RuntimeError propagated correctly: {e}")
        print("   The fix is working!")
        return True
    except Exception as e:
        print(f"❌ FAILED: Wrong exception type: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("FG-T1 RED PHASE TEST: Exception Propagation")
    print("=" * 70)

    result = test_vincular_alunos_turmas_propagates_db_error()

    print("\n" + "=" * 70)
    if result:
        print("TEST STATUS: PASSED (fix is working)")
        print("=" * 70)
        sys.exit(0)
    else:
        print("TEST STATUS: FAILED (bug exists - this is expected in RED phase)")
        print("=" * 70)
        sys.exit(1)
