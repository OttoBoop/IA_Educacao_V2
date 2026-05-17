"""Aggregate desempenho reports must not save duplicate cost documents."""

from pathlib import Path


def _method_body(source: str, name: str) -> str:
    start = source.index(f"async def {name}(")
    next_method = source.find("\n    async def ", start + 1)
    if next_method == -1:
        return source[start:]
    return source[start:next_method]


def test_aggregate_desempenho_methods_do_not_save_result_twice():
    source = Path("backend/executor.py").read_text(encoding="utf-8")
    methods = [
        "gerar_relatorio_desempenho_tarefa",
        "gerar_relatorio_desempenho_turma",
        "gerar_relatorio_desempenho_materia",
    ]

    for method in methods:
        body = _method_body(source, method)
        assert "executar_com_tools(" in body
        assert "_salvar_resultado(" not in body
