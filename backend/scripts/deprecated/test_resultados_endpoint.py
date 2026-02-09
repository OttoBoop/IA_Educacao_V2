import requests

BASE = 'https://ia-educacao-v2.onrender.com'

# Test the resultados endpoint that was giving 500
atividade_id = '048de9fbdbd1d66e'
aluno_id = 'b71912f0155e494f'
r = requests.get(f'{BASE}/api/resultados/{atividade_id}/{aluno_id}', timeout=30)
print(f'Resultados status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Sucesso: {data.get("sucesso")}')
    print(f'Completo: {data.get("completo")}')
    print(f'Progresso: {data.get("progresso", "N/A")}%')
else:
    print(f'Response: {r.text[:300]}')