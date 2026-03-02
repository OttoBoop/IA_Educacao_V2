"""
X1: Tests for new EtapaProcessamento + TipoDocumento values for Relatório de Desempenho pipeline.

Tests verify that:
- EtapaProcessamento has 3 new values: RELATORIO_DESEMPENHO_TAREFA, _TURMA, _MATERIA
- TipoDocumento has 3 matching new values with correct string keys
- tipo_map in executor._salvar_resultado maps new stages to new doc types
- DEPENDENCIAS_DOCUMENTOS has entries for new stages (require RELATORIO_NARRATIVO)
- documentos_gerados() includes all 3 new TipoDocumento values
"""

import sys
from pathlib import Path
import inspect

# Allow importing from backend root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================
# ETAPAPROCESSAMENTO TESTS
# ============================================================

def test_etapa_processamento_has_relatorio_desempenho_tarefa():
    """RELATORIO_DESEMPENHO_TAREFA must exist in EtapaProcessamento with correct string value."""
    from prompts import EtapaProcessamento
    assert hasattr(EtapaProcessamento, "RELATORIO_DESEMPENHO_TAREFA"), (
        "EtapaProcessamento must have RELATORIO_DESEMPENHO_TAREFA value. "
        "Add it to prompts.py EtapaProcessamento enum."
    )
    assert EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA.value == "relatorio_desempenho_tarefa"


def test_etapa_processamento_has_relatorio_desempenho_turma():
    """RELATORIO_DESEMPENHO_TURMA must exist in EtapaProcessamento."""
    from prompts import EtapaProcessamento
    assert hasattr(EtapaProcessamento, "RELATORIO_DESEMPENHO_TURMA"), (
        "EtapaProcessamento must have RELATORIO_DESEMPENHO_TURMA value."
    )
    assert EtapaProcessamento.RELATORIO_DESEMPENHO_TURMA.value == "relatorio_desempenho_turma"


def test_etapa_processamento_has_relatorio_desempenho_materia():
    """RELATORIO_DESEMPENHO_MATERIA must exist in EtapaProcessamento."""
    from prompts import EtapaProcessamento
    assert hasattr(EtapaProcessamento, "RELATORIO_DESEMPENHO_MATERIA"), (
        "EtapaProcessamento must have RELATORIO_DESEMPENHO_MATERIA value."
    )
    assert EtapaProcessamento.RELATORIO_DESEMPENHO_MATERIA.value == "relatorio_desempenho_materia"


# ============================================================
# TIPODOCUMENTO TESTS
# ============================================================

def test_tipo_documento_has_relatorio_desempenho_tarefa():
    """RELATORIO_DESEMPENHO_TAREFA must exist in TipoDocumento with correct string value."""
    from models import TipoDocumento
    assert hasattr(TipoDocumento, "RELATORIO_DESEMPENHO_TAREFA"), (
        "TipoDocumento must have RELATORIO_DESEMPENHO_TAREFA. Add it to models.py."
    )
    assert TipoDocumento.RELATORIO_DESEMPENHO_TAREFA.value == "relatorio_desempenho_tarefa"


def test_tipo_documento_has_relatorio_desempenho_turma():
    """RELATORIO_DESEMPENHO_TURMA must exist in TipoDocumento."""
    from models import TipoDocumento
    assert hasattr(TipoDocumento, "RELATORIO_DESEMPENHO_TURMA")
    assert TipoDocumento.RELATORIO_DESEMPENHO_TURMA.value == "relatorio_desempenho_turma"


def test_tipo_documento_has_relatorio_desempenho_materia():
    """RELATORIO_DESEMPENHO_MATERIA must exist in TipoDocumento."""
    from models import TipoDocumento
    assert hasattr(TipoDocumento, "RELATORIO_DESEMPENHO_MATERIA")
    assert TipoDocumento.RELATORIO_DESEMPENHO_MATERIA.value == "relatorio_desempenho_materia"


# ============================================================
# tipo_map IN executor._salvar_resultado TESTS
# ============================================================

def test_tipo_map_includes_relatorio_desempenho_tarefa():
    """tipo_map in executor._salvar_resultado must map RELATORIO_DESEMPENHO_TAREFA."""
    import executor
    source = inspect.getsource(executor.PipelineExecutor._salvar_resultado)
    assert "RELATORIO_DESEMPENHO_TAREFA" in source, (
        "executor._salvar_resultado tipo_map must include EtapaProcessamento.RELATORIO_DESEMPENHO_TAREFA "
        "→ TipoDocumento.RELATORIO_DESEMPENHO_TAREFA mapping."
    )


def test_tipo_map_includes_relatorio_desempenho_turma():
    """tipo_map in executor._salvar_resultado must map RELATORIO_DESEMPENHO_TURMA."""
    import executor
    source = inspect.getsource(executor.PipelineExecutor._salvar_resultado)
    assert "RELATORIO_DESEMPENHO_TURMA" in source


def test_tipo_map_includes_relatorio_desempenho_materia():
    """tipo_map in executor._salvar_resultado must map RELATORIO_DESEMPENHO_MATERIA."""
    import executor
    source = inspect.getsource(executor.PipelineExecutor._salvar_resultado)
    assert "RELATORIO_DESEMPENHO_MATERIA" in source


# ============================================================
# DEPENDENCIAS_DOCUMENTOS TESTS
# ============================================================

def test_dependencias_documentos_has_relatorio_desempenho_tarefa():
    """DEPENDENCIAS_DOCUMENTOS must have entry for RELATORIO_DESEMPENHO_TAREFA requiring RELATORIO_FINAL."""
    from models import TipoDocumento, DEPENDENCIAS_DOCUMENTOS
    assert TipoDocumento.RELATORIO_DESEMPENHO_TAREFA in DEPENDENCIAS_DOCUMENTOS, (
        "DEPENDENCIAS_DOCUMENTOS must have an entry for TipoDocumento.RELATORIO_DESEMPENHO_TAREFA. "
        "It should require TipoDocumento.RELATORIO_FINAL as an obligatory dependency."
    )
    deps = DEPENDENCIAS_DOCUMENTOS[TipoDocumento.RELATORIO_DESEMPENHO_TAREFA]
    assert TipoDocumento.RELATORIO_FINAL in deps["obrigatorios"], (
        "RELATORIO_DESEMPENHO_TAREFA must have RELATORIO_FINAL as a required input."
    )


def test_dependencias_documentos_has_relatorio_desempenho_turma():
    """DEPENDENCIAS_DOCUMENTOS must have entry for RELATORIO_DESEMPENHO_TURMA requiring RELATORIO_FINAL."""
    from models import TipoDocumento, DEPENDENCIAS_DOCUMENTOS
    assert TipoDocumento.RELATORIO_DESEMPENHO_TURMA in DEPENDENCIAS_DOCUMENTOS
    deps = DEPENDENCIAS_DOCUMENTOS[TipoDocumento.RELATORIO_DESEMPENHO_TURMA]
    assert TipoDocumento.RELATORIO_FINAL in deps["obrigatorios"]


def test_dependencias_documentos_has_relatorio_desempenho_materia():
    """DEPENDENCIAS_DOCUMENTOS must have entry for RELATORIO_DESEMPENHO_MATERIA requiring RELATORIO_FINAL."""
    from models import TipoDocumento, DEPENDENCIAS_DOCUMENTOS
    assert TipoDocumento.RELATORIO_DESEMPENHO_MATERIA in DEPENDENCIAS_DOCUMENTOS
    deps = DEPENDENCIAS_DOCUMENTOS[TipoDocumento.RELATORIO_DESEMPENHO_MATERIA]
    assert TipoDocumento.RELATORIO_FINAL in deps["obrigatorios"]


# ============================================================
# documentos_gerados() TESTS
# ============================================================

def test_documentos_gerados_includes_relatorio_desempenho_tarefa():
    """documentos_gerados() must include RELATORIO_DESEMPENHO_TAREFA."""
    from models import TipoDocumento
    gerados = TipoDocumento.documentos_gerados()
    assert TipoDocumento.RELATORIO_DESEMPENHO_TAREFA in gerados, (
        "TipoDocumento.documentos_gerados() must include RELATORIO_DESEMPENHO_TAREFA."
    )


def test_documentos_gerados_includes_relatorio_desempenho_turma():
    """documentos_gerados() must include RELATORIO_DESEMPENHO_TURMA."""
    from models import TipoDocumento
    gerados = TipoDocumento.documentos_gerados()
    assert TipoDocumento.RELATORIO_DESEMPENHO_TURMA in gerados


def test_documentos_gerados_includes_relatorio_desempenho_materia():
    """documentos_gerados() must include RELATORIO_DESEMPENHO_MATERIA."""
    from models import TipoDocumento
    gerados = TipoDocumento.documentos_gerados()
    assert TipoDocumento.RELATORIO_DESEMPENHO_MATERIA in gerados
