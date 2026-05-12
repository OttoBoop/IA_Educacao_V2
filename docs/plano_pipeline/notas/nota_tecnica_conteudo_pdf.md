# Nota Tecnica: `/api/documentos/{id}/conteudo` nao le PDFs de `prova_respondida`

**Data:** 2026-04-17
**Status:** ESCLARECIDO -- limitacao do endpoint `/conteudo`; nao classificar PDF como fantasma so por `conteudo=null`

---

## Resumo

Documentos `prova_respondida` em PDF podem retornar `conteudo: null` quando acessados
via `/api/documentos/{id}/conteudo`. Isso **nao prova que o documento esta vazio** --
e uma limitacao conhecida desse endpoint especifico, que so sabe ler arquivos `.json`,
`.txt` e `.md`.

**Os arquivos PDF estao intactos e acessiveis via outros endpoints.**

---

## Causa Raiz

O endpoint `/api/documentos/{id}/conteudo` (em `routes_prompts.py`, linhas 458-525)
tem um bloco condicional que so le 3 tipos de extensao:

```python
if documento.extensao.lower() == '.json':
    # le e retorna JSON parseado
elif documento.extensao.lower() in ['.txt', '.md']:
    # le e retorna texto
# ELSE: cai no return final com conteudo=None
```

Para PDFs (`.pdf`), nenhuma dessas condicoes e verdadeira, entao o endpoint retorna:
```json
{
  "tipo_conteudo": "arquivo",
  "conteudo": null,
  "pode_visualizar": false
}
```

---

## Evidencia: Arquivos estao intactos

Teste com o aluno **Eric Manoel Ribeiro de Sousa** (id `660e9421b246ad3f`),
atividade Lista0 (id `126e8b5ad7dd6d59`), documento `f60d37284d616ca4`:

| Endpoint | Resultado |
|----------|-----------|
| `/api/documentos/{id}/conteudo` | `conteudo: null`, `tipo_conteudo: "arquivo"` |
| `/api/documentos/{id}/download` | **HTTP 200**, 1.381.496 bytes, `application/pdf` |
| `/api/documentos/{id}/view` | **HTTP 200**, 1.381.496 bytes, `application/pdf` |

O PDF baixado e valido: "PDF document, version 1.4, 6 page(s)".

O campo `caminho_arquivo` no banco aponta para o caminho correto no Supabase Storage:
```
arquivos/57861d16958965d2/3f3ab03dfe783f30/126e8b5ad7dd6d59/660e9421b246ad3f/Eric Manoel Ribeiro de Sousa - ALA-Lista0.pdf_16e6.pdf
```

---

## Fluxo de Upload (funciona corretamente)

1. Professor faz upload via `POST /api/documentos/upload` (em `main_v2.py`, linha 648)
2. Arquivo e salvo em temp, depois copiado para a arvore de diretorios local
3. `storage.salvar_documento()` registra no banco (PostgreSQL/Supabase) com:
   - `caminho_arquivo` = caminho relativo no storage
   - `extensao` = `.pdf`
   - `tamanho_bytes` = tamanho real do arquivo
4. Arquivo e uploaded para Supabase Storage (persistencia cloud)

Nenhum conteudo textual e extraido do PDF nesse momento -- o arquivo e armazenado como
blob binario, nao como texto no banco.

---

## Tres Endpoints de Acesso a Documentos

| Endpoint | Retorna | Funciona com PDF? |
|----------|---------|-------------------|
| `/api/documentos/{id}/conteudo` | JSON com campo `conteudo` (texto/json parseado) | **NAO** -- retorna `null` |
| `/api/documentos/{id}/download` | `FileResponse` com `Content-Disposition: attachment` | **SIM** |
| `/api/documentos/{id}/view` | `FileResponse` com `Content-Disposition: inline` | **SIM** |

---

## Impacto no Pipeline

O pipeline usa `_ler_conteudo_documento()` (linha 437 de `routes_prompts.py`) para
alimentar os prompts de IA. Essa funcao tem o mesmo comportamento:

```python
if doc.extensao.lower() == '.json':
    # retorna JSON como string
elif doc.extensao.lower() in ['.txt', '.md']:
    # retorna texto
else:
    return f"[Arquivo: {doc.nome_arquivo}]"
```

Ou seja, quando o pipeline tenta usar a `prova_respondida` (PDF) como input para a
etapa `extrair_respostas`, ele recebe apenas `"[Arquivo: nome.pdf]"` -- **nao o conteudo
real do PDF**.

Isso significa que o pipeline depende de **outra forma** de processar PDFs. Verificar
se o `executor.py` usa visao (multimodal) ou extrai texto do PDF de outra maneira.

---

## Proximos Passos

1. **Para quem consome a API (frontend, scripts):**
   - Usar `/api/documentos/{id}/download` ou `/api/documentos/{id}/view` para acessar PDFs
   - O endpoint `/conteudo` so e util para JSONs gerados pelo pipeline

2. **Para o pipeline de correcao:**
   - Investigar como `executor.py` alimenta PDFs para a IA (provavelmente via
     multimodal/visao, nao via texto)
   - Se nao houver extracao de texto de PDF, isso e um gap real no pipeline

3. **Melhoria opcional no `/conteudo`:**
   - Adicionar suporte a extrair texto de PDF (com PyPDF2, pdfplumber, etc.)
   - Ou retornar URL de download em vez de `null` para arquivos binarios
