"""
Teste simples de download de documentos
"""

import asyncio
import httpx
import re
from pathlib import Path

BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("test_downloads")

# Extensoes para testar
EXTENSOES = [".csv", ".json", ".md", ".txt", ".html", ".py", ".xlsx", ".docx"]


async def main():
    print("\n=== TESTE DE DOWNLOAD ===\n")

    OUTPUT_DIR.mkdir(exist_ok=True)

    async with httpx.AsyncClient() as client:
        # Pegar modelo
        resp = await client.get(f"{BASE_URL}/api/settings/models")
        models = resp.json().get("models", [])
        model_id = models[0]["id"] if models else None

        if not model_id:
            print("Nenhum modelo!")
            return

        for ext in EXTENSOES:
            print(f"\nTestando {ext}...")

            prompt = f"""Gere um documento de exemplo.
```documento: teste{ext}
Conteudo de exemplo para {ext}
```"""

            resp = await client.post(
                f"{BASE_URL}/api/chat",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "model_id": model_id,
                    "context_docs": [],
                },
                timeout=60.0
            )

            if resp.status_code != 200:
                print(f"  [FAIL] HTTP {resp.status_code}")
                continue

            resposta = resp.json().get("response", "")

            # Extrair documento
            match = re.search(r'```\s*documento\s*:\s*([^\n]+)\n([\s\S]*?)```', resposta, re.I)

            if not match:
                print(f"  [FAIL] Documento nao encontrado")
                continue

            nome = match.group(1).strip()
            conteudo = match.group(2).strip()

            # Salvar arquivo
            filepath = OUTPUT_DIR / nome
            filepath.write_text(conteudo, encoding='utf-8')

            print(f"  [OK] {nome} ({len(conteudo)} bytes)")

    # Listar arquivos
    print("\n=== ARQUIVOS GERADOS ===\n")
    for f in sorted(OUTPUT_DIR.iterdir()):
        print(f"  {f.name} ({f.stat().st_size} bytes)")

    print(f"\nArquivos em: {OUTPUT_DIR.absolute()}")
    print("Tente abrir cada um!")


if __name__ == "__main__":
    asyncio.run(main())
