"""
Quick endpoint tests for pipeline debugging
"""
import requests
import json

BASE = "http://localhost:8000"

def test_atividades():
    """List atividades"""
    print("=" * 60)
    print("LISTING ATIVIDADES")
    print("=" * 60)
    
    r = requests.get(f"{BASE}/api/atividades", timeout=10, params={"turma_id": ""})
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        atividades = data if isinstance(data, list) else data.get("atividades", [])
        for a in atividades[:5]:
            print(f"  ID: {a.get('id', '?')} - {a.get('nome', '?')}")
        return atividades[0]["id"] if atividades else None
    else:
        print(f"Error: {r.text[:200]}")
        return None

def test_documentos(atividade_id):
    """List documents for an atividade"""
    print("\n" + "=" * 60)
    print(f"DOCUMENTS FOR ATIVIDADE {atividade_id}")
    print("=" * 60)
    
    r = requests.get(f"{BASE}/api/documentos", timeout=10, params={"atividade_id": atividade_id})
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        docs = data if isinstance(data, list) else data.get("documentos", [])
        for d in docs[:10]:
            print(f"  {d.get('tipo', '?')}: {d.get('nome_arquivo', '?')}")
        return docs
    else:
        print(f"Error: {r.text[:200]}")
        return []

def test_alunos(turma_id):
    """List alunos for a turma"""
    print("\n" + "=" * 60)
    print(f"ALUNOS FOR TURMA {turma_id}")
    print("=" * 60)
    
    r = requests.get(f"{BASE}/api/alunos", timeout=10, params={"turma_id": turma_id})
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        alunos = data if isinstance(data, list) else data.get("alunos", [])
        for a in alunos[:5]:
            print(f"  ID: {a.get('id', '?')} - {a.get('nome', '?')}")
        return alunos[0]["id"] if alunos else None
    else:
        print(f"Error: {r.text[:200]}")
        return None

def test_pipeline(atividade_id, aluno_id):
    """Test pipeline execution"""
    print("\n" + "=" * 60)
    print(f"TESTING PIPELINE: atividade={atividade_id}, aluno={aluno_id}")
    print("=" * 60)
    
    r = requests.post(
        f"{BASE}/api/executar/pipeline-completo",
        data={
            "atividade_id": atividade_id,
            "aluno_id": aluno_id,
            "provider": "180b8298a279"  # OpenAI gpt-4o
        },
        timeout=120
    )
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        data = r.json()
        print(f"Sucesso: {data.get('sucesso')}")
        print(f"Etapas executadas: {data.get('etapas_executadas')}")
        print(f"Etapas falharam: {data.get('etapas_falharam')}")
        
        resultados = data.get("resultados", {})
        for etapa, res in resultados.items():
            print(f"\n  [{etapa}]")
            print(f"    sucesso: {res.get('sucesso')}")
            if res.get("erro"):
                print(f"    erro: {res.get('erro')}")
    else:
        print(f"Error: {r.text[:500]}")

def main():
    # 1. Get an atividade
    atividade_id = test_atividades()
    if not atividade_id:
        print("No atividades found!")
        return
    
    # 2. Get documents
    docs = test_documentos(atividade_id)
    
    # 3. Get turma from atividade and list alunos
    r = requests.get(f"{BASE}/api/atividades/{atividade_id}", timeout=10)
    if r.status_code == 200:
        atividade = r.json()
        turma_id = atividade.get("turma_id")
        aluno_id = test_alunos(turma_id)
        
        if aluno_id:
            # 4. Test pipeline
            test_pipeline(atividade_id, aluno_id)
        else:
            print("No alunos found!")
    else:
        print(f"Could not get atividade details: {r.text[:200]}")

if __name__ == "__main__":
    main()
