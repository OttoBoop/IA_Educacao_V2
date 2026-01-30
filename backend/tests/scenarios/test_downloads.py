"""
PROVA AI - Teste End-to-End de Download de Documentos

Testa o fluxo COMPLETO:
1. Gera documento via chat
2. Processa como o frontend faria
3. Salva o arquivo
4. Valida se o arquivo abre corretamente

Uso:
    python test_download_e2e.py
"""

import asyncio
import httpx
import json
import re
import csv
import io
from pathlib import Path
from datetime import datetime


BASE_URL = "http://localhost:8000"
OUTPUT_DIR = Path("test_downloads")


# ============================================================
# CASOS DE TESTE - Formatos que DEVEM funcionar
# ============================================================

TEST_CASES = [
    {
        "nome": "CSV - Planilha",
        "prompt": """Gere um documento CSV com notas de 3 alunos.
```documento: notas_alunos.csv
Nome,Nota,Situacao
Ana Silva,9.0,Aprovado
Bruno Costa,7.5,Aprovado
Carlos Lima,5.0,Recuperacao
```""",
        "extensao": ".csv",
        "validar": "csv",
    },
    {
        "nome": "JSON - Dados",
        "prompt": """Gere um documento JSON com dados de uma turma.
```documento: turma_dados.json
{
  "turma": "3A",
  "professor": "Maria",
  "alunos": [
    {"nome": "Ana", "nota": 9.0},
    {"nome": "Bruno", "nota": 7.5}
  ]
}
```""",
        "extensao": ".json",
        "validar": "json",
    },
    {
        "nome": "Markdown - Relatorio",
        "prompt": """Gere um documento Markdown com um relatorio de correcao.
```documento: relatorio_correcao.md
# Relatorio de Correcao

**Aluno:** Maria Silva
**Disciplina:** Matematica
**Data:** 2026-01-28

## Resultado
- Nota: 8.5/10
- Situacao: Aprovado

## Comentarios
Bom desempenho geral.
```""",
        "extensao": ".md",
        "validar": "text",
    },
    {
        "nome": "TXT - Texto Simples",
        "prompt": """Gere um documento de texto simples com feedback.
```documento: feedback_aluno.txt
Caro aluno,

Seu desempenho na prova foi satisfatorio.
Continue se dedicando aos estudos.

Atenciosamente,
Professor
```""",
        "extensao": ".txt",
        "validar": "text",
    },
    {
        "nome": "HTML - Pagina",
        "prompt": """Gere um documento HTML com uma pagina de resultados.
```documento: resultados.html
<!DOCTYPE html>
<html>
<head><title>Resultados</title></head>
<body>
<h1>Resultados da Prova</h1>
<p>Turma: 3A</p>
<ul>
<li>Ana: 9.0</li>
<li>Bruno: 7.5</li>
</ul>
</body>
</html>
```""",
        "extensao": ".html",
        "validar": "html",
    },
    {
        "nome": "Python - Codigo",
        "prompt": """Gere um documento Python com uma funcao de calculo de media.
```documento: calcular_media.py
def calcular_media(notas):
    \"\"\"Calcula a media de uma lista de notas.\"\"\"
    if not notas:
        return 0
    return sum(notas) / len(notas)

# Exemplo de uso
notas = [9.0, 7.5, 8.0]
print(f"Media: {calcular_media(notas)}")
```""",
        "extensao": ".py",
        "validar": "python",
    },
]

# Casos de conversao (extensoes que serao convertidas)
CONVERSION_CASES = [
    {
        "nome": "XLSX -> CSV",
        "prompt": """Gere uma planilha Excel com dados.
```documento: planilha.xlsx
| Produto | Quantidade | Preco |
|---------|------------|-------|
| Item A  | 10         | 25.00 |
| Item B  | 5          | 15.00 |
```""",
        "extensao_original": ".xlsx",
        "extensao_convertida": ".csv",
        "validar": "csv",
    },
    {
        "nome": "DOCX -> MD",
        "prompt": """Gere um documento Word com texto formatado.
```documento: documento.docx
# Titulo do Documento

Este e um documento de exemplo.

## Secao 1
Conteudo da secao.

## Secao 2
Mais conteudo aqui.
```""",
        "extensao_original": ".docx",
        "extensao_convertida": ".md",
        "validar": "text",
    },
]


# ============================================================
# FUNCOES DE PROCESSAMENTO (Simula o frontend)
# ============================================================

def extract_document(response_text: str) -> dict:
    """Extrai documento da resposta (igual ao frontend)"""
    pattern = r'```\s*documento\s*:\s*([^\n]+)\n([\s\S]*?)```'
    match = re.search(pattern, response_text, re.IGNORECASE)

    if match:
        titulo = match.group(1).strip()
        conteudo = match.group(2).strip()
        ext_match = re.search(r'\.([a-zA-Z0-9]+)$', titulo)
        extensao = f".{ext_match.group(1).lower()}" if ext_match else ".txt"

        return {
            "encontrado": True,
            "titulo": titulo,
            "extensao": extensao,
            "conteudo": conteudo,
        }
    return {"encontrado": False}


def convert_markdown_table_to_csv(markdown: str) -> str:
    """Converte tabela markdown para CSV (igual ao frontend)"""
    lines = markdown.split('\n')
    csv_lines = []

    for line in lines:
        trimmed = line.strip()
        if trimmed.startswith('|') and trimmed.endswith('|'):
            # Ignorar linha separadora
            if re.match(r'^\|[\s\-:]+\|$', trimmed):
                continue
            # Extrair celulas
            cells = [c.strip() for c in trimmed.split('|')[1:-1]]
            # Escapar para CSV
            escaped = []
            for cell in cells:
                if ',' in cell or '"' in cell:
                    cell = '"' + cell.replace('"', '""') + '"'
                escaped.append(cell)
            csv_lines.append(','.join(escaped))

    return '\n'.join(csv_lines) if csv_lines else markdown


def process_download(doc: dict) -> tuple:
    """Processa documento para download (simula frontend)"""
    titulo = doc["titulo"]
    conteudo = doc["conteudo"]
    extensao = doc["extensao"]

    nome_arquivo = titulo
    conteudo_final = conteudo
    convertido = False

    if extensao in ['.xlsx', '.xls']:
        nome_arquivo = re.sub(r'\.xlsx?$', '.csv', titulo, flags=re.IGNORECASE)
        conteudo_final = convert_markdown_table_to_csv(conteudo)
        extensao = '.csv'
        convertido = True

    elif extensao in ['.docx', '.doc']:
        nome_arquivo = re.sub(r'\.docx?$', '.md', titulo, flags=re.IGNORECASE)
        extensao = '.md'
        convertido = True

    elif extensao in ['.pptx', '.ppt']:
        nome_arquivo = re.sub(r'\.pptx?$', '.md', titulo, flags=re.IGNORECASE)
        extensao = '.md'
        convertido = True

    elif extensao == '.pdf':
        nome_arquivo = re.sub(r'\.pdf$', '.html', titulo, flags=re.IGNORECASE)
        extensao = '.html'
        convertido = True

    return nome_arquivo, conteudo_final, extensao, convertido


# ============================================================
# VALIDADORES
# ============================================================

def validar_csv(conteudo: str, filepath: Path) -> tuple:
    """Valida se o CSV e valido"""
    try:
        reader = csv.reader(io.StringIO(conteudo))
        rows = list(reader)
        if len(rows) < 2:
            return False, "CSV com menos de 2 linhas"
        if len(rows[0]) < 2:
            return False, "CSV com menos de 2 colunas"
        return True, f"CSV valido: {len(rows)} linhas, {len(rows[0])} colunas"
    except Exception as e:
        return False, f"Erro ao parsear CSV: {e}"


def validar_json(conteudo: str, filepath: Path) -> tuple:
    """Valida se o JSON e valido"""
    try:
        data = json.loads(conteudo)
        return True, f"JSON valido: {type(data).__name__}"
    except json.JSONDecodeError as e:
        return False, f"JSON invalido: {e}"


def validar_text(conteudo: str, filepath: Path) -> tuple:
    """Valida se o texto tem conteudo"""
    if len(conteudo.strip()) < 10:
        return False, "Texto muito curto"
    return True, f"Texto valido: {len(conteudo)} chars"


def validar_html(conteudo: str, filepath: Path) -> tuple:
    """Valida se o HTML tem estrutura basica"""
    has_tag = '<' in conteudo and '>' in conteudo
    if not has_tag:
        # Se nao tem tags, pode ser markdown que sera convertido
        if len(conteudo) > 10:
            return True, "Conteudo texto (sera HTML quando aberto)"
        return False, "HTML sem tags e muito curto"
    return True, "HTML valido"


def validar_python(conteudo: str, filepath: Path) -> tuple:
    """Valida se o Python tem sintaxe valida"""
    try:
        compile(conteudo, filepath, 'exec')
        return True, "Python com sintaxe valida"
    except SyntaxError as e:
        return False, f"Erro de sintaxe Python: {e}"


VALIDADORES = {
    "csv": validar_csv,
    "json": validar_json,
    "text": validar_text,
    "html": validar_html,
    "python": validar_python,
}


# ============================================================
# FUNCAO DE TESTE
# ============================================================

async def run_test(client: httpx.AsyncClient, model_id: str, test_case: dict, is_conversion: bool = False) -> dict:
    """Executa um teste completo"""
    result = {
        "nome": test_case["nome"],
        "sucesso": False,
        "etapas": [],
    }

    # 1. Gerar documento via chat
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
            result["etapas"].append(f"[FAIL] Chat retornou HTTP {response.status_code}")
            return result

        data = response.json()
        resposta = data.get("response", "") or data.get("resposta", "")
        result["etapas"].append("[OK] Chat respondeu")

    except Exception as e:
        result["etapas"].append(f"[FAIL] Erro no chat: {e}")
        return result

    # 2. Extrair documento
    doc = extract_document(resposta)
    if not doc["encontrado"]:
        result["etapas"].append("[FAIL] Documento nao encontrado na resposta")
        result["resposta_preview"] = resposta[:300]
        return result
    result["etapas"].append(f"[OK] Documento extraido: {doc['titulo']}")

    # 3. Processar para download
    nome_arquivo, conteudo_final, extensao, convertido = process_download(doc)

    if is_conversion:
        if convertido:
            result["etapas"].append(f"[OK] Convertido: {doc['extensao']} -> {extensao}")
        else:
            result["etapas"].append(f"[WARN] Nao foi necessario converter")

    # 4. Salvar arquivo
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / nome_arquivo

    try:
        filepath.write_text(conteudo_final, encoding='utf-8')
        result["etapas"].append(f"[OK] Arquivo salvo: {filepath}")
        result["arquivo"] = str(filepath)
    except Exception as e:
        result["etapas"].append(f"[FAIL] Erro ao salvar: {e}")
        return result

    # 5. Validar conteudo
    validador = VALIDADORES.get(test_case["validar"], validar_text)
    valido, msg = validador(conteudo_final, filepath)

    if valido:
        result["etapas"].append(f"[OK] Validacao: {msg}")
        result["sucesso"] = True
    else:
        result["etapas"].append(f"[FAIL] Validacao: {msg}")

    return result


# ============================================================
# MAIN
# ============================================================

async def main():
    print("\n" + "=" * 70)
    print("PROVA AI - TESTE END-TO-END DE DOWNLOAD")
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Limpar diretorio de saida
    if OUTPUT_DIR.exists():
        for f in OUTPUT_DIR.iterdir():
            f.unlink()

    async with httpx.AsyncClient() as client:
        # Obter modelo
        response = await client.get(f"{BASE_URL}/api/settings/models")
        if response.status_code != 200:
            print("\n[FAIL] Nao foi possivel obter modelos")
            return

        models = response.json().get("models", [])
        model_id = None
        for m in models:
            if m.get("is_default"):
                model_id = m.get("id")
                break
        if not model_id and models:
            model_id = models[0].get("id")

        if not model_id:
            print("\n[FAIL] Nenhum modelo configurado")
            return

        print(f"\nModelo: {model_id}")
        print(f"Diretorio de saida: {OUTPUT_DIR.absolute()}")

        # Teste 1: Formatos nativos
        print("\n" + "-" * 70)
        print("TESTE 1: FORMATOS NATIVOS")
        print("-" * 70)

        results_nativos = []
        for tc in TEST_CASES:
            print(f"\n  [{tc['nome']}]")
            result = await run_test(client, model_id, tc)
            results_nativos.append(result)

            for etapa in result["etapas"]:
                print(f"    {etapa}")

        # Teste 2: Conversoes
        print("\n" + "-" * 70)
        print("TESTE 2: CONVERSOES AUTOMATICAS")
        print("-" * 70)

        results_conversao = []
        for tc in CONVERSION_CASES:
            print(f"\n  [{tc['nome']}]")
            result = await run_test(client, model_id, tc, is_conversion=True)
            results_conversao.append(result)

            for etapa in result["etapas"]:
                print(f"    {etapa}")

        # Resumo
        print("\n" + "=" * 70)
        print("RESUMO")
        print("=" * 70)

        nativos_ok = sum(1 for r in results_nativos if r["sucesso"])
        conversao_ok = sum(1 for r in results_conversao if r["sucesso"])

        print(f"\n  Formatos Nativos: {nativos_ok}/{len(results_nativos)}")
        print(f"  Conversoes: {conversao_ok}/{len(results_conversao)}")

        total_ok = nativos_ok + conversao_ok
        total = len(results_nativos) + len(results_conversao)

        print(f"\n  TOTAL: {total_ok}/{total} testes passaram")

        if total_ok < total:
            print("\n  Falhas:")
            for r in results_nativos + results_conversao:
                if not r["sucesso"]:
                    print(f"    - {r['nome']}")
                    for e in r["etapas"]:
                        if "[FAIL]" in e:
                            print(f"      {e}")

        # Listar arquivos gerados
        print("\n" + "-" * 70)
        print("ARQUIVOS GERADOS")
        print("-" * 70)

        if OUTPUT_DIR.exists():
            for f in sorted(OUTPUT_DIR.iterdir()):
                size = f.stat().st_size
                print(f"  {f.name:30} ({size:,} bytes)")

        print("\n" + "=" * 70)
        print(f"Arquivos salvos em: {OUTPUT_DIR.absolute()}")
        print("Verifique se os arquivos abrem corretamente!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
