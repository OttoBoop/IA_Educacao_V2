from pathlib import Path


def _frontend_html():
    html_path = Path(__file__).parent.parent.parent.parent / "frontend" / "index_v2.html"
    assert html_path.exists(), f"index_v2.html not found at {html_path}"
    return html_path.read_text(encoding="utf-8")


def _show_aluno_body(html):
    start = html.find("async function showAluno(")
    assert start != -1, "showAluno() not found"
    end = html.find("// ============================================================\n        // BREADCRUMB", start)
    assert end != -1, "Could not find end of showAluno() section"
    return html[start:end]


def _show_alunos_body(html):
    start = html.find("async function showAlunos()")
    assert start != -1, "showAlunos() not found"
    end = html.find("function filterVisaoAlunoList(", start)
    assert end != -1, "Could not find end of showAlunos() section"
    return html[start:end]


def _show_visao_aluno_selector_body(html):
    start = html.find("async function showVisaoAlunoSelector()")
    assert start != -1, "showVisaoAlunoSelector() not found"
    end = html.find("async function showPrompts()", start)
    assert end != -1, "Could not find end of showVisaoAlunoSelector() section"
    return html[start:end]


def test_sidebar_has_visao_aluno_entry():
    html = _frontend_html()

    assert 'data-nav-view="visao_aluno_selector"' in html
    assert 'onclick="showVisaoAlunoSelector()"' in html
    assert "🎓" in html
    assert "Visão do Aluno" in html
    assert "Escolha um aluno e veja apenas matérias, turmas e atividades em que ele participou" in html


def test_visao_aluno_selector_fetches_alunos():
    body = _show_visao_aluno_selector_body(_frontend_html())

    assert "currentView = 'visao_aluno_selector'" in body
    assert "currentMateria = currentTurma = currentAtividade = currentAluno = null" in body
    assert "api('/alunos')" in body
    assert "input-visao-aluno-search" in body
    assert "filterVisaoAlunoList(this.value)" in body


def test_visao_aluno_selector_opens_show_aluno():
    body = _show_visao_aluno_selector_body(_frontend_html())

    assert "Abrir Visão" in body
    assert "showAluno(${jsString(a.id)}, ${jsString(a.nome)}, ${jsString(a.matricula || '')})" in body


def test_popstate_restores_visao_aluno_selector():
    html = _frontend_html()

    assert "case 'visao_aluno_selector': await showVisaoAlunoSelector(); break;" in html


def test_show_alunos_button_opens_visao_label():
    body = _show_alunos_body(_frontend_html())

    assert "Abrir Visão" in body
    assert "Ver Turmas" not in body


def test_show_aluno_uses_student_view_endpoint():
    body = _show_aluno_body(_frontend_html())

    assert "api(`/alunos/${alunoId}/visao`)" in body


def test_show_aluno_renders_materia_turma_atividade_hierarchy():
    html = _frontend_html()

    assert "function renderAlunoVisaoMateria(" in html
    assert "function renderAlunoVisaoAtividades(" in html
    assert "materia.turmas" in html
    assert "turma.atividades" in html


def test_show_aluno_status_is_individual_document_status():
    html = _frontend_html()

    assert "function renderAlunoVisaoStatus(" in html
    assert "tem_prova_respondida" in html
    assert "tem_correcao" in html
    assert "tem_analise_habilidades" in html
    assert "tem_relatorio_final" in html
    assert "total_documentos_aluno" in html


def test_show_aluno_activity_action_keeps_aluno_context():
    html = _frontend_html()

    assert "showResultadoAluno('${atividade.atividade_id}', '${aluno.id}'" in html
