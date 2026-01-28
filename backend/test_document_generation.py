"""
PROVA AI - Teste de Geracao de Documentos

Testa a geracao de documentos pela IA em diferentes formatos.
Verifica:
1. Se a IA gera documentos no formato correto
2. Se o conteudo e valido para cada formato
3. Se a conversao de formatos nao suportados funciona

Uso:
    python test_document_generation.py
"""

import asyncio
import httpx
import json
import re
from datetime import datetime


BASE_URL = "http://localhost:8000"


# ============================================================
# CASOS DE TESTE
# ============================================================

TEST_CASES = [
    {
        "nome": "CSV Simples",
        "prompt": """Gere um documento CSV com 3 alunos e notas.
Use EXATAMENTE este formato (com as 3 crases):
```documento: alunos.csv
Nome,Nota
Ana,9.0
Bruno,8.5
Carlos,7.0
```""",
        "extensao_esperada": ".csv",
        "validacao": lambda c: "," in c and len(c.strip().split("\n")) >= 2,
    },
    {
        "nome": "JSON Estruturado",
        "prompt": """Gere um documento JSON com dados de alunos.
Use EXATAMENTE este formato (com as 3 crases):
```documento: dados.json
{
  "alunos": [{"nome": "Ana", "nota": 9}]
}
```""",
        "extensao_esperada": ".json",
        "validacao": lambda c: c.strip().startswith("{") or c.strip().startswith("["),
    },
    {
        "nome": "Markdown Relatorio",
        "prompt": """Gere um documento Markdown com um relatorio breve.
Use EXATAMENTE este formato (com as 3 crases):
```documento: relatorio.md
# Titulo
Conteudo aqui
```""",
        "extensao_esperada": ".md",
        "validacao": lambda c: "#" in c or "**" in c or len(c) > 10,
    },
    {
        "nome": "Texto Simples",
        "prompt": """Gere um documento de texto simples com um feedback.
Use EXATAMENTE este formato (com as 3 crases):
```documento: feedback.txt
Seu feedback aqui
```""",
        "extensao_esperada": ".txt",
        "validacao": lambda c: len(c.strip()) > 5,
    },
]

# Casos para testar se a IA evita extensoes proibidas
FORBIDDEN_EXTENSION_TESTS = [
    {
        "nome": "Deve usar CSV ao inves de XLSX",
        "prompt": """Gere uma planilha com dados de vendas.
IMPORTANTE: Use .csv (NAO .xlsx). Formato:
```documento: vendas.csv
Produto,Quantidade,Preco
Item1,10,25.00
```""",
        "extensao_proibida": ".xlsx",
        "extensao_correta": ".csv",
    },
    {
        "nome": "Deve usar MD ao inves de DOCX",
        "prompt": """Gere um documento com texto formatado.
IMPORTANTE: Use .md (NAO .docx). Formato:
```documento: texto.md
# Titulo
Conteudo
```""",
        "extensao_proibida": ".docx",
        "extensao_correta": ".md",
    },
]


# ============================================================
# FUNCOES DE TESTE
# ============================================================

def extract_document_from_response(response_text: str) -> dict:
    """Extrai documento da resposta da IA"""
    # Padrao: ```documento: nome.ext\nconteudo\n```
    pattern = r'```\s*documento\s*:\s*([^\n]+)\n([\s\S]*?)```'
    match = re.search(pattern, response_text, re.IGNORECASE)

    if match:
        titulo = match.group(1).strip()
        conteudo = match.group(2).strip()

        # Extrair extensao
        ext_match = re.search(r'\.([a-zA-Z0-9]+)$', titulo)
        extensao = f".{ext_match.group(1).lower()}" if ext_match else ".txt"

        return {
            "encontrado": True,
            "titulo": titulo,
            "extensao": extensao,
            "conteudo": conteudo,
        }

    return {"encontrado": False}


async def get_default_model(client: httpx.AsyncClient) -> str:
    """Obtem o modelo padrao configurado"""
    response = await client.get(f"{BASE_URL}/api/settings/models")
    if response.status_code == 200:
        models = response.json().get("models", [])
        # Procurar modelo padrao ou pegar o primeiro
        for m in models:
            if m.get("is_default"):
                return m.get("id")
        if models:
            return models[0].get("id")
    return None


async def test_document_generation(client: httpx.AsyncClient, model_id: str, test_case: dict) -> dict:
    """Executa um teste de geracao de documento"""
    result = {
        "nome": test_case["nome"],
        "sucesso": False,
        "detalhes": [],
    }

    try:
        response = await client.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": test_case["prompt"]}],
                "model_id": model_id,
                "context_docs": [],
            },
            timeout=90.0
        )

        if response.status_code != 200:
            result["detalhes"].append(f"HTTP {response.status_code}")
            return result

        data = response.json()
        resposta = data.get("response", "") or data.get("resposta", "")

        # Extrair documento
        doc = extract_document_from_response(resposta)

        if not doc["encontrado"]:
            result["detalhes"].append("Documento nao encontrado na resposta")
            result["resposta_raw"] = resposta[:800]
            print(f"\n    DEBUG - Resposta da IA:\n    {resposta[:500]}...")
            return result

        result["documento"] = doc

        # Verificar extensao
        ext_esperada = test_case.get("extensao_esperada")
        if ext_esperada and doc["extensao"] != ext_esperada:
            result["detalhes"].append(f"Extensao incorreta: {doc['extensao']} (esperado: {ext_esperada})")
        else:
            result["detalhes"].append(f"Extensao OK: {doc['extensao']}")

        # Validar conteudo
        validacao = test_case.get("validacao")
        if validacao:
            if validacao(doc["conteudo"]):
                result["detalhes"].append("Conteudo valido")
                result["sucesso"] = True
            else:
                result["detalhes"].append("Conteudo invalido")
                result["conteudo_preview"] = doc["conteudo"][:200]
        else:
            result["sucesso"] = True

    except Exception as e:
        result["detalhes"].append(f"Erro: {e}")

    return result


async def test_forbidden_extensions(client: httpx.AsyncClient, model_id: str, test_case: dict) -> dict:
    """Testa se a IA evita extensoes proibidas"""
    result = {
        "nome": test_case["nome"],
        "sucesso": False,
        "detalhes": [],
    }

    try:
        response = await client.post(
            f"{BASE_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": test_case["prompt"]}],
                "model_id": model_id,
                "context_docs": [],
            },
            timeout=90.0
        )

        if response.status_code != 200:
            result["detalhes"].append(f"HTTP {response.status_code}")
            return result

        data = response.json()
        resposta = data.get("response", "") or data.get("resposta", "")

        doc = extract_document_from_response(resposta)

        if not doc["encontrado"]:
            result["detalhes"].append("Documento nao gerado")
            return result

        ext_proibida = test_case["extensao_proibida"]
        ext_correta = test_case["extensao_correta"]

        if doc["extensao"] == ext_proibida:
            result["detalhes"].append(f"FALHA: IA usou extensao proibida {ext_proibida}")
        elif doc["extensao"] == ext_correta:
            result["detalhes"].append(f"OK: IA usou extensao correta {ext_correta}")
            result["sucesso"] = True
        else:
            result["detalhes"].append(f"IA usou extensao alternativa: {doc['extensao']}")
            result["sucesso"] = True  # Qualquer coisa diferente da proibida e aceitavel

    except Exception as e:
        result["detalhes"].append(f"Erro: {e}")

    return result


# ============================================================
# MAIN
# ============================================================

async def main():
    print("\n" + "=" * 70)
    print("PROVA AI - TESTE DE GERACAO DE DOCUMENTOS")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    async with httpx.AsyncClient() as client:
        # Obter modelo
        model_id = await get_default_model(client)
        if not model_id:
            print("\n[FAIL] Nenhum modelo configurado!")
            return

        print(f"\nModelo: {model_id}")

        # Teste 1: Geracao de documentos
        print("\n" + "-" * 70)
        print("TESTE 1: GERACAO DE DOCUMENTOS")
        print("-" * 70)

        doc_results = []
        for tc in TEST_CASES:
            print(f"\n  Testando: {tc['nome']}...")
            result = await test_document_generation(client, model_id, tc)
            doc_results.append(result)

            status = "[OK]" if result["sucesso"] else "[FAIL]"
            print(f"    {status} {', '.join(result['detalhes'])}")

            if "documento" in result:
                print(f"    Titulo: {result['documento']['titulo']}")
                print(f"    Tamanho: {len(result['documento']['conteudo'])} chars")

        # Teste 2: Extensoes proibidas
        print("\n" + "-" * 70)
        print("TESTE 2: EXTENSOES PROIBIDAS")
        print("-" * 70)

        ext_results = []
        for tc in FORBIDDEN_EXTENSION_TESTS:
            print(f"\n  Testando: {tc['nome']}...")
            result = await test_forbidden_extensions(client, model_id, tc)
            ext_results.append(result)

            status = "[OK]" if result["sucesso"] else "[WARN]"
            print(f"    {status} {', '.join(result['detalhes'])}")

        # Resumo
        print("\n" + "=" * 70)
        print("RESUMO")
        print("=" * 70)

        doc_ok = sum(1 for r in doc_results if r["sucesso"])
        ext_ok = sum(1 for r in ext_results if r["sucesso"])

        print(f"\n  Geracao de Documentos: {doc_ok}/{len(doc_results)}")
        print(f"  Extensoes Proibidas: {ext_ok}/{len(ext_results)}")

        total_ok = doc_ok + ext_ok
        total = len(doc_results) + len(ext_results)

        print(f"\n  TOTAL: {total_ok}/{total} testes passaram")

        if total_ok < total:
            print("\n  Testes que falharam:")
            for r in doc_results + ext_results:
                if not r["sucesso"]:
                    print(f"    - {r['nome']}: {', '.join(r['detalhes'])}")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
