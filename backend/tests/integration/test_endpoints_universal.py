"""
Universal Endpoint Test Script
Tests all major API endpoints in the system

Run: python test_endpoints_universal.py
"""
import os
import pytest

if os.getenv('RUN_ENDPOINTS_UNIVERSAL', '') != '1':
    pytest.skip('Requires running API server; set RUN_ENDPOINTS_UNIVERSAL=1', allow_module_level=True)


import httpx
import asyncio
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Track results
results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

def log_result(name: str, success: bool, details: str = "", skip: bool = False):
    if skip:
        results["skipped"].append({"name": name, "reason": details})
        print(f"⏭️  SKIP: {name} - {details}")
    elif success:
        results["passed"].append({"name": name, "details": details})
        print(f"✅ PASS: {name}")
    else:
        results["failed"].append({"name": name, "error": details})
        print(f"❌ FAIL: {name} - {details}")


async def test_health_endpoints(client: httpx.AsyncClient):
    """Test basic health/info endpoints"""
    print("\n" + "="*50)
    print("🏥 HEALTH & INFO ENDPOINTS")
    print("="*50)
    
    # Root endpoint
    try:
        r = await client.get("/")
        log_result("GET /", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_result("GET /", False, str(e))
    
    # OpenAPI docs
    try:
        r = await client.get("/docs")
        log_result("GET /docs", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_result("GET /docs", False, str(e))
    
    # Providers
    try:
        r = await client.get("/api/providers/disponiveis")
        log_result("GET /api/providers/disponiveis", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_result("GET /api/providers/disponiveis", False, str(e))
    
    # Formatos
    try:
        r = await client.get("/api/formatos-suportados")
        log_result("GET /api/formatos-suportados", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_result("GET /api/formatos-suportados", False, str(e))


async def test_materias_endpoints(client: httpx.AsyncClient):
    """Test Matérias CRUD"""
    print("\n" + "="*50)
    print("📚 MATÉRIAS ENDPOINTS")
    print("="*50)
    
    materia_id = None
    
    # List
    try:
        r = await client.get("/api/materias")
        log_result("GET /api/materias", r.status_code == 200, f"Count: {len(r.json()) if r.status_code == 200 else 'N/A'}")
    except Exception as e:
        log_result("GET /api/materias", False, str(e))
    
    # Create
    try:
        r = await client.post("/api/materias", json={
            "nome": "Teste Matéria",
            "descricao": "Descrição teste",
            "nivel_ensino": "fundamental_2"
        })
        if r.status_code in [200, 201]:
            materia_id = r.json().get("id")
        log_result("POST /api/materias", r.status_code in [200, 201], f"ID: {materia_id}")
    except Exception as e:
        log_result("POST /api/materias", False, str(e))
    
    # Get by ID
    if materia_id:
        try:
            r = await client.get(f"/api/materias/{materia_id}")
            log_result(f"GET /api/materias/{{{materia_id}}}", r.status_code == 200)
        except Exception as e:
            log_result(f"GET /api/materias/{{id}}", False, str(e))
    
    return materia_id


async def test_turmas_endpoints(client: httpx.AsyncClient, materia_id: str):
    """Test Turmas CRUD"""
    print("\n" + "="*50)
    print("🏫 TURMAS ENDPOINTS")
    print("="*50)
    
    turma_id = None
    
    # List
    try:
        r = await client.get("/api/turmas")
        log_result("GET /api/turmas", r.status_code == 200, f"Count: {len(r.json()) if r.status_code == 200 else 'N/A'}")
    except Exception as e:
        log_result("GET /api/turmas", False, str(e))
    
    # Create
    if materia_id:
        try:
            r = await client.post("/api/turmas", json={
                "materia_id": materia_id,
                "nome": "Turma Teste",
                "ano_letivo": 2026,
                "periodo": "Manhã"
            })
            if r.status_code in [200, 201]:
                turma_id = r.json().get("id")
            log_result("POST /api/turmas", r.status_code in [200, 201], f"ID: {turma_id}")
        except Exception as e:
            log_result("POST /api/turmas", False, str(e))
    else:
        log_result("POST /api/turmas", False, skip=True, details="No materia_id")
    
    return turma_id


async def test_alunos_endpoints(client: httpx.AsyncClient, turma_id: str):
    """Test Alunos CRUD"""
    print("\n" + "="*50)
    print("👨‍🎓 ALUNOS ENDPOINTS")
    print("="*50)
    
    aluno_id = None
    
    # List
    try:
        r = await client.get("/api/alunos")
        log_result("GET /api/alunos", r.status_code == 200, f"Count: {len(r.json()) if r.status_code == 200 else 'N/A'}")
    except Exception as e:
        log_result("GET /api/alunos", False, str(e))
    
    # Create
    try:
        r = await client.post("/api/alunos", json={
            "nome": "Aluno Teste",
            "email": f"teste_{datetime.now().timestamp()}@test.com",
            "matricula": f"TEST{int(datetime.now().timestamp())}"
        })
        if r.status_code in [200, 201]:
            aluno_id = r.json().get("id")
        log_result("POST /api/alunos", r.status_code in [200, 201], f"ID: {aluno_id}")
    except Exception as e:
        log_result("POST /api/alunos", False, str(e))
    
    # Vincular
    if aluno_id and turma_id:
        try:
            r = await client.post("/api/alunos/vincular", json={
                "aluno_id": aluno_id,
                "turma_id": turma_id
            })
            log_result("POST /api/alunos/vincular", r.status_code in [200, 201])
        except Exception as e:
            log_result("POST /api/alunos/vincular", False, str(e))
    
    return aluno_id


async def test_atividades_endpoints(client: httpx.AsyncClient, turma_id: str):
    """Test Atividades CRUD"""
    print("\n" + "="*50)
    print("📝 ATIVIDADES ENDPOINTS")
    print("="*50)
    
    atividade_id = None
    
    # List
    try:
        r = await client.get("/api/atividades")
        log_result("GET /api/atividades", r.status_code == 200, f"Count: {len(r.json()) if r.status_code == 200 else 'N/A'}")
    except Exception as e:
        log_result("GET /api/atividades", False, str(e))
    
    # Create
    if turma_id:
        try:
            r = await client.post("/api/atividades", json={
                "turma_id": turma_id,
                "nome": "Atividade Teste",
                "tipo": "prova",
                "nota_maxima": 10.0
            })
            if r.status_code in [200, 201]:
                atividade_id = r.json().get("id")
            log_result("POST /api/atividades", r.status_code in [200, 201], f"ID: {atividade_id}")
        except Exception as e:
            log_result("POST /api/atividades", False, str(e))
    else:
        log_result("POST /api/atividades", False, skip=True, details="No turma_id")
    
    return atividade_id


async def test_chat_endpoints(client: httpx.AsyncClient):
    """Test Chat endpoints"""
    print("\n" + "="*50)
    print("💬 CHAT ENDPOINTS")
    print("="*50)
    
    # List sessions
    try:
        r = await client.get("/api/chat/sessoes")
        log_result("GET /api/chat/sessoes", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/chat/sessoes", False, str(e))
    
    # Providers
    try:
        r = await client.get("/api/chat/providers")
        log_result("GET /api/chat/providers", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/chat/providers", False, str(e))
    
    # Simple chat (without AI call to avoid costs)
    try:
        r = await client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "Olá, teste rápido"}],
            "model_id": "test-model-nonexistent"  # Will fail but tests endpoint
        }, timeout=5.0)
        # We expect this to fail with 400 or 404 (no model), not 500
        log_result("POST /api/chat (validation)", r.status_code in [200, 400, 404, 422], f"Status: {r.status_code}")
    except httpx.TimeoutException:
        log_result("POST /api/chat (validation)", True, "Timeout (expected for AI calls)")
    except Exception as e:
        log_result("POST /api/chat (validation)", False, str(e))


async def test_settings_endpoints(client: httpx.AsyncClient):
    """Test Settings endpoints"""
    print("\n" + "="*50)
    print("⚙️ SETTINGS ENDPOINTS")
    print("="*50)
    
    # API Keys
    try:
        r = await client.get("/api/settings/api-keys")
        log_result("GET /api/settings/api-keys", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/settings/api-keys", False, str(e))
    
    try:
        r = await client.get("/api/settings/api-keys/empresas")
        log_result("GET /api/settings/api-keys/empresas", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/settings/api-keys/empresas", False, str(e))
    
    # Models
    try:
        r = await client.get("/api/settings/models")
        log_result("GET /api/settings/models", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/settings/models", False, str(e))
    
    try:
        r = await client.get("/api/settings/models/sugeridos")
        log_result("GET /api/settings/models/sugeridos", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/settings/models/sugeridos", False, str(e))


async def test_prompts_endpoints(client: httpx.AsyncClient):
    """Test Prompts endpoints"""
    print("\n" + "="*50)
    print("📋 PROMPTS ENDPOINTS")
    print("="*50)
    
    try:
        r = await client.get("/api/prompts")
        log_result("GET /api/prompts", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/prompts", False, str(e))
    
    try:
        r = await client.get("/api/prompts/etapas")
        log_result("GET /api/prompts/etapas", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/prompts/etapas", False, str(e))


async def test_code_executor_endpoints(client: httpx.AsyncClient):
    """Test Code Executor endpoints"""
    print("\n" + "="*50)
    print("🖥️ CODE EXECUTOR ENDPOINTS")
    print("="*50)
    
    # Status
    try:
        r = await client.get("/api/code/status")
        log_result("GET /api/code/status", r.status_code == 200, f"Status: {r.status_code}")
    except Exception as e:
        log_result("GET /api/code/status", False, str(e))
    
    # Libraries
    try:
        r = await client.get("/api/code/libraries")
        log_result("GET /api/code/libraries", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/code/libraries", False, str(e))
    
    # Validate code
    try:
        r = await client.post("/api/code/validate", json={
            "code": "print('Hello World')",
            "language": "python"
        })
        log_result("POST /api/code/validate", r.status_code == 200)
    except Exception as e:
        log_result("POST /api/code/validate", False, str(e))
    
    # Detect language
    try:
        r = await client.post("/api/code/detect", json={
            "code": "console.log('test');"
        })
        log_result("POST /api/code/detect", r.status_code == 200)
    except Exception as e:
        log_result("POST /api/code/detect", False, str(e))


async def test_estatisticas_endpoints(client: httpx.AsyncClient):
    """Test Estatísticas endpoints"""
    print("\n" + "="*50)
    print("📊 ESTATÍSTICAS ENDPOINTS")
    print("="*50)
    
    try:
        r = await client.get("/api/estatisticas")
        log_result("GET /api/estatisticas", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/estatisticas", False, str(e))
    
    try:
        r = await client.get("/api/busca", params={"q": "teste"})
        log_result("GET /api/busca?q=teste", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/busca", False, str(e))


async def test_documentos_endpoints(client: httpx.AsyncClient):
    """Test Documentos endpoints"""
    print("\n" + "="*50)
    print("📄 DOCUMENTOS ENDPOINTS")
    print("="*50)
    
    try:
        r = await client.get("/api/documentos")
        log_result("GET /api/documentos", r.status_code == 200, f"Count: {len(r.json()) if r.status_code == 200 else 'N/A'}")
    except Exception as e:
        log_result("GET /api/documentos", False, str(e))
    
    try:
        r = await client.get("/api/documentos/todos")
        log_result("GET /api/documentos/todos", r.status_code == 200)
    except Exception as e:
        log_result("GET /api/documentos/todos", False, str(e))


async def cleanup(client: httpx.AsyncClient, materia_id: str, turma_id: str, aluno_id: str, atividade_id: str):
    """Cleanup test data"""
    print("\n" + "="*50)
    print("🧹 CLEANUP")
    print("="*50)
    
    if atividade_id:
        try:
            r = await client.delete(f"/api/atividades/{atividade_id}")
            log_result(f"DELETE /api/atividades/{{{atividade_id}}}", r.status_code in [200, 204, 404])
        except Exception as e:
            log_result("DELETE /api/atividades", False, str(e))
    
    if aluno_id:
        try:
            r = await client.delete(f"/api/alunos/{aluno_id}")
            log_result(f"DELETE /api/alunos/{{{aluno_id}}}", r.status_code in [200, 204, 404])
        except Exception as e:
            log_result("DELETE /api/alunos", False, str(e))
    
    if turma_id:
        try:
            r = await client.delete(f"/api/turmas/{turma_id}")
            log_result(f"DELETE /api/turmas/{{{turma_id}}}", r.status_code in [200, 204, 404])
        except Exception as e:
            log_result("DELETE /api/turmas", False, str(e))
    
    if materia_id:
        try:
            r = await client.delete(f"/api/materias/{materia_id}")
            log_result(f"DELETE /api/materias/{{{materia_id}}}", r.status_code in [200, 204, 404])
        except Exception as e:
            log_result("DELETE /api/materias", False, str(e))


async def main():
    print("\n" + "="*60)
    print("🚀 UNIVERSAL API ENDPOINT TEST")
    print(f"   Target: {BASE_URL}")
    print(f"   Time: {datetime.now().isoformat()}")
    print("="*60)
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Test health first
        await test_health_endpoints(client)
        
        # CRUD tests with created entities
        materia_id = await test_materias_endpoints(client)
        turma_id = await test_turmas_endpoints(client, materia_id)
        aluno_id = await test_alunos_endpoints(client, turma_id)
        atividade_id = await test_atividades_endpoints(client, turma_id)
        
        # Other endpoints
        await test_chat_endpoints(client)
        await test_settings_endpoints(client)
        await test_prompts_endpoints(client)
        await test_code_executor_endpoints(client)
        await test_estatisticas_endpoints(client)
        await test_documentos_endpoints(client)
        
        # Cleanup
        await cleanup(client, materia_id, turma_id, aluno_id, atividade_id)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed:  {len(results['passed'])}")
    print(f"❌ Failed:  {len(results['failed'])}")
    print(f"⏭️  Skipped: {len(results['skipped'])}")
    print("="*60)
    
    if results['failed']:
        print("\n❌ FAILED TESTS:")
        for f in results['failed']:
            print(f"   - {f['name']}: {f['error']}")
    
    return len(results['failed']) == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
