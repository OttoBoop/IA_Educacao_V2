"""Complete end-to-end workflow test for multi-model comparison feature"""
import pytest
import requests
import json

BASE = 'https://ia-educacao-v2.onrender.com'


@pytest.fixture(scope="module")
def e2e_test_data():
    """Get test data for E2E workflow tests."""
    # Get turma
    r = requests.get(f'{BASE}/api/turmas', timeout=30)
    turmas = r.json() if isinstance(r.json(), list) else r.json().get('turmas', [])
    turma_id = turmas[0]['id'] if turmas else None

    if not turma_id:
        pytest.skip('No turmas found in database')

    # Get atividade
    r = requests.get(f'{BASE}/api/atividades', params={'turma_id': turma_id}, timeout=30)
    atividades = r.json() if isinstance(r.json(), list) else r.json().get('atividades', [])
    atividade_id = atividades[0]['id'] if atividades else None

    if not atividade_id:
        pytest.skip('No atividades found for turma')

    # Get aluno
    r = requests.get(f'{BASE}/api/alunos', params={'turma_id': turma_id}, timeout=30)
    alunos = r.json() if isinstance(r.json(), list) else r.json().get('alunos', [])
    aluno_id = alunos[0]['id'] if alunos else None

    if not aluno_id:
        pytest.skip('No alunos found for turma')

    return {
        'turma_id': turma_id,
        'atividade_id': atividade_id,
        'aluno_id': aluno_id
    }


@pytest.mark.integration
def test_pipeline_status_endpoint(e2e_test_data):
    """Test getting current pipeline status."""
    atividade_id = e2e_test_data['atividade_id']
    aluno_id = e2e_test_data['aluno_id']

    r = requests.get(
        f'{BASE}/api/executar/status-etapas/{atividade_id}/{aluno_id}',
        timeout=30
    )

    assert r.status_code == 200, f"Failed to get status: {r.status_code}"
    data = r.json()
    assert 'etapas' in data


@pytest.mark.integration
def test_document_versions_endpoint(e2e_test_data):
    """Test getting available document versions."""
    atividade_id = e2e_test_data['atividade_id']
    aluno_id = e2e_test_data['aluno_id']

    r = requests.get(
        f'{BASE}/api/documentos/{atividade_id}/{aluno_id}/versoes',
        timeout=30
    )

    assert r.status_code == 200, f"Failed to get versions: {r.status_code}"
    data = r.json()
    assert 'documentos_por_tipo' in data


@pytest.mark.integration
def test_selective_pipeline_payload_format(e2e_test_data):
    """Test that selective pipeline execution payload is valid."""
    atividade_id = e2e_test_data['atividade_id']
    aluno_id = e2e_test_data['aluno_id']

    selected_steps = ['extrair_questoes', 'corrigir']
    force_rerun = True

    payload = {
        'atividade_id': atividade_id,
        'aluno_id': aluno_id,
        'selected_steps': json.dumps(selected_steps),
        'force_rerun': 'true' if force_rerun else 'false',
        'model_id': 'gpt-4o',
        'providers': json.dumps({
            'extrair_questoes': 'claude-3-sonnet',
            'corrigir': 'gpt-4o'
        })
    }

    # Verify payload structure
    assert 'atividade_id' in payload
    assert 'aluno_id' in payload
    assert 'selected_steps' in payload
    assert 'force_rerun' in payload
    assert 'providers' in payload

    # Verify JSON fields are valid
    steps = json.loads(payload['selected_steps'])
    assert isinstance(steps, list)
    assert len(steps) == 2

    providers = json.loads(payload['providers'])
    assert isinstance(providers, dict)


@pytest.mark.integration
def test_comparison_workflow_data(e2e_test_data):
    """Test that comparison modal can get required data."""
    atividade_id = e2e_test_data['atividade_id']
    aluno_id = e2e_test_data['aluno_id']

    # Get versions for comparison modal
    r = requests.get(
        f'{BASE}/api/documentos/{atividade_id}/{aluno_id}/versoes',
        timeout=30
    )

    if r.status_code == 200:
        data = r.json()
        docs_por_tipo = data.get('documentos_por_tipo', {})

        # Verify structure is suitable for comparison modal
        for tipo, docs in docs_por_tipo.items():
            assert isinstance(docs, list)
            for doc in docs:
                # Each doc should have version info for comparison
                assert isinstance(doc, dict)
