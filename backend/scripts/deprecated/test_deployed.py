import requests
import json

BASE = 'https://ia-educacao-v2.onrender.com'

print('=== CHECKING WEBSITE STATUS ===')

try:
    r = requests.get(BASE, timeout=10)
    print(f'Website status: {r.status_code}')
    
    # Try API docs
    r_docs = requests.get(f'{BASE}/docs', timeout=10)
    print(f'API docs status: {r_docs.status_code}')
    
    # Get turmas first
    print('\n=== GETTING TURMAS ===')
    r_turmas = requests.get(f'{BASE}/api/turmas', timeout=30)
    print(f'Turmas endpoint: {r_turmas.status_code}')
    
    if r_turmas.status_code == 200:
        turmas_data = r_turmas.json()
        turmas = turmas_data.get('turmas', [])
        print(f'Found {len(turmas)} turmas')
        
        if turmas:
            turma_id = turmas[0]['id']
            print(f'Using turma_id: {turma_id}')
            
            # Get activities for this turma
            print('\n=== GETTING ACTIVITIES ===')
            r_activities = requests.get(f'{BASE}/api/atividades?turma_id={turma_id}', timeout=30)
            print(f'Activities endpoint: {r_activities.status_code}')
            
            if r_activities.status_code == 200:
                activities = r_activities.json()
                econometria_tasks = [a for a in activities if 'econometria' in a.get('materia', '').lower() or 'econometria' in a.get('nome', '').lower()]
                
                print(f'Found {len(econometria_tasks)} econometria tasks:')
                for task in econometria_tasks[:5]:  # Show first 5
                    print(f'  - ID: {task["id"]}, Nome: {task["nome"]}, Materia: {task.get("materia", "N/A")}')
                    
                # Run pipelines for all econometria tasks
                print('\n=== RUNNING PIPELINES FOR ECONOMETRIA TASKS ===')
                
                for i, task in enumerate(econometria_tasks):
                    task_id = task['id']
                    print(f'\n[{i+1}/{len(econometria_tasks)}] Running pipeline for task {task_id}: {task["nome"]}')
                    
                    # Run pipeline
                    pipeline_data = {
                        'atividade_id': task_id,
                        'force_rerun': True
                    }
                    
                    r_pipeline = requests.post(f'{BASE}/api/pipeline/executar-completo', json=pipeline_data, timeout=120)
                    print(f'  Pipeline status: {r_pipeline.status_code}')
                    
                    if r_pipeline.status_code == 200:
                        result = r_pipeline.json()
                        print(f'  Success: {result.get("sucesso", False)}')
                        
                        # Check for documents
                        if result.get('documentos_gerados'):
                            print(f'  Documents generated: {len(result["documentos_gerados"])}')
                            for doc in result['documentos_gerados']:
                                doc_id = doc['id']
                                doc_type = doc['tipo']
                                print(f'    - {doc_type}: {doc_id}')
                                
                                # Try to download if it's a report
                                if 'relatorio' in doc_type.lower():
                                    download_url = f'{BASE}/api/documentos/{doc_id}/download'
                                    r_download = requests.get(download_url, timeout=30)
                                    print(f'      PDF download: {r_download.status_code}, size: {len(r_download.content)} bytes')
                                    
                                    # Check if it's a valid PDF
                                    if r_download.status_code == 200:
                                        content = r_download.content
                                        if content.startswith(b'%PDF'):
                                            print('      ✓ Valid PDF')
                                        elif b'_error' in content:
                                            print('      ✗ Error response (not PDF)')
                                            # Show first 200 chars
                                            text = content.decode('utf-8', errors='ignore')[:200]
                                            print(f'      Content preview: {text}...')
                                        else:
                                            print('      ? Unknown format')
                                    else:
                                        print(f'      ✗ Download failed: {r_download.status_code}')
                        else:
                            print('  No documents generated')
                    else:
                        print(f'  Error: {r_pipeline.text[:300]}')
                        
            else:
                print(f'Error getting activities: {r_activities.text[:200]}')
        else:
            print('No turmas found')
    else:
        print(f'Error getting turmas: {r_turmas.text[:200]}')
        
except Exception as e:
    print(f'Error: {e}')