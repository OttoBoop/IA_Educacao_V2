"""
PROVA AI - Testes para TestDataGenerator (Fantasy Data Generator)

Este arquivo testa o comportamento do gerador de dados de teste,
especialmente casos de erro que devem propagar excecoes ao inves de
serem silenciosamente ignorados.

===============================================================================
BUG: Silent Error Swallowing em vincular_alunos_turmas() (FG-T1)
===============================================================================

PROBLEMA:
    O metodo vincular_alunos_turmas() em test_data_generator.py (linha 432)
    usa um bare `except: pass` que silenciosamente captura TODAS as excecoes,
    incluindo erros de banco de dados reais.

CODIGO ATUAL (linhas 427-433):
    for aluno in alunos_serie:
        for key, turma in turmas_serie:
            try:
                self.storage.vincular_aluno_turma(aluno.id, turma.id)
                self.stats["vinculos"] += 1
            except:
                pass  # Ignora se já vinculado

IMPACTO:
    - Erros reais de DB (connection lost, constraint violation, etc) sao
      silenciosamente ignorados
    - O gerador parece funcionar mas deixa dados inconsistentes
    - Debugging e muito dificil (sem logs, sem stack trace)
    - Viola principio "fail fast, fail loud"

SOLUCAO ESPERADA:
    - Capturar APENAS excecoes especificas (DuplicateKeyError, IntegrityError)
    - Deixar outras excecoes propagarem para o caller
    - Adicionar logging quando uma excecao e legitimamente ignorada

===============================================================================

Uso:
    cd IA_Educacao_V2/backend
    pytest tests/unit/test_generator.py -v -k "vincular"
"""

import pytest
from unittest.mock import MagicMock, Mock, patch, call
from pathlib import Path
import sys
import tempfile

# Adicionar diretorio backend ao path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from test_data_generator import TestDataGenerator


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def mock_storage():
    """Mock do StorageManager para isolar testes"""
    storage = MagicMock()
    storage.vincular_aluno_turma = MagicMock()
    return storage


@pytest.fixture
def generator_with_data(mock_storage):
    """
    Cria um TestDataGenerator com dados pre-populados
    (turmas e alunos) para testar vincular_alunos_turmas()
    """
    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    # Criar alunos fictícios
    aluno1 = Mock()
    aluno1.id = "aluno-001"
    aluno1.nome = "Ana Silva"

    aluno2 = Mock()
    aluno2.id = "aluno-002"
    aluno2.nome = "Bruno Santos"

    generator.alunos_criados = [aluno1, aluno2]

    # Criar turmas fictícias (mesma série)
    turma1 = Mock()
    turma1.id = "turma-001"
    turma1.nome = "9º Ano A"

    turma2 = Mock()
    turma2.id = "turma-002"
    turma2.nome = "9º Ano B"

    # turmas_criadas é um dict de key -> turma
    generator.turmas_criadas = {
        "mat_9a": turma1,
        "mat_9b": turma2
    }

    return generator


# ============================================================
# TESTES - RED PHASE (DEVE FALHAR)
# ============================================================

def test_vincular_alunos_turmas_propagates_db_error(generator_with_data, mock_storage):
    """
    RED PHASE TEST (FG-T1):
    Verifica que excecoes de DB propagam ao inves de serem silenciosamente ignoradas.

    COMPORTAMENTO ATUAL (BUG):
        - vincular_aluno_turma() lanca RuntimeError("DB connection lost")
        - O except: pass silenciosamente captura a excecao
        - vincular_alunos_turmas() completa sem erros
        - Este teste FALHA porque nao captura a excecao esperada

    COMPORTAMENTO ESPERADO (APOS FIX):
        - vincular_aluno_turma() lanca RuntimeError("DB connection lost")
        - A excecao NAO e capturada (ou apenas excecoes especificas sao capturadas)
        - A excecao propaga para o caller
        - Este teste PASSA porque a excecao e capturada por pytest.raises

    COMO RODAR:
        cd IA_Educacao_V2/backend
        pytest tests/unit/test_generator.py::test_vincular_alunos_turmas_propagates_db_error -v

    EXPECTATIVA:
        Este teste DEVE FALHAR ate que o bare except: pass seja corrigido
    """
    # Arrange: Configurar mock para simular erro de DB real
    mock_storage.vincular_aluno_turma.side_effect = RuntimeError("DB connection lost")

    # Act & Assert: Verificar que a excecao propaga
    with pytest.raises(RuntimeError, match="DB connection lost"):
        generator_with_data.vincular_alunos_turmas(alunos_por_turma=2)


def test_vincular_alunos_turmas_propagates_type_error(generator_with_data, mock_storage):
    """
    RED PHASE TEST (FG-T1 - caso alternativo):
    Verifica que TypeErrors (ex: argumento invalido) propagam ao inves de serem ignorados.

    CENARIO:
        - vincular_aluno_turma recebe argumento com tipo errado
        - Lanca TypeError
        - O except: pass captura e ignora
        - O bug continua silencioso

    EXPECTATIVA:
        Este teste DEVE FALHAR ate que o bare except: pass seja corrigido
    """
    # Arrange: Simular TypeError (ex: API mudou e agora requer parametro extra)
    mock_storage.vincular_aluno_turma.side_effect = TypeError("vincular_aluno_turma() missing 1 required positional argument: 'role'")

    # Act & Assert: Verificar que a excecao propaga
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        generator_with_data.vincular_alunos_turmas(alunos_por_turma=2)


def test_vincular_alunos_turmas_propagates_attribute_error(generator_with_data, mock_storage):
    """
    RED PHASE TEST (FG-T1 - caso alternativo):
    Verifica que AttributeErrors (ex: objeto aluno sem .id) propagam.

    CENARIO:
        - Aluno ficticio esta mal formado (sem atributo .id)
        - vincular_aluno_turma tenta acessar aluno.id -> AttributeError
        - O except: pass captura e ignora
        - Dados inconsistentes (alguns alunos vinculados, outros nao)

    EXPECTATIVA:
        Este teste DEVE FALHAR ate que o bare except: pass seja corrigido
    """
    # Arrange: Criar aluno mal formado (sem .id)
    aluno_broken = Mock(spec=[])  # Mock vazio, sem atributos
    generator_with_data.alunos_criados = [aluno_broken]

    mock_storage.vincular_aluno_turma.return_value = None  # Nao importa, nunca sera chamado

    # Act & Assert: Verificar que a excecao propaga
    with pytest.raises(AttributeError, match="'id'"):
        generator_with_data.vincular_alunos_turmas(alunos_por_turma=1)


# ============================================================
# TESTES COMPLEMENTARES (nao relacionados ao bug)
# ============================================================

def test_vincular_alunos_turmas_success_case(generator_with_data, mock_storage):
    """
    Teste de SUCESSO: Verifica comportamento correto quando nao ha erros.

    Este teste deve passar ANTES e DEPOIS do fix (nao e afetado pelo bug).
    """
    # Arrange: Mock retorna sucesso
    mock_storage.vincular_aluno_turma.return_value = None

    # Act
    generator_with_data.vincular_alunos_turmas(alunos_por_turma=2)

    # Assert: Verificar que vincular_aluno_turma foi chamado
    # 2 alunos * 2 turmas = 4 vinculos
    assert mock_storage.vincular_aluno_turma.call_count == 4

    # Verificar estatisticas
    assert generator_with_data.stats["vinculos"] == 4


def test_generator_initialization(mock_storage):
    """
    Teste basico: Verificar que o generator inicializa corretamente.
    """
    # Act
    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    # Assert
    assert generator.storage == mock_storage
    assert generator.verbose is False
    assert generator.alunos_criados == []
    assert generator.turmas_criadas == {}
    assert generator.stats["vinculos"] == 0


# ============================================================
# TESTES FG-T2: Cross-platform temp paths
# ============================================================

def test_no_hardcoded_tmp_paths():
    """
    FG-T2: Verifica que test_data_generator.py nao usa /tmp/ hardcoded.

    O codigo deve usar tempfile.gettempdir() para ser cross-platform
    (funciona em Windows, Linux, macOS).
    """
    import inspect
    from test_data_generator import TestDataGenerator

    source = inspect.getsource(TestDataGenerator)

    # Nao deve conter /tmp/ hardcoded
    assert "/tmp/" not in source, (
        "test_data_generator.py still contains hardcoded /tmp/ paths. "
        "Use tempfile.gettempdir() for cross-platform compatibility."
    )


# ============================================================
# TESTES FG-T3: Exception propagation in creation methods
# ============================================================

def test_no_silent_exception_swallowing():
    """
    FG-T3: Verifica que creation methods nao engolem excecoes silenciosamente.

    Todas as excecoes em metodos de criacao devem propagar (re-raise)
    ao inves de serem apenas logadas.
    """
    import inspect
    import re
    from test_data_generator import TestDataGenerator

    source = inspect.getsource(TestDataGenerator)

    # Find except blocks that log but don't re-raise
    # Match: "except Exception as e:" followed by lines until next dedent
    lines = source.split('\n')
    swallowed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if 'except Exception as e:' in stripped:
            # Capture the except block (indented lines after except)
            except_indent = len(line) - len(line.lstrip())
            block_lines = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if next_line.strip() == '':
                    j += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= except_indent:
                    break
                block_lines.append(next_line.strip())
                j += 1
            block_text = ' '.join(block_lines)
            if 'raise' not in block_text:
                swallowed.append(block_text)
            i = j
        else:
            i += 1

    assert len(swallowed) == 0, (
        f"Found {len(swallowed)} except blocks that swallow exceptions silently "
        f"(log without re-raise). Each 'except Exception as e' must re-raise: "
        f"{swallowed}"
    )


def test_criar_documentos_base_propagates_error(generator_with_data, mock_storage):
    """
    FG-T3: Verifica que criar_documentos_base() propaga excecoes de storage.
    """
    # Setup: criar atividade mock
    atividade = Mock()
    atividade.id = "ativ-001"
    atividade.nome = "Prova 1"

    materia = Mock()
    materia.nome = "Matematica"

    turma = Mock()
    turma.nome = "9A"

    generator_with_data.atividades_criadas = {
        "ativ-001": {
            "atividade": atividade,
            "materia": materia,
            "turma": turma
        }
    }

    # Arrange: salvar_documento raises
    mock_storage.salvar_documento.side_effect = RuntimeError("DB connection lost")

    # Act & Assert: excecao propaga
    with pytest.raises(RuntimeError, match="DB connection lost"):
        generator_with_data.criar_documentos_base(incluir_problemas=False)


# ============================================================
# TESTES FG-T4: Smaller default dataset config
# ============================================================

def test_default_dataset_is_small():
    """
    FG-T4: Verifica que o dataset padrao e menor (2-3 materias, ~10 alunos).

    O gerador deve ser rapido para startup em Render e produzir
    dados suficientes para demonstracao sem ser excessivo.
    """
    from test_data_generator import MATERIAS_CONFIG_MINI

    # No maximo 3 materias
    assert len(MATERIAS_CONFIG_MINI) <= 3, (
        f"MATERIAS_CONFIG_MINI has {len(MATERIAS_CONFIG_MINI)} materias, expected <= 3"
    )

    # Cada materia tem pelo menos 1 turma e 1 atividade
    for config in MATERIAS_CONFIG_MINI:
        assert len(config["turmas"]) >= 1
        assert len(config["atividades"]) >= 1

    # Total de turmas <= 4
    total_turmas = sum(len(c["turmas"]) for c in MATERIAS_CONFIG_MINI)
    assert total_turmas <= 4, f"Too many turmas: {total_turmas}"


def test_gerar_tudo_uses_mini_config_by_default(mock_storage):
    """
    FG-T4: Verifica que gerar_tudo() usa MATERIAS_CONFIG_MINI por padrao.
    """
    from test_data_generator import TestDataGenerator, MATERIAS_CONFIG_MINI

    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    # gerar_tudo sem materias_config deve usar MATERIAS_CONFIG_MINI
    # We just check the default parameter
    import inspect
    sig = inspect.signature(generator.gerar_tudo)
    defaults = {
        name: param.default
        for name, param in sig.parameters.items()
        if param.default is not inspect.Parameter.empty
    }

    # Default num_alunos should be <= 10
    assert defaults["num_alunos"] <= 10, (
        f"Default num_alunos is {defaults['num_alunos']}, expected <= 10"
    )

    # Default alunos_por_turma should be <= 5
    assert defaults["alunos_por_turma"] <= 5, (
        f"Default alunos_por_turma is {defaults['alunos_por_turma']}, expected <= 5"
    )


def test_criar_provas_alunos_propagates_error(generator_with_data, mock_storage):
    """
    FG-T3: Verifica que criar_provas_alunos() propaga excecoes de storage.
    """
    # Setup: criar_provas_alunos() looks up turma via f"{materia}_{turma_nome}"
    # where materia=ativ_info["materia"] and turma_nome=ativ_info["turma"]
    # So we need turmas_criadas key to match that pattern
    materia_name = "Matematica"
    turma_name = "9A"

    atividade = Mock()
    atividade.id = "ativ-001"
    atividade.nome = "Prova 1"

    turma = Mock()
    turma.id = "turma-001"
    turma.nome = turma_name

    # Key must match f"{materia}_{turma_nome}" = "Matematica_9A"
    generator_with_data.turmas_criadas = {
        f"{materia_name}_{turma_name}": turma
    }

    generator_with_data.atividades_criadas = {
        "ativ-001": {
            "atividade": atividade,
            "materia": materia_name,
            "turma": turma_name
        }
    }

    # Mock listar_alunos para retornar nossos alunos
    aluno = Mock()
    aluno.id = "aluno-001"
    aluno.nome = "Ana Silva"
    mock_storage.listar_alunos.return_value = [aluno]

    # Arrange: salvar_documento raises
    mock_storage.salvar_documento.side_effect = RuntimeError("Storage full")

    # Act & Assert
    with pytest.raises(RuntimeError, match="Storage full"):
        generator_with_data.criar_provas_alunos(incluir_problemas=False)


# ============================================================
# TESTES FG-T5: Fantasy data tagging
# ============================================================

def test_criar_materias_tags_metadata(mock_storage):
    """
    FG-T5: Verifica que materias criadas pelo generator recebem
    metadata com criado_por='test_generator'.
    """
    from test_data_generator import TestDataGenerator, MATERIAS_CONFIG_MINI

    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    # Mock criar_materia to return a materia-like object
    materia = Mock()
    materia.id = "mat-001"
    materia.nome = "Matematica"
    materia.metadata = {}
    mock_storage.criar_materia.return_value = materia

    # Mock criar_turma and criar_atividade to avoid side effects
    turma = Mock()
    turma.id = "turma-001"
    turma.nome = "9A"
    mock_storage.criar_turma.return_value = turma
    mock_storage.criar_atividade.return_value = Mock(id="ativ-001", nome="Prova")

    generator.criar_materias([{
        "nome": "Matematica",
        "descricao": "Test",
        "turmas": ["9A"],
        "atividades": [{"nome": "Prova", "tipo": "prova"}]
    }])

    # Assert: atualizar_materia was called with metadata tagging
    mock_storage.atualizar_materia.assert_called_once_with(
        "mat-001", metadata={"criado_por": "test_generator"}
    )


def test_criar_alunos_tags_metadata(mock_storage):
    """
    FG-T5: Verifica que alunos criados pelo generator recebem
    metadata com criado_por='test_generator'.
    """
    from test_data_generator import TestDataGenerator

    generator = TestDataGenerator(storage=mock_storage, verbose=False)

    aluno = Mock()
    aluno.id = "aluno-001"
    aluno.nome = "Ana Silva"
    aluno.metadata = {}
    mock_storage.criar_aluno.return_value = aluno

    generator.criar_alunos(quantidade=1)

    # Assert: atualizar_aluno was called with metadata tagging
    mock_storage.atualizar_aluno.assert_called_once_with(
        "aluno-001", metadata={"criado_por": "test_generator"}
    )


# ============================================================
# TESTES FG-T7: Fantasy data cleanup
# ============================================================

def test_limpar_dados_fantasy_exists():
    """
    FG-T7: Verifica que a funcao limpar_dados_fantasy existe.
    """
    from test_data_generator import limpar_dados_fantasy
    assert callable(limpar_dados_fantasy)


def test_limpar_dados_fantasy_deletes_tagged_materias(mock_storage):
    """
    FG-T7: Verifica que limpar_dados_fantasy deleta materias
    com metadata criado_por='test_generator'.
    """
    from test_data_generator import limpar_dados_fantasy

    # Mock listar_materias to return mix of fantasy and user data
    materia_fantasy = Mock()
    materia_fantasy.id = "mat-fantasy"
    materia_fantasy.nome = "Matematica"
    materia_fantasy.metadata = {"criado_por": "test_generator"}

    materia_user = Mock()
    materia_user.id = "mat-user"
    materia_user.nome = "Econometria"
    materia_user.metadata = {}

    mock_storage.listar_materias.return_value = [materia_fantasy, materia_user]
    mock_storage.listar_alunos.return_value = []
    mock_storage.deletar_materia.return_value = True

    result = limpar_dados_fantasy(mock_storage)

    # Assert: only fantasy materia was deleted
    mock_storage.deletar_materia.assert_called_once_with("mat-fantasy")
    # User materia should NOT be deleted
    assert result["materias_deleted"] == 1


def test_limpar_dados_fantasy_deletes_tagged_alunos(mock_storage):
    """
    FG-T7: Verifica que limpar_dados_fantasy deleta alunos
    com metadata criado_por='test_generator'.
    """
    from test_data_generator import limpar_dados_fantasy

    # No materias to delete
    mock_storage.listar_materias.return_value = []

    # Mix of fantasy and user alunos
    aluno_fantasy = Mock()
    aluno_fantasy.id = "aluno-fantasy"
    aluno_fantasy.metadata = {"criado_por": "test_generator"}

    aluno_user = Mock()
    aluno_user.id = "aluno-user"
    aluno_user.metadata = {}

    mock_storage.listar_alunos.return_value = [aluno_fantasy, aluno_user]
    mock_storage.deletar_aluno.return_value = True

    result = limpar_dados_fantasy(mock_storage)

    # Assert: only fantasy aluno deleted
    mock_storage.deletar_aluno.assert_called_once_with("aluno-fantasy")
    assert result["alunos_deleted"] == 1


def test_limpar_dados_fantasy_preserves_user_data(mock_storage):
    """
    FG-T7: Verifica que limpar_dados_fantasy NAO deleta dados de usuario.
    """
    from test_data_generator import limpar_dados_fantasy

    materia_user = Mock()
    materia_user.id = "mat-user"
    materia_user.metadata = {"custom_field": "value"}  # No criado_por

    mock_storage.listar_materias.return_value = [materia_user]
    mock_storage.listar_alunos.return_value = []

    result = limpar_dados_fantasy(mock_storage)

    # Assert: nothing deleted
    mock_storage.deletar_materia.assert_not_called()
    assert result["materias_deleted"] == 0
