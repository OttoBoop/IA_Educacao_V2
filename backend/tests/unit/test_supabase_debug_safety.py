"""Safety tests for Supabase debug and recovery helpers."""

from pathlib import Path


BACKEND_DIR = Path(__file__).parent.parent.parent
ROUTES_EXTRAS = BACKEND_DIR / "routes_extras.py"
RECOVER_SCRIPT = BACKEND_DIR.parent / "md documents" / "algebra-linear-providers-mapping" / "_recover_supabase.py"


def test_supabase_debug_does_not_echo_keys_or_patch():
    source = ROUTES_EXTRAS.read_text(encoding="utf-8")
    start = source.index('async def supabase_debug')
    end = source.find("\n\n@router.", start)
    body = source[start:end if end != -1 else len(source)]

    assert "SERVICE_KEY[:" not in body
    assert "ANON_KEY[:" not in body
    assert "_requests.patch" not in body
    assert "_requests.get" in body
    assert "service_key_configured" in body


def test_algebra_recovery_writes_complete_alunos_turmas_rows():
    source = RECOVER_SCRIPT.read_text(encoding="utf-8")
    step_start = source.index("# Step 5: Alunos_turmas")
    step_end = source.index("# Step 6: Documentos uploads")
    step = source[step_start:step_end]

    assert 'CONFIRM_SUPABASE_RECOVERY") != CONFIRM_TOKEN' in source
    assert '"id": stable_id("vinculo", aid, "3f3ab03dfe783f30")' in step
    assert '"ativo": True' in step
    assert '"data_entrada": "2026-04-13T14:00:00+00:00"' in step
    assert 'conflict_col="aluno_id,turma_id"' in step
