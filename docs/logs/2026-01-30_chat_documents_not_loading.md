# Chat Documents Not Loading Bug

**Date:** 2026-01-30
**Status:** RESOLVED
**Commits:** `bfd04c7`, `64255e0`, `e6dbaff`, `8aa3697`, `5b04366`, `821cfdf`

## Problem

The chat system was not loading documents even though the frontend showed 161 documents selected. The AI responded saying it had no access to any documents.

## Symptoms

1. Frontend displayed "161 documentos selecionados" correctly
2. Chat API returned responses like "Não tenho acesso a nenhum documento"
3. `context_docs` array was being sent correctly in API requests
4. Debug endpoint `/api/debug/documento/{id}` showed documents existed and could be resolved

## Root Cause Analysis

**Multiple issues were found:**

1. **Primary Issue: Storage import location** ([routes_chat.py:28](IA_Educacao_V2/backend/routes_chat.py#L28))
   - `storage` was imported INSIDE functions instead of at the module level
   - This caused inconsistent storage instance behavior
   - Debug endpoint worked because it imported at module level

2. **Secondary Issue: Path normalization** ([storage.py](IA_Educacao_V2/backend/storage.py))
   - Windows paths with backslashes (`data\arquivos\...`) weren't normalized
   - Caused path duplication: `/opt/render/.../data/data\arquivos\...`

3. **Tertiary Issue: Files not in Supabase**
   - Document records existed in SQLite database
   - Actual files were never uploaded to Supabase Storage
   - Render's ephemeral filesystem couldn't find local files

## Solution Implemented

### 1. Fix storage import ([routes_chat.py](IA_Educacao_V2/backend/routes_chat.py))

```python
# Before (line 262, inside function):
from storage import storage

# After (line 28, module level):
from storage import storage
```

### 2. Path normalization ([storage.py](IA_Educacao_V2/backend/storage.py))

```python
def resolver_caminho_documento(self, documento: Documento) -> Path:
    # Normalize: convert backslashes to forward slashes
    caminho_str = documento.caminho_arquivo.replace('\\', '/')

    # Remove duplicate 'data/' prefix
    remote_path = caminho_str
    if remote_path.startswith('data/'):
        remote_path = remote_path[5:]
```

### 3. Supabase sync script ([sync_to_supabase.py](IA_Educacao_V2/backend/sync_to_supabase.py))

Created script to upload all local files to Supabase:
- Iterates through all matérias → turmas → atividades → documentos
- Uploads each file to Supabase Storage
- Reports success/failure counts
- **Result:** 796 documents synced, 0 failures

### 4. Debug endpoint ([routes_extras.py:624](IA_Educacao_V2/backend/routes_extras.py#L624))

Added `/api/debug/documento/{id}` to diagnose document loading:
- Checks database record
- Checks local file existence
- Checks Supabase status
- Tests resolver function

## Tests Used

### Manual API Tests (curl)

```bash
# Test chat with document context
curl -s -X POST "https://ia-educacao-v2.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages":[{"role":"user","content":"Quais documentos voce tem acesso?"}],
    "model_id":"588f3efe7975",
    "context_docs":["af433f076af01ac6","a1d3701843bf5683","06b451adae2c300c"]
  }'

# Debug specific document
curl -s "https://ia-educacao-v2.onrender.com/api/debug/documento/af433f076af01ac6"

# List all documents
curl -s "https://ia-educacao-v2.onrender.com/api/documentos/todos"
```

### Expected Debug Response

```json
{
  "documento_id": "af433f076af01ac6",
  "etapas": {
    "1_banco_dados": {"encontrado": true, "nome_arquivo": "..."},
    "2_arquivo_local": {"caminho_direto_existe": false},
    "3_supabase": {"habilitado": true},
    "4_resolver_caminho": {"sucesso": true, "existe": true}
  }
}
```

### Expected Chat Response

Should list document names, NOT say "Não tenho acesso a nenhum documento".

## Verification Commands

```bash
# 1. Check debug endpoint works
curl -s "https://ia-educacao-v2.onrender.com/api/debug/documento/af433f076af01ac6" | grep '"sucesso":true'

# 2. Test chat with documents (should mention file names)
curl -s -X POST "https://ia-educacao-v2.onrender.com/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Liste os documentos"}],"model_id":"588f3efe7975","context_docs":["af433f076af01ac6"]}' \
  | grep -i "tmp5udocm0j"

# 3. Check Supabase has files (via debug)
curl -s "https://ia-educacao-v2.onrender.com/api/debug/documento/af433f076af01ac6" | grep '"habilitado":true'
```

## Files Changed

| File | Change |
|------|--------|
| `backend/routes_chat.py` | Move storage import to module level |
| `backend/storage.py` | Normalize paths, prioritize Supabase |
| `backend/routes_extras.py` | Add debug endpoint |
| `backend/main_v2.py` | Fix download endpoint |
| `backend/sync_to_supabase.py` | New sync script |
| `frontend/index_v2.html` | Replace CDN icons with emojis |

## Lessons Learned

1. **Import location matters** - Module-level imports ensure consistent singleton behavior
2. **Debug endpoints are invaluable** - The `/api/debug/documento/{id}` endpoint revealed the issue quickly
3. **Path normalization is critical** - Windows/Linux path differences cause subtle bugs
4. **Verify deployments** - Always test the LIVE endpoint, not just local
5. **Supabase for ephemeral environments** - Files must be in cloud storage, not local filesystem
6. **Check imports when debug works but main code doesn't** - If a debug endpoint works but the main feature doesn't, check if they import dependencies differently
