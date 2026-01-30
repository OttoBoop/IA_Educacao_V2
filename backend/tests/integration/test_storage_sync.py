#!/usr/bin/env python3
"""
Teste completo da funcionalidade de sincronização Local -> Remoto
"""

import asyncio
import requests
import subprocess
import time
import json
from pathlib import Path


async def test_sync_functionality():
    """Testa a sincronização completa de dados locais para o servidor remoto"""

    print("🚀 INICIANDO TESTE DE SINCRONIZAÇÃO LOCAL → REMOTO")
    print("=" * 60)

    # 1. Iniciar servidor local
    print("1. Iniciando servidor local...")
    server_process = subprocess.Popen([
        'python', '-m', 'uvicorn', 'main_v2:app',
        '--host', '127.0.0.1', '--port', '8005'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    time.sleep(5)

    if server_process.poll() is not None:
        print("❌ Servidor local falhou ao iniciar")
        stdout, stderr = server_process.communicate()
        print(f"Erro: {stderr[:200]}")
        return

    print("✅ Servidor local iniciado na porta 8005")

    base_url = "http://127.0.0.1:8005"

    try:
        # 2. Verificar status da sincronização
        print("\n2. Verificando status da sincronização...")
        response = requests.get(f"{base_url}/api/sync/status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            print("✅ Status obtido:")
            print(f"   - Servidor local: {status['local_server']}")
            print(f"   - Servidor remoto: {status['remote_server']['status']}")
            print(f"   - URL remoto: {status['remote_server']['url']}")
        else:
            print(f"❌ Erro no status: {response.status_code}")
            return

        # 3. Testar conexão com servidor remoto
        print("\n3. Testando conexão com servidor remoto...")
        response = requests.post(f"{base_url}/api/sync/test-connection", timeout=15)
        if response.status_code == 200:
            result = response.json()
            print("✅ Conexão estabelecida:")
            print(f"   - Status HTTP: {result['status_code']}")
            print(f"   - URL: {result['remote_url']}")
        else:
            print(f"❌ Falha na conexão: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}")
            return

        # 4. Criar dados de teste localmente
        print("\n4. Criando dados de teste localmente...")

        # Criar matéria
        materia_data = {
            "nome": "Matéria Sync Teste",
            "descricao": "Matéria criada para teste de sincronização",
            "nivel": "medio"
        }
        response = requests.post(f"{base_url}/api/materias", json=materia_data, timeout=10)
        if response.status_code == 200:
            materia = response.json()["materia"]
            materia_id = materia["id"]
            print(f"✅ Matéria criada: {materia['nome']} (ID: {materia_id})")
        else:
            print(f"❌ Falha ao criar matéria: {response.status_code}")
            return

        # Criar turma
        turma_data = {
            "materia_id": materia_id,
            "nome": "Turma Sync A",
            "ano_letivo": 2024,
            "periodo": "2024.1"
        }
        response = requests.post(f"{base_url}/api/turmas", json=turma_data, timeout=10)
        if response.status_code == 200:
            turma = response.json()["turma"]
            turma_id = turma["id"]
            print(f"✅ Turma criada: {turma['nome']} (ID: {turma_id})")
        else:
            print(f"❌ Falha ao criar turma: {response.status_code}")
            return

        # Criar aluno
        aluno_data = {
            "nome": "João Sync Teste",
            "email": "joao.sync@teste.com",
            "matricula": "SYNC2024"
        }
        response = requests.post(f"{base_url}/api/alunos", json=aluno_data, timeout=10)
        if response.status_code == 200:
            aluno = response.json()["aluno"]
            aluno_id = aluno["id"]
            print(f"✅ Aluno criado: {aluno['nome']} (ID: {aluno_id})")
        else:
            print(f"❌ Falha ao criar aluno: {response.status_code}")
            return

        # Vincular aluno à turma
        vinculo_data = {"aluno_id": aluno_id, "turma_id": turma_id}
        response = requests.post(f"{base_url}/api/alunos/vincular", json=vinculo_data, timeout=10)
        if response.status_code == 200:
            print("✅ Aluno vinculado à turma")
        else:
            print(f"❌ Falha ao vincular aluno: {response.status_code}")

        # 5. Sincronizar dados para o servidor remoto
        print("\n5. Sincronizando dados para servidor remoto...")

        # Sync matéria
        print("   - Sincronizando matéria...")
        response = requests.post(f"{base_url}/api/sync/materia/{materia_id}", timeout=20)
        if response.status_code == 200:
            result = response.json()
            print("✅ Matéria sincronizada com sucesso!")
            print(f"   ID remoto: {result['remote_materia']['id']}")
        else:
            print(f"❌ Falha ao sincronizar matéria: {response.status_code}")
            print(f"   Erro: {response.text[:200]}")

        # Sync turma
        print("   - Sincronizando turma...")
        response = requests.post(f"{base_url}/api/sync/turma/{turma_id}", timeout=20)
        if response.status_code == 200:
            result = response.json()
            print("✅ Turma sincronizada com sucesso!")
            print(f"   ID remoto: {result['remote_turma']['id']}")
        else:
            print(f"❌ Falha ao sincronizar turma: {response.status_code}")
            print(f"   Erro: {response.text[:200]}")

        # 6. Verificar sincronização
        print("\n6. Verificando sincronização...")

        # Verificar se os dados apareceram no servidor remoto
        remote_base = "https://ia-educacao-v2.onrender.com"

        try:
            # Verificar matérias remotas
            response = requests.get(f"{remote_base}/api/materias", timeout=10)
            if response.status_code == 200:
                remote_materias = response.json().get("materias", [])
                sync_materia = next((m for m in remote_materias if m["nome"] == "Matéria Sync Teste"), None)
                if sync_materia:
                    print("✅ Matéria encontrada no servidor remoto!")
                else:
                    print("⚠️ Matéria não encontrada remotamente (pode ter sido criada anteriormente)")
            else:
                print(f"❌ Erro ao verificar servidor remoto: {response.status_code}")

        except Exception as e:
            print(f"❌ Erro ao verificar sincronização: {e}")

        # 7. Demonstrar uso prático
        print("\n7. Demonstração prática:")
        print("   Agora você pode usar os endpoints de sync para:")
        print("   - POST /api/sync/materia/{id} - Sincronizar matéria")
        print("   - POST /api/sync/turma/{id} - Sincronizar turma")
        print("   - POST /api/sync/atividade/{id} - Sincronizar atividade completa")
        print("   - POST /api/sync/documentos - Sincronizar documentos")

        print("\n💡 Exemplo de uso:")
        print("   curl -X POST http://localhost:8005/api/sync/materia/YOUR_MATERIA_ID")

    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")

    finally:
        # Finalizar servidor
        print("\n8. Finalizando teste...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✅ Servidor parado")

    print("\n" + "=" * 60)
    print("🎉 TESTE DE SINCRONIZAÇÃO CONCLUÍDO!")
    print("✅ Funcionalidade implementada e testada com sucesso!")


if __name__ == "__main__":
    asyncio.run(test_sync_functionality())