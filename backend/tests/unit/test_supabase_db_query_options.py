"""Tests for projection and IN-filter support in SupabaseDB."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from supabase_db import SupabaseDB


def _make_enabled_db():
    table = MagicMock()
    query = MagicMock()
    table.select.return_value = query
    query.in_.return_value = query
    query.eq.return_value = query
    query.is_.return_value = query
    query.order.return_value = query
    query.limit.return_value = query
    query.execute.return_value = SimpleNamespace(data=[{"id": "doc-1"}], count=1)

    client = MagicMock()
    client.table.return_value = table

    db = SupabaseDB.__new__(SupabaseDB)
    db._client = client
    db._enabled = True
    return db, client, table, query


def test_select_supports_projection_and_in_filters():
    db, client, table, query = _make_enabled_db()

    rows = db.select(
        "documentos",
        filters={"atividade_id": ["ativ-1", "ativ-2"], "aluno_id": None},
        order_by="criado_em",
        order_desc=True,
        limit=5,
        columns=["id", "atividade_id"],
    )

    client.table.assert_called_once_with("documentos")
    table.select.assert_called_once_with("id,atividade_id")
    query.in_.assert_called_once_with("atividade_id", ["ativ-1", "ativ-2"])
    query.is_.assert_called_once_with("aluno_id", "null")
    query.order.assert_called_once_with("criado_em", desc=True)
    query.limit.assert_called_once_with(5)
    assert rows == [{"id": "doc-1"}]


def test_count_returns_zero_without_query_when_in_filter_is_empty():
    db, client, table, query = _make_enabled_db()

    total = db.count("documentos", filters={"atividade_id": []})

    client.table.assert_called_once_with("documentos")
    table.select.assert_called_once_with("id", count="exact")
    query.execute.assert_not_called()
    assert total == 0
