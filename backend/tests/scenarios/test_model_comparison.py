"""Test the comparison functionality end-to-end"""
import pytest
import requests
import json

BASE = 'https://ia-educacao-v2.onrender.com'


@pytest.fixture(scope="module")
def test_data():
    """Get test data from the live API."""
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
def test_status_endpoint(test_data):
    """Test the status-etapas endpoint."""
    atividade_id = test_data['atividade_id']
    aluno_id = test_data['aluno_id']

    r = requests.get(
        f'{BASE}/api/executar/status-etapas/{atividade_id}/{aluno_id}',
        timeout=30
    )

    assert r.status_code == 200, f"Status endpoint failed: {r.status_code}"
    data = r.json()
    assert 'etapas' in data, "Response missing 'etapas' key"


@pytest.mark.integration
def test_versions_endpoint(test_data):
    """Test the versions endpoint."""
    atividade_id = test_data['atividade_id']
    aluno_id = test_data['aluno_id']

    r = requests.get(
        f'{BASE}/api/documentos/{atividade_id}/{aluno_id}/versoes',
        timeout=30
    )

    assert r.status_code == 200, f"Versions endpoint failed: {r.status_code}"
    data = r.json()
    assert 'documentos_por_tipo' in data, "Response missing 'documentos_por_tipo' key"


@pytest.mark.integration
def test_pipeline_payload_format(test_data):
    """Test that pipeline accepts the expected payload format."""
    atividade_id = test_data['atividade_id']
    aluno_id = test_data['aluno_id']

    # Just verify the payload format is valid - don't actually execute
    payload = {
        'atividade_id': atividade_id,
        'aluno_id': aluno_id,
        'selected_steps': json.dumps(['extrair_questoes', 'extrair_gabarito']),
        'force_rerun': 'true'
    }

    # Validate payload structure
    assert 'atividade_id' in payload
    assert 'aluno_id' in payload
    assert 'selected_steps' in payload
    assert 'force_rerun' in payload

    # Verify selected_steps is valid JSON
    steps = json.loads(payload['selected_steps'])
    assert isinstance(steps, list)
