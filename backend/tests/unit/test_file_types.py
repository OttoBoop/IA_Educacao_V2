"""
NOVO CR - Teste de Tipos de Arquivo

Testa:
1. Detecção de MIME types
2. Endpoints de download/view
3. Processamento de arquivos por modelos de IA (reasoning vs non-reasoning)

Uso:
    python test_file_types.py [--with-ai]
"""

import asyncio
import tempfile
import httpx
import pytest
from pathlib import Path
from datetime import datetime
import argparse
import json

# Importar o helper de MIME type
import sys
sys.path.insert(0, str(Path(__file__).parent))

from routes_chat import get_mime_type, MIME_TYPES


# ============================================================
# ARQUIVOS DE TESTE
# ============================================================

TEST_FILES = {
    # Documentos
    "documento.pdf": b"%PDF-1.4 fake pdf content",
    "texto.txt": b"Conteudo de texto simples para teste.",
    "pagina.html": b"<html><body><h1>Teste HTML</h1></body></html>",
    "dados.json": b'{"nome": "teste", "valor": 123}',
    "planilha.csv": b"nome,idade,cidade\nJoao,25,SP\nMaria,30,RJ",
    "documento.md": b"# Titulo\n\nParagrafo com **negrito**.",

    # Imagens (headers minimos para serem reconhecidos)
    "imagem.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
    "foto.jpg": b"\xff\xd8\xff\xe0" + b"\x00" * 100,
    "icone.gif": b"GIF89a" + b"\x00" * 100,

    # Codigo - Linguagens populares
    "script.py": b"def hello():\n    print('Ola mundo!')\n\nhello()",
    "app.js": b"function hello() {\n    console.log('Hello world!');\n}\nhello();",
    "Main.java": b"public class Main {\n    public static void main(String[] args) {\n        System.out.println(\"Hello\");\n    }\n}",
    "programa.c": b"#include <stdio.h>\nint main() {\n    printf(\"Hello\");\n    return 0;\n}",
    "app.cpp": b"#include <iostream>\nint main() {\n    std::cout << \"Hello\";\n    return 0;\n}",
    "Program.cs": b"using System;\nclass Program {\n    static void Main() {\n        Console.WriteLine(\"Hello\");\n    }\n}",
    "main.go": b"package main\nimport \"fmt\"\nfunc main() {\n    fmt.Println(\"Hello\")\n}",
    "main.rs": b"fn main() {\n    println!(\"Hello\");\n}",
    "script.rb": b"puts 'Hello world!'",
    "index.php": b"<?php\necho 'Hello world!';\n?>",

    # Config
    "config.yaml": b"app:\n  name: teste\n  port: 8000",
    "config.toml": b"[app]\nname = \"teste\"\nport = 8000",
    "query.sql": b"SELECT * FROM users WHERE active = true;",

    # Office (headers minimos)
    "documento.docx": b"PK\x03\x04" + b"\x00" * 100,  # ZIP header (DOCX is ZIP)
    "planilha.xlsx": b"PK\x03\x04" + b"\x00" * 100,

    # Arquivo desconhecido
    "arquivo.xyz": b"conteudo qualquer de formato desconhecido",
    "dados.weird123": b"formato totalmente inventado",
}


# ============================================================
# TESTE 1: DETECÇÃO DE MIME TYPE
# ============================================================

def check_mime_detection():
    """Testa se todos os tipos de arquivo são detectados corretamente (standalone script, not a pytest test)"""
    print("\n" + "=" * 60)
    print("TESTE 1: DETECÇÃO DE MIME TYPE")
    print("=" * 60)

    results = []

    for filename in TEST_FILES.keys():
        path = Path(filename)
        mime = get_mime_type(path)
        ext = path.suffix.lower()

        # Verificar se é um tipo conhecido ou fallback
        is_known = ext in MIME_TYPES
        status = "OK" if is_known else "FALLBACK"

        results.append({
            "arquivo": filename,
            "extensao": ext,
            "mime_type": mime,
            "status": status
        })

        print(f"  {filename:20} -> {mime:45} [{status}]")

    # Resumo
    known = sum(1 for r in results if r["status"] == "OK")
    fallback = len(results) - known

    print(f"\n  Resumo: {known} conhecidos, {fallback} fallback")
    return results


# ============================================================
# TESTE 2: ENDPOINTS HTTP
# ============================================================

@pytest.mark.integration
async def test_endpoints(base_url: str = "http://localhost:8000"):
    """Testa se os endpoints retornam os headers corretos.

    NOTA: Este teste requer servidor rodando. Use:
        uvicorn main:app --port 8000
    """
    print("\n" + "=" * 60)
    print("TESTE 2: ENDPOINTS HTTP (Content-Type headers)")
    print("=" * 60)

    # Check if server is running first
    async with httpx.AsyncClient(timeout=3.0) as client:
        try:
            await client.get(f"{base_url}/api/debug/routers")
        except Exception:
            pytest.skip("Servidor não está rodando (localhost:8000). Este teste requer servidor ativo.")

    # Criar arquivos temporários no diretório de chat_outputs
    from storage import storage
    output_dir = Path(storage.base_path) / "chat_outputs" / "test_files"
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        for filename, content in TEST_FILES.items():
            # Criar arquivo
            file_path = output_dir / filename
            file_path.write_bytes(content)

            try:
                # Testar endpoint de download (GET com stream para nao baixar tudo)
                url = f"{base_url}/api/chat/arquivos/download/test_files/{filename}"
                async with client.stream("GET", url) as response:
                    content_type = response.headers.get("content-type", "N/A")
                    status_code = response.status_code

                    status = "[OK]" if status_code == 200 else "[FAIL]"

                    results.append({
                        "arquivo": filename,
                        "status_code": status_code,
                        "content_type": content_type,
                    })

                    print(f"  {status} {filename:20} -> {content_type:40} (HTTP {status_code})")

            except Exception as e:
                print(f"  [FAIL] {filename:20} -> ERRO: {e}")
                results.append({
                    "arquivo": filename,
                    "status_code": 0,
                    "content_type": f"ERRO: {e}",
                })

    # Limpar arquivos de teste (com retry para Windows)
    import time
    time.sleep(0.5)  # Aguardar conexoes fecharem
    for filename in TEST_FILES.keys():
        try:
            (output_dir / filename).unlink(missing_ok=True)
        except:
            pass
    try:
        output_dir.rmdir()
    except:
        pass

    return results


# ============================================================
# TESTE 3: PROCESSAMENTO POR IA
# ============================================================

async def test_ai_processing(base_url: str = "http://localhost:8000"):
    """Testa como diferentes modelos processam arquivos"""
    print("\n" + "=" * 60)
    print("TESTE 3: PROCESSAMENTO POR MODELOS DE IA")
    print("=" * 60)

    # Buscar modelos disponíveis
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{base_url}/api/settings/models")
            if response.status_code != 200:
                print("  [FAIL] Não foi possível obter lista de modelos")
                return []

            modelos = response.json().get("models", [])
            if not modelos:
                print("  [FAIL] Nenhum modelo configurado")
                return []

        except Exception as e:
            print(f"  [FAIL] Erro ao conectar: {e}")
            return []

    # Separar modelos por tipo (reasoning vs non-reasoning)
    reasoning_models = []
    standard_models = []

    for m in modelos:
        model_name = m.get("modelo", "").lower()
        # Modelos de reasoning geralmente têm "o1", "o3", "thinking", "reason" no nome
        if any(x in model_name for x in ["o1", "o3", "thinking", "reason"]):
            reasoning_models.append(m)
        else:
            standard_models.append(m)

    print(f"\n  Modelos encontrados:")
    print(f"    - Standard: {len(standard_models)}")
    print(f"    - Reasoning: {len(reasoning_models)}")

    # Selecionar um de cada tipo para teste
    test_models = []
    if standard_models:
        test_models.append(("Standard", standard_models[0]))
    if reasoning_models:
        test_models.append(("Reasoning", reasoning_models[0]))

    if not test_models:
        print("  [FAIL] Nenhum modelo disponível para teste")
        return []

    # Arquivos para testar (subset representativo)
    test_subset = {
        "codigo.py": b"def soma(a, b):\n    return a + b\n\nprint(soma(2, 3))",
        "dados.json": b'{"alunos": [{"nome": "Ana", "nota": 8.5}, {"nome": "Bruno", "nota": 7.0}]}',
        "texto.txt": b"Este e um texto simples para analise.",
    }

    # Teste especial: Geracao de documentos
    print("\n  Teste de geracao de documentos:")
    print("  " + "-" * 50)

    doc_test_prompt = """Gere um documento CSV simples com 3 alunos e suas notas.
Use EXATAMENTE o formato:
```documento: notas_teste.csv
Nome,Nota
...
```"""

    if test_models:
        model_type, model = test_models[0]
        model_id = model.get("id")

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    f"{base_url}/api/chat",
                    json={
                        "messages": [{"role": "user", "content": doc_test_prompt}],
                        "model_id": model_id,
                        "context_docs": [],
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    resposta = data.get("resposta", "")

                    # Verificar se gerou documento no formato correto
                    if "```documento:" in resposta:
                        print("    [OK] Documento gerado no formato correto")
                        # Verificar extensao
                        if ".csv" in resposta:
                            print("    [OK] Extensao CSV detectada")
                        elif any(ext in resposta for ext in [".xlsx", ".xls", ".docx", ".pptx"]):
                            print("    [WARN] IA usou extensao nao suportada!")
                        results.append({"teste": "doc_generation", "sucesso": True})
                    else:
                        print("    [WARN] Documento nao gerado no formato esperado")
                        results.append({"teste": "doc_generation", "sucesso": False})
                else:
                    print(f"    [FAIL] HTTP {response.status_code}")
        except Exception as e:
            print(f"    [FAIL] Erro: {e}")

    results = []

    for model_type, model in test_models:
        model_id = model.get("id")
        model_name = model.get("modelo", model_id)
        print(f"\n  Testando modelo {model_type}: {model_name} ({model_id})")
        print("  " + "-" * 50)

        for filename, content in test_subset.items():
            # Criar arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                # Preparar mensagem com contexto do arquivo
                prompt = f"Analise brevemente o seguinte arquivo ({filename}):\n\n{content.decode('utf-8')}"

                # Chamar o chat
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        f"{base_url}/api/chat",
                        json={
                            "messages": [{"role": "user", "content": prompt}],
                            "model_id": model_id,
                            "context_docs": [],
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        resposta = data.get("resposta", "")[:100] + "..."
                        tokens = data.get("tokens_usados", {})

                        print(f"    [OK] {filename}")
                        print(f"      Tokens: entrada={tokens.get('entrada', '?')}, saida={tokens.get('saida', '?')}")
                        print(f"      Resposta: {resposta[:80]}...")

                        results.append({
                            "modelo": model_id,
                            "tipo": model_type,
                            "arquivo": filename,
                            "sucesso": True,
                            "tokens": tokens,
                        })
                    else:
                        print(f"    [FAIL] {filename} - HTTP {response.status_code}")
                        results.append({
                            "modelo": model_id,
                            "tipo": model_type,
                            "arquivo": filename,
                            "sucesso": False,
                            "erro": f"HTTP {response.status_code}",
                        })

            except Exception as e:
                print(f"    [FAIL] {filename} - Erro: {e}")
                results.append({
                    "modelo": model_id,
                    "tipo": model_type,
                    "arquivo": filename,
                    "sucesso": False,
                    "erro": str(e),
                })

            finally:
                Path(temp_path).unlink(missing_ok=True)

    return results


# ============================================================
# MAIN
# ============================================================

async def main():
    parser = argparse.ArgumentParser(description="Teste de tipos de arquivo - Prova AI")
    parser.add_argument("--with-ai", action="store_true", help="Incluir testes com modelos de IA")
    parser.add_argument("--base-url", default="http://localhost:8000", help="URL base da API")
    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("PROVA AI - TESTE DE TIPOS DE ARQUIVO")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Teste 1: MIME detection (sempre executa)
    mime_results = check_mime_detection()

    # Teste 2: Endpoints HTTP
    print("\n  Testando endpoints HTTP...")
    try:
        endpoint_results = await test_endpoints(args.base_url)
    except Exception as e:
        print(f"  [FAIL] Servidor não disponível: {e}")
        print("  (Execute o servidor com: uvicorn main:app)")
        endpoint_results = []

    # Teste 3: AI (opcional)
    ai_results = []
    if args.with_ai:
        try:
            ai_results = await test_ai_processing(args.base_url)
        except Exception as e:
            print(f"  [FAIL] Erro nos testes de IA: {e}")
    else:
        print("\n  (Use --with-ai para testar processamento por modelos)")

    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO FINAL")
    print("=" * 60)

    print(f"\n  MIME Types testados: {len(mime_results)}")

    if endpoint_results:
        success = sum(1 for r in endpoint_results if r.get("status_code") == 200)
        print(f"  Endpoints OK: {success}/{len(endpoint_results)}")

    if ai_results:
        success = sum(1 for r in ai_results if r.get("sucesso"))
        print(f"  Testes de IA OK: {success}/{len(ai_results)}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
