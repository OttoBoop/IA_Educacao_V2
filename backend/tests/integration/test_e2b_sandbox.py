#!/usr/bin/env python3
"""
Test script for syncing files between local storage and E2B sandbox
"""

import asyncio
import os
import tempfile
from pathlib import Path
import json

# Import our modules
from storage import storage
from models import TipoDocumento
from code_executor import get_executor


async def test_sync_to_e2b():
    """Test syncing files from local storage to E2B"""
    print("=== TESTE: SYNC LOCAL STORAGE -> E2B ===")

    # Check if E2B is configured
    executor = get_executor()
    available, msg = await executor.check_availability()
    if not available:
        print(f"E2B not available: {msg}")
        return

    print("E2B is available, proceeding...")

    # Create a test file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        test_content = "Este é um arquivo de teste para sincronização com E2B.\nConteúdo de exemplo."
        f.write(test_content.encode('utf-8'))
        temp_file = f.name

    try:
        # Create a test document in storage
        doc_id = storage.salvar_documento(
            arquivo_origem=temp_file,
            tipo=TipoDocumento.MATERIAL_APOIO,
            atividade_id="test_atividade",
            aluno_id="test_aluno",
            ia_provider=None,
            ia_modelo=None
        )

        print(f"Created test document with ID: {doc_id}")

        # Now sync to E2B
        from e2b_code_interpreter import Sandbox

        synced_files = []
        errors = []

        with Sandbox.create() as sandbox:
            documento = storage.get_documento(doc_id)
            if documento:
                with open(documento.caminho_arquivo, 'rb') as f:
                    content = f.read()

                target_path = f"/home/user/{documento.nome_arquivo}"
                sandbox.files.write(target_path, content)

                synced_files.append({
                    "documento_id": doc_id,
                    "filename": documento.nome_arquivo,
                    "target_path": target_path,
                    "size_bytes": len(content)
                })

                print(f"Synced file: {documento.nome_arquivo} -> {target_path}")

                # Verify the file exists in E2B
                try:
                    e2b_content = sandbox.files.read(target_path, format="bytes")
                    if e2b_content == content:
                        print("✓ File content matches!")
                    else:
                        print("✗ File content mismatch!")
                except Exception as e:
                    print(f"Error verifying file in E2B: {e}")

                # Test executing code that reads the file
                code = f"""
with open('{target_path}', 'r', encoding='utf-8') as f:
    content = f.read()
    print(f"Conteúdo do arquivo: {{content}}")
    print(f"Tamanho: {{len(content)}} caracteres")
"""
                execution = sandbox.run_code(code)
                print("Code execution result:")
                for log in execution.logs.stdout:
                    print(f"  {log}")

            else:
                errors.append(f"Document {doc_id} not found")

        print(f"Sync completed: {len(synced_files)} files synced, {len(errors)} errors")

    finally:
        # Cleanup
        os.unlink(temp_file)
        if 'doc_id' in locals():
            storage.deletar_documento(doc_id)


async def test_sync_from_e2b():
    """Test syncing files from E2B back to local storage"""
    print("\n=== TESTE: SYNC E2B -> LOCAL STORAGE ===")

    executor = get_executor()
    available, msg = await executor.check_availability()
    if not available:
        print(f"E2B not available: {msg}")
        return

    from e2b_code_interpreter import Sandbox

    # Create a file in E2B
    test_filename = "generated_from_e2b.json"
    test_data = {"teste": "sync", "timestamp": "2024-01-01", "data": [1, 2, 3]}

    with Sandbox.create() as sandbox:
        # Create file in E2B
        json_content = json.dumps(test_data, indent=2)
        sandbox.files.write(f"/home/user/{test_filename}", json_content.encode('utf-8'))

        # Execute code to generate another file
        code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 6))
plt.plot(x, y)
plt.title('Test Plot')
plt.xlabel('X')
plt.ylabel('Y')
plt.savefig('/home/user/test_plot.png')
plt.close()

print("Plot generated successfully")
"""
        execution = sandbox.run_code(code)
        print("Code execution for plot generation:")
        for log in execution.logs.stdout:
            print(f"  {log}")

        # Now sync files back to local
        files_to_download = [test_filename, "test_plot.png"]
        target_dir = "./data/e2b_downloads"
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        downloaded_files = []
        errors = []

        for filename in files_to_download:
            try:
                content = sandbox.files.read(f"/home/user/{filename}", format="bytes")
                local_path = Path(target_dir) / filename
                with open(local_path, 'wb') as f:
                    f.write(content)

                downloaded_files.append({
                    "filename": filename,
                    "local_path": str(local_path),
                    "size_bytes": len(content)
                })
                print(f"Downloaded: {filename} -> {local_path} ({len(content)} bytes)")

            except Exception as e:
                errors.append(f"Error downloading {filename}: {str(e)}")

        print(f"Download completed: {len(downloaded_files)} files downloaded, {len(errors)} errors")


async def main():
    """Run all sync tests"""
    print("Iniciando testes de sincronização Local Storage <-> E2B")
    print("=" * 60)

    await test_sync_to_e2b()
    await test_sync_from_e2b()

    print("\n" + "=" * 60)
    print("Testes concluídos!")


if __name__ == "__main__":
    asyncio.run(main())