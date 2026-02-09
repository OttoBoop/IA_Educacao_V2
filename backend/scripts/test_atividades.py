import requests

BASE = 'https://ia-educacao-v2.onrender.com'
turma_id = '6263d50c7d8e3126'

r = requests.get(f'{BASE}/api/atividades?turma_id={turma_id}', timeout=30)
print(f'Status: {r.status_code}')
print(f'Content-Type: {r.headers.get("content-type")}')
print(f'Response: {r.text[:500]}')