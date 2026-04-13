from pathlib import Path


FRONTEND = Path(__file__).resolve().parents[3] / "frontend" / "index_v2.html"


def _html():
    return FRONTEND.read_text(encoding="utf-8")


def test_import_table_modal_has_mapping_flow():
    html = _html()
    assert "Importar Alunos por Tabela" in html
    assert 'accept=".csv,.xlsx,.xls,.ods"' in html
    assert 'id="select-importar-map-nome"' in html
    assert 'id="select-importar-map-email"' in html
    assert 'id="select-importar-map-matricula"' in html
    assert "/alunos/importar-tabela/preview" in html
    assert "/alunos/importar-tabela" in html


def test_import_table_buttons_have_busy_state_and_double_click_guard():
    html = _html()
    assert "setImportarTabelaBusy" in html
    assert "importarTabelaState.busy" in html
    assert 'id="btn-confirmar-importar"' in html
    assert "Mapeie a coluna de nome" in html


def test_batch_upload_sends_assignments_and_student_dropdowns():
    html = _html()
    assert "batch-aluno-select" in html
    assert "batch-action-select" in html
    assert "onBatchAssignmentChange" in html
    assert "formData.append('assignments'" in html
    assert "Substituir prova existente" in html
    assert "Escolha um aluno ou remova este arquivo" in html
