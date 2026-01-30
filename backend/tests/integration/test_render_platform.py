"""Test endpoints on Render deployment"""
import requests

BASE = 'https://ia-educacao-v2.onrender.com'

def get_list(data, key):
    """Extract list from response regardless of format"""
    if isinstance(data, list):
        return data
    return data.get(key, [])

print('=== TESTING RENDER DEPLOYMENT ===')

# 1. List turmas to find data
print('\n--- Turmas ---')
r = requests.get(f'{BASE}/api/turmas', timeout=30)
print('Status:', r.status_code)
if r.status_code == 200:
    turmas = get_list(r.json(), 'turmas')
    print(f'Found {len(turmas)} turmas')
    for t in turmas[:3]:
        print(f"  {t['id']}: {t['nome']}")
    
    if turmas:
        turma_id = turmas[0]['id']
        
        # 2. Get atividades
        print('\n--- Atividades ---')
        r = requests.get(f'{BASE}/api/atividades', params={'turma_id': turma_id}, timeout=30)
        if r.status_code == 200:
            atividades = get_list(r.json(), 'atividades')
            print(f'Found {len(atividades)} atividades')
            for a in atividades[:3]:
                print(f"  {a['id']}: {a['nome']}")
            
            if atividades:
                atividade_id = atividades[0]['id']
                
                # 3. Get alunos
                print('\n--- Alunos ---')
                r = requests.get(f'{BASE}/api/alunos', params={'turma_id': turma_id}, timeout=30)
                if r.status_code == 200:
                    alunos = get_list(r.json(), 'alunos')
                    print(f'Found {len(alunos)} alunos')
                    for a in alunos[:3]:
                        print(f"  {a['id']}: {a['nome']}")
                    
                    if alunos:
                        aluno_id = alunos[0]['id']
                        
                        # 4. Test new status endpoint
                        print('\n--- Status Etapas ---')
                        r = requests.get(f'{BASE}/api/executar/status-etapas/{atividade_id}/{aluno_id}', timeout=30)
                        print('Status:', r.status_code)
                        if r.status_code == 200:
                            data = r.json()
                            for etapa, info in data.get('etapas', {}).items():
                                status = 'OK' if info['executada'] else '--'
                                versoes = info['versoes']
                                docs = info.get('documentos', [])
                                modelo = docs[0]['modelo'] if docs else 'N/A'
                                print(f"  [{status}] {etapa}: {versoes} versoes, modelo={modelo}")
                        else:
                            print('Error:', r.text[:200])
                        
                        # 5. Test versions endpoint
                        print('\n--- Versoes Documentos ---')
                        r = requests.get(f'{BASE}/api/documentos/{atividade_id}/{aluno_id}/versoes', timeout=30)
                        print('Status:', r.status_code)
                        if r.status_code == 200:
                            data = r.json()
                            for tipo, docs in data.get('documentos_por_tipo', {}).items():
                                print(f"  {tipo}: {len(docs)} versoes")
                        else:
                            print('Error:', r.text[:200])
