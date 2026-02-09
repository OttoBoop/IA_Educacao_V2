import requests

BASE = 'https://ia-educacao-v2.onrender.com'

# Test the documentos endpoint that was giving 404
doc_id = 'b498021992e171c8'
r = requests.get(f'{BASE}/api/documentos/{doc_id}/conteudo', timeout=30)
print(f'Documento {doc_id} status: {r.status_code}')
if r.status_code == 200:
    data = r.json()
    print(f'Tipo conteudo: {data.get("tipo_conteudo")}')
    if 'erro' in data:
        print(f'Erro: {data["erro"]}')
else:
    print(f'Response: {r.text[:200]}')